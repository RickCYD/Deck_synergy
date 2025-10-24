"""
Scryfall API Integration
Fetches detailed card information from Scryfall.com
"""

import requests
import time
from typing import Dict, List


class ScryfallAPI:
    """Scryfall API client with rate limiting"""

    BASE_URL = "https://api.scryfall.com"
    RATE_LIMIT_DELAY = 0.1  # 100ms between requests (Scryfall requirement)

    def __init__(self):
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed Scryfall's rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last_request)

        self.last_request_time = time.time()

    def get_card_by_name(self, card_name: str) -> Dict:
        """
        Fetch card details by name

        Args:
            card_name: Name of the card

        Returns:
            Dictionary containing all card information from Scryfall

        Raises:
            Exception: If API request fails
        """
        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/cards/named"
            params = {'exact': card_name}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            # Try fuzzy search as fallback
            return self._fuzzy_search(card_name)

    def _fuzzy_search(self, card_name: str) -> Dict:
        """
        Fallback: Use fuzzy search if exact name fails

        Args:
            card_name: Name of the card

        Returns:
            Dictionary containing card information
        """
        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/cards/named"
            params = {'fuzzy': card_name}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch card '{card_name}' from Scryfall: {str(e)}")


def fetch_card_details(cards: List[Dict]) -> List[Dict]:
    """
    Fetch detailed information for a list of cards from Scryfall

    Args:
        cards: List of card dictionaries from Archidekt (must have 'name' field)

    Returns:
        List of cards with complete Scryfall data merged in

    Example:
        Each card will have fields like:
        - name: Card name
        - mana_cost: Mana cost string
        - cmc: Converted mana cost
        - type_line: Full type line
        - oracle_text: Card text
        - colors: Color array
        - color_identity: Color identity
        - keywords: Keyword abilities
        - power, toughness: P/T for creatures
        - loyalty: Loyalty for planeswalkers
        - image_uris: Image URLs
        - prices: Card prices
        - legalities: Format legalities
    """
    api = ScryfallAPI()
    enriched_cards = []

    total_cards = len(cards)
    print(f"Fetching details for {total_cards} cards from Scryfall...")

    for idx, card in enumerate(cards, 1):
        card_name = card.get('name')

        if not card_name:
            print(f"Warning: Card without name found, skipping")
            continue

        try:
            # Fetch full card data from Scryfall
            scryfall_data = api.get_card_by_name(card_name)

            # Merge Archidekt data with Scryfall data
            enriched_card = {
                # Basic info
                'name': scryfall_data.get('name'),
                'scryfall_id': scryfall_data.get('id'),

                # From Archidekt
                'quantity': card.get('quantity', 1),
                'categories': card.get('categories', []),
                'is_commander': card.get('is_commander', False),

                # Mana and costs
                'mana_cost': scryfall_data.get('mana_cost', ''),
                'cmc': scryfall_data.get('cmc', 0),
                'colors': scryfall_data.get('colors', []),
                'color_identity': scryfall_data.get('color_identity', []),

                # Type information
                'type_line': scryfall_data.get('type_line', ''),
                'card_types': parse_type_line(scryfall_data.get('type_line', '')),
                'supertypes': scryfall_data.get('supertypes', []),
                'subtypes': scryfall_data.get('subtypes', []),

                # Card text and abilities
                'oracle_text': scryfall_data.get('oracle_text', ''),
                'keywords': scryfall_data.get('keywords', []),

                # Stats
                'power': scryfall_data.get('power'),
                'toughness': scryfall_data.get('toughness'),
                'loyalty': scryfall_data.get('loyalty'),

                # Additional properties
                'rarity': scryfall_data.get('rarity'),
                'set': scryfall_data.get('set'),
                'set_name': scryfall_data.get('set_name'),

                # Images
                'image_uris': scryfall_data.get('image_uris', {}),

                # Prices and legalities
                'prices': scryfall_data.get('prices', {}),
                'legalities': scryfall_data.get('legalities', {}),

                # Card faces (for double-faced cards)
                'card_faces': scryfall_data.get('card_faces', []),

                # Additional metadata
                'edhrec_rank': scryfall_data.get('edhrec_rank'),
                'produced_mana': scryfall_data.get('produced_mana', []),

                # Raw Scryfall data for reference
                '_scryfall_raw': scryfall_data
            }

            enriched_cards.append(enriched_card)
            print(f"  [{idx}/{total_cards}] Fetched: {card_name}")

        except Exception as e:
            print(f"  [{idx}/{total_cards}] Error fetching {card_name}: {str(e)}")
            # Add card with basic info even if Scryfall fetch fails
            enriched_cards.append({
                'name': card_name,
                'quantity': card.get('quantity', 1),
                'categories': card.get('categories', []),
                'is_commander': card.get('is_commander', False),
                'error': str(e)
            })

    print(f"Successfully fetched details for {len(enriched_cards)} cards")
    return enriched_cards


def parse_type_line(type_line: str) -> Dict[str, List[str]]:
    """
    Parse a type line into components

    Args:
        type_line: Full type line (e.g., "Legendary Creature — Human Wizard")

    Returns:
        Dictionary with:
        {
            'supertypes': [...],
            'main_types': [...],
            'subtypes': [...]
        }
    """
    SUPERTYPES = ['Legendary', 'Basic', 'Snow', 'World', 'Ongoing']
    MAIN_TYPES = ['Artifact', 'Creature', 'Enchantment', 'Instant', 'Land',
                  'Planeswalker', 'Sorcery', 'Tribal', 'Battle']

    supertypes = []
    main_types = []
    subtypes = []

    # Split by " — " to separate main types from subtypes
    parts = type_line.split(' — ')
    main_part = parts[0].strip()
    subtype_part = parts[1].strip() if len(parts) > 1 else ''

    # Parse main part
    for word in main_part.split():
        if word in SUPERTYPES:
            supertypes.append(word)
        elif word in MAIN_TYPES:
            main_types.append(word)

    # Parse subtypes
    if subtype_part:
        subtypes = [st.strip() for st in subtype_part.split()]

    return {
        'supertypes': supertypes,
        'main_types': main_types,
        'subtypes': subtypes
    }


def extract_abilities_from_text(oracle_text: str) -> Dict[str, List[str]]:
    """
    Extract categorized abilities from oracle text

    Args:
        oracle_text: Card's oracle text

    Returns:
        Dictionary categorizing different types of abilities
    """
    if not oracle_text:
        return {}

    abilities = {
        'activated': [],
        'triggered': [],
        'static': [],
        'keywords': []
    }

    lines = oracle_text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Activated abilities (contain ':' before effect)
        if ':' in line and not line.startswith('('):
            abilities['activated'].append(line)

        # Triggered abilities (start with When/Whenever/At)
        elif any(line.startswith(trigger) for trigger in ['When ', 'Whenever ', 'At ']):
            abilities['triggered'].append(line)

        # Static abilities
        else:
            abilities['static'].append(line)

    return abilities
