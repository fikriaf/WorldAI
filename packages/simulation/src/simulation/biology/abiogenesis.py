from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from enum import Enum
import random
import uuid
from ..types import (
    Agent,
    AgentID,
    Genome,
    Gene,
    Vec2,
    ElementType,
    SimulationConfig,
    TickContext,
    WorldEvent,
    EventType,
    PersonalityTraits,
)
from .genome import create_initial_genome, decode_sensory_capabilities

if TYPE_CHECKING:
    from ..world import World


class AbiogenesisMode(Enum):
    PURE = "pure"
    SEEDED_CHEMISTRY = "seeded_chemistry"
    SEEDED_PROTOCELLS = "seeded_protocells"


@dataclass
class AbiogenesisConfig:
    min_TERRA_concentration: float = 2.0
    min_AETHER_concentration: float = 0.5
    min_IGNIS_concentration: float = 0.3
    energy_threshold: float = 5.0
    protobiont_probability: float = 0.01
    autocatalytic_set_probability: float = 0.01
    lipid_bubble_probability: float = 0.02


class AbiogenesisProtocol:
    def __init__(self, world: "World"):
        self.world = world
        self.config = AbiogenesisConfig()
        self.abiosis_ticks: int = 0
        self.total_abios_events: int = 0

    def check_abiosis_conditions(self, x: int, y: int) -> Optional[dict]:
        cell = self.world.grid.get((x, y))
        if not cell:
            return None

        energy = sum(cell.chemical_pool.values())
        if energy < self.config.energy_threshold:
            return None

        terra = cell.chemical_pool.get(ElementType.TERRA, 0)
        aether = cell.chemical_pool.get(ElementType.AETHER, 0)
        ignis = cell.chemical_pool.get(ElementType.IGNIS, 0)

        if terra < self.config.min_TERRA_concentration:
            return None
        if aether < self.config.min_AETHER_concentration:
            return None
        if ignis < self.config.min_IGNIS_concentration:
            return None

        mode = self.world.config.genesis_mode
        if mode == "pure":
            prob = self.config.protobiont_probability
        elif mode == "seeded_chemistry":
            prob = self.config.autocatalytic_set_probability * 2
        else:
            prob = self.config.lipid_bubble_probability * 3

        if random.random() > prob:
            return None

        return {
            "x": x,
            "y": y,
            "terra": terra,
            "aether": aether,
            "ignis": ignis,
            "total_energy": energy,
        }

    def spawn_agent(self, x: int, y: int, ctx: TickContext) -> Agent:
        agent_id = f"AG-{uuid.uuid4().hex[:8]}"
        genome = create_initial_genome()
        sensory = decode_sensory_capabilities(genome)

        position = Vec2(x=float(x), y=float(y))
        velocity = Vec2(x=random.uniform(-0.1, 0.1), y=random.uniform(-0.1, 0.1))

        energy = self.world.config.initial_energy_density * 0.5

        agent = Agent(
            id=agent_id,
            genome=genome,
            birth_tick=ctx.tick,
            position=position,
            velocity=velocity,
            mass=1.0,
            energy=energy,
            health=1.0,
            neural_complexity=len(genome.genes),
            sensory_capabilities=sensory,
            personality=PersonalityTraits(
                openness=random.random(),
                conscientiousness=random.random(),
                extraversion=random.random(),
                agreeableness=random.random(),
                neuroticism=random.random(),
            ),
        )

        return agent

    def process(self, ctx: TickContext) -> list[WorldEvent]:
        events = []
        self.abiosis_ticks += 1

        if ctx.tick % 100 != 0:
            return events

        for (x, y), cell in list(self.world.grid.items()):
            conditions = self.check_abiosis_conditions(x, y)
            if conditions:
                agent = self.spawn_agent(x, y, ctx)
                self.world.agents[agent.id] = agent
                self.total_abios_events += 1

                cell.agent_ids.append(agent.id)

                cell.chemical_pool[ElementType.TERRA] *= 0.7
                cell.chemical_pool[ElementType.AETHER] *= 0.5

                event = WorldEvent(
                    tick=ctx.tick,
                    type=EventType.ABIOGENESIS,
                    data={
                        "agent_id": agent.id,
                        "x": x,
                        "y": y,
                        "conditions": conditions,
                        "abiosis_count": self.total_abios_events,
                    },
                    source_id=agent.id,
                )
                events.append(event)

        return events
