from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np


class ChannelType(Enum):
    CHEMICAL = "chemical"
    POSTURAL = "postural"
    GESTURAL = "gestural"
    VOCAL = "vocal"


@dataclass
class GrammarRule:
    subject_position: int = 0
    predicate_position: int = 1
    object_position: int = 2
    allows_composition: bool = True


@dataclass
class Language:
    id: int
    name: str
    vocabulary: Set[int] = field(default_factory=set)
    grammar_rules: List[GrammarRule] = field(default_factory=list)
    speaker_ids: Set[AgentID] = field(default_factory=set)
    birth_tick: int = 0
    parent_language_id: Optional[int] = None

    def shared_vocab_pct(self, other: "Language") -> float:
        if not self.vocabulary or not other.vocabulary:
            return 0.0
        intersection = self.vocabulary & other.vocabulary
        smaller = min(len(self.vocabulary), len(other.vocabulary))
        return len(intersection) / smaller if smaller > 0 else 0.0


@dataclass
class Symbol:
    id: int
    form: str
    meanings: list[str]
    frequency: int = 0
    learned_by: list[str] = field(default_factory=list)
    emergent_meaning: Optional[str] = None
    is_composed: bool = False
    components: tuple[int, ...] = field(default_factory=tuple)
    is_indexical: bool = False
    indexical_ref: Optional[dict] = None


@dataclass
class Signal:
    channel: ChannelType
    cost_modifier: float = 1.0


@dataclass
class CommunicativeAct:
    sender_id: AgentID
    receiver_id: Optional[AgentID]
    symbol_id: int
    context: str
    tick: int
    is_deceptive: bool = False
    cost: float = 0.0
    channel: ChannelType = ChannelType.CHEMICAL


class CommunicationSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._symbol_table: Dict[int, Symbol] = {}
        self._symbol_counter = 0
        self._vocabularies: Dict[AgentID, Set[int]] = {}
        self._pending_utterances: List[CommunicativeAct] = []
        self._comprehension_history: Dict[AgentID, Dict[int, int]] = {}
        self._signal_cooldowns: Dict[AgentID, int] = {}
        self._languages: Dict[int, Language] = {}
        self._language_counter = 0
        self._extinct_languages: List[Language] = []
        self._language_membership: Dict[AgentID, int] = {}
        self._reputation_history: Dict[Tuple[AgentID, AgentID], List[Tuple[int, float]]] = {}
        self._deception_history: Dict[Tuple[AgentID, AgentID], List[int]] = {}
        self._emotional_contagion_strength: Dict[AgentID, float] = {}
        self._group_cohesion_ticks: Dict[str, int] = {}
        self._composed_symbols: Dict[int, tuple[int, ...]] = {}
        self._indexical_references: Dict[int, dict] = {}
        self._init_protolanguage()

    def _init_protolanguage(self):
        self._protosigns = {
            "food": [0],
            "danger": [1],
            "threat": [2],
            "friend": [3],
            "reproduce": [4],
            "groom": [5],
            "grieve": [6],
            "lead": [7],
        }
        for i, meaning in enumerate(self._protosigns.keys()):
            self._symbol_table[i] = Symbol(id=i, form=f"proto_{i}", meanings=[meaning])
            self._symbol_counter = i + 1

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in list(self.world.agents.values()):
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 1:
                continue

            self._process_communication(agent, ctx, events)

        self._propagate_language(ctx)
        self._evolve_language(ctx)
        self._emotional_contagion(ctx)
        self._update_trust_reputations(ctx)

        return events

    def _process_communication(self, agent: Agent, ctx: TickContext, events: list[WorldEvent]):
        cooldown = self._signal_cooldowns.get(agent.id, 0)
        if cooldown > 0:
            self._signal_cooldowns[agent.id] = cooldown - 1
            return

        utterance = self._generate_utterance(agent, ctx)
        if utterance is None:
            return

        self._pending_utterances.append(utterance)

        if len(self._pending_utterances) > 500:
            self._pending_utterances = self._pending_utterances[-500:]

        symbol = self._symbol_table.get(utterance.symbol_id)
        if symbol:
            symbol.frequency += 1
            if agent.id not in symbol.learned_by:
                symbol.learned_by.append(agent.id)

        cost = self._compute_signal_cost(agent, utterance)
        agent.energy = max(0, agent.energy - cost)
        utterance.cost = cost

        if utterance.receiver_id:
            was_detected, detection_prob = self._detect_deception(agent, utterance)
            if was_detected:
                self._record_deception(agent.id, utterance.receiver_id, ctx.tick)
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "deception_detected",
                            "deceiver": agent.id,
                            "receiver": utterance.receiver_id,
                            "probability": detection_prob,
                        },
                        source_id=agent.id,
                        target_id=utterance.receiver_id,
                    )
                )

        self._deliver_message(agent, utterance, ctx, events)

        self._signal_cooldowns[agent.id] = 20 + int((1.0 - self._get_vocabulary_size(agent)) * 30)

    def _generate_utterance(self, agent: Agent, ctx: TickContext) -> Optional[CommunicativeAct]:
        vocabulary = self._get_or_create_vocabulary(agent)

        if not vocabulary:
            return None

        communicative_intent = self._determine_intent(agent)
        if communicative_intent is None:
            return None

        channel = self._select_channel(agent)

        symbol_id = self._choose_symbol(agent, communicative_intent, vocabulary)
        if symbol_id is None:
            symbol_id = self._attempt_symbol_composition(agent, communicative_intent, vocabulary)

        if symbol_id is None:
            return None

        is_deceptive = self._determine_deception(agent, symbol_id, communicative_intent)

        receiver = self._select_receiver(agent, communicative_intent)

        return CommunicativeAct(
            sender_id=agent.id,
            receiver_id=receiver,
            symbol_id=symbol_id,
            context=communicative_intent,
            is_deceptive=is_deceptive,
            tick=ctx.tick,
            channel=channel,
        )

    def _select_channel(self, agent: Agent) -> ChannelType:
        complexity = agent.neural_complexity
        if complexity <= 2:
            return ChannelType.CHEMICAL
        elif complexity <= 4:
            return ChannelType.POSTURAL if np.random.random() < 0.3 else ChannelType.CHEMICAL
        else:
            weights = [0.2, 0.3, 0.3, 0.2]
            return np.random.choice(
                [
                    ChannelType.CHEMICAL,
                    ChannelType.POSTURAL,
                    ChannelType.GESTURAL,
                    ChannelType.VOCAL,
                ],
                p=weights,
            )

    def _attempt_symbol_composition(
        self, agent: Agent, intent: str, vocabulary: Set[int]
    ) -> Optional[int]:
        composed = self._compose_symbol(agent, intent, vocabulary)
        if composed is not None and composed in vocabulary:
            return composed
        return None

    def _compose_symbol(self, agent: Agent, intent: str, vocabulary: Set[int]) -> Optional[int]:
        if np.random.random() > 0.1:
            return None

        base_symbols = [sid for sid, sym in self._symbol_table.items() if sid in vocabulary]
        if len(base_symbols) < 2:
            return None

        components = tuple(np.random.choice(base_symbols, size=2, replace=False))
        composite_meaning = f"{components[0]}_{components[1]}"

        for sym_id, sym in self._symbol_table.items():
            if sym.is_composed and sym.components == components:
                if sym_id in vocabulary:
                    return sym_id

        new_id = self._symbol_counter
        self._symbol_counter += 1
        self._symbol_table[new_id] = Symbol(
            id=new_id,
            form=f"comp_{new_id}",
            meanings=[intent, composite_meaning],
            is_composed=True,
            components=components,
        )
        self._composed_symbols[new_id] = components
        vocabulary.add(new_id)
        return new_id

    def _determine_intent(self, agent: Agent) -> Optional[str]:
        if agent.emotion.fear > 0.7:
            return "danger"
        if agent.emotion.joy > 0.7:
            return "friend"
        if agent.energy < 0.2:
            return "food"
        if agent.emotion.anger > 0.6:
            return "threat"
        if agent.stage.value == "adult" and agent.group_id:
            if np.random.random() < 0.3:
                return "lead"
        if agent.emotion.sadness > 0.5:
            return "grieve"
        if np.random.random() < 0.05:
            return "groom"
        return None

    def _choose_symbol(self, agent: Agent, intent: str, vocabulary: Set[int]) -> Optional[int]:
        if intent in self._protosigns:
            candidates = [s for s in self._protosigns[intent] if s in vocabulary]
            if candidates:
                return np.random.choice(candidates)

        intent_symbols = [sid for sid, sym in self._symbol_table.items() if intent in sym.meanings]
        valid = [s for s in intent_symbols if s in vocabulary]
        if valid:
            return np.random.choice(valid)

        return None

    def _determine_deception(self, agent: Agent, symbol_id: int, intent: str) -> bool:
        if agent.neural_complexity < 3:
            return False

        personality = getattr(agent, "personality", None)
        if personality and personality.neuroticism > 0.6 and personality.agreeableness < 0.4:
            if np.random.random() < 0.4 * personality.neuroticism:
                return True

        if np.random.random() < 0.05 * agent.emotion.anger:
            symbol = self._symbol_table.get(symbol_id)
            if symbol and symbol.meanings:
                return symbol.meanings[0] != intent

        return False

    def _select_receiver(self, agent: Agent, intent: str) -> Optional[AgentID]:
        if intent == "danger":
            nearby = self._get_nearby_agents(agent, agent.sensory_range)
            trustworthy = [a for a in nearby if agent.reputation.get(a.id, 0.5) > 0.4]
            if trustworthy:
                return np.random.choice([a.id for a in trustworthy])

        elif intent == "lead" and agent.group_id:
            members = [
                a.id
                for a in self.world.agents.values()
                if a.group_id == agent.group_id and a.is_alive and a.id != agent.id
            ]
            if members:
                return np.random.choice(members)

        nearby = self._get_nearby_agents(agent, agent.sensory_range)
        if nearby:
            return np.random.choice([a.id for a in nearby])

        return None

    def _compute_signal_cost(self, agent: Agent, utterance: CommunicativeAct) -> float:
        symbol = self._symbol_table.get(utterance.symbol_id)
        base_cost = 0.01

        if symbol and symbol.frequency < 10:
            base_cost += 0.02

        vocabulary_size = self._get_vocabulary_size(agent)
        if vocabulary_size < 5:
            base_cost += 0.01

        channel_costs = {
            ChannelType.CHEMICAL: 1.0,
            ChannelType.POSTURAL: 1.2,
            ChannelType.GESTURAL: 1.5,
            ChannelType.VOCAL: 2.5,
        }
        base_cost *= channel_costs.get(utterance.channel, 1.0)

        if utterance.is_deceptive:
            base_cost += 0.03

        if utterance.channel == ChannelType.VOCAL and utterance.is_deceptive:
            base_cost += 0.05

        if agent.stage.value in ["neonatal", "juvenile"]:
            base_cost *= 0.5

        return base_cost

    def _deliver_message(
        self,
        agent: Agent,
        utterance: CommunicativeAct,
        ctx: TickContext,
        events: list[WorldEvent],
    ):
        if utterance.receiver_id and utterance.receiver_id in self.world.agents:
            receiver = self.world.agents[utterance.receiver_id]

            if not utterance.is_deceptive or not self._detect_deception(agent, utterance)[0]:
                self._process_reception(receiver, utterance)
                self._update_trust_on_interaction(agent.id, receiver.id, utterance, ctx.tick)

            if utterance.symbol_id not in self._get_or_create_vocabulary(receiver):
                self._get_or_create_vocabulary(receiver).add(utterance.symbol_id)

            symbol = self._symbol_table.get(utterance.symbol_id)
            events.append(
                WorldEvent(
                    tick=ctx.tick,
                    type=EventType.GOD_MODE_INTERVENTION,
                    data={
                        "type": "communicative_act",
                        "from": utterance.sender_id,
                        "to": utterance.receiver_id,
                        "meaning": utterance.context,
                        "symbol": symbol.form if symbol else "unknown",
                        "deceptive": utterance.is_deceptive,
                        "channel": utterance.channel.value,
                    },
                    source_id=utterance.sender_id,
                    target_id=utterance.receiver_id,
                )
            )

    def _process_reception(self, receiver: Agent, utterance: CommunicativeAct):
        if receiver.neural_complexity < 1:
            return

        if utterance.symbol_id not in self._comprehension_history.get(receiver.id, {}):
            if receiver.id not in self._comprehension_history:
                self._comprehension_history[receiver.id] = {}
            self._comprehension_history[receiver.id][utterance.symbol_id] = 0

        self._comprehension_history[receiver.id][utterance.symbol_id] += 1

        symbol = self._symbol_table.get(utterance.symbol_id)
        if symbol:
            comprehension = min(
                1.0,
                self._comprehension_history[receiver.id].get(utterance.symbol_id, 0) / 10.0,
            )

            if comprehension > 0.3:
                self._apply_message_effect(receiver, utterance, comprehension)

    def _apply_message_effect(
        self, receiver: Agent, utterance: CommunicativeAct, comprehension: float
    ):
        if utterance.context == "danger":
            receiver.emotion.fear = min(1.0, receiver.emotion.fear + 0.3 * comprehension)
            if receiver.group_id:
                receiver.emotion.trust = min(1.0, receiver.emotion.trust + 0.1 * comprehension)

        elif utterance.context == "friend":
            if utterance.sender_id in receiver.reputation:
                receiver.reputation[utterance.sender_id] = min(
                    1.0,
                    receiver.reputation[utterance.sender_id] + 0.1 * comprehension,
                )

        elif utterance.context == "threat":
            receiver.emotion.anger = min(1.0, receiver.emotion.anger + 0.2 * comprehension)
            receiver.reputation[utterance.sender_id] = max(
                0.0,
                receiver.reputation.get(utterance.sender_id, 0.5) - 0.2,
            )

        elif utterance.context == "lead":
            if receiver.group_id:
                receiver.emotion.trust = min(1.0, receiver.emotion.trust + 0.15 * comprehension)

    def _propagate_language(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            vocabulary = self._get_or_create_vocabulary(agent)

            for utterance in self._pending_utterances[-50:]:
                if utterance.tick < ctx.tick - 100:
                    continue
                if utterance.sender_id == agent.id:
                    continue

                dist = (
                    (utterance.position.x - agent.position.x) ** 2
                    + (utterance.position.y - agent.position.y) ** 2
                ) ** 0.5
                if dist > agent.sensory_range * 2:
                    continue

                if utterance.symbol_id not in vocabulary:
                    learn_prob = 0.01 * (1.0 + agent.emotion.trust * 0.5)
                    if np.random.random() < learn_prob:
                        vocabulary.add(utterance.symbol_id)

    def _evolve_language(self, ctx: TickContext):
        self._update_group_cohesion(ctx)

        alive_agents = [a for a in self.world.agents.values() if a.is_alive]

        for lang in list(self._languages.values()):
            lang.speaker_ids = {
                a.id for a in alive_agents if self._language_membership.get(a.id) == lang.id
            }

        for group_id, cohesion_ticks in self._group_cohesion_ticks.items():
            if cohesion_ticks < 100:
                continue

            group_agents = [a for a in alive_agents if a.group_id == group_id]
            if len(group_agents) < 3:
                continue

            vocabularies = [self._get_or_create_vocabulary(a) for a in group_agents]
            avg_vocab_size = np.mean([len(v) for v in vocabularies])

            shared_counts = 0
            for i, v1 in enumerate(vocabularies):
                for v2 in vocabularies[i + 1 :]:
                    if len(v1) > 0 and len(v2) > 0:
                        intersection = v1 & v2
                        smaller = min(len(v1), len(v2))
                        shared_pct = len(intersection) / smaller
                        if shared_pct > 0.5:
                            shared_counts += 1

            if shared_counts >= 3:
                existing_lang = self._find_language_for_group(group_id)
                if existing_lang is None:
                    self._create_language(group_id, group_agents, ctx.tick)
                elif cohesion_ticks > 200:
                    self._diverge_language(existing_lang, group_agents, ctx.tick)

        self._check_language_extinction(ctx.tick)

    def _update_group_cohesion(self, ctx: TickContext):
        current_groups: Dict[str, Set[AgentID]] = {}
        for agent in self.world.agents.values():
            if agent.is_alive and agent.group_id:
                if agent.group_id not in current_groups:
                    current_groups[agent.group_id] = set()
                current_groups[agent.group_id].add(agent.id)

        for group_id in list(self._group_cohesion_ticks.keys()):
            if group_id not in current_groups or len(current_groups[group_id]) < 3:
                self._group_cohesion_ticks[group_id] = 0
            else:
                self._group_cohesion_ticks[group_id] += 1

        for group_id in current_groups:
            if group_id not in self._group_cohesion_ticks:
                self._group_cohesion_ticks[group_id] = 1

    def _find_language_for_group(self, group_id: str) -> Optional[int]:
        for agent in self.world.agents.values():
            if agent.is_alive and agent.group_id == group_id:
                lang_id = self._language_membership.get(agent.id)
                if lang_id is not None and lang_id in self._languages:
                    return lang_id
        return None

    def _create_language(self, group_id: str, agents: List[Agent], tick: int):
        lang_id = self._language_counter
        self._language_counter += 1

        shared_vocab: Set[int] = set()
        for a in agents:
            vocab = self._get_or_create_vocabulary(a)
            if not shared_vocab:
                shared_vocab = set(vocab)
            else:
                shared_vocab &= vocab

        if not shared_vocab:
            for a in agents[:5]:
                shared_vocab |= self._get_or_create_vocabulary(a)

        language = Language(
            id=lang_id,
            name=f"lang_{lang_id}",
            vocabulary=shared_vocab,
            grammar_rules=[GrammarRule()],
            speaker_ids={a.id for a in agents},
            birth_tick=tick,
        )
        self._languages[lang_id] = language

        for a in agents:
            self._language_membership[a.id] = lang_id

    def _diverge_language(self, parent_lang_id: int, agents: List[Agent], tick: int):
        parent_lang = self._languages.get(parent_lang_id)
        if parent_lang is None:
            return

        lang_id = self._language_counter
        self._language_counter += 1

        new_vocab = set()
        for a in agents:
            new_vocab |= self._get_or_create_vocabulary(a)

        child_lang = Language(
            id=lang_id,
            name=f"lang_{lang_id}",
            vocabulary=new_vocab,
            grammar_rules=[GrammarRule()],
            speaker_ids={a.id for a in agents},
            birth_tick=tick,
            parent_language_id=parent_lang_id,
        )
        self._languages[lang_id] = child_lang

        for a in agents:
            self._language_membership[a.id] = lang_id

        parent_lang.speaker_ids -= {a.id for a in agents}

    def _check_language_extinction(self, tick: int):
        extinct_lang_ids = []
        for lang_id, lang in self._languages.items():
            if len(lang.speaker_ids) < 2:
                extinct_lang_ids.append(lang_id)
                self._extinct_languages.append(lang)

        for lang_id in extinct_lang_ids:
            del self._languages[lang_id]
            for agent_id in list(self._language_membership.keys()):
                if self._language_membership[agent_id] == lang_id:
                    del self._language_membership[agent_id]

    def _emotional_contagion(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            agent_id = agent.id
            self._emotional_contagion_strength[agent_id] = self._emotional_contagion_strength.get(
                agent_id, 0.0
            )

            recent_messages = [
                u for u in self._pending_utterances[-20:] if u.receiver_id == agent_id
            ]

            for utterance in recent_messages:
                if utterance.tick < ctx.tick - 50:
                    continue
                sender = self.world.agents.get(utterance.sender_id)
                if sender is None or not sender.is_alive:
                    continue

                if not self._detect_deception(sender, utterance)[0]:
                    contagion_factor = self._calculate_contagion_factor(agent, sender, utterance)

                    if utterance.context == "danger":
                        agent.emotion.fear += 0.15 * contagion_factor
                        agent.emotion.fear = min(1.0, agent.emotion.fear)
                    elif utterance.context == "friend":
                        agent.emotion.joy += 0.1 * contagion_factor
                        agent.emotion.joy = min(1.0, agent.emotion.joy)
                    elif utterance.context == "threat":
                        agent.emotion.anger += 0.12 * contagion_factor
                        agent.emotion.anger = min(1.0, agent.emotion.anger)

                    self._emotional_contagion_strength[agent_id] = min(
                        1.0,
                        self._emotional_contagion_strength.get(agent_id, 0.0)
                        + 0.05 * contagion_factor,
                    )

            self._emotional_contagion_strength[agent_id] *= 0.95

    def _calculate_contagion_factor(
        self, receiver: Agent, sender: Agent, utterance: CommunicativeAct
    ) -> float:
        base_factor = 0.5

        trust = receiver.reputation.get(sender.id, 0.5)
        base_factor *= trust

        if sender.group_id == receiver.group_id:
            base_factor *= 1.3

        receiver_complexity = receiver.neural_complexity
        sender_complexity = sender.neural_complexity
        if receiver_complexity > 0:
            similarity = 1.0 - abs(receiver_complexity - sender_complexity) / 10.0
            base_factor *= max(0.5, similarity)

        return base_factor

    def _detect_deception(self, sender: Agent, utterance: CommunicativeAct) -> Tuple[bool, float]:
        if utterance.receiver_id is None:
            return False, 0.0

        receiver_id = utterance.receiver_id
        receiver = self.world.agents.get(receiver_id)
        if receiver is None:
            return False, 0.0

        sender_complexity = sender.neural_complexity
        receiver_complexity = receiver.neural_complexity

        deception_ticks = self._deception_history.get((receiver_id, sender.id), [])
        recent_deceptions = (
            [t for t in deception_ticks if t > receiver.world_ctx.tick - 100]
            if hasattr(receiver, "world_ctx")
            else deception_ticks
        )

        previously_deceived = len(recent_deceptions) > 0

        if not previously_deceived:
            return False, 0.0

        if receiver_complexity <= sender_complexity:
            return False, 0.0

        detection_prob = 0.3 * (receiver_complexity - sender_complexity) / 10.0
        detected = np.random.random() < detection_prob

        return detected, detection_prob

    def _record_deception(self, deceiver_id: AgentID, target_id: AgentID, tick: int):
        key = (target_id, deceiver_id)
        if key not in self._deception_history:
            self._deception_history[key] = []
        self._deception_history[key].append(tick)
        if len(self._deception_history[key]) > 100:
            self._deception_history[key] = self._deception_history[key][-100:]

    def _update_trust_reputations(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            for other_id, history in list(self._reputation_history.items()):
                if history and history[-1][0] < ctx.tick - 100:
                    trust_val = history[-1][1]
                    decay = 0.01
                    new_trust = max(0.0, trust_val - decay)
                    history.append((ctx.tick, new_trust))

            for other_id in list(agent.reputation.keys()):
                key = (agent.id, other_id)
                if key in self._reputation_history:
                    history = self._reputation_history[key]
                    if history and history[-1][0] == ctx.tick:
                        continue
                    history.append((ctx.tick, agent.reputation[other_id]))
                    if len(history) > 100:
                        self._reputation_history[key] = history[-100:]

    def _update_trust(
        self, agent_id: AgentID, other_id: AgentID, tick: int, is_honest: bool = True
    ):
        key = (agent_id, other_id)
        if key not in self._reputation_history:
            self._reputation_history[key] = []

        current_trust = self.world.agents[other_id].reputation.get(agent_id, 0.5)

        if is_honest:
            recent_ticks = [t for t, _ in self._reputation_history[key][-50:] if tick - t < 50]
            honest_interactions = len(recent_ticks)
            trust_restoration = 0.02 * min(honest_interactions, 25)
            current_trust = min(1.0, current_trust + trust_restoration)
        else:
            current_trust = max(0.0, current_trust - 0.3)

        self.world.agents[other_id].reputation[agent_id] = current_trust
        self._reputation_history[key].append((tick, current_trust))

        if len(self._reputation_history[key]) > 100:
            self._reputation_history[key] = self._reputation_history[key][-100:]

    def _update_trust_on_interaction(
        self, agent_id: AgentID, other_id: AgentID, utterance: CommunicativeAct, tick: int
    ):
        key = (agent_id, other_id)
        if key not in self._reputation_history:
            self._reputation_history[key] = []

        current_trust = self.world.agents[other_id].reputation.get(agent_id, 0.5)

        if utterance.is_deceptive:
            detected, _ = self._detect_deception(self.world.agents[agent_id], utterance)
            if detected:
                current_trust = max(0.0, current_trust - 0.3)
            else:
                current_trust = max(0.0, current_trust - 0.05)
        else:
            recent_ticks = [t for t, _ in self._reputation_history[key][-50:] if tick - t < 50]
            honest_interactions = len(recent_ticks)
            trust_restoration = 0.02 * min(honest_interactions, 25)
            current_trust = min(1.0, current_trust + trust_restoration)

        self.world.agents[other_id].reputation[agent_id] = current_trust
        self._reputation_history[key].append((tick, current_trust))

        if len(self._reputation_history[key]) > 100:
            self._reputation_history[key] = self._reputation_history[key][-100:]

    def _get_or_create_vocabulary(self, agent: Agent) -> Set[int]:
        if agent.id not in self._vocabularies:
            self._vocabularies[agent.id] = set(self._protosigns.keys())
        return self._vocabularies[agent.id]

    def _get_vocabulary_size(self, agent: Agent) -> int:
        return len(self._get_or_create_vocabulary(agent))

    def _get_nearby_agents(self, agent: Agent, radius: float) -> List[Agent]:
        nearby = []
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            if dx * dx + dy * dy <= radius * radius:
                nearby.append(other)
        return nearby

    def get_language_stats(self) -> Dict:
        if not self._symbol_table:
            return {
                "vocab_size": 0,
                "total_utterances": 0,
                "avg_vocab_per_agent": 0.0,
                "living_languages": 0,
                "extinct_languages": 0,
                "language_families": [],
                "most_expressive_language": None,
            }

        total_vocab = sum(1 for s in self._symbol_table.values() if s.frequency > 0)
        avg_vocab = (
            np.mean([len(v) for v in self._vocabularies.values()]) if self._vocabularies else 0.0
        )

        living_languages = len(self._languages)
        extinct_languages = len(self._extinct_languages)

        language_families: Dict[int, List[int]] = {}
        for lang_id, lang in self._languages.items():
            parent_id = lang.parent_language_id
            if parent_id is not None:
                if parent_id not in language_families:
                    language_families[parent_id] = [parent_id]
                language_families[parent_id].append(lang_id)

        family_sizes = [(pid, len(members)) for pid, members in language_families.items()]

        most_expressive_lang = None
        if self._languages:
            most_expressive_lang = max(
                self._languages.values(), key=lambda l: len(l.vocabulary), default=None
            )
            if most_expressive_lang:
                most_expressive_lang = most_expressive_lang.id

        composed_count = sum(1 for s in self._symbol_table.values() if s.is_composed)

        return {
            "vocab_size": total_vocab,
            "total_utterances": len(self._pending_utterances),
            "avg_vocab_per_agent": float(avg_vocab),
            "tracked_agents": len(self._vocabularies),
            "most_used_symbol": max(
                self._symbol_table.items(), key=lambda x: x[1].frequency, default=(0, None)
            )[0]
            if self._symbol_table
            else None,
            "living_languages": living_languages,
            "extinct_languages": extinct_languages,
            "language_families": family_sizes,
            "most_expressive_language": most_expressive_lang,
            "composed_symbols": composed_count,
        }

    def get_trust_network(self) -> Dict:
        edges = []
        trust_matrix: Dict[AgentID, Dict[AgentID, float]] = {}

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            trust_matrix[agent.id] = dict(agent.reputation)

        for agent_id, reputations in trust_matrix.items():
            for other_id, trust in reputations.items():
                if trust > 0.3:
                    edges.append(
                        {
                            "from": agent_id,
                            "to": other_id,
                            "trust": trust,
                        }
                    )

        return {
            "nodes": list(trust_matrix.keys()),
            "edges": edges,
            "total_trust_connections": len(edges),
        }
