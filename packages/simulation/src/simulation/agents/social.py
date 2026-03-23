from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from ..types import AgentID, GroupID, WorldEvent, EventType, TickContext, Agent, Vec2

DUNBAR_NUMBER = 150
DUNBAR_COHORT_SIZE = 15
HIERARCHY_THRESHOLDS = {
    "flat": 8,
    "simple_hierarchy": 150,
    "multi_level": 1500,
}


@dataclass
class SocialRelationship:
    agent_id: AgentID
    trust: float
    interaction_count: int = 0
    last_interaction_tick: int = 0


@dataclass
class AgentSignal:
    sender_id: AgentID
    message: str
    intensity: float
    position: Vec2
    tick: int


@dataclass
class AgentGroup:
    id: GroupID
    member_ids: list[AgentID]
    center: Vec2
    formation: str = "loose"
    cohesion: float = 0.5
    shared_resources: float = 0.0
    created_tick: int = 0
    hierarchy_level: str = "flat"
    uses_formal_protocols: bool = False

    def _compute_hierarchy_level(self) -> str:
        size = len(self.member_ids)
        if size < HIERARCHY_THRESHOLDS["flat"]:
            return "flat"
        elif size < HIERARCHY_THRESHOLDS["simple_hierarchy"]:
            return "simple_hierarchy"
        elif size < HIERARCHY_THRESHOLDS["multi_level"]:
            return "multi_level"
        else:
            return "bureaucratic"

    def _uses_protocols(self) -> bool:
        return len(self.member_ids) >= HIERARCHY_THRESHOLDS["simple_hierarchy"]


