"""
Synergy Detection Rules
Individual rule functions for detecting different types of synergies between cards
"""

import re
from src.synergy_engine.regex_cache import search_cached, match_cached, findall_cached
from typing import Dict, List, Optional, Set
from functools import lru_cache
from src.utils.damage_extractors import classify_damage_effect
from src.synergy_engine.card_advantage_synergies import CARD_ADVANTAGE_SYNERGY_RULES
from src.synergy_engine.ally_prowess_synergies import ALLY_PROWESS_SYNERGY_RULES
from src.synergy_engine.spellslinger_engine_synergies import SPELLSLINGER_ENGINE_SYNERGY_RULES
from src.utils.token_extractors import extract_token_creation, extract_token_type_preferences
from src.utils.recursion_extractors import extract_treasure_tokens
from src.utils.tribal_extractors import (
    extract_cares_about_chosen_type,
    extract_cares_about_same_type,
    extract_tribal_payoffs,
    get_creature_types,
    extract_is_changeling
)

# Cache for damage classifications to avoid recomputing for same cards
_damage_classification_cache = {}

def get_damage_classification(card: Dict) -> Dict:
    """Get cached damage classification for a card"""
    card_name = card.get('name')
    if card_name not in _damage_classification_cache:
        _damage_classification_cache[card_name] = classify_damage_effect(card)
    return _damage_classification_cache[card_name]

def clear_damage_classification_cache():
    """Clear the damage classification cache (call when analyzing new deck)"""
    global _damage_classification_cache
    _damage_classification_cache = {}


