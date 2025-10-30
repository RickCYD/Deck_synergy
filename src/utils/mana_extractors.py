"""
Mana Land Extractors
Extract and classify different types of mana-producing lands from card text.
"""

import re
from typing import Dict, List, Set, Optional


def extract_mana_colors(oracle_text: str, type_line: str) -> Set[str]:
    """
    Extract what colors of mana a land can produce.

    Args:
        oracle_text: Card's oracle text
        type_line: Card's type line

    Returns:
        Set of color letters {'W', 'U', 'B', 'R', 'G', 'C'}
    """
    colors = set()
    text = oracle_text.lower()

    # Find all mana symbols in the text using findall
    if re.findall(r'\{w\}', text) or re.search(r'add.*white mana', text):
        colors.add('W')
    if re.findall(r'\{u\}', text) or re.search(r'add.*blue mana', text):
        colors.add('U')
    if re.findall(r'\{b\}', text) or re.search(r'add.*black mana', text):
        colors.add('B')
    if re.findall(r'\{r\}', text) or re.search(r'add.*red mana', text):
        colors.add('R')
    if re.findall(r'\{g\}', text) or re.search(r'add.*green mana', text):
        colors.add('G')
    if re.findall(r'\{c\}', text) or re.search(r'add.*colorless mana', text):
        colors.add('C')

    # "Add one mana of any color"
    if re.search(r'add one mana of any color', text):
        colors = {'W', 'U', 'B', 'R', 'G'}

    # "Add two mana in any combination of colors"
    if re.search(r'add.*mana in any combination', text):
        colors = {'W', 'U', 'B', 'R', 'G'}

    # Basic land types grant mana (e.g., "Forest" produces {G})
    if 'plains' in type_line.lower():
        colors.add('W')
    if 'island' in type_line.lower():
        colors.add('U')
    if 'swamp' in type_line.lower():
        colors.add('B')
    if 'mountain' in type_line.lower():
        colors.add('R')
    if 'forest' in type_line.lower():
        colors.add('G')

    return colors


def classify_basic_land(card: Dict) -> Optional[Dict]:
    """
    Classify basic lands.

    Types:
    - Basic lands (Plains, Island, Swamp, Mountain, Forest)
    - Snow-covered basics
    - Wastes (colorless basic)

    Args:
        card: Card dictionary

    Returns:
        Classification dict or None if not a basic land
    """
    type_line = card.get('type_line', '').lower()
    name = card.get('name', '').lower()
    oracle_text = card.get('oracle_text', '').lower()

    # Check if it's a basic land
    if 'basic' not in type_line:
        return None

    colors = extract_mana_colors(oracle_text, type_line)

    classification = {
        'land_type': 'basic',
        'colors': list(colors),
        'enters_tapped': False,
        'untap_conditions': [],
        'is_snow': 'snow' in type_line
    }

    # Determine specific basic type
    if 'plains' in type_line:
        classification['subtype'] = 'plains'
    elif 'island' in type_line:
        classification['subtype'] = 'island'
    elif 'swamp' in type_line:
        classification['subtype'] = 'swamp'
    elif 'mountain' in type_line:
        classification['subtype'] = 'mountain'
    elif 'forest' in type_line:
        classification['subtype'] = 'forest'
    elif 'wastes' in name:
        classification['subtype'] = 'wastes'
        classification['colors'] = ['C']

    return classification


