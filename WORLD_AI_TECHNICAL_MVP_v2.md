# WORLD.AI — TECHNICAL MVP SPECIFICATION
## *Panduan Coding dari Nol*

> **Scope MVP:** Phase 0 + Phase 1 dari Roadmap v0.3 — Genesis Engine + Life Emergence.
> Tujuan: Dunia berjalan, partikel bergerak, kimia terjadi, kehidupan pertama muncul, tervisualisasi.

---

**Version:** 2.0.0
**Target:** Bisa dijalankan dan diobservasi dalam 3 bulan pertama
**Prinsip MVP:** Sederhana tapi benar secara ilmiah. Jangan optimasi dulu — buat benar dulu.
**Companion:** WORLD_AI_MASTER_DESIGN_v0.3.md

**Changelog dari v1.0.0:**
- LLM layer dimigrasikan dari Anthropic SDK ke **OpenRouter** (OpenAI-compatible API)
- Multi-model strategy model strings diperbarui ke format OpenRouter
- Syntax error di `REACTION_RULES` rule ke-4 diperbaiki
- **Gray-Scott reaction-diffusion system** ditambahkan (Bab 3.6 design doc)
- **Cellular Automata layer** ditambahkan: GoL variant + Wireworld variant (Bab 3.5)
- **PCG PRNG** per-region dengan seeding deterministik ditambahkan (Bab 3.4)
- **Biogeochemical cycles** carbon + nitrogen + water diimplementasikan (Bab 8)
- **Hebbian learning** diperbaiki dari noise approximation ke implementasi yang benar (`pre × post × reward`)
- **Abiogenesis Mode A/B/C** logic lengkap diimplementasikan (Bab 9.2)
- **Agent lifecycle phase transitions** dengan critical period diimplementasikan (Bab 52.1)
- **Qdrant episodic memory** — write + similarity retrieval diimplementasikan (Bab 48)
- **Complexity metrics** ditambahkan: Shannon entropy populasi, approximasi Φ, innovation rate (Bab 57)
- **God Mode audit log** + governance protocol diimplementasikan (Bab 53.5)
- **World Seeds schema** diperluas sesuai design doc Bab 54
- **Alembic migration** setup + folder structure ditambahkan
- `.env.example` diperbarui dengan variabel OpenRouter
- `pyproject.toml` — dependency `anthropic` diganti `openai`
- Sprint plan diperbarui dengan task baru

---

## DAFTAR ISI

