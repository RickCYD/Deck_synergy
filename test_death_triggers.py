#!/usr/bin/env python3
"""Test script to verify death trigger parsing for aristocrats deck"""

import sys
from pathlib import Path

# Add Simulation to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from deck_loader import load_deck_from_scryfall

# Test with a subset of the aristocrats cards
test_cards = [
    "Sol Ring",
    "Arcane Signet",
    "Impact Tremors",
    "Warleader's Call",
    "Zulaport Cutthroat",
    "Cruel Celebrant",
    "Mirkwood Bats",
    "Bastion of Remembrance",
    "Goblin Bombardment",
    "Viscera Seer",
    "Pitiless Plunderer",
]

print("Testing death trigger parsing...")
print("=" * 70)

cards, commander, names = load_deck_from_scryfall(test_cards, "Queen Marchesa")

print("\nCommander:")
print(f"  {commander.name}")
print(f"  - death_trigger_value: {commander.death_trigger_value}")
print(f"  - sacrifice_outlet: {commander.sacrifice_outlet}")

print("\nCard Analysis:")
print("-" * 70)

for card in cards:
    death_val = getattr(card, 'death_trigger_value', 0)
    sac_outlet = getattr(card, 'sacrifice_outlet', False)

    if death_val > 0 or sac_outlet:
        print(f"\n{card.name}")
        if death_val > 0:
            print(f"  ✓ Death Trigger Value: {death_val}")
        if sac_outlet:
            print(f"  ✓ Sacrifice Outlet: True")
        print(f"  Oracle: {card.oracle_text[:100]}...")

print("\n" + "=" * 70)
print("Summary:")
print("-" * 70)

death_trigger_cards = [c for c in cards if getattr(c, 'death_trigger_value', 0) > 0]
sacrifice_outlets = [c for c in cards if getattr(c, 'sacrifice_outlet', False)]

print(f"Cards with death triggers: {len(death_trigger_cards)}")
for c in death_trigger_cards:
    print(f"  - {c.name} (drain: {c.death_trigger_value})")

print(f"\nSacrifice outlets: {len(sacrifice_outlets)}")
for c in sacrifice_outlets:
    print(f"  - {c.name}")

print("\n" + "=" * 70)

if len(death_trigger_cards) >= 4 and len(sacrifice_outlets) >= 2:
    print("✓ SUCCESS! Death triggers and sacrifice outlets parsed correctly!")
else:
    print("✗ FAILED! Expected at least 4 death triggers and 2 sacrifice outlets")
    sys.exit(1)
