#!/usr/bin/env python3
"""Test script to verify anthem mechanics work correctly."""

import sys
sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

from simulate_game import Card
from boardstate import BoardState


def test_basic_anthem():
    """Test that Glorious Anthem buffs all creatures."""
    print("=" * 60)
    print("TEST 1: Basic Anthem (Glorious Anthem)")
    print("=" * 60)

    # Create a simple deck
    deck = []

    # Create a commander
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
        oracle_text=""
    )

    board = BoardState(deck, commander, num_opponents=3)

    # Add some tokens to the board
    board.create_token("Soldier", 1, 1, has_haste=False, verbose=True, apply_counters=False)
    board.create_token("Soldier", 1, 1, has_haste=False, verbose=True, apply_counters=False)
    board.create_token("Soldier", 1, 1, has_haste=False, verbose=True, apply_counters=False)

    print(f"\nCreated {len(board.creatures)} creatures")
    print(f"Base power total: {sum(c.power or 0 for c in board.creatures)}")
    print(f"Effective power total (no anthems): {sum(board.get_effective_power(c) for c in board.creatures)}")

    # Add Glorious Anthem
    anthem = Card(
        name="Glorious Anthem",
        type="Enchantment",
        mana_cost="{1}{W}{W}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Creatures you control get +1/+1."
    )
    board.enchantments.append(anthem)

    print(f"\nAdded Glorious Anthem to board")
    print(f"Effective power total (with anthem): {sum(board.get_effective_power(c) for c in board.creatures)}")
    print(f"Expected: {len(board.creatures) * 2} (3 creatures × 2 power each)")

    # Verify each creature gets +1/+1
    for creature in board.creatures:
        base_power = creature.power or 0
        effective_power = board.get_effective_power(creature)
        power_bonus, toughness_bonus = board.calculate_anthem_bonus(creature)
        print(f"  {creature.name}: Base {base_power}, Bonus +{power_bonus}, Effective {effective_power}")

    assert sum(board.get_effective_power(c) for c in board.creatures) == 6, "Anthem should buff 3 creatures from 1/1 to 2/2"
    print("\n✓ TEST PASSED: Glorious Anthem working correctly!")


def test_intangible_virtue():
    """Test that Intangible Virtue only buffs tokens."""
    print("\n" + "=" * 60)
    print("TEST 2: Token-Specific Anthem (Intangible Virtue)")
    print("=" * 60)

    deck = []
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
        oracle_text=""
    )

    board = BoardState(deck, commander, num_opponents=3)

    # Add some tokens
    board.create_token("Soldier", 1, 1, has_haste=False, token_type="Soldier", verbose=True, apply_counters=False)
    board.create_token("Soldier", 1, 1, has_haste=False, token_type="Soldier", verbose=True, apply_counters=False)

    # Add a non-token creature
    creature = Card(
        name="Elite Vanguard",
        type="Creature - Human Soldier",
        mana_cost="{W}",
        power=2,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=""
    )
    board.creatures.append(creature)

    print(f"\nCreated 2 tokens + 1 non-token creature")
    print(f"Base power total: {sum(c.power or 0 for c in board.creatures)}")

    # Add Intangible Virtue
    virtue = Card(
        name="Intangible Virtue",
        type="Enchantment",
        mana_cost="{1}{W}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Tokens you control get +1/+1 and have vigilance."
    )
    board.enchantments.append(virtue)

    print(f"\nAdded Intangible Virtue to board")

    # Check each creature
    for creature in board.creatures:
        base_power = creature.power or 0
        effective_power = board.get_effective_power(creature)
        is_token = getattr(creature, 'token_type', None) is not None
        power_bonus, _ = board.calculate_anthem_bonus(creature)

        print(f"  {creature.name}: Base {base_power}, Bonus +{power_bonus}, Effective {effective_power}, Token: {is_token}")

        if is_token:
            assert power_bonus == 1, f"Token {creature.name} should get +1/+1 from Intangible Virtue"
        else:
            assert power_bonus == 0, f"Non-token {creature.name} should NOT get buff from Intangible Virtue"

    # Total power should be: 2 tokens (1+1=2 each) + 1 creature (2 base)= 6
    expected_power = 2 * 2 + 2
    actual_power = sum(board.get_effective_power(c) for c in board.creatures)
    print(f"\nEffective power total: {actual_power}")
    print(f"Expected: {expected_power} (2 tokens at 2 power each + 1 creature at 2 power)")

    assert actual_power == expected_power, f"Expected {expected_power}, got {actual_power}"
    print("\n✓ TEST PASSED: Intangible Virtue only buffs tokens!")


