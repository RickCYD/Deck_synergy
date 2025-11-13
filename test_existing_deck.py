#!/usr/bin/env python3
"""
Test the simulation system with an existing deck CSV to identify issues.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

from deck_loader import load_deck_from_csv
from run_simulation import run_simulations
from simulate_game import simulate_game
import random

def main():
    print("=" * 100)
    print("TESTING SIMULATION SYSTEM WITH EXISTING DECK")
    print("=" * 100)

    # Load deck from CSV
    print("\n[STEP 1] Loading deck from CSV...")
    try:
        cards, commander, card_names = load_deck_from_csv("Simulation/deck.csv")
        print(f"✓ Deck loaded successfully")
        print(f"  - Commander: {commander.name if commander else 'None'}")
        print(f"  - Total cards: {len(cards)}")
        print(f"  - Total card names: {len(card_names)}")
    except Exception as e:
        print(f"✗ Failed to load deck: {e}")
        import traceback
        traceback.print_exc()
        return

    # Analyze deck composition
    print("\n[STEP 2] Analyzing deck composition...")
    card_types = {}
    creatures = []
    token_related = []
    for card in cards:
        card_type = card.type.split(' — ')[0] if ' — ' in card.type else card.type
        card_types[card_type] = card_types.get(card_type, 0) + 1
        if 'Creature' in card.type:
            creatures.append(card)
        if 'token' in card.oracle_text.lower():
            token_related.append(card)

    print(f"\n  Card types:")
    for ctype, count in sorted(card_types.items(), key=lambda x: -x[1]):
        print(f"    {ctype}: {count}")

    print(f"\n  Creatures: {len(creatures)}")
    print(f"  Token-related cards: {len(token_related)}")

    if token_related:
        print(f"\n  Token-related cards found:")
        for card in token_related[:10]:
            print(f"    - {card.name}")

    # Run single detailed game
    print("\n[STEP 3] Running single detailed game...")
    random.seed(42)
    try:
        metrics = simulate_game(cards, commander, max_turns=10, verbose=False)

        print("\n  Game metrics:")
        total_combat = sum(metrics['combat_damage'][1:11])
        total_drain = sum(metrics.get('drain_damage', [0]*11)[1:11])
        total_tokens = sum(metrics.get('tokens_created', [0]*11)[1:11])
        peak_power = max(metrics.get('total_power', [0]))
        total_played = sum(metrics['cards_played'][1:11])
        total_mana = sum(metrics['total_mana'][1:11])

        print(f"    Combat damage: {total_combat}")
        print(f"    Drain damage: {total_drain}")
        print(f"    Total damage: {total_combat + total_drain}")
        print(f"    Tokens created: {total_tokens}")
        print(f"    Peak board power: {peak_power}")
        print(f"    Cards played: {total_played}")
        print(f"    Total mana generated: {total_mana}")

        # Detailed turn-by-turn
        print(f"\n  Turn-by-turn breakdown:")
        print(f"    {'Turn':<6} {'Mana':<8} {'Played':<8} {'Power':<8} {'Damage':<8}")
        print(f"    {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        for turn in range(1, 11):
            mana = metrics['total_mana'][turn]
            played = metrics['cards_played'][turn]
            power = metrics.get('total_power', [0]*11)[turn]
            damage = metrics['combat_damage'][turn]
            print(f"    {turn:<6} {mana:<8.1f} {played:<8} {power:<8.1f} {damage:<8.1f}")

    except Exception as e:
        print(f"✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run multiple games
    print("\n[STEP 4] Running 50 game simulation...")
    try:
        summary_df, commander_dist, creature_power, interaction_summary, stats = run_simulations(
            cards, commander,
            num_games=50,
            max_turns=10,
            verbose=False,
            log_dir=None,
            num_workers=1,
            calculate_statistics=True
        )

        print("\n  Average results (50 games):")
        avg_combat = summary_df['Avg Combat Damage'].iloc[-1]
        avg_drain = summary_df['Avg Drain Damage'].iloc[-1]
        avg_total_dmg = summary_df['Avg Total Damage'].iloc[-1]
        avg_tokens = summary_df['Avg Tokens Created'].iloc[-1]
        avg_power = summary_df['Avg Total Power'].iloc[-1]
        avg_played = summary_df['Avg Cards Played'].iloc[-1]
        avg_mana = summary_df['Avg Total Mana'].iloc[-1]

        print(f"    Avg combat damage by T10: {avg_combat:.2f}")
        print(f"    Avg drain damage by T10: {avg_drain:.2f}")
        print(f"    Avg total damage by T10: {avg_total_dmg:.2f}")
        print(f"    Avg tokens created: {avg_tokens:.2f}")
        print(f"    Avg board power: {avg_power:.2f}")
        print(f"    Avg cards played: {avg_played:.2f}")
        print(f"    Avg total mana: {avg_mana:.2f}")

        # Check for issues
        print("\n[STEP 5] Diagnostic analysis...")

        issues = []

        if avg_combat < 20 and len(creatures) > 10:
            issues.append(f"LOW COMBAT DAMAGE: {avg_combat:.1f} with {len(creatures)} creatures")

        if avg_power < 15 and len(creatures) > 10:
            issues.append(f"LOW BOARD POWER: {avg_power:.1f} with {len(creatures)} creatures")

        if avg_played < 15:
            issues.append(f"LOW CARD VELOCITY: {avg_played:.1f} cards played by turn 10")

        if avg_mana < 60:
            issues.append(f"LOW MANA GENERATION: {avg_mana:.1f} total mana by turn 10")

        if len(token_related) > 0 and avg_tokens < 1:
            issues.append(f"TOKEN GENERATION NOT WORKING: {len(token_related)} token cards but only {avg_tokens:.1f} tokens")

        if issues:
            print("\n  ⚠ Issues detected:")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print("\n  ✓ No major issues detected")

        # Statistical report
        if stats and 'formatted_report' in stats:
            print("\n[STEP 6] Statistical Validity:")
            print(stats['formatted_report'])

    except Exception as e:
        print(f"✗ Multi-game simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 100)
    print("TEST COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
