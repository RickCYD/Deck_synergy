#!/usr/bin/env python3
"""
Full deck analysis showing detailed synergy breakdown by card
"""

from src.api.local_cards import load_local_database, get_card_by_name
from src.synergy_engine.analyzer import analyze_deck_synergies

print("=" * 80)
print("FULL DECK ANALYSIS - DETAILED BREAKDOWN")
print("=" * 80)

# Load database
print("\nLoading card database...")
load_local_database()

# Build a representative spellslinger deck
deck_cards = []

print("\nBuilding test deck...")

# Commander
aang = None  # Custom card, not in database

# Core engines (THE STARS OF THE SHOW)
engines = [
    'Jeskai Ascendancy',
    'Veyran, Voice of Duality',
    'Whirlwind of Thought',
    'Storm-Kiln Artist',
    "Kykar, Wind's Fury",
    'Balmor, Battlemage Captain',
]

# Cheap cantrips (FUEL FOR THE ENGINES)
cantrips = [
    'Brainstorm',
    'Opt',
    'Ponder',
    'Preordain',
    'Consider',
    'Gitaxian Probe',
]

# Removal (INTERACTION + SPELL TRIGGERS)
removal = [
    'Lightning Bolt',
    'Path to Exile',
    'Swords to Plowshares',
    'Counterspell',
    'Negate',
    'Abrade',
    'Chaos Warp',
]

# Extra turns (WIN CONDITIONS)
extra_turns = [
    'Nexus of Fate',
    'Temporal Manipulation',
]

# Spell copy (COMBO PIECES)
spell_copy = [
    "Narset's Reversal",
    'Dualcaster Mage',
]

# Token generators (VALUE ENGINES)
token_gen = [
    'Talrand, Sky Summoner',
    'Murmuring Mystic',
    'Young Pyromancer',
]

# Prowess creatures (BEATDOWN)
prowess = [
    'Monastery Swiftspear',
    'Soul-Scar Mage',
    'Stormchaser Mage',
]

# Tribal allies
allies = [
    'Sea Gate Loremaster',
    'Halimar Excavator',
    'Kazuul Warlord',
    'Ondu Cleric',
]

all_card_names = engines + cantrips + removal + extra_turns + spell_copy + token_gen + prowess + allies

print(f"Loading {len(all_card_names)} cards...")
for name in all_card_names:
    card = get_card_by_name(name)
    if card:
        deck_cards.append(card)
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} not found")

print(f"\n✓ Loaded {len(deck_cards)} cards")

# Analyze synergies
print("\n" + "=" * 80)
print("ANALYZING DECK...")
print("=" * 80)

result = analyze_deck_synergies(deck_cards, run_simulation=False)

# Extract synergies
synergies = []
if isinstance(result, dict) and 'two_way' in result:
    for card_pair_key, pair_data in result['two_way'].items():
        if 'synergies' in pair_data:
            for category, synergy_list in pair_data['synergies'].items():
                for synergy in synergy_list:
                    # Add card names to synergy for easier filtering
                    synergy['card_pair'] = card_pair_key
                    synergies.append(synergy)

print(f"\n✅ Found {len(synergies)} total synergies")

# ============================================================================
# BREAKDOWN BY CATEGORY
# ============================================================================

print("\n" + "=" * 80)
print("SYNERGY BREAKDOWN BY CATEGORY")
print("=" * 80)

categories = {}
for syn in synergies:
    cat = syn.get('category', 'unknown')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(syn)

# Sort by count
sorted_cats = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)

for cat, cat_synergies in sorted_cats[:10]:
    print(f"\n{cat}: {len(cat_synergies)} synergies")
    # Show top 3 examples
    for syn in cat_synergies[:3]:
        print(f"  • {syn.get('name', 'Unknown')} (Value: {syn.get('value', 0)})")

# ============================================================================
# BREAKDOWN BY KEY ENGINE CARDS
# ============================================================================

print("\n" + "=" * 80)
print("SYNERGY BREAKDOWN BY ENGINE CARD")
print("=" * 80)

key_engines = [
    'Jeskai Ascendancy',
    'Veyran, Voice of Duality',
    'Whirlwind of Thought',
    'Storm-Kiln Artist',
    "Kykar, Wind's Fury",
]

