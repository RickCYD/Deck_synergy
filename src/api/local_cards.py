"""
Local Card Database
Fast local lookup of card data from cards-minimal.json

This provides instant card lookups without hitting the Scryfall API,
making deck loading 25-50x faster.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class LocalCardDatabase:
    """Local card database with fast lookup"""

    def __init__(self):
        self.cards_by_name = {}
        self.loaded = False

    def load(self):
        """
        Load cards-minimal.json into memory

        Returns:
            bool: True if successful, False otherwise
        """
        if self.loaded:
            return True

        cards_file = Path(__file__).parent.parent.parent / 'data' / 'cards' / 'cards-minimal.json'

        if not cards_file.exists():
            print(f"Warning: {cards_file} not found. Local card database unavailable.")
            print("Run: python scripts/create_minimal_cards.py")
            return False

        try:
            print(f"Loading local card database from {cards_file.name}...")
            with open(cards_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)

            # Create name → card lookup dictionary
            self.cards_by_name = {card['name']: card for card in cards}
            self.loaded = True

            print(f"✅ Loaded {len(self.cards_by_name)} cards into local database")
            return True

        except Exception as e:
            print(f"Error loading local card database: {e}")
            return False

    def get_card_by_name(self, card_name: str) -> Optional[Dict]:
        """
        Get card data by name from local database

        Args:
            card_name: Name of the card

        Returns:
            Dictionary with card data, or None if not found
        """
        if not self.loaded:
            return None

        return self.cards_by_name.get(card_name)

    def has_card(self, card_name: str) -> bool:
        """Check if a card exists in local database"""
        if not self.loaded:
            return False
        return card_name in self.cards_by_name


# Global instance
_local_db = LocalCardDatabase()


def load_local_database() -> bool:
    """
    Load the local card database (call once at app startup)

    Returns:
        bool: True if successful, False otherwise
    """
    return _local_db.load()


def get_card_by_name(card_name: str) -> Optional[Dict]:
    """
    Get card data from local database

    Args:
        card_name: Name of the card

    Returns:
        Dictionary with card data, or None if not found

    Example:
        card = get_card_by_name("Sol Ring")
        if card:
            print(card['oracle_text'])
    """
    return _local_db.get_card_by_name(card_name)


def has_card(card_name: str) -> bool:
    """
    Check if card exists in local database

    Args:
        card_name: Name of the card

    Returns:
        bool: True if card exists locally
    """
    return _local_db.has_card(card_name)


def is_loaded() -> bool:
    """Check if local database is loaded"""
    return _local_db.loaded
