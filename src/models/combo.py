"""
Data models for Magic: The Gathering combos
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ComboCard:
    """Represents a card in a combo"""
    name: str
    oracle_id: Optional[str] = None
    card_type: Optional[str] = None
    zone_locations: List[str] = field(default_factory=list)  # battlefield, graveyard, command zone, etc.

    def __hash__(self):
        return hash(self.name.lower())

    def __eq__(self, other):
        if isinstance(other, ComboCard):
            return self.name.lower() == other.name.lower()
        return False


@dataclass
class Combo:
    """Represents a Magic: The Gathering combo"""
    id: str  # Commander Spellbook ID or unique identifier
    cards: List[ComboCard]
    prerequisites: List[str]  # What needs to be true before combo works
    steps: List[str]  # How to execute the combo
    results: List[str]  # What the combo produces (infinite mana, infinite damage, etc.)
    color_identity: str  # WUBRG color identity
    permalink: Optional[str] = None
    mana_needed: Optional[str] = None
    other_requirements: List[str] = field(default_factory=list)
    has_banned_card: bool = False
    has_spoiled_card: bool = False

    @property
    def card_names(self) -> List[str]:
        """Get list of card names in this combo"""
        return [card.name for card in self.cards]

    @property
    def num_cards(self) -> int:
        """Number of cards required for combo"""
        return len(self.cards)

    @property
    def primary_result(self) -> str:
        """Get the primary result of the combo"""
        if self.results:
            return self.results[0]
        return "Unknown result"

    def matches_deck(self, deck_cards: List[str]) -> bool:
        """
        Check if all combo pieces are present in the deck

        Args:
            deck_cards: List of card names in the deck

        Returns:
            True if all combo pieces are in the deck
        """
        deck_cards_lower = [card.lower() for card in deck_cards]
        return all(card.name.lower() in deck_cards_lower for card in self.cards)

    def get_missing_cards(self, deck_cards: List[str]) -> List[str]:
        """
        Get list of combo pieces missing from the deck

        Args:
            deck_cards: List of card names in the deck

        Returns:
            List of missing card names
        """
        deck_cards_lower = [card.lower() for card in deck_cards]
        return [
            card.name for card in self.cards
            if card.name.lower() not in deck_cards_lower
        ]

    def to_dict(self) -> Dict:
        """Convert combo to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'cards': [{'name': card.name, 'zone_locations': card.zone_locations} for card in self.cards],
            'prerequisites': self.prerequisites,
            'steps': self.steps,
            'results': self.results,
            'color_identity': self.color_identity,
            'permalink': self.permalink,
            'mana_needed': self.mana_needed,
            'other_requirements': self.other_requirements,
            'has_banned_card': self.has_banned_card,
            'has_spoiled_card': self.has_spoiled_card,
            'num_cards': self.num_cards
        }

    @classmethod
    def from_spellbook_data(cls, data: Dict) -> 'Combo':
        """
        Create a Combo from Commander Spellbook API response

        Args:
            data: Dictionary from Commander Spellbook API

        Returns:
            Combo instance
        """
        # Parse cards
        cards = []
        for card_data in data.get('uses', []):
            # Commander Spellbook uses 'card' for card info
            # Handle both dict and string formats
            if isinstance(card_data, str):
                # If it's a string, just use it as the card name
                cards.append(ComboCard(name=card_data))
            elif isinstance(card_data, dict):
                card_info = card_data.get('card', {})
                cards.append(ComboCard(
                    name=card_info.get('name', ''),
                    oracle_id=card_info.get('oracle_id'),
                    zone_locations=card_data.get('zone_locations', [])
                ))
            else:
                # Skip unknown formats
                continue

        # Parse prerequisites, steps, results
        prerequisites = []
        for item in data.get('requires', []):
            if isinstance(item, str):
                prerequisites.append(item)
            elif isinstance(item, dict):
                prerequisites.append(item.get('feature', {}).get('name', ''))

        # Parse results
        results = []
        for item in data.get('produces', []):
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, dict):
                results.append(item.get('feature', {}).get('name', ''))

        return cls(
            id=str(data.get('id', '')),
            cards=cards,
            prerequisites=prerequisites,
            steps=data.get('description', '').split('\n') if data.get('description') else [],
            results=results,
            color_identity=data.get('identity', ''),
            permalink=f"https://commanderspellbook.com/combo/{data.get('id', '')}",
            mana_needed=data.get('mana_needed'),
            other_requirements=data.get('other_prerequisites', []),
            has_banned_card=any(card.get('card', {}).get('legal', True) == False for card in data.get('uses', [])),
            has_spoiled_card=False  # Would need additional logic
        )
