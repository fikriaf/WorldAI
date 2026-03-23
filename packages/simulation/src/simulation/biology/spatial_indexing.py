from dataclasses import dataclass, field
from typing import Optional
import math
from ..systems.base import System
from ..types import TickContext, Agent, Vec2, AgentID


@dataclass
class QuadNode:
    bounds: tuple[float, float, float, float]
    agents: list[AgentID] = field(default_factory=list)
    children: Optional[tuple["QuadNode", "QuadNode", "QuadNode", "QuadNode"]] = None

    @property
    def x1(self) -> float:
        return self.bounds[0]

    @property
    def y1(self) -> float:
        return self.bounds[1]

    @property
    def x2(self) -> float:
        return self.bounds[2]

    @property
    def y2(self) -> float:
        return self.bounds[3]

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def is_leaf(self) -> bool:
        return self.children is None


class QuadTree:
    def __init__(
        self,
        bounds: tuple[float, float, float, float],
        max_agents_per_leaf: int = 4,
        max_depth: int = 8,
        depth: int = 0,
    ):
        self.root = QuadNode(bounds=bounds)
        self.max_agents_per_leaf = max_agents_per_leaf
        self.max_depth = max_depth
        self.depth = depth
        self._agent_positions: dict[AgentID, tuple[float, float]] = {}

    def clear(self):
        self.root = QuadNode(bounds=self.root.bounds)
        self._agent_positions.clear()

    def insert(self, agent_id: AgentID, x: float, y: float):
        self._agent_positions[agent_id] = (x, y)
        self._insert_into_node(self.root, agent_id, x, y, self.depth)

    def _insert_into_node(
        self,
        node: QuadNode,
        agent_id: AgentID,
        x: float,
        y: float,
        depth: int,
    ):
        if not self._contains(node, x, y):
            return

        if node.is_leaf:
            if len(node.agents) < self.max_agents_per_leaf or depth >= self.max_depth:
                node.agents.append(agent_id)
            else:
                self._subdivide(node, depth)
                for existing_id in node.agents:
                    if existing_id in self._agent_positions:
                        ex, ey = self._agent_positions[existing_id]
                        self._insert_into_existing_node(node, existing_id, ex, ey, depth + 1)
                node.agents.append(agent_id)
        else:
            self._insert_into_existing_node(node, agent_id, x, y, depth + 1)

    def _insert_into_existing_node(
        self,
        node: QuadNode,
        agent_id: AgentID,
        x: float,
        y: float,
        depth: int,
    ):
        if node.children is None:
            return

        quadrants = self._get_quadrants(node, x, y)
        for quadrant in quadrants:
            self._insert_into_node(quadrant, agent_id, x, y, depth)

    def _subdivide(self, node: QuadNode, depth: int):
        x1, y1, x2, y2 = node.bounds
        cx, cy = node.cx, node.cy

        nw = QuadNode((x1, y1, cx, cy))
        ne = QuadNode((cx, y1, x2, cy))
        sw = QuadNode((x1, cy, cx, y2))
        se = QuadNode((cx, cy, x2, y2))

        node.children = (nw, ne, sw, se)

    def _get_quadrants(
        self,
        node: QuadNode,
        x: float,
        y: float,
    ) -> list[QuadNode]:
        if node.children is None:
            return [node]

        cx, cy = node.cx, node.cy
        quadrants = []

        nw, ne, sw, se = node.children

        if x < cx and y < cy:
            quadrants.append(nw)
        if x >= cx and y < cy:
            quadrants.append(ne)
        if x < cx and y >= cy:
            quadrants.append(sw)
        if x >= cx and y >= cy:
            quadrants.append(se)

        return quadrants if quadrants else [node]

    def _contains(self, node: QuadNode, x: float, y: float) -> bool:
        return node.x1 <= x < node.x2 and node.y1 <= y < node.y2

    def query_radius(self, x: float, y: float, radius: float) -> list[AgentID]:
        results = []
        self._query_radius_node(self.root, x, y, radius, results)
        return results

    def _query_radius_node(
        self,
        node: QuadNode,
        x: float,
        y: float,
        radius: float,
        results: list,
    ):
        if not self._intersects_circle(node, x, y, radius):
            return

        for agent_id in node.agents:
            if agent_id in self._agent_positions:
                ax, ay = self._agent_positions[agent_id]
                if self._distance_squared(x, y, ax, ay) <= radius * radius:
                    results.append(agent_id)

        if not node.is_leaf and node.children:
            for child in node.children:
                self._query_radius_node(child, x, y, radius, results)

    def _intersects_circle(
        self,
        node: QuadNode,
        cx: float,
        cy: float,
        radius: float,
    ) -> bool:
        closest_x = max(node.x1, min(cx, node.x2))
        closest_y = max(node.y1, min(cy, node.y2))

        distance_x = cx - closest_x
        distance_y = cy - closest_y

        return (distance_x * distance_x + distance_y * distance_y) <= (radius * radius)

    def query_box(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[AgentID]:
        results = []
        self._query_box_node(self.root, x1, y1, x2, y2, results)
        return results

    def _query_box_node(
        self,
        node: QuadNode,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        results: list,
    ):
        if not self._intersects_box(node, x1, y1, x2, y2):
            return

        for agent_id in node.agents:
            if agent_id in self._agent_positions:
                ax, ay = self._agent_positions[agent_id]
                if x1 <= ax < x2 and y1 <= ay < y2:
                    results.append(agent_id)

        if not node.is_leaf and node.children:
            for child in node.children:
                self._query_box_node(child, x1, y1, x2, y2, results)

    def _intersects_box(
        self,
        node: QuadNode,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> bool:
        return not (node.x2 < x1 or node.x1 > x2 or node.y2 < y1 or node.y1 > y2)

    @staticmethod
    def _distance_squared(x1: float, y1: float, x2: float, y2: float) -> float:
        dx = x2 - x1
        dy = y2 - y1
        return dx * dx + dy * dy


class SpatialHash:
    def __init__(self, cell_size: float = 10.0):
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list[AgentID]] = {}

    def clear(self):
        self.cells.clear()

    def _get_cell_key(self, x: float, y: float) -> tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert(self, agent_id: AgentID, x: float, y: float):
        key = self._get_cell_key(x, y)
        if key not in self.cells:
            self.cells[key] = []
        if agent_id not in self.cells[key]:
            self.cells[key].append(agent_id)

    def query_radius(self, x: float, y: float, radius: float) -> list[AgentID]:
        results = set()
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        radius_cells = int(math.ceil(radius / self.cell_size))

        for dx in range(-radius_cells, radius_cells + 1):
            for dy in range(-radius_cells, radius_cells + 1):
                key = (cx + dx, cy + dy)
                if key in self.cells:
                    for agent_id in self.cells[key]:
                        results.add(agent_id)

        return list(results)

    def query_box(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[AgentID]:
        results = set()

        cx1 = int(x1 // self.cell_size)
        cy1 = int(y1 // self.cell_size)
        cx2 = int(x2 // self.cell_size)
        cy2 = int(y2 // self.cell_size)

        for cx in range(cx1, cx2 + 1):
            for cy in range(cy1, cy2 + 1):
                key = (cx, cy)
                if key in self.cells:
                    for agent_id in self.cells[key]:
                        results.add(agent_id)

        return list(results)


class SpatialIndex:
    def __init__(
        self,
        world_width: int,
        world_height: int,
        use_hash: bool = False,
        cell_size: float = 10.0,
    ):
        self.world_width = world_width
        self.world_height = world_height
        self.use_hash = use_hash

        if use_hash:
            self.spatial_hash = SpatialHash(cell_size=cell_size)
            self.quadtree = None
        else:
            self.quadtree = QuadTree(bounds=(0.0, 0.0, float(world_width), float(world_height)))
            self.spatial_hash = None

    def clear(self):
        if self.spatial_hash:
            self.spatial_hash.clear()
        if self.quadtree:
            self.quadtree.clear()

    def insert(self, agent_id: AgentID, x: float, y: float):
        if self.spatial_hash:
            self.spatial_hash.insert(agent_id, x, y)
        elif self.quadtree:
            self.quadtree.insert(agent_id, x, y)

    def build_from_agents(self, agents: dict[AgentID, Agent]):
        self.clear()

        for agent_id, agent in agents.items():
            if agent.is_alive:
                self.insert(agent_id, agent.position.x, agent.position.y)

    def query_radius(self, x: float, y: float, radius: float) -> list[AgentID]:
        if self.spatial_hash:
            return self.spatial_hash.query_radius(x, y, radius)
        elif self.quadtree:
            return self.quadtree.query_radius(x, y, radius)
        return []

    def query_box(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[AgentID]:
        if self.spatial_hash:
            return self.spatial_hash.query_box(x1, y1, x2, y2)
        elif self.quadtree:
            return self.quadtree.query_box(x1, y1, x2, y2)
        return []

    def benchmark_vs_naive(
        self,
        agents: dict[AgentID, Agent],
        num_queries: int = 100,
        radius: float = 5.0,
    ) -> dict:
        import time
        import random

        agent_list = list(agents.values())
        if not agent_list:
            return {"speedup": 1.0, "naive_time": 0.0, "index_time": 0.0}

        self.build_from_agents(agents)

        queries = []
        for _ in range(num_queries):
            agent = random.choice(agent_list)
            queries.append((agent.position.x, agent.position.y, radius))

        start = time.perf_counter()
        for x, y, r in queries:
            self.query_radius(x, y, r)
        index_time = time.perf_counter() - start

        start = time.perf_counter()
        for x, y, r in queries:
            results = []
            for other in agent_list:
                if other.is_alive:
                    dx = other.position.x - x
                    dy = other.position.y - y
                    if dx * dx + dy * dy <= r * r:
                        results.append(other.id)
        naive_time = time.perf_counter() - start

        speedup = naive_time / index_time if index_time > 0 else 1.0

        return {
            "speedup": speedup,
            "naive_time": naive_time,
            "index_time": index_time,
            "num_queries": num_queries,
            "num_agents": len(agents),
            "radius": radius,
        }


class SpatialIndexingSystem(System):
    def __init__(
        self,
        world,
        use_spatial_hash: bool = False,
        cell_size: float = 10.0,
    ):
        self.world = world
        self.use_spatial_hash = use_spatial_hash
        self.cell_size = cell_size

        self.spatial_index = SpatialIndex(
            world_width=world.config.grid_width,
            world_height=world.config.grid_height,
            use_hash=use_spatial_hash,
            cell_size=cell_size,
        )

        self._benchmark_results: dict = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.physics_tick

    def update(self, ctx: TickContext) -> list:
        self.spatial_index.build_from_agents(self.world.agents)
        return []

    def query_radius(self, x: float, y: float, radius: float) -> list[AgentID]:
        return self.spatial_index.query_radius(x, y, radius)

    def query_box(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[AgentID]:
        return self.spatial_index.query_box(x1, y1, x2, y2)

    def benchmark_vs_naive(
        self,
        agents: dict[AgentID, Agent],
        num_queries: int = 100,
        radius: float = 5.0,
    ) -> dict:
        import time
        import random

        agent_list = list(agents.values())
        if not agent_list:
            return {"speedup": 1.0, "naive_time": 0.0, "index_time": 0.0}

        self.spatial_index.build_from_agents(agents)

        queries = []
        for _ in range(num_queries):
            agent = random.choice(agent_list)
            queries.append((agent.position.x, agent.position.y, radius))

        start = time.perf_counter()
        for x, y, r in queries:
            self.spatial_index.query_radius(x, y, r)
        index_time = time.perf_counter() - start

        start = time.perf_counter()
        for x, y, r in queries:
            results = []
            for other in agent_list:
                if other.is_alive:
                    dx = other.position.x - x
                    dy = other.position.y - y
                    if dx * dx + dy * dy <= r * r:
                        results.append(other.id)
        naive_time = time.perf_counter() - start

        speedup = naive_time / index_time if index_time > 0 else 1.0

        self._benchmark_results = {
            "speedup": speedup,
            "naive_time": naive_time,
            "index_time": index_time,
            "num_queries": num_queries,
            "num_agents": len(agents),
            "radius": radius,
        }

        return self._benchmark_results

    def get_benchmark_results(self) -> dict:
        return self._benchmark_results
