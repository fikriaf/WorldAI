from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import numpy as np


AgentID = str
SpeciesID = str
GroupID = str
MoleculeID = str
RegionID = str


class ElementType(Enum):
    PRIMUM = "P"
    AQUA = "A"
    TERRA = "T"
    IGNIS = "I"
    AETHER = "Ae"
    LAPIS = "L"


class BondType(Enum):
    COVALENT = "covalent"
    WEAK = "weak"
    IONIC = "ionic"


class AgentStage(Enum):
    NEONATAL = "neonatal"
    JUVENILE = "juvenile"
    ADOLESCENT = "adolescent"
    ADULT = "adult"
    ELDER = "elder"


class EventType(Enum):
    AGENT_BORN = "agent_born"
    AGENT_DIED = "agent_died"
    AGENT_REPRODUCED = "agent_reproduced"
    AGENT_STAGE_CHANGE = "agent_stage_change"
    CHEMICAL_REACTION = "chemical_reaction"
    ABIOGENESIS = "abiogenesis"
    SPECIATION = "speciation"
    COLLISION = "collision"
    ENERGY_TRANSFER = "energy_transfer"
    MUTATION = "mutation"
    CA_PATTERN = "ca_pattern"
    TICK_COMPLETE = "tick_complete"
    GOD_MODE_INTERVENTION = "god_mode_intervention"


@dataclass
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

    def normalized(self) -> Vec2:
        m = self.magnitude()
        return Vec2(self.x / m, self.y / m) if m > 0 else Vec2(0, 0)

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y])


@dataclass
class TickContext:
    tick: int
    dt: float
    physics_tick: bool
    chemistry_tick: bool
    biology_tick: bool
    cognitive_tick: bool
    social_tick: bool
    geological_tick: bool
    ca_tick: bool
    rd_tick: bool
    metrics_tick: bool


@dataclass
class Element:
    type: ElementType
    mass: float
    reactivity: float
    position: Vec2
    velocity: Vec2
    charge: float = 0.0
    bonded_to: list[MoleculeID] = field(default_factory=list)


@dataclass
class Molecule:
    id: MoleculeID
    elements: list[ElementType]
    bond_types: list[BondType]
    free_energy: float
    is_catalyst: bool = False
    can_replicate: bool = False
    can_form_membrane: bool = False


@dataclass
class Gene:
    id: str
    sequence: bytes
    expression_level: float
    promoter_condition: str
    product_type: str
    is_active: bool = True


@dataclass
class Genome:
    genes: list[Gene]
    mutation_rate: float = 0.001
    max_length: int = 1000
    epigenetic_marks: dict[str, float] = field(default_factory=dict)

    def checksum(self) -> str:
        import hashlib

        data = b"".join(g.sequence for g in self.genes)
        return hashlib.sha256(data).hexdigest()[:16]

    def mutate(self) -> Genome:
        import copy, random
        from .biology.genome import SENSORY_GENE_TYPES

        new_genome = copy.deepcopy(self)
        for gene in new_genome.genes:
            if random.random() < self.mutation_rate:
                if gene.sequence:
                    pos = random.randint(0, len(gene.sequence) * 8 - 1)
                    byte_pos, bit_pos = divmod(pos, 8)
                    ba = bytearray(gene.sequence)
                    ba[byte_pos] ^= 1 << bit_pos
                    gene.sequence = bytes(ba)
                gene.expression_level = max(
                    0.0, min(1.0, gene.expression_level + random.uniform(-0.1, 0.1))
                )
                if random.random() < 0.05:
                    gene.product_type = random.choice(
                        SENSORY_GENE_TYPES + ["structural", "regulatory", "catalytic", "neural"]
                    )
                gene.is_active = random.random() > 0.05 or gene.is_active
        if random.random() < self.mutation_rate * 0.1 and len(new_genome.genes) < self.max_length:
            new_gene = Gene(
                id=f"g_{random.randint(0, 999999):06d}",
                sequence=bytes([random.randint(0, 255) for _ in range(4)]),
                expression_level=random.random(),
                promoter_condition="default",
                product_type=random.choice(
                    SENSORY_GENE_TYPES + ["structural", "regulatory", "catalytic", "neural"]
                ),
            )
            new_genome.genes.append(new_gene)
        return new_genome

    def apply_epigenetic_modification(self, gene_id: str, expression_delta: float):
        if gene_id in self.epigenetic_marks:
            self.epigenetic_marks[gene_id] += expression_delta
            self.epigenetic_marks[gene_id] = max(-1.0, min(1.0, self.epigenetic_marks[gene_id]))
        else:
            self.epigenetic_marks[gene_id] = expression_delta

    def get_effective_expression(self, gene_id: str, base_level: float) -> float:
        if gene_id in self.epigenetic_marks:
            return base_level * (1.0 + self.epigenetic_marks[gene_id])
        return base_level

    def inherit_epigenetic_marks(self, parent_epigenetics: dict[str, float]) -> dict[str, float]:
        import random

        inherited = {}
        for gene_id, mark in parent_epigenetics.items():
            inherited[gene_id] = mark * (0.5 + random.random() * 0.5)
        return inherited

    def crossover(self, other: Genome) -> tuple[Genome, Genome]:
        import copy, random

        if not self.genes or not other.genes:
            return copy.deepcopy(self), copy.deepcopy(other)
        min_len = min(len(self.genes), len(other.genes))
        if min_len < 2:
            return copy.deepcopy(self), copy.deepcopy(other)
        p1, p2 = sorted(random.sample(range(min_len), 2))
        genes_a = self.genes[:p1] + other.genes[p1:p2] + self.genes[p2:]
        genes_b = other.genes[:p1] + self.genes[p1:p2] + other.genes[p2:]
        child_a = Genome(genes=copy.deepcopy(genes_a), mutation_rate=self.mutation_rate)
        child_b = Genome(genes=copy.deepcopy(genes_b), mutation_rate=other.mutation_rate)
        return child_a, child_b


