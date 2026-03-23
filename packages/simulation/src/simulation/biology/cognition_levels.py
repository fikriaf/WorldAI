from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent, AgentID
import numpy as np
from dataclasses import dataclass
from typing import Dict


@dataclass
class CognitiveLevelState:
    agent_id: str
    level: int = 0
    level_name: str = "chemotaxis"
    capabilities: list[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


COGNITIVE_LEVELS = {
    0: {
        "name": "chemotaxis",
        "description": "Direct response to chemical gradients",
        "min_complexity": 0,
        "capabilities": ["gradient_sensing"],
    },
    1: {
        "name": "reflex",
        "description": "Direct input-output without memory",
        "min_complexity": 1,
        "capabilities": ["reflex_response", "simple_stimulus"],
    },
    2: {
        "name": "habituation",
        "description": "Learning through repetition",
        "min_complexity": 2,
        "capabilities": ["habituation", "sensitization", "adaptive_threshold"],
    },
    3: {
        "name": "classical_conditioning",
        "description": "Associative learning between stimuli",
        "min_complexity": 3,
        "capabilities": ["hebbian_learning", "classical_conditioning", "associative_memory"],
    },
    4: {
        "name": "operant_conditioning",
        "description": "Learning from consequences",
        "min_complexity": 4,
        "capabilities": ["reward_processing", "punishment_learning", "trial_and_error"],
    },
    5: {
        "name": "internal_representation",
        "description": "Internal model of the world",
        "min_complexity": 6,
        "capabilities": ["world_model", "prospection", "planning", "working_memory_extended"],
    },
    6: {
        "name": "meta_cognition",
        "description": "Thinking about thinking",
        "min_complexity": 10,
        "capabilities": [
            "self_monitoring",
            "strategy_selection",
            "meta_learning",
            "theory_of_mind",
        ],
    },
}


class CognitiveLevelSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._level_states: Dict[AgentID, CognitiveLevelState] = {}
        self._level_transitions: list[dict] = []

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._get_or_create_state(agent)
            old_level = state.level

            new_level = self._determine_level(agent, state)

            if new_level != old_level:
                old_name = COGNITIVE_LEVELS[old_level]["name"]
                new_name = COGNITIVE_LEVELS[new_level]["name"]
                state.level = new_level
                state.level_name = new_name
                state.capabilities = COGNITIVE_LEVELS[new_level]["capabilities"].copy()

                self._level_transitions.append(
                    {
                        "tick": ctx.tick,
                        "agent_id": agent.id,
                        "from_level": old_level,
                        "to_level": new_level,
                        "from_name": old_name,
                        "to_name": new_name,
                    }
                )

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "cognitive_level_up",
                            "agent_id": agent.id,
                            "from_level": old_level,
                            "to_level": new_level,
                            "capabilities": state.capabilities,
                        },
                        source_id=agent.id,
                    )
                )

        return events

    def _get_or_create_state(self, agent: Agent) -> CognitiveLevelState:
        if agent.id not in self._level_states:
            initial = self._determine_initial_level(agent)
            self._level_states[agent.id] = CognitiveLevelState(
                agent_id=agent.id,
                level=initial,
                level_name=COGNITIVE_LEVELS[initial]["name"],
                capabilities=COGNITIVE_LEVELS[initial]["capabilities"].copy(),
            )
        return self._level_states[agent.id]

    def _determine_initial_level(self, agent: Agent) -> int:
        if agent.neural_complexity < 1:
            return 0
        elif agent.neural_complexity < 2:
            return 1
        elif agent.neural_complexity < 3:
            return 2
        elif agent.neural_complexity < 4:
            return 3
        elif agent.neural_complexity < 6:
            return 4
        elif agent.neural_complexity < 10:
            return 5
        else:
            return 6

    def _determine_level(self, agent: Agent, state: CognitiveLevelState) -> int:
        current = state.level

        if current == 0:
            if agent.neural_complexity >= 1:
                current = 1
        elif current == 1:
            if self._has_memory(agent) and agent.neural_complexity >= 2:
                current = 2
        elif current == 2:
            if self._has_associative_learning(agent) and agent.neural_complexity >= 3:
                current = 3
        elif current == 3:
            if self._has_reward_learning(agent) and agent.neural_complexity >= 4:
                current = 4
        elif current == 4:
            if self._has_world_model(agent) and agent.neural_complexity >= 6:
                current = 5
        elif current == 5:
            if self._has_meta_cognition(agent) and agent.neural_complexity >= 10:
                current = 6

        return min(6, current)

    def _has_memory(self, agent: Agent) -> bool:
        if not agent.memory:
            return False
        return len(agent.memory.working_memory) > 0 or len(agent.memory.episodic_refs) > 0

    def _has_associative_learning(self, agent: Agent) -> bool:
        if not hasattr(self.world, "consciousness"):
            return agent.neural_complexity >= 3
        return self.world.consciousness.get_agent_phi(agent.id) > 0.2

    def _has_reward_learning(self, agent: Agent) -> bool:
        return (
            agent.neural_complexity >= 4
            and len(agent.genome.genes) >= 5
            and agent.emotion.joy > 0
            or agent.emotion.fear > 0
        )

    def _has_world_model(self, agent: Agent) -> bool:
        if not agent.memory:
            return False
        return (
            len(agent.memory.sensory_buffer) >= 3 and len(agent.memory.working_memory) >= 2
        ) or (agent.neural_complexity >= 6 and agent.group_id is not None)

    def _has_meta_cognition(self, agent: Agent) -> bool:
        if agent.neural_complexity < 10:
            return False

        if hasattr(self.world, "consciousness"):
            phi = self.world.consciousness.get_agent_phi(agent.id)
            if phi < 0.5:
                return False

        return hasattr(self.world, "recursive_improvement") or (
            agent.group_id and agent.neural_complexity >= 10
        )

    def get_agent_level(self, agent_id: AgentID) -> int:
        state = self._level_states.get(agent_id)
        return state.level if state else 0

    def get_agent_capabilities(self, agent_id: AgentID) -> list[str]:
        state = self._level_states.get(agent_id)
        return state.capabilities if state else []

    def get_level_distribution(self) -> Dict:
        levels = {i: 0 for i in range(7)}
        for state in self._level_states.values():
            levels[state.level] += 1
        return {
            k: v,
            f"{k}_{COGNITIVE_LEVELS[k]['name']}": v,
            "total_tracked": len(self._level_states),
        }

    def get_level_stats(self) -> Dict:
        if not self._level_states:
            return {
                "avg_level": 0.0,
                "max_level": 0,
                "level_distribution": {},
                "total_transitions": 0,
            }

        levels = [s.level for s in self._level_states.values()]
        return {
            "avg_level": float(np.mean(levels)),
            "max_level": int(max(levels)),
            "level_distribution": self.get_level_distribution(),
            "total_transitions": len(self._level_transitions),
        }
