from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class StrategyState:
    strategy_id: str
    success_count: int = 0
    failure_count: int = 0
    total_reward: float = 0.0
    last_used_tick: int = 0


@dataclass
class RecursiveImprovementState:
    agent_id: AgentID
    strategies: Dict[str, StrategyState] = field(default_factory=dict)
    meta_learning_rate: float = 0.1
    adaptation_score: float = 0.5
    complexity_growth: float = 0.0
    self_modification_count: int = 0
    learning_to_learn_ability: float = 0.0


class RecursiveImprovementSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._agent_states: Dict[AgentID, RecursiveImprovementState] = {}
        self._strategy_counter = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._initialize_states(ctx)
        self._adapt_strategies(ctx, events)
        self._meta_learn(ctx, events)
        self._self_modify_behavior(ctx, events)
        self._grow_complexity(ctx, events)

        return events

    def _initialize_states(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            if agent.id not in self._agent_states:
                self._agent_states[agent.id] = RecursiveImprovementState(
                    agent_id=agent.id,
                    meta_learning_rate=0.1 + agent.neural_complexity * 0.02,
                    learning_to_learn_ability=agent.neural_complexity * 0.1,
                )

                self._strategy_counter += 1
                state = self._agent_states[agent.id]
                state.strategies["explore"] = StrategyState(
                    strategy_id="explore",
                    last_used_tick=ctx.tick,
                )
                state.strategies["exploit"] = StrategyState(
                    strategy_id="exploit",
                    last_used_tick=ctx.tick,
                )

    def _adapt_strategies(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None or len(state.strategies) == 0:
                continue

            reward = self._compute_reward(agent, ctx)

            for strategy_key, strategy in state.strategies.items():
                if ctx.tick - strategy.last_used_tick > 100:
                    continue

                total_uses = strategy.success_count + strategy.failure_count
                if total_uses > 0:
                    success_rate = strategy.success_count / total_uses

                    if success_rate > 0.6:
                        strategy.total_reward += 0.1
                    elif success_rate < 0.3:
                        strategy.total_reward -= 0.1

                strategy.total_reward += reward * 0.1

            if reward > 0.5:
                active_strategies = [
                    (k, s) for k, s in state.strategies.items() if ctx.tick - s.last_used_tick < 50
                ]
                if active_strategies:
                    best_key = max(active_strategies, key=lambda x: x[1].total_reward)[0]
                    state.strategies[best_key].success_count += 1
            else:
                active_strategies = [
                    (k, s) for k, s in state.strategies.items() if ctx.tick - s.last_used_tick < 50
                ]
                if active_strategies:
                    for key, strategy in active_strategies:
                        strategy.failure_count += 1

            if len(state.strategies) < 4 and np.random.random() < 0.01:
                self._strategy_counter += 1
                new_strategy_id = f"strategy_{self._strategy_counter}"
                state.strategies[new_strategy_id] = StrategyState(
                    strategy_id=new_strategy_id,
                    last_used_tick=ctx.tick,
                )

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "new_strategy_developed",
                            "agent_id": agent.id,
                            "strategy_id": new_strategy_id,
                        },
                        source_id=agent.id,
                    )
                )

    def _compute_reward(self, agent: Agent, ctx: TickContext) -> float:
        reward = 0.0
        reward += agent.energy * 0.5
        reward += agent.health * 0.3

        if agent.neural_complexity > 2:
            reward += 0.2

        return min(1.0, reward)

    def _meta_learn(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            if hasattr(self.world, "epistemology"):
                epi = self.world.epistemology
                if agent.id in epi._agent_states:
                    epi_state = epi._agent_states[agent.id]
                    belief_count = len(epi_state.beliefs)
                    state.learning_to_learn_ability = min(1.0, belief_count * 0.1)

            if state.learning_to_learn_ability > 0.3:
                state.meta_learning_rate = min(0.5, state.meta_learning_rate + 0.005)

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "meta_learning_advancement",
                            "agent_id": agent.id,
                            "learning_rate": state.meta_learning_rate,
                        },
                        source_id=agent.id,
                    )
                )

    def _self_modify_behavior(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 4:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            if np.random.random() < 0.001:
                state.self_modification_count += 1
                state.adaptation_score = min(1.0, state.adaptation_score + 0.05)

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "self_modification",
                            "agent_id": agent.id,
                            "modification_count": state.self_modification_count,
                            "adaptation_score": state.adaptation_score,
                        },
                        source_id=agent.id,
                    )
                )

    def _grow_complexity(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            knowledge_accumulation = 0.0

            if hasattr(self.world, "science"):
                science = self.world.science
                stats = science.get_science_stats()
                if stats.get("verified_hypotheses", 0) > 0:
                    knowledge_accumulation += 0.01

            if hasattr(self.world, "epistemology"):
                epi = self.world.epistemology
                if agent.id in epi._agent_states:
                    epi_state = epi._agent_states[agent.id]
                    knowledge_accumulation += len(epi_state.beliefs) * 0.005
                    knowledge_accumulation += len(epi_state.theory_components) * 0.01

            if state.adaptation_score > 0.7:
                knowledge_accumulation *= 1.5

            state.complexity_growth += knowledge_accumulation

            if state.complexity_growth > 1.0 and agent.neural_complexity < 10:
                if np.random.random() < 0.1:
                    agent.neural_complexity += 1

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "complexity_growth",
                                "agent_id": agent.id,
                                "new_complexity": agent.neural_complexity,
                            },
                            source_id=agent.id,
                        )
                    )

                    state.complexity_growth = 0.0

    def get_improvement_stats(self) -> Dict:
        total_agents = len(self._agent_states)
        total_strategies = sum(len(s.strategies) for s in self._agent_states.values())
        avg_adaptation = 0.0
        if self._agent_states:
            adaptations = [s.adaptation_score for s in self._agent_states.values()]
            avg_adaptation = float(np.mean(adaptations)) if adaptations else 0.0

        total_self_mods = sum(s.self_modification_count for s in self._agent_states.values())

        return {
            "agents_with_improvement": total_agents,
            "total_strategies": total_strategies,
            "avg_adaptation_score": avg_adaptation,
            "total_self_modifications": total_self_mods,
        }
