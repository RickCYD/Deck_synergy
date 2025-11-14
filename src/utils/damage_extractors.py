

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

"""
Damage & Life Drain Extractors
Extract and classify damage, burn, drain, and life gain effects from card text.
"""

import re
from typing import Dict, List, Optional


def extract_direct_damage(card: Dict) -> List[Dict]:
    """
    Extract direct damage effects (single target).

    Types:
    - Deals X damage to any target
    - Deals X damage to target creature
    - Deals X damage to target player/planeswalker
    - Deals X damage to target creature or player

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of direct damage dictionaries
    """
    damages = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return damages

    # Deals X damage to any target
    if re.search(r'deals? \d+ damage to any target', oracle_text):
        match = re.search(r'deals? (\d+) damage to any target', oracle_text)
        damages.append({
            'type': 'direct_damage',
            'subtype': 'any_target',
            'amount': int(match.group(1)),
            'target': 'any',
            'is_single_target': True,
            'description': f"Deals {match.group(1)} damage to any target"
        })

    # Deals X damage to target creature
    if re.search(r'deals? \d+ damage to target creature(?! or)', oracle_text):
        match = re.search(r'deals? (\d+) damage to target creature', oracle_text)
        damages.append({
            'type': 'direct_damage',
            'subtype': 'creature_only',
            'amount': int(match.group(1)),
            'target': 'creature',
            'is_single_target': True,
            'description': f"Deals {match.group(1)} damage to target creature"
        })

    # Deals X damage to target player or planeswalker
    if re.search(r'deals? \d+ damage to target (player|opponent)( or planeswalker)?', oracle_text):
        match = re.search(r'deals? (\d+) damage to target (player|opponent)', oracle_text)
        damages.append({
            'type': 'direct_damage',
            'subtype': 'player_or_planeswalker',
            'amount': int(match.group(1)),
            'target': 'player',
            'is_single_target': True,
            'description': f"Deals {match.group(1)} damage to target player"
        })

    # Deals X damage to target creature or player
    if re.search(r'deals? \d+ damage to target creature or player', oracle_text):
        match = re.search(r'deals? (\d+) damage to target creature or player', oracle_text)
        damages.append({
            'type': 'direct_damage',
            'subtype': 'creature_or_player',
            'amount': int(match.group(1)),
            'target': 'creature_or_player',
            'is_single_target': True,
            'description': f"Deals {match.group(1)} damage to target creature or player"
        })

    # Variable damage (X damage)
    if re.search(r'deals? x damage', oracle_text):
        damages.append({
            'type': 'direct_damage',
            'subtype': 'variable',
            'amount': 'X',
            'target': 'varies',
            'is_single_target': True,
            'is_variable': True,
            'description': "Deals X damage (variable)"
        })

    return damages


def extract_burn_effects(card: Dict) -> List[Dict]:
    """
    Extract burn effects that hit multiple targets or all opponents.

    Types:
    - Deals X damage to each opponent
    - Deals X damage to each creature
    - Deals X damage to each player
    - Deals X damage to all creatures

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of burn effect dictionaries
    """
    burns = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return burns

    # Deals X damage to each opponent
    if re.search(r'deals? \d+ damage to each opponent', oracle_text):
        match = re.search(r'deals? (\d+) damage to each opponent', oracle_text)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'each_opponent',
            'amount': int(match.group(1)),
            'target': 'each_opponent',
            'is_multiplayer': True,
            'description': f"Deals {match.group(1)} damage to each opponent"
        })

    # Deals X damage to each creature
    if re.search(r'deals? \d+ damage to each creature', oracle_text):
        match = re.search(r'deals? (\d+) damage to each creature', oracle_text)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'each_creature',
            'amount': int(match.group(1)),
            'target': 'each_creature',
            'is_board_damage': True,
            'description': f"Deals {match.group(1)} damage to each creature"
        })

    # Deals X damage to each player (including variable X)
    if re.search(r'deals? (x|\d+) damage to each player', oracle_text):
        match = re.search(r'deals? (x|\d+) damage to each player', oracle_text)
        amount = match.group(1)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'each_player',
            'amount': int(amount) if amount.isdigit() else 'X',
            'target': 'each_player',
            'is_symmetrical': True,
            'is_variable': not amount.isdigit(),
            'description': f"Deals {amount.upper()} damage to each player"
        })

    # Deals X damage to that player (triggered)
    if re.search(r'deals? \d+ damage to that player', oracle_text):
        match = re.search(r'deals? (\d+) damage to that player', oracle_text)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'each_player',
            'amount': int(match.group(1)),
            'target': 'each_player',
            'is_symmetrical': True,
            'description': f"Deals {match.group(1)} damage to that player"
        })

    # Deals X damage to all creatures
    if re.search(r'deals? \d+ damage to all creatures', oracle_text):
        match = re.search(r'deals? (\d+) damage to all creatures', oracle_text)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'all_creatures',
            'amount': int(match.group(1)),
            'target': 'all_creatures',
            'is_board_damage': True,
            'description': f"Deals {match.group(1)} damage to all creatures"
        })

    # Deals X damage divided
    if re.search(r'deals? \d+ damage divided', oracle_text):
        match = re.search(r'deals? (\d+) damage divided', oracle_text)
        burns.append({
            'type': 'burn_effect',
            'subtype': 'divided',
            'amount': int(match.group(1)),
            'target': 'multiple',
            'is_divided': True,
            'description': f"Deals {match.group(1)} damage divided among targets"
        })

    return burns


