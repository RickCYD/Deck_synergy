"""
Test to verify Teysa Karlov death trigger doubling is working correctly.

This test creates a controlled scenario where:
1. Multiple drain effects are on the battlefield
2. Teysa Karlov is cast
3. Creatures die
4. We verify the drain damage is DOUBLED with Teysa active
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulate_game import Card
from boardstate import BoardState


def create_drain_creature(name: str, drain_value: int = 1) -> Card:
    """Create a creature with death drain trigger."""
    oracle = f"Whenever a creature dies, each opponent loses {drain_value} life and you gain {drain_value} life."
    return Card(
        name=name,
        type="Creature",
        mana_cost="1B",
        power=1,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
        death_trigger_value=drain_value,  # This is what we're testing!
    )


def create_teysa() -> Card:
    """Create Teysa Karlov."""
    oracle = "If a creature dying causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time."
    return Card(
        name="Teysa Karlov",
        type="Creature",
        mana_cost="2WB",
        power=2,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle,
        death_trigger_value=0,
    )


def create_sacrifice_fodder(name: str) -> Card:
    """Create a basic creature to sacrifice."""
    return Card(
        name=name,
        type="Creature",
        mana_cost="1W",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="",
        death_trigger_value=0,
    )


def test_death_drain_without_teysa():
    """Test baseline: death drain without Teysa."""
    print("\n" + "="*70)
    print("TEST 1: Death drain WITHOUT Teysa Karlov")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put drain effects on board
    zulaport = create_drain_creature("Zulaport Cutthroat", 1)
    cruel_celebrant = create_drain_creature("Cruel Celebrant", 1)
    board.creatures = [zulaport, cruel_celebrant]

    # Create a creature to sacrifice
    token = create_sacrifice_fodder("Human Token")
    board.creatures.append(token)

    print(f"\nSetup:")
    print(f"  - Zulaport Cutthroat (1 drain/death)")
    print(f"  - Cruel Celebrant (1 drain/death)")
    print(f"  - 3 opponents at 40 life each")
    print(f"  - 1 token ready to sacrifice")

    # Trigger death
    board.drain_damage_this_turn = 0
    drain_total = board.trigger_death_effects(token, verbose=True)

    # Expected: 2 drain effects × 1 value × 3 opponents = 6 damage
    expected = 2 * 1 * 3

    print(f"\n📊 Results:")
    print(f"  Expected drain damage: {expected}")
    print(f"  Actual drain damage:   {drain_total}")
    print(f"  board.drain_damage_this_turn: {board.drain_damage_this_turn}")

    assert drain_total == expected, f"Expected {expected}, got {drain_total}"
    assert board.drain_damage_this_turn == expected, f"Expected {expected}, got {board.drain_damage_this_turn}"

    print(f"\n✅ PASSED: Baseline drain damage is correct (6 damage)")
    return drain_total


def test_death_drain_with_teysa():
    """Test: death drain WITH Teysa Karlov (should double!)."""
    print("\n" + "="*70)
    print("TEST 2: Death drain WITH Teysa Karlov (should DOUBLE!)")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put drain effects on board
    zulaport = create_drain_creature("Zulaport Cutthroat", 1)
    cruel_celebrant = create_drain_creature("Cruel Celebrant", 1)
    teysa = create_teysa()
    board.creatures = [zulaport, cruel_celebrant, teysa]

    # Create a creature to sacrifice
    token = create_sacrifice_fodder("Human Token")
    board.creatures.append(token)

    print(f"\nSetup:")
    print(f"  - Zulaport Cutthroat (1 drain/death)")
    print(f"  - Cruel Celebrant (1 drain/death)")
    print(f"  - TEYSA KARLOV (doubles death triggers!)")
    print(f"  - 3 opponents at 40 life each")
    print(f"  - 1 token ready to sacrifice")

    # Trigger death
    board.drain_damage_this_turn = 0
    drain_total = board.trigger_death_effects(token, verbose=True)

    # Expected: 2 drain effects × 1 value × 2 (TEYSA!) × 3 opponents = 12 damage
    expected = 2 * 1 * 2 * 3

    print(f"\n📊 Results:")
    print(f"  Expected drain damage (with Teysa 2x): {expected}")
    print(f"  Actual drain damage:                   {drain_total}")
    print(f"  board.drain_damage_this_turn:          {board.drain_damage_this_turn}")

    assert drain_total == expected, f"Expected {expected} (doubled!), got {drain_total}"
    assert board.drain_damage_this_turn == expected, f"Expected {expected}, got {board.drain_damage_this_turn}"

    print(f"\n✅ PASSED: Teysa correctly DOUBLES drain damage (12 damage)")
    return drain_total


def test_multiple_deaths_with_teysa():
    """Test: Multiple creature deaths with Teysa (realistic scenario)."""
    print("\n" + "="*70)
    print("TEST 3: Multiple deaths with Teysa (realistic sacrifice scenario)")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Put 4 drain effects on board (typical aristocrats board)
    zulaport = create_drain_creature("Zulaport Cutthroat", 1)
    cruel_celebrant = create_drain_creature("Cruel Celebrant", 1)
    mirkwood_bats = create_drain_creature("Mirkwood Bats", 1)
    bastion = create_drain_creature("Bastion of Remembrance", 1)
    teysa = create_teysa()
    board.creatures = [zulaport, cruel_celebrant, mirkwood_bats, bastion, teysa]

    print(f"\nSetup:")
    print(f"  - 4 drain effects (Zulaport, Cruel Celebrant, Mirkwood Bats, Bastion)")
    print(f"  - TEYSA KARLOV (doubles death triggers!)")
    print(f"  - 3 opponents at 40 life each")
    print(f"  - Sacrificing 5 tokens")

    # Sacrifice 5 tokens
    total_drain = 0
    board.drain_damage_this_turn = 0

    for i in range(5):
        token = create_sacrifice_fodder(f"Token {i+1}")
        board.creatures.append(token)
        drain = board.trigger_death_effects(token, verbose=False)
        total_drain += drain
        board.creatures.remove(token)

    # Expected per death: 4 drain × 1 value × 2 (Teysa) × 3 opponents = 24 damage
    # Total for 5 deaths: 24 × 5 = 120 damage
    expected_per_death = 4 * 1 * 2 * 3
    expected_total = expected_per_death * 5

    print(f"\n📊 Results:")
    print(f"  Expected per death (with Teysa): {expected_per_death} damage")
    print(f"  Expected total (5 deaths):       {expected_total} damage")
    print(f"  Actual total drain damage:       {total_drain} damage")
    print(f"  board.drain_damage_this_turn:    {board.drain_damage_this_turn}")

    assert total_drain == expected_total, f"Expected {expected_total}, got {total_drain}"
    assert board.drain_damage_this_turn == expected_total, f"Expected {expected_total}, got {board.drain_damage_this_turn}"

    print(f"\n✅ PASSED: Multiple deaths correctly tracked (120 damage total)")
    print(f"\n💀 Analysis: In a SINGLE TURN, sacrificing 5 tokens dealt 120 damage!")
    print(f"   This is why your deck is so powerful with Teysa active.")
    return total_drain


def test_teysa_removed_mid_game():
    """Test: Teysa gets removed, multiplier should stop."""
    print("\n" + "="*70)
    print("TEST 4: Teysa removed mid-game (multiplier should stop)")
    print("="*70)

    board = BoardState([], None)
    board.opponents = [
        {"name": "Opponent 1", "life_total": 40, "is_alive": True},
        {"name": "Opponent 2", "life_total": 40, "is_alive": True},
        {"name": "Opponent 3", "life_total": 40, "is_alive": True},
    ]

    # Setup with Teysa
    zulaport = create_drain_creature("Zulaport Cutthroat", 1)
    teysa = create_teysa()
    board.creatures = [zulaport, teysa]

    # First death WITH Teysa
    token1 = create_sacrifice_fodder("Token 1")
    board.creatures.append(token1)
    board.drain_damage_this_turn = 0
    drain1 = board.trigger_death_effects(token1, verbose=False)

    expected_with_teysa = 1 * 1 * 2 * 3  # 6 damage
    print(f"\nDeath 1 (with Teysa):    {drain1} damage (expected: {expected_with_teysa})")
    assert drain1 == expected_with_teysa

    # Remove Teysa
    board.creatures.remove(teysa)
    print(f"  → Teysa removed from battlefield")

    # Second death WITHOUT Teysa
    token2 = create_sacrifice_fodder("Token 2")
    board.creatures.append(token2)
    board.drain_damage_this_turn = 0
    drain2 = board.trigger_death_effects(token2, verbose=False)

    expected_without_teysa = 1 * 1 * 1 * 3  # 3 damage (NOT doubled!)
    print(f"Death 2 (without Teysa): {drain2} damage (expected: {expected_without_teysa})")
    assert drain2 == expected_without_teysa

    print(f"\n✅ PASSED: Multiplier correctly stops when Teysa is removed")
    print(f"   Damage went from {drain1} → {drain2} (halved)")


def run_all_tests():
    """Run all Teysa doubling tests."""
    print("\n" + "🧪"*35)
    print("TEYSA KARLOV DEATH TRIGGER DOUBLING - TEST SUITE")
    print("🧪"*35)

    try:
        # Run tests
        baseline = test_death_drain_without_teysa()
        doubled = test_death_drain_with_teysa()
        multiple = test_multiple_deaths_with_teysa()
        test_teysa_removed_mid_game()

        # Summary
        print("\n" + "="*70)
        print("📋 TEST SUMMARY")
        print("="*70)
        print(f"✅ Test 1: Baseline (no Teysa)    - {baseline} damage")
        print(f"✅ Test 2: With Teysa (doubled)   - {doubled} damage")
        print(f"✅ Test 3: Multiple deaths         - {multiple} damage")
        print(f"✅ Test 4: Teysa removed           - PASSED")
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n💡 Key Takeaway:")
        print(f"   Teysa Karlov DOUBLES all death drain damage!")
        print(f"   In your Queen Marchesa deck, this means:")
        print(f"   - 1 creature death = 6 damage → 12 damage (with Teysa)")
        print(f"   - 5 creature deaths = 30 damage → 60 damage (with Teysa)")
        print(f"   - 10 creature deaths = 60 damage → 120 damage (with Teysa)")
        print(f"\n   This is why your deck can easily deal 30+ damage in a single turn!")

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
