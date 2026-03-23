from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/observer", tags=["observer"])


class ObserverStateResponse:
    pass


@router.get("/state")
async def get_observer_state():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    if (
        not hasattr(world_manager.world, "observer")
        or world_manager.world.observer is None
    ):
        return {"enabled": False, "message": "Observer not enabled"}

    observer = world_manager.world.observer
    summary = observer.get_observation_summary()

    return {
        "enabled": True,
        "events_processed": summary["events_processed"],
        "unique_species": summary["unique_species"],
        "species_labels": summary["species_labels"],
        "recent_narrations": summary["recent_narrations"],
    }


@router.post("/enable")
async def enable_observer():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    world_manager.world.observer_enabled = True
    world_manager.world._init_observer()

    return {"status": "enabled"}


@router.post("/disable")
async def disable_observer():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    world_manager.world.observer_enabled = False
    world_manager.world.observer = None

    return {"status": "disabled"}


@router.get("/species")
async def get_species_list():
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    species_count = {}

    for agent in world_manager.world.agents.values():
        if agent.species_label:
            species_count[agent.species_label] = (
                species_count.get(agent.species_label, 0) + 1
            )

    return {
        "species": [
            {"name": name, "count": count}
            for name, count in sorted(species_count.items(), key=lambda x: -x[1])
        ],
        "total": sum(species_count.values()),
    }


@router.get("/narrations")
async def get_narrations(limit: int = 20):
    from api.main import world_manager

    if world_manager.world is None:
        raise HTTPException(status_code=404, detail="World not running")

    if (
        not hasattr(world_manager.world, "observer")
        or world_manager.world.observer is None
    ):
        return {"narrations": []}

    narrations = world_manager.world.observer.narrations[-limit:]

    return {"narrations": narrations}
