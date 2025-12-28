"""
Class Enchantment Extractors

Extracts mechanics from Class enchantments (leveling enchantments introduced in Zendikar Rising).

Class enchantments have multiple levels:
- Level 1 (base): Active when cast
- Level 2: Unlocked by paying activation cost
- Level 3: Unlocked by paying second activation cost

Each level can have different abilities that stack with previous levels.
"""

import re
from typing import Dict, List, Optional, Tuple


def extract_class_levels(card: Dict) -> Dict:
    """
    Extract all levels and abilities from a Class enchantment.

    Examples:
    - Artist's Talent: Level 1 = discard/draw trigger, Level 2 = cost reduction, Level 3 = damage boost
    - Barbarian Class: Level 1 = buff, Level 2 = double strike, Level 3 = combat triggers

    Returns:
        {
            'is_class': bool,
            'levels': List[Dict],  # Each dict is a level with abilities
            'max_level': int,
            'has_triggers': bool,
            'has_cost_reduction': bool,
            'has_damage_boost': bool,
            'has_static_buff': bool
        }
    """
    oracle_text = card.get('oracle_text', '')
    type_line = card.get('type_line', '').lower()

    result = {
        'is_class': False,
        'levels': [],
        'max_level': 1,
        'has_triggers': False,
        'has_cost_reduction': False,
        'has_damage_boost': False,
        'has_static_buff': False,
        'has_modal_trigger': False
    }

    # Check if this is a Class enchantment
    if 'class' not in type_line or 'enchantment' not in type_line:
        return result

    result['is_class'] = True

    # Parse levels from oracle text
    # Class format: Level 1 (implicit), then ": Level 2\n<abilities>", then ": Level 3\n<abilities>"
    levels = _parse_class_levels_from_text(oracle_text)
    result['levels'] = levels
    result['max_level'] = len(levels)

    # Analyze all levels for capability flags
    for level in levels:
        for ability in level.get('abilities', []):
            ability_lower = ability.lower()

            # Check for triggered abilities
            if 'whenever' in ability_lower or 'when ' in ability_lower:
                result['has_triggers'] = True

                # Check for modal triggers (may/choice)
                if 'you may' in ability_lower or 'choose' in ability_lower:
                    result['has_modal_trigger'] = True

            # Check for cost reduction
            if re.search(r'spells?.*cost.*less', ability_lower) or re.search(r'cost.*{.*}.*less', ability_lower):
                result['has_cost_reduction'] = True

            # Check for damage amplification/boost
            if re.search(r'deal.*damage.*plus|\+\d+ damage|damage.*additional|deals? that much.*plus', ability_lower):
                result['has_damage_boost'] = True

            # Check for static buffs (anthem effects)
            if re.search(r'creatures? you control get \+\d+/\+\d+', ability_lower):
                result['has_static_buff'] = True

    return result


def _parse_class_levels_from_text(oracle_text: str) -> List[Dict]:
    """
    Parse individual levels from Class enchantment oracle text.

    Format:
    <Level 1 abilities>
    : Level 2
    <Level 2 abilities>
    : Level 3
    <Level 3 abilities>

    Returns list of dicts, one per level, with abilities and metadata.
    """
    levels = []

    # Split by level markers
    # Level markers are formatted as ": Level 2" or similar
    level_pattern = r':\s*Level\s*(\d+)'

    # Split text into sections
    sections = re.split(level_pattern, oracle_text)

    if len(sections) == 1:
        # No explicit levels, just base ability
        abilities = _extract_abilities_from_section(sections[0])
        if abilities:
            levels.append({
                'level': 1,
                'abilities': abilities,
                'cost': None
            })
        return levels

    # First section is Level 1 (before first ": Level X")
    level_1_text = sections[0]
    level_1_abilities = _extract_abilities_from_section(level_1_text)
    if level_1_abilities:
        levels.append({
            'level': 1,
            'abilities': level_1_abilities,
            'cost': None  # Level 1 is free (comes with the card)
        })

    # Process remaining sections (Level 2+)
    # sections is now [level1_text, '2', level2_text, '3', level3_text, ...]
    i = 1
    while i < len(sections) - 1:
        level_num = int(sections[i])
        level_text = sections[i + 1] if i + 1 < len(sections) else ''

        # Extract activation cost (appears before level abilities)
        cost = _extract_level_cost(level_text)

        # Extract abilities for this level
        abilities = _extract_abilities_from_section(level_text)

        if abilities:
            levels.append({
                'level': level_num,
                'abilities': abilities,
                'cost': cost
            })

        i += 2

    return levels


def _extract_level_cost(level_text: str) -> Optional[str]:
    """
    Extract the mana cost to level up to this level.

    Format: typically appears before the abilities, like "{2}{R}: Level 2"
    But our split removes that, so this is a placeholder for now.
    """
    # Note: In actual card text, the cost appears BEFORE ": Level X"
    # Our parsing removes it, so we'd need the raw text
    # For now, return None - can be enhanced if needed
    return None


def _extract_abilities_from_section(text: str) -> List[str]:
    """
    Extract individual ability sentences from a section of text.

    Abilities are typically separated by newlines or periods.
    """
    if not text or not text.strip():
        return []

    # Clean up the text
    text = text.strip()

    # Remove level-up instruction line if present
    text = re.sub(r'\(Gain the next level.*?\)', '', text, flags=re.IGNORECASE)

    # Split by newlines first (most reliable separator)
    lines = text.split('\n')

    abilities = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(':'):
            continue

        # Some abilities may have multiple sentences - split by period
        # But be careful with mana symbols like "{2}."
        sentences = re.split(r'\.\s+', line)
        for sentence in sentences:
            sentence = sentence.strip().rstrip('.')
            if sentence and len(sentence) > 3:  # Filter out fragments
                abilities.append(sentence)

    return abilities


