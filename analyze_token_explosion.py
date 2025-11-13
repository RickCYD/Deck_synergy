#!/usr/bin/env python3
"""
Comprehensive analysis of Token Explosion deck to identify and fix all issues.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

from deck_loader import load_deck_from_archidekt
from run_simulation import run_simulations
from simulate_game import simulate_game
import random

DECK_ID = 16465488

def main():
    print("=" * 100)
    print("TOKEN EXPLOSION DECK - COMPREHENSIVE ANALYSIS")
    print("=" * 100)

    # Step 1: Load deck from Archidekt
    print("\n[STEP 1] Loading deck from Archidekt...")
    try:
        cards, commander, card_names = load_deck_from_archidekt(DECK_ID)
        print(f"✓ Deck loaded successfully")
        print(f"  - Commander: {commander.name if commander else 'None'}")
        print(f"  - Total cards in deck: {len(cards)}")
        print(f"  - Unique card names: {len(set(card_names))}")
    except Exception as e:
        print(f"✗ Failed to load deck: {e}")
        return

    # Step 2: Validate card count
    print("\n[STEP 2] Validating deck composition...")
    if len(cards) != 99:
        print(f"⚠ WARNING: Deck has {len(cards)} cards, expected 99 (excluding commander)")
    else:
        print(f"✓ Deck has correct number of cards (99)")

    # Count card types
    card_types = {}
    for card in cards:
        card_type = card.type.split(' — ')[0] if ' — ' in card.type else card.type
        card_types[card_type] = card_types.get(card_type, 0) + 1

    print("\n  Card type distribution:")
    for card_type, count in sorted(card_types.items(), key=lambda x: -x[1]):
        print(f"    {card_type}: {count}")

    # Step 3: Identify token generators and anthem effects
    print("\n[STEP 3] Identifying key token strategy cards...")
    token_generators = []
    anthem_effects = []
    sacrifice_outlets = []
    death_triggers = []

    for card in cards:
        oracle = card.oracle_text.lower()

        # Token generators
        if 'create' in oracle and 'token' in oracle:
            token_generators.append(card.name)

        # Anthem effects (buff creatures)
        if ('creature' in oracle and ('get +' in oracle or 'gets +' in oracle)) or \
           ('creatures you control get' in oracle):
            anthem_effects.append(card.name)

        # Sacrifice outlets
        if card.sacrifice_outlet:
            sacrifice_outlets.append(card.name)
        elif 'sacrifice' in oracle and ':' in oracle:
            sacrifice_outlets.append(card.name)

        # Death triggers
        if card.death_trigger_value and card.death_trigger_value > 0:
            death_triggers.append(card.name)
        elif 'dies' in oracle or 'whenever a creature you control dies' in oracle:
            death_triggers.append(card.name)

    print(f"\n  Token Generators ({len(token_generators)}):")
    for name in token_generators[:10]:
        print(f"    - {name}")
    if len(token_generators) > 10:
        print(f"    ... and {len(token_generators) - 10} more")

    print(f"\n  Anthem Effects ({len(anthem_effects)}):")
    for name in anthem_effects[:10]:
        print(f"    - {name}")
    if len(anthem_effects) > 10:
        print(f"    ... and {len(anthem_effects) - 10} more")

    print(f"\n  Sacrifice Outlets ({len(sacrifice_outlets)}):")
    for name in sacrifice_outlets:
        print(f"    - {name}")

    print(f"\n  Death Triggers ({len(death_triggers)}):")
    for name in death_triggers:
        print(f"    - {name}")

    # Step 4: Run single game simulation with detailed logging
    print("\n[STEP 4] Running single detailed game simulation...")
    random.seed(42)
    metrics = simulate_game(cards, commander, max_turns=10, verbose=True)

    print("\n  Single Game Results:")
    print(f"    Total combat damage: {sum(metrics['combat_damage'][1:11])}")
    print(f"    Total drain damage: {sum(metrics.get('drain_damage', [0]*11)[1:11])}")
    print(f"    Total tokens created: {sum(metrics.get('tokens_created', [0]*11)[1:11])}")
    print(f"    Total creatures sacrificed: {sum(metrics.get('creatures_sacrificed', [0]*11)[1:11])}")
    print(f"    Peak board power: {max(metrics.get('total_power', [0]))}")
    print(f"    Total cards played: {sum(metrics['cards_played'][1:11])}")

    # Step 5: Run multiple simulations
    print("\n[STEP 5] Running 100 game simulation...")
    summary_df, commander_dist, creature_power, interaction_summary, stats = run_simulations(
        cards, commander,
        num_games=100,
        max_turns=10,
        verbose=False,
        log_dir=None,
        num_workers=1,
        calculate_statistics=True
    )

    print("\n  Average Results (over 100 games):")
    print(f"    Avg total damage by turn 10: {summary_df['Avg Total Damage'].iloc[-1]:.2f}")
    print(f"    Avg combat damage by turn 10: {summary_df['Avg Combat Damage'].iloc[-1]:.2f}")
    print(f"    Avg drain damage by turn 10: {summary_df['Avg Drain Damage'].iloc[-1]:.2f}")
    print(f"    Avg tokens created by turn 10: {summary_df['Avg Tokens Created'].iloc[-1]:.2f}")
    print(f"    Avg board power by turn 10: {summary_df['Avg Total Power'].iloc[-1]:.2f}")
    print(f"    Avg cards played by turn 10: {summary_df['Avg Cards Played'].iloc[-1]:.2f}")

    # Step 6: Calculate deck effectiveness score
    print("\n[STEP 6] Calculating deck effectiveness...")
    avg_total_damage_t10 = summary_df['Avg Total Damage'].iloc[-1]
    avg_board_power_t10 = summary_df['Avg Total Power'].iloc[-1]
    avg_cards_played_t10 = summary_df['Avg Cards Played'].iloc[-1]

    # Effectiveness formula (normalized to 0-100 scale)
    # Token decks should have high board power and reasonable damage
    effectiveness = (
        (avg_total_damage_t10 / 120) * 40 +  # 40% weight on damage
        (avg_board_power_t10 / 80) * 40 +     # 40% weight on board power
        (avg_cards_played_t10 / 30) * 20      # 20% weight on cards played
    ) * 100

    effectiveness = min(100, max(0, effectiveness))

    print(f"\n  DECK EFFECTIVENESS SCORE: {effectiveness:.1f}/100")

    # Diagnostic breakdown
    print("\n  Score Breakdown:")
    damage_score = (avg_total_damage_t10 / 120) * 40 * 100
    power_score = (avg_board_power_t10 / 80) * 40 * 100
    cards_score = (avg_cards_played_t10 / 30) * 20 * 100
    print(f"    Damage component: {damage_score:.1f}/40 (damage: {avg_total_damage_t10:.1f}/120 expected)")
    print(f"    Board power component: {power_score:.1f}/40 (power: {avg_board_power_t10:.1f}/80 expected)")
    print(f"    Cards played component: {cards_score:.1f}/20 (cards: {avg_cards_played_t10:.1f}/30 expected)")

    # Step 7: Identify specific issues
    print("\n[STEP 7] Diagnostic Analysis - Identifying Issues...")

    issues = []

    if avg_total_damage_t10 < 60:
        issues.append(f"LOW DAMAGE: Only {avg_total_damage_t10:.1f} average damage by turn 10 (expected ~120)")
        issues.append("  Possible causes: Token triggers not firing, combat damage not calculated correctly")

    if avg_board_power_t10 < 40:
        issues.append(f"LOW BOARD POWER: Only {avg_board_power_t10:.1f} average power (expected ~80 for token deck)")
        issues.append("  Possible causes: Anthem effects not applied, tokens not being created")

    if summary_df['Avg Tokens Created'].iloc[-1] < 5:
        issues.append(f"LOW TOKEN GENERATION: Only {summary_df['Avg Tokens Created'].iloc[-1]:.1f} tokens by turn 10")
        issues.append(f"  Found {len(token_generators)} token generators in deck - they may not be triggering")

    if len(anthem_effects) > 5 and avg_board_power_t10 < 50:
        issues.append(f"ANTHEM EFFECTS NOT APPLYING: {len(anthem_effects)} anthems found but low board power")

    if issues:
        print("\n  ⚠ ISSUES DETECTED:")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
    else:
        print("\n  ✓ No major issues detected")

    # Step 8: Detailed card audit
    print("\n[STEP 8] Auditing specific high-impact cards...")

    high_impact_cards = [
        "Anointed Procession",
        "Doubling Season",
        "Parallel Lives",
        "Mondrak, Glory Dominus",
        "Second Harvest",
        "Avenger of Zendikar",
        "Craterhoof Behemoth",
        "Finale of Devastation",
        "Rhys the Redeemed",
        "Jetmir, Nexus of Revels",
    ]

    found_cards = [c for c in cards if c.name in high_impact_cards]
    missing_cards = [name for name in high_impact_cards if name not in [c.name for c in cards]]

    print(f"\n  High-impact cards in deck:")
    for card in found_cards:
        print(f"    ✓ {card.name}")
        print(f"      Oracle: {card.oracle_text[:100]}...")
        print(f"      Type: {card.type}")
        print(f"      Triggered abilities: {len(card.triggered_abilities)}")
        print(f"      Activated abilities: {len(card.activated_abilities)}")

    if missing_cards:
        print(f"\n  High-impact cards NOT in deck:")
        for name in missing_cards:
            print(f"    - {name}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    return {
        'effectiveness': effectiveness,
        'avg_damage': avg_total_damage_t10,
        'avg_power': avg_board_power_t10,
        'issues': issues,
        'token_generators': len(token_generators),
        'anthem_effects': len(anthem_effects),
    }

if __name__ == "__main__":
    result = main()
