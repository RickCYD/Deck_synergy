"""
Spellslinger Engine Extractors

Extracts mechanics specific to spellslinger strategies:
- Untap effects on spell cast
- Trigger doubling/multiplication
- Draw on creature ETB/attack
- Draw on spell cast
- Spell copying
"""

import re
from typing import Dict, List, Optional


def extract_untaps_creatures_on_spell(card: Dict) -> Dict:
    """
    Extract untap creature effects triggered by casting spells.

    Examples:
    - Jeskai Ascendancy: "Whenever you cast a noncreature spell, creatures you control get +1/+1 until end of turn. Untap those creatures."
    - Similar untap effects

    Returns:
        {
            'untaps_on_spell': bool,
            'spell_type': str,  # 'noncreature', 'instant_sorcery', 'any'
            'buff': Optional[str],  # e.g., '+1/+1'
            'untap_target': str  # 'creatures_you_control', 'all_creatures', etc.
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'untaps_on_spell': False,
        'spell_type': None,
        'buff': None,
        'untap_target': None
    }

    # Pattern: "Whenever you cast a [spell type], ... untap"
    untap_on_spell_patterns = [
        (r'whenever you cast a noncreature spell.*untap', 'noncreature'),
        (r'whenever you cast an instant or sorcery.*untap', 'instant_sorcery'),
        (r'whenever you cast a spell.*untap', 'any'),
    ]

    for pattern, spell_type in untap_on_spell_patterns:
        if re.search(pattern, oracle_text):
            result['untaps_on_spell'] = True
            result['spell_type'] = spell_type

            # Check for buff
            buff_match = re.search(r'get (\+\d+/\+\d+)', oracle_text)
            if buff_match:
                result['buff'] = buff_match.group(1)

            # Check what gets untapped
            if 'creatures you control' in oracle_text or 'those creatures' in oracle_text:
                result['untap_target'] = 'creatures_you_control'
            elif 'all creatures' in oracle_text:
                result['untap_target'] = 'all_creatures'

            break

    return result


def extract_doubles_triggers(card: Dict) -> Dict:
    """
    Extract trigger doubling/multiplication effects.

    Examples:
    - Veyran, Voice of Duality: "If you casting or copying an instant or sorcery spell causes a triggered ability... that ability triggers an additional time."
    - Panharmonicon: "If an artifact or creature entering the battlefield causes a triggered ability to trigger, that ability triggers an additional time."

    Returns:
        {
            'doubles_triggers': bool,
            'trigger_type': str,  # 'spell_triggers', 'etb', 'any'
            'multiplier': int  # Usually 2 (double), but could be more
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'doubles_triggers': False,
        'trigger_type': None,
        'multiplier': 2
    }

    # Veyran pattern - doubles spell-cast triggers (check both singular and plural)
    if 'casting or copying an instant or sorcery' in oracle_text and ('trigger an additional time' in oracle_text or 'triggers an additional time' in oracle_text):
        result['doubles_triggers'] = True
        result['trigger_type'] = 'spell_triggers'
        return result

    # Also check for old pattern (in case of oracle text variations)
    if 'magecraft' in oracle_text and ('trigger an additional time' in oracle_text or 'triggers an additional time' in oracle_text):
        result['doubles_triggers'] = True
        result['trigger_type'] = 'spell_triggers'
        return result

    # ETB doubling (Panharmonicon)
    if 'entering the battlefield' in oracle_text and ('trigger an additional time' in oracle_text or 'triggers an additional time' in oracle_text):
        result['doubles_triggers'] = True
        result['trigger_type'] = 'etb'
        return result

    # Generic trigger doubling
    if 'triggered ability' in oracle_text and ('trigger an additional time' in oracle_text or 'triggers an additional time' in oracle_text):
        result['doubles_triggers'] = True
        result['trigger_type'] = 'any'
        return result

    return result


