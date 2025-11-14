"""
Tribal Effects Extractors

Extracts tribal-related mechanics from MTG cards:
- Cards that care about creature types ("choose a creature type")
- Cards that benefit creatures of a chosen/same type
- Cards that trigger based on shared creature types
- Changeling and universal tribal effects
"""

import re
from typing import Dict, List, Optional, Set


def extract_cares_about_chosen_type(card: Dict) -> Dict:
    """
    Detect if a card cares about a chosen creature type.

    Examples:
    - "Choose a creature type"
    - "Creatures of the chosen type get +1/+1"
    - "The chosen creature type"

    Args:
        card: Card dictionary with oracle_text, type_line, etc.

    Returns:
        {
            'cares_about_chosen_type': bool,
            'effect_type': str,  # 'anthem', 'damage', 'draw', 'cost_reduction', etc.
            'patterns_matched': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'cares_about_chosen_type': False,
        'effect_type': None,
        'patterns_matched': [],
        'examples': []
    }

    if not text:
        return result

    # Patterns for "chosen type" effects
    chosen_type_patterns = [
        (r'choose a creature type', 'choice'),
        (r'creature type of your choice', 'choice'),
        (r'the chosen creature type', 'chosen_reference'),
        (r'creatures of the chosen type', 'chosen_reference'),
        (r'creature of the chosen type', 'chosen_reference'),
        (r'chosen type', 'chosen_reference'),
    ]

    for pattern, pattern_type in chosen_type_patterns:
        if re.search(pattern, text):
            result['cares_about_chosen_type'] = True
            result['patterns_matched'].append(pattern_type)
            # Find the sentence containing this pattern
            sentences = text.split('.')
            for sentence in sentences:
                if re.search(pattern, sentence):
                    result['examples'].append(sentence.strip())

    if result['cares_about_chosen_type']:
        # Determine effect type
        if re.search(r'get \+\d+/\+\d+|gets \+\d+/\+\d+', text):
            result['effect_type'] = 'anthem'
        elif re.search(r'deal|deals.*damage', text):
            result['effect_type'] = 'damage'
        elif re.search(r'draw|draws.*card', text):
            result['effect_type'] = 'draw'
        elif re.search(r'cost.*less|costs.*less', text):
            result['effect_type'] = 'cost_reduction'
        elif re.search(r'whenever.*cast|whenever you cast', text):
            result['effect_type'] = 'cast_trigger'
        elif re.search(r'whenever.*enters|when.*enters', text):
            result['effect_type'] = 'etb_trigger'
        else:
            result['effect_type'] = 'other'

    return result


def extract_cares_about_same_type(card: Dict) -> Dict:
    """
    Detect if a card cares about creatures of the same type.

    Examples:
    - "Creatures that share a creature type with it get +1/+1"
    - "Creature of the same type"
    - "Another creature that shares a type"

    Args:
        card: Card dictionary

    Returns:
        {
            'cares_about_same_type': bool,
            'effect_type': str,
            'patterns_matched': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'cares_about_same_type': False,
        'effect_type': None,
        'patterns_matched': [],
        'examples': []
    }

    if not text:
        return result

    # Patterns for "same type" effects
    same_type_patterns = [
        (r'share a creature type', 'shared_type'),
        (r'shares? a (?:creature )?type', 'shared_type'),
        (r'of the same (?:creature )?type', 'same_type'),
        (r'creature of the same type', 'same_type'),
        (r'creatures that share', 'shared_type'),
        (r'another.*that shares? a type', 'shared_type'),
        (r'share.*creature type', 'shared_type'),
    ]

    for pattern, pattern_type in same_type_patterns:
        if re.search(pattern, text):
            result['cares_about_same_type'] = True
            result['patterns_matched'].append(pattern_type)
            # Find the sentence containing this pattern
            sentences = text.split('.')
            for sentence in sentences:
                if re.search(pattern, sentence):
                    result['examples'].append(sentence.strip())

    if result['cares_about_same_type']:
        # Determine effect type
        if re.search(r'get \+\d+/\+\d+|gets \+\d+/\+\d+', text):
            result['effect_type'] = 'anthem'
        elif re.search(r'deal|deals.*damage', text):
            result['effect_type'] = 'damage'
        elif re.search(r'draw|draws.*card', text):
            result['effect_type'] = 'draw'
        elif re.search(r'cost.*less|costs.*less', text):
            result['effect_type'] = 'cost_reduction'
        elif re.search(r'whenever.*enters|when.*enters', text):
            result['effect_type'] = 'etb_trigger'
        else:
            result['effect_type'] = 'other'

    return result


