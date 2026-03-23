import torch
import torch.nn as nn
import numpy as np
from typing import Optional
from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent, AgentID, Vec2, SensoryInput
from ..biology.genome import create_initial_genome


class HebbianLayer(nn.Module):
    def __init__(self, input_size: int, output_size: int, learning_rate: float = 0.01):
        super().__init__()
        self.weights = torch.randn(input_size, output_size) * 0.1
        self.weights.requires_grad_(False)
        self.pre_trace = torch.zeros(input_size)
        self.learning_rate = learning_rate

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.pre_trace = x.detach().clone()
        return torch.tanh(x @ self.weights)

    def hebbian_update(self, post_activations: torch.Tensor, reward: float):
        delta = self.learning_rate * reward * torch.outer(post_activations, self.pre_trace)
        self.weights += delta


class AgentBrain(nn.Module):
    def __init__(self, input_size: int = 12, hidden_size: int = 8, output_size: int = 4):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.sensory_layer = HebbianLayer(input_size, hidden_size)
        self.hidden_layer = HebbianLayer(hidden_size, hidden_size)
        self.output_layer = nn.Linear(hidden_size, output_size)

        self.sensory_pre = torch.zeros(input_size)
        self.hidden_pre = torch.zeros(hidden_size)
        self._last_output = torch.zeros(output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.sensory_pre = x.detach()
        sensory_out = self.sensory_layer(x)

        self.hidden_pre = sensory_out.detach()
        hidden_out = self.hidden_layer(sensory_out)

        output = torch.tanh(self.output_layer(hidden_out))
        self._last_output = output.detach()
        return output

    def learn(self, reward: float):
        if reward == 0:
            return

        self.sensory_layer.hebbian_update(self._last_output, reward)
        self.hidden_layer.hebbian_update(self._last_output, reward)


class CognitiveSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.brains: dict[AgentID, AgentBrain] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent_id, agent in list(self.world.agents.items()):
            if not agent.is_alive:
                continue

            brain = self._get_or_create_brain(agent)

            sensory = self._build_sensory_input(agent)
            sensory_tensor = torch.tensor(sensory, dtype=torch.float32)

            with torch.no_grad():
                decision = brain(sensory_tensor)

            action = self._decode_action(decision, agent)

            self._apply_action(agent, action)

            reward = self._compute_reward(agent)
            brain.learn(reward)

        return events

    def _get_or_create_brain(self, agent: Agent) -> AgentBrain:
        if agent.id not in self.brains:
            caps = getattr(agent, "sensory_capabilities", None)
            sensory_channels = 5
            if caps:
                sensory_channels = sum(
                    [
                        caps.chemical > 0.3,
                        caps.light > 0.3,
                        caps.thermal > 0.3,
                        caps.mechanical > 0.3,
                        caps.electromagnetic > 0.3,
                        caps.social > 0.3,
                        caps.magnetic > 0.3,
                        caps.proprioceptive > 0.3,
                        caps.auditory > 0.3,
                        caps.visual_range > 0.3,
                    ]
                )
            genome_complexity = len(agent.genome.genes)
            input_size = min(16, max(6, 5 + sensory_channels + genome_complexity // 10))
            hidden_size = min(12, 4 + genome_complexity // 10)
            self.brains[agent.id] = AgentBrain(input_size, hidden_size, 4)
        return self.brains[agent.id]

    def _build_sensory_input(self, agent: Agent) -> list[float]:
        caps = getattr(agent, "sensory_capabilities", None)
        if caps is None:
            from ..types import SensoryCapabilities

            caps = SensoryCapabilities()

        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))

        sensory = [
            agent.energy,
            agent.health,
            float(agent.age_ticks) / 1000.0,
            agent.emotion.fear,
            agent.emotion.joy,
        ]

        if cell:
            sensory.append(cell.temperature / 100.0 * caps.thermal + 0.5 * (1.0 - caps.thermal))
            sensory.append(cell.light_level * caps.light + 0.5 * (1.0 - caps.light))
            sensory.append(
                sum(cell.chemical_pool.values()) / 20.0 * caps.chemical
                + 0.5 * (1.0 - caps.chemical)
            )

            sensory.append(
                cell.chemical_pool.get(self.world.config.chemical.element_set[0], 0)
                / 5.0
                * caps.chemical
            )
            sensory.append(len(cell.agent_ids) / 10.0 * caps.social + 0.5 * (1.0 - caps.social))
            sensory.append(1.0 if cell.ca.gol_alive else 0.0)
        else:
            sensory.extend([0.5] * 7)

        nearby_energy = 0.0
        nearby_count = 0
        nearby_thermal = 0.0
        nearby_mech = 0.0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < agent.sensory_range:
                nearby_energy += other.energy
                nearby_count += 1
                other_caps = getattr(other, "sensory_capabilities", None) or caps
                nearby_thermal += other_caps.thermal / max(1, dist)
                nearby_mech += other_caps.mechanical / max(1, dist)

        sensory.append(nearby_energy / 10.0 * caps.social + 0.5 * (1.0 - caps.social))
        sensory.append(nearby_count / 10.0 * caps.social + 0.5 * (1.0 - caps.social))

        sensory.append(nearby_thermal / max(1, nearby_count) * caps.thermal)
        sensory.append(nearby_mech / max(1, nearby_count) * caps.mechanical)

        sensory.append(caps.proprioceptive * (agent.energy - 0.5) * 2.0)

        sensory.append(
            caps.visual_range * min(1.0, nearby_count / 5.0) if caps.visual_range > 0 else 0.0
        )

        sensory.append(
            caps.auditory * caps.social * min(1.0, nearby_count / 3.0) if caps.auditory > 0 else 0.0
        )

        brain = self.brains.get(agent.id)
        target_size = brain.input_size if brain else 12
        while len(sensory) < target_size:
            sensory.append(0.0)
        return sensory[:target_size]

    def _decode_action(self, decision: torch.Tensor, agent: Agent) -> dict:
        action = decision.numpy()

        move_x = np.clip(action[0], -1, 1)
        move_y = np.clip(action[1], -1, 1)
        speed = max(0, action[2]) * 0.5
        emit_prob = max(0, min(1, action[3]))

        return {
            "move_direction": Vec2(move_x, move_y),
            "move_speed": speed,
            "emit_chemical": emit_prob > 0.5,
        }

    def _apply_action(self, agent: Agent, action: dict):
        direction = action["move_direction"]
        speed = action["move_speed"]

        if direction.magnitude() > 0.1:
            norm_dir = direction.normalized()
            agent.velocity.x += norm_dir.x * speed
            agent.velocity.y += norm_dir.y * speed

        if action["emit_chemical"]:
            cell_x = int(agent.position.x) % self.world.config.grid_width
            cell_y = int(agent.position.y) % self.world.config.grid_height
            cell = self.world.grid.get((cell_x, cell_y))
            if cell and agent.energy > 0.3:
                from ..types import ElementType

                cell.chemical_pool[ElementType.PRIMUM] = (
                    cell.chemical_pool.get(ElementType.PRIMUM, 0) + 0.1
                )
                agent.energy -= 0.05

    def _compute_reward(self, agent: Agent) -> float:
        reward = 0.0

        if agent.energy > 0.7:
            reward += 0.15
        elif agent.energy < 0.3:
            reward -= 0.25
        elif agent.energy > 0.5:
            reward += 0.05

        if agent.health > 0.8:
            reward += 0.1
        elif agent.health < 0.4:
            reward -= 0.15

        if agent.age_ticks > 0 and agent.age_ticks % 100 == 0:
            reward += 0.05

        if agent.stage.value == "adult":
            reward += 0.1

        if agent.stage.value == "neonatal":
            reward += 0.05

        if agent.group_id:
            reward += 0.05

        nearby_food = self._detect_food_nearby(agent)
        if nearby_food:
            reward += 0.1

        personality = getattr(agent, "personality", None)
        if personality:
            tom_level = self._compute_tom_level(agent)
            context = self._get_current_context(agent)
            situation_mod = self._personality_situation_interaction(agent, context)

            reward *= 0.8 + personality.conscientiousness * 0.4

            if personality.extraversion > 0.6 and agent.group_id:
                reward += 0.05
            if personality.neuroticism > 0.7 and agent.energy < 0.3:
                reward -= 0.1
            if personality.openness > 0.6 and nearby_food:
                reward += 0.05

            if personality.openness > 0.5:
                reward += situation_mod["openness"] * 0.05
            if personality.conscientiousness > 0.5:
                reward += situation_mod["conscientiousness"] * 0.05
            if personality.extraversion > 0.5:
                reward += situation_mod["extraversion"] * 0.05
            if personality.agreeableness > 0.5:
                reward += situation_mod["agreeableness"] * 0.05
            if personality.neuroticism > 0.5:
                reward += situation_mod["neuroticism"] * 0.05

            if tom_level >= 2 and agent.group_id:
                reward += 0.05 * (tom_level - 1)
            if tom_level >= 3 and personality.openness > 0.5:
                reward += 0.03

        return np.clip(reward, -1.0, 1.0)

    def _detect_food_nearby(self, agent: Agent) -> bool:
        from ..types import ElementType

        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))
        if cell:
            return cell.chemical_pool.get(ElementType.PRIMUM, 0) > 2.0
        return False

    def _compute_tom_level(self, agent: Agent) -> int:
        personality = getattr(agent, "personality", None)
        if personality is None:
            return 0

        base_level = 0
        if agent.neural_complexity >= 1:
            base_level = 1
        if agent.neural_complexity >= 3:
            base_level = 2
        if agent.neural_complexity >= 5:
            base_level = 3

        openness_mod = personality.openness * 0.5
        agreeableness_mod = personality.agreeableness * 0.3
        neuroticism_mod = -personality.neuroticism * 0.2

        adjusted_level = base_level + openness_mod + agreeableness_mod + neuroticism_mod

        return max(0, min(3, int(round(adjusted_level))))

    def _get_current_context(self, agent: Agent) -> dict:
        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))

        threat_count = 0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < agent.sensory_range * 0.5:
                if (
                    other.energy > agent.energy
                    and other.neural_complexity >= agent.neural_complexity
                ):
                    threat_count += 1

        social_density = 0.0
        if cell:
            social_density = len(cell.agent_ids) / 10.0

        resource_rich = False
        if cell:
            resource_rich = sum(cell.chemical_pool.values()) > 5.0

        return {
            "threat_level": min(1.0, threat_count * 0.3),
            "social_density": social_density,
            "resource_richness": 1.0 if resource_rich else 0.0,
            "energy_level": agent.energy,
            "in_group": agent.group_id is not None,
        }

    def _personality_situation_interaction(self, agent: Agent, context: dict) -> dict:
        personality = getattr(agent, "personality", None)
        if personality is None:
            return {
                "openness": 0.0,
                "conscientiousness": 0.0,
                "extraversion": 0.0,
                "agreeableness": 0.0,
                "neuroticism": 0.0,
            }

        threat = context["threat_level"]
        social = context["social_density"]
        resources = context["resource_richness"]
        energy = context["energy_level"]
        in_group = context["in_group"]

        openness_mod = 0.0
        if personality.openness > 0.5:
            if resources > 0.5:
                openness_mod += personality.openness * 0.2
            if threat < 0.3:
                openness_mod += personality.openness * 0.1

        conscientiousness_mod = 0.0
        if personality.conscientiousness > 0.5:
            if energy > 0.5:
                conscientiousness_mod += personality.conscientiousness * 0.15
            else:
                conscientiousness_mod -= personality.conscientiousness * 0.1

        extraversion_mod = 0.0
        if personality.extraversion > 0.5:
            if social > 0.3:
                extraversion_mod += personality.extraversion * 0.2
            if in_group:
                extraversion_mod += personality.extraversion * 0.1

        agreeableness_mod = 0.0
        if personality.agreeableness > 0.5:
            if social > 0.3:
                agreeableness_mod += personality.agreeableness * 0.15
            if threat > 0.5:
                agreeableness_mod -= personality.agreeableness * 0.1

        neuroticism_mod = 0.0
        if personality.neuroticism > 0.5:
            if threat > 0.5:
                neuroticism_mod -= personality.neuroticism * 0.2
            elif threat < 0.2:
                neuroticism_mod += personality.neuroticism * 0.1
            if energy < 0.3:
                neuroticism_mod -= personality.neuroticism * 0.15

        return {
            "openness": openness_mod,
            "conscientiousness": conscientiousness_mod,
            "extraversion": extraversion_mod,
            "agreeableness": agreeableness_mod,
            "neuroticism": neuroticism_mod,
        }

    def _build_sensory_input(self, agent: Agent) -> list[float]:
        caps = getattr(agent, "sensory_capabilities", None)
        if caps is None:
            from ..types import SensoryCapabilities

            caps = SensoryCapabilities()

        personality = getattr(agent, "personality", None)
        tom_level = self._compute_tom_level(agent)

        effective_sensory_range = agent.sensory_range
        if personality:
            if personality.openness > 0.5:
                effective_sensory_range *= 1.0 + personality.openness * 0.2
            if personality.neuroticism > 0.5:
                effective_sensory_range *= 1.0 + personality.neuroticism * 0.1

        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))

        sensory = [
            agent.energy,
            agent.health,
            float(agent.age_ticks) / 1000.0,
            agent.emotion.fear,
            agent.emotion.joy,
        ]

        if cell:
            sensory.append(cell.temperature / 100.0 * caps.thermal + 0.5 * (1.0 - caps.thermal))
            sensory.append(cell.light_level * caps.light + 0.5 * (1.0 - caps.light))
            sensory.append(
                sum(cell.chemical_pool.values()) / 20.0 * caps.chemical
                + 0.5 * (1.0 - caps.chemical)
            )

            sensory.append(
                cell.chemical_pool.get(self.world.config.chemical.element_set[0], 0)
                / 5.0
                * caps.chemical
            )
            sensory.append(len(cell.agent_ids) / 10.0 * caps.social + 0.5 * (1.0 - caps.social))
            sensory.append(1.0 if cell.ca.gol_alive else 0.0)
        else:
            sensory.extend([0.5] * 7)

        nearby_energy = 0.0
        nearby_count = 0
        nearby_thermal = 0.0
        nearby_mech = 0.0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < effective_sensory_range:
                nearby_energy += other.energy
                nearby_count += 1
                other_caps = getattr(other, "sensory_capabilities", None) or caps
                nearby_thermal += other_caps.thermal / max(1, dist)
                nearby_mech += other_caps.mechanical / max(1, dist)

                if tom_level >= 2 and personality and personality.agreeableness > 0.5:
                    other_personality = getattr(other, "personality", None)
                    if other_personality and other.group_id == agent.group_id:
                        nearby_energy += other_personality.agreeableness * 0.5

        sensory.append(nearby_energy / 10.0 * caps.social + 0.5 * (1.0 - caps.social))
        sensory.append(nearby_count / 10.0 * caps.social + 0.5 * (1.0 - caps.social))

        sensory.append(nearby_thermal / max(1, nearby_count) * caps.thermal)
        sensory.append(nearby_mech / max(1, nearby_count) * caps.mechanical)

        sensory.append(caps.proprioceptive * (agent.energy - 0.5) * 2.0)

        sensory.append(
            caps.visual_range * min(1.0, nearby_count / 5.0) if caps.visual_range > 0 else 0.0
        )

        sensory.append(
            caps.auditory * caps.social * min(1.0, nearby_count / 3.0) if caps.auditory > 0 else 0.0
        )

        if personality:
            sensory.append(personality.openness * 0.5)
            sensory.append(personality.conscientiousness * 0.5)
            sensory.append(personality.extraversion * 0.5)
            sensory.append(personality.agreeableness * 0.5)
            sensory.append(personality.neuroticism * 0.5)
        else:
            sensory.extend([0.25, 0.25, 0.25, 0.25, 0.25])

        brain = self.brains.get(agent.id)
        target_size = brain.input_size if brain else 12
        while len(sensory) < target_size:
            sensory.append(0.0)
        return sensory[:target_size]
