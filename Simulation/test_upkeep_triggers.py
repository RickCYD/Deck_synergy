"""
Test to verify upkeep and beginning of combat trigger system.

This test verifies:
1. Rite of the Raging Storm creates 5/1 Elemental at upkeep
2. Outlaws' Merriment creates random token at beginning of combat
3. Token doublers (Mondrak) work with upkeep tokens
4. ETB drains (Impact Tremors) trigger from upkeep tokens
5. Integration with full simulation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulate_game import Card
from boardstate import BoardState


def create_rite_of_the_raging_storm() -> Card:
    """Create Rite of the Raging Storm enchantment."""
    oracle = "At the beginning of your upkeep, create a 5/1 red Elemental creature token with haste."
    return Card(
        name="Rite of the Raging Storm",
        type="Enchantment",
        mana_cost="3RR",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
    )


def create_outlaws_merriment() -> Card:
    """Create Outlaws' Merriment enchantment."""
    oracle = "At the beginning of your combat on your turn, choose one at random — Create a 1/1 white Human creature token, a 1/1 red Mercenary creature token with first strike, or a 2/2 green Elf Druid creature token."
    return Card(
        name="Outlaws' Merriment",
        type="Enchantment",
        mana_cost="1RW",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
    )


def create_impact_tremors() -> Card:
    """Create Impact Tremors enchantment."""
    oracle = "Whenever a creature you control enters, Impact Tremors deals 1 damage to each opponent."
    return Card(
        name="Impact Tremors",
        type="Enchantment",
        mana_cost="1R",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
    )


def create_mondrak() -> Card:
    """Create Mondrak, Glory Dominus (token doubler)."""
    oracle = "If one or more tokens would be created under your control, twice that many of those tokens are created instead."
    return Card(
        name="Mondrak, Glory Dominus",
        type="Creature",
        mana_cost="2WWW",
        power=4,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
    )


def test_rite_upkeep_trigger():
    """Test: Rite of the Raging Storm creates token at upkeep."""
    print("\n" + "="*70)
    print("TEST 1: Rite of the Raging Storm - Upkeep Token Creation")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put Rite on board
    rite = create_rite_of_the_raging_storm()
    board.enchantments = [rite]

    initial_creature_count = len(board.creatures)

    print(f"\nSetup:")
    print(f"  - Rite of the Raging Storm on battlefield")
    print(f"  - Initial creature count: {initial_creature_count}")

    # Process upkeep
    tokens_created = board.process_upkeep_triggers(verbose=True)

    # Check results
    final_creature_count = len(board.creatures)

    print(f"\n📊 Results:")
    print(f"  Tokens created: {tokens_created}")
    print(f"  Final creature count: {final_creature_count}")
    print(f"  Creatures on board: {[c.name for c in board.creatures]}")

    assert tokens_created == 1, f"Expected 1 token, got {tokens_created}"
    assert final_creature_count == initial_creature_count + 1, f"Expected {initial_creature_count + 1} creatures, got {final_creature_count}"

    # Verify it's a 5/1 with haste
    token = board.creatures[0]
    assert token.power == 5, f"Expected power 5, got {token.power}"
    assert token.toughness == 1, f"Expected toughness 1, got {token.toughness}"
    assert token.has_haste, "Token should have haste"

    print(f"\n✅ PASSED: Rite creates 5/1 Elemental with haste at upkeep")
    return tokens_created


