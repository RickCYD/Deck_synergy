"""
Unified Architecture Integration for Simulation

This module integrates the unified architecture (Parts 1-2) with the
existing game simulation system.

Key responsibilities:
- Initialize trigger registry for a deck
- Register cards when they enter the battlefield
- Trigger events at appropriate game phases
- Clean up at end of turn

Usage:
    from Simulation.unified_integration import initialize_unified_system, handle_card_etb

    # At game start
    initialize_unified_system(board_state, deck)

    # When casting a creature
    handle_card_etb(board_state, creature_card)

    # When casting a noncreature spell
    handle_spell_cast(board_state, spell_card)

    # At end of turn
    handle_end_of_turn(board_state)
"""

from typing import List, Dict, Any
import logging

# Import unified architecture components
from src.core.card_parser import UnifiedCardParser
from src.core.trigger_registry import TriggerRegistry
from Simulation.boardstate_extensions import enhance_boardstate

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM INITIALIZATION
# =============================================================================

def initialize_unified_system(board_state, deck: List[Any]):
    """
    Initialize the unified architecture for a game simulation.

    This sets up:
    - Unified card parser
    - Trigger registry
    - BoardState enhancements
    - Card ID tracking

    Args:
        board_state: BoardState instance
        deck: List of Card objects in the deck

    Returns:
        Tuple of (parser, registry)
    """
    logger.info("Initializing unified architecture for simulation")

    # Enhance the board state with new methods
    enhance_boardstate(board_state)

    # Create parser and registry
    parser = UnifiedCardParser()
    registry = TriggerRegistry()

    # Attach registry to board state
    board_state.trigger_registry = registry
    board_state.unified_parser = parser

    # Initialize card ID tracking
    board_state.card_id_map = {}  # Maps Card object id -> registry card_id

    logger.info("Unified architecture initialized")
    return parser, registry


# =============================================================================
# EVENT HANDLERS
# =============================================================================

def handle_card_etb(board_state, card, card_dict: Dict[str, Any] = None):
    """
    Handle a card entering the battlefield.

    This:
    1. Registers the card's triggers with the registry
    2. Triggers 'etb' event
    3. Triggers 'rally' event if card is an Ally

    Args:
        board_state: BoardState instance
        card: Card object that entered
        card_dict: Optional raw card data dict (for parsing)
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        return

    # Get raw card data for parsing
    if card_dict is None:
        card_dict = _card_to_dict(card)

    # Parse abilities
    abilities = board_state.unified_parser.parse_card(card_dict)

    # Register card's triggers
    if abilities.triggers or abilities.static_abilities:
        registry_id = board_state.trigger_registry.register_card(card_dict, abilities)
        board_state.card_id_map[id(card)] = registry_id
        logger.debug(f"Registered {card.name} with {len(abilities.triggers)} trigger(s)")

    # Trigger ETB event
    event_data = {
        'card': card_dict,
        'source_card': card_dict,
    }
    board_state.trigger_event('etb', event_data)

    # If it's an Ally, also trigger rally
    if 'Ally' in card.type:
        board_state.trigger_event('rally', event_data)
        logger.debug(f"Rally triggered by {card.name}")


def handle_spell_cast(board_state, spell_card, spell_dict: Dict[str, Any] = None):
    """
    Handle a spell being cast.

    This triggers:
    - 'cast_spell' event (for all spells)
    - 'cast_noncreature_spell' event (for prowess, spellslinger)
    - 'cast_instant_sorcery' event (for magecraft)

    Args:
        board_state: BoardState instance
        spell_card: Card object being cast
        spell_dict: Optional raw card data dict
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        return

    if spell_dict is None:
        spell_dict = _card_to_dict(spell_card)

    event_data = {
        'card': spell_dict,
        'source_card': spell_dict,
    }

    # Always trigger cast_spell
    board_state.trigger_event('cast_spell', event_data)

    type_line = spell_card.type.lower()

    # Trigger noncreature spell event (prowess)
    if 'creature' not in type_line:
        board_state.trigger_event('cast_noncreature_spell', event_data)
        logger.debug(f"Noncreature spell cast: {spell_card.name}")

    # Trigger instant/sorcery event (magecraft)
    if 'instant' in type_line or 'sorcery' in type_line:
        board_state.trigger_event('cast_instant_sorcery', event_data)
        board_state.trigger_event('cast_or_copy_instant_sorcery', event_data)
        logger.debug(f"Instant/sorcery cast: {spell_card.name}")