def extract_drain_effects(card: Dict) -> List[Dict]:
    """
    Extract life drain effects (damage + life gain).

    Types:
    - Target player loses X life, you gain X life
    - Each opponent loses X life, you gain X life
    - Drain X (shorthand)

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of drain effect dictionaries
    """
    drains = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return drains

    # Target opponent loses X life, you gain X life
    if re.search(r'target (opponent|player) loses \d+ life.*you gain', oracle_text):
        match = re.search(r'target (opponent|player) loses (\d+) life', oracle_text)
        drains.append({
            'type': 'drain_effect',
            'subtype': 'single_target',
            'amount': int(match.group(2)),
            'target': 'single_opponent',
            'is_single_target': True,
            'gains_life': True,
            'description': f"Target opponent loses {match.group(2)} life, you gain that much"
        })

    # Each opponent loses X life, you gain X life (or that much life) - including variable X
    if re.search(r'each opponent loses (x|\d+) life', oracle_text):
        match = re.search(r'each opponent loses (x|\d+) life', oracle_text)
        amount = match.group(1)
        gains_life = 'you gain' in oracle_text or 'gain that much' in oracle_text or 'gain life equal' in oracle_text
        drains.append({
            'type': 'drain_effect',
            'subtype': 'each_opponent',
            'amount': int(amount) if amount.isdigit() else 'X',
            'target': 'each_opponent',
            'is_multiplayer': True,
            'is_variable': not amount.isdigit(),
            'gains_life': gains_life,
            'description': f"Each opponent loses {amount.upper()} life" +
                          (", you gain that much" if gains_life else "")
        })

    # Each opponent loses X life for each [something]
    if re.search(r'each opponent loses \d+ life for each', oracle_text):
        match = re.search(r'each opponent loses (\d+) life for each', oracle_text)
        drains.append({
            'type': 'drain_effect',
            'subtype': 'each_opponent_scaling',
            'amount': int(match.group(1)),
            'target': 'each_opponent',
            'is_multiplayer': True,
            'is_scaling': True,
            'gains_life': 'you gain' in oracle_text,
            'description': f"Each opponent loses {match.group(1)} life for each [condition]"
        })

    # Drain X (keyword)
    if re.search(r'\bdrain \d+\b', oracle_text):
        match = re.search(r'drain (\d+)', oracle_text)
        drains.append({
            'type': 'drain_effect',
            'subtype': 'keyword_drain',
            'amount': int(match.group(1)),
            'target': 'defending_player',
            'is_keyword': True,
            'gains_life': True,
            'description': f"Drain {match.group(1)} (opponent loses, you gain)"
        })

    # Each player loses X life (symmetrical)
    if re.search(r'each player loses \d+ life', oracle_text):
        match = re.search(r'each player loses (\d+) life', oracle_text)
        drains.append({
            'type': 'drain_effect',
            'subtype': 'each_player',
            'amount': int(match.group(1)),
            'target': 'each_player',
            'is_symmetrical': True,
            'gains_life': False,
            'description': f"Each player loses {match.group(1)} life"
        })

    return drains


def extract_life_gain(card: Dict) -> List[Dict]:
    """
    Extract life gain effects.

    Types:
    - You gain X life
    - You gain X life for each [something]
    - Whenever [trigger], you gain X life

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of life gain dictionaries
    """
    gains = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return gains

    # You gain X life for each [something] (check this FIRST)
    if re.search(r'(you gain|gains?) \d+ life for each', oracle_text):
        match = re.search(r'(?:you gain|gains?) (\d+) life for each', oracle_text)
        gains.append({
            'type': 'life_gain',
            'subtype': 'scaling',
            'amount': int(match.group(1)),
            'is_scaling': True,
            'description': f"You gain {match.group(1)} life for each [condition]"
        })

    # You gain X life (simple) - check after "for each" pattern
    elif re.search(r'you gain \d+ life', oracle_text):
        match = re.search(r'you gain (\d+) life', oracle_text)
        is_triggered = 'whenever' in oracle_text or 'when' in oracle_text
        gains.append({
            'type': 'life_gain',
            'subtype': 'static',
            'amount': int(match.group(1)),
            'is_triggered': is_triggered,
            'is_repeatable': is_triggered,
            'description': f"You gain {match.group(1)} life"
        })

    # Whenever [trigger], you gain X life
    if re.search(r'whenever.*you gain \d+ life', oracle_text):
        match = re.search(r'you gain (\d+) life', oracle_text)
        gains.append({
            'type': 'life_gain',
            'subtype': 'triggered',
            'amount': int(match.group(1)),
            'is_triggered': True,
            'is_repeatable': True,
            'description': f"Triggered ability: gain {match.group(1)} life"
        })

    # Gain X life equal to [something] (more specific patterns)
    if re.search(r'gain(s?) life equal to', oracle_text):
        gains.append({
            'type': 'life_gain',
            'subtype': 'variable',
            'amount': 'variable',
            'is_variable': True,
            'description': "Gain life equal to [something]"
        })

    # Target player gains X life (or controller gains)
    if re.search(r'(target player|its controller) gains \d+ life', oracle_text):
        match = re.search(r'(?:target player|its controller) gains (\d+) life', oracle_text)
        gains.append({
            'type': 'life_gain',
            'subtype': 'static',
            'amount': int(match.group(1)),
            'is_triggered': False,
            'is_repeatable': False,
            'description': f"Target player gains {match.group(1)} life"
        })

    # Each player gains X life (symmetrical)
    if re.search(r'each player gains \d+ life', oracle_text):
        match = re.search(r'each player gains (\d+) life', oracle_text)
        gains.append({
            'type': 'life_gain',
            'subtype': 'symmetrical',
            'amount': int(match.group(1)),
            'is_symmetrical': True,
            'description': f"Each player gains {match.group(1)} life"
        })

    return gains


