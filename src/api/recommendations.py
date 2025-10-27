"""
Card Recommendation Engine
Fast searching across 34k+ preprocessed cards for deck recommendations

Uses pre-computed synergy tags and roles for instant lookups.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import Counter


class RecommendationEngine:
    """
    Fast card recommendation engine using preprocessed database

    Provides instant recommendations based on:
    - Synergy tags (ETB, sacrifice, tokens, etc.)
    - Roles (ramp, draw, removal, etc.)
    - Color identity
    - Tribal synergies
    """

    def __init__(self):
        self.cards = []
        self.cards_by_name = {}
        self.cards_by_tag = {}  # tag -> [card indices]
        self.cards_by_role = {}  # role -> [card indices]
        self.loaded = False

    def load(self) -> bool:
        """
        Load preprocessed card database into memory

        Returns:
            bool: True if successful
        """
        if self.loaded:
            return True

        cards_file = Path(__file__).parent.parent.parent / 'data' / 'cards' / 'cards-preprocessed.json'

        if not cards_file.exists():
            print(f"Warning: {cards_file} not found. Recommendation engine unavailable.")
            print("Run: python scripts/create_preprocessed_cards.py")
            return False

        try:
            print(f"Loading recommendation database from {cards_file.name}...")
            with open(cards_file, 'r', encoding='utf-8') as f:
                self.cards = json.load(f)

            # Build lookup indices
            self._build_indices()

            self.loaded = True
            print(f"✅ Loaded {len(self.cards)} cards into recommendation engine")
            print(f"   Indexed {len(self.cards_by_tag)} synergy tags")
            print(f"   Indexed {len(self.cards_by_role)} roles")
            return True

        except Exception as e:
            print(f"Error loading recommendation database: {e}")
            return False

    def _build_indices(self):
        """Build fast lookup indices for tags and roles"""
        self.cards_by_name = {card['name']: card for card in self.cards}

        # Index by synergy tags
        for idx, card in enumerate(self.cards):
            for tag in card.get('synergy_tags', []):
                if tag not in self.cards_by_tag:
                    self.cards_by_tag[tag] = []
                self.cards_by_tag[tag].append(idx)

            # Index by roles
            for role in card.get('roles', []):
                if role not in self.cards_by_role:
                    self.cards_by_role[role] = []
                self.cards_by_role[role].append(idx)

    def get_recommendations(
        self,
        deck_cards: List[Dict],
        color_identity: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top card recommendations for a deck

        Args:
            deck_cards: Current cards in the deck
            color_identity: Color identity filter (e.g., ['W', 'U', 'B'])
            limit: Number of recommendations to return

        Returns:
            List of recommended cards with scores
        """
        if not self.loaded:
            if not self.load():
                return []

        # Extract deck's synergy profile
        deck_tags = self._extract_deck_tags(deck_cards)
        deck_roles = self._extract_deck_roles(deck_cards)
        deck_card_names = {card['name'] for card in deck_cards}

        # Score all cards
        card_scores = {}

        for idx, card in enumerate(self.cards):
            card_name = card['name']

            # Skip cards already in deck
            if card_name in deck_card_names:
                continue

            # Filter by color identity
            if color_identity:
                if not self._matches_color_identity(card, color_identity):
                    continue

            # Calculate synergy score
            score = self._calculate_synergy_score(
                card,
                deck_tags,
                deck_roles
            )

            if score > 0:
                card_scores[idx] = score

        # Get top N recommendations
        top_indices = sorted(card_scores.keys(), key=lambda i: card_scores[i], reverse=True)[:limit]

        recommendations = []
        for idx in top_indices:
            card = self.cards[idx]
            recommendations.append({
                **card,
                'recommendation_score': card_scores[idx],
                'synergy_reasons': self._explain_synergy(card, deck_tags, deck_roles)
            })

        return recommendations

    def _extract_deck_tags(self, deck_cards: List[Dict]) -> Counter:
        """Extract synergy tag counts from deck"""
        tag_counts = Counter()

        for card in deck_cards:
            # Get tags from preprocessed card if available
            card_name = card.get('name')
            preprocessed = self.cards_by_name.get(card_name)

            if preprocessed:
                tags = preprocessed.get('synergy_tags', [])
                tag_counts.update(tags)

        return tag_counts

    def _extract_deck_roles(self, deck_cards: List[Dict]) -> Counter:
        """Extract role counts from deck"""
        role_counts = Counter()

        for card in deck_cards:
            card_name = card.get('name')
            preprocessed = self.cards_by_name.get(card_name)

            if preprocessed:
                roles = preprocessed.get('roles', [])
                role_counts.update(roles)

        return role_counts

    def _calculate_synergy_score(
        self,
        card: Dict,
        deck_tags: Counter,
        deck_roles: Counter
    ) -> float:
        """
        Calculate how well a card synergizes with the deck

        Scoring:
        - +3 points per matching synergy tag
        - +2 points per matching role
        - Bonus for complementary mechanics (e.g., ETB + flicker)
        """
        score = 0.0

        card_tags = set(card.get('synergy_tags', []))
        card_roles = set(card.get('roles', []))

        # Tag synergy
        for tag in card_tags:
            if tag in deck_tags:
                score += 3.0 * deck_tags[tag]

        # Role synergy
        for role in card_roles:
            if role in deck_roles:
                score += 2.0 * deck_roles[role]

        # Complementary mechanics bonus
        complementary_pairs = [
            ('has_etb', 'flicker'),
            ('token_gen', 'sacrifice_outlet'),
            ('death_trigger', 'sacrifice_outlet'),
            ('graveyard', 'recursion'),
            ('counters', 'proliferate'),
            ('untap_others', 'mana_ability'),
        ]

        for tag1, tag2 in complementary_pairs:
            if tag1 in card_tags and tag2 in deck_tags:
                score += 5.0
            if tag2 in card_tags and tag1 in deck_tags:
                score += 5.0

        # Tribal synergy bonus
        card_tribes = {tag.replace('tribal_', '') for tag in card_tags if tag.startswith('tribal_')}
        deck_tribes = {tag.replace('tribal_', '') for tag in deck_tags if tag.startswith('tribal_')}

        for tribe in card_tribes & deck_tribes:
            score += 8.0  # Strong tribal bonus

        return score

    def _matches_color_identity(self, card: Dict, color_identity: List[str]) -> bool:
        """Check if card fits within color identity"""
        card_colors = set(card.get('color_identity', []))
        allowed_colors = set(color_identity)

        # Card must not have any colors outside the identity
        return card_colors.issubset(allowed_colors)

    def _explain_synergy(
        self,
        card: Dict,
        deck_tags: Counter,
        deck_roles: Counter
    ) -> List[str]:
        """
        Generate human-readable synergy explanations

        Returns:
            List of explanation strings
        """
        reasons = []
        card_tags = set(card.get('synergy_tags', []))
        card_roles = set(card.get('roles', []))

        # Tag explanations
        tag_explanations = {
            'has_etb': 'Has ETB abilities',
            'flicker': 'Can flicker/blink creatures',
            'sacrifice_outlet': 'Sacrifice outlet',
            'death_trigger': 'Triggers on creature death',
            'token_gen': 'Generates tokens',
            'card_draw': 'Draws cards',
            'ramp': 'Ramps mana',
            'graveyard': 'Graveyard interaction',
            'removal': 'Removes threats',
            'protection': 'Protects permanents',
            'counters': '+1/+1 counters theme',
            'untap_others': 'Untaps other permanents',
            'tribal_payoff': 'Tribal synergy payoff',
        }

        for tag in card_tags:
            if tag in deck_tags and tag in tag_explanations:
                count = deck_tags[tag]
                reasons.append(f"{tag_explanations[tag]} (synergizes with {count} cards)")

        # Complementary mechanics
        if 'has_etb' in card_tags and 'flicker' in deck_tags:
            reasons.append("ETB abilities for flicker effects")
        if 'flicker' in card_tags and 'has_etb' in deck_tags:
            reasons.append("Flicker to retrigger ETB abilities")
        if 'token_gen' in card_tags and 'sacrifice_outlet' in deck_tags:
            reasons.append("Token generation for sacrifice outlets")
        if 'sacrifice_outlet' in card_tags and ('token_gen' in deck_tags or 'death_trigger' in deck_tags):
            reasons.append("Sacrifice outlet for tokens/death triggers")

        # Tribal
        card_tribes = {tag.replace('tribal_', '') for tag in card_tags if tag.startswith('tribal_')}
        deck_tribes = {tag.replace('tribal_', '') for tag in deck_tags if tag.startswith('tribal_')}
        for tribe in card_tribes & deck_tribes:
            reasons.append(f"{tribe.capitalize()} tribal synergy")

        return reasons[:5]  # Top 5 reasons

    def search_by_tag(self, tag: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """
        Find all cards with a specific synergy tag

        Args:
            tag: Synergy tag to search for
            color_identity: Optional color identity filter
            limit: Max number of results

        Returns:
            List of matching cards
        """
        if not self.loaded:
            if not self.load():
                return []

        if tag not in self.cards_by_tag:
            return []

        indices = self.cards_by_tag[tag]
        results = []

        for idx in indices:
            card = self.cards[idx]

            # Filter by color identity
            if color_identity and not self._matches_color_identity(card, color_identity):
                continue

            results.append(card)

            if len(results) >= limit:
                break

        return results

    def search_by_role(self, role: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """
        Find all cards with a specific role

        Args:
            role: Role to search for (e.g., 'ramp', 'draw', 'removal')
            color_identity: Optional color identity filter
            limit: Max number of results

        Returns:
            List of matching cards
        """
        if not self.loaded:
            if not self.load():
                return []

        if role not in self.cards_by_role:
            return []

        indices = self.cards_by_role[role]
        results = []

        for idx in indices:
            card = self.cards[idx]

            # Filter by color identity
            if color_identity and not self._matches_color_identity(card, color_identity):
                continue

            results.append(card)

            if len(results) >= limit:
                break

        return results


# Global instance
_recommendation_engine = RecommendationEngine()


def load_recommendation_engine() -> bool:
    """Load the recommendation engine (call once at app startup)"""
    return _recommendation_engine.load()


def get_recommendations(
    deck_cards: List[Dict],
    color_identity: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Get top card recommendations for a deck

    Example:
        recommendations = get_recommendations(
            deck_cards=current_deck,
            color_identity=['W', 'U'],
            limit=10
        )
    """
    return _recommendation_engine.get_recommendations(deck_cards, color_identity, limit)


def search_by_tag(tag: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """Search for cards by synergy tag"""
    return _recommendation_engine.search_by_tag(tag, color_identity, limit)


def search_by_role(role: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """Search for cards by role"""
    return _recommendation_engine.search_by_role(role, color_identity, limit)


def is_loaded() -> bool:
    """Check if recommendation engine is loaded"""
    return _recommendation_engine.loaded
