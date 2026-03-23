from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum


class HistoricalEventType(Enum):
    ABIOGENESIS = "abiogenesis"
    SPECIATION = "speciation"
    EXTINCTION = "extinction"
    FIRST_CONTACT = "first_contact"
    REVOLUTION = "revolution"
    WAR = "war"
    PLAGUE = "plague"
    GREAT_DISCOVERY = "great_discovery"
    CULTURAL_RENAISSANCE = "cultural_renaissance"
    FOUNDER_EFFECT = "founder_effect"
    MIGRATION = "migration"
    CIVILIZATION_RISE = "civilization_rise"
    CIVILIZATION_FALL = "civilization_fall"


@dataclass
class HistoricalEntry:
    entry_id: str
    event_type: HistoricalEventType
    tick: int
    description: str
    witness_ids: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    location: Optional[tuple] = None
    significance: float = 1.0
    raw_data: Dict = field(default_factory=dict)


@dataclass
class Narrative:
    narrative_id: str
    entry_id: str
    group_id: str
    version: int = 1
    text: str = ""
    interpretation: str = ""
    mythic_elements: List[str] = field(default_factory=list)
    reliability: float = 1.0
    created_tick: int = 0
    last_updated_tick: int = 0


@dataclass
class HistoricalRecord:
    group_id: str
    episodic_memory: List[HistoricalEntry] = field(default_factory=list)
    semantic_memory: Dict[str, Narrative] = field(default_factory=dict)
    memorial_practices: List[str] = field(default_factory=list)
    founding_tick: int = 0
    collective_identity_strength: float = 0.5


class CollectiveMemorySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._records: Dict[str, HistoricalRecord] = {}
        self._all_entries: Dict[str, HistoricalEntry] = {}
        self._mythologization_rate = 0.001
        self._memory_decay_rate = 0.0001
        self._transmission_fidelity_base = 0.9
        self._cohesion_bonus_max = 0.2

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._record_significant_events(ctx, events)
        self._update_records(ctx)
        self._mythologize_old_entries(ctx)
        self._transmit_to_young(ctx)

        return events

    def _record_significant_events(self, ctx: TickContext, events: List[WorldEvent]):
        for event in self.world.event_bus._events[-100:]:
            event_type = self._classify_event(event)
            if event_type is None:
                continue

            group_id = self._determine_group_context(event)
            if group_id is None:
                continue

            entry = HistoricalEntry(
                entry_id=f"hist_{ctx.tick}_{event.source_id or 'evt'[:4]}",
                event_type=event_type,
                tick=ctx.tick,
                description=self._generate_description(event, event_type),
                witness_ids=self._find_witnesses(event),
                participants=[p for p in [event.source_id, event.target_id] if p],
                significance=self._calculate_significance(event, event_type),
                raw_data=event.data,
            )

            self._all_entries[entry.entry_id] = entry
            self._get_or_create_record(group_id).episodic_memory.append(entry)

            if event_type in [
                HistoricalEventType.ABIOGENESIS,
                HistoricalEventType.FIRST_CONTACT,
                HistoricalEventType.REVOLUTION,
            ]:
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={"historical_recorded": True, "event_type": event_type.value},
                        source_id=event.source_id,
                    )
                )

    def _classify_event(self, event: WorldEvent) -> Optional[HistoricalEventType]:
        if event.type == EventType.ABIOGENESIS:
            return HistoricalEventType.ABIOGENESIS
        elif event.type == EventType.SPECIATION:
            return HistoricalEventType.SPECIATION
        elif event.type == EventType.AGENT_DIED:
            return HistoricalEventType.EXTINCTION
        elif event.type == EventType.GOD_MODE_INTERVENTION:
            data = event.data or {}
            if data.get("first_contact"):
                return HistoricalEventType.FIRST_CONTACT
            if data.get("revolution"):
                return HistoricalEventType.REVOLUTION
            if data.get("discovery"):
                return HistoricalEventType.GREAT_DISCOVERY
        return None

    def _determine_group_context(self, event: WorldEvent) -> Optional[str]:
        source = self.world.agents.get(event.source_id) if event.source_id else None
        if source and source.group_id:
            return source.group_id

        if event.target_id:
            target = self.world.agents.get(event.target_id)
            if target and target.group_id:
                return target.group_id

        return None

    def _find_witnesses(self, event: WorldEvent) -> List[str]:
        witnesses = []
        location = None

        if event.source_id:
            source = self.world.agents.get(event.source_id)
            if source:
                location = (source.position.x, source.position.y)
                if source.group_id:
                    witnesses.append(source.id)

        if location:
            for agent in self.world.agents.values():
                if not agent.is_alive or agent.group_id is None:
                    continue
                if agent.id in witnesses:
                    continue
                if (
                    abs(agent.position.x - location[0]) <= 3
                    and abs(agent.position.y - location[1]) <= 3
                ):
                    witnesses.append(agent.id)

        return witnesses[:10]

    def _generate_description(self, event: WorldEvent, event_type: HistoricalEventType) -> str:
        base_descriptions = {
            HistoricalEventType.ABIOGENESIS: "The great awakening of life from the primordial soup",
            HistoricalEventType.SPECIATION: "A new form of life emerged from the ancient lineage",
            HistoricalEventType.EXTINCTION: "A great dying swept through the land",
            HistoricalEventType.FIRST_CONTACT: "The first meeting between distant peoples",
            HistoricalEventType.REVOLUTION: "The old ways were overthrown in a great upheaval",
            HistoricalEventType.PLAGUE: "A terrible sickness spread among the people",
            HistoricalEventType.GREAT_DISCOVERY: "A profound truth was revealed to the wise",
            HistoricalEventType.CULTURAL_RENAISSANCE: "A flourishing of art and wisdom",
            HistoricalEventType.FOUNDER_EFFECT: "A small band carried the seeds of a new people",
            HistoricalEventType.MIGRATION: "The people journeyed to find a new home",
            HistoricalEventType.CIVILIZATION_RISE: "A great civilization arose from humble beginnings",
            HistoricalEventType.CIVILIZATION_FALL: "The great civilization fell into ruin",
        }
        return base_descriptions.get(event_type, "A notable event in the flow of time")

    def _calculate_significance(self, event: WorldEvent, event_type: HistoricalEventType) -> float:
        significance_map = {
            HistoricalEventType.ABIOGENESIS: 1.0,
            HistoricalEventType.FIRST_CONTACT: 0.9,
            HistoricalEventType.REVOLUTION: 0.85,
            HistoricalEventType.SPECIATION: 0.8,
            HistoricalEventType.EXTINCTION: 0.75,
            HistoricalEventType.CIVILIZATION_RISE: 0.9,
            HistoricalEventType.CIVILIZATION_FALL: 0.85,
            HistoricalEventType.GREAT_DISCOVERY: 0.8,
            HistoricalEventType.PLAGUE: 0.7,
            HistoricalEventType.WAR: 0.7,
            HistoricalEventType.CULTURAL_RENAISSANCE: 0.6,
            HistoricalEventType.MIGRATION: 0.5,
            HistoricalEventType.FOUNDER_EFFECT: 0.5,
        }
        return significance_map.get(event_type, 0.5)

    def _get_or_create_record(self, group_id: str) -> HistoricalRecord:
        if group_id not in self._records:
            self._records[group_id] = HistoricalRecord(
                group_id=group_id,
                founding_tick=self.world.tick,
            )
        return self._records[group_id]

    def _update_records(self, ctx: TickContext):
        for record in self._records.values():
            if record.episodic_memory:
                recent_entries = [e for e in record.episodic_memory if ctx.tick - e.tick < 100]
                record.episodic_memory = recent_entries

            living_agents = [
                a
                for a in self.world.agents.values()
                if a.group_id == record.group_id and a.is_alive
            ]

            if len(living_agents) > 0:
                base_cohesion = record.collective_identity_strength
                memorial_bonus = len(record.memorial_practices) * 0.02
                record.collective_identity_strength = min(
                    1.0, base_cohesion + memorial_bonus * (ctx.tick / 1000)
                )

    def _mythologize_old_entries(self, ctx: TickContext):
        for record in self._records.values():
            for entry in record.episodic_memory:
                age = ctx.tick - entry.tick
                if age < 500:
                    continue

                entry_key = f"sem_{entry.entry_id}"
                if entry_key in record.semantic_memory:
                    narrative = record.semantic_memory[entry_key]
                    if np.random.random() < self._mythologization_rate * (age / 1000):
                        self._add_mythic_element(narrative, entry, age)
                        narrative.last_updated_tick = ctx.tick
                else:
                    if np.random.random() < self._mythologization_rate * (age / 500):
                        narrative = Narrative(
                            narrative_id=entry_key,
                            entry_id=entry.entry_id,
                            group_id=record.group_id,
                            text=entry.description,
                            interpretation=self._generate_interpretation(entry, age),
                            reliability=max(0.1, 1.0 - (age / 5000)),
                            created_tick=ctx.tick,
                            last_updated_tick=ctx.tick,
                        )
                        self._add_mythic_element(narrative, entry, age)
                        record.semantic_memory[entry_key] = narrative

    def _add_mythic_element(self, narrative: Narrative, entry: HistoricalEntry, age: int):
        mythic_themes = [
            "heroic ancestors",
            "divine intervention",
            "cosmic punishment",
            "prophecy fulfilled",
            "lost wisdom",
            "ancient curse",
            "blessed memory",
        ]

        if age > 1000 and np.random.random() < 0.1:
            theme = np.random.choice(mythic_themes)
            if theme not in narrative.mythic_elements:
                narrative.mythic_elements.append(theme)
                narrative.reliability = max(0.1, narrative.reliability - 0.1)

    def _generate_interpretation(self, entry: HistoricalEntry, age: int) -> str:
        interpretations = {
            HistoricalEventType.ABIOGENESIS: "The moment the spark of life ignited our world",
            HistoricalEventType.FIRST_CONTACT: "When we learned we were not alone in the universe",
            HistoricalEventType.REVOLUTION: "The turning point when the people reclaimed their destiny",
            HistoricalEventType.EXTINCTION: "A somber reminder of the fragility of existence",
        }
        base = interpretations.get(entry.event_type, entry.description)

        if age > 1000:
            base = "In the time of legend, " + base.lower()
        elif age > 500:
            base = "In ancient times, " + base.lower()

        return base

    def _transmit_to_young(self, ctx: TickContext):
        for record in self._records.values():
            young_agents = [
                a
                for a in self.world.agents.values()
                if a.group_id == record.group_id
                and a.is_alive
                and a.stage.value in ["neonatal", "juvenile", "adolescent"]
            ]

            if not young_agents or not record.semantic_memory:
                continue

            for agent in young_agents:
                for entry_id, narrative in record.semantic_memory.items():
                    age_at_transmission = ctx.tick - narrative.created_tick
                    fidelity = self._transmission_fidelity_base * (1.0 - age_at_transmission / 2000)
                    fidelity = max(0.3, fidelity)

                    if np.random.random() < fidelity * 0.05:
                        if "history_knowledge" not in agent.beliefs:
                            agent.beliefs["history_knowledge"] = []
                        if entry_id not in agent.beliefs["history_knowledge"]:
                            agent.beliefs["history_knowledge"].append(entry_id)

    def record_event(
        self,
        group_id: str,
        event_type: HistoricalEventType,
        description: str,
        participants: Optional[List[str]] = None,
        significance: float = 1.0,
    ) -> HistoricalEntry:
        entry = HistoricalEntry(
            entry_id=f"hist_{self.world.tick}_{event_type.value[:4]}",
            event_type=event_type,
            tick=self.world.tick,
            description=description,
            participants=participants or [],
            significance=significance,
        )

        self._all_entries[entry.entry_id] = entry
        record = self._get_or_create_record(group_id)
        record.episodic_memory.append(entry)

        return entry

    def query(self, group_id: str, query_text: str) -> List[HistoricalEntry]:
        results = []
        record = self._records.get(group_id)
        if not record:
            return results

        query_keywords = query_text.lower().split()
        for entry in record.episodic_memory:
            score = 0
            text = f"{entry.description} {entry.event_type.value}".lower()
            for keyword in query_keywords:
                if keyword in text:
                    score += 1

            if score > 0:
                results.append(entry)

        results.sort(key=lambda e: (e.significance, self.world.tick - e.tick), reverse=True)
        return results[:10]

    def get_cohesion_bonus(self, group_id: str) -> float:
        record = self._records.get(group_id)
        if not record:
            return 0.0

        memorial_count = len(record.memorial_practices)
        base_bonus = min(self._cohesion_bonus_max, memorial_count * 0.05)
        identity_bonus = record.collective_identity_strength * 0.1

        return min(self._cohesion_bonus_max, base_bonus + identity_bonus)

    def add_memorial_practice(self, group_id: str, practice: str):
        record = self._get_or_create_record(group_id)
        if practice not in record.memorial_practices:
            record.memorial_practices.append(practice)

    def get_record(self, group_id: str) -> Optional[HistoricalRecord]:
        return self._records.get(group_id)

    def get_stats(self) -> Dict:
        total_entries = len(self._all_entries)
        total_records = len(self._records)
        total_narratives = sum(len(r.semantic_memory) for r in self._records.values())
        total_memorials = sum(len(r.memorial_practices) for r in self._records.values())

        return {
            "total_entries": total_entries,
            "total_records": total_records,
            "total_narratives": total_narratives,
            "total_memorial_practices": total_memorials,
        }
