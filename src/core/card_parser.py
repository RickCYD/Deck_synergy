"""
Unified Card Parser - Single Source of Truth

This module provides a single, unified way to parse MTG card oracle text.
All card ability extraction happens here, eliminating duplication between
synergy detection and game simulation.

Usage:
    from src.core.card_parser import UnifiedCardParser

    parser = UnifiedCardParser()
    abilities = parser.parse_card(card_dict)

    # Check what the card does
    if abilities.has_rally:
        print(f"Rally triggers: {abilities.get_triggers('rally')}")

    if abilities.has_prowess:
        print(f"Prowess creature: {abilities.name}")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
import re


@dataclass
class TriggerAbility:
    """
    Represents a triggered ability.

    Examples:
        - "Whenever a creature enters, draw a card" (ETB trigger)
        - "Rally — Whenever an Ally enters, gain haste" (Rally trigger)
        - "Whenever you cast a noncreature spell, +1/+1" (Prowess/Spellslinger)
    """
    event: str  # 'etb', 'attack', 'death', 'cast_spell', 'rally', etc.
    condition: Optional[str]  # e.g., "if you control an artifact"
    effect: str  # What happens (descriptive)
    effect_type: str  # 'damage', 'draw', 'anthem', 'tokens', 'counters', etc.
    targets: List[str]  # What's affected
    value: float  # Numeric value if applicable (damage amount, token count, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info

    def __repr__(self):
        return f"TriggerAbility(event={self.event}, effect_type={self.effect_type}, value={self.value})"


@dataclass
class StaticAbility:
    """
    Static effects that are always active.

    Examples:
        - "Creatures you control get +1/+1" (Anthem)
        - "Spells you cast cost {1} less" (Cost reduction)
        - "Creatures you control have haste" (Keyword grant)
    """
    ability_type: str  # 'anthem', 'cost_reduction', 'keyword_grant', 'protection'
    effect: str  # Descriptive text
    targets: List[str]  # What's affected
    value: float  # Numeric value (e.g., +1/+1 is value=1.0)
    conditions: List[str] = field(default_factory=list)  # When it applies

    def __repr__(self):
        return f"StaticAbility(type={self.ability_type}, targets={self.targets}, value={self.value})"


@dataclass
class ActivatedAbility:
    """
    Activated abilities with costs.

    Examples:
        - "{T}: Draw a card" (Tap ability)
        - "{2}{R}: Deal 3 damage to target" (Mana ability)
        - "Sacrifice a creature: Gain 1 life" (Sacrifice ability)
    """
    cost: str  # Mana/tap/sacrifice cost
    effect: str  # What it does
    effect_type: str  # 'damage', 'draw', 'removal', etc.
    value: float  # Numeric value

    def __repr__(self):
        return f"ActivatedAbility(cost={self.cost}, effect_type={self.effect_type})"


@dataclass
class CardAbilities:
    """
    Complete parsed card abilities.

    This is the unified representation used by both synergy detection
    and game simulation.
    """
    name: str
    triggers: List[TriggerAbility] = field(default_factory=list)
    static_abilities: List[StaticAbility] = field(default_factory=list)
    activated_abilities: List[ActivatedAbility] = field(default_factory=list)
    keywords: Set[str] = field(default_factory=set)
    creature_types: Set[str] = field(default_factory=set)

    # Cached flags for quick checks (set by parser)
    has_etb: bool = False
    has_rally: bool = False
    has_prowess: bool = False
    has_magecraft: bool = False
    creates_tokens: bool = False
    is_removal: bool = False
    is_ramp: bool = False
    is_draw: bool = False
    is_sacrifice_outlet: bool = False
    is_spell: bool = False
    cmc: float = 0.0

    def get_triggers(self, event: str) -> List[TriggerAbility]:
        """Get all triggers for a specific event"""
        return [t for t in self.triggers if t.event == event]

    def has_trigger(self, event: str) -> bool:
        """Check if card has a specific trigger type"""
        return any(t.event == event for t in self.triggers)

    def get_static_abilities(self, ability_type: str) -> List[StaticAbility]:
        """Get all static abilities of a specific type"""
        return [a for a in self.static_abilities if a.ability_type == ability_type]

    def __repr__(self):
        return f"CardAbilities({self.name}, triggers={len(self.triggers)}, static={len(self.static_abilities)})"


class UnifiedCardParser:
    """
    Unified card parser - single source of truth for all card abilities.

    This replaces:
    - src/utils/*_extractors.py (14 files) for synergy detection
    - Simulation/oracle_text_parser.py for simulation

    Now both systems use the same parsed data.
    """

    def __init__(self):
        # Cache parsed cards to avoid re-parsing
        self._cache: Dict[str, CardAbilities] = {}

    def parse_card(self, card: Dict) -> CardAbilities:
        """
        Main entry point - parse everything about a card.

        Args:
            card: Card dict with 'oracle_text', 'type_line', 'keywords', etc.

        Returns:
            CardAbilities with all extracted information
        """
        name = card.get('name', '')

        # Check cache first
        if name in self._cache:
            return self._cache[name]

        text = card.get('oracle_text', '').lower()
        type_line = card.get('type_line', '')
        card_keywords = card.get('keywords', [])

        # Parse all ability types
        triggers = self._parse_triggers(text, type_line, card_keywords)
        static = self._parse_static_abilities(text, type_line)
        activated = self._parse_activated_abilities(text)
        keywords = self._parse_keywords(card_keywords, text)
        types = self._parse_creature_types(type_line)

        # Calculate cached flags
        flags = self._calculate_flags(triggers, static, activated, keywords, text, type_line, card)

        abilities = CardAbilities(
            name=name,
            triggers=triggers,
            static_abilities=static,
            activated_abilities=activated,
            keywords=keywords,
            creature_types=types,
            **flags
        )

        # Cache result
        self._cache[name] = abilities

        return abilities

    def clear_cache(self):
        """Clear the parser cache (e.g., when analyzing a new deck)"""
        self._cache.clear()

    # =========================================================================
    # TRIGGER PARSING
    # =========================================================================

    def _parse_triggers(self, text: str, type_line: str, keywords: List[str]) -> List[TriggerAbility]:
        """Parse all triggered abilities"""
        triggers = []

        # ETB triggers
        triggers.extend(self._parse_etb_triggers(text))

        # Rally (Ally ETB) triggers
        triggers.extend(self._parse_rally_triggers(text, type_line))

        # Attack triggers
        triggers.extend(self._parse_attack_triggers(text))

        # Cast spell triggers (prowess, magecraft, spellslinger)
        triggers.extend(self._parse_cast_triggers(text, keywords))

        # Death triggers
        triggers.extend(self._parse_death_triggers(text))

        # Sacrifice triggers
        triggers.extend(self._parse_sacrifice_triggers(text))

        # Landfall triggers
        triggers.extend(self._parse_landfall_triggers(text))

        return triggers

    def _parse_etb_triggers(self, text: str) -> List[TriggerAbility]:
        """Parse ETB (enter the battlefield) triggers"""
        triggers = []

        # Pattern: "When/Whenever ... enters the battlefield"
        etb_patterns = [
            (r'when(?:ever)? .* enters the battlefield, draw (\w+) cards?', 'draw'),
            (r'when(?:ever)? .* enters the battlefield, create (\w+) .*tokens?', 'tokens'),
            (r'when(?:ever)? .* enters the battlefield, deal (\w+) damage', 'damage'),
            (r'when(?:ever)? .* enters the battlefield, put (\w+) \+1/\+1 counter', 'counters'),
        ]

        for pattern, effect_type in etb_patterns:
            match = re.search(pattern, text)
            if match:
                value_str = match.group(1)
                value = self._parse_number(value_str)

                triggers.append(TriggerAbility(
                    event='etb',
                    condition=None,
                    effect=f"When enters, {effect_type}",
                    effect_type=effect_type,
                    targets=['self' if 'this' in text else 'any'],
                    value=value,
                    metadata={}
                ))

        # Generic ETB (no specific effect parsed yet)
        if 'enters the battlefield' in text and not triggers:
            triggers.append(TriggerAbility(
                event='etb',
                condition=None,
                effect=text[:100],
                effect_type='generic',
                targets=['unknown'],
                value=0.0,
                metadata={}
            ))

        return triggers

    def _parse_rally_triggers(self, text: str, type_line: str) -> List[TriggerAbility]:
        """
        Parse Rally mechanic (Ally ETB triggers).

        Rally = "Whenever this creature or another Ally enters the battlefield"

        Replaces logic from:
        - src/utils/etb_extractors.py::extract_rally_triggers()
        - Simulation/oracle_text_parser.py::parse_rally_triggers()
        """
        triggers = []

        # Rally patterns
        rally_patterns = [
            r'rally\s*[—-]\s*whenever',
            r'whenever this creature or another ally.*enters',
            r'whenever.*ally.*enters.*battlefield.*under your control',
        ]

        has_rally = any(re.search(pattern, text) for pattern in rally_patterns)

        if has_rally:
            # Determine effect type
            effect_type = 'unknown'
            effect = 'rally'
            value = 0.0

            if 'gain haste' in text or 'have haste' in text:
                effect_type = 'grant_keyword'
                effect = 'haste'
            elif 'gain vigilance' in text or 'have vigilance' in text:
                effect_type = 'grant_keyword'
                effect = 'vigilance'
            elif 'gain lifelink' in text or 'have lifelink' in text:
                effect_type = 'grant_keyword'
                effect = 'lifelink'
            elif 'gain double strike' in text or 'have double strike' in text:
                effect_type = 'grant_keyword'
                effect = 'double strike'
            elif re.search(r'put.*\+1/\+1 counter', text):
                effect_type = 'counters'
                effect = '+1/+1 counters'
                value = 1.0

            triggers.append(TriggerAbility(
                event='rally',
                condition='ally_enters',
                effect=effect,
                effect_type=effect_type,
                targets=['creatures_you_control'],
                value=value,
                metadata={'is_ally': 'ally' in type_line.lower()}
            ))

        return triggers

    def _parse_cast_triggers(self, text: str, keywords: List[str]) -> List[TriggerAbility]:
        """
        Parse spell cast triggers (prowess, magecraft, spellslinger).

        Examples:
        - Prowess: "Whenever you cast a noncreature spell, +1/+1"
        - Magecraft: "Whenever you cast or copy an instant or sorcery"
        - Spellslinger: "Whenever you cast an instant or sorcery spell"
        """
        triggers = []

        # Prowess
        if 'prowess' in [kw.lower() for kw in keywords] or 'prowess' in text:
            triggers.append(TriggerAbility(
                event='cast_noncreature_spell',
                condition=None,
                effect='prowess: +1/+1 until end of turn',
                effect_type='buff',
                targets=['self'],
                value=1.0,
                metadata={'is_prowess': True}
            ))

        # Magecraft
        if 'magecraft' in text:
            triggers.append(TriggerAbility(
                event='cast_or_copy_instant_sorcery',
                condition=None,
                effect='magecraft trigger',
                effect_type='generic',
                targets=['varies'],
                value=0.0,
                metadata={'is_magecraft': True}
            ))

        # Spellslinger patterns
        spellslinger_patterns = [
            (r'whenever you cast an instant or sorcery', 'instant_or_sorcery'),
            (r'whenever you cast a noncreature spell', 'noncreature'),
            (r'whenever you cast an instant', 'instant'),
            (r'whenever you cast a sorcery', 'sorcery'),
        ]

        for pattern, spell_type in spellslinger_patterns:
            if re.search(pattern, text):
                # Determine effect
                effect_type = 'generic'
                value = 0.0

                if 'create' in text and 'token' in text:
                    effect_type = 'tokens'
                    value = 1.0
                elif 'draw' in text:
                    effect_type = 'draw'
                    value = 1.0
                elif 'deal' in text and 'damage' in text:
                    effect_type = 'damage'
                    # Try to extract damage amount
                    dmg_match = re.search(r'deal (\d+) damage', text)
                    if dmg_match:
                        value = float(dmg_match.group(1))

                triggers.append(TriggerAbility(
                    event=f'cast_{spell_type}_spell',
                    condition=None,
                    effect='spellslinger trigger',
                    effect_type=effect_type,
                    targets=['varies'],
                    value=value,
                    metadata={'spell_type': spell_type}
                ))
                break  # Only add one spellslinger trigger

        return triggers

    def _parse_attack_triggers(self, text: str) -> List[TriggerAbility]:
        """Parse attack triggers"""
        triggers = []

        attack_patterns = [
            r'whenever .* attacks',
            r'whenever you attack',
            r'whenever .* attacks.*player',
        ]

        for pattern in attack_patterns:
            if re.search(pattern, text):
                triggers.append(TriggerAbility(
                    event='attack',
                    condition=None,
                    effect='attack trigger',
                    effect_type='generic',
                    targets=['varies'],
                    value=0.0,
                    metadata={}
                ))
                break

        return triggers

    def _parse_death_triggers(self, text: str) -> List[TriggerAbility]:
        """Parse death/dies triggers"""
        triggers = []

        death_patterns = [
            r'when .* dies',
            r'whenever .* dies',
            r'whenever .* is put into .* graveyard',
        ]

        for pattern in death_patterns:
            if re.search(pattern, text):
                triggers.append(TriggerAbility(
                    event='death',
                    condition=None,
                    effect='death trigger',
                    effect_type='generic',
                    targets=['varies'],
                    value=0.0,
                    metadata={}
                ))
                break

        return triggers

    def _parse_sacrifice_triggers(self, text: str) -> List[TriggerAbility]:
        """Parse sacrifice triggers"""
        triggers = []

        if re.search(r'whenever you sacrifice', text):
            triggers.append(TriggerAbility(
                event='sacrifice',
                condition=None,
                effect='sacrifice trigger',
                effect_type='generic',
                targets=['varies'],
                value=0.0,
                metadata={}
            ))

        return triggers

    def _parse_landfall_triggers(self, text: str) -> List[TriggerAbility]:
        """Parse landfall triggers"""
        triggers = []

        if 'landfall' in text or re.search(r'whenever a land enters.*under your control', text):
            triggers.append(TriggerAbility(
                event='landfall',
                condition=None,
                effect='landfall trigger',
                effect_type='generic',
                targets=['varies'],
                value=0.0,
                metadata={}
            ))

        return triggers

    # =========================================================================
    # STATIC ABILITY PARSING
    # =========================================================================

    def _parse_static_abilities(self, text: str, type_line: str) -> List[StaticAbility]:
        """Parse static abilities (anthems, cost reduction, etc.)"""
        abilities = []

        # Anthem effects
        abilities.extend(self._parse_anthems(text))

        # Cost reduction
        abilities.extend(self._parse_cost_reduction(text))

        # Keyword grants
        abilities.extend(self._parse_keyword_grants(text))

        return abilities

    def _parse_anthems(self, text: str) -> List[StaticAbility]:
        """Parse anthem effects (static +X/+X)"""
        anthems = []

        anthem_patterns = [
            r'creatures you control get (\+\d+)/(\+\d+)',
            r'other creatures you control get (\+\d+)/(\+\d+)',
            r'(\w+) creatures you control get (\+\d+)/(\+\d+)',
        ]

        for pattern in anthem_patterns:
            match = re.search(pattern, text)
            if match:
                # Extract power/toughness bonus
                groups = match.groups()
                if len(groups) >= 2:
                    power_str = groups[-2]
                    toughness_str = groups[-1]
                    power = float(power_str.replace('+', ''))
                    toughness = float(toughness_str.replace('+', ''))
                    value = (power + toughness) / 2  # Average

                    anthems.append(StaticAbility(
                        ability_type='anthem',
                        effect=f"+{power}/+{toughness}",
                        targets=['creatures_you_control'],
                        value=value,
                        conditions=[]
                    ))

        return anthems

    def _parse_cost_reduction(self, text: str) -> List[StaticAbility]:
        """Parse cost reduction effects"""
        reductions = []

        if re.search(r'cost.*less|costs.*less', text):
            reductions.append(StaticAbility(
                ability_type='cost_reduction',
                effect='cost reduction',
                targets=['spells'],
                value=1.0,
                conditions=[]
            ))

        return reductions

    def _parse_keyword_grants(self, text: str) -> List[StaticAbility]:
        """Parse static keyword grants"""
        grants = []

        keyword_patterns = [
            (r'creatures you control have (\w+)', 'creatures_you_control'),
            (r'other creatures you control have (\w+)', 'other_creatures'),
        ]

        for pattern, targets in keyword_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                keyword = match.group(1)
                grants.append(StaticAbility(
                    ability_type='keyword_grant',
                    effect=f"grant {keyword}",
                    targets=[targets],
                    value=0.5,
                    conditions=[]
                ))

        return grants

    # =========================================================================
    # ACTIVATED ABILITY PARSING
    # =========================================================================

    def _parse_activated_abilities(self, text: str) -> List[ActivatedAbility]:
        """Parse activated abilities with costs"""
        abilities = []

        # Simple pattern: {cost}: effect
        # This is a simplified implementation
        if '{' in text and '}:' in text:
            abilities.append(ActivatedAbility(
                cost='mana',
                effect='activated ability',
                effect_type='generic',
                value=0.0
            ))

        return abilities

    # =========================================================================
    # KEYWORD AND TYPE PARSING
    # =========================================================================

    def _parse_keywords(self, keywords: List[str], text: str) -> Set[str]:
        """Parse creature keywords"""
        keyword_set = set(kw.lower() for kw in keywords)

        # Also check text for keywords not in keywords field
        common_keywords = [
            'flying', 'haste', 'vigilance', 'trample', 'lifelink',
            'deathtouch', 'first strike', 'double strike', 'menace',
            'prowess', 'hexproof', 'indestructible', 'flash'
        ]

        for kw in common_keywords:
            if kw in text:
                keyword_set.add(kw)

        return keyword_set

    def _parse_creature_types(self, type_line: str) -> Set[str]:
        """Parse creature types from type line"""
        if '—' not in type_line:
            return set()

        try:
            _, subtypes = type_line.split('—', 1)
            types = {t.strip() for t in subtypes.split() if t.strip()}
            return types
        except ValueError:
            return set()

    # =========================================================================
    # FLAG CALCULATION
    # =========================================================================

    def _calculate_flags(self, triggers: List[TriggerAbility],
                         static: List[StaticAbility],
                         activated: List[ActivatedAbility],
                         keywords: Set[str],
                         text: str,
                         type_line: str,
                         card: Dict) -> Dict[str, Any]:
        """Calculate cached flags for quick checks"""
        return {
            'has_etb': any(t.event == 'etb' for t in triggers),
            'has_rally': any(t.event == 'rally' for t in triggers),
            'has_prowess': 'prowess' in keywords or any(t.metadata.get('is_prowess') for t in triggers),
            'has_magecraft': any(t.metadata.get('is_magecraft') for t in triggers),
            'creates_tokens': 'create' in text and 'token' in text,
            'is_removal': self._is_removal(text, type_line),
            'is_ramp': self._is_ramp(text, type_line),
            'is_draw': 'draw' in text and 'card' in text,
            'is_sacrifice_outlet': self._is_sacrifice_outlet(text),
            'is_spell': 'instant' in type_line.lower() or 'sorcery' in type_line.lower(),
            'cmc': card.get('cmc', 0.0),
        }

    def _is_removal(self, text: str, type_line: str) -> bool:
        """Check if card is removal"""
        removal_keywords = ['destroy', 'exile', 'return', 'bounce', 'counter target']
        return any(kw in text for kw in removal_keywords) and \
               ('instant' in type_line.lower() or 'sorcery' in type_line.lower())

    def _is_ramp(self, text: str, type_line: str) -> bool:
        """Check if card is ramp"""
        if 'land' in type_line.lower():
            return False  # Lands themselves aren't "ramp"
        return ('search' in text and 'land' in text) or \
               ('add' in text and any(c in text for c in ['{w}', '{u}', '{b}', '{r}', '{g}']))

    def _is_sacrifice_outlet(self, text: str) -> bool:
        """Check if card is a sacrifice outlet"""
        return 'sacrifice' in text and ':' in text  # Has activation cost with sacrifice

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _parse_number(self, text: str) -> float:
        """Parse number from text (handles 'a', 'two', '3', etc.)"""
        number_map = {
            'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3,
            'four': 4, 'five': 5, 'six': 6, 'seven': 7,
            'eight': 8, 'nine': 9, 'ten': 10, 'x': -1
        }

        text_lower = text.lower().strip()

        if text_lower in number_map:
            return float(number_map[text_lower])

        # Try to parse as number
        try:
            return float(text_lower)
        except ValueError:
            return 0.0
