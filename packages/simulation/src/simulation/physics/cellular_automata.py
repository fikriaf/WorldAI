from ..systems.base import System
from ..types import TickContext, WorldEvent


class CellularAutomataSystem(System):
    def __init__(self, world):
        super().__init__(world)
        W = world.config.grid_width
        H = world.config.grid_height
        import numpy as np

        self.gol_grid = np.zeros((H, W), dtype=np.int8)
        self.wire_grid = np.zeros((H, W), dtype=np.int8)
        self._initialized = False

    def _initialize_ca(self):
        import numpy as np

        W = self.world.config.grid_width
        H = self.world.config.grid_height
        prng = self.world.prng
        for y in range(H):
            for x in range(W):
                if prng.random(x, y) < 0.3:
                    self.gol_grid[y, x] = 1
                if prng.random(x, y) < 0.05:
                    self.wire_grid[y, x] = 1
        self._initialized = True

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.ca_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not self._initialized:
            self._initialize_ca()

        import numpy as np

        @np.vectorize
        def gol_step(grid):
            pass

        self.gol_grid = self._gol_step(self.gol_grid)
        self.wire_grid = self._wireworld_step(self.wire_grid)

        for (x, y), cell in self.world.grid.items():
            cell.ca.gol_alive = bool(self.gol_grid[y, x])
            cell.ca.wireworld_state = int(self.wire_grid[y, x])

        return []

    def _gol_step(self, grid):
        import numpy as np

        H, W = grid.shape
        new_grid = np.zeros_like(grid)
        for y in range(H):
            for x in range(W):
                neighbors = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dy == 0 and dx == 0:
                            continue
                        ny = (y + dy) % H
                        nx = (x + dx) % W
                        neighbors += grid[ny, nx]
                if grid[y, x] == 1:
                    new_grid[y, x] = 1 if neighbors in (2, 3) else 0
                else:
                    new_grid[y, x] = 1 if neighbors == 3 else 0
        return new_grid

    def _wireworld_step(self, grid):
        import numpy as np

        H, W = grid.shape
        new_grid = np.copy(grid)
        for y in range(H):
            for x in range(W):
                state = grid[y, x]
                if state == 0:
                    new_grid[y, x] = 0
                elif state == 2:
                    new_grid[y, x] = 3
                elif state == 3:
                    new_grid[y, x] = 1
                elif state == 1:
                    head_neighbors = 0
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dy == 0 and dx == 0:
                                continue
                            ny = (y + dy) % H
                            nx = (x + dx) % W
                            if grid[ny, nx] == 2:
                                head_neighbors += 1
                    if head_neighbors in (1, 2):
                        new_grid[y, x] = 2
        return new_grid
