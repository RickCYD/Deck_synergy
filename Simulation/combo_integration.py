"""
Integration layer between synergy engine combo detection and simulation AI.

This module provides functions to detect combos in a deck and attach combo
data to cards for use by the ImprovedAI during simulation.
"""

from typing import List, Dict, Any, Optional

try:
    import sys
    import os
    # Add src to path so we can import from synergy engine
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    from src.synergy_engine.combo_detector import ComboDetector
    from src.models.combo import Combo
    COMBO_DETECTION_AVAILABLE = True
except ImportError:
    COMBO_DETECTION_AVAILABLE = False
    print("Warning: Combo detection not available from synergy engine")


def detect_deck_combos(deck_cards: List[Any]) -> List[Any]:
    """
    Detect all combos present in a deck using the synergy engine.

    Args:
        deck_cards: List of Card objects from simulation

    Returns:
        List of Combo objects found in the deck
    """
    if not COMBO_DETECTION_AVAILABLE:
        return []

    try:
        # Convert simulation cards to format expected by combo detector
        card_dicts = []
        for card in deck_cards:
            card_dict = {
                'name': getattr(card, 'name', ''),
                'type': getattr(card, 'type', ''),
                'oracle_text': getattr(card, 'oracle_text', ''),
            }
            card_dicts.append(card_dict)

        # Run combo detection
        detector = ComboDetector()
        result = detector.detect_combos_in_deck(card_dicts)

        combos = result.get('combos', [])

        print(f"Combo Detection: Found {len(combos)} complete combos in deck")
        for combo in combos:
            print(f"  → {', '.join(combo.card_names)}: {combo.primary_result}")

        return combos

    except Exception as e:
        print(f"Warning: Combo detection failed: {e}")
        return []


def attach_combos_to_cards(deck_cards: List[Any], combos: List[Any]) -> None:
    """
    Attach combo data to individual cards for easy access during simulation.

    Modifies deck_cards in-place by adding a 'combos' attribute to each card.

    Args:
        deck_cards: List of Card objects from simulation
        combos: List of Combo objects detected in deck
    """
    # Build mapping of card name -> combos containing that card
    card_combo_map = {}
    for combo in combos:
        for card_name in combo.card_names:
            card_lower = card_name.lower()
            if card_lower not in card_combo_map:
                card_combo_map[card_lower] = []
            card_combo_map[card_lower].append(combo)

    # Attach to each card
    for card in deck_cards:
        card_name = getattr(card, 'name', '').lower()
        card.combos = card_combo_map.get(card_name, [])


def prepare_deck_for_simulation(deck_cards: List[Any], commander_card: Any = None) -> List[Any]:
    """
    Prepare a deck for simulation by detecting combos and attaching metadata.

    This is the main entry point for combo integration.

    Args:
        deck_cards: List of Card objects
        commander_card: Commander card (optional)

    Returns:
        List of Combo objects found
    """
    # Detect combos
    all_cards = deck_cards + ([commander_card] if commander_card else [])
    combos = detect_deck_combos(all_cards)

    # Attach combo data to cards
    attach_combos_to_cards(all_cards, combos)

    return combos


# Example usage
if __name__ == "__main__":
    # This would be used in simulate_game.py like:
    #
    # from combo_integration import prepare_deck_for_simulation
    #
    # # Before simulation
    # combos = prepare_deck_for_simulation(deck_cards, commander_card)
    #
    # # Initialize ImprovedAI with combo data
    # ai = ImprovedAI(board, deck_combos=combos)

    print("Combo integration module loaded successfully")
    print(f"Combo detection available: {COMBO_DETECTION_AVAILABLE}")
