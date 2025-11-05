"""
Recommendation Impact Analysis
Analyzes the impact of adding a recommended card to the deck
"""

from typing import Dict, List, Optional
from .weakness_detector import DeckWeaknessAnalyzer


class RecommendationImpactAnalyzer:
    """
    Analyzes how adding a recommended card would impact deck composition
    """

    def __init__(self):
        self.weakness_analyzer = DeckWeaknessAnalyzer()

    def analyze_card_impact(
        self,
        card: Dict,
        current_deck: List[Dict],
        current_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze the impact of adding a card to the deck

        Args:
            card: Card to analyze
            current_deck: Current deck cards
            current_analysis: Pre-computed current weakness analysis (optional, for performance)

        Returns:
            Dict with impact analysis:
            {
                'roles_filled': ['ramp', 'utility'],
                'score_change': +5,
                'weaknesses_addressed': [
                    {'role': 'ramp', 'severity': 'high', 'improvement': 'Brings ramp to 9/10 (ideal range)'}
                ],
                'before_score': 65,
                'after_score': 70,
                'role_changes': {
                    'ramp': {'before': 8, 'after': 9, 'status_before': 'low', 'status_after': 'good'},
                    ...
                },
                'impact_rating': 'high'  # high/medium/low
            }
        """
        # Get current analysis if not provided
        if current_analysis is None:
            current_analysis = self.weakness_analyzer.analyze_deck(current_deck)

        # Simulate adding the card
        simulated_deck = current_deck + [card]
        after_analysis = self.weakness_analyzer.analyze_deck(simulated_deck)

        # Identify which roles this card fills
        roles_filled = self.weakness_analyzer.categorize_card(card)

        # Calculate score change
        score_change = after_analysis['overall_score'] - current_analysis['overall_score']

        # Identify weaknesses addressed
        weaknesses_addressed = self._identify_weaknesses_addressed(
            roles_filled,
            current_analysis,
            after_analysis
        )

        # Calculate role changes
        role_changes = self._calculate_role_changes(
            current_analysis['role_distribution'],
            after_analysis['role_distribution']
        )

        # Calculate impact rating
        impact_rating = self._calculate_impact_rating(
            score_change,
            weaknesses_addressed,
            roles_filled
        )

        return {
            'roles_filled': roles_filled,
            'score_change': score_change,
            'weaknesses_addressed': weaknesses_addressed,
            'before_score': current_analysis['overall_score'],
            'after_score': after_analysis['overall_score'],
            'role_changes': role_changes,
            'impact_rating': impact_rating,
            'fills_critical_gap': any(w['severity'] == 'high' for w in weaknesses_addressed)
        }

    def _identify_weaknesses_addressed(
        self,
        roles_filled: List[str],
        before_analysis: Dict,
        after_analysis: Dict
    ) -> List[Dict]:
        """
        Identify which weaknesses are addressed by adding this card

        Returns:
            List of dictionaries describing improvements
        """
        addressed = []

        before_weaknesses = {w['role']: w for w in before_analysis['weaknesses']}
        after_weaknesses = {w['role']: w for w in after_analysis['weaknesses']}

        for role in roles_filled:
            if role not in self.weakness_analyzer.RECOMMENDED_RANGES:
                continue

            before_data = before_analysis['role_distribution'][role]
            after_data = after_analysis['role_distribution'][role]

            # Check if this role had a weakness before
            if role in before_weaknesses:
                weakness = before_weaknesses[role]

                # Check if weakness severity decreased or was resolved
                still_weak = role in after_weaknesses
                severity_improved = False

                if still_weak:
                    after_weakness = after_weaknesses[role]
                    # Map severity to numeric value for comparison
                    severity_rank = {'high': 3, 'medium': 2, 'low': 1}
                    before_rank = severity_rank.get(weakness['severity'], 0)
                    after_rank = severity_rank.get(after_weakness['severity'], 0)
                    severity_improved = after_rank < before_rank
                else:
                    severity_improved = True  # Weakness completely resolved

                if severity_improved or not still_weak:
                    ranges = self.weakness_analyzer.RECOMMENDED_RANGES[role]
                    improvement_desc = self._describe_improvement(
                        role,
                        before_data['count'],
                        after_data['count'],
                        before_data['status'],
                        after_data['status'],
                        ranges
                    )

                    addressed.append({
                        'role': role,
                        'severity': weakness['severity'],
                        'improvement': improvement_desc,
                        'resolved': not still_weak
                    })

        return addressed

    def _describe_improvement(
        self,
        role: str,
        before_count: int,
        after_count: int,
        before_status: str,
        after_status: str,
        ranges: Dict
    ) -> str:
        """Generate human-readable improvement description"""
        role_name = role.replace('_', ' ').title()

        if after_status == 'good':
            return f"Brings {role_name} to {after_count} (ideal range {ranges['min']}-{ranges['max']})"
        elif before_status == 'critical' and after_status in ['low', 'good']:
            return f"Improves {role_name} from {before_count} to {after_count} (minimum: {ranges['min']})"
        elif before_status == 'low' and after_status == 'good':
            return f"Optimizes {role_name} to {after_count} (ideal: {ranges['ideal']})"
        else:
            return f"Increases {role_name} from {before_count} to {after_count}"

    def _calculate_role_changes(
        self,
        before_dist: Dict,
        after_dist: Dict
    ) -> Dict:
        """
        Calculate changes in role distribution

        Returns:
            Dict mapping role names to change details
        """
        changes = {}

        for role in before_dist.keys():
            before_count = before_dist[role]['count']
            after_count = after_dist[role]['count']

            if before_count != after_count:
                changes[role] = {
                    'before': before_count,
                    'after': after_count,
                    'change': after_count - before_count,
                    'status_before': before_dist[role]['status'],
                    'status_after': after_dist[role]['status']
                }

        return changes

    def _calculate_impact_rating(
        self,
        score_change: int,
        weaknesses_addressed: List[Dict],
        roles_filled: List[str]
    ) -> str:
        """
        Calculate overall impact rating: high/medium/low

        High impact: Addresses critical weaknesses or significantly improves score
        Medium impact: Addresses some weaknesses or moderately improves score
        Low impact: Minor improvement
        """
        # Check if any critical weaknesses are addressed
        has_critical = any(w['severity'] == 'high' for w in weaknesses_addressed)
        has_medium = any(w['severity'] == 'medium' for w in weaknesses_addressed)

        if has_critical or score_change >= 5:
            return 'high'
        elif has_medium or score_change >= 2 or len(weaknesses_addressed) >= 2:
            return 'medium'
        else:
            return 'low'

    def analyze_batch_recommendations(
        self,
        recommendations: List[Dict],
        current_deck: List[Dict],
        limit: int = 20
    ) -> List[Dict]:
        """
        Analyze impact for a batch of recommendations

        Args:
            recommendations: List of recommended cards
            current_deck: Current deck cards
            limit: Maximum number to analyze (for performance)

        Returns:
            List of recommendations with impact data added
        """
        # Calculate current analysis once (for performance)
        current_analysis = self.weakness_analyzer.analyze_deck(current_deck)

        results = []

        for rec in recommendations[:limit]:
            try:
                impact = self.analyze_card_impact(
                    rec,
                    current_deck,
                    current_analysis
                )

                # Add impact data to recommendation
                rec_with_impact = dict(rec)
                rec_with_impact['impact_analysis'] = impact

                results.append(rec_with_impact)

            except Exception as e:
                # If analysis fails for a card, include it without impact data
                print(f"Warning: Failed to analyze impact for {rec.get('name', 'unknown')}: {e}")
                results.append(rec)

        # Sort by impact rating (high > medium > low)
        impact_order = {'high': 0, 'medium': 1, 'low': 2}

        results.sort(
            key=lambda x: impact_order.get(
                x.get('impact_analysis', {}).get('impact_rating', 'low'),
                3
            )
        )

        return results

    def get_impact_summary_text(self, impact: Dict) -> str:
        """
        Generate concise text summary of impact

        Args:
            impact: Impact analysis dict

        Returns:
            Human-readable summary string
        """
        parts = []

        # Score change
        if impact['score_change'] > 0:
            parts.append(f"+{impact['score_change']} score")
        elif impact['score_change'] < 0:
            parts.append(f"{impact['score_change']} score")

        # Roles
        if impact['roles_filled']:
            roles_text = ', '.join(r.replace('_', ' ').title() for r in impact['roles_filled'])
            parts.append(f"Fills: {roles_text}")

        # Critical gaps
        if impact['fills_critical_gap']:
            parts.append("⚠️ Addresses critical weakness")

        return " | ".join(parts) if parts else "Minor impact"

    def get_impact_icon(self, impact_rating: str) -> str:
        """Get icon/emoji for impact rating"""
        icons = {
            'high': '🔥',
            'medium': '⚡',
            'low': 'ℹ️'
        }
        return icons.get(impact_rating, '')

    def get_impact_color(self, impact_rating: str) -> str:
        """Get color code for impact rating"""
        colors = {
            'high': '#e74c3c',  # Red
            'medium': '#f39c12',  # Orange
            'low': '#3498db'  # Blue
        }
        return colors.get(impact_rating, '#95a5a6')