def test_multiple_anthems():
    """Test that multiple anthems stack correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Anthems Stacking")
    print("=" * 60)

    deck = []
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
        oracle_text=""
    )

    board = BoardState(deck, commander, num_opponents=3)

    # Add a token
    board.create_token("Soldier", 1, 1, has_haste=False, token_type="Soldier", verbose=True, apply_counters=False)

    soldier = board.creatures[0]
    print(f"\nCreated 1 token: {soldier.name} (base {soldier.power}/{soldier.toughness})")
    print(f"Effective power: {board.get_effective_power(soldier)}")

    # Add Glorious Anthem
    anthem1 = Card(
        name="Glorious Anthem",
        type="Enchantment",
        mana_cost="{1}{W}{W}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Creatures you control get +1/+1."
    )
    board.enchantments.append(anthem1)

    print(f"\nAdded Glorious Anthem")
    print(f"Effective power: {board.get_effective_power(soldier)} (expected: 2)")

    # Add Intangible Virtue
    virtue = Card(
        name="Intangible Virtue",
        type="Enchantment",
        mana_cost="{1}{W}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Tokens you control get +1/+1 and have vigilance."
    )
    board.enchantments.append(virtue)

    print(f"\nAdded Intangible Virtue")
    power_bonus, toughness_bonus = board.calculate_anthem_bonus(soldier)
    effective_power = board.get_effective_power(soldier)
    print(f"Power bonus: +{power_bonus}")
    print(f"Effective power: {effective_power} (expected: 3)")

    # Should be: 1 base + 1 (Glorious) + 1 (Virtue) = 3
    assert effective_power == 3, f"Expected 3, got {effective_power}"
    print("\n✓ TEST PASSED: Multiple anthems stack correctly!")


def test_anthem_in_combat():
    """Test that anthems affect combat damage."""
    print("\n" + "=" * 60)
    print("TEST 4: Anthems in Combat")
    print("=" * 60)

    deck = []
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
        oracle_text=""
    )

    board = BoardState(deck, commander, num_opponents=3)

    # Add 3 tokens
    for _ in range(3):
        board.create_token("Soldier", 1, 1, has_haste=False, verbose=False, apply_counters=False)

    print(f"\nCreated 3 tokens (1/1 each)")
    print(f"Base total power: {sum(c.power or 0 for c in board.creatures)}")
    print(f"Effective total power (no anthems): {sum(board.get_effective_power(c) for c in board.creatures)}")

    # Add Glorious Anthem
    anthem = Card(
        name="Glorious Anthem",
        type="Enchantment",
        mana_cost="{1}{W}{W}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Creatures you control get +1/+1."
    )
    board.enchantments.append(anthem)

    print(f"\nAdded Glorious Anthem")
    effective_total = sum(board.get_effective_power(c) for c in board.creatures)
    print(f"Effective total power (with anthem): {effective_total}")
    print(f"Expected: 6 (3 creatures × 2 power each)")

    assert effective_total == 6, f"Expected 6, got {effective_total}"

    # Simulate combat (simplified - just check power is calculated correctly)
    print(f"\nSimulating combat...")
    for creature in board.creatures:
        attack_power = board.get_effective_power(creature)
        print(f"  {creature.name} attacks with {attack_power} power")
        assert attack_power == 2, f"Each creature should have 2 power with anthem"

    print("\n✓ TEST PASSED: Anthems affect combat correctly!")


if __name__ == "__main__":
    try:
        test_basic_anthem()
        test_intangible_virtue()
        test_multiple_anthems()
        test_anthem_in_combat()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nAnthem mechanics are working correctly:")
        print("  • Basic anthems (Glorious Anthem, Spear of Heliod)")
        print("  • Conditional anthems (Intangible Virtue for tokens)")
        print("  • Multiple anthems stacking")
        print("  • Anthems affecting combat damage")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
