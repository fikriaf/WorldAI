import numpy as np


def _pcg32(state: int) -> tuple[int, int]:
    state = (state * 6364136223846793005 + 1442695040888963407) % (2**64)
    xorshifted = ((state >> 18) ^ state) >> 27
    rot = state >> 59
    output = ((xorshifted >> rot) | (xorshifted << ((32 - rot) % 32))) % (2**32)
    return output, state


class RegionalPRNG:
    def __init__(self, world_seed: int, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self._states: dict[tuple[int, int], int] = {}
        for x in range(grid_width):
            for y in range(grid_height):
                region_seed = int(world_seed) ^ (x * 73856093) ^ (y * 19349663)
                self._states[(x, y)] = abs(region_seed) % (2**64)

    def random(self, region_x: int, region_y: int) -> float:
        key = (region_x % self.grid_width, region_y % self.grid_height)
        output, new_state = _pcg32(self._states[key])
        self._states[key] = new_state
        return output / (2**32)

    def randint(self, region_x: int, region_y: int, low: int, high: int) -> int:
        r = self.random(region_x, region_y)
        return low + int(r * (high - low))

    def random_global(self) -> float:
        return self.random(0, 0)

    def choice(self, region_x: int, region_y: int, items: list) -> object:
        idx = self.randint(region_x, region_y, 0, len(items))
        return items[idx]
