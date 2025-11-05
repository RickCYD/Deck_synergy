"""
Embedding-based Synergy Analyzer
Uses semantic embeddings to calculate card synergies based on vector similarity
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


class EmbeddingAnalyzer:
    """
    Analyzes card synergies using pre-computed embeddings

    Uses cosine similarity between card embeddings to determine
    semantic relationships and synergies
    """

    def __init__(self):
        self.embeddings = {}  # card_name -> embedding vector
        self.similarities = {}  # card_name -> list of {card, similarity}
        self.card_texts = {}  # card_name -> text representation
        self.metadata = {}
        self.loaded = False

    def load(self) -> bool:
        """
        Load pre-computed embeddings from JSON file

        Returns:
            bool: True if successful
        """
        if self.loaded:
            return True

        embeddings_file = Path(__file__).parent.parent.parent / 'data' / 'cards' / 'card-embeddings.json'

        if not embeddings_file.exists():
            print(f"Warning: {embeddings_file} not found. Embedding analyzer unavailable.")
            print("Run: python scripts/generate_embeddings.py")
            return False

        try:
            print(f"Loading embeddings from {embeddings_file.name}...")
            with open(embeddings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.metadata = data.get('metadata', {})

            # Build lookup dictionaries
            for item in data.get('embeddings', []):
                card_name = item['card_name']
                self.embeddings[card_name] = item['embedding']
                self.card_texts[card_name] = item['text']

            self.similarities = data.get('similarities', {})

            self.loaded = True
            print(f"✅ Loaded {len(self.embeddings)} card embeddings")
            print(f"   Model: {self.metadata.get('model', 'unknown')}")
            print(f"   Dimensions: {self.metadata.get('embedding_dimensions', 0)}")
            return True

        except Exception as e:
            print(f"Error loading embeddings: {e}")
            return False

    def get_similar_cards(self, card_name: str, limit: int = 10) -> List[Dict]:
        """
        Get most similar cards to a given card

        Args:
            card_name: Name of the card
            limit: Number of similar cards to return

        Returns:
            List of dicts with 'card' and 'similarity' keys
        """
        if not self.loaded:
            if not self.load():
                return []

        if card_name not in self.similarities:
            return []

        return self.similarities[card_name][:limit]

    def get_deck_recommendations(
        self,
        deck_cards: List[Dict],
        available_cards: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get card recommendations based on embedding similarity

        Args:
            deck_cards: List of cards currently in deck
            available_cards: Optional list of card names to consider (if None, use all)
            limit: Number of recommendations to return

        Returns:
            List of recommended cards with similarity scores
        """
        if not self.loaded:
            if not self.load():
                return []

        # Get deck card names
        deck_card_names = {card['name'] for card in deck_cards if card.get('name')}

        # Calculate average similarity for each candidate card
        candidate_scores = {}

        # If no available cards specified, use all cards in embeddings
        if available_cards is None:
            available_cards = list(self.embeddings.keys())

        for candidate in available_cards:
            # Skip cards already in deck
            if candidate in deck_card_names:
                continue

            # Skip if we don't have embeddings for this card
            if candidate not in self.similarities:
                continue

            # Calculate average similarity to all cards in deck
            total_similarity = 0.0
            count = 0

            for deck_card in deck_card_names:
                # Find similarity between candidate and deck card
                if deck_card in self.similarities[candidate]:
                    # Find the similarity score
                    for sim_item in self.similarities[candidate]:
                        if sim_item['card'] == deck_card:
                            total_similarity += sim_item['similarity']
                            count += 1
                            break

            if count > 0:
                avg_similarity = total_similarity / count
                candidate_scores[candidate] = avg_similarity

        # Sort by average similarity (highest first)
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        # Format results
        recommendations = []
        for card_name, score in sorted_candidates:
            # Find top synergies with deck cards
            top_synergies = []
            for deck_card in deck_card_names:
                for sim_item in self.similarities.get(card_name, []):
                    if sim_item['card'] == deck_card:
                        top_synergies.append({
                            'with': deck_card,
                            'similarity': sim_item['similarity']
                        })
                        break

            # Sort and take top 3
            top_synergies.sort(key=lambda x: x['similarity'], reverse=True)

            recommendations.append({
                'name': card_name,
                'average_similarity': round(score, 4),
                'top_synergies': top_synergies[:3]
            })

        return recommendations

    def score_deck_cards(self, deck_cards: List[Dict]) -> List[Dict]:
        """
        Score each card in the deck based on similarity to other deck cards

        Args:
            deck_cards: List of cards in the deck

        Returns:
            List of cards with similarity scores (sorted lowest to highest)
        """
        if not self.loaded:
            if not self.load():
                return []

        scored_cards = []

        for i, card in enumerate(deck_cards):
            card_name = card.get('name')

            if not card_name or card_name not in self.embeddings:
                continue

            # Calculate average similarity to all other cards in deck
            total_similarity = 0.0
            count = 0
            top_connections = []

            for j, other_card in enumerate(deck_cards):
                if i == j:
                    continue

                other_name = other_card.get('name')
                if not other_name or other_name not in self.similarities.get(card_name, []):
                    continue

                # Find similarity
                for sim_item in self.similarities[card_name]:
                    if sim_item['card'] == other_name:
                        similarity = sim_item['similarity']
                        total_similarity += similarity
                        count += 1
                        top_connections.append({
                            'card': other_name,
                            'similarity': similarity
                        })
                        break

            if count > 0:
                avg_similarity = total_similarity / count

                # Sort top connections
                top_connections.sort(key=lambda x: x['similarity'], reverse=True)

                scored_cards.append({
                    'name': card_name,
                    'synergy_score': round(avg_similarity, 4),
                    'connections': count,
                    'top_connections': top_connections[:5]
                })

        # Sort by synergy score (lowest first = candidates for cutting)
        scored_cards.sort(key=lambda x: x['synergy_score'])

        return scored_cards

    def analyze_deck_synergies_embedding(
        self,
        deck_cards: List[Dict],
        min_similarity: float = 0.5
    ) -> Dict[str, Dict]:
        """
        Analyze synergies between deck cards using embeddings

        Args:
            deck_cards: List of cards in the deck
            min_similarity: Minimum similarity threshold

        Returns:
            Dictionary mapping card pairs to similarity data
        """
        if not self.loaded:
            if not self.load():
                return {}

        synergies = {}

        # Get all deck card names
        deck_card_names = [card['name'] for card in deck_cards if card.get('name')]

        # Compare all pairs
        for i, card1_name in enumerate(deck_card_names):
            if card1_name not in self.similarities:
                continue

            for card2_name in deck_card_names[i+1:]:
                # Find similarity between card1 and card2
                similarity = 0.0

                for sim_item in self.similarities[card1_name]:
                    if sim_item['card'] == card2_name:
                        similarity = sim_item['similarity']
                        break

                # Only include if above threshold
                if similarity >= min_similarity:
                    key = f"{card1_name}||{card2_name}"

                    synergies[key] = {
                        'card1': card1_name,
                        'card2': card2_name,
                        'similarity': round(similarity, 4),
                        'total_weight': round(similarity * 10, 2)  # Scale for graph display
                    }

        return synergies

    def build_embedding_graph_elements(
        self,
        deck_cards: List[Dict],
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Build graph elements (nodes and edges) based on embedding similarities

        Args:
            deck_cards: List of cards in the deck
            min_similarity: Minimum similarity for creating edges

        Returns:
            List of Cytoscape elements
        """
        if not self.loaded:
            if not self.load():
                return []

        elements = []

        # Create nodes for each card (reuse existing node structure)
        from src.utils.graph_builder import create_card_node

        for card in deck_cards:
            if not card.get('name'):
                continue

            node = create_card_node(card)
            elements.append(node)

        # Create edges based on similarity
        synergies = self.analyze_deck_synergies_embedding(deck_cards, min_similarity)

        for key, synergy_data in synergies.items():
            card1 = synergy_data['card1']
            card2 = synergy_data['card2']

            edge_id = f"{card1}_{card2}".replace(' ', '_').replace(',', '').replace("'", '')

            edge = {
                'data': {
                    'id': edge_id,
                    'source': card1,
                    'target': card2,
                    'weight': synergy_data['total_weight'],
                    'similarity': synergy_data['similarity'],
                    'synergy_type': 'embedding'
                },
                'classes': 'embedding-edge'
            }

            elements.append(edge)

        return elements

    def get_top_synergies(
        self,
        deck_cards: List[Dict],
        top_n: int = 10
    ) -> List[Tuple[str, str, float]]:
        """
        Get top N card pairs with highest similarity in deck

        Args:
            deck_cards: List of cards in deck
            top_n: Number of top pairs to return

        Returns:
            List of tuples (card1, card2, similarity)
        """
        synergies = self.analyze_deck_synergies_embedding(deck_cards, min_similarity=0.0)

        # Sort by similarity
        sorted_synergies = sorted(
            [(v['card1'], v['card2'], v['similarity']) for v in synergies.values()],
            key=lambda x: x[2],
            reverse=True
        )

        return sorted_synergies[:top_n]


# Global instance
_embedding_analyzer = EmbeddingAnalyzer()


def load_embedding_analyzer() -> bool:
    """Load the embedding analyzer (call once at app startup)"""
    return _embedding_analyzer.load()


def get_embedding_recommendations(
    deck_cards: List[Dict],
    available_cards: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict]:
    """Get card recommendations based on embeddings"""
    return _embedding_analyzer.get_deck_recommendations(deck_cards, available_cards, limit)


def score_deck_cards_embedding(deck_cards: List[Dict]) -> List[Dict]:
    """Score deck cards using embeddings (lowest score = best cut candidates)"""
    return _embedding_analyzer.score_deck_cards(deck_cards)


def get_top_embedding_synergies(deck_cards: List[Dict], top_n: int = 10) -> List[Tuple[str, str, float]]:
    """Get top synergies based on embeddings"""
    return _embedding_analyzer.get_top_synergies(deck_cards, top_n)


def build_embedding_graph(deck_cards: List[Dict], min_similarity: float = 0.5) -> List[Dict]:
    """Build graph elements based on embeddings"""
    return _embedding_analyzer.build_embedding_graph_elements(deck_cards, min_similarity)


def is_loaded() -> bool:
    """Check if embedding analyzer is loaded"""
    return _embedding_analyzer.loaded
