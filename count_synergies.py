#!/usr/bin/env python3
"""
Count how many synergies are detected in the ally prowess deck
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.synergy_engine.analyzer import analyze_card_pair

print("Loading database...")
load_local_database()

# Deck list (non-land cards only)
deck_list = [
    "Banner of Kinship",
    "Chasm Guide",
    "Makindi Patrol",
    "Obelisk of Urd",
    "Resolute Blademaster",
    "Warleader's Call",
    "Bender's Waterskin",
    "Impact Tremors",
    "Jwari Shapeshifter",
    "Veyran, Voice of Duality",
    "Hakoda, Selfless Commander",
    "Brainstorm",
    "Expressive Iteration",
    "Faithless Looting",
    "Frantic Search",
    "Frostcliff Siege",
    "Jeskai Ascendancy",
    "Kindred Discovery",
    "Opt",
    "Ponder",
    "Preordain",
    "Skullclamp",
    "Whirlwind of Thought",
    "Bria, Riptide Rogue",
    "Nexus of Fate",
    "Redirect Lightning",
    "Lantern Scout",
    "Boros Charm",
    "Swiftfoot Boots",
    "Balmor, Battlemage Captain",
    "Arcane Signet",
    "Azorius Signet",
    "Boros Signet",
    "Fellwar Stone",
    "Izzet Signet",
    "Patchwork Banner",
    "Sol Ring",
    "Storm-Kiln Artist",
    "Talisman of Conviction",
    "Talisman of Creativity",
    "Talisman of Progress",
    "Thought Vessel",
    "Narset, Enlightened Exile",
    "Abrade",
    "An Offer You Can't Refuse",
    "Arcane Denial",
    "Blasphemous Act",
    "Counterspell",
    "Cyclonic Rift",
    "Dovin's Veto",
    "Farewell",
    "Lightning Bolt",
    "Narset's Reversal",
    "Negate",
    "Path to Exile",
    "Swords to Plowshares",
    "Tuktuk Scrapper",
    "Gideon, Ally of Zendikar",
    "Kykar, Wind's Fury",
    "Renewed Solidarity",
]

print("Fetching cards...")
cards = []
for name in deck_list:
    card = get_card_by_name(name)
    if card:
        cards.append(card)

print(f"Loaded {len(cards)} cards\n")

# Count synergies
print("Counting synergies...")
synergy_counts = {}
total_synergies = 0

for i, card1 in enumerate(cards):
    for card2 in cards[i+1:]:
        synergies = analyze_card_pair(card1, card2)
        if synergies:
            total_synergies += len(synergies)
            for syn in synergies:
                syn_type = syn.get('name', 'Unknown')
                synergy_counts[syn_type] = synergy_counts.get(syn_type, 0) + 1

print(f"\n{'='*80}")
print(f"TOTAL SYNERGIES DETECTED: {total_synergies}")
print(f"{'='*80}\n")

# Sort by count
sorted_synergies = sorted(synergy_counts.items(), key=lambda x: x[1], reverse=True)

print("Top 20 synergy types:")
for i, (syn_type, count) in enumerate(sorted_synergies[:20], 1):
    print(f"{i:2}. {syn_type:40} x{count}")

# Show newly added synergies specifically
print(f"\n{'='*80}")
print("NEW ALLY/PROWESS SYNERGIES:")
print(f"{'='*80}")
new_synergies = {
    'Rally + Token Creation': 0,
    'Prowess + Cheap Spell': 0,
    'Multiple Rally Triggers': 0,
    'Ally Tribal Synergy': 0,
    'ETB Trigger + Tokens': 0,
    'Spellslinger + Cantrip': 0
}

for syn_type, count in synergy_counts.items():
    if syn_type in new_synergies:
        new_synergies[syn_type] = count
        print(f"✓ {syn_type:40} x{count}")

total_new = sum(new_synergies.values())
print(f"\nTotal new synergies: {total_new}")
print(f"Percentage of total: {total_new/total_synergies*100:.1f}%")
