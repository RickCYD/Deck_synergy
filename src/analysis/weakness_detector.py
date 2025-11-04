"""
Deck Weakness Detection
Analyzes deck composition and identifies gaps in role distribution
"""

from typing import Dict, List, Tuple, Optional
import re


class DeckWeaknessAnalyzer:
    """
    Analyzes deck composition to identify weaknesses and imbalances

    Categorizes cards by role and compares against recommended ranges
    for Commander format decks.
    """

    # Recommended card counts for 100-card Commander decks
    RECOMMENDED_RANGES = {
        'ramp': {
            'min': 8,
            'ideal': 10,
            'max': 15,
            'description': 'Mana acceleration (ramp spells, mana rocks, dorks)'
        },
        'card_draw': {
            'min': 8,
            'ideal': 10,
            'max': 15,
            'description': 'Card draw and card advantage engines'
        },
        'removal': {
            'min': 8,
            'ideal': 10,
            'max': 15,
            'description': 'Targeted removal (creature, artifact, enchantment)'
        },
        'board_wipes': {
            'min': 2,
            'ideal': 3,
            'max': 5,
            'description': 'Mass removal and board wipes'
        },
        'protection': {
            'min': 3,
            'ideal': 5,
            'max': 8,
            'description': 'Protection spells (counterspells, hexproof, indestructible)'
        },
        'recursion': {
            'min': 2,
            'ideal': 4,
            'max': 8,
            'description': 'Recursion and graveyard interaction'
        },
        'threats': {
            'min': 8,
            'ideal': 12,
            'max': 20,
            'description': 'Win conditions and major threats'
        },
        'utility': {
            'min': 5,
            'ideal': 8,
            'max': 15,
            'description': 'Utility creatures and support spells'
        }
    }

    # Keywords and patterns for role detection
    ROLE_PATTERNS = {
        'ramp': [
            # Explicit mana production
            r'add\s+\{[WUBRGC]\}',
            r'add.*mana',
            r'search.*land.*battlefield',
            r'search.*basic land',
            # Common ramp effects
            r'treasures?',
            r'mana.*rocks?',
            r'ramp',
            # Specific card types
            r'type.*artifact.*mana',
        ],
        'card_draw': [
            r'draw.*cards?',
            r'draws?.*cards?',
            r'draws?\s+\d+',
            r'card advantage',
            r'rhystic study',
            r'divination',
            r'scry',
            r'impulse draw',
            r'whenever.*draw',
        ],
        'removal': [
            r'destroy target',
            r'exile target',
            r'remove.*from.*game',
            r'sacrifice.*permanent',
            r'return.*to.*hand',
            r'return.*to.*owner',
            r'-\d+/-\d+',  # -X/-X effects
            r'deals?\s+\d+\s+damage',
            r'fight',
            r'tap target',
        ],
        'board_wipes': [
            r'destroy all',
            r'exile all',
            r'each.*destroy',
            r'wrath',
            r'damnation',
            r'board wipe',
            r'mass removal',
            r'all creatures get -\d+/-\d+',
        ],
        'protection': [
            r'counter target',
            r'hexproof',
            r'indestructible',
            r'shroud',
            r'ward',
            r'protection from',
            r'prevent.*damage',
            r'regenerate',
            r'phase out',
        ],
        'recursion': [
            r'return.*from.*graveyard',
            r'reanimate',
            r'unearth',
            r'flashback',
            r'escape',
            r'disturb',
            r'embalm',
            r'eternalize',
            r'when.*dies.*return',
        ],
        'threats': [
            r'commander damage',
            r'combat damage',
            r'when.*attacks',
            r'whenever.*attacks',
            r'power\s+\d+\s+or\s+greater',
            r'infect',
            r'double strike',
            r'voltron',
            r'combo piece',
        ],
    }

    def __init__(self):
        self.compiled_patterns = {}
        for role, patterns in self.ROLE_PATTERNS.items():
            self.compiled_patterns[role] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def categorize_card(self, card: Dict) -> List[str]:
        """
        Categorize a card by its roles

        Args:
            card: Card dictionary with oracle_text, type_line, etc.

        Returns:
            List of role strings (e.g., ['ramp', 'utility'])
        """
        roles = []

        # Get searchable text
        oracle_text = card.get('oracle_text', '').lower()
        type_line = card.get('type_line', '').lower()
        card_name = card.get('name', '').lower()

        # Combine all text for searching
        search_text = f"{oracle_text} {type_line} {card_name}"

        # Check for board wipes first (more specific than removal)
        if self._matches_role('board_wipes', search_text):
            roles.append('board_wipes')
        # Then check for general removal
        elif self._matches_role('removal', search_text):
            roles.append('removal')

        # Check other roles
        for role in ['ramp', 'card_draw', 'protection', 'recursion']:
            if self._matches_role(role, search_text):
                roles.append(role)

        # Threats: Creatures with high power or special abilities
        if self._is_threat(card):
            roles.append('threats')

        # Utility: catch-all for cards that don't fit other categories
        if not roles:
            roles.append('utility')

        return roles

    def _matches_role(self, role: str, text: str) -> bool:
        """Check if text matches role patterns"""
        if role not in self.compiled_patterns:
            return False

        for pattern in self.compiled_patterns[role]:
            if pattern.search(text):
                return True

        return False

    def _is_threat(self, card: Dict) -> bool:
        """
        Determine if card is a threat (win condition or major value engine)
        """
        type_line = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()
        power = card.get('power')
        cmc = card.get('cmc', 0)

        # High CMC creatures are often threats
        if 'creature' in type_line and cmc >= 6:
            return True

        # High power creatures
        if power:
            try:
                power_val = int(power)
                if power_val >= 5:
                    return True
            except (ValueError, TypeError):
                pass

        # Planeswalkers are often threats
        if 'planeswalker' in type_line:
            return True

        # Check for threat patterns
        threat_patterns = [
            r'win the game',
            r'combat damage',
            r'commander damage',
            r'when.*attacks',
            r'whenever.*attacks',
            r'infect',
            r'poison counter',
            r'voltron',
        ]

        for pattern in threat_patterns:
            if re.search(pattern, oracle_text, re.IGNORECASE):
                return True

        return False

    def analyze_deck(self, cards: List[Dict]) -> Dict:
        """
        Analyze deck composition and identify weaknesses

        Args:
            cards: List of card dictionaries

        Returns:
            Dict with analysis results:
            {
                'role_distribution': {
                    'ramp': {'count': 10, 'cards': [...], 'status': 'good'},
                    ...
                },
                'weaknesses': [
                    {'role': 'removal', 'severity': 'high', 'message': '...'},
                    ...
                ],
                'strengths': [...],
                'overall_score': 75,
                'suggestions': [...]
            }
        """
        # Count cards by role
        role_distribution = {
            role: {'count': 0, 'cards': [], 'status': 'unknown'}
            for role in self.RECOMMENDED_RANGES.keys()
        }

        # Categorize all cards
        for card in cards:
            # Skip commander from counts (they're always available)
            if card.get('is_commander', False):
                continue

            roles = self.categorize_card(card)

            for role in roles:
                if role in role_distribution:
                    role_distribution[role]['count'] += 1
                    role_distribution[role]['cards'].append(card['name'])

        # Evaluate each role
        weaknesses = []
        strengths = []
        total_score = 0

        for role, data in role_distribution.items():
            count = data['count']
            ranges = self.RECOMMENDED_RANGES[role]

            # Calculate status
            if count < ranges['min']:
                data['status'] = 'critical'
                severity = 'high' if count < ranges['min'] - 2 else 'medium'
                weaknesses.append({
                    'role': role,
                    'severity': severity,
                    'current': count,
                    'recommended': ranges['ideal'],
                    'message': f"Too few {role} cards ({count}/{ranges['ideal']} recommended)"
                })
                score = max(0, 50 * (count / ranges['min']))
            elif count < ranges['ideal']:
                data['status'] = 'low'
                weaknesses.append({
                    'role': role,
                    'severity': 'low',
                    'current': count,
                    'recommended': ranges['ideal'],
                    'message': f"Could use more {role} ({count}/{ranges['ideal']} recommended)"
                })
                score = 50 + 25 * ((count - ranges['min']) / (ranges['ideal'] - ranges['min']))
            elif count <= ranges['max']:
                data['status'] = 'good'
                strengths.append({
                    'role': role,
                    'current': count,
                    'message': f"Good {role} count ({count} cards)"
                })
                score = 75 + 25 * ((ranges['max'] - count) / (ranges['max'] - ranges['ideal']))
            else:
                data['status'] = 'high'
                weaknesses.append({
                    'role': role,
                    'severity': 'low',
                    'current': count,
                    'recommended': ranges['ideal'],
                    'message': f"Many {role} cards ({count}, might dilute strategy)"
                })
                score = max(50, 100 - 5 * (count - ranges['max']))

            total_score += score

        # Calculate overall score
        overall_score = int(total_score / len(role_distribution))

        # Generate suggestions
        suggestions = self._generate_suggestions(role_distribution, weaknesses)

        return {
            'role_distribution': role_distribution,
            'weaknesses': sorted(weaknesses, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']]),
            'strengths': strengths,
            'overall_score': overall_score,
            'suggestions': suggestions,
            'deck_size': len(cards)
        }

    def _generate_suggestions(self, role_distribution: Dict, weaknesses: List[Dict]) -> List[str]:
        """Generate actionable suggestions based on analysis"""
        suggestions = []

        # High severity issues first
        critical_weaknesses = [w for w in weaknesses if w['severity'] == 'high']

        for weakness in critical_weaknesses:
            role = weakness['role']
            needed = weakness['recommended'] - weakness['current']
            description = self.RECOMMENDED_RANGES[role]['description']

            suggestions.append(
                f"Add {needed} more {role} cards ({description})"
            )

        # Check for balance issues
        ramp = role_distribution['ramp']['count']
        draw = role_distribution['card_draw']['count']

        if ramp < 8 and draw < 8:
            suggestions.append(
                "Low card advantage - prioritize both ramp and draw to maintain resources"
            )

        removal = role_distribution['removal']['count']
        protection = role_distribution['protection']['count']

        if removal < 8 and protection < 3:
            suggestions.append(
                "Limited interaction - add removal or protection to answer threats"
            )

        return suggestions[:5]  # Top 5 suggestions

    def get_role_status_color(self, status: str) -> str:
        """Get color code for role status"""
        colors = {
            'critical': '#e74c3c',  # Red
            'low': '#f39c12',       # Orange
            'good': '#27ae60',      # Green
            'high': '#3498db'       # Blue
        }
        return colors.get(status, '#95a5a6')