for engine in key_engines:
    engine_synergies = [s for s in synergies if engine in s.get('description', '')]

    if engine_synergies:
        print(f"\n{engine}: {len(engine_synergies)} synergies")

        # Breakdown by synergy value
        high_value = [s for s in engine_synergies if s.get('value', 0) >= 10.0]
        medium_value = [s for s in engine_synergies if 5.0 <= s.get('value', 0) < 10.0]
        low_value = [s for s in engine_synergies if s.get('value', 0) < 5.0]

        print(f"  High value (10+): {len(high_value)}")
        print(f"  Medium value (5-10): {len(medium_value)}")
        print(f"  Low value (<5): {len(low_value)}")

        # Show top 3
        top_synergies = sorted(engine_synergies, key=lambda x: x.get('value', 0), reverse=True)[:3]
        print(f"  Top 3:")
        for syn in top_synergies:
            desc = syn.get('description', '')[:60] + "..."
            print(f"    • {desc} (Value: {syn.get('value', 0)})")

# ============================================================================
# INFINITE COMBOS
# ============================================================================

print("\n" + "=" * 80)
print("INFINITE COMBOS")
print("=" * 80)

infinite_combos = [s for s in synergies if s.get('value', 0) == 50.0]

if infinite_combos:
    print(f"\n🔥 Found {len(infinite_combos)} INFINITE COMBOS:")
    for combo in infinite_combos:
        print(f"\n  • {combo.get('name', 'Unknown')}")
        print(f"    {combo.get('description', '')}")
        print(f"    Value: {combo.get('value', 0)}")
else:
    print("\n⚠️  No infinite combos detected")

# ============================================================================
# HIGHEST VALUE SYNERGIES
# ============================================================================

print("\n" + "=" * 80)
print("TOP 20 HIGHEST VALUE SYNERGIES")
print("=" * 80)

top_synergies = sorted(synergies, key=lambda x: x.get('value', 0), reverse=True)[:20]

for i, syn in enumerate(top_synergies, 1):
    print(f"\n{i}. {syn.get('name', 'Unknown')} (Value: {syn.get('value', 0)})")
    print(f"   {syn.get('description', '')[:80]}...")
    print(f"   Category: {syn.get('category', 'unknown')}/{syn.get('subcategory', 'none')}")

# ============================================================================
# CARD SYNERGY DENSITY
# ============================================================================

print("\n" + "=" * 80)
print("CARD SYNERGY DENSITY (Most Connected Cards)")
print("=" * 80)

# Count how many synergies each card appears in
card_synergy_count = {}
for syn in synergies:
    card_pair = syn.get('card_pair', '')
    if '||' in card_pair:
        card1, card2 = card_pair.split('||')
        card_synergy_count[card1] = card_synergy_count.get(card1, 0) + 1
        card_synergy_count[card2] = card_synergy_count.get(card2, 0) + 1

# Sort by count
sorted_cards = sorted(card_synergy_count.items(), key=lambda x: x[1], reverse=True)[:15]

print("\nMost synergistic cards (top 15):")
for card, count in sorted_cards:
    print(f"  {card}: {count} synergies")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

total_value = sum(s.get('value', 0) for s in synergies)
avg_value = total_value / len(synergies) if synergies else 0

print(f"\nTotal cards: {len(deck_cards)}")
print(f"Total synergies: {len(synergies)}")
print(f"Total synergy value: {total_value:.1f}")
print(f"Average synergy value: {avg_value:.2f}")
print(f"Categories: {len(categories)}")
print(f"Infinite combos: {len(infinite_combos)}")

# Synergy distribution
high_value_synergies = [s for s in synergies if s.get('value', 0) >= 10.0]
medium_value_synergies = [s for s in synergies if 5.0 <= s.get('value', 0) < 10.0]
low_value_synergies = [s for s in synergies if s.get('value', 0) < 5.0]

print(f"\nSynergy value distribution:")
print(f"  High value (10+): {len(high_value_synergies)} ({len(high_value_synergies)/len(synergies)*100:.1f}%)")
print(f"  Medium value (5-10): {len(medium_value_synergies)} ({len(medium_value_synergies)/len(synergies)*100:.1f}%)")
print(f"  Low value (<5): {len(low_value_synergies)} ({len(low_value_synergies)/len(synergies)*100:.1f}%)")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