def extract_draw_on_creature_event(card: Dict) -> Dict:
    """
    Extract draw effects triggered by creature events (ETB, attack, etc).

    Examples:
    - Kindred Discovery: "Whenever a creature of the chosen type enters the battlefield or attacks, you may draw a card."
    - Elemental Bond: "Whenever a creature with power 3 or greater enters the battlefield under your control, draw a card."

    Returns:
        {
            'draws_on_creature_event': bool,
            'event_type': str,  # 'etb', 'attack', 'etb_or_attack'
            'condition': Optional[str],  # 'chosen_type', 'power_3_or_greater', etc.
            'tribal': bool  # Whether it cares about creature type
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'draws_on_creature_event': False,
        'event_type': None,
        'condition': None,
        'tribal': False
    }

    # Kindred Discovery pattern
    if 'choose a creature type' in oracle_text:
        # Check for "enters or attacks" or "enters the battlefield or attacks"
        if ('enters or attacks' in oracle_text or 'enters the battlefield or attacks' in oracle_text) and 'draw a card' in oracle_text:
            result['draws_on_creature_event'] = True
            result['event_type'] = 'etb_or_attack'
            result['condition'] = 'chosen_type'
            result['tribal'] = True
            return result

    # Generic creature ETB draw
    if re.search(r'whenever a creature.*enters the battlefield.*draw', oracle_text):
        result['draws_on_creature_event'] = True
        result['event_type'] = 'etb'

        # Check for power condition
        if 'power 3 or greater' in oracle_text or 'power 4 or greater' in oracle_text:
            result['condition'] = 'power_condition'

        return result

    # Attack draw
    if re.search(r'whenever.*creature.*attacks.*draw', oracle_text):
        result['draws_on_creature_event'] = True
        result['event_type'] = 'attack'
        return result

    return result


def extract_draw_on_spell_cast(card: Dict) -> Dict:
    """
    Extract draw effects triggered by casting spells.

    Examples:
    - Whirlwind of Thought: "Whenever you cast a noncreature spell, draw a card."
    - Diviner's Wand: "Whenever you cast an instant or sorcery spell, you may draw a card."

    Returns:
        {
            'draws_on_spell': bool,
            'spell_type': str,  # 'noncreature', 'instant_sorcery', 'any'
            'cards_drawn': int
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'draws_on_spell': False,
        'spell_type': None,
        'cards_drawn': 1
    }

    # Noncreature spell draw
    if re.search(r'whenever you cast a noncreature spell.*draw a card', oracle_text):
        result['draws_on_spell'] = True
        result['spell_type'] = 'noncreature'
        return result

    # Instant/sorcery draw
    if re.search(r'whenever you cast an instant or sorcery.*draw', oracle_text):
        result['draws_on_spell'] = True
        result['spell_type'] = 'instant_sorcery'

        # Check how many cards
        draw_match = re.search(r'draw (\d+)', oracle_text)
        if draw_match:
            result['cards_drawn'] = int(draw_match.group(1))

        return result

    return result


