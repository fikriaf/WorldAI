from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/control", tags=["control"])


class InterventionRequest(BaseModel):
    target_id: str
    intervention_type: str  # "boost_energy", "modify_genome", "kill", "teleport"
    parameters: Optional[dict] = None


class AuditLogEntry(BaseModel):
    timestamp: str
    tick: int
    intervention_type: str
    target_id: str
    user: str
    result: str


class GodModeState(BaseModel):
    enabled: bool
    audit_log: List[AuditLogEntry]
    intervention_count: int


_audit_log: List[dict] = []
_god_mode_enabled = False


@router.get("/godmode/state", response_model=GodModeState)
async def get_god_mode_state():
    return GodModeState(
        enabled=_god_mode_enabled,
        audit_log=[AuditLogEntry(**entry) for entry in _audit_log[-50:]],
        intervention_count=len(_audit_log),
    )


@router.post("/godmode/enable")
async def enable_god_mode():
    global _god_mode_enabled
    _god_mode_enabled = True
    return {"status": "enabled", "timestamp": datetime.utcnow().isoformat()}


@router.post("/godmode/disable")
async def disable_god_mode():
    global _god_mode_enabled
    _god_mode_enabled = False
    return {"status": "disabled", "timestamp": datetime.utcnow().isoformat()}


@router.post("/intervene")
async def intervene(req: InterventionRequest):
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    if not _god_mode_enabled:
        raise HTTPException(status_code=403, detail="God mode not enabled")

    target = world_manager.world.agents.get(req.target_id)
    if target is None and req.intervention_type != "spawn":
        raise HTTPException(status_code=404, detail="Target agent not found")

    result = "success"
    try:
        if req.intervention_type == "boost_energy":
            target.energy = min(1.0, target.energy + 0.5)
        elif req.intervention_type == "kill":
            target.is_alive = False
            target.death_tick = world_manager.world.tick
        elif req.intervention_type == "teleport":
            if req.parameters and "x" in req.parameters and "y" in req.parameters:
                target.position.x = req.parameters["x"]
                target.position.y = req.parameters["y"]
        elif req.intervention_type == "modify_genome":
            pass
        elif req.intervention_type == "spawn":
            pass
        else:
            result = "unknown_intervention_type"
    except Exception as e:
        result = f"error: {str(e)}"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tick": world_manager.world.tick,
        "intervention_type": req.intervention_type,
        "target_id": req.target_id,
        "user": "admin",
        "result": result,
    }
    _audit_log.append(log_entry)

    return {"status": result, "log_entry": log_entry}


@router.get("/audit")
async def get_audit_log(limit: int = 50):
    return {"audit_log": _audit_log[-limit:]}


@router.delete("/audit")
async def clear_audit_log():
    global _audit_log
    _audit_log = []
    return {"status": "cleared"}
