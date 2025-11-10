#!/usr/bin/env python3
"""
Test the user's aristocrats deck to verify death triggers work
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

# User's deck list
DECK_LIST = """1x Adeline, Resplendent Cathar
1x Ainok Strike Leader
1x Anguished Unmaking
1x Anim Pakal, Thousandth Moon
1x Arcane Signet
1x Avenger of the Fallen
1x Bastion of Remembrance
1x Battlefield Forge
1x Bitter Triumph
1x Bojuka Bog
1x Bone-Cairn Butcher
1x Braids, Arisen Nightmare
1x Caesar, Legion's Emperor
1x Canyon Slough
1x Caretaker's Talent
1x Cathars' Crusade
1x Caves of Koilos
1x Command Tower
1x Cruel Celebrant
1x Dalkovan Encampment
1x Damn
1x Deadly Dispute
1x Delina, Wild Mage
1x Diabolic Intent
1x Dollmaker's Shop // Porcelain Gallery
1x Dragonskull Summit
1x Elas il-Kor, Sadistic Pilgrim
1x Elesh Norn, Grand Cenobite
1x Elspeth, Sun's Champion
1x Enduring Innocence
1x Exalted Sunborn
1x Exotic Orchard
1x Farewell
1x Fellwar Stone
1x Fetid Heath
1x Final Vengeance
1x Forth Eorlingas!
1x Fountainport
1x Garna, Bloodfist of Keld
1x Gix, Yawgmoth Praetor
1x Goblin Bombardment
1x Godless Shrine
1x Goldlust Triad
1x Grand Crescendo
1x Grim Hireling
1x Heirloom Blade
1x High Market
1x Horn of the Mark
1x Idol of Oblivion
1x Impact Tremors
1x Inevitable Defeat
1x Isolated Chapel
1x Kambal, Profiteering Mayor
1x Kher Keep
1x Lightning Greaves
1x Mahadi, Emporium Master
1x Mardu Siegebreaker
1x Mirkwood Bats
1x Mondrak, Glory Dominus
1x Morbid Opportunist
4x Mountain
1x Nadier's Nightblade
1x Nomad Outpost
1x Outlaws' Merriment
1x Path of Ancestry
1x Path to Exile
1x Pitiless Plunderer
6x Plains
1x Priest of Forgotten Gods
1x Queen Marchesa
1x Redoubled Stormsinger
1x Retrofitter Foundry
1x Riders of Rohan
1x Rite of the Raging Storm
1x Rugged Prairie
1x Ruinous Ultimatum
1x Shattered Landscape
1x Smoldering Marsh
1x Sol Ring
1x Sulfurous Springs
4x Swamp
1x Swords to Plowshares
1x Talisman of Hierarchy
1x Talisman of Indulgence
1x Temple of Triumph
1x Tempt with Vengeance
1x Teysa Karlov
1x Viscera Seer
1x Voice of Victory
1x Warleader's Call
1x Warren Soultrader
1x Will of the Mardu
1x Windbrisk Heights
1x Wurmcoil Engine
1x Zulaport Cutthroat
1x Zurgo Stormrender"""

COMMANDER = "Queen Marchesa"

def parse_deck_list(deck_text):
    """Parse deck list into card names"""
    import re
    cards = []
    for line in deck_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # Parse "1x Card Name" format
        match = re.match(r'(\d+)x\s+(.+)', line)
        if match:
            count = int(match.group(1))
            name = match.group(2)
            cards.extend([name] * count)
    return cards

print("="*80)
print("TESTING USER'S ARISTOCRATS DECK")
print("="*80)

# Parse deck
card_names = parse_deck_list(DECK_LIST)
print(f"\n✓ Parsed {len(card_names)} cards from deck list")

# Show aristocrats cards in deck
print("\nAristocrats cards in deck:")
aristocrats_keywords = ['zulaport', 'cruel celebrant', 'bastion', 'nadier', 'mirkwood', 'elas il-kor',
                        'goblin bombardment', 'viscera seer', 'priest of forgotten', 'impact tremors', 'warleader']
for name in card_names:
    if any(kw in name.lower() for kw in aristocrats_keywords):
        print(f"  • {name}")

# Try to run simulation using the app's integration
print("\n" + "="*80)
print("RUNNING SIMULATION (via app integration)")
print("="*80)

try:
    from simulation.deck_simulator import simulate_deck_effectiveness
    from api.scryfall import fetch_card_details

    print("\n✓ Successfully imported simulation modules")

    # Fetch card details from Scryfall
    print(f"\nFetching card details from Scryfall for {len(set(card_names))} unique cards...")
    print("(This may take a moment...)")

    cards_with_details = []
    for name in set(card_names):
        try:
            card_data = fetch_card_details(name)
            if card_data:
                # Add quantity
                quantity = card_names.count(name)
                for _ in range(quantity):
                    cards_with_details.append(card_data)
        except Exception as e:
            print(f"  Warning: Could not fetch {name}: {e}")

    print(f"✓ Fetched details for {len(cards_with_details)} cards")

    # Find commander
    commander_data = None
    non_commander_cards = []

    for card in cards_with_details:
        if card['name'] == COMMANDER:
            commander_data = card
            commander_data['is_commander'] = True
        else:
            non_commander_cards.append(card)

    print(f"✓ Commander: {COMMANDER}")
    print(f"✓ Deck: {len(non_commander_cards)} cards")

    # Run simulation
    print("\nRunning 100 game simulation...")
    results = simulate_deck_effectiveness(
        cards=non_commander_cards,
        commander=commander_data,
        num_games=100,
        max_turns=10,
        verbose=False
    )

    # Display results
    print("\n" + "="*80)
    print("SIMULATION RESULTS")
    print("="*80)

    if 'summary' in results and 'error' not in results['summary']:
        summary = results['summary']

        print("\n📊 Deck Effectiveness:")
        print(f"  Total Damage (10 turns):    {summary.get('total_damage_10_turns', 0):.1f}")
        print(f"    └─ Combat Damage:          {summary.get('combat_damage_10_turns', 0):.1f}")
        print(f"    └─ Drain Damage:           {summary.get('drain_damage_10_turns', 0):.1f}")
        print(f"  Avg Damage/Turn:            {summary.get('avg_damage_per_turn', 0):.2f}")
        print(f"  Peak Board Power:           {summary.get('peak_power', 0):.1f}")
        print(f"  Commander Avg Turn:         {summary.get('commander_avg_cast_turn', 'N/A')}")
        print(f"  Total Tokens Created:       {summary.get('total_tokens_created', 0):.1f}")

        # Check if death triggers are working
        drain_damage = summary.get('drain_damage_10_turns', 0)
        total_damage = summary.get('total_damage_10_turns', 0)

        print("\n" + "="*80)
        if drain_damage > 50:
            print("✓ SUCCESS! Death triggers are firing correctly!")
            print(f"  Drain damage: {drain_damage:.1f} (expected 150-270 for aristocrats)")
            print(f"  Total damage: {total_damage:.1f} (expected 200-350 for aristocrats)")
        else:
            print("✗ FAILED! Death triggers still not working properly")
            print(f"  Drain damage: {drain_damage:.1f} (expected > 50)")
            print(f"  Total damage: {total_damage:.1f}")
            sys.exit(1)
    else:
        print(f"✗ ERROR: {results.get('summary', {}).get('error', 'Unknown error')}")
        sys.exit(1)

except ImportError as e:
    print(f"\n✗ Cannot run full integration test: {e}")
    print("\nTrying direct simulation test...")

    # Fallback: Test with deck_loader directly
    try:
        from deck_loader import load_deck_from_scryfall
        from run_simulation import run_simulations

        print("\n✓ Successfully imported Simulation modules")

        # Load deck
        print(f"\nLoading deck from Scryfall...")
        cards, commander, names = load_deck_from_scryfall(card_names, COMMANDER)

        print(f"✓ Loaded {len(cards)} cards + commander")

        # Check aristocrats cards have death triggers set
        print("\nChecking aristocrats cards:")
        aristocrats_found = 0
        for card in cards:
            death_val = getattr(card, 'death_trigger_value', 0)
            sac_outlet = getattr(card, 'sacrifice_outlet', False)
            if death_val > 0 or sac_outlet:
                aristocrats_found += 1
                print(f"  • {card.name}: death={death_val}, sac_outlet={sac_outlet}")

        if aristocrats_found == 0:
            print("✗ ERROR: No aristocrats cards detected!")
            sys.exit(1)

        print(f"\n✓ Found {aristocrats_found} aristocrats cards")

        # Run simulation
        print("\nRunning simulation...")
        summary_df, commander_cast_dist, avg_creature_power, interaction_summary = run_simulations(
            cards=cards,
            commander_card=commander,
            num_games=100,
            max_turns=10,
            verbose=False
        )

        # Get results
        total_damage = summary_df['Avg Total Damage'].sum()
        drain_damage = summary_df['Avg Drain Damage'].sum()

        print("\n" + "="*80)
        print("RESULTS:")
        print(f"  Total Damage (10 turns): {total_damage:.1f}")
        print(f"  Drain Damage (10 turns): {drain_damage:.1f}")

        if drain_damage > 50:
            print("\n✓ SUCCESS! Death triggers working!")
        else:
            print("\n✗ FAILED! Drain damage too low")
            sys.exit(1)

    except Exception as e2:
        print(f"\n✗ Fallback test also failed: {e2}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
