#!/usr/bin/env python3
"""
Central trigger registry for the unified architecture.

This module manages registration and execution of triggered abilities
during game simulation. It serves as the bridge between parsed card
abilities and actual game state changes.

Key Responsibilities:
- Register triggers from CardAbilities instances
- Organize triggers by event type for efficient lookup
- Execute triggers in correct priority order
- Check trigger conditions before execution
- Integrate with BoardState for state changes
"""

from typing import Dict, List, Callable, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from src.core.card_parser import CardAbilities, TriggerAbility, StaticAbility
from src.core.trigger_effects import create_effect_from_trigger, create_effect_from_static

logger = logging.getLogger(__name__)


@dataclass
class RegisteredTrigger:
    """
    A trigger that has been registered for a specific card in play.

    Attributes:
        card_name: Name of the source card
        card_id: Unique identifier for this card instance
        event: Event type that triggers this ability
        condition: Optional condition that must be true
        effect_func: Callable to execute when triggered
        priority: Execution priority (higher = first)
        metadata: Additional data for advanced handling
    """
    card_name: str
    card_id: str
    event: str
    condition: Optional[str]
    effect_func: Callable
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_trigger(self, board_state, event_data: Dict[str, Any]) -> bool:
        """
        Check if this trigger's condition is met.

        Args:
            board_state: Current BoardState instance
            event_data: Data about the triggering event

        Returns:
            True if trigger should execute
        """
        # No condition = always triggers
        if not self.condition:
            return True

        # TODO: Implement condition checking
        # For now, basic conditions:
        condition = self.condition.lower()

        # "if you control an ally" type conditions
        if 'control' in condition and 'ally' in condition:
            # Check if we have allies
            if hasattr(board_state, 'battlefield'):
                return any('Ally' in c.get('type_line', '') for c in board_state.battlefield)
            return True  # Assume true for now

        # "if you cast an instant or sorcery" type conditions
        if 'instant' in condition or 'sorcery' in condition:
            card = event_data.get('card', {})
            type_line = card.get('type_line', '').lower()
            return 'instant' in type_line or 'sorcery' in type_line

        # "if creature has power 2 or less" type conditions
        if 'power' in condition and 'or less' in condition:
            card = event_data.get('card', {})
            power = card.get('power', '0')
            try:
                return int(power) <= 2
            except (ValueError, TypeError):
                return False

        # Default to True for unimplemented conditions
        return True

    def execute(self, board_state, event_data: Dict[str, Any]) -> None:
        """
        Execute this trigger's effect.

        Args:
            board_state: Current BoardState instance
            event_data: Data about the triggering event
        """
        if not self.can_trigger(board_state, event_data):
            logger.debug(f"Trigger condition not met for {self.card_name}")
            return

        logger.debug(f"Executing trigger: {self.card_name} ({self.event})")

        try:
            # Find source card
            source_card = event_data.get('source_card')
            if not source_card:
                # Try to find it by card_id
                source_card = {'name': self.card_name, 'id': self.card_id}

            # Remove source_card from event_data to avoid duplication
            filtered_data = {k: v for k, v in event_data.items() if k != 'source_card'}

            # Execute the effect
            self.effect_func(board_state, source_card, **filtered_data)

        except Exception as e:
            logger.error(f"Error executing trigger {self.card_name}: {e}")


