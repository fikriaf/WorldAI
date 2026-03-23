from ..systems.base import System
from ..types import (
    TickContext,
    WorldEvent,
    EventType,
    Agent,
    AgentID,
    WorldState,
    GridCell,
    ElementType,
)
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


ANOMALY_THRESHOLD = 3
REPLICATION_THRESHOLD = 2


@dataclass
class FalsificationRecord:
    experiment_id: str
    hypothesis_id: str
    tick: int
    anomaly_count: int
    is_falsified: bool
    ad_hoc_modifications: int


@dataclass
class ScientificConsensus:
    hypothesis_id: str
    supporting_agents: list[str]
    confidence: float
    consensus_tick: int


@dataclass
class AuxiliaryHypothesis:
    id: str
    statement: str
    modification_count: int = 0


@dataclass
class Hypothesis:
    id: str
    hypothesis: str
    creator_id: AgentID
    testable_prediction: str
    supporting_evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5
    created_tick: int = 0
    tested: bool = False
    falsified: bool = False
    verified: bool = False
    anomaly_count: int = 0
    ad_hoc_modifications: int = 0
    auxiliaries: List[AuxiliaryHypothesis] = field(default_factory=list)
    falsification_records: List[FalsificationRecord] = field(default_factory=list)


@dataclass
class Experiment:
    id: str
    hypothesis_id: str
    designer_id: AgentID
    design: str
    result: Optional[str] = None
    result_tick: Optional[int] = None
    competing_hypothesis_id: Optional[str] = None
    replicated_by: List[str] = field(default_factory=list)
    result_value: Optional[float] = None
    predicted_value: Optional[float] = None


@dataclass
class ScientificKnowledge:
    group_id: str
    hypotheses: List[Hypothesis] = field(default_factory=list)
    experiments: List[Experiment] = field(default_factory=list)
    verified_knowledge: List[str] = field(default_factory=list)
    innovation_count: int = 0
    consensus: Optional[ScientificConsensus] = None


class ScienceSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._group_knowledge: Dict[str, ScientificKnowledge] = {}
        self._consensuses: Dict[str, ScientificConsensus] = {}
        self._hypothesis_counter = 0
        self._experiment_counter = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._form_hypotheses(ctx, events)
        self._design_experiments(ctx)
        self._run_falsification_checks(ctx, events)
        self._accumulate_knowledge(ctx, events)
        self._generate_innovations(ctx, events)

        return events

    def _form_hypotheses(self, ctx: TickContext, events: list[WorldEvent]):
        epi = getattr(self.world, "epistemology", None)
        if epi is None:
            return

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 3:
                continue
            if agent.group_id is None:
                continue

            epi_stats = epi.get_epistemology_stats()
            if epi_stats.get("total_theories", 0) == 0:
                continue

            if np.random.random() < 0.005:
                self._hypothesis_counter += 1
                hypothesis_id = f"hyp_{self._hypothesis_counter}"

                observations = [
                    "environment_pattern",
                    "agent_behavior",
                    "resource_distribution",
                ]
                selected_obs = np.random.choice(observations, 1).tolist()

                predictions = [
                    "increase_survival",
                    "improve_efficiency",
                    "enhance_reproduction",
                ]
                selected_pred = np.random.choice(predictions, 1).tolist()

                aux_id = f"aux_{hypothesis_id}_0"
                aux = AuxiliaryHypothesis(
                    id=aux_id,
                    statement=f"Default auxiliary assumption for {selected_obs[0]}",
                )

                hypothesis = Hypothesis(
                    id=hypothesis_id,
                    hypothesis=f"Observation: {selected_obs[0]} leads to {selected_pred[0]}",
                    creator_id=agent.id,
                    testable_prediction=selected_pred[0],
                    supporting_evidence=selected_obs,
                    confidence=0.3 + agent.neural_complexity * 0.1,
                    created_tick=ctx.tick,
                    auxiliaries=[aux],
                )

                self._hypotheses[hypothesis_id] = hypothesis

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "hypothesis_formed",
                            "hypothesis_id": hypothesis_id,
                            "creator_id": agent.id,
                            "prediction": selected_pred[0],
                        },
                        source_id=agent.id,
                    )
                )

    def _design_experiments(self, ctx: TickContext):
        active_hypotheses = [
            h for h in self._hypotheses.values() if not h.tested and not h.falsified
        ]
        if not active_hypotheses:
            return

        for hypothesis in active_hypotheses:
            age = ctx.tick - hypothesis.created_tick
            if age < 50:
                continue

            if np.random.random() < 0.05:
                self._experiment_counter += 1
                experiment_id = f"exp_{self._experiment_counter}"

                design = self._select_experiment_design(hypothesis)
                competing_h_id = self._find_competing_hypothesis(hypothesis)

                experiment = Experiment(
                    id=experiment_id,
                    hypothesis_id=hypothesis.id,
                    designer_id=hypothesis.creator_id,
                    design=design,
                    result_tick=None,
                    competing_hypothesis_id=competing_h_id,
                )

                self._experiments[experiment_id] = experiment
                hypothesis.tested = True

    def _select_experiment_design(self, hypothesis: Hypothesis) -> str:
        pred = hypothesis.testable_prediction
        if "survival" in pred.lower():
            return "test_mortality_rate"
        elif "efficiency" in pred.lower():
            return "test_energy_conservation"
        elif "reproduction" in pred.lower() or "agent" in str(hypothesis.supporting_evidence):
            return "test_agent_aggregation"
        else:
            return "test_food_distribution"

    def _find_competing_hypothesis(self, hypothesis: Hypothesis) -> Optional[str]:
        for other in self._hypotheses.values():
            if other.id == hypothesis.id:
                continue
            if other.falsified or other.verified:
                continue
            if other.testable_prediction == hypothesis.testable_prediction:
                if other.supporting_evidence != hypothesis.supporting_evidence:
                    return other.id
        return None

    def _run_falsification_checks(self, ctx: TickContext, events: list[WorldEvent]):
        world_state = self._get_world_state_summary()

        for hypothesis in self._hypotheses.values():
            if hypothesis.falsified:
                continue

            matching_experiments = [
                e
                for e in self._experiments.values()
                if e.hypothesis_id == hypothesis.id and e.result is not None
            ]

            if not matching_experiments:
                for exp in [
                    e for e in self._experiments.values() if e.hypothesis_id == hypothesis.id
                ]:
                    if exp.result is None:
                        result_data = self._execute_experiment(exp, hypothesis, world_state)
                        exp.result = result_data["result"]
                        exp.result_value = result_data["value"]
                        exp.predicted_value = result_data["predicted"]
                        exp.result_tick = ctx.tick
                        matching_experiments.append(exp)
                        break
                if not matching_experiments:
                    continue

            for exp in matching_experiments:
                if exp.result is None:
                    continue

                anomaly_detected, discrepancy = self._check_anomaly(exp, hypothesis, world_state)

                if anomaly_detected:
                    hypothesis.anomaly_count += 1

                    record = FalsificationRecord(
                        experiment_id=exp.id,
                        hypothesis_id=hypothesis.id,
                        tick=ctx.tick,
                        anomaly_count=hypothesis.anomaly_count,
                        is_falsified=False,
                        ad_hoc_modifications=hypothesis.ad_hoc_modifications,
                    )
                    hypothesis.falsification_records.append(record)

                    if hypothesis.anomaly_count >= ANOMALY_THRESHOLD:
                        hypothesis.falsified = True
                        hypothesis.confidence = 0.0

                        events.append(
                            WorldEvent(
                                tick=ctx.tick,
                                type=EventType.GOD_MODE_INTERVENTION,
                                data={
                                    "type": "hypothesis_falsified",
                                    "hypothesis_id": hypothesis.id,
                                    "experiment_id": exp.id,
                                    "anomaly_count": hypothesis.anomaly_count,
                                },
                                source_id=hypothesis.creator_id,
                            )
                        )
                    else:
                        if np.random.random() < 0.3:
                            self._apply_ad_hoc_modification(
                                hypothesis, exp, discrepancy, events, ctx
                            )

                else:
                    if exp.replicated_by.__len__() >= REPLICATION_THRESHOLD:
                        if not hypothesis.verified:
                            hypothesis.verified = True
                            hypothesis.confidence = min(1.0, hypothesis.confidence + 0.2)

                            events.append(
                                WorldEvent(
                                    tick=ctx.tick,
                                    type=EventType.GOD_MODE_INTERVENTION,
                                    data={
                                        "type": "hypothesis_verified",
                                        "hypothesis_id": hypothesis.id,
                                        "replication_count": exp.replicated_by.__len__(),
                                    },
                                    source_id=hypothesis.creator_id,
                                )
                            )

    def _get_world_state_summary(self) -> Dict:
        agents = list(self.world.agents.values())
        alive_agents = [a for a in agents if a.is_alive]

        grid_width = getattr(self.world, "grid_width", 64)
        grid_height = getattr(self.world, "grid_height", 64)

        if hasattr(self.world, "grid") and self.world.grid:
            primum_densities = []
            agent_positions = []

            for cell in self.world.grid.values():
                if isinstance(cell, GridCell):
                    primum = cell.chemical_pool.get(ElementType.PRIMUM, 0.0)
                    primum_densities.append(primum)
                    for ag in cell.agent_ids:
                        if ag in self.world.agents:
                            agent_positions.append(self.world.agents[ag].position)

            food_variance = float(np.var(primum_densities)) if primum_densities else 0.0
            food_mean = float(np.mean(primum_densities)) if primum_densities else 0.0
        else:
            food_variance = 0.0
            food_mean = 0.0
            agent_positions = [a.position for a in alive_agents]

        spatial_aggregation = 0.0
        if len(agent_positions) > 1:
            positions_array = np.array([[p.x, p.y] for p in agent_positions])
            centroid = np.mean(positions_array, axis=0)
            distances = np.linalg.norm(positions_array - centroid, axis=1)
            spatial_aggregation = float(np.mean(distances))

        death_count = 0
        current_tick = getattr(self.world, "tick", 0)
        for agent in agents:
            if not agent.is_alive and agent.death_tick is not None:
                if agent.death_tick > current_tick - 100:
                    death_count += 1

        mortality_rate = death_count / max(1, len(agents))

        total_energy = sum(a.energy for a in alive_agents)
        energy_conservation_holds = 0.95 < total_energy / max(1, len(alive_agents) * 100) < 1.05

        return {
            "food_variance": food_variance,
            "food_mean": food_mean,
            "spatial_aggregation": spatial_aggregation,
            "mortality_rate": mortality_rate,
            "energy_conservation_holds": energy_conservation_holds,
            "agent_count": len(alive_agents),
            "grid_width": grid_width,
            "grid_height": grid_height,
        }

    def _execute_experiment(
        self, exp: Experiment, hypothesis: Hypothesis, world_state: Dict
    ) -> Dict:
        design = exp.design
        predicted = hypothesis.confidence * 0.5 + 0.25

        if design == "test_food_distribution":
            observed = world_state["food_variance"]
            predicted = (
                predicted * world_state["food_mean"] if world_state["food_mean"] > 0 else predicted
            )
            result = "confirm" if abs(observed - predicted) < predicted * 0.5 else "contradict"

        elif design == "test_agent_aggregation":
            observed = world_state["spatial_aggregation"]
            predicted = predicted * 10.0
            result = "confirm" if observed < predicted else "contradict"

        elif design == "test_energy_conservation":
            observed = world_state["energy_conservation_holds"]
            predicted = 1.0
            result = "confirm" if observed else "contradict"

        elif design == "test_mortality_rate":
            observed = world_state["mortality_rate"]
            predicted = (1.0 - predicted) * 0.5
            result = "confirm" if abs(observed - predicted) < 0.2 else "contradict"

        else:
            observed = np.random.random()
            predicted = predicted
            result = "confirm" if observed > 0.4 else "contradict"

        return {
            "result": result,
            "value": observed,
            "predicted": predicted,
        }

    def _check_anomaly(
        self, exp: Experiment, hypothesis: Hypothesis, world_state: Dict
    ) -> Tuple[bool, float]:
        if exp.result is None:
            return False, 0.0

        design = exp.design

        if design == "test_food_distribution":
            observed = world_state["food_variance"]
            predicted = (
                exp.predicted_value
                if exp.predicted_value
                else hypothesis.confidence * world_state["food_mean"]
            )
            if world_state["food_mean"] > 0:
                normalized_diff = abs(observed - predicted) / max(world_state["food_mean"], 0.01)
            else:
                normalized_diff = abs(observed - predicted)
            threshold = 0.5
            discrepancy = normalized_diff

        elif design == "test_agent_aggregation":
            observed = world_state["spatial_aggregation"]
            predicted = exp.predicted_value if exp.predicted_value else hypothesis.confidence * 10.0
            discrepancy = abs(observed - predicted) / max(predicted, 0.01) if predicted > 0 else 0.0
            threshold = 0.5

        elif design == "test_energy_conservation":
            observed = world_state["energy_conservation_holds"]
            discrepancy = 0.0 if observed else 1.0
            threshold = 0.5

        elif design == "test_mortality_rate":
            observed = world_state["mortality_rate"]
            predicted = (
                exp.predicted_value if exp.predicted_value else (1.0 - hypothesis.confidence) * 0.5
            )
            discrepancy = abs(observed - predicted)
            threshold = 0.2

        else:
            discrepancy = 0.0
            threshold = 0.5

        is_anomaly = discrepancy > threshold and exp.result == "contradict"
        return is_anomaly, discrepancy

    def _apply_ad_hoc_modification(
        self,
        hypothesis: Hypothesis,
        exp: Experiment,
        discrepancy: float,
        events: list[WorldEvent],
        ctx: TickContext,
    ):
        hypothesis.ad_hoc_modifications += 1

        new_aux_id = f"aux_{hypothesis.id}_{len(hypothesis.auxiliaries)}"
        new_aux = AuxiliaryHypothesis(
            id=new_aux_id,
            statement=f"Ad-hoc modification {hypothesis.ad_hoc_modifications}: adjusting for {exp.design}",
            modification_count=1,
        )
        hypothesis.auxiliaries.append(new_aux)

        hypothesis.confidence = max(0.1, hypothesis.confidence - 0.15)

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "type": "ad_hoc_accommodation",
                    "hypothesis_id": hypothesis.id,
                    "modification_count": hypothesis.ad_hoc_modifications,
                    "new_confidence": hypothesis.confidence,
                },
                source_id=hypothesis.creator_id,
            )
        )

    def _attempt_replication(
        self, exp: Experiment, replicating_agent_id: AgentID, ctx: TickContext, world_state: Dict
    ) -> bool:
        if replicating_agent_id in exp.replicated_by:
            return False

        hypothesis = self._hypotheses.get(exp.hypothesis_id)
        if hypothesis is None:
            return False

        replication_result = self._execute_experiment(exp, hypothesis, world_state)

        original_result = exp.result
        replication_confirmed = replication_result["result"] == original_result

        if replication_confirmed:
            exp.replicated_by.append(replicating_agent_id)

            if len(exp.replicated_by) >= REPLICATION_THRESHOLD:
                hypothesis.verified = True
                hypothesis.confidence = min(1.0, hypothesis.confidence + 0.1)

            return True
        return False

    def _accumulate_knowledge(self, ctx: TickContext, events: list[WorldEvent]):
        social = getattr(self.world, "social", None)
        if social is None:
            return

        world_state = self._get_world_state_summary()

        for group_id, group in social._groups.items():
            if group_id not in self._group_knowledge:
                self._group_knowledge[group_id] = ScientificKnowledge(group_id=group_id)

            knowledge = self._group_knowledge[group_id]

            group_hypotheses = [
                h for h in self._hypotheses.values() if h.creator_id in group.member_ids
            ]
            knowledge.hypotheses = group_hypotheses[:10]

            verified = [h for h in group_hypotheses if h.verified]
            knowledge.verified_knowledge = list(set(h.hypothesis for h in verified))[:20]

            if hasattr(self.world, "epistemology"):
                epi = self.world.epistemology
                group_theories = []
                for member_id in group.member_ids:
                    if member_id in epi._agent_states:
                        state = epi._agent_states[member_id]
                        group_theories.extend(state.theory_components.keys())

            weighted_confidence_sum = 0.0
            weight_sum = 0.0
            for h in verified:
                replication_count = 0
                for exp in self._experiments.values():
                    if exp.hypothesis_id == h.id:
                        replication_count = len(exp.replicated_by)
                        break

                weight = max(0.1, (h.confidence * replication_count) / (1 + h.ad_hoc_modifications))
                weighted_confidence_sum += h.confidence * weight
                weight_sum += weight

            group_confidence = weighted_confidence_sum / max(weight_sum, 0.1)

            supporting_agents = [h.creator_id for h in verified]
            if (
                group_confidence > 0.8
                and len(verified) > 0
                and any(
                    len(exp.replicated_by) >= REPLICATION_THRESHOLD
                    for exp in self._experiments.values()
                    if exp.hypothesis_id in [h.id for h in verified]
                )
            ):
                consensus_hypothesis = max(verified, key=lambda h: h.confidence)

                if (
                    knowledge.consensus is None
                    or knowledge.consensus.hypothesis_id != consensus_hypothesis.id
                ):
                    knowledge.consensus = ScientificConsensus(
                        hypothesis_id=consensus_hypothesis.id,
                        supporting_agents=supporting_agents,
                        confidence=group_confidence,
                        consensus_tick=ctx.tick,
                    )
                    self._consensuses[consensus_hypothesis.id] = knowledge.consensus

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "scientific_consensus",
                                "group_id": group_id,
                                "hypothesis_id": consensus_hypothesis.id,
                                "confidence": group_confidence,
                                "supporting_agents": supporting_agents,
                            },
                            source_id=None,
                        )
                    )

    def _generate_innovations(self, ctx: TickContext, events: list[WorldEvent]):
        world_state = self._get_world_state_summary()

        for group_id, knowledge in self._group_knowledge.items():
            if len(knowledge.verified_knowledge) < 2:
                continue

            verified_hypotheses = [h for h in knowledge.hypotheses if h.verified]
            if not verified_hypotheses:
                continue

            innovation_type = self._determine_innovation_from_knowledge(
                verified_hypotheses, world_state
            )

            if innovation_type is None:
                continue

            if np.random.random() < 0.01:
                knowledge.innovation_count += 1

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "innovation",
                            "group_id": group_id,
                            "innovation_type": innovation_type,
                            "knowledge_bases": len(knowledge.verified_knowledge),
                            "triggered_by_knowledge": True,
                        },
                    )
                )

    def _determine_innovation_from_knowledge(
        self, verified_hypotheses: List[Hypothesis], world_state: Dict
    ) -> Optional[str]:
        hypothesis_texts = []
        for h in verified_hypotheses:
            hypothesis_texts.extend(h.supporting_evidence)
            hypothesis_texts.append(h.testable_prediction)

        hypothesis_str = " ".join(hypothesis_texts).lower()

        food_related = any(
            kw in hypothesis_str
            for kw in ["resource", "food", "distribution", "efficiency", "energy", "survival"]
        )
        social_related = any(
            kw in hypothesis_str
            for kw in ["agent", "behavior", "aggregation", "social", "reproduction"]
        )

        if food_related and world_state["food_variance"] > 0.3:
            return "resource_optimization"
        elif social_related and world_state["spatial_aggregation"] > 5.0:
            return "social_structure_formation"
        elif food_related:
            return "resource_optimization"
        elif social_related:
            return "social_structure"
        else:
            return None

    def get_science_stats(self) -> Dict:
        total_hypotheses = len(self._hypotheses)
        verified = sum(1 for h in self._hypotheses.values() if h.verified)
        falsified = sum(1 for h in self._hypotheses.values() if h.falsified)
        total_experiments = len(self._experiments)
        total_innovations = sum(k.innovation_count for k in self._group_knowledge.values())
        consensus_count = len(self._consensuses)

        replicated_experiments = sum(
            1 for e in self._experiments.values() if len(e.replicated_by) >= REPLICATION_THRESHOLD
        )

        total_anomalies = sum(h.anomaly_count for h in self._hypotheses.values())
        total_ad_hoc = sum(h.ad_hoc_modifications for h in self._hypotheses.values())

        return {
            "total_hypotheses": total_hypotheses,
            "verified_hypotheses": verified,
            "falsified_hypotheses": falsified,
            "total_experiments": total_experiments,
            "replicated_experiments": replicated_experiments,
            "total_innovations": total_innovations,
            "groups_with_knowledge": len(self._group_knowledge),
            "consensuses_reached": consensus_count,
            "total_anomalies": total_anomalies,
            "total_ad_hoc_modifications": total_ad_hoc,
        }
