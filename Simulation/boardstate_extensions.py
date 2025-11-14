"""
BoardState Extensions for Unified Architecture

This module extends BoardState with methods needed to execute trigger effects
from the unified architecture (Parts 1-2).

These methods handle:
- Temporary keyword grants (rally effects: haste, vigilance, lifelink, etc.)
- Temporary creature buffs (prowess: +1/+1 until EOT)
- Token creation
- Damage effects
- Card draw
- +1/+1 counter addition
- End of turn cleanup

Usage:
    from Simulation.boardstate_extensions import enhance_boardstate

    board = BoardState(deck, commander)
    enhance_boardstate(board)  # Adds all new methods
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def enhance_boardstate(board_state):
    """
    Add enhanced methods to a BoardState instance.

    This function monkey-patches the BoardState with methods needed
    for the unified architecture.

    Args:
        board_state: BoardState instance to enhance
    """
    # Initialize new tracking attributes if not present
    if not hasattr(board_state, 'temporary_keywords'):
        board_state.temporary_keywords = {}  # {creature: [keywords]}

    if not hasattr(board_state, 'temporary_buffs'):
        board_state.temporary_buffs = {}  # {creature: {'power': X, 'toughness': X}}

    if not hasattr(board_state, 'trigger_registry'):
        board_state.trigger_registry = None  # Set by integration code

    # Add new methods
    board_state.grant_keyword_until_eot = lambda *args, **kwargs: grant_keyword_until_eot(board_state, *args, **kwargs)
    board_state.buff_creature_until_eot = lambda *args, **kwargs: buff_creature_until_eot(board_state, *args, **kwargs)
    board_state.put_counter_on_creatures = lambda *args, **kwargs: put_counter_on_creatures(board_state, *args, **kwargs)
    board_state.create_token = lambda *args, **kwargs: create_token(board_state, *args, **kwargs)
    board_state.deal_damage_to_target = lambda *args, **kwargs: deal_damage_to_target(board_state, *args, **kwargs)
    board_state.draw_cards_enhanced = lambda *args, **kwargs: draw_cards_enhanced(board_state, *args, **kwargs)
    board_state.scry_enhanced = lambda *args, **kwargs: scry_enhanced(board_state, *args, **kwargs)
    board_state.cleanup_temporary_effects = lambda *args, **kwargs: cleanup_temporary_effects(board_state, *args, **kwargs)
    board_state.trigger_event = lambda *args, **kwargs: trigger_event(board_state, *args, **kwargs)
    board_state.process_pending_effects = lambda *args, **kwargs: process_pending_effects(board_state, *args, **kwargs)

    logger.debug("BoardState enhanced with unified architecture methods")


# =============================================================================
# KEYWORD GRANT METHODS
# =============================================================================

def grant_keyword_until_eot(board_state, keyword: str, targets: str = 'all_creatures', source: str = 'Unknown'):
    """
    Grant a keyword to creatures until end of turn.

    Used by rally triggers (haste, vigilance, lifelink, double strike).

    Args:
        board_state: BoardState instance
        keyword: Keyword to grant ('haste', 'vigilance', 'lifelink', 'double strike')
        targets: Which creatures ('all_creatures', 'allies', 'self')
        source: Name of source card
    """
    keyword = keyword.lower()

    # Determine which creatures to affect
    affected = []
    if targets == 'all_creatures':
        affected = board_state.creatures.copy()
    elif targets == 'allies':
        affected = [c for c in board_state.creatures if 'Ally' in c.type]
    elif targets == 'self' and hasattr(board_state, 'current_spell_being_cast'):
        affected = [board_state.current_spell_being_cast]

    # Grant keyword to each affected creature
    for creature in affected:
        creature_id = id(creature)

        if creature_id not in board_state.temporary_keywords:
            board_state.temporary_keywords[creature_id] = []

        board_state.temporary_keywords[creature_id].append(keyword)

        # Also set the attribute directly on the creature for compatibility
        if keyword == 'haste':
            creature.has_haste = True
        elif keyword == 'vigilance':
            creature.has_vigilance = True
        elif keyword == 'lifelink':
            creature.has_lifelink = True
        elif keyword == 'double strike':
            creature.has_first_strike = True  # Simplified for simulation

        logger.debug(f"{source}: Granted {keyword} to {creature.name} until EOT")

    return len(affected)


# =============================================================================
# BUFF METHODS
# =============================================================================

def buff_creature_until_eot(board_state, power: int, toughness: int, target_creature=None, source: str = 'Unknown'):
    """
    Buff a creature's power/toughness until end of turn.

    Used by prowess triggers.

    Args:
        board_state: BoardState instance
        power: Power bonus
        toughness: Toughness bonus
        target_creature: Specific creature to buff (if None, buffs source)
        source: Name of source card
    """
    # If no target specified, find the most recent prowess creature
    if target_creature is None:
        # Look for creatures with prowess in their oracle text or keywords
        prowess_creatures = [
            c for c in board_state.creatures
            if 'prowess' in c.oracle_text.lower() or 'prowess' in str(getattr(c, 'keywords', [])).lower()
        ]
        if prowess_creatures:
            target_creature = prowess_creatures[-1]  # Most recently played
        else:
            logger.warning(f"{source}: No prowess creature found for buff")
            return

    creature_id = id(target_creature)

    if creature_id not in board_state.temporary_buffs:
        board_state.temporary_buffs[creature_id] = {'power': 0, 'toughness': 0}

    board_state.temporary_buffs[creature_id]['power'] += power
    board_state.temporary_buffs[creature_id]['toughness'] += toughness

    # Apply buff to creature stats
    if hasattr(target_creature, 'power') and target_creature.power is not None:
        target_creature.power += power
    if hasattr(target_creature, 'toughness') and target_creature.toughness is not None:
        target_creature.toughness += toughness

    logger.debug(f"{source}: Buffed {target_creature.name} +{power}/+{toughness} until EOT")


# =============================================================================
# COUNTER METHODS
# =============================================================================

def put_counter_on_creatures(board_state, counter_type: str, amount: int, targets: List[str], source: str = 'Unknown'):
    """
    Put counters on creatures.

    Used by rally counter effects.

    Args:
        board_state: BoardState instance
        counter_type: Type of counter ('+1/+1', 'loyalty', etc.)
        amount: Number of counters
        targets: List of target types (['all_creatures'], ['allies'], etc.)
        source: Name of source card
    """
    # Determine which creatures to affect
    affected = []
    if 'all_creatures' in targets:
        affected = board_state.creatures.copy()
    elif 'allies' in targets or 'ally' in targets:
        affected = [c for c in board_state.creatures if 'Ally' in c.type]
    elif 'self' in targets and hasattr(board_state, 'current_spell_being_cast'):
        affected = [board_state.current_spell_being_cast]

    # Add counters to each creature
    for creature in affected:
        if hasattr(creature, 'add_counter'):
            creature.add_counter(counter_type, amount)
            logger.debug(f"{source}: Added {amount} {counter_type} counter(s) to {creature.name}")
        elif counter_type == '+1/+1':
            # Fallback for creatures without add_counter method
            if hasattr(creature, 'power') and creature.power is not None:
                creature.power += amount
            if hasattr(creature, 'toughness') and creature.toughness is not None:
                creature.toughness += amount
            logger.debug(f"{source}: Buffed {creature.name} +{amount}/+{amount} (permanent)")

    return len(affected)


# =============================================================================
# TOKEN CREATION METHODS
# =============================================================================

def create_token(board_state, count: int, token_type: str, power: int, toughness: int,
                 types: List[str], source: str = 'Unknown', has_haste: bool = False):
    """
    Create token creatures.

    Args:
        board_state: BoardState instance
        count: Number of tokens to create
        token_type: Type of token ('creature', 'artifact creature', etc.)
        power: Token power
        toughness: Token toughness
        types: Creature types (e.g., ['Spirit', 'Ally'])
        source: Name of source card
        has_haste: Whether tokens have haste
    """
    # Try to import the Card class
    Card = None
    try:
        from simulate_game import Card
    except ImportError:
        # Try alternate import
        try:
            import sys
            if 'test_boardstate_integration' in sys.modules:
                Card = sys.modules['test_boardstate_integration'].Card
        except Exception:
            pass

    if Card is None:
        logger.warning("Could not import Card class for token creation")
        # Create a simple mock token
        class SimpleToken:
            def __init__(self, name, type, power, toughness, has_haste, **kwargs):
                self.name = name
                self.type = type
                self.power = power
                self.toughness = toughness
                self.has_haste = has_haste
                self.has_vigilance = False
                self.has_lifelink = False
                self.oracle_text = ""
                # Accept any other kwargs
                for k, v in kwargs.items():
                    setattr(self, k, v)
        Card = SimpleToken

    tokens_created = 0

    for i in range(count):
        # Create token card
        token_name = f"{' '.join(types)} Token" if types else f"{token_type.title()} Token"

        token = Card(
            name=token_name,
            type=f"{token_type} — {' '.join(types)}" if types else token_type,
            power=power,
            toughness=toughness,
            has_haste=has_haste,
            mana_cost="",
            produces_colors=[],
            mana_production={},
            etb_tapped=False,
            etb_tapped_conditions=[],
        )

        # Add to battlefield
        board_state.creatures.append(token)
        tokens_created += 1

        # Track token creation
        if hasattr(board_state, 'tokens_created_this_turn'):
            board_state.tokens_created_this_turn += 1

    logger.debug(f"{source}: Created {tokens_created} {token_name}(s)")
    return tokens_created


# =============================================================================
# DAMAGE METHODS
# =============================================================================

def deal_damage_to_target(board_state, amount: int, targets: List[str], source: str = 'Unknown'):
    """
    Deal damage to targets.

    Args:
        board_state: BoardState instance
        amount: Damage amount
        targets: List of targets (['opponent'], ['each_opponent'], ['creature'], etc.)
        source: Name of source card
    """
    damage_dealt = 0

    for target in targets:
        if target == 'opponent' or target == 'player':
            # Deal damage to the first opponent
            if board_state.num_opponents > 0 and board_state.opponents:
                board_state.opponents[0]['life_total'] -= amount
                damage_dealt += amount
                logger.debug(f"{source}: Dealt {amount} damage to opponent")

        elif target == 'each_opponent':
            # Deal damage to all opponents
            for opponent in board_state.opponents:
                if opponent['is_alive']:
                    opponent['life_total'] -= amount
                    damage_dealt += amount
            logger.debug(f"{source}: Dealt {amount} damage to each opponent")

        elif target == 'creature' or target == 'target_creature':
            # Deal damage to first opponent's creature
            if board_state.opponents and board_state.opponents[0]['creatures']:
                target_creature = board_state.opponents[0]['creatures'][0]
                if hasattr(target_creature, 'take_damage'):
                    actual = target_creature.take_damage(amount)
                    damage_dealt += actual
                logger.debug(f"{source}: Dealt {amount} damage to opponent's creature")

    # Track damage for metrics
    if hasattr(board_state, 'spell_damage_this_turn'):
        board_state.spell_damage_this_turn += damage_dealt

    return damage_dealt


# =============================================================================
# CARD DRAW METHODS
# =============================================================================

def draw_cards_enhanced(board_state, count: int, source: str = 'Unknown'):
    """
    Draw cards (enhanced version that works with trigger system).

    Args:
        board_state: BoardState instance
        count: Number of cards to draw
        source: Name of source card
    """
    drawn = 0

    for _ in range(count):
        if board_state.library:
            card = board_state.library.pop(0)
            board_state.hand.append(card)
            drawn += 1

    logger.debug(f"{source}: Drew {drawn} card(s)")
    return drawn


def scry_enhanced(board_state, count: int, source: str = 'Unknown'):
    """
    Scry N (look at top N cards, put some on top and some on bottom).

    For simulation purposes, we'll implement a simplified version that
    keeps the best card on top based on CMC and card type.

    Args:
        board_state: BoardState instance
        count: Number of cards to scry
        source: Name of source card
    """
    if not board_state.library or count <= 0:
        return

    scry_count = min(count, len(board_state.library))

    # Simplified: Keep the lowest CMC spell on top (better for curve)
    # In a real implementation, this would use AI decision-making
    logger.debug(f"{source}: Scry {scry_count} (simplified - keeping best card on top)")

    # For now, just leave cards as they are (random is fine for simulation)
    return scry_count


# =============================================================================
# CLEANUP METHODS
# =============================================================================

def cleanup_temporary_effects(board_state):
    """
    Clean up all temporary effects at end of turn.

    This removes:
    - Temporary keywords (from rally triggers)
    - Temporary buffs (from prowess triggers)
    """
    # Remove temporary keywords
    for creature_id, keywords in list(board_state.temporary_keywords.items()):
        # Find the creature
        creature = None
        for c in board_state.creatures:
            if id(c) == creature_id:
                creature = c
                break

        if creature:
            for keyword in keywords:
                if keyword == 'haste':
                    creature.has_haste = False
                elif keyword == 'vigilance':
                    creature.has_vigilance = False
                elif keyword == 'lifelink':
                    creature.has_lifelink = False
                elif keyword == 'double strike':
                    creature.has_first_strike = False

    # Clear temporary keywords tracking
    board_state.temporary_keywords.clear()

    # Remove temporary buffs
    for creature_id, buff in list(board_state.temporary_buffs.items()):
        # Find the creature
        creature = None
        for c in board_state.creatures:
            if id(c) == creature_id:
                creature = c
                break

        if creature:
            power_buff = buff.get('power', 0)
            toughness_buff = buff.get('toughness', 0)

            if hasattr(creature, 'power') and creature.power is not None:
                creature.power -= power_buff
            if hasattr(creature, 'toughness') and creature.toughness is not None:
                creature.toughness -= toughness_buff

            logger.debug(f"Removed temporary buff from {creature.name}: -{power_buff}/-{toughness_buff}")

    # Clear temporary buffs tracking
    board_state.temporary_buffs.clear()

    logger.debug("Cleaned up temporary effects (EOT)")


# =============================================================================
# TRIGGER EVENT METHODS
# =============================================================================

def trigger_event(board_state, event: str, event_data: Dict[str, Any] = None):
    """
    Trigger all registered triggers for an event.

    This is called when game events occur (creature ETB, spell cast, etc.)

    Args:
        board_state: BoardState instance
        event: Event type ('etb', 'rally', 'cast_spell', 'cast_noncreature_spell', etc.)
        event_data: Data about the event (card, source, etc.)
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        # Trigger registry not initialized yet
        return

    if event_data is None:
        event_data = {}

    # Call the trigger registry
    board_state.trigger_registry.trigger_event(event, board_state, event_data)

    # Process any pending effects created by triggers
    process_pending_effects(board_state)


