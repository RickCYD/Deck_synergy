#!/usr/bin/env python
"""
Test real-time AI decision metrics added to BoardState.

Tests the 6 new methods:
1. get_library_stats() - Library count tracking
2. analyze_hand_resources() - Hand resource analysis
3. calculate_mana_efficiency() - Mana efficiency score
4. can_play_next_turn() - Look-ahead playability
5. detect_resource_scarcity() - Resource scarcity detection
6. calculate_opportunity_cost() - Opportunity cost calculator
"""

import sys
import os

# Add Simulation directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

from boardstate import BoardState
from simulate_game import Card


def create_test_card(name, card_type, mana_cost="{0}", power=0, toughness=0, **kwargs):
    """Helper to create test cards."""
    return Card(
        name=name,
        type=card_type,
        mana_cost=mana_cost,
        power=power,
        toughness=toughness,
        produces_colors=kwargs.get('produces_colors', []),
        mana_production=kwargs.get('mana_production', 0),
        etb_tapped=kwargs.get('etb_tapped', False),
        etb_tapped_conditions=kwargs.get('etb_tapped_conditions', {}),
        has_haste=kwargs.get('has_haste', False),
        oracle_text=kwargs.get('oracle_text', ''),
        draw_cards=kwargs.get('draw_cards', 0),
    )


def test_library_stats():
    """Test library statistics tracking."""
    print("\n" + "="*60)
    print("TEST 1: Library Stats")
    print("="*60)

    # Create deck
    deck = [create_test_card(f"Card {i}", "Creature") for i in range(50)]
    commander = create_test_card("Commander", "Legendary Creature", "{2}{G}", 3, 3)

    board = BoardState(deck, commander)

    # Test initial state
    stats = board.get_library_stats()
    print(f"✓ Library Stats:")
    print(f"  - Cards remaining: {stats['cards_remaining']}")
    print(f"  - Draw probability: {stats['draw_probability']:.2f}")
    print(f"  - Scarcity level: {stats['scarcity_level']:.2f}")
    print(f"  - Turns until empty: {stats['turns_until_empty']}")

    assert stats['cards_remaining'] == 50, "Should have 50 cards"
    assert stats['scarcity_level'] < 0.5, "Should not be scarce yet"

    # Draw some cards
    for _ in range(30):
        if board.library:
            board.library.pop()

    stats_after = board.get_library_stats()
    print(f"\n✓ After drawing 30 cards:")
    print(f"  - Cards remaining: {stats_after['cards_remaining']}")
    print(f"  - Scarcity level: {stats_after['scarcity_level']:.2f}")

    assert stats_after['scarcity_level'] > 0.5, "Should be scarce now"
    print("\n✅ Library Stats Test PASSED")


def test_hand_resources():
    """Test hand resource analysis."""
    print("\n" + "="*60)
    print("TEST 2: Hand Resource Analysis")
    print("="*60)

    deck = []
    commander = create_test_card("Commander", "Legendary Creature")
    board = BoardState(deck, commander)

    # Add diverse hand
    board.hand = [
        create_test_card("Forest", "Land"),
        create_test_card("Plains", "Land"),
        create_test_card("Grizzly Bears", "Creature", "{1}{G}", 2, 2),
        create_test_card("Sol Ring", "Artifact", "{1}"),
        create_test_card("Lightning Bolt", "Instant", "{R}"),
        create_test_card("Enchantment", "Enchantment", "{2}"),
    ]

    stats = board.analyze_hand_resources()
    print(f"✓ Hand Analysis:")
    print(f"  - Hand size: {stats['hand_size']}")
    print(f"  - Lands: {stats['hand_lands']}")
    print(f"  - Spells: {stats['hand_spells']}")
    print(f"  - Land ratio: {stats['land_ratio']:.2f}")
    print(f"  - Diversity score: {stats['diversity_score']:.2f}")
    print(f"  - Types in hand: {stats['types_in_hand']}")

    assert stats['hand_size'] == 6, "Should have 6 cards"
    assert stats['hand_lands'] == 2, "Should have 2 lands"
    assert stats['diversity_score'] > 0.6, "Should have good diversity"

    print("\n✅ Hand Resource Analysis Test PASSED")


def test_mana_efficiency():
    """Test mana efficiency calculation."""
    print("\n" + "="*60)
    print("TEST 3: Mana Efficiency")
    print("="*60)

    deck = []
    commander = create_test_card("Commander", "Legendary Creature")
    board = BoardState(deck, commander)

    # Add mana pool (5 mana available)
    board.mana_pool = [("G",), ("G",), ("Any",), ("Any",), ("Any",)]

    # Add castable cards to hand
    board.hand = [
        create_test_card("2-drop", "Creature", "{2}", 2, 2),
        create_test_card("3-drop", "Creature", "{3}", 3, 3),
        create_test_card("1-drop", "Creature", "{1}", 1, 1),
    ]

    eff = board.calculate_mana_efficiency()
    print(f"✓ Mana Efficiency:")
    print(f"  - Mana available: {eff['mana_available']}")
    print(f"  - Optimal usage: {eff['optimal_mana_usage']}")
    print(f"  - Wasted mana: {eff['wasted_mana']}")
    print(f"  - Efficiency score: {eff['efficiency_score']:.2f}")
    print(f"  - Castable cards: {eff['castable_count']}")

    assert eff['mana_available'] == 5, "Should have 5 mana"
    assert eff['efficiency_score'] > 0.6, "Should be able to use most mana"

    print("\n✅ Mana Efficiency Test PASSED")


