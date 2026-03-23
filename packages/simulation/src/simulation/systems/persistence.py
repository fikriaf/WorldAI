import json
import pickle
from pathlib import Path
from typing import Optional
from ..types import WorldState, SimulationConfig


class PersistenceManager:
    _save_dir = Path("saves")

    @classmethod
    def _ensure_dir(cls):
        cls._save_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def save_snapshot(cls, world, filename: Optional[str] = None):
        cls._ensure_dir()

        if filename is None:
            filename = f"snapshot_{world.tick}.json"

        path = cls._save_dir / filename

        snapshot = {
            "tick": world.tick,
            "config": {
                "seed_id": world.config.seed_id,
                "genesis_mode": world.config.genesis_mode,
                "grid_width": world.config.grid_width,
                "grid_height": world.config.grid_height,
            },
            "population": len(world.agents),
            "total_energy": world.total_energy(),
        }

        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2)

        return str(path)

    @classmethod
    def save_full_state(cls, world, filename: Optional[str] = None):
        cls._ensure_dir()

        if filename is None:
            filename = f"world_{world.tick}.pkl"

        path = cls._save_dir / filename

        with open(path, "wb") as f:
            pickle.dump(
                {
                    "tick": world.tick,
                    "config": world.config,
                    "grid": dict(world.grid),
                    "agents": dict(world.agents),
                    "metrics_history": world.metrics_history,
                },
                f,
            )

        return str(path)

    @classmethod
    def load_state(cls, filename: str):
        path = cls._save_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"Save file not found: {filename}")

        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def list_saves(cls):
        cls._ensure_dir()
        return sorted(cls._save_dir.glob("*.pkl")) + sorted(cls._save_dir.glob("*.json"))

    @classmethod
    def delete_save(cls, filename: str):
        path = cls._save_dir / filename
        if path.exists():
            path.unlink()
            return True
        return False

    @classmethod
    def get_save_info(cls, filename: str) -> dict:
        path = cls._save_dir / filename

        if not path.exists():
            return {"error": "File not found"}

        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
                return {
                    "filename": filename,
                    "tick": data.get("tick", "unknown"),
                    "type": "snapshot",
                }

        elif path.suffix == ".pkl":
            return {
                "filename": filename,
                "type": "full_state",
            }

        return {"error": "Unknown file type"}