class SocialSystem:
    def __init__(self, world):
        self.world = world
        self._groups: dict[GroupID, AgentGroup] = {}
        self._pending_signals: list[AgentSignal] = []
        self._signal_cooldowns: dict[AgentID, int] = {}
        self._group_counter = 0
        self._relationship_tracker: dict[AgentID, list[SocialRelationship]] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []
        agents = [a for a in self.world.agents.values() if a.is_alive]

        self._process_signals(agents, events)
        self._update_groups(agents)
        self._form_groups(agents)
        self._process_reputation(agents)

        return events

    def _process_signals(self, agents: list[Agent], events: list[WorldEvent]) -> None:
        for agent in agents:
            if agent.neural_complexity < 2:
                continue

            cooldown = self._signal_cooldowns.get(agent.id, 0)
            if cooldown > 0:
                self._signal_cooldowns[agent.id] = cooldown - 1
                continue

            nearby = self._get_nearby_agents(agent, agent.sensory_range * 2)
            if not nearby:
                continue

            signal_msg = self._generate_signal(agent)
            if signal_msg and nearby:
                region_x = int(agent.position.x) // 10
                region_y = int(agent.position.y) // 10
                idx = self.world.prng.randint(region_x, region_y, 0, len(nearby))
                target = nearby[idx]
                self._pending_signals.append(
                    AgentSignal(
                        sender_id=agent.id,
                        message=signal_msg,
                        intensity=min(agent.energy / 100, 1.0),
                        position=agent.position,
                        tick=self.world.tick,
                    )
                )
                self._signal_cooldowns[agent.id] = 50

                events.append(
                    WorldEvent(
                        tick=self.world.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={"signal": signal_msg, "from": agent.id, "to": target.id},
                        source_id=agent.id,
                        target_id=target.id,
                    )
                )

    def _generate_signal(self, agent: Agent) -> Optional[str]:
        if agent.emotion.fear > 0.7:
            return "danger"
        elif agent.emotion.joy > 0.6:
            return "food_found"
        elif agent.emotion.trust > 0.7 and agent.group_id:
            return "ally"
        elif agent.energy < 20:
            return "need_resources"
        return None

    def _get_nearby_agents(self, agent: Agent, radius: float) -> list[Agent]:
        nearby = []
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            if dx * dx + dy * dy <= radius * radius:
                nearby.append(other)
        return nearby

    def _update_groups(self, agents: list[Agent]) -> None:
        for group in self._groups.values():
            if not group.member_ids:
                continue

            total_x = 0.0
            total_y = 0.0
            alive_members = 0
            total_leadership_score = 0.0
            leader_candidate = None

            for member_id in group.member_ids:
                member = self.world.agents.get(member_id)
                if member and member.is_alive:
                    total_x += member.position.x
                    total_y += member.position.y
                    alive_members += 1

                    personality = getattr(member, "personality", None)
                    if personality:
                        leadership_score = (
                            personality.conscientiousness * 0.4
                            + personality.openness * 0.3
                            + personality.extraversion * 0.2
                            + (1.0 - personality.neuroticism) * 0.1
                        )
                        if leadership_score > total_leadership_score:
                            total_leadership_score = leadership_score
                            leader_candidate = member_id

            if alive_members > 0:
                group.center = Vec2(total_x / alive_members, total_y / alive_members)
                group.cohesion = min(alive_members / 5, 1.0)
                group.hierarchy_level = group._compute_hierarchy_level()
                group.uses_formal_protocols = group._uses_protocols()
            else:
                group.cohesion = 0.0

        dead_groups = [gid for gid, g in self._groups.items() if g.cohesion <= 0]
        for gid in dead_groups:
            del self._groups[gid]

    def _get_dunbar_limit(self, agent: Agent) -> int:
        base = DUNBAR_COHORT_SIZE
        extraversion = getattr(agent, "personality", None)
        if extraversion:
            extraversion = extraversion.extraversion
        else:
            extraversion = 0.5
        return min(DUNBAR_NUMBER, int(base * (0.5 + extraversion)))

    def _enforce_dunbar_limit(self, agent: Agent) -> None:
        if agent is None or agent.id not in self._relationship_tracker:
            return
        relationships = self._relationship_tracker[agent.id]
        dunbar_limit = self._get_dunbar_limit(agent)
        if len(relationships) > dunbar_limit:
            sorted_rels = sorted(
                relationships,
                key=lambda r: (r.trust, r.interaction_count),
                reverse=True,
            )
            self._relationship_tracker[agent.id] = sorted_rels[:dunbar_limit]

    def _track_interaction(self, agent_id: AgentID, other_id: AgentID) -> None:
        if agent_id not in self._relationship_tracker:
            self._relationship_tracker[agent_id] = []
        relationships = self._relationship_tracker[agent_id]
        existing = next((r for r in relationships if r.agent_id == other_id), None)
        if existing:
            existing.interaction_count += 1
            existing.last_interaction_tick = self.world.tick
        else:
            relationships.append(
                SocialRelationship(
                    agent_id=other_id,
                    trust=0.5,
                    interaction_count=1,
                    last_interaction_tick=self.world.tick,
                )
            )
        agent = self.world.agents.get(agent_id)
        if agent:
            self._enforce_dunbar_limit(agent)

    def _form_groups(self, agents: list[Agent]) -> None:
        ungrouped = [a for a in agents if not a.group_id and a.neural_complexity >= 1]

        for agent in ungrouped:
            personality = getattr(agent, "personality", None)
            join_threshold = 0.4
            if personality:
                if personality.extraversion > 0.5:
                    join_threshold -= personality.extraversion * 0.15
                if personality.agreeableness > 0.5:
                    join_threshold -= personality.agreeableness * 0.1
                if personality.neuroticism > 0.6:
                    join_threshold += personality.neuroticism * 0.1

            nearby = self._get_nearby_agents(agent, agent.sensory_range * 1.5)
            potential_members = [a for a in nearby if not a.group_id and a.neural_complexity >= 1]

            if len(potential_members) >= 2:
                trust_scores = []
                for other in potential_members:
                    trust = agent.reputation.get(other.id, 0.5)

                    other_personality = getattr(other, "personality", None)
                    if other_personality and personality:
                        if other.group_id and other.group_id == agent.group_id:
                            trust += personality.agreeableness * 0.05
                        else:
                            similarity = (
                                abs(personality.openness - other_personality.openness)
                                + abs(personality.agreeableness - other_personality.agreeableness)
                            ) * 0.1
                            trust += (1.0 - similarity) * personality.agreeableness * 0.1

                    if trust > join_threshold:
                        trust_scores.append((other, trust))

                if len(trust_scores) >= 2:
                    self._group_counter += 1
                    group_id = f"group_{self._group_counter}"
                    members = [agent.id] + [t[0].id for t in trust_scores[:4]]

                    center_x = sum(self.world.agents[m].position.x for m in members) / len(members)
                    center_y = sum(self.world.agents[m].position.y for m in members) / len(members)

                    self._groups[group_id] = AgentGroup(
                        id=group_id,
                        member_ids=members,
                        center=Vec2(center_x, center_y),
                        created_tick=self.world.tick,
                    )

                    for member_id in members:
                        if member_id in self.world.agents:
                            self.world.agents[member_id].group_id = group_id

    def _process_reputation(self, agents: list[Agent]) -> None:
        for agent in agents:
            personality = getattr(agent, "personality", None)
            in_group_bias_strength = 0.01
            out_group_penalty = 0.005

            if personality:
                in_group_bias_strength *= 0.5 + personality.agreeableness * 0.5
                out_group_penalty *= 0.5 + personality.agreeableness * 0.3

            nearby = self._get_nearby_agents(agent, agent.sensory_range)

            for other in nearby:
                if other.id == agent.id:
                    continue

                if other.group_id and agent.group_id == other.group_id:
                    agent.reputation[other.id] = min(
                        agent.reputation.get(other.id, 0.5) + in_group_bias_strength, 1.0
                    )
                    self._track_interaction(agent.id, other.id)

                    if personality and personality.agreeableness > 0.5:
                        other_personality = getattr(other, "personality", None)
                        if other_personality:
                            similarity = (
                                1.0
                                - (
                                    abs(personality.openness - other_personality.openness)
                                    + abs(
                                        personality.conscientiousness
                                        - other_personality.conscientiousness
                                    )
                                    + abs(personality.extraversion - other_personality.extraversion)
                                )
                                / 3.0
                            )
                            agent.reputation[other.id] = min(
                                agent.reputation.get(other.id, 0.5) + similarity * 0.01, 1.0
                            )
                else:
                    distance = (
                        (other.position.x - agent.position.x) ** 2
                        + (other.position.y - agent.position.y) ** 2
                    ) ** 0.5
                    if distance < agent.sensory_range * 0.5:
                        agent.reputation[other.id] = max(
                            agent.reputation.get(other.id, 0.5) - out_group_penalty, 0.0
                        )

    def get_group(self, group_id: GroupID) -> Optional[AgentGroup]:
        return self._groups.get(group_id)

    def get_agent_groups(self, agent_id: AgentID) -> list[AgentGroup]:
        return [g for g in self._groups.values() if agent_id in g.member_ids]

    def get_recent_signals(
        self, position: Vec2, radius: float, since_tick: int
    ) -> list[AgentSignal]:
        signals = []
        for signal in self._pending_signals:
            if signal.tick < since_tick:
                continue
            dx = signal.position.x - position.x
            dy = signal.position.y - position.y
            if dx * dx + dy * dy <= radius * radius:
                signals.append(signal)
        return signals

    def get_group_count(self) -> int:
        return len(self._groups)

    def get_total_members(self) -> int:
        return sum(len(g.member_ids) for g in self._groups.values())

    def get_social_stats(self) -> dict:
        total_relationships = sum(len(r) for r in self._relationship_tracker.values())
        avg_relationships = (
            total_relationships / len(self._relationship_tracker)
            if self._relationship_tracker
            else 0
        )
        hierarchy_counts = {
            "flat": 0,
            "simple_hierarchy": 0,
            "multi_level": 0,
            "bureaucratic": 0,
        }
        for g in self._groups.values():
            hierarchy_counts[g.hierarchy_level] = hierarchy_counts.get(g.hierarchy_level, 0) + 1
        return {
            "total_groups": len(self._groups),
            "total_members": self.get_total_members(),
            "total_relationships": total_relationships,
            "avg_relationships_per_agent": avg_relationships,
            "dunbar_limit": DUNBAR_NUMBER,
            "hierarchy_distribution": hierarchy_counts,
            "groups_with_protocols": sum(
                1 for g in self._groups.values() if g.uses_formal_protocols
            ),
        }
