"""
Synergy Detection Rules
Individual rule functions for detecting different types of synergies between cards
"""

import re
from typing import Dict, List, Optional


def detect_etb_triggers(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect ETB (Enters the Battlefield) trigger synergies

    Returns synergy if one card has ETB ability and another can trigger it
    """
    etb_keywords = ['enters the battlefield', 'when .* enters', 'whenever .* enters']
    flicker_keywords = ['exile.*return', 'blink', 'flicker', 'return.*to the battlefield']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check if card1 has ETB and card2 can trigger it
    card1_has_etb = any(re.search(kw, card1_text) for kw in etb_keywords)
    card2_can_trigger = any(re.search(kw, card2_text) for kw in flicker_keywords)

    if card1_has_etb and card2_can_trigger:
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

    if card2_has_etb and card1_can_trigger:
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
    sacrifice_outlet_keywords = ['sacrifice', 'as an additional cost', 'you may sacrifice']
    death_trigger_keywords = ['when .* dies', 'whenever .* dies', 'when .* is put into a graveyard']
    token_generation = ['create.*token', 'put.*token']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_is_outlet = any(kw in card1_text for kw in sacrifice_outlet_keywords)
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
    card2_is_outlet = any(kw in card2_text for kw in sacrifice_outlet_keywords)
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
    """Detect color identity and mana synergies"""
    colors1 = set(card1.get('colors', []))
    colors2 = set(card2.get('colors', []))

    if not colors1 or not colors2:
        return None

    # Calculate color overlap
    overlap = colors1.intersection(colors2)
    overlap_ratio = len(overlap) / max(len(colors1), len(colors2))

    if overlap_ratio >= 0.5:
        return {
            'name': 'Color Synergy',
            'description': f"Cards share {len(overlap)} color(s): {', '.join(overlap)}",
            'value': overlap_ratio * 2.0,
            'category': 'mana_synergy',
            'subcategory': 'color_match'
        }

    return None


def detect_tribal_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """Detect tribal synergies based on creature types"""
    card1_types = card1.get('card_types', {})
    card2_types = card2.get('card_types', {})

    card1_subtypes = set(card1_types.get('subtypes', []))
    card2_subtypes = set(card2_types.get('subtypes', []))

    # Check if one card cares about a type the other has
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    for subtype in card2_subtypes:
        if subtype.lower() in card1_text:
            return {
                'name': 'Tribal Synergy',
                'description': f"{card1['name']} cares about {subtype}s, {card2['name']} is a {subtype}",
                'value': 3.0,
                'category': 'benefits',
                'subcategory': 'tribal'
            }

    for subtype in card1_subtypes:
        if subtype.lower() in card2_text:
            return {
                'name': 'Tribal Synergy',
                'description': f"{card2['name']} cares about {subtype}s, {card1['name']} is a {subtype}",
                'value': 3.0,
                'category': 'benefits',
                'subcategory': 'tribal'
            }

    # Check for shared creature types
    shared_types = card1_subtypes.intersection(card2_subtypes)
    if shared_types and 'Creature' in card1_types.get('main_types', []) and 'Creature' in card2_types.get('main_types', []):
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
    """Detect mana ramp synergies"""
    ramp_keywords = ['search.*library.*land', 'put.*land.*battlefield', 'add.*mana']
    high_cmc_threshold = 6

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_is_ramp = any(re.search(kw, card1_text) for kw in ramp_keywords) or \
                    ('Land' in card1.get('type_line', '') and 'add' in card1_text)
    card2_is_ramp = any(re.search(kw, card2_text) for kw in ramp_keywords) or \
                    ('Land' in card2.get('type_line', '') and 'add' in card2_text)

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
    type_matters = {
        'artifact': 'artifact_matters',
        'enchantment': 'enchantment_matters',
        'creature': 'creature_matters',
        'instant': 'instant_sorcery_matters',
        'sorcery': 'instant_sorcery_matters',
        'planeswalker': 'planeswalker_synergy',
        'land': 'land_matters'
    }

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    for card_type, subcategory in type_matters.items():
        # Check if card1 cares about card_type and card2 is that type
        if card_type in card1_text and card_type in card2_type:
            return {
                'name': f'{card_type.title()} Synergy',
                'description': f"{card1['name']} cares about {card_type}s, {card2['name']} is a {card_type}",
                'value': 2.5,
                'category': 'type_synergy',
                'subcategory': subcategory
            }

        # Check reverse
        if card_type in card2_text and card_type in card1_type:
            return {
                'name': f'{card_type.title()} Synergy',
                'description': f"{card2['name']} cares about {card_type}s, {card1['name']} is a {card_type}",
                'value': 2.5,
                'category': 'type_synergy',
                'subcategory': subcategory
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
        if 'untap' in card1_text and 'mana' in card2_text:
            return {
                'name': 'Potential Infinite Mana',
                'description': f"Potential infinite mana combo between {card1['name']} and {card2['name']}",
                'value': 5.0,
                'category': 'combo',
                'subcategory': 'infinite_mana'
            }

        # General combo potential
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
    token_generation = ['create.*token', 'put.*token']
    token_payoff = ['whenever.*token', 'token.*you control', 'for each.*token']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    card1_generates = any(re.search(kw, card1_text) for kw in token_generation)
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
    card2_generates = any(re.search(kw, card2_text) for kw in token_generation)
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
    """Detect graveyard and recursion synergies"""
    graveyard_fill = ['mill', 'put.*into.*graveyard', 'discard']
    graveyard_payoff = ['from.*graveyard', 'return.*from.*graveyard', 'threshold', 'delve', 'flashback']

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
    detect_graveyard_synergy
]
