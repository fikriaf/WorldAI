from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass
class DiseaseState:
    susceptible: int = 0
    infected: int = 0
    recovered: int = 0

    @property
    def total(self) -> int:
        return self.susceptible + self.infected + self.recovered

    @property
    def r0_estimate(self) -> float:
        if self.infected == 0:
            return 0.0
        return self.recovered / max(1, self.infected)


class EpidemiologySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._disease_params = {
            "beta": 0.3,
            "gamma": 0.1,
            "infection_radius": 3.0,
            "mortality_rate": 0.02,
        }
        self._disease_state = DiseaseState()
        self._infection_history: list[DiseaseState] = []
        self._active_outbreaks: list[dict] = []

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._update_disease_state()
        self._process_infections()
        self._process_recovery()

        if ctx.tick % 50 == 0:
            self._infection_history.append(
                DiseaseState(
                    susceptible=self._disease_state.susceptible,
                    infected=self._disease_state.infected,
                    recovered=self._disease_state.recovered,
                )
            )
            if len(self._infection_history) > 100:
                self._infection_history = self._infection_history[-100:]

        return events

    def _update_disease_state(self):
        susceptible = 0
        infected = 0
        recovered = 0

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            if agent.pathogen_exposure > 0.5:
                infected += 1
            elif agent.inflammation_level > 0.3:
                infected += 1
            elif agent.immune_system_strength > 0.6 and agent.pathogen_exposure > 0:
                recovered += 1
            else:
                susceptible += 1

        self._disease_state = DiseaseState(
            susceptible=susceptible, infected=infected, recovered=recovered
        )

    def _process_infections(self):
        beta = self._disease_params["beta"]
        radius = self._disease_params["infection_radius"]

        infected_agents = [
            a for a in self.world.agents.values() if a.is_alive and a.pathogen_exposure > 0.5
        ]

        for susceptible in self.world.agents.values():
            if not susceptible.is_alive:
                continue
            if susceptible.pathogen_exposure > 0.3:
                continue

            for infected in infected_agents:
                dx = susceptible.position.x - infected.position.x
                dy = susceptible.position.y - infected.position.y
                dist = np.sqrt(dx * dx + dy * dy)

                if dist < radius and dist > 0:
                    exposure_prob = beta * (1 - dist / radius)

                    susceptibility = 1.0 - susceptible.immune_system_strength
                    if np.random.random() < exposure_prob * susceptibility:
                        susceptible.pathogen_exposure = min(
                            1.0, susceptible.pathogen_exposure + 0.3
                        )

                        if susceptible.pathogen_exposure > 0.5:
                            self._active_outbreaks.append(
                                {
                                    "tick": self.world.tick,
                                    "location": (susceptible.position.x, susceptible.position.y),
                                    "agent_id": susceptible.id,
                                }
                            )

    def _process_recovery(self):
        gamma = self._disease_params["gamma"]
        mortality = self._disease_params["mortality_rate"]

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.pathogen_exposure < 0.3:
                continue

            if agent.immune_system_strength > 0.5:
                recovery_prob = gamma * agent.immune_system_strength
                if np.random.random() < recovery_prob:
                    agent.pathogen_exposure = max(0, agent.pathogen_exposure - 0.2)
                    agent.inflammation_level = max(0, agent.inflammation_level - 0.1)
                    agent.immune_memory.append(f"pathogen_{self.world.tick}")

            if agent.pathogen_exposure > 0.7:
                death_prob = mortality * (agent.pathogen_exposure - 0.7) / 0.3
                if np.random.random() < death_prob:
                    agent.is_alive = False
                    agent.death_tick = self.world.tick

    def compute_r0(self) -> float:
        if len(self._infection_history) < 10:
            return self._disease_state.r0_estimate

        recent = self._infection_history[-10:]

        infections = [s.infected for s in recent]
        recoveries = [s.recovered for s in recent]

        if sum(infections) > 0:
            return sum(recoveries) / sum(infections)
        return 0.0

    def get_epidemiology_stats(self) -> Dict:
        return {
            "susceptible": self._disease_state.susceptible,
            "infected": self._disease_state.infected,
            "recovered": self._disease_state.recovered,
            "r0": self.compute_r0(),
            "active_outbreaks": len(self._active_outbreaks),
            "outbreak_locations": [
                {"tick": o["tick"], "x": o["location"][0], "y": o["location"][1]}
                for o in self._active_outbreaks[-10:]
            ],
        }

    def is_epidemic(self) -> bool:
        total_pop = self._disease_state.total
        if total_pop == 0:
            return False

        prevalence = self._disease_state.infected / total_pop
        return prevalence > 0.1