def extract_creature_damage(card: Dict) -> List[Dict]:
    """
    Extract damage dealt by creature's power or when creatures deal damage.

    Types:
    - Deals damage equal to its power
    - Whenever a creature you control deals damage
    - Combat damage triggers

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of creature damage dictionaries
    """
    damages = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return damages

    # Deals damage equal to its power or number of cards
    if re.search(r'deals? damage equal to (its|their|the (number|amount))', oracle_text):
        damages.append({
            'type': 'creature_damage',
            'subtype': 'power_based',
            'amount': 'power',
            'is_variable': True,
            'description': "Deals damage equal to creature's power or variable amount"
        })

    # Whenever a creature you control deals damage (general)
    if re.search(r'whenever.*creature.*deals? (combat )?damage', oracle_text):
        damages.append({
            'type': 'creature_damage',
            'subtype': 'damage_trigger',
            'is_triggered': True,
            'is_repeatable': True,
            'description': "Triggers when creatures deal damage"
        })

    # Whenever this creature/equipped creature deals combat damage
    if re.search(r'whenever.*(this|equipped creature).*deals? combat damage', oracle_text):
        damages.append({
            'type': 'creature_damage',
            'subtype': 'combat_damage_trigger',
            'is_triggered': True,
            'is_combat': True,
            'is_repeatable': True,
            'description': "Triggers on combat damage"
        })

    # Whenever you draw a card, deal damage
    if re.search(r'whenever you draw.*deals? \d+ damage', oracle_text):
        match = re.search(r'deals? (\d+) damage', oracle_text)
        damages.append({
            'type': 'creature_damage',
            'subtype': 'draw_trigger',
            'amount': int(match.group(1)) if match else 'variable',
            'is_triggered': True,
            'is_repeatable': True,
            'description': "Triggers on card draw to deal damage"
        })

    return damages


def classify_damage_effect(card: Dict) -> Dict:
    """
    Comprehensive classification of all damage and life effects.

    Args:
        card: Card dictionary with oracle_text

    Returns:
        Dictionary with complete damage/life classification
    """
    direct_damages = extract_direct_damage(card)
    burn_effects = extract_burn_effects(card)
    drain_effects = extract_drain_effects(card)
    life_gains = extract_life_gain(card)
    creature_damages = extract_creature_damage(card)

    # Determine overall strategy
    strategy = 'none'
    if drain_effects:
        strategy = 'drain'
    elif burn_effects and any(b.get('is_multiplayer') for b in burn_effects):
        strategy = 'burn'
    elif direct_damages and len(direct_damages) > 1:
        strategy = 'burn'
    elif life_gains and any(g.get('is_repeatable') for g in life_gains):
        strategy = 'lifegain'

    # Calculate total potential damage
    total_damage = 0
    for effect in direct_damages + burn_effects:
        if isinstance(effect.get('amount'), int):
            total_damage += effect['amount']

    # Check for synergy keywords
    oracle_text = card.get('oracle_text', '').lower()
    has_lifelink = 'lifelink' in oracle_text or 'lifelink' in card.get('keywords', [])

    return {
        'card_name': card.get('name', 'Unknown'),
        'has_damage_effects': len(direct_damages + burn_effects + drain_effects + creature_damages) > 0,
        'has_life_gain': len(life_gains) > 0,
        'direct_damages': direct_damages,
        'burn_effects': burn_effects,
        'drain_effects': drain_effects,
        'life_gains': life_gains,
        'creature_damages': creature_damages,
        'total_effects': (len(direct_damages) + len(burn_effects) +
                         len(drain_effects) + len(life_gains) + len(creature_damages)),
        'strategy': strategy,
        'estimated_damage': total_damage,
        'has_lifelink': has_lifelink,
        'is_multiplayer_focused': any(
            e.get('is_multiplayer', False)
            for e in (burn_effects + drain_effects)
        )
    }