def classify_fetch_land(card: Dict) -> Optional[Dict]:
    """
    Classify fetch lands.

    Types:
    - True fetches (sacrifice, search for land, put onto battlefield)
    - Slow fetches (enters tapped, search)
    - Evolving Wilds variants

    Args:
        card: Card dictionary

    Returns:
        Classification dict or None if not a fetch land
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    if 'land' not in type_line:
        return None

    # Pattern: sacrifice + search library + land
    is_fetch = re.search(r'sacrifice.*search your library.*land', oracle_text) or \
               re.search(r'{t}.*sacrifice.*search.*land', oracle_text)

    if not is_fetch:
        return None

    classification = {
        'land_type': 'fetch',
        'colors': [],  # Fetch lands typically don't produce mana themselves
        'enters_tapped': 'enters the battlefield tapped' in oracle_text,
        'untap_conditions': []
    }

    # True fetch (can get any land type)
    if re.search(r'search.*for a.*land card', oracle_text):
        if re.search(r'plains|island|swamp|mountain|forest', oracle_text):
            classification['subtype'] = 'typed_fetch'
            # Extract which basic types
            fetch_types = []
            if 'plains' in oracle_text:
                fetch_types.append('Plains')
            if 'island' in oracle_text:
                fetch_types.append('Island')
            if 'swamp' in oracle_text:
                fetch_types.append('Swamp')
            if 'mountain' in oracle_text:
                fetch_types.append('Mountain')
            if 'forest' in oracle_text:
                fetch_types.append('Forest')
            classification['can_fetch'] = fetch_types
        else:
            classification['subtype'] = 'basic_fetch'
            classification['can_fetch'] = ['any_basic']

    # Enters tapped (slow fetch)
    if classification['enters_tapped']:
        classification['is_slow'] = True
    else:
        classification['is_slow'] = False

    return classification


def classify_dual_land(card: Dict) -> Optional[Dict]:
    """
    Classify dual lands (lands that produce two colors).

    Types:
    - Original duals (untapped, no drawback)
    - Shock lands (untapped with life payment)
    - Check lands (untapped with condition)
    - Pain lands (deal damage)
    - Filter lands
    - Bounce lands (return land to hand)
    - Gain lands (enters tapped, gain life)
    - Scry lands (enters tapped, scry)
    - Surveil lands (enters tapped, surveil)

    Args:
        card: Card dictionary

    Returns:
        Classification dict or None if not a dual land
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    if 'land' not in type_line:
        return None

    colors = extract_mana_colors(oracle_text, type_line)

    # Must produce at least 2 colors to be a dual
    if len(colors) < 2:
        return None

    classification = {
        'land_type': 'dual',
        'colors': list(colors),
        'enters_tapped': False,
        'untap_conditions': []
    }

    # Count basic land types in type line
    basic_types_count = sum([
        'plains' in type_line,
        'island' in type_line,
        'swamp' in type_line,
        'mountain' in type_line,
        'forest' in type_line
    ])

    # Shock land (pay 2 life or enters tapped) - CHECK FIRST
    if re.search(r'(as .* enters|when .* enters).*you may pay 2 life', oracle_text) or \
       re.search(r'you may pay 2 life.*if you don\'?t.*enters.*tapped', oracle_text):
        classification['subtype'] = 'shock_land'
        classification['enters_tapped'] = False  # Can be untapped
        classification['untap_conditions'].append({
            'condition': 'pay_life',
            'cost': 2,
            'description': 'Pay 2 life to enter untapped'
        })
        return classification

    # Check land (untapped if you control specific land type)
    if re.search(r'enters.*tapped unless you control (a|an) (plains|island|swamp|mountain|forest)', oracle_text):
        classification['subtype'] = 'check_land'
        classification['enters_tapped'] = True
        match = re.search(r'unless you control (a|an) (plains|island|swamp|mountain|forest)', oracle_text)
        if match:
            classification['untap_conditions'].append({
                'condition': 'control_land_type',
                'required_type': match.group(2).capitalize(),
                'description': f'Enter untapped if you control a {match.group(2).capitalize()}'
            })
        return classification

    # Original dual (has basic land types, no drawback after other checks)
    if basic_types_count >= 2 and 'enters the battlefield tapped' not in oracle_text and 'enters tapped' not in oracle_text:
        classification['subtype'] = 'original_dual'
        classification['enters_tapped'] = False
        return classification

    # Pain land (deals damage when used for colored mana)
    if re.search(r'deals 1 damage to you', oracle_text) and '{t}: add {c}' in oracle_text:
        classification['subtype'] = 'pain_land'
        classification['enters_tapped'] = False
        classification['drawback'] = 'deals_damage'
        return classification

    # Bounce land (return land to hand)
    if re.search(r'return.*land you control to (its owner\'?s|your) hand', oracle_text):
        classification['subtype'] = 'bounce_land'
        classification['enters_tapped'] = 'enters the battlefield tapped' in oracle_text
        classification['drawback'] = 'bounce_land'
        return classification

    # Gain land (enters tapped, gain life)
    if 'enters the battlefield tapped' in oracle_text and 'you gain' in oracle_text and 'life' in oracle_text:
        classification['subtype'] = 'gain_land'
        classification['enters_tapped'] = True
        return classification

    # Scry land (enters tapped, scry)
    if 'enters the battlefield tapped' in oracle_text and 'scry' in oracle_text:
        classification['subtype'] = 'scry_land'
        classification['enters_tapped'] = True
        return classification

    # Surveil land (enters tapped, surveil)
    if 'enters the battlefield tapped' in oracle_text and 'surveil' in oracle_text:
        classification['subtype'] = 'surveil_land'
        classification['enters_tapped'] = True
        return classification

    # Fast land (untapped if you control 2 or fewer other lands)
    if re.search(r'enters.*tapped unless you control (two or fewer|2 or fewer) other lands', oracle_text):
        classification['subtype'] = 'fast_land'
        classification['enters_tapped'] = True
        classification['untap_conditions'].append({
            'condition': 'land_count',
            'max_lands': 2,
            'description': 'Enter untapped if you control 2 or fewer other lands'
        })
        return classification

    # Generic tapped dual
    if 'enters the battlefield tapped' in oracle_text:
        classification['subtype'] = 'tapped_dual'
        classification['enters_tapped'] = True
        return classification

    # Untapped dual with no identified drawback
    classification['subtype'] = 'untapped_dual'
    return classification