def extract_tribal_lords(card: Dict) -> Dict:
    """
    Detect tribal lord effects (cards that buff specific creature types).

    Examples:
    - "Goblins you control get +1/+1"
    - "Other Elves you control have haste"
    - "Zombie creatures you control get +1/+1"

    Args:
        card: Card dictionary

    Returns:
        {
            'is_tribal_lord': bool,
            'creature_types': List[str],  # Types that are buffed
            'buff_type': str,  # 'anthem', 'keyword_grant', 'cost_reduction', etc.
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    result = {
        'is_tribal_lord': False,
        'creature_types': [],
        'buff_type': None,
        'examples': []
    }

    if not text:
        return result

    # Common creature types to check for
    common_types = [
        'angel', 'artifact', 'assassin', 'beast', 'bird', 'cat', 'cleric',
        'demon', 'dragon', 'drake', 'elemental', 'elf', 'faerie', 'giant',
        'goblin', 'horror', 'human', 'illusion', 'knight', 'merfolk', 'rat',
        'rogue', 'shaman', 'sliver', 'soldier', 'spirit', 'vampire', 'wizard',
        'warrior', 'zombie', 'dwarf', 'artificer', 'druid', 'monk', 'dinosaur',
        'pirate', 'ninja', 'samurai', 'bat', 'wolf', 'snake', 'spider'
    ]

    for creature_type in common_types:
        # Pattern: "{type}s you control get/have"
        # Pattern: "other {type}s you control"
        # Pattern: "{type} creatures you control"
        patterns = [
            rf'{creature_type}s you control (?:get|have)',
            rf'other {creature_type}s you control',
            rf'{creature_type} creatures you control (?:get|have)',
            rf'each {creature_type} you control',
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                result['is_tribal_lord'] = True
                result['creature_types'].append(creature_type.capitalize())
                # Find the sentence containing this pattern
                sentences = text.split('.')
                for sentence in sentences:
                    if re.search(pattern, sentence):
                        result['examples'].append(sentence.strip())
                break

    if result['is_tribal_lord']:
        # Determine buff type
        if re.search(r'get \+\d+/\+\d+|gets \+\d+/\+\d+', text):
            result['buff_type'] = 'anthem'
        elif re.search(r'have|has.*(flying|haste|vigilance|trample|lifelink|deathtouch|first strike|double strike|menace|reach)', text):
            result['buff_type'] = 'keyword_grant'
        elif re.search(r'cost.*less|costs.*less', text):
            result['buff_type'] = 'cost_reduction'
        else:
            result['buff_type'] = 'other'

    return result


def extract_tribal_triggers(card: Dict) -> Dict:
    """
    Detect tribal triggered abilities.

    Examples:
    - "Whenever you cast an Elf spell"
    - "Whenever a Goblin enters the battlefield under your control"
    - "When a creature of a type you chose enters"

    Args:
        card: Card dictionary

    Returns:
        {
            'has_tribal_trigger': bool,
            'trigger_type': str,  # 'cast', 'etb', 'dies', 'attacks', etc.
            'creature_types': List[str],  # Specific types, or ['chosen'] for chosen types
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_tribal_trigger': False,
        'trigger_type': None,
        'creature_types': [],
        'examples': []
    }

    if not text:
        return result

    # Chosen type triggers
    chosen_trigger_patterns = [
        (r'whenever you cast.*chosen type', 'cast'),
        (r'whenever.*chosen type.*enters', 'etb'),
        (r'whenever.*chosen type.*dies', 'dies'),
        (r'whenever.*chosen type.*attacks', 'attacks'),
        (r'when.*creature of.*chosen.*enters', 'etb'),
    ]

    for pattern, trigger_type in chosen_trigger_patterns:
        if re.search(pattern, text):
            result['has_tribal_trigger'] = True
            result['trigger_type'] = trigger_type
            result['creature_types'].append('chosen')
            sentences = text.split('.')
            for sentence in sentences:
                if re.search(pattern, sentence):
                    result['examples'].append(sentence.strip())

    # Specific type triggers
    common_types = [
        'angel', 'artifact', 'assassin', 'beast', 'bird', 'cat', 'cleric',
        'demon', 'dragon', 'drake', 'elemental', 'elf', 'faerie', 'giant',
        'goblin', 'horror', 'human', 'illusion', 'knight', 'merfolk', 'rat',
        'rogue', 'shaman', 'sliver', 'soldier', 'spirit', 'vampire', 'wizard',
        'warrior', 'zombie', 'dwarf', 'artificer', 'druid', 'monk'
    ]

    for creature_type in common_types:
        type_trigger_patterns = [
            (rf'whenever you cast (?:a |an )?{creature_type}', 'cast'),
            (rf'whenever (?:a |an )?{creature_type}.*enters', 'etb'),
            (rf'whenever (?:a |an )?{creature_type}.*dies', 'dies'),
            (rf'whenever (?:a |an )?{creature_type}.*attacks', 'attacks'),
            (rf'when (?:a |an )?{creature_type}.*enters', 'etb'),
        ]

        for pattern, trigger_type in type_trigger_patterns:
            if re.search(pattern, text):
                result['has_tribal_trigger'] = True
                result['trigger_type'] = trigger_type
                if creature_type.capitalize() not in result['creature_types']:
                    result['creature_types'].append(creature_type.capitalize())
                sentences = text.split('.')
                for sentence in sentences:
                    if re.search(pattern, sentence):
                        result['examples'].append(sentence.strip())

    return result


