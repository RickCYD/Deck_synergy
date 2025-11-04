"""
Deck Editing Session Management
Manages in-memory deck editing state with undo/redo support
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .deck import Deck
import copy


class DeckChange:
    """
    Represents a single deck modification
    """

    def __init__(
        self,
        change_type: str,
        card_added: Optional[Dict] = None,
        card_removed: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        self.change_type = change_type  # 'add', 'remove', 'swap'
        self.card_added = card_added
        self.card_removed = card_removed
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'change_type': self.change_type,
            'card_added': self.card_added,
            'card_removed': self.card_removed,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DeckChange':
        """Create from dictionary"""
        return cls(
            change_type=data['change_type'],
            card_added=data.get('card_added'),
            card_removed=data.get('card_removed'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        )


class DeckEditingSession:
    """
    Manages deck editing state with undo/redo support
    """

    def __init__(self, deck: Deck):
        self.current_deck = deck
        self.original_deck = deck.copy()
        self.change_history: List[DeckChange] = []
        self.change_index = -1  # Current position in history
        self.unsaved_changes = False

    def add_card(self, card: Dict) -> Dict[str, Any]:
        """
        Add card to deck

        Args:
            card: Card dictionary with name, oracle_text, etc.

        Returns:
            Dict with success status and message
        """
        # Validate deck size
        if len(self.current_deck.cards) >= 100:
            return {
                'success': False,
                'error': 'Deck already has 100 cards. Remove a card first.'
            }

        # Check singleton rule (Commander format)
        existing_card = self.current_deck.get_card_by_name(card['name'])
        if existing_card:
            return {
                'success': False,
                'error': f"{card['name']} is already in the deck."
            }

        # Add card
        self.current_deck.cards.append(card)
        self.unsaved_changes = True

        # Create change record
        change = DeckChange(
            change_type='add',
            card_added=card,
            card_removed=None
        )

        # Add to history (clear any redo history)
        self.change_history = self.change_history[:self.change_index + 1]
        self.change_history.append(change)
        self.change_index += 1

        return {
            'success': True,
            'message': f"Added {card['name']} to deck",
            'change': change,
            'deck_size': len(self.current_deck.cards)
        }

    def remove_card(self, card_name: str) -> Dict[str, Any]:
        """
        Remove card from deck

        Args:
            card_name: Name of card to remove

        Returns:
            Dict with success status and message
        """
        # Find card
        card = self.current_deck.get_card_by_name(card_name)
        if not card:
            return {
                'success': False,
                'error': f"{card_name} not found in deck."
            }

        # Don't allow removing commander
        if card.get('is_commander', False):
            return {
                'success': False,
                'error': "Cannot remove commander from deck."
            }

        # Remove card
        self.current_deck.cards = [
            c for c in self.current_deck.cards
            if c['name'] != card_name
        ]
        self.unsaved_changes = True

        # Create change record
        change = DeckChange(
            change_type='remove',
            card_added=None,
            card_removed=card
        )

        # Add to history
        self.change_history = self.change_history[:self.change_index + 1]
        self.change_history.append(change)
        self.change_index += 1

        return {
            'success': True,
            'message': f"Removed {card_name} from deck",
            'change': change,
            'deck_size': len(self.current_deck.cards)
        }

    def swap_cards(self, remove_name: str, add_card: Dict) -> Dict[str, Any]:
        """
        Atomically swap two cards (remove one, add another)

        Args:
            remove_name: Name of card to remove
            add_card: Card to add

        Returns:
            Dict with success status and message
        """
        # Find card to remove
        card_to_remove = self.current_deck.get_card_by_name(remove_name)
        if not card_to_remove:
            return {
                'success': False,
                'error': f"{remove_name} not found in deck."
            }

        # Don't allow removing commander
        if card_to_remove.get('is_commander', False):
            return {
                'success': False,
                'error': "Cannot remove commander from deck."
            }

        # Check singleton rule for new card
        if self.current_deck.get_card_by_name(add_card['name']):
            return {
                'success': False,
                'error': f"{add_card['name']} is already in the deck."
            }

        # Perform swap
        self.current_deck.cards = [
            c if c['name'] != remove_name else add_card
            for c in self.current_deck.cards
        ]
        self.unsaved_changes = True

        # Create change record
        change = DeckChange(
            change_type='swap',
            card_added=add_card,
            card_removed=card_to_remove
        )

        # Add to history
        self.change_history = self.change_history[:self.change_index + 1]
        self.change_history.append(change)
        self.change_index += 1

        return {
            'success': True,
            'message': f"Swapped {remove_name} for {add_card['name']}",
            'change': change,
            'deck_size': len(self.current_deck.cards)
        }

    def undo(self) -> Dict[str, Any]:
        """
        Undo last change

        Returns:
            Dict with success status and message
        """
        if self.change_index < 0:
            return {
                'success': False,
                'error': 'Nothing to undo'
            }

        change = self.change_history[self.change_index]

        # Reverse the change
        if change.change_type == 'add':
            # Remove the added card
            self.current_deck.cards = [
                c for c in self.current_deck.cards
                if c['name'] != change.card_added['name']
            ]
        elif change.change_type == 'remove':
            # Re-add the removed card
            self.current_deck.cards.append(change.card_removed)
        elif change.change_type == 'swap':
            # Swap back
            self.current_deck.cards = [
                c if c['name'] != change.card_added['name'] else change.card_removed
                for c in self.current_deck.cards
            ]

        self.change_index -= 1
        self.unsaved_changes = self.change_index >= 0

        return {
            'success': True,
            'message': f"Undid {change.change_type}",
            'deck_size': len(self.current_deck.cards)
        }

    def redo(self) -> Dict[str, Any]:
        """
        Redo previously undone change

        Returns:
            Dict with success status and message
        """
        if self.change_index >= len(self.change_history) - 1:
            return {
                'success': False,
                'error': 'Nothing to redo'
            }

        self.change_index += 1
        change = self.change_history[self.change_index]

        # Reapply the change
        if change.change_type == 'add':
            self.current_deck.cards.append(change.card_added)
        elif change.change_type == 'remove':
            self.current_deck.cards = [
                c for c in self.current_deck.cards
                if c['name'] != change.card_removed['name']
            ]
        elif change.change_type == 'swap':
            self.current_deck.cards = [
                c if c['name'] != change.card_removed['name'] else change.card_added
                for c in self.current_deck.cards
            ]

        self.unsaved_changes = True

        return {
            'success': True,
            'message': f"Redid {change.change_type}",
            'deck_size': len(self.current_deck.cards)
        }

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.change_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.change_index < len(self.change_history) - 1

    def get_changes_summary(self) -> Dict[str, Any]:
        """
        Get summary of all changes

        Returns:
            Dict with change counts and details
        """
        adds = sum(1 for c in self.change_history[:self.change_index + 1] if c.change_type == 'add')
        removes = sum(1 for c in self.change_history[:self.change_index + 1] if c.change_type == 'remove')
        swaps = sum(1 for c in self.change_history[:self.change_index + 1] if c.change_type == 'swap')

        return {
            'total_changes': self.change_index + 1,
            'adds': adds,
            'removes': removes,
            'swaps': swaps,
            'unsaved': self.unsaved_changes,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo()
        }

    def save(self, directory: str = 'data/decks') -> Dict[str, Any]:
        """
        Save current deck state

        Returns:
            Dict with success status and file path
        """
        try:
            file_path = self.current_deck.save(directory)
            self.unsaved_changes = False
            self.original_deck = self.current_deck.copy()

            return {
                'success': True,
                'message': f"Deck saved successfully",
                'file_path': str(file_path)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to save deck: {str(e)}"
            }

    def discard_changes(self) -> Dict[str, Any]:
        """
        Discard all changes and revert to original deck

        Returns:
            Dict with success status
        """
        self.current_deck = self.original_deck.copy()
        self.change_history = []
        self.change_index = -1
        self.unsaved_changes = False

        return {
            'success': True,
            'message': 'All changes discarded',
            'deck_size': len(self.current_deck.cards)
        }

    def to_dict(self) -> Dict:
        """Serialize session to dictionary for storage"""
        return {
            'current_deck': self.current_deck.to_dict(),
            'original_deck': self.original_deck.to_dict(),
            'change_history': [c.to_dict() for c in self.change_history],
            'change_index': self.change_index,
            'unsaved_changes': self.unsaved_changes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DeckEditingSession':
        """Deserialize session from dictionary"""
        current_deck = Deck.from_dict(data['current_deck'])
        session = cls(current_deck)

        session.original_deck = Deck.from_dict(data['original_deck'])
        session.change_history = [
            DeckChange.from_dict(c) for c in data.get('change_history', [])
        ]
        session.change_index = data.get('change_index', -1)
        session.unsaved_changes = data.get('unsaved_changes', False)

        return session
