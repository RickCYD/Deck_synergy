"""
ETB (Enter The Battlefield) Trigger Extractors

Extracts ETB-related mechanics from MTG cards:
- Rally triggers (Ally-specific ETB)
- General creature ETB triggers
- ETB triggers for specific creature types
- Token ETB triggers
"""

import re
from typing import Dict, List, Optional


def extract_rally_triggers(card: Dict) -> Dict:
    """
    Detect Rally mechanic (Ally ETB triggers).

    Rally = "Whenever this creature or another Ally enters the battlefield under your control"

    Examples:
    - "Rally — Whenever this creature or another Ally enters, creatures you control gain haste"
    - "Whenever this creature or another Ally enters the battlefield under your control, draw a card"

    Args:
        card: Card dictionary with oracle_text, type_line, etc.

    Returns:
        {
            'has_rally': bool,
            'effect_type': str,  # 'anthem', 'draw', 'damage', 'buff', etc.
            'effect_description': str,
            'is_ally': bool  # Whether this card is an Ally
        }
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '')

    result = {
        'has_rally': False,
        'effect_type': None,
        'effect_description': '',
        'is_ally': 'Ally' in type_line
    }

    if not text:
        return result

    # Rally patterns
    rally_patterns = [
        r'rally\s*—\s*whenever',
        r'rally\s*-\s*whenever',
        r'whenever this creature or another ally.*enters',
        r'whenever.*ally.*enters.*battlefield.*under your control',
    ]

    for pattern in rally_patterns:
        if re.search(pattern, text):
            result['has_rally'] = True
            result['effect_description'] = card.get('oracle_text', '')

            # Determine effect type
            if re.search(r'gain|get \+\d+/\+\d+|gets \+\d+/\+\d+', text):
                result['effect_type'] = 'anthem'
            elif re.search(r'draw|draws.*card', text):
                result['effect_type'] = 'draw'
            elif re.search(r'deal|deals.*damage', text):
                result['effect_type'] = 'damage'
            elif re.search(r'destroy|exile|return', text):
                result['effect_type'] = 'removal'
            elif re.search(r'put.*counter', text):
                result['effect_type'] = 'counters'
            else:
                result['effect_type'] = 'other'

            break

    return result


def extract_creature_etb_triggers(card: Dict) -> Dict:
    """
    Detect general creature ETB triggers.

    Examples:
    - "Whenever a creature you control enters"
    - "Whenever a creature enters under your control"
    - "Whenever another creature enters"

    Args:
        card: Card dictionary

    Returns:
        {
            'has_creature_etb_trigger': bool,
            'trigger_scope': str,  # 'any_creature', 'your_creatures', 'other_creatures', 'specific_type'
            'creature_type': Optional[str],  # If specific type
            'effect_type': str,
            'effect_description': str
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_creature_etb_trigger': False,
        'trigger_scope': None,
        'creature_type': None,
        'effect_type': None,
        'effect_description': ''
    }

    if not text:
        return result

    # General creature ETB patterns
    etb_patterns = [
        (r'whenever a creature you control enters', 'your_creatures'),
        (r'whenever a creature enters.*under your control', 'your_creatures'),
        (r'whenever another creature enters.*under your control', 'other_creatures'),
        (r'whenever a creature enters', 'any_creature'),
        (r'whenever.*creature.*enters the battlefield', 'any_creature'),
    ]

    for pattern, scope in etb_patterns:
        if re.search(pattern, text):
            result['has_creature_etb_trigger'] = True
            result['trigger_scope'] = scope
            result['effect_description'] = card.get('oracle_text', '')

            # Determine effect type
            if re.search(r'put.*\+1/\+1 counter', text):
                result['effect_type'] = 'counters'
            elif re.search(r'deal|deals.*damage', text):
                result['effect_type'] = 'damage'
            elif re.search(r'draw|draws.*card', text):
                result['effect_type'] = 'draw'
            elif re.search(r'gain.*life', text):
                result['effect_type'] = 'lifegain'
            elif re.search(r'create.*token', text):
                result['effect_type'] = 'tokens'
            else:
                result['effect_type'] = 'other'

            break

    return result