def extract_spell_copy_ability(card: Dict) -> Dict:
    """
    Extract spell copying abilities.

    Examples:
    - Narset's Reversal: "Copy target instant or sorcery spell, then return it to its owner's hand."
    - Fork: "Copy target instant or sorcery spell. You may choose new targets for the copy."
    - Dualcaster Mage: "When Dualcaster Mage enters the battlefield, copy target instant or sorcery spell."

    Returns:
        {
            'copies_spells': bool,
            'copy_type': str,  # 'instant', 'sorcery', 'instant_or_sorcery'
            'trigger_type': str,  # 'spell', 'etb', 'activated'
            'bounces_original': bool  # For Narset's Reversal
        }
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    result = {
        'copies_spells': False,
        'copy_type': None,
        'trigger_type': None,
        'bounces_original': False
    }

    # Check if it copies spells
    if 'copy target instant or sorcery' in oracle_text:
        result['copies_spells'] = True
        result['copy_type'] = 'instant_or_sorcery'

        # Determine trigger type
        if 'instant' in type_line or 'sorcery' in type_line:
            result['trigger_type'] = 'spell'
        elif 'enters the battlefield' in oracle_text:
            result['trigger_type'] = 'etb'
        elif '{t}' in oracle_text or 'activate' in oracle_text:
            result['trigger_type'] = 'activated'

        # Check if it bounces the original (Narset's Reversal)
        if 'return it to its owner\'s hand' in oracle_text or 'return that spell to its owner\'s hand' in oracle_text:
            result['bounces_original'] = True

        return result

    # Check for instant-only or sorcery-only copying
    if 'copy target instant' in oracle_text:
        result['copies_spells'] = True
        result['copy_type'] = 'instant'
        result['trigger_type'] = 'spell' if 'instant' in type_line else 'other'
        return result

    if 'copy target sorcery' in oracle_text:
        result['copies_spells'] = True
        result['copy_type'] = 'sorcery'
        result['trigger_type'] = 'spell' if 'sorcery' in type_line else 'other'
        return result

    return result


def extract_creates_treasures_on_spell(card: Dict) -> Dict:
    """
    Extract treasure creation on spell cast.

    Examples:
    - Storm-Kiln Artist: "Whenever you cast or copy an instant or sorcery spell, create a Treasure token."

    Returns:
        {
            'creates_treasures_on_spell': bool,
            'spell_type': str,  # 'instant_sorcery', 'noncreature', etc.
            'includes_copies': bool  # Whether it triggers on copies too
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'creates_treasures_on_spell': False,
        'spell_type': None,
        'includes_copies': False
    }

    # Check for treasure creation on spell cast
    if 'treasure token' in oracle_text or 'treasure artifact token' in oracle_text:
        # Storm-Kiln Artist pattern
        if 'whenever you cast or copy an instant or sorcery' in oracle_text:
            result['creates_treasures_on_spell'] = True
            result['spell_type'] = 'instant_sorcery'
            result['includes_copies'] = True
            return result

        # Generic instant/sorcery pattern
        if 'whenever you cast an instant or sorcery' in oracle_text:
            result['creates_treasures_on_spell'] = True
            result['spell_type'] = 'instant_sorcery'
            return result

        # Noncreature spell pattern
        if 'whenever you cast a noncreature spell' in oracle_text:
            result['creates_treasures_on_spell'] = True
            result['spell_type'] = 'noncreature'
            return result

    return result