@dataclass
class Cell:
    id: str
    genome: Genome
    position: Vec2
    velocity: Vec2
    mass: float
    radius: float
    energy: float
    health: float
    age_ticks: int = 0
    atp_level: float = 0.5
    membrane_integrity: float = 1.0
    internal_ph: float = 7.0
    immune_memory: list[str] = field(default_factory=list)
    is_alive: bool = True
    can_reproduce: bool = False


@dataclass
class LifecycleThresholds:
    juvenile_at: int = 50
    adolescent_at: int = 200
    adult_at: int = 500
    elder_at: int = 2000
    max_lifespan: int = 5000


@dataclass
class SensoryCapabilities:
    chemical: float = 1.0
    light: float = 1.0
    thermal: float = 0.0
    mechanical: float = 0.0
    electromagnetic: float = 0.0
    social: float = 0.5
    magnetic: float = 0.0
    proprioceptive: float = 0.5
    auditory: float = 0.0
    visual_range: float = 0.0

    def to_dict(self) -> dict:
        return {
            "chemical": self.chemical,
            "light": self.light,
            "thermal": self.thermal,
            "mechanical": self.mechanical,
            "electromagnetic": self.electromagnetic,
            "social": self.social,
            "magnetic": self.magnetic,
            "proprioceptive": self.proprioceptive,
            "auditory": self.auditory,
            "visual_range": self.visual_range,
        }

    @staticmethod
    def from_gene_value(val: float) -> "SensoryCapabilities":
        c = SensoryCapabilities()
        if val < 0.1:
            c.chemical, c.light = 0.3, 0.2
        elif val < 0.25:
            c.chemical, c.light, c.social = 0.7, 0.5, 0.3
        elif val < 0.5:
            c.chemical, c.light, c.thermal, c.social, c.proprioceptive = (0.9, 0.8, 0.3, 0.5, 0.6)
        elif val < 0.75:
            c.chemical, c.light, c.thermal, c.mechanical, c.social, c.proprioceptive, c.auditory = (
                1.0,
                0.9,
                0.6,
                0.4,
                0.7,
                0.8,
                0.3,
            )
        else:
            c.chemical, c.light, c.thermal, c.mechanical = 1.0, 1.0, 0.8, 0.7
            c.electromagnetic, c.social, c.magnetic = 0.5, 0.9, 0.3
            c.proprioceptive, c.auditory, c.visual_range = 0.9, 0.6, 0.5
        return c


@dataclass
class SensoryInput:
    chemical_gradients: dict[ElementType, float]
    nearby_agents: list[AgentID]
    light_level: float
    temperature: float
    pressure: float
    pain_signal: float
    ca_state: int = 0


@dataclass
class ActionOutput:
    move_direction: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    move_speed: float = 0.0
    emit_chemical: Optional[tuple[ElementType, float]] = None
    eat_target: Optional[AgentID] = None
    signal_to: Optional[tuple[AgentID, str]] = None
    interact_with: Optional[AgentID] = None
    reproduce_with: Optional[AgentID] = None


