#!/usr/bin/env python3
"""
Direct simulation test using deck_loader (bypasses app API layer)
"""

import sys
from pathlib import Path

# Add Simulation to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

# Critical aristocrats cards to test
TEST_CARDS = [
    # Death triggers
    "Zulaport Cutthroat",
    "Cruel Celebrant",
    "Bastion of Remembrance",
    "Nadier's Nightblade",
    # Sacrifice outlets
    "Goblin Bombardment",
    "Viscera Seer",
    # Token generators
    "Anim Pakal, Thousandth Moon",
    "Delina, Wild Mage",
    # ETB drain
    "Impact Tremors",
    "Warleader's Call",
    # Support
    "Sol Ring",
    "Arcane Signet",
    "Command Tower",
    "Pitiless Plunderer",
    "Teysa Karlov",
    # Basics
    "Plains", "Plains", "Plains",
    "Swamp", "Swamp", "Swamp",
    "Mountain", "Mountain", "Mountain",
]

COMMANDER = "Queen Marchesa"

print("="*80)
print("DIRECT SIMULATION TEST - ARISTOCRATS MECHANICS")
print("="*80)

try:
    from deck_loader import load_deck_from_scryfall
    from run_simulation import run_simulations

    print("\n✓ Successfully imported Simulation modules")

    # Load deck
    print(f"\nLoading {len(TEST_CARDS)} test cards from Scryfall...")
    print("(This uses Scryfall bulk API and may take a moment...)")

    cards, commander, names = load_deck_from_scryfall(TEST_CARDS, COMMANDER)

    print(f"✓ Loaded {len(cards)} cards + commander ({commander.name})")

    # Verify aristocrats cards have death triggers set
    print("\n" + "="*80)
    print("CARD ATTRIBUTE VERIFICATION")
    print("="*80)

    death_trigger_cards = []
    sac_outlet_cards = []

    for card in cards + [commander]:
        death_val = getattr(card, 'death_trigger_value', 0)
        sac_outlet = getattr(card, 'sacrifice_outlet', False)

        if death_val > 0:
            death_trigger_cards.append((card.name, death_val))
            print(f"✓ {card.name}")
            print(f"    death_trigger_value = {death_val}")

        if sac_outlet:
            sac_outlet_cards.append(card.name)
            print(f"✓ {card.name}")
            print(f"    sacrifice_outlet = True")

    print("\n" + "="*80)
    print(f"Summary: {len(death_trigger_cards)} death trigger cards, {len(sac_outlet_cards)} sacrifice outlets")

    if len(death_trigger_cards) < 4:
        print("✗ ERROR: Expected at least 4 death trigger cards!")
        print("  Death triggers found:", [c[0] for c in death_trigger_cards])
        sys.exit(1)

    if len(sac_outlet_cards) < 2:
        print("✗ ERROR: Expected at least 2 sacrifice outlets!")
        print("  Sacrifice outlets found:", sac_outlet_cards)
        sys.exit(1)

    print("✓ Aristocrats cards detected correctly!")

    # Run simulation
    print("\n" + "="*80)
    print("RUNNING SIMULATION")
    print("="*80)

    print(f"\nSimulating 100 games, 10 turns each...")

    summary_df, commander_cast_dist, avg_creature_power, interaction_summary = run_simulations(
        cards=cards,
        commander_card=commander,
        num_games=100,
        max_turns=10,
        verbose=False,
        num_workers=1
    )

    # Extract results
    print("\n✓ Simulation complete!")

    # Get turn-by-turn data
    total_damage = [0] + summary_df['Avg Total Damage'].tolist()
    combat_damage = [0] + summary_df['Avg Combat Damage'].tolist()
    drain_damage = [0] + summary_df['Avg Drain Damage'].tolist()
    tokens_created = [0] + summary_df['Avg Tokens Created'].tolist()

    # Calculate totals
    total_damage_10 = sum(total_damage[:11])
    combat_damage_10 = sum(combat_damage[:11])
    drain_damage_10 = sum(drain_damage[:11])
    tokens_created_10 = sum(tokens_created[:11])

    # Display results
    print("\n" + "="*80)
    print("SIMULATION RESULTS")
    print("="*80)

    print(f"\nTotal Damage (10 turns):     {total_damage_10:.1f}")
    print(f"  ├─ Combat Damage:           {combat_damage_10:.1f}")
    print(f"  └─ Drain Damage:            {drain_damage_10:.1f}")
    print(f"\nAvg Damage/Turn:             {total_damage_10/10:.2f}")
    print(f"Peak Board Power:            {summary_df['Avg Total Power'].max():.1f}")
    print(f"Total Tokens Created:        {tokens_created_10:.1f}")

    # Turn-by-turn breakdown
    print(f"\nTurn-by-Turn Breakdown:")
    print(f"  Turn | Combat | Drain  | Total  | Tokens")
    print(f"  -----|--------|--------|--------|-------")
    for turn in range(1, 11):
        print(f"   {turn:2d}  |  {combat_damage[turn]:5.1f} |  {drain_damage[turn]:5.1f} |  {total_damage[turn]:5.1f} |  {tokens_created[turn]:5.1f}")

    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)

    if drain_damage_10 > 10:
        print(f"✓ SUCCESS! Death triggers are firing!")
        print(f"  Drain damage: {drain_damage_10:.1f}")
        print(f"  This deck has limited token generation, so drain damage")
        print(f"  may be lower than a full aristocrats deck (expect 50-150)")
    else:
        print(f"✗ FAILED! Death triggers not working")
        print(f"  Drain damage: {drain_damage_10:.1f} (expected > 10)")
        sys.exit(1)

    if total_damage_10 > 20:
        print(f"✓ Total damage looks reasonable: {total_damage_10:.1f}")
    else:
        print(f"⚠ Total damage seems low: {total_damage_10:.1f}")

    print("\n" + "="*80)
    print("TEST PASSED!")
    print("="*80)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
