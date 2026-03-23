from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID, GroupID
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class PoliticalEntity:
    entity_id: str
    entity_type: str
    leader_id: Optional[AgentID]
    member_ids: list[AgentID] = field(default_factory=list)
    power_index: float = 0.0
    dominance_rank: int = 0
    institutional_trust: float = 0.5
    resources_controlled: float = 0.0
    created_tick: int = 0


class PoliticsSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._political_entities: Dict[str, PoliticalEntity] = {}
        self._dominance_hierarchy: Dict[AgentID, float] = {}
        self._conflict_history: list[dict] = []
        self._entity_counter = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._update_dominance_hierarchy(ctx)
        self._process_power_struggles(ctx, events)
        self._form_political_entities(ctx, events)
        self._evolve_institutions(ctx, events)

        return events

    def _update_dominance_hierarchy(self, ctx: TickContext):
        agents = [a for a in self.world.agents.values() if a.is_alive]

        for agent in agents:
            power = self._compute_power_index(agent)

            conflict_prone = 0.0
            if agent.emotion.anger > 0.5:
                conflict_prone += agent.emotion.anger * 0.3
            if hasattr(self.world, "stress"):
                stress_state = self.world.stress._stress_states.get(agent.id)
                if stress_state and stress_state.is_acutely_stressed:
                    conflict_prone += 0.2

            power *= 1.0 + conflict_prone

            self._dominance_hierarchy[agent.id] = power

        sorted_agents = sorted(self._dominance_hierarchy.items(), key=lambda x: x[1], reverse=True)
        for rank, (agent_id, _) in enumerate(sorted_agents):
            pass

    def _compute_power_index(self, agent: Agent) -> float:
        power = 0.0

        power += agent.neural_complexity * 2.0

        power += agent.energy * 3.0

        if agent.group_id:
            members = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )
            power += members * 0.5

        if hasattr(self.world, "network_science"):
            profile = self.world.network_science.get_agent_network_profile(agent.id)
            power += profile.get("betweenness_centrality", 0.0) * 10.0
            if profile.get("is_hub", False):
                power += 3.0

        if hasattr(self.world, "economy"):
            eco_stats = self.world.economy.get_economy_stats()
            if eco_stats.get("total_exchanges", 0) > 0:
                power += 1.0

        if hasattr(self.world, "tool_use"):
            tool_stats = self.world.tool_use.get_tool_stats()
            if tool_stats.get("total_tools_in_use", 0) > 0:
                power += 2.0

        power += agent.health * 2.0

        return power

    def _process_power_struggles(self, ctx: TickContext, events: list):
        if len(self._dominance_hierarchy) < 2:
            return

        sorted_agents = sorted(self._dominance_hierarchy.items(), key=lambda x: x[1], reverse=True)

        for i in range(min(5, len(sorted_agents) - 1)):
            top_id, top_power = sorted_agents[i]
            challenger_id, challenger_power = sorted_agents[i + 1]

            top_agent = self.world.agents.get(top_id)
            challenger_agent = self.world.agents.get(challenger_id)

            if not top_agent or not challenger_agent:
                continue

            power_gap = top_power - challenger_power

            if power_gap < 1.0:
                conflict_prob = 0.05 * (1.0 - power_gap)
                if np.random.random() < conflict_prob:
                    self._resolve_conflict(
                        top_agent, challenger_agent, top_power, challenger_power, ctx, events
                    )

    def _resolve_conflict(
        self,
        defender: Agent,
        challenger: Agent,
        defender_power: float,
        challenger_power: float,
        ctx: TickContext,
        events: list,
    ):
        defender_strength = defender_power * (1.0 + defender.emotion.anger * 0.2)
        challenger_strength = challenger_power * (1.0 + challenger.emotion.anger * 0.2)

        defender_cost = challenger_strength * 0.1
        challenger_cost = defender_strength * 0.1

        defender.energy = max(0, defender.energy - defender_cost)
        challenger.energy = max(0, challenger.energy - challenger_cost)

        defender.health = max(0, defender.health - 0.05)
        challenger.health = max(0, challenger.health - 0.05)

        defender.emotion.anger = min(1.0, defender.emotion.anger + 0.2)
        challenger.emotion.anger = min(1.0, challenger.emotion.anger + 0.2)

        challenger_power_after = challenger_power * 0.9
        self._dominance_hierarchy[challenger.id] = challenger_power_after

        self._conflict_history.append(
            {
                "tick": ctx.tick,
                "defender": defender.id,
                "challenger": challenger.id,
                "outcome": "challenger_weakened",
            }
        )

        if len(self._conflict_history) > 100:
            self._conflict_history = self._conflict_history[-100:]

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "type": "power_struggle",
                    "defender": defender.id,
                    "challenger": challenger.id,
                    "defender_power": float(defender_power),
                    "challenger_power": float(challenger_power),
                },
                source_id=challenger.id,
                target_id=defender.id,
            )
        )

    def _form_political_entities(self, ctx: TickContext, events: list):
        social = getattr(self.world, "social", None)
        if social is None:
            return
        for group_id, group in social._groups.items():
            if group_id in self._political_entities:
                continue

            if len(group.member_ids) >= 5:
                self._entity_counter += 1
                entity_id = f"pol_entity_{self._entity_counter}"

                leader = self._select_leader(group.member_ids)

                total_power = sum(
                    self._dominance_hierarchy.get(m, 0.0)
                    for m in group.member_ids
                    if m in self._dominance_hierarchy
                )

                self._political_entities[entity_id] = PoliticalEntity(
                    entity_id=entity_id,
                    entity_type="proto_government",
                    leader_id=leader.id if leader else None,
                    member_ids=group.member_ids.copy(),
                    power_index=total_power,
                    resources_controlled=len(group.member_ids),
                    created_tick=ctx.tick,
                )

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "political_entity_formed",
                            "entity_id": entity_id,
                            "members": len(group.member_ids),
                            "leader": leader.id if leader else None,
                        },
                    )
                )

    def _select_leader(self, member_ids: list[AgentID]) -> Optional[Agent]:
        candidates = []
        for member_id in member_ids:
            agent = self.world.agents.get(member_id)
            if not agent or not agent.is_alive:
                continue
            power = self._dominance_hierarchy.get(member_id, 0.0)
            trust = sum(
                agent.reputation.get(other, 0.5) for other in member_ids if other != member_id
            ) / max(1, len(member_ids) - 1)
            leadership_score = power * 0.6 + trust * 0.4
            candidates.append((agent, leadership_score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _evolve_institutions(self, ctx: TickContext, events: list):
        for entity in self._political_entities.values():
            if len(entity.member_ids) < 3:
                continue

            age = ctx.tick - entity.created_tick

            if age > 100:
                member_count = sum(
                    1
                    for m in entity.member_ids
                    if m in self.world.agents and self.world.agents[m].is_alive
                )
                entity.institutional_trust = min(
                    1.0,
                    entity.institutional_trust
                    + (member_count / max(1, len(entity.member_ids))) * 0.01,
                )

            if hasattr(self.world, "economy"):
                eco_stats = self.world.economy.get_economy_stats()
                if eco_stats.get("total_exchanges", 0) > 0:
                    entity.institutional_trust = min(1.0, entity.institutional_trust + 0.005)

            recent_conflicts = [
                c
                for c in self._conflict_history[-20:]
                if c["defender"] in entity.member_ids or c["challenger"] in entity.member_ids
            ]
            if len(recent_conflicts) > 3:
                entity.institutional_trust = max(
                    0.0, entity.institutional_trust - 0.02 * len(recent_conflicts)
                )

    def get_political_stats(self) -> Dict:
        if not self._political_entities:
            return {
                "num_entities": 0,
                "num_conflicts": 0,
                "avg_institutional_trust": 0.0,
                "avg_power_index": 0.0,
            }

        return {
            "num_entities": len(self._political_entities),
            "num_conflicts": len(self._conflict_history),
            "avg_institutional_trust": float(
                np.mean([e.institutional_trust for e in self._political_entities.values()])
            ),
            "avg_power_index": float(
                np.mean([e.power_index for e in self._political_entities.values()])
            ),
            "most_powerful_entity": max(
                self._political_entities.items(),
                key=lambda x: x[1].power_index,
                default=(None, None),
            )[0],
            "entities_with_trust": sum(
                1 for e in self._political_entities.values() if e.institutional_trust > 0.5
            ),
        }
