from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import json

from .world_manager import world_manager
from .routes import world, observer, profiling, metrics, control
from .websocket.manager import get_stream_simulator, ws_manager

app = FastAPI(
    title="World.ai API",
    description="Genesis Engine API - Emergent Life Simulation",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(world.router)
app.include_router(observer.router)
app.include_router(profiling.router)
app.include_router(metrics.router)
app.include_router(control.router)


@app.get("/")
async def root():
    return {
        "name": "World.ai API",
        "version": "0.2.0",
        "status": "running" if world_manager.world else "idle",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "world_running": world_manager.world is not None,
        "redis_enabled": world_manager._redis_enabled
        if hasattr(world_manager, "_redis_enabled")
        else False,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.websocket("/ws/world")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "ping":
                await ws_manager.send_json(
                    websocket,
                    {
                        "type": "pong",
                        "tick": world_manager.world.tick if world_manager.world else 0,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            elif msg_type == "step":
                if world_manager.world:
                    result = await world_manager.step()
                    state = await world_manager.get_state()
                    await ws_manager.send_json(
                        websocket,
                        {
                            "type": "tick",
                            **result,
                            "state": state,
                        },
                    )

            elif msg_type == "subscribe":
                await ws_manager.send_json(
                    websocket,
                    {
                        "type": "subscribed",
                        "tick": world_manager.world.tick if world_manager.world else 0,
                    },
                )

            elif msg_type == "subscribe_state":
                await ws_manager.send_json(
                    websocket,
                    {
                        "type": "subscribed_state",
                    },
                )

            elif msg_type == "set_speed":
                speed = message.get("speed", 10)
                simulator = get_stream_simulator(world_manager)
                simulator.set_speed(speed)
                await ws_manager.send_json(
                    websocket,
                    {
                        "type": "speed_set",
                        "speed": speed,
                    },
                )

            elif msg_type == "get_state":
                if world_manager.world:
                    state = await world_manager.get_state()
                    await ws_manager.send_json(
                        websocket,
                        {
                            "type": "state",
                            "state": state,
                        },
                    )

            elif msg_type == "get_agent":
                agent_id = message.get("agent_id")
                if agent_id:
                    agent = await world_manager.get_agent(agent_id)
                    await ws_manager.send_json(
                        websocket,
                        {
                            "type": "agent",
                            "agent": agent,
                        },
                    )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        await ws_manager.send_json(websocket, {"type": "error", "message": str(e)})


@app.post("/api/stream/start")
async def start_streaming(ticks_per_second: float = 10.0):
    simulator = get_stream_simulator(world_manager)
    await simulator.start()
    simulator.set_speed(ticks_per_second)
    return {"status": "streaming", "ticks_per_second": ticks_per_second}


@app.post("/api/stream/stop")
async def stop_streaming():
    simulator = get_stream_simulator(world_manager)
    await simulator.stop()
    return {"status": "stopped"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
