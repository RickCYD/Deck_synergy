"""
API client for Commander Spellbook combo database
https://backend.commanderspellbook.com/
"""
import requests
import json
from typing import List, Dict, Optional
from functools import lru_cache
import logging

from src.models.combo import Combo

logger = logging.getLogger(__name__)


class CommanderSpellbookAPI:
    """Client for accessing Commander Spellbook API"""

    BASE_URL = "https://backend.commanderspellbook.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DeckSynergyApp/1.0',
            'Accept': 'application/json'
        })

    def get_variants(self, limit: int = 100, offset: int = 0) -> Dict:
        """
        Get combo variants from the API

        Args:
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            API response containing combo variants
        """
        try:
            url = f"{self.BASE_URL}/variants/"
            params = {
                'limit': limit,
                'offset': offset
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching variants from Commander Spellbook: {e}")
            return {'count': 0, 'results': []}

    def find_my_combos(self, card_names: List[str]) -> List[Combo]:
        """
        Find combos that can be made with the given cards

        Args:
            card_names: List of card names to search for

        Returns:
            List of Combo objects
        """
        try:
            url = f"{self.BASE_URL}/find-my-combos/"

            # API expects card names separated by newlines
            data = {
                'cards': '\n'.join(card_names)
            }

            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Parse combos from response
            combos = []
            for combo_data in result.get('results', []):
                try:
                    combo = Combo.from_spellbook_data(combo_data)
                    combos.append(combo)
                except Exception as e:
                    logger.warning(f"Error parsing combo data: {e}")
                    continue

            logger.info(f"Found {len(combos)} combos for {len(card_names)} cards")
            return combos

        except requests.exceptions.RequestException as e:
            logger.error(f"Error finding combos: {e}")
            return []

    @lru_cache(maxsize=1000)
    def get_combos_for_card(self, card_name: str) -> List[Dict]:
        """
        Get all combos containing a specific card (cached)

        Args:
            card_name: Name of the card to search for

        Returns:
            List of combo data dictionaries
        """
        try:
            url = f"{self.BASE_URL}/variants/"
            params = {
                'cards': card_name,
                'limit': 100
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('results', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching combos for card {card_name}: {e}")
            return []

    def search_combos(
        self,
        cards: Optional[List[str]] = None,
        color_identity: Optional[str] = None,
        results: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Combo]:
        """
        Search for combos with specific criteria

        Args:
            cards: List of card names that must be in the combo
            color_identity: Color identity filter (e.g., 'UBR')
            results: List of results the combo must produce
            prerequisites: List of prerequisites required
            limit: Maximum number of results

        Returns:
            List of Combo objects
        """
        try:
            url = f"{self.BASE_URL}/variants/"
            params = {'limit': limit}

            if cards:
                params['cards'] = ','.join(cards)
            if color_identity:
                params['colorIdentity'] = color_identity
            if results:
                params['results'] = ','.join(results)
            if prerequisites:
                params['prerequisites'] = ','.join(prerequisites)

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()

            combos = []
            for combo_data in result.get('results', []):
                try:
                    combo = Combo.from_spellbook_data(combo_data)
                    combos.append(combo)
                except Exception as e:
                    logger.warning(f"Error parsing combo: {e}")
                    continue

            return combos

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching combos: {e}")
            return []


# Global instance for easy access
spellbook_api = CommanderSpellbookAPI()
