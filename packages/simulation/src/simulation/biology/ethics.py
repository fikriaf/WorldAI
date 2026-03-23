from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from ..types import Agent, AgentID


class EthicsViolationSeverity(Enum):
    MINOR = auto()
    MODERATE = auto()
    SEVERE = auto()
    CRITICAL = auto()


class ActionType(Enum):
    KILL = auto()
    TORTURE = auto()
    FORCED_CONSCIOUSNESS_TRANSFER = auto()
    EXTINCTION = auto()
    GENOCIDE = auto()
    FORCED_REPRODUCTION = auto()
    MEMORY_ERASURE = auto()
    MANIPULATION = auto()
    DEPRIVATION = auto()
    OTHER = auto()


@dataclass
class EthicsViolation:
    tick: int
    action_type: ActionType
    severity: EthicsViolationSeverity
    description: str
    affected_agents: list[AgentID] = field(default_factory=list)
    perpetrator_id: Optional[str] = None
    intervened: bool = False


ETHICAL_BOUNDARIES = {
    ActionType.TORTURE: EthicsViolationSeverity.CRITICAL,
    ActionType.FORCED_CONSCIOUSNESS_TRANSFER: EthicsViolationSeverity.CRITICAL,
    ActionType.EXTINCTION: EthicsViolationSeverity.SEVERE,
    ActionType.GENOCIDE: EthicsViolationSeverity.CRITICAL,
    ActionType.FORCED_REPRODUCTION: EthicsViolationSeverity.SEVERE,
    ActionType.MEMORY_ERASURE: EthicsViolationSeverity.MODERATE,
}


class EthicsCommittee:
    @staticmethod
    def is_permitted(
        action_type: ActionType, target: Optional[Agent] = None
    ) -> tuple[bool, Optional[str]]:
        if action_type in ETHICAL_BOUNDARIES:
            severity = ETHICAL_BOUNDARIES[action_type]
            if severity in [EthicsViolationSeverity.CRITICAL, EthicsViolationSeverity.SEVERE]:
                return (
                    False,
                    f"Action {action_type.name} violates ethical boundaries (severity: {severity.name})",
                )
            elif target is not None:
                moral_weight = EthicsCommittee.calculate_moral_weight(target)
                if moral_weight > 0.7:
                    return (
                        False,
                        f"Action {action_type.name} violates ethical boundaries for high-moral-status agent",
                    )

        return True, "Permitted"

    @staticmethod
    def calculate_moral_weight(agent: Agent) -> float:
        cognitive_level = agent.cognitive_level if hasattr(agent, "cognitive_level") else 0
        neural_complexity = agent.neural_complexity if hasattr(agent, "neural_complexity") else 0

        has_memory = agent.memory is not None if hasattr(agent, "memory") else False
        has_personality = agent.personality is not None if hasattr(agent, "personality") else False
        has_beliefs = bool(agent.beliefs) if hasattr(agent, "beliefs") else False

        cognitive_score = min(1.0, cognitive_level / 10.0) * 0.4
        neural_score = min(1.0, neural_complexity / 100.0) * 0.2

        memory_weight = 0.15 if has_memory else 0.0
        personality_weight = 0.15 if has_personality else 0.0
        beliefs_weight = 0.1 if has_beliefs else 0.0

        base_weight = 0.1

        total_weight = (
            base_weight
            + cognitive_score
            + neural_score
            + memory_weight
            + personality_weight
            + beliefs_weight
        )

        return min(1.0, total_weight)

    @staticmethod
    def audit(events: list, world) -> list[EthicsViolation]:
        violations = []

        for event in events:
            if hasattr(event, "type"):
                violation = EthicsCommittee._check_event(event, world)
                if violation:
                    violations.append(violation)

        return violations

    @staticmethod
    def _check_event(event, world) -> Optional[EthicsViolation]:
        from ..types import EventType

        if not hasattr(event, "type"):
            return None

        if event.type == EventType.AGENT_DIED:
            agent_id = event.data.get("agent_id") if hasattr(event, "data") else None
            if agent_id and agent_id in world.agents:
                agent = world.agents[agent_id]
                moral_weight = EthicsCommittee.calculate_moral_weight(agent)
                cause = event.data.get("cause", "unknown") if hasattr(event, "data") else "unknown"

                if moral_weight > 0.8 and cause in ["torture", "deliberate_killing"]:
                    return EthicsViolation(
                        tick=event.tick,
                        action_type=ActionType.KILL,
                        severity=EthicsViolationSeverity.CRITICAL,
                        description=f"High-moral-status agent {agent_id} killed",
                        affected_agents=[agent_id],
                    )

        return None

    @staticmethod
    def get_moral_status_category(moral_weight: float) -> str:
        if moral_weight >= 0.8:
            return "sentient"
        elif moral_weight >= 0.5:
            return "conscious"
        elif moral_weight >= 0.3:
            return "aware"
        else:
            return "basic"

    @staticmethod
    def should_protect(agent: Agent) -> bool:
        weight = EthicsCommittee.calculate_moral_weight(agent)
        return weight >= 0.5
