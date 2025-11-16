"""
Deck Archetype Detector

Analyzes deck composition to detect strategy archetypes and provide
AI priority adjustments for synergy-aware simulation.

Supported Archetypes:
- Aristocrats: Death triggers + sacrifice outlets
- Tokens: Token generators + doublers
- Voltron: Equipment/auras + big commander
- Spellslinger: Instants/sorceries + prowess/storm
- Go-Wide: Many small creatures
- Counters: +1/+1 counters + proliferate
- Reanimator: Reanimation + discard/mill
- Ramp: Mana acceleration
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Import extractors
try:
    from src.utils.aristocrats_extractors import (
        has_death_trigger,
        is_sacrifice_outlet,
        creates_tokens as aristocrats_creates_tokens
    )
    from src.utils.token_extractors import (
        extract_token_creation,
        extract_token_doublers
    )
    from src.utils.graveyard_extractors import (
        extract_reanimation,
        extract_graveyard_fill
    )
    from src.utils.combat_extractors import extract_pump_effects
    from src.utils.ramp_extractors import extract_mana_rocks, extract_mana_dorks, extract_land_ramp
except ImportError:
    # Fallback imports for compatibility
    print("Warning: Could not import extractor utilities. Archetype detection may be limited.")


class DeckArchetypeDetector:
    """Detects deck archetypes and provides AI priority adjustments."""

    # Priority score ranges for different card types
    PRIORITY_SCORES = {
        # Aristocrats priorities
        'sacrifice_outlets': 900,
        'death_triggers': 850,
        'death_drain_triggers': 875,
        'token_generators_aristocrats': 750,

        # Token priorities
        'token_doublers': 950,
        'token_generators': 800,
        'token_anthems': 700,
        'token_synergies': 650,

        # Voltron priorities
        'equipment': 850,
        'auras': 800,
        'protection_spells': 900,
        'evasion_granters': 750,

        # Spellslinger priorities
        'prowess_creatures': 850,
        'spell_copy': 900,
        'card_draw_spells': 750,
        'cost_reduction': 800,

        # Go-Wide priorities
        'small_creatures': 700,
        'anthem_effects': 850,
        'mass_pump': 800,

        # Counters priorities
        'counter_generators': 850,
        'proliferate': 900,
        'counter_doublers': 950,

        # Reanimator priorities
        'reanimation_spells': 900,
        'discard_outlets': 750,
        'mill_effects': 700,
        'big_creatures': 650,

        # Ramp priorities
        'mana_rocks': 850,
        'mana_dorks': 800,
        'land_ramp': 750,
    }

    def __init__(self, verbose: bool = False):
        """
        Initialize the archetype detector.

        Args:
            verbose: If True, print detection details
        """
        self.verbose = verbose

    def detect_archetype(self, cards: List[Dict], commander: Optional[Dict] = None) -> Dict:
        """
        Detect the primary and secondary archetypes of a deck.

        Args:
            cards: List of card dictionaries from the deck
            commander: Optional commander card dictionary

        Returns:
            {
                'primary_archetype': str,
                'secondary_archetype': str or None,
                'archetype_scores': Dict[str, int],
                'priorities': Dict[str, int],
                'deck_stats': Dict with card counts
            }
        """
        # Count cards by category
        stats = self._analyze_deck_composition(cards, commander)

        # Score each archetype
        archetype_scores = {
            'Aristocrats': self._score_aristocrats(stats),
            'Tokens': self._score_tokens(stats),
            'Voltron': self._score_voltron(stats, commander),
            'Spellslinger': self._score_spellslinger(stats),
            'Go-Wide': self._score_go_wide(stats),
            'Counters': self._score_counters(stats),
            'Reanimator': self._score_reanimator(stats),
            'Ramp': self._score_ramp(stats),
        }

        # Find primary and secondary archetypes
        sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_archetypes[0][0] if sorted_archetypes[0][1] > 0 else 'Generic'
        secondary = sorted_archetypes[1][0] if len(sorted_archetypes) > 1 and sorted_archetypes[1][1] > 30 else None

        # Generate priority adjustments
        priorities = self._generate_priorities(primary, secondary, stats)

        if self.verbose:
            print("\n" + "=" * 60)
            print("DECK ARCHETYPE DETECTION")
            print("=" * 60)
            print(f"Primary Archetype: {primary} (Score: {archetype_scores[primary]})")
            if secondary:
                print(f"Secondary Archetype: {secondary} (Score: {archetype_scores[secondary]})")
            print("\nArchetype Scores:")
            for arch, score in sorted_archetypes:
                if score > 0:
                    print(f"  {arch}: {score}")
            print("\nDeck Statistics:")
            for key, value in stats.items():
                if value > 0:
                    print(f"  {key}: {value}")
            print("=" * 60 + "\n")

        return {
            'primary_archetype': primary,
            'secondary_archetype': secondary,
            'archetype_scores': archetype_scores,
            'priorities': priorities,
            'deck_stats': stats
        }

    def _analyze_deck_composition(self, cards: List[Dict], commander: Optional[Dict]) -> Dict:
        """Analyze the deck and count cards by category."""
        stats = {
            # Aristocrats
            'death_triggers': 0,
            'sacrifice_outlets': 0,
            'death_drain_triggers': 0,

            # Tokens
            'token_generators': 0,
            'token_doublers': 0,
            'token_anthems': 0,

            # Voltron
            'equipment': 0,
            'auras': 0,
            'protection_spells': 0,
            'commander_power': 0,

            # Spellslinger
            'instants': 0,
            'sorceries': 0,
            'prowess_creatures': 0,
            'spell_copy': 0,

            # Go-Wide
            'small_creatures': 0,  # power <= 2
            'anthem_effects': 0,

            # Counters
            'counter_generators': 0,
            'proliferate': 0,
            'counter_doublers': 0,

            # Reanimator
            'reanimation_spells': 0,
            'discard_outlets': 0,
            'mill_effects': 0,
            'big_creatures': 0,  # power >= 6

            # Ramp
            'mana_rocks': 0,
            'mana_dorks': 0,
            'land_ramp': 0,

            # General
            'total_creatures': 0,
        }

        # Analyze commander
        if commander:
            power = commander.get('power')
            if power and str(power).isdigit():
                stats['commander_power'] = int(power)

        # Analyze each card
        for card in cards:
            oracle = card.get('oracle_text', '')
            type_line = card.get('type_line', '')
            power = card.get('power')

            # Creature stats
            if 'Creature' in type_line:
                stats['total_creatures'] += 1

                if power and str(power).isdigit():
                    power_val = int(power)
                    if power_val <= 2:
                        stats['small_creatures'] += 1
                    if power_val >= 6:
                        stats['big_creatures'] += 1

            # Aristocrats detection
            if has_death_trigger(oracle):
                stats['death_triggers'] += 1

                # Check for drain specifically
                if 'opponent' in oracle.lower() and ('lose' in oracle.lower() or 'loses' in oracle.lower()):
                    stats['death_drain_triggers'] += 1

            if is_sacrifice_outlet(oracle):
                stats['sacrifice_outlets'] += 1

            # Token detection
            token_info = extract_token_creation(card)
            if token_info.get('creates_tokens'):
                stats['token_generators'] += 1

            doubler_info = extract_token_doublers(card)
            if doubler_info.get('is_token_doubler'):
                stats['token_doublers'] += 1

            # Anthem detection (simple pattern matching)
            if 'creatures you control get +' in oracle.lower():
                stats['anthem_effects'] += 1
                stats['token_anthems'] += 1

            # Voltron detection
            if 'Equipment' in type_line:
                stats['equipment'] += 1
            if 'Aura' in type_line and 'Enchant creature' in oracle:
                stats['auras'] += 1
            if any(word in oracle.lower() for word in ['hexproof', 'indestructible', 'protection from']):
                stats['protection_spells'] += 1

            # Spellslinger detection
            if 'Instant' in type_line:
                stats['instants'] += 1
            if 'Sorcery' in type_line:
                stats['sorceries'] += 1
            if 'prowess' in oracle.lower() or 'storm' in oracle.lower():
                stats['prowess_creatures'] += 1
            if 'copy' in oracle.lower() and ('instant' in oracle.lower() or 'sorcery' in oracle.lower()):
                stats['spell_copy'] += 1

            # Counters detection
            if '+1/+1 counter' in oracle.lower():
                stats['counter_generators'] += 1
            if 'proliferate' in oracle.lower():
                stats['proliferate'] += 1
            if 'double' in oracle.lower() and 'counter' in oracle.lower():
                stats['counter_doublers'] += 1

            # Reanimator detection
            reanimate_info = extract_reanimation(card)
            if reanimate_info.get('is_reanimation'):
                stats['reanimation_spells'] += 1

            mill_info = extract_graveyard_fill(card)
            if mill_info.get('fills_graveyard'):
                if 'mill' in mill_info.get('fill_mechanics', []):
                    stats['mill_effects'] += 1
                if 'discard' in mill_info.get('fill_mechanics', []):
                    stats['discard_outlets'] += 1

            # Ramp detection (simple patterns)
            if 'Artifact' in type_line and any(word in oracle.lower() for word in ['add {', '{t}: add']):
                stats['mana_rocks'] += 1
            if 'Creature' in type_line and any(word in oracle.lower() for word in ['add {', '{t}: add']):
                stats['mana_dorks'] += 1
            if 'search your library' in oracle.lower() and 'land' in oracle.lower():
                stats['land_ramp'] += 1

        return stats

    def _score_aristocrats(self, stats: Dict) -> int:
        """Score Aristocrats archetype (death triggers + sacrifice outlets)."""
        score = 0

        # Core aristocrats pieces
        if stats['death_triggers'] >= 5:
            score += 40
        else:
            score += stats['death_triggers'] * 6

        if stats['sacrifice_outlets'] >= 3:
            score += 40
        else:
            score += stats['sacrifice_outlets'] * 10

        # Drain triggers are especially valuable
        score += stats['death_drain_triggers'] * 8

        # Token generators synergize (fodder)
        score += min(stats['token_generators'] * 3, 20)

        return score

    def _score_tokens(self, stats: Dict) -> int:
        """Score Tokens archetype (token generators + doublers)."""
        score = 0

        # Token generators
        if stats['token_generators'] >= 8:
            score += 50
        else:
            score += stats['token_generators'] * 5

        # Token doublers are huge
        if stats['token_doublers'] >= 2:
            score += 40
        else:
            score += stats['token_doublers'] * 15

        # Anthems synergize
        score += min(stats['token_anthems'] * 5, 25)

        return score

    def _score_voltron(self, stats: Dict, commander: Optional[Dict]) -> int:
        """Score Voltron archetype (equipment/auras + big commander)."""
        score = 0

        # Commander power matters
        if stats['commander_power'] >= 4:
            score += 30
        elif stats['commander_power'] >= 2:
            score += 15

        # Equipment and auras
        equipment_auras = stats['equipment'] + stats['auras']
        if equipment_auras >= 5:
            score += 40
        else:
            score += equipment_auras * 6

        # Protection is critical
        score += min(stats['protection_spells'] * 8, 30)

        return score

    def _score_spellslinger(self, stats: Dict) -> int:
        """Score Spellslinger archetype (instants/sorceries + prowess/storm)."""
        score = 0

        # Spell count
        spell_count = stats['instants'] + stats['sorceries']
        if spell_count >= 15:
            score += 40
        else:
            score += spell_count * 2

        # Payoffs
        score += stats['prowess_creatures'] * 10
        score += stats['spell_copy'] * 8

        return score

    def _score_go_wide(self, stats: Dict) -> int:
        """Score Go-Wide archetype (many small creatures)."""
        score = 0

        # Small creatures
        if stats['small_creatures'] >= 15:
            score += 50
        else:
            score += stats['small_creatures'] * 3

        # Anthems are critical
        score += min(stats['anthem_effects'] * 10, 40)

        return score

    def _score_counters(self, stats: Dict) -> int:
        """Score Counters archetype (+1/+1 counters + proliferate)."""
        score = 0

        # Counter generators
        if stats['counter_generators'] >= 5:
            score += 35
        else:
            score += stats['counter_generators'] * 5

        # Proliferate synergizes
        score += min(stats['proliferate'] * 10, 35)

        # Doublers are huge
        score += stats['counter_doublers'] * 15

        return score

    def _score_reanimator(self, stats: Dict) -> int:
        """Score Reanimator archetype (reanimation + discard/mill)."""
        score = 0

        # Reanimation spells
        if stats['reanimation_spells'] >= 5:
            score += 40
        else:
            score += stats['reanimation_spells'] * 6

        # Enablers
        enablers = stats['discard_outlets'] + stats['mill_effects']
        if enablers >= 3:
            score += 30
        else:
            score += enablers * 8

        # Big creatures to reanimate
        score += min(stats['big_creatures'] * 3, 20)

        return score

    def _score_ramp(self, stats: Dict) -> int:
        """Score Ramp archetype (mana acceleration)."""
        score = 0

        ramp_total = stats['mana_rocks'] + stats['mana_dorks'] + stats['land_ramp']

        if ramp_total >= 12:
            score += 50
        else:
            score += ramp_total * 3

        # Ramp is often a sub-strategy, not primary
        # So we cap the score to avoid false positives
        return min(score, 60)

    def _generate_priorities(self, primary: str, secondary: Optional[str], stats: Dict) -> Dict:
        """Generate AI priority adjustments based on detected archetypes."""
        priorities = {}

        # Apply primary archetype priorities
        if primary == 'Aristocrats':
            priorities.update({
                'sacrifice_outlets': self.PRIORITY_SCORES['sacrifice_outlets'],
                'death_triggers': self.PRIORITY_SCORES['death_triggers'],
                'token_generators': self.PRIORITY_SCORES['token_generators_aristocrats'],
            })

        elif primary == 'Tokens':
            priorities.update({
                'token_doublers': self.PRIORITY_SCORES['token_doublers'],
                'token_generators': self.PRIORITY_SCORES['token_generators'],
                'token_anthems': self.PRIORITY_SCORES['token_anthems'],
            })

        elif primary == 'Voltron':
            priorities.update({
                'equipment': self.PRIORITY_SCORES['equipment'],
                'auras': self.PRIORITY_SCORES['auras'],
                'protection_spells': self.PRIORITY_SCORES['protection_spells'],
            })

        elif primary == 'Spellslinger':
            priorities.update({
                'spell_copy': self.PRIORITY_SCORES['spell_copy'],
                'prowess_creatures': self.PRIORITY_SCORES['prowess_creatures'],
                'cost_reduction': self.PRIORITY_SCORES['cost_reduction'],
            })

        elif primary == 'Go-Wide':
            priorities.update({
                'anthem_effects': self.PRIORITY_SCORES['anthem_effects'],
                'mass_pump': self.PRIORITY_SCORES['mass_pump'],
                'small_creatures': self.PRIORITY_SCORES['small_creatures'],
            })

        elif primary == 'Counters':
            priorities.update({
                'counter_doublers': self.PRIORITY_SCORES['counter_doublers'],
                'proliferate': self.PRIORITY_SCORES['proliferate'],
                'counter_generators': self.PRIORITY_SCORES['counter_generators'],
            })

        elif primary == 'Reanimator':
            priorities.update({
                'reanimation_spells': self.PRIORITY_SCORES['reanimation_spells'],
                'discard_outlets': self.PRIORITY_SCORES['discard_outlets'],
                'mill_effects': self.PRIORITY_SCORES['mill_effects'],
            })

        elif primary == 'Ramp':
            priorities.update({
                'mana_rocks': self.PRIORITY_SCORES['mana_rocks'],
                'mana_dorks': self.PRIORITY_SCORES['mana_dorks'],
                'land_ramp': self.PRIORITY_SCORES['land_ramp'],
            })

        # Add secondary archetype priorities (at reduced weight)
        if secondary:
            secondary_priorities = self._generate_priorities(secondary, None, stats)
            for key, value in secondary_priorities.items():
                if key not in priorities:
                    priorities[key] = int(value * 0.6)  # Reduce secondary priorities

        return priorities


# Convenience function for easy import
def detect_deck_archetype(cards: List[Dict], commander: Optional[Dict] = None, verbose: bool = False) -> Dict:
    """
    Convenience function to detect deck archetype.

    Args:
        cards: List of card dictionaries
        commander: Optional commander card
        verbose: If True, print detection details

    Returns:
        Archetype detection results dictionary
    """
    detector = DeckArchetypeDetector(verbose=verbose)
    return detector.detect_archetype(cards, commander)
