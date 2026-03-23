from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/profiling", tags=["profiling"])


@router.get("/stats")
async def get_profiling_stats():
    try:
        from simulation.profiling import get_profiler, get_tick_timer

        profiler = get_profiler()
        tick_timer = get_tick_timer()

        return {
            "profiler": profiler.get_all_stats(),
            "top_slow": [
                {"name": name, "ms": ms} for name, ms in profiler.get_top_slow()
            ],
            "tick_stats": tick_timer.get_tick_stats(),
            "system_stats": tick_timer.get_system_stats(),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Profiler not available")


@router.post("/reset")
async def reset_profiling():
    try:
        from simulation.profiling import get_profiler, get_tick_timer

        profiler = get_profiler()
        tick_timer = get_tick_timer()

        profiler.reset()

        return {"status": "reset"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Profiler not available")


@router.get("/report")
async def get_profiling_report():
    try:
        from simulation.profiling import get_profiler, get_tick_timer

        profiler = get_profiler()
        tick_timer = get_tick_timer()

        return {
            "tick": tick_timer.get_tick_stats(),
            "systems": tick_timer.get_system_stats(),
            "top_functions": profiler.get_top_slow(),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Profiler not available")
