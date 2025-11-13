#!/usr/bin/env python3
"""
Test the main phase loop to see why creatures aren't being cast.
"""

import sys
sys.path.insert(0, 'Simulation')

from deck_loader import load_deck_from_csv
from simulate_game import BoardState, Mana_utils, draw_starting_hand
import random

# Load deck
cards, commander, _ = load_deck_from_csv("zurgo_deck.csv")

print("="*100)
print("TESTING MAIN PHASE LOOP - WHY NO CREATURES ARE CAST")
print("="*100)

# Set up a turn 3 scenario manually
board = BoardState(cards, commander)
board.turn = 3
board.lands_untapped = []
board.lands_tapped = []
board.hand = []
board.library = cards[:]
board.creatures = []
board.artifacts = []
board.equipment_attached = []

# Add 3 lands to battlefield
plains = next(c for c in cards if c.name == "Plains")
nomad = next(c for c in cards if c.name == "Nomad Outpost")
canyon = next(c for c in cards if "Canyon" in c.name)

board.lands_untapped = [plains, nomad, canyon]

# Add creatures to hand
elas = next(c for c in cards if "Elas il-Kor" in c.name)
delina = next(c for c in cards if "Delina" in c.name)
queen = next(c for c in cards if "Queen Marchesa" in c.name)

board.hand = [elas, delina, queen]

print("\nSetup:")
print(f"  Turn: {board.turn}")
print(f"  Lands: {[l.name for l in board.lands_untapped]}")
print(f"  Hand: {[c.name for c in board.hand]}")
print(f"  Creatures on board: {len(board.creatures)}")

# Calculate mana pool
pool = board.mana_sources_from_board(
    board.lands_untapped,
    board.artifacts,
    board.creatures,
)

print(f"\nMana pool from lands:")
print(f"  Sources: {pool}")
print(f"  Total: {len(pool)}")

board.mana_pool = pool

# Test each creature for castability
print(f"\nTesting castability:")
for creature in board.hand:
    if "Creature" not in creature.type:
        continue

    print(f"\n  {creature.name}:")
    print(f"    Mana cost: {creature.mana_cost}")
    print(f"    Type: {creature.type}")

    can_cast = Mana_utils.can_pay(creature.mana_cost, board.mana_pool)
    print(f"    Can cast with current pool? {can_cast}")

    if can_cast:
        print(f"    ✓ SHOULD BE CAST!")
    else:
        print(f"    ✗ Not enough mana")

# Now simulate the actual main phase loop logic
print("\n" + "="*100)
print("SIMULATING MAIN PHASE LOOP")
print("="*100)

commander_done = True  # Assume commander already cast to simplify
iteration = 0
max_iterations = 10

while iteration < max_iterations:
    iteration += 1
    print(f"\nIteration {iteration}:")

    did_action = False

    # Step 1: Try to cast mana rocks (skip for this test)
    print(f"  Step 1: Mana rocks - none in hand")

    # Step 2: Try to cast commander (skip - already done)
    print(f"  Step 2: Commander - already cast")

    # Step 3: Try to cast ramp sorceries
    ramp_spell = next(
        (
            c
            for c in board.hand
            if "Sorcery" in c.type
            and getattr(c, "puts_land", False)
            and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
        ),
        None,
    )
    if ramp_spell:
        print(f"  Step 3: Found ramp spell: {ramp_spell.name}")
        did_action = True
    else:
        print(f"  Step 3: No ramp spells")

    # Step 4: Try to cast a creature
    print(f"  Step 4: Looking for castable creature...")
    creature = next(
        (
            c
            for c in board.hand
            if "Creature" in c.type
            and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
        ),
        None,
    )

    if creature:
        print(f"    Found: {creature.name}")
        print(f"    Mana cost: {creature.mana_cost}")
        print(f"    Can pay: {Mana_utils.can_pay(creature.mana_cost, board.mana_pool)}")

        # Check if we should hold back
        print(f"    Checking should_hold_back_creature...")
        try:
            should_hold = board.should_hold_back_creature(creature, verbose=False)
            print(f"    Hold back? {should_hold}")

            if should_hold:
                print(f"    ⚠ Creature being held back by AI!")
                did_action = False
                break
            else:
                print(f"    ✓ AI says we can cast this creature")
                did_action = True
                # In real simulation, would call board.play_card(creature)
                print(f"    ✓ CREATURE SHOULD BE CAST HERE!")
                break
        except Exception as e:
            print(f"    ERROR in should_hold_back_creature: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"    No castable creatures found")

    if not did_action:
        print(f"\n  No action taken, breaking loop")
        break

print("\n" + "="*100)
print("ANALYSIS COMPLETE")
print("="*100)
