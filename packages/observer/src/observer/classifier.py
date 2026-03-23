from typing import Optional
from .client import get_client, OpenRouterClient


class SpeciesClassifier:
    def __init__(self):
        self.client = get_client()

    def classify_new_agent(self, agent_data: dict) -> Optional[str]:
        if not self.client.is_configured():
            return self._fallback_classification(agent_data)

        return self.client.classify_species(agent_data)

    def _fallback_classification(self, agent_data: dict) -> str:
        genes = agent_data.get("genes_count", 0)
        complexity = agent_data.get("neural_complexity", 0)

        if complexity > 10:
            return "Complex Organism"
        elif complexity > 5:
            return "Evolved Cell"
        elif genes > 15:
            return "Gene-Rich Protobiont"
        elif genes > 10:
            return "Standard Protobiont"
        else:
            return "Simple Protobiont"


class EventNarrator:
    def __init__(self):
        self.client = get_client()

    def narrate(self, event: dict) -> str:
        if not self.client.is_configured():
            return self._fallback_narration(event)

        result = self.client.narrate_event(event)
        return result or self._fallback_narration(event)

    def _fallback_narration(self, event: dict) -> str:
        event_type = event.get("type", "unknown")
        tick = event.get("tick", 0)

        narrations = {
            "abiogenesis": f"At tick {tick}, life emerged from primordial chemistry.",
            "agent_born": f"A new organism appeared at tick {tick}.",
            "agent_died": f"An organism ceased metabolic activity at tick {tick}.",
            "agent_reproduced": f"Reproduction event recorded at tick {tick}.",
            "agent_stage_change": f"Development milestone reached at tick {tick}.",
            "chemical_reaction": f"Chemical transformation occurred at tick {tick}.",
            "ca_pattern": f"Emergent pattern detected at tick {tick}.",
        }

        return narrations.get(event_type, f"Event recorded at tick {tick}.")


class PatternAnalyzer:
    def __init__(self):
        self.client = get_client()

    def analyze(self, world_state: dict) -> str:
        if not self.client.is_configured():
            return self._fallback_analysis(world_state)

        result = self.client.analyze_pattern(world_state)
        return result or self._fallback_analysis(world_state)

    def _fallback_analysis(self, world_state: dict) -> str:
        pop = world_state.get("population", 0)

        if pop == 0:
            return "The simulation awaits the emergence of life."
        elif pop < 10:
            return "Early life forms are beginning to emerge."
        elif pop < 100:
            return "A nascent ecosystem is forming with diverse organisms."
        elif pop < 500:
            return "The population is thriving with complex interactions."
        else:
            return "A mature ecosystem has established itself."


classifier = SpeciesClassifier()
narrator = EventNarrator()
analyzer = PatternAnalyzer()
