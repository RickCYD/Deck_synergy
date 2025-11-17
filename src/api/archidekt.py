"""
Archidekt API Integration
Fetches deck data from Archidekt.com
"""

import requests
import re
from typing import Dict, List


def extract_deck_id(url: str) -> str:
    """
    Extract deck ID from Archidekt URL

    Args:
        url: Archidekt deck URL (e.g., https://archidekt.com/decks/12345)

    Returns:
        Deck ID as string

    Raises:
        ValueError: If URL format is invalid
    """
    # Match various Archidekt URL formats
    patterns = [
        r'archidekt\.com/decks/(\d+)',
        r'archidekt\.com/decks/view/(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Invalid Archidekt URL format: {url}")


def fetch_deck_from_archidekt(url: str) -> Dict:
    """
    Fetch deck data from Archidekt API

    Args:
        url: Archidekt deck URL

    Returns:
        Dictionary containing deck information:
        {
            'id': deck_id,
            'name': deck_name,
            'cards': [
                {
                    'name': card_name,
                    'quantity': quantity,
                    'categories': [category_list],
                    'is_commander': bool
                },
                ...
            ]
        }

    Raises:
        Exception: If API request fails
    """
    try:
        # Extract deck ID
        deck_id = extract_deck_id(url)

        # Create a session for better compatibility
        session = requests.Session()

        # Headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': f'https://archidekt.com/decks/{deck_id}/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        session.headers.update(headers)

        # Try different API endpoint formats
        api_urls = [
            f"https://archidekt.com/api/decks/{deck_id}/",
            f"https://archidekt.com/api/decks/{deck_id}/small/",
            f"https://www.archidekt.com/api/decks/{deck_id}/",
        ]

        response = None
        last_error = None

        for api_url in api_urls:
            try:
                response = session.get(api_url, timeout=30)
                response.raise_for_status()
                break  # Success, exit loop
            except requests.RequestException as e:
                last_error = e
                continue

        if response is None or response.status_code != 200:
            raise last_error or Exception("All API endpoint attempts failed")

        data = response.json()

        # Parse deck information
        deck_name = data.get('name', f'Deck_{deck_id}')
        cards_data = data.get('cards', [])

        # Process cards
        cards = []
        for card_entry in cards_data:
            card_info = card_entry.get('card', {})

            card = {
                'name': card_info.get('oracleCard', {}).get('name', 'Unknown'),
                'quantity': card_entry.get('quantity', 1),
                'categories': card_entry.get('categories', []),
                'is_commander': 'Commander' in card_entry.get('categories', []),
                # Store additional metadata if available
                'archidekt_id': card_info.get('uid'),
                'color_identity': card_info.get('oracleCard', {}).get('colorIdentity', [])
            }

            cards.append(card)

        return {
            'id': deck_id,
            'name': deck_name,
            'cards': cards
        }

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch deck from Archidekt: {str(e)}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Failed to parse Archidekt response: {str(e)}")


def get_deck_categories(deck_data: Dict) -> List[str]:
    """
    Extract all unique categories from a deck

    Args:
        deck_data: Deck dictionary from fetch_deck_from_archidekt

    Returns:
        List of unique category names
    """
    categories = set()
    for card in deck_data.get('cards', []):
        categories.update(card.get('categories', []))

    return sorted(list(categories))