def extract_token_creation_etb(card: Dict) -> Dict:
    """
    Detect if a card creates tokens when entering the battlefield.

    Examples:
    - "When this creature enters, create a 1/1 token"
    - "When this permanent enters the battlefield, create two Treasure tokens"

    Args:
        card: Card dictionary

    Returns:
        {
            'creates_tokens_on_etb': bool,
            'token_count': int,  # Number of tokens created (-1 if variable)
            'token_type': str,  # Type of token
            'is_creature_token': bool
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'creates_tokens_on_etb': False,
        'token_count': 0,
        'token_type': '',
        'is_creature_token': False
    }

    if not text:
        return result

    # ETB token creation patterns
    etb_token_patterns = [
        r'when.*enters.*create.*token',
        r'when.*enters the battlefield.*create.*token',
        r'etb.*create.*token'
    ]

    for pattern in etb_token_patterns:
        if re.search(pattern, text):
            result['creates_tokens_on_etb'] = True

            # Try to extract token count
            count_match = re.search(r'create (\w+) .*token', text)
            if count_match:
                count_word = count_match.group(1)
                number_map = {
                    'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3,
                    'four': 4, 'five': 5, 'six': 6, 'x': -1
                }
                result['token_count'] = number_map.get(count_word, 1)

            # Check if it's a creature token
            if re.search(r'\d+/\d+.*creature token', text):
                result['is_creature_token'] = True

            # Try to extract token type
            type_match = re.search(r'create.*?(\w+) (?:creature )?token', text)
            if type_match:
                result['token_type'] = type_match.group(1).title()

            break

    return result


def extract_ally_matters(card: Dict) -> Dict:
    """
    Detect if a card cares about Allies specifically.

    Examples:
    - "Allies you control get +1/+1"
    - "Whenever you cast an Ally spell"
    - Card types include "Ally"

    Args:
        card: Card dictionary

    Returns:
        {
            'is_ally': bool,
            'cares_about_allies': bool,
            'ally_effect_type': str,  # 'anthem', 'cast_trigger', 'etb_trigger', etc.
            'effect_description': str
        }
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '')

    result = {
        'is_ally': 'Ally' in type_line,
        'cares_about_allies': False,
        'ally_effect_type': None,
        'effect_description': ''
    }

    if not text:
        return result

    # Ally-matters patterns
    ally_patterns = [
        (r'allies you control get', 'anthem'),
        (r'whenever you cast an ally', 'cast_trigger'),
        (r'whenever.*ally.*enters', 'etb_trigger'),
        (r'ally creatures you control', 'anthem'),
        (r'each ally you control', 'anthem'),
        (r'target ally', 'targeted_buff'),
    ]

    for pattern, effect_type in ally_patterns:
        if re.search(pattern, text):
            result['cares_about_allies'] = True
            result['ally_effect_type'] = effect_type
            result['effect_description'] = card.get('oracle_text', '')
            break

    return result


def extract_creates_ally_tokens(card: Dict) -> bool:
    """
    Detect if a card creates Ally creature tokens.

    Examples:
    - "Create a 2/2 white Knight Ally creature token"
    - "Create X 1/1 Ally tokens"

    Args:
        card: Card dictionary

    Returns:
        bool: True if card creates Ally tokens
    """
    text = card.get('oracle_text', '').lower()

    if not text:
        return False

    # Check for Ally token creation
    if 'create' in text and 'ally' in text and 'token' in text:
        return True

    return False


def extract_etb_synergies(card: Dict) -> Dict:
    """
    Comprehensive ETB analysis combining all ETB extractors.

    Args:
        card: Card dictionary

    Returns:
        Dict with all ETB-related information
    """
    return {
        'rally': extract_rally_triggers(card),
        'creature_etb_trigger': extract_creature_etb_triggers(card),
        'token_creation_etb': extract_token_creation_etb(card),
        'ally_matters': extract_ally_matters(card),
        'creates_ally_tokens': extract_creates_ally_tokens(card)
    }
