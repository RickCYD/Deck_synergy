"""MIGRATION NOTICE:
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

Graveyard Interaction Extractors

Extracts graveyard-related mechanics from MTG cards:
- Reanimation (return creatures from graveyard to battlefield)
- Recursion (return cards from graveyard to hand)
- Self-recursion (flashback, jump-start, retrace)
- Graveyard counting (threshold, delirium, undergrowth)
- Graveyard exile (delve, escape)
- Graveyard fill (self-mill, dredge)
"""

import re
from typing import Dict, List, Optional


def extract_reanimation(card: Dict) -> Dict:
    """
    Extract reanimation effects (return creatures from graveyard to battlefield).

    Returns:
        {
            'is_reanimation': bool,
            'reanimation_type': str,  # 'single', 'mass', 'repeatable'
            'target_type': str,  # 'creature', 'permanent', 'specific_type'
            'restrictions': List[str],  # CMC, power, type restrictions
            'from_your_graveyard': bool,
            'to_battlefield': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_reanimation': False,
        'reanimation_type': None,
        'target_type': None,
        'restrictions': [],
        'from_your_graveyard': True,
        'to_battlefield': False,
        'examples': []
    }

    if not text:
        return result

    # Reanimation patterns - return from graveyard to battlefield
    reanimation_patterns = [
        r'return\s+(?:target|a|up to \d+)\s+(.*?)\s+(?:card|cards)\s+from\s+(?:your|a|an opponent\'s)\s+graveyard\s+to\s+the\s+battlefield',
        r'put\s+(?:target|a|all)\s+(.*?)\s+(?:card|cards)\s+from\s+(?:your|a)\s+graveyard\s+onto\s+the\s+battlefield',
        r'return.*from.*graveyard.*to.*battlefield',
    ]

    for pattern in reanimation_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_reanimation'] = True
            result['to_battlefield'] = True
            result['examples'].append(match.group(0))

            # Determine target type from match
            if match.lastindex and match.group(1):
                target_text = match.group(1)
                if 'creature' in target_text:
                    result['target_type'] = 'creature'
                elif 'permanent' in target_text:
                    result['target_type'] = 'permanent'
                elif 'artifact' in target_text or 'enchantment' in target_text:
                    result['target_type'] = 'specific_type'
                else:
                    result['target_type'] = 'creature'  # Default
            else:
                result['target_type'] = 'creature'

            break

    if not result['is_reanimation']:
        return result

    # Determine reanimation type
    if 'all' in text and 'graveyard' in text and 'battlefield' in text:
        result['reanimation_type'] = 'mass'
    elif re.search(r'whenever|at\s+the\s+beginning|\{.*\}:', text):
        result['reanimation_type'] = 'repeatable'
    else:
        result['reanimation_type'] = 'single'

    # Check restrictions
    restriction_patterns = [
        (r'with\s+(?:converted\s+)?mana\s+(?:cost|value)\s+(\d+)\s+or\s+less', 'cmc_restriction'),
        (r'with\s+power\s+(\d+)\s+or\s+less', 'power_restriction'),
        (r'with\s+total\s+power\s+(\d+)\s+or\s+less', 'total_power_restriction'),
        (r'(?:zombie|elf|goblin|dragon)', 'creature_type'),
    ]

    for pattern, restriction in restriction_patterns:
        if re.search(pattern, text):
            result['restrictions'].append(restriction)

    # Check whose graveyard
    if "opponent's graveyard" in text or 'any graveyard' in text:
        result['from_your_graveyard'] = False

    return result


def extract_recursion(card: Dict) -> Dict:
    """
    Extract recursion effects (return cards from graveyard to hand).

    Returns:
        {
            'has_recursion': bool,
            'recursion_type': str,  # 'single', 'repeatable', 'mass'
            'target_type': str,  # 'creature', 'instant', 'sorcery', 'any'
            'restrictions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_recursion': False,
        'recursion_type': None,
        'target_type': None,
        'restrictions': [],
        'examples': []
    }

    if not text:
        return result

    # Recursion patterns - return from graveyard to hand
    recursion_patterns = [
        r'return\s+(?:target|a|up to \d+)\s+(.*?)\s+(?:card|cards)\s+from\s+(?:your|a)\s+graveyard\s+to\s+your\s+hand',
        r'return\s+target\s+card\s+from\s+your\s+graveyard\s+to\s+your\s+hand',  # Eternal Witness pattern
        r'put.*from.*graveyard.*into.*hand',
    ]

    for pattern in recursion_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_recursion'] = True
            result['examples'].append(match.group(0))

            # Determine target type
            if match.lastindex and match.group(1):
                target_text = match.group(1)
                if 'creature' in target_text:
                    result['target_type'] = 'creature'
                elif 'instant' in target_text:
                    result['target_type'] = 'instant'
                elif 'sorcery' in target_text:
                    result['target_type'] = 'sorcery'
                elif 'artifact' in target_text:
                    result['target_type'] = 'artifact'
                elif 'enchantment' in target_text:
                    result['target_type'] = 'enchantment'
                else:
                    result['target_type'] = 'any'
            else:
                result['target_type'] = 'any'

            break

    if not result['has_recursion']:
        return result

    # Determine recursion type
    if re.search(r'whenever|at\s+the\s+beginning', text):
        result['recursion_type'] = 'repeatable'
    elif 'all' in text or 'each' in text:
        result['recursion_type'] = 'mass'
    else:
        result['recursion_type'] = 'single'

    return result


