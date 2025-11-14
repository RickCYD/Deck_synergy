"""
Core unified architecture components.

This package contains the foundational components of the unified architecture:
- card_parser: Single source of truth for parsing MTG card abilities
- trigger_registry: Central system for registering and executing triggers
- trigger_effects: Standard effect functions for common trigger patterns
"""

from src.core.card_parser import (
    UnifiedCardParser,
    CardAbilities,
    TriggerAbility,
    StaticAbility,
    ActivatedAbility,
)

from src.core.trigger_registry import (
    TriggerRegistry,
    RegisteredTrigger,
    create_registry_from_deck,
    register_battlefield,
)

from src.core.trigger_effects import (
    create_effect_from_trigger,
    create_effect_from_static,
    # Rally effects
    create_rally_haste_effect,
    create_rally_vigilance_effect,
    create_rally_lifelink_effect,
    create_rally_double_strike_effect,
    create_rally_counter_effect,
    # Prowess effects
    create_prowess_effect,
    # Token effects
    create_token_effect,
    # Damage effects
    create_damage_effect,
    # Card advantage effects
    create_draw_effect,
    create_scry_effect,
    # Static effects
    create_anthem_effect,
)

__all__ = [
    # Parser
    'UnifiedCardParser',
    'CardAbilities',
    'TriggerAbility',
    'StaticAbility',
    'ActivatedAbility',
    # Registry
    'TriggerRegistry',
    'RegisteredTrigger',
    'create_registry_from_deck',
    'register_battlefield',
    # Effects
    'create_effect_from_trigger',
    'create_effect_from_static',
    'create_rally_haste_effect',
    'create_rally_vigilance_effect',
    'create_rally_lifelink_effect',
    'create_rally_double_strike_effect',
    'create_rally_counter_effect',
    'create_prowess_effect',
    'create_token_effect',
    'create_damage_effect',
    'create_draw_effect',
    'create_scry_effect',
    'create_anthem_effect',
]
