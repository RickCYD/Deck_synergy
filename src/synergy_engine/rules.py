"""
Synergy Detection Rules
Individual rule functions for detecting different types of synergies between cards
"""

import re
from typing import Dict, List, Optional, Set
from functools import lru_cache
from src.utils.damage_extractors import classify_damage_effect
from src.synergy_engine.card_advantage_synergies import CARD_ADVANTAGE_SYNERGY_RULES

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
    card1_has_etb = any(re.search(kw, card1_text) for kw in etb_keywords)
    card2_can_trigger = any(re.search(kw, card2_text) for kw in flicker_keywords)
    card2_is_reanimation = any(re.search(kw, card2_text) for kw in anti_flicker)

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
    card2_has_etb = any(re.search(kw, card2_text) for kw in etb_keywords)
    card1_can_trigger = any(re.search(kw, card1_text) for kw in flicker_keywords)
    card1_is_reanimation = any(re.search(kw, card1_text) for kw in anti_flicker)

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

    death_trigger_keywords = [r'when .* dies', r'whenever .* dies', r'when .* is put into a graveyard']
    token_generation = [r'create.*token', r'put.*token']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_is_outlet = any(re.search(pattern, card1_text) for pattern in sacrifice_outlet_patterns) and \
                      not any(re.search(pattern, card1_text) for pattern in exclude_patterns)
    card2_creates_tokens = any(re.search(kw, card2_text) for kw in token_generation)
    card2_death_trigger = any(re.search(kw, card2_text) for kw in death_trigger_keywords)

    if card1_is_outlet and (card2_creates_tokens or card2_death_trigger):
        return {
            'name': 'Sacrifice Synergy',
            'description': f"{card1['name']} can sacrifice permanents from {card2['name']}",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    # Check reverse
    card2_is_outlet = any(re.search(pattern, card2_text) for pattern in sacrifice_outlet_patterns) and \
                      not any(re.search(pattern, card2_text) for pattern in exclude_patterns)
    card1_creates_tokens = any(re.search(kw, card1_text) for kw in token_generation)
    card1_death_trigger = any(re.search(kw, card1_text) for kw in death_trigger_keywords)

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
    card1_produces_colorless = any(re.search(pattern, card1_text) for pattern in colorless_patterns)
    if card1_produces_colorless and card2_cmc > 0:
        return {
            'name': 'Mana Acceleration',
            'description': f"{card1['name']} produces colorless mana for {card2['name']}'s generic cost",
            'value': 1.0,
            'category': 'mana_synergy',
            'subcategory': 'mana_production'
        }

    # Check if card2 produces colorless mana and card1 has any mana cost
    card2_produces_colorless = any(re.search(pattern, card2_text) for pattern in colorless_patterns)
    if card2_produces_colorless and card1_cmc > 0:
        return {
            'name': 'Mana Acceleration',
            'description': f"{card2['name']} produces colorless mana for {card1['name']}'s generic cost",
            'value': 1.0,
            'category': 'mana_synergy',
            'subcategory': 'mana_production'
        }

    # Check if card1 produces mana and card2 needs that color
    for color, patterns in mana_production_patterns.items():
        card1_produces_color = any(re.search(pattern, card1_text) for pattern in patterns) or \
                               ('land' in card1_type and color in card1_colors)

        if card1_produces_color and color in card2_colors:
            color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
            return {
                'name': 'Mana Fixing',
                'description': f"{card1['name']} produces {color_names[color]} mana for {card2['name']}'s cost",
                'value': 2.0,
                'category': 'mana_synergy',
                'subcategory': 'mana_production'
            }

    # Check reverse
    for color, patterns in mana_production_patterns.items():
        card2_produces_color = any(re.search(pattern, card2_text) for pattern in patterns) or \
                               ('land' in card2_type and color in card2_colors)

        if card2_produces_color and color in card1_colors:
            color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
            return {
                'name': 'Mana Fixing',
                'description': f"{card2['name']} produces {color_names[color]} mana for {card1['name']}'s cost",
                'value': 2.0,
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
        if any(re.search(pattern, card1_text) for pattern in patterns):
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
        if any(re.search(pattern, card2_text) for pattern in patterns):
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


def detect_card_draw_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect card draw and card advantage synergies"""
    draw_keywords = ['draw.*card', 'draws.*card', 'you draw']
    wheel_keywords = ['each player draws', 'discard.*hand.*draw']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_draws = any(re.search(kw, card1_text) for kw in draw_keywords + wheel_keywords)
    card2_draws = any(re.search(kw, card2_text) for kw in draw_keywords + wheel_keywords)

    # Both cards draw - card advantage engine
    if card1_draws and card2_draws:
        return {
            'name': 'Card Draw Engine',
            'description': f"Both cards contribute to card advantage",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'draw_engine'
        }

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
    card1_is_ramp = (not card1_is_land) and any(re.search(kw, card1_text) for kw in ramp_keywords)
    card2_is_ramp = (not card2_is_land) and any(re.search(kw, card2_text) for kw in ramp_keywords)

    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Ramp enables high CMC card
    if card1_is_ramp and card2_cmc >= high_cmc_threshold:
        return {
            'name': 'Ramp Enabler',
            'description': f"{card1['name']} helps cast expensive {card2['name']} (CMC {card2_cmc})",
            'value': 2.0,
            'category': 'role_interaction',
            'subcategory': 'ramp'
        }

    if card2_is_ramp and card1_cmc >= high_cmc_threshold:
        return {
            'name': 'Ramp Enabler',
            'description': f"{card2['name']} helps cast expensive {card1['name']} (CMC {card1_cmc})",
            'value': 2.0,
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
        card1_cares = any(re.search(pattern, card1_text) for pattern in patterns)
        card1_is_negative = any(re.search(pattern, card1_text) for pattern in negative_patterns)

        if card1_cares and not card1_is_negative and card_type in card2_type:
            return {
                'name': f'{card_type.title()} Synergy',
                'description': f"{card1['name']} cares about {card_type}s, {card2['name']} is a {card_type}",
                'value': 2.5,
                'category': 'type_synergy',
                'subcategory': subcategory_map[card_type]
            }

        # Check reverse
        card2_cares = any(re.search(pattern, card2_text) for pattern in patterns)
        card2_is_negative = any(re.search(pattern, card2_text) for pattern in negative_patterns)

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
        card1_untaps_others = re.search(r'untap (target|another|all|up to)', card1_text)
        card2_untaps_others = re.search(r'untap (target|another|all|up to)', card2_text)

        # Must produce mana from tapping
        card1_taps_for_mana = re.search(r'\{t\}.*add.*mana', card1_text) or re.search(r'\{t\}:.*add \{[wubrgc]\}', card1_text)
        card2_taps_for_mana = re.search(r'\{t\}.*add.*mana', card2_text) or re.search(r'\{t\}:.*add \{[wubrgc]\}', card2_text)

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
    """Detect token generation and payoff synergies"""
    # Token generation patterns (must be under YOUR control)
    token_generation = [
        r'you create.*token',
        r'create.*token.*under your control',
        r'put.*token.*onto the battlefield under your control',
        r'create a .*token'  # Most token creation is for you unless specified
    ]

    # Exclude opponent token generation
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

    token_payoff = [r'whenever.*token', r'tokens you control', r'for each.*token you control']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_generates = any(re.search(kw, card1_text) for kw in token_generation) and \
                      not any(re.search(kw, card1_text) for kw in opponent_token_patterns)
    card2_payoff = any(re.search(kw, card2_text) for kw in token_payoff)

    if card1_generates and card2_payoff:
        return {
            'name': 'Token Synergy',
            'description': f"{card1['name']} creates tokens that {card2['name']} benefits from",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'token_generation'
        }

    # Check reverse
    card2_generates = any(re.search(kw, card2_text) for kw in token_generation) and \
                      not any(re.search(kw, card2_text) for kw in opponent_token_patterns)
    card1_payoff = any(re.search(kw, card1_text) for kw in token_payoff)

    if card2_generates and card1_payoff:
        return {
            'name': 'Token Synergy',
            'description': f"{card2['name']} creates tokens that {card1['name']} benefits from",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'token_generation'
        }

    return None


def detect_graveyard_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect graveyard and recursion synergies.

    NOTE: Flashback, Jump-start, and Retrace are SELF-RECURSION mechanics.
    They don't benefit from OTHER cards filling the graveyard - only their own card.
    These should NOT trigger graveyard synergies.

    True graveyard payoffs care about OTHER cards in the graveyard:
    - Reanimation (return OTHER creatures from graveyard)
    - Delve/Escape (exile OTHER cards from graveyard)
    - Threshold/Delirium (count cards in graveyard)
    - Recursion that targets (return target card from graveyard)
    """
    graveyard_fill = ['mill', 'put.*into.*graveyard', 'discard']

    # Real graveyard payoffs - cards that benefit from OTHER cards in graveyard
    # EXCLUDE: flashback, jump-start, retrace (self-recursion only)
    graveyard_payoff = [
        r'return\s+(?:target|a|up to).*(?:card|creature|permanent).*from.*graveyard',  # Reanimation
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

    card1_fills = any(re.search(kw, card1_text) for kw in graveyard_fill)
    card2_payoff = any(re.search(kw, card2_text) for kw in graveyard_payoff)

    if card1_fills and card2_payoff:
        return {
            'name': 'Graveyard Synergy',
            'description': f"{card1['name']} fills graveyard for {card2['name']} to utilize",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'recursion'
        }

    # Check reverse
    card2_fills = any(re.search(kw, card2_text) for kw in graveyard_fill)
    card1_payoff = any(re.search(kw, card1_text) for kw in graveyard_payoff)

    if card2_fills and card1_payoff:
        return {
            'name': 'Graveyard Synergy',
            'description': f"{card2['name']} fills graveyard for {card1['name']} to utilize",
            'value': 2.5,
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
    card1_pays_life = any(re.search(pattern, card1_text) for pattern in life_payment_patterns)
    card1_targets_opponent = any(re.search(pattern, card1_text) for pattern in opponent_patterns)
    card2_gains_life = any(re.search(pattern, card2_text) for pattern in life_gain_patterns) or 'lifelink' in card2_keywords

    if card1_pays_life and not card1_targets_opponent and card2_gains_life:
        return {
            'name': 'Life as Resource',
            'description': f"{card1['name']} pays life as a cost, {card2['name']} gains life to offset",
            'value': 3.0,
            'category': 'mana_synergy',
            'subcategory': 'cost_reduction'
        }

    # Check reverse
    card2_pays_life = any(re.search(pattern, card2_text) for pattern in life_payment_patterns)
    card2_targets_opponent = any(re.search(pattern, card2_text) for pattern in opponent_patterns)
    card1_gains_life = any(re.search(pattern, card1_text) for pattern in life_gain_patterns) or 'lifelink' in card1_keywords

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
    card1_has_deathtouch = 'deathtouch' in card1_keywords or any(re.search(pattern, card1_text) for pattern in deathtouch_patterns)
    card1_grants_deathtouch = any(re.search(pattern, card1_text) for pattern in grants_deathtouch)
    card2_deals_damage = any(re.search(pattern, card2_text) for pattern in pinger_patterns)

    if (card1_has_deathtouch or card1_grants_deathtouch) and card2_deals_damage:
        return {
            'name': 'Deathtouch Pinger',
            'description': f"{card1['name']} provides deathtouch, {card2['name']} deals damage for removal",
            'value': 2.5,
            'category': 'role_interaction',
            'subcategory': 'removal'
        }

    # Check reverse
    card2_has_deathtouch = 'deathtouch' in card2_keywords or any(re.search(pattern, card2_text) for pattern in deathtouch_patterns)
    card2_grants_deathtouch = any(re.search(pattern, card2_text) for pattern in grants_deathtouch)
    card1_deals_damage = any(re.search(pattern, card1_text) for pattern in pinger_patterns)

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
    card1_has_indestructible = 'indestructible' in card1_keywords or any(re.search(pattern, card1_text) for pattern in indestructible_patterns)
    card2_is_destroy_wipe = any(re.search(pattern, card2_text) for pattern in destroy_wipe_patterns)
    card2_is_exile_wipe = any(re.search(pattern, card2_text) for pattern in exile_wipe_patterns)
    card2_is_one_sided = any(re.search(pattern, card2_text) for pattern in one_sided_patterns)

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
    card2_has_indestructible = 'indestructible' in card2_keywords or any(re.search(pattern, card2_text) for pattern in indestructible_patterns)
    card1_is_destroy_wipe = any(re.search(pattern, card1_text) for pattern in destroy_wipe_patterns)
    card1_is_exile_wipe = any(re.search(pattern, card1_text) for pattern in exile_wipe_patterns)
    card1_is_one_sided = any(re.search(pattern, card1_text) for pattern in one_sided_patterns)

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
    card1_extra_combat = any(re.search(pattern, card1_text) for pattern in extra_combat_patterns)
    card2_combat_ability = any(kw in card2_keywords for kw in combat_keywords) or \
                           any(re.search(pattern, card2_text) for pattern in combat_ability_patterns)

    if card1_extra_combat and card2_combat_ability:
        return {
            'name': 'Extra Combat',
            'description': f"{card1['name']} grants extra combats, {card2['name']} benefits from attacking",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_extra_combat = any(re.search(pattern, card2_text) for pattern in extra_combat_patterns)
    card1_combat_ability = any(kw in card1_keywords for kw in combat_keywords) or \
                           any(re.search(pattern, card1_text) for pattern in combat_ability_patterns)

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
    card1_neheb = any(re.search(p, card1_text) for p in neheb_patterns)
    card2_neheb = any(re.search(p, card2_text) for p in neheb_patterns)
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
    card1_is_wheel = any(re.search(pattern, card1_text) for pattern in wheel_patterns)
    card2_punishes_draw = any(re.search(pattern, card2_text) for pattern in draw_punisher_patterns)
    card2_punishes_discard = any(re.search(pattern, card2_text) for pattern in discard_punisher_patterns)

    if card1_is_wheel and (card2_punishes_draw or card2_punishes_discard):
        return {
            'name': 'Wheel and Deal',
            'description': f"{card1['name']} forces mass draw/discard, {card2['name']} punishes opponents",
            'value': 3.0,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_is_wheel = any(re.search(pattern, card2_text) for pattern in wheel_patterns)
    card1_punishes_draw = any(re.search(pattern, card1_text) for pattern in draw_punisher_patterns)
    card1_punishes_discard = any(re.search(pattern, card1_text) for pattern in discard_punisher_patterns)

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
    card1_untaps = any(re.search(pattern, card1_text) for pattern in untap_patterns)
    card2_has_tap_ability = any(re.search(pattern, card2_text) for pattern in tap_ability_patterns)
    card2_is_basic_mana = any(re.search(pattern, card2_text) for pattern in basic_mana_patterns)

    if card1_untaps and card2_has_tap_ability and not card2_is_basic_mana:
        return {
            'name': 'Tap/Untap Engine',
            'description': f"{card1['name']} untaps {card2['name']} for repeated value",
            'value': 2.5,
            'category': 'combo',
            'subcategory': 'two_card_combo'
        }

    # Check reverse
    card2_untaps = any(re.search(pattern, card2_text) for pattern in untap_patterns)
    card1_has_tap_ability = any(re.search(pattern, card1_text) for pattern in tap_ability_patterns)
    card1_is_basic_mana = any(re.search(pattern, card1_text) for pattern in basic_mana_patterns)

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
        r'put.*onto the battlefield',  # For permanents
        r'affinity',
        r'convoke',
        r'delve'
    ]

    # High CMC threshold
    HIGH_CMC = 6

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 cheats and card2 is expensive
    card1_cheats = any(re.search(pattern, card1_text) for pattern in cheat_patterns)

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
    card2_cheats = any(re.search(pattern, card2_text) for pattern in cheat_patterns)

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
    card1_scrys = 'scry' in card1_keywords or any(re.search(pattern, card1_text) for pattern in scry_patterns)
    card2_benefits_scry = any(re.search(pattern, card2_text) for pattern in scry_benefit_patterns)

    if card1_scrys and card2_benefits_scry:
        return {
            'name': 'Scry Synergy',
            'description': f"{card1['name']} scrys to set up {card2['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'scry_synergy'
        }

    # Check reverse
    card2_scrys = 'scry' in card2_keywords or any(re.search(pattern, card2_text) for pattern in scry_patterns)
    card1_benefits_scry = any(re.search(pattern, card1_text) for pattern in scry_benefit_patterns)

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
    card1_surveys = 'surveil' in card1_keywords or any(re.search(pattern, card1_text) for pattern in surveil_patterns)
    card2_benefits_surveil = any(re.search(pattern, card2_text) for pattern in surveil_benefit_patterns)

    if card1_surveys and card2_benefits_surveil:
        return {
            'name': 'Surveil Synergy',
            'description': f"{card1['name']} surveils to set up {card2['name']}'s benefits",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'surveil_synergy'
        }

    # Check reverse
    card2_surveys = 'surveil' in card2_keywords or any(re.search(pattern, card2_text) for pattern in surveil_patterns)
    card1_benefits_surveil = any(re.search(pattern, card1_text) for pattern in surveil_benefit_patterns)

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
    card1_manipulates = 'top' in card2_keywords or any(re.search(pattern, card1_text) for pattern in top_manipulation_patterns)
    card1_is_bounce = any(re.search(pattern, card1_text) for pattern in bounce_patterns)
    card2_cares_top = any(re.search(pattern, card2_text) for pattern in top_matters_patterns) or 'miracle' in card2_keywords

    if card1_manipulates and not card1_is_bounce and card2_cares_top:
        return {
            'name': 'Topdeck Manipulation',
            'description': f"{card1['name']} sets up top of library for {card2['name']}",
            'value': 2.0,
            'category': 'card_advantage',
            'subcategory': 'top_deck_synergy'
        }

    # Check reverse
    card2_manipulates = 'top' in card2_keywords or any(re.search(pattern, card2_text) for pattern in top_manipulation_patterns)
    card2_is_bounce = any(re.search(pattern, card2_text) for pattern in bounce_patterns)
    card1_cares_top = any(re.search(pattern, card1_text) for pattern in top_matters_patterns) or 'miracle' in card1_keywords

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
    card1_threatens = any(re.search(pattern, card1_text) for pattern in threaten_patterns)
    card2_is_sac_outlet = 'sacrifice' in card2_text and ('a creature' in card2_text or 'another creature' in card2_text)
    card2_blinks = any(re.search(pattern, card2_text) for pattern in blink_patterns)

    if card1_threatens and (card2_is_sac_outlet or card2_blinks):
        return {
            'name': 'Threaten & Sacrifice',
            'description': f"{card1['name']} steals creatures, {card2['name']} sacrifices/blinks them permanently",
            'value': 4.0,
            'category': 'role_interaction',
            'subcategory': 'sacrifice'
        }

    # Check reverse
    card2_threatens = any(re.search(pattern, card2_text) for pattern in threaten_patterns)
    card1_is_sac_outlet = 'sacrifice' in card1_text and ('a creature' in card1_text or 'another creature' in card1_text)
    card1_blinks = any(re.search(pattern, card1_text) for pattern in blink_patterns)

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
    card1_makes_tokens = any(re.search(pattern, card1_text) for pattern in token_patterns)
    card2_buffs = any(re.search(pattern, card2_text) for pattern in buff_patterns)
    card2_is_negative = any(re.search(pattern, card2_text) for pattern in negative_patterns)

    if card1_makes_tokens and card2_buffs and not card2_is_negative:
        return {
            'name': 'Token Anthem',
            'description': f"{card1['name']} creates tokens, {card2['name']} pumps them for lethal",
            'value': 5.0,
            'category': 'benefits',
            'subcategory': 'anthem_effect'
        }

    # Check reverse
    card2_makes_tokens = any(re.search(pattern, card2_text) for pattern in token_patterns)
    card1_buffs = any(re.search(pattern, card1_text) for pattern in buff_patterns)
    card1_is_negative = any(re.search(pattern, card1_text) for pattern in negative_patterns)

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
    card2_makes_creatures = any(re.search(pattern, card2_text) for pattern in token_patterns)
    card2_makes_artifacts = any(re.search(pattern, card2_text) for pattern in artifact_token_patterns)

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
    card1_makes_creatures = any(re.search(pattern, card1_text) for pattern in token_patterns)
    card1_makes_artifacts = any(re.search(pattern, card1_text) for pattern in artifact_token_patterns)

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
    card1_is_fling = any(re.search(pattern, card1_text) for pattern in fling_patterns)

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
    card2_is_fling = any(re.search(pattern, card2_text) for pattern in fling_patterns)

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
                                  any(re.search(pattern, card1_text) for pattern in double_strike_patterns)
    card1_doubles_damage = any(re.search(pattern, card1_text) for pattern in damage_doubler_patterns)

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
                                  any(re.search(pattern, card2_text) for pattern in double_strike_patterns)
    card2_doubles_damage = any(re.search(pattern, card2_text) for pattern in damage_doubler_patterns)

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

    # Check if card1 has spell triggers and card2 is a cheap instant/sorcery
    card1_has_trigger = any(re.search(pattern, card1_text) for pattern in spell_trigger_patterns) or \
                        any(re.search(pattern, card1_text) for pattern in magecraft_patterns) or \
                        'prowess' in card1_keywords

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
    card2_has_trigger = any(re.search(pattern, card2_text) for pattern in spell_trigger_patterns) or \
                        any(re.search(pattern, card2_text) for pattern in magecraft_patterns) or \
                        'prowess' in card2_keywords

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
    # Artifact token generation patterns
    artifact_token_patterns = [
        r'create.*treasure',
        r'create.*clue',
        r'create.*food',
        r'create.*artifact.*token'
    ]

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
    card1_makes_artifacts = any(re.search(pattern, card1_text) for pattern in artifact_token_patterns)
    card2_has_etb = any(re.search(pattern, card2_text) for pattern in artifact_etb_patterns)
    card2_has_death = any(re.search(pattern, card2_text) for pattern in artifact_death_patterns)

    if card1_makes_artifacts and (card2_has_etb or card2_has_death):
        trigger_type = "enters" if card2_has_etb else "dies"
        return {
            'name': 'Artifact Token Engine',
            'description': f"{card1['name']} creates artifact tokens, {card2['name']} triggers when they {trigger_type}",
            'value': 4.0,
            'category': 'type_synergy',
            'subcategory': 'artifact_matters'
        }

    # Check reverse
    card2_makes_artifacts = any(re.search(pattern, card2_text) for pattern in artifact_token_patterns)
    card1_has_etb = any(re.search(pattern, card1_text) for pattern in artifact_etb_patterns)
    card1_has_death = any(re.search(pattern, card1_text) for pattern in artifact_death_patterns)

    if card2_makes_artifacts and (card1_has_etb or card1_has_death):
        trigger_type = "enters" if card1_has_etb else "dies"
        return {
            'name': 'Artifact Token Engine',
            'description': f"{card2['name']} creates artifact tokens, {card1['name']} triggers when they {trigger_type}",
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
                       any(re.search(pattern, card1_text) for pattern in token_doubler_patterns)
    card2_makes_tokens = any(re.search(pattern, card2_text) for pattern in token_patterns)

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
                       any(re.search(pattern, card2_text) for pattern in token_doubler_patterns)
    card1_makes_tokens = any(re.search(pattern, card1_text) for pattern in token_patterns)

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
    card1_is_outlet = any(re.search(pattern, card1_text) for pattern in discard_outlet_patterns) or \
                      any(re.search(pattern, card1_text) for pattern in oneshot_discard_patterns)

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
    card2_is_outlet = any(re.search(pattern, card2_text) for pattern in discard_outlet_patterns) or \
                      any(re.search(pattern, card2_text) for pattern in oneshot_discard_patterns)

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
        any(re.search(pattern, card1_text) for pattern in enchantress_patterns)
        or any(re.search(pattern, card1_text) for pattern in constellation_patterns)
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
        any(re.search(pattern, card2_text) for pattern in enchantress_patterns)
        or any(re.search(pattern, card2_text) for pattern in constellation_patterns)
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
                              any(re.search(pattern, card1_text) for pattern in equipment_aura_patterns)
    card1_boosts_power = any(re.search(pattern, card1_text) for pattern in power_boost_patterns)

    card2_grants_evasion = any(kw in card2_keywords for kw in evasion_keywords) or \
                           any(re.search(pattern, card2_text) for pattern in evasion_patterns)
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
                              any(re.search(pattern, card2_text) for pattern in equipment_aura_patterns)
    card2_boosts_power = any(re.search(pattern, card2_text) for pattern in power_boost_patterns)

    card1_grants_evasion = any(kw in card1_keywords for kw in evasion_keywords) or \
                           any(re.search(pattern, card1_text) for pattern in evasion_patterns)
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

    # Death trigger patterns
    death_trigger_patterns = [r'when .* dies', r'whenever .* dies', r'when .* is put into a graveyard']

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

    card1_has_death_trigger = any(re.search(pattern, card1_text) for pattern in death_trigger_patterns)
    card2_has_death_trigger = any(re.search(pattern, card2_text) for pattern in death_trigger_patterns)

    card1_is_sac_outlet = any(re.search(pattern, card1_text) for pattern in sacrifice_outlet_patterns)
    card2_is_sac_outlet = any(re.search(pattern, card2_text) for pattern in sacrifice_outlet_patterns)

    card1_makes_tokens = any(re.search(pattern, card1_text) for pattern in token_generation_patterns)
    card2_makes_tokens = any(re.search(pattern, card2_text) for pattern in token_generation_patterns)

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

    card1_is_amplifier = any(re.search(pattern, card1_text) for pattern in damage_amplifier_patterns)
    card2_is_amplifier = any(re.search(pattern, card2_text) for pattern in damage_amplifier_patterns)

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

    card1_is_payoff = any(re.search(pattern, card1_text) for pattern in lifegain_payoff_patterns)
    card2_is_payoff = any(re.search(pattern, card2_text) for pattern in lifegain_payoff_patterns)

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

    card1_is_draw_trigger = any(re.search(pattern, card1_text) for pattern in damage_draw_patterns)
    card2_is_draw_trigger = any(re.search(pattern, card2_text) for pattern in damage_draw_patterns)

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

    card1_boosts_power = any(re.search(pattern, card1_text) for pattern in power_boost_patterns)
    card2_boosts_power = any(re.search(pattern, card2_text) for pattern in power_boost_patterns)

    card1_combat_matters = any(re.search(pattern, card1_text) for pattern in combat_matters_patterns)
    card2_combat_matters = any(re.search(pattern, card2_text) for pattern in combat_matters_patterns)

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

    # Equipment matters patterns
    equipment_matters_patterns = [
        r'whenever.*equipped',
        r'when.*becomes equipped',
        r'equipped creature',
        r'search.*library.*equipment',
        r'equipment.*from.*graveyard',
        r'equipment.*cost.*to equip',
        r'equipment.*you control',
        r'creatures you control with equipment'
    ]

    # Equipment synergy keywords
    equipment_keywords = ['equipped', 'equip']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Check if one is equipment and the other cares about equipment
    card1_is_equipment = 'equipment' in card1_type or any(re.search(pattern, card1_text) for pattern in equipment_patterns)
    card2_is_equipment = 'equipment' in card2_type or any(re.search(pattern, card2_text) for pattern in equipment_patterns)

    card1_cares_equipment = any(re.search(pattern, card1_text) for pattern in equipment_matters_patterns)
    card2_cares_equipment = any(re.search(pattern, card2_text) for pattern in equipment_matters_patterns)

    # Equipment + equipment matters
    if card1_is_equipment and card2_cares_equipment:
        return {
            'name': 'Equipment Synergy',
            'description': f"{card2['name']} synergizes with equipment like {card1['name']}",
            'value': 3.0,
            'category': 'type_synergy',
            'subcategory': 'equipment_matters'
        }

    if card2_is_equipment and card1_cares_equipment:
        return {
            'name': 'Equipment Synergy',
            'description': f"{card1['name']} synergizes with equipment like {card2['name']}",
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

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if one has landfall and the other ramps/fetches lands
    card1_has_landfall = any(re.search(pattern, card1_text) for pattern in landfall_patterns)
    card2_has_landfall = any(re.search(pattern, card2_text) for pattern in landfall_patterns)

    card1_ramps_lands = any(re.search(pattern, card1_text) for pattern in land_ramp_patterns)
    card2_ramps_lands = any(re.search(pattern, card2_text) for pattern in land_ramp_patterns)

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

    card1_places_counters = any(re.search(pattern, card1_text) for pattern in counter_place_patterns)
    card2_places_counters = any(re.search(pattern, card2_text) for pattern in counter_place_patterns)

    card1_cares_counters = any(re.search(pattern, card1_text) for pattern in counter_matters_patterns)
    card2_cares_counters = any(re.search(pattern, card2_text) for pattern in counter_matters_patterns)

    # Counter doubler patterns (higher value)
    counter_doubler_patterns = [
        r'double.*counters',
        r'twice.*many counters',
        r'if.*would.*counter.*instead.*twice that many',
        r'if.*\+1/\+1 counters? would be placed.*instead.*that many plus',
        r'that many plus one \+1/\+1',
        r'additional \+1/\+1 counter'
    ]

    card1_doubles_counters = any(re.search(pattern, card1_text) for pattern in counter_doubler_patterns)
    card2_doubles_counters = any(re.search(pattern, card2_text) for pattern in counter_doubler_patterns)

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
    """
    # Copy/clone patterns
    copy_patterns = [
        r'\bcopy\b',
        r'\bclone\b',
        r'create a token.*copy',
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

    # Check for creature clones
    card1_is_clone = any(re.search(pattern, card1_text) for pattern in copy_patterns) and 'creature' in card1_type
    card2_is_clone = any(re.search(pattern, card2_text) for pattern in copy_patterns) and 'creature' in card2_type

    # Check for spell copiers
    card1_copies_spells = any(re.search(pattern, card1_text) for pattern in spell_copy_patterns)
    card2_copies_spells = any(re.search(pattern, card2_text) for pattern in spell_copy_patterns)

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

    card1_has_etb = any(re.search(pattern, card1_text) for pattern in high_value_etb_patterns)
    card2_has_etb = any(re.search(pattern, card2_text) for pattern in high_value_etb_patterns)

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
    card1_has_storm = any(re.search(pattern, card1_text) for pattern in storm_patterns)
    card2_has_storm = any(re.search(pattern, card2_text) for pattern in storm_patterns)

    # Check for cheap enablers
    card1_is_enabler = (card1_cmc <= 2 and ('instant' in card1_type or 'sorcery' in card1_type)) and \
                       any(re.search(pattern, card1_text) for pattern in cheap_spell_patterns)
    card2_is_enabler = (card2_cmc <= 2 and ('instant' in card2_type or 'sorcery' in card2_type)) and \
                       any(re.search(pattern, card2_text) for pattern in cheap_spell_patterns)

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
    card1_generates_energy = any(re.search(pattern, card1_text) for pattern in energy_generation_patterns)
    card2_generates_energy = any(re.search(pattern, card2_text) for pattern in energy_generation_patterns)

    card1_consumes_energy = any(re.search(pattern, card1_text) for pattern in energy_consumption_patterns)
    card2_consumes_energy = any(re.search(pattern, card2_text) for pattern in energy_consumption_patterns)

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
    card1_is_tax = any(re.search(pattern, card1_text) for pattern in tax_patterns)
    card2_is_tax = any(re.search(pattern, card2_text) for pattern in tax_patterns)

    # Check for tax payoffs
    card1_is_payoff = any(re.search(pattern, card1_text) for pattern in tax_payoff_patterns)
    card2_is_payoff = any(re.search(pattern, card2_text) for pattern in tax_payoff_patterns)

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


# List of all detection functions
ALL_RULES = [
    detect_etb_triggers,
    detect_sacrifice_synergy,
    detect_mana_color_synergy,
    detect_tribal_synergy,
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
    detect_energy_synergy,
    detect_stax_synergy
] + CARD_ADVANTAGE_SYNERGY_RULES  # Add card advantage synergies
