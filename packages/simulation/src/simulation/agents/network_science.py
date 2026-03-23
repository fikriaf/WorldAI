from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent, AgentID
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


@dataclass
class NetworkMetrics:
    agent_id: str
    degree_centrality: float
    betweenness_centrality: float
    clustering_coefficient: float
    eigenvector_centrality: float
    page_rank: float


class NetworkScienceSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._adjacency: Dict[AgentID, set[AgentID]] = {}
        self._network_metrics: Dict[str, NetworkMetrics] = {}
        self._community_ids: Dict[AgentID, int] = {}
        self._community_counter = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._build_adjacency_matrix()
        self._compute_network_metrics()
        self._detect_communities()
        self._compute_collective_intelligence(ctx, events)

        return events

    def _build_adjacency_matrix(self):
        self._adjacency.clear()

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            self._adjacency[agent.id] = set()

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            if agent.group_id:
                for other in self.world.agents.values():
                    if not other.is_alive:
                        continue
                    if other.group_id == agent.group_id:
                        self._adjacency[agent.id].add(other.id)
                        self._adjacency[other.id].add(agent.id)

            for other in self.world.agents.values():
                if other.id == agent.id or not other.is_alive:
                    continue

                dx = other.position.x - agent.position.x
                dy = other.position.y - agent.position.y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < agent.sensory_range * 0.5:
                    self._adjacency[agent.id].add(other.id)

                trust = agent.reputation.get(other.id, 0.5)
                if trust > 0.7:
                    self._adjacency[agent.id].add(other.id)
                    self._adjacency[other.id].add(agent.id)

    def _compute_network_metrics(self):
        agents = list(self._adjacency.keys())
        n = len(agents)

        degree_centrality = {}
        for agent_id in agents:
            degree_centrality[agent_id] = len(self._adjacency.get(agent_id, set())) / max(1, n - 1)

        betweenness = {}
        for agent_id in agents:
            bw = self._compute_betweenness(agent_id, agents)
            betweenness[agent_id] = bw / max(1, (n - 1) * (n - 2) / 2)

        clustering = {}
        for agent_id in agents:
            clustering[agent_id] = self._compute_clustering(agent_id)

        page_rank = self._compute_page_rank(agents)

        eigenvector = self._compute_eigenvector_centrality(agents)

        for agent_id in agents:
            self._network_metrics[agent_id] = NetworkMetrics(
                agent_id=agent_id,
                degree_centrality=degree_centrality.get(agent_id, 0.0),
                betweenness_centrality=betweenness.get(agent_id, 0.0),
                clustering_coefficient=clustering.get(agent_id, 0.0),
                eigenvector_centrality=eigenvector.get(agent_id, 0.0),
                page_rank=page_rank.get(agent_id, 0.0),
            )

    def _compute_betweenness(self, source_id: str, all_agents: List[str]) -> float:
        if source_id not in self._adjacency:
            return 0.0

        paths = 0.0
        for a in all_agents:
            for b in all_agents:
                if a == b or a == source_id or b == source_id:
                    continue
                if self._has_path_through(a, source_id, b, all_agents):
                    paths += 1

        return paths

    def _has_path_through(self, start: str, through: str, end: str, all_agents: List[str]) -> bool:
        visited = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            if current in visited:
                continue
            visited.add(current)
            for neighbor in self._adjacency.get(current, set()):
                if neighbor not in visited:
                    if neighbor == through:
                        visited.add(through)
                    queue.append(neighbor)
        return False

    def _compute_clustering(self, agent_id: str) -> float:
        neighbors = self._adjacency.get(agent_id, set())
        k = len(neighbors)
        if k < 2:
            return 0.0

        edges_between = 0
        neighbors_list = list(neighbors)
        for i in range(k):
            for j in range(i + 1, k):
                if neighbors_list[j] in self._adjacency.get(neighbors_list[i], set()):
                    edges_between += 1

        max_edges = k * (k - 1) / 2
        return edges_between / max_edges if max_edges > 0 else 0.0

    def _compute_page_rank(
        self, agents: List[str], damping: float = 0.85, iterations: int = 20
    ) -> Dict[str, float]:
        n = len(agents)
        if n == 0:
            return {}

        pr = {a: 1.0 / n for a in agents}

        for _ in range(iterations):
            new_pr = {}
            for node in agents:
                rank_sum = 0.0
                for other in agents:
                    if node in self._adjacency.get(other, set()):
                        out_degree = len(self._adjacency.get(other, set()))
                        if out_degree > 0:
                            rank_sum += pr[other] / out_degree
                new_pr[node] = (1 - damping) / n + damping * rank_sum

            total = sum(new_pr.values())
            if total > 0:
                pr = {k: v / total for k, v in new_pr.items()}

        return pr

    def _compute_eigenvector_centrality(
        self, agents: List[str], iterations: int = 20
    ) -> Dict[str, float]:
        n = len(agents)
        if n == 0:
            return {}

        ec = {a: 1.0 for a in agents}

        for _ in range(iterations):
            new_ec = {}
            for node in agents:
                neighbor_sum = sum(
                    ec.get(neighbor, 0.0) for neighbor in self._adjacency.get(node, set())
                )
                new_ec[node] = neighbor_sum

            norm = math.sqrt(sum(v * v for v in new_ec.values()))
            if norm > 0:
                ec = {k: v / norm for k, v in new_ec.items()}
            else:
                ec = {a: 1.0 / n for a in agents}

        return ec

    def _detect_communities(self):
        agents = list(self._adjacency.keys())
        assigned = set()

        community_map: Dict[int, set] = {}

        for agent_id in agents:
            if agent_id in assigned:
                continue

            community_id = len(community_map)
            members = self._bfs_community(agent_id, assigned)
            community_map[community_id] = members
            assigned.update(members)

        self._community_ids.clear()
        for comm_id, members in community_map.items():
            for member in members:
                self._community_ids[member] = comm_id

        self._community_counter = len(community_map)

    def _bfs_community(self, start: str, assigned: set) -> set:
        members = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in assigned:
                continue
            if node in members:
                continue
            members.add(node)
            queue.extend(self._adjacency.get(node, set()))

        return members

    def _compute_collective_intelligence(self, ctx: TickContext, events: list):
        if self._community_counter < 2:
            return

        communities = {}
        for agent_id, comm_id in self._community_ids.items():
            if comm_id not in communities:
                communities[comm_id] = []
            communities[comm_id].append(agent_id)

        for comm_id, members in communities.items():
            if len(members) < 3:
                continue

            avg_cognitive = np.mean(
                [self.world.agents[m].neural_complexity for m in members if m in self.world.agents]
            )

            connectivity = np.mean(
                [
                    self._network_metrics.get(
                        m,
                        NetworkMetrics(
                            agent_id=m,
                            degree_centrality=0,
                            betweenness_centrality=0,
                            clustering_coefficient=0,
                            eigenvector_centrality=0,
                            page_rank=0,
                        ),
                    ).clustering_coefficient
                    for m in members
                    if m in self._network_metrics
                ]
            )

            collective_iq = avg_cognitive * (1.0 + connectivity * 0.5)

            if collective_iq > 5.0 and ctx.tick % 500 == 0:
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "collective_intelligence",
                            "community": comm_id,
                            "members": len(members),
                            "collective_iq": collective_iq,
                        },
                    )
                )

    def get_network_stats(self) -> Dict:
        if not self._network_metrics:
            return {
                "num_nodes": 0,
                "num_communities": 0,
                "avg_clustering": 0.0,
                "avg_betweenness": 0.0,
                "avg_degree": 0.0,
            }

        metrics = list(self._network_metrics.values())
        degrees = [len(self._adjacency.get(m.agent_id, set())) for m in metrics]

        small_world = self._check_small_world()
        small_world_sigma = self._compute_small_world_sigma() if small_world else 0.0
        power_law = self._compute_power_law_fit(degrees)
        robustness = self._compute_robustness()

        return {
            "num_nodes": len(self._adjacency),
            "num_communities": self._community_counter,
            "avg_clustering": float(np.mean([m.clustering_coefficient for m in metrics])),
            "avg_betweenness": float(np.mean([m.betweenness_centrality for m in metrics])),
            "avg_degree": float(np.mean(degrees)) if degrees else 0.0,
            "max_degree": max(degrees) if degrees else 0,
            "is_small_world": small_world,
            "small_world_sigma": small_world_sigma,
            "is_scale_free": power_law["is_scale_free"],
            "power_law_r_squared": power_law["r_squared"],
            "power_law_alpha": power_law["alpha"],
            "robustness_random_failure": robustness["random_failure_survival"],
            "robustness_targeted_attack": robustness["targeted_attack_survival"],
        }

    def _check_small_world(self) -> bool:
        if not self._network_metrics:
            return False

        avg_clustering = np.mean([m.clustering_coefficient for m in self._network_metrics.values()])
        avg_degree = np.mean(
            [len(self._adjacency.get(m.agent_id, set())) for m in self._network_metrics.values()]
        )

        if avg_clustering > 0.3 and avg_degree > 2.0:
            return True
        return False

    def _compute_small_world_sigma(self) -> float:
        """
        Computes the small-world coefficient sigma.
        sigma = (clustering / random_clustering) / (path_length / random_path_length)

        sigma > 2 indicates a small-world network.
        """
        if not self._adjacency or len(self._adjacency) < 3:
            return 0.0

        avg_clustering = np.mean([m.clustering_coefficient for m in self._network_metrics.values()])
        avg_path_length = self._compute_average_path_length()

        n = len(self._adjacency)
        avg_degree = np.mean([len(neighbors) for neighbors in self._adjacency.values()])

        if avg_degree < 1:
            return 0.0

        random_clustering = avg_degree / n
        random_path_length = np.log(n) / np.log(avg_degree) if avg_degree > 1 else 1.0

        if random_clustering == 0 or random_path_length == 0:
            return 0.0

        sigma = (avg_clustering / random_clustering) / (avg_path_length / random_path_length)
        return float(sigma)

    def _compute_average_path_length(self) -> float:
        """Computes the average shortest path length between all pairs of nodes."""
        agents = list(self._adjacency.keys())
        n = len(agents)
        if n < 2:
            return 0.0

        total_path_length = 0.0
        path_count = 0

        for i, start in enumerate(agents):
            distances = self._bfs_distances(start)
            for j, end in enumerate(agents):
                if i >= j:
                    continue
                dist = distances.get(end, float("inf"))
                if dist != float("inf"):
                    total_path_length += dist
                    path_count += 1

        if path_count == 0:
            return float(n)

        return total_path_length / path_count

    def _bfs_distances(self, start: str) -> Dict[str, int]:
        """BFS to compute distances from start to all reachable nodes."""
        distances = {start: 0}
        queue = [start]
        while queue:
            current = queue.pop(0)
            current_dist = distances[current]
            for neighbor in self._adjacency.get(current, set()):
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)
        return distances

    def _compute_power_law_fit(self, degrees: List[int]) -> Dict:
        """
        Fits degree distribution to power law: P(k) ~ k^(-alpha)
        Returns R² and alpha. R² > 0.7 indicates scale-free property.
        """
        if len(degrees) < 5:
            return {"is_scale_free": False, "r_squared": 0.0, "alpha": 0.0}

        degree_counts: Dict[int, int] = {}
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1

        unique_degrees = sorted(degree_counts.keys())
        if len(unique_degrees) < 3:
            return {"is_scale_free": False, "r_squared": 0.0, "alpha": 0.0}

        log_k = [np.log(k) for k in unique_degrees if k > 0]
        log_p = [np.log(degree_counts[k] / len(degrees)) for k in unique_degrees if k > 0]

        if len(log_k) < 3:
            return {"is_scale_free": False, "r_squared": 0.0, "alpha": 0.0}

        coeffs = np.polyfit(log_k, log_p, 1)
        alpha = -coeffs[0]

        fitted_log_p = [coeffs[0] * lk + coeffs[1] for lk in log_k]

        ss_res = sum((lp - fp) ** 2 for lp, fp in zip(log_p, fitted_log_p))
        ss_tot = sum((lp - np.mean(log_p)) ** 2 for lp in log_p)

        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            "is_scale_free": r_squared > 0.7 and alpha > 1 and alpha < 4,
            "r_squared": float(r_squared),
            "alpha": float(alpha),
        }

    def _compute_robustness(self) -> Dict:
        """
        Simulates network resilience to random failures and targeted attacks.
        Returns percentage of nodes that remain connected after 20% failure.
        """
        if len(self._adjacency) < 5:
            return {"random_failure_survival": 100.0, "targeted_attack_survival": 100.0}

        n = len(self._adjacency)
        failure_count = int(n * 0.2)
        if failure_count < 1:
            failure_count = 1

        nodes = list(self._adjacency.keys())
        rng = np.random.default_rng(42)

        random_survived = self._simulate_failures(nodes, failure_count, rng, targeted=False)

        targeted_survived = self._simulate_failures(nodes, failure_count, rng, targeted=True)

        return {
            "random_failure_survival": (random_survived / n) * 100.0,
            "targeted_attack_survival": (targeted_survived / n) * 100.0,
        }

    def _simulate_failures(
        self, nodes: List[str], count: int, rng: np.random.Generator, targeted: bool
    ) -> int:
        """Simulates node failures and counts how many remain connected."""
        if targeted:
            degrees = [(n, len(self._adjacency.get(n, set()))) for n in nodes]
            degrees.sort(key=lambda x: x[1], reverse=True)
            to_remove = [n for n, _ in degrees[:count]]
        else:
            to_remove = list(rng.choice(nodes, size=min(count, len(nodes)), replace=False))

        remaining = [n for n in nodes if n not in to_remove]

        if not remaining:
            return 0

        adj_copy: Dict[str, set] = {}
        for node in remaining:
            neighbors = set(self._adjacency.get(node, set())) - set(to_remove)
            adj_copy[node] = neighbors

        visited = set()
        queue = [remaining[0]]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for neighbor in adj_copy.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)

        return len(visited)

    def get_agent_network_profile(self, agent_id: str) -> Dict:
        if agent_id not in self._network_metrics:
            return {"degree": 0, "community": None, "is_hub": False}

        metrics = self._network_metrics[agent_id]
        degree = len(self._adjacency.get(agent_id, set()))
        comm_id = self._community_ids.get(agent_id)

        return {
            "degree": degree,
            "degree_centrality": metrics.degree_centrality,
            "betweenness_centrality": metrics.betweenness_centrality,
            "clustering": metrics.clustering_coefficient,
            "page_rank": metrics.page_rank,
            "community": comm_id,
            "is_hub": degree > 5,
        }
