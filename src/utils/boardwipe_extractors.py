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

Board Wipe Extractors
Extract and classify board wipe effects from card text.
"""

import re
from typing import Dict, List, Optional


def extract_creature_wipes(card: Dict) -> List[Dict]:
    """
    Extract creature board wipe effects.

    Types:
    - Destroy all creatures (symmetrical)
    - Destroy all creatures you don't control (one-sided)
    - Destroy all creatures with condition (conditional)
    - Damage to all creatures (damage-based)
    - -X/-X to all creatures (toughness reduction)
    - Exile all creatures

    Args:
        card: Card dictionary

    Returns:
        List of creature wipe dictionaries
    """
    wipes = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return wipes

    # Destroy all creatures (symmetrical)
    if re.search(r'destroy all creatures(?!.*you control|.*you don\'t control)', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all creatures'
        })

    # Destroy all creatures you don't control (one-sided)
    if re.search(r'destroy all creatures you don\'t control', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'destroy',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Destroy all creatures you don\'t control'
        })

    # Destroy creatures with condition
    conditional_patterns = [
        (r'destroy all (nonland|nontoken|attacking|tapped|untapped) creatures', 'conditional'),
        (r'destroy all creatures with (power|toughness|mana value)', 'power_toughness'),
        (r'destroy all (white|blue|black|red|green) creatures', 'color_based'),
        (r'destroy all (artifact|enchantment) creatures', 'type_based'),
    ]

    for pattern, subtype in conditional_patterns:
        if re.search(pattern, oracle_text):
            wipes.append({
                'type': 'creature_wipe',
                'method': 'destroy',
                'scope': 'conditional',
                'subtype': subtype,
                'is_symmetrical': True,
                'is_one_sided': False,
                'description': f'Destroy creatures with condition ({subtype})'
            })

    # Damage to all creatures
    if re.search(r'deals \d+ damage to (each|all) creature', oracle_text):
        damage_match = re.search(r'deals (\d+) damage', oracle_text)
        wipes.append({
            'type': 'creature_wipe',
            'method': 'damage',
            'scope': 'all',
            'damage_amount': int(damage_match.group(1)) if damage_match else None,
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Damage-based board wipe'
        })

    # -X/-X to all creatures
    if re.search(r'(all|each) creature.*gets? -\d+/-\d+', oracle_text) or \
       re.search(r'gets? -\d+/-\d+.*all creatures', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'toughness_reduction',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Toughness reduction board wipe'
        })

    # Exile all creatures
    if re.search(r'exile all creatures', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'exile',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Exile all creatures'
        })

    # Exile all creatures you don't control
    if re.search(r'exile all creatures you don\'t control', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'exile',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Exile all creatures you don\'t control'
        })

    # Return all creatures to hand
    if re.search(r'return all creatures to their owner', oracle_text):
        wipes.append({
            'type': 'creature_wipe',
            'method': 'bounce',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Return all creatures to hand'
        })

    return wipes


def extract_artifact_enchantment_wipes(card: Dict) -> List[Dict]:
    """
    Extract artifact and enchantment board wipe effects.

    Args:
        card: Card dictionary

    Returns:
        List of artifact/enchantment wipe dictionaries
    """
    wipes = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return wipes

    # Destroy all artifacts
    if re.search(r'destroy all artifacts(?!.*you control)', oracle_text):
        wipes.append({
            'type': 'artifact_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all artifacts'
        })

    # Destroy all artifacts you don't control
    if re.search(r'destroy all artifacts you don\'t control', oracle_text):
        wipes.append({
            'type': 'artifact_wipe',
            'method': 'destroy',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Destroy all artifacts you don\'t control'
        })

    # Destroy all enchantments
    if re.search(r'destroy all enchantments(?!.*you control)', oracle_text):
        wipes.append({
            'type': 'enchantment_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all enchantments'
        })

    # Destroy all enchantments you don't control
    if re.search(r'destroy all enchantments you don\'t control', oracle_text):
        wipes.append({
            'type': 'enchantment_wipe',
            'method': 'destroy',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Destroy all enchantments you don\'t control'
        })

    # Destroy all artifacts and enchantments
    if re.search(r'destroy all artifacts and enchantments', oracle_text):
        wipes.append({
            'type': 'artifact_enchantment_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all artifacts and enchantments'
        })

    return wipes


def extract_land_wipes(card: Dict) -> List[Dict]:
    """
    Extract land destruction effects.

    Args:
        card: Card dictionary

    Returns:
        List of land wipe dictionaries
    """
    wipes = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return wipes

    # Destroy all lands
    if re.search(r'destroy all lands', oracle_text):
        wipes.append({
            'type': 'land_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all lands',
            'is_mass_land_destruction': True
        })

    # Destroy all lands you don't control
    if re.search(r'destroy all lands you don\'t control', oracle_text):
        wipes.append({
            'type': 'land_wipe',
            'method': 'destroy',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Destroy all lands you don\'t control',
            'is_mass_land_destruction': True
        })

    # Destroy all nonbasic lands
    if re.search(r'destroy all nonbasic lands', oracle_text):
        wipes.append({
            'type': 'land_wipe',
            'method': 'destroy',
            'scope': 'nonbasic',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all nonbasic lands',
            'is_mass_land_destruction': True
        })

    return wipes


def extract_token_wipes(card: Dict) -> List[Dict]:
    """
    Extract token-specific wipe effects.

    Args:
        card: Card dictionary

    Returns:
        List of token wipe dictionaries
    """
    wipes = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return wipes

    # Destroy all tokens
    if re.search(r'destroy all tokens', oracle_text):
        wipes.append({
            'type': 'token_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all tokens'
        })

    # Exile all tokens
    if re.search(r'exile all tokens', oracle_text):
        wipes.append({
            'type': 'token_wipe',
            'method': 'exile',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Exile all tokens'
        })

    return wipes


def extract_permanent_wipes(card: Dict) -> List[Dict]:
    """
    Extract permanent board wipe effects (everything).

    Args:
        card: Card dictionary

    Returns:
        List of permanent wipe dictionaries
    """
    wipes = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return wipes

    # Destroy all permanents
    if re.search(r'destroy all permanents', oracle_text):
        wipes.append({
            'type': 'permanent_wipe',
            'method': 'destroy',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all permanents',
            'is_apocalypse': True
        })

    # Destroy all nonland permanents
    if re.search(r'destroy all nonland permanents', oracle_text):
        wipes.append({
            'type': 'permanent_wipe',
            'method': 'destroy',
            'scope': 'nonland',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Destroy all nonland permanents'
        })

    # Exile all permanents
    if re.search(r'exile all permanents', oracle_text):
        wipes.append({
            'type': 'permanent_wipe',
            'method': 'exile',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Exile all permanents',
            'is_apocalypse': True
        })

    # Return all permanents to hand
    if re.search(r'return all (nonland )?permanents to their owner', oracle_text):
        wipes.append({
            'type': 'permanent_wipe',
            'method': 'bounce',
            'scope': 'all',
            'is_symmetrical': True,
            'is_one_sided': False,
            'description': 'Return all permanents to hand'
        })

    # Return all nonland permanents you don't control
    if re.search(r'return all (nonland )?permanents you don\'t control', oracle_text):
        wipes.append({
            'type': 'permanent_wipe',
            'method': 'bounce',
            'scope': 'opponents',
            'is_symmetrical': False,
            'is_one_sided': True,
            'description': 'Return all permanents you don\'t control to hand'
        })

    return wipes


def classify_board_wipe(card: Dict) -> Dict:
    """
    Comprehensive classification of all board wipe effects.

    Args:
        card: Card dictionary

    Returns:
        Dictionary with complete board wipe classification
    """
    creature_wipes = extract_creature_wipes(card)
    artifact_enchantment_wipes = extract_artifact_enchantment_wipes(card)
    land_wipes = extract_land_wipes(card)
    token_wipes = extract_token_wipes(card)
    permanent_wipes = extract_permanent_wipes(card)

    # Determine if card is one-sided
    is_one_sided = any(
        wipe.get('is_one_sided', False)
        for wipe in (creature_wipes + artifact_enchantment_wipes +
                     land_wipes + token_wipes + permanent_wipes)
    )

    # Determine if card is symmetrical
    is_symmetrical = any(
        wipe.get('is_symmetrical', False)
        for wipe in (creature_wipes + artifact_enchantment_wipes +
                     land_wipes + token_wipes + permanent_wipes)
    )

    # Count total wipe effects
    total_wipes = (len(creature_wipes) + len(artifact_enchantment_wipes) +
                   len(land_wipes) + len(token_wipes) + len(permanent_wipes))

    return {
        'card_name': card.get('name', 'Unknown'),
        'is_board_wipe': total_wipes > 0,
        'creature_wipes': creature_wipes,
        'artifact_enchantment_wipes': artifact_enchantment_wipes,
        'land_wipes': land_wipes,
        'token_wipes': token_wipes,
        'permanent_wipes': permanent_wipes,
        'total_wipe_effects': total_wipes,
        'is_one_sided': is_one_sided,
        'is_symmetrical': is_symmetrical,
        'is_apocalypse': any(wipe.get('is_apocalypse', False)
                            for wipe in permanent_wipes),
        'affects_lands': len(land_wipes) > 0 or any(
            wipe.get('is_apocalypse', False) for wipe in permanent_wipes
        )
    }


def get_wipe_severity(classification: Dict) -> str:
    """
    Determine the severity of a board wipe.

    Args:
        classification: Board wipe classification dictionary

    Returns:
        Severity level: 'apocalypse', 'severe', 'moderate', 'selective', 'none'
    """
    if classification.get('is_apocalypse'):
        return 'apocalypse'

    if classification['permanent_wipes']:
        return 'severe'

    if classification['creature_wipes'] and classification['artifact_enchantment_wipes']:
        return 'severe'

    if classification['land_wipes']:
        return 'severe'

    if classification['creature_wipes']:
        creature_wipe = classification['creature_wipes'][0]
        if creature_wipe.get('scope') == 'all':
            return 'moderate'
        elif creature_wipe.get('scope') == 'conditional':
            return 'selective'

    if classification['artifact_enchantment_wipes'] or classification['token_wipes']:
        return 'selective'

    return 'none'
