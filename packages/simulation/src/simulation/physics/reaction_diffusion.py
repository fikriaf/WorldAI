import numpy as np
from ..systems.base import System
from ..types import TickContext, WorldEvent


class ReactionDiffusionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        W = world.config.grid_width
        H = world.config.grid_height
        self.u = np.ones((H, W), dtype=np.float64)
        self.v = np.zeros((H, W), dtype=np.float64)
        self._initialized = False
        self._use_parallel = world.config.grid_width >= 32

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.rd_tick

    def _initialize_rd(self):
        if self._initialized:
            return

        from .rd_optimized import init_rd_grid

        self.u, self.v = init_rd_grid(
            self.world.config.grid_height, self.world.config.grid_width, seed_density=0.01
        )
        self._initialized = True

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        self._initialize_rd()

        chem = self.world.config.chemical

        if self._use_parallel:
            from .rd_optimized import gray_scott_parallel

            self.u, self.v = gray_scott_parallel(
                self.u, self.v, chem.rd_feed_rate, chem.rd_kill_rate, chem.rd_Du, chem.rd_Dv, dt=1.0
            )
        else:
            from .rd_optimized import gray_scott_fast

            self.u, self.v = gray_scott_fast(
                self.u, self.v, chem.rd_feed_rate, chem.rd_kill_rate, chem.rd_Du, chem.rd_Dv, dt=1.0
            )

        for (x, y), cell in self.world.grid.items():
            cell.rd.u = float(self.u[y, x])
            cell.rd.v = float(self.v[y, x])

        return []

    def get_pattern(self) -> np.ndarray:
        from .rd_optimized import compute_rd_pattern

        return compute_rd_pattern(
            self.u,
            self.v,
            self.world.config.chemical.rd_feed_rate,
            self.world.config.chemical.rd_kill_rate,
        )

    def get_stats(self) -> dict:
        from .rd_optimized import get_stats

        stats = get_stats()
        stats.update(self.u, self.v)
        return stats.to_dict()
