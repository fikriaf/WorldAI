from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class MetricsResponse(BaseModel):
    tick: int
    shannon_entropy: float
    effective_complexity: float
    innovation_rate: float
    avg_neural_phi: float
    genome_diversity: float
    population: int
    species_count: int


@router.get("", response_model=MetricsResponse)
async def get_metrics():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    metrics_history = world_manager.world.metrics_history
    if not metrics_history:
        return MetricsResponse(
            tick=world_manager.world.tick,
            shannon_entropy=0.0,
            effective_complexity=0.0,
            innovation_rate=0.0,
            avg_neural_phi=0.0,
            genome_diversity=0.0,
            population=len(world_manager.world.agents),
            species_count=0,
        )

    latest = metrics_history[-1]
    return MetricsResponse(
        tick=latest.get("tick", world_manager.world.tick),
        shannon_entropy=latest.get("shannon_entropy", 0.0),
        effective_complexity=latest.get("effective_complexity", 0.0),
        innovation_rate=latest.get("innovation_rate", 0.0),
        avg_neural_phi=latest.get("avg_neural_phi", 0.0),
        genome_diversity=latest.get("genome_diversity", 0.0),
        population=len(world_manager.world.agents),
        species_count=len(
            set(
                a.species_label
                for a in world_manager.world.agents.values()
                if a.species_label
            )
        ),
    )


@router.get("/history")
async def get_metrics_history(limit: int = 100):
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    history = world_manager.world.metrics_history[-limit:]
    return {"metrics": history}


@router.get("/entropy")
async def get_entropy():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    try:
        from simulation.metrics.entropy import calculate_shannon_entropy

        population = list(world_manager.world.agents.values())
        entropy = calculate_shannon_entropy(population)
        return {"entropy": entropy, "population": len(population)}
    except Exception as e:
        return {"error": str(e)}
