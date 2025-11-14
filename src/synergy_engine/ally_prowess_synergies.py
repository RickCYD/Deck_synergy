"""
Ally and Prowess Synergy Rules

Specialized synergy detection for Ally tribal decks and Prowess-based strategies.
These synergies were missing from the main rules and caused undervaluation of
ally/prowess decks.
"""

import re
from typing import Dict, Optional
from src.synergy_engine.regex_cache import search_cached
from src.utils.etb_extractors import (
    extract_rally_triggers,
    extract_creature_etb_triggers,
    extract_ally_matters,
    extract_creates_ally_tokens
)
from src.utils.token_extractors import extract_token_creation


def detect_rally_token_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Rally + Token Creation synergy.

    Rally triggers when creatures enter. Token creation makes creatures enter.
    This is a HIGH VALUE synergy for Ally tribal decks.

    Examples:
    - Chasm Guide (rally) + Gideon, Ally of Zendikar (creates ally tokens)
    - Lantern Scout (rally) + Kykar, Wind's Fury (creates creature tokens)

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    rally1 = extract_rally_triggers(card1)
    rally2 = extract_rally_triggers(card2)

    token1 = extract_token_creation(card1)
    token2 = extract_token_creation(card2)

    creates_ally_tokens1 = extract_creates_ally_tokens(card1)
    creates_ally_tokens2 = extract_creates_ally_tokens(card2)

    # Card1 has rally, Card2 creates tokens
    if rally1['has_rally'] and token2.get('creates_tokens', False):
        # Extra value if the tokens are Allies
        value = 6.0 if creates_ally_tokens2 else 4.0
        effect = rally1['effect_type'] or 'triggers'

        return {
            'name': 'Rally + Token Creation',
            'description': f"{card1['name']}'s rally ({effect}) triggers when {card2['name']} creates tokens",
            'value': value,
            'category': 'triggers',
            'subcategory': 'rally_token_synergy'
        }

    # Card2 has rally, Card1 creates tokens
    if rally2['has_rally'] and token1.get('creates_tokens', False):
        value = 6.0 if creates_ally_tokens1 else 4.0
        effect = rally2['effect_type'] or 'triggers'

        return {
            'name': 'Rally + Token Creation',
            'description': f"{card2['name']}'s rally ({effect}) triggers when {card1['name']} creates tokens",
            'value': value,
            'category': 'triggers',
            'subcategory': 'rally_token_synergy'
        }

    return None


def detect_prowess_cheap_spell_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Prowess + Cheap Spell synergy.

    Prowess = "Whenever you cast a noncreature spell, this creature gets +1/+1"
    Cheap spells (CMC <= 2) = easy to cast multiple per turn to grow prowess creatures

    This is a VERY HIGH VALUE synergy because:
    - Cantrips replace themselves, making them "free" prowess triggers
    - Multiple cheap spells per turn = exponential growth
    - Enables aggressive combat strategies

    Examples:
    - Bria, Riptide Rogue (prowess) + Brainstorm (1 CMC cantrip)
    - Narset, Enlightened Exile (prowess) + Lightning Bolt (1 CMC removal)

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 has prowess
    card1_has_prowess = 'prowess' in card1_keywords or 'prowess' in card1_text

    # Check if card2 is a cheap noncreature spell
    card2_is_instant_sorcery = 'instant' in card2_type or 'sorcery' in card2_type
    card2_is_cheap = card2_cmc <= 2
    card2_is_cantrip = 'draw a card' in card2_text or 'draw' in card2_text

    if card1_has_prowess and card2_is_instant_sorcery and card2_is_cheap:
        # Cantrips are worth more because they replace themselves
        value = 5.0 if card2_is_cantrip else 4.0

        spell_type = "cantrip" if card2_is_cantrip else "spell"

        return {
            'name': 'Prowess + Cheap Spell',
            'description': f"{card1['name']} (prowess) grows when you cast {card2['name']} ({card2_cmc} CMC {spell_type})",
            'value': value,
            'category': 'type_synergy',
            'subcategory': 'prowess_synergy'
        }

    # Check reverse (card2 has prowess, card1 is cheap spell)
    card2_has_prowess = 'prowess' in card2_keywords or 'prowess' in card2_text
    card1_is_instant_sorcery = 'instant' in card1_type or 'sorcery' in card1_type
    card1_is_cheap = card1_cmc <= 2
    card1_is_cantrip = 'draw a card' in card1_text or 'draw' in card1_text

    if card2_has_prowess and card1_is_instant_sorcery and card1_is_cheap:
        value = 5.0 if card1_is_cantrip else 4.0
        spell_type = "cantrip" if card1_is_cantrip else "spell"

        return {
            'name': 'Prowess + Cheap Spell',
            'description': f"{card2['name']} (prowess) grows when you cast {card1['name']} ({card1_cmc} CMC {spell_type})",
            'value': value,
            'category': 'type_synergy',
            'subcategory': 'prowess_synergy'
        }

    return None


def detect_rally_rally_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Rally + Rally synergy (multiple rally triggers).

    When you have multiple rally cards, each creature you play triggers ALL of them.
    This creates a multiplicative effect that's very powerful.

    Examples:
    - Chasm Guide (rally: haste) + Lantern Scout (rally: lifelink)
      = Each ally you play grants haste AND lifelink to your team

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    rally1 = extract_rally_triggers(card1)
    rally2 = extract_rally_triggers(card2)

    if rally1['has_rally'] and rally2['has_rally']:
        effect1 = rally1['effect_type'] or 'triggers'
        effect2 = rally2['effect_type'] or 'triggers'

        return {
            'name': 'Multiple Rally Triggers',
            'description': f"Each Ally triggers both {card1['name']} ({effect1}) and {card2['name']} ({effect2})",
            'value': 5.0,
            'category': 'triggers',
            'subcategory': 'rally_stacking'
        }

    return None


