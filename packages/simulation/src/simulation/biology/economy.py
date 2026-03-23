from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID, ElementType
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class ResourceOffering:
    agent_id: AgentID
    resource_type: str
    quantity: float
    desired_resource: str
    asking_price: float
    tick: int


@dataclass
class Exchange:
    buyer_id: AgentID
    seller_id: AgentID
    resource_given: str
    resource_received: str
    quantity: float
    price: float
    tick: int


@dataclass
class MarketState:
    resource_type: str
    avg_price: float
    volatility: float
    total_volume: float
    active_listings: int


class EconomySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._offerings: List[ResourceOffering] = []
        self._exchange_history: List[Exchange] = []
        self._market_states: Dict[str, MarketState] = {}
        self._resource_types = ["P", "A", "T", "I", "Ae", "L", "energy", "service"]
        self._price_history: Dict[str, list[float]] = {rt: [] for rt in self._resource_types}
        self._exchange_cooldowns: Dict[AgentID, int] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._generate_offerings(ctx)
        self._process_exchanges(ctx, events)
        self._update_market_prices(ctx)
        self._evict_stale_offerings(ctx.tick)

        return events

    def _generate_offerings(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            cooldown = self._exchange_cooldowns.get(agent.id, 0)
            if cooldown > 0:
                self._exchange_cooldowns[agent.id] = cooldown - 1
                continue

            if agent.energy > 0.6 and np.random.random() < 0.1:
                offering = self._create_offering(agent, ctx)
                if offering:
                    self._offerings.append(offering)
                    self._exchange_cooldowns[agent.id] = 50

    def _create_offering(self, agent: Agent, ctx: TickContext) -> Optional[ResourceOffering]:
        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))

        if not cell:
            return None

        resources = {}
        for elem_name, val in [
            ("P", cell.chemical_pool.get(ElementType.PRIMUM, 0)),
            ("A", cell.chemical_pool.get(ElementType.AQUA, 0)),
            ("T", cell.chemical_pool.get(ElementType.TERRA, 0)),
            ("I", cell.chemical_pool.get(ElementType.IGNIS, 0)),
            ("Ae", cell.chemical_pool.get(ElementType.AETHER, 0)),
            ("L", cell.chemical_pool.get(ElementType.LAPIS, 0)),
        ]:
            if val > 1.0:
                resources[elem_name] = val

        if not resources:
            return None

        offered = np.random.choice(list(resources.keys()))
        desired = np.random.choice([r for r in self._resource_types if r != offered])

        avg_price = self._market_states.get(offered, MarketState(offered, 1.0, 0.1, 0, 0)).avg_price
        price = max(0.1, avg_price + np.random.uniform(-0.5, 0.5))

        return ResourceOffering(
            agent_id=agent.id,
            resource_type=offered,
            quantity=min(resources[offered], 1.0),
            desired_resource=desired,
            asking_price=price,
            tick=ctx.tick,
        )

    def _process_exchanges(self, ctx: TickContext, events: list[WorldEvent]):
        for offering in self._offerings[:]:
            if offering.tick < ctx.tick - 50:
                continue

            buyer = self._find_buyer(offering)
            if buyer is None:
                continue

            self._execute_exchange(buyer, offering, ctx, events)

            if offering in self._offerings:
                self._offerings.remove(offering)

    def _find_buyer(self, offering: ResourceOffering) -> Optional[Agent]:
        candidates = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.id == offering.agent_id:
                continue
            if agent.neural_complexity < 2:
                continue

            dx = agent.position.x - self.world.agents[offering.agent_id].position.x
            dy = agent.position.y - self.world.agents[offering.agent_id].position.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > agent.sensory_range * 3:
                continue

            need_score = self._assess_need(agent, offering)
            affordability = max(0, agent.energy - offering.asking_price) / max(1, agent.energy)
            trust = agent.reputation.get(offering.agent_id, 0.5)

            total_score = need_score * 0.4 + affordability * 0.3 + trust * 0.3
            candidates.append((agent, total_score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _assess_need(self, agent: Agent, offering: ResourceOffering) -> float:
        if offering.resource_type == "P" and agent.energy < 0.5:
            return (0.5 - agent.energy) * 2.0
        if offering.desired_resource == "energy":
            return agent.energy * 0.5
        return 0.2

    def _execute_exchange(
        self,
        buyer: Agent,
        offering: ResourceOffering,
        ctx: TickContext,
        events: list[WorldEvent],
    ):
        if buyer.energy < offering.asking_price:
            return

        price = offering.asking_price

        buyer.energy -= price
        buyer.energy = max(0, buyer.energy)

        seller = self.world.agents.get(offering.agent_id)
        if seller:
            seller.energy += price * 0.8

        self._exchange_history.append(
            Exchange(
                buyer_id=buyer.id,
                seller_id=offering.agent_id,
                resource_given=offering.resource_type,
                resource_received="energy",
                quantity=offering.quantity,
                price=price,
                tick=ctx.tick,
            )
        )

        self._record_price(offering.resource_type, price)

        if len(self._exchange_history) > 1000:
            self._exchange_history = self._exchange_history[-1000:]

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "type": "exchange",
                    "buyer": buyer.id,
                    "seller": offering.agent_id,
                    "resource": offering.resource_type,
                    "price": price,
                },
                source_id=buyer.id,
                target_id=offering.agent_id,
            )
        )

    def _record_price(self, resource_type: str, price: float):
        if resource_type not in self._price_history:
            self._price_history[resource_type] = []
        self._price_history[resource_type].append(price)
        if len(self._price_history[resource_type]) > 100:
            self._price_history[resource_type] = self._price_history[resource_type][-100:]

    def _update_market_prices(self, ctx: TickContext):
        for resource_type in self._resource_types:
            prices = self._price_history.get(resource_type, [])
            if not prices:
                continue

            recent = prices[-20:] if len(prices) >= 20 else prices
            avg = np.mean(recent)
            volatility = np.std(recent) / max(0.01, avg) if avg > 0 else 0.0

            volume = sum(
                1 for e in self._exchange_history[-100:] if e.resource_given == resource_type
            )

            self._market_states[resource_type] = MarketState(
                resource_type=resource_type,
                avg_price=avg,
                volatility=volatility,
                total_volume=volume,
                active_listings=sum(1 for o in self._offerings if o.resource_type == resource_type),
            )

    def _evict_stale_offerings(self, current_tick: int):
        self._offerings = [o for o in self._offerings if current_tick - o.tick < 100]

    def get_economy_stats(self) -> Dict:
        total_exchanges = len(self._exchange_history)
        recent_exchanges = [e for e in self._exchange_history[-100:]]

        active_markets = len(self._market_states)

        if recent_exchanges:
            avg_price = np.mean([e.price for e in recent_exchanges])
        else:
            avg_price = 0.0

        return {
            "total_exchanges": total_exchanges,
            "active_offerings": len(self._offerings),
            "active_markets": active_markets,
            "avg_price_recent": float(avg_price),
            "market_states": {
                rt: {
                    "avg_price": ms.avg_price,
                    "volatility": ms.volatility,
                    "volume": ms.total_volume,
                }
                for rt, ms in self._market_states.items()
                if ms.total_volume > 0
            },
        }
