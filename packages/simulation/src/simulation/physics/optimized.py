import numpy as np
from numba import njit, prange
from typing import Optional


@njit(cache=True)
def verlet_integrate(
    positions: np.ndarray, velocities: np.ndarray, forces: np.ndarray, masses: np.ndarray, dt: float
) -> tuple[np.ndarray, np.ndarray]:
    n = positions.shape[0]
    accelerations = np.zeros((n, 2))
    for i in range(n):
        accelerations[i, 0] = forces[i, 0] / masses[i]
        accelerations[i, 1] = forces[i, 1] / masses[i]

    new_positions = positions + velocities * dt + 0.5 * accelerations * dt * dt
    new_velocities = velocities + accelerations * dt
    return new_positions, new_velocities


@njit(cache=True)
def compute_pairwise_forces_numba(
    positions: np.ndarray, masses: np.ndarray, G: float, cutoff: float, dt: float
) -> np.ndarray:
    n = positions.shape[0]
    forces = np.zeros((n, 2))

    for i in range(n):
        for j in range(i + 1, n):
            dx = positions[j, 0] - positions[i, 0]
            dy = positions[j, 1] - positions[i, 1]
            r_sq = dx * dx + dy * dy
            r = np.sqrt(r_sq)

            if r < 1e-6 or r > cutoff:
                continue

            f = G * masses[i] * masses[j] / r
            fx = f * dx / r
            fy = f * dy / r

            forces[i, 0] += fx
            forces[i, 1] += fy
            forces[j, 0] -= fx
            forces[j, 1] -= fy

    return forces


@njit(cache=True, parallel=True)
def compute_spatial_grid_forces(
    positions: np.ndarray, masses: np.ndarray, grid_size: float, G: float, damping: float
) -> np.ndarray:
    n = positions.shape[0]
    forces = np.zeros((n, 2))

    cell_forces = np.zeros((n, 2))

    for i in prange(n):
        cx = int(positions[i, 0] / grid_size)
        cy = int(positions[i, 1] / grid_size)

        for di in range(-1, 2):
            for dj in range(-1, 2):
                nx = cx + di
                ny = cy + dj

                for j in range(n):
                    if i == j:
                        continue

                    jx = int(positions[j, 0] / grid_size)
                    jy = int(positions[j, 1] / grid_size)

                    if jx == nx and jy == ny:
                        dx = positions[j, 0] - positions[i, 0]
                        dy = positions[j, 1] - positions[i, 1]
                        r_sq = dx * dx + dy * dy

                        if r_sq < 1e-6:
                            continue

                        r = np.sqrt(r_sq)
                        f = G * masses[i] * masses[j] / max(r, 0.1)

                        cell_forces[i, 0] += f * dx / r
                        cell_forces[i, 1] += f * dy / r

    for i in range(n):
        forces[i, 0] = cell_forces[i, 0]
        forces[i, 1] = cell_forces[i, 1]

        forces[i, 0] -= damping * 0.1
        forces[i, 1] -= damping * 0.1

    return forces


@njit(cache=True)
def apply_boundary_conditions(
    positions: np.ndarray, velocities: np.ndarray, width: float, height: float, bounce: float = 0.5
) -> tuple[np.ndarray, np.ndarray]:
    n = positions.shape[0]

    for i in range(n):
        if positions[i, 0] < 0:
            positions[i, 0] = 0
            velocities[i, 0] = -velocities[i, 0] * bounce
        elif positions[i, 0] >= width:
            positions[i, 0] = width - 0.001
            velocities[i, 0] = -velocities[i, 0] * bounce

        if positions[i, 1] < 0:
            positions[i, 1] = 0
            velocities[i, 1] = -velocities[i, 1] * bounce
        elif positions[i, 1] >= height:
            positions[i, 1] = height - 0.001
            velocities[i, 1] = -velocities[i, 1] * bounce

    return positions, velocities


def compute_forces_fast(
    positions: np.ndarray,
    masses: np.ndarray,
    G: float = 0.01,
    damping: float = 0.01,
    cutoff: float = 20.0,
    use_spatial: bool = False,
    grid_size: float = 5.0,
) -> np.ndarray:
    if len(positions) == 0:
        return np.zeros((0, 2))

    if len(positions) < 50 or not use_spatial:
        return compute_pairwise_forces_numba(positions, masses, G, cutoff, damping)
    else:
        return compute_spatial_grid_forces(positions, masses, grid_size, G, damping)
