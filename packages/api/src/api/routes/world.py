from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/api/world", tags=["world"])


class WorldStartRequest(BaseModel):
    seed_id: str = "default"
    grid_width: int = 64
    grid_height: int = 64
    genesis_mode: str = "seeded_chemistry"


class AgentResponse(BaseModel):
    id: str
    position_x: float
    position_y: float
    energy: float
    health: float
    age_ticks: int
    stage: str
    genome_hash: str
    parent_count: int
    children_count: int


class WorldStateResponse(BaseModel):
    tick: int
    population: int
    total_energy: float
    agents: list[AgentResponse]
    recent_events: list[dict]


class WorldStatsResponse(BaseModel):
    tick: int
    population: int
    births_total: int
    deaths_total: int
    chemistry_events: int
    total_energy: float


@router.post("/start")
async def start_world(req: WorldStartRequest):
    from .main import world_manager

    try:
        world_id = await world_manager.create_world(
            seed_id=req.seed_id,
            grid_width=req.grid_width,
            grid_height=req.grid_height,
            genesis_mode=req.genesis_mode,
        )
        return {"status": "started", "world_id": world_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_world():
    from .main import world_manager

    await world_manager.stop_world()
    return {"status": "stopped"}


@router.get("/state", response_model=WorldStateResponse)
async def get_state():
    from .main import world_manager

    state = await world_manager.get_state()
    if state is None:
        raise HTTPException(status_code=404, detail="World not running")
    return state


@router.get("/stats", response_model=WorldStatsResponse)
async def get_stats():
    from .main import world_manager

    stats = await world_manager.get_stats()
    if stats is None:
        raise HTTPException(status_code=404, detail="World not running")
    return stats


@router.post("/step")
async def step_world():
    from .main import world_manager

    try:
        result = await world_manager.step()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_world(ticks: int = 100):
    from .main import world_manager

    try:
        result = await world_manager.run(ticks)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_id}")
async def get_agent(agent_id: str):
    from .main import world_manager

    agent = await world_manager.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/events")
async def get_events(limit: int = 50):
    from .main import world_manager

    events = await world_manager.get_recent_events(limit)
    return {"events": events}