def extract_cost_reduction_from_class(card: Dict) -> Dict:
    """
    Extract cost reduction specifically from Class levels.

    Examples:
    - Artist's Talent Level 2: "Noncreature spells you cast cost {1} less to cast"

    Returns:
        {
            'has_cost_reduction': bool,
            'reduction_amount': int,  # Generic mana reduced
            'spell_types': List[str],  # 'noncreature', 'instant_sorcery', 'all'
            'at_level': int  # Which level grants this
        }
    """
    class_info = extract_class_levels(card)

    result = {
        'has_cost_reduction': False,
        'reduction_amount': 0,
        'spell_types': [],
        'at_level': 0
    }

    if not class_info['is_class']:
        return result

    # Check each level for cost reduction
    for level in class_info['levels']:
        for ability in level.get('abilities', []):
            ability_lower = ability.lower()

            # Pattern: "Spells you cast cost {X} less"
            cost_match = re.search(r'spells?.*cost\s+{(\d+)}.*less', ability_lower)
            if cost_match:
                result['has_cost_reduction'] = True
                result['reduction_amount'] = int(cost_match.group(1))
                result['at_level'] = level['level']

                # Determine what types of spells
                if 'noncreature' in ability_lower:
                    result['spell_types'].append('noncreature')
                elif 'instant or sorcery' in ability_lower or 'instant and sorcery' in ability_lower:
                    result['spell_types'].append('instant_sorcery')
                elif 'creature' in ability_lower and 'noncreature' not in ability_lower:
                    result['spell_types'].append('creature')
                else:
                    result['spell_types'].append('all')

                break

    return result


def extract_damage_boost_from_class(card: Dict) -> Dict:
    """
    Extract damage amplification from Class levels.

    Examples:
    - Artist's Talent Level 3: "...deals that much damage plus 2 instead"

    Returns:
        {
            'has_damage_boost': bool,
            'boost_amount': int,
            'damage_types': List[str],  # 'noncombat', 'combat', 'all'
            'source_restriction': str,  # 'sources_you_control', 'any'
            'at_level': int
        }
    """
    class_info = extract_class_levels(card)

    result = {
        'has_damage_boost': False,
        'boost_amount': 0,
        'damage_types': [],
        'source_restriction': None,
        'at_level': 0
    }

    if not class_info['is_class']:
        return result

    # Check each level
    for level in class_info['levels']:
        for ability in level.get('abilities', []):
            ability_lower = ability.lower()

            # Pattern: "deals that much damage plus X instead"
            boost_match = re.search(r'deals? that much damage plus (\d+)', ability_lower)
            if not boost_match:
                # Alternative: "deals X additional damage" or "+X damage"
                boost_match = re.search(r'deals? (\d+) additional damage', ability_lower)
                if not boost_match:
                    boost_match = re.search(r'\+(\d+) damage', ability_lower)

            if boost_match:
                result['has_damage_boost'] = True
                result['boost_amount'] = int(boost_match.group(1))
                result['at_level'] = level['level']

                # Check damage type restriction
                if 'noncombat damage' in ability_lower:
                    result['damage_types'].append('noncombat')
                elif 'combat damage' in ability_lower:
                    result['damage_types'].append('combat')
                else:
                    result['damage_types'].append('all')

                # Check source restriction
                if 'source you control' in ability_lower or 'sources you control' in ability_lower:
                    result['source_restriction'] = 'sources_you_control'
                else:
                    result['source_restriction'] = 'any'

                break

    return result


def extract_modal_triggers_from_class(card: Dict) -> Dict:
    """
    Extract triggered abilities with modal/optional effects from Class levels.

    Examples:
    - Artist's Talent Level 1: "Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card."

    Returns:
        {
            'has_modal_trigger': bool,
            'trigger_event': str,  # 'cast_noncreature', 'etb', etc.
            'modal_type': str,  # 'optional' (you may), 'choice' (choose one)
            'effects': List[str],  # The effects that can happen
            'at_level': int
        }
    """
    class_info = extract_class_levels(card)

    result = {
        'has_modal_trigger': False,
        'trigger_event': None,
        'modal_type': None,
        'effects': [],
        'at_level': 0
    }

    if not class_info['is_class']:
        return result

    # Check each level
    for level in class_info['levels']:
        for ability in level.get('abilities', []):
            ability_lower = ability.lower()

            # Check if it's a triggered ability
            if not ('whenever' in ability_lower or 'when ' in ability_lower):
                continue

            # Check if it's modal
            is_modal = 'you may' in ability_lower or 'choose' in ability_lower

            if is_modal:
                result['has_modal_trigger'] = True
                result['at_level'] = level['level']

                # Determine modal type
                if 'you may' in ability_lower:
                    result['modal_type'] = 'optional'
                elif 'choose' in ability_lower:
                    result['modal_type'] = 'choice'

                # Determine trigger event
                if 'cast a noncreature spell' in ability_lower:
                    result['trigger_event'] = 'cast_noncreature'
                elif 'cast an instant or sorcery' in ability_lower:
                    result['trigger_event'] = 'cast_instant_sorcery'
                elif 'enters the battlefield' in ability_lower:
                    result['trigger_event'] = 'etb'
                elif 'attacks' in ability_lower or 'attack' in ability_lower:
                    result['trigger_event'] = 'attack'

                # Extract effects (simplified)
                # For "you may discard a card. If you do, draw a card"
                if 'discard' in ability_lower and 'draw' in ability_lower:
                    result['effects'] = ['discard_to_draw']
                elif 'sacrifice' in ability_lower:
                    result['effects'] = ['sacrifice']
                elif 'damage' in ability_lower:
                    result['effects'] = ['damage']

                break

    return result
