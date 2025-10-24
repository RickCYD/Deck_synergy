"""
Deck Data Model
Manages deck data, cards, and synergies
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class Deck:
    """
    Represents a Magic: The Gathering Commander deck

    Attributes:
        deck_id: Unique identifier (from Archidekt)
        name: Deck name
        cards: List of card dictionaries
        synergies: Dictionary of synergies between cards
        metadata: Additional deck metadata
    """

    def __init__(self, deck_id: str, name: str, cards: List[Dict],
                 synergies: Optional[Dict] = None, metadata: Optional[Dict] = None):
        self.deck_id = deck_id
        self.name = name
        self.cards = cards
        self.synergies = synergies or {}
        self.metadata = metadata or {}

        # Add creation timestamp if not present
        if 'created_at' not in self.metadata:
            self.metadata['created_at'] = datetime.now().isoformat()

        self.metadata['updated_at'] = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert deck to dictionary format"""
        return {
            'deck_id': self.deck_id,
            'name': self.name,
            'cards': self.cards,
            'synergies': self.synergies,
            'metadata': self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert deck to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, directory: str = 'data/decks') -> Path:
        """
        Save deck to JSON file

        Args:
            directory: Directory to save the file

        Returns:
            Path to the saved file
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')

        file_path = dir_path / f"{safe_name}_{self.deck_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        return file_path

    @classmethod
    def from_dict(cls, data: Dict) -> 'Deck':
        """Create Deck instance from dictionary"""
        return cls(
            deck_id=data['deck_id'],
            name=data['name'],
            cards=data.get('cards', []),
            synergies=data.get('synergies', {}),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Deck':
        """Create Deck instance from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, file_path: str) -> 'Deck':
        """Load deck from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_commander(self) -> Optional[Dict]:
        """Get the commander card(s)"""
        commanders = [card for card in self.cards if card.get('is_commander', False)]
        return commanders[0] if commanders else None

    def get_commanders(self) -> List[Dict]:
        """Get all commander cards (for partner commanders)"""
        return [card for card in self.cards if card.get('is_commander', False)]

    def get_cards_by_type(self, card_type: str) -> List[Dict]:
        """
        Get all cards of a specific type

        Args:
            card_type: Card type to filter (e.g., 'Creature', 'Artifact')

        Returns:
            List of matching cards
        """
        return [
            card for card in self.cards
            if card_type in card.get('type_line', '')
        ]

    def get_cards_by_color(self, colors: List[str]) -> List[Dict]:
        """
        Get all cards with specific colors

        Args:
            colors: List of color codes (W, U, B, R, G)

        Returns:
            List of matching cards
        """
        return [
            card for card in self.cards
            if any(color in card.get('colors', []) for color in colors)
        ]

    def get_card_by_name(self, name: str) -> Optional[Dict]:
        """Get a card by its name"""
        for card in self.cards:
            if card.get('name') == name:
                return card
        return None

    def add_synergy(self, card1_name: str, card2_name: str, synergy_data: Dict):
        """
        Add synergy between two cards

        Args:
            card1_name: Name of first card
            card2_name: Name of second card
            synergy_data: Dictionary containing synergy information
        """
        # Create unique synergy key
        key = f"{card1_name}||{card2_name}"

        if key not in self.synergies:
            self.synergies[key] = []

        self.synergies[key].append(synergy_data)

    def get_synergies_for_card(self, card_name: str) -> List[Dict]:
        """
        Get all synergies involving a specific card

        Args:
            card_name: Name of the card

        Returns:
            List of synergy dictionaries
        """
        synergies = []

        for key, synergy_list in self.synergies.items():
            card1, card2 = key.split('||')
            if card_name in (card1, card2):
                for synergy in synergy_list:
                    synergies.append({
                        'card1': card1,
                        'card2': card2,
                        'synergy': synergy
                    })

        return synergies

    def get_deck_statistics(self) -> Dict:
        """
        Calculate deck statistics

        Returns:
            Dictionary with deck statistics
        """
        total_cards = len(self.cards)
        total_synergies = len(self.synergies)

        # Count by type
        type_counts = {}
        for card in self.cards:
            types = card.get('card_types', {}).get('main_types', [])
            for card_type in types:
                type_counts[card_type] = type_counts.get(card_type, 0) + 1

        # Count by color
        color_counts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}
        for card in self.cards:
            colors = card.get('colors', [])
            if not colors:
                color_counts['C'] += 1
            else:
                for color in colors:
                    if color in color_counts:
                        color_counts[color] += 1

        # Average CMC
        cmcs = [card.get('cmc', 0) for card in self.cards if card.get('cmc')]
        avg_cmc = sum(cmcs) / len(cmcs) if cmcs else 0

        return {
            'total_cards': total_cards,
            'total_synergies': total_synergies,
            'type_distribution': type_counts,
            'color_distribution': color_counts,
            'average_cmc': round(avg_cmc, 2),
            'commanders': [c.get('name') for c in self.get_commanders()]
        }
