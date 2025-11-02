"""
Combat Modifier Extractors

Extracts combat-related mechanics from MTG cards:
- Pump effects (temporary power/toughness boosts)
- Evasion granters (give flying, unblockable, etc.)
- Attack triggers (effects when creatures attack)
- Combat damage triggers
- Mass pump effects
"""

import re
from typing import Dict, List, Optional


def extract_pump_effects(card: Dict) -> Dict:
    """
    Extract pump effects (temporary P/T boosts).

    Returns:
        {
            'has_pump': bool,
            'pump_type': str,  # 'targeted', 'self', 'mass', 'conditional'
            'power_boost': int,
            'toughness_boost': int,
            'duration': str,  # 'until_end_of_turn', 'permanent', 'until_end_of_combat'
            'activation_cost': Optional[str],
            'additional_effects': List[str],  # Keywords granted
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_pump': False,
        'pump_type': None,
        'power_boost': 0,
        'toughness_boost': 0,
        'duration': None,
        'activation_cost': None,
        'additional_effects': [],
        'examples': []
    }

    if not text:
        return result

    # Pump effect patterns
    # "{1}{W}: Target creature gets +1/+1 until end of turn"
    # "Attacking creatures get +2/+0"
    # "Creatures you control get +1/+1"
    pump_patterns = [
        r'(target\s+creature|creatures?\s+you\s+control|attacking\s+creatures?|.*creature.*)\s+(?:gets?|get)\s+([+\-]\d+)/([+\-]\d+)',
        r'\{.*\}:\s*(target\s+creature|.*creature.*)\s+(?:gets?|get)\s+([+\-]\d+)/([+\-]\d+)',
    ]

    for pattern in pump_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_pump'] = True
            result['examples'].append(match.group(0))

            # Parse target type
            groups = match.groups()
            target = groups[0] if groups else ''

            if 'target creature' in target:
                result['pump_type'] = 'targeted'
            elif 'creatures you control' in target or 'each creature you control' in target:
                result['pump_type'] = 'mass'
            elif 'attacking' in target:
                result['pump_type'] = 'attacking'
            else:
                result['pump_type'] = 'self'

            # Parse boost amounts - get last two groups
            power_str = groups[-2] if len(groups) >= 2 else '+0'
            toughness_str = groups[-1] if len(groups) >= 1 else '+0'

            try:
                result['power_boost'] = int(power_str)
                result['toughness_boost'] = int(toughness_str)
            except (ValueError, IndexError):
                pass

            # Check for activation cost
            cost_match = re.search(r'(\{.*?\}):', text)
            if cost_match:
                result['activation_cost'] = cost_match.group(1)

            break

    if not result['has_pump']:
        return result

    # Determine duration
    if 'until end of turn' in text:
        result['duration'] = 'until_end_of_turn'
    elif 'until end of combat' in text:
        result['duration'] = 'until_end_of_combat'
    elif result['activation_cost'] or 'gets' in text:
        result['duration'] = 'until_end_of_turn'  # Default for activated/spell pumps
    else:
        result['duration'] = 'permanent'  # Static buff

    # Check for additional keyword grants
    keyword_patterns = [
        (r'gains?\s+flying', 'flying'),
        (r'gains?\s+trample', 'trample'),
        (r'gains?\s+vigilance', 'vigilance'),
        (r'gains?\s+lifelink', 'lifelink'),
        (r'gains?\s+first\s+strike', 'first strike'),
        (r'gains?\s+double\s+strike', 'double strike'),
        (r'gains?\s+haste', 'haste'),
        (r'gains?\s+deathtouch', 'deathtouch'),
        (r'gains?\s+menace', 'menace'),
    ]

    for pattern, keyword in keyword_patterns:
        if re.search(pattern, text):
            result['additional_effects'].append(keyword)

    return result


def extract_evasion_granters(card: Dict) -> Dict:
    """
    Extract evasion granting effects.

    Returns:
        {
            'grants_evasion': bool,
            'evasion_types': List[str],  # 'flying', 'unblockable', 'menace', 'shadow', etc.
            'target_type': str,  # 'targeted', 'self', 'all_creatures', 'attacking'
            'is_permanent': bool,
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'grants_evasion': False,
        'evasion_types': [],
        'target_type': None,
        'is_permanent': False,
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Evasion keywords and their patterns
    evasion_patterns = [
        (r'(?:gains?|have?|has)\s+flying', 'flying'),
        (r"can't\s+be\s+blocked", 'unblockable'),
        (r'unblockable', 'unblockable'),
        (r'(?:gains?|have?|has)\s+menace', 'menace'),
        (r'(?:gains?|have?|has)\s+shadow', 'shadow'),
        (r'(?:gains?|have?|has)\s+horsemanship', 'horsemanship'),
        (r'(?:gains?|have?|has)\s+fear', 'fear'),
        (r'(?:gains?|have?|has)\s+intimidate', 'intimidate'),
        (r'blocked\s+only\s+by', 'conditional_block'),
    ]

    for pattern, evasion_type in evasion_patterns:
        if re.search(pattern, text):
            result['grants_evasion'] = True
            result['evasion_types'].append(evasion_type)

    if not result['grants_evasion']:
        return result

    # Determine target type
    if 'target creature' in text:
        result['target_type'] = 'targeted'
    elif 'creatures you control' in text or 'each creature you control' in text:
        result['target_type'] = 'all_creatures'
    elif 'attacking' in text:
        result['target_type'] = 'attacking'
    else:
        result['target_type'] = 'self'

    # Check if permanent or temporary
    if 'until end of turn' in text or 'until end of combat' in text:
        result['is_permanent'] = False
    else:
        result['is_permanent'] = True

    # Check for conditions
    condition_patterns = [
        (r'as\s+long\s+as', 'conditional'),
        (r'during\s+(?:your|combat)', 'phase_limited'),
        (r'if\s+you\s+control', 'control_condition'),
    ]

    for pattern, condition in condition_patterns:
        if re.search(pattern, text):
            result['conditions'].append(condition)

    # Find example text
    for pattern, _ in evasion_patterns:
        match = re.search(pattern, text)
        if match:
            result['examples'].append(match.group(0))

    return result


def extract_attack_triggers(card: Dict) -> Dict:
    """
    Extract attack trigger effects.

    Returns:
        {
            'has_attack_trigger': bool,
            'trigger_condition': str,  # 'self_attacks', 'creature_attacks', 'any_attack'
            'trigger_effects': List[str],  # 'damage', 'draw', 'token', 'pump', 'scry'
            'triggers_per_combat': str,  # 'once', 'per_creature', 'unlimited'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_attack_trigger': False,
        'trigger_condition': None,
        'trigger_effects': [],
        'triggers_per_combat': 'unlimited',
        'examples': []
    }

    if not text:
        return result

    # Attack trigger patterns
    trigger_patterns = [
        (r'whenever\s+.*\s+attacks', 'attacks'),
        (r'whenever.*attacks', 'attacks'),
        (r'when.*attacks', 'attacks'),
    ]

    for pattern, trigger_type in trigger_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_attack_trigger'] = True
            result['examples'].append(match.group(0))

            # Determine what triggers
            trigger_text = match.group(0)
            if 'this creature attacks' in trigger_text or re.search(r'when\s+\w+\s+attacks', text):
                result['trigger_condition'] = 'self_attacks'
            elif 'creature you control attacks' in trigger_text or 'a creature you control attacks' in trigger_text:
                result['trigger_condition'] = 'creature_attacks'
            elif 'one or more creatures you control attack' in trigger_text:
                result['trigger_condition'] = 'any_attack'
                result['triggers_per_combat'] = 'once'
            else:
                result['trigger_condition'] = 'self_attacks'

            break

    if not result['has_attack_trigger']:
        return result

    # Determine trigger effects
    effect_patterns = [
        (r'deals?\s+\d+\s+damage', 'damage'),
        (r'draws?\s+(?:a\s+)?cards?', 'draw'),
        (r'creates?\s+.*tokens?', 'token'),
        (r'(?:gets?|get)\s+\+\d+/\+\d+', 'pump'),
        (r'scrys?\s+\d+', 'scry'),
        (r'(?:put|gets?)\s+(?:a\s+)?\+1/\+1\s+counter', 'counter'),
        (r'gains?\s+(?:a\s+)?life', 'life'),
    ]

    for pattern, effect in effect_patterns:
        if re.search(pattern, text):
            result['trigger_effects'].append(effect)

    return result


def extract_combat_damage_triggers(card: Dict) -> Dict:
    """
    Extract combat damage trigger effects.

    Returns:
        {
            'has_damage_trigger': bool,
            'trigger_source': str,  # 'self', 'any_creature', 'specific_type'
            'damage_target': str,  # 'player', 'any', 'creature'
            'trigger_effects': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_damage_trigger': False,
        'trigger_source': None,
        'damage_target': None,
        'trigger_effects': [],
        'examples': []
    }

    if not text:
        return result

    # Combat damage trigger patterns
    damage_patterns = [
        r'whenever.*deals?\s+combat\s+damage',
        r'when.*deals?\s+combat\s+damage',
    ]

    for pattern in damage_patterns:
        match = re.search(pattern, text)
        if match:
            result['has_damage_trigger'] = True
            result['examples'].append(match.group(0))

            trigger_text = match.group(0)

            # Determine source
            if 'this creature deals' in trigger_text or re.search(r'when\s+\w+\s+deals', text):
                result['trigger_source'] = 'self'
            elif 'a creature you control deals' in trigger_text or 'creature you control deals' in trigger_text:
                result['trigger_source'] = 'any_creature'
            else:
                result['trigger_source'] = 'self'

            # Determine target
            if 'to a player' in trigger_text or 'to an opponent' in trigger_text:
                result['damage_target'] = 'player'
            elif 'to a creature' in trigger_text:
                result['damage_target'] = 'creature'
            else:
                result['damage_target'] = 'any'

            break

    if not result['has_damage_trigger']:
        return result

    # Determine trigger effects
    effect_patterns = [
        (r'draws?\s+(?:a\s+)?cards?', 'draw'),
        (r'creates?\s+.*tokens?', 'token'),
        (r'(?:put|gets?)\s+(?:a\s+)?\+1/\+1\s+counter', 'counter'),
        (r'gains?\s+(?:a\s+)?life', 'life'),
        (r'exile.*card', 'exile'),
        (r'search\s+your\s+library', 'tutor'),
    ]

    for pattern, effect in effect_patterns:
        if re.search(pattern, text):
            result['trigger_effects'].append(effect)

    return result


def extract_mass_pump(card: Dict) -> Dict:
    """
    Extract mass pump effects (affects multiple creatures).

    Returns:
        {
            'is_mass_pump': bool,
            'affected_creatures': str,  # 'all_yours', 'all_attacking', 'specific_type'
            'power_bonus': int,
            'toughness_bonus': int,
            'duration': str,
            'keywords_granted': List[str],
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_mass_pump': False,
        'affected_creatures': None,
        'power_bonus': 0,
        'toughness_bonus': 0,
        'duration': None,
        'keywords_granted': [],
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Mass pump patterns
    # "Creatures you control get +2/+2 until end of turn"
    # "Attacking creatures get +1/+0"
    mass_patterns = [
        r'(creatures?\s+you\s+control|attacking\s+creatures?|.*creatures?)\s+(?:gets?|get)\s+([+\-]\d+)/([+\-]\d+)',
    ]

    for pattern in mass_patterns:
        match = re.search(pattern, text)
        if match:
            target = match.group(1)

            # Only count as "mass" if it affects multiple creatures
            if 'target creature' in target:
                continue  # This is single-target, not mass

            result['is_mass_pump'] = True
            result['examples'].append(match.group(0))

            # Determine affected creatures
            if 'creatures you control' in target:
                result['affected_creatures'] = 'all_yours'
            elif 'attacking creatures' in target:
                result['affected_creatures'] = 'all_attacking'
            elif 'creature you control' in target:  # "Each creature you control"
                result['affected_creatures'] = 'all_yours'
            else:
                result['affected_creatures'] = 'specific_type'

            # Parse boost
            try:
                result['power_bonus'] = int(match.group(2))
                result['toughness_bonus'] = int(match.group(3))
            except (ValueError, IndexError):
                pass

            break

    if not result['is_mass_pump']:
        return result

    # Determine duration
    if 'until end of turn' in text:
        result['duration'] = 'until_end_of_turn'
    elif 'until end of combat' in text:
        result['duration'] = 'until_end_of_combat'
    else:
        result['duration'] = 'permanent'

    # Check for keyword grants
    keyword_patterns = [
        (r'gains?\s+flying', 'flying'),
        (r'gains?\s+trample', 'trample'),
        (r'gains?\s+vigilance', 'vigilance'),
        (r'gains?\s+lifelink', 'lifelink'),
        (r'gains?\s+first\s+strike', 'first strike'),
        (r'gains?\s+haste', 'haste'),
    ]

    for pattern, keyword in keyword_patterns:
        if re.search(pattern, text):
            result['keywords_granted'].append(keyword)

    # Check for conditions
    if 'during combat' in text or 'during your turn' in text:
        result['conditions'].append('phase_limited')
    if 'as long as' in text:
        result['conditions'].append('conditional')

    return result


def classify_combat_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all combat mechanics.

    Returns a comprehensive dictionary with all combat information.
    """
    return {
        'pump_effects': extract_pump_effects(card),
        'evasion_granters': extract_evasion_granters(card),
        'attack_triggers': extract_attack_triggers(card),
        'combat_damage_triggers': extract_combat_damage_triggers(card),
        'mass_pump': extract_mass_pump(card)
    }
