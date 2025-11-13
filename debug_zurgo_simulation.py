#!/usr/bin/env python3
"""
Deep diagnostic analysis of why the Zurgo deck isn't working.
"""

import sys
sys.path.insert(0, 'Simulation')

from deck_loader import load_deck_from_csv
from simulate_game import simulate_game
import random

print("="*100)
print("DEEP DIAGNOSTIC - ZURGO DECK SIMULATION")
print("="*100)

# Load deck
cards, commander, card_names = load_deck_from_csv("zurgo_deck.csv")
print(f"\nLoaded {len(cards)} cards + commander: {commander.name}")

# Check which token generators have triggered abilities
print("\n[DIAGNOSTIC 1] Token Generator Cards - Triggered Abilities:")
print("-"*100)

token_gens = [c for c in cards if 'create' in c.oracle_text.lower() and 'token' in c.oracle_text.lower()]
print(f"\nFound {len(token_gens)} cards that create tokens\n")

for card in token_gens[:15]:
    print(f"\n{card.name}:")
    print(f"  Type: {card.type}")
    print(f"  Oracle: {card.oracle_text[:120]}...")
    print(f"  Triggered abilities parsed: {len(card.triggered_abilities)}")
    if card.triggered_abilities:
        for i, ability in enumerate(card.triggered_abilities):
            print(f"    [{i+1}] Trigger: {ability.trigger_condition}")
            print(f"        Effect: {ability.effect_description}")
    else:
        print(f"    ⚠ NO TRIGGERED ABILITIES PARSED!")

print("\n" + "-"*100)
print("[DIAGNOSTIC 2] Running Detailed Single Game with Verbose Output")
print("-"*100)

random.seed(42)
print("\nSimulating game with verbose=True to see what's happening...\n")

# Run with output captured
import io
import contextlib

output_buffer = io.StringIO()
with contextlib.redirect_stdout(output_buffer):
    metrics = simulate_game(cards, commander, max_turns=5, verbose=True)

output = output_buffer.getvalue()

# Analyze the output
lines = output.split('\n')

print(f"Total output lines: {len(lines)}")
print(f"\nSearching for key events...")

# Check for creature casts
creature_casts = [l for l in lines if 'Playing' in l and 'Creature' in l]
print(f"\n  Creatures cast: {len(creature_casts)}")
if creature_casts:
    for line in creature_casts[:5]:
        print(f"    {line.strip()}")

# Check for attacks
attacks = [l for l in lines if 'attacking' in l.lower() or 'attack' in l.lower()]
print(f"\n  Attack events: {len(attacks)}")
if attacks:
    for line in attacks[:5]:
        print(f"    {line.strip()}")

# Check for triggers
triggers = [l for l in lines if 'trigger' in l.lower() or 'ability' in l.lower()]
print(f"\n  Trigger events: {len(triggers)}")
if triggers:
    for line in triggers[:5]:
        print(f"    {line.strip()}")

# Check for token creation
token_creates = [l for l in lines if 'token' in l.lower() and 'creat' in l.lower()]
print(f"\n  Token creation events: {len(token_creates)}")
if token_creates:
    for line in token_creates[:5]:
        print(f"    {line.strip()}")
else:
    print(f"    ⚠ NO TOKEN CREATION DETECTED!")

# Check metrics
print(f"\n\n[DIAGNOSTIC 3] Game Metrics:")
print("-"*100)
print(f"\n  By turn:")
print(f"  {'Turn':<6} {'Mana':<8} {'Cast':<8} {'Board':<8} {'Power':<8} {'Damage':<8} {'Tokens':<8}")
print(f"  {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

for turn in range(1, 6):
    mana = metrics['total_mana'][turn]
    cast = metrics['cards_played'][turn]
    board_creatures = len([p for p in metrics.get('board_state', {}).get(turn, {}).get('creatures', [])])
    power = metrics.get('total_power', [0]*11)[turn]
    damage = metrics['combat_damage'][turn]
    tokens = metrics.get('tokens_created', [0]*11)[turn]
    print(f"  {turn:<6} {mana:<8.1f} {cast:<8} {board_creatures:<8} {power:<8.1f} {damage:<8.1f} {tokens:<8.1f}")

# Dump first 100 lines of verbose output
print(f"\n\n[DIAGNOSTIC 4] First 100 Lines of Verbose Simulation Output:")
print("-"*100)
for i, line in enumerate(lines[:100]):
    print(line)

print("\n" + "="*100)
print("DIAGNOSTIC COMPLETE")
print("="*100)
