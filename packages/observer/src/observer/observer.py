from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ObserverConfig:
    enabled: bool = False
    use_llm_classification: bool = False
    use_llm_narration: bool = False
    memory_store_enabled: bool = True
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    openrouter_api_key: Optional[str] = None
    event_sampling_rate: int = 10


class ObserverLayer:
    def __init__(self, world, config: Optional[ObserverConfig] = None):
        self.world = world
        self.config = config or ObserverConfig()
        self.event_count = 0
        self.species_labels: dict[str, str] = {}
        self.narrations: list[str] = []

        self._init_memory()
        self._init_llm()

    def _init_memory(self):
        if not self.config.memory_store_enabled:
            return

        try:
            from ..agents.memory import get_memory_store

            self.memory_store = get_memory_store()
        except Exception as e:
            print(f"Warning: Could not initialize memory store: {e}")
            self.memory_store = None

    def _init_llm(self):
        if not self.config.use_llm_classification and not self.config.use_llm_narration:
            return

        try:
            from observer import get_client

            self.llm_client = get_client()
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
            self.llm_client = None

    def process_event(self, event) -> Optional[dict]:
        self.event_count += 1

        if self.event_count % self.config.event_sampling_rate != 0:
            return None

        if self.memory_store and event.source_id:
            self._store_episode(event)

        if self.config.use_llm_narration and self.llm_client:
            return self._generate_narration(event)

        return None

    def _store_episode(self, event):
        if not self.memory_store:
            return

        try:
            self.memory_store.store_episode(
                agent_id=event.source_id or "unknown",
                tick=event.tick,
                event_type=event.type.value,
                description=str(event.data),
                importance=self._estimate_importance(event),
                metadata=event.data,
            )
        except Exception as e:
            pass

    def _estimate_importance(self, event) -> float:
        importance_map = {
            "abiogenesis": 1.0,
            "agent_reproduced": 0.9,
            "agent_stage_change": 0.7,
            "agent_born": 0.6,
            "agent_died": 0.5,
            "chemical_reaction": 0.2,
            "ca_pattern": 0.3,
        }
        return importance_map.get(event.type.value, 0.5)

    def _generate_narration(self, event) -> Optional[dict]:
        if not self.llm_client:
            return None

        try:
            from observer.classifier import narrator

            narration_text = narrator.narrate(
                {
                    "type": event.type.value,
                    "tick": event.tick,
                    "data": event.data,
                }
            )

            if narration_text:
                self.narrations.append(narration_text)
                if len(self.narrations) > 100:
                    self.narrations = self.narrations[-50:]

                return {
                    "tick": event.tick,
                    "type": event.type.value,
                    "narration": narration_text,
                }
        except Exception as e:
            pass

        return None

    def classify_agent(self, agent) -> Optional[str]:
        if agent.id in self.species_labels:
            return self.species_labels[agent.id]

        if self.config.use_llm_classification and self.llm_client:
            try:
                from observer.classifier import classifier

                species = classifier.classify_new_agent(
                    {
                        "id": agent.id,
                        "genes_count": len(agent.genome.genes),
                        "neural_complexity": agent.neural_complexity,
                        "energy": agent.energy,
                        "stage": agent.stage.value,
                    }
                )

                if species:
                    self.species_labels[agent.id] = species
                    return species
            except Exception:
                pass

        return self._fallback_classification(agent)

    def _fallback_classification(self, agent) -> str:
        complexity = len(agent.genome.genes)

        if complexity > 15:
            return "Complex Organism"
        elif complexity > 10:
            return "Evolved Cell"
        elif complexity > 5:
            return "Protobiont"
        else:
            return "Simple Life Form"

    def get_observation_summary(self) -> dict:
        return {
            "events_processed": self.event_count,
            "unique_species": len(set(self.species_labels.values())),
            "species_labels": dict(self.species_labels),
            "recent_narrations": self.narrations[-5:],
        }
