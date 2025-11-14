#!/usr/bin/env python3
"""
Standard trigger effect functions for the unified architecture.

This module provides reusable effect functions that can be created from
parsed trigger data and executed by the BoardState during simulation.

Effect functions follow the pattern:
    effect_func(board_state, source_card, **kwargs) -> None

Effect creation functions follow the pattern:
    create_xxx_effect(trigger_data) -> Callable
"""

from typing import Callable, Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# RALLY EFFECT CREATORS
# =============================================================================

def create_rally_haste_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that grants haste to all creatures until end of turn.

    Used by: Chasm Guide, etc.
    """
    def effect(board_state, source_card, **kwargs):
        """Grant haste to all creatures until EOT."""
        logger.debug(f"{source_card.get('name', 'Unknown')} rally: granting haste")

        # When BoardState methods are available (Part 3), this will call:
        # board_state.grant_keyword_until_eot('haste', targets='all_creatures')

        # For now, we'll prepare the data structure
        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'grant_keyword',
            'keyword': 'haste',
            'targets': 'all_creatures',
            'duration': 'eot',
            'source': source_card.get('name', 'Unknown')
        })

    return effect


def create_rally_vigilance_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that grants vigilance to all creatures until end of turn.

    Used by: Makindi Patrol, etc.
    """
    def effect(board_state, source_card, **kwargs):
        """Grant vigilance to all creatures until EOT."""
        logger.debug(f"{source_card.get('name', 'Unknown')} rally: granting vigilance")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'grant_keyword',
            'keyword': 'vigilance',
            'targets': 'all_creatures',
            'duration': 'eot',
            'source': source_card.get('name', 'Unknown')
        })

    return effect


def create_rally_lifelink_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that grants lifelink to all creatures until end of turn.

    Used by: Lantern Scout, etc.
    """
    def effect(board_state, source_card, **kwargs):
        """Grant lifelink to all creatures until EOT."""
        logger.debug(f"{source_card.get('name', 'Unknown')} rally: granting lifelink")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'grant_keyword',
            'keyword': 'lifelink',
            'targets': 'all_creatures',
            'duration': 'eot',
            'source': source_card.get('name', 'Unknown')
        })

    return effect


def create_rally_double_strike_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that grants double strike to all creatures until end of turn.

    Used by: Resolute Blademaster, etc.
    """
    def effect(board_state, source_card, **kwargs):
        """Grant double strike to all creatures until EOT."""
        logger.debug(f"{source_card.get('name', 'Unknown')} rally: granting double strike")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'grant_keyword',
            'keyword': 'double strike',
            'targets': 'all_creatures',
            'duration': 'eot',
            'source': source_card.get('name', 'Unknown')
        })

    return effect


def create_rally_counter_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that puts +1/+1 counters on creatures.

    Used by: Oran-Rief Survivalist, Tajuru Warcaller, etc.
    """
    value = trigger_data.get('value', 1.0)
    targets = trigger_data.get('targets', ['all_creatures'])

    def effect(board_state, source_card, **kwargs):
        """Put +1/+1 counters on target creatures."""
        logger.debug(f"{source_card.get('name', 'Unknown')} rally: adding counters")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'add_counters',
            'counter_type': '+1/+1',
            'amount': int(value),
            'targets': targets,
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# PROWESS EFFECT CREATORS
# =============================================================================

def create_prowess_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that buffs a creature +1/+1 until end of turn.

    Used by: All prowess creatures
    """
    value = trigger_data.get('value', 1.0)

    def effect(board_state, source_card, **kwargs):
        """Buff this creature +1/+1 until EOT."""
        logger.debug(f"{source_card.get('name', 'Unknown')} prowess: +{int(value)}/+{int(value)}")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'buff_creature',
            'power': int(value),
            'toughness': int(value),
            'targets': 'self',
            'duration': 'eot',
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# TOKEN CREATION EFFECT CREATORS
# =============================================================================

def create_token_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that creates token(s).

    Used by: Kykar, Gideon, Dragon Fodder, etc.
    """
    token_count = trigger_data.get('value', 1.0)
    token_type = trigger_data.get('metadata', {}).get('token_type', 'creature')
    token_power = trigger_data.get('metadata', {}).get('power', 1)
    token_toughness = trigger_data.get('metadata', {}).get('toughness', 1)
    token_types = trigger_data.get('metadata', {}).get('types', [])

    def effect(board_state, source_card, **kwargs):
        """Create token(s)."""
        logger.debug(f"{source_card.get('name', 'Unknown')}: creating {int(token_count)} token(s)")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'create_tokens',
            'count': int(token_count),
            'token_type': token_type,
            'power': token_power,
            'toughness': token_toughness,
            'types': token_types,
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# DAMAGE EFFECT CREATORS
# =============================================================================

def create_damage_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that deals damage.

    Used by: Impact Tremors, Lightning Bolt, etc.
    """
    damage = trigger_data.get('value', 1.0)
    targets = trigger_data.get('targets', ['opponent'])

    def effect(board_state, source_card, **kwargs):
        """Deal damage to target(s)."""
        logger.debug(f"{source_card.get('name', 'Unknown')}: dealing {int(damage)} damage")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'deal_damage',
            'amount': int(damage),
            'targets': targets,
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# CARD DRAW EFFECT CREATORS
# =============================================================================

