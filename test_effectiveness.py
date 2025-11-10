#!/usr/bin/env python3
"""
Test deck effectiveness simulation
"""

import json
import sys
from pathlib import Path

# Test with a saved deck if available
deck_files = list(Path('data/decks').glob('*.json'))

if not deck_files:
    print("No deck files found in data/decks/")
    sys.exit(1)

# Use the most recent deck file
deck_file = sorted(deck_files, key=lambda x: x.stat().st_mtime)[-1]
print(f"Testing with deck file: {deck_file.name}")

# Load deck data
with open(deck_file, 'r') as f:
    deck_data = json.load(f)

# Extract simulation results
simulation_results = deck_data.get('simulation_results', {})
summary = simulation_results.get('summary', {})

print("\n" + "="*60)
print("DECK EFFECTIVENESS METRICS")
print("="*60)

if 'error' in summary:
    print(f"❌ Simulation Error: {summary['error']}")
    sys.exit(1)

# Print main metrics
print(f"\nTotal Damage (10 turns):     {summary.get('total_damage_10_turns', 0):.1f}")
print(f"  - Combat Damage:           {summary.get('combat_damage_10_turns', 0):.1f}")
print(f"  - Drain Damage (triggers): {summary.get('drain_damage_10_turns', 0):.1f}")
print(f"\nAverage Damage per Turn:     {summary.get('avg_damage_per_turn', 0):.2f}")
print(f"Peak Board Power:            {summary.get('peak_power', 0):.1f}")
print(f"Commander Avg Cast Turn:     {summary.get('commander_avg_cast_turn', 'N/A')}")
print(f"\nTotal Tokens Created:        {summary.get('total_tokens_created', 0):.1f}")
print(f"Games Simulated:             {summary.get('num_games_simulated', 0)}")

# Check if metrics look reasonable
print("\n" + "="*60)
print("VALIDATION CHECKS")
print("="*60)

issues = []

total_dmg = summary.get('total_damage_10_turns', 0)
peak_power = summary.get('peak_power', 0)
commander_turn = summary.get('commander_avg_cast_turn')

# Check for suspiciously low values
if total_dmg < 10:
    issues.append(f"⚠️  Total damage is very low ({total_dmg:.1f}) - expected > 10 for most decks")

if peak_power < 5:
    issues.append(f"⚠️  Peak power is very low ({peak_power:.1f}) - expected > 5 for most decks")

if commander_turn and commander_turn > 7:
    issues.append(f"⚠️  Commander cast turn is late ({commander_turn:.1f}) - might indicate mana issues")

# Check for aristocrats deck specifically
deck_name = deck_data.get('name', '')
if 'token' in deck_name.lower() or 'aristocrat' in deck_name.lower():
    tokens = summary.get('total_tokens_created', 0)
    drain = summary.get('drain_damage_10_turns', 0)

    if tokens < 10:
        issues.append(f"⚠️  Token deck created few tokens ({tokens:.1f}) - expected > 10")

    if drain == 0:
        issues.append(f"⚠️  Aristocrats deck dealt no drain damage - death triggers may not be working")

if issues:
    print("\nFound potential issues:")
    for issue in issues:
        print(issue)
else:
    print("\n✓ All metrics look reasonable!")

# Print detailed damage breakdown
print("\n" + "="*60)
print("TURN-BY-TURN BREAKDOWN")
print("="*60)

total_damage_list = simulation_results.get('total_damage', [])
combat_damage_list = simulation_results.get('combat_damage', [])
drain_damage_list = simulation_results.get('drain_damage', [])
total_power_list = simulation_results.get('total_power', [])

print(f"\n{'Turn':<6} {'Combat':<8} {'Drain':<8} {'Total':<8} {'Power':<8}")
print("-" * 45)

for turn in range(1, min(11, len(total_damage_list))):
    combat = combat_damage_list[turn] if turn < len(combat_damage_list) else 0
    drain = drain_damage_list[turn] if turn < len(drain_damage_list) else 0
    total = total_damage_list[turn] if turn < len(total_damage_list) else 0
    power = total_power_list[turn] if turn < len(total_power_list) else 0

    print(f"{turn:<6} {combat:<8.2f} {drain:<8.2f} {total:<8.2f} {power:<8.2f}")

print("\n" + "="*60)
