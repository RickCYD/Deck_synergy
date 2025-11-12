#!/usr/bin/env python3
"""Test script to analyze Teval deck effectiveness and identify missing mechanics."""

import sys
from pathlib import Path

# Add Simulation directory to path
sim_dir = Path(__file__).parent / "Simulation"
sys.path.insert(0, str(sim_dir))

from deck_loader import load_deck_from_scryfall_file
from run_simulation import run_simulations

# Your Teval deck list
DECK_LIST = """Commander
1 Teval, the Balanced Scale

Blink
1 Gossip's Talent

Creature
1 Siegfried, Famed Swordsman

Drain
1 Diregraf Captain
1 Ob Nixilis, the Fallen
1 Syr Konrad, the Grim

Draw
1 Disciple of Bolas
1 Frantic Search
1 Kindred Discovery
1 Kishla Skimmer
1 Priest of Forgotten Gods
1 Tatyova, Benthic Druid
1 Teval's Judgment
1 Treasure Cruise
1 Welcome the Dead

Finisher
1 Eldrazi Monument
1 Living Death
1 Wonder

Land
1 Cephalid Coliseum
1 Command Beacon
1 Command Tower
1 Contaminated Aquifer
1 Crypt of Agadeem
1 Darkwater Catacombs
1 Dreamroot Cascade
1 Drownyard Temple
1 Evolving Wilds
1 Exotic Orchard
1 Fabled Passage
1 Fetid Pools
1 Foreboding Landscape
5 Forest
1 Golgari Rot Farm
1 Haunted Mire
1 Hinterland Harbor
3 Island
1 Llanowar Wastes
1 Memorial to Folly
1 Myriad Landscape
1 Opulent Palace
1 Sunken Hollow
5 Swamp
1 Temple of Malady
1 Terramorphic Expanse
1 Woodland Cemetery

Mill
1 Aftermath Analyst
1 Cemetery Tampering
1 Dredger's Insight
1 Eccentric Farmer
1 Hedron Crab
1 Nyx Weaver
1 Shigeki, Jukai Visionary
1 Sidisi, Brood Tyrant
1 Smuggler's Surprise
1 Stitcher's Supplier

Ramp
1 Arcane Signet
1 Deathrite Shaman
1 Hedge Shredder
1 Icetill Explorer
1 Millikin
1 Molt Tender
1 Seton, Krosan Protector
1 Skull Prophet
1 Sol Ring
1 Titans' Nest
1 Wight of the Reliquary
1 Will of the Sultai

Recursion
1 Afterlife from the Loam
1 Colossal Grave-Reaver
1 Conduit of Worlds
1 Dread Return
1 Eternal Witness
1 Gravecrawler
1 Kotis, Sibsig Champion
1 Life from the Loam
1 Lost Monarch of Ifnir
1 Meren of Clan Nel Toth
1 Muldrotha, the Gravetide
1 Phyrexian Reclamation
1 The Scarab God
1 Tortured Existence

Removal
1 Amphin Mutineer
1 An Offer You Can't Refuse
1 Counterspell
1 Deadly Brew
1 Ghost Vacuum
1 Heritage Reclamation
1 Into the Flood Maw
1 Lethal Scheme
1 Necromantic Selection
1 Overwhelming Remorse
1 Tear Asunder

Stax
1 Dauthi Voidwalker
"""

