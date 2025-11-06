"""
Advanced fuzzy search utility for card searching with multiple matching strategies.
Provides smart ranking based on multiple criteria for optimal search results.
"""

from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
import re


class CardFuzzySearcher:
    """
    Advanced fuzzy search for Magic: The Gathering cards.
    Uses multiple matching strategies to provide intelligent search results.
    """

    def __init__(self):
        self.match_threshold = 0.3  # Lower threshold to catch more potential matches

    def search(self, query: str, cards: List[Dict], limit: int = 15) -> List[Tuple[Dict, float, str]]:
        """
        Perform intelligent fuzzy search on cards.

        Args:
            query: Search query string
            cards: List of card dictionaries
            limit: Maximum number of results to return

        Returns:
            List of (card, score, match_reason) tuples sorted by score descending
        """
        if not query or not cards:
            return []

        query = query.lower().strip()
        matches = []

        for card in cards:
            score, reason = self._calculate_match_score(query, card)
            if score > 0:
                matches.append((card, score, reason))

        # Sort by score (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    def _calculate_match_score(self, query: str, card: Dict) -> Tuple[float, str]:
        """
        Calculate comprehensive match score using multiple strategies.

        Returns:
            Tuple of (score, match_reason)
        """
        card_name = card.get('name', '').lower()
        card_type = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()

        # Strategy 1: Exact match (highest priority)
        if query == card_name:
            return (1.0, 'Exact match')

        # Strategy 2: Exact word match in name
        name_words = set(card_name.split())
        query_words = set(query.split())
        if query_words.issubset(name_words):
            return (0.95, 'Exact word match')

        # Strategy 3: Name starts with query (very high priority)
        if card_name.startswith(query):
            ratio = len(query) / len(card_name)
            return (0.9 + ratio * 0.05, 'Name starts with query')

        # Strategy 4: Query is a substring of name
        if query in card_name:
            ratio = len(query) / len(card_name)
            return (0.7 + ratio * 0.2, 'Substring match')

        # Strategy 5: Fuzzy name match (using sequence matching)
        name_ratio = SequenceMatcher(None, query, card_name).ratio()
        if name_ratio >= self.match_threshold:
            return (name_ratio * 0.85, f'Fuzzy name match ({int(name_ratio*100)}%)')

        # Strategy 6: Token-based matching (handles word order differences)
        token_score = self._token_match_score(query, card_name)
        if token_score >= 0.5:
            return (token_score * 0.75, 'Token match')

        # Strategy 7: Type line match
        if query in card_type:
            type_ratio = len(query) / len(card_type)
            return (0.6 * type_ratio, 'Type match')

        # Strategy 8: Oracle text match (oracle text contains query)
        if query in oracle_text:
            # Boost score if query is a significant portion of a sentence
            oracle_ratio = min(len(query) / max(len(oracle_text), 1), 1.0)
            return (0.5 * oracle_ratio, 'Oracle text match')

        # Strategy 9: Color search (e.g., "red", "white", "blue")
        color_score = self._color_match_score(query, card)
        if color_score > 0:
            return (color_score * 0.45, 'Color match')

        # Strategy 10: Partial word matching (for typos)
        partial_score = self._partial_word_match(query, card_name)
        if partial_score >= 0.4:
            return (partial_score * 0.6, 'Partial match')

        return (0.0, 'No match')

    def _token_match_score(self, query: str, text: str) -> float:
        """
        Calculate match score based on individual tokens/words.
        Handles cases like "bolt lightning" matching "Lightning Bolt".
        """
        query_tokens = set(query.split())
        text_tokens = set(text.split())

        if not query_tokens or not text_tokens:
            return 0.0

        # Count matching tokens
        matching_tokens = query_tokens.intersection(text_tokens)

        if not matching_tokens:
            return 0.0

        # Calculate score based on proportion of matching tokens
        precision = len(matching_tokens) / len(query_tokens)
        recall = len(matching_tokens) / len(text_tokens)

        # F1 score
        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def _partial_word_match(self, query: str, text: str) -> float:
        """
        Match based on partial words (for handling typos).
        """
        query_parts = query.split()
        text_parts = text.split()

        total_score = 0.0
        for q_part in query_parts:
            max_ratio = 0.0
            for t_part in text_parts:
                ratio = SequenceMatcher(None, q_part, t_part).ratio()
                max_ratio = max(max_ratio, ratio)
            total_score += max_ratio

        return total_score / len(query_parts) if query_parts else 0.0

    def _color_match_score(self, query: str, card: Dict) -> float:
        """
        Match based on color keywords.
        """
        color_map = {
            'white': 'W',
            'blue': 'U',
            'black': 'B',
            'red': 'R',
            'green': 'G',
            'colorless': 'C',
            'w': 'W',
            'u': 'U',
            'b': 'B',
            'r': 'R',
            'g': 'G',
            'c': 'C'
        }

        query_color = color_map.get(query.lower())
        if not query_color:
            return 0.0

        card_colors = card.get('colors', [])
        card_color_identity = card.get('color_identity', [])

        if query_color in card_colors or query_color in card_color_identity:
            return 1.0

        return 0.0

    def search_by_attribute(self, attribute: str, value: str, cards: List[Dict]) -> List[Dict]:
        """
        Search cards by specific attribute.

        Args:
            attribute: Card attribute to search (e.g., 'type_line', 'colors', 'oracle_text')
            value: Value to search for
            cards: List of card dictionaries

        Returns:
            List of matching cards
        """
        value = value.lower()
        matches = []

        for card in cards:
            card_value = str(card.get(attribute, '')).lower()
            if value in card_value:
                matches.append(card)

        return matches


def format_card_colors(colors: List[str]) -> str:
    """
    Format card colors for display.
    """
    if not colors:
        return "Colorless"
    return "".join(colors)


def format_mana_cost(mana_cost: str) -> str:
    """
    Format mana cost for display.
    """
    if not mana_cost:
        return "—"
    return mana_cost
