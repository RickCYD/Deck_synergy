"""
Card Importance and Ranking Utilities
Calculate card importance using various centrality metrics
"""

from typing import Dict, List, Tuple


def calculate_weighted_degree_centrality(deck_data: Dict) -> Dict[str, float]:
    """
    Calculate weighted degree centrality for all cards in the deck.

    This measures the total synergy strength connected to each card.
    Higher values = more important/central cards.

    Args:
        deck_data: Dictionary containing deck information with synergies

    Returns:
        Dictionary mapping card names to their centrality scores
        {
            'Card Name': total_synergy_weight,
            ...
        }
    """
    card_scores = {}

    # Initialize all cards with 0 score
    for card in deck_data.get('cards', []):
        card_name = card.get('name')
        if card_name:
            card_scores[card_name] = 0.0

    # Sum up synergy weights for each card
    synergies = deck_data.get('synergies', {})
    for synergy_key, synergy_data in synergies.items():
        card1, card2 = synergy_key.split('||')
        weight = synergy_data.get('total_weight', 0)

        if card1 in card_scores:
            card_scores[card1] += weight
        if card2 in card_scores:
            card_scores[card2] += weight

    return card_scores


def get_top_cards(card_scores: Dict[str, float], top_n: int = 10) -> List[Tuple[str, float]]:
    """
    Get the top N cards by centrality score.

    Args:
        card_scores: Dictionary of card names to scores
        top_n: Number of top cards to return

    Returns:
        List of (card_name, score) tuples, sorted by score descending
    """
    sorted_cards = sorted(
        card_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_cards[:top_n]


def get_card_rank(card_name: str, card_scores: Dict[str, float]) -> int:
    """
    Get the rank of a specific card (1 = highest importance).

    Args:
        card_name: Name of the card
        card_scores: Dictionary of card names to scores

    Returns:
        Rank (1-indexed), or 0 if card not found
    """
    sorted_cards = sorted(
        card_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for rank, (name, score) in enumerate(sorted_cards, 1):
        if name == card_name:
            return rank

    return 0


def calculate_connection_counts(deck_data: Dict) -> Dict[str, int]:
    """
    Calculate the number of synergy connections for each card.

    Args:
        deck_data: Dictionary containing deck information with synergies

    Returns:
        Dictionary mapping card names to connection counts
    """
    connection_counts = {}

    # Initialize all cards with 0 connections
    for card in deck_data.get('cards', []):
        card_name = card.get('name')
        if card_name:
            connection_counts[card_name] = 0

    # Count connections
    synergies = deck_data.get('synergies', {})
    for synergy_key in synergies.keys():
        card1, card2 = synergy_key.split('||')

        if card1 in connection_counts:
            connection_counts[card1] += 1
        if card2 in connection_counts:
            connection_counts[card2] += 1

    return connection_counts


def calculate_average_synergy_strength(deck_data: Dict) -> Dict[str, float]:
    """
    Calculate the average synergy strength for each card's connections.

    High average = card has consistently strong synergies
    High total but low average = many weak synergies

    Args:
        deck_data: Dictionary containing deck information with synergies

    Returns:
        Dictionary mapping card names to average synergy strength
    """
    card_totals = {}
    card_counts = {}

    # Initialize
    for card in deck_data.get('cards', []):
        card_name = card.get('name')
        if card_name:
            card_totals[card_name] = 0.0
            card_counts[card_name] = 0

    # Sum and count
    synergies = deck_data.get('synergies', {})
    for synergy_key, synergy_data in synergies.items():
        card1, card2 = synergy_key.split('||')
        weight = synergy_data.get('total_weight', 0)

        if card1 in card_totals:
            card_totals[card1] += weight
            card_counts[card1] += 1
        if card2 in card_totals:
            card_totals[card2] += weight
            card_counts[card2] += 1

    # Calculate averages
    averages = {}
    for card_name in card_totals.keys():
        count = card_counts[card_name]
        if count > 0:
            averages[card_name] = card_totals[card_name] / count
        else:
            averages[card_name] = 0.0

    return averages


def categorize_card_importance(score: float, max_score: float) -> str:
    """
    Categorize a card's importance based on its score.

    Args:
        score: Card's centrality score
        max_score: Highest score in the deck

    Returns:
        Category string: 'essential', 'high', 'medium', 'low', or 'minimal'
    """
    if max_score == 0:
        return 'minimal'

    ratio = score / max_score

    if ratio >= 0.7:
        return 'essential'
    elif ratio >= 0.4:
        return 'high'
    elif ratio >= 0.2:
        return 'medium'
    elif ratio >= 0.1:
        return 'low'
    else:
        return 'minimal'


def get_importance_color(category: str) -> str:
    """
    Get a color code for an importance category.

    Args:
        category: Importance category

    Returns:
        Hex color code
    """
    colors = {
        'essential': '#e74c3c',  # Red
        'high': '#e67e22',       # Orange
        'medium': '#f39c12',     # Yellow
        'low': '#3498db',        # Blue
        'minimal': '#95a5a6'     # Gray
    }

    return colors.get(category, '#95a5a6')


def get_card_statistics(deck_data: Dict, card_name: str) -> Dict:
    """
    Get comprehensive statistics for a specific card.

    Args:
        deck_data: Dictionary containing deck information
        card_name: Name of the card

    Returns:
        Dictionary with card statistics
    """
    card_scores = calculate_weighted_degree_centrality(deck_data)
    connection_counts = calculate_connection_counts(deck_data)
    avg_strengths = calculate_average_synergy_strength(deck_data)

    score = card_scores.get(card_name, 0)
    max_score = max(card_scores.values()) if card_scores else 0

    return {
        'name': card_name,
        'total_synergy': score,
        'rank': get_card_rank(card_name, card_scores),
        'connection_count': connection_counts.get(card_name, 0),
        'average_synergy': avg_strengths.get(card_name, 0),
        'importance_category': categorize_card_importance(score, max_score),
        'importance_color': get_importance_color(categorize_card_importance(score, max_score))
    }


def get_deck_rankings_summary(deck_data: Dict, top_n: int = 10) -> Dict:
    """
    Get a comprehensive ranking summary for the deck.

    Args:
        deck_data: Dictionary containing deck information
        top_n: Number of top cards to include

    Returns:
        Dictionary with ranking information
    """
    card_scores = calculate_weighted_degree_centrality(deck_data)
    top_cards = get_top_cards(card_scores, top_n)
    connection_counts = calculate_connection_counts(deck_data)
    avg_strengths = calculate_average_synergy_strength(deck_data)

    max_score = max(card_scores.values()) if card_scores else 0

    # Build detailed top cards list
    top_cards_detailed = []
    for rank, (card_name, score) in enumerate(top_cards, 1):
        top_cards_detailed.append({
            'rank': rank,
            'name': card_name,
            'total_synergy': round(score, 2),
            'connections': connection_counts.get(card_name, 0),
            'avg_synergy': round(avg_strengths.get(card_name, 0), 2),
            'importance': categorize_card_importance(score, max_score),
            'color': get_importance_color(categorize_card_importance(score, max_score))
        })

    return {
        'top_cards': top_cards_detailed,
        'total_cards': len(card_scores),
        'max_synergy': round(max_score, 2),
        'avg_synergy': round(sum(card_scores.values()) / len(card_scores), 2) if card_scores else 0
    }
