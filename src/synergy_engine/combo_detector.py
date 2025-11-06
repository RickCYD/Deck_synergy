"""
Real combo detection using Commander Spellbook database
"""
from typing import List, Dict, Set, Tuple, Optional
import logging
from collections import defaultdict

from src.models.combo import Combo
from src.api.commander_spellbook import spellbook_api

logger = logging.getLogger(__name__)


class ComboDetector:
    """Detects real combos in a deck using Commander Spellbook data"""

    def __init__(self):
        self.combo_cache: Dict[str, List[Combo]] = {}

    def detect_combos_in_deck(self, deck_cards: List[Dict]) -> Dict[str, any]:
        """
        Detect all combos present in a deck

        Args:
            deck_cards: List of card dictionaries with 'name' field

        Returns:
            Dictionary containing:
                - combos: List of complete combos found
                - near_combos: List of combos missing 1-2 cards
                - combo_pieces: Dict mapping card names to combos they're in
        """
        card_names = [card.get('name', '') for card in deck_cards if card.get('name')]

        if not card_names:
            return {
                'combos': [],
                'near_combos': [],
                'combo_pieces': {}
            }

        logger.info(f"Searching for combos in deck with {len(card_names)} cards")

        # Query Commander Spellbook API
        all_combos = spellbook_api.find_my_combos(card_names)

        # Separate complete combos from near-combos
        complete_combos = []
        near_combos = []

        for combo in all_combos:
            missing_cards = combo.get_missing_cards(card_names)

            if not missing_cards:
                # Complete combo found!
                complete_combos.append(combo)
                logger.info(f"Found complete combo: {combo.card_names} -> {combo.primary_result}")
            elif len(missing_cards) <= 2:
                # Near combo (missing 1-2 cards)
                near_combos.append({
                    'combo': combo,
                    'missing': missing_cards
                })
                logger.debug(f"Near combo: {combo.card_names} (missing: {missing_cards})")

        # Build mapping of cards to combos
        combo_pieces = defaultdict(list)
        for combo in complete_combos:
            for card in combo.cards:
                combo_pieces[card.name.lower()].append(combo)

        return {
            'combos': complete_combos,
            'near_combos': near_combos,
            'combo_pieces': dict(combo_pieces)
        }

    def get_combo_synergies(self, deck_cards: List[Dict]) -> Dict[str, Dict]:
        """
        Generate synergy edges for combos in the deck

        This integrates with the existing synergy system by creating
        high-strength synergy edges between combo pieces.

        Args:
            deck_cards: List of card dictionaries

        Returns:
            Dictionary mapping "Card1||Card2" to synergy data
        """
        detection_result = self.detect_combos_in_deck(deck_cards)
        combos = detection_result['combos']

        synergy_edges = {}

        for combo in combos:
            # Create edges between all pairs of cards in the combo
            card_names = combo.card_names

            for i, card1 in enumerate(card_names):
                for card2 in card_names[i + 1:]:
                    edge_key = f"{card1}||{card2}"

                    # Create a special synergy for this combo
                    synergy = {
                        'name': 'Verified Combo',
                        'description': self._format_combo_description(combo),
                        'value': 10.0,  # Very high value for verified combos
                        'category': 'combo',
                        'subcategory': 'verified_combo',
                        'combo_id': combo.id,
                        'combo_permalink': combo.permalink,
                        'combo_steps': combo.steps,
                        'combo_results': combo.results,
                        'combo_prerequisites': combo.prerequisites,
                        'combo_card_count': combo.num_cards,
                        'combo_all_pieces': card_names
                    }

                    # If edge already exists, add to it
                    if edge_key in synergy_edges:
                        synergy_edges[edge_key]['synergies'].append(synergy)
                    else:
                        synergy_edges[edge_key] = {
                            'card1': card1,
                            'card2': card2,
                            'total_weight': 10.0,  # High weight for combos
                            'synergies': [synergy],
                            'synergy_count': 1
                        }

        return synergy_edges

    def _format_combo_description(self, combo: Combo) -> str:
        """
        Format a combo into a readable description

        Args:
            combo: The Combo object

        Returns:
            Formatted description string
        """
        parts = []

        # List all cards
        card_list = ", ".join(combo.card_names)
        parts.append(f"Cards: {card_list}")

        # Primary result
        if combo.results:
            parts.append(f"Result: {combo.primary_result}")

        # Prerequisites if any
        if combo.prerequisites:
            prereqs = ", ".join(combo.prerequisites[:2])  # Show first 2
            if len(combo.prerequisites) > 2:
                prereqs += f" (+{len(combo.prerequisites) - 2} more)"
            parts.append(f"Requires: {prereqs}")

        return " | ".join(parts)

    def get_combo_suggestions(self, deck_cards: List[Dict], max_missing: int = 1) -> List[Dict]:
        """
        Get suggestions for cards that would complete near-combos

        Args:
            deck_cards: List of card dictionaries
            max_missing: Maximum number of missing cards to consider

        Returns:
            List of suggestions with combo information
        """
        detection_result = self.detect_combos_in_deck(deck_cards)
        near_combos = detection_result['near_combos']

        suggestions = []
        card_frequencies = defaultdict(int)

        # Count how many combos each missing card would complete
        for near_combo_data in near_combos:
            combo = near_combo_data['combo']
            missing = near_combo_data['missing']

            if len(missing) <= max_missing:
                for card_name in missing:
                    card_frequencies[card_name] += 1
                    suggestions.append({
                        'card_name': card_name,
                        'combo': combo,
                        'missing_count': len(missing),
                        'cards_in_deck': [c for c in combo.card_names if c not in missing],
                        'would_complete': True
                    })

        # Sort by frequency (cards that complete multiple combos first)
        suggestions.sort(key=lambda x: (
            -card_frequencies[x['card_name']],
            x['missing_count']
        ))

        return suggestions

    def analyze_combo_card_pairs(self, deck_cards: List[Dict]) -> List[Tuple[str, str, List[Combo]]]:
        """
        Analyze which pairs of cards in the deck participate in combos together

        Args:
            deck_cards: List of card dictionaries

        Returns:
            List of (card1, card2, [combos]) tuples
        """
        detection_result = self.detect_combos_in_deck(deck_cards)
        combos = detection_result['combos']

        # Build a map of card pairs to combos
        pair_combos = defaultdict(list)

        for combo in combos:
            card_names = combo.card_names
            # Generate all pairs
            for i, card1 in enumerate(card_names):
                for card2 in card_names[i + 1:]:
                    # Normalize pair order
                    pair = tuple(sorted([card1.lower(), card2.lower()]))
                    pair_combos[pair].append(combo)

        # Convert to list format
        result = []
        for (card1, card2), combo_list in pair_combos.items():
            result.append((card1, card2, combo_list))

        # Sort by number of combos (most combos first)
        result.sort(key=lambda x: -len(x[2]))

        return result


# Global instance
combo_detector = ComboDetector()