def extract_is_changeling(card: Dict) -> bool:
    """
    Detect if a card is a Changeling (has all creature types).

    Args:
        card: Card dictionary

    Returns:
        bool: True if card is a Changeling
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    # Changeling keyword
    if 'changeling' in text:
        return True

    # Some cards explicitly state "all creature types"
    if re.search(r'(?:is |has |have )all creature types', text):
        return True

    # Check type line for "Shapeshifter" (common for changelings)
    if 'shapeshifter' in type_line and 'creature' in type_line:
        # Read oracle text to confirm
        if 'changeling' in text or 'all creature types' in text:
            return True

    return False


def extract_tribal_payoffs(card: Dict) -> Dict:
    """
    Comprehensive extraction of all tribal payoffs from a card.

    Combines all the extraction functions to give a complete picture.

    Args:
        card: Card dictionary

    Returns:
        {
            'has_tribal_payoff': bool,
            'chosen_type': Dict,  # From extract_cares_about_chosen_type
            'same_type': Dict,    # From extract_cares_about_same_type
            'tribal_lord': Dict,  # From extract_tribal_lords
            'tribal_trigger': Dict,  # From extract_tribal_triggers
            'is_changeling': bool
        }
    """
    chosen_type = extract_cares_about_chosen_type(card)
    same_type = extract_cares_about_same_type(card)
    tribal_lord = extract_tribal_lords(card)
    tribal_trigger = extract_tribal_triggers(card)
    is_changeling = extract_is_changeling(card)

    has_tribal_payoff = (
        chosen_type['cares_about_chosen_type'] or
        same_type['cares_about_same_type'] or
        tribal_lord['is_tribal_lord'] or
        tribal_trigger['has_tribal_trigger'] or
        is_changeling
    )

    return {
        'has_tribal_payoff': has_tribal_payoff,
        'chosen_type': chosen_type,
        'same_type': same_type,
        'tribal_lord': tribal_lord,
        'tribal_trigger': tribal_trigger,
        'is_changeling': is_changeling
    }


def get_creature_types(card: Dict) -> Set[str]:
    """
    Extract all creature types from a card.

    Args:
        card: Card dictionary

    Returns:
        Set of creature type strings
    """
    type_line = card.get('type_line', '')

    # Check if it's a creature
    if 'creature' not in type_line.lower():
        return set()

    # Check for changeling (has all creature types)
    if extract_is_changeling(card):
        return {'Changeling'}  # Special marker

    # Parse subtypes from type line
    if '—' in type_line:
        try:
            _, subtypes_str = type_line.split('—', 1)
            subtypes = {s.strip() for s in subtypes_str.split() if s.strip()}
            return subtypes
        except ValueError:
            return set()

    return set()
