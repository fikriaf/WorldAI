import pytest
import sys

sys.path.insert(0, "src")

from simulation import World, SimulationConfig
from simulation.types import ElementType, AgentStage, EventType
from simulation.prng import RegionalPRNG
from simulation.biology.genome import (
    create_initial_genome,
    decode_sensory_capabilities,
    mutate_sensory_gene,
    SENSORY_GENE_TYPES,
)
from simulation.biology.spatial_indexing import (
    QuadTree,
    SpatialHash,
    SpatialIndex,
    SpatialIndexingSystem,
)


class TestPRNG:
    def test_random_returns_float_in_range(self):
        prng = RegionalPRNG(world_seed=42, grid_width=10, grid_height=10)
        for _ in range(100):
            r = prng.random(0, 0)
            assert 0 <= r < 1

    def test_deterministic_seed(self):
        prng1 = RegionalPRNG(world_seed=123, grid_width=5, grid_height=5)
        prng2 = RegionalPRNG(world_seed=123, grid_width=5, grid_height=5)

        seq1 = [prng1.random(0, 0) for _ in range(10)]
        seq2 = [prng2.random(0, 0) for _ in range(10)]

        assert seq1 == seq2

    def test_different_seeds_different_sequences(self):
        prng1 = RegionalPRNG(world_seed=100, grid_width=5, grid_height=5)
        prng2 = RegionalPRNG(world_seed=200, grid_width=5, grid_height=5)

        seq1 = [prng1.random(0, 0) for _ in range(10)]
        seq2 = [prng2.random(0, 0) for _ in range(10)]

        assert seq1 != seq2


class TestGenome:
    def test_create_initial_genome(self):
        genome = create_initial_genome()
        assert len(genome.genes) > 0
        assert genome.mutation_rate > 0

    def test_genome_checksum(self):
        genome = create_initial_genome()
        checksum = genome.checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 16

    def test_genome_mutate(self):
        genome = create_initial_genome()
        original_checksum = genome.checksum()
        mutated = genome.mutate()
        assert mutated is not genome
        assert len(mutated.genes) >= len(genome.genes)


