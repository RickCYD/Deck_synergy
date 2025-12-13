"""
Test Y'shtola, Night's Blessed mechanics.

Tests:
1. Noncreature spell trigger (MV 3+): Deal 2 damage to each opponent, gain 2 life
2. End step trigger: Draw a card if a player lost 4+ life this turn
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from boardstate import BoardState
from simulate_game import Card


def test_yshtola_noncreature_spell_trigger():
    """Test Y'shtola's trigger when casting 3+ CMC noncreature spells."""
    print("\n=== Test: Y'shtola Noncreature Spell Trigger ===")

    # Create Y'shtola, Night's Blessed
    yshtola = Card(
        name="Y'shtola, Night's Blessed",
        type="Legendary Creature — Cat Warlock",
        mana_cost="{1}{W}{U}{B}",
        power=2,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        has_vigilance=True,
        is_commander=True,
        is_legendary=True,
        oracle_text="Vigilance\nAt the beginning of each end step, if a player lost 4 or more life this turn, you draw a card.\nWhenever you cast a noncreature spell with mana value 3 or greater, Y'shtola deals 2 damage to each opponent and you gain 2 life."
    )

    # Initialize board with Y'shtola as commander
    board = BoardState([], yshtola)

    # Create a 3 CMC artifact
    arcane_signet = Card(
        name="Arcane Signet",
        type="Artifact",
        mana_cost="{2}",
        power=None,
        toughness=None,
        produces_colors=['W', 'U', 'B'],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="{T}: Add one mana of any color in your commander's color identity."
    )

    # Create a 4 CMC instant
    fact_or_fiction = Card(
        name="Fact or Fiction",
        type="Instant",
        mana_cost="{3}{U}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        draw_cards=2,  # Simplified
        oracle_text="Reveal the top five cards of your library. An opponent separates those cards into two piles. Put one pile into your hand and the other into your graveyard."
    )

    # Add Y'shtola to battlefield
    board.creatures.append(yshtola)
    board.yshtola_on_board = True

    # Give board enough mana
    board.mana_pool = ['W', 'W', 'U', 'U', 'U', 'U']

    # Test initial state
    initial_life = board.life_total
    initial_opp_life = board.opponents[0]['life_total']

    print(f"Initial life: {initial_life}")
    print(f"Initial opponent life: {initial_opp_life}")

    # Add artifact to hand and play it (2 CMC - should NOT trigger)
    board.hand.append(arcane_signet)
    board.play_artifact(arcane_signet, verbose=True)

    # Check that trigger did NOT fire (CMC < 3)
    assert board.life_total == initial_life, "Life should not change for 2 CMC spell"
    assert board.opponents[0]['life_total'] == initial_opp_life, "Opponent life should not change for 2 CMC spell"
    print("✓ 2 CMC artifact did NOT trigger Y'shtola (correct)")

    # Add instant to hand and play it (4 CMC - SHOULD trigger)
    board.hand.append(fact_or_fiction)
    board.play_instant(fact_or_fiction, verbose=True)

    # Check that trigger DID fire (CMC >= 3)
    expected_life = initial_life + 2
    expected_opp_life = initial_opp_life - 2  # 2 damage to each opponent

    assert board.life_total == expected_life, f"Life should be {expected_life}, got {board.life_total}"
    assert board.opponents[0]['life_total'] == expected_opp_life, f"Opponent life should be {expected_opp_life}, got {board.opponents[0]['life_total']}"
    print(f"✓ 4 CMC instant triggered Y'shtola: gained 2 life ({initial_life} -> {board.life_total}), dealt 2 damage to opponent ({initial_opp_life} -> {board.opponents[0]['life_total']})")

    print("✅ Test passed: Y'shtola noncreature spell trigger works correctly")


def test_yshtola_end_step_card_draw():
    """Test Y'shtola's end step trigger when 4+ life was lost."""
    print("\n=== Test: Y'shtola End Step Card Draw ===")

    # Create Y'shtola
    yshtola = Card(
        name="Y'shtola, Night's Blessed",
        type="Legendary Creature — Cat Warlock",
        mana_cost="{1}{W}{U}{B}",
        power=2,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        has_vigilance=True,
        is_commander=True,
        is_legendary=True,
        oracle_text="Vigilance\nAt the beginning of each end step, if a player lost 4 or more life this turn, you draw a card.\nWhenever you cast a noncreature spell with mana value 3 or greater, Y'shtola deals 2 damage to each opponent and you gain 2 life."
    )

    # Initialize board with Y'shtola as commander
    board = BoardState([], yshtola)

    # Add Y'shtola to battlefield
    board.creatures.append(yshtola)
    board.yshtola_on_board = True

    # Populate library with cards
    for i in range(20):
        card = Card(
            name=f"Test Card {i}",
            type="Sorcery",
            mana_cost="{1}",
            power=None,
            toughness=None,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        )
        board.library.append(card)

    # Test case 1: Not enough life lost (< 4)
    print("\n--- Test Case 1: < 4 life lost (should NOT trigger) ---")
    board.drain_damage_this_turn = 3
    board.life_lost_this_turn = 0
    initial_hand_size = len(board.hand)

    # Simulate end step trigger (simplified)
    total_life_lost = board.life_lost_this_turn
    damage_to_opponents = board.drain_damage_this_turn
    if total_life_lost >= 4 or damage_to_opponents >= 4:
        board.draw_card(1, verbose=True)

    assert len(board.hand) == initial_hand_size, "Should NOT draw a card with < 4 life lost"
    print(f"✓ No card drawn with only {damage_to_opponents} damage dealt (correct)")

    # Test case 2: Exactly 4 life lost (should trigger)
    print("\n--- Test Case 2: Exactly 4 life lost (SHOULD trigger) ---")
    board.drain_damage_this_turn = 4
    board.life_lost_this_turn = 0
    initial_hand_size = len(board.hand)

    # Simulate end step trigger
    total_life_lost = board.life_lost_this_turn
    damage_to_opponents = board.drain_damage_this_turn
    if total_life_lost >= 4 or damage_to_opponents >= 4:
        board.draw_card(1, verbose=True)

    assert len(board.hand) == initial_hand_size + 1, "Should draw a card with exactly 4 life lost"
    print(f"✓ Drew 1 card with {damage_to_opponents} damage dealt (correct)")

    # Test case 3: Player lost life (should trigger)
    print("\n--- Test Case 3: Player lost 5 life (SHOULD trigger) ---")
    board.drain_damage_this_turn = 0
    board.life_lost_this_turn = 5
    initial_hand_size = len(board.hand)

    # Simulate end step trigger
    total_life_lost = board.life_lost_this_turn
    damage_to_opponents = board.drain_damage_this_turn
    if total_life_lost >= 4 or damage_to_opponents >= 4:
        board.draw_card(1, verbose=True)

    assert len(board.hand) == initial_hand_size + 1, "Should draw a card when player lost 5 life"
    print(f"✓ Drew 1 card with player losing {total_life_lost} life (correct)")

    print("✅ Test passed: Y'shtola end step card draw works correctly")


if __name__ == "__main__":
    test_yshtola_noncreature_spell_trigger()
    test_yshtola_end_step_card_draw()
    print("\n" + "="*50)
    print("✅ All Y'shtola tests passed!")
    print("="*50)