def classify_triome(card: Dict) -> Optional[Dict]:
    """
    Classify triome lands (lands that produce three colors).

    Triomes typically:
    - Have three basic land types
    - Enter tapped
    - Have cycling

    Args:
        card: Card dictionary

    Returns:
        Classification dict or None if not a triome
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    if 'land' not in type_line:
        return None

    colors = extract_mana_colors(oracle_text, type_line)

    # Must produce exactly 3 colors to be a triome
    if len(colors) != 3 or 'C' in colors:
        return None

    # Count basic land types in type line
    basic_types_count = sum([
        'plains' in type_line,
        'island' in type_line,
        'swamp' in type_line,
        'mountain' in type_line,
        'forest' in type_line
    ])

    # Triomes have 3 basic land types
    if basic_types_count != 3:
        return None

    classification = {
        'land_type': 'triome',
        'subtype': 'triome',
        'colors': list(colors),
        'enters_tapped': 'enters the battlefield tapped' in oracle_text,
        'untap_conditions': [],
        'has_cycling': 'cycling' in oracle_text
    }

    return classification


def classify_special_land(card: Dict) -> Optional[Dict]:
    """
    Classify special/unique lands.

    Types:
    - Command Tower (produces commander's colors)
    - Utility lands (man-lands, creature lands)
    - Colorless utility lands

    Args:
        card: Card dictionary

    Returns:
        Classification dict or None
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()
    name = card.get('name', '').lower()

    if 'land' not in type_line:
        return None

    colors = extract_mana_colors(oracle_text, type_line)

    classification = {
        'land_type': 'special',
        'colors': list(colors),
        'enters_tapped': 'enters the battlefield tapped' in oracle_text,
        'untap_conditions': []
    }

    # Command Tower
    if 'command tower' in name:
        classification['subtype'] = 'command_tower'
        classification['colors'] = ['W', 'U', 'B', 'R', 'G']  # Can produce any commander color
        classification['special_ability'] = 'commander_colors'
        return classification

    # Commander's Sphere, Opal Palace, etc.
    if 'commander' in oracle_text or "your commander's color identity" in oracle_text:
        classification['subtype'] = 'commander_related'
        classification['special_ability'] = 'commander_colors'
        return classification

    # Man-land / Creature land
    if re.search(r'becomes? a.*creature', oracle_text):
        classification['subtype'] = 'man_land'
        classification['special_ability'] = 'becomes_creature'
        return classification

    # Utility land with activated ability
    if re.search(r'{[0-9wtubrgc]*}.*:', oracle_text) and len(colors) <= 1:
        classification['subtype'] = 'utility_land'
        classification['special_ability'] = 'activated_ability'
        return classification

    return classification


def classify_mana_land(card: Dict) -> Dict:
    """
    Comprehensive classification of a mana-producing land.

    Args:
        card: Card dictionary with type_line and oracle_text

    Returns:
        Dictionary with land classification
    """
    type_line = card.get('type_line', '').lower()

    # Must be a land
    if 'land' not in type_line:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': False,
            'classification': None
        }

    # Try each classification in order of specificity
    result = None

    # Basic lands first (most specific)
    result = classify_basic_land(card)
    if result:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': True,
            'classification': result
        }

    # Fetch lands
    result = classify_fetch_land(card)
    if result:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': True,
            'classification': result
        }

    # Triomes (before duals, as they're more specific)
    result = classify_triome(card)
    if result:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': True,
            'classification': result
        }

    # Dual lands
    result = classify_dual_land(card)
    if result:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': True,
            'classification': result
        }

    # Special lands
    result = classify_special_land(card)
    if result:
        return {
            'card_name': card.get('name', 'Unknown'),
            'is_land': True,
            'classification': result
        }

    # Generic land (couldn't classify further)
    oracle_text = card.get('oracle_text', '').lower()
    colors = extract_mana_colors(oracle_text, type_line)

    return {
        'card_name': card.get('name', 'Unknown'),
        'is_land': True,
        'classification': {
            'land_type': 'generic',
            'subtype': 'unclassified',
            'colors': list(colors),
            'enters_tapped': 'enters the battlefield tapped' in oracle_text,
            'untap_conditions': []
        }
    }
