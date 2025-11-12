#!/usr/bin/env python3
"""Test deck using local card database."""

import sys
import json
sys.path.insert(0, 'Simulation')

from simulate_game import Card
from run_simulation import run_simulations

def load_local_cards_db():
    """Load the local cards database."""
    with open('data/cards/cards-minimal.json', 'r') as f:
        return json.load(f)

def find_card_by_name(cards_db, name):
    """Find a card in the database by name."""
    name_lower = name.lower()
    for card in cards_db:
        if card['name'].lower() == name_lower:
            return card
    return None

def create_card_from_json(card_json):
    """Create a Card object from JSON data."""
    return Card(
        name=card_json['name'],
        type=card_json.get('type_line', ''),
        mana_cost=card_json.get('mana_cost', ''),
        power=int(card_json.get('power', 0)) if card_json.get('power') else 0,
        toughness=int(card_json.get('toughness', 0)) if card_json.get('toughness') else 0,
        produces_colors=card_json.get('produced_mana', []),
        mana_production=0,  # Will be calculated
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste='Haste' in card_json.get('keywords', []),
        has_flash='Flash' in card_json.get('keywords', []),
        equip_cost="",
        power_buff=0,
        is_commander=False,
        is_legendary='Legendary' in card_json.get('type_line', ''),
        keywords_when_equipped=[],
        puts_land=False,
        draw_cards=0,
        deals_damage=0,
        activated_abilities=[],
        triggered_abilities=[],
        oracle_text=card_json.get('oracle_text', ''),
        fetch_basic=False,
        fetch_land_types=[],
        fetch_land_tapped=False,
    )

print("=" * 80)
print("TESTING WITH LOCAL CARD DATABASE")
print("=" * 80)

print("\n[Step 1] Loading local card database...")
cards_db = load_local_cards_db()
print(f"✓ Loaded {len(cards_db)} cards from database")

# Key cards for the deck
card_names = [
    "Syr Konrad, the Grim",
    "Hedron Crab",
    "Muldrotha, the Gravetide",
    "Meren of Clan Nel Toth",
    "Living Death",
    "Gravecrawler",
    "Diregraf Captain",
    "Sol Ring",
    "Arcane Signet",
    "Command Tower",
    "Swamp", "Swamp", "Swamp", "Swamp", "Swamp",
    "Forest", "Forest", "Forest", "Forest", "Forest",
    "Island", "Island", "Island",
]

print("\n[Step 2] Finding cards in database...")
deck_cards = []
commander = None

for name in card_names:
    card_json = find_card_by_name(cards_db, name)
    if card_json:
        card = create_card_from_json(card_json)

        # Apply mill values
        from oracle_text_parser import parse_mill_value
        mill_value = parse_mill_value(card.oracle_text, card.name)
        if mill_value > 0:
            card.mill_value = mill_value
            print(f"  ✓ {card.name}: mill_value={mill_value}")

        # Check for key cards
        if 'syr konrad' in name.lower():
            print(f"  ✓ {name}: oracle_text={len(card.oracle_text)} chars")
        elif 'muldrotha' in name.lower():
            print(f"  ✓ {name}: oracle_text={len(card.oracle_text)} chars")
        elif 'meren' in name.lower():
            print(f"  ✓ {name}: oracle_text={len(card.oracle_text)} chars")
        elif 'living death' in name.lower():
            print(f"  ✓ {name}: oracle_text={len(card.oracle_text)} chars")

        deck_cards.append(card)
    else:
        print(f"  ✗ {name}: NOT FOUND in database")

# Use Syr Konrad as commander for testing
for card in deck_cards:
    if 'syr konrad' in card.name.lower():
        commander = card
        deck_cards.remove(card)
        break

if not commander:
    print("\n✗ Commander not found, using first card")
    commander = deck_cards.pop(0)

commander.is_commander = True

print(f"\n✓ Deck ready: {len(deck_cards)} cards + commander ({commander.name})")

# Run simulation
print("\n[Step 3] Running simulation (10 games, 10 turns)...")
print("-" * 80)

try:
    summary, cmd_dist, creature_power, interaction, stats = run_simulations(
        cards=deck_cards,
        commander_card=commander,
        num_games=10,
        max_turns=10,
        verbose=False,
        log_dir=None,
        num_workers=1,
        calculate_statistics=True
    )

    # Calculate metrics
    total_damage = summary["Avg Total Damage"].sum()
    total_combat = summary["Avg Combat Damage"].sum()
    total_drain = summary["Avg Drain Damage"].sum()
    avg_damage_per_turn = total_damage / 10
    peak_power = summary["Avg Total Power"].max()

    print("\n" + "=" * 80)
    print("SIMULATION RESULTS")
    print("=" * 80)

    print(f"\nDeck Effectiveness:")
    print(f"  Total Damage (10 turns):  {total_damage:.1f}")
    print(f"    - Combat Damage:        {total_combat:.1f}")
    print(f"    - Drain Damage:         {total_drain:.1f}  ⬅ Syr Konrad triggers")
    print(f"  Avg Damage/Turn:          {avg_damage_per_turn:.2f}")
    print(f"  Peak Board Power:         {peak_power:.1f}  ⬅ Reanimation")

    print(f"\nGraveyard Metrics:")
    print(f"  Avg Graveyard Size:       {summary['Avg Graveyard Size'].mean():.1f}")

    # Compare to before
    print("\n" + "=" * 80)
    print("COMPARISON TO BEFORE FIXES")
    print("=" * 80)
    print(f"\nBEFORE: Total Damage = 26")
    print(f"AFTER:  Total Damage = {total_damage:.1f}")
    print(f"IMPROVEMENT: {((total_damage - 26) / 26 * 100):.0f}%")

    print(f"\nBEFORE: Drain Damage = ~0-5")
    print(f"AFTER:  Drain Damage = {total_drain:.1f}")

    if total_drain > 30:
        print("\n✓ EXCELLENT: Syr Konrad is working!")
    elif total_drain > 10:
        print("\n✓ GOOD: Syr Konrad triggers visible")
    else:
        print("\n⚠ Syr Konrad may not be triggering enough")
        print("  Try running with verbose=True to see what's happening")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