def create_draw_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that draws card(s).

    Used by: Mentor of the Meek, Brainstorm, etc.
    """
    draw_count = trigger_data.get('value', 1.0)

    def effect(board_state, source_card, **kwargs):
        """Draw card(s)."""
        logger.debug(f"{source_card.get('name', 'Unknown')}: drawing {int(draw_count)} card(s)")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'draw_cards',
            'count': int(draw_count),
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# SCRY EFFECT CREATORS
# =============================================================================

def create_scry_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect that scrys.

    Used by: Monastery Swiftspear with scry triggers, etc.
    """
    scry_count = trigger_data.get('value', 1.0)

    def effect(board_state, source_card, **kwargs):
        """Scry N."""
        logger.debug(f"{source_card.get('name', 'Unknown')}: scry {int(scry_count)}")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        board_state.pending_effects.append({
            'type': 'scry',
            'count': int(scry_count),
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# ANTHEM EFFECT CREATORS (Static Abilities)
# =============================================================================

def create_anthem_effect(static_data: Dict[str, Any]) -> Callable:
    """
    Create static anthem effect (+X/+X to creatures).

    Used by: Thalia's Lieutenant, Shared Animosity, etc.
    """
    power = static_data.get('metadata', {}).get('power', 1)
    toughness = static_data.get('metadata', {}).get('toughness', 1)
    targets = static_data.get('targets', ['all_creatures'])

    def effect(board_state, source_card, **kwargs):
        """Apply static anthem buff."""
        logger.debug(f"{source_card.get('name', 'Unknown')}: anthem +{power}/+{toughness}")

        if not hasattr(board_state, 'static_effects'):
            board_state.static_effects = []

        board_state.static_effects.append({
            'type': 'anthem',
            'power': power,
            'toughness': toughness,
            'targets': targets,
            'source': source_card.get('name', 'Unknown')
        })

    return effect


# =============================================================================
# EFFECT FACTORY
# =============================================================================

EFFECT_TYPE_CREATORS = {
    # Rally effects
    'rally_haste': create_rally_haste_effect,
    'rally_vigilance': create_rally_vigilance_effect,
    'rally_lifelink': create_rally_lifelink_effect,
    'rally_double_strike': create_rally_double_strike_effect,
    'rally_counters': create_rally_counter_effect,

    # Prowess effects
    'prowess': create_prowess_effect,
    'buff': create_prowess_effect,  # Alias
    'generic': create_prowess_effect,  # For generic buff effects

    # Token effects
    'tokens': create_token_effect,
    'create_tokens': create_token_effect,  # Alias

    # Damage effects
    'damage': create_damage_effect,
    'deal_damage': create_damage_effect,  # Alias

    # Card advantage effects
    'draw': create_draw_effect,
    'scry': create_scry_effect,

    # Static effects
    'anthem': create_anthem_effect,
    'keyword_grant': create_anthem_effect,  # Keyword grants are like anthems
}


def create_effect_from_trigger(trigger) -> Optional[Callable]:
    """
    Create an executable effect function from a TriggerAbility.

    Args:
        trigger: TriggerAbility instance from unified parser

    Returns:
        Callable effect function, or None if effect type not recognized
    """
    effect_type = trigger.effect_type

    # Handle special cases for rally
    if trigger.event == 'rally':
        effect = trigger.effect.lower()
        if 'haste' in effect:
            effect_type = 'rally_haste'
        elif 'vigilance' in effect:
            effect_type = 'rally_vigilance'
        elif 'lifelink' in effect:
            effect_type = 'rally_lifelink'
        elif 'double strike' in effect or 'doublestrike' in effect:
            effect_type = 'rally_double_strike'
        elif 'counter' in effect or '+1/+1' in effect:
            effect_type = 'rally_counters'

    # Get creator function
    creator = EFFECT_TYPE_CREATORS.get(effect_type)
    if not creator:
        logger.warning(f"Unknown effect type: {effect_type}")
        return None

    # Create effect with trigger data
    trigger_data = {
        'event': trigger.event,
        'effect': trigger.effect,
        'effect_type': trigger.effect_type,
        'value': trigger.value,
        'targets': trigger.targets,
        'metadata': trigger.metadata,
        'condition': trigger.condition,
    }

    return creator(trigger_data)


def create_effect_from_static(static_ability) -> Optional[Callable]:
    """
    Create an executable effect function from a StaticAbility.

    Args:
        static_ability: StaticAbility instance from unified parser

    Returns:
        Callable effect function, or None if ability type not recognized
    """
    ability_type = static_ability.ability_type

    # Handle keyword_grant as anthem-type effect
    if ability_type == 'keyword_grant':
        ability_type = 'anthem'

    creator = EFFECT_TYPE_CREATORS.get(ability_type)
    if not creator:
        logger.warning(f"Unknown static ability type: {ability_type}")
        return None

    static_data = {
        'ability_type': static_ability.ability_type,
        'effect': static_ability.effect,
        'targets': static_ability.targets,
        'metadata': {
            'power': int(static_ability.value),
            'toughness': int(static_ability.value),
            'conditions': static_ability.conditions,
        }
    }

    return creator(static_data)