def extract_creates_tokens_on_spell(card: Dict) -> Dict:
    """
    Extract general token creation on spell cast.

    Examples:
    - Kykar, Wind's Fury: "Whenever you cast a noncreature spell, create a 1/1 white Spirit creature token with flying."
    - Young Pyromancer: "Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."

    Returns:
        {
            'creates_tokens_on_spell': bool,
            'spell_type': str,
            'token_type': Optional[str],
            'power': Optional[int],
            'toughness': Optional[int]
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'creates_tokens_on_spell': False,
        'spell_type': None,
        'token_type': None,
        'power': None,
        'toughness': None
    }

    # Pattern: "Whenever you cast [spell type], create [token]"
    spell_patterns = [
        (r'whenever you cast a noncreature spell.*create', 'noncreature'),
        (r'whenever you cast an instant or sorcery spell.*create', 'instant_sorcery'),
    ]

    for pattern, spell_type in spell_patterns:
        if re.search(pattern, oracle_text):
            result['creates_tokens_on_spell'] = True
            result['spell_type'] = spell_type

            # Extract token power/toughness
            pt_match = re.search(r'(\d+)/(\d+)', oracle_text)
            if pt_match:
                result['power'] = int(pt_match.group(1))
                result['toughness'] = int(pt_match.group(2))

            # Extract token type
            if 'spirit' in oracle_text:
                result['token_type'] = 'Spirit'
            elif 'elemental' in oracle_text:
                result['token_type'] = 'Elemental'
            elif 'soldier' in oracle_text:
                result['token_type'] = 'Soldier'

            break

    return result


def extract_deals_damage_on_spell(card: Dict) -> Dict:
    """
    Extract damage effects triggered by casting spells.

    Examples:
    - Guttersnipe: "Whenever you cast an instant or sorcery spell, Guttersnipe deals 2 damage to each opponent."
    - Firebrand Archer: "Whenever you cast a noncreature spell, Firebrand Archer deals 1 damage to each opponent."
    - Thermo-Alchemist: Activated ability, not spell trigger

    Returns:
        {
            'deals_damage_on_spell': bool,
            'spell_type': str,  # 'noncreature', 'instant_sorcery', 'any'
            'damage_amount': int,
            'damage_target': str,  # 'each_opponent', 'any_target', 'player', 'creature'
            'magecraft': bool  # Whether it uses magecraft keyword
        }
    """
    oracle_text = card.get('oracle_text', '').lower()

    result = {
        'deals_damage_on_spell': False,
        'spell_type': None,
        'damage_amount': 0,
        'damage_target': None,
        'magecraft': False
    }

    # Check for magecraft keyword
    if 'magecraft' in oracle_text:
        result['magecraft'] = True

    # Pattern 1: "Whenever you cast an instant or sorcery spell, ... deals X damage to ..."
    instant_sorcery_patterns = [
        r'whenever you cast an instant or sorcery spell.*deals?\s+(\d+)\s+damage\s+to\s+(.*?)(?:\.|,)',
        r'whenever you cast an instant or sorcery.*(\d+)\s+damage.*to\s+(.*?)(?:\.|,)',
    ]

    for pattern in instant_sorcery_patterns:
        match = re.search(pattern, oracle_text)
        if match:
            result['deals_damage_on_spell'] = True
            result['spell_type'] = 'instant_sorcery'
            result['damage_amount'] = int(match.group(1))

            # Parse target
            target_text = match.group(2) if len(match.groups()) >= 2 else ''
            if 'each opponent' in target_text:
                result['damage_target'] = 'each_opponent'
            elif 'any target' in target_text:
                result['damage_target'] = 'any_target'
            elif 'target player' in target_text or 'target opponent' in target_text:
                result['damage_target'] = 'player'
            elif 'target creature' in target_text:
                result['damage_target'] = 'creature'
            else:
                result['damage_target'] = 'any_target'

            return result

    # Pattern 2: "Whenever you cast a noncreature spell, ... deals X damage to ..."
    noncreature_patterns = [
        r'whenever you cast a noncreature spell.*deals?\s+(\d+)\s+damage\s+to\s+(.*?)(?:\.|,)',
        r'whenever you cast a noncreature.*(\d+)\s+damage.*to\s+(.*?)(?:\.|,)',
    ]

    for pattern in noncreature_patterns:
        match = re.search(pattern, oracle_text)
        if match:
            result['deals_damage_on_spell'] = True
            result['spell_type'] = 'noncreature'
            result['damage_amount'] = int(match.group(1))

            # Parse target
            target_text = match.group(2) if len(match.groups()) >= 2 else ''
            if 'each opponent' in target_text:
                result['damage_target'] = 'each_opponent'
            elif 'any target' in target_text:
                result['damage_target'] = 'any_target'
            elif 'target player' in target_text or 'target opponent' in target_text:
                result['damage_target'] = 'player'
            elif 'target creature' in target_text:
                result['damage_target'] = 'creature'
            else:
                result['damage_target'] = 'any_target'

            return result

    # Pattern 3: Magecraft damage (generic pattern)
    if result['magecraft']:
        # "Magecraft — Whenever you cast or copy an instant or sorcery spell, ..."
        magecraft_pattern = r'magecraft.*deals?\s+(\d+)\s+damage\s+to\s+(.*?)(?:\.|,)'
        match = re.search(magecraft_pattern, oracle_text)
        if match:
            result['deals_damage_on_spell'] = True
            result['spell_type'] = 'instant_sorcery'  # Magecraft triggers on instant/sorcery
            result['damage_amount'] = int(match.group(1))

            # Parse target
            target_text = match.group(2)
            if 'each opponent' in target_text:
                result['damage_target'] = 'each_opponent'
            elif 'any target' in target_text:
                result['damage_target'] = 'any_target'
            elif 'target player' in target_text or 'target opponent' in target_text:
                result['damage_target'] = 'player'
            elif 'target creature' in target_text:
                result['damage_target'] = 'creature'
            else:
                result['damage_target'] = 'any_target'

            return result

    return result