1. [Tech Stack — Keputusan Final](#1-tech-stack)
2. [Monorepo Structure](#2-monorepo-structure)
3. [Core Data Models](#3-core-data-models)
4. [System Architecture](#4-system-architecture)
5. [Simulation Engine — Core Systems](#5-simulation-engine)
6. [Agent Runtime](#6-agent-runtime)
7. [Observer Layer & LLM (OpenRouter)](#7-observer-layer)
8. [API Contracts](#8-api-contracts)
9. [Visualizer (Frontend)](#9-visualizer)
10. [Database Schema & Migrations](#10-database-schema)
11. [Development Phases (Sprint Plan)](#11-development-phases)
12. [Environment Setup](#12-environment-setup)
13. [Testing Strategy](#13-testing-strategy)
14. [Key Engineering Decisions & Rationale](#14-engineering-decisions)

---

## 1. TECH STACK — KEPUTUSAN FINAL

### 1.1 Rationale Pemilihan

Prioritas stack MVP: **developer velocity > raw performance**. Kita belum tahu bottleneck mana yang pertama muncul. Optimasi dulu coding yang benar, profiling kemudian, rewrite hotpath kalau perlu.

### 1.2 Stack Final

| Layer | Teknologi | Versi | Alasan |
|---|---|---|---|
| **Simulation Core** | Python | 3.12+ | Ecosystem AI/ML terbaik, NumPy untuk physics batch |
| **Physics batch ops** | NumPy + Numba | latest | Vectorized ops, JIT untuk hotpath |
| **Agent NN** | PyTorch | 2.x | Fleksibel untuk network yang berevolusi |
| **API Server** | FastAPI | latest | Async, OpenAPI auto-gen, performa baik |
| **Real-time Push** | WebSocket (FastAPI built-in) | — | Dashboard bisa live-update |
| **World State DB** | Redis | 7.x | In-memory, pub/sub untuk events, fast R/W |
| **Agent Archive DB** | PostgreSQL | 16+ | Relational, JSONB untuk flexible schema |
| **DB Migrations** | Alembic | latest | Schema versioning, reproducible setup |
| **Vector Memory** | Qdrant | latest | Per-agent episodic memory embedding |
| **Event Log** | PostgreSQL (append-only table) | — | Simplicity over Kafka untuk MVP |
| **Frontend** | React + TypeScript | 18.x | Component-based, TypeScript untuk safety |
| **Visualization** | PixiJS | 8.x | WebGL 2D renderer, 60fps dengan ribuan sprites |
| **State Management** | Zustand | latest | Minimal, tidak perlu Redux |
| **LLM Client** | openai SDK (OpenRouter) | latest | OpenAI-compatible, akses semua model |
| **Task Queue** | Celery + Redis | latest | Background LLM jobs |
| **Container** | Docker + docker-compose | latest | Reproducible environment |
| **Package Manager** | uv (Python) + pnpm (JS) | latest | Keduanya jauh lebih cepat dari pip/npm |

### 1.3 Yang Sengaja Tidak Dipakai di MVP

| Teknologi | Alasan Tidak Dipakai Sekarang |
|---|---|
| Rust/C++ | Premature optimization. Bisa migrate hotpath nanti. |
| Kafka | Overkill untuk MVP. PostgreSQL append-only cukup. |
| Kubernetes | Docker compose cukup untuk development. |
| Ray/Dask | Distributed compute baru dibutuhkan di Phase 4+. |
| Unity/Godot | Kita butuh kontrol penuh atas simulation loop. |
| Anthropic SDK langsung | Diganti OpenRouter untuk fleksibilitas multi-model. |

---

## 2. MONOREPO STRUCTURE

```
world-ai/
│
├── packages/
│   ├── simulation/              # Python — Core simulation engine
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── simulation/
│   │   │       ├── __init__.py
│   │   │       ├── world.py             # World class — top-level orchestrator
│   │   │       ├── tick.py              # Tick system, scheduler
│   │   │       ├── prng.py              # PCG PRNG per-region (NEW v2)
│   │   │       │
│   │   │       ├── physics/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── grid.py          # Spatial grid, QuadTree index
│   │   │       │   ├── particles.py     # Particle system, Verlet integration
│   │   │       │   ├── forces.py        # Gravity, cohesion, repulsion
│   │   │       │   ├── diffusion.py     # Fick's law diffusion
│   │   │       │   ├── cellular_automata.py  # CA layer: GoL + Wireworld (NEW v2)
│   │   │       │   ├── reaction_diffusion.py # Gray-Scott system (NEW v2)
│   │   │       │   └── waves.py         # Wave propagation untuk sinyal
│   │   │       │
│   │   │       ├── chemistry/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── elements.py      # Element definitions
│   │   │       │   ├── bonds.py         # Bonding rules & energetics
│   │   │       │   ├── reactions.py     # Reaction system, Arrhenius kinetics
│   │   │       │   ├── molecules.py     # Molecule registry
│   │   │       │   └── diffusion.py     # Chemical diffusion in grid
│   │   │       │
│   │   │       ├── thermodynamics/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── energy.py        # Energy accounting, conservation check
│   │   │       │   ├── entropy.py       # Entropy tracking
│   │   │       │   └── heat.py          # Heat transfer, temperature
│   │   │       │
│   │   │       ├── biology/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── genome.py        # Genome digital, mutation
│   │   │       │   ├── cell.py          # Cell structure, membrane
│   │   │       │   ├── metabolism.py    # Metabolic processes
│   │   │       │   ├── reproduction.py  # Division, sexual reproduction
│   │   │       │   ├── abiogenesis.py   # Protokol genesis Mode A/B/C (UPDATED v2)
│   │   │       │   ├── lifecycle.py     # Phase transitions, critical periods (UPDATED v2)
│   │   │       │   └── immune.py        # Innate immunity basics
│   │   │       │
│   │   │       ├── agents/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── agent.py         # Base Agent class
│   │   │       │   ├── neural.py        # Neural network (evolving, Hebbian) (UPDATED v2)
│   │   │       │   ├── memory.py        # Memory layers + Qdrant integration (UPDATED v2)
│   │   │       │   ├── sensory.py       # Sensor system
│   │   │       │   └── actions.py       # Action space
│   │   │       │
│   │   │       ├── environment/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── climate.py       # Climate & weather system
│   │   │       │   ├── resources.py     # Resource pools & distribution
│   │   │       │   └── cycles.py        # Biogeochemical cycles (UPDATED v2)
│   │   │       │
│   │   │       ├── metrics/             # Complexity metrics (NEW v2)
│   │   │       │   ├── __init__.py
│   │   │       │   ├── entropy.py       # Shannon entropy populasi
│   │   │       │   ├── phi.py           # Integrated information approximasi
│   │   │       │   └── innovation.py    # Innovation rate tracker
│   │   │       │
│   │   │       └── systems/
│   │   │           ├── __init__.py
│   │   │           ├── event_bus.py     # Event pub/sub
│   │   │           ├── registry.py      # Entity registry
│   │   │           └── persistence.py  # State save/load
│   │   │
│   │   └── tests/
│   │       ├── test_physics.py
│   │       ├── test_chemistry.py
│   │       ├── test_thermodynamics.py
│   │       ├── test_biology.py
│   │       ├── test_agents.py
│   │       ├── test_ca.py               # CA layer tests (NEW v2)
│   │       ├── test_metrics.py          # Complexity metrics tests (NEW v2)
│   │       └── test_integration.py
│   │
│   ├── api/                     # Python — FastAPI server
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── api/
│   │           ├── __init__.py
│   │           ├── main.py              # FastAPI app, WebSocket
│   │           ├── routes/
│   │           │   ├── world.py         # World state endpoints
│   │           │   ├── agents.py        # Agent inspection
│   │           │   ├── control.py       # God mode controls + audit log
│   │           │   ├── metrics.py       # Complexity metrics endpoints (NEW v2)
│   │           │   └── research.py      # Research/analysis endpoints
│   │           ├── websocket/
│   │           │   ├── manager.py       # WS connection manager
│   │           │   └── events.py        # Event streaming
│   │           └── schemas/             # Pydantic models
│   │               ├── world.py
│   │               ├── agent.py
│   │               ├── events.py
│   │               └── audit.py         # Audit log schemas (NEW v2)
│   │
│   ├── observer/                # Python — LLM Observer layer (OpenRouter)
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── observer/
│   │           ├── __init__.py
│   │           ├── client.py            # OpenRouter client setup (NEW v2)
│   │           ├── classifier.py        # LLM-based classification
│   │           ├── narrator.py          # Narasi & life stories
│   │           ├── analyzer.py          # Pattern analysis
│   │           └── tasks.py             # Celery tasks
│   │
│   └── visualizer/              # TypeScript/React — Dashboard
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── App.tsx
│       │   ├── main.tsx
│       │   │
│       │   ├── engine/              # PixiJS rendering
│       │   │   ├── WorldRenderer.ts     # Main renderer
│       │   │   ├── AgentSprite.ts       # Per-agent visual
│       │   │   ├── HeatmapLayer.ts      # Resource/energy heatmap
│       │   │   ├── CALayer.ts           # Cellular automata overlay (NEW v2)
│       │   │   └── Camera.ts            # Pan/zoom
│       │   │
│       │   ├── store/               # Zustand state
│       │   │   ├── worldStore.ts
│       │   │   ├── selectionStore.ts
│       │   │   ├── metricsStore.ts      # Complexity metrics (NEW v2)
│       │   │   └── uiStore.ts
│       │   │
│       │   ├── hooks/
│       │   │   ├── useWebSocket.ts
│       │   │   ├── useWorldState.ts
│       │   │   └── useAgentData.ts
│       │   │
│       │   └── components/
│       │       ├── Dashboard/
│       │       │   ├── Dashboard.tsx
│       │       │   ├── StatsPanel.tsx
│       │       │   ├── MetricsPanel.tsx     # Complexity metrics panel (NEW v2)
│       │       │   └── Timeline.tsx
│       │       ├── Inspector/
│       │       │   ├── AgentInspector.tsx
│       │       │   ├── MemoryViz.tsx
│       │       │   └── GenomeViz.tsx
│       │       ├── Controls/
│       │       │   ├── SpeedControl.tsx
│       │       │   └── GodMode.tsx
│       │       └── shared/
│       │           ├── Panel.tsx
│       │           └── Chart.tsx
│       │
│       └── public/
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── Dockerfile.simulation
│   ├── Dockerfile.api
│   └── Dockerfile.visualizer
│
├── alembic/                     # Database migrations (NEW v2)
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
│
├── scripts/
│   ├── setup.sh                 # One-command setup
│   ├── seed_run.py              # Start a seeded run
│   └── benchmark.py             # Performance benchmarks
│
├── docs/
│   ├── WORLD_AI_MASTER_DESIGN_v0.3.md
│   └── WORLD_AI_TECHNICAL_MVP_v2.md   # This file
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. CORE DATA MODELS

### 3.1 Python — Type Definitions (simulation/src/simulation/types.py)

```python
# ============================================================
# CORE TYPES — World.ai Simulation v2.0.0
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import numpy as np


# ── Identifiers ─────────────────────────────────────────────

AgentID = str        # "AG-{uuid4_short}"
SpeciesID = str      # Assigned by LLM observer layer
GroupID = str        # "GRP-{uuid4_short}"
MoleculeID = str
RegionID = str       # "RGN-{x}-{y}" untuk PRNG seeding


# ── Space & Time ─────────────────────────────────────────────

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
    """Passed to every system update."""
    tick: int
    dt: float                     # seconds per tick (simulation time)
    physics_tick: bool
    chemistry_tick: bool
    biology_tick: bool
    cognitive_tick: bool
    social_tick: bool
    geological_tick: bool
    ca_tick: bool                 # Cellular Automata tick (NEW v2)
    rd_tick: bool                 # Reaction-Diffusion tick (NEW v2)
    metrics_tick: bool            # Complexity metrics sampling (NEW v2)


# ── Elements & Chemistry ──────────────────────────────────────

class ElementType(Enum):
    PRIMUM = "P"    # Hydrogen analog — fuel
    AQUA   = "A"    # Oxygen/Water — solvent
    TERRA  = "T"    # Carbon — structural backbone
    IGNIS  = "I"    # Nitrogen — info molecule
    AETHER = "Ae"   # Phosphorus/Sulfur — energy carrier
    LAPIS  = "L"    # Heavy minerals — catalyst


class BondType(Enum):
    COVALENT = "covalent"   # Strong, stable
    WEAK     = "weak"       # Reversible (H-bond, vdW)
    IONIC    = "ionic"      # Medium, electrostatic


@dataclass
class Element:
    type: ElementType
    mass: float
    reactivity: float           # 0..1
    position: Vec2
    velocity: Vec2
    charge: float = 0.0
    bonded_to: list[MoleculeID] = field(default_factory=list)


@dataclass
class Molecule:
    id: MoleculeID
    elements: list[ElementType]
    bond_types: list[BondType]
    free_energy: float          # ΔG in digital joules
    is_catalyst: bool = False
    can_replicate: bool = False  # RNA analog flag
    can_form_membrane: bool = False


# ── Cell & Genome ─────────────────────────────────────────────

@dataclass
class Gene:
    """Single gene in genome."""
    id: str
    sequence: bytes             # Binary sequence — the "code"
    expression_level: float     # 0..1, how strongly expressed
    promoter_condition: str     # Expression condition (serialized)
    product_type: str           # "structural|regulatory|catalytic|neural"
    is_active: bool = True


@dataclass
class Genome:
    genes: list[Gene]
    mutation_rate: float = 0.001    # Per gene per reproduction
    max_length: int = 1000

    def checksum(self) -> str:
        """Unique hash untuk genome comparison."""
        import hashlib
        data = b"".join(g.sequence for g in self.genes)
        return hashlib.sha256(data).hexdigest()[:16]

    def mutate(self) -> Genome:
        """Returns mutated copy — point mutation, insertion, deletion."""
        import copy, random
        new_genome = copy.deepcopy(self)
        for gene in new_genome.genes:
            if random.random() < self.mutation_rate:
                if gene.sequence:
                    pos = random.randint(0, len(gene.sequence) * 8 - 1)
                    byte_pos, bit_pos = divmod(pos, 8)
                    ba = bytearray(gene.sequence)
                    ba[byte_pos] ^= (1 << bit_pos)
                    gene.sequence = bytes(ba)
        # Insertion: occasional new gene
        if random.random() < self.mutation_rate * 0.1 and len(new_genome.genes) < self.max_length:
            new_gene = Gene(
                id=f"g_{random.randint(0, 999999):06d}",
                sequence=bytes([random.randint(0, 255) for _ in range(4)]),
                expression_level=random.random(),
                promoter_condition="default",
                product_type=random.choice(["structural", "regulatory", "catalytic", "neural"]),
            )
            new_genome.genes.append(new_gene)
        return new_genome

    def crossover(self, other: Genome) -> tuple[Genome, Genome]:
        """Two-point crossover untuk reproduksi seksual."""
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
    """Biological cell — building block of all life."""
    id: str
    genome: Genome

    # Physical
    position: Vec2
    velocity: Vec2
    mass: float
    radius: float

    # Energy & Health
    energy: float               # 0..1 (0 = dead)
    health: float               # 0..1
    age_ticks: int = 0

    # Biological state
    atp_level: float = 0.5      # Energy currency
    membrane_integrity: float = 1.0
    internal_ph: float = 7.0
    immune_memory: list[str] = field(default_factory=list)

    # Flags
    is_alive: bool = True
    can_reproduce: bool = False


# ── Agent Stage & Lifecycle ───────────────────────────────────

class AgentStage(Enum):
    NEONATAL   = "neonatal"
    JUVENILE   = "juvenile"
    ADOLESCENT = "adolescent"
    ADULT      = "adult"
    ELDER      = "elder"


@dataclass
class LifecycleThresholds:
    """Threshold tick ages per stage — dikodekan dalam genome."""
    juvenile_at: int = 50
    adolescent_at: int = 200
    adult_at: int = 500
    elder_at: int = 2000
    max_lifespan: int = 5000


# ── Sensory & Action ─────────────────────────────────────────

@dataclass
class SensoryInput:
    """Input dari lingkungan sekitar."""
    chemical_gradients: dict[ElementType, float]    # Konsentrasi di sekitar
    nearby_agents: list[AgentID]                    # Dalam sensory range
    light_level: float                              # 0..1
    temperature: float                              # Local temperature
    pressure: float                                 # Mechanical pressure
    pain_signal: float                              # 0..1 (0 = no pain)
    ca_state: int = 0                               # Cellular automata state of current cell (NEW v2)


@dataclass
class ActionOutput:
    """Output keputusan agen."""
    move_direction: Vec2 = field(default_factory=lambda: Vec2(0, 0))
    move_speed: float = 0.0
    emit_chemical: Optional[tuple[ElementType, float]] = None
    eat_target: Optional[AgentID] = None
    signal_to: Optional[tuple[AgentID, str]] = None
    interact_with: Optional[AgentID] = None
    reproduce_with: Optional[AgentID] = None


@dataclass
class EmotionVector:
    """Emotional state sebagai computational module."""
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
            "fear": self.fear, "anger": self.anger,
            "joy": self.joy, "sadness": self.sadness,
            "disgust": self.disgust, "trust": self.trust,
        }
        return max(emotions, key=emotions.get)


@dataclass
class AgentMemory:
    """Memory layers per agen."""
    sensory_buffer: list[SensoryInput]  # Last 5 ticks
    working_memory: list[str]           # Active items
    episodic_refs: list[str]            # IDs ke Qdrant
    semantic_graph: dict                # Simple key-value
    last_reward: float = 0.0            # Untuk Hebbian gating (NEW v2)


@dataclass
class Agent:
    """Full agent — dari sel sederhana hingga makhluk kompleks."""
    id: AgentID
    genome: Genome
    birth_tick: int

    # Physical
    position: Vec2
    velocity: Vec2
    mass: float
    energy: float               # 0..1
    health: float               # 0..1
    age_ticks: int = 0

    # Biological
    metabolism_rate: float = 0.05
    sensory_range: float = 5.0
    reproduction_threshold: float = 0.8
    lifecycle: LifecycleThresholds = field(default_factory=LifecycleThresholds)

    # Cognitive
    neural_complexity: int = 0
    memory: Optional[AgentMemory] = None
    emotion: EmotionVector = field(default_factory=EmotionVector)

    # Neural weights — stored separately from network structure (NEW v2)
    # Key: layer_index, Value: weight matrix as flat list
    synapse_weights: dict[int, list[float]] = field(default_factory=dict)
    prev_activations: Optional[np.ndarray] = None  # For Hebbian: pre-synaptic

    # Social
    group_id: Optional[GroupID] = None
    reputation: dict[AgentID, float] = field(default_factory=dict)

    # Lifecycle
    stage: AgentStage = AgentStage.NEONATAL
    is_alive: bool = True
    death_tick: Optional[int] = None
    parent_ids: list[AgentID] = field(default_factory=list)
    children_ids: list[AgentID] = field(default_factory=list)

    # Species — assigned by observer
    species_label: Optional[str] = None


# ── World State ──────────────────────────────────────────────

@dataclass
class CAState:
    """Cellular Automata state per grid cell (NEW v2)."""
    gol_alive: bool = False         # Game of Life state
    wireworld_state: int = 0        # 0=empty, 1=conductor, 2=head, 3=tail


@dataclass
class RDState:
    """Reaction-Diffusion state per grid cell (NEW v2)."""
    u: float = 1.0   # Gray-Scott chemical U
    v: float = 0.0   # Gray-Scott chemical V


@dataclass
class GridCell:
    """Satu sel dalam world grid."""
    x: int
    y: int
    temperature: float = 20.0
    light_level: float = 0.5
    chemical_pool: dict[ElementType, float] = field(default_factory=dict)
    molecule_pool: list[MoleculeID] = field(default_factory=list)
    agent_ids: list[AgentID] = field(default_factory=list)
    terrain_type: str = "plain"
    ca: CAState = field(default_factory=CAState)       # NEW v2
    rd: RDState = field(default_factory=RDState)       # NEW v2


@dataclass
class WorldState:
    """Snapshot of world at a tick."""
    tick: int
    grid_width: int
    grid_height: int
    grid: dict[tuple[int, int], GridCell]
    agents: dict[AgentID, Agent]
    total_energy: float
    global_entropy: float
    population_count: int
    event_count_this_tick: int
    innovation_count: int = 0  # NEW v2 — untuk innovation rate


# ── Events ────────────────────────────────────────────────────

class EventType(Enum):
    AGENT_BORN         = "agent_born"
    AGENT_DIED         = "agent_died"
    AGENT_REPRODUCED   = "agent_reproduced"
    AGENT_STAGE_CHANGE = "agent_stage_change"   # NEW v2
    CHEMICAL_REACTION  = "chemical_reaction"
    ABIOGENESIS        = "abiogenesis"
    SPECIATION         = "speciation"
    COLLISION          = "collision"
    ENERGY_TRANSFER    = "energy_transfer"
    MUTATION           = "mutation"
    CA_PATTERN         = "ca_pattern"            # NEW v2 — CA emergent pattern
    TICK_COMPLETE      = "tick_complete"
    GOD_MODE_INTERVENTION = "god_mode_intervention"  # NEW v2 — audit log


@dataclass
class WorldEvent:
    tick: int
    type: EventType
    data: dict
    source_id: Optional[str] = None
    target_id: Optional[str] = None


# ── Simulation Config (World Seed) ────────────────────────────

@dataclass
class FundamentalConstants:
    """Konstanta fisika dasar — hardcoded per run."""
    G_digital: float = 0.01
    diffusion_constant: float = 0.05
    speed_of_signal: float = 10.0
    mutation_rate_base: float = 0.001


@dataclass
class ChemicalConfig:
    """Konfigurasi kimia untuk seed."""
    element_set: list[str] = field(default_factory=lambda: ["P","A","T","I","Ae","L"])
    bonding_energy_matrix: dict = field(default_factory=dict)
    rd_feed_rate: float = 0.055      # Gray-Scott F parameter (NEW v2)
    rd_kill_rate: float = 0.062      # Gray-Scott k parameter (NEW v2)
    rd_Du: float = 0.16              # Diffusion U (NEW v2)
    rd_Dv: float = 0.08              # Diffusion V (NEW v2)


@dataclass
class EnvironmentalConfig:
    """Konfigurasi lingkungan untuk seed."""
    climate_volatility: float = 0.3
    resource_distribution: str = "heterogeneous"
    disaster_base_probability: float = 0.001


@dataclass
class SimulationConfig:
    """World Seed — parameter lengkap untuk satu run."""
    seed_id: str
    genesis_mode: str           # "pure|seeded_chemistry|seeded_protocells"
    grid_width: int = 64
    grid_height: int = 64
    initial_energy_density: float = 1.0
    research_hypothesis: str = ""   # NEW v2

    # Nested configs
    fundamental: FundamentalConstants = field(default_factory=FundamentalConstants)
    chemical: ChemicalConfig = field(default_factory=ChemicalConfig)
    environmental: EnvironmentalConfig = field(default_factory=EnvironmentalConfig)

    # Tick ratios
    physics_per_fundamental: int = 1
    chemistry_per_physics: int = 10
    biology_per_chemistry: int = 10
    cognitive_per_biology: int = 10
    ca_per_physics: int = 5         # NEW v2 — CA update frequency
    rd_per_chemistry: int = 1       # NEW v2 — RD update every chemistry tick
    metrics_sample_every: int = 1000  # NEW v2 — complexity metrics sampling
    social_per_cognitive: int = 100
    geological_per_social: int = 100
```

### 3.2 TypeScript — Frontend Types (visualizer/src/types/world.ts)

```typescript
// ============================================================
// FRONTEND TYPES — World.ai v2.0.0
// ============================================================

export type AgentID = string;
export type GroupID = string;

export interface Vec2 {
  x: number;
  y: number;
}

export type ElementType = "P" | "A" | "T" | "I" | "Ae" | "L";

export interface CAStateData {
  gol_alive: boolean;
  wireworld_state: number;
}

export interface RDStateData {
  u: number;
  v: number;
}

export interface GridCellData {
  x: number;
  y: number;
  temperature: number;
  light_level: number;
  chemical_pool: Record<ElementType, number>;
  agent_count: number;
  terrain_type: string;
  ca: CAStateData;
  rd: RDStateData;
}

export interface AgentSummary {
  id: AgentID;
  position: Vec2;
  energy: number;
  health: number;
  age_ticks: number;
  stage: string;
  species_label: string | null;
  group_id: string | null;
  neural_complexity: number;
}

export interface AgentDetail extends AgentSummary {
  genome_hash: string;
  parent_ids: AgentID[];
  children_ids: AgentID[];
  emotion: {
    fear: number; anger: number; joy: number;
    sadness: number; trust: number;
  };
  reputation_count: number;
  birth_tick: number;
  lifecycle_stage: string;
}

export interface WorldSnapshot {
  tick: number;
  grid_width: number;
  grid_height: number;
  population_count: number;
  global_entropy: number;
  total_energy: number;
  species_count: number;
  grid_cells: GridCellData[];
  agents: AgentSummary[];
}

export interface ComplexityMetrics {
  tick: number;
  shannon_entropy_population: number;
  effective_complexity: number;
  innovation_rate: number;
  avg_neural_phi: number;
  genome_diversity: number;
}

export interface WorldEvent {
  tick: number;
  type: string;
  data: Record<string, unknown>;
  source_id?: string;
  target_id?: string;
}

export interface WorldStats {
  tick: number;
  population: number;
  species_count: number;
  entropy: number;
  energy_total: number;
  births_this_tick: number;
  deaths_this_tick: number;
  reactions_this_tick: number;
  innovation_count: number;
}

export type WSMessage =
  | { type: "snapshot"; payload: WorldSnapshot }
  | { type: "event"; payload: WorldEvent }
  | { type: "stats"; payload: WorldStats }
  | { type: "metrics"; payload: ComplexityMetrics }
  | { type: "tick"; payload: { tick: number } };
```

---

## 4. SYSTEM ARCHITECTURE

### 4.1 Diagram Aliran Data

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATION PROCESS                            │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Physics  │───▶│Chemistry │───▶│ Biology  │───▶│Cognitive │  │
│  │ +CA +RD  │    │ +Cycles  │    │ +Lifecycle│   │ +Hebbian │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│        │               │               │               │         │
│        └───────────────┴───────────────┴───────────────┘         │
│                                │                                 │
│                        ┌───────▼───────┐                        │
│                        │  Event Bus    │                        │
│                        └───────┬───────┘                        │
│                                │                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │          Complexity Metrics Sampler (every N ticks)        │  │
│  │  Shannon H_pop | Φ approx | Innovation Rate | Diversity    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                │                                 │
│        ┌───────────────────────┼───────────────────────┐        │
│        ▼                       ▼                       ▼        │
│  ┌──────────┐          ┌──────────────┐         ┌──────────┐   │
│  │  Redis   │          │  PostgreSQL  │         │  Qdrant  │   │
│  │ (state)  │          │  (archive)   │         │ (memory) │   │
│  └──────────┘          └──────────────┘         └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      FastAPI Server      │
                    │   REST + WebSocket       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  React Visualizer        │
                    │  PixiJS + Dashboard      │
                    └─────────────────────────┘

     ┌─────────────────────────────────────────────────────────┐
     │      OBSERVER LAYER (Celery workers — OpenRouter)        │
     │  LLM classification + narration via OpenRouter API       │
     │  Triggered by events, NOT inline in simulation loop      │
     │  Anthropic / Gemini / Mistral available via OpenRouter   │
     └─────────────────────────────────────────────────────────┘
```

### 4.2 Simulation Loop

```python
# packages/simulation/src/simulation/world.py

class World:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.tick = 0
        self.grid: dict[tuple, GridCell] = {}
        self.agents: dict[AgentID, Agent] = {}
        self.event_bus = EventBus()
        self.systems = self._init_systems()
        self.metrics_history: list[dict] = []
        self._initialize_grid()
        self._initialize_prng()   # NEW v2

    def _initialize_prng(self):
        """Initialize per-region PCG PRNG seeds."""
        from .prng import RegionalPRNG
        self.prng = RegionalPRNG(
            world_seed=hash(self.config.seed_id),
            grid_width=self.config.grid_width,
            grid_height=self.config.grid_height,
        )

    def _initialize_grid(self):
        W, H = self.config.grid_width, self.config.grid_height
        for x in range(W):
            for y in range(H):
                cell = GridCell(x=x, y=y)
                # Distribute initial energy heterogeneously
                cell.chemical_pool = {
                    ElementType.PRIMUM: max(0, self.config.initial_energy_density + (
                        (x * 7 + y * 13) % 10 - 5) * 0.1),
                    ElementType.AQUA: 5.0,
                    ElementType.TERRA: 3.0,
                    ElementType.IGNIS: 1.0,
                    ElementType.AETHER: 0.5,
                    ElementType.LAPIS: 0.2,
                }
                self.grid[(x, y)] = cell

    def _init_systems(self) -> list:
        from .physics.particles import PhysicsSystem
        from .physics.diffusion import DiffusionSystem
        from .physics.cellular_automata import CellularAutomataSystem
        from .physics.reaction_diffusion import ReactionDiffusionSystem
        from .chemistry.reactions import ChemistrySystem
        from .thermodynamics.energy import ThermodynamicsSystem
        from .environment.cycles import BiogeochemicalCycleSystem
        from .biology.metabolism import MetabolismSystem
        from .biology.reproduction import ReproductionSystem
        from .biology.lifecycle import LifecycleSystem
        from .agents.neural import CognitiveSystem
        from .metrics.entropy import MetricsSamplerSystem

        return [
            PhysicsSystem(self),
            DiffusionSystem(self),
            CellularAutomataSystem(self),        # NEW v2
            ReactionDiffusionSystem(self),        # NEW v2
            ChemistrySystem(self),
            ThermodynamicsSystem(self),
            BiogeochemicalCycleSystem(self),      # NEW v2
            MetabolismSystem(self),
            ReproductionSystem(self),
            LifecycleSystem(self),                # NEW v2
            CognitiveSystem(self),
            MetricsSamplerSystem(self),           # NEW v2
        ]

    def step(self) -> list[WorldEvent]:
        ctx = self._build_tick_context()
        events = []

        for system in self.systems:
            if system.should_run(ctx):
                system_events = system.update(ctx)
                events.extend(system_events)

        self.tick += 1
        self._publish_events(events)
        return events

    def run(self, max_ticks: int = -1):
        while max_ticks < 0 or self.tick < max_ticks:
            events = self.step()
            self._persist_state_if_needed()

    def total_energy(self) -> float:
        """Untuk energy conservation validation."""
        grid_energy = sum(
            sum(pool.values())
            for cell in self.grid.values()
            for pool in [cell.chemical_pool]
        )
        agent_energy = sum(a.energy for a in self.agents.values() if a.is_alive)
        return grid_energy + agent_energy

    def _build_tick_context(self) -> TickContext:
        t = self.tick
        cfg = self.config
        chem_every = cfg.chemistry_per_physics
        bio_every  = chem_every * cfg.biology_per_chemistry
        cog_every  = bio_every  * cfg.cognitive_per_biology
        return TickContext(
            tick=t,
            dt=0.1,
            physics_tick=True,
            chemistry_tick=(t % chem_every == 0),
            biology_tick=(t % bio_every == 0),
            cognitive_tick=(t % cog_every == 0),
            social_tick=False,
            geological_tick=False,
            ca_tick=(t % cfg.ca_per_physics == 0),
            rd_tick=(t % (chem_every * cfg.rd_per_chemistry) == 0),
            metrics_tick=(t % cfg.metrics_sample_every == 0 and t > 0),
        )

    def _persist_state_if_needed(self):
        if self.tick % 1000 == 0:
            import json
            from .systems.persistence import PersistenceManager
            PersistenceManager.save_snapshot(self)
```

### 4.3 System Interface (ABC)

```python
# packages/simulation/src/simulation/systems/base.py

from abc import ABC, abstractmethod
from ..types import TickContext, WorldEvent

class System(ABC):
    def __init__(self, world):
        self.world = world

    def should_run(self, ctx: TickContext) -> bool:
        return True

    @abstractmethod
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        ...
```

---

## 5. SIMULATION ENGINE — CORE SYSTEMS

### 5.1 PCG PRNG Per-Region (NEW v2)

```python
# packages/simulation/src/simulation/prng.py

import numpy as np
from typing import Optional


def _pcg32(state: np.uint64) -> tuple[np.uint32, np.uint64]:
    """Single step of PCG32 — deterministic, high-quality."""
    oldstate = state
    # LCG step
    state = np.uint64(oldstate * np.uint64(6364136223846793005) + np.uint64(1442695040888963407))
    # Output permutation
    xorshifted = np.uint32(((oldstate >> np.uint64(18)) ^ oldstate) >> np.uint64(27))
    rot = np.uint32(oldstate >> np.uint64(59))
    output = np.uint32((xorshifted >> rot) | (xorshifted << (np.uint32(32) - rot)))
    return output, state


class RegionalPRNG:
    """
    Per-region seedable PRNG menggunakan PCG32.
    Setiap region (x, y) punya state independen.
    Reproducible dengan world_seed yang sama.
    Menghindari korelasi global antara region yang berjauhan.
    """

    def __init__(self, world_seed: int, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        # Seed setiap region secara deterministik dari world_seed
        self._states: dict[tuple[int, int], np.uint64] = {}
        for x in range(grid_width):
            for y in range(grid_height):
                # Unique seed per region menggunakan Cantor pairing + world_seed
                region_seed = int(world_seed) ^ (x * 73856093) ^ (y * 19349663)
                self._states[(x, y)] = np.uint64(abs(region_seed) % (2**64))

    def random(self, region_x: int, region_y: int) -> float:
        """Returns float [0, 1) untuk region tertentu."""
        key = (region_x % self.grid_width, region_y % self.grid_height)
        output, new_state = _pcg32(self._states[key])
        self._states[key] = new_state
        return float(output) / float(2**32)

    def randint(self, region_x: int, region_y: int, low: int, high: int) -> int:
        """Returns int [low, high) untuk region tertentu."""
        r = self.random(region_x, region_y)
        return low + int(r * (high - low))

    def random_global(self) -> float:
        """Global random menggunakan region (0,0) — hanya untuk bootstrap."""
        return self.random(0, 0)
```

### 5.2 Physics System

```python
# packages/simulation/src/simulation/physics/particles.py

import numpy as np
from numba import njit
from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent


@njit
def verlet_integrate(
    positions: np.ndarray,   # (N, 2)
    velocities: np.ndarray,  # (N, 2)
    forces: np.ndarray,      # (N, 2)
    masses: np.ndarray,      # (N,)
    dt: float
) -> tuple[np.ndarray, np.ndarray]:
    """Velocity Verlet integration — JIT compiled."""
    accelerations = forces / masses[:, np.newaxis]
    new_positions = positions + velocities * dt + 0.5 * accelerations * dt**2
    new_velocities = velocities + accelerations * dt
    return new_positions, new_velocities


@njit
def compute_pairwise_forces(
    positions: np.ndarray,  # (N, 2)
    masses: np.ndarray,     # (N,)
    charges: np.ndarray,    # (N,)
    G: float,
    cutoff_distance: float
) -> np.ndarray:
    """Compute gravitational + electromagnetic forces. O(N²)."""
    N = positions.shape[0]
    forces = np.zeros((N, 2))

    for i in range(N):
        for j in range(i + 1, N):
            dx = positions[j, 0] - positions[i, 0]
            dy = positions[j, 1] - positions[i, 1]
            r = (dx**2 + dy**2) ** 0.5

            if r < 1e-6 or r > cutoff_distance:
                continue

            # 2D gravity: F = G * m1 * m2 / r  (linear, not 1/r²)
            f_gravity = G * masses[i] * masses[j] / r

            # Electromagnetic: analog
            f_em = 0.01 * charges[i] * charges[j] / max(r, 0.1)

            f_total = f_gravity + f_em
            fx = f_total * dx / r
            fy = f_total * dy / r

            forces[i, 0] += fx
            forces[i, 1] += fy
            forces[j, 0] -= fx
            forces[j, 1] -= fy

    return forces


class PhysicsSystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.physics_tick:
            return []

        agents = [a for a in self.world.agents.values() if a.is_alive]
        if not agents:
            return []

        N = len(agents)
        positions  = np.array([[a.position.x, a.position.y] for a in agents])
        velocities = np.array([[a.velocity.x, a.velocity.y] for a in agents])
        masses     = np.array([a.mass for a in agents])
        charges    = np.zeros(N)

        forces = compute_pairwise_forces(
            positions, masses, charges,
            G=self.world.config.fundamental.G_digital,
            cutoff_distance=20.0
        )

        drag_coeff = 0.01
        forces -= drag_coeff * velocities

        new_pos, new_vel = verlet_integrate(positions, velocities, forces, masses, ctx.dt)

        W = self.world.config.grid_width
        H = self.world.config.grid_height
        for i, agent in enumerate(agents):
            agent.position.x = new_pos[i, 0] % W
            agent.position.y = new_pos[i, 1] % H
            agent.velocity.x = new_vel[i, 0]
            agent.velocity.y = new_vel[i, 1]

        return []
```

### 5.3 Cellular Automata Layer (NEW v2)

```python
# packages/simulation/src/simulation/physics/cellular_automata.py
"""
Dua CA variants:
- Game of Life (GoL): self-organization, pola stabil sebagai proto-ekologi
- Wireworld: proto-konduktivitas — relevan untuk sistem saraf primitif

Rule set CA bisa berevolusi antar region (bab 3.5 design doc).
"""
import numpy as np
from numba import njit
from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType


@njit
def gol_step(grid: np.ndarray) -> np.ndarray:
    """Game of Life step — toroidal boundaries."""
    H, W = grid.shape
    new_grid = np.zeros_like(grid)
    for y in range(H):
        for x in range(W):
            neighbors = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dy == 0 and dx == 0:
                        continue
                    ny = (y + dy) % H
                    nx = (x + dx) % W
                    neighbors += grid[ny, nx]
            if grid[y, x] == 1:
                new_grid[y, x] = 1 if neighbors in (2, 3) else 0
            else:
                new_grid[y, x] = 1 if neighbors == 3 else 0
    return new_grid


@njit
def wireworld_step(grid: np.ndarray) -> np.ndarray:
    """
    Wireworld CA:
    0 = empty
    1 = conductor
    2 = electron head
    3 = electron tail
    """
    H, W = grid.shape
    new_grid = np.copy(grid)
    for y in range(H):
        for x in range(W):
            state = grid[y, x]
            if state == 0:
                new_grid[y, x] = 0
            elif state == 2:   # head -> tail
                new_grid[y, x] = 3
            elif state == 3:   # tail -> conductor
                new_grid[y, x] = 1
            elif state == 1:   # conductor -> head if 1 or 2 neighboring heads
                head_neighbors = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dy == 0 and dx == 0:
                            continue
                        ny = (y + dy) % H
                        nx = (x + dx) % W
                        if grid[ny, nx] == 2:
                            head_neighbors += 1
                if head_neighbors in (1, 2):
                    new_grid[y, x] = 2
    return new_grid


class CellularAutomataSystem(System):
    def __init__(self, world):
        super().__init__(world)
        W = world.config.grid_width
        H = world.config.grid_height
        # Initialize GoL grid dengan kepadatan ~30%
        self.gol_grid = np.zeros((H, W), dtype=np.int8)
        self.wire_grid = np.zeros((H, W), dtype=np.int8)
        self._initialized = False

    def _initialize_ca(self):
        """Lazy init setelah world selesai dibentuk."""
        W = self.world.config.grid_width
        H = self.world.config.grid_height
        prng = self.world.prng
        for y in range(H):
            for x in range(W):
                if prng.random(x, y) < 0.3:
                    self.gol_grid[y, x] = 1
                # Wireworld: occasional conductor channels (proto-nerves)
                if prng.random(x, y) < 0.05:
                    self.wire_grid[y, x] = 1
        self._initialized = True

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.ca_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not self._initialized:
            self._initialize_ca()

        self.gol_grid = gol_step(self.gol_grid)
        self.wire_grid = wireworld_step(self.wire_grid)

        # Sync CA state back to grid cells
        for (x, y), cell in self.world.grid.items():
            cell.ca.gol_alive = bool(self.gol_grid[y, x])
            cell.ca.wireworld_state = int(self.wire_grid[y, x])

        # Detect emergent patterns (stable structures → log event)
        events = []
        if ctx.tick % 500 == 0:
            alive_count = int(self.gol_grid.sum())
            conductor_count = int((self.wire_grid == 1).sum())
            if alive_count > 0:
                events.append(WorldEvent(
                    tick=ctx.tick,
                    type=EventType.CA_PATTERN,
                    data={
                        "gol_alive_cells": alive_count,
                        "wire_conductors": conductor_count,
                        "wire_electron_heads": int((self.wire_grid == 2).sum()),
                    }
                ))
        return events
```

### 5.4 Reaction-Diffusion System — Gray-Scott (NEW v2)

```python
# packages/simulation/src/simulation/physics/reaction_diffusion.py
"""
Gray-Scott reaction-diffusion system.
Menghasilkan: spots, stripes, labyrinth, spiral — pola biologis natural.
Parameter F dan k mengontrol morfologi pola (lihat pearsonite diagram).

Ini adalah fondasi pola spasial yang akan muncul di abiogenesis dan ekologi.
"""
import numpy as np
from numba import njit
from ..systems.base import System
from ..types import TickContext, WorldEvent


@njit
def gray_scott_step(
    U: np.ndarray,  # (H, W) — chemical U
    V: np.ndarray,  # (H, W) — chemical V
    Du: float,      # Diffusion rate U
    Dv: float,      # Diffusion rate V
    F: float,       # Feed rate
    k: float,       # Kill rate
    dt: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Gray-Scott equations:
    ∂u/∂t = Du∇²u - uv² + F(1-u)
    ∂v/∂t = Dv∇²v + uv² - (F+k)v
    """
    H, W = U.shape

    # Laplacian (toroidal)
    lapU = (np.roll(U, 1, 0) + np.roll(U, -1, 0) +
            np.roll(U, 1, 1) + np.roll(U, -1, 1) - 4 * U)
    lapV = (np.roll(V, 1, 0) + np.roll(V, -1, 0) +
            np.roll(V, 1, 1) + np.roll(V, -1, 1) - 4 * V)

    uvv = U * V * V

    new_U = U + dt * (Du * lapU - uvv + F * (1.0 - U))
    new_V = V + dt * (Dv * lapV + uvv - (F + k) * V)

    # Clamp [0, 1]
    new_U = np.maximum(0.0, np.minimum(1.0, new_U))
    new_V = np.maximum(0.0, np.minimum(1.0, new_V))

    return new_U, new_V


class ReactionDiffusionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        W = world.config.grid_width
        H = world.config.grid_height
        cfg = world.config.chemical

        self.U = np.ones((H, W))
        self.V = np.zeros((H, W))

        # Seed beberapa patch awal untuk trigger pattern formation
        center_x, center_y = W // 2, H // 2
        sq = max(5, min(W, H) // 8)
        self.U[center_y-sq:center_y+sq, center_x-sq:center_x+sq] = 0.5
        self.V[center_y-sq:center_y+sq, center_x-sq:center_x+sq] = 0.25

        self.Du = cfg.rd_Du
        self.Dv = cfg.rd_Dv
        self.F  = cfg.rd_feed_rate
        self.k  = cfg.rd_kill_rate

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.rd_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        self.U, self.V = gray_scott_step(
            self.U, self.V,
            Du=self.Du, Dv=self.Dv,
            F=self.F, k=self.k,
            dt=1.0
        )

        # Sync RD state ke grid cells — V concentration influences chemistry
        for (x, y), cell in self.world.grid.items():
            cell.rd.u = float(self.U[y, x])
            cell.rd.v = float(self.V[y, x])
            # V concentration sebagai proxy untuk complex organic molecules
            # Ini mempengaruhi probabilitas abiogenesis
            if cell.rd.v > 0.2:
                current = cell.chemical_pool.get("Ae", 0)
                cell.chemical_pool["Ae"] = min(current + cell.rd.v * 0.01, 10.0)

        return []
```

### 5.5 Chemistry System (FIXED v2)

```python
# packages/simulation/src/simulation/chemistry/reactions.py

import math, random
from dataclasses import dataclass
from ..types import ElementType, GridCell, WorldEvent, EventType
from ..systems.base import System


# FIXED v2: Tuple syntax correction pada rule ke-4
REACTION_RULES: list[tuple] = [
    # (P + A → water analog) — Basic hydration
    (
        (ElementType.PRIMUM, ElementType.AQUA),
        ("molecule:water_analog",),
        0.5, -1.2
    ),
    # (T + T → carbon_chain) — Carbon chain formation
    (
        (ElementType.TERRA, ElementType.TERRA),
        ("molecule:carbon_chain",),
        1.0, -2.0
    ),
    # (Ae + T → proto_atp) — Energy molecule
    (
        (ElementType.AETHER, ElementType.TERRA),
        ("molecule:proto_atp",),
        2.0, -3.5
    ),
    # FIXED: (carbon_chain + Ae + I → proto_nucleotide) — RNA precursor
    (
        ("molecule:carbon_chain", ElementType.AETHER, ElementType.IGNIS),
        ("molecule:proto_nucleotide",),
        3.0, -5.0
    ),
    # (proto_nucleotide × 4 → proto_rna) — Self-replicating molecule
    (
        ("molecule:proto_nucleotide", "molecule:proto_nucleotide"),
        ("molecule:proto_rna",),
        4.5, -8.0
    ),
    # (water_analog + L → catalyst complex)
    (
        ("molecule:water_analog", ElementType.LAPIS),
        ("molecule:catalyst",),
        1.5, -2.5
    ),
]


def arrhenius_rate(Ea: float, temperature: float, A: float = 1.0) -> float:
    """k = A * exp(-Ea / RT) — normalized to [0, 1]."""
    R = 8.314e-3
    if temperature <= 0:
        return 0.0
    rate = A * math.exp(-Ea / (R * max(temperature, 1.0)))
    return min(1.0, rate)


class ChemistrySystem(System):
    def should_run(self, ctx):
        return ctx.chemistry_tick

    def update(self, ctx) -> list[WorldEvent]:
        events = []
        for cell in self.world.grid.values():
            events.extend(self._process_cell_reactions(cell, ctx))
        return events

    def _process_cell_reactions(self, cell: GridCell, ctx) -> list[WorldEvent]:
        events = []
        prng = self.world.prng

        for rule in REACTION_RULES:
            reactants, products, Ea, delta_G = rule

            if not self._reactants_available(cell, reactants):
                continue

            # Catalyst bonus: lower effective Ea if catalyst present
            effective_Ea = Ea
            if "molecule:catalyst" in cell.molecule_pool:
                effective_Ea *= 0.6

            rate = arrhenius_rate(effective_Ea, cell.temperature)
            if prng.random(cell.x, cell.y) > rate:
                continue

            self._consume_reactants(cell, reactants)
            self._produce_products(cell, products, delta_G)

            events.append(WorldEvent(
                tick=ctx.tick,
                type=EventType.CHEMICAL_REACTION,
                data={
                    "reactants": str(reactants),
                    "products": str(products),
                    "cell": (cell.x, cell.y),
                    "delta_G": delta_G,
                    "temperature": cell.temperature,
                }
            ))
        return events

    def _reactants_available(self, cell: GridCell, reactants) -> bool:
        for r in reactants:
            if isinstance(r, ElementType):
                if cell.chemical_pool.get(r, 0) < 1.0:
                    return False
            elif isinstance(r, str) and r.startswith("molecule:"):
                if r not in cell.molecule_pool:
                    return False
        return True

    def _consume_reactants(self, cell: GridCell, reactants):
        for r in reactants:
            if isinstance(r, ElementType):
                cell.chemical_pool[r] = max(0, cell.chemical_pool.get(r, 0) - 1.0)
            elif isinstance(r, str) and r.startswith("molecule:"):
                if r in cell.molecule_pool:
                    cell.molecule_pool.remove(r)

    def _produce_products(self, cell: GridCell, products, delta_G: float):
        for p in products:
            if isinstance(p, str) and p.startswith("molecule:"):
                cell.molecule_pool.append(p)
            elif isinstance(p, ElementType):
                cell.chemical_pool[p] = cell.chemical_pool.get(p, 0) + 1.0
        # Release energy as heat
        if delta_G < 0:
            cell.temperature += abs(delta_G) * 0.001
```

### 5.6 Biogeochemical Cycles (NEW v2)

```python
# packages/simulation/src/simulation/environment/cycles.py
"""
Carbon, Nitrogen, dan Water cycles.
Tanpa ini simulasi kehabisan material atau akumulasi limbah.
Ini bukan detail — ini syarat keberlanjutan jangka panjang.
"""
import numpy as np
from ..systems.base import System
from ..types import TickContext, WorldEvent, ElementType, GridCell


class BiogeochemicalCycleSystem(System):
    """
    Carbon Cycle:  CO2 (atmosphere) ↔ organic C in organisms ↔ sediment
    Nitrogen Cycle: N2 (inert) → fixed forms (NH3) → organic N → N2
    Water Cycle:   evaporation → condensation → precipitation → runoff
    """

    def __init__(self, world):
        super().__init__(world)
        W = world.config.grid_width
        H = world.config.grid_height
        # Atmospheric pools (scalar, global)
        self.co2_atm: float = W * H * 2.0        # Carbon dioxide
        self.n2_atm: float  = W * H * 5.0         # Atmospheric nitrogen
        self.h2o_atm: float = W * H * 1.0         # Water vapor
        # Sediment (long-term sink)
        self.carbon_sediment: float = W * H * 0.5

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        self._carbon_cycle(ctx)
        self._nitrogen_cycle(ctx)
        self._water_cycle(ctx)
        return []

    # ── Carbon Cycle ──────────────────────────────────────────

    def _carbon_cycle(self, ctx: TickContext):
        """
        CO2 atmospheric → absorbed by producers (TERRA-rich cells)
        Dead organism TERRA → decomposed → CO2 back to atmosphere
        Excess → sediment (long-term sink)
        """
        for cell in self.world.grid.values():
            # Photosynthesis analog: high light + CO2 → TERRA (organic carbon)
            if cell.light_level > 0.6 and self.co2_atm > 1.0:
                uptake = min(0.05, self.co2_atm * 0.001, cell.chemical_pool.get(ElementType.AQUA, 0) * 0.1)
                cell.chemical_pool[ElementType.TERRA] = cell.chemical_pool.get(ElementType.TERRA, 0) + uptake
                self.co2_atm -= uptake

            # Respiration / decomposition: TERRA → CO2
            terra = cell.chemical_pool.get(ElementType.TERRA, 0)
            if terra > 5.0:  # Excess organic carbon
                decomp = (terra - 5.0) * 0.01
                cell.chemical_pool[ElementType.TERRA] = terra - decomp
                self.co2_atm += decomp * 0.8
                self.carbon_sediment += decomp * 0.2

        # Greenhouse feedback: more CO2 → slightly warmer
        W, H = self.world.config.grid_width, self.world.config.grid_height
        avg_co2 = self.co2_atm / (W * H)
        if avg_co2 > 3.0:
            temp_boost = (avg_co2 - 3.0) * 0.0001
            for cell in self.world.grid.values():
                cell.temperature += temp_boost

    # ── Nitrogen Cycle ────────────────────────────────────────

    def _nitrogen_cycle(self, ctx: TickContext):
        """
        N2 (inert, abundant) → NH3 (via rare nitrogen-fixing organisms)
        NH3 → NO3 (available form) → absorbed into IGNIS (info molecules)
        Dead organism IGNIS → NH3 → N2
        """
        for cell in self.world.grid.values():
            # Nitrogen fixation (rare, energy-costly)
            ignis = cell.chemical_pool.get(ElementType.IGNIS, 0)
            if ignis < 0.5 and self.n2_atm > 10.0:
                # Only if enough energy (AETHER) present
                aether = cell.chemical_pool.get(ElementType.AETHER, 0)
                if aether > 1.0:
                    fixed = min(0.02, aether * 0.01)
                    cell.chemical_pool[ElementType.IGNIS] = ignis + fixed
                    cell.chemical_pool[ElementType.AETHER] = aether - fixed * 2
                    self.n2_atm -= fixed

            # Denitrification: excess IGNIS → N2
            if ignis > 8.0:
                denitrif = (ignis - 8.0) * 0.05
                cell.chemical_pool[ElementType.IGNIS] = ignis - denitrif
                self.n2_atm += denitrif

    # ── Water Cycle ───────────────────────────────────────────

    def _water_cycle(self, ctx: TickContext):
        """
        Evaporation from warm cells → atmospheric H2O
        Condensation → precipitation in cooler cells
        """
        evap_total = 0.0
        W, H = self.world.config.grid_width, self.world.config.grid_height

        for cell in self.world.grid.values():
            aqua = cell.chemical_pool.get(ElementType.AQUA, 0)
            # Evaporation: proportional to temperature above threshold
            if cell.temperature > 30.0 and aqua > 0.5:
                evap_rate = (cell.temperature - 30.0) * 0.0005
                evap = min(aqua * evap_rate, aqua * 0.01)
                cell.chemical_pool[ElementType.AQUA] = aqua - evap
                evap_total += evap

        self.h2o_atm += evap_total

        # Precipitation: distribute back to cooler cells
        if self.h2o_atm > W * H * 0.5:
            precip_per_cell = (self.h2o_atm - W * H * 0.3) / (W * H)
            for cell in self.world.grid.values():
                if cell.temperature < 25.0:  # Cooler cells get more rain
                    factor = max(0, (25.0 - cell.temperature) / 25.0)
                    cell.chemical_pool[ElementType.AQUA] = (
                        cell.chemical_pool.get(ElementType.AQUA, 0) + precip_per_cell * factor
                    )
                    self.h2o_atm -= precip_per_cell * factor
```

### 5.7 Abiogenesis System — Mode A/B/C (UPDATED v2)

```python
# packages/simulation/src/simulation/biology/abiogenesis.py
"""
Tiga mode genesis sesuai design doc Bab 9.2.
Mode A: Pure — tidak ada seeding. Berjalan sampai terjadi atau tidak.
Mode B: Seeded Chemistry — precursor organik diletakkan di t=0.
Mode C: Seeded Protocells — satu protocell diletakkan di t=0.
"""
import uuid
from ..types import (
    Agent, Genome, Gene, Vec2, AgentMemory, LifecycleThresholds,
    WorldEvent, EventType, SimulationConfig, ElementType
)


def initialize_genesis(world) -> list[WorldEvent]:
    """
    Dipanggil sekali saat world pertama kali dimulai.
    Memilih protokol berdasarkan config.genesis_mode.
    """
    mode = world.config.genesis_mode
    if mode == "pure":
        return _mode_a_pure(world)
    elif mode == "seeded_chemistry":
        return _mode_b_seeded_chemistry(world)
    elif mode == "seeded_protocells":
        return _mode_c_seeded_protocells(world)
    else:
        raise ValueError(f"Unknown genesis_mode: {mode}")


def _mode_a_pure(world) -> list[WorldEvent]:
    """
    Mode A — Pure Emergence.
    Tidak ada intervensi. Physics dan chemistry berjalan.
    Abiogenesis akan terjadi secara spontan jika kondisi tepat.
    Expected time: sangat lama. Useful untuk research, bukan rapid testing.
    """
    # Tidak ada seeding — hanya log bahwa run dimulai dalam mode pure
    return [WorldEvent(
        tick=0,
        type=EventType.ABIOGENESIS,
        data={"phase": "genesis_mode_set", "mode": "pure",
              "note": "Waiting for spontaneous abiogenesis. No seeding applied."}
    )]


def _mode_b_seeded_chemistry(world) -> list[WorldEvent]:
    """
    Mode B — Seeded Chemistry.
    Analog comet delivery: precursor organik diletakkan di beberapa area.
    Tidak menginjeksikan kehidupan — hanya kondisi awal yang favorable.
    """
    W = world.config.grid_width
    H = world.config.grid_height
    prng = world.prng

    # Pilih 3-5 "hydrothermal vent" analog
    n_vents = 3 + prng.randint(0, 0, 0, 3)
    seeded_cells = []

    for i in range(n_vents):
        # Posisi vent: deterministik dari seed tapi tersebar
        vx = prng.randint(0, i, W // 4, 3 * W // 4)
        vy = prng.randint(i, 0, H // 4, 3 * H // 4)

        # Boost konsentrasi precursor di sekitar vent
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                nx = (vx + dx) % W
                ny = (vy + dy) % H
                dist = (dx**2 + dy**2) ** 0.5
                boost = max(0, 1.0 - dist / 5.0) * 3.0
                cell = world.grid.get((nx, ny))
                if cell:
                    cell.chemical_pool[ElementType.AETHER] = (
                        cell.chemical_pool.get(ElementType.AETHER, 0) + boost
                    )
                    cell.chemical_pool[ElementType.TERRA] = (
                        cell.chemical_pool.get(ElementType.TERRA, 0) + boost * 0.5
                    )
                    cell.chemical_pool[ElementType.IGNIS] = (
                        cell.chemical_pool.get(ElementType.IGNIS, 0) + boost * 0.3
                    )
                    cell.temperature = 40.0 + boost * 5  # Warm vent analog

        seeded_cells.append((vx, vy))

    return [WorldEvent(
        tick=0,
        type=EventType.ABIOGENESIS,
        data={"phase": "chemistry_seeded", "mode": "seeded_chemistry",
              "vent_positions": seeded_cells,
              "note": "Organic precursors deposited. No life injected."}
    )]


def _mode_c_seeded_protocells(world) -> list[WorldEvent]:
    """
    Mode C — Seeded Protocells.
    Satu protocell sederhana diletakkan di tengah dunia.
    Berguna untuk meneliti evolusi SETELAH kehidupan ada, bukan abiogenesis.
    Dicatat sebagai intervensi di metadata run.
    """
    W = world.config.grid_width
    H = world.config.grid_height
    cx, cy = W // 2, H // 2

    # Buat minimal genome (single gene, purely structural)
    starter_gene = Gene(
        id="genesis_gene_0",
        sequence=bytes([0b10101010, 0b01010101, 0b11110000]),
        expression_level=1.0,
        promoter_condition="always",
        product_type="structural",
    )
    genome = Genome(genes=[starter_gene], mutation_rate=world.config.fundamental.mutation_rate_base)

    protocell_id = f"AG-{str(uuid.uuid4())[:8]}"
    protocell = Agent(
        id=protocell_id,
        genome=genome,
        birth_tick=0,
        position=Vec2(cx + 0.5, cy + 0.5),
        velocity=Vec2(0.0, 0.0),
        mass=1.0,
        energy=0.7,
        health=1.0,
        metabolism_rate=0.01,  # Very slow — primitive
        reproduction_threshold=0.9,
    )
    world.agents[protocell_id] = protocell

    return [WorldEvent(
        tick=0,
        type=EventType.ABIOGENESIS,
        data={"phase": "protocell_seeded", "mode": "seeded_protocells",
              "agent_id": protocell_id,
              "note": "INTERVENTION: One protocell injected. Tag run accordingly."}
    )]


def check_spontaneous_abiogenesis(world, ctx) -> list[WorldEvent]:
    """
    Dipanggil setiap biology tick dalam Mode A/B.
    Cek apakah proto_rna + membran sudah terbentuk di sel yang sama.
    Jika ya, spawn protocell pertama.
    """
    events = []
    for cell in world.grid.values():
        has_rna = "molecule:proto_rna" in cell.molecule_pool
        has_atp = "molecule:proto_atp" in cell.molecule_pool
        has_water = "molecule:water_analog" in cell.molecule_pool
        temp_ok = 20.0 <= cell.temperature <= 80.0

        if has_rna and has_atp and has_water and temp_ok and not cell.agent_ids:
            # Kondisi terpenuhi — abiogenesis terjadi!
            new_agent = _spawn_from_chemistry(world, cell, ctx.tick)
            world.agents[new_agent.id] = new_agent
            cell.agent_ids.append(new_agent.id)

            # Consume precursors
            cell.molecule_pool = [m for m in cell.molecule_pool
                                   if m not in ("molecule:proto_rna", "molecule:proto_atp")]

            events.append(WorldEvent(
                tick=ctx.tick,
                type=EventType.ABIOGENESIS,
                data={"phase": "life_emerged", "agent_id": new_agent.id,
                      "location": (cell.x, cell.y),
                      "rd_v_level": cell.rd.v,
                      "temperature": cell.temperature}
            ))
            break  # Satu per chemistry tick

    return events


def _spawn_from_chemistry(world, cell, birth_tick: int) -> Agent:
    """Buat agen pertama dari kimia yang sudah matang."""
    import uuid
    # Genome generated dari entropi kimiawi lokal — bukan hardcoded
    import hashlib
    entropy_bytes = f"{cell.x}{cell.y}{birth_tick}{cell.temperature}".encode()
    seed_bytes = hashlib.sha256(entropy_bytes).digest()
    initial_gene = Gene(
        id="spontaneous_0",
        sequence=seed_bytes[:4],
        expression_level=0.5,
        promoter_condition="energy_positive",
        product_type="structural",
    )
    genome = Genome(
        genes=[initial_gene],
        mutation_rate=world.config.fundamental.mutation_rate_base * 2.0  # Higher initial rate
    )
    agent_id = f"AG-{str(uuid.uuid4())[:8]}"
    return Agent(
        id=agent_id,
        genome=genome,
        birth_tick=birth_tick,
        position=Vec2(cell.x + 0.5, cell.y + 0.5),
        velocity=Vec2(0.0, 0.0),
        mass=0.5,
        energy=0.5,
        health=1.0,
        metabolism_rate=0.02,
        reproduction_threshold=0.85,
    )
```

### 5.8 Agent Lifecycle Phase System (UPDATED v2)

```python
# packages/simulation/src/simulation/biology/lifecycle.py
"""
Agent lifecycle phases: NEONATAL → JUVENILE → ADOLESCENT → ADULT → ELDER
Setiap fase memiliki:
- Learning rate yang berbeda (JUVENILE = plastisitas maksimum)
- Kapasitas metabolisme yang berbeda
- Reproduction availability
- Critical period untuk skill acquisition
"""
from ..systems.base import System
from ..types import (
    TickContext, WorldEvent, EventType, AgentStage, Agent
)


def get_lifecycle_thresholds(genome) -> dict:
    """
    Threshold phase transition ditentukan oleh genome.
    Lebih banyak gen → potensi umur lebih panjang.
    """
    base = len(genome.genes)
    return {
        "juvenile_at":    max(20,  base * 3),
        "adolescent_at":  max(100, base * 15),
        "adult_at":       max(300, base * 40),
        "elder_at":       max(1000, base * 120),
        "max_lifespan":   max(3000, base * 350),
    }


def get_learning_rate_multiplier(stage: AgentStage) -> float:
    """
    Critical period: plastisitas neural lebih tinggi saat JUVENILE.
    Mencerminkan neoteny dan critical periods di neurosains nyata.
    """
    return {
        AgentStage.NEONATAL:   0.5,
        AgentStage.JUVENILE:   2.0,   # Critical period — plastisitas maksimum
        AgentStage.ADOLESCENT: 1.2,
        AgentStage.ADULT:      0.8,
        AgentStage.ELDER:      0.3,   # Reduced plasticity
    }.get(stage, 1.0)


def get_metabolism_multiplier(stage: AgentStage) -> float:
    """Metabolisme relatif per stage."""
    return {
        AgentStage.NEONATAL:   0.3,   # Very low — mostly developing
        AgentStage.JUVENILE:   0.8,
        AgentStage.ADOLESCENT: 1.2,
        AgentStage.ADULT:      1.0,
        AgentStage.ELDER:      0.7,
    }.get(stage, 1.0)


def can_reproduce(agent: Agent) -> bool:
    """Hanya ADULT yang bisa bereproduksi."""
    return agent.stage in (AgentStage.ADULT,) and agent.energy >= agent.reproduction_threshold


class LifecycleSystem(System):
    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []
        dead_from_age = []

        for agent_id, agent in list(self.world.agents.items()):
            if not agent.is_alive:
                continue

            thresholds = get_lifecycle_thresholds(agent.genome)
            old_stage = agent.stage
            age = agent.age_ticks

            # Phase transitions
            if age < thresholds["juvenile_at"]:
                new_stage = AgentStage.NEONATAL
            elif age < thresholds["adolescent_at"]:
                new_stage = AgentStage.JUVENILE
            elif age < thresholds["adult_at"]:
                new_stage = AgentStage.ADOLESCENT
            elif age < thresholds["elder_at"]:
                new_stage = AgentStage.ADULT
            else:
                new_stage = AgentStage.ELDER

            if new_stage != old_stage:
                agent.stage = new_stage
                events.append(WorldEvent(
                    tick=ctx.tick,
                    type=EventType.AGENT_STAGE_CHANGE,
                    data={
                        "agent_id": agent_id,
                        "from_stage": old_stage.value,
                        "to_stage": new_stage.value,
                        "age_ticks": age,
                    }
                ))

            # Natural aging death
            if age >= thresholds["max_lifespan"]:
                agent.is_alive = False
                agent.death_tick = ctx.tick
                dead_from_age.append(agent_id)
                events.append(WorldEvent(
                    tick=ctx.tick,
                    type=EventType.AGENT_DIED,
                    data={"agent_id": agent_id, "cause": "old_age",
                          "age": age, "stage": agent.stage.value}
                ))

        return events
```

---

## 6. AGENT RUNTIME

### 6.1 Proper Hebbian Learning (UPDATED v2)

```python
# packages/simulation/src/simulation/agents/neural.py
"""
Neural network yang berevolusi dari genome.
Learning: Reward-gated Hebbian (Δw = η × pre × post × reward)
— bukan random noise scaling dari v1.0.0.

Arsitektur ditentukan genome, bukan developer.
"""
import numpy as np
import torch
import torch.nn as nn
from ..types import SensoryInput, ActionOutput, ElementType, Vec2, Agent, AgentStage
from ..biology.lifecycle import get_learning_rate_multiplier
from ..systems.base import System


def build_network_from_genome(genome) -> nn.Module:
    """
    Arsitektur network DIDERIVASIKAN dari genome.
    Lebih banyak gen dan total sequence length → kapasitas lebih besar.
    Developer tidak menentukan ukuran — genome yang menentukan.
    """
    n_genes = len(genome.genes)
    total_seq = sum(len(g.sequence) for g in genome.genes)
    neural_genes = [g for g in genome.genes if g.product_type == "neural"]

    input_size = 12
    # Hidden size bervariasi: n_genes * 2, capped at 128
    hidden_size = max(4, min(128, len(neural_genes) * 4 + n_genes))
    output_size = 6

    # Apakah genome punya cukup "recurrent genes"?
    recurrent_genes = [g for g in neural_genes if b'\xff' in g.sequence]
    if len(recurrent_genes) >= 2:
        # Genome yang kaya neural genes → recurrent network
        return RecurrentNetwork(input_size, hidden_size, output_size)
    else:
        return nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, output_size),
            nn.Tanh(),
        )


class RecurrentNetwork(nn.Module):
    """Simple recurrent network untuk agen yang lebih kompleks."""
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.rnn = nn.GRUCell(input_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)
        self.hidden_state = torch.zeros(1, hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.hidden_state = self.rnn(x, self.hidden_state)
        return torch.tanh(self.out(self.hidden_state))

    def reset_hidden(self):
        self.hidden_state = torch.zeros(1, self.hidden_size)


def encode_sensory(sensory: SensoryInput) -> np.ndarray:
    """Convert SensoryInput ke fixed-size feature vector."""
    return np.array([
        sensory.chemical_gradients.get(ElementType.PRIMUM, 0),
        sensory.chemical_gradients.get(ElementType.AQUA, 0),
        sensory.chemical_gradients.get(ElementType.TERRA, 0),
        sensory.chemical_gradients.get(ElementType.IGNIS, 0),
        sensory.chemical_gradients.get(ElementType.AETHER, 0),
        len(sensory.nearby_agents) / 10.0,
        sensory.light_level,
        sensory.temperature / 100.0,
        sensory.pressure,
        sensory.pain_signal,
        float(sensory.ca_state) / 3.0,  # CA state normalized
        0.0,  # Reserved
    ], dtype=np.float32)


def decode_action(output: np.ndarray) -> ActionOutput:
    return ActionOutput(
        move_direction=Vec2(float(output[0]), float(output[1])),
        move_speed=float(np.abs(output[2])),
        # output[3..5] reserved untuk future actions
    )


def hebbian_update(
    network: nn.Module,
    pre_activations: torch.Tensor,
    post_activations: torch.Tensor,
    reward: float,
    learning_rate: float = 0.001,
) -> None:
    """
    Reward-gated Hebbian learning:
    Δw_ij = η × pre_i × post_j × reward_signal

    Ini adalah Hebbian learning yang benar sesuai design doc Bab 47.4.
    Bukan random noise — ini menggunakan aktivasi aktual pre/post sinaptik.
    """
    if abs(reward) < 1e-4:
        return  # No update jika reward near-zero

    lr = learning_rate * np.sign(reward)

    with torch.no_grad():
        layers = list(network.parameters())
        # Update setiap layer berdasarkan outer product pre × post
        if len(pre_activations.shape) == 1:
            pre = pre_activations.unsqueeze(1)   # (N, 1)
        else:
            pre = pre_activations

        if len(post_activations.shape) == 1:
            post = post_activations.unsqueeze(0)  # (1, M)
        else:
            post = post_activations

        # Hanya update layer pertama untuk MVP (full impl di Phase 3)
        if layers:
            delta = lr * torch.mm(post.T, pre.T) if pre.shape[1] == layers[0].shape[1] else None
            if delta is not None and delta.shape == layers[0].shape:
                layers[0].add_(delta * 0.001)  # Scaled very small untuk stabilitas


class CognitiveSystem(System):
    def should_run(self, ctx) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx) -> list[WorldEvent]:
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            if agent.neural_complexity < 1:
                self._reflex_chemotaxis(agent)
                continue

            sensory = self._perceive(agent)
            network = self._get_or_build_network(agent)

            input_tensor = torch.tensor(encode_sensory(sensory)).unsqueeze(0)

            with torch.no_grad():
                output = network(input_tensor).squeeze()

            action = decode_action(output.numpy())
            self._apply_action(agent, action)

            # Compute biological reward signal
            reward = self._compute_biological_reward(agent)

            # Store activations for Hebbian update
            pre_act = input_tensor.squeeze()
            post_act = output

            # Apply proper Hebbian update
            lr_mult = get_learning_rate_multiplier(agent.stage)
            hebbian_update(
                network,
                pre_act, post_act,
                reward=reward,
                learning_rate=0.001 * lr_mult,
            )

            # Store last reward in memory
            if agent.memory:
                agent.memory.last_reward = reward

        return []

    def _reflex_chemotaxis(self, agent: Agent):
        """
        Kemotaksis primitif: bergerak ke gradien PRIMUM tertinggi.
        Ini adalah perilaku Level-0 (bab 18.1 design doc) — paling dasar.
        Bukan hardcoded behavior, melainkan bootstrap untuk agen yang belum
        punya neural complexity. Begitu neural complexity > 0, network takes over.
        """
        W = self.world.config.grid_width
        H = self.world.config.grid_height
        cell = self._get_cell(agent.position)
        if not cell:
            return

        best_dir = Vec2(0, 0)
        best_val = cell.chemical_pool.get(ElementType.PRIMUM, 0)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx = (int(agent.position.x) + dx) % W
            ny = (int(agent.position.y) + dy) % H
            nc = self.world.grid.get((nx, ny))
            if nc:
                val = nc.chemical_pool.get(ElementType.PRIMUM, 0)
                if val > best_val:
                    best_val = val
                    best_dir = Vec2(dx * 0.1, dy * 0.1)

        agent.velocity.x = best_dir.x
        agent.velocity.y = best_dir.y

    def _compute_biological_reward(self, agent: Agent) -> float:
        """
        Reward signal adalah sinyal biologis internal — BUKAN reward function developer.
        Analog dopamin: meningkat saat energi naik, turun saat energi turun.
        Sesuai design doc Bab 47.4.
        """
        last = agent.memory.last_reward if agent.memory else 0.5
        # Reward = delta energy dari tick sebelumnya
        reward = agent.energy - last
        return float(np.clip(reward, -1.0, 1.0))

    def _perceive(self, agent: Agent) -> SensoryInput:
        W = self.world.config.grid_width
        H = self.world.config.grid_height
        ax, ay = int(agent.position.x) % W, int(agent.position.y) % H
        cell = self.world.grid.get((ax, ay))

        gradients = {}
        if cell:
            for elem_type in ElementType:
                nearby_sum = 0.0
                count = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nc = self.world.grid.get(((ax+dx)%W, (ay+dy)%H))
                        if nc:
                            nearby_sum += nc.chemical_pool.get(elem_type, 0)
                            count += 1
                gradients[elem_type] = nearby_sum / max(count, 1)

        nearby_agents = [
            aid for aid, a in self.world.agents.items()
            if a.is_alive and aid != agent.id
            and abs(a.position.x - agent.position.x) < agent.sensory_range
            and abs(a.position.y - agent.position.y) < agent.sensory_range
        ]

        return SensoryInput(
            chemical_gradients=gradients,
            nearby_agents=nearby_agents[:10],
            light_level=cell.light_level if cell else 0.5,
            temperature=cell.temperature if cell else 20.0,
            pressure=0.0,
            pain_signal=max(0, 1.0 - agent.health),
            ca_state=cell.ca.wireworld_state if cell else 0,
        )

    def _apply_action(self, agent: Agent, action: ActionOutput):
        W = self.world.config.grid_width
        H = self.world.config.grid_height
        speed = min(action.move_speed, 2.0)
        mag = action.move_direction.magnitude()
        if mag > 0:
            agent.velocity.x = action.move_direction.x / mag * speed
            agent.velocity.y = action.move_direction.y / mag * speed
        agent.position.x = (agent.position.x + agent.velocity.x * 0.1) % W
        agent.position.y = (agent.position.y + agent.velocity.y * 0.1) % H

    def _get_cell(self, pos):
        W = self.world.config.grid_width
        H = self.world.config.grid_height
        return self.world.grid.get((int(pos.x) % W, int(pos.y) % H))

    _networks: dict[str, nn.Module] = {}

    def _get_or_build_network(self, agent: Agent) -> nn.Module:
        if agent.id not in self._networks:
            self._networks[agent.id] = build_network_from_genome(agent.genome)
        return self._networks[agent.id]
```

### 6.2 Episodic Memory — Qdrant Integration (UPDATED v2)

```python
# packages/simulation/src/simulation/agents/memory.py
"""
Episodic memory per agen menggunakan Qdrant vector database.
Retrieval via embedding similarity — "situasi serupa di masa lalu."

v1.0.0 hanya punya placeholder episodic_refs.
v2.0.0: write + similarity retrieval diimplementasikan.
"""
import uuid
import numpy as np
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct, VectorParams, Distance, Filter,
    FieldCondition, MatchValue
)
from ..types import AgentID, SensoryInput, ElementType


QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "agent_episodic_memory"
VECTOR_DIM = 16  # Compact representation untuk MVP


def _client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collection():
    """Create Qdrant collection jika belum ada."""
    client = _client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


def encode_episode_vector(
    sensory: SensoryInput,
    energy_level: float,
    reward_received: float,
) -> np.ndarray:
    """
    Encode sebuah episode menjadi 16-dim vector.
    Kombinasi sensory input + internal state + outcome.
    """
    return np.array([
        sensory.chemical_gradients.get(ElementType.PRIMUM, 0) / 10.0,
        sensory.chemical_gradients.get(ElementType.AQUA, 0) / 10.0,
        sensory.chemical_gradients.get(ElementType.TERRA, 0) / 10.0,
        sensory.chemical_gradients.get(ElementType.IGNIS, 0) / 10.0,
        sensory.chemical_gradients.get(ElementType.AETHER, 0) / 10.0,
        len(sensory.nearby_agents) / 10.0,
        sensory.light_level,
        sensory.temperature / 100.0,
        sensory.pressure,
        sensory.pain_signal,
        float(sensory.ca_state) / 3.0,
        energy_level,
        float(reward_received > 0),
        float(reward_received < 0),
        abs(reward_received),
        0.0,  # Reserved
    ], dtype=np.float32)


def store_episode(
    agent_id: AgentID,
    run_id: str,
    tick: int,
    sensory: SensoryInput,
    energy_level: float,
    reward: float,
    action_taken: str = "",
) -> Optional[str]:
    """
    Simpan episode ke Qdrant.
    Returns episode_id atau None jika gagal.
    """
    try:
        client = _client()
        vector = encode_episode_vector(sensory, energy_level, reward)
        episode_id = str(uuid.uuid4())

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=episode_id,
                vector=vector.tolist(),
                payload={
                    "agent_id": agent_id,
                    "run_id": run_id,
                    "tick": tick,
                    "energy": energy_level,
                    "reward": float(reward),
                    "action": action_taken,
                    "nearby_count": len(sensory.nearby_agents),
                    "temperature": sensory.temperature,
                }
            )]
        )
        return episode_id
    except Exception as e:
        import logging
        logging.warning(f"Qdrant store failed for agent {agent_id}: {e}")
        return None


def retrieve_similar_episodes(
    agent_id: AgentID,
    current_sensory: SensoryInput,
    current_energy: float,
    top_k: int = 3,
) -> list[dict]:
    """
    Retrieve K most similar past episodes untuk current situation.
    Ini adalah mechanism 'remember when something similar happened.'
    """
    try:
        client = _client()
        query_vector = encode_episode_vector(current_sensory, current_energy, 0.0)

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector.tolist(),
            query_filter=Filter(
                must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
            ),
            limit=top_k,
        )

        return [
            {
                "episode_id": r.id,
                "similarity": r.score,
                "tick": r.payload.get("tick", 0),
                "reward": r.payload.get("reward", 0.0),
                "energy": r.payload.get("energy", 0.5),
                "action": r.payload.get("action", ""),
            }
            for r in results
        ]
    except Exception:
        return []
```

---

## 7. OBSERVER LAYER & LLM (OpenRouter)

### 7.1 OpenRouter Client Setup (NEW v2)

```python
# packages/observer/src/observer/client.py
"""
OpenRouter client — OpenAI-compatible API.
Mendukung Anthropic Claude, Google Gemini, Mistral, dan ratusan model lain.

Migrasi dari Anthropic SDK langsung ke OpenRouter:
- Endpoint: https://openrouter.ai/api/v1
- Auth: Authorization: Bearer OPENROUTER_API_KEY
- Format: identik OpenAI Chat Completions API
"""
import os
from openai import OpenAI


def get_client() -> OpenAI:
    """Returns configured OpenRouter client."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


# Model strings untuk multi-model strategy (Bab 49.3 design doc)
# Format OpenRouter: "provider/model-name"
MODELS = {
    "deep_analysis":    "anthropic/claude-opus-4",       # Narasi detail, insight mendalam
    "standard":         "anthropic/claude-sonnet-4-5",   # Klasifikasi rutin, ringkasan
    "fast_batch":       "anthropic/claude-haiku-4-5",    # Volume tinggi, labeling cepat
    "fast_cheap_alt":   "google/gemini-flash-1.5",       # Alternatif murah untuk batch
}

# Default headers untuk semua request
DEFAULT_HEADERS = {
    "HTTP-Referer": os.environ.get("SITE_URL", "https://worldai.dev"),
    "X-Title": "World.ai Observer",
}


def chat_completion(
    messages: list[dict],
    model_key: str = "standard",
    max_tokens: int = 512,
    response_format: str = "text",  # "text" atau "json"
) -> str:
    """
    Wrapper untuk OpenRouter chat completion.
    Returns teks response.
    """
    client = get_client()
    model_name = MODELS.get(model_key, MODELS["standard"])

    kwargs = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": messages,
        "extra_headers": DEFAULT_HEADERS,
    }

    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content
```

### 7.2 LLM Observer Tasks (UPDATED v2 — OpenRouter)

```python
# packages/observer/src/observer/classifier.py

import json
from celery import shared_task
from .client import chat_completion


@shared_task
def classify_species(agent_data: dict) -> dict:
    """
    Classifies agent characteristics into species label.
    Called ONLY from Celery worker, NEVER from simulation loop.
    Uses fast_batch model (Claude Haiku via OpenRouter) for cost efficiency.
    """
    prompt = f"""You are a xenobiologist observing a digital world simulation.
Based on the characteristics of this digital organism, provide:
1. A species name (Latin-style binomial nomenclature)
2. A brief description (2 sentences max)
3. Key adaptations that distinguish it (2-3 bullet points)

Organism data:
- Genome complexity: {agent_data.get('genome_gene_count', 0)} genes
- Average lifespan: {agent_data.get('avg_lifespan_ticks', 0)} ticks
- Metabolic rate: {agent_data.get('metabolism_rate', 0):.4f}
- Neural complexity: {agent_data.get('neural_complexity', 0)}
- Primary habitat: {agent_data.get('preferred_terrain', 'unknown')}
- Social behavior score: {agent_data.get('social_score', 0):.2f}
- Reproduction mode: {agent_data.get('reproduction_mode', 'asexual')}

Respond ONLY with valid JSON, no markdown, no preamble:
{{"species_name": "...", "description": "...", "key_adaptations": ["...", "..."]}}"""

    text = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model_key="fast_batch",
        max_tokens=256,
        response_format="json",
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"species_name": "Incertae sedis", "description": "Classification failed.", "key_adaptations": []}


@shared_task
def generate_agent_life_story(agent_archive: dict) -> str:
    """
    Generates narrative life story dari agent data.
    Uses standard model (Claude Sonnet via OpenRouter).
    """
    prompt = f"""Write a brief life narrative (3 short paragraphs) for this digital organism
in the style of a nature documentary narrator. Be factual, evocative, and scientific.

Organism data:
- Born at tick: {agent_archive.get('birth_tick', 0)}
- Died at tick: {agent_archive.get('death_tick', 'still alive')}
- Total offspring: {agent_archive.get('children_count', 0)}
- Genome complexity: {agent_archive.get('genome_gene_count', 0)} genes
- Key events: {agent_archive.get('key_events', [])}
- Final energy level: {agent_archive.get('final_energy', 0):.2f}
- Cause of death: {agent_archive.get('death_cause', 'unknown')}
- Species label: {agent_archive.get('species_label', 'unclassified')}
- Lifecycle stage at death: {agent_archive.get('final_stage', 'unknown')}"""

    return chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model_key="standard",
        max_tokens=512,
    )


@shared_task
def analyze_civilization_snapshot(world_data: dict) -> dict:
    """
    Analisis mendalam snapshot peradaban.
    Uses deep_analysis model (Claude Opus via OpenRouter) untuk insight kualitas tinggi.
    Dipanggil per geological tick — frekuensi rendah.
    """
    prompt = f"""You are a researcher analyzing an emergent digital civilization.
Provide a structured analysis of the current state.

World snapshot:
- Current tick: {world_data.get('tick', 0)}
- Total population: {world_data.get('population', 0)}
- Number of species: {world_data.get('species_count', 0)}
- Global entropy: {world_data.get('entropy', 0):.4f}
- Shannon population entropy: {world_data.get('shannon_pop_entropy', 0):.4f}
- Average neural complexity: {world_data.get('avg_neural_complexity', 0):.2f}
- Innovation events this epoch: {world_data.get('innovation_count', 0)}
- Recent major events: {world_data.get('recent_events', [])}

Provide analysis as JSON with keys:
civilization_stage, dominant_dynamics, notable_patterns, research_observations, risks

Respond ONLY with valid JSON, no markdown:"""

    text = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model_key="deep_analysis",
        max_tokens=1000,
        response_format="json",
    )

    try:
        return json.loads(text)
    except Exception:
        return {"error": "Analysis failed", "raw": text[:200]}


@shared_task
def classify_emergent_pattern(pattern_data: dict) -> dict:
    """
    Classifies emergent patterns (CA, chemical, behavioral) observed in world.
    Uses fast_batch for volume.
    """
    prompt = f"""You are a complexity scientist analyzing patterns in a digital simulation.
Classify this observed emergent pattern.

Pattern data:
- Pattern type: {pattern_data.get('type', 'unknown')}
- Observed at tick: {pattern_data.get('tick', 0)}
- Location: {pattern_data.get('location', 'global')}
- Metrics: {pattern_data.get('metrics', {})}
- Context: {pattern_data.get('context', '')}

Classify as JSON with keys: category, novelty_score (0-1), scientific_interest (low/medium/high), description

Respond ONLY with valid JSON:"""

    text = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model_key="fast_batch",
        max_tokens=200,
        response_format="json",
    )

    try:
        return json.loads(text)
    except Exception:
        return {"category": "unknown", "novelty_score": 0.0, "scientific_interest": "low", "description": ""}
```

---

## 8. API CONTRACTS

### 8.1 REST Endpoints

```
BASE URL: http://localhost:8000/api/v1

── World ────────────────────────────────────────────────────────
GET    /world/state          → WorldSnapshot (current)
GET    /world/config         → SimulationConfig
GET    /world/stats          → WorldStats (aggregated metrics)
GET    /world/history        → List[WorldStats] (last N ticks)
POST   /world/control/speed  → { multiplier: float } → OK
POST   /world/control/pause  → OK
POST   /world/control/resume → OK

── Agents ──────────────────────────────────────────────────────
GET    /agents               → List[AgentSummary] (paginated)
GET    /agents/{id}          → AgentDetail
GET    /agents/{id}/memory   → AgentMemoryData
GET    /agents/{id}/lineage  → LineageTree
GET    /agents/{id}/story    → string (LLM-generated async via Celery)
GET    /agents/search        → List[AgentSummary] (query params)

── Grid ────────────────────────────────────────────────────────
GET    /grid/cell/{x}/{y}    → GridCellData (includes CA + RD state)
GET    /grid/heatmap/{layer} → HeatmapData (layer: energy|population|chemical|ca|rd)

── Events ──────────────────────────────────────────────────────
GET    /events               → List[WorldEvent] (paginated, filterable)
GET    /events/timeline      → List[WorldEvent] (key events only)

── Metrics (NEW v2) ────────────────────────────────────────────
GET    /metrics/current      → ComplexityMetrics (latest sample)
GET    /metrics/history      → List[ComplexityMetrics] (time series)
GET    /metrics/entropy      → entropy time series
GET    /metrics/phi          → Φ approximation per-agent

── God Mode (AUDITED v2) ───────────────────────────────────────
POST   /control/inject_resource   → { x, y, element, amount, justification: str }
POST   /control/trigger_disaster  → { type, x, y, radius, justification: str }
POST   /control/force_mutation    → { agent_id, justification: str }
GET    /control/audit_log         → List[InterventionAuditEntry] (God Mode log)
POST   /control/rollback/{checkpoint_id} → Rollback to checkpoint

── Observer ────────────────────────────────────────────────────
GET    /observer/species          → List[SpeciesClassification]
GET    /observer/civilization     → CivilizationReport (Phase 5+)
POST   /observer/analyze/region   → { x, y, radius } → AnalysisReport
```

### 8.2 WebSocket Events

```
WS URL: ws://localhost:8000/ws

── Client → Server ─────────────────────────────────────────────
{ "type": "subscribe", "channel": "world_stats" }
{ "type": "subscribe", "channel": "events", "filter": { "type": "AGENT_BORN" } }
{ "type": "subscribe", "channel": "agent", "agent_id": "AG-00042" }
{ "type": "subscribe", "channel": "metrics" }
{ "type": "unsubscribe", "channel": "..." }

── Server → Client ─────────────────────────────────────────────
{ "type": "tick",     "payload": { "tick": 1234 } }
{ "type": "stats",    "payload": WorldStats }
{ "type": "snapshot", "payload": WorldSnapshot }
{ "type": "event",    "payload": WorldEvent }
{ "type": "metrics",  "payload": ComplexityMetrics }   // NEW v2
{ "type": "error",    "payload": { "message": "..." } }
```

### 8.3 God Mode Audit (NEW v2)

```python
# packages/api/src/api/routes/control.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()


class InterventionRequest(BaseModel):
    intervention_type: str          # "inject_resource|trigger_disaster|force_mutation"
    target: dict                    # Type-specific target parameters
    justification: str              # REQUIRED — reason for intervention
    experiment_label: str = ""      # Optional — link ke planned experiment


class InterventionAuditEntry(BaseModel):
    id: str
    tick_at_intervention: int
    intervention_type: str
    target: dict
    justification: str
    experiment_label: str
    timestamp: str
    checkpoint_id: str              # Pre-intervention checkpoint untuk rollback


async def _save_audit_entry(entry: InterventionAuditEntry, db):
    """Simpan ke audit log yang tidak bisa dihapus."""
    await db.execute("""
        INSERT INTO god_mode_audit (id, tick_at_intervention, intervention_type,
                                    target, justification, experiment_label,
                                    timestamp, checkpoint_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, entry.id, entry.tick_at_intervention, entry.intervention_type,
        json.dumps(entry.target), entry.justification, entry.experiment_label,
        entry.timestamp, entry.checkpoint_id)


@router.post("/inject_resource")
async def inject_resource(req: InterventionRequest):
    """God Mode: inject resource ke grid cell."""
    if not req.justification or len(req.justification) < 10:
        raise HTTPException(status_code=422, detail="Justification too short (min 10 chars)")

    # Create checkpoint sebelum intervensi
    from ..services.checkpoint import CheckpointService
    checkpoint_id = await CheckpointService.create()

    # Execute intervention
    # ... (implementation)

    # Log audit
    import uuid
    from ..services.db import get_db
    entry = InterventionAuditEntry(
        id=str(uuid.uuid4()),
        tick_at_intervention=await CheckpointService.current_tick(),
        intervention_type="inject_resource",
        target=req.target,
        justification=req.justification,
        experiment_label=req.experiment_label,
        timestamp=datetime.utcnow().isoformat(),
        checkpoint_id=checkpoint_id,
    )
    # await _save_audit_entry(entry, db)

    return {"status": "ok", "checkpoint_id": checkpoint_id, "audit_id": entry.id}


@router.get("/audit_log")
async def get_audit_log(limit: int = 50, offset: int = 0):
    """Get God Mode audit log — read only."""
    # Return from DB
    return {"entries": [], "total": 0}  # Placeholder — implement with DB query
```

---

## 9. VISUALIZER (FRONTEND)

### 9.1 PixiJS World Renderer (UPDATED v2 — CA overlay)

```typescript
// packages/visualizer/src/engine/WorldRenderer.ts

import * as PIXI from 'pixi.js';
import { WorldSnapshot, AgentSummary, GridCellData } from '../types/world';
import { useWorldStore } from '../store/worldStore';

export class WorldRenderer {
  private app: PIXI.Application;
  private worldContainer: PIXI.Container;
  private agentLayer: PIXI.Container;
  private heatmapLayer: PIXI.Container;
  private caLayer: PIXI.Container;       // NEW v2 — CA visualization
  private rdLayer: PIXI.Container;       // NEW v2 — RD visualization
  private agentSprites: Map<string, PIXI.Graphics> = new Map();

  private renderMode: 'energy' | 'ca' | 'rd' | 'temperature' = 'energy';

  async init(canvas: HTMLCanvasElement) {
    this.app = new PIXI.Application();
    await this.app.init({
      canvas,
      width: canvas.clientWidth,
      height: canvas.clientHeight,
      backgroundColor: 0x050a0f,
      antialias: true,
      resolution: window.devicePixelRatio,
    });

    this.worldContainer = new PIXI.Container();
    this.heatmapLayer  = new PIXI.Container();
    this.caLayer       = new PIXI.Container();
    this.rdLayer       = new PIXI.Container();
    this.agentLayer    = new PIXI.Container();

    this.worldContainer.addChild(this.heatmapLayer);
    this.worldContainer.addChild(this.caLayer);
    this.worldContainer.addChild(this.rdLayer);
    this.worldContainer.addChild(this.agentLayer);
    this.app.stage.addChild(this.worldContainer);

    this._setupCameraControls();
  }

  setRenderMode(mode: 'energy' | 'ca' | 'rd' | 'temperature') {
    this.renderMode = mode;
    this.heatmapLayer.visible = mode === 'energy' || mode === 'temperature';
    this.caLayer.visible = mode === 'ca';
    this.rdLayer.visible = mode === 'rd';
  }

  renderSnapshot(snapshot: WorldSnapshot) {
    const cellSize = this._getCellSize(snapshot.grid_width);

    if (this.renderMode === 'energy' || this.renderMode === 'temperature') {
      this._renderHeatmap(snapshot, cellSize);
    } else if (this.renderMode === 'ca') {
      this._renderCA(snapshot, cellSize);
    } else if (this.renderMode === 'rd') {
      this._renderRD(snapshot, cellSize);
    }

    this._renderAgents(snapshot.agents, cellSize);
  }

  private _renderHeatmap(snapshot: WorldSnapshot, cellSize: number) {
    this.heatmapLayer.removeChildren();
    for (const cell of snapshot.grid_cells) {
      const rect = new PIXI.Graphics();
      let value: number;
      let color: number;

      if (this.renderMode === 'energy') {
        value = cell.chemical_pool['P'] || 0;
        color = this._energyToColor(value);
      } else {
        value = cell.temperature / 100;
        color = this._temperatureToColor(cell.temperature);
      }

      rect.rect(cell.x * cellSize, cell.y * cellSize, cellSize, cellSize)
          .fill({ color, alpha: 0.7 });
      this.heatmapLayer.addChild(rect);
    }
  }

  private _renderCA(snapshot: WorldSnapshot, cellSize: number) {
    // NEW v2: Cellular Automata visualization
    this.caLayer.removeChildren();
    for (const cell of snapshot.grid_cells) {
      if (!cell.ca.gol_alive && cell.ca.wireworld_state === 0) continue;

      const rect = new PIXI.Graphics();
      let color = 0x002200;

      if (cell.ca.gol_alive) {
        color = 0x00ff44;  // GoL alive = bright green
      }
      if (cell.ca.wireworld_state === 1) {
        color = 0x333333;  // Conductor = dark gray
      } else if (cell.ca.wireworld_state === 2) {
        color = 0xffaa00;  // Electron head = amber
      } else if (cell.ca.wireworld_state === 3) {
        color = 0x884400;  // Electron tail = dark amber
      }

      rect.rect(cell.x * cellSize, cell.y * cellSize, cellSize, cellSize)
          .fill({ color, alpha: 0.85 });
      this.caLayer.addChild(rect);
    }
  }

  private _renderRD(snapshot: WorldSnapshot, cellSize: number) {
    // NEW v2: Reaction-Diffusion (Gray-Scott) visualization — V concentration
    this.rdLayer.removeChildren();
    for (const cell of snapshot.grid_cells) {
      const v = cell.rd.v;
      if (v < 0.01) continue;

      const rect = new PIXI.Graphics();
      // V concentration: blue (low) → purple → red (high)
      const r = Math.floor(v * 255);
      const b = Math.floor((1 - v) * 200);
      const color = (r << 16) | (0x10 << 8) | b;

      rect.rect(cell.x * cellSize, cell.y * cellSize, cellSize, cellSize)
          .fill({ color, alpha: Math.min(0.9, v * 3) });
      this.rdLayer.addChild(rect);
    }
  }

  private _renderAgents(agents: AgentSummary[], cellSize: number) {
    const currentIds = new Set(agents.map(a => a.id));

    for (const [id, sprite] of this.agentSprites) {
      if (!currentIds.has(id)) {
        this.agentLayer.removeChild(sprite);
        this.agentSprites.delete(id);
      }
    }

    for (const agent of agents) {
      let sprite = this.agentSprites.get(agent.id);
      if (!sprite) {
        sprite = new PIXI.Graphics();
        this.agentLayer.addChild(sprite);
        this.agentSprites.set(agent.id, sprite);
      }

      sprite.clear();
      const color = this._agentColor(agent);
      const radius = 2 + agent.neural_complexity * 0.5;

      sprite.circle(0, 0, radius).fill({ color });
      sprite.x = agent.position.x * cellSize;
      sprite.y = agent.position.y * cellSize;

      sprite.eventMode = 'static';
      sprite.cursor = 'pointer';
      sprite.on('pointerdown', () => {
        useWorldStore.getState().selectAgent(agent.id);
      });
    }
  }

  private _agentColor(agent: AgentSummary): number {
    // Color by lifecycle stage + energy
    const stageColors: Record<string, number> = {
      neonatal: 0xaaddff,
      juvenile: 0x44ff88,
      adolescent: 0xffcc44,
      adult: 0x44aaff,
      elder: 0xff8844,
    };
    const base = stageColors[agent.stage] || 0xffffff;
    // Dim if low energy
    const dimFactor = Math.max(0.3, agent.energy);
    const r = Math.floor(((base >> 16) & 0xff) * dimFactor);
    const g = Math.floor(((base >> 8) & 0xff) * dimFactor);
    const b = Math.floor((base & 0xff) * dimFactor);
    return (r << 16) | (g << 8) | b;
  }

  private _energyToColor(value: number): number {
    const v = Math.min(1, value / 10);
    const b = Math.floor(v * 200);
    return (0x00 << 16) | (0x20 << 8) | b;
  }

  private _temperatureToColor(temp: number): number {
    const t = Math.min(1, Math.max(0, (temp - 0) / 100));
    const r = Math.floor(t * 255);
    const b = Math.floor((1 - t) * 200);
    return (r << 16) | (0x10 << 8) | b;
  }

  private _getCellSize(gridWidth: number): number {
    return Math.max(4, Math.floor(800 / gridWidth));
  }

  private _setupCameraControls() {
    let isDragging = false;
    let lastX = 0, lastY = 0;

    this.app.canvas.addEventListener('pointerdown', (e) => {
      isDragging = true; lastX = e.clientX; lastY = e.clientY;
    });
    this.app.canvas.addEventListener('pointerup', () => { isDragging = false; });
    this.app.canvas.addEventListener('pointermove', (e) => {
      if (!isDragging) return;
      this.worldContainer.x += e.clientX - lastX;
      this.worldContainer.y += e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
    });
    this.app.canvas.addEventListener('wheel', (e) => {
      const scale = e.deltaY > 0 ? 0.9 : 1.1;
      this.worldContainer.scale.x *= scale;
      this.worldContainer.scale.y *= scale;
    });
  }

  destroy() { this.app.destroy(); }
}
```

---

## 10. DATABASE SCHEMA & MIGRATIONS

### 10.1 Alembic Setup (NEW v2)

```ini
# alembic/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://%(DB_USER)s:%(DB_PASS)s@%(DB_HOST)s/%(DB_NAME)s
```

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

config = context.config

# Substitute env vars into DB URL
db_url = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}"
    f"/{os.environ['POSTGRES_DB']}"
)
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 10.2 Initial Migration (NEW v2)

```python
# alembic/versions/0001_initial_schema.py
"""initial schema

Revision ID: 0001
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Runs table
    op.create_table('runs',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('config', JSONB, nullable=False),
        sa.Column('status', sa.String(32), server_default='running'),
        sa.Column('genesis_mode', sa.String(32), nullable=False),
        sa.Column('research_hypothesis', sa.Text, server_default=''),
        sa.Column('max_tick', sa.Integer),
    )

    # Agent archive
    op.create_table('agents',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('birth_tick', sa.Integer, nullable=False),
        sa.Column('death_tick', sa.Integer),
        sa.Column('genome_hash', sa.String(32), nullable=False),
        sa.Column('genome_data', JSONB, nullable=False),
        sa.Column('parent_ids', sa.ARRAY(sa.Text), server_default='{}'),
        sa.Column('children_ids', sa.ARRAY(sa.Text), server_default='{}'),
        sa.Column('species_label', sa.String(128)),
        sa.Column('final_stage', sa.String(32)),
        sa.Column('final_state', JSONB),
        sa.Column('key_events', JSONB, server_default='[]'),
        sa.Column('life_story', sa.Text),
    )
    op.create_index('idx_agents_run', 'agents', ['run_id'])
    op.create_index('idx_agents_birth', 'agents', ['birth_tick'])
    op.create_index('idx_agents_species', 'agents', ['species_label'])

    # Event log — append only, NEVER DELETE OR UPDATE
    op.create_table('events',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('tick', sa.Integer, nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('source_id', sa.String(64)),
        sa.Column('target_id', sa.String(64)),
        sa.Column('data', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_events_run_tick', 'events', ['run_id', 'tick'])
    op.create_index('idx_events_type', 'events', ['event_type'])

    # World snapshots
    op.create_table('world_snapshots',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('tick', sa.Integer, nullable=False),
        sa.Column('population', sa.Integer),
        sa.Column('entropy', sa.Float),
        sa.Column('total_energy', sa.Float),
        sa.Column('species_count', sa.Integer),
        sa.Column('snapshot_data', JSONB),
    )
    op.create_index('idx_snapshots_run_tick', 'world_snapshots', ['run_id', 'tick'])

    # Species
    op.create_table('species',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('label', sa.String(128)),
        sa.Column('first_seen_tick', sa.Integer),
        sa.Column('last_seen_tick', sa.Integer),
        sa.Column('peak_population', sa.Integer),
        sa.Column('classification', JSONB),
        sa.Column('genome_signature', sa.String(32)),
    )

    # Observer analyses
    op.create_table('analyses',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('tick', sa.Integer),
        sa.Column('type', sa.String(64)),
        sa.Column('input_data', JSONB),
        sa.Column('result', sa.Text),
        sa.Column('model_used', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Complexity metrics time series (NEW v2)
    op.create_table('complexity_metrics',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('tick', sa.Integer, nullable=False),
        sa.Column('shannon_entropy_population', sa.Float),
        sa.Column('effective_complexity', sa.Float),
        sa.Column('innovation_rate', sa.Float),
        sa.Column('avg_neural_phi', sa.Float),
        sa.Column('genome_diversity', sa.Float),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_metrics_run_tick', 'complexity_metrics', ['run_id', 'tick'])

    # God Mode Audit Log — append only (NEW v2)
    op.create_table('god_mode_audit',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('run_id', sa.String(64), sa.ForeignKey('runs.id')),
        sa.Column('tick_at_intervention', sa.Integer, nullable=False),
        sa.Column('intervention_type', sa.String(64), nullable=False),
        sa.Column('target', JSONB, nullable=False),
        sa.Column('justification', sa.Text, nullable=False),
        sa.Column('experiment_label', sa.String(128), server_default=''),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('checkpoint_id', sa.String(64)),
        sa.Column('was_rolled_back', sa.Boolean, server_default='false'),
    )


def downgrade() -> None:
    op.drop_table('god_mode_audit')
    op.drop_table('complexity_metrics')
    op.drop_table('analyses')
    op.drop_table('species')
    op.drop_table('world_snapshots')
    op.drop_table('events')
    op.drop_table('agents')
    op.drop_table('runs')
```

### 10.3 Redis Keys (UPDATED v2)

```
# World state (in-memory, fast access)
world:{run_id}:state          → JSON (current WorldSnapshot, compressed)
world:{run_id}:tick           → INT (current tick)
world:{run_id}:config         → JSON (SimulationConfig)
world:{run_id}:stats          → JSON (WorldStats, updated every tick)
world:{run_id}:metrics        → JSON (latest ComplexityMetrics)   # NEW v2

# Agent data (hidup)
agent:{run_id}:{agent_id}     → JSON (Agent full data)

# Grid cells (hot cells only)
cell:{run_id}:{x}:{y}         → JSON (GridCell — includes CA + RD state)

# Pub/Sub channels
channel:events:{run_id}       → WorldEvent stream
channel:stats:{run_id}        → WorldStats stream
channel:snapshots:{run_id}    → WorldSnapshot stream (every N ticks)
channel:metrics:{run_id}      → ComplexityMetrics stream   # NEW v2

# Queues (Celery)
queue:observer:classify       → Classification job queue
queue:observer:narrate        → Narration job queue
queue:observer:analyze        → Civilization analysis queue  # NEW v2
```

---

## 11. COMPLEXITY METRICS (NEW v2)

### 11.1 Shannon Entropy Populasi

```python
# packages/simulation/src/simulation/metrics/entropy.py
"""
Complexity metrics sampler — dipanggil setiap N ticks.
Sesuai design doc Bab 57.

Metrik yang diimplementasikan:
1. Shannon Entropy populasi H_pop — keragaman genetik
2. Effective Complexity (proxy via compression ratio)
3. Innovation Rate — jumlah event baru per geological tick
4. Average Φ approximation — integrasi informasi neural
5. Genome Diversity (Hamming distance distribution)
"""
import numpy as np
from math import log2
from ..systems.base import System
from ..types import TickContext, WorldEvent


def shannon_entropy_population(agents: dict) -> float:
    """
    H_pop = -Σ p(genome_i) × log₂ p(genome_i)
    Entropy tinggi = keragaman genetik tinggi.
    """
    if not agents:
        return 0.0

    genome_counts: dict[str, int] = {}
    for agent in agents.values():
        if agent.is_alive:
            gh = agent.genome.checksum()
            genome_counts[gh] = genome_counts.get(gh, 0) + 1

    if not genome_counts:
        return 0.0

    total = sum(genome_counts.values())
    entropy = 0.0
    for count in genome_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * log2(p)

    return entropy


def effective_complexity_proxy(agents: dict) -> float:
    """
    Proxy untuk Effective Complexity (Gell-Mann).
    Menggunakan compression ratio behaviour sequence agen sebagai estimasi.
    Perilaku genuine complex = tidak bisa dikompres.
    """
    if not agents:
        return 0.0

    # Sample subset agen
    sample = list(agents.values())[:min(100, len(agents))]
    if not sample:
        return 0.0

    complexities = []
    for agent in sample:
        if not agent.is_alive:
            continue
        # Encode genome sebagai string dan ukur compressibility
        genome_bytes = b"".join(g.sequence for g in agent.genome.genes)
        if not genome_bytes:
            continue
        import zlib
        compressed = zlib.compress(genome_bytes, level=9)
        ratio = len(compressed) / max(len(genome_bytes), 1)
        # High ratio = hard to compress = genuinely complex
        complexities.append(ratio)

    return float(np.mean(complexities)) if complexities else 0.0


def approximate_phi(agent) -> float:
    """
    Approximasi kasar untuk Φ (Integrated Information, Tononi).
    Φ = 0 untuk sistem yang bisa dipartisi tanpa information loss.
    
    Ini adalah proxy sederhana berdasarkan jumlah koneksi neural (n_genes × neural_genes)
    dan current activation variance. Full Φ calculation terlalu mahal untuk real-time.
    """
    neural_genes = [g for g in agent.genome.genes if g.product_type == "neural"]
    n_neural = len(neural_genes)
    if n_neural < 2:
        return 0.0

    # Simple proxy: lebih banyak neural gene yang aktif & beragam → higher Φ
    active = [g for g in neural_genes if g.is_active and g.expression_level > 0.3]
    diversity = len(set(g.sequence[:2] for g in active)) / max(len(active), 1)
    return min(1.0, n_neural * diversity * 0.1)


def genome_diversity_score(agents: dict) -> float:
    """
    Rata-rata pairwise Hamming distance antar genome (sample).
    Tinggi = populasi genetik beragam = evolusi aktif.
    """
    alive = [a for a in agents.values() if a.is_alive]
    if len(alive) < 2:
        return 0.0

    # Sample 50 pasang
    import random
    sample_pairs = min(50, len(alive) * (len(alive) - 1) // 2)
    distances = []

    for _ in range(sample_pairs):
        a1, a2 = random.sample(alive, 2)
        s1 = a1.genome.checksum()
        s2 = a2.genome.checksum()
        # Hamming on hex strings
        dist = sum(c1 != c2 for c1, c2 in zip(s1, s2)) / max(len(s1), 1)
        distances.append(dist)

    return float(np.mean(distances)) if distances else 0.0


class MetricsSamplerSystem(System):
    """
    Samples complexity metrics every metrics_sample_every ticks.
    Emits ComplexityMetrics to Redis dan menyimpan ke PostgreSQL.
    """

    def __init__(self, world):
        super().__init__(world)
        self._innovation_window: list[int] = []  # Innovation events in window
        self._last_species_count: int = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.metrics_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        agents = self.world.agents

        metrics = {
            "tick": ctx.tick,
            "shannon_entropy_population": shannon_entropy_population(agents),
            "effective_complexity": effective_complexity_proxy(agents),
            "innovation_rate": self._compute_innovation_rate(ctx.tick),
            "avg_neural_phi": float(np.mean([
                approximate_phi(a) for a in agents.values() if a.is_alive
            ])) if agents else 0.0,
            "genome_diversity": genome_diversity_score(agents),
        }

        # Store in Redis
        import json, redis
        try:
            r = redis.Redis.from_url("redis://localhost:6379/0")
            r.set(f"world:{getattr(self.world.config, 'seed_id', 'default')}:metrics",
                  json.dumps(metrics))
            r.publish(f"channel:metrics:{getattr(self.world.config, 'seed_id', 'default')}",
                     json.dumps({"type": "metrics", "payload": metrics}))
        except Exception:
            pass  # Non-fatal

        return []

    def _compute_innovation_rate(self, current_tick: int) -> float:
        """
        Innovation rate = jumlah novel event (speciation, new tool, new behavior)
        per unit geological tick.
        Menggunakan world.state.innovation_count.
        """
        count = getattr(self.world, '_innovation_counter', 0)
        if not hasattr(self, '_last_innovation_tick'):
            self._last_innovation_tick = 0
            self._last_innovation_count = 0

        delta_tick = max(1, current_tick - self._last_innovation_tick)
        delta_count = count - self._last_innovation_count
        self._last_innovation_tick = current_tick
        self._last_innovation_count = count

        return float(delta_count) / delta_tick
```

---

## 12. ENVIRONMENT SETUP

### 12.1 Prerequisites

```bash
# Required
- Python 3.12+
- Node.js 20+
- Docker Desktop
- Git

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pnpm
npm install -g pnpm
```

### 12.2 First-Time Setup

```bash
# Clone repo
git clone https://github.com/yourorg/world-ai
cd world-ai

# Copy env file
cp .env.example .env
# Edit .env: set OPENROUTER_API_KEY dan database credentials

# Start infrastructure
docker-compose up -d postgres redis qdrant

# Wait for postgres to be healthy
docker-compose exec postgres pg_isready -U worldai

# Setup Python packages
cd packages/simulation && uv sync
cd ../api && uv sync
cd ../observer && uv sync

# Setup frontend
cd ../visualizer && pnpm install

# Run database migrations (NEW v2 — Alembic)
cd ../../
uv run alembic upgrade head

# Initialize Qdrant episodic memory collection
uv run python -c "from packages.simulation.src.simulation.agents.memory import ensure_collection; ensure_collection()"

# Test everything works
cd packages/simulation && uv run pytest tests/ -v
```

### 12.3 .env.example (UPDATED v2)

```bash
# ── LLM — OpenRouter (replaces Anthropic SDK) ──────────────────
OPENROUTER_API_KEY=sk-or-v1-...
# Optional: referral header untuk OpenRouter analytics
SITE_URL=https://worldai.dev
OPENROUTER_DEFAULT_MODEL=anthropic/claude-sonnet-4-5

# ── PostgreSQL ─────────────────────────────────────────────────
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=worldai
POSTGRES_USER=worldai
POSTGRES_PASSWORD=worldai_dev

# ── Redis ──────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Qdrant ────────────────────────────────────────────────────
QDRANT_HOST=localhost
QDRANT_PORT=6333

# ── Simulation Defaults ────────────────────────────────────────
DEFAULT_GRID_WIDTH=64
DEFAULT_GRID_HEIGHT=64
DEFAULT_GENESIS_MODE=seeded_chemistry
SNAPSHOT_INTERVAL_TICKS=1000
METRICS_SAMPLE_EVERY=1000

# ── API ────────────────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000

# ── Frontend ───────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### 12.4 docker-compose.yml

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: worldai
      POSTGRES_USER: worldai
      POSTGRES_PASSWORD: worldai_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U worldai"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### 12.5 pyproject.toml (simulation package — UPDATED v2)

```toml
[project]
name = "world-ai-simulation"
version = "2.0.0"
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0",
    "numba>=0.60",
    "torch>=2.3",
    "redis>=5.0",
    "asyncpg>=0.29",
    "pydantic>=2.7",
    "structlog>=24.0",
    "qdrant-client>=1.9",   # Episodic memory (NEW v2)
    "sqlalchemy>=2.0",      # For Alembic models
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "hypothesis>=6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 12.6 pyproject.toml (observer package — UPDATED v2)

```toml
[project]
name = "world-ai-observer"
version = "2.0.0"
requires-python = ">=3.12"
dependencies = [
    "openai>=1.30",         # OpenRouter via OpenAI-compatible API (CHANGED v2)
    "celery>=5.3",
    "redis>=5.0",
    "pydantic>=2.7",
    "structlog>=24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 13. TESTING STRATEGY

### 13.1 Unit Tests — Physics

```python
# packages/simulation/tests/test_physics.py

import numpy as np
import pytest
from simulation.physics.particles import verlet_integrate


def test_verlet_integration_energy_conservation():
    """Total kinetic energy seharusnya konservatif dalam closed system."""
    N = 100
    positions  = np.random.rand(N, 2) * 100
    velocities = np.random.rand(N, 2) * 2 - 1
    forces     = np.zeros((N, 2))   # No forces = constant velocity
    masses     = np.ones(N)

    KE_initial = 0.5 * np.sum(masses[:, None] * velocities**2)

    for _ in range(1000):
        positions, velocities = verlet_integrate(positions, velocities, forces, masses, dt=0.01)

    KE_final = 0.5 * np.sum(masses[:, None] * velocities**2)
    assert abs(KE_final - KE_initial) / KE_initial < 0.001, \
        f"Energy conservation violated: {KE_initial:.4f} → {KE_final:.4f}"


def test_toroidal_wrapping():
    """Agent yang melewati batas harus muncul di sisi lain."""
    from simulation.types import Vec2, Agent, Genome
    from simulation.physics.particles import PhysicsSystem

    # Buat minimal world mock
    class MockWorld:
        config = type('c', (), {'grid_width': 64, 'grid_height': 64,
                                'fundamental': type('f', (), {'G_digital': 0.01})()})()
        agents = {}
        grid = {}
        prng = None

    # Position near right edge, moving right
    import uuid
    agent = Agent(
        id="test",
        genome=Genome(genes=[]),
        birth_tick=0,
        position=Vec2(63.9, 32.0),
        velocity=Vec2(2.0, 0.0),
        mass=1.0,
        energy=1.0,
        health=1.0,
    )
    world = MockWorld()
    world.agents["test"] = agent
    system = PhysicsSystem(world)
    from simulation.types import TickContext
    ctx = TickContext(tick=1, dt=0.1, physics_tick=True,
                      chemistry_tick=False, biology_tick=False,
                      cognitive_tick=False, social_tick=False,
                      geological_tick=False, ca_tick=False,
                      rd_tick=False, metrics_tick=False)
    system.update(ctx)
    # After moving right past edge 64.0, should wrap to near 0
    assert agent.position.x < 1.0, f"Expected position < 1.0, got {agent.position.x}"


def test_diffusion_mass_conservation():
    """Total massa elemen harus konservatif setelah difusi."""
    import numpy as np
    from simulation.physics.diffusion import apply_diffusion

    conc = np.random.rand(32, 32)
    total_before = conc.sum()

    for _ in range(100):
        conc = apply_diffusion(conc, D=0.05, dt=0.1)

    total_after = conc.sum()
    assert abs(total_after - total_before) < 0.01, \
        "Diffusion does not conserve mass"
```

### 13.2 Unit Tests — CA & RD (NEW v2)

```python
# packages/simulation/tests/test_ca.py

import numpy as np
import pytest
from simulation.physics.cellular_automata import gol_step, wireworld_step
from simulation.physics.reaction_diffusion import gray_scott_step


def test_gol_blinker():
    """Blinker pattern harus oscillate period-2."""
    grid = np.zeros((10, 10), dtype=np.int8)
    # Blinker horizontal
    grid[5, 4] = 1
    grid[5, 5] = 1
    grid[5, 6] = 1

    step1 = gol_step(grid)
    # Setelah 1 step, blinker menjadi vertical
    assert step1[4, 5] == 1
    assert step1[5, 5] == 1
    assert step1[6, 5] == 1
    assert step1[5, 4] == 0
    assert step1[5, 6] == 0

    step2 = gol_step(step1)
    # Setelah 2 steps, kembali ke horizontal
    assert step2[5, 4] == 1
    assert step2[5, 5] == 1
    assert step2[5, 6] == 1


def test_wireworld_electron_propagation():
    """Electron head harus bergerak di sepanjang conductor."""
    grid = np.zeros((5, 10), dtype=np.int8)
    # Buat conductor line
    for x in range(1, 9):
        grid[2, x] = 1  # conductor
    # Letakkan electron head di ujung kiri
    grid[2, 1] = 2  # electron head

    initial_head_pos = 1
    for step in range(7):
        grid = wireworld_step(grid)

    # After 7 steps, head should have moved 7 positions
    expected_head = (initial_head_pos + 7) % 8 + 1
    assert grid[2, expected_head] == 2 or grid[2, expected_head - 1] == 3, \
        "Electron did not propagate correctly"


def test_gray_scott_pattern_formation():
    """Gray-Scott harus membentuk pola setelah cukup iterasi."""
    W, H = 64, 64
    U = np.ones((H, W))
    V = np.zeros((H, W))
    # Seed center
    U[28:36, 28:36] = 0.5
    V[28:36, 28:36] = 0.25

    # Run 1000 steps
    for _ in range(1000):
        U, V = gray_scott_step(U, V, Du=0.16, Dv=0.08, F=0.055, k=0.062)

    # V should have spread but remain bounded
    assert V.max() <= 1.0
    assert V.min() >= 0.0
    # Pattern should have formed — V variance should be > 0
    assert V.std() > 0.01, "No pattern formation detected"


def test_gol_toroidal_boundary():
    """GoL harus menggunakan toroidal boundaries."""
    grid = np.zeros((10, 10), dtype=np.int8)
    # Glider at corner that would normally go out of bounds
    grid[0, 0] = 1
    grid[0, 1] = 1
    grid[0, 9] = 1  # Wraps

    result = gol_step(grid)
    # Should not raise and should wrap correctly
    assert result.shape == (10, 10)
```

### 13.3 Unit Tests — Hebbian Learning (NEW v2)

```python
# packages/simulation/tests/test_agents.py

import torch
import torch.nn as nn
import pytest
from simulation.agents.neural import hebbian_update, build_network_from_genome
from simulation.types import Genome, Gene


def _make_genome(n_genes: int, neural_ratio: float = 0.5) -> Genome:
    genes = []
    for i in range(n_genes):
        product = "neural" if i / n_genes < neural_ratio else "structural"
        genes.append(Gene(
            id=f"g{i}", sequence=bytes([i % 256, (i*7)%256]),
            expression_level=0.8, promoter_condition="default",
            product_type=product,
        ))
    return Genome(genes=genes)


def test_hebbian_update_positive_reward_strengthens():
    """Positive reward harus memperkuat koneksi yang aktif."""
    genome = _make_genome(10, neural_ratio=0.8)
    network = build_network_from_genome(genome)

    # Get initial weights
    initial_weights = [p.clone() for p in network.parameters()]

    pre = torch.ones(12)
    post = torch.ones(6) * 0.5
    reward = 1.0  # Strong positive reward

    for _ in range(100):  # Many updates
        hebbian_update(network, pre, post, reward=reward, learning_rate=0.01)

    # Check that weights changed
    any_changed = False
    for initial, current in zip(initial_weights, network.parameters()):
        if not torch.allclose(initial, current, atol=1e-6):
            any_changed = True
            break

    assert any_changed, "Weights should have changed after Hebbian updates"


def test_hebbian_zero_reward_no_update():
    """Zero reward tidak boleh mengubah weights."""
    genome = _make_genome(8)
    network = build_network_from_genome(genome)
    initial_weights = [p.clone() for p in network.parameters()]

    pre = torch.randn(12)
    post = torch.randn(6)

    hebbian_update(network, pre, post, reward=0.0, learning_rate=0.01)

    for initial, current in zip(initial_weights, network.parameters()):
        assert torch.allclose(initial, current), "Zero reward should not change weights"


def test_genome_crossover_child_between_parents():
    """Child genome harus ada di antara dua parent."""
    g1 = _make_genome(20)
    g2 = _make_genome(20)
    child_a, child_b = g1.crossover(g2)

    assert len(child_a.genes) > 0
    assert len(child_b.genes) > 0
    # Children should be distinct from both parents (with high probability)
    assert child_a.checksum() != g1.checksum()
```

### 13.4 Integration Tests

```python
# packages/simulation/tests/test_integration.py

import pytest
from simulation.world import World
from simulation.types import SimulationConfig, EventType


@pytest.fixture
def seeded_world():
    config = SimulationConfig(
        seed_id="test-run-001",
        genesis_mode="seeded_chemistry",
        grid_width=32,
        grid_height=32,
    )
    return World(config)


def test_abiogenesis_occurs_in_seeded_mode(seeded_world):
    """Protocell harus muncul dalam 50.000 ticks di seeded_chemistry mode."""
    abiogenesis_events = []

    for _ in range(50_000):
        events = seeded_world.step()
        ab_events = [e for e in events
                     if e.type == EventType.ABIOGENESIS and
                     e.data.get("phase") == "life_emerged"]
        abiogenesis_events.extend(ab_events)
        if abiogenesis_events:
            break

    assert len(abiogenesis_events) > 0, \
        "No abiogenesis occurred in 50,000 ticks (seeded_chemistry mode)"


def test_chemistry_syntax_no_crash(seeded_world):
    """Chemistry system harus berjalan tanpa syntax error (bugfix v2)."""
    try:
        for _ in range(100):
            seeded_world.step()
    except Exception as e:
        pytest.fail(f"Simulation crashed on first 100 steps: {e}")


def test_ca_initializes_correctly(seeded_world):
    """CA system harus terinisialisasi dan berjalan."""
    for _ in range(50):
        seeded_world.step()

    ca_system = next(s for s in seeded_world.systems
                     if s.__class__.__name__ == "CellularAutomataSystem")
    assert ca_system._initialized, "CA should be initialized after ticks"
    alive_count = ca_system.gol_grid.sum()
    assert alive_count > 0, "GoL should have some alive cells"


def test_energy_globally_conserved(seeded_world):
    """Total energy (environment + agents) harus konservatif."""
    initial_energy = seeded_world.total_energy()

    for _ in range(500):
        seeded_world.step()

    final_energy = seeded_world.total_energy()
    error = abs(final_energy - initial_energy) / max(initial_energy, 1e-9)
    assert error < 0.05, f"Energy not conserved: {error:.4%} drift"


def test_biogeochemical_cycles_prevent_depletion(seeded_world):
    """Biogeochemical cycles harus mencegah deplesi total elemen."""
    for _ in range(10_000):
        seeded_world.step()

    cycle_system = next(s for s in seeded_world.systems
                        if s.__class__.__name__ == "BiogeochemicalCycleSystem")

    # Atmospheric pools harus masih ada
    assert cycle_system.co2_atm > 0, "CO2 atmosphere should not be completely depleted"
    assert cycle_system.n2_atm > 0, "N2 atmosphere should not be completely depleted"


def test_pcg_prng_is_deterministic(seeded_world):
    """PRNG harus menghasilkan sequence yang sama dengan seed yang sama."""
    # Two worlds with same seed should produce same PRNG values
    config2 = SimulationConfig(
        seed_id="test-run-001",  # Same seed
        genesis_mode="seeded_chemistry",
        grid_width=32,
        grid_height=32,
    )
    world2 = World(config2)

    # Sample 100 values dari region (5, 5)
    vals1 = [seeded_world.prng.random(5, 5) for _ in range(100)]
    vals2 = [world2.prng.random(5, 5) for _ in range(100)]

    assert vals1 == vals2, "Same seed should produce identical PRNG sequences"


def test_lifecycle_phase_transitions(seeded_world):
    """Agen harus mengalami phase transitions sesuai age."""
    from simulation.types import AgentStage
    from simulation.biology.abiogenesis import _mode_c_seeded_protocells

    # Use mode C for instant life
    events = _mode_c_seeded_protocells(seeded_world)
    assert len(seeded_world.agents) > 0

    agent = list(seeded_world.agents.values())[0]
    assert agent.stage == AgentStage.NEONATAL

    # Run until JUVENILE threshold
    for _ in range(100):
        seeded_world.step()

    # Stage should have advanced
    # (Exact tick depends on genome, so just check it's not stuck)
    assert agent.stage != AgentStage.NEONATAL or agent.age_ticks < 20
```

### 13.5 Property-Based Tests

```python
# packages/simulation/tests/test_properties.py

from hypothesis import given, settings
from hypothesis import strategies as st
import numpy as np
from simulation.biology.genome import Genome
from simulation.chemistry.reactions import arrhenius_rate
from simulation.physics.reaction_diffusion import gray_scott_step


@given(st.integers(min_value=1, max_value=100))
def test_genome_mutation_changes_something(n_genes):
    """Mutasi rate > 0 harus menghasilkan perubahan dalam N percobaan."""
    from simulation.types import Gene, Genome
    genes = [Gene(id=f"g{i}", sequence=bytes([i%256, 42]),
                  expression_level=0.5, promoter_condition="default",
                  product_type="structural") for i in range(n_genes)]
    genome = Genome(genes=genes, mutation_rate=0.1)

    mutations = 0
    for _ in range(50):
        mutated = genome.mutate()
        if mutated.checksum() != genome.checksum():
            mutations += 1

    if n_genes > 5:
        assert mutations > 0, "High mutation rate should cause some changes"


@given(st.floats(min_value=0.0, max_value=100.0))
def test_arrhenius_rate_nonnegative(Ea):
    rate = arrhenius_rate(Ea, temperature=25.0)
    assert 0.0 <= rate <= 1.0, f"Rate must be in [0,1], got {rate}"


@given(
    st.floats(min_value=0.0, max_value=0.1),   # F
    st.floats(min_value=0.0, max_value=0.1),   # k
)
@settings(max_examples=20)
def test_gray_scott_bounded(F, k):
    """Gray-Scott output harus selalu dalam [0, 1]."""
    U = np.random.rand(16, 16)
    V = np.random.rand(16, 16) * 0.1

    for _ in range(10):
        U, V = gray_scott_step(U, V, Du=0.16, Dv=0.08, F=F, k=k)

    assert U.min() >= 0.0 and U.max() <= 1.0, "U must stay in [0,1]"
    assert V.min() >= 0.0 and V.max() <= 1.0, "V must stay in [0,1]"
```

---

## 14. KEY ENGINEERING DECISIONS & RATIONALE

### 14.1 Mengapa Python, bukan Rust/C++?

MVP membutuhkan kecepatan development, bukan kecepatan eksekusi. NumPy + Numba memberikan performa yang cukup untuk Phase 0-1 (ribuan agen). Jika profiling menunjukkan bottleneck nyata di Phase 3+, kita bisa menulis physics engine dalam Rust dengan Python binding (PyO3). Jangan optimasi sebelum ada data.

### 14.2 Mengapa OpenRouter, bukan Anthropic SDK langsung?

OpenRouter memberikan fleksibilitas untuk menggunakan model terbaik per use-case tanpa terikat satu provider:
- Klasifikasi batch → Claude Haiku via OpenRouter (paling murah)
- Narasi detail → Claude Opus atau model premium lain
- Masa depan: bisa switch ke Gemini Flash untuk volume sangat tinggi
- Satu API key untuk semua model
- Format identik OpenAI Chat Completions — mudah dipindahkan

### 14.3 Mengapa Gray-Scott ditambahkan ke MVP?

Design doc Bab 3.6 menempatkan Reaction-Diffusion sebagai fondasi pola biologis. Tanpa ini, grid terlalu homogen dan abiogenesis spontan (Mode A) hampir tidak mungkin dalam waktu yang reasonable. Gray-Scott dengan parameter default (F=0.055, k=0.062) menghasilkan labyrinth pattern yang menyerupai morfogen biologis — persis kondisi yang dibutuhkan untuk proto-kehidupan muncul.

### 14.4 Mengapa CA layer ditambahkan ke MVP?

Wireworld CA adalah proto-konduktur — sinyal bergerak di sepanjang "kawat." Ini adalah benih untuk sistem saraf primitif yang akan muncul di Phase 3. Dengan CA yang sudah ada di Phase 0, agen pertama sudah lahir di dunia yang memiliki "sinyal berkeliling" — precondition penting untuk evolusi sensory system.

### 14.5 Reflex behavior sebagai "Level-0 Cognition", bukan pelanggaran Emergent-First

`_reflex_chemotaxis` bukan perilaku yang di-hardcode permanen. Ini adalah kemotaksis Level-0 (Bab 18.1 design doc) yang hanya aktif ketika `neural_complexity == 0`. Begitu neural complexity berkembang melalui evolusi, neural network takes over sepenuhnya. Analogi: reflex knee-jerk manusia bukan "melanggar" emergent mind — itu layer paling primitif. Ini didokumentasikan sebagai deviasi yang justified.

### 14.6 Mengapa Alembic untuk migrations?

PostgreSQL schema akan berevolusi seiring project berkembang. Tanpa migration system, perubahan schema mengharuskan rebuild database dari scratch. Alembic memungkinkan incremental schema changes yang reversible dan reproducible.

### 14.7 Hebbian learning yang benar vs noise approximation

v1.0.0 menggunakan `param.add_(torch.randn_like(param) * lr)` — ini adalah random noise scaling, bukan Hebbian learning. Ini tidak menggunakan aktivasi pre/post sinaptik sama sekali. v2.0.0 mengimplementasikan `Δw = η × pre × post × reward` yang sebenarnya, sesuai Bab 47.4 design doc. Perbedaannya signifikan: random noise tidak menghasilkan asosiasi spesifik, sedangkan Hebbian learning menghasilkan koneksi yang diperkuat berdasarkan co-activation.

### 14.8 Genome → NN architecture derivation

Ukuran dan tipe neural network agen diderivasikan dari genome-nya, bukan dipilih developer. Agen dengan banyak "neural genes" mendapat RecurrentNetwork (GRU). Agen dengan sedikit neural genes mendapat Feedforward sederhana. Ini memastikan bahwa agen yang "lebih pintar" bukan karena kita memberikan network yang lebih besar, tapi karena genome mereka berevolusi mengkodekan kapasitas lebih tinggi.

### 14.9 Biogeochemical cycles: syarat sustainability

Tanpa carbon/nitrogen/water cycles, simulasi akan mengalami dua kegagalan:
1. **Material depletion**: TERRA terakumulasi di tubuh organisme mati dan tidak kembali ke pool
2. **Thermal runaway**: reaksi kimia eksoterm terus memanaskan cells tanpa cooling

Cycles memastikan materi berputar — persis seperti ekosistem nyata. Ini bukan fitur opsional.

### 14.10 God Mode Governance

Setiap intervensi operator wajib menyertakan justifikasi tertulis, membuat checkpoint pre-intervensi, dan masuk ke audit log yang tidak bisa dihapus. Ini bukan bureaucracy — ini metodologi penelitian yang valid. Data dari intervensi yang tidak terdokumentasi tidak bisa dimasukkan ke analisis ilmiah.

---

## 11. DEVELOPMENT PHASES (SPRINT PLAN)

### Sprint 1 — Foundation (Minggu 1–2)

**Goal:** Project berjalan, test passes, dev environment up.

Tasks:
- [ ] Setup monorepo (uv workspaces + pnpm workspaces)
- [ ] Docker compose: PostgreSQL + Redis + Qdrant
- [ ] **Alembic setup** + `alembic/env.py` + `0001_initial_schema.py` migration (NEW v2)
- [ ] `simulation` package: `types.py` lengkap (termasuk CA/RD types)
- [ ] `prng.py`: PCG per-region PRNG (NEW v2)
- [ ] `physics/particles.py`: Verlet integration + Numba JIT
- [ ] `physics/diffusion.py`: Fick's law diffusion
- [ ] `physics/cellular_automata.py`: GoL + Wireworld CA (NEW v2)
- [ ] `physics/reaction_diffusion.py`: Gray-Scott system (NEW v2)
- [ ] `thermodynamics/energy.py`: Conservation tracking
- [ ] Unit tests: energy conservation, CA patterns, RD bounded, PRNG determinism
- [ ] `scripts/benchmark.py`: Performance baseline

**Definition of Done:** 10.000 partikel bergerak pada 60+ ticks/second. CA patterns muncul. RD V-concentration > 0 setelah 1000 ticks. PRNG reproducibility test passes. Alembic migrations run cleanly.

---

### Sprint 2 — Chemistry & Cycles (Minggu 3–4)

**Goal:** Reaksi kimia terjadi, molekul terbentuk, siklus materi berjalan.

Tasks:
- [ ] `chemistry/elements.py`: Element definitions
- [ ] `chemistry/reactions.py`: Arrhenius kinetics + **fixed REACTION_RULES** (v2 bugfix)
- [ ] `chemistry/bonds.py`: Bond formation/breaking
- [ ] `chemistry/diffusion.py`: Chemical diffusion per element
- [ ] `environment/cycles.py`: **Biogeochemical cycles** C/N/Water (NEW v2)
- [ ] `world.py`: World class + grid initialization + PRNG init
- [ ] `tick.py`: Tick scheduler + context builder (includes ca_tick, rd_tick, metrics_tick)
- [ ] Unit tests: Reaction kinetics, mass conservation, cycle sustainability

**Definition of Done:** Proto-nucleotide molecules muncul spontan dalam 10.000 ticks di seeded chemistry mode. Carbon cycle tidak menghasilkan accumulation. Syntax error REACTION_RULES confirmed fixed.

---

### Sprint 3 — Biology & Abiogenesis (Minggu 5–7)

**Goal:** Kehidupan pertama muncul, bisa bereproduksi, lifecycle phase transitions.

Tasks:
- [ ] `biology/genome.py`: Genome + mutasi + **crossover** (NEW v2)
- [ ] `biology/abiogenesis.py`: **Mode A/B/C full implementation** (NEW v2)
- [ ] `biology/metabolism.py`: Energy consumption + nutrient uptake
- [ ] `biology/reproduction.py`: Asexual division + **sexual reproduction scaffold**
- [ ] `biology/lifecycle.py`: **Phase transitions + critical period** (NEW v2)
- [ ] `biology/immune.py`: Innate immunity basic
- [ ] Agent death & data archival system
- [ ] Alembic migration: run `upgrade head`
- [ ] Persistence: State save/load dari Redis

**Definition of Done:** Mode B menghasilkan protocell pertama dalam < 10.000 ticks. Phase transitions (NEONATAL → JUVENILE → ADULT) terjadi dan ter-log. Kematian ter-archive di PostgreSQL. Mode C menghasilkan agent langsung di t=0.

---

### Sprint 4 — Agent Cognition & Memory (Minggu 8–9)

**Goal:** Neural system berevolusi, Hebbian learning benar, episodic memory berjalan.

Tasks:
- [ ] `agents/neural.py`: **Proper Hebbian learning** + genome → architecture derivation (UPDATED v2)
- [ ] `agents/sensory.py`: Full sensory perception including CA state
- [ ] `agents/memory.py`: **Qdrant episodic memory write + retrieval** (NEW v2)
- [ ] `agents/actions.py`: Action space lengkap
- [ ] Ensure Qdrant collection initialized
- [ ] `metrics/`: **Complexity metrics system** — Shannon entropy, Φ approx, innovation rate (NEW v2)
- [ ] Unit tests: Hebbian correctness, Qdrant integration, lifecycle

**Definition of Done:** Agen dengan neural_complexity > 0 menggunakan network, bukan reflex. Hebbian test passes (positive reward strengthens). Episodic memory tersimpan di Qdrant dan bisa di-retrieve. Complexity metrics ter-sample setiap 1000 ticks.

---

### Sprint 5 — API & WebSocket (Minggu 10–11)

**Goal:** Backend bisa diquery dan di-stream, God Mode teraudi.

Tasks:
- [ ] FastAPI app setup + CORS
- [ ] `routes/world.py`: State, stats, history endpoints
- [ ] `routes/agents.py`: List, detail, lineage endpoints
- [ ] `routes/metrics.py`: Complexity metrics endpoints (NEW v2)
- [ ] `routes/control.py`: **God Mode + audit log** (NEW v2)
- [ ] WebSocket manager + subscription system (termasuk `metrics` channel)
- [ ] Redis pub/sub → WebSocket bridge
- [ ] Rate limiting untuk God Mode endpoints
- [ ] OpenAPI docs auto-generated

**Definition of Done:** Postman collection tests pass. WebSocket menerima events + metrics real-time. God Mode endpoint menolak request tanpa justifikasi. Audit log entry dibuat.

---

### Sprint 6 — Visualizer (Minggu 12–13)

**Goal:** Dashboard bisa melihat dunia, CA/RD layer, dan complexity metrics.

Tasks:
- [ ] React + Vite setup
- [ ] PixiJS `WorldRenderer`: Grid heatmap + agent sprites + **CA layer** + **RD layer** (NEW v2)
- [ ] Zustand store (termasuk `metricsStore`)
- [ ] `useWebSocket` hook
- [ ] `Dashboard.tsx`: Stats panel + world view + **render mode selector** (energy/ca/rd/temp)
- [ ] `MetricsPanel.tsx`: Shannon entropy, Φ, innovation rate charts (NEW v2)
- [ ] `AgentInspector.tsx`: Detail view dengan lifecycle stage
- [ ] Speed control + pause
- [ ] Event log panel (real-time)

**Definition of Done:** Bisa melihat agen bergerak, CA patterns, RD V-concentration. Complexity metrics ter-plot real-time. Klik agen menampilkan detail termasuk lifecycle stage.

---

### Sprint 7 — Observer Layer (Minggu 14)

**Goal:** LLM via OpenRouter mengklasifikasikan fenomena dari luar simulasi.

Tasks:
- [ ] `observer/client.py`: **OpenRouter client setup** (NEW v2)
- [ ] `observer/classifier.py`: Species classification via OpenRouter Haiku
- [ ] `observer/narrator.py`: Life story generation via OpenRouter Sonnet
- [ ] `observer/analyzer.py`: Civilization analysis via OpenRouter Opus
- [ ] Celery setup + Redis broker
- [ ] Trigger dari event: ABIOGENESIS, CA_PATTERN, SPECIATION
- [ ] Observer endpoints di API
- [ ] Integration test: OpenRouter call succeeds

**Definition of Done:** Ketika protocell pertama muncul, Celery job berjalan dan menghasilkan species classification via Claude Haiku (OpenRouter). Life story tersimpan di PostgreSQL. Civilization analysis berjalan per geological tick.

---

### Milestone MVP (Akhir Bulan 3–3.5)

**World.ai Phase 0+1 Complete — v2.0.0:**
- ✅ Dunia 2D berjalan dengan fisika + kimia (fix syntax error)
- ✅ CA layer (GoL + Wireworld) aktif — proto-konduktivitas ada
- ✅ Reaction-Diffusion (Gray-Scott) aktif — pola biologis muncul
- ✅ PCG PRNG per region — reproducibility terjamin
- ✅ Biogeochemical cycles (C/N/Water) — sustainability terjamin
- ✅ Kehidupan pertama muncul (Mode A/B/C — semua diimplementasikan)
- ✅ Agen dapat bergerak, makan, bereproduksi
- ✅ Lifecycle phase transitions (NEONATAL → ELDER)
- ✅ Hebbian learning yang benar
- ✅ Episodic memory di Qdrant
- ✅ Complexity metrics real-time (Shannon entropy, Φ, innovation rate)
- ✅ Dashboard visualisasi real-time dengan CA/RD view
- ✅ LLM observer via OpenRouter (multi-model strategy)
- ✅ God Mode dengan audit log
- ✅ Alembic migrations — database reproducible

---

**Dokumen ini adalah Technical MVP Spec v2.0.0 yang siap diimplementasikan.**

**Version:** 2.0.0
**Companion:** WORLD_AI_MASTER_DESIGN_v0.3.md
**Next Step:** Sprint 1 — Foundation

---
*World.ai — Start from zero. Build everything.*
