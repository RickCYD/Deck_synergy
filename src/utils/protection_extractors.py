"""
Protection & Prevention Extractors

Extracts protection and damage prevention mechanics from MTG cards:
- Indestructible effects
- Hexproof/Shroud effects
- Protection from X
- Damage prevention
- Counterspell protection
- Sacrifice protection
"""

import re
from typing import Dict, List, Optional


def extract_indestructible(card: Dict) -> Dict:
    """
    Extract indestructible effects.

    Returns:
        {
            'grants_indestructible': bool,
            'target_type': str,  # 'self', 'target', 'all_yours', 'all_permanents'
            'is_permanent': bool,
            'conditional': bool,
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'grants_indestructible': False,
        'target_type': None,
        'is_permanent': False,
        'conditional': False,
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Indestructible patterns
    indestructible_patterns = [
        r'indestructible',
        r'has indestructible',
        r'have indestructible',
        r'gains? indestructible',
        r'gets? indestructible',
    ]

    for pattern in indestructible_patterns:
        match = re.search(pattern, text)
        if match:
            result['grants_indestructible'] = True
            result['examples'].append(match.group(0))
            break

    if not result['grants_indestructible']:
        return result

    # Determine target type
    if 'target' in text and 'permanent' in text:
        result['target_type'] = 'target_permanent'
    elif 'target creature' in text:
        result['target_type'] = 'target'
    elif 'creatures you control' in text or 'permanents you control' in text:
        result['target_type'] = 'all_yours'
    elif 'all permanents' in text or 'all creatures' in text:
        result['target_type'] = 'all_permanents'
    else:
        result['target_type'] = 'self'

    # Check if permanent or temporary
    if 'until end of turn' in text or 'until end of combat' in text:
        result['is_permanent'] = False
    elif result['target_type'] == 'self' and 'gains' not in text:
        result['is_permanent'] = True  # Static ability
    else:
        result['is_permanent'] = False

    # Check for conditions
    condition_patterns = [
        (r'as\s+long\s+as', 'as_long_as'),
        (r'if\s+you\s+control', 'control_condition'),
        (r'during\s+your\s+turn', 'your_turn'),
        (r'while\s+attacking', 'attacking'),
        (r'when.*enters', 'etb'),
    ]

    for pattern, condition in condition_patterns:
        if re.search(pattern, text):
            result['conditional'] = True
            result['conditions'].append(condition)

    return result


def extract_hexproof_shroud(card: Dict) -> Dict:
    """
    Extract hexproof and shroud effects.

    Returns:
        {
            'grants_hexproof': bool,
            'hexproof_type': str,  # 'hexproof', 'shroud', 'hexproof_from_X', 'ward'
            'target_type': str,
            'is_permanent': bool,
            'ward_cost': Optional[str],
            'hexproof_from': List[str],  # For "hexproof from red"
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'grants_hexproof': False,
        'hexproof_type': None,
        'target_type': None,
        'is_permanent': False,
        'ward_cost': None,
        'hexproof_from': [],
        'examples': []
    }

    if not text:
        return result

    # Hexproof/shroud patterns
    protection_patterns = [
        (r'hexproof\s+from\s+(\w+)', 'hexproof_from'),
        (r'hexproof', 'hexproof'),
        (r'shroud', 'shroud'),
        (r'ward\s+(\{[^\}]+\}|\d+)', 'ward'),
        (r"can't\s+be\s+the\s+target", 'cant_be_targeted'),
    ]

    for pattern, ptype in protection_patterns:
        match = re.search(pattern, text)
        if match:
            result['grants_hexproof'] = True
            result['hexproof_type'] = ptype
            result['examples'].append(match.group(0))

            # Extract specifics for "hexproof from X"
            if ptype == 'hexproof_from' and match.lastindex:
                result['hexproof_from'].append(match.group(1))

            # Extract ward cost
            if ptype == 'ward' and match.lastindex:
                result['ward_cost'] = match.group(1)

            break

    if not result['grants_hexproof']:
        return result

    # Determine target type
    if 'target creature' in text or 'target permanent' in text:
        result['target_type'] = 'target'
    elif 'creatures you control' in text or 'permanents you control' in text:
        result['target_type'] = 'all_yours'
    else:
        result['target_type'] = 'self'

    # Check if permanent
    if 'until end of turn' in text or 'gains' in text:
        result['is_permanent'] = False
    else:
        result['is_permanent'] = True

    return result


