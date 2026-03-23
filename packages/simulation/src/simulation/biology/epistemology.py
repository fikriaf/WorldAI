from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class Belief:
    proposition: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    source_type: str = "direct"
    formed_tick: int = 0


@dataclass
class EpistemologyState:
    agent_id: AgentID
    beliefs: Dict[str, Belief] = field(default_factory=dict)
    direct_experiences: List[str] = field(default_factory=list)
    testimony_received: List[Dict] = field(default_factory=list)
    rationality_bound: float = 0.5
    theory_components: Dict[str, List[str]] = field(default_factory=dict)


class EpistemologySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._agent_states: Dict[AgentID, EpistemologyState] = {}
        self._theories: Dict[str, Dict] = {}
        self._theory_counter = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._initialize_agent_states(ctx)
        self._process_direct_perception(ctx)
        self._process_testimony(ctx)
        self._form_theories(ctx, events)
        self._update_beliefs(ctx, events)

        return events

    def _initialize_agent_states(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue
            if agent.id not in self._agent_states:
                self._agent_states[agent.id] = EpistemologyState(
                    agent_id=agent.id,
                    rationality_bound=self._compute_rationality_bound(agent),
                )

    def _compute_rationality_bound(self, agent: Agent) -> float:
        bound = 0.3
        bound += agent.neural_complexity * 0.1
        if hasattr(self.world, "economy"):
            eco_stats = self.world.economy.get_economy_stats()
            if eco_stats.get("total_exchanges", 0) > 10:
                bound += 0.1
        if hasattr(self.world, "social"):
            bound += 0.05
        return min(0.9, bound)

    def _get_max_beliefs(self, rationality_bound: float) -> int:
        return max(3, int(rationality_bound * 20))

    def _get_max_social_processing(self, rationality_bound: float) -> int:
        return max(2, int(rationality_bound * 10))

    def _get_max_theory_complexity(self, rationality_bound: float) -> int:
        return max(2, int(rationality_bound * 5))

    def _enforce_belief_limit(self, state: EpistemologyState) -> None:
        max_beliefs = self._get_max_beliefs(state.rationality_bound)
        if len(state.beliefs) > max_beliefs:
            sorted_beliefs = sorted(
                state.beliefs.items(),
                key=lambda x: (x[1].confidence, x[1].formed_tick),
                reverse=True,
            )
            kept = dict(sorted_beliefs[:max_beliefs])
            state.beliefs.clear()
            state.beliefs.update(kept)

    def _process_direct_perception(self, ctx: TickContext):
        comm = getattr(self.world, "communication", None)
        if comm is None:
            return

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            cell_x = int(agent.position.x) % self.world.config.grid_width
            cell_y = int(agent.position.y) % self.world.config.grid_height
            cell = self.world.grid.get((cell_x, cell_y))

            if not cell:
                continue

            environment_cues = []
            if cell.temperature > 25:
                environment_cues.append("hot")
            elif cell.temperature < 15:
                environment_cues.append("cold")
            if cell.light_level > 0.7:
                environment_cues.append("bright")
            elif cell.light_level < 0.3:
                environment_cues.append("dark")

            for cue in environment_cues:
                if cue not in state.direct_experiences:
                    state.direct_experiences.append(cue)

            max_social = self._get_max_social_processing(state.rationality_bound)
            nearby_agents = [
                a
                for a in self.world.agents.values()
                if a.is_alive
                and a.id != agent.id
                and (
                    (a.position.x - agent.position.x) ** 2 + (a.position.y - agent.position.y) ** 2
                )
                ** 0.5
                < agent.sensory_range
            ]
            nearby_agents = nearby_agents[:max_social]
            if len(nearby_agents) > 2:
                belief_key = "social_density_high"
                if belief_key not in state.beliefs:
                    state.beliefs[belief_key] = Belief(
                        proposition=belief_key,
                        confidence=0.3,
                        evidence=["direct_observation"],
                        source_type="direct",
                        formed_tick=ctx.tick,
                    )
                else:
                    state.beliefs[belief_key].confidence = min(
                        0.9, state.beliefs[belief_key].confidence + 0.05
                    )

    def _process_testimony(self, ctx: TickContext):
        comm = getattr(self.world, "communication", None)
        if comm is None:
            return

        messages = getattr(comm, "_message_history", [])
        recent_messages = [m for m in messages if ctx.tick - m.get("tick", 0) < 50]

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            relevant = [
                m
                for m in recent_messages
                if m.get("receiver_id") == agent.id or m.get("sender_id") == agent.id
            ]

            for msg in relevant:
                sender_id = msg.get("sender_id")
                if not sender_id or sender_id == agent.id:
                    continue

                sender_trust = agent.reputation.get(sender_id, 0.5)
                content = msg.get("content", "")

                if content and sender_trust > 0.3:
                    belief_key = f"testimony_{sender_id}_{content[:20]}"
                    if belief_key not in state.beliefs:
                        state.beliefs[belief_key] = Belief(
                            proposition=content[:50],
                            confidence=sender_trust * 0.5,
                            evidence=[f"testimony_from_{sender_id}"],
                            source_type="testimony",
                            formed_tick=ctx.tick,
                        )
                        state.testimony_received.append(
                            {
                                "from": sender_id,
                                "content": content[:30],
                                "tick": ctx.tick,
                            }
                        )

            self._enforce_belief_limit(state)

    def _form_theories(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 3:
                continue

            state = self._agent_states.get(agent.id)
            if state is None or len(state.beliefs) < 3:
                continue

            if np.random.random() < 0.01:
                self._theory_counter += 1
                theory_id = f"theory_{self._theory_counter}"

                relevant_beliefs = [b for b in state.beliefs.values() if b.confidence > 0.4]
                if len(relevant_beliefs) < 2:
                    continue

                max_complexity = self._get_max_theory_complexity(state.rationality_bound)
                propositions = [b.proposition for b in relevant_beliefs[:max_complexity]]
                state.theory_components[theory_id] = propositions

                self._theories[theory_id] = {
                    "propositions": propositions,
                    "creator_id": agent.id,
                    "created_tick": ctx.tick,
                    "confidence": np.mean([b.confidence for b in relevant_beliefs]),
                }

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "theory_formation",
                            "agent_id": agent.id,
                            "theory_id": theory_id,
                            "propositions": propositions,
                        },
                        source_id=agent.id,
                    )
                )

    def _update_beliefs(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            for key, belief in state.beliefs.items():
                if belief.source_type == "direct":
                    decay_rate = 0.001
                else:
                    decay_rate = 0.005
                belief.confidence = max(0.1, belief.confidence - decay_rate)

                if belief.confidence < 0.1 and key in state.beliefs:
                    del state.beliefs[key]

            env = getattr(self.world, "environment", None)
            if env and hasattr(env, "_cycles"):
                season = env._cycles.get("season", "spring")
                if season == "winter" and agent.energy < 0.3:
                    belief_key = "survival_difficult"
                    if belief_key not in state.beliefs:
                        state.beliefs[belief_key] = Belief(
                            proposition="survival_difficult",
                            confidence=0.6,
                            evidence=["direct_experience"],
                            source_type="direct",
                            formed_tick=ctx.tick,
                        )

    def get_epistemology_stats(self) -> Dict:
        total_agents = len(self._agent_states)
        total_beliefs = sum(len(s.beliefs) for s in self._agent_states.values())
        total_theories = len(self._theories)

        avg_confidence = 0.0
        if total_beliefs > 0:
            all_confidences = [
                b.confidence for s in self._agent_states.values() for b in s.beliefs.values()
            ]
            avg_confidence = float(np.mean(all_confidences)) if all_confidences else 0.0

        avg_rationality_bound = 0.0
        if total_agents > 0:
            bounds = [s.rationality_bound for s in self._agent_states.values()]
            avg_rationality_bound = float(np.mean(bounds))

        return {
            "agents_with_beliefs": total_agents,
            "total_beliefs": total_beliefs,
            "total_theories": total_theories,
            "avg_belief_confidence": avg_confidence,
            "avg_rationality_bound": avg_rationality_bound,
        }