class TriggerRegistry:
    """
    Central registry for all active triggers in a game.

    This class manages the lifecycle of triggers:
    1. Registration when cards enter the battlefield
    2. Lookup when events occur
    3. Execution in correct priority order
    4. Removal when cards leave the battlefield
    """

    def __init__(self):
        """Initialize empty trigger registry."""
        # Triggers organized by event type for fast lookup
        self._triggers_by_event: Dict[str, List[RegisteredTrigger]] = defaultdict(list)

        # All triggers by card ID for removal
        self._triggers_by_card: Dict[str, List[RegisteredTrigger]] = defaultdict(list)

        # Static abilities (anthems, cost reduction, etc.)
        self._static_abilities: List[RegisteredTrigger] = []

        # Counter for unique card IDs
        self._next_card_id = 0

    def register_card(self, card: Dict[str, Any], abilities: CardAbilities) -> str:
        """
        Register all triggers and abilities from a card.

        Args:
            card: Raw card data dict
            abilities: Parsed CardAbilities instance

        Returns:
            Unique card_id for this card instance
        """
        card_id = f"{card.get('name', 'Unknown')}_{self._next_card_id}"
        self._next_card_id += 1

        card_name = card.get('name', 'Unknown')
        logger.debug(f"Registering card: {card_name} (ID: {card_id})")

        # Register triggered abilities
        for trigger in abilities.triggers:
            effect_func = create_effect_from_trigger(trigger)
            if not effect_func:
                logger.warning(f"Could not create effect for {card_name} trigger: {trigger.event}")
                continue

            # Determine priority
            priority = self._calculate_priority(trigger)

            registered = RegisteredTrigger(
                card_name=card_name,
                card_id=card_id,
                event=trigger.event,
                condition=trigger.condition,
                effect_func=effect_func,
                priority=priority,
                metadata=trigger.metadata
            )

            self._triggers_by_event[trigger.event].append(registered)
            self._triggers_by_card[card_id].append(registered)

            logger.debug(f"  Registered trigger: {trigger.event} -> {trigger.effect_type}")

        # Register static abilities
        for static in abilities.static_abilities:
            effect_func = create_effect_from_static(static)
            if not effect_func:
                logger.warning(f"Could not create effect for {card_name} static: {static.ability_type}")
                continue

            registered = RegisteredTrigger(
                card_name=card_name,
                card_id=card_id,
                event='static',
                condition=None,
                effect_func=effect_func,
                priority=0,
                metadata={'ability_type': static.ability_type}
            )

            self._static_abilities.append(registered)
            self._triggers_by_card[card_id].append(registered)

            logger.debug(f"  Registered static ability: {static.ability_type}")

        return card_id

    def unregister_card(self, card_id: str) -> None:
        """
        Remove all triggers for a card (when it leaves battlefield).

        Args:
            card_id: Unique card identifier from registration
        """
        triggers = self._triggers_by_card.get(card_id, [])
        if not triggers:
            logger.warning(f"No triggers found for card_id: {card_id}")
            return

        logger.debug(f"Unregistering card: {card_id} ({len(triggers)} triggers)")

        # Remove from event lookup
        for trigger in triggers:
            if trigger.event == 'static':
                if trigger in self._static_abilities:
                    self._static_abilities.remove(trigger)
            else:
                event_triggers = self._triggers_by_event.get(trigger.event, [])
                if trigger in event_triggers:
                    event_triggers.remove(trigger)

        # Remove from card lookup
        del self._triggers_by_card[card_id]

    def trigger_event(self, event: str, board_state, event_data: Dict[str, Any] = None) -> None:
        """
        Execute all triggers for a given event.

        Args:
            event: Event type (e.g., 'rally', 'etb', 'cast_spell')
            board_state: Current BoardState instance
            event_data: Optional data about the event
        """
        if event_data is None:
            event_data = {}

        triggers = self._triggers_by_event.get(event, [])
        if not triggers:
            logger.debug(f"No triggers registered for event: {event}")
            return

        logger.debug(f"Event '{event}' triggered ({len(triggers)} trigger(s))")

        # Sort by priority (higher priority = execute first)
        sorted_triggers = sorted(triggers, key=lambda t: t.priority, reverse=True)

        # Execute each trigger
        for trigger in sorted_triggers:
            trigger.execute(board_state, event_data)

    def apply_static_abilities(self, board_state) -> None:
        """
        Apply all active static abilities to board state.

        This should be called whenever board state changes or at
        specific calculation points.

        Args:
            board_state: Current BoardState instance
        """
        if not self._static_abilities:
            return

        logger.debug(f"Applying {len(self._static_abilities)} static abilities")

        for ability in self._static_abilities:
            try:
                source_card = {'name': ability.card_name, 'id': ability.card_id}
                ability.effect_func(board_state, source_card)
            except Exception as e:
                logger.error(f"Error applying static ability from {ability.card_name}: {e}")

    def get_triggers_for_event(self, event: str) -> List[RegisteredTrigger]:
        """
        Get all triggers registered for a specific event.

        Args:
            event: Event type

        Returns:
            List of RegisteredTrigger instances
        """
        return self._triggers_by_event.get(event, []).copy()

    def get_triggers_for_card(self, card_id: str) -> List[RegisteredTrigger]:
        """
        Get all triggers for a specific card.

        Args:
            card_id: Unique card identifier

        Returns:
            List of RegisteredTrigger instances
        """
        return self._triggers_by_card.get(card_id, []).copy()

    def get_all_events(self) -> Set[str]:
        """
        Get all event types that have registered triggers.

        Returns:
            Set of event names
        """
        return set(self._triggers_by_event.keys())

    def clear(self) -> None:
        """Clear all registered triggers and static abilities."""
        self._triggers_by_event.clear()
        self._triggers_by_card.clear()
        self._static_abilities.clear()
        self._next_card_id = 0
        logger.debug("Trigger registry cleared")

    def _calculate_priority(self, trigger: TriggerAbility) -> int:
        """
        Calculate execution priority for a trigger.

        Higher priority triggers execute first.
        Priority helps ensure correct order of effects.

        Args:
            trigger: TriggerAbility to calculate priority for

        Returns:
            Priority value (0-100)
        """
        # Default priority
        priority = 50

        # Rally triggers should execute before other ETB triggers
        if trigger.event == 'rally':
            priority = 60

        # Token creation triggers
        if trigger.effect_type in ['tokens', 'create_tokens']:
            priority = 55

        # Damage triggers (like Impact Tremors)
        if trigger.effect_type == 'damage':
            priority = 45

        # Draw triggers
        if trigger.effect_type == 'draw':
            priority = 40

        # Magecraft/doubling triggers should execute last
        if 'magecraft' in trigger.event or 'double' in trigger.effect.lower():
            priority = 70

        return priority

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered triggers.

        Returns:
            Dict with counts and information
        """
        total_triggers = sum(len(triggers) for triggers in self._triggers_by_event.values())

        return {
            'total_triggers': total_triggers,
            'total_static_abilities': len(self._static_abilities),
            'total_cards': len(self._triggers_by_card),
            'events_with_triggers': list(self._triggers_by_event.keys()),
            'triggers_by_event': {
                event: len(triggers)
                for event, triggers in self._triggers_by_event.items()
            }
        }

    def __str__(self) -> str:
        """String representation showing registry stats."""
        stats = self.get_stats()
        return (
            f"TriggerRegistry("
            f"cards={stats['total_cards']}, "
            f"triggers={stats['total_triggers']}, "
            f"static={stats['total_static_abilities']})"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_registry_from_deck(deck: List[Dict[str, Any]], parser) -> TriggerRegistry:
    """
    Create a TriggerRegistry with all cards from a deck.

    Args:
        deck: List of card dicts
        parser: UnifiedCardParser instance

    Returns:
        TriggerRegistry with all deck cards registered
    """
    registry = TriggerRegistry()

    for card in deck:
        abilities = parser.parse_card(card)
        registry.register_card(card, abilities)

    logger.info(f"Created registry from deck: {registry}")
    return registry


def register_battlefield(registry: TriggerRegistry, battlefield: List[Dict[str, Any]], parser) -> Dict[str, str]:
    """
    Register all cards currently on the battlefield.

    Args:
        registry: TriggerRegistry instance
        battlefield: List of cards on battlefield
        parser: UnifiedCardParser instance

    Returns:
        Dict mapping card index to card_id
    """
    card_ids = {}

    for i, card in enumerate(battlefield):
        abilities = parser.parse_card(card)
        card_id = registry.register_card(card, abilities)
        card_ids[i] = card_id

    logger.info(f"Registered {len(battlefield)} cards from battlefield")
    return card_ids
