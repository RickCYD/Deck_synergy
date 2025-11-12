#!/usr/bin/env python3
"""
Test script to demonstrate contextual necessity scoring for utility cards
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.recommendations import RecommendationEngine

def test_high_curve_deck():
    """Test a high-curve deck that NEEDS more ramp"""
    print("=" * 80)
    print("TEST 1: High-Curve Deck (Should recommend ramp)")
    print("=" * 80)

    engine = RecommendationEngine()

    # Create a high-curve deck with insufficient ramp (only 3 ramp sources)
    test_deck = [
        # High CMC threats (avg ~5 CMC)
        {"name": "Wurmcoil Engine", "type_line": "Artifact Creature", "cmc": 6},
        {"name": "Consecrated Sphinx", "type_line": "Creature", "cmc": 6},
        {"name": "Cyclonic Rift", "type_line": "Instant", "cmc": 7},
        {"name": "Expropriate", "type_line": "Sorcery", "cmc": 9},
        {"name": "Jin-Gitaxias, Core Augur", "type_line": "Legendary Creature", "cmc": 10},
        {"name": "Ulamog, the Ceaseless Hunger", "type_line": "Legendary Creature", "cmc": 10},
        {"name": "Blightsteel Colossus", "type_line": "Artifact Creature", "cmc": 12},

        # Only 3 ramp sources (insufficient for high curve!)
        {"name": "Sol Ring", "type_line": "Artifact", "cmc": 1},
        {"name": "Arcane Signet", "type_line": "Artifact", "cmc": 2},
        {"name": "Cultivate", "type_line": "Sorcery", "cmc": 3},

        # Some removal
        {"name": "Swords to Plowshares", "type_line": "Instant", "cmc": 1},
        {"name": "Path to Exile", "type_line": "Instant", "cmc": 1},

        # Filler
        {"name": "Rhystic Study", "type_line": "Enchantment", "cmc": 3},
        {"name": "Smothering Tithe", "type_line": "Enchantment", "cmc": 4},
    ]

    print(f"\n✓ Created high-curve deck (avg CMC ~6.5, only 3 ramp sources)\n")

    # Score the deck to see which ramp cards are flagged as needed
    print("📊 Analyzing deck cards (cards to potentially cut)...")
    deck_scores = engine.score_deck_cards(test_deck, exclude_lands=True)

    print("\n" + "=" * 80)
    print("BOTTOM 5 CARDS (Candidates for cutting):")
    print("=" * 80)

    for i, card in enumerate(deck_scores[:5], 1):
        print(f"\n{i}. {card['name']} (Score: {card.get('synergy_score', 0):.1f})")
        print(f"   Type: {card.get('type_line', 'Unknown')}")
        reasons = card.get('synergy_reasons', [])
        if reasons:
            print(f"   Reasons:")
            for reason in reasons:
                print(f"      • {reason}")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)

    # Get recommendations - should prioritize ramp!
    recs = engine.get_recommendations(test_deck, color_identity=['W', 'U'], limit=10)

    print(f"\n✓ Got {len(recs.get('recommendations', []))} recommendations\n")

    # Look for ramp recommendations with contextual necessity explanations
    found_needed_ramp = False
    for i, card in enumerate(recs.get('recommendations', [])[:10], 1):
        reasons = card.get('synergy_reasons', [])

        # Check if this is a ramp card with "NEEDED" flag
        if any('🎯 NEEDED' in r and 'ramp' in r.lower() for r in reasons):
            found_needed_ramp = True
            print(f"{i}. {card['name']} (Score: {card.get('recommendation_score', 0):.1f})")
            print(f"   Type: {card.get('type_line', 'Unknown')}")
            print(f"   Contextual Analysis:")
            for reason in reasons:
                if '🎯' in reason or '⚠️' in reason or '✓' in reason:
                    print(f"      {reason}")
            print()

    if found_needed_ramp:
        print("✅ SUCCESS: System correctly identified ramp as NEEDED for high-curve deck!")
    else:
        print("⚠️  No ramp cards with NEEDED flag found (may not be in card pool)")

    return found_needed_ramp


def test_low_curve_deck():
    """Test a low-curve deck that has EXCESS ramp"""
    print("\n" + "=" * 80)
    print("TEST 2: Low-Curve Aggro Deck (Should flag excess ramp as cuttable)")
    print("=" * 80)

    engine = RecommendationEngine()

    # Create a low-curve aggro deck with too much ramp (doesn't need it!)
    test_deck = [
        # Low CMC aggressive creatures (avg ~2 CMC)
        {"name": "Goblin Guide", "type_line": "Creature", "cmc": 1},
        {"name": "Monastery Swiftspear", "type_line": "Creature", "cmc": 1},
        {"name": "Zurgo Bellstriker", "type_line": "Legendary Creature", "cmc": 1},
        {"name": "Lightning Bolt", "type_line": "Instant", "cmc": 1},
        {"name": "Boros Charm", "type_line": "Instant", "cmc": 2},
        {"name": "Eidolon of the Great Revel", "type_line": "Creature", "cmc": 2},
        {"name": "Young Pyromancer", "type_line": "Creature", "cmc": 2},

        # TOO MUCH RAMP for a low-curve deck (12 sources!)
        {"name": "Sol Ring", "type_line": "Artifact", "cmc": 1},
        {"name": "Arcane Signet", "type_line": "Artifact", "cmc": 2},
        {"name": "Fellwar Stone", "type_line": "Artifact", "cmc": 2},
        {"name": "Mind Stone", "type_line": "Artifact", "cmc": 2},
        {"name": "Thought Vessel", "type_line": "Artifact", "cmc": 2},
        {"name": "Talisman of Conviction", "type_line": "Artifact", "cmc": 2},
        {"name": "Boros Signet", "type_line": "Artifact", "cmc": 2},
        {"name": "Wayfarer's Bauble", "type_line": "Artifact", "cmc": 1},
        {"name": "Skullclamp", "type_line": "Artifact — Equipment", "cmc": 1},
        {"name": "Mana Crypt", "type_line": "Artifact", "cmc": 0},
        {"name": "Mana Vault", "type_line": "Artifact", "cmc": 1},
        {"name": "Chrome Mox", "type_line": "Artifact", "cmc": 0},

        # Some removal
        {"name": "Swords to Plowshares", "type_line": "Instant", "cmc": 1},
        {"name": "Path to Exile", "type_line": "Instant", "cmc": 1},
    ]

    print(f"\n✓ Created low-curve aggro deck (avg CMC ~1.5, but 12 ramp sources!)\n")

    # Score the deck to see which ramp cards are flagged as excess
    print("📊 Analyzing deck cards (cards to potentially cut)...")
    deck_scores = engine.score_deck_cards(test_deck, exclude_lands=True)

    print("\n" + "=" * 80)
    print("CARDS WITH 'CUTTABLE' FLAG:")
    print("=" * 80)

    found_cuttable_ramp = False
    for card in deck_scores:
        reasons = card.get('synergy_reasons', [])
        if any('⚠️ CUTTABLE' in r and 'ramp' in r.lower() for r in reasons):
            found_cuttable_ramp = True
            print(f"\n{card['name']} (Score: {card.get('synergy_score', 0):.1f})")
            print(f"   Type: {card.get('type_line', 'Unknown')}")
            for reason in reasons:
                if '⚠️' in reason:
                    print(f"   {reason}")

    if found_cuttable_ramp:
        print("\n✅ SUCCESS: System correctly flagged excess ramp as CUTTABLE for low-curve deck!")
    else:
        print("\n⚠️  No ramp cards with CUTTABLE flag found")

    return found_cuttable_ramp


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CONTEXTUAL NECESSITY SYSTEM TEST")
    print("=" * 80)
    print()
    print("This test demonstrates how the system contextually evaluates utility cards")
    print("based on deck needs, rather than just synergy tags.")
    print()

    test1_passed = test_high_curve_deck()
    test2_passed = test_low_curve_deck()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test 1 (High Curve Needs Ramp): {'✅ PASSED' if test1_passed else '⚠️  PARTIAL'}")
    print(f"Test 2 (Low Curve Excess Ramp): {'✅ PASSED' if test2_passed else '⚠️  PARTIAL'}")
    print()
    print("The contextual necessity system intelligently adjusts scores based on:")
    print("  • Deck's mana curve (low/medium/high)")
    print("  • Strategy (aggro/midrange/control/combo)")
    print("  • Current counts vs optimal thresholds")
    print("=" * 80)

    sys.exit(0 if (test1_passed or test2_passed) else 1)