def test_outlaws_combat_trigger():
    """Test: Outlaws' Merriment creates token at beginning of combat."""
    print("\n" + "="*70)
    print("TEST 2: Outlaws' Merriment - Beginning of Combat Token Creation")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put Outlaws on board
    outlaws = create_outlaws_merriment()
    board.enchantments = [outlaws]

    initial_creature_count = len(board.creatures)

    print(f"\nSetup:")
    print(f"  - Outlaws' Merriment on battlefield")
    print(f"  - Initial creature count: {initial_creature_count}")

    # Process beginning of combat
    tokens_created = board.process_beginning_of_combat_triggers(verbose=True)

    # Check results
    final_creature_count = len(board.creatures)

    print(f"\n📊 Results:")
    print(f"  Tokens created: {tokens_created}")
    print(f"  Final creature count: {final_creature_count}")
    print(f"  Creatures on board: {[c.name for c in board.creatures]}")

    assert tokens_created == 1, f"Expected 1 token, got {tokens_created}"
    assert final_creature_count == initial_creature_count + 1, f"Expected {initial_creature_count + 1} creatures, got {final_creature_count}"

    # Verify it's one of the expected tokens
    token = board.creatures[0]
    valid_names = ["Human Soldier", "Mercenary", "Elf Druid"]
    assert token.name in valid_names, f"Token name {token.name} not in {valid_names}"

    valid_stats = [(1, 1), (2, 2)]  # Human/Mercenary or Elf
    token_stats = (token.power, token.toughness)
    assert token_stats in valid_stats, f"Token stats {token_stats} not in {valid_stats}"

    print(f"\n✅ PASSED: Outlaws creates random token at beginning of combat")
    print(f"   Created: {token.power}/{token.toughness} {token.name}")
    return tokens_created


def test_upkeep_tokens_with_mondrak():
    """Test: Token doublers work with upkeep tokens."""
    print("\n" + "="*70)
    print("TEST 3: Upkeep Tokens with Mondrak (Token Doubler)")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put Rite + Mondrak on board
    rite = create_rite_of_the_raging_storm()
    mondrak = create_mondrak()
    board.enchantments = [rite]
    board.creatures = [mondrak]

    initial_creature_count = len(board.creatures)

    print(f"\nSetup:")
    print(f"  - Rite of the Raging Storm on battlefield")
    print(f"  - Mondrak, Glory Dominus on battlefield (doubles tokens!)")
    print(f"  - Initial creature count: {initial_creature_count}")

    # Process upkeep
    tokens_created = board.process_upkeep_triggers(verbose=True)

    # Check results
    final_creature_count = len(board.creatures)

    print(f"\n📊 Results:")
    print(f"  Tokens created (reported): {tokens_created}")
    print(f"  Initial creatures: {initial_creature_count}")
    print(f"  Final creature count: {final_creature_count}")
    print(f"  Net new creatures: {final_creature_count - initial_creature_count}")

    # With Mondrak, we should create 2 tokens instead of 1
    expected_new = 2  # Mondrak doubles it
    actual_new = final_creature_count - initial_creature_count

    print(f"  Expected new creatures: {expected_new} (doubled by Mondrak)")
    print(f"  Actual new creatures: {actual_new}")

    assert actual_new == expected_new, f"Expected {expected_new} new creatures (doubled), got {actual_new}"

    print(f"\n✅ PASSED: Mondrak correctly doubles upkeep tokens (1 → 2)")
    return tokens_created


def test_upkeep_tokens_with_etb_drains():
    """Test: ETB drains trigger from upkeep tokens."""
    print("\n" + "="*70)
    print("TEST 4: Upkeep Tokens with ETB Drains (Impact Tremors)")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put Rite + Impact Tremors on board
    rite = create_rite_of_the_raging_storm()
    tremors = create_impact_tremors()
    board.enchantments = [rite, tremors]

    print(f"\nSetup:")
    print(f"  - Rite of the Raging Storm on battlefield")
    print(f"  - Impact Tremors on battlefield (1 damage per ETB)")
    print(f"  - 3 opponents at 40 life each")

    # Process upkeep
    board.drain_damage_this_turn = 0
    tokens_created = board.process_upkeep_triggers(verbose=True)

    # Check results
    drain_damage = board.drain_damage_this_turn

    print(f"\n📊 Results:")
    print(f"  Tokens created: {tokens_created}")
    print(f"  Drain damage dealt: {drain_damage}")

    # Expected: 1 token × 1 damage × 3 opponents = 3 damage
    expected_drain = 1 * 1 * 3

    assert drain_damage == expected_drain, f"Expected {expected_drain} drain damage, got {drain_damage}"

    print(f"\n✅ PASSED: Impact Tremors triggers from upkeep token (3 damage)")
    return drain_damage