def extract_protection_from(card: Dict) -> Dict:
    """
    Extract "protection from X" effects.

    Returns:
        {
            'has_protection': bool,
            'protection_from': List[str],  # Colors, card types, etc.
            'target_type': str,
            'is_permanent': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_protection': False,
        'protection_from': [],
        'target_type': None,
        'is_permanent': False,
        'examples': []
    }

    if not text:
        return result

    # Protection patterns
    protection_patterns = [
        r'protection\s+from\s+(\w+(?:\s+and\s+\w+)?)',
        r'protection\s+from\s+all\s+colors',
        r'protection\s+from\s+everything',
    ]

    for pattern in protection_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            result['has_protection'] = True
            result['examples'].append(match.group(0))

            # Extract what it has protection from
            if 'everything' in match.group(0):
                result['protection_from'].append('everything')
            elif 'all colors' in match.group(0):
                result['protection_from'].extend(['white', 'blue', 'black', 'red', 'green'])
            elif match.lastindex:
                protected = match.group(1)
                result['protection_from'].append(protected)

    if not result['has_protection']:
        return result

    # Determine target type
    if 'target creature' in text:
        result['target_type'] = 'target'
    elif 'creatures you control' in text:
        result['target_type'] = 'all_yours'
    else:
        result['target_type'] = 'self'

    # Check if permanent
    if 'until end of turn' in text or 'gains' in text:
        result['is_permanent'] = False
    else:
        result['is_permanent'] = True

    return result


def extract_damage_prevention(card: Dict) -> Dict:
    """
    Extract damage prevention effects.

    Returns:
        {
            'prevents_damage': bool,
            'prevention_type': str,  # 'prevent_all', 'prevent_X', 'prevent_combat', 'prevent_noncombat'
            'amount': Optional[int],  # Amount of damage prevented
            'targets': List[str],  # What's protected
            'is_permanent': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'prevents_damage': False,
        'prevention_type': None,
        'amount': None,
        'targets': [],
        'is_permanent': False,
        'examples': []
    }

    if not text:
        return result

    # Damage prevention patterns
    prevention_patterns = [
        (r'prevent\s+all\s+(?:combat\s+)?damage', 'prevent_all'),
        (r'prevent\s+the\s+next\s+(\d+)\s+damage', 'prevent_X'),
        (r'prevent\s+all\s+combat\s+damage', 'prevent_combat'),
        (r"damage.*can't\s+be\s+dealt", 'prevent_cant_deal'),
        (r"if.*damage.*would.*be.*dealt.*prevent", 'prevent_conditional'),
    ]

    for pattern, ptype in prevention_patterns:
        match = re.search(pattern, text)
        if match:
            result['prevents_damage'] = True
            result['prevention_type'] = ptype
            result['examples'].append(match.group(0))

            # Extract amount for "prevent X damage"
            if ptype == 'prevent_X' and match.lastindex:
                try:
                    result['amount'] = int(match.group(1))
                except (ValueError, IndexError):
                    pass

            break

    if not result['prevents_damage']:
        return result

    # Determine targets
    target_patterns = [
        (r'to\s+(?:target\s+)?creature', 'creature'),
        (r'to\s+you', 'player'),
        (r'to\s+(?:any\s+)?target', 'any'),
        (r'that\s+would\s+be\s+dealt\s+to\s+creatures?\s+you\s+control', 'your_creatures'),
    ]

    for pattern, target in target_patterns:
        if re.search(pattern, text):
            result['targets'].append(target)

    # Check if permanent effect
    if 'until end of turn' in text or 'prevent the next' in text:
        result['is_permanent'] = False
    elif 'as long as' in text or 'if' in text:
        result['is_permanent'] = False
    else:
        result['is_permanent'] = True

    return result


def extract_counterspell_protection(card: Dict) -> Dict:
    """
    Extract protection from counterspells.

    Returns:
        {
            'has_counter_protection': bool,
            'protection_type': str,  # 'cant_be_countered', 'counter_protection', 'flash'
            'applies_to': str,  # 'self', 'all_your_spells', 'creature_spells'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_counter_protection': False,
        'protection_type': None,
        'applies_to': None,
        'examples': []
    }

    if not text:
        return result

    # Counterspell protection patterns
    counter_patterns = [
        (r"(?:this\s+spell\s+)?can't\s+be\s+countered", 'cant_be_countered'),
        (r"(?:your\s+)?spells\s+can't\s+be\s+countered", 'all_spells_protected'),
        (r"creature\s+spells\s+(?:you\s+control\s+)?can't\s+be\s+countered", 'creature_spells_protected'),
    ]

    for pattern, ptype in counter_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_counter_protection'] = True
            result['protection_type'] = ptype
            result['examples'].append(match.group(0))
            break

    if not result['has_counter_protection']:
        return result

    # Determine what it applies to
    if result['protection_type'] == 'cant_be_countered':
        result['applies_to'] = 'self'
    elif result['protection_type'] == 'all_spells_protected':
        result['applies_to'] = 'all_your_spells'
    elif result['protection_type'] == 'creature_spells_protected':
        result['applies_to'] = 'creature_spells'

    return result


def extract_sacrifice_protection(card: Dict) -> Dict:
    """
    Extract protection from sacrifice effects.

    Returns:
        {
            'has_sacrifice_protection': bool,
            'protection_scope': str,  # 'self', 'all_yours', 'tokens'
            'is_permanent': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_sacrifice_protection': False,
        'protection_scope': None,
        'is_permanent': False,
        'examples': []
    }

    if not text:
        return result

    # Sacrifice protection patterns
    sacrifice_patterns = [
        r"can't\s+(?:be\s+)?sacrificed?",
        r"permanents?\s+you\s+control\s+(?:have\s+)?(?:\"|can't\s+be\s+sacrificed)",
        r"sacrifice.*instead\s+sacrifice",  # Redirection effects
    ]

    for pattern in sacrifice_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_sacrifice_protection'] = True
            result['examples'].append(match.group(0))
            break

    if not result['has_sacrifice_protection']:
        return result

    # Determine scope
    if 'permanents you control' in text or 'creatures you control' in text:
        result['protection_scope'] = 'all_yours'
    elif 'tokens' in text:
        result['protection_scope'] = 'tokens'
    else:
        result['protection_scope'] = 'self'

    # Check if permanent
    if 'until end of turn' in text or 'this turn' in text:
        result['is_permanent'] = False
    else:
        result['is_permanent'] = True

    return result


def classify_protection_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all protection mechanics.

    Returns a comprehensive dictionary with all protection information.
    """
    return {
        'indestructible': extract_indestructible(card),
        'hexproof_shroud': extract_hexproof_shroud(card),
        'protection_from': extract_protection_from(card),
        'damage_prevention': extract_damage_prevention(card),
        'counterspell_protection': extract_counterspell_protection(card),
        'sacrifice_protection': extract_sacrifice_protection(card)
    }
