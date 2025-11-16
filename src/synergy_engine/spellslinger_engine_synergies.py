"""
Spellslinger Engine Synergy Rules

Specialized synergy detection for spellslinger strategies including:
- Jeskai Ascendancy untap engines
- Veyran trigger doubling
- Kindred Discovery card advantage
- Whirlwind of Thought card draw
- Spell copy combos
- Treasure/token generation on spell cast

These are high-impact engine pieces that were missing from the main synergy detection.
"""

import re
from typing import Dict, List, Optional
from src.utils.spellslinger_extractors import (
    extract_untaps_creatures_on_spell,
    extract_doubles_triggers,
    extract_draw_on_creature_event,
    extract_draw_on_spell_cast,
    extract_spell_copy_ability,
    extract_creates_treasures_on_spell,
    extract_creates_tokens_on_spell
)
from src.utils.token_extractors import extract_token_creation


def detect_jeskai_ascendancy_untap_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Jeskai Ascendancy + Cheap Spell synergy.

    Jeskai Ascendancy untaps creatures when you cast noncreature spells.
    This creates pseudo-vigilance and enables:
    - Multiple attacks per turn
    - Reusing tap abilities
    - Going "wide" with creatures

    This is EXTREMELY POWERFUL with cheap spells because you can:
    - Attack, cast spell, untap, attack again
    - Tap for value, cast spell, untap, tap again

    Examples:
    - Jeskai Ascendancy + Brainstorm = Untap all creatures for 1 mana
    - Jeskai Ascendancy + Opt = Untap all creatures, cantrip
    - Jeskai Ascendancy + Lightning Bolt = Untap all creatures, remove threat

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    untap1 = extract_untaps_creatures_on_spell(card1)
    untap2 = extract_untaps_creatures_on_spell(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Card1 has untap effect, Card2 is a spell that triggers it
    if untap1['untaps_on_spell']:
        spell_type = untap1['spell_type']

        # Check if card2 is the right type of spell
        is_trigger_spell = False
        if spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type
        elif spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type
        elif spell_type == 'any':
            is_trigger_spell = True

        if is_trigger_spell:
            # Cheap spells are MORE valuable (can cast multiple per turn)
            base_value = 7.0
            if card2_cmc <= 2:
                value = base_value + 2.0  # 9.0 for cheap spells
            elif card2_cmc <= 4:
                value = base_value + 1.0  # 8.0 for medium spells
            else:
                value = base_value  # 7.0 for expensive spells

            # Cantrips are even better (replace themselves)
            if 'draw a card' in card2_text or 'draw' in card2_text:
                value += 1.0

            spell_desc = "cheap " if card2_cmc <= 2 else ""
            cantrip_desc = " (cantrip)" if 'draw' in card2_text else ""

            return {
                'name': 'Jeskai Ascendancy + Spell',
                'description': f"{card1['name']} untaps all creatures when you cast {card2['name']} ({spell_desc}{card2_cmc} CMC{cantrip_desc})",
                'value': value,
                'category': 'combo_engines',
                'subcategory': 'untap_engine'
            }

    # Card2 has untap effect, Card1 is a spell that triggers it
    if untap2['untaps_on_spell']:
        spell_type = untap2['spell_type']

        is_trigger_spell = False
        if spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type
        elif spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type
        elif spell_type == 'any':
            is_trigger_spell = True

        if is_trigger_spell:
            base_value = 7.0
            if card1_cmc <= 2:
                value = base_value + 2.0
            elif card1_cmc <= 4:
                value = base_value + 1.0
            else:
                value = base_value

            if 'draw a card' in card1_text or 'draw' in card1_text:
                value += 1.0

            spell_desc = "cheap " if card1_cmc <= 2 else ""
            cantrip_desc = " (cantrip)" if 'draw' in card1_text else ""

            return {
                'name': 'Jeskai Ascendancy + Spell',
                'description': f"{card2['name']} untaps all creatures when you cast {card1['name']} ({spell_desc}{card1_cmc} CMC{cantrip_desc})",
                'value': value,
                'category': 'combo_engines',
                'subcategory': 'untap_engine'
            }

    return None


def detect_jeskai_ascendancy_creature_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Jeskai Ascendancy + Creature with Tap Ability.

    Jeskai Ascendancy untaps creatures, so creatures with tap abilities
    can be used multiple times per turn.

    Examples:
    - Jeskai Ascendancy + mana dork = Tap for mana, cast spell, untap, tap again
    - Jeskai Ascendancy + utility creature = Use ability, cast spell, use again

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    untap1 = extract_untaps_creatures_on_spell(card1)
    untap2 = extract_untaps_creatures_on_spell(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Card1 has untap effect, Card2 is a creature with tap ability
    if untap1['untaps_on_spell'] and 'creature' in card2_type:
        if '{t}:' in card2_text or 'tap:' in card2_text or '{t},' in card2_text:
            return {
                'name': 'Untap Engine + Tap Ability',
                'description': f"{card1['name']} untaps {card2['name']}, allowing repeated use of its tap ability",
                'value': 6.0,
                'category': 'combo_engines',
                'subcategory': 'tap_untap_engine'
            }

    # Card2 has untap effect, Card1 is a creature with tap ability
    if untap2['untaps_on_spell'] and 'creature' in card1_type:
        if '{t}:' in card1_text or 'tap:' in card1_text or '{t},' in card1_text:
            return {
                'name': 'Untap Engine + Tap Ability',
                'description': f"{card2['name']} untaps {card1['name']}, allowing repeated use of its tap ability",
                'value': 6.0,
                'category': 'combo_engines',
                'subcategory': 'tap_untap_engine'
            }

    return None


def detect_veyran_trigger_doubling_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Veyran (trigger doubling) + Magecraft/Prowess synergy.

    Veyran doubles magecraft triggers, which is HUGE for spellslinger decks.
    This effectively doubles all your payoffs from casting spells.

    Examples:
    - Veyran + Storm-Kiln Artist = 2 treasures per spell instead of 1
    - Veyran + Kykar = 2 tokens per spell instead of 1
    - Veyran + Prowess creatures = +2/+2 instead of +1/+1

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    doubles1 = extract_doubles_triggers(card1)
    doubles2 = extract_doubles_triggers(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card1_keywords = [kw.lower() for kw in card1.get('keywords', [])]
    card2_keywords = [kw.lower() for kw in card2.get('keywords', [])]

    # Card1 doubles triggers
    if doubles1['doubles_triggers']:
        trigger_type = doubles1['trigger_type']

        # Check if card2 has relevant triggers
        has_relevant_trigger = False
        trigger_desc = ""

        if trigger_type == 'spell_triggers':
            # Check for magecraft, prowess, or spell-cast triggers
            if 'magecraft' in card2_text:
                has_relevant_trigger = True
                trigger_desc = "magecraft trigger"
            elif 'prowess' in card2_keywords or 'prowess' in card2_text:
                has_relevant_trigger = True
                trigger_desc = "prowess"
            elif 'whenever you cast' in card2_text or 'whenever you cast or copy' in card2_text:
                has_relevant_trigger = True
                trigger_desc = "spell-cast trigger"

        if has_relevant_trigger:
            # Determine value based on what gets doubled
            value = 10.0  # Base value for doubling any trigger

            # Treasure generation is VERY high value
            if 'treasure' in card2_text:
                value = 12.0
                trigger_desc = "treasure creation"
            # Token generation is high value
            elif 'create' in card2_text and 'token' in card2_text:
                value = 11.0
                trigger_desc = "token creation"
            # Prowess is good value
            elif 'prowess' in card2_keywords or 'prowess' in card2_text:
                value = 10.0
                trigger_desc = "prowess triggers"

            return {
                'name': 'Trigger Doubling + Magecraft',
                'description': f"{card1['name']} doubles {card2['name']}'s {trigger_desc} (2x value!)",
                'value': value,
                'category': 'combo_engines',
                'subcategory': 'trigger_multiplication'
            }

    # Card2 doubles triggers
    if doubles2['doubles_triggers']:
        trigger_type = doubles2['trigger_type']

        has_relevant_trigger = False
        trigger_desc = ""

        if trigger_type == 'spell_triggers':
            if 'magecraft' in card1_text:
                has_relevant_trigger = True
                trigger_desc = "magecraft trigger"
            elif 'prowess' in card1_keywords or 'prowess' in card1_text:
                has_relevant_trigger = True
                trigger_desc = "prowess"
            elif 'whenever you cast' in card1_text or 'whenever you cast or copy' in card1_text:
                has_relevant_trigger = True
                trigger_desc = "spell-cast trigger"

        if has_relevant_trigger:
            value = 10.0

            if 'treasure' in card1_text:
                value = 12.0
                trigger_desc = "treasure creation"
            elif 'create' in card1_text and 'token' in card1_text:
                value = 11.0
                trigger_desc = "token creation"
            elif 'prowess' in card1_keywords or 'prowess' in card1_text:
                value = 10.0
                trigger_desc = "prowess triggers"

            return {
                'name': 'Trigger Doubling + Magecraft',
                'description': f"{card2['name']} doubles {card1['name']}'s {trigger_desc} (2x value!)",
                'value': value,
                'category': 'combo_engines',
                'subcategory': 'trigger_multiplication'
            }

    return None


def detect_kindred_discovery_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Kindred Discovery + Tribal Creature/Token synergy.

    Kindred Discovery draws cards when creatures of chosen type enter or attack.
    This is MASSIVE card advantage in tribal decks.

    Examples:
    - Kindred Discovery (choose Allies) + Ally creatures = Draw on ETB and attack
    - Kindred Discovery + Token generators = Draw for each token created

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    draw1 = extract_draw_on_creature_event(card1)
    draw2 = extract_draw_on_creature_event(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()

    # Card1 is Kindred Discovery, Card2 is a creature or token generator
    if draw1['draws_on_creature_event'] and draw1['tribal']:
        # Check if card2 is a creature
        if 'creature' in card2_type:
            return {
                'name': 'Kindred Discovery + Tribal Creature',
                'description': f"{card1['name']} draws a card when {card2['name']} enters or attacks",
                'value': 8.0,  # Very high value
                'category': 'card_advantage',
                'subcategory': 'tribal_draw'
            }

        # Check if card2 creates tokens
        token2 = extract_token_creation(card2)
        if token2.get('creates_tokens'):
            # TOKEN GENERATORS ARE HUGE VALUE (draw multiple cards)
            return {
                'name': 'Kindred Discovery + Token Generator',
                'description': f"{card1['name']} draws cards when {card2['name']} creates tokens (if chosen type matches)",
                'value': 9.0,  # Even higher for token generators
                'category': 'card_advantage',
                'subcategory': 'tribal_draw_tokens'
            }

    # Card2 is Kindred Discovery, Card1 is a creature or token generator
    if draw2['draws_on_creature_event'] and draw2['tribal']:
        if 'creature' in card1_type:
            return {
                'name': 'Kindred Discovery + Tribal Creature',
                'description': f"{card2['name']} draws a card when {card1['name']} enters or attacks",
                'value': 8.0,
                'category': 'card_advantage',
                'subcategory': 'tribal_draw'
            }

        token1 = extract_token_creation(card1)
        if token1.get('creates_tokens'):
            return {
                'name': 'Kindred Discovery + Token Generator',
                'description': f"{card2['name']} draws cards when {card1['name']} creates tokens (if chosen type matches)",
                'value': 9.0,
                'category': 'card_advantage',
                'subcategory': 'tribal_draw_tokens'
            }

    return None


def detect_whirlwind_of_thought_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Whirlwind of Thought + Noncreature Spell synergy.

    Whirlwind of Thought draws a card whenever you cast a noncreature spell.
    This turns every spell into a cantrip, which is INSANE card advantage.

    Examples:
    - Whirlwind of Thought + Brainstorm = Draw 2 cards (1 from Brainstorm, 1 from Whirlwind)
    - Whirlwind of Thought + Lightning Bolt = Remove threat AND draw a card

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    draw1 = extract_draw_on_spell_cast(card1)
    draw2 = extract_draw_on_spell_cast(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Card1 draws on spell cast, Card2 is a spell
    if draw1['draws_on_spell']:
        spell_type = draw1['spell_type']

        is_trigger_spell = False
        if spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type
        elif spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type

        if is_trigger_spell:
            # Base value
            value = 7.0

            # Cheap spells are MORE valuable (can cast more per turn)
            if card2_cmc <= 2:
                value += 1.5

            # Cantrips are EXTREME value (draw 2 cards!)
            if 'draw a card' in card2_text or 'draw' in card2_text:
                value += 1.5
                cantrip_note = " (draws 2 cards total!)"
            else:
                cantrip_note = ""

            return {
                'name': 'Spell Draw Engine + Spell',
                'description': f"{card1['name']} draws a card when you cast {card2['name']}{cantrip_note}",
                'value': value,
                'category': 'card_advantage',
                'subcategory': 'spell_draw_engine'
            }

    # Card2 draws on spell cast, Card1 is a spell
    if draw2['draws_on_spell']:
        spell_type = draw2['spell_type']

        is_trigger_spell = False
        if spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type
        elif spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type

        if is_trigger_spell:
            value = 7.0

            if card1_cmc <= 2:
                value += 1.5

            if 'draw a card' in card1_text or 'draw' in card1_text:
                value += 1.5
                cantrip_note = " (draws 2 cards total!)"
            else:
                cantrip_note = ""

            return {
                'name': 'Spell Draw Engine + Spell',
                'description': f"{card2['name']} draws a card when you cast {card1['name']}{cantrip_note}",
                'value': value,
                'category': 'card_advantage',
                'subcategory': 'spell_draw_engine'
            }

    return None


def detect_spell_copy_extra_turn_combo(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Spell Copy + Extra Turn = Infinite Turns combo.

    Copying an extra turn spell that shuffles back into library = infinite turns.

    Examples:
    - Narset's Reversal + Nexus of Fate = Copy Nexus, bounce original back to hand, repeat
    - Any spell copy + Time Warp variants

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    copy1 = extract_spell_copy_ability(card1)
    copy2 = extract_spell_copy_ability(card2)

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check for extra turn spells
    extra_turn_patterns = [
        'take an extra turn',
        'take another turn',
        'extra turn after this one',
    ]

    card1_is_extra_turn = any(pattern in card1_text for pattern in extra_turn_patterns)
    card2_is_extra_turn = any(pattern in card2_text for pattern in extra_turn_patterns)

    # Card1 copies spells, Card2 is extra turn
    if copy1['copies_spells'] and card2_is_extra_turn:
        # Check if it shuffles back (Nexus of Fate) or bounces (Narset's Reversal)
        if 'shuffle' in card2_text or copy1['bounces_original']:
            return {
                'name': 'Spell Copy + Extra Turns = INFINITE',
                'description': f"{card1['name']} can copy {card2['name']} for infinite turns (POTENTIAL GAME-WINNING COMBO)",
                'value': 50.0,  # INFINITE COMBO
                'category': 'combo',
                'subcategory': 'infinite_turns',
                'combo': True
            }
        else:
            # Still good value even without infinite
            return {
                'name': 'Spell Copy + Extra Turns',
                'description': f"{card1['name']} can copy {card2['name']} for multiple extra turns",
                'value': 12.0,
                'category': 'combo_engines',
                'subcategory': 'extra_turns'
            }

    # Card2 copies spells, Card1 is extra turn
    if copy2['copies_spells'] and card1_is_extra_turn:
        if 'shuffle' in card1_text or copy2['bounces_original']:
            return {
                'name': 'Spell Copy + Extra Turns = INFINITE',
                'description': f"{card2['name']} can copy {card1['name']} for infinite turns (POTENTIAL GAME-WINNING COMBO)",
                'value': 50.0,  # INFINITE COMBO
                'category': 'combo',
                'subcategory': 'infinite_turns',
                'combo': True
            }
        else:
            return {
                'name': 'Spell Copy + Extra Turns',
                'description': f"{card2['name']} can copy {card1['name']} for multiple extra turns",
                'value': 12.0,
                'category': 'combo_engines',
                'subcategory': 'extra_turns'
            }

    return None


def detect_treasure_generation_spell_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Treasure Generation on Spell Cast + Cheap Spells.

    Creating treasures when casting spells = mana for more spells = explosive turns.

    Examples:
    - Storm-Kiln Artist + cheap spells = Ramp into bigger spells
    - Storm-Kiln Artist + cantrips = "Free" spells (treasure pays for next spell)

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    treasure1 = extract_creates_treasures_on_spell(card1)
    treasure2 = extract_creates_treasures_on_spell(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Card1 creates treasures, Card2 is a spell
    if treasure1['creates_treasures_on_spell']:
        spell_type = treasure1['spell_type']

        is_trigger_spell = False
        if spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type
        elif spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type

        if is_trigger_spell:
            # Cheap spells are BEST (treasure can pay for next spell)
            if card2_cmc <= 2:
                value = 7.0
                desc = f"{card1['name']} creates treasure when you cast {card2['name']} ({card2_cmc} CMC - treasure pays for next spell!)"
            else:
                value = 5.0
                desc = f"{card1['name']} creates treasure when you cast {card2['name']}"

            return {
                'name': 'Treasure Generation + Spell',
                'description': desc,
                'value': value,
                'category': 'ramp',
                'subcategory': 'spell_ramp'
            }

    # Card2 creates treasures, Card1 is a spell
    if treasure2['creates_treasures_on_spell']:
        spell_type = treasure2['spell_type']

        is_trigger_spell = False
        if spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type
        elif spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type

        if is_trigger_spell:
            if card1_cmc <= 2:
                value = 7.0
                desc = f"{card2['name']} creates treasure when you cast {card1['name']} ({card1_cmc} CMC - treasure pays for next spell!)"
            else:
                value = 5.0
                desc = f"{card2['name']} creates treasure when you cast {card1['name']}"

            return {
                'name': 'Treasure Generation + Spell',
                'description': desc,
                'value': value,
                'category': 'ramp',
                'subcategory': 'spell_ramp'
            }

    return None


def detect_token_generation_spell_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect Token Generation on Spell Cast + Cheap Spells.

    Creating tokens when casting spells builds an army while slinging spells.

    Examples:
    - Kykar + cheap spells = Build spirit army
    - Kykar + cantrips = "Free" tokens

    Args:
        card1: First card
        card2: Second card

    Returns:
        Synergy dict or None
    """
    token1 = extract_creates_tokens_on_spell(card1)
    token2 = extract_creates_tokens_on_spell(card2)

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Card1 creates tokens, Card2 is a spell
    if token1['creates_tokens_on_spell']:
        spell_type = token1['spell_type']

        is_trigger_spell = False
        if spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type
        elif spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card2_type or 'sorcery' in card2_type

        if is_trigger_spell:
            # Cheap spells = more tokens
            if card2_cmc <= 2:
                value = 6.0
            else:
                value = 4.0

            return {
                'name': 'Token Generation + Spell',
                'description': f"{card1['name']} creates token when you cast {card2['name']}",
                'value': value,
                'category': 'tokens',
                'subcategory': 'spell_tokens'
            }

    # Card2 creates tokens, Card1 is a spell
    if token2['creates_tokens_on_spell']:
        spell_type = token2['spell_type']

        is_trigger_spell = False
        if spell_type == 'instant_sorcery':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type
        elif spell_type == 'noncreature':
            is_trigger_spell = 'instant' in card1_type or 'sorcery' in card1_type

        if is_trigger_spell:
            if card1_cmc <= 2:
                value = 6.0
            else:
                value = 4.0

            return {
                'name': 'Token Generation + Spell',
                'description': f"{card2['name']} creates token when you cast {card1['name']}",
                'value': value,
                'category': 'tokens',
                'subcategory': 'spell_tokens'
            }

    return None


# List of all spellslinger engine synergy rules to export
SPELLSLINGER_ENGINE_SYNERGY_RULES = [
    detect_jeskai_ascendancy_untap_synergy,
    detect_jeskai_ascendancy_creature_synergy,
    detect_veyran_trigger_doubling_synergy,
    detect_kindred_discovery_synergy,
    detect_whirlwind_of_thought_synergy,
    detect_spell_copy_extra_turn_combo,
    detect_treasure_generation_spell_synergy,
    detect_token_generation_spell_synergy,
]
