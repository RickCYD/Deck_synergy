#!/usr/bin/env python3
"""
Load a deck from a manual decklist file and run comprehensive analysis.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

from deck_loader import load_deck_from_scryfall
from run_simulation import run_simulations
from simulate_game import simulate_game
import random

def parse_decklist_file(filepath):
    """
    Parse a decklist file.
    Format examples:
      1 Card Name
      1x Card Name
      Card Name
    """
    cards = []
    commander = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # Check if this is commander line
            if 'commander' in line.lower() or line.startswith('*'):
                # Extract card name
                name = line.replace('*', '').replace('commander:', '').replace('Commander:', '').strip()
                # Remove quantity prefix
                import re
                match = re.match(r'^\d+x?\s+(.+)$', name)
                if match:
                    name = match.group(1).strip()
                commander = name
                print(f"Found commander: {commander}")
                continue

            # Parse quantity and card name
            import re
            match = re.match(r'^(\d+)x?\s+(.+)$', line)
            if match:
                qty = int(match.group(1))
                name = match.group(2).strip()
            else:
                qty = 1
                name = line.strip()

            cards.extend([name] * qty)

    return cards, commander

def main(decklist_file):
    print("=" * 100)
    print("DECK ANALYSIS - MANUAL DECKLIST")
    print("=" * 100)

    # Step 1: Parse decklist
    print(f"\n[STEP 1] Parsing decklist from {decklist_file}...")
    try:
        card_names, commander_name = parse_decklist_file(decklist_file)
        print(f"✓ Decklist parsed successfully")
        print(f"  - Commander: {commander_name}")
        print(f"  - Total cards: {len(card_names)}")
        print(f"  - Unique cards: {len(set(card_names))}")
    except Exception as e:
        print(f"✗ Failed to parse decklist: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Load cards from Scryfall
    print("\n[STEP 2] Fetching card data from Scryfall...")
    try:
        cards, commander, names = load_deck_from_scryfall(card_names, commander_name)
        print(f"✓ Cards loaded successfully")
        print(f"  - Commander: {commander.name if commander else 'None'}")
        print(f"  - Deck cards: {len(cards)}")
    except Exception as e:
        print(f"✗ Failed to load cards: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Validate deck composition
    print("\n[STEP 3] Validating deck composition...")
    if len(cards) != 99:
        print(f"⚠ WARNING: Deck has {len(cards)} cards, expected 99 (excluding commander)")
    else:
        print(f"✓ Deck has correct number of cards (99)")

    # Count card types
    card_types = {}
    creatures = []
    for card in cards:
        card_type = card.type.split(' — ')[0] if ' — ' in card.type else card.type
        card_types[card_type] = card_types.get(card_type, 0) + 1
        if 'Creature' in card.type:
            creatures.append(card)

    print("\n  Card type distribution:")
    for card_type, count in sorted(card_types.items(), key=lambda x: -x[1]):
        print(f"    {card_type}: {count}")

    # Step 4: Identify key strategy cards
    print("\n[STEP 4] Identifying key strategy cards...")
    token_generators = []
    anthem_effects = []
    doubling_effects = []
    finishers = []

    for card in cards:
        oracle = card.oracle_text.lower()
        name_lower = card.name.lower()

        # Token generators
        if 'create' in oracle and 'token' in oracle:
            token_generators.append(card)

        # Doubling effects
        if ('token' in oracle and ('double' in oracle or 'twice that many' in oracle)) or \
           name_lower in ['anointed procession', 'doubling season', 'parallel lives', 'primal vigor',
                          'mondrak, glory dominus', 'adrix and nev, twincasters']:
            doubling_effects.append(card)

        # Anthem effects (buff all creatures)
        if (('creature' in oracle and ('get +' in oracle or 'gets +' in oracle)) or
            ('creatures you control get' in oracle)) and \
           not 'target' in oracle[:50]:  # Exclude single-target buffs
            anthem_effects.append(card)

        # Finishers
        if name_lower in ['craterhoof behemoth', 'end-raze forerunners', 'overwhelming stampede',
                         'triumph of the hordes', 'beastmaster ascension', 'finale of devastation',
                         'overwhelming splendor', 'coat of arms']:
            finishers.append(card)

    print(f"\n  Token Generators ({len(token_generators)}):")
    for card in token_generators[:15]:
        print(f"    - {card.name}")
    if len(token_generators) > 15:
        print(f"    ... and {len(token_generators) - 15} more")

    print(f"\n  Token Doublers ({len(doubling_effects)}):")
    for card in doubling_effects:
        print(f"    - {card.name}")

    print(f"\n  Anthem Effects ({len(anthem_effects)}):")
    for card in anthem_effects[:10]:
        print(f"    - {card.name}")
    if len(anthem_effects) > 10:
        print(f"    ... and {len(anthem_effects) - 10} more")

    print(f"\n  Finishers ({len(finishers)}):")
    for card in finishers:
        print(f"    - {card.name}")

    # Step 5: Run single detailed game
    print("\n[STEP 5] Running single detailed game simulation...")
    random.seed(42)
    metrics = simulate_game(cards, commander, max_turns=10, verbose=False)

    print("\n  Single Game Results:")
    total_combat = sum(metrics['combat_damage'][1:11])
    total_drain = sum(metrics.get('drain_damage', [0]*11)[1:11])
    total_tokens = sum(metrics.get('tokens_created', [0]*11)[1:11])
    peak_power = max(metrics.get('total_power', [0]))
    total_played = sum(metrics['cards_played'][1:11])

    print(f"    Total combat damage: {total_combat}")
    print(f"    Total drain damage: {total_drain}")
    print(f"    Total damage: {total_combat + total_drain}")
    print(f"    Total tokens created: {total_tokens}")
    print(f"    Peak board power: {peak_power}")
    print(f"    Total cards played: {total_played}")

    # Step 6: Run multiple simulations
    print("\n[STEP 6] Running 100 game simulation (this may take a minute)...")
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
    avg_total_dmg = summary_df['Avg Total Damage'].iloc[-1]
    avg_combat_dmg = summary_df['Avg Combat Damage'].iloc[-1]
    avg_drain_dmg = summary_df['Avg Drain Damage'].iloc[-1]
    avg_tokens = summary_df['Avg Tokens Created'].iloc[-1]
    avg_power = summary_df['Avg Total Power'].iloc[-1]
    avg_played = summary_df['Avg Cards Played'].iloc[-1]

    print(f"    Avg total damage by turn 10: {avg_total_dmg:.2f}")
    print(f"    Avg combat damage by turn 10: {avg_combat_dmg:.2f}")
    print(f"    Avg drain damage by turn 10: {avg_drain_dmg:.2f}")
    print(f"    Avg tokens created by turn 10: {avg_tokens:.2f}")
    print(f"    Avg board power by turn 10: {avg_power:.2f}")
    print(f"    Avg cards played by turn 10: {avg_played:.2f}")

    # Step 7: Calculate deck effectiveness
    print("\n[STEP 7] Calculating deck effectiveness...")

    # For a token deck, we expect:
    # - High board power (60-100)
    # - Moderate to high damage (60-120)
    # - Good token generation (10-30 tokens)
    # - Reasonable card velocity (20-30 cards played)

    # Scoring formula
    damage_score = min(100, (avg_total_dmg / 120) * 100)
    power_score = min(100, (avg_power / 80) * 100)
    token_score = min(100, (avg_tokens / 20) * 100)
    velocity_score = min(100, (avg_played / 25) * 100)

    # Weighted average
    effectiveness = (
        damage_score * 0.35 +
        power_score * 0.35 +
        token_score * 0.20 +
        velocity_score * 0.10
    )

    print(f"\n  DECK EFFECTIVENESS SCORE: {effectiveness:.1f}/100")
    print(f"\n  Score Breakdown:")
    print(f"    Damage (35%): {damage_score:.1f}/100 (avg {avg_total_dmg:.1f} / target 120)")
    print(f"    Board Power (35%): {power_score:.1f}/100 (avg {avg_power:.1f} / target 80)")
    print(f"    Token Generation (20%): {token_score:.1f}/100 (avg {avg_tokens:.1f} / target 20)")
    print(f"    Card Velocity (10%): {velocity_score:.1f}/100 (avg {avg_played:.1f} / target 25)")

    # Step 8: Diagnostic analysis
    print("\n[STEP 8] Diagnostic Analysis...")

    issues = []
    recommendations = []

    if avg_total_dmg < 60:
        issues.append(f"⚠ LOW DAMAGE: {avg_total_dmg:.1f} (expected 80-120)")
        recommendations.append("Check: Combat damage calculation, token triggers, anthem effects")

    if avg_power < 40:
        issues.append(f"⚠ LOW BOARD POWER: {avg_power:.1f} (expected 60-100)")
        recommendations.append("Check: Token creation triggers, anthem applications, power buffs")

    if avg_tokens < 5:
        issues.append(f"⚠ LOW TOKEN GENERATION: {avg_tokens:.1f} (expected 10-30)")
        recommendations.append(f"Found {len(token_generators)} token generators - check ETB/triggered abilities")

    if len(doubling_effects) > 0 and avg_tokens < 10:
        issues.append(f"⚠ TOKEN DOUBLERS NOT EFFECTIVE: {len(doubling_effects)} doublers but only {avg_tokens:.1f} tokens")
        recommendations.append("Check: Token doubling effect implementation, replacement effects")

    if len(anthem_effects) > 5 and (avg_power / max(1, len(creatures))) < 3:
        issues.append(f"⚠ ANTHEMS NOT APPLYING: {len(anthem_effects)} anthems but low per-creature power")
        recommendations.append("Check: Global pump effect implementation, static ability tracking")

    if issues:
        print("\n  Issues Detected:")
        for issue in issues:
            print(f"    {issue}")
        print("\n  Recommendations:")
        for rec in recommendations:
            print(f"    • {rec}")
    else:
        print("\n  ✓ No major issues detected - deck performing as expected!")

    # Step 9: Detailed card audit
    print("\n[STEP 9] Auditing high-impact cards...")

    print("\n  Token Doublers:")
    for card in doubling_effects:
        print(f"\n    {card.name}")
        print(f"      Type: {card.type}")
        print(f"      Oracle: {card.oracle_text[:150]}...")

    print("\n  Key Finishers:")
    for card in finishers:
        print(f"\n    {card.name}")
        print(f"      Type: {card.type}")
        print(f"      Power buff: {card.power_buff}")
        print(f"      Oracle: {card.oracle_text[:150]}...")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    return {
        'effectiveness': effectiveness,
        'avg_damage': avg_total_dmg,
        'avg_power': avg_power,
        'avg_tokens': avg_tokens,
        'issues': issues,
        'recommendations': recommendations,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python load_manual_decklist.py <decklist.txt>")
        print("\nDecklist format:")
        print("  Commander: Card Name")
        print("  1 Card Name")
        print("  2 Another Card")
        print("  etc.")
        sys.exit(1)

    result = main(sys.argv[1])
