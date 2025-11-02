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

    def calculate_total_deck_synergy(
        self,
        deck_cards: List[Dict],
        exclude_lands: bool = True,
        exclude_sideboard: bool = True
    ) -> Dict:
        """
        Calculate total synergy score for the entire deck

        Returns:
            Dict with total_score, average_score, card_count
        """
        scored_cards = self.score_deck_cards(deck_cards, exclude_lands, exclude_sideboard)

        if not scored_cards:
            return {'total_score': 0.0, 'average_score': 0.0, 'card_count': 0}

        total = sum(card['synergy_score'] for card in scored_cards)
        count = len(scored_cards)
        average = total / count if count > 0 else 0.0

        return {
            'total_score': total,
            'average_score': average,
            'card_count': count
        }

    def score_deck_cards(
        self,
        deck_cards: List[Dict],
        exclude_lands: bool = True,
        exclude_sideboard: bool = True
    ) -> List[Dict]:
        """
        Score each card in the deck against the rest of the deck

        Args:
            deck_cards: Current cards in the deck
            exclude_lands: Don't score lands (they have no synergy)
            exclude_sideboard: Don't score sideboard/maybeboard cards

        Returns:
            List of deck cards with their synergy scores
        """
        if not self.loaded:
            if not self.load():
                return []

        scored_cards = []

        for i, card in enumerate(deck_cards):
            # Skip sideboard/maybeboard cards
            if exclude_sideboard:
                board = card.get('board', 'mainboard')
                if board in ['sideboard', 'maybeboard']:
                    continue

            # Skip lands
            if exclude_lands:
                type_line = card.get('type_line', '').lower()
                # Skip pure lands (not MDFCs with land on one side)
                if '//' not in type_line and 'land' in type_line:
                    continue

            # Create a deck without this card
            deck_without_card = deck_cards[:i] + deck_cards[i+1:]

            # Extract synergy profile of deck without this card
            deck_tags = self._extract_deck_tags(deck_without_card)
            deck_roles = self._extract_deck_roles(deck_without_card)
            deck_type_counts = self._count_card_types(deck_without_card)

            # Get preprocessed card data
            card_name = card.get('name')
            preprocessed = self.cards_by_name.get(card_name)

            if preprocessed:
                # Score this card against the rest of the deck
                score = self._calculate_synergy_score(
                    preprocessed,
                    deck_tags,
                    deck_roles,
                    deck_type_counts,
                    debug=False
                )

                scored_cards.append({
                    'name': card_name,
                    'synergy_score': score,
                    'synergy_reasons': self._explain_synergy(preprocessed, deck_tags, deck_roles),
                    'type_line': card.get('type_line', '')
                })
            else:
                # Card not in preprocessed database
                scored_cards.append({
                    'name': card_name,
                    'synergy_score': 0.0,
                    'synergy_reasons': ['Card not in database'],
                    'type_line': card.get('type_line', '')
                })

        # Sort by score (lowest first - these are candidates for replacement)
        scored_cards.sort(key=lambda x: x['synergy_score'])

        return scored_cards

    def get_recommendations(
        self,
        deck_cards: List[Dict],
        color_identity: Optional[List[str]] = None,
        limit: int = 10,
        debug: bool = False,
        include_deck_scores: bool = False
    ) -> Dict:
        """
        Get top card recommendations for a deck

        Args:
            deck_cards: Current cards in the deck
            color_identity: Color identity filter (e.g., ['W', 'U', 'B'])
            limit: Number of recommendations to return
            debug: Enable debug output showing scoring breakdown
            include_deck_scores: Also score cards in the deck for comparison

        Returns:
            Dict with 'recommendations' and optionally 'deck_scores'
        """
        if not self.loaded:
            if not self.load():
                return {'recommendations': [], 'deck_scores': []}

        # Extract deck's synergy profile
        deck_tags = self._extract_deck_tags(deck_cards)
        deck_roles = self._extract_deck_roles(deck_cards)
        deck_type_counts = self._count_card_types(deck_cards)
        deck_card_names = {card['name'] for card in deck_cards}

        if debug:
            print("\n=== DECK TAG DISTRIBUTION ===")
            print("Top 20 tags:")
            for tag, count in deck_tags.most_common(20):
                print(f"  {tag}: {count}")
            print("\nTop 10 roles:")
            for role, count in deck_roles.most_common(10):
                print(f"  {role}: {count}")
            print("\nCard type counts:")
            for card_type, count in deck_type_counts.items():
                print(f"  {card_type}: {count}")

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

            # Skip lands - they create noise in recommendations
            # Lands have generic utility that isn't strategically interesting
            card_type = card.get('type_line', '').lower()
            if '//' not in card_type and 'land' in card_type:
                continue

            # Calculate synergy score
            score = self._calculate_synergy_score(
                card,
                deck_tags,
                deck_roles,
                deck_type_counts,
                debug=False  # Don't debug all cards, only top ones
            )

            if score > 0:
                card_scores[idx] = score

        # Get top N recommendations
        top_indices = sorted(card_scores.keys(), key=lambda i: card_scores[i], reverse=True)[:limit]

        if debug:
            print("\n=== TOP RECOMMENDATIONS DEBUG ===")
            for idx in top_indices:
                card = self.cards[idx]
                # Re-calculate with debug enabled to show breakdown
                self._calculate_synergy_score(card, deck_tags, deck_roles, deck_type_counts, debug=True)

        recommendations = []
        for idx in top_indices:
            card = self.cards[idx]
            recommendations.append({
                **card,
                'recommendation_score': card_scores[idx],
                'synergy_reasons': self._explain_synergy(card, deck_tags, deck_roles)
            })

        result = {'recommendations': recommendations}

        # Optionally score deck cards for comparison
        if include_deck_scores:
            # Score deck cards (excluding lands and sideboard)
            deck_scores = self.score_deck_cards(deck_cards, exclude_lands=True, exclude_sideboard=True)
            result['deck_scores'] = deck_scores

            # Calculate total deck synergy
            total_synergy = self.calculate_total_deck_synergy(deck_cards, exclude_lands=True, exclude_sideboard=True)
            result['total_deck_synergy'] = total_synergy

            # Add replacement suggestions to recommendations
            # Find weakest cards in deck
            weakest_threshold = deck_scores[len(deck_scores) // 3]['synergy_score'] if deck_scores else 0

            for rec in recommendations:
                rec_score = rec['recommendation_score']
                # Find cards in deck that this recommendation would be better than
                worse_cards = [dc for dc in deck_scores if dc['synergy_score'] < rec_score and dc['synergy_score'] < weakest_threshold]
                if worse_cards:
                    rec['could_replace'] = worse_cards[:3]  # Top 3 replacement candidates
                else:
                    rec['could_replace'] = []

        return result

    def _extract_deck_tags(self, deck_cards: List[Dict]) -> Counter:
        """
        Extract synergy tag counts from deck

        Only counts mainboard cards - excludes sideboard/maybeboard
        """
        tag_counts = Counter()

        for card in deck_cards:
            # Skip sideboard/maybeboard cards
            board = card.get('board', 'mainboard')
            if board in ['sideboard', 'maybeboard']:
                continue

            # Get tags from preprocessed card if available
            card_name = card.get('name')
            preprocessed = self.cards_by_name.get(card_name)

            if preprocessed:
                tags = preprocessed.get('synergy_tags', [])
                tag_counts.update(tags)

        return tag_counts

    def _extract_deck_roles(self, deck_cards: List[Dict]) -> Counter:
        """
        Extract role counts from deck

        Only counts mainboard cards - excludes sideboard/maybeboard
        """
        role_counts = Counter()

        for card in deck_cards:
            # Skip sideboard/maybeboard cards
            board = card.get('board', 'mainboard')
            if board in ['sideboard', 'maybeboard']:
                continue

            card_name = card.get('name')
            preprocessed = self.cards_by_name.get(card_name)

            if preprocessed:
                roles = preprocessed.get('roles', [])
                role_counts.update(roles)

        return role_counts

    def _count_card_types(self, deck_cards: List[Dict]) -> Dict[str, int]:
        """
        Count card types in deck for global synergies

        Returns counts of: artifacts, equipment, creatures, instants, sorceries, lands, etc.
        Only counts mainboard cards
        """
        counts = {
            'artifacts': 0,
            'equipment': 0,
            'creatures': 0,
            'instants': 0,
            'sorceries': 0,
            'lands': 0,
            'enchantments': 0,
            'planeswalkers': 0,
            'permanents': 0,  # Everything except instants/sorceries
        }

        for card in deck_cards:
            # Skip sideboard/maybeboard
            board = card.get('board', 'mainboard')
            if board in ['sideboard', 'maybeboard']:
                continue

            type_line = card.get('type_line', '').lower()

            # Count specific types
            if 'artifact' in type_line:
                counts['artifacts'] += 1
            if 'equipment' in type_line:
                counts['equipment'] += 1
            if 'creature' in type_line:
                counts['creatures'] += 1
            if 'instant' in type_line:
                counts['instants'] += 1
            if 'sorcery' in type_line:
                counts['sorceries'] += 1
            if 'land' in type_line:
                counts['lands'] += 1
            if 'enchantment' in type_line:
                counts['enchantments'] += 1
            if 'planeswalker' in type_line:
                counts['planeswalkers'] += 1

            # Count permanents (not instant/sorcery)
            if 'instant' not in type_line and 'sorcery' not in type_line:
                counts['permanents'] += 1

        return counts

    def _calculate_synergy_score(
        self,
        card: Dict,
        deck_tags: Counter,
        deck_roles: Counter,
        deck_type_counts: Dict[str, int],
        debug: bool = False
    ) -> float:
        """
        Calculate how well a card synergizes with the deck

        Multi-level synergy scoring:
        1. LOCAL (pairwise): Tag overlap (e.g., equipment + equipment_matters)
        2. THREE-WAY: Requires 3 components (e.g., artifact recursion needs artifacts + graveyard + recursion)
        3. GLOBAL (scaling): Scales with deck composition (e.g., Inspiring Statuary scales with artifact count)

        Scoring weights:
        - Generic utility tags: 0.1 per card
        - Strategic tags: 0.5 per card
        - Complementary pairs: +50 points
        - Three-way synergies: +30 points
        - Global scaling: 0.3-0.5 per relevant card (capped)
        - Tribal: +100 for 10+ (real tribal), +5 per card otherwise
        """
        score = 0.0
        score_breakdown = []

        card_tags = set(card.get('synergy_tags', []))
        card_roles = set(card.get('roles', []))

        # Tag weights - generic utility gets low weight, strategic synergies get higher weight
        generic_tags = {'ramp', 'card_draw', 'removal', 'graveyard', 'counters', 'protection'}
        strategic_tags = {'self_mill', 'mill', 'death_trigger', 'sacrifice_outlet', 'token_gen',
                         'has_etb', 'flicker', 'untap_others', 'mana_ability', 'spellslinger',
                         'equipment', 'equipment_matters', 'artifact_synergy', 'enchantment_synergy'}

        # Tag synergy with reduced weights
        for tag in card_tags:
            if tag in deck_tags:
                count = deck_tags[tag]
                if tag in generic_tags:
                    # Generic utility: 0.1 per card (max ~6 points for 60 cards)
                    points = 0.1 * count
                    score += points
                    if debug:
                        score_breakdown.append(f"{tag} (generic): +{points:.1f} ({count} cards)")
                elif tag in strategic_tags:
                    # Strategic synergy: 0.5 per card (max ~30 points for 60 cards)
                    points = 0.5 * count
                    score += points
                    if debug:
                        score_breakdown.append(f"{tag} (strategic): +{points:.1f} ({count} cards)")
                else:
                    # Default: 0.3 per card
                    points = 0.3 * count
                    score += points
                    if debug:
                        score_breakdown.append(f"{tag} (default): +{points:.1f} ({count} cards)")

        # Role synergy (also reduced)
        for role in card_roles:
            if role in deck_roles:
                points = 0.5 * deck_roles[role]
                score += points
                if debug:
                    score_breakdown.append(f"role:{role}: +{points:.1f}")

        # Complementary mechanics bonus
        # Only apply when BOTH tags show the deck has committed to the strategy
        # Format: (enabler_tag, payoff_tag, min_enabler, min_payoff)
        complementary_pairs = [
            ('has_etb', 'flicker', 5, 3),          # Need 5+ ETB cards and 3+ flicker effects
            ('flicker', 'has_etb', 3, 5),          # Or 3+ flicker and 5+ ETB
            ('token_gen', 'sacrifice_outlet', 5, 3),  # Need token generators and outlets
            ('sacrifice_outlet', 'token_gen', 3, 5),  # Or outlets and token gen
            ('death_trigger', 'sacrifice_outlet', 3, 3),  # Death triggers need outlets
            ('sacrifice_outlet', 'death_trigger', 3, 3),  # Outlets need death triggers
            ('graveyard', 'recursion', 5, 3),      # Graveyard cards need recursion
            ('self_mill', 'graveyard', 3, 5),      # Self-mill enables graveyard
            ('mill', 'graveyard', 3, 5),           # Mill enables graveyard
            ('equipment', 'equipment_matters', 3, 5),  # Equipment + equipment payoffs
            ('equipment_matters', 'equipment', 5, 3),  # Equipment payoffs + equipment
        ]

        for tag1, tag2, min1, min2 in complementary_pairs:
            if tag1 in card_tags and tag2 in deck_tags:
                # Only bonus if deck is COMMITTED to both sides of the combo
                tag1_in_deck = deck_tags.get(tag1, 0)
                tag2_in_deck = deck_tags.get(tag2, 0)

                if tag1_in_deck >= min1 and tag2_in_deck >= min2:
                    score += 50.0
                    if debug:
                        score_breakdown.append(f"complementary {tag1}+{tag2}: +50.0 (deck has {tag1_in_deck} {tag1}, {tag2_in_deck} {tag2})")
                    break  # Only count once per card

        # Tribal synergy bonus - only meaningful if deck has real tribal theme
        card_tribes = {tag.replace('tribal_', '') for tag in card_tags if tag.startswith('tribal_')}
        deck_tribes = {tag.replace('tribal_', '') for tag in deck_tags if tag.startswith('tribal_')}

        for tribe in card_tribes & deck_tribes:
            tribe_count = deck_tags.get(f'tribal_{tribe}', 0)
            # Only give tribal bonus if deck has 10+ of that tribe (real tribal theme)
            # Otherwise tribal overlap is just incidental (e.g., "human" appears on many cards)
            if tribe_count >= 10:
                score += 100.0  # Strong tribal bonus for dedicated tribal decks
                if debug:
                    score_breakdown.append(f"tribal {tribe}: +100.0 ({tribe_count} cards)")
            else:
                # Small bonus for incidental tribal overlap
                score += 5.0 * tribe_count  # 15 points for 3 humans, 50 points for 10 humans
                if debug:
                    score_breakdown.append(f"tribal {tribe} (minor): +{5.0 * tribe_count:.1f} ({tribe_count} cards)")

        # ============================================================================
        # GLOBAL SYNERGIES (scales with deck composition)
        # ============================================================================

        # Scales with artifacts (Inspiring Statuary, Jhoira's Familiar, etc.)
        if 'scales_with_artifacts' in card_tags:
            artifact_count = deck_type_counts.get('artifacts', 0)
            if artifact_count >= 10:  # Meaningful artifact count
                points = min(0.4 * artifact_count, 20.0)  # Cap at 20 points (50 artifacts)
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with artifacts: +{points:.1f} ({artifact_count} artifacts)")

        # Scales with equipment (Hammer of Nazahn, Heavenly Blademaster, etc.)
        if 'scales_with_equipment' in card_tags:
            equipment_count = deck_type_counts.get('equipment', 0)
            if equipment_count >= 5:  # Meaningful equipment count
                points = min(0.5 * equipment_count, 20.0)  # Cap at 20 points (40 equipment)
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with equipment: +{points:.1f} ({equipment_count} equipment)")

        # Scales with spells (Sword of Once and Future, Aria of Flame, etc.)
        if 'scales_with_spells' in card_tags:
            spell_count = deck_type_counts.get('instants', 0) + deck_type_counts.get('sorceries', 0)
            if spell_count >= 10:
                points = min(0.3 * spell_count, 15.0)  # Cap at 15 points
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with spells: +{points:.1f} ({spell_count} instants/sorceries)")

        # Scales with permanents (Deadly Brew, Ulvenwald Mysteries, etc.)
        if 'scales_with_permanents' in card_tags:
            permanent_count = deck_type_counts.get('permanents', 0)
            if permanent_count >= 20:
                points = min(0.2 * permanent_count, 15.0)  # Cap at 15 points
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with permanents: +{points:.1f} ({permanent_count} permanents)")

        # Scales with creatures
        if 'scales_with_creatures' in card_tags:
            creature_count = deck_type_counts.get('creatures', 0)
            if creature_count >= 15:
                points = min(0.3 * creature_count, 15.0)
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with creatures: +{points:.1f} ({creature_count} creatures)")

        # Scales with lands
        if 'scales_with_lands' in card_tags:
            land_count = deck_type_counts.get('lands', 0)
            if land_count >= 20:
                points = min(0.2 * land_count, 10.0)  # Lower cap - lands are expected
                score += points
                if debug:
                    score_breakdown.append(f"GLOBAL: scales with lands: +{points:.1f} ({land_count} lands)")

        # ============================================================================
        # THREE-WAY SYNERGIES (requires multiple components)
        # ============================================================================

        # Land recursion (Conduit of Worlds: needs lands + graveyard + ramp strategy)
        if 'recursion_land' in card_tags:
            has_lands = deck_type_counts.get('lands', 0) >= 25
            has_graveyard = 'graveyard' in deck_tags and deck_tags['graveyard'] >= 5
            if has_lands and has_graveyard:
                score += 30.0
                if debug:
                    score_breakdown.append(f"THREE-WAY: land recursion (lands+graveyard+ramp): +30.0")

        # Artifact recursion (needs artifacts + graveyard + recursion effects)
        if 'recursion_artifact' in card_tags:
            has_artifacts = deck_type_counts.get('artifacts', 0) >= 15
            has_graveyard = 'graveyard' in deck_tags and deck_tags['graveyard'] >= 5
            if has_artifacts and has_graveyard:
                score += 30.0
                if debug:
                    score_breakdown.append(f"THREE-WAY: artifact recursion (artifacts+graveyard): +30.0")

        # Creature recursion (needs creatures + graveyard + recursion)
        if 'recursion_creature' in card_tags:
            has_creatures = deck_type_counts.get('creatures', 0) >= 20
            has_graveyard = 'graveyard' in deck_tags and deck_tags['graveyard'] >= 5
            if has_creatures and has_graveyard:
                score += 30.0
                if debug:
                    score_breakdown.append(f"THREE-WAY: creature recursion (creatures+graveyard): +30.0")

        # Spell recursion (needs instants/sorceries + graveyard + spellslinger)
        if 'recursion_spell' in card_tags:
            spell_count = deck_type_counts.get('instants', 0) + deck_type_counts.get('sorceries', 0)
            has_spells = spell_count >= 10
            has_graveyard = 'graveyard' in deck_tags and deck_tags['graveyard'] >= 3
            if has_spells and has_graveyard:
                score += 30.0
                if debug:
                    score_breakdown.append(f"THREE-WAY: spell recursion (spells+graveyard): +30.0")

        # Equipment enabler (Ardenn: needs equipment + creatures + equipment_matters)
        if 'equipment_enabler' in card_tags:
            has_equipment = deck_type_counts.get('equipment', 0) >= 5
            has_creatures = deck_type_counts.get('creatures', 0) >= 15
            has_equipment_matters = 'equipment_matters' in deck_tags and deck_tags['equipment_matters'] >= 5
            if has_equipment and has_creatures and has_equipment_matters:
                score += 30.0
                if debug:
                    score_breakdown.append(f"THREE-WAY: equipment enabler (equipment+creatures+synergy): +30.0")

        if debug:
            print(f"\n{card['name']} scoring breakdown:")
            print(f"  Card tags: {sorted(card_tags)}")
            print(f"  Score breakdown:")
            for line in score_breakdown:
                print(f"    {line}")
            print(f"  TOTAL: {score}")

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
            'mill': 'Mills cards',
            'self_mill': 'Self-mill effect',
            'graveyard': 'Graveyard interaction',
            'removal': 'Removes threats',
            'protection': 'Protects permanents',
            'counters': '+1/+1 counters theme',
            'untap_others': 'Untaps other permanents',
            'tribal_payoff': 'Tribal synergy payoff',
            'equipment': 'Equipment card',
            'equipment_matters': 'Equipment synergy',
            'artifact_synergy': 'Artifact synergy',
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
        if 'self_mill' in card_tags and 'graveyard' in deck_tags:
            reasons.append("Self-mill enables graveyard strategy")
        if 'mill' in card_tags and 'graveyard' in deck_tags:
            reasons.append("Mill effects for graveyard payoffs")
        if 'equipment' in card_tags and 'equipment_matters' in deck_tags:
            reasons.append("Equipment for equipment payoffs")
        if 'equipment_matters' in card_tags and 'equipment' in deck_tags:
            reasons.append("Equipment synergy for voltron strategy")

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
    limit: int = 10,
    debug: bool = False,
    include_deck_scores: bool = False
) -> Dict:
    """
    Get top card recommendations for a deck

    Example:
        result = get_recommendations(
            deck_cards=current_deck,
            color_identity=['W', 'U'],
            limit=10,
            include_deck_scores=True  # Also score cards in deck
        )
        # result = {
        #   'recommendations': [...],
        #   'deck_scores': [...]  # if include_deck_scores=True
        # }
    """
    return _recommendation_engine.get_recommendations(deck_cards, color_identity, limit, debug, include_deck_scores)


def score_deck_cards(deck_cards: List[Dict], exclude_lands: bool = True, exclude_sideboard: bool = True) -> List[Dict]:
    """
    Score each card in the deck against the rest of the deck

    Returns list sorted by score (lowest first = weakest cards)
    """
    return _recommendation_engine.score_deck_cards(deck_cards, exclude_lands, exclude_sideboard)


def calculate_total_deck_synergy(deck_cards: List[Dict], exclude_lands: bool = True, exclude_sideboard: bool = True) -> Dict:
    """
    Calculate total synergy score for entire deck

    Returns: {'total_score': float, 'average_score': float, 'card_count': int}
    """
    return _recommendation_engine.calculate_total_deck_synergy(deck_cards, exclude_lands, exclude_sideboard)


def search_by_tag(tag: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """Search for cards by synergy tag"""
    return _recommendation_engine.search_by_tag(tag, color_identity, limit)


def search_by_role(role: str, color_identity: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """Search for cards by role"""
    return _recommendation_engine.search_by_role(role, color_identity, limit)


def is_loaded() -> bool:
    """Check if recommendation engine is loaded"""
    return _recommendation_engine.loaded
