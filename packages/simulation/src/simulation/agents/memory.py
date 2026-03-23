from typing import Optional, List
import numpy as np
import uuid


class QdrantEpisodicMemoryStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "agent_episodes",
        vector_size: int = 128,
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._init_collection()

    def _init_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except (UnexpectedResponse, Exception):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def _encode_episode(self, episode: dict) -> np.ndarray:
        encoding = np.zeros(self.vector_size, dtype=np.float32)

        tick = episode.get("tick", 0)
        agent_id = episode.get("agent_id", "")
        event_type = episode.get("event_type", "")

        encoding[0] = min(tick / 10000, 1.0)

        for i, char in enumerate(agent_id[:32]):
            encoding[i + 1] = ord(char) / 255.0

        type_offset = 50
        type_mapping = {
            "abiogenesis": 0,
            "agent_born": 1,
            "agent_died": 2,
            "agent_reproduced": 3,
            "chemical_reaction": 4,
            "ca_pattern": 5,
        }
        if event_type in type_mapping:
            encoding[type_offset + type_mapping[event_type]] = 1.0

        return encoding

    def store_episode(
        self,
        agent_id: str,
        tick: int,
        event_type: str,
        description: str,
        importance: float = 0.5,
        metadata: Optional[dict] = None,
    ) -> str:
        episode_id = str(uuid.uuid4())

        episode = {
            "agent_id": agent_id,
            "tick": tick,
            "event_type": event_type,
            "description": description,
            "importance": importance,
            "metadata": metadata or {},
        }

        vector = self._encode_episode(episode)

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=episode_id,
                    vector=vector.tolist(),
                    payload={
                        "agent_id": agent_id,
                        "tick": tick,
                        "event_type": event_type,
                        "description": description,
                        "importance": importance,
                        "metadata": metadata or {},
                    },
                )
            ],
        )

        return episode_id

    def retrieve_similar(
        self,
        agent_id: str,
        query_episode: dict,
        limit: int = 5,
        min_importance: float = 0.0,
    ) -> list[dict]:
        vector = self._encode_episode(query_episode)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector.tolist(),
            limit=limit,
            query_filter={
                "must": [
                    {"key": "agent_id", "match": {"value": agent_id}},
                    {
                        "key": "importance",
                        "range": {"gte": min_importance},
                    },
                ]
            },
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "tick": hit.payload["tick"],
                "event_type": hit.payload["event_type"],
                "description": hit.payload["description"],
                "importance": hit.payload["importance"],
                "metadata": hit.payload.get("metadata", {}),
            }
            for hit in results
        ]

    def get_recent_episodes(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> list[dict]:
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "agent_id", "match": {"value": agent_id}},
                ]
            },
            limit=limit,
            order_by={"key": "tick", "direction": "desc"},
        )

        return [
            {
                "id": point.id,
                "tick": point.payload["tick"],
                "event_type": point.payload["event_type"],
                "description": point.payload["description"],
                "importance": point.payload["importance"],
            }
            for point in results[0]
        ]

    def get_memory_summary(self, agent_id: str) -> dict:
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "agent_id", "match": {"value": agent_id}},
                ]
            },
            limit=1000,
        )

        episodes = results[0]

        event_types = {}
        for ep in episodes:
            et = ep.payload["event_type"]
            event_types[et] = event_types.get(et, 0) + 1

        return {
            "agent_id": agent_id,
            "total_episodes": len(episodes),
            "event_types": event_types,
            "memory_coverage": min(len(episodes) / 100, 1.0),
        }


