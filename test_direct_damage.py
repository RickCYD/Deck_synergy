#!/usr/bin/env python3
"""
Test script to verify direct damage spell implementation.
"""

import sys
from pathlib import Path

# Add Simulation directory to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from simulate_game import Card
from boardstate import BoardState
from oracle_text_parser import parse_direct_damage_from_oracle


def test_damage_parsing():
    """Test that damage parsing works correctly."""
    print("="*80)
    print("TEST 1: Damage Parsing from Oracle Text")
    print("="*80)

    test_cases = [
        ("Lightning Bolt", "Lightning Bolt deals 3 damage to any target.", 3),
        ("Shock", "Shock deals 2 damage to any target.", 2),
        ("Lava Spike", "Lava Spike deals 3 damage to target player or planeswalker.", 3),
        ("Lightning Strike", "Lightning Strike deals 3 damage to any target.", 3),
        ("Flame Rift", "Flame Rift deals 4 damage to each player.", 4),
        ("Fireball", "Fireball deals X damage to any target.", 0),  # X spells return 0
    ]

    passed = 0
    failed = 0

    for name, oracle, expected in test_cases:
        result = parse_direct_damage_from_oracle(oracle, name)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} {name}: expected {expected}, got {result}")

    print(f"\nParsing Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_damage_execution():
    """Test that damage is actually dealt when spells are cast."""
    print("\n" + "="*80)
    print("TEST 2: Damage Execution in Game")
    print("="*80)

    # Create a simple commander
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production={},
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=True
    )

    # Create a minimal deck
    deck = []

    # Create a simple board state
    board = BoardState(deck, commander)

    # Create Lightning Bolt
    lightning_bolt = Card(
        name="Lightning Bolt",
        type="Instant",
        mana_cost="{R}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production={},
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=False,
        deals_damage=3,  # Direct damage
        oracle_text="Lightning Bolt deals 3 damage to any target."
    )

    # Create Shock
    shock = Card(
        name="Shock",
        type="Instant",
        mana_cost="{R}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production={},
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=False,
        deals_damage=2,
        oracle_text="Shock deals 2 damage to any target."
    )

    # Add mana and cards to hand
    board.mana_pool = [{"R": 1}] * 5
    board.hand = [lightning_bolt, shock]

    # Check initial opponent life
    initial_life = board.opponents[0]['life_total']
    print(f"\nInitial opponent life: {initial_life}")

    # Cast Lightning Bolt
    print("\nCasting Lightning Bolt (3 damage)...")
    board.play_instant(lightning_bolt, verbose=False)
    life_after_bolt = board.opponents[0]['life_total']
    bolt_damage = initial_life - life_after_bolt
    print(f"  Opponent life: {life_after_bolt} (dealt {bolt_damage} damage)")
    print(f"  Spell damage this turn: {board.spell_damage_this_turn}")

    # Cast Shock
    print("\nCasting Shock (2 damage)...")
    board.play_instant(shock, verbose=False)
    life_after_shock = board.opponents[0]['life_total']
    shock_damage = life_after_bolt - life_after_shock
    print(f"  Opponent life: {life_after_shock} (dealt {shock_damage} damage)")
    print(f"  Spell damage this turn: {board.spell_damage_this_turn}")

    # Verify results
    expected_total = 3 + 2  # Lightning Bolt + Shock
    actual_total = initial_life - life_after_shock
    expected_spell_damage = 5  # 3 + 2

    print(f"\nExpected total damage: {expected_total}")
    print(f"Actual total damage: {actual_total}")
    print(f"Expected spell_damage_this_turn: {expected_spell_damage}")
    print(f"Actual spell_damage_this_turn: {board.spell_damage_this_turn}")

    # Check if test passed
    passed = (actual_total == expected_total and
              board.spell_damage_this_turn == expected_spell_damage)

    if passed:
        print("\n✓ Damage Execution Test PASSED")
    else:
        print("\n✗ Damage Execution Test FAILED")

    return passed


def main():
    """Run all tests."""
    print("TESTING DIRECT DAMAGE SPELL IMPLEMENTATION")
    print("="*80)

    test1_passed = test_damage_parsing()
    test2_passed = test_damage_execution()

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"Test 1 (Damage Parsing): {'PASSED ✓' if test1_passed else 'FAILED ✗'}")
    print(f"Test 2 (Damage Execution): {'PASSED ✓' if test2_passed else 'FAILED ✗'}")

    if test1_passed and test2_passed:
        print("\n✓ ALL TESTS PASSED!")
        print("\nDirect damage spells are now working correctly.")
        print("Spells like Lightning Bolt, Shock, etc. will now deal damage in simulations.")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