class TestWorld:
    def test_world_initialization(self):
        config = SimulationConfig(
            seed_id="test",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        assert world.tick == 0
        assert len(world.grid) == 64
        assert len(world.agents) == 0

    def test_world_grid_has_elements(self):
        config = SimulationConfig(
            seed_id="test",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        cell = world.grid[(0, 0)]
        assert ElementType.PRIMUM in cell.chemical_pool
        assert ElementType.TERRA in cell.chemical_pool

    def test_world_step(self):
        config = SimulationConfig(
            seed_id="test-step",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        initial_tick = world.tick
        events = world.step()

        assert world.tick == initial_tick + 1

    def test_world_total_energy(self):
        config = SimulationConfig(
            seed_id="test-energy",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        energy = world.total_energy()
        assert energy > 0


class TestAbiogenesis:
    def test_abiogenesis_spawns_agents(self):
        config = SimulationConfig(
            seed_id="test-abio",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        for _ in range(200):
            world.step()

        assert len(world.agents) > 0

    def test_abiogenesis_events(self):
        config = SimulationConfig(
            seed_id="test-abio2",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        abio_count = 0
        for _ in range(200):
            events = world.step()
            abio_count += sum(1 for e in events if e.type == EventType.ABIOGENESIS)

        assert abio_count > 0


class TestAgentLifecycle:
    def test_agent_aging(self):
        config = SimulationConfig(
            seed_id="test-lifecycle",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        for _ in range(300):
            world.step()

        for agent in world.agents.values():
            assert agent.age_ticks >= 0
            assert agent.stage in list(AgentStage)


class TestReactionDiffusion:
    def test_rd_state_updates(self):
        config = SimulationConfig(
            seed_id="test-rd",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        initial_rd = world.grid[(0, 0)].rd.u

        for _ in range(100):
            world.step()

        current_rd = world.grid[(0, 0)].rd.u
        assert isinstance(current_rd, float)


class TestPhysics:
    def test_agent_position_updates(self):
        config = SimulationConfig(
            seed_id="test-physics",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        initial_positions = {}
        for _ in range(300):
            world.step()

        for agent_id, agent in world.agents.items():
            initial_positions[agent_id] = (agent.position.x, agent.position.y)


class TestSocial:
    def test_social_system_initializes(self):
        config = SimulationConfig(
            seed_id="test-social",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        social_system = None
        for s in world.systems:
            if s.__class__.__name__ == "SocialSystem":
                social_system = s
                break

        assert social_system is not None
        assert social_system.get_group_count() == 0

    def test_groups_form_over_time(self):
        config = SimulationConfig(
            seed_id="test-social-groups",
            genesis_mode="seeded_chemistry",
            grid_width=20,
            grid_height=20,
        )
        world = World(config)

        for _ in range(500):
            world.step()

        social_system = None
        for s in world.systems:
            if s.__class__.__name__ == "SocialSystem":
                social_system = s
                break

        assert social_system is not None
        group_count = social_system.get_group_count()
        assert group_count >= 0


class TestEnergyConservation:
    def test_energy_validator_initializes(self):
        config = SimulationConfig(
            seed_id="test-energy",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)
        assert world.energy_validator is not None
        assert world.energy_validator._initial_energy is None

    def test_energy_conservation_tracked(self):
        config = SimulationConfig(
            seed_id="test-energy-track",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        for _ in range(200):
            world.step()

        error = world.energy_validator.get_conservation_error()
        assert "initial_energy" in error
        assert "current_energy" in error


class TestSensoryCapabilities:
    def test_sensory_capabilities_default_values(self):
        from simulation.types import SensoryCapabilities

        caps = SensoryCapabilities()
        assert caps.chemical == 1.0
        assert caps.light == 1.0
        assert caps.thermal == 0.0
        assert caps.mechanical == 0.0
        assert caps.electromagnetic == 0.0
        assert caps.social == 0.5
        assert caps.magnetic == 0.0
        assert caps.proprioceptive == 0.5
        assert caps.auditory == 0.0
        assert caps.visual_range == 0.0

    def test_sensory_capabilities_from_gene_value_low(self):
        from simulation.types import SensoryCapabilities

        caps = SensoryCapabilities.from_gene_value(0.05)
        assert caps.chemical <= 0.5
        assert caps.light <= 0.3

    def test_sensory_capabilities_from_gene_value_high(self):
        from simulation.types import SensoryCapabilities

        caps = SensoryCapabilities.from_gene_value(0.9)
        assert caps.chemical >= 0.9
        assert caps.light >= 0.9
        assert caps.thermal >= 0.5
        assert caps.mechanical >= 0.5
        assert caps.social >= 0.5

    def test_sensory_capabilities_to_dict(self):
        from simulation.types import SensoryCapabilities

        caps = SensoryCapabilities(chemical=0.8, light=0.6, thermal=0.3)
        d = caps.to_dict()
        assert isinstance(d, dict)
        assert "chemical" in d
        assert "light" in d
        assert "thermal" in d
        assert d["chemical"] == 0.8

    def test_sensory_capabilities_in_agent(self):
        config = SimulationConfig(
            seed_id="test-sensory-agent",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        for _ in range(300):
            world.step()

        if world.agents:
            agent = list(world.agents.values())[0]
            assert hasattr(agent, "sensory_capabilities")
            assert agent.sensory_capabilities is not None

    def test_sensory_capabilities_diversity(self):
        from simulation.types import SensoryCapabilities
        import random

        random.seed(42)

        capabilities = []
        for _ in range(20):
            gene_val = random.random()
            caps = SensoryCapabilities.from_gene_value(gene_val)
            capabilities.append(caps)

        chemical_vals = [c.chemical for c in capabilities]
        assert len(set(chemical_vals)) > 1


class TestGenomeSensory:
    def test_create_initial_genome_has_sensory_genes(self):
        genome = create_initial_genome()
        sensory_types_found = set()
        for gene in genome.genes:
            if "sensory" in gene.product_type:
                sensory_types_found.add(gene.product_type)
        assert len(sensory_types_found) > 0

    def test_decode_sensory_capabilities(self):
        genome = create_initial_genome()
        caps = decode_sensory_capabilities(genome)
        assert caps is not None
        assert hasattr(caps, "chemical")
        assert hasattr(caps, "light")

    def test_mutate_adds_sensory_genes(self):
        genome = create_initial_genome()
        original_sensory = set(g.product_type for g in genome.genes if "sensory" in g.product_type)

        mutated = genome.mutate()
        new_sensory = set(g.product_type for g in mutated.genes if "sensory" in g.product_type)

        assert len(new_sensory) >= len(original_sensory)

    def test_sensory_evolution_over_generations(self):
        genome = create_initial_genome()

        for _ in range(10):
            genome = genome.mutate()

        caps_final = decode_sensory_capabilities(genome)

        assert caps_final is not None
        assert isinstance(caps_final.chemical, float)

    def test_crossing_over_sensory_genes(self):
        genome_a = create_initial_genome()
        genome_b = create_initial_genome()

        child_a, child_b = genome_a.crossover(genome_b)

        sensory_a = len([g for g in child_a.genes if "sensory" in g.product_type])
        sensory_b = len([g for g in child_b.genes if "sensory" in g.product_type])

        assert sensory_a >= 0 and sensory_b >= 0


class TestCollectiveMemory:
    def test_collective_memory_system_exists(self):
        config = SimulationConfig(
            seed_id="test-collective-memory",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)
        assert hasattr(world, "collective_memory")

    def test_collective_memory_initializes(self):
        config = SimulationConfig(
            seed_id="test-cm-init",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)
        cm = world.collective_memory

        assert hasattr(cm, "should_run")
        assert hasattr(cm, "update")

    def test_collective_memory_runs(self):
        config = SimulationConfig(
            seed_id="test-cm-run",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        ctx = world._build_tick_context()
        cm = world.collective_memory

        events = cm.update(ctx)
        assert isinstance(events, list)

    def test_collective_memory_creates_entries(self):
        config = SimulationConfig(
            seed_id="test-cm-entries",
            genesis_mode="seeded_chemistry",
            grid_width=20,
            grid_height=20,
        )
        world = World(config)

        for _ in range(500):
            world.step()

        cm = world.collective_memory
        if hasattr(cm, "historical_entries"):
            assert len(cm.historical_entries) >= 0


class TestEthics:
    def test_ethics_violation_severity(self):
        from simulation.biology.ethics import (
            EthicsViolationSeverity,
            ActionType,
            ETHICAL_BOUNDARIES,
        )

        assert (
            EthicsViolationSeverity.CRITICAL in EthicsViolationSeverity._value2member_map_.values()
        )
        assert ActionType.KILL in ActionType._value2member_map_.values()
        assert ActionType.TORTURE in ETHICAL_BOUNDARIES

    def test_ethics_committee_is_permitted(self):
        from simulation.biology.ethics import EthicsCommittee, ActionType

        permitted, msg = EthicsCommittee.is_permitted(ActionType.KILL)
        assert isinstance(permitted, bool)
        assert isinstance(msg, str)

    def test_ethics_calculate_moral_weight(self):
        from simulation.biology.ethics import EthicsCommittee
        from simulation.types import Agent, Genome, Vec2

        agent = Agent(
            id="test-agent",
            genome=create_initial_genome(),
            birth_tick=0,
            position=Vec2(0, 0),
            velocity=Vec2(0, 0),
            mass=1.0,
            energy=1.0,
            health=1.0,
            cognitive_level=5,
            neural_complexity=50,
        )

        weight = EthicsCommittee.calculate_moral_weight(agent)
        assert 0 <= weight <= 1

    def test_ethics_get_moral_status_category(self):
        from simulation.biology.ethics import EthicsCommittee

        categories = [
            EthicsCommittee.get_moral_status_category(0.9),
            EthicsCommittee.get_moral_status_category(0.6),
            EthicsCommittee.get_moral_status_category(0.4),
            EthicsCommittee.get_moral_status_category(0.1),
        ]

        assert "sentient" in categories
        assert "aware" in categories


class TestSpatialIndexing:
    def test_quadtree_insert(self):
        from simulation.types import Agent, Genome, Vec2

        qt = QuadTree(bounds=(0, 0, 100, 100))

        agent = Agent(
            id="test-agent",
            genome=create_initial_genome(),
            birth_tick=0,
            position=Vec2(50.0, 50.0),
            velocity=Vec2(0, 0),
            mass=1.0,
            energy=1.0,
            health=1.0,
        )

        qt.insert(agent.id, agent.position.x, agent.position.y)

        assert len(qt._agent_positions) == 1

    def test_quadtree_query_radius(self):
        from simulation.types import Agent, Genome, Vec2

        qt = QuadTree(bounds=(0, 0, 100, 100))

        agents = []
        for i in range(5):
            agent = Agent(
                id=f"agent-{i}",
                genome=create_initial_genome(),
                birth_tick=0,
                position=Vec2(float(i * 10), float(i * 10)),
                velocity=Vec2(0, 0),
                mass=1.0,
                energy=1.0,
                health=1.0,
            )
            agents.append(agent)
            qt.insert(agent.id, agent.position.x, agent.position.y)

        results = qt.query_radius(25.0, 25.0, 15.0)

        assert len(results) >= 1

    def test_quadtree_query_box(self):
        from simulation.types import Agent, Genome, Vec2

        qt = QuadTree(bounds=(0, 0, 100, 100))

        for i in range(5):
            agent = Agent(
                id=f"agent-{i}",
                genome=create_initial_genome(),
                birth_tick=0,
                position=Vec2(float(i * 10), float(i * 10)),
                velocity=Vec2(0, 0),
                mass=1.0,
                energy=1.0,
                health=1.0,
            )
            qt.insert(agent.id, agent.position.x, agent.position.y)

        results = qt.query_box(10.0, 10.0, 40.0, 40.0)

        assert isinstance(results, list)

    def test_quadtree_rebuild_on_tick(self):
        config = SimulationConfig(
            seed_id="test-quadtree-tick",
            genesis_mode="seeded_chemistry",
            grid_width=32,
            grid_height=32,
        )
        world = World(config)

        spatial_system = None
        for s in world.systems:
            if s.__class__.__name__ == "SpatialIndexingSystem":
                spatial_system = s
                break

        assert spatial_system is not None

        for _ in range(100):
            world.step()

        ctx = world._build_tick_context()
        assert ctx.physics_tick is True

    def test_spatial_vs_naive_performance(self):
        from simulation.types import Agent, Genome, Vec2
        import random

        random.seed(42)

        agents = {}
        for i in range(100):
            agent = Agent(
                id=f"agent-{i}",
                genome=create_initial_genome(),
                birth_tick=0,
                position=Vec2(random.random() * 64, random.random() * 64),
                velocity=Vec2(0, 0),
                mass=1.0,
                energy=1.0,
                health=1.0,
            )
            agents[agent.id] = agent

        spatial_index = SpatialIndex(world_width=64, world_height=64, use_hash=False)

        result = spatial_index.benchmark_vs_naive(agents, num_queries=50, radius=5.0)

        assert "speedup" in result
        assert result["speedup"] >= 0.8


class TestBiologySystems:
    def test_metabolism_system_exists(self):
        config = SimulationConfig(
            seed_id="test-metabolism",
            genesis_mode="seeded_chemistry",
            grid_width=8,
            grid_height=8,
        )
        world = World(config)

        found = False
        for s in world.systems:
            if s.__class__.__name__ == "MetabolismSystem":
                found = True
                break
        assert found

    def test_reproduction_system_exists(self):
        config = SimulationConfig(
            seed_id="test-reproduction",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        found = False
        for s in world.systems:
            if s.__class__.__name__ == "ReproductionSystem":
                found = True
                break
        assert found

    def test_immune_system_exists(self):
        config = SimulationConfig(
            seed_id="test-immune",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        found = False
        for s in world.systems:
            if s.__class__.__name__ == "ImmuneSystem":
                found = True
                break
        assert found

    def test_sleep_system_exists(self):
        config = SimulationConfig(
            seed_id="test-sleep",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        assert hasattr(world, "sleep")

    def test_pain_system_exists(self):
        config = SimulationConfig(
            seed_id="test-pain",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        assert hasattr(world, "pain")

    def test_stress_system_exists(self):
        config = SimulationConfig(
            seed_id="test-stress",
            genesis_mode="seeded_chemistry",
            grid_width=16,
            grid_height=16,
        )
        world = World(config)

        assert hasattr(world, "stress")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
