from ..systems.base import System
from ..types import (
    TickContext,
    WorldEvent,
    EventType,
    Agent,
    AgentStage,
    PersonalityTraits,
    SensoryCapabilities,
)
from .genome import decode_sensory_capabilities
import uuid
import random


class MetabolismSystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        events = []
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            energy_cost = agent.metabolism_rate * agent.mass
            agent.energy -= energy_cost

            if self.world.energy_validator:
                self.world.energy_validator.record_change(f"metabolism_{agent.id}", -energy_cost)

            if agent.energy <= 0:
                agent.is_alive = False
                agent.death_tick = ctx.tick
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.AGENT_DIED,
                        data={"agent_id": agent.id, "cause": "energy_depleted"},
                        source_id=agent.id,
                    )
                )

            agent.age_ticks += 1

        return events


class ReproductionSystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        events = []
        potential_mates = []
        solitary_reproducers = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.stage not in [AgentStage.ADULT, AgentStage.ADOLESCENT]:
                continue
            if agent.energy < agent.reproduction_threshold:
                continue
            if agent.age_ticks < 100:
                continue
            if random.random() < 0.3 and len(potential_mates) > 0:
                potential_mates.append(agent)
            else:
                solitary_reproducers.append(agent)

        random.shuffle(potential_mates)
        paired = []
        for i in range(0, len(potential_mates) - 1, 2):
            parent_a = potential_mates[i]
            parent_b = potential_mates[i + 1]

            fitness_a = self._calculate_fitness(parent_a)
            fitness_b = self._calculate_fitness(parent_b)

            if (
                fitness_a > 0.3
                and fitness_b > 0.3
                and parent_a.energy > 0.6
                and parent_b.energy > 0.6
            ):
                child_genome_a, child_genome_b = parent_a.genome.crossover(parent_b.genome)

                child = Agent(
                    id=f"AG-{uuid.uuid4().hex[:8]}",
                    genome=child_genome_a,
                    birth_tick=ctx.tick,
                    position=parent_a.position,
                    velocity=parent_a.velocity,
                    mass=(parent_a.mass + parent_b.mass) * 0.25,
                    energy=(parent_a.energy + parent_b.energy) * 0.2,
                    health=1.0,
                    parent_ids=[parent_a.id, parent_b.id],
                    personality=self._inherit_personality(parent_a, parent_b),
                    sensory_capabilities=decode_sensory_capabilities(child_genome_a),
                )

                self.world.agents[child.id] = child
                parent_a.children_ids.append(child.id)
                parent_b.children_ids.append(child.id)
                parent_a.energy *= 0.6
                parent_b.energy *= 0.6

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.AGENT_REPRODUCED,
                        data={
                            "parent_a": parent_a.id,
                            "parent_b": parent_b.id,
                            "child_id": child.id,
                        },
                        source_id=parent_a.id,
                        target_id=child.id,
                    )
                )

        for agent in solitary_reproducers[:5]:
            if agent.energy < 0.5:
                continue

            child_genome = agent.genome.mutate()

            child_id = f"AG-{uuid.uuid4().hex[:8]}"
            child = Agent(
                id=child_id,
                genome=child_genome,
                birth_tick=ctx.tick,
                position=agent.position,
                velocity=agent.velocity,
                mass=agent.mass * 0.5,
                energy=agent.energy * 0.3,
                health=1.0,
                parent_ids=[agent.id],
                personality=self._inherit_personality(agent, None),
                sensory_capabilities=decode_sensory_capabilities(child_genome),
            )

            self.world.agents[child_id] = child
            agent.children_ids.append(child_id)
            agent.energy *= 0.5

            if self.world.energy_validator:
                self.world.energy_validator.record_change(
                    f"reproduction_{agent.id}", -agent.energy * 0.5
                )

            cell_x = int(agent.position.x) % self.world.config.grid_width
            cell_y = int(agent.position.y) % self.world.config.grid_height
            cell = self.world.grid.get((cell_x, cell_y))
            if cell:
                cell.agent_ids.append(child_id)

            events.append(
                WorldEvent(
                    tick=ctx.tick,
                    type=EventType.AGENT_REPRODUCED,
                    data={
                        "parent_id": agent.id,
                        "child_id": child_id,
                    },
                    source_id=agent.id,
                    target_id=child_id,
                )
            )

        return events

    def _calculate_fitness(self, agent: Agent) -> float:
        fitness = 0.0

        fitness += agent.energy * 0.3
        fitness += agent.health * 0.3

        if agent.stage == AgentStage.ADULT:
            fitness += 0.2
        elif agent.stage == AgentStage.ADOLESCENT:
            fitness += 0.1

        fitness += min(agent.age_ticks / 1000, 0.2)

        if agent.group_id:
            fitness += 0.1

        return min(1.0, max(0.0, fitness))

    def _inherit_personality(self, parent_a: Agent, parent_b: Agent | None) -> PersonalityTraits:
        HERITABILITY = 0.6
        MUTATION_RATE = 0.1
        MUTATION_MAGNETUDE = 0.1

        def mutate(trait_value: float) -> float:
            if random.random() < MUTATION_RATE:
                return max(
                    0.0,
                    min(1.0, trait_value + random.uniform(-MUTATION_MAGNETUDE, MUTATION_MAGNETUDE)),
                )
            return trait_value

        def clamp(v: float) -> float:
            return max(0.0, min(1.0, v))

        if parent_b is None:
            pa = getattr(parent_a, "personality", None)
            if pa:
                return PersonalityTraits(
                    openness=clamp(mutate(pa.openness)),
                    conscientiousness=clamp(mutate(pa.conscientiousness)),
                    extraversion=clamp(mutate(pa.extraversion)),
                    agreeableness=clamp(mutate(pa.agreeableness)),
                    neuroticism=clamp(mutate(pa.neuroticism)),
                )
            return PersonalityTraits()
        else:
            pa = getattr(parent_a, "personality", None) or PersonalityTraits()
            pb = getattr(parent_b, "personality", None) or PersonalityTraits()

            openness_herit = pa.openness * HERITABILITY + pb.openness * HERITABILITY
            conscientiousness_herit = (
                pa.conscientiousness * HERITABILITY + pb.conscientiousness * HERITABILITY
            )
            extraversion_herit = pa.extraversion * HERITABILITY + pb.extraversion * HERITABILITY
            agreeableness_herit = pa.agreeableness * HERITABILITY + pb.agreeableness * HERITABILITY
            neuroticism_herit = pa.neuroticism * HERITABILITY + pb.neuroticism * HERITABILITY

            openness_complement = abs(pa.openness - pb.openness) * 0.1
            conscientiousness_complement = abs(pa.conscientiousness - pb.conscientiousness) * 0.1
            extraversion_complement = (pa.extraversion + pb.extraversion) / 2.0 * 0.1
            agreeableness_complement = (pa.agreeableness + pb.agreeableness) / 2.0 * 0.1
            neuroticism_complement = abs(pa.neuroticism - pb.neuroticism) * 0.05

            sexual_selection_bonus = random.random() * 0.1
            openness_combined = openness_herit + openness_complement * sexual_selection_bonus
            conscientiousness_combined = (
                conscientiousness_herit + conscientiousness_complement * sexual_selection_bonus
            )
            extraversion_combined = (
                extraversion_herit + extraversion_complement * sexual_selection_bonus
            )
            agreeableness_combined = (
                agreeableness_herit + agreeableness_complement * sexual_selection_bonus
            )
            neuroticism_combined = (
                neuroticism_herit + neuroticism_complement * sexual_selection_bonus
            )

            return PersonalityTraits(
                openness=clamp(mutate(openness_combined / 2.0)),
                conscientiousness=clamp(mutate(conscientiousness_combined / 2.0)),
                extraversion=clamp(mutate(extraversion_combined / 2.0)),
                agreeableness=clamp(mutate(agreeableness_combined / 2.0)),
                neuroticism=clamp(mutate(neuroticism_combined / 2.0)),
            )


class LifecycleSystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            old_stage = agent.stage
            new_stage = self._determine_stage(agent)

            if new_stage != old_stage:
                agent.stage = new_stage
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.AGENT_STAGE_CHANGE,
                        data={
                            "agent_id": agent.id,
                            "from": old_stage.value,
                            "to": new_stage.value,
                        },
                        source_id=agent.id,
                    )
                )

        return events

    def _determine_stage(self, agent: Agent) -> AgentStage:
        age = agent.age_ticks
        thresholds = agent.lifecycle

        if age >= thresholds.elder_at:
            return AgentStage.ELDER
        elif age >= thresholds.adult_at:
            return AgentStage.ADULT
        elif age >= thresholds.adolescent_at:
            return AgentStage.ADOLESCENT
        elif age >= thresholds.juvenile_at:
            return AgentStage.JUVENILE
        else:
            return AgentStage.NEONATAL
