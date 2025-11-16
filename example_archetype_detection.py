"""
Example Usage: Mathematically Rigorous Archetype Detection

This demonstrates how to use the new optimization-based archetype detection.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from analysis.deck_archetype_detector import (
    detect_deck_archetype,
    validate_detection_quality
)


# Example: Detect archetype for a deck with synergies
def example_with_synergies():
    """Example with full synergy data (best accuracy)."""
    print("="*60)
    print("EXAMPLE 1: Detection with Synergies")
    print("="*60)

    # Sample deck cards
    cards = [
        {
            'name': 'Blood Artist',
            'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.',
            'type_line': 'Creature — Vampire',
            'roles': ['Death Trigger', 'Aristocrat', 'Drain']
        },
        {
            'name': 'Ashnod\'s Altar',
            'oracle_text': 'Sacrifice a creature: Add {C}{C}.',
            'type_line': 'Artifact',
            'roles': ['Sacrifice Outlet']
        },
        # ... more cards
    ]

    # Synergies from analyzer
    deck_synergies = {
        'Blood Artist||Ashnod\'s Altar': {
            'total_weight': 5,
            'synergies': {
                'death_trigger_synergy': ['Sacrifice outlet enables death triggers'],
                'sacrifice_synergy': ['Direct sacrifice combo']
            }
        }
    }

    # Detect archetype
    result = detect_deck_archetype(
        cards=cards,
        deck_synergies=deck_synergies,
        verbose=True
    )

    # Validate quality
    validation = validate_detection_quality(result)

    print(f"\n🎯 Result:")
    print(f"  Primary: {result['primary_archetype']}")
    print(f"  Confidence: {result['confidence']:.3f}")
    print(f"  Quality: {validation['quality']}")
    print(f"  Modularity: {validation['modularity']:.3f}")

    return result


# Example: Detect archetype without synergies (still works!)
def example_without_synergies():
    """Example without synergies (uses TF-IDF and roles only)."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Detection without Synergies")
    print("="*60)

    cards = [
        {
            'name': 'Sword of Fire and Ice',
            'oracle_text': 'Equipped creature gets +2/+2 and has protection from red and from blue.',
            'type_line': 'Artifact — Equipment',
            'roles': ['Equipment', 'Voltron']
        },
        {
            'name': 'Lightning Greaves',
            'oracle_text': 'Equipped creature has haste and shroud.',
            'type_line': 'Artifact — Equipment',
            'roles': ['Equipment', 'Voltron', 'Protection']
        },
        # ... more cards
    ]

    # No synergies passed - still works using TF-IDF and roles
    result = detect_deck_archetype(
        cards=cards,
        verbose=True
    )

    print(f"\n🎯 Result:")
    print(f"  Primary: {result['primary_archetype']}")
    print(f"  Confidence: {result['confidence']:.3f}")

    return result


# Example: Use validation to get recommendations
def example_validation():
    """Example showing how to validate and get recommendations."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Quality Validation")
    print("="*60)

    cards = [
        {'name': 'Sol Ring', 'oracle_text': '{T}: Add {C}{C}.', 'type_line': 'Artifact', 'roles': ['Ramp']},
        {'name': 'Counterspell', 'oracle_text': 'Counter target spell.', 'type_line': 'Instant', 'roles': ['Counterspell']},
    ]

    result = detect_deck_archetype(cards=cards)
    validation = validate_detection_quality(result)

    print(f"\n📊 Validation Results:")
    print(f"  Quality: {validation['quality']}")
    print(f"  Confidence: {validation['confidence']:.3f}")
    print(f"  Modularity: {validation['modularity']:.3f}")
    print(f"\n💡 Recommendations:")
    for rec in validation['recommendations']:
        print(f"  • {rec}")


if __name__ == "__main__":
    example_with_synergies()
    example_without_synergies()
    example_validation()

    print("\n" + "="*60)
    print("✓ All examples completed!")
    print("="*60)