def extract_self_recursion(card: Dict) -> Dict:
    """
    Extract self-recursion mechanics (flashback, jump-start, retrace, etc.).

    NOTE: These DON'T synergize with mill/graveyard filling!
    They only care about THEIR OWN card being in the graveyard.

    Returns:
        {
            'has_self_recursion': bool,
            'recursion_mechanics': List[str],  # 'flashback', 'jump-start', 'retrace', 'disturb', etc.
            'costs': List[str],  # Additional costs for recursion
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'has_self_recursion': False,
        'recursion_mechanics': [],
        'costs': [],
        'examples': []
    }

    if not text:
        return result

    # Self-recursion mechanics
    self_recursion_patterns = [
        (r'flashback\s+(\{[^\}]+\}|\d+)', 'flashback'),
        (r'jump-start', 'jump-start'),
        (r'retrace', 'retrace'),
        (r'disturb\s+(\{[^\}]+\})', 'disturb'),
        (r'embalm\s+(\{[^\}]+\})', 'embalm'),
        (r'eternalize\s+(\{[^\}]+\})', 'eternalize'),
        (r'aftermath', 'aftermath'),
        (r'escape\s+.*exile', 'escape'),  # Escape requires exiling other cards, so it's borderline
    ]

    for pattern, mechanic in self_recursion_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_self_recursion'] = True
            result['recursion_mechanics'].append(mechanic)
            result['examples'].append(match.group(0))

            # Extract cost if captured
            if match.lastindex and match.group(1):
                result['costs'].append(match.group(1))

    # Check keywords
    keyword_recursion = ['flashback', 'jump-start', 'retrace', 'disturb', 'embalm', 'eternalize', 'aftermath']
    for kw in keyword_recursion:
        if kw in keywords and kw not in result['recursion_mechanics']:
            result['has_self_recursion'] = True
            result['recursion_mechanics'].append(kw)

    return result


def extract_graveyard_counting(card: Dict) -> Dict:
    """
    Extract graveyard counting effects (threshold, delirium, undergrowth).

    Returns:
        {
            'counts_graveyard': bool,
            'counting_mechanics': List[str],  # 'threshold', 'delirium', 'undergrowth', 'custom'
            'what_counts': str,  # 'cards', 'creatures', 'card_types', 'permanents'
            'threshold_number': Optional[int],
            'payoff_effects': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'counts_graveyard': False,
        'counting_mechanics': [],
        'what_counts': None,
        'threshold_number': None,
        'payoff_effects': [],
        'examples': []
    }

    if not text:
        return result

    # Graveyard counting mechanics
    counting_patterns = [
        (r'threshold', 'threshold', 7),
        (r'delirium', 'delirium', 4),
        (r'undergrowth', 'undergrowth', None),
        (r'(\d+)\s+or\s+more\s+cards?\s+in\s+your\s+graveyard', 'custom', None),
        (r'for\s+each\s+(.*?)\s+in\s+(?:your|a|all)\s+graveyard', 'scaling', None),
        (r'equal\s+to\s+the\s+number\s+of\s+(.*?)\s+in\s+(?:your|all)\s+graveyard', 'scaling', None),
    ]

    for pattern, mechanic, threshold in counting_patterns:
        match = re.search(pattern, text)
        if match:
            result['counts_graveyard'] = True
            result['counting_mechanics'].append(mechanic)
            result['examples'].append(match.group(0))

            if threshold:
                result['threshold_number'] = threshold

            # Extract what's being counted
            if match.lastindex and match.group(1):
                what = match.group(1)
                if 'creature' in what:
                    result['what_counts'] = 'creatures'
                elif 'card' in what and 'type' in what:
                    result['what_counts'] = 'card_types'
                elif 'permanent' in what:
                    result['what_counts'] = 'permanents'
                else:
                    result['what_counts'] = 'cards'
            elif mechanic == 'threshold':
                result['what_counts'] = 'cards'
            elif mechanic == 'delirium':
                result['what_counts'] = 'card_types'
            elif mechanic == 'undergrowth':
                result['what_counts'] = 'creatures'

    # Check keywords
    keyword_counting = ['threshold', 'delirium', 'undergrowth']
    for kw in keyword_counting:
        if kw in keywords and kw not in result['counting_mechanics']:
            result['counts_graveyard'] = True
            result['counting_mechanics'].append(kw)

    if result['counts_graveyard']:
        # Determine payoff effects
        payoff_patterns = [
            (r'gets?\s+\+\d+/\+\d+', 'pump'),
            (r'deals?\s+\d+\s+damage', 'damage'),
            (r'costs?\s+\{?\d+\}?\s+less', 'cost_reduction'),
            (r'draws?\s+(?:a\s+)?cards?', 'draw'),
            (r'(?:create|creates?)\s+.*tokens?', 'token'),
        ]

        for pattern, effect in payoff_patterns:
            if re.search(pattern, text):
                result['payoff_effects'].append(effect)

    return result