def detect_ally_tribal_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Ally Tribal synergy.

    Cards that care about Allies + Ally creatures.

    Examples:
    - Banner of Kinship (choose Allies) + any Ally creature
    - Obelisk of Urd (choose Allies) + Ally creatures

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    ally1 = extract_ally_matters(card1)
    ally2 = extract_ally_matters(card2)

    # Card1 cares about allies, Card2 is an ally
    if ally1['cares_about_allies'] and ally2['is_ally']:
        effect = ally1['ally_effect_type'] or 'benefits'

        return {
            'name': 'Ally Tribal Synergy',
            'description': f"{card1['name']} ({effect}) benefits {card2['name']} (Ally)",
            'value': 4.0,
            'category': 'tribal',
            'subcategory': 'ally_tribal'
        }

    # Card2 cares about allies, Card1 is an ally
    if ally2['cares_about_allies'] and ally1['is_ally']:
        effect = ally2['ally_effect_type'] or 'benefits'

        return {
            'name': 'Ally Tribal Synergy',
            'description': f"{card2['name']} ({effect}) benefits {card1['name']} (Ally)",
            'value': 4.0,
            'category': 'tribal',
            'subcategory': 'ally_tribal'
        }

    return None


def detect_creature_etb_trigger_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect general creature ETB trigger synergies.

    Cards that trigger when creatures enter + token creators.

    Examples:
    - Impact Tremors (damage on ETB) + Kykar (creates tokens)
    - Warleader's Call (damage/buff on ETB) + token generators

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    etb1 = extract_creature_etb_triggers(card1)
    etb2 = extract_creature_etb_triggers(card2)

    token1 = extract_token_creation(card1)
    token2 = extract_token_creation(card2)

    # Card1 has ETB trigger, Card2 creates tokens
    if etb1['has_creature_etb_trigger'] and token2.get('creates_tokens', False):
        effect = etb1['effect_type'] or 'triggers'

        return {
            'name': 'ETB Trigger + Tokens',
            'description': f"{card1['name']}'s ETB trigger ({effect}) activates when {card2['name']} creates tokens",
            'value': 5.0,
            'category': 'triggers',
            'subcategory': 'etb_token_synergy'
        }

    # Card2 has ETB trigger, Card1 creates tokens
    if etb2['has_creature_etb_trigger'] and token1.get('creates_tokens', False):
        effect = etb2['effect_type'] or 'triggers'

        return {
            'name': 'ETB Trigger + Tokens',
            'description': f"{card2['name']}'s ETB trigger ({effect}) activates when {card1['name']} creates tokens",
            'value': 5.0,
            'category': 'triggers',
            'subcategory': 'etb_token_synergy'
        }

    return None


def detect_spellslinger_cantrip_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Spellslinger + Cantrip synergy.

    Spellslinger payoffs (triggers on casting instants/sorceries) +
    Cantrips (cheap spells that draw a card).

    Cantrips are VERY HIGH VALUE for spellslinger because:
    - They replace themselves (card neutral)
    - Can be cast multiple times per turn cycle
    - Enable "storm" turns with many triggers

    Examples:
    - Jeskai Ascendancy (spellslinger) + Brainstorm (cantrip)
    - Kykar, Wind's Fury (creates tokens on noncreature spells) + Opt (cantrip)

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Spellslinger trigger patterns
    spellslinger_patterns = [
        r'whenever you cast an instant',
        r'whenever you cast a sorcery',
        r'whenever you cast a noncreature',
        r'whenever you cast an instant or sorcery',
        r'magecraft',
    ]

    card1_is_spellslinger = any(search_cached(pattern, card1_text) for pattern in spellslinger_patterns)
    card2_is_spellslinger = any(search_cached(pattern, card2_text) for pattern in spellslinger_patterns)

    # Cantrip = instant/sorcery that draws a card, CMC <= 2
    card1_is_cantrip = (
        ('instant' in card1_type or 'sorcery' in card1_type) and
        ('draw a card' in card1_text or 'draw' in card1_text) and
        card1_cmc <= 2
    )

    card2_is_cantrip = (
        ('instant' in card2_type or 'sorcery' in card2_type) and
        ('draw a card' in card2_text or 'draw' in card2_text) and
        card2_cmc <= 2
    )

    # Card1 is spellslinger, Card2 is cantrip
    if card1_is_spellslinger and card2_is_cantrip:
        return {
            'name': 'Spellslinger + Cantrip',
            'description': f"{card1['name']} triggers on spells, {card2['name']} ({card2_cmc} CMC cantrip) fuels it efficiently",
            'value': 6.0,  # High value because cantrips are self-replacing
            'category': 'type_synergy',
            'subcategory': 'spellslinger_cantrip'
        }

    # Card2 is spellslinger, Card1 is cantrip
    if card2_is_spellslinger and card1_is_cantrip:
        return {
            'name': 'Spellslinger + Cantrip',
            'description': f"{card2['name']} triggers on spells, {card1['name']} ({card1_cmc} CMC cantrip) fuels it efficiently",
            'value': 6.0,
            'category': 'type_synergy',
            'subcategory': 'spellslinger_cantrip'
        }

    return None


# List of all ally/prowess synergy rules to export
ALLY_PROWESS_SYNERGY_RULES = [
    detect_rally_token_synergy,
    detect_prowess_cheap_spell_synergy,
    detect_rally_rally_synergy,
    detect_ally_tribal_synergy,
    detect_creature_etb_trigger_synergy,
    detect_spellslinger_cantrip_synergy,
]