def handle_creature_attacks(board_state, attackers: List[Any]):
    """
    Handle creatures attacking.

    This triggers 'attack' event for each attacker.

    Args:
        board_state: BoardState instance
        attackers: List of attacking creatures
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        return

    for attacker in attackers:
        attacker_dict = _card_to_dict(attacker)
        event_data = {
            'card': attacker_dict,
            'source_card': attacker_dict,
            'attackers': [_card_to_dict(a) for a in attackers],
        }
        board_state.trigger_event('attack', event_data)


def handle_creature_death(board_state, dead_creature):
    """
    Handle a creature dying.

    This:
    1. Triggers 'death' event
    2. Unregisters the creature's triggers

    Args:
        board_state: BoardState instance
        dead_creature: Card object that died
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        return

    # Trigger death event
    creature_dict = _card_to_dict(dead_creature)
    event_data = {
        'card': creature_dict,
        'source_card': creature_dict,
    }
    board_state.trigger_event('death', event_data)

    # Unregister creature's triggers
    creature_obj_id = id(dead_creature)
    if creature_obj_id in board_state.card_id_map:
        registry_id = board_state.card_id_map[creature_obj_id]
        board_state.trigger_registry.unregister_card(registry_id)
        del board_state.card_id_map[creature_obj_id]
        logger.debug(f"Unregistered {dead_creature.name} triggers")


def handle_end_of_turn(board_state):
    """
    Handle end of turn cleanup.

    This:
    1. Triggers 'end_of_turn' event
    2. Cleans up temporary effects (keywords, buffs)

    Args:
        board_state: BoardState instance
    """
    if not hasattr(board_state, 'cleanup_temporary_effects'):
        return

    # Trigger end of turn event
    if hasattr(board_state, 'trigger_registry') and board_state.trigger_registry:
        board_state.trigger_event('end_of_turn', {})

    # Clean up temporary effects
    board_state.cleanup_temporary_effects()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _card_to_dict(card) -> Dict[str, Any]:
    """
    Convert a Card object to a dictionary for parsing.

    Args:
        card: Card object from simulation

    Returns:
        Dict with card data in expected format
    """
    return {
        'name': card.name,
        'type_line': card.type,
        'oracle_text': getattr(card, 'oracle_text', ''),
        'keywords': getattr(card, 'keywords', []),
        'power': str(card.power) if hasattr(card, 'power') and card.power is not None else None,
        'toughness': str(card.toughness) if hasattr(card, 'toughness') and card.toughness is not None else None,
        'mana_cost': card.mana_cost if hasattr(card, 'mana_cost') else '',
    }


def preregister_deck_cards(board_state, deck_dicts: List[Dict[str, Any]]):
    """
    Pre-register all cards in the deck at game start.

    This allows synergy detection to work with trigger data.

    Args:
        board_state: BoardState instance
        deck_dicts: List of raw card data dicts
    """
    if not hasattr(board_state, 'unified_parser') or not hasattr(board_state, 'trigger_registry'):
        logger.warning("Unified system not initialized, cannot preregister deck")
        return

    logger.info(f"Pre-registering {len(deck_dicts)} deck cards...")

    for card_dict in deck_dicts:
        abilities = board_state.unified_parser.parse_card(card_dict)
        # Just parse, don't register yet (will register on ETB)

    logger.info("Deck cards pre-parsed for synergy detection")


# =============================================================================
# INTEGRATION HOOKS
# =============================================================================

def patch_simulate_game_with_triggers():
    """
    Monkey-patch the simulate_game module to add trigger support.

    This is a temporary solution until we can modify simulate_game.py directly.
    """
    try:
        import simulate_game

        # Store original functions
        original_simulate = simulate_game.simulate_game

        def simulate_with_triggers(*args, **kwargs):
            """Wrapper that initializes unified system."""
            # Call original simulate
            result = original_simulate(*args, **kwargs)

            # TODO: Add unified system initialization here
            return result

        # Replace function
        simulate_game.simulate_game = simulate_with_triggers

        logger.info("Patched simulate_game with trigger support")

    except Exception as e:
        logger.error(f"Failed to patch simulate_game: {e}")


# =============================================================================
# TESTING HELPERS
# =============================================================================

def test_trigger_integration(board_state):
    """
    Test that trigger integration is working.

    Args:
        board_state: BoardState instance

    Returns:
        Dict with test results
    """
    results = {
        'has_registry': hasattr(board_state, 'trigger_registry'),
        'has_parser': hasattr(board_state, 'unified_parser'),
        'has_trigger_event': hasattr(board_state, 'trigger_event'),
        'has_cleanup': hasattr(board_state, 'cleanup_temporary_effects'),
        'registry_stats': None,
    }

    if results['has_registry'] and board_state.trigger_registry:
        results['registry_stats'] = board_state.trigger_registry.get_stats()

    return results
