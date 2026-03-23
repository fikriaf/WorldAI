import numpy as np
from numba import njit, prange, vectorize


@njit(cache=True, fastmath=True)
def gray_scott_fast(
    u: np.ndarray, v: np.ndarray, F: float, k: float, Du: float, Dv: float, dt: float
) -> tuple[np.ndarray, np.ndarray]:
    H, W = u.shape
    u_new = u.copy()
    v_new = v.copy()

    uvv = u * v * v

    lap_u = np.zeros_like(u)
    lap_v = np.zeros_like(v)

    for y in range(H):
        for x in range(W):
            lap_u[y, x] = (
                u[(y - 1) % H, x]
                + u[(y + 1) % H, x]
                + u[y, (x - 1) % W]
                + u[y, (x + 1) % W]
                - 4.0 * u[y, x]
            )
            lap_v[y, x] = (
                v[(y - 1) % H, x]
                + v[(y + 1) % H, x]
                + v[y, (x - 1) % W]
                + v[y, (x + 1) % W]
                - 4.0 * v[y, x]
            )

    u_new = u + dt * (Du * lap_u - uvv + F * (1.0 - u))
    v_new = v + dt * (Dv * lap_v + uvv - (F + k) * v)

    return np.clip(u_new, 0.0, 1.0), np.clip(v_new, 0.0, 1.0)


@njit(cache=True, parallel=True)
def gray_scott_parallel(
    u: np.ndarray, v: np.ndarray, F: float, k: float, Du: float, Dv: float, dt: float
) -> tuple[np.ndarray, np.ndarray]:
    H, W = u.shape
    u_new = np.empty_like(u)
    v_new = np.empty_like(v)

    for y in prange(H):
        for x in range(W):
            u_val = u[y, x]
            v_val = v[y, x]
            uvv = u_val * v_val * v_val

            lap_u = (
                u[(y - 1) % H, x]
                + u[(y + 1) % H, x]
                + u[y, (x - 1) % W]
                + u[y, (x + 1) % W]
                - 4.0 * u_val
            )
            lap_v = (
                v[(y - 1) % H, x]
                + v[(y + 1) % H, x]
                + v[y, (x - 1) % W]
                + v[y, (x + 1) % W]
                - 4.0 * v_val
            )

            u_new[y, x] = max(0.0, min(1.0, u_val + dt * (Du * lap_u - uvv + F * (1.0 - u_val))))
            v_new[y, x] = max(0.0, min(1.0, v_val + dt * (Dv * lap_v + uvv - (F + k) * v_val)))

    return u_new, v_new


@njit(cache=True)
def init_rd_grid(H: int, W: int, seed_density: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    u = np.ones((H, W), dtype=np.float64)
    v = np.zeros((H, W), dtype=np.float64)

    center_y, center_x = H // 2, W // 2

    for i in range(max(0, center_y - 10), min(H, center_y + 10)):
        for j in range(max(0, center_x - 10), min(W, center_x + 10)):
            dx = i - center_y
            dy = j - center_x
            dist = dx * dx + dy * dy
            if dist < 25:
                if np.random.random() < seed_density:
                    u[i, j] = 0.5
                    v[i, j] = 0.25

    return u, v


def compute_rd_pattern(u: np.ndarray, v: np.ndarray, F: float, k: float) -> np.ndarray:
    pattern = np.zeros_like(u)

    pattern = np.clip(v * 3.0, 0.0, 1.0)

    return pattern


class RDStats:
    def __init__(self):
        self.total_cells = 0
        self.active_cells = 0
        self.avg_v = 0.0
        self.pattern_complexity = 0.0

    def update(self, u: np.ndarray, v: np.ndarray):
        self.total_cells = u.size
        self.active_cells = np.sum(v > 0.01)
        self.avg_v = np.mean(v)

        if self.total_cells > 0:
            variance = np.var(v)
            max_v = np.max(v)
            self.pattern_complexity = variance / max(max_v, 0.001)

        return self

    def to_dict(self) -> dict:
        return {
            "total_cells": int(self.total_cells),
            "active_cells": int(self.active_cells),
            "avg_v": float(self.avg_v),
            "pattern_complexity": float(self.pattern_complexity),
        }


_stats = RDStats()


def get_stats() -> RDStats:
    return _stats
