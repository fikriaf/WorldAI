import redis
import json
from typing import Optional, Any
from datetime import datetime


class RedisStateManager:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        world_key: str = "world:current",
        events_key: str = "world:events",
        state_channel: str = "world:state",
    ):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.world_key = world_key
        self.events_key = events_key
        self.state_channel = state_channel
        self._connected = self._check_connection()

    def _check_connection(self) -> bool:
        try:
            self.redis.ping()
            return True
        except Exception:
            return False

    def is_connected(self) -> bool:
        return self._connected

    def save_world_state(self, state: dict) -> bool:
        if not self._connected:
            return False
        try:
            state["_saved_at"] = datetime.utcnow().isoformat()
            self.redis.set(self.world_key, json.dumps(state))
            return True
        except Exception as e:
            print(f"Redis save error: {e}")
            return False

    def load_world_state(self) -> Optional[dict]:
        if not self._connected:
            return None
        try:
            data = self.redis.get(self.world_key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def save_event(self, event: dict) -> bool:
        if not self._connected:
            return False
        try:
            event["_timestamp"] = datetime.utcnow().isoformat()
            self.redis.lpush(self.events_key, json.dumps(event))
            self.redis.ltrim(self.events_key, 0, 9999)
            return True
        except Exception:
            return False

    def get_recent_events(self, limit: int = 100) -> list:
        if not self._connected:
            return []
        try:
            events = self.redis.lrange(self.events_key, 0, limit - 1)
            return [json.loads(e) for e in events]
        except Exception:
            return []

    def publish_state(self, state: dict) -> bool:
        if not self._connected:
            return False
        try:
            state["_timestamp"] = datetime.utcnow().isoformat()
            self.redis.publish(self.state_channel, json.dumps(state))
            return True
        except Exception:
            return False

    def subscribe_state(self, callback):
        if not self._connected:
            return None
        try:
            pubsub = self.redis.pubsub()
            pubsub.subscribe(self.state_channel)
            for message in pubsub.listen():
                if message["type"] == "message":
                    yield json.loads(message["data"])
        except Exception:
            pass

    def save_metrics(self, metrics: dict) -> bool:
        if not self._connected:
            return False
        try:
            key = f"world:metrics:{metrics.get('tick', 0)}"
            self.redis.set(key, json.dumps(metrics))
            self.redis.expire(key, 3600)
            return True
        except Exception:
            return False

    def get_metrics_history(self, limit: int = 100) -> list:
        if not self._connected:
            return []
        try:
            keys = self.redis.keys("world:metrics:*")
            metrics = []
            for key in keys[:limit]:
                data = self.redis.get(key)
                if data:
                    metrics.append(json.loads(data))
            return sorted(metrics, key=lambda x: x.get("tick", 0))
        except Exception:
            return []

    def save_agent_state(self, agent_id: str, state: dict) -> bool:
        if not self._connected:
            return False
        try:
            key = f"world:agent:{agent_id}"
            state["_updated_at"] = datetime.utcnow().isoformat()
            self.redis.set(key, json.dumps(state))
            return True
        except Exception:
            return False

    def get_agent_state(self, agent_id: str) -> Optional[dict]:
        if not self._connected:
            return None
        try:
            key = f"world:agent:{agent_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def increment_counter(self, counter_name: str) -> int:
        if not self._connected:
            return 0
        try:
            return self.redis.incr(counter_name)
        except Exception:
            return 0

    def get_counter(self, counter_name: str) -> int:
        if not self._connected:
            return 0
        try:
            val = self.redis.get(counter_name)
            return int(val) if val else 0
        except Exception:
            return 0

    def clear_all(self) -> bool:
        if not self._connected:
            return False
        try:
            keys = self.redis.keys("world:*")
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception:
            return False


_state_manager: Optional[RedisStateManager] = None


def get_state_manager() -> RedisStateManager:
    global _state_manager
    if _state_manager is None:
        redis_url = "redis://localhost:6379/0"
        _state_manager = RedisStateManager(redis_url)
    return _state_manager
