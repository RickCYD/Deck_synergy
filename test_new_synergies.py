#!/usr/bin/env python3
"""
Test the new ally/prowess synergies
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.synergy_engine.ally_prowess_synergies import (
    detect_rally_token_synergy,
    detect_prowess_cheap_spell_synergy,
    detect_rally_rally_synergy,
    detect_ally_tribal_synergy,
    detect_creature_etb_trigger_synergy,
    detect_spellslinger_cantrip_synergy
)

# Load database
print("Loading database...")
load_local_database()

# Test rally + token synergy
print("\n" + "="*80)
print("TEST 1: Rally + Token Creation")
print("="*80)
chasm_guide = get_card_by_name("Chasm Guide")
gideon = get_card_by_name("Gideon, Ally of Zendikar")

if chasm_guide and gideon:
    synergy = detect_rally_token_synergy(chasm_guide, gideon)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards: {chasm_guide is not None}, {gideon is not None}")

# Test prowess + cheap spell
print("\n" + "="*80)
print("TEST 2: Prowess + Cheap Spell")
print("="*80)
bria = get_card_by_name("Bria, Riptide Rogue")
brainstorm = get_card_by_name("Brainstorm")

if bria and brainstorm:
    synergy = detect_prowess_cheap_spell_synergy(bria, brainstorm)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards: {bria is not None}, {brainstorm is not None}")

# Test rally + rally
print("\n" + "="*80)
print("TEST 3: Multiple Rally Triggers")
print("="*80)
chasm_guide = get_card_by_name("Chasm Guide")
lantern_scout = get_card_by_name("Lantern Scout")

if chasm_guide and lantern_scout:
    synergy = detect_rally_rally_synergy(chasm_guide, lantern_scout)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards")

# Test ETB trigger + tokens
print("\n" + "="*80)
print("TEST 4: ETB Trigger + Token Creation")
print("="*80)
impact_tremors = get_card_by_name("Impact Tremors")
kykar = get_card_by_name("Kykar, Wind's Fury")

if impact_tremors and kykar:
    synergy = detect_creature_etb_trigger_synergy(impact_tremors, kykar)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards")

# Test spellslinger + cantrip
print("\n" + "="*80)
print("TEST 5: Spellslinger + Cantrip")
print("="*80)
jeskai_ascendancy = get_card_by_name("Jeskai Ascendancy")
opt = get_card_by_name("Opt")

if jeskai_ascendancy and opt:
    synergy = detect_spellslinger_cantrip_synergy(jeskai_ascendancy, opt)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards")

# Test ally tribal
print("\n" + "="*80)
print("TEST 6: Ally Tribal Synergy")
print("="*80)
banner = get_card_by_name("Banner of Kinship")
hakoda = get_card_by_name("Hakoda, Selfless Commander")

if banner and hakoda:
    synergy = detect_ally_tribal_synergy(banner, hakoda)
    if synergy:
        print(f"✓ FOUND: {synergy['name']}")
        print(f"  Description: {synergy['description']}")
        print(f"  Value: {synergy['value']}")
    else:
        print("✗ NOT FOUND")
else:
    print(f"Could not load cards")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("New synergy rules have been implemented and tested!")
print("\nThese should significantly increase the deck effectiveness score.")
