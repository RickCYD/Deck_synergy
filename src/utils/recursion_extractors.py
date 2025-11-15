"""
MIGRATION NOTICE:
==================
This module uses legacy regex-based extraction. For new code, consider using
the unified parser instead:

    from src.core.card_parser import UnifiedCardParser

import warnings

# Optional: Import unified parser for recommended path
try:
    from src.core.card_parser import UnifiedCardParser
    _UNIFIED_PARSER_AVAILABLE = True
except ImportError:
    _UNIFIED_PARSER_AVAILABLE = False
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)

See UNIFIED_ARCHITECTURE_GUIDE.md for details.

The functions in this file are maintained for backward compatibility.

Recursion & Graveyard Mechanics Extractors

Extracts recursion and graveyard-related mechanics from MTG cards:
- Reanimation (graveyard → battlefield)
- Recursion to hand (graveyard → hand)
- Flashback/Jump-start/Escape (cast from graveyard)
- Extra turns
- Cascade
- Treasure/Clue/Food tokens
"""

import re
from typing import Dict, List, Optional


def extract_reanimation(card: Dict) -> Dict:
    """
    Extract reanimation effects (graveyard → battlefield).

    Returns:
        {
            'has_reanimation': bool,
            'reanimation_type': str,  # 'single', 'mass', 'temporary', 'recurring'
            'targets': List[str],  # 'creature', 'artifact', 'enchantment', 'any'
            'restrictions': List[str],  # CMC, power, color restrictions
            'source': str,  # 'your_graveyard', 'any_graveyard', 'opponent_graveyard'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_reanimation': False,
        'reanimation_type': None,
        'targets': [],
        'restrictions': [],
        'source': 'your_graveyard',
        'examples': []
    }

    if not text:
        return result

    # Main reanimation pattern: "return ... from ... graveyard ... to the battlefield"
    reanimate_patterns = [
        r'return.*?(?:creature|permanent|card).*?from.*?graveyard.*?to the battlefield',
        r'put.*?(?:creature|permanent|card).*?from.*?graveyard.*?onto the battlefield',
        r'return.*?from.*?graveyard.*?to the battlefield',
        r'return.*?from.*?graveyard.*?onto the battlefield',
        r'puts?.*?(?:creature|permanent|card).*?onto the battlefield',  # Animate Dead pattern
        r'put.*?onto the battlefield'  # Generic battlefield pattern
    ]

    for pattern in reanimate_patterns:
        if re.search(pattern, text):
            result['has_reanimation'] = True
            break

    if not result['has_reanimation']:
        return result

    # Determine reanimation type
    if 'at the beginning' in text or 'whenever' in text or 'when.*enters' in text:
        result['reanimation_type'] = 'recurring'
    elif 'each player' in text or 'all creatures' in text or 'all creature cards' in text:
        result['reanimation_type'] = 'mass'
    elif 'until end of turn' in text or 'exile.*at the beginning' in text:
        result['reanimation_type'] = 'temporary'
    else:
        result['reanimation_type'] = 'single'

    # Determine target types
    if 'creature card' in text or 'creature cards' in text:
        result['targets'].append('creature')
    if 'artifact card' in text:
        result['targets'].append('artifact')
    if 'enchantment card' in text:
        result['targets'].append('enchantment')
    if 'permanent card' in text or re.search(r'return.*?card.*?from.*?graveyard', text):
        result['targets'].append('any')

    # Default to creature if no specific type mentioned
    if not result['targets']:
        result['targets'].append('creature')

    # Determine source
    if 'any graveyard' in text or 'a graveyard' in text:
        result['source'] = 'any_graveyard'
    elif "opponent's graveyard" in text or 'target opponent' in text:
        result['source'] = 'opponent_graveyard'

    # Extract restrictions
    restriction_patterns = [
        (r'with (?:converted )?mana (?:cost|value) (\d+) or less', 'cmc_restriction'),
        (r'with power (\d+) or less', 'power_restriction'),
        (r'with mana value [xX] or less', 'cmc_x_or_less'),
        (r'(?:white|blue|black|red|green)', 'color_restriction')
    ]

    for pattern, restriction in restriction_patterns:
        if re.search(pattern, text):
            result['restrictions'].append(restriction)

    # Extract examples
    match = re.search(r'return.*?from.*?graveyard.*?to.*?battlefield', text)
    if match:
        result['examples'].append(match.group(0))

    return result


def extract_recursion_to_hand(card: Dict) -> Dict:
    """
    Extract recursion to hand effects (graveyard → hand).

    Returns:
        {
            'has_recursion': bool,
            'recursion_type': str,  # 'single', 'multiple', 'repeatable'
            'targets': List[str],  # 'creature', 'instant', 'sorcery', 'any'
            'source': str,  # 'your_graveyard', 'any_graveyard'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_recursion': False,
        'recursion_type': 'single',
        'targets': [],
        'source': 'your_graveyard',
        'examples': []
    }

    if not text:
        return result

    # Recursion pattern: "return ... from graveyard to hand"
    recursion_patterns = [
        r'return.*?(?:card|cards).*?from.*?graveyard.*?to.*?hand',
        r'return.*?from.*?graveyard.*?to.*?hand',
        r'put.*?from.*?graveyard.*?into.*?hand'
    ]

    for pattern in recursion_patterns:
        if re.search(pattern, text):
            result['has_recursion'] = True
            break

    if not result['has_recursion']:
        return result

    # Determine recursion type
    if 'whenever' in text or 'at the beginning' in text:
        result['recursion_type'] = 'repeatable'
    elif 'up to' in text or re.search(r'return.*?(?:two|three|four|\d+).*?cards?', text):
        result['recursion_type'] = 'multiple'
    else:
        result['recursion_type'] = 'single'

    # Determine target types
    if 'creature card' in text:
        result['targets'].append('creature')
    if 'instant card' in text:
        result['targets'].append('instant')
    if 'sorcery card' in text:
        result['targets'].append('sorcery')
    if 'instant or sorcery' in text:
        result['targets'].append('instant_or_sorcery')
    if 'permanent card' in text or re.search(r'return.*?card.*?from.*?graveyard', text):
        result['targets'].append('any')

    if not result['targets']:
        result['targets'].append('any')

    # Determine source
    if 'any graveyard' in text or 'a graveyard' in text:
        result['source'] = 'any_graveyard'

    # Extract examples
    match = re.search(r'return.*?from.*?graveyard.*?to.*?hand', text)
    if match:
        result['examples'].append(match.group(0))

    return result


