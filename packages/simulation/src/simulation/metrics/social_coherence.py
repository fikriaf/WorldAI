import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Optional
from collections import defaultdict


@dataclass
class MutualInformationTracker:
    agent_pairs: Dict[tuple[str, str], list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    observation_window: int = 100

    def record_interaction(self, agent_a: str, agent_b: str, shared_info: float):
        key = tuple(sorted([agent_a, agent_b]))
        self.agent_pairs[key].append(shared_info)
        if len(self.agent_pairs[key]) > self.observation_window:
            self.agent_pairs[key] = self.agent_pairs[key][-self.observation_window :]

    def compute_mutual_information(self, agent_a: str, agent_b: str) -> float:
        key = tuple(sorted([agent_a, agent_b]))
        if key not in self.agent_pairs or len(self.agent_pairs[key]) < 10:
            return 0.0

        observations = np.array(self.agent_pairs[key])
        entropy_x = -np.sum(observations * np.log(observations + 1e-10))
        entropy_y = -np.sum((1 - observations) * np.log(1 - observations + 1e-10))

        joint_entropy = -np.sum(
            observations * np.log(observations + 1e-10)
            + (1 - observations) * np.log(1 - observations + 1e-10)
        )

        if joint_entropy > 0:
            mi = (entropy_x + entropy_y - joint_entropy) / joint_entropy
            return max(0, min(1, mi))
        return 0.0

    def get_average_mi(self) -> float:
        if not self.agent_pairs:
            return 0.0
        total = sum(self.compute_mutual_information(a, b) for a, b in self.agent_pairs.keys())
        return total / len(self.agent_pairs)

    def get_most_connected(self, agent_id: str) -> list[tuple[str, float]]:
        connections = []
        for (a, b), observations in self.agent_pairs.items():
            if agent_id in (a, b):
                other = b if a == agent_id else a
                mi = self.compute_mutual_information(a, b)
                connections.append((other, mi))
        return sorted(connections, key=lambda x: x[1], reverse=True)


class SocialCoherenceSystem:
    def __init__(self, world):
        self.world = world
        self.mi_tracker = MutualInformationTracker()
        self.group_coherence: Dict[str, list[float]] = defaultdict(list)
        self.social_network_metrics = {
            "avg_clustering": 0.0,
            "avg_path_length": 0.0,
            "network_density": 0.0,
        }

    def update(self, ctx) -> list:
        from ..types import WorldEvent, EventType

        events = []
        if not hasattr(ctx, "social_tick") or not ctx.social_tick:
            return events

        self._track_interactions()
        self._compute_network_metrics()
        self._detect_emergent_groups()

        return events

    def _track_interactions(self):
        agents = [a for a in self.world.agents.values() if a.is_alive]

        for i, agent_a in enumerate(agents):
            for agent_b in agents[i + 1 :]:
                dx = agent_a.position.x - agent_b.position.x
                dy = agent_a.position.y - agent_b.position.y
                dist = np.sqrt(dx * dx + dy * dy)

                if dist < agent_a.sensory_range and dist < agent_b.sensory_range:
                    shared_info = 1.0 - (dist / min(agent_a.sensory_range, agent_b.sensory_range))
                    shared_info *= (agent_a.energy + agent_b.energy) / 2

                    if (
                        agent_a.group_id
                        and agent_b.group_id
                        and agent_a.group_id == agent_b.group_id
                    ):
                        shared_info *= 1.5

                    self.mi_tracker.record_interaction(agent_a.id, agent_b.id, shared_info)

    def _compute_network_metrics(self):
        agents = list(self.world.agents.values())
        n = len(agents)
        if n < 2:
            return

        edges = 0
        triangles = 0

        for i, a in enumerate(agents):
            neighbors = []
            for j, b in enumerate(agents):
                if i == j:
                    continue
                dx = a.position.x - b.position.x
                dy = a.position.y - b.position.y
                if np.sqrt(dx * dx + dy * dy) < a.sensory_range:
                    neighbors.append(j)
                    edges += 1

            for j in range(len(neighbors)):
                for k in range(j + 1, len(neighbors)):
                    b_idx = neighbors[j]
                    c_idx = neighbors[k]
                    b = agents[b_idx]
                    c = agents[c_idx]
                    dx = b.position.x - c.position.x
                    dy = b.position.y - c.position.y
                    if np.sqrt(dx * dx + dy * dy) < min(b.sensory_range, c.sensory_range):
                        triangles += 1

        if n > 1:
            max_edges = n * (n - 1) / 2
            self.social_network_metrics["network_density"] = (
                edges / max_edges if max_edges > 0 else 0
            )

        if edges > 0:
            self.social_network_metrics["avg_clustering"] = (
                (2 * triangles) / edges if edges > 0 else 0
            )

    def _detect_emergent_groups(self):
        for group_id, group in self.world._groups.items() if hasattr(self.world, "_groups") else []:
            if len(group.member_ids) < 2:
                continue

            members = [
                self.world.agents[mid] for mid in group.member_ids if mid in self.world.agents
            ]
            if len(members) < 2:
                continue

            avg_energy = np.mean([m.energy for m in members])
            avg_health = np.mean([m.health for m in members])

            mi_values = []
            for i, m1 in enumerate(members):
                for m2 in members[i + 1 :]:
                    mi = self.mi_tracker.compute_mutual_information(m1.id, m2.id)
                    mi_values.append(mi)

            if mi_values:
                coherence = np.mean(mi_values) * (avg_energy + avg_health) / 2
                self.group_coherence[group_id].append(coherence)
                if len(self.group_coherence[group_id]) > 50:
                    self.group_coherence[group_id] = self.group_coherence[group_id][-50:]

    def get_coherence(self, group_id: str) -> float:
        if group_id in self.group_coherence and self.group_coherence[group_id]:
            return np.mean(self.group_coherence[group_id])
        return 0.0

    def get_network_metrics(self) -> dict:
        return dict(self.social_network_metrics)
