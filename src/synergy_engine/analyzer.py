"""
Synergy Analyzer
Main module for analyzing deck synergies
"""

from typing import Dict, List, Tuple
from itertools import combinations
from .rules import ALL_RULES, clear_damage_classification_cache
from .categories import get_category_weight


def analyze_card_pair(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Analyze synergies between two cards

    Args:
        card1: First card dictionary
        card2: Second card dictionary

    Returns:
        List of detected synergies
    """
    synergies = []

    # Run all detection rules
    for rule_func in ALL_RULES:
        try:
            result = rule_func(card1, card2)
            if result:
                # Handle both old format (Optional[Dict]) and new format (List[Dict])
                if isinstance(result, list):
                    synergies.extend(result)
                elif isinstance(result, dict):
                    synergies.append(result)
        except Exception as e:
            # Log error but continue with other rules
            print(f"Error in {rule_func.__name__} for {card1.get('name')} and {card2.get('name')}: {e}")

    return synergies


def calculate_edge_weight(synergies: List[Dict]) -> float:
    """
    Calculate the total weight of an edge based on its synergies

    Args:
        synergies: List of synergy dictionaries

    Returns:
        Total weighted synergy value
    """
    if not synergies:
        return 0.0

    total_weight = 0.0

    for synergy in synergies:
        category = synergy.get('category', 'benefits')
        subcategory = synergy.get('subcategory')
        # Support both old format (value) and new format (strength)
        value = synergy.get('value') or synergy.get('strength', 1.0)

        # Get category weight multiplier
        category_weight = get_category_weight(category, subcategory)

        # Calculate weighted value
        weighted_value = value * category_weight
        total_weight += weighted_value

    return round(total_weight, 2)


def organize_synergies_by_category(synergies: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Organize synergies by their categories

    Args:
        synergies: List of synergy dictionaries

    Returns:
        Dictionary with categories as keys and lists of synergies as values
    """
    organized = {}

    for synergy in synergies:
        category = synergy.get('category', 'other')

        if category not in organized:
            organized[category] = []

        organized[category].append(synergy)

    return organized


def analyze_deck_synergies(cards: List[Dict], min_synergy_threshold: float = 0.5) -> Dict[str, Dict]:
    """
    Analyze all synergies in a deck

    Args:
        cards: List of card dictionaries
        min_synergy_threshold: Minimum synergy weight to include in results

    Returns:
        Dictionary mapping card pairs to their synergies:
        {
            'CardA||CardB': {
                'total_weight': float,
                'synergies': {
                    'category1': [synergy1, synergy2, ...],
                    'category2': [...]
                }
            }
        }
    """
    import time
    start_time = time.time()

    num_cards = len(cards)
    print(f"\nAnalyzing synergies for {num_cards} cards...")

    # Clear damage classification cache for fresh analysis
    clear_damage_classification_cache()

    synergy_dict = {}
    total_pairs = (num_cards * (num_cards - 1)) // 2
    analyzed = 0

    # For large decks, show more frequent progress updates
    progress_interval = 100 if num_cards < 100 else 500

    # Analyze all card pairs
    for card1, card2 in combinations(cards, 2):
        analyzed += 1

        if analyzed % progress_interval == 0 or analyzed == total_pairs:
            elapsed = time.time() - start_time
            pairs_per_sec = analyzed / elapsed if elapsed > 0 else 0
            remaining = (total_pairs - analyzed) / pairs_per_sec if pairs_per_sec > 0 else 0
            print(f"  Progress: {analyzed}/{total_pairs} pairs ({100*analyzed/total_pairs:.1f}%) - "
                  f"Elapsed: {elapsed:.1f}s - ETA: {remaining:.1f}s")

        # Skip if either card has errors
        if 'error' in card1 or 'error' in card2:
            continue

        # Skip land synergies - they create noise in the graph and recommendations
        # Lands have generic synergies (ramp, color fixing) that aren't strategically interesting
        card1_type = card1.get('type_line', '').lower()
        card2_type = card2.get('type_line', '').lower()

        # Skip if either card is a land (excluding MDFCs with // in type line)
        if ('//' not in card1_type and 'land' in card1_type) or \
           ('//' not in card2_type and 'land' in card2_type):
            continue

        # Detect synergies
        synergies = analyze_card_pair(card1, card2)

        if synergies:
            # Calculate total weight
            total_weight = calculate_edge_weight(synergies)

            # Only include if above threshold
            if total_weight >= min_synergy_threshold:
                # Create unique key
                key = f"{card1['name']}||{card2['name']}"

                # Organize by category
                organized_synergies = organize_synergies_by_category(synergies)

                synergy_dict[key] = {
                    'card1': card1['name'],
                    'card2': card2['name'],
                    'total_weight': total_weight,
                    'synergies': organized_synergies,
                    'synergy_count': len(synergies)
                }

    elapsed = time.time() - start_time
    print(f"  Completed in {elapsed:.1f}s ({total_pairs/elapsed:.0f} pairs/sec)")
    print(f"  Found {len(synergy_dict)} synergies above threshold ({min_synergy_threshold})")
    print(f"  Total synergy connections: {sum(s['synergy_count'] for s in synergy_dict.values())}")

    return synergy_dict


def get_top_synergies(synergy_dict: Dict, top_n: int = 10) -> List[Tuple[str, Dict]]:
    """
    Get the top N synergies by weight

    Args:
        synergy_dict: Dictionary of synergies from analyze_deck_synergies
        top_n: Number of top synergies to return

    Returns:
        List of (key, synergy_data) tuples sorted by weight
    """
    sorted_synergies = sorted(
        synergy_dict.items(),
        key=lambda x: x[1]['total_weight'],
        reverse=True
    )

    return sorted_synergies[:top_n]


def get_synergies_for_card(card_name: str, synergy_dict: Dict) -> List[Dict]:
    """
    Get all synergies involving a specific card

    Args:
        card_name: Name of the card
        synergy_dict: Dictionary of synergies from analyze_deck_synergies

    Returns:
        List of synergy dictionaries involving the card
    """
    card_synergies = []

    for key, synergy_data in synergy_dict.items():
        if card_name in key:
            card_synergies.append({
                'key': key,
                'partner': synergy_data['card2'] if synergy_data['card1'] == card_name else synergy_data['card1'],
                **synergy_data
            })

    # Sort by weight
    card_synergies.sort(key=lambda x: x['total_weight'], reverse=True)

    return card_synergies


def get_synergy_statistics(synergy_dict: Dict) -> Dict:
    """
    Calculate statistics about deck synergies

    Args:
        synergy_dict: Dictionary of synergies from analyze_deck_synergies

    Returns:
        Dictionary with synergy statistics
    """
    if not synergy_dict:
        return {
            'total_synergies': 0,
            'average_weight': 0,
            'max_weight': 0,
            'category_distribution': {}
        }

    weights = [s['total_weight'] for s in synergy_dict.values()]
    category_counts = {}

    for synergy_data in synergy_dict.values():
        for category in synergy_data['synergies'].keys():
            category_counts[category] = category_counts.get(category, 0) + 1

    return {
        'total_synergies': len(synergy_dict),
        'average_weight': round(sum(weights) / len(weights), 2),
        'max_weight': max(weights),
        'min_weight': min(weights),
        'category_distribution': category_counts,
        'total_synergy_connections': sum(s['synergy_count'] for s in synergy_dict.values())
    }