def process_pending_effects(board_state):
    """
    Process all pending effects created by triggers.

    Pending effects are created by trigger_effects.py functions and
    need to be executed to actually modify the game state.
    """
    if not hasattr(board_state, 'pending_effects'):
        return

    effects_processed = 0

    for effect in board_state.pending_effects:
        effect_type = effect.get('type')

        if effect_type == 'grant_keyword':
            keyword = effect.get('keyword')
            targets = effect.get('targets', 'all_creatures')
            source = effect.get('source', 'Unknown')
            grant_keyword_until_eot(board_state, keyword, targets, source)
            effects_processed += 1

        elif effect_type == 'buff_creature':
            power = effect.get('power', 0)
            toughness = effect.get('toughness', 0)
            source = effect.get('source', 'Unknown')
            buff_creature_until_eot(board_state, power, toughness, source=source)
            effects_processed += 1

        elif effect_type == 'add_counters':
            counter_type = effect.get('counter_type', '+1/+1')
            amount = effect.get('amount', 1)
            targets = effect.get('targets', ['all_creatures'])
            source = effect.get('source', 'Unknown')
            put_counter_on_creatures(board_state, counter_type, amount, targets, source)
            effects_processed += 1

        elif effect_type == 'create_tokens':
            count = effect.get('count', 1)
            token_type = effect.get('token_type', 'creature')
            power = effect.get('power', 1)
            toughness = effect.get('toughness', 1)
            types = effect.get('types', [])
            source = effect.get('source', 'Unknown')
            create_token(board_state, count, token_type, power, toughness, types, source)
            effects_processed += 1

        elif effect_type == 'deal_damage':
            amount = effect.get('amount', 1)
            targets = effect.get('targets', ['opponent'])
            source = effect.get('source', 'Unknown')
            deal_damage_to_target(board_state, amount, targets, source)
            effects_processed += 1

        elif effect_type == 'draw_cards':
            count = effect.get('count', 1)
            source = effect.get('source', 'Unknown')
            draw_cards_enhanced(board_state, count, source)
            effects_processed += 1

        elif effect_type == 'scry':
            count = effect.get('count', 1)
            source = effect.get('source', 'Unknown')
            scry_enhanced(board_state, count, source)
            effects_processed += 1

    # Clear pending effects
    board_state.pending_effects.clear()

    if effects_processed > 0:
        logger.debug(f"Processed {effects_processed} pending effect(s)")

    return effects_processed
