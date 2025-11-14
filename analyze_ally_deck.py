#!/usr/bin/env python3
"""
Analyze the ally prowess deck to find missing synergies
"""

import sys
import json
from src.api.local_cards import get_card_by_name, load_local_database
from src.utils.keyword_extractors import extract_creature_keywords
from src.utils.tribal_extractors import extract_tribal_payoffs, get_creature_types

# Load the card database
print("Loading card database...")
load_local_database()
print("Database loaded!\n")

# Load deck
deck_list = [
    "Sokka, Tenacious Tactician",
    "Banner of Kinship",
    "Chasm Guide",
    "Makindi Patrol",
    "Obelisk of Urd",
    "Resolute Blademaster",
    "Warleader's Call",
    "Bender's Waterskin",
    "White Lotus Tile",
    "Impact Tremors",
    "Jwari Shapeshifter",
    "Veyran, Voice of Duality",
    "Aang, Swift Savior",
    "Hakoda, Selfless Commander",
    "South Pole Voyager",
    "Ty Lee, Chi Blocker",
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
    "United Front",
    "Gideon, Ally of Zendikar",
    "Kykar, Wind's Fury",
    "Renewed Solidarity",
]

print("Fetching cards...")
cards = []
for name in deck_list:
    try:
        card = get_card_by_name(name)
        if card:
            cards.append(card)
        else:
            print(f"  WARNING: Could not find: {name}")
    except Exception as e:
        print(f"  ERROR fetching {name}: {e}")

print(f"\nFetched {len(cards)}/{len(deck_list)} cards\n")

# Analyze specific mechanics
print("=" * 80)
print("PROWESS ANALYSIS")
print("=" * 80)
prowess_cards = []
for card in cards:
    keywords = extract_creature_keywords(card)
    for kw in keywords:
        if kw['keyword'].lower() == 'prowess':
            prowess_cards.append(card)
            print(f"  ✓ {card['name']} has prowess")
            break

print(f"\nTotal prowess cards: {len(prowess_cards)}")

# Analyze rally triggers
print("\n" + "=" * 80)
print("RALLY / ETB TRIGGER ANALYSIS")
print("=" * 80)
rally_cards = []
for card in cards:
    text = card.get('oracle_text', '').lower()
    if 'rally' in text or ('whenever' in text and 'ally' in text and 'enters' in text):
        rally_cards.append(card)
        print(f"  ✓ {card['name']}")
        print(f"     Text: {card.get('oracle_text', '')[:100]}...")

print(f"\nTotal rally/ally ETB cards: {len(rally_cards)}")

# Analyze ally tribal
print("\n" + "=" * 80)
print("ALLY TRIBAL ANALYSIS")
print("=" * 80)
ally_creatures = []
for card in cards:
    types = get_creature_types(card)
    if 'Ally' in types or 'Changeling' in types:
        ally_creatures.append(card)
        print(f"  ✓ {card['name']} - Types: {types}")

print(f"\nTotal ally creatures: {len(ally_creatures)}")

# Analyze tribal payoffs
print("\n" + "=" * 80)
print("TRIBAL PAYOFF ANALYSIS")
print("=" * 80)
tribal_payoff_cards = []
for card in cards:
    payoffs = extract_tribal_payoffs(card)
    if payoffs['has_tribal_payoff']:
        tribal_payoff_cards.append((card, payoffs))
        print(f"  ✓ {card['name']}")
        if payoffs['chosen_type']['cares_about_chosen_type']:
            print(f"     - Cares about chosen type: {payoffs['chosen_type']['effect_type']}")
        if payoffs['tribal_lord']['is_tribal_lord']:
            print(f"     - Tribal lord for: {payoffs['tribal_lord']['creature_types']}")
        if payoffs['tribal_trigger']['has_tribal_trigger']:
            print(f"     - Tribal trigger: {payoffs['tribal_trigger']['trigger_type']}")

print(f"\nTotal tribal payoff cards: {len(tribal_payoff_cards)}")

# Analyze token generators
print("\n" + "=" * 80)
print("TOKEN GENERATOR ANALYSIS")
print("=" * 80)
token_generators = []
for card in cards:
    text = card.get('oracle_text', '').lower()
    if 'create' in text and 'token' in text:
        token_generators.append(card)
        print(f"  ✓ {card['name']}")
        # Find the token creation text
        for line in card.get('oracle_text', '').split('\n'):
            if 'create' in line.lower() and 'token' in line.lower():
                print(f"     {line.strip()}")

print(f"\nTotal token generators: {len(token_generators)}")

# Analyze spellslinger payoffs
print("\n" + "=" * 80)
print("SPELLSLINGER PAYOFF ANALYSIS")
print("=" * 80)
spellslinger_cards = []
patterns = [
    'whenever you cast an instant',
    'whenever you cast a sorcery',
    'whenever you cast a noncreature',
    'whenever you cast an instant or sorcery',
    'magecraft',
    'prowess'
]
for card in cards:
    text = card.get('oracle_text', '').lower()
    for pattern in patterns:
        if pattern in text:
            if card not in spellslinger_cards:
                spellslinger_cards.append(card)
                print(f"  ✓ {card['name']}")
                print(f"     Pattern: {pattern}")
            break

print(f"\nTotal spellslinger payoff cards: {len(spellslinger_cards)}")

# Analyze cheap instants/sorceries
print("\n" + "=" * 80)
print("CHEAP INSTANT/SORCERY ANALYSIS (CMC <= 2)")
print("=" * 80)
cheap_spells = []
for card in cards:
    type_line = card.get('type_line', '').lower()
    cmc = card.get('cmc', 99)
    if ('instant' in type_line or 'sorcery' in type_line) and cmc <= 2:
        cheap_spells.append(card)
        print(f"  ✓ {card['name']} (CMC: {cmc})")

print(f"\nTotal cheap spells: {len(cheap_spells)}")

# Summary
print("\n" + "=" * 80)
print("DECK THEME SUMMARY")
print("=" * 80)
print(f"Ally creatures: {len(ally_creatures)}")
print(f"Rally/ETB triggers: {len(rally_cards)}")
print(f"Tribal payoffs: {len(tribal_payoff_cards)}")
print(f"Token generators: {len(token_generators)}")
print(f"Prowess cards: {len(prowess_cards)}")
print(f"Spellslinger payoffs: {len(spellslinger_cards)}")
print(f"Cheap spells (CMC≤2): {len(cheap_spells)}")

print("\n" + "=" * 80)
print("POTENTIAL SYNERGY GAPS")
print("=" * 80)
print(f"1. Rally + Token generators: {len(rally_cards)} rally cards × {len(token_generators)} token generators")
print(f"2. Prowess + Cheap spells: {len(prowess_cards)} prowess cards × {len(cheap_spells)} cheap spells")
print(f"3. Spellslinger + Cheap spells: {len(spellslinger_cards)} spellslinger × {len(cheap_spells)} cheap spells")
print(f"4. Token generators + ETB triggers: {len(token_generators)} × {len(rally_cards)}")

print("\n" + "=" * 80)
print("MISSING MECHANICS TO IMPLEMENT")
print("=" * 80)
print("1. Rally mechanic detection (specific Ally ETB triggers)")
print("2. ETB trigger synergies with token generation")
print("3. Prowess + cantrip synergies (specific high-value pairing)")
print("4. Multiple spell per turn synergies (storm-like effects)")
print("5. Ally-specific tribal bonuses")
