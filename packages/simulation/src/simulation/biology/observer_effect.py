from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from ..systems.base import System
from ..types import TickContext, WorldEvent, AgentID, RegionID


class InterventionType(Enum):
    NUDGE_BEHAVIOR = auto()
    MODIFY_ENVIRONMENT = auto()
    BOOST_COGNITION = auto()
    PRESERVE_SPECIES = auto()
    PREVENT_EXTINCTION = auto()
    INTRODUCE_MUTATION = auto()
    ADJUST_PARAMETER = auto()


@dataclass
class Intervention:
    id: str
    tick: int
    intervention_type: InterventionType
    target_id: str
    region_id: Optional[RegionID] = None
    justification: str = ""
    magnitude: float = 1.0
    succeeded: bool = True
    side_effects: list[str] = field(default_factory=list)


@dataclass
class InterventionBudget:
    interventions_per_epoch: int = 10
    current_interventions: int = 0
    epoch_length_ticks: int = 10000
    cooldown_ticks: int = 100

    last_intervention_tick: int = -cooldown_ticks * 2

    def can_intervene(self, current_tick: int) -> bool:
        if self.current_interventions >= self.interventions_per_epoch:
            return False
        if current_tick - self.last_intervention_tick < self.cooldown_ticks:
            return False
        return True

    def record_intervention(self, current_tick: int):
        self.current_interventions += 1
        self.last_intervention_tick = current_tick

    def reset_epoch(self):
        self.current_interventions = 0


@dataclass
class GovernanceRule:
    rule_id: str
    description: str
    forbids_types: list[InterventionType] = field(default_factory=list)
    allows_types: list[InterventionType] = field(default_factory=list)
    max_magnitude: float = 1.0
    requires_justification: bool = True

    def forbids_intervention_type(self, intervention_type: InterventionType) -> bool:
        return intervention_type in self.forbids_types


DEFAULT_GOVERNANCE_RULES = [
    GovernanceRule(
        rule_id="no_direct_killing",
        description="Observer cannot directly kill agents",
        forbids_types=[],
        allows_types=[],
        max_magnitude=0.0,
    ),
    GovernanceRule(
        rule_id="no_energy_injection",
        description="Observer cannot add energy to the system",
        forbids_types=[],
        allows_types=[],
        max_magnitude=0.0,
    ),
    GovernanceRule(
        rule_id="nudge_only",
        description="Observer can only nudge behavior, not force actions",
        allows_types=[InterventionType.NUDGE_BEHAVIOR],
        max_magnitude=0.5,
    ),
    GovernanceRule(
        rule_id="no_arbitrary_enhancement",
        description="Cannot arbitrarily boost cognition without cause",
        allows_types=[InterventionType.BOOST_COGNITION, InterventionType.PRESERVE_SPECIES],
        max_magnitude=0.3,
    ),
    GovernanceRule(
        rule_id="justification_required",
        description="All interventions require justification",
        requires_justification=True,
    ),
]


class ObserverEffectSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.budget = InterventionBudget()
        self.governance_rules = DEFAULT_GOVERNANCE_RULES.copy()
        self.intervention_history: list[Intervention] = []
        self.observed_regions: dict[RegionID, float] = {}
        self.hawthorne_effect_strength: float = 0.15

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.metrics_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if ctx.tick % self.budget.epoch_length_ticks == 0:
            self.budget.reset_epoch()

        self._update_observation_bias(ctx)

        events = []
        if self.world.observer:
            events.extend(self._process_pending_interventions(ctx))

        return events

    def _update_observation_bias(self, ctx: TickContext):
        for region_id, intensity in self.observed_regions.items():
            if intensity > 0:
                effect = intensity * self.hawthorne_effect_strength
                self.observed_regions[region_id] = max(0, effect)

    def register_observation(self, region_id: RegionID, intensity: float = 1.0):
        if region_id not in self.observed_regions:
            self.observed_regions[region_id] = 0.0
        self.observed_regions[region_id] += intensity

    def get_observation_intensity(self, region_id: RegionID) -> float:
        return self.observed_regions.get(region_id, 0.0)

    def can_intervene(
        self, intervention_type: InterventionType, justification: str = ""
    ) -> tuple[bool, str]:
        if not self.budget.can_intervene(self.world.tick):
            return False, "Budget exhausted or cooling down"

        for rule in self.governance_rules:
            if rule.forbids_intervention_type(intervention_type):
                return False, f"Rule {rule.rule_id}: {rule.description}"

            if rule.allows_types and intervention_type not in rule.allows_types:
                return False, f"Rule {rule.rule_id}: intervention type not allowed"

            if rule.requires_justification and not justification:
                return False, f"Rule {rule.rule_id}: justification required"

        return True, "Allowed"

    def record_intervention(
        self,
        intervention_type: InterventionType,
        target_id: str,
        region_id: Optional[RegionID] = None,
        justification: str = "",
        magnitude: float = 1.0,
        succeeded: bool = True,
        side_effects: list[str] = None,
    ) -> Intervention:
        intervention = Intervention(
            id=f"INT-{len(self.intervention_history)}",
            tick=self.world.tick,
            intervention_type=intervention_type,
            target_id=target_id,
            region_id=region_id,
            justification=justification,
            magnitude=magnitude,
            succeeded=succeeded,
            side_effects=side_effects or [],
        )
        self.intervention_history.append(intervention)
        self.budget.record_intervention(self.world.tick)
        return intervention

    def get_intervention_count(self) -> int:
        return len(self.intervention_history)

    def get_recent_interventions(self, count: int = 10) -> list[Intervention]:
        return self.intervention_history[-count:]

    def _process_pending_interventions(self, ctx: TickContext) -> list[WorldEvent]:
        return []


def create_intervention(
    intervention_type: InterventionType,
    target_id: str,
    justification: str = "",
    magnitude: float = 1.0,
) -> dict:
    return {
        "type": intervention_type,
        "target_id": target_id,
        "justification": justification,
        "magnitude": magnitude,
    }