def extract_graveyard_casting(card: Dict) -> Dict:
    """
    Extract graveyard casting mechanics (flashback, escape, jump-start, etc.).

    Returns:
        {
            'has_graveyard_casting': bool,
            'casting_types': List[str],  # 'flashback', 'escape', 'jump-start', 'aftermath', 'embalm', 'eternalize'
            'additional_costs': List[str],  # 'discard', 'exile_cards', 'mana'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'has_graveyard_casting': False,
        'casting_types': [],
        'additional_costs': [],
        'examples': []
    }

    if not text and not keywords:
        return result

    # Check for graveyard casting keywords
    graveyard_keywords = {
        'flashback': 'flashback',
        'escape': 'escape',
        'jump-start': 'jump-start',
        'aftermath': 'aftermath',
        'embalm': 'embalm',
        'eternalize': 'eternalize',
        'disturb': 'disturb',
        'unearth': 'unearth',
        'retrace': 'retrace'
    }

    for keyword, cast_type in graveyard_keywords.items():
        if keyword in keywords or keyword in text:
            result['has_graveyard_casting'] = True
            result['casting_types'].append(cast_type)

    # Check for generic graveyard casting patterns
    graveyard_cast_patterns = [
        r'cast.*?from.*?graveyard',
        r'play.*?from.*?graveyard',
        r'you may cast.*?from.*?graveyard'
    ]

    for pattern in graveyard_cast_patterns:
        if re.search(pattern, text):
            result['has_graveyard_casting'] = True
            if 'other' not in result['casting_types']:
                result['casting_types'].append('other')
            break

    if not result['has_graveyard_casting']:
        return result

    # Determine additional costs
    if 'discard a card' in text or 'discard' in text and 'jump-start' in result['casting_types']:
        result['additional_costs'].append('discard')
    if 'exile' in text and ('escape' in result['casting_types'] or 'flashback' in result['casting_types']):
        result['additional_costs'].append('exile_cards')
    if re.search(r'flashback.*?\{', text) or re.search(r'escape.*?\{', text):
        result['additional_costs'].append('mana')

    # Extract examples
    if result['casting_types']:
        result['examples'].append(f"graveyard casting: {', '.join(result['casting_types'])}")

    return result


def extract_extra_turns(card: Dict) -> Dict:
    """
    Extract extra turn effects.

    Returns:
        {
            'has_extra_turns': bool,
            'turn_type': str,  # 'single', 'multiple', 'conditional', 'infinite_potential'
            'restrictions': List[str],  # 'exile_on_cast', 'skip_next_turn', 'creatures_cant_attack'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_extra_turns': False,
        'turn_type': 'single',
        'restrictions': [],
        'examples': []
    }

    if not text:
        return result

    # Extra turn patterns
    extra_turn_patterns = [
        r'take an extra turn',
        r'takes? an extra turn',
        r'extra turn after this one',
        r'take another turn',
        r'extra combat phase'  # Not technically extra turn but similar effect
    ]

    for pattern in extra_turn_patterns:
        if re.search(pattern, text):
            result['has_extra_turns'] = True
            break

    if not result['has_extra_turns']:
        return result

    # Determine turn type
    if 'for each' in text or re.search(r'take.*?(\d+).*?extra turns?', text):
        result['turn_type'] = 'multiple'
    elif 'whenever' in text or 'when' in text:
        result['turn_type'] = 'conditional'
        # Check for infinite potential (can be repeated)
        if 'you control' in text or 'attacks' in text:
            result['turn_type'] = 'infinite_potential'
    else:
        result['turn_type'] = 'single'

    # Determine restrictions
    if 'exile' in text and ('cast' in text or 'cast this spell' in text):
        result['restrictions'].append('exile_on_cast')
    if 'skip' in text and 'next turn' in text:
        result['restrictions'].append('skip_next_turn')
    if "can't attack" in text or "can't untap" in text:
        result['restrictions'].append('creatures_cant_attack')
    if 'loses the game' in text or 'lose the game' in text:
        result['restrictions'].append('lose_if_not_win')

    # Extract examples
    match = re.search(r'take.*?extra turn', text)
    if match:
        result['examples'].append(match.group(0))

    return result


