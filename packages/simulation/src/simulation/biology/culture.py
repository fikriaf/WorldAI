from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class CulturalTrait:
    name: str
    trait_type: str
    strength: float = 1.0
    origin_tick: int = 0


@dataclass
class CultureState:
    agent_id: str
    cultural_traits: Dict[str, CulturalTrait] = field(default_factory=dict)
    aesthetic_preferences: Dict[str, float] = field(default_factory=dict)
    ritual_practices: List[str] = field(default_factory=list)
    art_production: float = 0.0
    belief_system: List[str] = field(default_factory=list)
    cultural_heritage: List[str] = field(default_factory=list)


class CultureSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._culture_states: Dict[str, CultureState] = {}
        self._transmission_vertical_rate = 0.8
        self._transmission_horizontal_rate = 0.3
        self._transmission_oblique_rate = 0.1

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive or agent.neural_complexity < 1:
                continue

            state = self._get_or_create_state(agent)
            self._transmit_cultural_traits(agent, state, ctx, events)
            self._form_rituals(agent, state, ctx, events)
            self._emergent_art(agent, state, ctx)
            self._form_beliefs(agent, state, ctx)

        return events

    def _get_or_create_state(self, agent: Agent) -> CultureState:
        if agent.id not in self._culture_states:
            self._culture_states[agent.id] = CultureState(agent_id=agent.id)
            self._init_cultural_traits(agent.id)
        return self._culture_states[agent.id]

    def _init_cultural_traits(self, agent_id: str):
        state = self._culture_states[agent_id]
        state.cultural_traits = {
            "cooperation": CulturalTrait("cooperation", "value", 0.5),
            "hierarchy": CulturalTrait("hierarchy", "value", 0.3),
        }
        state.aesthetic_preferences = {"symmetry": 0.3, "color": 0.4, "novelty": 0.2}

    def _transmit_cultural_traits(
        self, agent: Agent, state: CultureState, ctx: TickContext, events: List[WorldEvent]
    ):
        if agent.group_id is None:
            return

        vertical_sources = [
            a
            for a in self.world.agents.values()
            if a.group_id == agent.group_id
            and a.id != agent.id
            and a.is_alive
            and a.stage.value in ["adult", "elder"]
        ]

        for source in vertical_sources:
            source_state = self._get_or_create_state(source)
            for trait_name, trait in source_state.cultural_traits.items():
                if trait_name not in state.cultural_traits:
                    if np.random.random() < self._transmission_vertical_rate * trait.strength:
                        state.cultural_traits[trait_name] = CulturalTrait(
                            name=trait.name,
                            trait_type=trait.trait_type,
                            strength=trait.strength * np.random.uniform(0.8, 1.2),
                            origin_tick=ctx.tick,
                        )

        horizontal_sources = [
            a
            for a in self.world.agents.values()
            if a.group_id == agent.group_id
            and a.id != agent.id
            and a.is_alive
            and a.stage.value in ["juvenile", "adolescent"]
        ]

        for source in horizontal_sources:
            source_state = self._get_or_create_state(source)
            for trait_name, trait in source_state.cultural_traits.items():
                if np.random.random() < self._transmission_horizontal_rate * trait.strength:
                    existing = state.cultural_traits.get(trait_name)
                    if existing:
                        existing.strength = (existing.strength + trait.strength) / 2
                    else:
                        state.cultural_traits[trait_name] = CulturalTrait(
                            name=trait.name,
                            trait_type=trait.trait_type,
                            strength=trait.strength * np.random.uniform(0.7, 1.0),
                            origin_tick=ctx.tick,
                        )

        oblique_sources = [
            a
            for a in self.world.agents.values()
            if a.group_id != agent.group_id and a.is_alive and agent.neural_complexity > 2
        ]

        for source in oblique_sources:
            source_state = self._get_or_create_state(source)
            for trait_name, trait in source_state.cultural_traits.items():
                if np.random.random() < self._transmission_oblique_rate * trait.strength:
                    if trait_name not in state.cultural_traits:
                        state.cultural_traits[trait_name] = CulturalTrait(
                            name=trait.name,
                            trait_type=trait.trait_type,
                            strength=trait.strength * 0.5,
                            origin_tick=ctx.tick,
                        )

    def _form_rituals(
        self, agent: Agent, state: CultureState, ctx: TickContext, events: List[WorldEvent]
    ):
        if agent.stage.value != "adult":
            return

        if len(state.ritual_practices) >= 5:
            return

        social_bonding = agent.emotion.joy + agent.emotion.trust
        if social_bonding > 0.4 and np.random.random() < 0.01:
            new_ritual = f"ritual_{ctx.tick}_{agent.id[:4]}"
            if new_ritual not in state.ritual_practices:
                state.ritual_practices.append(new_ritual)

                if agent.group_id:
                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={"ritual_formed": new_ritual},
                            source_id=agent.id,
                        )
                    )

    def _emergent_art(self, agent: Agent, state: CultureState, ctx: TickContext):
        if agent.neural_complexity < 2:
            return

        aesthetic_score = (
            state.aesthetic_preferences.get("symmetry", 0.3) * 0.4
            + state.aesthetic_preferences.get("color", 0.4) * 0.3
            + state.aesthetic_preferences.get("novelty", 0.2) * 0.3
        )

        social_context = agent.emotion.joy * agent.emotion.trust

        art_potential = (agent.neural_complexity / 5.0) * aesthetic_score * social_context

        if np.random.random() < art_potential:
            state.art_production = min(1.0, state.art_production + 0.1)

        if agent.emotion.joy > 0.6 and np.random.random() < 0.05:
            state.aesthetic_preferences["novelty"] = min(
                1.0, state.aesthetic_preferences.get("novelty", 0) + 0.05
            )

    def _form_beliefs(self, agent: Agent, state: CultureState, ctx: TickContext):
        if agent.neural_complexity < 2:
            return

        uncertainty = 1.0 - agent.emotion.trust

        if uncertainty > 0.5 and np.random.random() < uncertainty * 0.01:
            belief_types = ["materialism", "idealism", "determinism", "spirituality"]
            new_belief = np.random.choice(belief_types)
            if new_belief not in state.belief_system:
                state.belief_system.append(new_belief)

        if len(state.belief_system) > 0 and np.random.random() < 0.02:
            for i, belief in enumerate(state.belief_system):
                if "materialism" in belief and agent.health < 0.3:
                    state.belief_system[i] = "idealism"
                elif "idealism" in belief and agent.emotion.fear > 0.7:
                    state.belief_system[i] = "spirituality"

    def get_culture_stats(self) -> Dict:
        if not self._culture_states:
            return {"total_tracked": 0}

        total_traits = sum(len(s.cultural_traits) for s in self._culture_states.values())
        total_rituals = sum(len(s.ritual_practices) for s in self._culture_states.values())
        avg_art = np.mean([s.art_production for s in self._culture_states.values()])

        return {
            "total_tracked": len(self._culture_states),
            "avg_cultural_traits": total_traits / len(self._culture_states)
            if self._culture_states
            else 0,
            "total_rituals": total_rituals,
            "avg_art_production": avg_art,
        }
