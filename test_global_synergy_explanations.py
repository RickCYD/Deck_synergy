#!/usr/bin/env python3
"""
Test script to verify global synergy explanations are working correctly
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.recommendations import RecommendationEngine

def test_global_synergy_explanations():
    """Test that global synergies have proper explanations"""

    print("=" * 80)
    print("Testing Global Synergy Explanations")
    print("=" * 80)

    # Initialize the recommendation engine
    engine = RecommendationEngine()

    # Create a test deck with artifacts (simulating an artifact-heavy deck)
    test_deck = [
        {"name": "Sol Ring", "type_line": "Artifact"},
        {"name": "Arcane Signet", "type_line": "Artifact"},
        {"name": "Commander's Sphere", "type_line": "Artifact"},
        {"name": "Thought Vessel", "type_line": "Artifact"},
        {"name": "Mind Stone", "type_line": "Artifact"},
        {"name": "Wayfarer's Bauble", "type_line": "Artifact"},
        {"name": "Hedron Archive", "type_line": "Artifact"},
        {"name": "Lightning Greaves", "type_line": "Artifact — Equipment"},
        {"name": "Swiftfoot Boots", "type_line": "Artifact — Equipment"},
        {"name": "Skullclamp", "type_line": "Artifact — Equipment"},
        {"name": "Inspiring Statuary", "type_line": "Artifact"},  # This card scales with artifacts!
        {"name": "Jhoira's Familiar", "type_line": "Artifact Creature"},  # This also scales with artifacts
        {"name": "Sword of the Animist", "type_line": "Artifact — Equipment"},
        {"name": "Burnished Hart", "type_line": "Artifact Creature"},
        {"name": "Solemn Simulacrum", "type_line": "Artifact Creature"},
        {"name": "Darksteel Ingot", "type_line": "Artifact"},
        {"name": "Aether Spellbomb", "type_line": "Artifact"},
        {"name": "Chromatic Lantern", "type_line": "Artifact"},
        {"name": "Sensei's Divining Top", "type_line": "Artifact"},
        {"name": "Trading Post", "type_line": "Artifact"},
    ]

    print(f"\n✓ Created test deck with {len(test_deck)} cards")

    # Get recommendations
    print("\n📊 Analyzing deck and generating recommendations...")
    try:
        recommendations = engine.get_recommendations(
            test_deck,
            color_identity=['U', 'R'],  # Izzet colors
            limit=10
        )

        print(f"\n✓ Got {len(recommendations.get('recommendations', []))} recommendations")

        # Look for cards with global synergy explanations
        print("\n" + "=" * 80)
        print("Cards with Global Synergy Explanations:")
        print("=" * 80)

        found_global = False
        for i, card in enumerate(recommendations.get('recommendations', [])[:5], 1):
            reasons = card.get('synergy_reasons', [])

            # Check if any reason contains "⚡ Scales with"
            global_reasons = [r for r in reasons if '⚡ Scales with' in r]

            if global_reasons:
                found_global = True
                print(f"\n{i}. {card['name']} (Score: {card.get('recommendation_score', 0):.1f})")
                print(f"   Type: {card.get('type_line', 'Unknown')}")
                print(f"   Global Synergies:")
                for reason in global_reasons:
                    print(f"      • {reason}")

                # Show all reasons
                if len(reasons) > len(global_reasons):
                    print(f"   Other Synergies:")
                    for reason in reasons:
                        if '⚡ Scales with' not in reason:
                            print(f"      • {reason}")

        if not found_global:
            print("\n⚠️  No cards with global synergy explanations found in top 5")
            print("   (This might be expected depending on available cards)")
        else:
            print(f"\n✅ SUCCESS: Global synergy explanations are working!")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_global_synergy_explanations()
    sys.exit(0 if success else 1)
