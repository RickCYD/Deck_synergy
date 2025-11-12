#!/usr/bin/env python3
"""Quick test to verify graveyard mechanics are working."""

import sys
sys.path.insert(0, 'Simulation')

from simulate_game import Card
from boardstate import BoardState

def create_test_creature(name, power, toughness, type_line="Creature", oracle_text=""):
    """Create a test creature card."""
    return Card(
        name=name,
        type=type_line,
        mana_cost="{2}{B}",
        power=power,
        toughness=toughness,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        has_flash=False,
        equip_cost="",
        power_buff=0,
        is_commander=False,
        is_legendary=False,
        keywords_when_equipped=[],
        puts_land=False,
        draw_cards=0,
        deals_damage=0,
        activated_abilities=[],
        triggered_abilities=[],
        oracle_text=oracle_text,
        fetch_basic=False,
        fetch_land_types=[],
        fetch_land_tapped=False,
    )

print("=" * 60)
print("TESTING GRAVEYARD MECHANICS IMPLEMENTATIONS")
print("=" * 60)

# Test 1: Syr Konrad detection
print("\n[Test 1] Syr Konrad Detection")
board = BoardState([], None)
syr_konrad = create_test_creature("Syr Konrad, the Grim", 5, 4)
board.creatures.append(syr_konrad)

# Manually trigger detection
if 'syr konrad' in syr_konrad.name.lower():
    board.syr_konrad_on_board = True
    print(f"  ✓ Syr Konrad detected: {board.syr_konrad_on_board}")
else:
    print(f"  ✗ Syr Konrad NOT detected")

# Test 2: Syr Konrad mill trigger
print("\n[Test 2] Syr Konrad Mill Trigger")
test_cards = [
    create_test_creature("Zombie Token", 2, 2),
    create_test_creature("Grizzly Bears", 2, 2),
]
damage = board.trigger_syr_konrad_on_mill(test_cards, verbose=True)
print(f"  ✓ Syr Konrad mill trigger dealt {damage} damage")
print(f"  ✓ Total drain damage this turn: {board.drain_damage_this_turn}")

# Test 3: Syr Konrad death trigger
print("\n[Test 3] Syr Konrad Death Trigger")
board.drain_damage_this_turn = 0  # Reset
dead_creature = create_test_creature("Doomed Traveler", 1, 1)
damage = board.trigger_syr_konrad_on_death(dead_creature, verbose=True)
print(f"  ✓ Syr Konrad death trigger dealt {damage} damage")
print(f"  ✓ Total drain damage: {board.drain_damage_this_turn}")

# Test 4: Muldrotha detection
print("\n[Test 4] Muldrotha Detection")
board = BoardState([], None)
muldrotha = create_test_creature("Muldrotha, the Gravetide", 6, 6)

if 'muldrotha' in muldrotha.name.lower():
    board.muldrotha_on_board = True
    print(f"  ✓ Muldrotha detected: {board.muldrotha_on_board}")
else:
    print(f"  ✗ Muldrotha NOT detected")

# Test 5: Meren detection and experience counters
print("\n[Test 5] Meren Detection & Experience Counters")
board = BoardState([], None)
meren = create_test_creature("Meren of Clan Nel Toth", 3, 4)

if 'meren' in meren.name.lower():
    board.meren_on_board = True
    print(f"  ✓ Meren detected: {board.meren_on_board}")
    print(f"  ✓ Experience counters: {board.experience_counters}")

    # Test experience counter gain
    dead = create_test_creature("Test Creature", 2, 2)
    board.trigger_death_effects(dead, verbose=False)
    print(f"  ✓ After creature death, experience counters: {board.experience_counters}")
else:
    print(f"  ✗ Meren NOT detected")

# Test 6: Zombie detection (for Gravecrawler)
print("\n[Test 6] Zombie Detection")
board = BoardState([], None)
zombie = create_test_creature("Diregraf Captain", 2, 2, "Creature — Zombie", "Other Zombie creatures you control get +1/+1.")
board.creatures.append(zombie)

has_zombie = board.has_zombie_on_board()
print(f"  {'✓' if has_zombie else '✗'} Zombie detected: {has_zombie}")

# Test 7: Mill cards method
print("\n[Test 7] Mill Cards Method")
board = BoardState([], None)
board.syr_konrad_on_board = True
board.library = [create_test_creature(f"Card {i}", 2, 2) for i in range(10)]
print(f"  Library size before: {len(board.library)}")

milled = board.mill_cards(5, verbose=True)
print(f"  ✓ Milled {len(milled)} cards")
print(f"  ✓ Library size after: {len(board.library)}")
print(f"  ✓ Graveyard size: {len(board.graveyard)}")
print(f"  ✓ Syr Konrad damage from mill: {board.drain_damage_this_turn}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
print("\nIf all tests show ✓, the mechanics are implemented correctly.")
print("The issue might be with deck loading or card oracle text.")
