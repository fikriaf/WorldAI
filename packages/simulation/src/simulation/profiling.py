import time
from contextlib import contextmanager
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict
import functools


@dataclass
class ProfilerStats:
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0

    def add(self, elapsed: float):
        self.total_calls += 1
        self.total_time += elapsed
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.avg_time = self.total_time / self.total_calls


class PerformanceProfiler:
    def __init__(self):
        self._stats: dict[str, ProfilerStats] = defaultdict(ProfilerStats)
        self._enabled = True
        self._current_context: Optional[str] = None

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def record(self, name: str, elapsed: float):
        if not self._enabled:
            return
        self._stats[name].add(elapsed)

    @contextmanager
    def profile(self, name: str):
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.record(name, elapsed)

    def get_stats(self, name: str) -> Optional[ProfilerStats]:
        return self._stats.get(name)

    def get_all_stats(self) -> dict[str, dict]:
        return {
            name: {
                "calls": stats.total_calls,
                "total_ms": stats.total_time * 1000,
                "avg_ms": stats.avg_time * 1000,
                "min_ms": stats.min_time * 1000 if stats.min_time != float("inf") else 0,
                "max_ms": stats.max_time * 1000,
            }
            for name, stats in self._stats.items()
        }

    def get_top_slow(self, limit: int = 10) -> list[tuple[str, float]]:
        sorted_stats = sorted(self._stats.items(), key=lambda x: x[1].total_time, reverse=True)
        return [(name, stats.total_time * 1000) for name, stats in sorted_stats[:limit]]

    def reset(self):
        self._stats.clear()

    def print_report(self):
        print("\n=== Performance Profile ===")
        print(f"{'Function':<40} {'Calls':>8} {'Total(ms)':>12} {'Avg(ms)':>10} {'Max(ms)':>10}")
        print("-" * 82)

        for name, stats in sorted(self._stats.items(), key=lambda x: x[1].total_time, reverse=True):
            if stats.total_calls > 0:
                print(
                    f"{name:<40} "
                    f"{stats.total_calls:>8} "
                    f"{stats.total_time * 1000:>12.3f} "
                    f"{stats.avg_time * 1000:>10.3f} "
                    f"{stats.max_time * 1000:>10.3f}"
                )


def profile(name: str = None):
    def decorator(func):
        actual_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = _get_profiler()
            with profiler.profile(actual_name):
                return func(*args, **kwargs)

        wrapper.__profiler_name__ = actual_name
        return wrapper

    return decorator


_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


def _get_profiler() -> PerformanceProfiler:
    return get_profiler()


class TickTimer:
    def __init__(self):
        self.tick_times: list[float] = []
        self.system_times: dict[str, list[float]] = defaultdict(list)
        self._tick_start: Optional[float] = None
        self._system_start: dict[str, float] = {}

    def start_tick(self):
        self._tick_start = time.perf_counter()

    def end_tick(self):
        if self._tick_start:
            elapsed = time.perf_counter() - self._tick_start
            self.tick_times.append(elapsed)
            self._tick_start = None

    def start_system(self, system_name: str):
        self._system_start[system_name] = time.perf_counter()

    def end_system(self, system_name: str):
        if system_name in self._system_start:
            elapsed = time.perf_counter() - self._system_start[system_name]
            self.system_times[system_name].append(elapsed)
            del self._system_start[system_name]

    def get_tick_stats(self) -> dict:
        if not self.tick_times:
            return {}

        return {
            "avg_ms": sum(self.tick_times) / len(self.tick_times) * 1000,
            "min_ms": min(self.tick_times) * 1000,
            "max_ms": max(self.tick_times) * 1000,
            "total_ms": sum(self.tick_times) * 1000,
            "count": len(self.tick_times),
        }

    def get_system_stats(self) -> dict:
        result = {}
        for system, times in self.system_times.items():
            if times:
                result[system] = {
                    "avg_ms": sum(times) / len(times) * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "total_ms": sum(times) * 1000,
                    "count": len(times),
                }
        return result

    def print_report(self):
        print("\n=== Tick Performance ===")
        stats = self.get_tick_stats()
        if stats:
            print(f"Average tick time: {stats['avg_ms']:.3f}ms")
            print(f"Min tick time: {stats['min_ms']:.3f}ms")
            print(f"Max tick time: {stats['max_ms']:.3f}ms")
            print(f"Total ticks: {stats['count']}")

        print("\n=== System Performance ===")
        system_stats = self.get_system_stats()
        for system, stats in sorted(
            system_stats.items(), key=lambda x: x[1]["avg_ms"], reverse=True
        ):
            print(f"{system}: avg={stats['avg_ms']:.3f}ms, max={stats['max_ms']:.3f}ms")


_tick_timer: Optional[TickTimer] = None


def get_tick_timer() -> TickTimer:
    global _tick_timer
    if _tick_timer is None:
        _tick_timer = TickTimer()
    return _tick_timer
