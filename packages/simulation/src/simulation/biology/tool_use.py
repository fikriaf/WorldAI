from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class Tool:
    id: str
    name: str
    tier: int
    components: list[str]
    efficiency: float
    discovered_tick: int
    discovered_by: str
    is_emergent: bool = False
    novel_combination: Optional[tuple] = None


@dataclass
class NovelToolTemplate:
    required_objects: list[str]
    produced_tool_tier: int
    produced_tool_name: str
    produced_tool_desc: str
    probability: float
    neural_complexity_min: int


@dataclass
class ToolState:
    agent_id: str
    owned_tools: list[str] = field(default_factory=list)
    craft_skill: float = 0.0
    tool_knowledge: Dict[str, float] = field(default_factory=dict)
    last_crafted_tick: int = 0


TOOL_TIERS = {
    0: {"name": "rock", "desc": "move objects", "energy_cost": 0.05},
    1: {"name": "stick", "desc": "extend reach", "energy_cost": 0.03},
    2: {"name": "binding", "desc": "combine objects", "energy_cost": 0.08},
    3: {"name": "container", "desc": "store resources", "energy_cost": 0.1},
    4: {"name": "lever", "desc": "amplify force", "energy_cost": 0.12},
    5: {"name": "fire_keeper", "desc": "control combustion", "energy_cost": 0.15},
    6: {"name": "grinder", "desc": "process materials", "energy_cost": 0.18},
    7: {"name": "carrier", "desc": "transport efficiently", "energy_cost": 0.2},
    8: {"name": "sensor", "desc": "detect at distance", "energy_cost": 0.25},
    9: {"name": "amplifier", "desc": "magnify output", "energy_cost": 0.3},
    10: {"name": "machine", "desc": "automate processes", "energy_cost": 0.5},
}

EMERGENT_TEMPLATES = [
    NovelToolTemplate(
        required_objects=["stone", "branch"],
        produced_tool_tier=2,
        produced_tool_name="stone_axe",
        produced_tool_desc="cut and chop",
        probability=0.001,
        neural_complexity_min=3,
    ),
    NovelToolTemplate(
        required_objects=["fiber", "branch"],
        produced_tool_tier=2,
        produced_tool_name="rope",
        produced_tool_desc="bind things together",
        probability=0.0015,
        neural_complexity_min=2,
    ),
    NovelToolTemplate(
        required_objects=["container", "water_source"],
        produced_tool_tier=3,
        produced_tool_name="water_carrier",
        produced_tool_desc="transport liquids",
        probability=0.0008,
        neural_complexity_min=4,
    ),
    NovelToolTemplate(
        required_objects=["rock", "fire"],
        produced_tool_tier=4,
        produced_tool_name="heat_stone",
        produced_tool_desc="retain and radiate heat",
        probability=0.0005,
        neural_complexity_min=5,
    ),
    NovelToolTemplate(
        required_objects=["lever", "fulcrum"],
        produced_tool_tier=4,
        produced_tool_name="pry_bar",
        produced_tool_desc="lift heavy objects",
        probability=0.0006,
        neural_complexity_min=5,
    ),
    NovelToolTemplate(
        required_objects=["carrier", "bone"],
        produced_tool_tier=5,
        produced_tool_name="sled",
        produced_tool_desc="drag heavy loads",
        probability=0.0004,
        neural_complexity_min=6,
    ),
    NovelToolTemplate(
        required_objects=["sensor", "fire"],
        produced_tool_tier=6,
        produced_tool_name="torch",
        produced_tool_desc="light and burn",
        probability=0.0003,
        neural_complexity_min=7,
    ),
    NovelToolTemplate(
        required_objects=["amplifier", "container"],
        produced_tool_tier=7,
        produced_tool_name="pressure_vessel",
        produced_tool_desc="cook efficiently under pressure",
        probability=0.0002,
        neural_complexity_min=8,
    ),
]


class ToolUseSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._tool_registry: Dict[str, Tool] = {}
        self._tool_states: Dict[str, ToolState] = {}
        self._tool_counter = 0
        self._init_starter_tools()

    def _init_starter_tools(self):
        for tier, info in TOOL_TIERS.items():
            tool = Tool(
                id=f"tool_tier{tier}",
                name=info["name"],
                tier=tier,
                components=[],
                efficiency=0.5 + tier * 0.05,
                discovered_tick=0,
                discovered_by="nature",
            )
            self._tool_registry[tool.id] = tool

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 1:
                continue

            state = self._get_or_create_state(agent)

            self._process_tool_discovery(agent, state, ctx, events)
            self._process_tool_crafting(agent, state, ctx, events)
            self._apply_tool_benefits(agent, state)

        return events

    def _get_or_create_state(self, agent: Agent) -> ToolState:
        if agent.id not in self._tool_states:
            self._tool_states[agent.id] = ToolState(agent_id=agent.id)
        return self._tool_states[agent.id]

    def _process_tool_discovery(
        self, agent: Agent, state: ToolState, ctx: TickContext, events: list
    ):
        discovery_prob = self._compute_discovery_prob(agent, state)
        emergent_prob = self._compute_emergent_prob(agent, state)

        if np.random.random() < emergent_prob:
            emergent = self._try_emergent_discovery(agent, state, ctx, events)
            if emergent:
                return

        if np.random.random() < discovery_prob:
            new_tier = self._find_discoverable_tier(agent, state)
            if new_tier is not None:
                self._discover_tool(agent, state, new_tier, ctx, events)

    def _compute_emergent_prob(self, agent: Agent, state: ToolState) -> float:
        if agent.neural_complexity < 3:
            return 0.0
        base = 0.0002 * (agent.neural_complexity - 2)
        social_bonus = 0.5 if agent.group_id else 0.0
        craft_bonus = state.craft_skill * 0.5
        return min(0.05, base * (1.0 + social_bonus + craft_bonus))

    def _try_emergent_discovery(
        self, agent: Agent, state: ToolState, ctx: TickContext, events: list
    ) -> bool:
        agent_objects = self._inventory_objects(agent, state)
        for template in EMERGENT_TEMPLATES:
            if agent.neural_complexity < template.neural_complexity_min:
                continue
            if self._has_objects(agent_objects, template.required_objects):
                if np.random.random() < template.probability:
                    tool_id = self._register_emergent_tool(template, agent.id, ctx.tick)
                    state.tool_knowledge[tool_id] = 1.0
                    state.craft_skill = min(1.0, state.craft_skill + 0.1)
                    if tool_id not in state.owned_tools:
                        state.owned_tools.append(tool_id)
                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "emergent_tool_discovered",
                                "agent_id": agent.id,
                                "tool_name": template.produced_tool_name,
                                "tier": template.produced_tool_tier,
                                "components": template.required_objects,
                            },
                            source_id=agent.id,
                        )
                    )
                    if agent.group_id:
                        self._share_knowledge(agent, state, tool_id, ctx)
                    return True
        return False

    def _inventory_objects(self, agent: Agent, state: ToolState) -> set:
        objects = set()
        owned_names = set()
        for tool_id in state.owned_tools:
            tool = self._tool_registry.get(tool_id)
            if tool:
                owned_names.add(tool.name)
        known_names = set()
        for tool_id in state.tool_knowledge:
            tool = self._tool_registry.get(tool_id)
            if tool:
                known_names.add(tool.name)
        for known in known_names:
            if "rock" in known or "stone" in known:
                objects.add("stone")
            if "stick" in known or "branch" in known:
                objects.add("branch")
            if "container" in known:
                objects.add("container")
            if "lever" in known:
                objects.add("lever")
            if "carrier" in known:
                objects.add("carrier")
            if "sensor" in known:
                objects.add("sensor")
            if "amplifier" in known:
                objects.add("amplifier")
            if "fire" in known:
                objects.add("fire")
        if agent.group_id:
            group_caps = set()
            for other in self.world.agents.values():
                if other.group_id == agent.group_id and other.id != agent.id:
                    other_state = self._tool_states.get(other.id)
                    if other_state:
                        for tool_id in other_state.owned_tools:
                            tool = self._tool_registry.get(tool_id)
                            if tool:
                                group_caps.add(tool.name)
            objects.update(group_caps)
        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))
        if cell:
            primum = cell.chemical_pool.get(self.world.config.chemical.element_set[0], 0)
            if primum > 2.0:
                objects.add("water_source")
            if cell.light_level > 0.7:
                objects.add("fire")
        return objects

    def _has_objects(self, inventory: set, required: list) -> bool:
        for obj in required:
            if obj not in inventory:
                return False
        return True

    def _register_emergent_tool(
        self, template: NovelToolTemplate, discoverer_id: str, tick: int
    ) -> str:
        tool_id = f"emergent_{discoverer_id[:8]}_{tick}"
        tool = Tool(
            id=tool_id,
            name=template.produced_tool_name,
            tier=template.produced_tool_tier,
            components=template.required_objects,
            efficiency=0.5 + template.produced_tool_tier * 0.05,
            discovered_tick=tick,
            discovered_by=discoverer_id,
            is_emergent=True,
            novel_combination=tuple(template.required_objects),
        )
        self._tool_registry[tool_id] = tool
        return tool_id

    def _compute_discovery_prob(self, agent: Agent, state: ToolState) -> float:
        if agent.neural_complexity < 1:
            return 0.0

        base_prob = 0.0005 * agent.neural_complexity

        if agent.stage.value == "juvenile":
            base_prob *= 1.5
        elif agent.stage.value == "adolescent":
            base_prob *= 1.3

        if agent.group_id:
            members = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )
            base_prob *= 1.0 + members * 0.1

        base_prob *= 1.0 + state.craft_skill

        return min(0.1, base_prob)

    def _find_discoverable_tier(self, agent: Agent, state: ToolState) -> Optional[int]:
        if agent.neural_complexity < 1:
            return None

        max_affordable_tier = min(10, max(1, agent.neural_complexity))

        for tier in range(max_affordable_tier, -1, -1):
            tool_id = f"tool_tier{tier}"
            if tool_id not in state.tool_knowledge:
                prerequisites = self._check_prerequisites(tier, state)
                if prerequisites:
                    return tier

        return None

    def _check_prerequisites(self, tier: int, state: ToolState) -> bool:
        if tier <= 1:
            return True
        if tier <= 3:
            return any(f"tool_tier{i}" in state.tool_knowledge for i in range(tier))
        if tier <= 6:
            return (
                sum(1 for i in range(tier) if f"tool_tier{i}" in state.tool_knowledge) >= tier // 2
            )
        return state.craft_skill > 0.3

    def _discover_tool(
        self,
        agent: Agent,
        state: ToolState,
        tier: int,
        ctx: TickContext,
        events: list,
    ):
        tool_id = f"tool_tier{tier}"
        tool = self._tool_registry.get(tool_id)
        if not tool:
            return

        state.tool_knowledge[tool_id] = 1.0
        state.craft_skill = min(1.0, state.craft_skill + 0.05 * tier)

        if tool_id not in state.owned_tools:
            state.owned_tools.append(tool_id)

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "type": "tool_discovered",
                    "agent_id": agent.id,
                    "tool_name": tool.name,
                    "tier": tier,
                },
                source_id=agent.id,
            )
        )

        if agent.group_id:
            self._share_knowledge(agent, state, tool_id, ctx)

    def _share_knowledge(self, discoverer: Agent, state: ToolState, tool_id: str, ctx: TickContext):
        if not discoverer.group_id:
            return

        for other in self.world.agents.values():
            if not other.is_alive:
                continue
            if other.id == discoverer.id:
                continue
            if other.group_id != discoverer.group_id:
                continue

            other_state = self._get_or_create_state(other)
            if tool_id in other_state.tool_knowledge:
                continue

            trust = discoverer.reputation.get(other.id, 0.5)
            if trust > 0.3:
                learn_prob = trust * 0.3
                if np.random.random() < learn_prob:
                    other_state.tool_knowledge[tool_id] = 0.5

    def _process_tool_crafting(
        self, agent: Agent, state: ToolState, ctx: TickContext, events: list
    ):
        if state.craft_skill < 0.1:
            return

        if ctx.tick - state.last_crafted_tick < 50:
            return

        available_knowledge = [t for t in state.tool_knowledge if t not in state.owned_tools]
        if not available_knowledge:
            return

        tier = max((int(t.split("tier")[1]) for t in available_knowledge), default=0)
        tool_id = f"tool_tier{tier}"

        craft_cost = TOOL_TIERS.get(tier, {}).get("energy_cost", 0.1)
        if agent.energy < craft_cost + 0.2:
            return

        if np.random.random() < state.craft_skill * 0.3:
            agent.energy -= craft_cost
            state.owned_tools.append(tool_id)
            state.craft_skill = min(1.0, state.craft_skill + 0.02)
            state.last_crafted_tick = ctx.tick

            events.append(
                WorldEvent(
                    tick=ctx.tick,
                    type=EventType.GOD_MODE_INTERVENTION,
                    data={
                        "type": "tool_crafted",
                        "agent_id": agent.id,
                        "tool_name": TOOL_TIERS.get(tier, {}).get("name", "unknown"),
                        "tier": tier,
                    },
                    source_id=agent.id,
                )
            )

    def _apply_tool_benefits(self, agent: Agent, state: ToolState):
        if not state.owned_tools:
            return

        efficiency_bonus = 0.0
        for tool_id in state.owned_tools:
            tool = self._tool_registry.get(tool_id)
            if tool:
                efficiency_bonus += tool.efficiency * 0.05

        if efficiency_bonus > 0:
            agent.energy = min(1.0, agent.energy + efficiency_bonus * 0.01)

        if "tool_tier0" in state.owned_tools or "tool_tier1" in state.owned_tools:
            agent.sensory_range = min(20.0, agent.sensory_range * (1.0 + efficiency_bonus * 0.1))

        if "tool_tier3" in state.owned_tools:
            if agent.energy < 0.5:
                agent.energy = min(1.0, agent.energy + 0.02)

    def get_tool_stats(self) -> Dict:
        agents_with_tools = sum(1 for s in self._tool_states.values() if len(s.owned_tools) > 0)
        total_tools = sum(len(s.owned_tools) for s in self._tool_states.values())
        avg_skill = (
            np.mean([s.craft_skill for s in self._tool_states.values()])
            if self._tool_states
            else 0.0
        )

        tier_distribution = {}
        for state in self._tool_states.values():
            for tool_id in state.owned_tools:
                tier = int(tool_id.split("tier")[1])
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

        return {
            "agents_with_tools": agents_with_tools,
            "total_tools_in_use": total_tools,
            "avg_craft_skill": float(avg_skill),
            "tier_distribution": tier_distribution,
            "highest_tier_discovered": max(
                (
                    int(t.split("tier")[1])
                    for state in self._tool_states.values()
                    for t in state.owned_tools
                ),
                default=0,
            ),
        }