@dataclass
class EmotionVector:
    fear: float = 0.0
    anger: float = 0.0
    joy: float = 0.0
    sadness: float = 0.0
    disgust: float = 0.0
    trust: float = 0.5
    anticipation: float = 0.0
    surprise: float = 0.0

    def dominant(self) -> str:
        emotions = {
            "fear": self.fear,
            "anger": self.anger,
            "joy": self.joy,
            "sadness": self.sadness,
            "disgust": self.disgust,
            "trust": self.trust,
        }
        return max(emotions, key=emotions.get)


@dataclass
class PersonalityTraits:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    def to_dict(self) -> dict:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }


@dataclass
class AgentMemory:
    sensory_buffer: list[SensoryInput] = field(default_factory=list)
    working_memory: list[str] = field(default_factory=list)
    episodic_refs: list[str] = field(default_factory=list)
    semantic_graph: dict = field(default_factory=dict)
    semantic_assertions: dict = field(default_factory=dict)
    procedural_skills: dict = field(default_factory=dict)
    last_reward: float = 0.0
    memory_capacity: int = 100
    episodic_decay_rate: float = 0.001
    episodic_timestamps: dict[str, int] = field(default_factory=dict)
    episodic_importance: dict[str, float] = field(default_factory=dict)
    semantic_timestamps: dict[str, int] = field(default_factory=dict)
    procedural_timestamps: dict[str, int] = field(default_factory=dict)
    last_consolidation_tick: int = 0
    identity_coherence: float = 1.0
    in_identity_crisis: bool = False
    skill_proficiency: dict[str, float] = field(default_factory=dict)
    action_sequence_history: list[tuple[int, list[str], float]] = field(default_factory=list)

    def consolidate(self, episodic_store, current_tick: int) -> int:
        moved = 0
        importance_threshold = 0.3
        time_threshold = 200

        to_remove = []
        for ref_id, timestamp in self.episodic_timestamps.items():
            age = current_tick - timestamp
            importance = self.episodic_importance.get(ref_id, 0.5)
            if age > time_threshold and importance < importance_threshold:
                to_remove.append(ref_id)

        for ref_id in to_remove:
            if ref_id in self.episodic_refs:
                self.episodic_refs.remove(ref_id)
            self.episodic_timestamps.pop(ref_id, None)
            self.episodic_importance.pop(ref_id, None)
            moved += 1

        self.last_consolidation_tick = current_tick
        return moved

    def extract_semantic(self, episodic_store, current_tick: int) -> int:
        extracted = 0
        agent_events: dict[str, list[dict]] = {}

        for ref_id in self.episodic_refs:
            try:
                episodes = episodic_store.retrieve_similar(
                    agent_id="",
                    query_episode={"event_type": ref_id},
                    limit=1,
                    min_importance=0.5,
                )
                for ep in episodes:
                    et = ep.get("event_type", "")
                    if et not in agent_events:
                        agent_events[et] = []
                    agent_events[et].append(ep)
            except Exception:
                pass

        for event_type, eps in agent_events.items():
            if len(eps) >= 3:
                fact = f"frequent_{event_type}"
                if fact not in self.semantic_assertions:
                    self.semantic_assertions[fact] = 0.0
                self.semantic_assertions[fact] = min(
                    1.0, self.semantic_assertions[fact] + 0.1 * len(eps)
                )
                self.semantic_timestamps[fact] = current_tick
                extracted += 1

        return extracted

    def imprint_procedural(self, current_tick: int) -> int:
        imprinted = 0
        if len(self.action_sequence_history) < 5:
            return 0

        from collections import Counter

        sequences: Counter[tuple] = Counter()
        for _, actions, reward in self.action_sequence_history:
            if reward > 0:
                seq_tuple = tuple(actions[-5:])
                sequences[seq_tuple] += reward

        for seq, total_reward in sequences.items():
            if total_reward > 5:
                skill_name = f"skill_{seq[0] if seq else 'unknown'}"
                if skill_name not in self.procedural_skills:
                    self.procedural_skills[skill_name] = 0.0
                    self.skill_proficiency[skill_name] = 0.0
                    self.procedural_timestamps[skill_name] = current_tick

                proficiency_gain = min(0.3, total_reward * 0.05)
                self.skill_proficiency[skill_name] = min(
                    1.0, self.skill_proficiency[skill_name] + proficiency_gain
                )
                self.procedural_skills[skill_name] = len(seq)
                imprinted += 1

        return imprinted

    def identity_coherence_check(self, current_tick: int) -> float:
        if not self.semantic_assertions:
            return 1.0

        belief_count = len(self.semantic_assertions)
        recent_beliefs = sum(
            1 for ts in self.semantic_timestamps.values() if current_tick - ts < 500
        )

        coherence = recent_beliefs / max(belief_count, 1)
        self.identity_coherence = coherence
        self.in_identity_crisis = coherence < 0.3
        return coherence


