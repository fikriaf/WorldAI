from ..systems.base import System
from ..types import TickContext, WorldEvent
import numpy as np
from collections import defaultdict


class MetricsSamplerSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._population_history: list[int] = []
        self._death_counts: list[int] = []
        self._event_sizes: list[float] = []
        self._innovation_timestamps: list[int] = []

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.metrics_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        metrics = self._compute_metrics(ctx)
        self.world.metrics_history.append(metrics)
        return []

    def _compute_metrics(self, ctx: TickContext) -> dict:
        agents = [a for a in self.world.agents.values() if a.is_alive]

        population = len(agents)
        self._population_history.append(population)

        shannon_entropy = 0.0
        if population > 0:
            energies = [a.energy for a in agents]
            hist, _ = np.histogram(energies, bins=10)
            hist = hist / population
            hist = hist[hist > 0]
            shannon_entropy = -np.sum(hist * np.log(hist))

        genome_diversity = 0.0
        if agents:
            hashes = [a.genome.checksum() for a in agents]
            unique = len(set(hashes))
            genome_diversity = unique / len(hashes)

        power_law = self._compute_power_law_metrics()

        return {
            "tick": ctx.tick,
            "population": population,
            "shannon_entropy": float(shannon_entropy),
            "genome_diversity": float(genome_diversity),
            "innovation_count": len(self._innovation_timestamps),
            "power_law_alpha": power_law.get("alpha", 0),
            "power_law_r2": power_law.get("r_squared", 0),
            "soc_confidence": power_law.get("confidence", 0),
        }

    def _compute_power_law_metrics(self) -> dict:
        if len(self._population_history) < 50:
            return {"alpha": 0, "r_squared": 0, "confidence": 0}

        deltas = []
        for i in range(1, len(self._population_history)):
            delta = abs(self._population_history[i] - self._population_history[i - 1])
            if delta > 0:
                deltas.append(delta)

        if len(deltas) < 20:
            return {"alpha": 0, "r_squared": 0, "confidence": 0}

        deltas = np.array(deltas)
        deltas = np.log(deltas + 1e-10)

        ranks = np.arange(1, len(deltas) + 1)
        log_ranks = np.log(ranks)

        coeffs = np.polyfit(log_ranks, deltas, 1)
        alpha = -coeffs[0]

        pred = np.polyval(coeffs, log_ranks)
        ss_res = np.sum((deltas - pred) ** 2)
        ss_tot = np.sum((deltas - np.mean(deltas)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        confidence = max(0, min(1, r_squared)) if 1.5 <= alpha <= 3.0 else 0

        return {
            "alpha": float(alpha),
            "r_squared": float(r_squared),
            "confidence": float(confidence),
        }

    def record_innovation(self, tick: int):
        self._innovation_timestamps.append(tick)

    def record_event_size(self, size: float):
        self._event_sizes.append(size)

    def get_power_law_stats(self) -> dict:
        return self._compute_power_law_metrics()
