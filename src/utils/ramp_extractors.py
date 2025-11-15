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

Ramp & Acceleration Extractors

Extracts mana acceleration mechanics from MTG cards:
- Mana rocks (artifacts that produce mana)
- Mana dorks (creatures that produce mana)
- Ritual effects (temporary mana)
- Cost reduction effects
- Land ramp (effects that put lands onto battlefield)
"""

import re
from typing import Dict, List, Optional


def extract_mana_rocks(card: Dict) -> Dict:
    """
    Extract mana rock mechanics (artifacts that produce mana).

    Returns:
        {
            'is_mana_rock': bool,
            'rock_type': str,  # 'tapped', 'untapped', 'conditional', 'storage'
            'mana_produced': List[str],  # ['W', 'U', 'B', 'R', 'G', 'C'] or ['any']
            'activation_cost': Optional[str],  # '{T}', '{1}, {T}', etc.
            'cmc': int,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    card_type = card.get('type_line', '').lower()

    result = {
        'is_mana_rock': False,
        'rock_type': None,
        'mana_produced': [],
        'activation_cost': None,
        'cmc': card.get('cmc', 0),
        'examples': []
    }

    # Must be an artifact
    if 'artifact' not in card_type:
        return result

    if not text:
        return result

    # Mana production patterns
    # Pattern: "{T}: Add {C}" or "{T}: Add {W}{U}" or "{T}: Add one mana of any color"
    mana_patterns = [
        r'\{t\}:\s*add\s+((?:\{[wubrgc]\})+)',  # {T}: Add {C} or {W}{U}{B}
        r'\{t\}:\s*add\s+(?:one\s+mana\s+of\s+)?any\s+(?:color|one\s+color)',  # {T}: Add one mana of any color
        r'\{t\}:\s*add\s+(\d+)\s+mana',  # {T}: Add 3 mana
        r'\{[^\}]*\{t\}[^\}]*\}:\s*add\s+((?:\{[wubrgc]\})+)',  # {2}, {T}: Add {W}
    ]

    for pattern in mana_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_mana_rock'] = True
            result['examples'].append(match.group(0))

            # Determine mana produced
            if 'any color' in match.group(0) or 'any one color' in match.group(0):
                result['mana_produced'] = ['any']
            elif match.lastindex and match.group(1):
                mana_str = match.group(1)
                # Extract individual mana symbols (case insensitive)
                mana_symbols = re.findall(r'\{([wubrgc])\}', mana_str.lower())
                result['mana_produced'] = [m.upper() for m in mana_symbols]
                if not mana_symbols and mana_str.isdigit():
                    # "{T}: Add 3 mana" - usually colorless
                    result['mana_produced'] = ['C'] * int(mana_str)

            # Determine activation cost
            activation_match = re.search(r'(\{.*?\{t\}\})', text)
            if activation_match:
                result['activation_cost'] = activation_match.group(1)
            else:
                result['activation_cost'] = '{T}'

            break

    if not result['is_mana_rock']:
        return result

    # Determine rock type
    if 'enters the battlefield tapped' in text or 'enters tapped' in text:
        result['rock_type'] = 'tapped'
    elif 'storage counter' in text or 'charge counter' in text:
        result['rock_type'] = 'storage'
    elif '{' in result.get('activation_cost', '') and result['activation_cost'] != '{T}':
        result['rock_type'] = 'conditional'  # Requires mana to activate
    else:
        result['rock_type'] = 'untapped'

    return result


def extract_mana_dorks(card: Dict) -> Dict:
    """
    Extract mana dork mechanics (creatures that produce mana).

    Returns:
        {
            'is_mana_dork': bool,
            'mana_produced': List[str],
            'has_summoning_sickness': bool,
            'conditional': bool,
            'power': str,
            'toughness': str,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    card_type = card.get('type_line', '').lower()

    result = {
        'is_mana_dork': False,
        'mana_produced': [],
        'has_summoning_sickness': True,  # Assume yes unless haste
        'conditional': False,
        'power': card.get('power', ''),
        'toughness': card.get('toughness', ''),
        'examples': []
    }

    # Must be a creature
    if 'creature' not in card_type:
        return result

    if not text:
        return result

    # Mana production patterns (same as rocks)
    mana_patterns = [
        r'\{t\}:\s*add\s+((?:\{[wubrgc]\})+)',
        r'\{t\}:\s*add\s+(?:one\s+mana\s+of\s+)?any\s+(?:color|one\s+color)',
        r'\{t\}:\s*add\s+.*mana',
    ]

    for pattern in mana_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_mana_dork'] = True
            result['examples'].append(match.group(0))

            # Determine mana produced
            if 'any color' in match.group(0):
                result['mana_produced'] = ['any']
            elif match.lastindex and match.group(1):
                mana_str = match.group(1)
                mana_symbols = re.findall(r'\{([wubrgc])\}', mana_str.lower())
                result['mana_produced'] = [m.upper() for m in mana_symbols]

            break

    if not result['is_mana_dork']:
        return result

    # Check for haste
    if 'haste' in text:
        result['has_summoning_sickness'] = False

    # Check if conditional
    conditional_keywords = ['as long as', 'if you control', 'only if', 'only activate']
    result['conditional'] = any(keyword in text for keyword in conditional_keywords)

    return result


def extract_ritual_effects(card: Dict) -> Dict:
    """
    Extract ritual effects (temporary mana).

    Returns:
        {
            'is_ritual': bool,
            'mana_produced': int,  # Total mana added
            'mana_types': List[str],
            'net_mana': int,  # Mana produced - spell cost
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    card_type = card.get('type_line', '').lower()

    result = {
        'is_ritual': False,
        'mana_produced': 0,
        'mana_types': [],
        'net_mana': 0,
        'conditions': [],
        'examples': []
    }

    # Must be instant or sorcery (or have ritual-like ability)
    if 'instant' not in card_type and 'sorcery' not in card_type:
        return result

    if not text:
        return result

    # Ritual patterns: "Add {C}{C}{C}" or "Add {R}{R}{R}"
    ritual_patterns = [
        r'add\s+((?:\{[wubrgc]\})+)',  # Match multiple mana symbols
        r'add\s+(\d+)\s+mana',
        r'add.*mana\s+equal\s+to',
    ]

    for pattern in ritual_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_ritual'] = True
            result['examples'].append(match.group(0))

            # Parse mana produced
            if match.lastindex and match.group(1):
                mana_str = match.group(1)

                # Count mana symbols
                mana_symbols = re.findall(r'\{([wubrgc])\}', mana_str.lower())
                if mana_symbols:
                    result['mana_produced'] = len(mana_symbols)
                    result['mana_types'] = [m.upper() for m in list(set(mana_symbols))]
                elif mana_str.isdigit():
                    result['mana_produced'] = int(mana_str)
                    result['mana_types'] = ['C']

            # Calculate net mana (mana produced - spell cost)
            cmc = card.get('cmc', 0)
            result['net_mana'] = result['mana_produced'] - cmc

            break

    if not result['is_ritual']:
        return result

    # Check for conditions
    condition_patterns = [
        (r'equal\s+to.*devotion', 'devotion'),
        (r'equal\s+to.*creatures?', 'creature_count'),
        (r'equal\s+to.*lands?', 'land_count'),
        (r'storm', 'storm'),
    ]

    for pattern, condition in condition_patterns:
        if re.search(pattern, text):
            result['conditions'].append(condition)

    return result


def extract_cost_reduction(card: Dict) -> Dict:
    """
    Extract cost reduction effects.

    Returns:
        {
            'has_cost_reduction': bool,
            'reduction_type': str,  # 'all_spells', 'creature_spells', 'artifact_spells', 'specific_type'
            'reduction_amount': int,  # How much cheaper (in generic mana)
            'affects': str,  # 'you', 'all_players', 'opponents'
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_cost_reduction': False,
        'reduction_type': None,
        'reduction_amount': 0,
        'affects': 'you',
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Cost reduction patterns
    # "Creature spells you cast cost {2} less to cast"
    # "Artifact spells cost {1} less to cast"
    reduction_patterns = [
        r'(.*?)\s+spells?\s+(?:you\s+cast\s+)?costs?\s+\{(\d+)\}\s+less',
        r'spells?\s+(?:you\s+cast\s+)?costs?\s+\{(\d+)\}\s+less',
    ]

    for pattern in reduction_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_cost_reduction'] = True
            result['examples'].append(match.group(0))

            # Parse reduction amount
            groups = match.groups()
            for group in reversed(groups):
                if group and group.isdigit():
                    result['reduction_amount'] = int(group)
                    break

            # Determine spell type
            if 'creature' in match.group(0):
                result['reduction_type'] = 'creature_spells'
            elif 'artifact' in match.group(0):
                result['reduction_type'] = 'artifact_spells'
            elif 'instant' in match.group(0) or 'sorcery' in match.group(0):
                result['reduction_type'] = 'instant_sorcery_spells'
            else:
                result['reduction_type'] = 'all_spells'

            break

    if not result['has_cost_reduction']:
        return result

    # Check who it affects
    if 'each player' in text:
        result['affects'] = 'all_players'
    elif 'opponent' in text:
        result['affects'] = 'opponents'
    else:
        result['affects'] = 'you'

    # Check for conditions
    condition_patterns = [
        (r'during\s+your\s+turn', 'your_turn'),
        (r'as\s+long\s+as', 'conditional'),
        (r'if\s+you\s+control', 'control_condition'),
    ]

    for pattern, condition in condition_patterns:
        if re.search(pattern, text):
            result['conditions'].append(condition)

    return result


def extract_land_ramp(card: Dict) -> Dict:
    """
    Extract land ramp effects (effects that put lands onto battlefield).

    Returns:
        {
            'is_land_ramp': bool,
            'lands_fetched': int,  # Number of lands
            'land_type': str,  # 'basic', 'any', 'specific_type'
            'destination': str,  # 'battlefield', 'hand', 'top'
            'tapped': bool,  # Do lands enter tapped?
            'repeatable': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_land_ramp': False,
        'lands_fetched': 0,
        'land_type': None,
        'destination': None,
        'tapped': False,
        'repeatable': False,
        'examples': []
    }

    if not text:
        return result

    # Land ramp patterns
    # "Search your library for a basic land card and put it onto the battlefield"
    # "Put a land card from your hand onto the battlefield"
    ramp_patterns = [
        r'search\s+your\s+library\s+for\s+(?:a\s+|up\s+to\s+)?(\w+\s+)?lands?\s+card.*?(?:put|place)',
        r'(?:put|place)\s+(?:a\s+|up\s+to\s+\d+\s+)?lands?\s+card.*?(?:onto\s+the\s+battlefield|into\s+play)',
    ]

    for pattern in ramp_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_land_ramp'] = True
            result['examples'].append(match.group(0))

            # Determine number of lands
            numbers = re.findall(r'up\s+to\s+(\d+)', match.group(0))
            if numbers:
                result['lands_fetched'] = int(numbers[0])
            else:
                result['lands_fetched'] = 1

            # Determine land type
            if 'basic' in match.group(0):
                result['land_type'] = 'basic'
            elif 'forest' in match.group(0) or 'plains' in match.group(0) or 'island' in match.group(0):
                result['land_type'] = 'specific_type'
            else:
                result['land_type'] = 'any'

            # Determine destination
            if 'onto the battlefield' in match.group(0) or 'into play' in match.group(0):
                result['destination'] = 'battlefield'
            elif 'into your hand' in match.group(0):
                result['destination'] = 'hand'
            elif 'on top' in match.group(0):
                result['destination'] = 'top'
            else:
                result['destination'] = 'battlefield'  # Default

            # Check if tapped
            result['tapped'] = 'tapped' in match.group(0)

            break

    if not result['is_land_ramp']:
        return result

    # Check if repeatable
    repeatable_keywords = ['whenever', 'at the beginning', '{t}:']
    result['repeatable'] = any(keyword in text for keyword in repeatable_keywords)

    return result


def classify_ramp_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all ramp mechanics.

    Returns a comprehensive dictionary with all ramp information.
    """
    return {
        'mana_rocks': extract_mana_rocks(card),
        'mana_dorks': extract_mana_dorks(card),
        'ritual_effects': extract_ritual_effects(card),
        'cost_reduction': extract_cost_reduction(card),
        'land_ramp': extract_land_ramp(card)
    }