class InMemoryEpisodicStore:
    def __init__(self):
        self.episodes: dict[str, dict] = {}

    def store_episode(
        self,
        agent_id: str,
        tick: int,
        event_type: str,
        description: str,
        importance: float = 0.5,
        metadata: Optional[dict] = None,
    ) -> str:
        episode_id = str(uuid.uuid4())
        self.episodes[episode_id] = {
            "agent_id": agent_id,
            "tick": tick,
            "event_type": event_type,
            "description": description,
            "importance": importance,
            "metadata": metadata or {},
        }
        return episode_id

    def retrieve_similar(
        self,
        agent_id: str,
        query_episode: dict,
        limit: int = 5,
        min_importance: float = 0.0,
    ) -> list[dict]:
        event_type = query_episode.get("event_type", "")
        results = []
        for ep_id, ep in self.episodes.items():
            if ep["agent_id"] == agent_id and ep["importance"] >= min_importance:
                if not event_type or ep["event_type"] == event_type:
                    score = 1.0 if ep["event_type"] == event_type else 0.5
                    results.append(
                        {
                            "id": ep_id,
                            "score": score,
                            "tick": ep["tick"],
                            "event_type": ep["event_type"],
                            "description": ep["description"],
                            "importance": ep["importance"],
                            "metadata": ep.get("metadata", {}),
                        }
                    )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_recent_episodes(self, agent_id: str, limit: int = 10) -> list[dict]:
        agent_eps = [
            {"id": ep_id, **ep} for ep_id, ep in self.episodes.items() if ep["agent_id"] == agent_id
        ]
        agent_eps.sort(key=lambda x: x["tick"], reverse=True)
        return agent_eps[:limit]

    def get_memory_summary(self, agent_id: str) -> dict:
        agent_eps = [ep for ep in self.episodes.values() if ep["agent_id"] == agent_id]
        event_types = {}
        for ep in agent_eps:
            et = ep["event_type"]
            event_types[et] = event_types.get(et, 0) + 1
        return {
            "agent_id": agent_id,
            "total_episodes": len(agent_eps),
            "event_types": event_types,
            "memory_coverage": min(len(agent_eps) / 100, 1.0),
        }


EpisodicMemoryStore = None
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from qdrant_client.http.exceptions import UnexpectedResponse

    EpisodicMemoryStore = QdrantEpisodicMemoryStore
except Exception:
    EpisodicMemoryStore = InMemoryEpisodicStore


class SemanticMemoryStore:
    def __init__(self):
        self.assertions: dict[str, float] = {}
        self.timestamps: dict[str, int] = {}
        self.concept_graph: dict[str, dict[str, list[str]]] = {}

    def add_assertion(
        self, agent_id: str, fact: str, confidence: float, current_tick: int = 0
    ) -> None:
        if fact in self.assertions:
            self.assertions[fact] = min(1.0, self.assertions[fact] + confidence * 0.1)
        else:
            self.assertions[fact] = confidence
        self.timestamps[fact] = current_tick

    def query_assertion(self, fact: str) -> float:
        return self.assertions.get(fact, 0.0)

    def forget_assertion(
        self, fact: str, current_tick: int = 0, decay_threshold: int = 500
    ) -> bool:
        if fact not in self.assertions:
            return False
        if fact in self.timestamps:
            age = current_tick - self.timestamps[fact]
            if age > decay_threshold:
                self.assertions[fact] *= 0.9
                if self.assertions[fact] < 0.1:
                    del self.assertions[fact]
                    self.timestamps.pop(fact, None)
                    return True
        return False

    def bind_concepts(self, concept1: str, concept2: str, relation: str) -> None:
        if concept1 not in self.concept_graph:
            self.concept_graph[concept1] = {}
        if relation not in self.concept_graph[concept1]:
            self.concept_graph[concept1][relation] = []
        if concept2 not in self.concept_graph[concept1][relation]:
            self.concept_graph[concept1][relation].append(concept2)

        if concept2 not in self.concept_graph:
            self.concept_graph[concept2] = {}
        reverse_relation = f"reverse_{relation}"
        if reverse_relation not in self.concept_graph[concept2]:
            self.concept_graph[concept2][reverse_relation] = []
        if concept1 not in self.concept_graph[concept2][reverse_relation]:
            self.concept_graph[concept2][reverse_relation].append(concept1)

    def get_related_concepts(self, concept: str, relation: Optional[str] = None) -> list[str]:
        if concept not in self.concept_graph:
            return []
        if relation is None:
            results = []
            for rel, targets in self.concept_graph[concept].items():
                results.extend(targets)
            return results
        return self.concept_graph[concept].get(relation, [])

    def confidence_decay(self, current_tick: int, decay_rate: float = 0.001) -> int:
        decayed = 0
        for fact in list(self.assertions.keys()):
            if fact in self.timestamps:
                age = current_tick - self.timestamps[fact]
                if age > 100:
                    decay = decay_rate * age
                    self.assertions[fact] = max(0.0, self.assertions[fact] - decay)
                    if self.assertions[fact] < 0.05:
                        del self.assertions[fact]
                        self.timestamps.pop(fact, None)
                        decayed += 1
        return decayed