def extract_graveyard_exile(card: Dict) -> Dict:
    """
    Extract graveyard exile mechanics (delve, escape).

    Returns:
        {
            'exiles_from_graveyard': bool,
            'exile_mechanics': List[str],  # 'delve', 'escape', 'custom'
            'is_cost_reduction': bool,
            'exile_count': Optional[int],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'exiles_from_graveyard': False,
        'exile_mechanics': [],
        'is_cost_reduction': False,
        'exile_count': None,
        'examples': []
    }

    if not text:
        return result

    # Graveyard exile patterns
    exile_patterns = [
        (r'delve', 'delve', True),
        (r'escape.*exile\s+(\d+)', 'escape', True),
        (r'exile\s+(\d+)\s+cards?\s+from\s+your\s+graveyard', 'custom', False),
        (r'exile.*from.*graveyard', 'custom', False),
    ]

    for pattern, mechanic, is_cost in exile_patterns:
        match = re.search(pattern, text)
        if match:
            result['exiles_from_graveyard'] = True
            result['exile_mechanics'].append(mechanic)
            result['examples'].append(match.group(0))

            if is_cost:
                result['is_cost_reduction'] = True

            # Extract exile count
            if match.lastindex and match.group(1):
                try:
                    result['exile_count'] = int(match.group(1))
                except ValueError:
                    pass

    # Check keywords
    if 'delve' in keywords:
        result['exiles_from_graveyard'] = True
        if 'delve' not in result['exile_mechanics']:
            result['exile_mechanics'].append('delve')
        result['is_cost_reduction'] = True

    return result


def extract_graveyard_fill(card: Dict) -> Dict:
    """
    Extract graveyard filling mechanics (self-mill, dredge).

    Returns:
        {
            'fills_graveyard': bool,
            'fill_mechanics': List[str],  # 'mill', 'dredge', 'discard', 'sacrifice'
            'mill_amount': Optional[int],
            'is_repeatable': bool,
            'targets_self': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    keywords = [kw.lower() for kw in card.get('keywords', [])]

    result = {
        'fills_graveyard': False,
        'fill_mechanics': [],
        'mill_amount': None,
        'is_repeatable': False,
        'targets_self': False,
        'examples': []
    }

    if not text:
        return result

    # Graveyard fill patterns
    fill_patterns = [
        (r'mills?\s+(\d+|[xX])\s+cards?', 'mill'),
        (r'dredge\s+(\d+)', 'dredge'),
        (r'put\s+(?:the\s+)?(?:top\s+)?(\d+)\s+cards?\s+(?:of|from).*library\s+into.*graveyard', 'mill'),
        (r'put\s+the\s+rest\s+into\s+your\s+graveyard', 'mill'),  # Satyr Wayfinder pattern
        (r'discard', 'discard'),
        (r'sacrifice', 'sacrifice'),
        (r'surveil\s+(\d+)', 'surveil'),
    ]

    for pattern, mechanic in fill_patterns:
        match = re.search(pattern, text)
        if match:
            result['fills_graveyard'] = True
            if mechanic not in result['fill_mechanics']:
                result['fill_mechanics'].append(mechanic)
            result['examples'].append(match.group(0))

            # Extract amount
            if match.lastindex and match.group(1):
                amount_str = match.group(1)
                if amount_str.isdigit():
                    if result['mill_amount'] is None or int(amount_str) > result['mill_amount']:
                        result['mill_amount'] = int(amount_str)

    # Check keywords
    if 'dredge' in keywords:
        result['fills_graveyard'] = True
        if 'dredge' not in result['fill_mechanics']:
            result['fill_mechanics'].append('dredge')

    if result['fills_graveyard']:
        # Check if it mills/fills your own graveyard
        result['targets_self'] = 'you' in text or 'your' in text

        # Check if repeatable
        repeatable_keywords = ['whenever', 'at the beginning', '{t}:', 'dredge']
        result['is_repeatable'] = any(kw in text for kw in repeatable_keywords)

    return result


def classify_graveyard_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all graveyard mechanics.

    Returns a comprehensive dictionary with all graveyard information.
    """
    return {
        'reanimation': extract_reanimation(card),
        'recursion': extract_recursion(card),
        'self_recursion': extract_self_recursion(card),
        'graveyard_counting': extract_graveyard_counting(card),
        'graveyard_exile': extract_graveyard_exile(card),
        'graveyard_fill': extract_graveyard_fill(card)
    }
