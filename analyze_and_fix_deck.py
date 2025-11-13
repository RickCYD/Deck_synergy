#!/usr/bin/env python3
"""
Comprehensive deck analysis and fix tool.
This will load, simulate, diagnose, and fix all issues with the provided deck.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

import random
import time
from deck_loader import load_deck_from_scryfall, parse_decklist_file
from run_simulation import run_simulations
from simulate_game import simulate_game

def analyze_deck(decklist_file):
    """Main analysis pipeline."""

    print("=" * 100)
    print("COMPREHENSIVE DECK ANALYSIS AND FIX PIPELINE")
    print("=" * 100)

    # PHASE 1: LOAD
    print("\n" + "="*100)
    print("PHASE 1: LOADING DECK")
    print("="*100)

    print("\n[1.1] Parsing decklist...")
    try:
        card_names, commander_name = parse_decklist_file(decklist_file)
        print(f"✓ Parsed {len(card_names)} cards + commander: {commander_name}")
    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        return None

    print("\n[1.2] Fetching card data from Scryfall...")
    print("     (This may take 30-60 seconds for 100 cards...)")
    try:
        cards, commander, names = load_deck_from_scryfall(card_names, commander_name)
        print(f"✓ Loaded {len(cards)} cards successfully")
    except Exception as e:
        print(f"✗ Failed to load cards: {e}")
        print("\nNote: If Scryfall is blocked, you'll need to provide a CSV with card data")
        return None

    print("\n[1.3] Validating deck composition...")
    if len(cards) != 99:
        print(f"⚠ WARNING: Deck has {len(cards)} cards (expected 99)")
    else:
        print(f"✓ Deck has correct card count")

    # Card type breakdown
    card_types = {}
    for card in cards:
        t = card.type.split(' — ')[0]
        card_types[t] = card_types.get(t, 0) + 1

    print("\n  Card types:")
    for t, count in sorted(card_types.items(), key=lambda x: -x[1]):
        print(f"    {t}: {count}")

    # PHASE 2: STRATEGY ANALYSIS
    print("\n" + "="*100)
    print("PHASE 2: STRATEGY ANALYSIS")
    print("="*100)

    token_generators = []
    token_doublers = []
    anthems = []
    finishers = []

    for card in cards:
        oracle = card.oracle_text.lower()
        name = card.name.lower()

        # Token generators
        if 'create' in oracle and 'token' in oracle:
            token_generators.append(card)

        # Doublers
        if 'twice that many' in oracle or \
           any(x in name for x in ['anointed procession', 'doubling season', 'parallel lives',
                                    'primal vigor', 'mondrak', 'adrix']):
            token_doublers.append(card)

        # Anthems
        if ('creatures you control get' in oracle or \
            'creatures you control have' in oracle) and \
           '+' in oracle:
            anthems.append(card)

        # Finishers
        if any(x in name for x in ['craterhoof', 'triumph', 'overwhelming', 'beastmaster',
                                     'coat of arms', 'finale of devastation']):
            finishers.append(card)

    print(f"\n[2.1] Token Strategy Cards:")
    print(f"  Token Generators: {len(token_generators)}")
    for c in token_generators[:10]:
        print(f"    • {c.name}")
    if len(token_generators) > 10:
        print(f"    ... and {len(token_generators)-10} more")

    print(f"\n  Token Doublers: {len(token_doublers)}")
    for c in token_doublers:
        print(f"    • {c.name}")

    print(f"\n  Anthem Effects: {len(anthems)}")
    for c in anthems[:8]:
        print(f"    • {c.name}")
    if len(anthems) > 8:
        print(f"    ... and {len(anthems)-8} more")

    print(f"\n  Finishers: {len(finishers)}")
    for c in finishers:
        print(f"    • {c.name}")

    # PHASE 3: SIMULATION
    print("\n" + "="*100)
    print("PHASE 3: INITIAL SIMULATION")
    print("="*100)

    print("\n[3.1] Running single detailed game...")
    random.seed(42)
    single_metrics = simulate_game(cards, commander, max_turns=10, verbose=False)

    single_combat = sum(single_metrics['combat_damage'][1:11])
    single_drain = sum(single_metrics.get('drain_damage', [0]*11)[1:11])
    single_tokens = sum(single_metrics.get('tokens_created', [0]*11)[1:11])
    single_power = max(single_metrics.get('total_power', [0]))

    print(f"  Single game results:")
    print(f"    Combat damage: {single_combat}")
    print(f"    Drain damage: {single_drain}")
    print(f"    Total damage: {single_combat + single_drain}")
    print(f"    Tokens created: {single_tokens}")
    print(f"    Peak power: {single_power}")

    print("\n[3.2] Running 100-game simulation...")
    print("     (This will take 2-3 minutes...)")
    start_time = time.time()

    summary_df, commander_dist, creature_power, interaction_summary, stats = run_simulations(
        cards, commander,
        num_games=100,
        max_turns=10,
        verbose=False,
        log_dir=None,
        num_workers=1,
        calculate_statistics=True
    )

    elapsed = time.time() - start_time
    print(f"  Completed in {elapsed:.1f} seconds")

    # Extract cumulative metrics
    avg_combat = sum(summary_df['Avg Combat Damage'])
    avg_drain = sum(summary_df['Avg Drain Damage'])
    avg_total_dmg = sum(summary_df['Avg Total Damage'])
    avg_tokens = sum(summary_df['Avg Tokens Created'])
    avg_power_t10 = summary_df['Avg Total Power'].iloc[-1]
    avg_played = sum(summary_df['Avg Cards Played'])

    print(f"\n  Average results (100 games, cumulative over 10 turns):")
    print(f"    Total combat damage: {avg_combat:.2f}")
    print(f"    Total drain damage: {avg_drain:.2f}")
    print(f"    Total damage: {avg_total_dmg:.2f}")
    print(f"    Total tokens created: {avg_tokens:.2f}")
    print(f"    Peak board power (T10): {avg_power_t10:.2f}")
    print(f"    Total cards played: {avg_played:.2f}")

    # PHASE 4: DIAGNOSTIC ANALYSIS
    print("\n" + "="*100)
    print("PHASE 4: DIAGNOSTIC ANALYSIS")
    print("="*100)

    issues = []

    print("\n[4.1] Damage Analysis...")
    expected_damage = 100 if len(token_generators) > 10 else 80
    if avg_total_dmg < expected_damage * 0.6:
        issues.append({
            'category': 'DAMAGE',
            'severity': 'HIGH',
            'description': f'Low total damage: {avg_total_dmg:.1f} (expected ~{expected_damage})',
            'likely_causes': [
                'Combat damage not calculated correctly',
                'Creatures not attacking',
                'Power buffs not applying',
            ]
        })
        print(f"  ⚠ LOW DAMAGE: {avg_total_dmg:.1f} / {expected_damage} expected")
    else:
        print(f"  ✓ Damage output adequate: {avg_total_dmg:.1f}")

    print("\n[4.2] Token Generation Analysis...")
    expected_tokens = len(token_generators) * 3  # Rough estimate
    if avg_tokens < expected_tokens * 0.3:
        issues.append({
            'category': 'TOKENS',
            'severity': 'CRITICAL',
            'description': f'Very low token generation: {avg_tokens:.1f} (expected ~{expected_tokens})',
            'likely_causes': [
                'ETB triggers not firing',
                'Token creation not implemented',
                'Triggered abilities not parsed',
            ]
        })
        print(f"  ⚠ CRITICAL: Only {avg_tokens:.1f} tokens created ({len(token_generators)} generators found)")
    else:
        print(f"  ✓ Token generation working: {avg_tokens:.1f}")

    print("\n[4.3] Token Doubler Analysis...")
    if len(token_doublers) > 0 and avg_tokens > 0:
        doubling_effectiveness = avg_tokens / (len(token_generators) * 2)
        if doubling_effectiveness < 1.3:  # Should be closer to 2x
            issues.append({
                'category': 'DOUBLERS',
                'severity': 'HIGH',
                'description': f'Doublers not effective ({len(token_doublers)} doublers, effectiveness: {doubling_effectiveness:.1f}x)',
                'likely_causes': [
                    'Replacement effects not implemented',
                    'Doubling Season / Anointed Procession not working',
                    'Token creation bypassing doubler logic',
                ]
            })
            print(f"  ⚠ Doublers ineffective: {len(token_doublers)} doublers but only {doubling_effectiveness:.1f}x effect")

    print("\n[4.4] Anthem Effect Analysis...")
    if len(anthems) > 5:
        expected_power_per_creature = 3 + (len(anthems) * 0.5)
        creatures_count = len([c for c in cards if 'Creature' in c.type])
        if avg_power_t10 < creatures_count * expected_power_per_creature * 0.5:
            issues.append({
                'category': 'ANTHEMS',
                'severity': 'HIGH',
                'description': f'Anthem effects not applying ({len(anthems)} anthems found)',
                'likely_causes': [
                    'Global pump effects not implemented',
                    'Static abilities not tracked',
                    'Power calculations not including buffs',
                ]
            })
            print(f"  ⚠ Anthems not working: {len(anthems)} anthems but low board power")

    print("\n[4.5] Card Velocity Analysis...")
    if avg_played < 20:
        issues.append({
            'category': 'VELOCITY',
            'severity': 'MEDIUM',
            'description': f'Low card velocity: {avg_played:.1f} (expected 25-30)',
            'likely_causes': [
                'Mana constraints',
                'Draw effects not working',
                'High average CMC',
            ]
        })
        print(f"  ⚠ Low velocity: {avg_played:.1f} cards/game")

    # PHASE 5: EFFECTIVENESS SCORE
    print("\n" + "="*100)
    print("PHASE 5: DECK EFFECTIVENESS")
    print("="*100)

    # Calculate effectiveness (0-100 scale)
    damage_score = min(100, (avg_total_dmg / 120) * 100)
    power_score = min(100, (avg_power_t10 / 80) * 100)
    token_score = min(100, (avg_tokens / 20) * 100) if len(token_generators) > 5 else 50
    velocity_score = min(100, (avg_played / 25) * 100)

    effectiveness = (
        damage_score * 0.35 +
        power_score * 0.30 +
        token_score * 0.25 +
        velocity_score * 0.10
    )

    print(f"\n  DECK EFFECTIVENESS: {effectiveness:.1f}/100")
    print(f"\n  Component Scores:")
    print(f"    Damage (35%):   {damage_score:.1f}/100")
    print(f"    Power (30%):    {power_score:.1f}/100")
    print(f"    Tokens (25%):   {token_score:.1f}/100")
    print(f"    Velocity (10%): {velocity_score:.1f}/100")

    # PHASE 6: ISSUES SUMMARY
    print("\n" + "="*100)
    print("PHASE 6: ISSUES FOUND")
    print("="*100)

    if issues:
        print(f"\n  Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            print(f"  [{i}] {issue['severity']}: {issue['category']}")
            print(f"      {issue['description']}")
            print(f"      Likely causes:")
            for cause in issue['likely_causes']:
                print(f"        - {cause}")
            print()
    else:
        print("\n  ✓ No critical issues detected!")
        print("  Deck is performing well in simulation.")

    print("\n" + "="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)

    return {
        'cards': cards,
        'commander': commander,
        'effectiveness': effectiveness,
        'avg_damage': avg_total_dmg,
        'avg_tokens': avg_tokens,
        'avg_power': avg_power_t10,
        'issues': issues,
        'summary_df': summary_df,
        'stats': stats,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_and_fix_deck.py <decklist.txt>")
        print("\nThe decklist should be a text file with one card per line:")
        print("  Commander: Card Name")
        print("  1 Card Name")
        print("  1 Another Card")
        sys.exit(1)

    result = analyze_deck(sys.argv[1])

    if result and result['issues']:
        print("\n" + "="*100)
        print("NEXT STEPS: FIXING ISSUES")
        print("="*100)
        print("\nIssues have been identified. To fix them, I need to:")
        print("1. Examine the specific card implementations")
        print("2. Update oracle_text_parser.py for better trigger detection")
        print("3. Update simulate_game.py for proper effect application")
        print("4. Update boardstate.py for replacement effects")
        print("\nReady to proceed with fixes!")