def test_lookahead_playability():
    """Test look-ahead playability."""
    print("\n" + "="*60)
    print("TEST 4: Look-Ahead Playability")
    print("="*60)

    deck = []
    commander = create_test_card("Commander", "Legendary Creature")
    board = BoardState(deck, commander)

    # Current state: 3 lands
    board.lands_untapped = [
        create_test_card("Forest", "Land"),
        create_test_card("Forest", "Land"),
        create_test_card("Forest", "Land"),
    ]

    # Test a 5-drop card
    expensive_card = create_test_card("Big Creature", "Creature", "{5}", 5, 5)

    lookahead = board.can_play_next_turn(expensive_card, look_ahead_turns=3)
    print(f"✓ Look-Ahead for 5-drop with 3 lands:")
    for turn_key, data in lookahead.items():
        print(f"  - {turn_key}: playable={data['playable']}, expected_mana={data['expected_mana']}, mana_short={data['mana_short']}")

    assert not lookahead['turn_1']['playable'], "Should NOT be playable turn 1 (4 mana)"
    assert lookahead['turn_2']['playable'], "SHOULD be playable turn 2 (5 mana)"

    print("\n✅ Look-Ahead Playability Test PASSED")


def test_resource_scarcity():
    """Test resource scarcity detection."""
    print("\n" + "="*60)
    print("TEST 5: Resource Scarcity Detection")
    print("="*60)

    deck = [create_test_card(f"Card {i}", "Creature") for i in range(10)]
    commander = create_test_card("Commander", "Legendary Creature")
    board = BoardState(deck, commander)

    # Low library + low hand = scarcity
    board.hand = [create_test_card("Card", "Creature")]

    scarcity = board.detect_resource_scarcity()
    print(f"✓ Resource Scarcity (low resources):")
    print(f"  - Scarcity score: {scarcity['scarcity_score']:.2f}")
    print(f"  - Turns until empty: {scarcity['turns_until_empty']:.1f}")
    print(f"  - Prioritize draw: {scarcity['prioritize_draw']}")
    print(f"  - Critical scarcity: {scarcity['critical_scarcity']}")
    print(f"  - Hand size: {scarcity['hand_size']}")
    print(f"  - Library size: {scarcity['library_size']}")

    assert scarcity['prioritize_draw'], "Should prioritize draw with low resources"

    # Test abundant resources
    board2 = BoardState([create_test_card(f"Card {i}", "Creature") for i in range(60)], commander)
    board2.hand = [create_test_card("Card", "Creature") for _ in range(7)]

    scarcity2 = board2.detect_resource_scarcity()
    print(f"\n✓ Resource Scarcity (abundant resources):")
    print(f"  - Scarcity score: {scarcity2['scarcity_score']:.2f}")
    print(f"  - Prioritize draw: {scarcity2['prioritize_draw']}")

    assert not scarcity2['prioritize_draw'], "Should NOT prioritize draw with abundant resources"

    print("\n✅ Resource Scarcity Detection Test PASSED")


def test_opportunity_cost():
    """Test opportunity cost calculation."""
    print("\n" + "="*60)
    print("TEST 6: Opportunity Cost Calculation")
    print("="*60)

    deck = []
    commander = create_test_card("Commander", "Legendary Creature")
    board = BoardState(deck, commander)
    board.turn = 3

    # Test high immediate value card (haste creature)
    haste_creature = create_test_card("Dragon", "Creature", "{4}", 4, 4, has_haste=True)

    opp_cost = board.calculate_opportunity_cost(haste_creature)
    print(f"✓ Opportunity Cost (Haste Creature):")
    print(f"  - Immediate value: {opp_cost['immediate_value']:.2f}")
    print(f"  - Future value: {opp_cost['future_value']:.2f}")
    print(f"  - Net value: {opp_cost['net_value']:.2f}")
    print(f"  - Recommendation: {opp_cost['recommendation']}")
    print(f"  - Confidence: {opp_cost['confidence']:.2f}")

    assert opp_cost['recommendation'] in ['PLAY_NOW', 'NEUTRAL'], "Haste creature should be played or neutral"

    # Test mana rock early game
    board.turn = 2
    mana_rock = create_test_card("Sol Ring", "Artifact", "{1}", mana_production=2)

    opp_cost2 = board.calculate_opportunity_cost(mana_rock)
    print(f"\n✓ Opportunity Cost (Mana Rock early game):")
    print(f"  - Immediate value: {opp_cost2['immediate_value']:.2f}")
    print(f"  - Recommendation: {opp_cost2['recommendation']}")

    assert opp_cost2['immediate_value'] > 0, "Mana rock should have immediate value"

    print("\n✅ Opportunity Cost Calculation Test PASSED")


def main():
    print("\n" + "="*60)
    print("REAL-TIME AI DECISION METRICS TEST SUITE")
    print("="*60)

    try:
        test_library_stats()
        test_hand_resources()
        test_mana_efficiency()
        test_lookahead_playability()
        test_resource_scarcity()
        test_opportunity_cost()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*60)
        print("\nReal-time AI metrics are working correctly!")
        print("Ready for Phase 2: Integration into greedy loop")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
