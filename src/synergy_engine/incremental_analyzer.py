"""
Incremental Synergy Analyzer
Provides fast synergy updates when adding/removing cards without full re-analysis
"""

from typing import Dict, List
from .analyzer import analyze_card_pair


def analyze_card_addition(
    new_card: Dict,
    existing_cards: List[Dict],
    existing_synergies: Dict
) -> Dict:
    """
    Analyze synergies for a newly added card against existing deck cards

    This is much faster than full re-analysis as it only checks N pairs
    instead of N*(N-1)/2 pairs where N is the deck size.

    Args:
        new_card: The card being added to the deck
        existing_cards: List of cards already in the deck
        existing_synergies: Current synergy dictionary

    Returns:
        Dict with NEW synergies that should be added to existing_synergies
        Format: {"Card1||Card2": {"total_weight": X, "synergies_by_category": {...}, "count": N}}
    """
    new_synergies = {}
    new_card_name = new_card.get('name')

    if not new_card_name:
        return new_synergies

    # Analyze new card against each existing card
    for existing_card in existing_cards:
        existing_card_name = existing_card.get('name')

        if not existing_card_name:
            continue

        # Skip if same card (shouldn't happen but be safe)
        if new_card_name == existing_card_name:
            continue

        # Analyze the pair (both directions)
        synergies_forward = analyze_card_pair(new_card, existing_card)
        synergies_backward = analyze_card_pair(existing_card, new_card)

        # Combine synergies
        combined_synergies = synergies_forward + synergies_backward

        if combined_synergies:
            # Store with consistent ordering (alphabetical)
            card1, card2 = sorted([new_card_name, existing_card_name])
            key = f"{card1}||{card2}"

            # Calculate synergy data in same format as full analyzer
            synergies_by_category = {}
            total_weight = 0.0

            for synergy in combined_synergies:
                category = synergy.get('category', 'other')
                weight = synergy.get('weight', 1.0)
                total_weight += weight

                if category not in synergies_by_category:
                    synergies_by_category[category] = []
                synergies_by_category[category].append(synergy)

            new_synergies[key] = {
                'total_weight': total_weight,
                'synergies_by_category': synergies_by_category,
                'count': len(combined_synergies)
            }

    return new_synergies


def analyze_card_removal(
    removed_card_name: str,
    existing_synergies: Dict
) -> Dict:
    """
    Remove all synergies involving a specific card

    Args:
        removed_card_name: Name of the card being removed
        existing_synergies: Current synergy dictionary

    Returns:
        Updated synergies dict with all references to removed card deleted
    """
    updated_synergies = {}

    for key, synergy_data in existing_synergies.items():
        # Check if this synergy involves the removed card
        if removed_card_name not in key.split('||'):
            # Keep this synergy
            updated_synergies[key] = synergy_data

    return updated_synergies


def merge_synergies(
    base_synergies: Dict,
    new_synergies: Dict
) -> Dict:
    """
    Merge new synergies into base synergies dictionary

    Args:
        base_synergies: Existing synergy dict
        new_synergies: New synergies to add

    Returns:
        Merged synergy dictionary
    """
    merged = dict(base_synergies)
    merged.update(new_synergies)
    return merged


def get_synergy_delta_stats(
    old_synergies: Dict,
    new_synergies: Dict
) -> Dict:
    """
    Calculate statistics about synergy changes

    Args:
        old_synergies: Synergy dict before change
        new_synergies: Synergy dict after change

    Returns:
        Dict with stats: {
            'synergies_added': int,
            'synergies_removed': int,
            'synergies_net_change': int,
            'weight_added': float,
            'weight_removed': float,
            'weight_net_change': float
        }
    """
    old_keys = set(old_synergies.keys())
    new_keys = set(new_synergies.keys())

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    weight_added = sum(new_synergies[k]['total_weight'] for k in added_keys)
    weight_removed = sum(old_synergies[k]['total_weight'] for k in removed_keys)

    return {
        'synergies_added': len(added_keys),
        'synergies_removed': len(removed_keys),
        'synergies_net_change': len(added_keys) - len(removed_keys),
        'weight_added': weight_added,
        'weight_removed': weight_removed,
        'weight_net_change': weight_added - weight_removed
    }
