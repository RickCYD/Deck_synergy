"""
Commander Deck Builder Engine
Builds optimized Commander decks based on synergies and requirements
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
import random

from src.api import recommendations
from src.api.scryfall import ScryfallAPI


class CommanderDeckBuilder:
    """
    Builds Commander decks starting from a commander card

    Uses synergy analysis and role-based card selection to build
    optimized 100-card singleton decks for Commander format.
    """

    def __init__(self):
        self.api = ScryfallAPI()

    def build_deck(
        self,
        commander: Dict,
        num_lands: int = 37,
        num_ramp: int = 10,
        num_draw: int = 10,
        num_removal_single: int = 5,
        num_removal_mass: int = 3,
        prefer_synergy: bool = True
    ) -> Dict:
        """
        Build a Commander deck based on requirements

        Args:
            commander: Commander card dict with Scryfall data
            num_lands: Number of lands (default 37)
            num_ramp: Number of ramp cards (default 10)
            num_draw: Number of card draw (default 10)
            num_removal_single: Number of single target removal (default 5)
            num_removal_mass: Number of board wipes (default 3)
            prefer_synergy: Prioritize synergy over raw power (default True)

        Returns:
            Dict with:
                - cards: List of selected cards
                - mana_curve: Mana curve analysis
                - color_distribution: Color breakdown
                - deck_composition: Category counts
                - validation: Deck validation results
        """
        # Validate commander
        if not self._is_valid_commander(commander):
            raise ValueError(f"{commander.get('name')} is not a valid commander")

        # Get commander color identity
        color_identity = commander.get('color_identity', [])

        # Initialize deck with commander
        deck_cards = []
        commander_copy = commander.copy()
        commander_copy['is_commander'] = True
        commander_copy['quantity'] = 1
        deck_cards.append(commander_copy)

        # Calculate slots needed for each category
        total_non_lands = 100 - num_lands - 1  # -1 for commander

        # Reserve slots for required categories
        reserved_slots = num_ramp + num_draw + num_removal_single + num_removal_mass
        flex_slots = total_non_lands - reserved_slots

        if flex_slots < 0:
            raise ValueError(f"Too many required cards ({reserved_slots}) for {total_non_lands} non-land slots")

        print(f"\n=== Building deck for {commander['name']} ===")
        print(f"Color identity: {color_identity}")
        print(f"Total slots: 100 (1 commander, {num_lands} lands, {total_non_lands} nonlands)")
        print(f"Reserved: {reserved_slots} slots (ramp={num_ramp}, draw={num_draw}, removal={num_removal_single + num_removal_mass})")
        print(f"Flexible: {flex_slots} slots")

        # Start building deck categories using recommendation engine
        if not recommendations.is_loaded():
            recommendations.load_recommendation_engine()

        # Extract commander synergies to seed the deck
        commander_tags = set(commander.get('synergy_tags', []))
        commander_roles = set(commander.get('roles', []))

        print(f"\nCommander synergies: {sorted(commander_tags)}")
        print(f"Commander roles: {sorted(commander_roles)}")

        # Get initial card pool based on commander
        print("\n=== Phase 1: Building core synergies ===")
        core_cards = self._get_synergy_cards(deck_cards, color_identity, flex_slots)
        deck_cards.extend(core_cards)

        # Add required categories
        print("\n=== Phase 2: Adding ramp ===")
        ramp_cards = self._get_role_cards(deck_cards, 'ramp', color_identity, num_ramp)
        deck_cards.extend(ramp_cards)

        print(f"=== Phase 3: Adding card draw ===")
        draw_cards = self._get_role_cards(deck_cards, 'card_draw', color_identity, num_draw)
        deck_cards.extend(draw_cards)

        print(f"=== Phase 4: Adding single-target removal ===")
        removal_cards = self._get_role_cards(deck_cards, 'removal', color_identity, num_removal_single)
        deck_cards.extend(removal_cards)

        print(f"=== Phase 5: Adding board wipes ===")
        wipe_cards = self._get_role_cards(deck_cards, 'board_wipe', color_identity, num_removal_mass)
        deck_cards.extend(wipe_cards)

        # Fill remaining slots with high-synergy cards
        remaining_slots = 100 - num_lands - len(deck_cards)
        if remaining_slots > 0:
            print(f"\n=== Phase 6: Filling {remaining_slots} remaining slots ===")
            filler_cards = self._get_synergy_cards(deck_cards, color_identity, remaining_slots)
            deck_cards.extend(filler_cards)

        # Build optimized mana base
        print(f"\n=== Phase 7: Building mana base ({num_lands} lands) ===")
        lands = self._build_mana_base(deck_cards, color_identity, num_lands)
        deck_cards.extend(lands)

        # Analyze and validate
        print("\n=== Phase 8: Analyzing deck ===")
        result = {
            'cards': deck_cards,
            'mana_curve': self._analyze_mana_curve(deck_cards),
            'color_distribution': self._analyze_color_distribution(deck_cards),
            'deck_composition': self._analyze_composition(deck_cards),
            'validation': self._validate_deck(deck_cards, commander)
        }

        print(f"\n=== Deck build complete! ===")
        print(f"Total cards: {len(deck_cards)}")
        print(f"Validation: {'✅ PASSED' if result['validation']['is_valid'] else '❌ FAILED'}")

        return result

    def _is_valid_commander(self, card: Dict) -> bool:
        """Check if a card can be a commander"""
        type_line = card.get('type_line', '').lower()
        oracle_text = card.get('oracle_text', '').lower()

        # Must be legendary creature or planeswalker
        is_legendary = 'legendary' in type_line
        is_creature = 'creature' in type_line
        is_planeswalker = 'planeswalker' in type_line
        can_be_commander = 'can be your commander' in oracle_text

        return (is_legendary and (is_creature or is_planeswalker)) or can_be_commander

    def _get_synergy_cards(
        self,
        current_deck: List[Dict],
        color_identity: List[str],
        count: int
    ) -> List[Dict]:
        """Get cards that synergize well with current deck"""
        if count <= 0:
            return []

        # Get recommendations based on current deck
        result = recommendations.get_recommendations(
            current_deck,
            color_identity=color_identity,
            limit=count * 3,  # Get extra to filter
            debug=False
        )

        recs = result.get('recommendations', [])

        # Filter out duplicates and select top cards
        current_names = {c['name'] for c in current_deck}
        unique_recs = [r for r in recs if r['name'] not in current_names]

        selected = []
        for rec in unique_recs[:count]:
            card = {
                'name': rec['name'],
                'mana_cost': rec.get('mana_cost', ''),
                'cmc': rec.get('cmc', 0),
                'type_line': rec.get('type_line', ''),
                'oracle_text': rec.get('oracle_text', ''),
                'color_identity': rec.get('color_identity', []),
                'colors': rec.get('colors', []),
                'synergy_score': rec.get('recommendation_score', 0),
                'synergy_tags': rec.get('synergy_tags', []),
                'roles': rec.get('roles', []),
                'quantity': 1
            }
            selected.append(card)
            print(f"  + {card['name']} (synergy: {card['synergy_score']:.1f})")

        return selected

    def _get_role_cards(
        self,
        current_deck: List[Dict],
        role: str,
        color_identity: List[str],
        count: int
    ) -> List[Dict]:
        """Get cards with a specific role"""
        if count <= 0:
            return []

        # Search for cards with the role
        role_cards = recommendations.search_by_role(
            role=role,
            color_identity=color_identity,
            limit=count * 3
        )

        # Filter out duplicates
        current_names = {c['name'] for c in current_deck}
        unique_cards = [c for c in role_cards if c['name'] not in current_names]

        # Score based on synergy with current deck
        deck_tags = Counter()
        for card in current_deck:
            for tag in card.get('synergy_tags', []):
                deck_tags[tag] += 1

        scored = []
        for card in unique_cards:
            card_tags = set(card.get('synergy_tags', []))
            overlap = sum(deck_tags[tag] for tag in card_tags if tag in deck_tags)
            scored.append((overlap, card))

        # Sort by synergy overlap
        scored.sort(key=lambda x: x[0], reverse=True)

        selected = []
        for _, card in scored[:count]:
            card_copy = {
                'name': card['name'],
                'mana_cost': card.get('mana_cost', ''),
                'cmc': card.get('cmc', 0),
                'type_line': card.get('type_line', ''),
                'oracle_text': card.get('oracle_text', ''),
                'color_identity': card.get('color_identity', []),
                'colors': card.get('colors', []),
                'synergy_tags': card.get('synergy_tags', []),
                'roles': card.get('roles', []),
                'quantity': 1
            }
            selected.append(card_copy)
            print(f"  + {card_copy['name']}")

        return selected

    def _build_mana_base(
        self,
        deck_cards: List[Dict],
        color_identity: List[str],
        num_lands: int
    ) -> List[Dict]:
        """
        Build optimized mana base using color requirements

        Analyzes the deck's color needs and builds a land base with:
        - Appropriate color distribution
        - Mix of basics and duals
        - Special lands (utility, card draw, etc.)
        """
        lands = []

        # Count color pips in deck
        color_pips = Counter()
        for card in deck_cards:
            mana_cost = card.get('mana_cost', '')
            for color in ['W', 'U', 'B', 'R', 'G']:
                # Count occurrences of {W}, {U}, etc.
                color_pips[color] += mana_cost.count(f'{{{color}}}')

        print(f"Color pip distribution: {dict(color_pips)}")

        # Calculate land distribution based on pips
        total_pips = sum(color_pips.values())
        if total_pips == 0:
            # Colorless deck
            lands.extend(self._get_basic_lands('Wastes', num_lands))
            return lands

        # Allocate lands by color weight
        color_lands_needed = {}
        for color in color_identity:
            if color in color_pips:
                proportion = color_pips[color] / total_pips
                color_lands_needed[color] = max(3, int(num_lands * proportion * 0.6))  # 60% basics

        print(f"Land allocation: {color_lands_needed}")

        # Reserve slots for special lands
        utility_lands = min(5, num_lands // 10)  # ~10% utility
        dual_lands = min(len(color_identity) * 2, num_lands // 5) if len(color_identity) > 1 else 0

        basic_land_slots = num_lands - utility_lands - dual_lands

        # Add dual lands for multi-color decks
        if len(color_identity) > 1:
            dual_lands_added = self._get_dual_lands(color_identity, dual_lands)
            lands.extend(dual_lands_added)
            print(f"Added {len(dual_lands_added)} dual lands")

        # Add utility lands
        utility_lands_added = self._get_utility_lands(color_identity, utility_lands)
        lands.extend(utility_lands_added)
        print(f"Added {len(utility_lands_added)} utility lands")

        # Fill rest with basics based on color distribution
        basics_added = 0
        for color in sorted(color_identity):
            if color == 'C':
                continue
            needed = color_lands_needed.get(color, 0)
            basic_name = self._get_basic_land_name(color)
            for _ in range(needed):
                if basics_added < basic_land_slots:
                    lands.append(self._create_basic_land(basic_name, color))
                    basics_added += 1

        # Fill remaining slots with most-needed color
        while len(lands) < num_lands and color_identity:
            top_color = max(color_pips.items(), key=lambda x: x[1])[0] if color_pips else color_identity[0]
            basic_name = self._get_basic_land_name(top_color)
            lands.append(self._create_basic_land(basic_name, top_color))

        print(f"Added {basics_added} basic lands")
        print(f"Total lands: {len(lands)}")

        return lands

    def _get_basic_land_name(self, color: str) -> str:
        """Get basic land name for a color"""
        return {
            'W': 'Plains',
            'U': 'Island',
            'B': 'Swamp',
            'R': 'Mountain',
            'G': 'Forest',
            'C': 'Wastes'
        }.get(color, 'Forest')

    def _create_basic_land(self, name: str, color: str) -> Dict:
        """Create a basic land card dict"""
        return {
            'name': name,
            'type_line': f'Basic Land — {name}',
            'mana_cost': '',
            'cmc': 0,
            'oracle_text': '',
            'color_identity': [color] if color != 'C' else [],
            'colors': [],
            'produced_mana': [color],
            'quantity': 1
        }

    def _get_dual_lands(self, color_identity: List[str], count: int) -> List[Dict]:
        """Get dual lands for the color identity"""
        duals = []

        # Simple dual land templates
        color_pairs = [
            (color_identity[i], color_identity[j])
            for i in range(len(color_identity))
            for j in range(i+1, len(color_identity))
        ]

        for i, (c1, c2) in enumerate(color_pairs[:count]):
            name = f"{self._get_basic_land_name(c1)}/{self._get_basic_land_name(c2)} Dual"
            duals.append({
                'name': name,
                'type_line': 'Land',
                'mana_cost': '',
                'cmc': 0,
                'oracle_text': f'{name} enters the battlefield tapped.\nT: Add {{{c1}}} or {{{c2}}}.',
                'color_identity': [c1, c2],
                'colors': [],
                'produced_mana': [c1, c2],
                'quantity': 1
            })

        return duals

    def _get_utility_lands(self, color_identity: List[str], count: int) -> List[Dict]:
        """Get utility lands"""
        utilities = []

        # Add common utility lands
        utility_templates = [
            ('Command Tower', 'T: Add one mana of any color in your commander\'s color identity.', color_identity),
            ('Reliquary Tower', 'You have no maximum hand size.\nT: Add {C}.', ['C']),
            ('Rogue\'s Passage', 'T: Add {C}.\n4, T: Target creature can\'t be blocked this turn.', ['C']),
        ]

        for i, (name, text, colors) in enumerate(utility_templates[:count]):
            utilities.append({
                'name': name,
                'type_line': 'Land',
                'mana_cost': '',
                'cmc': 0,
                'oracle_text': text,
                'color_identity': colors if colors != ['C'] else [],
                'colors': [],
                'produced_mana': colors,
                'quantity': 1
            })

        return utilities

    def _get_basic_lands(self, name: str, count: int) -> List[Dict]:
        """Get multiple basic lands"""
        return [self._create_basic_land(name, 'C') for _ in range(count)]

    def _analyze_mana_curve(self, cards: List[Dict]) -> Dict:
        """Analyze mana curve distribution"""
        curve = Counter()
        for card in cards:
            if 'Land' in card.get('type_line', ''):
                continue
            cmc = int(card.get('cmc', 0))
            curve[cmc] += 1

        return {
            'distribution': dict(curve),
            'average_cmc': sum(cmc * count for cmc, count in curve.items()) / max(sum(curve.values()), 1),
            'total_nonlands': sum(curve.values())
        }

    def _analyze_color_distribution(self, cards: List[Dict]) -> Dict:
        """Analyze color distribution"""
        color_counts = Counter()
        for card in cards:
            for color in card.get('color_identity', []):
                color_counts[color] += 1

        return {
            'counts': dict(color_counts),
            'total': len(cards)
        }

    def _analyze_composition(self, cards: List[Dict]) -> Dict:
        """Analyze deck composition by card types and roles"""
        types = Counter()
        roles = Counter()

        for card in cards:
            type_line = card.get('type_line', '').lower()

            # Count types
            if 'creature' in type_line:
                types['Creatures'] += 1
            if 'instant' in type_line:
                types['Instants'] += 1
            if 'sorcery' in type_line:
                types['Sorceries'] += 1
            if 'artifact' in type_line:
                types['Artifacts'] += 1
            if 'enchantment' in type_line:
                types['Enchantments'] += 1
            if 'planeswalker' in type_line:
                types['Planeswalkers'] += 1
            if 'land' in type_line:
                types['Lands'] += 1

            # Count roles
            for role in card.get('roles', []):
                roles[role] += 1

        return {
            'by_type': dict(types),
            'by_role': dict(roles),
            'total': len(cards)
        }

    def _validate_deck(self, cards: List[Dict], commander: Dict) -> Dict:
        """Validate deck meets Commander format rules"""
        errors = []
        warnings = []

        # Check total cards
        if len(cards) != 100:
            errors.append(f"Deck must have exactly 100 cards (has {len(cards)})")

        # Check singleton
        card_names = Counter(c['name'] for c in cards)
        duplicates = {name: count for name, count in card_names.items() if count > 1 and not self._is_basic_land(name)}
        if duplicates:
            errors.append(f"Deck has duplicates (Commander is singleton): {duplicates}")

        # Check color identity
        commander_colors = set(commander.get('color_identity', []))
        for card in cards:
            card_colors = set(card.get('color_identity', []))
            if not card_colors.issubset(commander_colors):
                errors.append(f"{card['name']} has colors {card_colors} outside commander identity {commander_colors}")

        # Check for commander
        has_commander = any(c.get('is_commander') for c in cards)
        if not has_commander:
            errors.append("Deck must have a commander")

        # Warnings for deck balance
        nonlands = [c for c in cards if 'Land' not in c.get('type_line', '')]
        if len(nonlands) < 30:
            warnings.append(f"Low spell count ({len(nonlands)} nonlands)")

        lands = [c for c in cards if 'Land' in c.get('type_line', '')]
        if len(lands) < 30:
            warnings.append(f"Low land count ({len(lands)} lands)")
        elif len(lands) > 45:
            warnings.append(f"High land count ({len(lands)} lands)")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _is_basic_land(self, name: str) -> bool:
        """Check if a card is a basic land"""
        basics = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes', 'Snow-Covered Plains',
                  'Snow-Covered Island', 'Snow-Covered Swamp', 'Snow-Covered Mountain', 'Snow-Covered Forest']
        return name in basics
