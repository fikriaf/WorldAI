import asyncio
import json
from typing import Optional, Callable
from fastapi import WebSocket
import datetime


class WSConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self._subscriptions: dict[str, list[Callable]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for websocket in self.connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws)

    def subscribe(self, channel: str, callback: Callable):
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        self._subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable):
        if channel in self._subscriptions:
            if callback in self._subscriptions[channel]:
                self._subscriptions[channel].remove(callback)

    async def publish(self, channel: str, message: dict):
        if channel in self._subscriptions:
            for callback in self._subscriptions[channel]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception:
                    pass

        await self.broadcast(message)


ws_manager = WSConnectionManager()


class StreamSimulator:
    def __init__(self, world_manager):
        self.world_manager = world_manager
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_delay = 0.1

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._stream_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _stream_loop(self):
        while self._running:
            if self.world_manager.world:
                step_result = await self.world_manager.step()
                state = await self.world_manager.get_state()

                await ws_manager.broadcast(
                    {
                        "type": "tick",
                        "tick": state.get("tick", 0),
                        "population": state.get("population", 0),
                        "total_energy": state.get("total_energy", 0),
                        "agents": state.get("agents", []),
                        "recent_events": state.get("recent_events", []),
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                    }
                )

            await asyncio.sleep(self._tick_delay)

    def set_speed(self, ticks_per_second: float):
        self._tick_delay = 1.0 / ticks_per_second


_stream_simulator: Optional[StreamSimulator] = None


def get_stream_simulator(world_manager) -> StreamSimulator:
    global _stream_simulator
    if _stream_simulator is None:
        _stream_simulator = StreamSimulator(world_manager)
    return _stream_simulator
