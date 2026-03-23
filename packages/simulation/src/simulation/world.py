from typing import Optional
from dataclasses import field
from .types import (
    SimulationConfig,
    WorldState,
    GridCell,
    Agent,
    AgentID,
    ElementType,
    TickContext,
    WorldEvent,
    EventType,
)
from .systems.event_bus import EventBus
from .prng import RegionalPRNG
from .physics.particles import PhysicsSystem
from .chemistry.reactions import ChemistrySystem

try:
    from .profiling import get_tick_timer

    _use_profiler = True
except ImportError:
    _use_profiler = False


class World:
    def __init__(self, config: SimulationConfig, observer_enabled: bool = False):
        self.config = config
        self.tick = 0
        self.grid: dict[tuple, GridCell] = {}
        self.agents: dict[AgentID, Agent] = {}
        self.event_bus = EventBus()
        self.systems = self._init_systems()
        self.metrics_history: list[dict] = []
        self.observer_enabled = observer_enabled
        self.observer = None
        self._initialize_grid()
        self._initialize_prng()
        self._init_observer()

    def _init_observer(self):
        if not self.observer_enabled:
            return
        try:
            from observer.observer import ObserverLayer, ObserverConfig

            self.observer = ObserverLayer(self)
        except Exception as e:
            print(f"Warning: Could not initialize observer: {e}")

    def _initialize_prng(self):
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
                cell.chemical_pool = {
                    ElementType.PRIMUM: max(
                        0, self.config.initial_energy_density + ((x * 7 + y * 13) % 10 - 5) * 0.1
                    ),
                    ElementType.AQUA: 5.0,
                    ElementType.TERRA: 3.0,
                    ElementType.IGNIS: 1.0,
                    ElementType.AETHER: 0.5,
                    ElementType.LAPIS: 0.2,
                }
                self.grid[(x, y)] = cell

    def _init_systems(self) -> list:
        from .physics.diffusion import DiffusionSystem
        from .physics.cellular_automata import CellularAutomataSystem
        from .physics.reaction_diffusion import ReactionDiffusionSystem
        from .thermodynamics.energy import ThermodynamicsSystem
        from .environment.cycles import BiogeochemicalCycleSystem
        from .environment.climate import ClimateSystem
        from .biology.metabolism import MetabolismSystem, ReproductionSystem, LifecycleSystem
        from .biology.abiogenesis import AbiogenesisProtocol
        from .biology.competition import ResourceCompetitionSystem, TerritorialSystem
        from .biology.immune import ImmuneSystem
        from .biology.epidemiology import EpidemiologySystem
        from .biology.proto_metabolism import ProtoMetabolismSystem
        from .biology.sleep import SleepSystem
        from .biology.pain import PainSystem
        from .biology.play import PlaySystem
        from .biology.stress import StressSystem
        from .biology.economy import EconomySystem
        from .biology.addiction import AddictionSystem
        from .biology.mental_health import MentalHealthSystem
        from .biology.tool_use import ToolUseSystem
        from .biology.politics import PoliticsSystem
        from .biology.corruption import CorruptionSystem
        from .biology.culture import CultureSystem
        from .biology.death_rituals import DeathRitualsSystem
        from .biology.revolution import RevolutionSystem
        from .biology.misinformation import MisinformationSystem
        from .biology.philosophy import PhilosophySystem
        from .biology.first_contact import FirstContactSystem
        from .biology.epistemology import EpistemologySystem
        from .biology.science import ScienceSystem
        from .biology.simulation_awareness import SimulationAwarenessSystem
        from .biology.recursive_improvement import RecursiveImprovementSystem
        from .biology.cognition_levels import CognitiveLevelSystem
        from .biology.observer_effect import ObserverEffectSystem
        from .biology.collective_memory import CollectiveMemorySystem
        from .biology.spatial_indexing import SpatialIndexingSystem
        from .agents.neural import CognitiveSystem
        from .agents.social import SocialSystem
        from .agents.communication import CommunicationSystem
        from .agents.network_science import NetworkScienceSystem
        from .metrics.entropy import MetricsSamplerSystem
        from .metrics.consciousness import ConsciousnessMetricsSystem
        from .energy import EnergyConservationValidator

        self.abiogenesis = AbiogenesisProtocol(self)
        self.energy_validator = EnergyConservationValidator(self)
        self.resource_competition = ResourceCompetitionSystem(self)
        self.territorial = TerritorialSystem(self)

        self.epidemiology = EpidemiologySystem(self)
        self.proto_metabolism = ProtoMetabolismSystem(self)
        self.sleep = SleepSystem(self)
        self.pain = PainSystem(self)
        self.play = PlaySystem(self)
        self.stress = StressSystem(self)
        self.economy = EconomySystem(self)
        self.addiction = AddictionSystem(self)
        self.mental_health = MentalHealthSystem(self)
        self.tool_use = ToolUseSystem(self)
        self.politics = PoliticsSystem(self)
        self.corruption = CorruptionSystem(self)
        self.culture = CultureSystem(self)
        self.death_rituals = DeathRitualsSystem(self)
        self.revolution = RevolutionSystem(self)
        self.misinformation = MisinformationSystem(self)
        self.philosophy = PhilosophySystem(self)
        self.first_contact = FirstContactSystem(self)
        self.epistemology = EpistemologySystem(self)
        self.science = ScienceSystem(self)
        self.simulation_awareness = SimulationAwarenessSystem(self)
        self.recursive_improvement = RecursiveImprovementSystem(self)
        self.cognition_levels = CognitiveLevelSystem(self)
        self.collective_memory = CollectiveMemorySystem(self)
        self.observer_effect = ObserverEffectSystem(self)
        self.spatial_indexing = SpatialIndexingSystem(self)
        self.biogeochemical = BiogeochemicalCycleSystem(self)
        self.climate = ClimateSystem(self)

        self.social = SocialSystem(self)
        self.communication = CommunicationSystem(self)
        self.network_science = NetworkScienceSystem(self)
        self.consciousness = ConsciousnessMetricsSystem(self)

        return [
            PhysicsSystem(self),
            DiffusionSystem(self),
            CellularAutomataSystem(self),
            ReactionDiffusionSystem(self),
            ChemistrySystem(self),
            ThermodynamicsSystem(self),
            self.biogeochemical,
            self.climate,
            self.proto_metabolism,
            MetabolismSystem(self),
            ReproductionSystem(self),
            LifecycleSystem(self),
            ImmuneSystem(self),
            self.epidemiology,
            self.sleep,
            self.pain,
            self.play,
            self.stress,
            self.economy,
            self.addiction,
            self.mental_health,
            self.tool_use,
            self.politics,
            self.corruption,
            self.culture,
            self.death_rituals,
            self.revolution,
            self.misinformation,
            self.philosophy,
            self.first_contact,
            self.epistemology,
            self.science,
            self.simulation_awareness,
            self.recursive_improvement,
            self.cognition_levels,
            self.collective_memory,
            self.observer_effect,
            self.spatial_indexing,
            CognitiveSystem(self),
            self.social,
            self.communication,
            self.network_science,
            MetricsSamplerSystem(self),
            self.consciousness,
            self.energy_validator,
        ]

    def step(self) -> list[WorldEvent]:
        ctx = self._build_tick_context()
        events = []

        energy_before = (
            self.total_energy()
            if hasattr(self, "energy_validator") and self.energy_validator._enabled
            else None
        )

        if _use_profiler:
            timer = get_tick_timer()
            timer.start_tick()

        for system in self.systems:
            if system.should_run(ctx):
                if _use_profiler:
                    timer = get_tick_timer()
                    timer.start_system(system.__class__.__name__)
                system_events = system.update(ctx)
                if _use_profiler:
                    timer.end_system(system.__class__.__name__)
                events.extend(system_events)

        if _use_profiler:
            timer = get_tick_timer()
            timer.start_system("abiogenesis")
        abio_events = self.abiogenesis.process(ctx)
        if _use_profiler:
            timer.end_system("abiogenesis")
        events.extend(abio_events)

        for event in events:
            if event.type == EventType.ABIOGENESIS or event.type == EventType.AGENT_BORN:
                if event.source_id and event.source_id in self.agents:
                    agent = self.agents[event.source_id]
                    if self.observer:
                        species = self.observer.classify_agent(agent)
                        if species:
                            agent.species_label = species
            if self.observer:
                self.observer.process_event(event)

        self.tick += 1
        self.event_bus.publish_batch(events)

        if energy_before is not None and hasattr(self, "energy_validator"):
            energy_after = self.total_energy()
            expected = energy_before + sum(self.energy_validator._tick_changes.values())
            diff = energy_after - expected
            if abs(diff) > self.energy_validator._tolerance * 10:
                self.energy_validator._violations.append(
                    {
                        "tick": self.tick,
                        "before": energy_before,
                        "after": energy_after,
                        "expected": expected,
                        "diff": diff,
                        "sources": dict(self.energy_validator._tick_changes),
                    }
                )
            self.energy_validator._tick_changes.clear()

        return events

    def run(self, max_ticks: int = -1):
        while max_ticks < 0 or self.tick < max_ticks:
            events = self.step()
            self._persist_state_if_needed()

    def total_energy(self) -> float:
        grid_energy = sum(
            sum(pool.values()) for cell in self.grid.values() for pool in [cell.chemical_pool]
        )
        agent_energy = sum(a.energy for a in self.agents.values() if a.is_alive)
        return grid_energy + agent_energy

    def _build_tick_context(self) -> TickContext:
        t = self.tick
        cfg = self.config
        chem_every = cfg.chemistry_per_physics
        bio_every = chem_every * cfg.biology_per_chemistry
        cog_every = bio_every * cfg.cognitive_per_biology
        return TickContext(
            tick=t,
            dt=0.1,
            physics_tick=True,
            chemistry_tick=(t % chem_every == 0),
            biology_tick=(t % bio_every == 0),
            cognitive_tick=(t % cog_every == 0),
            social_tick=(t % (bio_every * 2) == 0),
            geological_tick=(t % (bio_every * 10) == 0),
            ca_tick=(t % cfg.ca_per_physics == 0),
            rd_tick=(t % (chem_every * cfg.rd_per_chemistry) == 0),
            metrics_tick=(t % cfg.metrics_sample_every == 0 and t > 0),
        )

    def _persist_state_if_needed(self):
        if self.tick % 1000 == 0:
            from .systems.persistence import PersistenceManager

            PersistenceManager.save_snapshot(self)
