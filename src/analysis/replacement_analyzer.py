"""
Smart Card Replacement Analysis
Identifies cards to replace and suggests optimal replacements
"""

from typing import Dict, List, Tuple, Optional
from .weakness_detector import DeckWeaknessAnalyzer
from .impact_analyzer import RecommendationImpactAnalyzer


class ReplacementAnalyzer:
    """
    Analyzes deck to suggest smart card replacements

    Identifies underperforming cards and finds better alternatives that:
    - Fill similar roles
    - Have similar mana cost
    - Match card type
    - Improve overall deck synergy
    """

    def __init__(self):
        self.weakness_analyzer = DeckWeaknessAnalyzer()
        self.impact_analyzer = RecommendationImpactAnalyzer()

    def identify_replacement_candidates(
        self,
        deck_cards: List[Dict],
        deck_scores: Optional[List[Dict]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Identify cards in deck that are candidates for replacement

        Args:
            deck_cards: Current deck cards
            deck_scores: Pre-computed synergy scores (optional)
            limit: Maximum number of candidates to return

        Returns:
            List of cards that could be replaced, with reasons
            [
                {
                    'card': {...},
                    'synergy_score': 45,
                    'replacement_priority': 'high',  # high/medium/low
                    'reasons': ['Low synergy with deck', 'Role oversaturated'],
                    'suggested_role': 'card_draw'  # What role to replace it with
                },
                ...
            ]
        """
        # Analyze deck composition
        analysis = self.weakness_analyzer.analyze_deck(deck_cards)
        role_distribution = analysis['role_distribution']
        weaknesses = {w['role']: w for w in analysis['weaknesses']}

        candidates = []

        # Categorize each card
        for card in deck_cards:
            # Skip commander
            if card.get('is_commander', False):
                continue

            # Skip basic lands
            type_line = card.get('type_line', '').lower()
            if 'basic' in type_line and 'land' in type_line:
                continue

            # Get synergy score if available
            synergy_score = None
            if deck_scores:
                for score_entry in deck_scores:
                    if score_entry['name'] == card['name']:
                        synergy_score = score_entry.get('synergy_score', 0)
                        break

            # Analyze this card
            card_roles = self.weakness_analyzer.categorize_card(card)

            # Calculate replacement priority
            priority, reasons, suggested_role = self._calculate_replacement_priority(
                card,
                card_roles,
                synergy_score,
                role_distribution,
                weaknesses
            )

            if priority != 'none':
                candidates.append({
                    'card': card,
                    'synergy_score': synergy_score,
                    'replacement_priority': priority,
                    'reasons': reasons,
                    'suggested_role': suggested_role,
                    'current_roles': card_roles
                })

        # Sort by priority (high > medium > low) and synergy score (low first)
        priority_rank = {'high': 0, 'medium': 1, 'low': 2}
        candidates.sort(key=lambda x: (
            priority_rank[x['replacement_priority']],
            x['synergy_score'] if x['synergy_score'] is not None else 999
        ))

        return candidates[:limit]

    def _calculate_replacement_priority(
        self,
        card: Dict,
        card_roles: List[str],
        synergy_score: Optional[float],
        role_distribution: Dict,
        weaknesses: Dict
    ) -> Tuple[str, List[str], Optional[str]]:
        """
        Calculate replacement priority for a card

        Returns:
            (priority, reasons, suggested_role)
            priority: 'high', 'medium', 'low', or 'none'
        """
        reasons = []
        suggested_role = None

        # Check synergy score
        low_synergy = synergy_score is not None and synergy_score < 50
        very_low_synergy = synergy_score is not None and synergy_score < 30

        if very_low_synergy:
            reasons.append(f"Very low synergy ({synergy_score:.0f})")
        elif low_synergy:
            reasons.append(f"Low synergy ({synergy_score:.0f})")

        # Check if card's roles are oversaturated
        oversaturated_roles = []
        undersaturated_roles = []

        for role in card_roles:
            if role in role_distribution:
                status = role_distribution[role]['status']
                if status == 'high':
                    oversaturated_roles.append(role)

        # Identify critical weaknesses
        for role, weakness in weaknesses.items():
            if weakness['severity'] == 'high':
                undersaturated_roles.append(role)

        if oversaturated_roles:
            roles_text = ', '.join(r.replace('_', ' ') for r in oversaturated_roles)
            reasons.append(f"Oversaturated role: {roles_text}")

        # Suggest what role to replace it with
        if undersaturated_roles:
            # Prioritize high-severity weaknesses
            suggested_role = undersaturated_roles[0]

        # Calculate priority
        if very_low_synergy and oversaturated_roles:
            priority = 'high'
        elif (low_synergy and oversaturated_roles) or very_low_synergy:
            priority = 'high'
        elif low_synergy or oversaturated_roles:
            priority = 'medium'
        elif synergy_score is not None and synergy_score < 70:
            priority = 'low'
            reasons.append("Could be improved")
        else:
            priority = 'none'

        return priority, reasons, suggested_role

    def find_replacements(
        self,
        card_to_replace: Dict,
        deck_cards: List[Dict],
        candidate_pool: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """
        Find optimal replacement cards for a given card

        Args:
            card_to_replace: The card to replace
            deck_cards: Current deck (without the card to replace)
            candidate_pool: Pool of potential replacement cards
            limit: Max number of replacements to return

        Returns:
            List of replacement candidates with impact analysis
            [
                {
                    'card': {...},
                    'type_match': True,
                    'cmc_diff': 0,
                    'role_match': True,
                    'net_impact': {
                        'score_change': +5,
                        'weaknesses_addressed': [...],
                        ...
                    }
                },
                ...
            ]
        """
        # Get properties of card to replace
        old_cmc = card_to_replace.get('cmc', 0)
        old_type = card_to_replace.get('type_line', '').lower()
        old_roles = self.weakness_analyzer.categorize_card(card_to_replace)

        # Categorize old card type
        old_card_type = self._categorize_card_type(old_type)

        # Remove the card to replace from deck for simulation
        deck_without_card = [c for c in deck_cards if c['name'] != card_to_replace['name']]

        replacements = []

        for candidate in candidate_pool:
            # Skip if candidate is already in deck
            if any(c['name'] == candidate['name'] for c in deck_cards):
                continue

            # Get candidate properties
            candidate_cmc = candidate.get('cmc', 0)
            candidate_type = candidate.get('type_line', '').lower()
            candidate_roles = self.weakness_analyzer.categorize_card(candidate)
            candidate_card_type = self._categorize_card_type(candidate_type)

            # Calculate matching scores
            cmc_diff = abs(candidate_cmc - old_cmc)
            type_match = candidate_card_type == old_card_type
            role_overlap = len(set(old_roles) & set(candidate_roles))
            role_match = role_overlap > 0

            # Prefer candidates that:
            # 1. Match card type (creature for creature, etc.)
            # 2. Have similar CMC (±2)
            # 3. Fill similar roles
            if cmc_diff > 3:
                continue  # Too different in mana cost

            # Calculate net impact of the swap
            # Simulate: deck_without_card + candidate
            simulated_deck = deck_without_card + [candidate]

            # Compare to original deck
            original_analysis = self.weakness_analyzer.analyze_deck(deck_cards)
            new_analysis = self.weakness_analyzer.analyze_deck(simulated_deck)

            net_impact = {
                'score_change': new_analysis['overall_score'] - original_analysis['overall_score'],
                'before_score': original_analysis['overall_score'],
                'after_score': new_analysis['overall_score'],
                'weaknesses_addressed': self._compare_weaknesses(
                    original_analysis['weaknesses'],
                    new_analysis['weaknesses']
                ),
                'role_improvements': self._compare_role_distribution(
                    original_analysis['role_distribution'],
                    new_analysis['role_distribution']
                )
            }

            replacements.append({
                'card': candidate,
                'type_match': type_match,
                'cmc_diff': cmc_diff,
                'role_match': role_match,
                'role_overlap': role_overlap,
                'net_impact': net_impact,
                'match_score': self._calculate_match_score(
                    type_match, cmc_diff, role_overlap, net_impact['score_change']
                )
            })

        # Sort by match score (best replacements first)
        replacements.sort(key=lambda x: x['match_score'], reverse=True)

        return replacements[:limit]

    def _categorize_card_type(self, type_line: str) -> str:
        """Categorize card into broad type"""
        type_line = type_line.lower()

        if 'creature' in type_line:
            return 'creature'
        elif 'planeswalker' in type_line:
            return 'planeswalker'
        elif 'artifact' in type_line and 'creature' not in type_line:
            return 'artifact'
        elif 'enchantment' in type_line and 'creature' not in type_line:
            return 'enchantment'
        elif 'instant' in type_line:
            return 'instant'
        elif 'sorcery' in type_line:
            return 'sorcery'
        elif 'land' in type_line:
            return 'land'
        else:
            return 'other'

    def _calculate_match_score(
        self,
        type_match: bool,
        cmc_diff: int,
        role_overlap: int,
        score_change: int
    ) -> float:
        """Calculate overall match quality score"""
        score = 0.0

        # Type match is important
        if type_match:
            score += 30

        # CMC similarity (closer is better)
        if cmc_diff == 0:
            score += 20
        elif cmc_diff == 1:
            score += 15
        elif cmc_diff == 2:
            score += 10

        # Role overlap
        score += role_overlap * 10

        # Score improvement is most important
        score += score_change * 2

        return score

    def _compare_weaknesses(
        self,
        old_weaknesses: List[Dict],
        new_weaknesses: List[Dict]
    ) -> List[Dict]:
        """Identify which weaknesses improved"""
        improvements = []

        old_weak_map = {w['role']: w for w in old_weaknesses}
        new_weak_map = {w['role']: w for w in new_weaknesses}

        for role, old_weakness in old_weak_map.items():
            if role not in new_weak_map:
                # Weakness resolved!
                improvements.append({
                    'role': role,
                    'old_severity': old_weakness['severity'],
                    'status': 'resolved',
                    'message': f"{role.replace('_', ' ').title()} weakness resolved"
                })
            else:
                new_weakness = new_weak_map[role]
                severity_rank = {'high': 3, 'medium': 2, 'low': 1}
                if severity_rank[new_weakness['severity']] < severity_rank[old_weakness['severity']]:
                    # Severity improved
                    improvements.append({
                        'role': role,
                        'old_severity': old_weakness['severity'],
                        'new_severity': new_weakness['severity'],
                        'status': 'improved',
                        'message': f"{role.replace('_', ' ').title()}: {old_weakness['severity']} → {new_weakness['severity']}"
                    })

        return improvements

    def _compare_role_distribution(
        self,
        old_dist: Dict,
        new_dist: Dict
    ) -> Dict:
        """Compare role distributions and identify improvements"""
        improvements = {}

        for role in old_dist.keys():
            old_count = old_dist[role]['count']
            new_count = new_dist[role]['count']
            old_status = old_dist[role]['status']
            new_status = new_dist[role]['status']

            if old_count != new_count or old_status != new_status:
                improvements[role] = {
                    'count_change': new_count - old_count,
                    'old_status': old_status,
                    'new_status': new_status,
                    'improved': self._is_status_better(new_status, old_status)
                }

        return improvements

    def _is_status_better(self, new_status: str, old_status: str) -> bool:
        """Check if new status is better than old"""
        # Good is best, then low/high (not enough/too many), then critical (worst)
        status_rank = {'good': 0, 'low': 1, 'high': 1, 'critical': 2}
        return status_rank.get(new_status, 2) < status_rank.get(old_status, 2)

    def get_replacement_summary(self, replacement: Dict) -> str:
        """Generate human-readable summary of replacement"""
        card_name = replacement['card']['name']
        net_impact = replacement['net_impact']
        score_change = net_impact['score_change']

        parts = [f"{card_name}"]

        if replacement['type_match']:
            parts.append("(same type)")

        if replacement['cmc_diff'] == 0:
            parts.append("(same CMC)")
        elif replacement['cmc_diff'] == 1:
            parts.append("(±1 CMC)")

        if score_change > 0:
            parts.append(f"+{score_change} score")
        elif score_change < 0:
            parts.append(f"{score_change} score")

        return " ".join(parts)