class ProceduralMemory:
    def __init__(self):
        self.skills: dict[str, float] = {}
        self.skill_proficiency: dict[str, float] = {}
        self.timestamps: dict[str, int] = {}
        self.action_sequences: dict[str, list[tuple[int, list[str], float]]] = {}

    def record_action_sequence(
        self,
        agent_id: str,
        action_sequence: list[str],
        reward: float,
        current_tick: int = 0,
    ) -> None:
        if agent_id not in self.action_sequences:
            self.action_sequences[agent_id] = []
        self.action_sequences[agent_id].append((current_tick, action_sequence, reward))
        if len(self.action_sequences[agent_id]) > 100:
            self.action_sequences[agent_id] = self.action_sequences[agent_id][-100:]

    def get_best_sequence(self, goal: str) -> list[str]:
        from collections import Counter

        if goal not in self.action_sequences:
            return []
        sequences = self.action_sequences[goal]
        if not sequences:
            return []
        seq_counter: Counter[tuple] = Counter()
        for _, actions, reward in sequences:
            if reward > 0:
                seq_counter[tuple(actions)] += reward
        if not seq_counter:
            return []
        best_seq = seq_counter.most_common(1)[0][0]
        return list(best_seq)

    def skill_decay(
        self, current_tick: int, decay_interval: int = 500, decay_amount: float = 0.1
    ) -> int:
        decayed = 0
        for skill_name in list(self.skills.keys()):
            if skill_name in self.timestamps:
                age = current_tick - self.timestamps[skill_name]
                if age > decay_interval:
                    if skill_name in self.skill_proficiency:
                        self.skill_proficiency[skill_name] = max(
                            0.0, self.skill_proficiency[skill_name] - decay_amount
                        )
                    if self.skill_proficiency.get(skill_name, 1.0) < 0.05:
                        del self.skills[skill_name]
                        del self.skill_proficiency[skill_name]
                        self.timestamps.pop(skill_name, None)
                        decayed += 1
        return decayed

    def skill_composition(
        self, skill1: str, skill2: str, new_skill_name: str, current_tick: int = 0
    ) -> bool:
        if skill1 not in self.skills or skill2 not in self.skills:
            return False
        proficiency1 = self.skill_proficiency.get(skill1, 0.0)
        proficiency2 = self.skill_proficiency.get(skill2, 0.0)
        new_proficiency = (proficiency1 + proficiency2) / 2.0
        self.skills[new_skill_name] = self.skills[skill1] + self.skills[skill2]
        self.skill_proficiency[new_skill_name] = new_proficiency
        self.timestamps[new_skill_name] = current_tick
        return True

    def imprint_skill(
        self,
        agent_id: str,
        skill_name: str,
        proficiency: float,
        current_tick: int = 0,
    ) -> None:
        self.skills[skill_name] = proficiency
        self.skill_proficiency[skill_name] = proficiency
        self.timestamps[skill_name] = current_tick

    def get_skill_proficiency(self, skill_name: str) -> float:
        return self.skill_proficiency.get(skill_name, 0.0)


_memory_store: Optional[EpisodicMemoryStore] = None


def get_memory_store() -> EpisodicMemoryStore:
    global _memory_store
    if _memory_store is None:
        try:
            _memory_store = EpisodicMemoryStore()
        except Exception:
            _memory_store = InMemoryEpisodicStore()
    return _memory_store