def detect_etb_triggers(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect ETB (Enters the Battlefield) trigger synergies

    Returns synergy if one card has ETB ability and another can trigger it (flicker/blink)
    """
    etb_keywords = ['enters the battlefield', 'when .* enters', 'whenever .* enters']
    # More specific flicker patterns - must include exile to be a true flicker effect
    flicker_keywords = [
        r'exile.*return.*to the battlefield',  # Standard flicker
        r'exile.*return.*under.*control',       # Variant flicker wording
        r'\bblink\b',                           # Blink keyword
        r'\bflicker\b'                          # Flicker keyword
    ]

    # Exclude reanimation patterns that aren't flicker
    anti_flicker = [
        r'return.*card.*from.*graveyard.*to the battlefield',  # Reanimation
        r'return.*from.*graveyard.*to.*hand',                  # Recursion
        r'return.*token',                                       # Token return (not flicker)
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 has ETB and card2 can trigger it
    card1_has_etb = any(search_cached(kw, card1_text) for kw in etb_keywords)
    card2_can_trigger = any(search_cached(kw, card2_text) for kw in flicker_keywords)
    card2_is_reanimation = any(search_cached(kw, card2_text) for kw in anti_flicker)

    # Only count as flicker if it's not reanimation
    if card1_has_etb and card2_can_trigger and not card2_is_reanimation:
        return {
            'name': 'ETB Trigger Synergy',
            'description': f"{card1['name']} has ETB abilities that {card2['name']} can repeatedly trigger",
            'value': 3.0,
            'category': 'triggers',
            'subcategory': 'etb_trigger'
        }

    # Check reverse
    card2_has_etb = any(search_cached(kw, card2_text) for kw in etb_keywords)
    card1_can_trigger = any(search_cached(kw, card1_text) for kw in flicker_keywords)
    card1_is_reanimation = any(search_cached(kw, card1_text) for kw in anti_flicker)

    if card2_has_etb and card1_can_trigger and not card1_is_reanimation:
        return {
            'name': 'ETB Trigger Synergy',
            'description': f"{card2['name']} has ETB abilities that {card1['name']} can repeatedly trigger",
            'value': 3.0,
            'category': 'triggers',
            'subcategory': 'etb_trigger'
        }

    return None


def detect_sacrifice_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect sacrifice outlet and fodder synergies"""
    # Sacrifice outlet patterns - must be able to sacrifice YOUR permanents
    sacrifice_outlet_patterns = [
        r'sacrifice a creature',
        r'sacrifice a permanent',
        r'sacrifice an artifact',
        r'sacrifice an enchantment',
        r'sacrifice.*you control',
        r'as an additional cost.*sacrifice',
        r'you may sacrifice',
        r'\{.*\}:.*sacrifice'  # Activated ability with sacrifice
    ]

    # Exclude patterns - opponent sacrificing is NOT a sacrifice outlet for you
    exclude_patterns = [
        r'opponent.*sacrifice',
        r'player.*sacrifice',
        r'counter.*unless.*sacrifice',  # Counterspells with sacrifice clause
        r'sacrifice this',               # Self-sacrifice (like fetch lands)
        r'sacrifice .* land.*search'    # Fetch lands that sacrifice themselves
    ]

    # Death trigger patterns - exclude self-death triggers
    death_trigger_keywords = [
        r'whenever (?:a|another|one or more) creature', # "whenever a creature dies"
        r'whenever.*creatures.*die',                     # "whenever one or more creatures die"
        r'when (?:a|another) creature.*dies',           # "when a creature dies"
        r'whenever (?:a|another) .*permanent.*dies',    # "whenever a permanent dies"
    ]
    # Self-death patterns to EXCLUDE (not payoffs, just self-triggers)
    self_death_patterns = [
        r'when (this|~) .*dies',                        # "when this creature dies"
        r'when (this|~) .*is put into.*graveyard',     # "when this is put into a graveyard"
        r'whenever (this|~) dies',                      # "whenever this dies"
    ]

    token_generation = [r'create.*token', r'put.*token']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_is_outlet = any(search_cached(pattern, card1_text) for pattern in sacrifice_outlet_patterns) and \
                      not any(search_cached(pattern, card1_text) for pattern in exclude_patterns)
    card2_creates_tokens = any(search_cached(kw, card2_text) for kw in token_generation)
    # Only count as death trigger if NOT a self-death trigger
    card2_death_trigger = any(search_cached(kw, card2_text) for kw in death_trigger_keywords) and \
                          not any(search_cached(kw, card2_text) for kw in self_death_patterns)

    if card1_is_outlet and (card2_creates_tokens or card2_death_trigger):
        return {
            'name': 'Sacrifice Synergy',
            'description': f"{card1['name']} can sacrifice permanents from {card2['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    # Check reverse
    card2_is_outlet = any(search_cached(pattern, card2_text) for pattern in sacrifice_outlet_patterns) and \
                      not any(search_cached(pattern, card2_text) for pattern in exclude_patterns)
    card1_creates_tokens = any(search_cached(kw, card1_text) for kw in token_generation)
    # Only count as death trigger if NOT a self-death trigger
    card1_death_trigger = any(search_cached(kw, card1_text) for kw in death_trigger_keywords) and \
                          not any(search_cached(kw, card1_text) for kw in self_death_patterns)

    if card2_is_outlet and (card1_creates_tokens or card1_death_trigger):
        return {
            'name': 'Sacrifice Synergy',
            'description': f"{card2['name']} can sacrifice permanents from {card1['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    return None


def detect_mana_color_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect mana production synergies - cards that produce mana matching color requirements"""
    # Mana production patterns (lands, mana dorks, rocks)
    mana_production_patterns = {
        'W': [r'add \{w\}', r'add.*white', r'add one mana of any color'],
        'U': [r'add \{u\}', r'add.*blue', r'add one mana of any color'],
        'B': [r'add \{b\}', r'add.*black', r'add one mana of any color'],
        'R': [r'add \{r\}', r'add.*red', r'add one mana of any color'],
        'G': [r'add \{g\}', r'add.*green', r'add one mana of any color']
    }

    # Colorless/generic mana production patterns
    colorless_patterns = [r'add \{c\}', r'add \{c\}\{c\}', r'add.*colorless mana']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Get mana cost colors (colors actually needed to cast)
    card1_colors = set(card1.get('colors', []))
    card2_colors = set(card2.get('colors', []))

    # Get CMC for generic mana detection
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 produces colorless mana and card2 has any mana cost
    # NOTE: Reduced weight from 1.0 to 0.2 - mana production is generic utility
    card1_produces_colorless = any(search_cached(pattern, card1_text) for pattern in colorless_patterns)
    if card1_produces_colorless and card2_cmc > 0:
        return {
            'name': 'Mana Acceleration',
            'description': f"{card1['name']} produces colorless mana for {card2['name']}'s generic cost",
            'value': 0.2,  # Reduced from 1.0 - too generic
            'category': 'mana_synergy',
            'subcategory': 'mana_production'
        }

    # Check if card2 produces colorless mana and card1 has any mana cost
    card2_produces_colorless = any(search_cached(pattern, card2_text) for pattern in colorless_patterns)
    if card2_produces_colorless and card1_cmc > 0:
        return {
            'name': 'Mana Acceleration',
            'description': f"{card2['name']} produces colorless mana for {card1['name']}'s generic cost",
            'value': 0.2,  # Reduced from 1.0 - too generic
            'category': 'mana_synergy',
            'subcategory': 'mana_production'
        }

    # Check if card1 produces mana and card2 needs that color
    for color, patterns in mana_production_patterns.items():
        card1_produces_color = any(search_cached(pattern, card1_text) for pattern in patterns) or \
                               ('land' in card1_type and color in card1_colors)

        if card1_produces_color and color in card2_colors:
            color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
            return {
                'name': 'Mana Fixing',
                'description': f"{card1['name']} produces {color_names[color]} mana for {card2['name']}'s cost",
                'value': 0.3,  # Reduced from 2.0 - mana fixing is generic utility
                'category': 'mana_synergy',
                'subcategory': 'mana_production'
            }

    # Check reverse
    for color, patterns in mana_production_patterns.items():
        card2_produces_color = any(search_cached(pattern, card2_text) for pattern in patterns) or \
                               ('land' in card2_type and color in card2_colors)

        if card2_produces_color and color in card1_colors:
            color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
            return {
                'name': 'Mana Fixing',
                'description': f"{card2['name']} produces {color_names[color]} mana for {card1['name']}'s cost",
                'value': 0.3,  # Reduced from 2.0 - mana fixing is generic utility
                'category': 'mana_synergy',
                'subcategory': 'mana_production'
            }

    return None


def detect_tribal_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect tribal synergies based on creature types

    Only triggers when a card ACTUALLY cares about a creature type with specific patterns,
    not just when the creature type appears in the text (e.g., in token creation).
    """
    card1_types = card1.get('card_types', {})
    card2_types = card2.get('card_types', {})

    card1_subtypes = set(card1_types.get('subtypes', []))
    card2_subtypes = set(card2_types.get('subtypes', []))

    # Fallback: parse type_line for subtypes when card_types are missing or empty
    def parse_subtypes_from_type_line(tl: str) -> Set[str]:
        tl = (tl or '').lower()
        if '—' in tl:
            try:
                _, sub = tl.split('—', 1)
                return {s.strip().capitalize() for s in sub.split() if s.strip()}
            except ValueError:
                return set()
        return set()

    if not card1_subtypes:
        card1_subtypes = parse_subtypes_from_type_line(card1.get('type_line', ''))
    if not card2_subtypes:
        card2_subtypes = parse_subtypes_from_type_line(card2.get('type_line', ''))

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Specific patterns that indicate a card CARES about a creature type
    def makes_tribal_pattern(creature_type: str) -> List[str]:
        """Generate patterns that indicate caring about a specific creature type"""
        ct = creature_type.lower()
        return [
            rf'whenever you cast a {ct}',
            rf'whenever a {ct} enters',
            rf'whenever a {ct} you control',
            rf'{ct}s you control get',
            rf'{ct}s you control have',
            rf'for each {ct} you control',
            rf'for each {ct}',
            rf'target {ct}',
            rf'choose a {ct}',
            rf'{ct} creatures you control',
            rf'other {ct}s you control',
            rf'other {ct} creatures',
            rf'{ct} spells you cast',
            rf'each {ct} you control',
        ]

    # Check if card1 cares about a type that card2 has
    for subtype in card2_subtypes:
        patterns = makes_tribal_pattern(subtype)
        if any(search_cached(pattern, card1_text) for pattern in patterns):
            return {
                'name': 'Tribal Synergy',
                'description': f"{card1['name']} cares about {subtype}s, {card2['name']} is a {subtype}",
                'value': 3.0,
                'category': 'benefits',
                'subcategory': 'tribal'
            }

    # Check if card2 cares about a type that card1 has
    for subtype in card1_subtypes:
        patterns = makes_tribal_pattern(subtype)
        if any(search_cached(pattern, card2_text) for pattern in patterns):
            return {
                'name': 'Tribal Synergy',
                'description': f"{card2['name']} cares about {subtype}s, {card1['name']} is a {subtype}",
                'value': 3.0,
                'category': 'benefits',
                'subcategory': 'tribal'
            }

    # Check for shared creature types
    shared_types = card1_subtypes.intersection(card2_subtypes)
    card1_is_creature = 'creature' in (card1.get('type_line', '').lower()) or 'Creature' in card1_types.get('main_types', [])
    card2_is_creature = 'creature' in (card2.get('type_line', '').lower()) or 'Creature' in card2_types.get('main_types', [])
    if shared_types and card1_is_creature and card2_is_creature:
        return {
            'name': 'Shared Tribe',
            'description': f"Both cards share creature type(s): {', '.join(shared_types)}",
            'value': 1.5,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    return None


def detect_tribal_chosen_type_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies involving "choose a creature type" effects.

    Examples:
    - Door of Destinies + any creatures
    - Coat of Arms + tribal deck
    - Radiant Destiny + creature deck
    """
    # Extract tribal payoffs for both cards
    card1_payoffs = extract_tribal_payoffs(card1)
    card2_payoffs = extract_tribal_payoffs(card2)

    card1_is_creature = 'creature' in card1.get('type_line', '').lower()
    card2_is_creature = 'creature' in card2.get('type_line', '').lower()

    # Card1 cares about chosen type, card2 is a creature
    if card1_payoffs['chosen_type']['cares_about_chosen_type'] and card2_is_creature:
        effect_type = card1_payoffs['chosen_type']['effect_type']
        value = 3.5  # Strong synergy because chosen type effects are powerful

        description = f"{card1['name']} can choose {card2['name']}'s creature type"
        if effect_type == 'anthem':
            description += " for a stat boost"
            value = 4.0
        elif effect_type == 'cost_reduction':
            description += " for cost reduction"
            value = 3.5
        elif effect_type in ['cast_trigger', 'etb_trigger']:
            description += " to trigger its ability"
            value = 4.0

        return {
            'name': 'Chosen Type Synergy',
            'description': description,
            'value': value,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    # Card2 cares about chosen type, card1 is a creature
    if card2_payoffs['chosen_type']['cares_about_chosen_type'] and card1_is_creature:
        effect_type = card2_payoffs['chosen_type']['effect_type']
        value = 3.5

        description = f"{card2['name']} can choose {card1['name']}'s creature type"
        if effect_type == 'anthem':
            description += " for a stat boost"
            value = 4.0
        elif effect_type == 'cost_reduction':
            description += " for cost reduction"
            value = 3.5
        elif effect_type in ['cast_trigger', 'etb_trigger']:
            description += " to trigger its ability"
            value = 4.0

        return {
            'name': 'Chosen Type Synergy',
            'description': description,
            'value': value,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    return None


def detect_tribal_same_type_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies involving "same type" or "share a creature type" effects.

    Examples:
    - Adaptive Automaton + creatures of same type
    - Metallic Mimic + creatures of same type
    - Cavern of Souls + creature spells
    """
    # Extract tribal payoffs
    card1_payoffs = extract_tribal_payoffs(card1)
    card2_payoffs = extract_tribal_payoffs(card2)

    # Get creature types
    card1_types = get_creature_types(card1)
    card2_types = get_creature_types(card2)

    card1_is_creature = 'creature' in card1.get('type_line', '').lower()
    card2_is_creature = 'creature' in card2.get('type_line', '').lower()

    # Handle Changelings (have all creature types)
    card1_is_changeling = extract_is_changeling(card1)
    card2_is_changeling = extract_is_changeling(card2)

    # Card1 cares about same type, card2 is a creature
    if card1_payoffs['same_type']['cares_about_same_type'] and card2_is_creature:
        effect_type = card1_payoffs['same_type']['effect_type']
        value = 3.5

        description = f"{card1['name']} benefits creatures that share types with {card2['name']}"
        if effect_type == 'anthem':
            description = f"{card1['name']} buffs creatures sharing types with {card2['name']}"
            value = 4.0
        elif effect_type == 'etb_trigger':
            description = f"{card1['name']} triggers when creatures share types with {card2['name']}"
            value = 3.5

        return {
            'name': 'Same Type Synergy',
            'description': description,
            'value': value,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    # Card2 cares about same type, card1 is a creature
    if card2_payoffs['same_type']['cares_about_same_type'] and card1_is_creature:
        effect_type = card2_payoffs['same_type']['effect_type']
        value = 3.5

        description = f"{card2['name']} benefits creatures that share types with {card1['name']}"
        if effect_type == 'anthem':
            description = f"{card2['name']} buffs creatures sharing types with {card1['name']}"
            value = 4.0
        elif effect_type == 'etb_trigger':
            description = f"{card2['name']} triggers when creatures share types with {card1['name']}"
            value = 3.5

        return {
            'name': 'Same Type Synergy',
            'description': description,
            'value': value,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    # Changeling synergies - changelings work with all tribal cards
    if card1_is_changeling and (card2_payoffs['tribal_lord']['is_tribal_lord'] or
                                 card2_payoffs['tribal_trigger']['has_tribal_trigger']):
        return {
            'name': 'Changeling Synergy',
            'description': f"{card1['name']} is a Changeling and benefits from {card2['name']}'s tribal effects",
            'value': 4.5,  # Changelings are very strong with tribal cards
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    if card2_is_changeling and (card1_payoffs['tribal_lord']['is_tribal_lord'] or
                                 card1_payoffs['tribal_trigger']['has_tribal_trigger']):
        return {
            'name': 'Changeling Synergy',
            'description': f"{card2['name']} is a Changeling and benefits from {card1['name']}'s tribal effects",
            'value': 4.5,
            'category': 'benefits',
            'subcategory': 'tribal'
        }

    return None


def detect_tribal_trigger_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies between tribal triggers and creatures.

    Examples:
    - "Whenever you cast an Elf spell" + Elf creatures
    - "Whenever a Goblin enters" + Goblin token makers
    """
    card1_payoffs = extract_tribal_payoffs(card1)
    card2_payoffs = extract_tribal_payoffs(card2)

    card1_types = get_creature_types(card1)
    card2_types = get_creature_types(card2)

    card1_is_creature = 'creature' in card1.get('type_line', '').lower()
    card2_is_creature = 'creature' in card2.get('type_line', '').lower()

    # Card1 has tribal trigger, card2 is relevant creature
    if card1_payoffs['tribal_trigger']['has_tribal_trigger']:
        trigger_types = card1_payoffs['tribal_trigger']['creature_types']
        trigger_type = card1_payoffs['tribal_trigger']['trigger_type']

        # Check if trigger is for "chosen" type and card2 is a creature
        if 'chosen' in trigger_types and card2_is_creature:
            value = 3.5
            if trigger_type == 'cast':
                description = f"{card1['name']} triggers when you cast creatures like {card2['name']}"
                value = 4.0
            elif trigger_type == 'etb':
                description = f"{card1['name']} triggers when creatures like {card2['name']} enter"
                value = 4.0
            else:
                description = f"{card1['name']} triggers with creatures like {card2['name']}"

            return {
                'name': 'Tribal Trigger Synergy',
                'description': description,
                'value': value,
                'category': 'combo',
                'subcategory': 'tribal'
            }

        # Check if trigger is for specific type that card2 has
        if card2_types and any(t in trigger_types for t in card2_types):
            matching_type = next(t for t in card2_types if t in trigger_types)
            value = 4.0

            if trigger_type == 'cast':
                description = f"{card1['name']} triggers when you cast {matching_type}s like {card2['name']}"
                value = 4.5
            elif trigger_type == 'etb':
                description = f"{card1['name']} triggers when {matching_type}s like {card2['name']} enter"
                value = 4.5
            elif trigger_type == 'dies':
                description = f"{card1['name']} triggers when {matching_type}s like {card2['name']} die"
                value = 4.0
            elif trigger_type == 'attacks':
                description = f"{card1['name']} triggers when {matching_type}s like {card2['name']} attack"
                value = 4.0
            else:
                description = f"{card1['name']} has tribal synergy with {card2['name']}"

            return {
                'name': 'Tribal Trigger Synergy',
                'description': description,
                'value': value,
                'category': 'combo',
                'subcategory': 'tribal'
            }

    # Card2 has tribal trigger, card1 is relevant creature (reverse check)
    if card2_payoffs['tribal_trigger']['has_tribal_trigger']:
        trigger_types = card2_payoffs['tribal_trigger']['creature_types']
        trigger_type = card2_payoffs['tribal_trigger']['trigger_type']

        if 'chosen' in trigger_types and card1_is_creature:
            value = 3.5
            if trigger_type == 'cast':
                description = f"{card2['name']} triggers when you cast creatures like {card1['name']}"
                value = 4.0
            elif trigger_type == 'etb':
                description = f"{card2['name']} triggers when creatures like {card1['name']} enter"
                value = 4.0
            else:
                description = f"{card2['name']} triggers with creatures like {card1['name']}"

            return {
                'name': 'Tribal Trigger Synergy',
                'description': description,
                'value': value,
                'category': 'combo',
                'subcategory': 'tribal'
            }

        if card1_types and any(t in trigger_types for t in card1_types):
            matching_type = next(t for t in card1_types if t in trigger_types)
            value = 4.0

            if trigger_type == 'cast':
                description = f"{card2['name']} triggers when you cast {matching_type}s like {card1['name']}"
                value = 4.5
            elif trigger_type == 'etb':
                description = f"{card2['name']} triggers when {matching_type}s like {card1['name']} enter"
                value = 4.5
            elif trigger_type == 'dies':
                description = f"{card2['name']} triggers when {matching_type}s like {card1['name']} die"
                value = 4.0
            elif trigger_type == 'attacks':
                description = f"{card2['name']} triggers when {matching_type}s like {card1['name']} attack"
                value = 4.0
            else:
                description = f"{card2['name']} has tribal synergy with {card1['name']}"

            return {
                'name': 'Tribal Trigger Synergy',
                'description': description,
                'value': value,
                'category': 'combo',
                'subcategory': 'tribal'
            }

    return None


def detect_card_draw_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect card draw and card advantage synergies"""
    draw_keywords = ['draw.*card', 'draws.*card', 'you draw']
    wheel_keywords = ['each player draws', 'discard.*hand.*draw']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_draws = any(search_cached(kw, card1_text) for kw in draw_keywords + wheel_keywords)
    card2_draws = any(search_cached(kw, card2_text) for kw in draw_keywords + wheel_keywords)

    # DISABLED: Both cards draw - card advantage engine
    # This creates false synergies between any two draw cards
    # Cards that both draw don't synergize just because they share the same role
    # Real synergies are when one card enables/enhances another, not when they do the same thing
    # if card1_draws and card2_draws:
    #     return {
    #         'name': 'Card Draw Engine',
    #         'description': f"Both cards contribute to card advantage",
    #         'value': 2.0,
    #         'category': 'card_advantage',
    #         'subcategory': 'draw_engine'
    #     }

    return None


def detect_ramp_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect mana ramp synergies.

    Heuristic rules:
    - Treat NON-LAND cards that add mana or fetch/put lands as ramp (mana rocks/dorks, Cultivate effects).
    - Treat LAND cards as NOT ramp for this pairwise rule (regular lands are baseline, not enablers).
    - Include extra land drop effects ("play an additional land") as ramp.
    """
    ramp_keywords = [
        r'search.*library.*land',
        r'put.*land.*battlefield',
        r'add.*mana',
        r'play an additional land',
        r'you may play an additional land',
    ]
    high_cmc_threshold = 6

    card1_text = (card1.get('oracle_text') or '').lower()
    card2_text = (card2.get('oracle_text') or '').lower()

    card1_type = (card1.get('type_line') or '')
    card2_type = (card2.get('type_line') or '')
    card1_is_land = 'land' in card1_type.lower()
    card2_is_land = 'land' in card2_type.lower()

    # Only non-lands can be considered 
    card1_is_ramp = (not card1_is_land) and any(search_cached(kw, card1_text) for kw in ramp_keywords)
    card2_is_ramp = (not card2_is_land) and any(search_cached(kw, card2_text) for kw in ramp_keywords)

    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Ramp enables high CMC card
    # NOTE: Reduced weight from 2.0 to 0.3 because this creates too many generic synergies
    # Ramp is utility, not a strategic combo. Every ramp spell pairs with every big spell,
    # creating hundreds of low-value edges that drown out actual strategic synergies.
    if card1_is_ramp and card2_cmc >= high_cmc_threshold:
        return {
            'name': 'Ramp Enabler',
            'description': f"{card1['name']} helps cast expensive {card2['name']} (CMC {card2_cmc})",
            'value': 0.3,  # Reduced from 2.0 - generic utility, not strategic synergy
            'category': 'role_interaction',
            'subcategory': 'ramp'
        }

    if card2_is_ramp and card1_cmc >= high_cmc_threshold:
        return {
            'name': 'Ramp Enabler',
            'description': f"{card2['name']} helps cast expensive {card1['name']} (CMC {card1_cmc})",
            'value': 0.3,  # Reduced from 2.0 - generic utility, not strategic synergy
            'category': 'role_interaction',
            'subcategory': 'ramp'
        }

    return None


def detect_type_matters_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect synergies where one card cares about the type of another"""
    # Define patterns that indicate a card positively cares about a type
    positive_care_patterns = {
        'artifact': [r'artifacts you control get', r'for each artifact you control', r'artifacts.*you control.*have', r'artifacts enter'],
        'enchantment': [r'enchantments you control get', r'for each enchantment you control', r'enchantments.*you control.*have'],
        'creature': [r'creatures you control get', r'for each creature you control', r'creatures.*you control.*have', r'other creatures you control', r'creature tokens you control'],
        'instant': [r'instant.*from.*graveyard', r'whenever.*cast.*instant', r'instant.*cost.*less'],
        'sorcery': [r'sorcery.*from.*graveyard', r'whenever.*cast.*sorcery', r'sorcery.*cost.*less'],
        'planeswalker': [r'planeswalkers you control get', r'for each planeswalker you control'],
        'land': [r'lands you control', r'for each land you control', r'landfall']
    }

    # Patterns that indicate NEGATIVE interaction (countering, destroying, etc.)
    negative_patterns = [
        r'\bnon[a-z]*creature',  # noncreature
        r'\bnon[a-z]*artifact',  # nonartifact
        r'counter target',
        r'destroy target creature',  # Removal spells
        r'destroy.*creature',  # Any creature destruction
        r'exile target creature',  # Exile removal
        r'exile.*creature',  # Any creature exile
        r'sacrifice target',
        r'sacrifice a creature',  # Using creatures as cost, not caring about them
        r'sacrifice.*creature.*you control',  # Sacrifice cost
        r'as an additional cost.*sacrifice',  # Sacrifice as cost
        r'return.*creature.*you control',  # Bounce cost
        r'return target creature',  # Bounce removal
        r'tap.*creature.*you control',  # Tap as cost
        r'target creature gets -',  # Debuff effects
        r'creatures.*opponent.*control'  # Targeting opponent's creatures
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    subcategory_map = {
        'artifact': 'artifact_matters',
        'enchantment': 'enchantment_matters',
        'creature': 'creature_matters',
        'instant': 'instant_sorcery_matters',
        'sorcery': 'instant_sorcery_matters',
        'planeswalker': 'planeswalker_synergy',
        'land': 'land_matters'
    }

    for card_type, patterns in positive_care_patterns.items():
        # Check if card1 positively cares about card_type and card2 is that type
        card1_cares = any(search_cached(pattern, card1_text) for pattern in patterns)
        card1_is_negative = any(search_cached(pattern, card1_text) for pattern in negative_patterns)

        if card1_cares and not card1_is_negative and card_type in card2_type:
            return {
                'name': f'{card_type.title()} Synergy',
                'description': f"{card1['name']} cares about {card_type}s, {card2['name']} is a {card_type}",
                'value': 2.5,
                'category': 'type_synergy',
                'subcategory': subcategory_map[card_type]
            }

        # Check reverse
        card2_cares = any(search_cached(pattern, card2_text) for pattern in patterns)
        card2_is_negative = any(search_cached(pattern, card2_text) for pattern in negative_patterns)

        if card2_cares and not card2_is_negative and card_type in card1_type:
            return {
                'name': f'{card_type.title()} Synergy',
                'description': f"{card2['name']} cares about {card_type}s, {card1['name']} is a {card_type}",
                'value': 2.5,
                'category': 'type_synergy',
                'subcategory': subcategory_map[card_type]
            }

    return None


def detect_combo_potential(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect potential combo interactions
    This is a simplified version - real combo detection would be much more complex
    """
    combo_indicators = [
        'infinite', 'untap', 'copy', 'extra turn', 'extra combat',
        'whenever you cast', 'storm', 'cascade'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_has_combo_word = any(keyword in card1_text for keyword in combo_indicators)
    card2_has_combo_word = any(keyword in card2_text for keyword in combo_indicators)

    # Both cards have combo-potential keywords
    if card1_has_combo_word and card2_has_combo_word:
        # Check for specific infinite mana combos
        # Must have "untap target" or "untap another" (not self-untap)
        card1_untaps_others = search_cached(r'untap (target|another|all|up to)', card1_text)
        card2_untaps_others = search_cached(r'untap (target|another|all|up to)', card2_text)

        # Must produce mana from tapping
        card1_taps_for_mana = search_cached(r'\{t\}.*add.*mana', card1_text) or search_cached(r'\{t\}:.*add \{[wubrgc]\}', card1_text)
        card2_taps_for_mana = search_cached(r'\{t\}.*add.*mana', card2_text) or search_cached(r'\{t\}:.*add \{[wubrgc]\}', card2_text)

        if (card1_untaps_others and card2_taps_for_mana) or (card2_untaps_others and card1_taps_for_mana):
            return {
                'name': 'Potential Infinite Mana',
                'description': f"Potential infinite mana combo between {card1['name']} and {card2['name']}",
                'value': 5.0,
                'category': 'combo',
                'subcategory': 'infinite_mana'
            }

        # General combo potential (but be more conservative)
        return {
            'name': 'Combo Potential',
            'description': f"Potential combo interaction detected",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    return None


def detect_protection_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect protection and hexproof synergies"""
    protection_keywords = ['hexproof', 'shroud', 'indestructible', 'protection', 'ward']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if one card grants protection
    grants_protection = ['creatures you control have', 'target creature gains']

    card1_grants = any(kw in card1_text for kw in grants_protection) and \
                   any(kw in card1_text for kw in protection_keywords)
    card2_is_creature = 'creature' in card2.get('type_line', '').lower()

    if card1_grants and card2_is_creature:
        return {
            'name': 'Protection Synergy',
            'description': f"{card1['name']} can protect {card2['name']}",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'protection'
        }

    # Check reverse
    card2_grants = any(kw in card2_text for kw in grants_protection) and \
                   any(kw in card2_text for kw in protection_keywords)
    card1_is_creature = 'creature' in card1.get('type_line', '').lower()

    if card2_grants and card1_is_creature:
        return {
            'name': 'Protection Synergy',
            'description': f"{card2['name']} can protect {card1['name']}",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'protection'
        }

    return None


def detect_token_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect token generation and payoff synergies with specific token type matching"""

    # Extract token generation info for both cards
    card1_token_gen = extract_token_creation(card1)
    card2_token_gen = extract_token_creation(card2)

    # Extract token payoff preferences for both cards
    card1_payoff = extract_token_type_preferences(card1)
    card2_payoff = extract_token_type_preferences(card2)

    # Exclude opponent token generation
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    opponent_token_patterns = [
        r'opponent.*create.*token',
        r'defending player creates.*token',
        r'that player creates.*token',
        r'create.*token.*under.*opponent.*control',
        r'its controller creates.*token',
        r'its controller creates.*treasure',
        r'controller creates.*token',
        r'controller creates.*treasure'
    ]

    card1_opponent_tokens = any(search_cached(kw, card1_text) for kw in opponent_token_patterns)
    card2_opponent_tokens = any(search_cached(kw, card2_text) for kw in opponent_token_patterns)

    # Helper function to get token types from a card's generation
    def get_generated_token_types(token_gen_result):
        """Extract list of token types generated"""
        types = set()
        for token_info in token_gen_result.get('token_types', []):
            token_types_list = token_info.get('types', [])
            for t in token_types_list:
                types.add(t.lower())
            # Check if it's a creature token (has power/toughness)
            if token_info.get('power') is not None:
                types.add('creature')
        return types

    # Helper function to check if token types match payoff preferences
    def types_match(generated_types, payoff_prefs):
        """Check if generated token types match what the payoff card cares about"""
        if not payoff_prefs['cares_about_tokens']:
            return False

        # If payoff cares about any tokens, it matches
        if payoff_prefs['cares_about_any_tokens']:
            return True

        # Check if specific types match
        specific_types = set(payoff_prefs['specific_token_types'])
        return bool(generated_types & specific_types)  # Any overlap is a match

    # Check card1 generates, card2 has payoff
    if card1_token_gen['creates_tokens'] and not card1_opponent_tokens and card2_payoff['cares_about_tokens']:
        generated_types = get_generated_token_types(card1_token_gen)

        if types_match(generated_types, card2_payoff):
            # Determine description based on specificity
            if card2_payoff['cares_about_any_tokens']:
                token_desc = "tokens"
            else:
                token_desc = f"{', '.join(card2_payoff['specific_token_types'])} tokens"

            return {
                'name': 'Token Synergy',
                'description': f"{card1['name']} creates {token_desc} that {card2['name']} benefits from",
                'value': 2.5,
                'category': 'role_interaction',
                'subcategory': 'token_generation'
            }

    # Check card2 generates, card1 has payoff
    if card2_token_gen['creates_tokens'] and not card2_opponent_tokens and card1_payoff['cares_about_tokens']:
        generated_types = get_generated_token_types(card2_token_gen)

        if types_match(generated_types, card1_payoff):
            # Determine description based on specificity
            if card1_payoff['cares_about_any_tokens']:
                token_desc = "tokens"
            else:
                token_desc = f"{', '.join(card1_payoff['specific_token_types'])} tokens"

            return {
                'name': 'Token Synergy',
                'description': f"{card2['name']} creates {token_desc} that {card1['name']} benefits from",
                'value': 2.5,
                'category': 'role_interaction',
                'subcategory': 'token_generation'
            }

    return None


def extract_graveyard_recursion_preferences(card: Dict) -> Dict:
    """
    Extract what specific card types a card recurrs from the graveyard.

    This distinguishes between:
    - Cards that return specific card types (instant/sorcery, creatures, artifacts, etc.)
    - Cards that return any card type

    Returns:
        {
            'has_recursion': bool,
            'specific_card_types': List[str],  # ['instant', 'sorcery', 'creature', 'artifact', etc.]
            'returns_any_card': bool,  # True if returns any card type
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_recursion': False,
        'specific_card_types': [],
        'returns_any_card': False,
        'examples': []
    }

    if not text:
        return result

    # Specific card type recursion patterns
    # Use word boundaries and "card" keyword to avoid false matches
    specific_patterns = {
        'instant': [
            r'return.*instant.*card.*from.*graveyard',
            r'instant.*card.*from.*graveyard.*to.*hand',
        ],
        'sorcery': [
            r'return.*sorcery.*card.*from.*graveyard',
            r'sorcery.*card.*from.*graveyard.*to.*hand',
        ],
        'creature': [
            r'return.*creature\s+card.*from.*graveyard',
            r'creature\s+card.*from.*graveyard.*to.*(?:hand|battlefield)',
            r'return\s+target\s+creature\s+card\s+from.*graveyard',
            r'reanimate',
        ],
        'artifact': [
            r'return.*artifact.*card.*from.*graveyard',
            r'artifact.*card.*from.*graveyard.*to.*(?:hand|battlefield)',
            r'return target artifact.*from.*graveyard',
        ],
        'enchantment': [
            r'return.*enchantment.*card.*from.*graveyard',
            r'enchantment.*card.*from.*graveyard.*to.*(?:hand|battlefield)',
            r'return target enchantment.*from.*graveyard',
        ],
        'planeswalker': [
            r'return.*planeswalker.*card.*from.*graveyard',
            r'planeswalker.*card.*from.*graveyard.*to.*(?:hand|battlefield)',
            r'return target planeswalker.*from.*graveyard',
        ],
        'land': [
            r'return.*land.*card.*from.*graveyard',
            r'land.*card.*from.*graveyard.*to.*(?:hand|battlefield)',
            r'return target land.*from.*graveyard',
        ],
    }

    # Check for specific card types
    for card_type, patterns in specific_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                result['has_recursion'] = True
                if card_type not in result['specific_card_types']:
                    result['specific_card_types'].append(card_type)
                if match.group(0) not in result['examples']:
                    result['examples'].append(match.group(0))

    # Check for "instant or sorcery" together
    if re.search(r'instant.*(?:and|or).*sorcery.*from.*graveyard', text):
        if 'instant' not in result['specific_card_types']:
            result['specific_card_types'].append('instant')
        if 'sorcery' not in result['specific_card_types']:
            result['specific_card_types'].append('sorcery')
        result['has_recursion'] = True

    # Check for general recursion (returns any card, permanent, etc.)
    general_patterns = [
        r'return.*(?:target|a|up to).*card.*from.*graveyard',  # "return target card" (any card)
        r'return.*permanent.*from.*graveyard',  # Permanents (broad)
    ]

    for pattern in general_patterns:
        match = re.search(pattern, text)
        if match:
            match_text = match.group(0)
            # Check if this mentions specific types - if so, it's NOT general
            has_specific_type = any(
                card_type in match_text
                for card_type in ['instant', 'sorcery', 'creature', 'artifact', 'enchantment', 'planeswalker', 'land']
            )

            if not has_specific_type:
                result['has_recursion'] = True
                result['returns_any_card'] = True
                if match.group(0) not in result['examples']:
                    result['examples'].append(match.group(0))

    return result


def detect_graveyard_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect graveyard and recursion synergies with specific card type matching.

    NOTE: Flashback, Jump-start, and Retrace are SELF-RECURSION mechanics.
    They don't benefit from OTHER cards filling the graveyard - only their own card.
    These should NOT trigger graveyard synergies.

    True graveyard payoffs care about OTHER cards in the graveyard:
    - Reanimation (return OTHER creatures from graveyard)
    - Delve/Escape (exile OTHER cards from graveyard)
    - Threshold/Delirium (count cards in graveyard)
    - Recursion that targets (return target card from graveyard)

    Now also checks if specific recursion matches card types being milled.
    """
    # Extract recursion preferences for both cards
    card1_recursion = extract_graveyard_recursion_preferences(card1)
    card2_recursion = extract_graveyard_recursion_preferences(card2)

    # Graveyard fill patterns
    graveyard_fill = ['mill', 'put.*into.*graveyard', 'discard']

    # Non-recursion graveyard payoffs (delve, threshold, etc.)
    non_recursion_payoff = [
        r'delve',  # Delve
        r'escape',  # Escape
        r'threshold',  # Threshold
        r'delirium',  # Delirium
        r'undergrowth',  # Undergrowth
        r'cards?\s+in\s+(?:your|a|all)\s+graveyard',  # Counts graveyard
        r'for\s+each.*in.*graveyard',  # Counts graveyard
        r'exile.*from.*graveyard',  # Delve-like effects
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Helper to get card types from type_line
    def get_card_types(type_line):
        """Extract card types from type_line"""
        types = set()
        if 'instant' in type_line:
            types.add('instant')
        if 'sorcery' in type_line:
            types.add('sorcery')
        if 'creature' in type_line:
            types.add('creature')
        if 'artifact' in type_line:
            types.add('artifact')
        if 'enchantment' in type_line:
            types.add('enchantment')
        if 'planeswalker' in type_line:
            types.add('planeswalker')
        if 'land' in type_line:
            types.add('land')
        return types

    # Check card1 fills graveyard, card2 has recursion
    card1_fills = any(search_cached(kw, card1_text) for kw in graveyard_fill)

    if card1_fills and card2_recursion['has_recursion']:
        # If card2 has specific recursion, check if card1's type matches
        if card2_recursion['specific_card_types'] and not card2_recursion['returns_any_card']:
            card1_types = get_card_types(card1_type)
            specific_types = set(card2_recursion['specific_card_types'])

            # Only synergize if the filler card matches the recursion type
            # For example, instant/sorcery filler with instant/sorcery recursion
            if card1_types & specific_types:
                card_type_desc = ', '.join(card2_recursion['specific_card_types'])
                return {
                    'name': 'Graveyard Synergy',
                    'description': f"{card1['name']} fills graveyard with {card_type_desc}s for {card2['name']}",
                    'value': 2.0,  # Higher value for matched types
                    'category': 'role_interaction',
                    'subcategory': 'recursion'
                }
        # General recursion or matches
        elif card2_recursion['returns_any_card']:
            return {
                'name': 'Graveyard Synergy',
                'description': f"{card1['name']} fills graveyard for {card2['name']} to utilize",
                'value': 1.5,
                'category': 'role_interaction',
                'subcategory': 'recursion'
            }

    # Check card1 fills, card2 has non-recursion payoff (delve, threshold, etc.)
    card2_other_payoff = any(search_cached(kw, card2_text) for kw in non_recursion_payoff)
    if card1_fills and card2_other_payoff:
        return {
            'name': 'Graveyard Synergy',
            'description': f"{card1['name']} fills graveyard for {card2['name']} to utilize",
            'value': 1.5,
            'category': 'role_interaction',
            'subcategory': 'recursion'
        }

    # Check reverse: card2 fills, card1 has recursion
    card2_fills = any(search_cached(kw, card2_text) for kw in graveyard_fill)

    if card2_fills and card1_recursion['has_recursion']:
        # If card1 has specific recursion, check if card2's type matches
        if card1_recursion['specific_card_types'] and not card1_recursion['returns_any_card']:
            card2_types = get_card_types(card2_type)
            specific_types = set(card1_recursion['specific_card_types'])

            if card2_types & specific_types:
                card_type_desc = ', '.join(card1_recursion['specific_card_types'])
                return {
                    'name': 'Graveyard Synergy',
                    'description': f"{card2['name']} fills graveyard with {card_type_desc}s for {card1['name']}",
                    'value': 2.0,
                    'category': 'role_interaction',
                    'subcategory': 'recursion'
                }
        elif card1_recursion['returns_any_card']:
            return {
                'name': 'Graveyard Synergy',
                'description': f"{card2['name']} fills graveyard for {card1['name']} to utilize",
                'value': 1.5,
                'category': 'role_interaction',
                'subcategory': 'recursion'
            }

    # Check reverse: card2 fills, card1 has non-recursion payoff
    card1_other_payoff = any(search_cached(kw, card1_text) for kw in non_recursion_payoff)
    if card2_fills and card1_other_payoff:
        return {
            'name': 'Graveyard Synergy',
            'description': f"{card2['name']} fills graveyard for {card1['name']} to utilize",
            'value': 1.5,
            'category': 'role_interaction',
            'subcategory': 'recursion'
        }

    return None


def detect_life_as_resource(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Life as Resource synergy (Rule 26)
    Cards that pay life work well with life gain effects
    """
    # Life payment patterns (excluding opponent targeting)
    life_payment_patterns = [
        r'pay.*life',
        r'lose.*life',
        r'\{[0-9]+\s*life\}',  # Phyrexian mana
        r'as.*additional.*cost.*pay.*life'
    ]

    # Life gain patterns
    life_gain_patterns = [
        r'you gain.*life',
        r'gain.*life',
        r'lifelink',
        r'whenever.*gain.*life'
    ]

    # Exclude opponent-targeting
    opponent_patterns = [
        r'opponent.*pay.*life',
        r'each opponent.*lose.*life',
        r'target player.*lose.*life'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check card1 pays life, card2 gains life
    card1_pays_life = any(search_cached(pattern, card1_text) for pattern in life_payment_patterns)
    card1_targets_opponent = any(search_cached(pattern, card1_text) for pattern in opponent_patterns)
    card2_gains_life = any(search_cached(pattern, card2_text) for pattern in life_gain_patterns) or 'lifelink' in card2_keywords

    if card1_pays_life and not card1_targets_opponent and card2_gains_life:
        return {
            'name': 'Life as Resource',
            'description': f"{card1['name']} pays life as a cost, {card2['name']} gains life to offset",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    # Check reverse
    card2_pays_life = any(search_cached(pattern, card2_text) for pattern in life_payment_patterns)
    card2_targets_opponent = any(search_cached(pattern, card2_text) for pattern in opponent_patterns)
    card1_gains_life = any(search_cached(pattern, card1_text) for pattern in life_gain_patterns) or 'lifelink' in card1_keywords

    if card2_pays_life and not card2_targets_opponent and card1_gains_life:
        return {
            'name': 'Life as Resource',
            'description': f"{card2['name']} pays life as a cost, {card1['name']} gains life to offset",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    return None


def detect_deathtouch_pingers(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Deathtouch Pingers synergy (Rule 27)
    Deathtouch + damage dealing = efficient creature removal
    """
    deathtouch_patterns = [r'\bdeathtouch\b']

    # Damage dealing patterns (not combat damage)
    pinger_patterns = [
        r'deals.*damage to.*creature',
        r'deals.*damage to any target',
        r'deals.*damage to.*player or planeswalker',
        r'deals 1 damage',
        r'ping',
        r'tap.*deals.*damage'
    ]

    # Deathtouch granting patterns
    grants_deathtouch = [
        r'creatures.*you control.*have deathtouch',
        r'equipped creature.*deathtouch',
        r'enchanted creature.*deathtouch',
        r'target creature.*deathtouch'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 has/grants deathtouch and card2 deals damage
    card1_has_deathtouch = 'deathtouch' in card1_keywords or any(search_cached(pattern, card1_text) for pattern in deathtouch_patterns)
    card1_grants_deathtouch = any(search_cached(pattern, card1_text) for pattern in grants_deathtouch)
    card2_deals_damage = any(search_cached(pattern, card2_text) for pattern in pinger_patterns)

    if (card1_has_deathtouch or card1_grants_deathtouch) and card2_deals_damage:
        return {
            'name': 'Deathtouch Pinger',
            'description': f"{card1['name']} provides deathtouch, {card2['name']} deals damage for removal",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'removal'
        }

    # Check reverse
    card2_has_deathtouch = 'deathtouch' in card2_keywords or any(search_cached(pattern, card2_text) for pattern in deathtouch_patterns)
    card2_grants_deathtouch = any(search_cached(pattern, card2_text) for pattern in grants_deathtouch)
    card1_deals_damage = any(search_cached(pattern, card1_text) for pattern in pinger_patterns)

    if (card2_has_deathtouch or card2_grants_deathtouch) and card1_deals_damage:
        return {
            'name': 'Deathtouch Pinger',
            'description': f"{card2['name']} provides deathtouch, {card1['name']} deals damage for removal",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'removal'
        }

    return None


def detect_indestructible_board_wipe(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Indestructible + Board Wipe synergy (Rule 28)
    Indestructible creatures survive destroy-based board wipes
    """
    # Indestructible patterns
    indestructible_patterns = [
        r'\bindestructible\b',
        r'creatures.*you control.*indestructible',
        r'permanents.*you control.*indestructible'
    ]

    # Board wipe patterns (destroy-based only)
    destroy_wipe_patterns = [
        r'destroy all creatures',
        r'destroy all.*creatures',
        r'destroy each creature',
        r'\-[0-9]+/\-[0-9]+.*to all creatures',  # -X/-X effects
        r'wrath'
    ]

    # One-sided wipe patterns (higher value)
    one_sided_patterns = [
        r'destroy all.*except',
        r'destroy all creatures you don\'t control'
    ]

    # Exile-based wipes (indestructible doesn't help)
    exile_wipe_patterns = [
        r'exile all creatures',
        r'exile each creature'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 has/grants indestructible and card2 is a destroy-wipe
    card1_has_indestructible = 'indestructible' in card1_keywords or any(search_cached(pattern, card1_text) for pattern in indestructible_patterns)
    card2_is_destroy_wipe = any(search_cached(pattern, card2_text) for pattern in destroy_wipe_patterns)
    card2_is_exile_wipe = any(search_cached(pattern, card2_text) for pattern in exile_wipe_patterns)
    card2_is_one_sided = any(search_cached(pattern, card2_text) for pattern in one_sided_patterns)

    if card1_has_indestructible and card2_is_destroy_wipe and not card2_is_exile_wipe:
        value = 3.5 if card2_is_one_sided else 3.0
        return {
            'name': 'Indestructible + Wipe',
            'description': f"{card1['name']} survives {card2['name']}'s board wipe",
            'value': value,
            'category': 'role_interaction',
            'subcategory': 'protection'
        }

    # Check reverse
    card2_has_indestructible = 'indestructible' in card2_keywords or any(search_cached(pattern, card2_text) for pattern in indestructible_patterns)
    card1_is_destroy_wipe = any(search_cached(pattern, card1_text) for pattern in destroy_wipe_patterns)
    card1_is_exile_wipe = any(search_cached(pattern, card1_text) for pattern in exile_wipe_patterns)
    card1_is_one_sided = any(search_cached(pattern, card1_text) for pattern in one_sided_patterns)

    if card2_has_indestructible and card1_is_destroy_wipe and not card1_is_exile_wipe:
        value = 3.5 if card1_is_one_sided else 3.0
        return {
            'name': 'Indestructible + Wipe',
            'description': f"{card2['name']} survives {card1['name']}'s board wipe",
            'value': value,
            'category': 'role_interaction',
            'subcategory': 'protection'
        }

    return None


def detect_extra_combat_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Extra Combat Steps synergy (Rule 29)
    Extra combat effects benefit creatures with combat abilities
    """
    # Extra combat patterns
    extra_combat_patterns = [
        r'additional combat',
        r'extra combat',
        r'additional combat phase',
        r'after this phase.*additional combat',
        r'untap all creatures.*additional combat'
    ]

    # Combat-relevant keywords and abilities
    combat_keywords = ['vigilance', 'haste', 'double strike', 'first strike', 'trample']
    combat_ability_patterns = [
        r'whenever.*attacks',
        r'when.*attacks',
        r'whenever.*deals combat damage',
        r'combat damage to a player'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 gives extra combat and card2 benefits from it
    card1_extra_combat = any(search_cached(pattern, card1_text) for pattern in extra_combat_patterns)
    card2_combat_ability = any(kw in card2_keywords for kw in combat_keywords) or \
                           any(search_cached(pattern, card2_text) for pattern in combat_ability_patterns)

    if card1_extra_combat and card2_combat_ability:
        return {
            'name': 'Extra Combat',
            'description': f"{card1['name']} grants extra combats, {card2['name']} benefits from attacking",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_extra_combat = any(search_cached(pattern, card2_text) for pattern in extra_combat_patterns)
    card1_combat_ability = any(kw in card1_keywords for kw in combat_keywords) or \
                           any(search_cached(pattern, card1_text) for pattern in combat_ability_patterns)

    if card2_extra_combat and card1_combat_ability:
        return {
            'name': 'Extra Combat',
            'description': f"{card2['name']} grants extra combats, {card1['name']} benefits from attacking",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Special-case: Extra combat + postcombat mana (Neheb-like)
    neheb_patterns = [
        r'postcombat main phase, add \{r\}',
        r'add \{r\} for each 1 life your opponents have lost this turn',
        r'for each 1 life your opponents have lost this turn, add \{r\}'
    ]
    card1_neheb = any(search_cached(p, card1_text) for p in neheb_patterns)
    card2_neheb = any(search_cached(p, card2_text) for p in neheb_patterns)
    if (card1_extra_combat and card2_neheb) or (card2_extra_combat and card1_neheb):
        return {
            'name': 'Extra Combat Mana Loop',
            'description': 'Extra combats plus postcombat mana generation enable explosive turns',
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    return None


def detect_wheel_and_deal(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Wheel and Deal synergy (Rule 30)
    Wheel effects (mass draw/discard) with punishment for drawing/discarding
    """
    # Wheel effect patterns
    wheel_patterns = [
        r'each player draws.*cards',
        r'each player discards.*hand.*draws',
        r'discard.*hand.*draw.*cards',
        r'wheel',
        r'windfall'
    ]

    # Punishment for drawing
    draw_punisher_patterns = [
        r'whenever.*opponent draws',
        r'whenever.*player draws.*except',
        r'for each card.*opponent.*drew',
        r'deals.*damage.*equal.*cards drawn'
    ]

    # Punishment for discarding
    discard_punisher_patterns = [
        r'whenever.*opponent discards',
        r'whenever.*player discards',
        r'for each card.*discarded'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 is wheel and card2 is punisher
    card1_is_wheel = any(search_cached(pattern, card1_text) for pattern in wheel_patterns)
    card2_punishes_draw = any(search_cached(pattern, card2_text) for pattern in draw_punisher_patterns)
    card2_punishes_discard = any(search_cached(pattern, card2_text) for pattern in discard_punisher_patterns)

    if card1_is_wheel and (card2_punishes_draw or card2_punishes_discard):
        return {
            'name': 'Wheel and Deal',
            'description': f"{card1['name']} forces mass draw/discard, {card2['name']} punishes opponents",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_is_wheel = any(search_cached(pattern, card2_text) for pattern in wheel_patterns)
    card1_punishes_draw = any(search_cached(pattern, card1_text) for pattern in draw_punisher_patterns)
    card1_punishes_discard = any(search_cached(pattern, card1_text) for pattern in discard_punisher_patterns)

    if card2_is_wheel and (card1_punishes_draw or card1_punishes_discard):
        return {
            'name': 'Wheel and Deal',
            'description': f"{card2['name']} forces mass draw/discard, {card1['name']} punishes opponents",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    return None


def detect_tap_untap_engines(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Tap/Untap Engines synergy (Rule 31)
    Untap effects + repeatable tap abilities (excluding basic mana abilities)
    """
    # Untap patterns
    untap_patterns = [
        r'untap target',
        r'untap.*permanent',
        r'untap.*creature',
        r'untap.*artifact',
        r'untap all',
        r'becomes untapped'
    ]

    # Tap ability patterns (non-mana)
    tap_ability_patterns = [
        r'\{t\}:.*draw',
        r'\{t\}:.*deal.*damage',
        r'\{t\}:.*create',
        r'\{t\}:.*put',
        r'\{t\}:.*return',
        r'\{t\}:.*search',
        r'\{t\}:.*sacrifice',
        r'\{t\}:.*copy',
        r'tap.*creature.*you control:',
        r'tap.*artifact.*you control:'
    ]

    # Exclude basic mana abilities
    basic_mana_patterns = [
        r'\{t\}: add \{[wubrgc]\}',
        r'\{t\}: add one mana',
        r'\{t\}.*add.*\{[wubrgc]\}.*to your mana pool'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_name = (card1.get('name') or '').lower()
    card2_name = (card2.get('name') or '').lower()

    # Check if card1 untaps and card2 has tap abilities
    card1_untaps = any(search_cached(pattern, card1_text) for pattern in untap_patterns)
    card2_has_tap_ability = any(search_cached(pattern, card2_text) for pattern in tap_ability_patterns)
    card2_is_basic_mana = any(search_cached(pattern, card2_text) for pattern in basic_mana_patterns)

    if card1_untaps and card2_has_tap_ability and not card2_is_basic_mana:
        return {
            'name': 'Tap/Untap Engine',
            'description': f"{card1['name']} untaps {card2['name']} for repeated value",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_untaps = any(search_cached(pattern, card2_text) for pattern in untap_patterns)
    card1_has_tap_ability = any(search_cached(pattern, card1_text) for pattern in tap_ability_patterns)
    card1_is_basic_mana = any(search_cached(pattern, card1_text) for pattern in basic_mana_patterns)

    if card2_untaps and card1_has_tap_ability and not card1_is_basic_mana:
        return {
            'name': 'Tap/Untap Engine',
            'description': f"{card2['name']} untaps {card1['name']} for repeated value",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Special-case: Isochron Scepter + Dramatic Reversal style
    scepter_like = ('isochron scepter' in card1_name) or ('isochron scepter' in card2_name) or ('imprint' in card1_text) or ('imprint' in card2_text)
    reversal_like = ('untap all nonland permanents' in card1_text) or ('untap all nonland permanents' in card2_text)
    if scepter_like and reversal_like:
        return {
            'name': 'Isochron Reversal Loop',
            'description': 'Imprinted untap effect enables repeatable untaps (Scepter + Reversal engine)',
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'tap_untap_loop'
        }

    return None


def detect_cheat_big_spells(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Cheat Big Spells synergy (Rule 32)
    Cost reduction/cheating effects + expensive spells
    """
    # Cheat/reduction patterns
    cheat_patterns = [
        r'without paying.*mana cost',
        r'you may cast.*without paying',
        r'cast.*for free',
        r'\bcascade\b',
        r'costs.*less to cast',
        r'cost.*less',
        r'put.*creature.*onto the battlefield',  # FIXED: Specify creatures, not lands
        r'put.*artifact.*onto the battlefield',  # FIXED: Specify artifacts
        r'put.*enchantment.*onto the battlefield',  # FIXED: Specify enchantments
        r'affinity',
        r'convoke',
        r'delve'
    ]

    # CRITICAL FIX: Exclude land ramp patterns (these are NOT cheat effects)
    ramp_patterns = [
        r'search.*library.*land',
        r'put.*land.*onto the battlefield',
        r'basic land.*onto the battlefield',
        r'land card.*onto the battlefield'
    ]

    # High CMC threshold
    HIGH_CMC = 6

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 cheats and card2 is expensive
    # CRITICAL FIX: Exclude ramp spells from cheat detection
    card1_cheats = any(search_cached(pattern, card1_text) for pattern in cheat_patterns) and \
                   not any(search_cached(pattern, card1_text) for pattern in ramp_patterns)

    if card1_cheats and card2_cmc >= HIGH_CMC:
        cmc_diff = card2_cmc - 3  # Assume average cheat cost is 3
        value = 2.0 + (cmc_diff * 0.3)  # Higher CMC = higher value
        return {
            'name': 'Cheat Big Spells',
            'description': f"{card1['name']} cheats {card2['name']} (CMC {card2_cmc}) into play",
            'value': min(value, 4.0),  # Cap at 4.0
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    # Check reverse
    # CRITICAL FIX: Exclude ramp spells from cheat detection
    card2_cheats = any(search_cached(pattern, card2_text) for pattern in cheat_patterns) and \
                   not any(search_cached(pattern, card2_text) for pattern in ramp_patterns)

    if card2_cheats and card1_cmc >= HIGH_CMC:
        cmc_diff = card1_cmc - 3
        value = 2.0 + (cmc_diff * 0.3)
        return {
            'name': 'Cheat Big Spells',
            'description': f"{card2['name']} cheats {card1['name']} (CMC {card1_cmc}) into play",
            'value': min(value, 4.0),
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    return None

def detect_scry_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    detect Scry Synergy (Rule 34)
    Cards that scry + cards that benefit from scrying
    """
    # Scry patterns
    scry_patterns = [
        r'\bscry\b',
    ]

    # Cards that benefit from scrying
    scry_benefit_patterns = [
        r'whenever you scry',
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 scrys and card2 benefits from scrying
    card1_scrys = 'scry' in card1_keywords or any(search_cached(pattern, card1_text) for pattern in scry_patterns)
    card2_benefits_scry = any(search_cached(pattern, card2_text) for pattern in scry_benefit_patterns)

    if card1_scrys and card2_benefits_scry:
        return {
            'name': 'Scry Synergy',
            'description': f"{card1['name']} scrys to set up {card2['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'scry_synergy'
        }

    # Check reverse
    card2_scrys = 'scry' in card2_keywords or any(search_cached(pattern, card2_text) for pattern in scry_patterns)
    card1_benefits_scry = any(search_cached(pattern, card1_text) for pattern in scry_benefit_patterns)

    if card2_scrys and card1_benefits_scry:
        return {
            'name': 'Scry Synergy',
            'description': f"{card2['name']} scrys to set up {card1['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'scry_synergy'
        }

def detect_surveil_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    detect Surveil Synergy (Rule 34)
    Cards that Surveil + cards that benefit from Surveiling
    """
    # Surveil patterns
    surveil_patterns = [
        r'\bsurveil\b',
    ]

    # Cards that benefit from Surveiling
    surveil_benefit_patterns = [
        r'whenever you surveil',
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 surveils and card2 benefits from Surveiling
    card1_surveys = 'surveil' in card1_keywords or any(search_cached(pattern, card1_text) for pattern in surveil_patterns)
    card2_benefits_surveil = any(search_cached(pattern, card2_text) for pattern in surveil_benefit_patterns)

    if card1_surveys and card2_benefits_surveil:
        return {
            'name': 'Surveil Synergy',
            'description': f"{card1['name']} surveils to set up {card2['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'surveil_synergy'
        }

    # Check reverse
    card2_surveys = 'surveil' in card2_keywords or any(search_cached(pattern, card2_text) for pattern in surveil_patterns)
    card1_benefits_surveil = any(search_cached(pattern, card1_text) for pattern in surveil_benefit_patterns)

    if card2_surveys and card1_benefits_surveil:
        return {
            'name': 'Surveil Synergy',
            'description': f"{card2['name']} surveils to set up {card1['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'surveil_synergy'
        }


def detect_topdeck_manipulation(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Topdeck Manipulation synergy (Rule 33)
    Cards that manipulate top of library + cards that care about top of library
    """
    # Top manipulation patterns
    top_manipulation_patterns = [
        r'\bscry\b',
        r'\bsurveil\b',
        r'look at the top',
        r'reveal.*top.*library',
        r'put.*on top of.*library',
        r'search.*library.*top'
    ]

    # Exclude bounce effects (put cards on top as removal)
    bounce_patterns = [
        r'return.*to.*hand',
        r'return.*owner\'s hand',
        r'bounce'
    ]

    # Cards that care about top of library
    top_matters_patterns = [
        r'top card of.*library',
        r'whenever you draw',
        r'play.*from the top',
        r'cast.*from the top',
        r'reveal the top card',
        r'miracle'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 manipulates top and card2 cares about top
    card1_manipulates = 'top' in card2_keywords or any(search_cached(pattern, card1_text) for pattern in top_manipulation_patterns)
    card1_is_bounce = any(search_cached(pattern, card1_text) for pattern in bounce_patterns)
    card2_cares_top = any(search_cached(pattern, card2_text) for pattern in top_matters_patterns) or 'miracle' in card2_keywords

    if card1_manipulates and not card1_is_bounce and card2_cares_top:
        return {
            'name': 'Topdeck Manipulation',
            'description': f"{card1['name']} sets up top of library for {card2['name']}",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'top_deck_synergy'
        }

    # Check reverse
    card2_manipulates = 'top' in card2_keywords or any(search_cached(pattern, card2_text) for pattern in top_manipulation_patterns)
    card2_is_bounce = any(search_cached(pattern, card2_text) for pattern in bounce_patterns)
    card1_cares_top = any(search_cached(pattern, card1_text) for pattern in top_matters_patterns) or 'miracle' in card1_keywords

    if card2_manipulates and not card2_is_bounce and card1_cares_top:
        return {
            'name': 'Topdeck Manipulation',
            'description': f"{card2['name']} sets up top of library for {card1['name']}",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'top_deck_synergy'   
            
        }

    return None


def detect_threaten_and_sac(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Threaten + Sacrifice/Blink synergy (Rule 4)
    Steal opponent's creatures temporarily, then sacrifice or blink them
    """
    # Threaten effect patterns
    threaten_patterns = [
        r'gain control of target creature.*until end of turn',
        r'gain control.*until end of turn.*it gains haste',
        r'untap target creature.*gain control.*until end of turn'
    ]

    # Blink patterns (to permanently steal)
    blink_patterns = [
        r'exile.*return.*to the battlefield under your control',
        r'exile target creature you control.*return it'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 threatens and card2 can sac or blink
    card1_threatens = any(search_cached(pattern, card1_text) for pattern in threaten_patterns)
    card2_is_sac_outlet = 'sacrifice' in card2_text and ('a creature' in card2_text or 'another creature' in card2_text)
    card2_blinks = any(search_cached(pattern, card2_text) for pattern in blink_patterns)

    if card1_threatens and (card2_is_sac_outlet or card2_blinks):
        return {
            'name': 'Threaten & Sacrifice',
            'description': f"{card1['name']} steals creatures, {card2['name']} sacrifices/blinks them permanently",
            'value': 4.0,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    # Check reverse
    card2_threatens = any(search_cached(pattern, card2_text) for pattern in threaten_patterns)
    card1_is_sac_outlet = 'sacrifice' in card1_text and ('a creature' in card1_text or 'another creature' in card1_text)
    card1_blinks = any(search_cached(pattern, card1_text) for pattern in blink_patterns)

    if card2_threatens and (card1_is_sac_outlet or card1_blinks):
        return {
            'name': 'Threaten & Sacrifice',
            'description': f"{card2['name']} steals creatures, {card1['name']} sacrifices/blinks them permanently",
            'value': 4.0,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    return None


def detect_token_anthems(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Token Swarm + Anthems/Overruns synergy (Rule 8)
    Token generators + global creature buffs
    """
    # Token generation patterns
    token_patterns = [
        r'create.*token',
        r'create.*\d+/\d+.*token',
        r'put.*token.*onto the battlefield'
    ]

    # CRITICAL FIX: Patterns that indicate tokens go to OPPONENT (exclude these)
    opponent_token_patterns = [
        r'opponent.*creates?.*token',
        r'target opponent.*creates?',
        r'its controller creates?.*token',
        r'defending player creates?.*token',
        r'each opponent creates?.*token'
    ]

    # Global buff patterns (positive only - exclude negative effects)
    buff_patterns = [
        r'creatures you control get \+\d+/\+\d+',
        r'creature tokens you control get \+\d+/\+\d+',
        r'creatures you control have',
        r'overrun',
        r'creatures you control gain'
    ]

    # Negative buff patterns to exclude
    negative_patterns = [
        r'get -\d+/-\d+',
        r'creatures.*opponent.*control'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 makes tokens and card2 buffs
    # CRITICAL FIX: Exclude cards that give tokens to opponents
    card1_makes_tokens = any(search_cached(pattern, card1_text) for pattern in token_patterns) and \
                         not any(search_cached(pattern, card1_text) for pattern in opponent_token_patterns)
    card2_buffs = any(search_cached(pattern, card2_text) for pattern in buff_patterns)
    card2_is_negative = any(search_cached(pattern, card2_text) for pattern in negative_patterns)

    if card1_makes_tokens and card2_buffs and not card2_is_negative:
        return {
            'name': 'Token Anthem',
            'description': f"{card1['name']} creates tokens, {card2['name']} pumps them for lethal",
            'value': 5.0,
            'category': 'benefits',
            'subcategory': 'anthem_effect'
        }

    # Check reverse
    # CRITICAL FIX: Exclude cards that give tokens to opponents
    card2_makes_tokens = any(search_cached(pattern, card2_text) for pattern in token_patterns) and \
                         not any(search_cached(pattern, card2_text) for pattern in opponent_token_patterns)
    card1_buffs = any(search_cached(pattern, card1_text) for pattern in buff_patterns)
    card1_is_negative = any(search_cached(pattern, card1_text) for pattern in negative_patterns)

    if card2_makes_tokens and card1_buffs and not card1_is_negative:
        return {
            'name': 'Token Anthem',
            'description': f"{card2['name']} creates tokens, {card1['name']} pumps them for lethal",
            'value': 5.0,
            'category': 'benefits',
            'subcategory': 'anthem_effect'
        }

    return None


def detect_convoke_improvise(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Convoke/Improvise synergy (Rule 10)
    Use tokens/artifacts to reduce spell costs
    """
    # Token generation patterns
    token_patterns = [
        r'create.*token',
        r'create.*creature.*token'
    ]

    # Artifact token patterns
    artifact_token_patterns = [
        r'create.*treasure',
        r'create.*clue',
        r'create.*food',
        r'create.*artifact.*token'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 has convoke/improvise and card2 makes tokens
    card1_has_convoke = 'convoke' in card1_keywords or 'convoke' in card1_text
    card1_has_improvise = 'improvise' in card1_keywords or 'improvise' in card1_text
    card2_makes_creatures = any(search_cached(pattern, card2_text) for pattern in token_patterns)
    card2_makes_artifacts = any(search_cached(pattern, card2_text) for pattern in artifact_token_patterns)

    if card1_has_convoke and card2_makes_creatures:
        return {
            'name': 'Convoke Engine',
            'description': f"{card1['name']} uses convoke, {card2['name']} provides creatures to tap",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    if card1_has_improvise and card2_makes_artifacts:
        return {
            'name': 'Improvise Engine',
            'description': f"{card1['name']} uses improvise, {card2['name']} provides artifacts to tap",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    # Check reverse
    card2_has_convoke = 'convoke' in card2_keywords or 'convoke' in card2_text
    card2_has_improvise = 'improvise' in card2_keywords or 'improvise' in card2_text
    card1_makes_creatures = any(search_cached(pattern, card1_text) for pattern in token_patterns)
    card1_makes_artifacts = any(search_cached(pattern, card1_text) for pattern in artifact_token_patterns)

    if card2_has_convoke and card1_makes_creatures:
        return {
            'name': 'Convoke Engine',
            'description': f"{card2['name']} uses convoke, {card1['name']} provides creatures to tap",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    if card2_has_improvise and card1_makes_artifacts:
        return {
            'name': 'Improvise Engine',
            'description': f"{card2['name']} uses improvise, {card1['name']} provides artifacts to tap",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    return None


def detect_fling_effects(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Fling Effects synergy (Rule 12)
    High-power creatures + sacrifice for damage
    """
    # Fling effect patterns
    fling_patterns = [
        r'sacrifice a creature.*deals damage equal to its power',
        r'sacrifice.*creature.*damage equal to.*power',
        r'deals damage equal to its power to any target'
    ]

    # High power threshold
    HIGH_POWER = 5

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_power = card1.get('power', 0)
    card2_power = card2.get('power', 0)

    # Try to convert power to int if it's a string
    try:
        card1_power = int(card1_power) if card1_power else 0
    except (ValueError, TypeError):
        card1_power = 0

    try:
        card2_power = int(card2_power) if card2_power else 0
    except (ValueError, TypeError):
        card2_power = 0

    # Check if card1 is fling and card2 is high power
    card1_is_fling = any(search_cached(pattern, card1_text) for pattern in fling_patterns)

    # Ephemeral/high-power heuristic when power is unknown: look for haste+trample and end-step sacrifice
    card2_ephemeral_big = ('haste' in card2_text and 'trample' in card2_text and ('sacrifice' in card2_text and 'end step' in card2_text))

    if card1_is_fling and (card2_power >= HIGH_POWER or card2_ephemeral_big):
        return {
            'name': 'Fling Finisher',
            'description': f"{card1['name']} flings {card2['name']} for heavy damage",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_is_fling = any(search_cached(pattern, card2_text) for pattern in fling_patterns)

    card1_ephemeral_big = ('haste' in card1_text and 'trample' in card1_text and ('sacrifice' in card1_text and 'end step' in card1_text))

    if card2_is_fling and (card1_power >= HIGH_POWER or card1_ephemeral_big):
        return {
            'name': 'Fling Finisher',
            'description': f"{card2['name']} flings {card1['name']} for heavy damage",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    return None


def detect_double_strike_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Double Strike synergy (Rule 14)
    High-power creatures + double strike = doubled damage
    """
    # Double strike patterns
    double_strike_patterns = [
        r'has double strike',
        r'gains double strike',
        r'have double strike',
        r'with double strike'
    ]

    # Damage doubler patterns
    damage_doubler_patterns = [
        r'deals double that damage',
        r'double the damage',
        r'deals twice that much damage'
    ]

    # Minimum power threshold for synergy
    MIN_POWER = 3

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]
    card1_power = card1.get('power', 0)
    card2_power = card2.get('power', 0)

    # Try to convert power to int
    try:
        card1_power = int(card1_power) if card1_power else 0
    except (ValueError, TypeError):
        card1_power = 0

    try:
        card2_power = int(card2_power) if card2_power else 0
    except (ValueError, TypeError):
        card2_power = 0

    # Check if card1 grants double strike and card2 has good power
    card1_grants_double_strike = 'double strike' in card1_keywords or \
                                  any(search_cached(pattern, card1_text) for pattern in double_strike_patterns)
    card1_doubles_damage = any(search_cached(pattern, card1_text) for pattern in damage_doubler_patterns)

    if (card1_grants_double_strike or card1_doubles_damage) and card2_power >= MIN_POWER:
        multiplier = "doubles" if card1_grants_double_strike else "multiplies"
        return {
            'name': 'Double Strike',
            'description': f"{card1['name']} {multiplier} {card2['name']}'s {card2_power} power",
            'value': 4.0,
            'category': 'benefits',
            'subcategory': 'keyword_grant'
        }

    # Check reverse
    card2_grants_double_strike = 'double strike' in card2_keywords or \
                                  any(search_cached(pattern, card2_text) for pattern in double_strike_patterns)
    card2_doubles_damage = any(search_cached(pattern, card2_text) for pattern in damage_doubler_patterns)

    if (card2_grants_double_strike or card2_doubles_damage) and card1_power >= MIN_POWER:
        multiplier = "doubles" if card2_grants_double_strike else "multiplies"
        return {
            'name': 'Double Strike',
            'description': f"{card2['name']} {multiplier} {card1['name']}'s {card1_power} power",
            'value': 4.0,
            'category': 'benefits',
            'subcategory': 'keyword_grant'
        }

    return None


def detect_spellslinger_payoffs(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Spellslinger Payoffs synergy (Rule 20)
    "Whenever you cast" triggers + cheap instants/sorceries
    """
    # CRITICAL FIX: Distinguish Aura/Equipment triggers from general spell triggers
    # Aura/Equipment/Vehicle trigger patterns (NOT general spellslinger)
    aura_equipment_patterns = [
        r'whenever you cast an aura',
        r'whenever you cast an equipment',
        r'whenever you cast a vehicle',
        r'whenever you cast an aura, equipment, or vehicle'
    ]

    # Spell trigger patterns
    spell_trigger_patterns = [
        r'whenever you cast an instant or sorcery',
        r'whenever you cast an instant',
        r'whenever you cast a sorcery',
        r'whenever you cast a noncreature spell',
        r'whenever you cast.*spell'
    ]

    # Magecraft keyword
    magecraft_patterns = [
        r'magecraft',
        r'whenever you cast or copy an instant or sorcery'
    ]

    # Prowess keyword
    prowess_patterns = [r'prowess']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card2_cmc = card2.get('cmc', 0)
    card1_cmc = card1.get('cmc', 0)

    # CRITICAL FIX: Exclude Aura/Equipment triggers from spellslinger detection
    card1_is_aura_equipment_trigger = any(search_cached(pattern, card1_text) for pattern in aura_equipment_patterns)

    # Check if card1 has spell triggers and card2 is a cheap instant/sorcery
    card1_has_trigger = (any(search_cached(pattern, card1_text) for pattern in spell_trigger_patterns) or \
                        any(search_cached(pattern, card1_text) for pattern in magecraft_patterns) or \
                        'prowess' in card1_keywords) and \
                        not card1_is_aura_equipment_trigger  # FIXED: Exclude Aura/Equipment triggers

    # Heuristic: Instant/Sorcery by type, or by common spell-like text when type is missing
    likely_spell_text = any(kw in card2_text for kw in [
        'scry', 'draw', 'counter target', 'destroy target', 'deal', 'exile target', 'return target', 'create two', 'create', 'gain control of', 'target creature'
    ]) and not any(kw in card2_text for kw in ['equipped creature', 'enchanted creature', 'whenever'])
    card2_is_spell = ('instant' in card2_type or 'sorcery' in card2_type) or likely_spell_text
    card2_is_cheap = card2_cmc <= 3

    if card1_has_trigger and card2_is_spell and card2_is_cheap:
        return {
            'name': 'Spellslinger Engine',
            'description': f"{card1['name']} triggers on spells, {card2['name']} (CMC {card2_cmc}) fuels it",
            'value': 5.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    # Check reverse
    # CRITICAL FIX: Exclude Aura/Equipment triggers from spellslinger detection
    card2_is_aura_equipment_trigger = any(search_cached(pattern, card2_text) for pattern in aura_equipment_patterns)

    card2_has_trigger = (any(search_cached(pattern, card2_text) for pattern in spell_trigger_patterns) or \
                        any(search_cached(pattern, card2_text) for pattern in magecraft_patterns) or \
                        'prowess' in card2_keywords) and \
                        not card2_is_aura_equipment_trigger  # FIXED: Exclude Aura/Equipment triggers

    likely_spell_text1 = any(kw in card1_text for kw in [
        'scry', 'draw', 'counter target', 'destroy target', 'deal', 'exile target', 'return target', 'create two', 'create', 'gain control of', 'target creature'
    ]) and not any(kw in card1_text for kw in ['equipped creature', 'enchanted creature', 'whenever'])
    card1_is_spell = ('instant' in card1_type or 'sorcery' in card1_type) or likely_spell_text1
    card1_is_cheap = card1_cmc <= 3

    if card2_has_trigger and card1_is_spell and card1_is_cheap:
        return {
            'name': 'Spellslinger Engine',
            'description': f"{card2['name']} triggers on spells, {card1['name']} (CMC {card1_cmc}) fuels it",
            'value': 5.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    return None


def detect_artifact_token_triggers(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Artifact Token Triggers synergy (Rule 22)
    Treasure/Clue/Food generation + artifact ETB/death triggers
    """
    # Use the extraction function to get treasure/artifact token info
    card1_treasure_tokens = extract_treasure_tokens(card1)
    card2_treasure_tokens = extract_treasure_tokens(card2)

    # Artifact ETB triggers
    artifact_etb_patterns = [
        r'whenever an artifact enters the battlefield',
        r'whenever.*artifact.*enters'
    ]

    # Artifact death/sac triggers
    artifact_death_patterns = [
        r'whenever an artifact.*put into.*graveyard',
        r'whenever an artifact you control is put into',
        r'whenever.*artifact.*dies',
        r'whenever you sacrifice an artifact'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 makes artifact tokens and card2 has triggers
    card1_makes_artifacts = card1_treasure_tokens['generates_tokens']
    card2_has_etb = any(search_cached(pattern, card2_text) for pattern in artifact_etb_patterns)
    card2_has_death = any(search_cached(pattern, card2_text) for pattern in artifact_death_patterns)

    if card1_makes_artifacts and (card2_has_etb or card2_has_death):
        trigger_type = "enters" if card2_has_etb else "dies"
        token_types = ', '.join(card1_treasure_tokens['token_types']) if card1_treasure_tokens['token_types'] else 'artifact'
        return {
            'name': 'Artifact Token Engine',
            'description': f"{card1['name']} creates {token_types} tokens, {card2['name']} triggers when they {trigger_type}",
            'value': 4.0,
            'category': 'type_synergy',
            'subcategory': 'artifact_matters'
        }

    # Check reverse
    card2_makes_artifacts = card2_treasure_tokens['generates_tokens']
    card1_has_etb = any(search_cached(pattern, card1_text) for pattern in artifact_etb_patterns)
    card1_has_death = any(search_cached(pattern, card1_text) for pattern in artifact_death_patterns)

    if card2_makes_artifacts and (card1_has_etb or card1_has_death):
        trigger_type = "enters" if card1_has_etb else "dies"
        token_types = ', '.join(card2_treasure_tokens['token_types']) if card2_treasure_tokens['token_types'] else 'artifact'
        return {
            'name': 'Artifact Token Engine',
            'description': f"{card2['name']} creates {token_types} tokens, {card1['name']} triggers when they {trigger_type}",
            'value': 4.0,
            'category': 'type_synergy',
            'subcategory': 'artifact_matters'
        }

    return None


def detect_token_doublers(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Token Doubler synergy (Rule 9)
    Token generation + doubling effects (Doubling Season, Parallel Lives)
    """
    # Specific token doubler cards (name-check approach for precision)
    token_doubler_names = [
        'doubling season',
        'parallel lives',
        'anointed procession',
        'primal vigor',
        'mondrak, glory dominus'
    ]

    # Token doubling text patterns
    token_doubler_patterns = [
        r'create twice that many.*tokens',
        r'creates twice that many tokens',
        r'if.*effect would create.*tokens.*creates twice that many'
    ]

    # Token generation patterns
    token_patterns = [
        r'create.*token',
        r'create.*\d+/\d+.*token',
        r'put.*token.*onto the battlefield'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_name = card1.get('name', '').lower()
    card2_name = card2.get('name', '').lower()

    # Check if card1 is a doubler and card2 makes tokens
    card1_is_doubler = card1_name in token_doubler_names or \
                       any(search_cached(pattern, card1_text) for pattern in token_doubler_patterns)
    card2_makes_tokens = any(search_cached(pattern, card2_text) for pattern in token_patterns)

    if card1_is_doubler and card2_makes_tokens:
        return {
            'name': 'Token Doubler',
            'description': f"{card1['name']} doubles {card2['name']}'s token production",
            'value': 4.0,
            'category': 'role_interaction',
            'subcategory': 'token_generation'
        }

    # Check reverse
    card2_is_doubler = card2_name in token_doubler_names or \
                       any(search_cached(pattern, card2_text) for pattern in token_doubler_patterns)
    card1_makes_tokens = any(search_cached(pattern, card1_text) for pattern in token_patterns)

    if card2_is_doubler and card1_makes_tokens:
        return {
            'name': 'Token Doubler',
            'description': f"{card2['name']} doubles {card1['name']}'s token production",
            'value': 4.0,
            'category': 'role_interaction',
            'subcategory': 'token_generation'
        }

    return None


def detect_discard_madness_flashback(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Discard + Madness/Flashback synergy (Rule 19)
    Discard outlets + cards that benefit from being discarded
    """
    # Repeatable discard outlet patterns (not one-shot)
    discard_outlet_patterns = [
        r'\{.*\}:.*discard',  # Activated ability with discard
        r'tap.*discard',
        r'whenever.*draw.*discard',  # Looting effects
        r'may discard.*if you do'
    ]

    # One-shot discard spells (lower priority)
    oneshot_discard_patterns = [
        r'draw.*cards.*discard',  # Looting spells
        r'discard.*draw'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 is discard outlet and card2 has madness/flashback
    card1_is_outlet = any(search_cached(pattern, card1_text) for pattern in discard_outlet_patterns) or \
                      any(search_cached(pattern, card1_text) for pattern in oneshot_discard_patterns)

    card2_has_madness = 'madness' in card2_keywords or 'madness' in card2_text
    card2_has_flashback = 'flashback' in card2_keywords or 'flashback' in card2_text
    card2_has_jumpstart = 'jump-start' in card2_keywords

    if card1_is_outlet and (card2_has_madness or card2_has_flashback or card2_has_jumpstart):
        mechanic = 'Madness' if card2_has_madness else 'Flashback' if card2_has_flashback else 'Jump-Start'
        return {
            'name': 'Discard Synergy',
            'description': f"{card1['name']} discards {card2['name']} ({mechanic}) for value",
            'value': 3.0,
            'category': 'card_advantage',
            'subcategory': 'recursion_loop'
        }

    # Check reverse
    card2_is_outlet = any(search_cached(pattern, card2_text) for pattern in discard_outlet_patterns) or \
                      any(search_cached(pattern, card2_text) for pattern in oneshot_discard_patterns)

    card1_has_madness = 'madness' in card1_keywords or 'madness' in card1_text
    card1_has_flashback = 'flashback' in card1_keywords or 'flashback' in card1_text
    card1_has_jumpstart = 'jump-start' in card1_keywords

    if card2_is_outlet and (card1_has_madness or card1_has_flashback or card1_has_jumpstart):
        mechanic = 'Madness' if card1_has_madness else 'Flashback' if card1_has_flashback else 'Jump-Start'
        return {
            'name': 'Discard Synergy',
            'description': f"{card2['name']} discards {card1['name']} ({mechanic}) for value",
            'value': 3.0,
            'category': 'card_advantage',
            'subcategory': 'recursion_loop'
        }

    return None


def detect_enchantress_effects(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Enchantress Effects synergy (Rule 23)
    Enchantment cast triggers + high enchantment count
    """
    # Enchantress effect patterns
    enchantress_patterns = [
        r'whenever you cast an enchantment spell.*draw',
        r'whenever you cast an enchantment.*draw',
        r'whenever.*enchantment enters the battlefield.*draw'
    ]

    # Constellation patterns
    constellation_patterns = [
        r'constellation',
        r'whenever.*enchantment enters the battlefield under your control'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Check if card1 has enchantress effect and card2 is an enchantment
    card1_is_enchantress = (
        any(search_cached(pattern, card1_text) for pattern in enchantress_patterns)
        or any(search_cached(pattern, card1_text) for pattern in constellation_patterns)
    )
    # Consider enchantments by type or by clear Aura/enchant wording if type_line missing
    card2_is_enchantment = 'enchantment' in card2_type or \
                           ('enchant ' in card2_text) or ('aura' in card2_text)

    if card1_is_enchantress and card2_is_enchantment:
        return {
            'name': 'Enchantress Engine',
            'description': f"{card1['name']} draws when you cast {card2['name']} (enchantment)",
            'value': 4.0,
            'category': 'card_advantage',
            'subcategory': 'draw_engine'
        }

    # Check reverse
    card2_is_enchantress = (
        any(search_cached(pattern, card2_text) for pattern in enchantress_patterns)
        or any(search_cached(pattern, card2_text) for pattern in constellation_patterns)
    )
    card1_is_enchantment = 'enchantment' in card1_type or \
                           ('enchant ' in card1_text) or ('aura' in card1_text)

    if card2_is_enchantress and card1_is_enchantment:
        return {
            'name': 'Enchantress Engine',
            'description': f"{card2['name']} draws when you cast {card1['name']} (enchantment)",
            'value': 4.0,
            'category': 'card_advantage',
            'subcategory': 'draw_engine'
        }

    return None


def detect_voltron_evasion(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Voltron + Evasion synergy (Rule 24)
    Equipment/Auras that grant power + evasion abilities
    """
    # Equipment/Aura indicators
    equipment_aura_patterns = [
        r'equipped creature',
        r'enchanted creature',
        r'attach.*creature'
    ]

    # Power boost patterns
    power_boost_patterns = [
        r'gets \+\d+/\+',
        r'gets \+\d+/\+\d+',
        r'has \+\d+/\+'
    ]

    # Evasion keywords and patterns
    evasion_keywords = ['flying', 'trample', 'menace', 'unblockable', 'hexproof', 'protection', 'indestructible']
    evasion_patterns = [
        r'can\'t be blocked',
        r'unblockable',
        r'flying',
        r'trample',
        r'menace',
        r'protection from',
        r'hexproof',
        r'shroud',
        r'indestructible'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 is equipment/aura with power boost and card2 grants evasion
    card1_is_equipment_aura = 'equipment' in card1_type or 'aura' in card1_type or \
                              any(search_cached(pattern, card1_text) for pattern in equipment_aura_patterns)
    card1_boosts_power = any(search_cached(pattern, card1_text) for pattern in power_boost_patterns)

    card2_grants_evasion = any(kw in card2_keywords for kw in evasion_keywords) or \
                           any(search_cached(pattern, card2_text) for pattern in evasion_patterns)
    card2_is_equipment_aura = 'equipment' in card2_type or 'aura' in card2_type

    if card1_is_equipment_aura and card1_boosts_power and card2_is_equipment_aura and card2_grants_evasion:
        return {
            'name': 'Voltron Package',
            'description': f"{card1['name']} boosts power, {card2['name']} grants evasion",
            'value': 3.5,
            'category': 'benefits',
            'subcategory': 'keyword_grant'
        }

    # Check reverse
    card2_is_equipment_aura = 'equipment' in card2_type or 'aura' in card2_type or \
                              any(search_cached(pattern, card2_text) for pattern in equipment_aura_patterns)
    card2_boosts_power = any(search_cached(pattern, card2_text) for pattern in power_boost_patterns)

    card1_grants_evasion = any(kw in card1_keywords for kw in evasion_keywords) or \
                           any(search_cached(pattern, card1_text) for pattern in evasion_patterns)
    card1_is_equipment_aura = 'equipment' in card1_type or 'aura' in card1_type

    if card2_is_equipment_aura and card2_boosts_power and card1_is_equipment_aura and card1_grants_evasion:
        return {
            'name': 'Voltron Package',
            'description': f"{card2['name']} boosts power, {card1['name']} grants evasion",
            'value': 3.5,
            'category': 'benefits',
            'subcategory': 'keyword_grant'
        }

    return None


def detect_aristocrats_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect aristocrats synergies: death triggers + sacrifice outlets + drain effects

    Aristocrats is a strategy where creatures dying triggers beneficial effects,
    especially life drain effects like Blood Artist, Zulaport Cutthroat.
    """
    # Classify both cards (using cache)
    class1 = get_damage_classification(card1)
    class2 = get_damage_classification(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Death trigger patterns - exclude self-death triggers
    death_trigger_patterns = [
        r'whenever (?:a|another|one or more) creature', # "whenever a creature dies"
        r'whenever.*creatures.*die',                     # "whenever one or more creatures die"
        r'when (?:a|another) creature.*dies',           # "when a creature dies"
        r'whenever (?:a|another) .*permanent.*dies',    # "whenever a permanent dies"
    ]
    # Self-death patterns to EXCLUDE (not payoffs, just self-triggers)
    self_death_patterns = [
        r'when (this|~) .*dies',                        # "when this creature dies"
        r'when (this|~) .*is put into.*graveyard',     # "when this is put into a graveyard"
        r'whenever (this|~) dies',                      # "whenever this dies"
    ]

    # Sacrifice outlet patterns
    sacrifice_outlet_patterns = [
        r'sacrifice a creature',
        r'sacrifice a permanent',
        r'sacrifice.*you control',
        r'you may sacrifice'
    ]

    # Token generation patterns
    token_generation_patterns = [r'create.*token', r'put.*token.*onto the battlefield']

    card1_is_drain = class1['strategy'] == 'drain'
    card2_is_drain = class2['strategy'] == 'drain'

    # Only count as death trigger if NOT a self-death trigger
    card1_has_death_trigger = any(search_cached(pattern, card1_text) for pattern in death_trigger_patterns) and \
                               not any(search_cached(pattern, card1_text) for pattern in self_death_patterns)
    card2_has_death_trigger = any(search_cached(pattern, card2_text) for pattern in death_trigger_patterns) and \
                               not any(search_cached(pattern, card2_text) for pattern in self_death_patterns)

    card1_is_sac_outlet = any(search_cached(pattern, card1_text) for pattern in sacrifice_outlet_patterns)
    card2_is_sac_outlet = any(search_cached(pattern, card2_text) for pattern in sacrifice_outlet_patterns)

    card1_makes_tokens = any(search_cached(pattern, card1_text) for pattern in token_generation_patterns)
    card2_makes_tokens = any(search_cached(pattern, card2_text) for pattern in token_generation_patterns)

    # Drain effect + sacrifice outlet = aristocrats combo
    if card1_is_drain and card2_is_sac_outlet:
        return {
            'name': 'Aristocrats Combo',
            'description': f"{card1['name']} drains life when creatures die, {card2['name']} provides sacrifice outlet",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'aristocrats'
        }

    if card2_is_drain and card1_is_sac_outlet:
        return {
            'name': 'Aristocrats Combo',
            'description': f"{card2['name']} drains life when creatures die, {card1['name']} provides sacrifice outlet",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'aristocrats'
        }

    # Drain effect + token generation = fodder for aristocrats
    if card1_is_drain and card2_makes_tokens:
        return {
            'name': 'Aristocrats Fodder',
            'description': f"{card1['name']} drains life when creatures die, {card2['name']} creates sacrificial tokens",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'aristocrats'
        }

    if card2_is_drain and card1_makes_tokens:
        return {
            'name': 'Aristocrats Fodder',
            'description': f"{card2['name']} drains life when creatures die, {card1['name']} creates sacrificial tokens",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'aristocrats'
        }

    # Multiple drain effects stack together
    if card1_is_drain and card2_is_drain:
        return {
            'name': 'Stacking Drain Effects',
            'description': f"{card1['name']} and {card2['name']} both drain opponents when creatures die",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'aristocrats'
        }

    # Death trigger with death trigger (aristocrats package)
    if card1_has_death_trigger and card2_has_death_trigger:
        return {
            'name': 'Death Trigger Synergy',
            'description': f"{card1['name']} and {card2['name']} both trigger when creatures die",
            'value': 2.5,
            'category': 'triggers',
            'subcategory': 'death_triggers'
        }

    return None


def detect_burn_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect burn synergies: damage amplifiers + damage dealers

    Burn strategy focuses on dealing direct damage to opponents.
    """
    class1 = get_damage_classification(card1)
    class2 = get_damage_classification(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Damage amplifier patterns
    damage_amplifier_patterns = [
        r'if.*source.*would deal damage.*deals.*instead',
        r'if.*would deal damage.*deals.*plus',
        r'if.*would deal damage.*double',
        r'if.*would deal damage.*triple',
        r'whenever.*deals damage.*deals.*additional'
    ]

    # Direct damage patterns
    direct_damage_patterns = [
        r'deals? \d+ damage',
        r'deals? damage equal to',
        r'each opponent loses \d+ life'
    ]

    card1_has_damage = class1['has_damage_effects'] or len(class1['direct_damages']) > 0 or len(class1['burn_effects']) > 0
    card2_has_damage = class2['has_damage_effects'] or len(class2['direct_damages']) > 0 or len(class2['burn_effects']) > 0

    card1_is_amplifier = any(search_cached(pattern, card1_text) for pattern in damage_amplifier_patterns)
    card2_is_amplifier = any(search_cached(pattern, card2_text) for pattern in damage_amplifier_patterns)

    card1_multiplayer = class1['is_multiplayer_focused']
    card2_multiplayer = class2['is_multiplayer_focused']

    # Damage amplifier + damage dealer
    if card1_is_amplifier and card2_has_damage:
        return {
            'name': 'Burn Amplification',
            'description': f"{card1['name']} amplifies damage from {card2['name']}",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'burn'
        }

    if card2_is_amplifier and card1_has_damage:
        return {
            'name': 'Burn Amplification',
            'description': f"{card2['name']} amplifies damage from {card1['name']}",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'burn'
        }

    # Multiple burn effects for multiplayer
    if card1_multiplayer and card2_multiplayer:
        return {
            'name': 'Multiplayer Burn Package',
            'description': f"{card1['name']} and {card2['name']} both hit multiple opponents",
            'value': 3.0,
            'category': 'strategy',
            'subcategory': 'burn'
        }

    # Multiple damage sources
    if card1_has_damage and card2_has_damage:
        total_damage = class1['estimated_damage'] + class2['estimated_damage']
        if total_damage >= 10:
            return {
                'name': 'Burn Package',
                'description': f"{card1['name']} and {card2['name']} combine for high damage output",
                'value': 2.5,
                'category': 'strategy',
                'subcategory': 'burn'
            }

    return None


def detect_lifegain_payoffs(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect lifegain synergies: lifegain triggers + lifegain sources

    Cards that benefit when you gain life + cards that gain life.
    """
    class1 = get_damage_classification(card1)
    class2 = get_damage_classification(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Lifegain trigger patterns (payoffs)
    lifegain_payoff_patterns = [
        r'whenever you gain life.*put.*counter',
        r'whenever you gain life.*draw',
        r'whenever you gain life.*create',
        r'whenever you gain life.*gain',
        r'if you would gain life.*gain.*instead'
    ]

    card1_has_lifegain = class1['has_life_gain'] or class1['strategy'] == 'lifegain'
    card2_has_lifegain = class2['has_life_gain'] or class2['strategy'] == 'lifegain'

    card1_is_payoff = any(search_cached(pattern, card1_text) for pattern in lifegain_payoff_patterns)
    card2_is_payoff = any(search_cached(pattern, card2_text) for pattern in lifegain_payoff_patterns)

    # Lifegain payoff + lifegain source
    if card1_is_payoff and card2_has_lifegain:
        return {
            'name': 'Lifegain Synergy',
            'description': f"{card1['name']} benefits when {card2['name']} gains you life",
            'value': 3.5,
            'category': 'triggers',
            'subcategory': 'lifegain'
        }

    if card2_is_payoff and card1_has_lifegain:
        return {
            'name': 'Lifegain Synergy',
            'description': f"{card2['name']} benefits when {card1['name']} gains you life",
            'value': 3.5,
            'category': 'triggers',
            'subcategory': 'lifegain'
        }

    # Multiple lifegain sources
    if card1_has_lifegain and card2_has_lifegain:
        return {
            'name': 'Lifegain Package',
            'description': f"{card1['name']} and {card2['name']} both provide life gain",
            'value': 2.0,
            'category': 'strategy',
            'subcategory': 'lifegain'
        }

    return None


def detect_damage_based_card_draw(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies between damage dealers and cards that draw when dealing damage

    Examples: Niv-Mizzet draws when you deal damage, or deals damage when you draw
    """
    class1 = get_damage_classification(card1)
    class2 = get_damage_classification(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Draw when dealing damage patterns
    damage_draw_patterns = [
        r'whenever.*deal.*damage.*draw',
        r'whenever you draw.*deals? damage',
        r'whenever.*deals combat damage.*draw'
    ]

    card1_has_damage = class1['has_damage_effects']
    card2_has_damage = class2['has_damage_effects']

    card1_is_draw_trigger = any(search_cached(pattern, card1_text) for pattern in damage_draw_patterns)
    card2_is_draw_trigger = any(search_cached(pattern, card2_text) for pattern in damage_draw_patterns)

    # Damage + draw trigger creates engine
    if card1_is_draw_trigger and card2_has_damage:
        return {
            'name': 'Damage Draw Engine',
            'description': f"{card1['name']} creates draw/damage loop with {card2['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'draw_damage'
        }

    if card2_is_draw_trigger and card1_has_damage:
        return {
            'name': 'Damage Draw Engine',
            'description': f"{card2['name']} creates draw/damage loop with {card1['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'draw_damage'
        }

    # Multiple draw/damage triggers create powerful engine
    if card1_is_draw_trigger and card2_is_draw_trigger:
        return {
            'name': 'Double Draw/Damage Engine',
            'description': f"{card1['name']} and {card2['name']} create powerful draw/damage loop",
            'value': 5.0,
            'category': 'combo',
            'subcategory': 'draw_damage'
        }

    return None


def detect_creature_damage_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies with creature-based damage (power matters, combat damage triggers)
    """
    class1 = get_damage_classification(card1)
    class2 = get_damage_classification(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Power boost patterns
    power_boost_patterns = [
        r'\+\d+/\+\d+',
        r'gets \+\d+/\+\d+',
        r'creatures you control get \+\d+/\+\d+'
    ]

    # Combat damage matter patterns
    combat_matters_patterns = [
        r'whenever.*deals combat damage',
        r'when.*deals combat damage',
        r'if.*dealt combat damage'
    ]

    card1_has_creature_damage = len(class1['creature_damages']) > 0
    card2_has_creature_damage = len(class2['creature_damages']) > 0

    card1_boosts_power = any(search_cached(pattern, card1_text) for pattern in power_boost_patterns)
    card2_boosts_power = any(search_cached(pattern, card2_text) for pattern in power_boost_patterns)

    card1_combat_matters = any(search_cached(pattern, card1_text) for pattern in combat_matters_patterns)
    card2_combat_matters = any(search_cached(pattern, card2_text) for pattern in combat_matters_patterns)

    # Power boost + combat damage trigger
    if card1_boosts_power and card2_combat_matters:
        return {
            'name': 'Combat Damage Synergy',
            'description': f"{card1['name']} boosts power for {card2['name']}'s combat triggers",
            'value': 3.0,
            'category': 'combat',
            'subcategory': 'combat_damage'
        }

    if card2_boosts_power and card1_combat_matters:
        return {
            'name': 'Combat Damage Synergy',
            'description': f"{card2['name']} boosts power for {card1['name']}'s combat triggers",
            'value': 3.0,
            'category': 'combat',
            'subcategory': 'combat_damage'
        }

    # Multiple combat damage triggers
    if card1_combat_matters and card2_combat_matters:
        return {
            'name': 'Combat Trigger Package',
            'description': f"{card1['name']} and {card2['name']} both trigger on combat damage",
            'value': 2.5,
            'category': 'combat',
            'subcategory': 'combat_damage'
        }

    return None


def detect_equipment_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect equipment synergy - equipment + creatures that benefit, tutors, or recursion
    """
    # Equipment patterns
    equipment_patterns = [
        r'\bequipment\b',
        r'equip \{',
        r'attach.*to target creature',
        r'living weapon'  # Equipment that creates tokens
    ]

    # Equipment tutor patterns (specific - check these first)
    equipment_tutor_patterns = [
        r'search.*library.*equipment',
        r'search.*library.*for.*equipment'
    ]

    # Equipment recursion patterns
    equipment_recursion_patterns = [
        r'equipment.*from.*graveyard',
        r'return.*equipment.*from.*graveyard'
    ]

    # Equipment matters patterns (general)
    equipment_matters_patterns = [
        r'whenever.*equipped',
        r'when.*becomes equipped',
        r'equipped creature',
        r'equipment.*cost.*to equip',
        r'equipment.*you control',
        r'creatures you control with equipment',
        r'whenever.*equipment.*enters'
    ]

    # Equipment synergy keywords
    equipment_keywords = ['equipped', 'equip']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Check if one is equipment and the other cares about equipment
    card1_is_equipment = 'equipment' in card1_type or any(search_cached(pattern, card1_text) for pattern in equipment_patterns)
    card2_is_equipment = 'equipment' in card2_type or any(search_cached(pattern, card2_text) for pattern in equipment_patterns)

    # Check for specific equipment interactions (tutors, recursion, matters)
    card1_tutors_equipment = any(search_cached(pattern, card1_text) for pattern in equipment_tutor_patterns)
    card2_tutors_equipment = any(search_cached(pattern, card2_text) for pattern in equipment_tutor_patterns)

    card1_recurs_equipment = any(search_cached(pattern, card1_text) for pattern in equipment_recursion_patterns)
    card2_recurs_equipment = any(search_cached(pattern, card2_text) for pattern in equipment_recursion_patterns)

    card1_cares_equipment = any(search_cached(pattern, card1_text) for pattern in equipment_matters_patterns)
    card2_cares_equipment = any(search_cached(pattern, card2_text) for pattern in equipment_matters_patterns)

    # FIXED: Equipment + tutor (most specific)
    if card1_is_equipment and card2_tutors_equipment:
        return {
            'name': 'Equipment Tutor',
            'description': f"{card2['name']} can tutor for equipment like {card1['name']}",
            'value': 3.5,
            'category': 'card_advantage',
            'subcategory': 'tutor_target'
        }

    if card2_is_equipment and card1_tutors_equipment:
        return {
            'name': 'Equipment Tutor',
            'description': f"{card1['name']} can tutor for equipment like {card2['name']}",
            'value': 3.5,
            'category': 'card_advantage',
            'subcategory': 'tutor_target'
        }

    # FIXED: Equipment + recursion
    if card1_is_equipment and card2_recurs_equipment:
        return {
            'name': 'Equipment Recursion',
            'description': f"{card2['name']} can recur equipment like {card1['name']} from graveyard",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'recursion'
        }

    if card2_is_equipment and card1_recurs_equipment:
        return {
            'name': 'Equipment Recursion',
            'description': f"{card1['name']} can recur equipment like {card2['name']} from graveyard",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'recursion'
        }

    # FIXED: Equipment + equipment matters (general)
    if card1_is_equipment and card2_cares_equipment:
        return {
            'name': 'Equipment Synergy',
            'description': f"{card2['name']} cares about equipment, {card1['name']} is equipment",
            'value': 3.0,
            'category': 'type_synergy',
            'subcategory': 'equipment_matters'
        }

    if card2_is_equipment and card1_cares_equipment:
        return {
            'name': 'Equipment Synergy',
            'description': f"{card1['name']} cares about equipment, {card2['name']} is equipment",
            'value': 3.0,
            'category': 'type_synergy',
            'subcategory': 'equipment_matters'
        }

    # Multiple equipment cards
    if card1_is_equipment and card2_is_equipment:
        return {
            'name': 'Equipment Package',
            'description': f"{card1['name']} and {card2['name']} form equipment package",
            'value': 2.0,
            'category': 'type_synergy',
            'subcategory': 'equipment_matters'
        }

    return None


def detect_landfall_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect landfall synergy - landfall triggers + ramp/land fetching
    """
    # Landfall patterns
    landfall_patterns = [
        r'\blandfall\b',
        r'whenever a land enters the battlefield',
        r'whenever a land enters.*under your control',
        r'whenever.*play a land'
    ]

    # Land ramp/fetch patterns
    land_ramp_patterns = [
        r'search.*library.*land',
        r'put.*land.*onto the battlefield',
        r'you may play an additional land',
        r'put a land.*from.*hand onto the battlefield',
        r'return.*land.*from.*graveyard',
        r'land.*from.*graveyard.*to.*battlefield'
    ]

    # Extra land drop patterns (high synergy with landfall)
    extra_land_patterns = [
        r'you may play an additional land',
        r'play.*additional lands?',
        r'play.*extra lands?'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_name = card1.get('name', '').lower()
    card2_name = card2.get('name', '').lower()

    # Check if one has landfall and the other ramps/fetches lands
    card1_has_landfall = any(search_cached(pattern, card1_text) for pattern in landfall_patterns)
    card2_has_landfall = any(search_cached(pattern, card2_text) for pattern in landfall_patterns)

    card1_ramps_lands = any(search_cached(pattern, card1_text) for pattern in land_ramp_patterns)
    card2_ramps_lands = any(search_cached(pattern, card2_text) for pattern in land_ramp_patterns)

    card1_extra_lands = any(search_cached(pattern, card1_text) for pattern in extra_land_patterns)
    card2_extra_lands = any(search_cached(pattern, card2_text) for pattern in extra_land_patterns)

    # HIGH VALUE: Scute Swarm + extra land drops (exponential growth!)
    if ('scute swarm' in card1_name and card2_extra_lands) or ('scute swarm' in card2_name and card1_extra_lands):
        return {
            'name': 'Exponential Landfall',
            'description': f"Scute Swarm creates exponentially more copies with extra land drops!",
            'value': 5.0,  # Very high value!
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    # HIGH VALUE: Avenger of Zendikar + landfall enablers
    if ('avenger of zendikar' in card1_name and card2_ramps_lands) or ('avenger of zendikar' in card2_name and card1_ramps_lands):
        return {
            'name': 'Massive Token Army',
            'description': f"Avenger creates plants for each land, then buffs them with landfall",
            'value': 4.5,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    # HIGH VALUE: Omnath + extra land drops (multiple triggers per turn)
    omnath_names = ['omnath, locus of rage', 'omnath, locus of creation', 'omnath, locus of the roil']
    if (any(name in card1_name for name in omnath_names) and card2_extra_lands) or \
       (any(name in card2_name for name in omnath_names) and card1_extra_lands):
        return {
            'name': 'Multiple Omnath Triggers',
            'description': f"Omnath triggers multiple times per turn with extra land drops",
            'value': 4.5,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    # Landfall + extra land drops (high synergy!)
    if card1_has_landfall and card2_extra_lands:
        return {
            'name': 'Extra Landfall Triggers',
            'description': f"{card1['name']}'s landfall triggers multiple times with {card2['name']}'s extra drops",
            'value': 4.0,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    if card2_has_landfall and card1_extra_lands:
        return {
            'name': 'Extra Landfall Triggers',
            'description': f"{card2['name']}'s landfall triggers multiple times with {card1['name']}'s extra drops",
            'value': 4.0,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    # Landfall + land ramp
    if card1_has_landfall and card2_ramps_lands:
        return {
            'name': 'Landfall Synergy',
            'description': f"{card1['name']}'s landfall triggers from {card2['name']}'s land ramp",
            'value': 3.5,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    if card2_has_landfall and card1_ramps_lands:
        return {
            'name': 'Landfall Synergy',
            'description': f"{card2['name']}'s landfall triggers from {card1['name']}'s land ramp",
            'value': 3.5,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    # Multiple landfall triggers
    if card1_has_landfall and card2_has_landfall:
        return {
            'name': 'Landfall Package',
            'description': f"{card1['name']} and {card2['name']} both trigger on landfall",
            'value': 2.5,
            'category': 'triggers',
            'subcategory': 'landfall'
        }

    return None


def detect_counter_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect +1/+1 counter synergy - counter placement + counter payoffs/doublers
    """
    # +1/+1 counter placement patterns
    counter_place_patterns = [
        r'put.*\+1/\+1 counter',
        r'enters.*with.*\+1/\+1 counter',
        r'gets.*\+1/\+1 counter',
        r'distribute.*\+1/\+1 counter',
        r'proliferate'
    ]

    # +1/+1 counter matters patterns
    counter_matters_patterns = [
        r'whenever.*\+1/\+1 counter is put',
        r'whenever.*with a \+1/\+1 counter',
        r'creature with a \+1/\+1 counter',
        r'remove a \+1/\+1 counter',
        r'for each \+1/\+1 counter',
        r'creatures with \+1/\+1 counters',
        r'double.*counters',
        r'twice.*many counters',
        r'if a creature.*would enter.*\+1/\+1 counters.*instead'  # Doubling season
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_places_counters = any(search_cached(pattern, card1_text) for pattern in counter_place_patterns)
    card2_places_counters = any(search_cached(pattern, card2_text) for pattern in counter_place_patterns)

    card1_cares_counters = any(search_cached(pattern, card1_text) for pattern in counter_matters_patterns)
    card2_cares_counters = any(search_cached(pattern, card2_text) for pattern in counter_matters_patterns)

    # Counter doubler patterns (higher value)
    counter_doubler_patterns = [
        r'double.*counters',
        r'twice.*many counters',
        r'if.*would.*counter.*instead.*twice that many',
        r'if.*\+1/\+1 counters? would be placed.*instead.*that many plus',
        r'that many plus one \+1/\+1',
        r'additional \+1/\+1 counter'
    ]

    card1_doubles_counters = any(search_cached(pattern, card1_text) for pattern in counter_doubler_patterns)
    card2_doubles_counters = any(search_cached(pattern, card2_text) for pattern in counter_doubler_patterns)

    # Counter placement + counter doubler (highest value)
    if card1_places_counters and card2_doubles_counters:
        return {
            'name': 'Counter Doubling',
            'description': f"{card2['name']} doubles counters from {card1['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'counter_synergy'
        }

    if card2_places_counters and card1_doubles_counters:
        return {
            'name': 'Counter Doubling',
            'description': f"{card1['name']} doubles counters from {card2['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'counter_synergy'
        }

    # Counter placement + counter matters
    if card1_places_counters and card2_cares_counters:
        return {
            'name': 'Counter Synergy',
            'description': f"{card1['name']} places counters for {card2['name']}'s payoffs",
            'value': 3.0,
            'category': 'benefits',
            'subcategory': 'counter_synergy'
        }

    if card2_places_counters and card1_cares_counters:
        return {
            'name': 'Counter Synergy',
            'description': f"{card2['name']} places counters for {card1['name']}'s payoffs",
            'value': 3.0,
            'category': 'benefits',
            'subcategory': 'counter_synergy'
        }

    # Multiple counter placers
    if card1_places_counters and card2_places_counters:
        return {
            'name': 'Counter Package',
            'description': f"{card1['name']} and {card2['name']} both place +1/+1 counters",
            'value': 2.0,
            'category': 'benefits',
            'subcategory': 'counter_synergy'
        }

    return None


def detect_copy_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect copy/clone effects synergy - clones + high-value ETBs or abilities

    Enhanced to use extract_token_copy_effects for better detection of token copy spells.
    """
    # Import extractor
    try:
        from src.utils.token_extractors import extract_token_copy_effects
    except ImportError:
        extract_token_copy_effects = None

    # Copy/clone patterns
    copy_patterns = [
        r'\bcopy\b',
        r'\bclone\b',
        r'create a token.*copy',
        r'create.*token.*that.*cop(?:y|ies)',
        r'copy target',
        r'as a copy of',
        r'enters.*as a copy',
        r'you may have.*enter.*as a copy'
    ]

    # Spell copy patterns (separate from creature clones)
    spell_copy_patterns = [
        r'copy.*instant',
        r'copy.*sorcery',
        r'copy target instant or sorcery',
        r'copy the next instant',
        r'when you cast.*instant or sorcery.*copy'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Check for creature clones (permanent creatures that copy)
    card1_is_clone = any(search_cached(pattern, card1_text) for pattern in copy_patterns) and 'creature' in card1_type
    card2_is_clone = any(search_cached(pattern, card2_text) for pattern in copy_patterns) and 'creature' in card2_type

    # Check for token copy spells (using extractor if available)
    card1_token_copy = None
    card2_token_copy = None
    if extract_token_copy_effects:
        card1_token_copy = extract_token_copy_effects(card1)
        card2_token_copy = extract_token_copy_effects(card2)

    card1_creates_token_copy = (card1_token_copy and card1_token_copy.get('creates_token_copies', False)) or \
                                search_cached(r'create.*token.*cop(?:y|ies)', card1_text)
    card2_creates_token_copy = (card2_token_copy and card2_token_copy.get('creates_token_copies', False)) or \
                                search_cached(r'create.*token.*cop(?:y|ies)', card2_text)

    # Check for spell copiers
    card1_copies_spells = any(search_cached(pattern, card1_text) for pattern in spell_copy_patterns)
    card2_copies_spells = any(search_cached(pattern, card2_text) for pattern in spell_copy_patterns)

    # High-value ETB patterns
    high_value_etb_patterns = [
        r'enters the battlefield.*draw',
        r'enters the battlefield.*destroy',
        r'enters the battlefield.*exile',
        r'enters the battlefield.*return',
        r'enters the battlefield.*search',
        r'enters the battlefield.*create',
        r'enters the battlefield.*put'
    ]

    card1_has_etb = any(search_cached(pattern, card1_text) for pattern in high_value_etb_patterns)
    card2_has_etb = any(search_cached(pattern, card2_text) for pattern in high_value_etb_patterns)

    # Check for legendary creatures (higher value for token copy effects that remove legendary)
    card1_is_legendary = 'legendary' in card1_type and 'creature' in card1_type
    card2_is_legendary = 'legendary' in card2_type and 'creature' in card2_type

    # Clone + high-value ETB
    if card1_is_clone and card2_has_etb:
        return {
            'name': 'Clone Value',
            'description': f"{card1['name']} can copy {card2['name']}'s powerful ETB",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'copy_effects'
        }

    if card2_is_clone and card1_has_etb:
        return {
            'name': 'Clone Value',
            'description': f"{card2['name']} can copy {card1['name']}'s powerful ETB",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'copy_effects'
        }

    # Token copy spell + high-value ETB (even stronger synergy since it creates an extra creature)
    if card1_creates_token_copy and card2_has_etb:
        # Check if the copy removes legendary (bonus value)
        removes_legendary = card1_token_copy and 'not_legendary' in card1_token_copy.get('modifications', []) if card1_token_copy else False
        value = 5.0 if (card2_is_legendary and removes_legendary) else 4.0

        return {
            'name': 'Token Copy + ETB Value',
            'description': f"{card1['name']} creates token copies that trigger {card2['name']}'s ETB again" +
                          (" (works with legendary!)" if removes_legendary and card2_is_legendary else ""),
            'value': value,
            'category': 'tokens',
            'subcategory': 'token_copy'
        }

    if card2_creates_token_copy and card1_has_etb:
        # Check if the copy removes legendary (bonus value)
        removes_legendary = card2_token_copy and 'not_legendary' in card2_token_copy.get('modifications', []) if card2_token_copy else False
        value = 5.0 if (card1_is_legendary and removes_legendary) else 4.0

        return {
            'name': 'Token Copy + ETB Value',
            'description': f"{card2['name']} creates token copies that trigger {card1['name']}'s ETB again" +
                          (" (works with legendary!)" if removes_legendary and card1_is_legendary else ""),
            'value': value,
            'category': 'tokens',
            'subcategory': 'token_copy'
        }

    # Token copy + powerful static abilities
    powerful_ability_patterns = [
        r'creatures you control (?:get|have)',
        r'whenever.*creature.*attacks',
        r'whenever.*creature.*dies',
        r'sacrifice.*creature',
    ]

    card1_has_powerful_ability = any(search_cached(pattern, card1_text) for pattern in powerful_ability_patterns)
    card2_has_powerful_ability = any(search_cached(pattern, card2_text) for pattern in powerful_ability_patterns)

    if card1_creates_token_copy and card2_has_powerful_ability and 'creature' in card2_type:
        return {
            'name': 'Token Copy + Powerful Ability',
            'description': f"{card1['name']} can duplicate {card2['name']}'s powerful abilities",
            'value': 3.5,
            'category': 'tokens',
            'subcategory': 'token_copy'
        }

    if card2_creates_token_copy and card1_has_powerful_ability and 'creature' in card1_type:
        return {
            'name': 'Token Copy + Powerful Ability',
            'description': f"{card2['name']} can duplicate {card1['name']}'s powerful abilities",
            'value': 3.5,
            'category': 'tokens',
            'subcategory': 'token_copy'
        }

    # Spell copier + instant/sorcery
    card1_is_instant_sorcery = 'instant' in card1_type or 'sorcery' in card1_type
    card2_is_instant_sorcery = 'instant' in card2_type or 'sorcery' in card2_type

    if card1_copies_spells and card2_is_instant_sorcery:
        return {
            'name': 'Spell Copy Synergy',
            'description': f"{card1['name']} can copy {card2['name']}",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'spell_copy'
        }

    if card2_copies_spells and card1_is_instant_sorcery:
        return {
            'name': 'Spell Copy Synergy',
            'description': f"{card2['name']} can copy {card1['name']}",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'spell_copy'
        }

    return None


def detect_storm_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect storm synergy - storm spells + cheap cantrips/rituals
    """
    # Storm patterns
    storm_patterns = [
        r'\bstorm\b',
        r'for each spell cast before it this turn',
        r'copy.*for each spell cast',
        r'whenever you cast.*instant or sorcery.*copy'  # Bonus storm-like effects
    ]

    # Storm enablers - cheap spells and ritual effects
    cheap_spell_patterns = [
        r'draw a card',
        r'add \{[rgbuwc]\}',
        r'add [rgbuwc]',
        r'add.*mana',
        r'cost.*less to cast',
        r'costs? \{1\} less'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 999)
    card2_cmc = card2.get('cmc', 999)

    # Check for storm
    card1_has_storm = any(search_cached(pattern, card1_text) for pattern in storm_patterns)
    card2_has_storm = any(search_cached(pattern, card2_text) for pattern in storm_patterns)

    # Check for cheap enablers
    card1_is_enabler = (card1_cmc <= 2 and ('instant' in card1_type or 'sorcery' in card1_type)) and \
                       any(search_cached(pattern, card1_text) for pattern in cheap_spell_patterns)
    card2_is_enabler = (card2_cmc <= 2 and ('instant' in card2_type or 'sorcery' in card2_type)) and \
                       any(search_cached(pattern, card2_text) for pattern in cheap_spell_patterns)

    # Storm + cheap enabler
    if card1_has_storm and card2_is_enabler:
        return {
            'name': 'Storm Enabler',
            'description': f"{card2['name']} helps build storm count for {card1['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'storm'
        }

    if card2_has_storm and card1_is_enabler:
        return {
            'name': 'Storm Enabler',
            'description': f"{card1['name']} helps build storm count for {card2['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'storm'
        }

    # Multiple storm cards
    if card1_has_storm and card2_has_storm:
        return {
            'name': 'Storm Package',
            'description': f"{card1['name']} and {card2['name']} both benefit from spell velocity",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'storm'
        }

    return None


def detect_aetherflux_reservoir_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Aetherflux Reservoir synergy - life gain triggers + cast triggers
    Cards like Aetherflux Reservoir that trigger on spell casts and gain life
    """
    # Aetherflux Reservoir-like patterns
    aetherflux_patterns = [
        r'whenever you cast a spell.*gain.*life',
        r'whenever you cast.*you gain.*life',
        r'whenever you cast.*gain 1 life'
    ]

    # Life gain payoff patterns
    life_gain_payoff_patterns = [
        r'whenever you gain life',
        r'when you gain life',
        r'if you gained life',
        r'for each life gained'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card2_cmc = card2.get('cmc', 0)
    card1_cmc = card1.get('cmc', 0)

    # Check if card1 is Aetherflux-like (gains life on cast)
    card1_is_aetherflux = any(search_cached(pattern, card1_text) for pattern in aetherflux_patterns)
    card2_is_spell = 'instant' in card2_type or 'sorcery' in card2_type

    if card1_is_aetherflux and card2_is_spell:
        return {
            'name': 'Aetherflux Engine',
            'description': f"{card1['name']} gains life when casting {card2['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'storm'
        }

    # Check reverse - card2 is Aetherflux-like
    card2_is_aetherflux = any(search_cached(pattern, card2_text) for pattern in aetherflux_patterns)
    card1_is_spell = 'instant' in card1_type or 'sorcery' in card1_type

    if card2_is_aetherflux and card1_is_spell:
        return {
            'name': 'Aetherflux Engine',
            'description': f"{card2['name']} gains life when casting {card1['name']}",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'storm'
        }

    # Life gain payoff + cheap spells that trigger Aetherflux
    card1_payoff = any(search_cached(pattern, card1_text) for pattern in life_gain_payoff_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in life_gain_payoff_patterns)

    if (card1_payoff and card2_is_aetherflux) or (card2_payoff and card1_is_aetherflux):
        payoff_card = card1['name'] if card1_payoff else card2['name']
        aetherflux_card = card2['name'] if card2_is_aetherflux else card1['name']
        return {
            'name': 'Life Gain Storm',
            'description': f"{aetherflux_card} gains life on casts, {payoff_card} rewards life gain",
            'value': 5.0,
            'category': 'combo',
            'subcategory': 'storm'
        }

    return None


def detect_spell_cost_reduction(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect spell cost reduction synergies
    Cost reducers + instants/sorceries
    """
    # Cost reduction patterns
    cost_reduction_patterns = [
        r'instant.*cost.*\{[0-9]+\} less',
        r'sorcery.*cost.*\{[0-9]+\} less',
        r'instant and sorcery spells.*cost.*less',
        r'noncreature spells.*cost.*less',
        r'spells you cast.*cost.*less',
        r'instant.*cost.*\{1\} less',
        r'sorcery.*cost.*\{1\} less'
    ]

    # Flashback/graveyard cost reduction
    graveyard_cost_patterns = [
        r'you may cast.*from your graveyard',
        r'instant.*from.*graveyard',
        r'sorcery.*from.*graveyard',
        r'flashback'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 reduces costs
    card1_reduces_costs = any(search_cached(pattern, card1_text) for pattern in cost_reduction_patterns)
    card1_graveyard_casts = any(search_cached(pattern, card1_text) for pattern in graveyard_cost_patterns) or \
                           'flashback' in card1_keywords

    card2_is_spell = 'instant' in card2_type or 'sorcery' in card2_type

    if card1_reduces_costs and card2_is_spell:
        return {
            'name': 'Cost Reduction Engine',
            'description': f"{card1['name']} reduces the cost of {card2['name']}",
            'value': 3.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    if card1_graveyard_casts and card2_is_spell:
        return {
            'name': 'Graveyard Recursion',
            'description': f"{card1['name']} enables casting {card2['name']} from graveyard",
            'value': 3.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    # Check reverse
    card2_reduces_costs = any(search_cached(pattern, card2_text) for pattern in cost_reduction_patterns)
    card2_graveyard_casts = any(search_cached(pattern, card2_text) for pattern in graveyard_cost_patterns) or \
                           'flashback' in card2_keywords

    card1_is_spell = 'instant' in card1_type or 'sorcery' in card1_type

    if card2_reduces_costs and card1_is_spell:
        return {
            'name': 'Cost Reduction Engine',
            'description': f"{card2['name']} reduces the cost of {card1['name']}",
            'value': 3.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    if card2_graveyard_casts and card1_is_spell:
        return {
            'name': 'Graveyard Recursion',
            'description': f"{card2['name']} enables casting {card1['name']} from graveyard",
            'value': 3.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    return None


def detect_flashback_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect flashback/rebound synergies
    Flashback spells + cast triggers or graveyard enablers
    """
    # Flashback/rebound patterns
    flashback_patterns = [
        r'flashback',
        r'you may cast this card from your graveyard',
        r'cast.*from your graveyard'
    ]

    rebound_patterns = [
        r'rebound'
    ]

    # Graveyard enabler patterns
    graveyard_enabler_patterns = [
        r'mill',
        r'put.*into your graveyard',
        r'self-mill',
        r'discard'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Check for flashback/rebound
    card1_has_flashback = any(search_cached(pattern, card1_text) for pattern in flashback_patterns) or \
                         'flashback' in card1_keywords
    card1_has_rebound = any(search_cached(pattern, card1_text) for pattern in rebound_patterns) or \
                       'rebound' in card1_keywords

    card2_has_flashback = any(search_cached(pattern, card2_text) for pattern in flashback_patterns) or \
                         'flashback' in card2_keywords
    card2_has_rebound = any(search_cached(pattern, card2_text) for pattern in rebound_patterns) or \
                       'rebound' in card2_keywords

    # Check for graveyard enablers
    card1_enables_graveyard = any(search_cached(pattern, card1_text) for pattern in graveyard_enabler_patterns)
    card2_enables_graveyard = any(search_cached(pattern, card2_text) for pattern in graveyard_enabler_patterns)

    # Flashback spell + graveyard enabler
    if card1_has_flashback and card2_enables_graveyard:
        return {
            'name': 'Flashback Enabler',
            'description': f"{card2['name']} fills graveyard for {card1['name']}'s flashback",
            'value': 3.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    if card2_has_flashback and card1_enables_graveyard:
        return {
            'name': 'Flashback Enabler',
            'description': f"{card1['name']} fills graveyard for {card2['name']}'s flashback",
            'value': 3.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    # Rebound spell + spell triggers (double trigger value)
    spell_trigger_patterns = [
        r'whenever you cast an instant or sorcery',
        r'whenever you cast a noncreature spell',
        r'magecraft',
        r'prowess'
    ]

    card1_has_spell_trigger = any(search_cached(pattern, card1_text) for pattern in spell_trigger_patterns)
    card2_has_spell_trigger = any(search_cached(pattern, card2_text) for pattern in spell_trigger_patterns)

    if card1_has_rebound and card2_has_spell_trigger:
        return {
            'name': 'Rebound Value',
            'description': f"{card1['name']}'s rebound triggers {card2['name']} twice",
            'value': 4.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    if card2_has_rebound and card1_has_spell_trigger:
        return {
            'name': 'Rebound Value',
            'description': f"{card2['name']}'s rebound triggers {card1['name']} twice",
            'value': 4.0,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    return None


def detect_cantrip_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect cantrip synergies
    Cheap card draw spells + spell triggers
    """
    # Cantrip patterns (cheap spells that draw cards)
    cantrip_patterns = [
        r'draw a card',
        r'draw two cards',
        r'scry.*draw'
    ]

    # Spell velocity patterns (care about casting multiple spells)
    spell_velocity_patterns = [
        r'whenever you cast an instant or sorcery',
        r'whenever you cast a noncreature spell',
        r'magecraft',
        r'prowess',
        r'storm',
        r'for each spell cast'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 999)
    card2_cmc = card2.get('cmc', 999)
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Check if card1 is a cantrip
    card1_is_cantrip = (card1_cmc <= 2) and \
                      ('instant' in card1_type or 'sorcery' in card1_type) and \
                      any(search_cached(pattern, card1_text) for pattern in cantrip_patterns)

    # Check if card2 cares about spell velocity
    card2_spell_velocity = any(search_cached(pattern, card2_text) for pattern in spell_velocity_patterns) or \
                          any(kw in card2_keywords for kw in ['prowess', 'storm'])

    if card1_is_cantrip and card2_spell_velocity:
        return {
            'name': 'Cantrip Engine',
            'description': f"{card1['name']} fuels {card2['name']}'s spell triggers while maintaining card advantage",
            'value': 4.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    # Check reverse
    card2_is_cantrip = (card2_cmc <= 2) and \
                      ('instant' in card2_type or 'sorcery' in card2_type) and \
                      any(search_cached(pattern, card2_text) for pattern in cantrip_patterns)

    card1_spell_velocity = any(search_cached(pattern, card1_text) for pattern in spell_velocity_patterns) or \
                          any(kw in card1_keywords for kw in ['prowess', 'storm'])

    if card2_is_cantrip and card1_spell_velocity:
        return {
            'name': 'Cantrip Engine',
            'description': f"{card2['name']} fuels {card1['name']}'s spell triggers while maintaining card advantage",
            'value': 4.5,
            'category': 'type_synergy',
            'subcategory': 'instant_sorcery_matters'
        }

    return None


def detect_energy_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect energy synergy - energy generation + energy consumption
    """
    # Energy generation patterns
    energy_generation_patterns = [
        r'get \{e\}',
        r'you get.*\{e\}',
        r'get.*energy counter'
    ]

    # Energy consumption patterns
    energy_consumption_patterns = [
        r'pay \{e\}',
        r'pay.*\{e\}',
        r'spend energy',
        r'if you have.*\{e\}'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check for energy generation and consumption
    card1_generates_energy = any(search_cached(pattern, card1_text) for pattern in energy_generation_patterns)
    card2_generates_energy = any(search_cached(pattern, card2_text) for pattern in energy_generation_patterns)

    card1_consumes_energy = any(search_cached(pattern, card1_text) for pattern in energy_consumption_patterns)
    card2_consumes_energy = any(search_cached(pattern, card2_text) for pattern in energy_consumption_patterns)

    # Energy generation + consumption
    if card1_generates_energy and card2_consumes_energy:
        return {
            'name': 'Energy Synergy',
            'description': f"{card1['name']} generates energy for {card2['name']} to use",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'energy'
        }

    if card2_generates_energy and card1_consumes_energy:
        return {
            'name': 'Energy Synergy',
            'description': f"{card2['name']} generates energy for {card1['name']} to use",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'energy'
        }

    # Card that both generates and consumes
    if (card1_generates_energy and card1_consumes_energy and card2_generates_energy) or \
       (card2_generates_energy and card2_consumes_energy and card1_generates_energy):
        return {
            'name': 'Energy Package',
            'description': f"{card1['name']} and {card2['name']} work together in energy strategy",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'energy'
        }

    return None


def detect_stax_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect stax/tax effects synergy - tax effects + low CMC cards or tax payoffs
    """
    # Tax effect patterns
    tax_patterns = [
        r'costs? \{[0-9]+\} more to cast',
        r'costs? \{[0-9]+\} more to activate',
        r'players? can\'t cast',
        r'opponents? can\'t activate',
        r'spells? cost.*more to cast',
        r'whenever an opponent casts',
        r'sacrifice.*unless.*pay',
        r'players? can\'t search',
        r'players? can\'t draw',
        r'as.*enters.*unless.*pay'
    ]

    # Tax payoff patterns (you benefit from opponent's spells/mana spending)
    tax_payoff_patterns = [
        r'whenever an opponent casts.*draw',
        r'whenever an opponent casts.*create',
        r'whenever an opponent casts.*deal',
        r'whenever a player pays'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_cmc = card1.get('cmc', 999)
    card2_cmc = card2.get('cmc', 999)

    # Check for tax effects
    card1_is_tax = any(search_cached(pattern, card1_text) for pattern in tax_patterns)
    card2_is_tax = any(search_cached(pattern, card2_text) for pattern in tax_patterns)

    # Check for tax payoffs
    card1_is_payoff = any(search_cached(pattern, card1_text) for pattern in tax_payoff_patterns)
    card2_is_payoff = any(search_cached(pattern, card2_text) for pattern in tax_payoff_patterns)

    # Tax effect + tax payoff
    if card1_is_tax and card2_is_payoff:
        return {
            'name': 'Stax Payoff',
            'description': f"{card1['name']} taxes opponents while {card2['name']} benefits",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'stax'
        }

    if card2_is_tax and card1_is_payoff:
        return {
            'name': 'Stax Payoff',
            'description': f"{card2['name']} taxes opponents while {card1['name']} benefits",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'stax'
        }

    # Multiple tax effects (stax package)
    if card1_is_tax and card2_is_tax:
        return {
            'name': 'Stax Package',
            'description': f"{card1['name']} and {card2['name']} both tax opponents",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'stax'
        }

    # Tax effect + very low CMC cards (asymmetric benefit)
    if card1_is_tax and card2_cmc <= 2:
        return {
            'name': 'Asymmetric Stax',
            'description': f"{card1['name']} taxes opponents while {card2['name']}'s low cost avoids tax",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'stax'
        }

    if card2_is_tax and card1_cmc <= 2:
        return {
            'name': 'Asymmetric Stax',
            'description': f"{card2['name']} taxes opponents while {card1['name']}'s low cost avoids tax",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'stax'
        }

    return None


def detect_sacrifice_outlet_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect synergies between free sacrifice outlets and sacrifice payoffs
    """
    sac_outlet_patterns = [
        r'sacrifice.*:',
        r'sacrifice.*as an additional cost',
        r'you may sacrifice',
        r'sacrifice a creature'
    ]

    sac_payoff_patterns = [
        r'whenever.*you sacrifice',
        r'whenever.*is put into.*graveyard from the battlefield',
        r'when.*dies'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_outlet = any(search_cached(pattern, card1_text) for pattern in sac_outlet_patterns)
    card2_outlet = any(search_cached(pattern, card2_text) for pattern in sac_outlet_patterns)
    card1_payoff = any(search_cached(pattern, card1_text) for pattern in sac_payoff_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in sac_payoff_patterns)

    if card1_outlet and card2_payoff:
        return {
            'name': 'Sacrifice Engine',
            'description': f"{card1['name']} provides sacrifice outlet for {card2['name']}'s death triggers",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'sacrifice'
        }

    if card2_outlet and card1_payoff:
        return {
            'name': 'Sacrifice Engine',
            'description': f"{card2['name']} provides sacrifice outlet for {card1['name']}'s death triggers",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'sacrifice'
        }

    return None


def detect_blink_etb_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect flicker/blink effects with strong ETB creatures
    """
    blink_patterns = [
        r'exile.*return.*battlefield',
        r'\bblink\b',
        r'\bflicker\b'
    ]

    strong_etb_patterns = [
        r'when.*enters.*draw',
        r'when.*enters.*destroy',
        r'when.*enters.*exile',
        r'when.*enters.*create.*token',
        r'when.*enters.*return.*from.*graveyard'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_blink = any(search_cached(pattern, card1_text) for pattern in blink_patterns)
    card2_blink = any(search_cached(pattern, card2_text) for pattern in blink_patterns)
    card1_etb = any(search_cached(pattern, card1_text) for pattern in strong_etb_patterns)
    card2_etb = any(search_cached(pattern, card2_text) for pattern in strong_etb_patterns)

    if (card1_blink and card2_etb) or (card2_blink and card1_etb):
        return {
            'name': 'Blink Value',
            'description': f"Blinking {card2['name'] if card1_blink else card1['name']} generates repeated value",
            'value': 4.0,
            'category': 'combo',
            'subcategory': 'etb'
        }

    return None


def detect_proliferate_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect proliferate with counters/poison/planeswalkers
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_proliferate = 'proliferate' in card1_text
    card2_proliferate = 'proliferate' in card2_text

    counter_patterns = [
        r'\+1/\+1 counter',
        r'poison counter',
        r'loyalty counter',
        r'charge counter',
        r'experience counter'
    ]

    card1_counters = any(pattern in card1_text for pattern in counter_patterns) or 'planeswalker' in card1.get('type_line', '').lower()
    card2_counters = any(pattern in card2_text for pattern in counter_patterns) or 'planeswalker' in card2.get('type_line', '').lower()

    if card1_proliferate and card2_counters:
        return {
            'name': 'Proliferate Synergy',
            'description': f"{card1['name']} proliferates {card2['name']}'s counters",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'counters'
        }

    if card2_proliferate and card1_counters:
        return {
            'name': 'Proliferate Synergy',
            'description': f"{card2['name']} proliferates {card1['name']}'s counters",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'counters'
        }

    return None


def detect_infect_damage_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect infect/poison with damage doubling or direct damage
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_infect = 'infect' in card1_text or 'poison counter' in card1_text or 'poisonous' in card1_text
    card2_infect = 'infect' in card2_text or 'poison counter' in card2_text or 'poisonous' in card2_text

    damage_double_patterns = [
        r'double.*damage',
        r'deals double',
        r'deals.*twice'
    ]

    card1_double = any(search_cached(pattern, card1_text) for pattern in damage_double_patterns)
    card2_double = any(search_cached(pattern, card2_text) for pattern in damage_double_patterns)

    if (card1_infect and card2_double) or (card2_infect and card1_double):
        return {
            'name': 'Poison Amplifier',
            'description': f"Doubling poison counters for faster kills",
            'value': 4.5,
            'category': 'combo',
            'subcategory': 'infect'
        }

    return None


def detect_mill_self_payoff(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect self-mill with graveyard payoffs like threshold/delirium
    """
    mill_self_patterns = [
        r'mill.*yourself',
        r'put.*top.*cards.*library.*graveyard',
        r'surveil',
        r'dredge'
    ]

    graveyard_count_patterns = [
        r'threshold',
        r'delirium',
        r'undergrowth',
        r'cards in your graveyard'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_self_mill = any(search_cached(pattern, card1_text) for pattern in mill_self_patterns)
    card2_self_mill = any(search_cached(pattern, card2_text) for pattern in mill_self_patterns)
    card1_gy_count = any(pattern in card1_text for pattern in graveyard_count_patterns)
    card2_gy_count = any(pattern in card2_text for pattern in graveyard_count_patterns)

    if card1_self_mill and card2_gy_count:
        return {
            'name': 'Self-Mill Payoff',
            'description': f"{card1['name']} fills graveyard for {card2['name']}'s ability",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'graveyard'
        }

    if card2_self_mill and card1_gy_count:
        return {
            'name': 'Self-Mill Payoff',
            'description': f"{card2['name']} fills graveyard for {card1['name']}'s ability",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'graveyard'
        }

    return None


def detect_flash_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect flash enablers with powerful instants/creatures
    """
    flash_grant_patterns = [
        r'you may cast.*as though.*had flash',
        r'flash to',
        r'creatures you control have flash',
        r'may cast.*any time'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_grants_flash = any(search_cached(pattern, card1_text) for pattern in flash_grant_patterns)
    card2_grants_flash = any(search_cached(pattern, card2_text) for pattern in flash_grant_patterns)

    # Check if the other card would benefit from flash
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # High CMC creatures or sorceries benefit from flash
    if card1_grants_flash and ('creature' in card2_type or 'sorcery' in card2_type) and card2_cmc >= 4:
        return {
            'name': 'Flash Enabler',
            'description': f"{card1['name']} lets you cast {card2['name']} at instant speed",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'flash'
        }

    if card2_grants_flash and ('creature' in card1_type or 'sorcery' in card1_type) and card1_cmc >= 4:
        return {
            'name': 'Flash Enabler',
            'description': f"{card2['name']} lets you cast {card1['name']} at instant speed",
            'value': 3.0,
            'category': 'role_interaction',
            'subcategory': 'flash'
        }

    return None


def detect_haste_enabler_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect haste enablers with high-power creatures
    """
    haste_grant_patterns = [
        r'creatures you control have haste',
        r'gains haste',
        r'has haste'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    card1_grants_haste = any(search_cached(pattern, card1_text) for pattern in haste_grant_patterns)
    card2_grants_haste = any(search_cached(pattern, card2_text) for pattern in haste_grant_patterns)

    card1_power = card1.get('power', '')
    card2_power = card2.get('power', '')

    # Check for high power creatures
    try:
        if card1_grants_haste and 'creature' in card2_type and card2_power and int(card2_power) >= 4:
            return {
                'name': 'Haste Enabler',
                'description': f"{card1['name']} gives {card2['name']} immediate impact",
                'value': 2.5,
                'category': 'role_interaction',
                'subcategory': 'haste'
            }
    except (ValueError, TypeError):
        pass

    try:
        if card2_grants_haste and 'creature' in card1_type and card1_power and int(card1_power) >= 4:
            return {
                'name': 'Haste Enabler',
                'description': f"{card2['name']} gives {card1['name']} immediate impact",
                'value': 2.5,
                'category': 'role_interaction',
                'subcategory': 'haste'
            }
    except (ValueError, TypeError):
        pass

    return None


def detect_vigilance_tap_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect vigilance with tap abilities
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    vigilance_patterns = [r'\bvigilance\b', r'doesn\'t tap', r'attacks each combat if able']
    tap_ability_patterns = [r'{t}:', r'tap.*:']

    card1_vigilance = any(search_cached(pattern, card1_text) for pattern in vigilance_patterns)
    card2_vigilance = any(search_cached(pattern, card2_text) for pattern in vigilance_patterns)
    card1_tap_ability = any(search_cached(pattern, card1_text) for pattern in tap_ability_patterns)
    card2_tap_ability = any(search_cached(pattern, card2_text) for pattern in tap_ability_patterns)

    if card1_vigilance and card1_tap_ability:
        return {
            'name': 'Vigilance Value',
            'description': f"{card1['name']} can attack and still use tap ability",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'vigilance'
        }

    if card2_vigilance and card2_tap_ability:
        return {
            'name': 'Vigilance Value',
            'description': f"{card2['name']} can attack and still use tap ability",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'vigilance'
        }

    return None


def detect_hexproof_aura_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect hexproof/shroud with auras/equipment for voltron
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    protection_keywords = [r'\bhexproof\b', r'\bshroud\b', r'protection from', r'\bward\b']

    card1_protected = any(search_cached(pattern, card1_text) for pattern in protection_keywords)
    card2_protected = any(search_cached(pattern, card2_text) for pattern in protection_keywords)

    card1_is_aura = 'aura' in card1_type or 'equipment' in card1_type
    card2_is_aura = 'aura' in card2_type or 'equipment' in card2_type

    if card1_protected and card2_is_aura and 'creature' in card1_type:
        return {
            'name': 'Protected Voltron',
            'description': f"{card1['name']} is protected while being enhanced by {card2['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'voltron'
        }

    if card2_protected and card1_is_aura and 'creature' in card2_type:
        return {
            'name': 'Protected Voltron',
            'description': f"{card2['name']} is protected while being enhanced by {card1['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'voltron'
        }

    return None


def detect_trample_pump_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect trample with pump spells for damage
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_trample = 'trample' in card1_text or 'trample' in card1.get('keywords', [])
    card2_trample = 'trample' in card2_text or 'trample' in card2.get('keywords', [])

    pump_patterns = [
        r'gets \+[0-9]+/\+[0-9]+',
        r'target creature gets',
        r'enchanted creature gets \+[0-9]+/\+[0-9]+'
    ]

    card1_pump = any(search_cached(pattern, card1_text) for pattern in pump_patterns)
    card2_pump = any(search_cached(pattern, card2_text) for pattern in pump_patterns)

    if card1_trample and card2_pump:
        return {
            'name': 'Trample Pump',
            'description': f"Pumping {card1['name']} with trample for massive damage",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'combat'
        }

    if card2_trample and card1_pump:
        return {
            'name': 'Trample Pump',
            'description': f"Pumping {card2['name']} with trample for massive damage",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'combat'
        }

    return None


def detect_lifelink_damage_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect lifelink with damage multiplication
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_lifelink = 'lifelink' in card1_text or 'lifelink' in card1.get('keywords', [])
    card2_lifelink = 'lifelink' in card2_text or 'lifelink' in card2.get('keywords', [])

    damage_mult_patterns = [
        r'double.*damage',
        r'deals double',
        r'additional.*damage'
    ]

    card1_mult = any(search_cached(pattern, card1_text) for pattern in damage_mult_patterns)
    card2_mult = any(search_cached(pattern, card2_text) for pattern in damage_mult_patterns)

    if card1_lifelink and card2_mult:
        return {
            'name': 'Lifelink Multiplier',
            'description': f"Multiplying {card1['name']}'s lifelink damage for massive lifegain",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'lifegain'
        }

    if card2_lifelink and card1_mult:
        return {
            'name': 'Lifelink Multiplier',
            'description': f"Multiplying {card2['name']}'s lifelink damage for massive lifegain",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'lifegain'
        }

    return None


def detect_flying_evasion_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect flying matters cards with flying creatures
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    flying_matters_patterns = [
        r'flying.*you control',
        r'whenever.*flying.*deals',
        r'creatures with flying you control get'
    ]

    card1_flying_matters = any(search_cached(pattern, card1_text) for pattern in flying_matters_patterns)
    card2_flying_matters = any(search_cached(pattern, card2_text) for pattern in flying_matters_patterns)

    card1_flying = 'flying' in card1_text or 'flying' in card1.get('keywords', [])
    card2_flying = 'flying' in card2_text or 'flying' in card2.get('keywords', [])

    if card1_flying_matters and card2_flying:
        return {
            'name': 'Flying Tribal',
            'description': f"{card1['name']} rewards {card2['name']}'s flying",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'tribal'
        }

    if card2_flying_matters and card1_flying:
        return {
            'name': 'Flying Tribal',
            'description': f"{card2['name']} rewards {card1['name']}'s flying",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'tribal'
        }

    return None


def detect_menace_token_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect menace/unblockable with go-wide token strategies
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    evasion_keywords = ['menace', 'unblockable', 'can\'t be blocked']

    card1_evasion = any(keyword in card1_text for keyword in evasion_keywords)
    card2_evasion = any(keyword in card2_text for keyword in evasion_keywords)

    token_gen_patterns = [r'create.*token', r'create.*\d+/\d+']

    card1_tokens = any(search_cached(pattern, card1_text) for pattern in token_gen_patterns)
    card2_tokens = any(search_cached(pattern, card2_text) for pattern in token_gen_patterns)

    if card1_evasion and card2_tokens:
        return {
            'name': 'Evasive Tokens',
            'description': f"{card1['name']}'s evasion makes {card2['name']}'s tokens hard to block",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'tokens'
        }

    if card2_evasion and card1_tokens:
        return {
            'name': 'Evasive Tokens',
            'description': f"{card2['name']}'s evasion makes {card1['name']}'s tokens hard to block",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'tokens'
        }

    return None


def detect_first_strike_damage_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect first strike with deathtouch or high power
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    first_strike_keywords = ['first strike', 'double strike']

    card1_first_strike = any(keyword in card1_text for keyword in first_strike_keywords)
    card2_first_strike = any(keyword in card2_text for keyword in first_strike_keywords)

    card1_deathtouch = 'deathtouch' in card1_text
    card2_deathtouch = 'deathtouch' in card2_text

    if (card1_first_strike and card2_deathtouch) or (card2_first_strike and card1_deathtouch):
        return {
            'name': 'First Strike Deathtouch',
            'description': f"First strike + deathtouch kills blockers before damage",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'combat'
        }

    return None


def detect_planeswalker_proliferate_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect planeswalkers with proliferate engines
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_walker = 'planeswalker' in card1_type
    card2_walker = 'planeswalker' in card2_type

    card1_proliferate = 'proliferate' in card1_text
    card2_proliferate = 'proliferate' in card2_text

    if card1_walker and card2_proliferate:
        return {
            'name': 'Superfriends Proliferate',
            'description': f"{card2['name']} accelerates {card1['name']}'s loyalty",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'planeswalker'
        }

    if card2_walker and card1_proliferate:
        return {
            'name': 'Superfriends Proliferate',
            'description': f"{card1['name']} accelerates {card2['name']}'s loyalty",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'planeswalker'
        }

    return None


def detect_planeswalker_protection_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect planeswalkers with creature protection (blockers/fogs)
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_walker = 'planeswalker' in card1_type
    card2_walker = 'planeswalker' in card2_type

    protection_patterns = [
        r'prevent all combat damage',
        r'creatures can\'t attack',
        r'defender',
        r'fog'
    ]

    card1_protection = any(search_cached(pattern, card1_text) for pattern in protection_patterns) or ('creature' in card1_type and 'defender' in card1.get('keywords', []))
    card2_protection = any(search_cached(pattern, card2_text) for pattern in protection_patterns) or ('creature' in card2_type and 'defender' in card2.get('keywords', []))

    if card1_walker and card2_protection:
        return {
            'name': 'Walker Protection',
            'description': f"{card2['name']} protects {card1['name']} from attacks",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'planeswalker'
        }

    if card2_walker and card1_protection:
        return {
            'name': 'Walker Protection',
            'description': f"{card1['name']} protects {card2['name']} from attacks",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'planeswalker'
        }

    return None


def detect_commander_damage_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect commander damage enablers with power boosts
    """
    pump_patterns = [
        r'gets \+[3-9]/\+[0-9]',
        r'double.*power',
        r'power equal to'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_pump = any(search_cached(pattern, card1_text) for pattern in pump_patterns)
    card2_pump = any(search_cached(pattern, card2_text) for pattern in pump_patterns)

    # Check if either is legendary creature (potential commander)
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    card1_commander = 'legendary' in card1_type and 'creature' in card1_type
    card2_commander = 'legendary' in card2_type and 'creature' in card2_type

    if card1_commander and card2_pump:
        return {
            'name': 'Commander Damage',
            'description': f"{card2['name']} enables faster commander damage kills with {card1['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'voltron'
        }

    if card2_commander and card1_pump:
        return {
            'name': 'Commander Damage',
            'description': f"{card1['name']} enables faster commander damage kills with {card2['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'voltron'
        }

    return None


def detect_untap_land_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect land untap effects with utility lands
    """
    untap_land_patterns = [
        r'untap.*land',
        r'untap up to',
        r'untap target land'
    ]

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    card1_untaps = any(search_cached(pattern, card1_text) for pattern in untap_land_patterns)
    card2_untaps = any(search_cached(pattern, card2_text) for pattern in untap_land_patterns)

    # Check for utility lands with tap abilities
    tap_ability = r'{t}:.*(?:add|draw|create|deal)'

    card1_utility = 'land' in card1_type and search_cached(tap_ability, card1_text)
    card2_utility = 'land' in card2_type and search_cached(tap_ability, card2_text)

    if card1_untaps and card2_utility:
        return {
            'name': 'Land Untap Engine',
            'description': f"{card1['name']} untaps {card2['name']} for extra value",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'ramp'
        }

    if card2_untaps and card1_utility:
        return {
            'name': 'Land Untap Engine',
            'description': f"{card2['name']} untaps {card1['name']} for extra value",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'ramp'
        }

    return None


def detect_fetch_land_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect fetchlands with landfall triggers
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Fetch land pattern
    fetch_pattern = r'search.*library.*land.*battlefield'

    card1_fetch = 'land' in card1_type and search_cached(fetch_pattern, card1_text)
    card2_fetch = 'land' in card2_type and search_cached(fetch_pattern, card2_text)

    # Landfall pattern
    landfall_pattern = r'landfall|whenever.*land enters'

    card1_landfall = search_cached(landfall_pattern, card1_text)
    card2_landfall = search_cached(landfall_pattern, card2_text)

    if card1_fetch and card2_landfall:
        return {
            'name': 'Fetch Landfall',
            'description': f"{card1['name']} triggers {card2['name']}'s landfall twice",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'landfall'
        }

    if card2_fetch and card1_landfall:
        return {
            'name': 'Fetch Landfall',
            'description': f"{card2['name']} triggers {card1['name']}'s landfall twice",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'landfall'
        }

    return None


def detect_artifact_sac_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect artifact sacrifice outlets with artifact death triggers
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    artifact_sac_patterns = [
        r'sacrifice.*artifact:',
        r'sacrifice an artifact'
    ]

    artifact_death_patterns = [
        r'whenever.*artifact.*put into.*graveyard',
        r'whenever you sacrifice.*artifact',
        r'whenever an artifact.*dies'
    ]

    card1_sac = any(search_cached(pattern, card1_text) for pattern in artifact_sac_patterns)
    card2_sac = any(search_cached(pattern, card2_text) for pattern in artifact_sac_patterns)
    card1_payoff = any(search_cached(pattern, card1_text) for pattern in artifact_death_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in artifact_death_patterns)

    if card1_sac and card2_payoff:
        return {
            'name': 'Artifact Sacrifice Engine',
            'description': f"{card1['name']} sacrifices artifacts to trigger {card2['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_sac and card1_payoff:
        return {
            'name': 'Artifact Sacrifice Engine',
            'description': f"{card2['name']} sacrifices artifacts to trigger {card1['name']}",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_enchantment_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect enchantment matters cards with enchantments
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    enchantment_matters_patterns = [
        r'enchantments you control',
        r'whenever.*enchantment enters',
        r'whenever you cast.*enchantment'
    ]

    card1_matters = any(search_cached(pattern, card1_text) for pattern in enchantment_matters_patterns)
    card2_matters = any(search_cached(pattern, card2_text) for pattern in enchantment_matters_patterns)

    card1_is_enchantment = 'enchantment' in card1_type
    card2_is_enchantment = 'enchantment' in card2_type

    if card1_matters and card2_is_enchantment:
        return {
            'name': 'Enchantment Synergy',
            'description': f"{card1['name']} rewards playing {card2['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'enchantments'
        }

    if card2_matters and card1_is_enchantment:
        return {
            'name': 'Enchantment Synergy',
            'description': f"{card2['name']} rewards playing {card1['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'enchantments'
        }

    return None


def detect_saga_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect saga doublers or saga proliferate
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_saga = 'saga' in card1_type
    card2_saga = 'saga' in card2_type

    saga_synergy_patterns = [
        r'proliferate',
        r'chapter abilities.*trigger.*additional time',
        r'lore counter'
    ]

    card1_synergy = any(search_cached(pattern, card1_text) for pattern in saga_synergy_patterns)
    card2_synergy = any(search_cached(pattern, card2_text) for pattern in saga_synergy_patterns)

    if card1_saga and card2_synergy:
        return {
            'name': 'Saga Accelerator',
            'description': f"{card2['name']} accelerates or doubles {card1['name']}'s chapters",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    if card2_saga and card1_synergy:
        return {
            'name': 'Saga Accelerator',
            'description': f"{card1['name']} accelerates or doubles {card2['name']}'s chapters",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    return None


def detect_room_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect room cards with bounce/flicker effects
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Room is a newer card type (Duskmourn)
    card1_room = 'room' in card1_type
    card2_room = 'room' in card2_type

    bounce_patterns = [
        r'return.*to.*hand',
        r'bounce'
    ]

    card1_bounce = any(search_cached(pattern, card1_text) for pattern in bounce_patterns)
    card2_bounce = any(search_cached(pattern, card2_text) for pattern in bounce_patterns)

    if card1_room and card2_bounce:
        return {
            'name': 'Room Reset',
            'description': f"{card2['name']} bounces {card1['name']} to unlock different doors",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    if card2_room and card1_bounce:
        return {
            'name': 'Room Reset',
            'description': f"{card1['name']} bounces {card2['name']} to unlock different doors",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    return None


def detect_vehicle_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect vehicles with token generators or creatures
    """
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_vehicle = 'vehicle' in card1_type
    card2_vehicle = 'vehicle' in card2_type

    crew_enabler_patterns = [
        r'create.*token.*creature',
        r'servo',
        r'myr'
    ]

    card1_enabler = any(search_cached(pattern, card1_text) for pattern in crew_enabler_patterns) or 'creature' in card1_type
    card2_enabler = any(search_cached(pattern, card2_text) for pattern in crew_enabler_patterns) or 'creature' in card2_type

    if card1_vehicle and card2_enabler:
        return {
            'name': 'Vehicle Crew',
            'description': f"{card2['name']} crews {card1['name']}",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'artifacts'
        }

    if card2_vehicle and card1_enabler:
        return {
            'name': 'Vehicle Crew',
            'description': f"{card1['name']} crews {card2['name']}",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'artifacts'
        }

    return None


def detect_food_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect food token generation with sacrifice payoffs
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_food = 'food' in card1_text
    card2_food = 'food' in card2_text

    artifact_sac_matters = [
        r'whenever you sacrifice.*artifact',
        r'artifacts you control',
        r'artifact.*enters'
    ]

    card1_matters = any(search_cached(pattern, card1_text) for pattern in artifact_sac_matters)
    card2_matters = any(search_cached(pattern, card2_text) for pattern in artifact_sac_matters)

    if card1_food and card2_matters:
        return {
            'name': 'Food Synergy',
            'description': f"{card1['name']}'s food tokens synergize with {card2['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_food and card1_matters:
        return {
            'name': 'Food Synergy',
            'description': f"{card2['name']}'s food tokens synergize with {card1['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_blood_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect blood token generation with discard payoffs
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_blood = 'blood' in card1_text
    card2_blood = 'blood' in card2_text

    discard_matters_patterns = [
        r'whenever you discard',
        r'madness',
        r'when.*discarded'
    ]

    card1_matters = any(search_cached(pattern, card1_text) for pattern in discard_matters_patterns)
    card2_matters = any(search_cached(pattern, card2_text) for pattern in discard_matters_patterns)

    if card1_blood and card2_matters:
        return {
            'name': 'Blood Discard',
            'description': f"{card1['name']}'s blood tokens enable {card2['name']}'s discard payoffs",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'discard'
        }

    if card2_blood and card1_matters:
        return {
            'name': 'Blood Discard',
            'description': f"{card2['name']}'s blood tokens enable {card1['name']}'s discard payoffs",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'discard'
        }

    return None


def detect_investigate_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect investigate with clue/artifact payoffs
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_investigate = 'investigate' in card1_text or 'clue' in card1_text
    card2_investigate = 'investigate' in card2_text or 'clue' in card2_text

    artifact_payoff_patterns = [
        r'whenever.*artifact enters',
        r'artifacts you control',
        r'affinity'
    ]

    card1_payoff = any(search_cached(pattern, card1_text) for pattern in artifact_payoff_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in artifact_payoff_patterns)

    if card1_investigate and card2_payoff:
        return {
            'name': 'Investigate Payoff',
            'description': f"{card1['name']}'s clues trigger {card2['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_investigate and card1_payoff:
        return {
            'name': 'Investigate Payoff',
            'description': f"{card2['name']}'s clues trigger {card1['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_role_token_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect role token generation with aura/enchantment synergies
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Role tokens are enchantment tokens (Wilds of Eldraine)
    role_patterns = [r'\brole\b', r'role token']

    card1_role = any(search_cached(pattern, card1_text) for pattern in role_patterns)
    card2_role = any(search_cached(pattern, card2_text) for pattern in role_patterns)

    enchantment_matters = [
        r'whenever.*enchantment enters',
        r'enchantments you control',
        r'constellation'
    ]

    card1_matters = any(search_cached(pattern, card1_text) for pattern in enchantment_matters)
    card2_matters = any(search_cached(pattern, card2_text) for pattern in enchantment_matters)

    if card1_role and card2_matters:
        return {
            'name': 'Role Enchantment Synergy',
            'description': f"{card1['name']}'s roles trigger {card2['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    if card2_role and card1_matters:
        return {
            'name': 'Role Enchantment Synergy',
            'description': f"{card2['name']}'s roles trigger {card1['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'enchantments'
        }

    return None


def detect_bargain_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect bargain with treasure/artifact generation
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_bargain = 'bargain' in card1_text
    card2_bargain = 'bargain' in card2_text

    artifact_token_patterns = [
        r'treasure',
        r'create.*artifact.*token',
        r'food',
        r'clue'
    ]

    card1_artifacts = any(pattern in card1_text for pattern in artifact_token_patterns)
    card2_artifacts = any(pattern in card2_text for pattern in artifact_token_patterns)

    if card1_bargain and card2_artifacts:
        return {
            'name': 'Bargain Enabler',
            'description': f"{card2['name']} creates artifacts to enable {card1['name']}'s bargain",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_bargain and card1_artifacts:
        return {
            'name': 'Bargain Enabler',
            'description': f"{card1['name']} creates artifacts to enable {card2['name']}'s bargain",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_modified_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect modified matters with auras/equipment/counters
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    modified_matters_patterns = [
        r'modified',
        r'equipped.*you control',
        r'enchanted creatures you control'
    ]

    card1_matters = any(search_cached(pattern, card1_text) for pattern in modified_matters_patterns)
    card2_matters = any(search_cached(pattern, card2_text) for pattern in modified_matters_patterns)

    modifier_patterns = [
        r'equipment',
        r'aura',
        r'\+1/\+1 counter',
        r'attach'
    ]

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    card1_modifier = any(pattern in card1_text for pattern in modifier_patterns) or 'equipment' in card1_type or 'aura' in card1_type
    card2_modifier = any(pattern in card2_text for pattern in modifier_patterns) or 'equipment' in card2_type or 'aura' in card2_type

    if card1_matters and card2_modifier:
        return {
            'name': 'Modified Synergy',
            'description': f"{card2['name']} modifies creatures for {card1['name']}'s payoff",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'equipment'
        }

    if card2_matters and card1_modifier:
        return {
            'name': 'Modified Synergy',
            'description': f"{card1['name']} modifies creatures for {card2['name']}'s payoff",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'equipment'
        }

    return None


def detect_ninjutsu_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect ninjutsu with unblockable creatures
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_ninjutsu = 'ninjutsu' in card1_text
    card2_ninjutsu = 'ninjutsu' in card2_text

    evasion_patterns = [
        r'unblockable',
        r'can\'t be blocked',
        r'flying',
        r'shadow',
        r'horsemanship'
    ]

    card1_evasion = any(search_cached(pattern, card1_text) for pattern in evasion_patterns)
    card2_evasion = any(search_cached(pattern, card2_text) for pattern in evasion_patterns)

    if card1_ninjutsu and card2_evasion:
        return {
            'name': 'Ninjutsu Enabler',
            'description': f"{card2['name']}'s evasion enables {card1['name']}'s ninjutsu",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'tribal'
        }

    if card2_ninjutsu and card1_evasion:
        return {
            'name': 'Ninjutsu Enabler',
            'description': f"{card1['name']}'s evasion enables {card2['name']}'s ninjutsu",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'tribal'
        }

    return None


def detect_mutate_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect mutate with ETB or mutation payoffs
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_mutate = 'mutate' in card1_text
    card2_mutate = 'mutate' in card2_text

    mutate_payoff_patterns = [
        r'whenever.*mutates',
        r'when.*enters.*draw',
        r'whenever.*creature enters'
    ]

    card1_payoff = any(search_cached(pattern, card1_text) for pattern in mutate_payoff_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in mutate_payoff_patterns)

    if card1_mutate and card2_payoff:
        return {
            'name': 'Mutate Synergy',
            'description': f"{card1['name']}'s mutate triggers {card2['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'mutate'
        }

    if card2_mutate and card1_payoff:
        return {
            'name': 'Mutate Synergy',
            'description': f"{card2['name']}'s mutate triggers {card1['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'mutate'
        }

    return None


def detect_companion_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect companion restriction synergy with deck building
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # This is a weak detection - companions have specific deck building restrictions
    card1_companion = 'companion' in card1_text
    card2_companion = 'companion' in card2_text

    if card1_companion or card2_companion:
        # This is tricky without full deck context
        # Basic detection for now
        return {
            'name': 'Companion Synergy',
            'description': f"Cards work within companion restrictions",
            'value': 1.5,
            'category': 'role_interaction',
            'subcategory': 'companion'
        }

    return None


def detect_party_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect party mechanics with Cleric/Rogue/Warrior/Wizard
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    party_matters = 'party' in card1_text or 'party' in card2_text

    party_types = ['cleric', 'rogue', 'warrior', 'wizard']

    card1_party_member = any(ptype in card1_type for ptype in party_types)
    card2_party_member = any(ptype in card2_type for ptype in party_types)

    if party_matters and (card1_party_member or card2_party_member):
        return {
            'name': 'Party Member',
            'description': f"Party synergy between cards",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'tribal'
        }

    return None


def detect_foretell_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect foretell with cost reduction or extra value
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_foretell = 'foretell' in card1_text
    card2_foretell = 'foretell' in card2_text

    exile_matters_patterns = [
        r'whenever.*exile',
        r'cards in exile',
        r'cast.*from exile'
    ]

    card1_exile = any(search_cached(pattern, card1_text) for pattern in exile_matters_patterns)
    card2_exile = any(search_cached(pattern, card2_text) for pattern in exile_matters_patterns)

    if card1_foretell and card2_exile:
        return {
            'name': 'Foretell Payoff',
            'description': f"{card1['name']}'s foretell synergizes with {card2['name']}'s exile matters",
            'value': 2.0,
            'category': 'combo',
            'subcategory': 'exile'
        }

    if card2_foretell and card1_exile:
        return {
            'name': 'Foretell Payoff',
            'description': f"{card2['name']}'s foretell synergizes with {card1['name']}'s exile matters",
            'value': 2.0,
            'category': 'combo',
            'subcategory': 'exile'
        }

    return None


def detect_boast_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect boast with untap effects
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_boast = 'boast' in card1_text
    card2_boast = 'boast' in card2_text

    untap_creature_patterns = [
        r'untap.*creature',
        r'untap all creatures',
        r'vigilance'
    ]

    card1_untap = any(search_cached(pattern, card1_text) for pattern in untap_creature_patterns)
    card2_untap = any(search_cached(pattern, card2_text) for pattern in untap_creature_patterns)

    if card1_boast and card2_untap:
        return {
            'name': 'Boast Enabler',
            'description': f"{card2['name']} untaps {card1['name']} for multiple boast activations",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'activated_ability'
        }

    if card2_boast and card1_untap:
        return {
            'name': 'Boast Enabler',
            'description': f"{card1['name']} untaps {card2['name']} for multiple boast activations",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'activated_ability'
        }

    return None


def detect_backup_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect backup with counter synergies
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_backup = 'backup' in card1_text
    card2_backup = 'backup' in card2_text

    counter_payoff_patterns = [
        r'whenever.*\+1/\+1 counter',
        r'for each \+1/\+1 counter',
        r'remove.*\+1/\+1 counter'
    ]

    card1_payoff = any(search_cached(pattern, card1_text) for pattern in counter_payoff_patterns)
    card2_payoff = any(search_cached(pattern, card2_text) for pattern in counter_payoff_patterns)

    if card1_backup and card2_payoff:
        return {
            'name': 'Backup Counter Synergy',
            'description': f"{card1['name']}'s backup counters synergize with {card2['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'counters'
        }

    if card2_backup and card1_payoff:
        return {
            'name': 'Backup Counter Synergy',
            'description': f"{card2['name']}'s backup counters synergize with {card1['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'counters'
        }

    return None


def detect_blitz_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect blitz with death triggers
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_blitz = 'blitz' in card1_text
    card2_blitz = 'blitz' in card2_text

    death_matters_patterns = [
        r'whenever.*dies',
        r'whenever.*creature.*put into.*graveyard',
        r'when.*dies'
    ]

    card1_death = any(search_cached(pattern, card1_text) for pattern in death_matters_patterns)
    card2_death = any(search_cached(pattern, card2_text) for pattern in death_matters_patterns)

    if card1_blitz and card2_death:
        return {
            'name': 'Blitz Sacrifice',
            'description': f"{card1['name']}'s blitz triggers {card2['name']}'s death payoff",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'sacrifice'
        }

    if card2_blitz and card1_death:
        return {
            'name': 'Blitz Sacrifice',
            'description': f"{card2['name']}'s blitz triggers {card1['name']}'s death payoff",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'sacrifice'
        }

    return None


def detect_craft_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect craft with artifact tokens
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_craft = 'craft' in card1_text and 'exile' in card1_text
    card2_craft = 'craft' in card2_text and 'exile' in card2_text

    artifact_generation = [
        r'treasure',
        r'create.*artifact',
        r'powerstone'
    ]

    card1_artifacts = any(pattern in card1_text for pattern in artifact_generation)
    card2_artifacts = any(pattern in card2_text for pattern in artifact_generation)

    if card1_craft and card2_artifacts:
        return {
            'name': 'Craft Enabler',
            'description': f"{card2['name']} creates artifacts for {card1['name']}'s craft cost",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_craft and card1_artifacts:
        return {
            'name': 'Craft Enabler',
            'description': f"{card1['name']} creates artifacts for {card2['name']}'s craft cost",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_discover_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect discover with low CMC powerful spells
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_discover = 'discover' in card1_text
    card2_discover = 'discover' in card2_text

    # Discover finds low CMC spells, so high-value low CMC cards synergize
    card1_cmc = card1.get('cmc', 999)
    card2_cmc = card2.get('cmc', 999)

    if card1_discover and card2_cmc <= 3:
        return {
            'name': 'Discover Target',
            'description': f"{card1['name']}'s discover can find {card2['name']}",
            'value': 2.0,
            'category': 'combo',
            'subcategory': 'cascade'
        }

    if card2_discover and card1_cmc <= 3:
        return {
            'name': 'Discover Target',
            'description': f"{card2['name']}'s discover can find {card1['name']}",
            'value': 2.0,
            'category': 'combo',
            'subcategory': 'cascade'
        }

    return None


def detect_incubate_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect incubate with artifact/creature matters
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_incubate = 'incubate' in card1_text
    card2_incubate = 'incubate' in card2_text

    token_synergy_patterns = [
        r'whenever.*artifact enters',
        r'whenever.*creature enters',
        r'artifacts you control'
    ]

    card1_synergy = any(search_cached(pattern, card1_text) for pattern in token_synergy_patterns)
    card2_synergy = any(search_cached(pattern, card2_text) for pattern in token_synergy_patterns)

    if card1_incubate and card2_synergy:
        return {
            'name': 'Incubate Payoff',
            'description': f"{card1['name']}'s incubate tokens trigger {card2['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_incubate and card1_synergy:
        return {
            'name': 'Incubate Payoff',
            'description': f"{card2['name']}'s incubate tokens trigger {card1['name']}",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_affinity_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect affinity cost reduction with artifact generation
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_affinity = 'affinity for' in card1_text
    card2_affinity = 'affinity for' in card2_text

    artifact_gen_patterns = [
        r'create.*artifact.*token',
        r'treasure',
        r'servo',
        r'clue',
        r'food',
        r'powerstone'
    ]

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    card1_artifacts = any(pattern in card1_text for pattern in artifact_gen_patterns) or 'artifact' in card1_type
    card2_artifacts = any(pattern in card2_text for pattern in artifact_gen_patterns) or 'artifact' in card2_type

    if card1_affinity and card2_artifacts:
        return {
            'name': 'Affinity Cost Reduction',
            'description': f"{card2['name']} reduces {card1['name']}'s affinity cost",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    if card2_affinity and card1_artifacts:
        return {
            'name': 'Affinity Cost Reduction',
            'description': f"{card1['name']} reduces {card2['name']}'s affinity cost",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'artifacts'
        }

    return None


def detect_kicker_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect kicker/multikicker with mana generation or cost reduction
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    kicker_patterns = [r'\bkicker\b', r'multikicker', r'was kicked']

    card1_kicker = any(search_cached(pattern, card1_text) for pattern in kicker_patterns)
    card2_kicker = any(search_cached(pattern, card2_text) for pattern in kicker_patterns)

    mana_gen_patterns = [
        r'add.*{[wubrgc]}',
        r'treasure',
        r'ritual',
        r'cost.*less to cast'
    ]

    card1_mana = any(search_cached(pattern, card1_text) for pattern in mana_gen_patterns)
    card2_mana = any(search_cached(pattern, card2_text) for pattern in mana_gen_patterns)

    if card1_kicker and card2_mana:
        return {
            'name': 'Kicker Enabler',
            'description': f"{card2['name']} provides mana to kick {card1['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'ramp'
        }

    if card2_kicker and card1_mana:
        return {
            'name': 'Kicker Enabler',
            'description': f"{card1['name']} provides mana to kick {card2['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'ramp'
        }

    return None


def detect_overload_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect overload with mana generation
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_overload = 'overload' in card1_text
    card2_overload = 'overload' in card2_text

    big_mana_patterns = [
        r'add.*{[wubrg]}.*{[wubrg]}.*{[wubrg]}',  # 3+ mana
        r'untap all',
        r'add.*mana equal to',
        r'ritual'
    ]

    card1_big_mana = any(search_cached(pattern, card1_text) for pattern in big_mana_patterns)
    card2_big_mana = any(search_cached(pattern, card2_text) for pattern in big_mana_patterns)

    if card1_overload and card2_big_mana:
        return {
            'name': 'Overload Enabler',
            'description': f"{card2['name']} provides mana to overload {card1['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'ramp'
        }

    if card2_overload and card1_big_mana:
        return {
            'name': 'Overload Enabler',
            'description': f"{card1['name']} provides mana to overload {card2['name']}",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'ramp'
        }

    return None


def detect_miracle_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect miracle with top deck manipulation
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_miracle = 'miracle' in card1_text
    card2_miracle = 'miracle' in card2_text

    topdeck_patterns = [
        r'top.*library',
        r'put.*on top',
        r'scry',
        r'brainstorm',
        r'sensei\'s divining top'
    ]

    card1_topdeck = any(search_cached(pattern, card1_text) for pattern in topdeck_patterns)
    card2_topdeck = any(search_cached(pattern, card2_text) for pattern in topdeck_patterns)

    if card1_miracle and card2_topdeck:
        return {
            'name': 'Miracle Setup',
            'description': f"{card2['name']} sets up {card1['name']}'s miracle cast",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'top_deck_manipulation'
        }

    if card2_miracle and card1_topdeck:
        return {
            'name': 'Miracle Setup',
            'description': f"{card1['name']} sets up {card2['name']}'s miracle cast",
            'value': 3.5,
            'category': 'combo',
            'subcategory': 'top_deck_manipulation'
        }

    return None


def detect_reflexive_trigger_synergies(card1: Dict, card2: Dict, deck_info: Optional[Dict] = None) -> List[Dict]:
    """
    Detect synergies with reflexive triggers ("whenever X, you may Y. When you do, Z").

    Generic detection for cards like:
    - Caesar, Legion's Emperor (attack → sacrifice → modal effects)
    - Cards with optional sacrifice costs that trigger effects
    - Cards that enable or enhance reflexive triggers

    Returns synergies between reflexive trigger cards and enablers/payoffs.
    """
    synergies = []
    oracle1 = card1.get('oracle_text', '').lower()
    oracle2 = card2.get('oracle_text', '').lower()

    # Pattern: "whenever X, you may Y. when you do, Z"
    reflexive_pattern = re.compile(
        r'(whenever|when)\s+([^.]+?),\s+you may\s+([^.]+?)\.\s+when you do',
        re.IGNORECASE
    )

    # Check which card has the reflexive trigger
    card_with_trigger = None
    other_card = None

    if reflexive_pattern.search(oracle1):
        card_with_trigger = card1
        other_card = card2
        trigger_oracle = oracle1
        other_oracle = oracle2
    elif reflexive_pattern.search(oracle2):
        card_with_trigger = card2
        other_card = card1
        trigger_oracle = oracle2
        other_oracle = oracle1
    else:
        return synergies

    # Reflexive trigger detected - check for synergies with the other card

    # Synergy 1: Attack triggers + token generators
    if 'whenever you attack' in trigger_oracle and 'sacrifice' in trigger_oracle:
        # Check if other card creates tokens (fodder for sacrifice)
        if ('create' in other_oracle and 'token' in other_oracle):
            synergies.append({
                'name': 'Attack Trigger + Token Fodder',
                'description': f"{card_with_trigger['name']} can sacrifice tokens from {other_card['name']}",
                'value': 8.0,
                'category': 'tokens',
                'subcategory': 'sacrifice_synergy'
            })

    # Synergy 2: Reflexive triggers + sacrifice outlets (extra value)
    if 'sacrifice' in trigger_oracle and 'you may sacrifice' in trigger_oracle:
        # Check if other card cares about sacrifices
        if ('whenever' in other_oracle and 'sacrifice' in other_oracle and 'creature' in other_oracle):
            synergies.append({
                'name': 'Reflexive Sacrifice + Sacrifice Payoff',
                'description': f"{card_with_trigger['name']}'s optional sacrifice triggers {other_card['name']}",
                'value': 7.0,
                'category': 'aristocrats',
                'subcategory': 'sacrifice_triggers'
            })

    # Synergy 3: Attack triggers + attack enablers
    if 'whenever you attack' in trigger_oracle:
        # Check if other card grants extra combats or enables attacks
        if ('additional combat' in other_oracle or 'extra combat' in other_oracle or
            'attack again' in other_oracle):
            synergies.append({
                'name': 'Attack Trigger + Extra Combat',
                'description': f"{other_card['name']} enables multiple triggers of {card_with_trigger['name']}",
                'value': 9.0,
                'category': 'combat',
                'subcategory': 'extra_combats'
            })

        # Check if other card gives haste (enables immediate attacks)
        if 'haste' in other_oracle and ('creature' in other_oracle or 'gain haste' in other_oracle):
            synergies.append({
                'name': 'Attack Trigger + Haste Enabler',
                'description': f"{other_card['name']} enables {card_with_trigger['name']} to attack immediately",
                'value': 6.0,
                'category': 'combat',
                'subcategory': 'haste'
            })

    # Synergy 4: Modal reflexive effects + draw/selection
    if 'choose' in trigger_oracle and '•' in card_with_trigger.get('oracle_text', ''):
        # Check if other card provides card selection/draw
        if ('draw' in other_oracle or 'scry' in other_oracle or 'surveil' in other_oracle):
            synergies.append({
                'name': 'Modal Trigger + Card Selection',
                'description': f"{other_card['name']} helps find optimal modes for {card_with_trigger['name']}",
                'value': 5.0,
                'category': 'card_advantage',
                'subcategory': 'selection'
            })

    return synergies


# List of all detection functions
ALL_RULES = [
    detect_etb_triggers,
    detect_sacrifice_synergy,
    detect_mana_color_synergy,
    detect_tribal_synergy,
    detect_tribal_chosen_type_synergy,  # New: detects "choose a creature type" synergies
    detect_tribal_same_type_synergy,     # New: detects "same type" and changeling synergies
    detect_tribal_trigger_synergy,       # New: detects tribal triggered abilities
    detect_card_draw_synergy,
    detect_ramp_synergy,
    detect_type_matters_synergy,
    detect_combo_potential,
    detect_protection_synergy,
    detect_token_synergy,
    detect_graveyard_synergy,
    detect_life_as_resource,
    detect_deathtouch_pingers,
    detect_indestructible_board_wipe,
    detect_extra_combat_synergy,
    detect_reflexive_trigger_synergies,  # Generic reflexive trigger detection (e.g., Caesar)
    detect_wheel_and_deal,
    detect_tap_untap_engines,
    detect_cheat_big_spells,
    detect_topdeck_manipulation,
    detect_surveil_synergy,
    detect_scry_synergy,
    detect_threaten_and_sac,
    detect_token_anthems,
    detect_convoke_improvise,
    detect_fling_effects,
    detect_double_strike_synergy,
    detect_spellslinger_payoffs,
    detect_artifact_token_triggers,
    detect_token_doublers,
    detect_discard_madness_flashback,
    detect_enchantress_effects,
    detect_voltron_evasion,
    # New damage/drain/burn synergies
    detect_aristocrats_synergy,
    detect_burn_synergy,
    detect_lifegain_payoffs,
    detect_damage_based_card_draw,
    detect_creature_damage_synergy,
    # New synergy rules - equipment, landfall, counters, copy, storm, energy, stax
    detect_equipment_synergy,
    detect_landfall_synergy,
    detect_counter_synergy,
    detect_copy_synergy,
    detect_storm_synergy,
    # Spellslinger archetype rules
    detect_aetherflux_reservoir_synergy,
    detect_spell_cost_reduction,
    detect_flashback_synergy,
    detect_cantrip_synergy,
    detect_energy_synergy,
    detect_stax_synergy,
    # New comprehensive synergy rules (46 new rules added)
    detect_sacrifice_outlet_synergy,
    detect_blink_etb_synergy,
    detect_proliferate_synergy,
    detect_infect_damage_synergy,
    detect_mill_self_payoff,
    detect_flash_synergy,
    detect_haste_enabler_synergy,
    detect_vigilance_tap_synergy,
    detect_hexproof_aura_synergy,
    detect_trample_pump_synergy,
    detect_lifelink_damage_synergy,
    detect_flying_evasion_synergy,
    detect_menace_token_synergy,
    detect_first_strike_damage_synergy,
    detect_planeswalker_proliferate_synergy,
    detect_planeswalker_protection_synergy,
    detect_commander_damage_synergy,
    detect_untap_land_synergy,
    detect_fetch_land_synergy,
    detect_artifact_sac_synergy,
    detect_enchantment_synergy,
    detect_saga_synergy,
    detect_room_synergy,
    detect_vehicle_synergy,
    detect_food_synergy,
    detect_blood_synergy,
    detect_investigate_synergy,
    detect_role_token_synergy,
    detect_bargain_synergy,
    detect_modified_synergy,
    detect_ninjutsu_synergy,
    detect_mutate_synergy,
    detect_companion_synergy,
    detect_party_synergy,
    detect_foretell_synergy,
    detect_boast_synergy,
    detect_backup_synergy,
    detect_blitz_synergy,
    detect_craft_synergy,
    detect_discover_synergy,
    detect_incubate_synergy,
    detect_affinity_synergy,
    detect_kicker_synergy,
    detect_overload_synergy,
    detect_miracle_synergy
] + CARD_ADVANTAGE_SYNERGY_RULES + ALLY_PROWESS_SYNERGY_RULES + SPELLSLINGER_ENGINE_SYNERGY_RULES  # Add card advantage + Ally/Prowess + Spellslinger engine synergies
