"""
Card Recommendation Engine
Fast searching across 34k+ preprocessed cards for deck recommendations

Uses pre-computed synergy tags and roles for instant lookups.
"""

import json
import time
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

    def calculate_card_contribution(
        self,
        card: Dict,
        deck_cards: List[Dict],
        deck_tags: Optional[Counter] = None,
        deck_roles: Optional[Counter] = None,
        deck_type_counts: Optional[Dict[str, int]] = None
    ) -> float:
        """
        Calculate incremental score contribution of a single card to the deck

        This is much faster than recalculating the entire deck synergy.
        Uses cached deck profile (tags, roles, type_counts) if provided.

        Args:
            card: The card to score
            deck_cards: Current deck
            deck_tags: Pre-computed deck tags (optional, for performance)
            deck_roles: Pre-computed deck roles (optional, for performance)
            deck_type_counts: Pre-computed type counts (optional, for performance)

        Returns:
            Estimated synergy score contribution of this card
        """
        if not self.loaded:
            if not self.load():
                return 0.0

        # Use cached deck profile or compute it
        if deck_tags is None:
            deck_tags = self._extract_deck_tags(deck_cards)
        if deck_roles is None:
            deck_roles = self._extract_deck_roles(deck_cards)
        if deck_type_counts is None:
            deck_type_counts = self._count_card_types(deck_cards)

        # Get preprocessed card data
        card_name = card.get('name')
        preprocessed = self.cards_by_name.get(card_name)

        if not preprocessed:
            return 0.0

        # Calculate synergy score against the deck
        score = self._calculate_synergy_score(
            preprocessed,
            deck_tags,
            deck_roles,
            deck_type_counts,
            debug=False
        )

        return score

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

    def _find_smart_replacements(
        self,
        recommendation: Dict,
        deck_cards: List[Dict],
        deck_scores: List[Dict],
        max_replacements: int = 3
    ) -> List[Dict]:
        """
        Find smart replacement candidates for a recommendation

        Considers:
        - Card type matching (creature → creature, instant → instant)
        - Mana curve balance (prefer similar CMC)
        - Role coverage (don't replace last removal spell)
        - Score improvement

        Args:
            recommendation: The recommended card
            deck_cards: Current deck
            deck_scores: Scored deck cards (sorted by score, weakest first)
            max_replacements: Maximum number of replacements to suggest

        Returns:
            List of replacement suggestions with metadata
        """
        rec_type = recommendation.get('type_line', '').lower()
        rec_cmc = recommendation.get('cmc', 0)
        rec_roles = set(recommendation.get('roles', []))
        rec_score = recommendation.get('recommendation_score', 0)

        # Extract card types from type line
        def get_card_types(type_line: str) -> Set[str]:
            """Extract main card types from type line"""
            type_line = type_line.lower()
            types = set()

            # Check for main types
            if 'creature' in type_line:
                types.add('creature')
            if 'instant' in type_line:
                types.add('instant')
            if 'sorcery' in type_line:
                types.add('sorcery')
            if 'artifact' in type_line:
                types.add('artifact')
            if 'enchantment' in type_line:
                types.add('enchantment')
            if 'planeswalker' in type_line:
                types.add('planeswalker')
            if 'land' in type_line:
                types.add('land')

            return types

        rec_types = get_card_types(rec_type)

        # Count role coverage in deck
        role_counts = Counter()
        for card in deck_cards:
            preprocessed = self.cards_by_name.get(card.get('name'))
            if preprocessed:
                for role in preprocessed.get('roles', []):
                    role_counts[role] += 1

        # Count CMC distribution
        cmc_counts = Counter()
        for card in deck_cards:
            cmc = card.get('cmc', 0)
            if cmc is not None:
                cmc_counts[int(cmc)] += 1

        # Score each potential replacement
        replacement_candidates = []

        for deck_card in deck_scores:
            # Get full card data
            card_name = deck_card['name']
            full_card = next((c for c in deck_cards if c.get('name') == card_name), None)
            if not full_card:
                continue

            preprocessed = self.cards_by_name.get(card_name)
            if not preprocessed:
                continue

            card_type = deck_card.get('type_line', '').lower()
            card_cmc = full_card.get('cmc', 0)
            card_roles = set(preprocessed.get('roles', []))
            card_score = deck_card['synergy_score']

            # Skip if not an improvement
            if card_score >= rec_score:
                continue

            card_types = get_card_types(card_type)

            # Calculate type matching score (0-100)
            type_overlap = len(rec_types & card_types)
            type_score = (type_overlap / max(len(rec_types), 1)) * 100

            # Skip if no type overlap at all (don't replace creature with instant)
            if type_overlap == 0 and rec_types and card_types:
                continue

            # Calculate CMC similarity score (0-100)
            cmc_diff = abs(rec_cmc - card_cmc)
            cmc_score = max(0, 100 - (cmc_diff * 20))  # -20 points per CMC difference

            # Check role coverage - penalize if removing last of a critical role
            role_coverage_penalty = 0
            critical_roles = {'removal', 'board_wipe', 'card_draw', 'ramp'}
            for role in card_roles:
                if role in critical_roles:
                    count_in_deck = role_counts.get(role, 0)
                    if count_in_deck <= 2:  # Last 1-2 cards with this role
                        role_coverage_penalty += 50  # Heavy penalty
                    elif count_in_deck <= 4:
                        role_coverage_penalty += 25  # Moderate penalty

            # Calculate role synergy score (0-100)
            role_overlap = len(rec_roles & card_roles)
            role_score = (role_overlap / max(len(rec_roles | card_roles), 1)) * 100

            # Check mana curve balance - penalize if this CMC slot is already thin
            curve_penalty = 0
            cmc_count = cmc_counts.get(int(card_cmc), 0)
            if cmc_count <= 2:
                curve_penalty = 30  # Penalty for removing from thin CMC slot
            elif cmc_count <= 4:
                curve_penalty = 15

            # Calculate overall replacement quality score
            quality_score = (
                type_score * 0.35 +  # Type matching is most important
                cmc_score * 0.20 +    # CMC similarity
                role_score * 0.20 +   # Role overlap
                (100 - role_coverage_penalty) * 0.15 +  # Role coverage protection
                (100 - curve_penalty) * 0.10   # Curve balance
            )

            # Calculate net score improvement
            score_improvement = rec_score - card_score

            replacement_candidates.append({
                'name': card_name,
                'type_line': card_type,
                'cmc': card_cmc,
                'current_score': card_score,
                'quality_score': quality_score,
                'score_improvement': score_improvement,
                'type_match': type_overlap > 0,
                'cmc_diff': cmc_diff,
                'role_overlap': role_overlap,
                'removes_critical_role': role_coverage_penalty > 0,
                'thins_curve': curve_penalty > 0,
                'match_reasons': []
            })

        # Sort by quality score (best matches first)
        replacement_candidates.sort(key=lambda x: x['quality_score'], reverse=True)

        # Add match reasons for top candidates
        for candidate in replacement_candidates[:max_replacements]:
            reasons = []
            if candidate['type_match']:
                reasons.append(f"Same card type")
            if candidate['cmc_diff'] <= 1:
                reasons.append(f"Similar CMC ({candidate['cmc']:.0f})")
            if candidate['role_overlap'] > 0:
                reasons.append(f"Shares {candidate['role_overlap']} roles")
            if candidate['score_improvement'] > 20:
                reasons.append(f"Large improvement (+{candidate['score_improvement']:.0f})")
            if candidate['removes_critical_role']:
                reasons.append(f"⚠️ Removes critical role")
            if candidate['thins_curve']:
                reasons.append(f"⚠️ Thins mana curve")

            candidate['match_reasons'] = reasons

        return replacement_candidates[:max_replacements]

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

        # Performance monitoring
        perf_start = time.time()
        perf_timings = {}

        # Extract deck's synergy profile
        profile_start = time.time()
        deck_tags = self._extract_deck_tags(deck_cards)
        deck_roles = self._extract_deck_roles(deck_cards)
        deck_type_counts = self._count_card_types(deck_cards)
        deck_card_names = {card['name'] for card in deck_cards}
        perf_timings['deck_profile'] = time.time() - profile_start

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
        scoring_start = time.time()
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

        perf_timings['candidate_scoring'] = time.time() - scoring_start

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
            # Get detailed synergy information
            detailed_synergy = self._get_detailed_synergy_info(
                card,
                deck_cards,
                deck_tags,
                deck_roles
            )
            recommendations.append({
                **card,
                'recommendation_score': card_scores[idx],
                'synergy_reasons': self._explain_synergy(card, deck_tags, deck_roles),
                'synergy_details': detailed_synergy  # NEW: Detailed info for tooltips
            })

        result = {'recommendations': recommendations}

        # Optionally score deck cards for comparison
        if include_deck_scores:
            deck_scoring_start = time.time()

            # Score deck cards (excluding lands and sideboard)
            deck_scores = self.score_deck_cards(deck_cards, exclude_lands=True, exclude_sideboard=True)
            result['deck_scores'] = deck_scores

            # Calculate total deck synergy
            total_synergy = self.calculate_total_deck_synergy(deck_cards, exclude_lands=True, exclude_sideboard=True)
            result['total_deck_synergy'] = total_synergy

            perf_timings['deck_scoring'] = time.time() - deck_scoring_start

            # OPTIMIZED: Cache deck profile for performance
            # Instead of recalculating full deck synergy for each recommendation (O(n²)),
            # we calculate each recommendation's incremental contribution (O(n))
            # This changes complexity from O(n² × m) to O(n × m) where m = recommendations
            optimization_start = time.time()

            # Get current total deck synergy score
            current_total_score = total_synergy.get('total_score', 0)

            # Pre-compute deck profile once for all recommendations
            cached_deck_tags = self._extract_deck_tags(deck_cards)
            cached_deck_roles = self._extract_deck_roles(deck_cards)
            cached_deck_type_counts = self._count_card_types(deck_cards)

            for rec in recommendations:
                # FAST: Calculate incremental contribution only (O(n) instead of O(n²))
                # Create card dict for contribution calculation
                new_card = {
                    'name': rec.get('name'),
                    'type_line': rec.get('type_line', ''),
                    'synergy_tags': rec.get('synergy_tags', []),
                    'roles': rec.get('roles', []),
                    'board': 'mainboard',
                    'cmc': rec.get('cmc', 0)
                }

                # Calculate how much this card contributes to deck synergy
                card_contribution = self.calculate_card_contribution(
                    new_card,
                    deck_cards,
                    deck_tags=cached_deck_tags,
                    deck_roles=cached_deck_roles,
                    deck_type_counts=cached_deck_type_counts
                )

                # Estimate new total score (approximation: assumes existing cards' scores don't change much)
                # This is accurate enough for comparison and 10-20x faster
                estimated_new_score = current_total_score + card_contribution
                score_improvement = card_contribution

                # Add to recommendation
                rec['score_before'] = current_total_score
                rec['score_after'] = estimated_new_score
                rec['score_change'] = score_improvement

                # Find smart replacement candidates
                smart_replacements = self._find_smart_replacements(
                    rec,
                    deck_cards,
                    deck_scores,
                    max_replacements=3
                )
                rec['smart_replacements'] = smart_replacements

            perf_timings['score_optimization'] = time.time() - optimization_start

        # Calculate total time
        perf_timings['total'] = time.time() - perf_start

        # Add performance info to result (useful for monitoring)
        result['performance'] = perf_timings

        if debug:
            print("\n=== PERFORMANCE METRICS ===")
            print(f"Deck profile extraction: {perf_timings.get('deck_profile', 0):.3f}s")
            print(f"Candidate scoring: {perf_timings.get('candidate_scoring', 0):.3f}s")
            if 'deck_scoring' in perf_timings:
                print(f"Deck scoring: {perf_timings.get('deck_scoring', 0):.3f}s")
            if 'score_optimization' in perf_timings:
                print(f"Score optimization (FAST): {perf_timings.get('score_optimization', 0):.3f}s")
            print(f"Total time: {perf_timings['total']:.3f}s")
            print(f"Cards evaluated: {len(card_scores)}")
            print(f"Deck size: {len(deck_cards)} cards")

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
                         'equipment', 'equipment_matters', 'artifact_synergy', 'enchantment_synergy',
                         'attack_trigger', 'block_trigger', 'trigger_doubler',
                         'cast_creature_trigger', 'cast_spell_trigger',
                         'sac_creature', 'sac_token', 'sac_artifact', 'sac_land', 'sac_permanent', 'sac_nonland'}

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
            # Trigger synergies
            ('attack_trigger', 'trigger_doubler', 5, 1),  # Attack triggers + doublers (Annie Joins Up, etc.)
            ('trigger_doubler', 'attack_trigger', 1, 5),  # Doublers + attack triggers
            ('block_trigger', 'trigger_doubler', 5, 1),   # Block triggers + doublers
            ('trigger_doubler', 'block_trigger', 1, 5),   # Doublers + block triggers
            ('cast_creature_trigger', 'trigger_doubler', 5, 1),  # Cast creature triggers + doublers
            ('trigger_doubler', 'cast_creature_trigger', 1, 5),  # Doublers + cast creature triggers
            ('cast_spell_trigger', 'trigger_doubler', 5, 1),     # Cast spell triggers + doublers
            ('trigger_doubler', 'cast_spell_trigger', 1, 5),     # Doublers + cast spell triggers
            # Specific sacrifice synergies
            ('token_gen', 'sac_creature', 5, 3),   # Token generators + creature sacrifice
            ('sac_creature', 'token_gen', 3, 5),   # Creature sacrifice + token generators
            ('token_gen', 'sac_token', 5, 3),      # Token generators + token sacrifice
            ('sac_token', 'token_gen', 3, 5),      # Token sacrifice + token generators
            ('death_trigger', 'sac_creature', 3, 3),  # Death triggers + creature sacrifice
            ('sac_creature', 'death_trigger', 3, 3),  # Creature sacrifice + death triggers
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

        # ============================================================================
        # PENALTIES (reduce score for mismatched synergies)
        # ============================================================================

        # Penalty for equipment-only token generation in creature token decks
        # Cards like "Firion, Wild Rose Warrior" generate equipment tokens, not creature tokens
        # They shouldn't score highly in decks focused on creature token strategies
        if 'token_gen_equipment' in card_tags and 'token_gen_creature' not in card_tags:
            # This card ONLY generates equipment tokens
            creature_token_count = deck_tags.get('token_gen_creature', 0)
            if creature_token_count >= 5:  # Deck has significant creature token generation
                # Apply penalty scaled to how creature-token-focused the deck is
                penalty = min(creature_token_count * 3, 30)  # Cap at 30 point penalty
                score -= penalty
                if debug:
                    score_breakdown.append(f"PENALTY: equipment-only tokens in creature token deck: -{penalty:.1f}")

        # Penalty for spell recursion in non-spell decks
        # Cards like "Repository Skaab" return instant/sorcery from graveyard
        # They shouldn't score highly if the deck has few instants/sorceries
        if 'recursion_spell' in card_tags:
            spell_count = deck_type_counts.get('instants', 0) + deck_type_counts.get('sorceries', 0)
            if spell_count < 10:  # Deck has few spells
                # Apply penalty scaled to how few spells the deck has
                # Maximum penalty at 0 spells, decreases as spell count approaches 10
                penalty = (10 - spell_count) * 4  # Up to 40 point penalty for 0 spells
                score -= penalty
                if debug:
                    score_breakdown.append(f"PENALTY: spell recursion in low-spell deck ({spell_count} spells): -{penalty:.1f}")

        # Penalty for creature recursion in non-creature decks
        # Cards that only reanimate creatures shouldn't score highly in spell-heavy decks
        if 'recursion_creature' in card_tags:
            creature_count = deck_type_counts.get('creatures', 0)
            if creature_count < 15:  # Deck has few creatures
                # Apply penalty for decks with very few creatures
                penalty = (15 - creature_count) * 2  # Up to 30 point penalty
                score -= penalty
                if debug:
                    score_breakdown.append(f"PENALTY: creature recursion in low-creature deck ({creature_count} creatures): -{penalty:.1f}")

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

    def _get_detailed_synergy_info(
        self,
        card: Dict,
        deck_cards: List[Dict],
        deck_tags: Counter,
        deck_roles: Counter
    ) -> Dict:
        """
        Generate detailed synergy information including specific card partners

        Returns:
            Dict with synergy details including partners and strength
        """
        card_tags = set(card.get('synergy_tags', []))
        card_roles = set(card.get('roles', []))
        card_name = card.get('name', '')

        # Track synergy partners by tag
        synergy_partners = {}  # tag -> [(card_name, strength, reason)]
        combo_partners = []  # [(card_names, combo_type, description)]

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
            'recursion': 'Recursion effects',
            'trigger_doubler': 'Doubles triggers',
        }

        # Find specific synergy partners
        for tag in card_tags:
            if tag in deck_tags and tag in tag_explanations:
                partners = []

                # Find cards with matching or complementary tags
                for deck_card in deck_cards:
                    deck_card_name = deck_card.get('name', '')
                    if deck_card_name == card_name:
                        continue

                    # Get preprocessed data
                    preprocessed = self.cards_by_name.get(deck_card_name)
                    if not preprocessed:
                        continue

                    deck_card_tags = set(preprocessed.get('synergy_tags', []))

                    # Direct tag overlap
                    if tag in deck_card_tags:
                        strength = 'medium'
                        reason = f"Both have {tag}"
                        partners.append((deck_card_name, strength, reason))

                    # Complementary tags (enabler + payoff)
                    complementary_map = {
                        'has_etb': 'flicker',
                        'flicker': 'has_etb',
                        'token_gen': 'sacrifice_outlet',
                        'sacrifice_outlet': 'token_gen',
                        'death_trigger': 'sacrifice_outlet',
                        'graveyard': 'recursion',
                        'self_mill': 'graveyard',
                        'equipment': 'equipment_matters',
                        'equipment_matters': 'equipment',
                        'attack_trigger': 'trigger_doubler',
                        'trigger_doubler': 'attack_trigger',
                    }

                    if tag in complementary_map:
                        complement = complementary_map[tag]
                        if complement in deck_card_tags:
                            strength = 'strong'
                            reason = f"Complementary: {tag} + {complement}"
                            partners.append((deck_card_name, strength, reason))

                # Sort by strength and limit to top 5
                strength_order = {'strong': 0, 'medium': 1, 'weak': 2}
                partners.sort(key=lambda x: strength_order.get(x[1], 3))
                synergy_partners[tag] = partners[:5]

        # Detect 2-card combos
        combo_patterns = [
            (['has_etb', 'flicker'], 'ETB Loop', 'Infinite ETB triggers'),
            (['token_gen', 'sacrifice_outlet', 'death_trigger'], 'Aristocrats', 'Token sacrifice value engine'),
            (['graveyard', 'recursion', 'self_mill'], 'Graveyard Loop', 'Recurring threats from graveyard'),
            (['equipment', 'equipment_matters'], 'Voltron', 'Equipment synergy'),
            (['trigger_doubler', 'attack_trigger'], 'Trigger Amplifier', 'Double attack triggers'),
        ]

        for pattern_tags, combo_type, description in combo_patterns:
            # Check if card has any tags from pattern
            if any(tag in card_tags for tag in pattern_tags):
                # Find partners that complete the pattern
                for deck_card in deck_cards:
                    deck_card_name = deck_card.get('name', '')
                    if deck_card_name == card_name:
                        continue

                    preprocessed = self.cards_by_name.get(deck_card_name)
                    if not preprocessed:
                        continue

                    deck_card_tags = set(preprocessed.get('synergy_tags', []))

                    # Check if together they form the combo
                    combined_tags = card_tags | deck_card_tags
                    if all(tag in combined_tags for tag in pattern_tags[:2]):  # 2-card combo
                        combo_partners.append(([deck_card_name], combo_type, description))

        return {
            'synergy_partners': synergy_partners,
            'combo_partners': combo_partners[:3],  # Top 3 combos
            'tag_explanations': tag_explanations
        }

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
