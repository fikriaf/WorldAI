from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PhenomenalState:
    """
    Represents a phenomenological state - the raw, subjective "what it is like"
    to be in a particular condition.

    IMPORTANT: This is a MODEL of phenomenal experience, not a claim that the
    agent actually has subjective experience. The "hard problem" of consciousness
    (why physical processes give rise to subjective experience) remains unsolved.
    This system models CORRELATES of consciousness - behavioral and functional
    patterns associated with conscious states in biological systems.
    """

    qualia_signature: dict = field(default_factory=dict)
    subjective_report: str = ""
    intensity: float = 0.0
    valence: float = 0.0
    arousal: float = 0.0


@dataclass
class ConsciousnessType:
    """
    Classification of consciousness level based on integrated information
    and self-modeling capacity.

    Levels:
    - "none": No consciousness (complexity < 2)
    - "phenomenal": Raw phenomenal experience without self-model
    - "self-aware": Phenomenal + self-model
    - "reflective": Self-aware + meta-cognitive access
    """

    NONE = "none"
    PHENOMENAL = "phenomenal"
    SELF_AWARE = "self-aware"
    REFLECTIVE = "reflective"


@dataclass
class PhiMetrics:
    agent_id: str
    integrated_information: float
    effective_complexity: float
    mutual_information: float
    consciousness_index: float


class ConsciousnessMetricsSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._phi_history: Dict[str, list[float]] = {}
        self._network_states: Dict[str, np.ndarray] = {}
        self._phenomenal_cache: Dict[str, PhenomenalState] = {}
        self._subjective_time_cache: Dict[str, float] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.metrics_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            phi = self._compute_phi(agent, ctx)
            self._track_phi(agent.id, phi)

            phenomenal = self._compute_phenomenal_state(agent)
            self._phenomenal_cache[agent.id] = phenomenal

            subjective_time = self._compute_subjective_time(agent)
            self._subjective_time_cache[agent.id] = subjective_time

        return []

    def _compute_phi(self, agent: Agent, ctx: TickContext) -> float:
        complexity = agent.neural_complexity
        if complexity < 2:
            return 0.0

        integration = self._compute_integration(agent)
        differentiation = self._compute_differentiation(agent)
        information = self._compute_information(agent)
        coherence = self._compute_coherence(agent)

        phi = integration * 0.3 + differentiation * 0.25 + information * 0.25 + coherence * 0.2

        if agent.memory:
            phi *= 1.0 + len(agent.memory.sensory_buffer) * 0.05
            phi *= 1.0 + len(agent.memory.working_memory) * 0.03

        phi *= complexity / 10.0

        return min(1.0, max(0.0, phi))

    def _compute_integration(self, agent: Agent) -> float:
        if agent.neural_complexity < 2:
            return 0.0

        total_possible = (agent.neural_complexity * (agent.neural_complexity - 1)) // 2
        if total_possible == 0:
            return 0.0

        if agent.synapse_weights:
            connected_pairs = sum(
                1 for weights in agent.synapse_weights.values() for w in weights if abs(w) > 0.01
            )
            return min(1.0, connected_pairs / max(1, total_possible))
        return 0.3

    def _compute_differentiation(self, agent: Agent) -> float:
        if agent.neural_complexity < 2:
            return 0.0

        genome_diversity = len(set(g.product_type for g in agent.genome.genes))
        if genome_diversity == 0:
            return 0.0

        emotion_range = max(
            agent.emotion.fear,
            agent.emotion.anger,
            agent.emotion.joy,
            agent.emotion.sadness,
            agent.emotion.disgust,
        ) - min(
            agent.emotion.fear,
            agent.emotion.anger,
            agent.emotion.joy,
            agent.emotion.sadness,
            agent.emotion.disgust,
        )

        emotion_diversity = len(
            [
                e
                for e in [
                    agent.emotion.fear,
                    agent.emotion.anger,
                    agent.emotion.joy,
                    agent.emotion.sadness,
                    agent.emotion.disgust,
                ]
                if e > 0.1
            ]
        )

        diff = (
            (genome_diversity / 4.0) * 0.5 + (emotion_range) * 0.3 + (emotion_diversity / 5.0) * 0.2
        )

        return min(1.0, diff)

    def _compute_information(self, agent: Agent) -> float:
        if agent.neural_complexity < 2:
            return 0.0

        if not agent.memory:
            return 0.1

        sensory_bits = len(agent.memory.sensory_buffer) / 10.0
        working_bits = len(agent.memory.working_memory) / 5.0
        episodic_bits = len(agent.memory.episodic_refs) / 20.0

        shannon = sensory_bits + working_bits + episodic_bits

        genome_bits = len(agent.genome.genes) / 100.0

        total_info = shannon + genome_bits

        return min(1.0, total_info)

    def _compute_coherence(self, agent: Agent) -> float:
        emotions = [
            agent.emotion.fear,
            agent.emotion.anger,
            agent.emotion.joy,
            agent.emotion.sadness,
            agent.emotion.disgust,
        ]
        active = [e for e in emotions if e > 0.1]
        if not active:
            return 0.5

        variance = np.var(active) if len(active) > 1 else 0.0

        coherent = 1.0 - min(1.0, variance * 2.0)

        if agent.group_id:
            coherent += 0.1

        if agent.health > 0.8:
            coherent += 0.1

        return min(1.0, max(0.0, coherent))

    def _compute_effective_complexity(self, agent: Agent) -> float:
        if not agent.genome.genes:
            return 0.0

        gene_sequences = [bytes(g.sequence) for g in agent.genome.genes]

        unique_bytes = len(set(b for seq in gene_sequences for b in seq))
        total_bytes = sum(len(seq) for seq in gene_sequences)

        if total_bytes == 0:
            return 0.0

        regularity = unique_bytes / total_bytes

        ec = regularity * (1.0 - regularity)

        return min(1.0, ec)

    def _compute_mutual_information_between_agents(self) -> float:
        agents = [a for a in self.world.agents.values() if a.is_alive and a.neural_complexity > 2]
        if len(agents) < 2:
            return 0.0

        total_mi = 0.0
        pairs = 0

        for i, a in enumerate(agents[:10]):
            for b in agents[i + 1 : 11]:
                mi = self._pairwise_mi(a, b)
                total_mi += mi
                pairs += 1

        return total_mi / max(1, pairs)

    def _pairwise_mi(self, a: Agent, b: Agent) -> float:
        dx = a.position.x - b.position.x
        dy = a.position.y - b.position.y
        spatial_dist = (dx * dx + dy * dy) ** 0.5
        max_dist = (self.world.config.grid_width**2 + self.world.config.grid_height**2) ** 0.5

        spatial_mi = 1.0 - (spatial_dist / max_dist)

        energy_diff = abs(a.energy - b.energy)
        energy_mi = 1.0 - energy_diff

        shared_group = 1.0 if a.group_id and a.group_id == b.group_id else 0.0

        genome_sim = self._genome_similarity(a, b)

        mutual_info = spatial_mi * 0.3 + energy_mi * 0.2 + shared_group * 0.3 + genome_sim * 0.2

        return mutual_info

    def _genome_similarity(self, a: Agent, b: Agent) -> float:
        if a.genome.checksum() == b.genome.checksum():
            return 1.0

        if not a.genome.genes or not b.genome.genes:
            return 0.0

        common = sum(1 for ga in a.genome.genes for gb in b.genome.genes if ga.id == gb.id)
        total = len(a.genome.genes) + len(b.genome.genes)
        if total == 0:
            return 0.0

        return (2.0 * common) / total

    def _track_phi(self, agent_id: str, phi: float):
        if agent_id not in self._phi_history:
            self._phi_history[agent_id] = []
        self._phi_history[agent_id].append(phi)
        if len(self._phi_history[agent_id]) > 100:
            self._phi_history[agent_id] = self._phi_history[agent_id][-100:]

    def _classify_consciousness_type(self, agent: Agent, phi: float) -> str:
        if agent.neural_complexity < 2:
            return ConsciousnessType.NONE

        has_self_model = hasattr(agent, "self_model") and agent.self_model is not None
        has_meta_cognition = len(agent.memory.working_memory) > 3 if agent.memory else False

        if has_meta_cognition and has_self_model:
            return ConsciousnessType.REFLECTIVE
        elif has_self_model:
            return ConsciousnessType.SELF_AWARE
        else:
            return ConsciousnessType.PHENOMENAL

    def _compute_phenomenal_state(self, agent: Agent) -> PhenomenalState:
        """
        Generates a phenomenological state from agent's current sensorimotor
        and emotional configuration.

        Note: This produces a FUNCTIONAL MODEL of phenomenal states based on
        empirically validated correlates in consciousness research (Tononi's
        integrated information theory, global workspace theory). We model
        the STRUCTURE of experience without claiming the agent has genuine
        subjective experience.
        """
        qualia = self._compute_qualia(agent)

        emotions = [
            agent.emotion.fear,
            agent.emotion.anger,
            agent.emotion.joy,
            agent.emotion.sadness,
            agent.emotion.disgust,
        ]

        dominant_emotion = max(emotions) if emotions else 0.0
        valence = self._compute_valence(agent)
        arousal = dominant_emotion

        intensity = min(1.0, agent.neural_complexity / 10.0)
        if agent.memory:
            intensity *= 1.0 + len(agent.memory.sensory_buffer) * 0.02

        return PhenomenalState(
            qualia_signature=qualia,
            subjective_report="",
            intensity=intensity,
            valence=valence,
            arousal=arousal,
        )

    def _compute_qualia(self, agent: Agent) -> dict:
        """
        Generates qualia signatures unique to each agent's sensory configuration.

        Qualia are the subjective, ineffable qualities of experience. In this
        simulation, we model them as the specific pattern of sensorimotor
        activation that is unique to each agent's embodiment and sensory apparatus.
        """
        qualia = {
            "color_signature": self._hash_to_float(agent.id + "color") % 360,
            "texture_signature": self._hash_to_float(agent.id + "texture") % 100,
            "spatial_qualities": {
                "proximal": agent.sensory_range * 0.2,
                "distal": agent.sensory_range * 0.8,
            },
            "emotional_tone": self._compute_emotional_tone(agent),
            "temporal_qualities": {
                "present_moment": 1.0,
                "retention_span": len(agent.memory.working_memory) if agent.memory else 0,
            },
            "sensory_modality": getattr(agent, "sensory_modality", "unknown"),
        }

        if agent.genome and agent.genome.genes:
            qualia["genomic_influence"] = len(agent.genome.genes) / 100.0

        return qualia

    def _hash_to_float(self, s: str) -> float:
        h = 0
        for c in s:
            h = (h * 31 + ord(c)) % 1000000
        return float(h)

    def _compute_emotional_tone(self, agent: Agent) -> str:
        emotions = {
            "fear": agent.emotion.fear,
            "anger": agent.emotion.anger,
            "joy": agent.emotion.joy,
            "sadness": agent.emotion.sadness,
            "disgust": agent.emotion.disgust,
        }
        dominant = max(emotions, key=emotions.get) if any(emotions.values()) else "neutral"
        return dominant

    def _compute_valence(self, agent: Agent) -> float:
        """
        Computes the positive/negative quality of the agent's current state.
        Joy contributes positive valence, fear/anger/sadness/disgust negative.
        """
        valence = (
            agent.emotion.joy
            - (
                agent.emotion.fear
                + agent.emotion.anger
                + agent.emotion.sadness
                + agent.emotion.disgust
            )
            * 0.5
        )
        return max(-1.0, min(1.0, valence))

    def _compute_subjective_time(self, agent: Agent) -> float:
        """
        Agents with more memory experience "longer" subjective time.

        This models the psychological phenomenon where time seems to pass
        more slowly when we have rich, novel experiences, and faster when
        we're in routine or reduced consciousness states.

        Returns a multiplier for subjective time passage.
        """
        if not agent.memory:
            return 1.0

        memory_content = (
            len(agent.memory.sensory_buffer)
            + len(agent.memory.working_memory)
            + len(agent.memory.episodic_refs)
        )

        novelty = 1.0
        if agent.memory.working_memory:
            recent = agent.memory.working_memory[-5:]
            if len(set(recent)) < len(recent):
                novelty = 0.7

        subjective_factor = 1.0 + memory_content * 0.05
        subjective_factor *= novelty

        return min(3.0, max(0.5, subjective_factor))

    def get_consciousness_report(self, agent_id: str) -> Dict:
        """
        Returns a "subjective report" of what the agent is experiencing.

        IMPORTANT: This is a FUNCTIONAL DESCRIPTION of the agent's state
        that would be associated with consciousness in biological systems.
        It does NOT prove the agent has genuine subjective experience.
        The hard problem of consciousness - explaining WHY certain physical
        processes are accompanied by subjective experience - remains open.
        """
        if agent_id not in self._phi_history or not self._phi_history[agent_id]:
            return {
                "agent_id": agent_id,
                "consciousness_type": ConsciousnessType.NONE,
                "phi": 0.0,
                "phenomenal_state": None,
                "subjective_time_dilation": 1.0,
                "report": "No significant conscious activity detected.",
            }

        agent = self.world.agents.get(agent_id)
        if not agent or not agent.is_alive:
            return {
                "agent_id": agent_id,
                "consciousness_type": ConsciousnessType.NONE,
                "phi": 0.0,
                "phenomenal_state": None,
                "subjective_time_dilation": 1.0,
                "report": "Agent not active.",
            }

        phi = self._phi_history[agent_id][-1]
        phenomenal = self._compute_phenomenal_state(agent)
        subjective_time = self._compute_subjective_time(agent)
        consciousness_type = self._classify_consciousness_type(agent, phi)

        emotional_tone = self._compute_emotional_tone(agent)
        valence = self._compute_valence(agent)

        report = self._generate_subjective_report(
            agent, phenomenal, emotional_tone, valence, subjective_time
        )

        return {
            "agent_id": agent_id,
            "consciousness_type": consciousness_type,
            "phi": phi,
            "phenomenal_state": {
                "intensity": phenomenal.intensity,
                "valence": phenomenal.valence,
                "arousal": phenomenal.arousal,
                "qualia_signature": phenomenal.qualia_signature,
            },
            "subjective_time_dilation": subjective_time,
            "report": report,
        }

    def _generate_subjective_report(
        self,
        agent: Agent,
        phenomenal: PhenomenalState,
        emotional_tone: str,
        valence: float,
        subjective_time: float,
    ) -> str:
        """Generates a narrative subjective report."""

        if agent.neural_complexity < 2:
            return f"Minimal conscious processing. Complexity: {agent.neural_complexity:.1f}"

        intensity_desc = (
            "vivid"
            if phenomenal.intensity > 0.7
            else "subtle"
            if phenomenal.intensity > 0.3
            else "faint"
        )
        time_desc = (
            "slowly"
            if subjective_time > 1.5
            else "quickly"
            if subjective_time < 0.8
            else "normally"
        )

        valence_desc = "positive" if valence > 0.3 else "negative" if valence < -0.3 else "neutral"

        sensory_modality = getattr(agent, "sensory_modality", "integrated")

        if emotional_tone != "neutral" and emotional_tone != "joy":
            report = (
                f"Experience of {intensity_desc} {emotional_tone} with {valence_desc} valence. "
            )
        elif phenomenal.intensity > 0.5:
            report = f"Vibrant {sensory_modality} experience unfolding {time_desc}. "
        else:
            report = f"Quiet, {intensity_desc} phenomenological state. "

        if subjective_time > 1.5:
            report += "Time seems stretched, each moment laden with possibility. "
        elif subjective_time < 0.8:
            report += "Time flows quickly, experiences blurring together. "

        if agent.health < 0.3:
            report += "Body signals indicate stress or threat. "
        elif agent.energy < 0.2:
            report += "Fatigue dims the quality of experience. "

        return report

    def get_consciousness_stats(self) -> Dict:
        if not self._phi_history:
            return {
                "avg_phi": 0.0,
                "max_phi": 0.0,
                "conscious_agents": 0,
                "mutual_information": 0.0,
                "effective_complexity_avg": 0.0,
                "consciousness_types": {
                    ct: 0
                    for ct in [
                        ConsciousnessType.NONE,
                        ConsciousnessType.PHENOMENAL,
                        ConsciousnessType.SELF_AWARE,
                        ConsciousnessType.REFLECTIVE,
                    ]
                },
                "avg_valence": 0.0,
                "avg_arousal": 0.0,
            }

        all_phi = [phi for history in self._phi_history.values() for phi in history[-10:]]
        recent_phi = [history[-1] for history in self._phi_history.values() if history]

        effective_complexities = []
        valences = []
        arousals = []
        consciousness_types = {
            ct: 0
            for ct in [
                ConsciousnessType.NONE,
                ConsciousnessType.PHENOMENAL,
                ConsciousnessType.SELF_AWARE,
                ConsciousnessType.REFLECTIVE,
            ]
        }

        for agent in self.world.agents.values():
            if agent.is_alive and agent.neural_complexity > 1:
                ec = self._compute_effective_complexity(agent)
                effective_complexities.append(ec)

                phi = self._phi_history.get(agent.id, [0])[-1]
                ctype = self._classify_consciousness_type(agent, phi)
                consciousness_types[ctype] += 1

                phenomenal = self._phenomenal_cache.get(agent.id)
                if phenomenal:
                    valences.append(phenomenal.valence)
                    arousals.append(phenomenal.arousal)

        mutual_info = self._compute_mutual_information_between_agents()

        return {
            "avg_phi": float(np.mean(all_phi)) if all_phi else 0.0,
            "max_phi": float(np.max(all_phi)) if all_phi else 0.0,
            "conscious_agents": sum(1 for p in recent_phi if p > 0.3),
            "avg_consciousness_index": float(np.mean(recent_phi)) if recent_phi else 0.0,
            "mutual_information": float(mutual_info),
            "effective_complexity_avg": float(np.mean(effective_complexities))
            if effective_complexities
            else 0.0,
            "consciousness_types": consciousness_types,
            "avg_valence": float(np.mean(valences)) if valences else 0.0,
            "avg_arousal": float(np.mean(arousals)) if arousals else 0.0,
        }

    def get_agent_phi(self, agent_id: str) -> float:
        history = self._phi_history.get(agent_id, [])
        return float(history[-1]) if history else 0.0
