from openai import OpenAI
from typing import Optional
import os


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "anthropic/claude-3-haiku",
    ):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = base_url
        self.default_model = default_model

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Optional[str]:
        if not self.is_configured():
            return None

        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a scientific observer of an artificial life simulation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return None

    def classify_species(self, agent_data: dict) -> Optional[str]:
        prompt = f"""Classify this emerging life form based on its characteristics:

Agent ID: {agent_data.get("id")}
Genes: {agent_data.get("genes_count", 0)}
Neural Complexity: {agent_data.get("neural_complexity", 0)}
Energy Efficiency: {agent_data.get("energy", 0):.2f}
Stage: {agent_data.get("stage", "unknown")}

Provide a brief species name (1-3 words) that describes this organism's characteristics."""

        return self.generate(prompt, model="anthropic/claude-3-haiku")

    def narrate_event(self, event: dict) -> Optional[str]:
        prompt = f"""Write a brief, scientific narration of this event in the simulation:

Event Type: {event.get("type")}
Tick: {event.get("tick")}
Data: {event.get("data", {})}

Write 1-2 sentences describing what happened, as if documenting a scientific observation."""

        return self.generate(prompt, temperature=0.8)

    def analyze_pattern(self, world_state: dict) -> Optional[str]:
        prompt = f"""Analyze the current state of this artificial life simulation:

Population: {world_state.get("population", 0)}
Total Events: {world_state.get("total_events", 0)}
Shannon Entropy: {world_state.get("shannon_entropy", 0):.3f}

Provide a brief scientific observation about emergent patterns or behaviors."""

        return self.generate(prompt)


_client: Optional[OpenRouterClient] = None


def get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