def extract_cascade(card: Dict) -> Dict:
    """
    Extract cascade effects.

    Returns:
        {
            'has_cascade': bool,
            'cascade_count': int,  # How many cascade triggers (1, 2, 4, etc.)
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'has_cascade': False,
        'cascade_count': 0,
        'examples': []
    }

    if not text and not keywords:
        return result

    # Check for cascade keyword
    if 'cascade' in keywords or 'cascade' in text:
        result['has_cascade'] = True

        # Count cascades (Apex Devastator has Cascade x4)
        cascade_count = text.count('cascade')
        result['cascade_count'] = max(1, cascade_count)

        result['examples'].append(f"cascade (x{result['cascade_count']})")

    return result


def extract_treasure_tokens(card: Dict) -> Dict:
    """
    Extract treasure/clue/food token generation.

    Returns:
        {
            'generates_tokens': bool,
            'token_types': List[str],  # 'treasure', 'clue', 'food'
            'generation_type': str,  # 'etb', 'repeatable', 'triggered', 'activated'
            'amount': Optional[int],  # How many tokens created
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'generates_tokens': False,
        'token_types': [],
        'generation_type': None,
        'amount': None,
        'examples': []
    }

    if not text:
        return result

    # Token patterns
    token_patterns = {
        'treasure': r'create.*?treasure',
        'clue': r'create.*?clue|investigate',  # investigate creates clues
        'food': r'create.*?food'
    }

    for token_type, pattern in token_patterns.items():
        if re.search(pattern, text):
            result['generates_tokens'] = True
            result['token_types'].append(token_type)

    if not result['generates_tokens']:
        return result

    # Determine generation type
    if 'when' in text and 'enters the battlefield' in text:
        result['generation_type'] = 'etb'
    elif 'whenever' in text or 'at the beginning' in text:
        result['generation_type'] = 'repeatable'
    elif '{' in text and ':' in text:
        result['generation_type'] = 'activated'
    else:
        result['generation_type'] = 'triggered'

    # Extract amount
    amount_pattern = r'create.*?(\d+|a|an|two|three|four|five|six|seven|eight|nine|ten).*?(?:treasure|clue|food)'
    match = re.search(amount_pattern, text)
    if match:
        amount_str = match.group(1)
        number_words = {
            'a': 1, 'an': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        if amount_str in number_words:
            result['amount'] = number_words[amount_str]
        elif amount_str.isdigit():
            result['amount'] = int(amount_str)

    # Extract examples
    for token_type in result['token_types']:
        match = re.search(rf'create.*?{token_type}', text)
        if match:
            result['examples'].append(match.group(0))

    return result


def classify_recursion_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all recursion mechanics.

    Returns a comprehensive dictionary with all recursion information.
    """
    return {
        'reanimation': extract_reanimation(card),
        'recursion_to_hand': extract_recursion_to_hand(card),
        'graveyard_casting': extract_graveyard_casting(card),
        'extra_turns': extract_extra_turns(card),
        'cascade': extract_cascade(card),
        'treasure_tokens': extract_treasure_tokens(card)
    }