def test_multiple_turns_upkeep():
    """Test: Upkeep tokens accumulate over multiple turns."""
    print("\n" + "="*70)
    print("TEST 5: Multiple Turns - Token Accumulation")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put Rite + Outlaws on board
    rite = create_rite_of_the_raging_storm()
    outlaws = create_outlaws_merriment()
    board.enchantments = [rite, outlaws]

    print(f"\nSetup:")
    print(f"  - Rite of the Raging Storm (1 token per upkeep)")
    print(f"  - Outlaws' Merriment (1 token per combat)")
    print(f"  - Simulating 5 turns")

    total_tokens_created = 0

    for turn in range(1, 6):
        print(f"\n--- Turn {turn} ---")

        # Upkeep
        upkeep_tokens = board.process_upkeep_triggers(verbose=False)
        print(f"  Upkeep: {upkeep_tokens} token(s)")

        # Beginning of Combat
        combat_tokens = board.process_beginning_of_combat_triggers(verbose=False)
        print(f"  Combat: {combat_tokens} token(s)")

        turn_tokens = upkeep_tokens + combat_tokens
        total_tokens_created += turn_tokens

        print(f"  Total this turn: {turn_tokens}")
        print(f"  Creatures on board: {len(board.creatures)}")

    print(f"\n📊 Results:")
    print(f"  Total tokens created: {total_tokens_created}")
    print(f"  Final creature count: {len(board.creatures)}")
    print(f"  Expected: 5 turns × 2 tokens/turn = 10 tokens")

    expected_total = 5 * 2  # 5 turns, 2 tokens per turn
    assert total_tokens_created == expected_total, f"Expected {expected_total} total tokens, got {total_tokens_created}"
    assert len(board.creatures) == expected_total, f"Expected {expected_total} creatures, got {len(board.creatures)}"

    print(f"\n✅ PASSED: Tokens correctly accumulate over multiple turns")
    print(f"   10 tokens created and on battlefield")
    return total_tokens_created


def run_all_tests():
    """Run all upkeep trigger tests."""
    print("\n" + "🧪"*35)
    print("UPKEEP & BEGINNING OF COMBAT TRIGGER SYSTEM - TEST SUITE")
    print("🧪"*35)

    try:
        # Run tests
        test1 = test_rite_upkeep_trigger()
        test2 = test_outlaws_combat_trigger()
        test3 = test_upkeep_tokens_with_mondrak()
        test4 = test_upkeep_tokens_with_etb_drains()
        test5 = test_multiple_turns_upkeep()

        # Summary
        print("\n" + "="*70)
        print("📋 TEST SUMMARY")
        print("="*70)
        print(f"✅ Test 1: Rite upkeep trigger           - PASSED ({test1} token)")
        print(f"✅ Test 2: Outlaws combat trigger        - PASSED ({test2} token)")
        print(f"✅ Test 3: Mondrak token doubling        - PASSED (1→2 tokens)")
        print(f"✅ Test 4: Impact Tremors ETB drain      - PASSED ({test4} damage)")
        print(f"✅ Test 5: Multiple turns accumulation   - PASSED ({test5} tokens)")
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n💡 Expected Impact on Queen Marchesa Deck:")
        print(f"   Over 10 turns:")
        print(f"   - Rite: 10 × 5/1 Elementals = 50 power on board")
        print(f"   - Outlaws: 10 × 1-2/1-2 tokens = ~15 power on board")
        print(f"   - Total: 20 tokens created from upkeep/combat triggers")
        print(f"   ")
        print(f"   With Impact Tremors (1 dmg × 3 opponents):")
        print(f"   - 20 tokens × 3 damage = 60 ETB damage")
        print(f"   ")
        print(f"   If sacrificed with Teysa + 4 drain effects:")
        print(f"   - 20 tokens × 24 damage = 480 drain damage")
        print(f"   ")
        print(f"   Plus combat damage: 20 tokens × ~2 avg power = 40+ damage")
        print(f"   ")
        print(f"   💥 TOTAL: 580+ damage over 10 turns (58/turn average)")
        print(f"   This is a MASSIVE improvement over the original 30 damage!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