@dataclass
class CAState:
    gol_alive: bool = False
    wireworld_state: int = 0


@dataclass
class RDState:
    u: float = 1.0
    v: float = 0.0


@dataclass
class GridCell:
    x: int
    y: int
    temperature: float = 20.0
    light_level: float = 0.5
    chemical_pool: dict[ElementType, float] = field(default_factory=dict)
    molecule_pool: list[MoleculeID] = field(default_factory=list)
    agent_ids: list[AgentID] = field(default_factory=list)
    terrain_type: str = "plain"
    ca: CAState = field(default_factory=CAState)
    rd: RDState = field(default_factory=RDState)


@dataclass
class Agent:
    id: AgentID
    genome: Genome
    birth_tick: int
    position: Vec2
    velocity: Vec2
    mass: float
    energy: float
    health: float
    age_ticks: int = 0
    metabolism_rate: float = 0.05
    sensory_range: float = 5.0
    reproduction_threshold: float = 0.8
    lifecycle: LifecycleThresholds = field(default_factory=LifecycleThresholds)
    neural_complexity: int = 0
    memory: Optional[AgentMemory] = None
    emotion: EmotionVector = field(default_factory=EmotionVector)
    synapse_weights: dict[int, list[float]] = field(default_factory=dict)
    prev_activations: Optional[np.ndarray] = None
    group_id: Optional[GroupID] = None
    reputation: dict[AgentID, float] = field(default_factory=dict)
    stage: AgentStage = AgentStage.NEONATAL
    is_alive: bool = True
    death_tick: Optional[int] = None
    parent_ids: list[AgentID] = field(default_factory=list)
    children_ids: list[AgentID] = field(default_factory=list)
    species_label: Optional[str] = None
    immune_memory: list[str] = field(default_factory=list)
    immune_system_strength: float = 0.5
    inflammation_level: float = 0.0
    pathogen_exposure: float = 0.0
    personality: Optional[PersonalityTraits] = None
    cognitive_level: int = 0
    beliefs: dict = field(default_factory=dict)
    sensory_capabilities: SensoryCapabilities = field(default_factory=SensoryCapabilities)


@dataclass
class WorldState:
    tick: int
    grid_width: int
    grid_height: int
    grid: dict[tuple[int, int], GridCell]
    agents: dict[AgentID, Agent]
    total_energy: float
    global_entropy: float
    population_count: int
    event_count_this_tick: int
    innovation_count: int = 0


@dataclass
class WorldEvent:
    tick: int
    type: EventType
    data: dict
    source_id: Optional[str] = None
    target_id: Optional[str] = None


@dataclass
class FundamentalConstants:
    G_digital: float = 0.01
    diffusion_constant: float = 0.05
    speed_of_signal: float = 10.0
    mutation_rate_base: float = 0.001


@dataclass
class ChemicalConfig:
    element_set: list[str] = field(default_factory=lambda: ["P", "A", "T", "I", "Ae", "L"])
    bonding_energy_matrix: dict = field(default_factory=dict)
    rd_feed_rate: float = 0.055
    rd_kill_rate: float = 0.062
    rd_Du: float = 0.16
    rd_Dv: float = 0.08


@dataclass
class EnvironmentalConfig:
    climate_volatility: float = 0.3
    resource_distribution: str = "heterogeneous"
    disaster_base_probability: float = 0.001


@dataclass
class SimulationConfig:
    seed_id: str
    genesis_mode: str
    grid_width: int = 64
    grid_height: int = 64
    initial_energy_density: float = 1.0
    research_hypothesis: str = ""
    fundamental: FundamentalConstants = field(default_factory=FundamentalConstants)
    chemical: ChemicalConfig = field(default_factory=ChemicalConfig)
    environmental: EnvironmentalConfig = field(default_factory=EnvironmentalConfig)
    physics_per_fundamental: int = 1
    chemistry_per_physics: int = 10
    biology_per_chemistry: int = 10
    cognitive_per_biology: int = 10
    ca_per_physics: int = 5
    rd_per_chemistry: int = 1
    metrics_sample_every: int = 1000
    social_per_cognitive: int = 100
    geological_per_social: int = 100