def analyze_deck():
    """Analyze the deck and identify missing mechanics."""

    print("=" * 80)
    print("TEVAL DECK ANALYSIS - Identifying Missing Mechanics")
    print("=" * 80)

    # Save deck list to temporary file
    deck_file = Path("/tmp/teval_deck.txt")
    deck_file.write_text(DECK_LIST)

    # Load the deck
    print("\n[1/3] Loading deck...")
    try:
        cards, commander = load_deck_from_scryfall_file(str(deck_file), "Teval, the Balanced Scale")
        print(f"✓ Loaded {len(cards)} cards")
        print(f"✓ Commander: {commander.name if commander else 'Not found'}")
    except Exception as e:
        print(f"✗ Error loading deck: {e}")
        import traceback
        traceback.print_exc()
        return

    # Count deck composition
    print("\n[2/3] Analyzing deck composition...")

    creatures = [c for c in cards if "creature" in c.type.lower()]
    lands = [c for c in cards if "land" in c.type.lower()]
    artifacts = [c for c in cards if "artifact" in c.type.lower()]

    # Check for recursion/graveyard cards
    recursion_keywords = ["return", "reanimate", "graveyard", "died", "dies"]
    mill_keywords = ["mill", "graveyard", "self-mill"]

    recursion_cards = []
    mill_cards = []

    for card in cards:
        oracle = getattr(card, 'oracle_text', '').lower()
        name = card.name.lower()

        if any(kw in oracle or kw in name for kw in recursion_keywords):
            recursion_cards.append(card.name)

        if any(kw in oracle or kw in name for kw in mill_keywords):
            mill_cards.append(card.name)

    print(f"\nDeck composition:")
    print(f"  Creatures: {len(creatures)}")
    print(f"  Lands: {len(lands)}")
    print(f"  Artifacts: {len(artifacts)}")
    print(f"  Recursion/graveyard cards: {len(recursion_cards)}")
    print(f"  Mill cards: {len(mill_cards)}")

    # Run simulation
    print("\n[3/3] Running simulation (10 games, 10 turns)...")
    print("-" * 80)

    try:
        summary, cmd_dist, creature_power, interaction, stats = run_simulations(
            cards=cards,
            commander_card=commander,
            num_games=10,
            max_turns=10,
            verbose=False,  # Don't print every game
            log_dir=None,
            num_workers=1,
            calculate_statistics=True
        )

        # Print summary metrics
        print("\n" + "=" * 80)
        print("SIMULATION RESULTS")
        print("=" * 80)

        # Calculate key metrics
        total_damage = summary["Avg Total Damage"].sum()
        total_combat = summary["Avg Combat Damage"].sum()
        total_drain = summary["Avg Drain Damage"].sum()
        avg_damage_per_turn = total_damage / 10
        peak_power = summary["Avg Total Power"].max()

        # Commander stats
        cmd_turns = [t for t in cmd_dist.index if cmd_dist[t] > 0]
        avg_cmd_turn = sum(t * cmd_dist[t] for t in cmd_turns) / sum(cmd_dist.values()) if sum(cmd_dist.values()) > 0 else 0

        print(f"\nDeck Effectiveness:")
        print(f"  Total Damage (10 turns):  {total_damage:.1f}")
        print(f"    - Combat Damage:        {total_combat:.1f}")
        print(f"    - Drain Damage:         {total_drain:.1f}")
        print(f"  Avg Damage/Turn:          {avg_damage_per_turn:.2f}")
        print(f"  Peak Board Power:         {peak_power:.1f}")
        print(f"  Commander Avg Turn:       {avg_cmd_turn:.1f}")

        print(f"\nResource Generation:")
        print(f"  Avg Mana (Turn 5):        {summary.loc[4, 'Avg Total Mana']:.1f}")
        print(f"  Avg Cards Played:         {summary['Avg Cards Played'].sum():.1f}")
        print(f"  Avg Cards Drawn:          {summary['Avg Cards Drawn'].sum():.1f}")

        print(f"\nGraveyard Metrics:")
        print(f"  Avg Graveyard Size:       {summary['Avg Graveyard Size'].mean():.1f}")
        print(f"  Tokens Created:           {summary['Avg Tokens Created'].sum():.1f}")
        print(f"  Creatures Sacrificed:     {summary['Avg Creatures Sacrificed'].sum():.1f}")

        # Print turn-by-turn breakdown
        print("\n" + "=" * 80)
        print("TURN-BY-TURN BREAKDOWN")
        print("=" * 80)
        print(f"\n{'Turn':<6}{'Mana':<8}{'Power':<8}{'Combat':<10}{'Drain':<8}{'Total DMG':<12}")
        print("-" * 60)

        for idx, row in summary.iterrows():
            turn = row['Turn']
            mana = row['Avg Total Mana']
            power = row['Avg Total Power']
            combat = row['Avg Combat Damage']
            drain = row['Avg Drain Damage']
            total_dmg = row['Avg Total Damage']
            print(f"{turn:<6}{mana:<8.1f}{power:<8.1f}{combat:<10.1f}{drain:<8.1f}{total_dmg:<12.1f}")

    except Exception as e:
        print(f"✗ Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Identify missing mechanics
    print("\n" + "=" * 80)
    print("MISSING MECHANICS ANALYSIS")
    print("=" * 80)

    issues = []

    if total_damage < 50:
        issues.append("❌ CRITICAL: Extremely low damage output (expected 80-120 for graveyard deck)")

    if peak_power < 15:
        issues.append("❌ CRITICAL: Very low board presence (expected 20-40+ power on board)")

    if avg_cmd_turn > 6:
        issues.append("⚠️  WARNING: Commander cast too late (should be turns 3-5)")

    if summary['Avg Graveyard Size'].mean() < 10:
        issues.append("❌ CRITICAL: Graveyard not being filled (mill cards not working)")

    if summary['Avg Cards Drawn'].sum() < 15:
        issues.append("⚠️  WARNING: Low card draw (deck has many draw effects)")

    print("\nIdentified Issues:")
    for issue in issues:
        print(f"  {issue}")

    print("\nLikely Missing Mechanics:")
    print("  1. ❌ RECURSION: Muldrotha, Meren, Living Death not triggering properly")
    print("  2. ❌ MILL: Self-mill cards not filling graveyard adequately")
    print("  3. ❌ REANIMATION: Probabilistic reanimation (5-15% chance) too low")
    print("  4. ❌ CAST FROM GRAVEYARD: Muldrotha's ability not implemented")
    print("  5. ❌ BEGINNING OF END STEP: Meren triggers not working")
    print("  6. ❌ MASS REANIMATION: Living Death should return ALL creatures")
    print("  7. ❌ GRAVEYARD AS RESOURCE: Cards like Gravecrawler not recursing")
    print("  8. ⚠️  DRAIN TRIGGERS: Syr Konrad not triggering on mill/recursion")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
The simulation is severely undervaluing graveyard/recursion decks:

1. Reanimation is PROBABILISTIC (5-15% chance per turn)
   → Should be GUARANTEED when you have reanimation spells

2. Living Death should return ALL creatures at once
   → Currently only returns 1 creature probabilistically

3. Muldrotha should let you cast from graveyard EACH TURN
   → Not implemented

4. Meren should reanimate at end of turn EVERY TURN
   → Not implemented

5. Mill effects need to be much more aggressive
   → Hedron Crab, Stitcher's Supplier should mill 3-9 cards

6. Gravecrawler should be infinitely recursive
   → Not implemented

7. Syr Konrad should trigger on EVERY mill/recursion event
   → Not tracking these triggers

For a graveyard deck, expected metrics should be:
  - Total Damage: 80-150 (including Syr Konrad triggers)
  - Peak Power: 25-50 (from reanimated creatures)
  - Graveyard Size: 20-40 cards by turn 10
  - Commander: Turn 4-6 (with ramp)
""")

if __name__ == "__main__":
    analyze_deck()
