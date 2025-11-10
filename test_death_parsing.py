#!/usr/bin/env python3
"""Direct test of death trigger parsing functions"""

import sys
from pathlib import Path

# Add Simulation to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from oracle_text_parser import parse_death_triggers_from_oracle, parse_sacrifice_outlet_from_oracle

# Test cases with actual MTG card oracle text
test_cases = [
    {
        "name": "Zulaport Cutthroat",
        "oracle": "Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.",
        "expected_death": 1,
        "expected_sac": False
    },
    {
        "name": "Cruel Celebrant",
        "oracle": "Whenever Cruel Celebrant or another creature you control dies, each opponent loses 1 life and you gain 1 life.",
        "expected_death": 1,
        "expected_sac": False
    },
    {
        "name": "Mirkwood Bats",
        "oracle": "Whenever you create or sacrifice a token, each opponent loses 1 life.",
        "expected_death": 0,  # This is token-specific, not general death
        "expected_sac": False
    },
    {
        "name": "Bastion of Remembrance",
        "oracle": "When Bastion of Remembrance enters the battlefield, create a 1/1 white Human Soldier creature token.\nWhenever a creature you control dies, each opponent loses 1 life and you gain 1 life.",
        "expected_death": 1,
        "expected_sac": False
    },
    {
        "name": "Goblin Bombardment",
        "oracle": "Sacrifice a creature: Goblin Bombardment deals 1 damage to any target.",
        "expected_death": 0,
        "expected_sac": True
    },
    {
        "name": "Viscera Seer",
        "oracle": "Sacrifice a creature: Scry 1.",
        "expected_death": 0,
        "expected_sac": True
    },
    {
        "name": "Pitiless Plunderer",
        "oracle": "Whenever another creature you control dies, create a Treasure token.",
        "expected_death": 0,  # Creates treasure, but not a drain effect
        "expected_sac": False
    },
    {
        "name": "Impact Tremors",
        "oracle": "Whenever a creature enters the battlefield under your control, Impact Tremors deals 1 damage to each opponent.",
        "expected_death": 0,
        "expected_sac": False
    },
    {
        "name": "Nadier's Nightblade",
        "oracle": "Whenever a token you control leaves the battlefield, each opponent loses 1 life.",
        "expected_death": 1,
        "expected_sac": False
    },
]

print("Testing death trigger and sacrifice outlet parsing...")
print("=" * 70)

all_passed = True

for test in test_cases:
    name = test["name"]
    oracle = test["oracle"]
    expected_death = test["expected_death"]
    expected_sac = test["expected_sac"]

    actual_death = parse_death_triggers_from_oracle(oracle)
    actual_sac = parse_sacrifice_outlet_from_oracle(oracle)

    death_pass = actual_death == expected_death
    sac_pass = actual_sac == expected_sac

    status = "✓" if (death_pass and sac_pass) else "✗"

    print(f"\n{status} {name}")
    print(f"   Death trigger: {actual_death} (expected: {expected_death}) {'✓' if death_pass else '✗'}")
    print(f"   Sacrifice outlet: {actual_sac} (expected: {expected_sac}) {'✓' if sac_pass else '✗'}")

    if not (death_pass and sac_pass):
        all_passed = False
        print(f"   Oracle: {oracle[:80]}...")

print("\n" + "=" * 70)

if all_passed:
    print("✓ SUCCESS! All parsing tests passed!")
else:
    print("✗ FAILED! Some tests did not pass as expected")
    print("\nNote: Some failures may be expected (e.g., Mirkwood Bats is token-specific)")

# Key cards that MUST work for aristocrats
critical_cards = ["Zulaport Cutthroat", "Cruel Celebrant", "Bastion of Remembrance",
                  "Goblin Bombardment", "Viscera Seer", "Nadier's Nightblade"]

critical_passed = all(
    parse_death_triggers_from_oracle(test["oracle"]) == test["expected_death"] and
    parse_sacrifice_outlet_from_oracle(test["oracle"]) == test["expected_sac"]
    for test in test_cases if test["name"] in critical_cards
)

print("\n" + "=" * 70)
print("CRITICAL CARD TEST:")
print("-" * 70)

if critical_passed:
    print("✓ All critical aristocrats cards parsing correctly!")
    sys.exit(0)
else:
    print("✗ Critical cards not parsing correctly!")
    sys.exit(1)
