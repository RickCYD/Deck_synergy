"""
Test synergy detection on the user's actual Aang deck.
"""

from src.api.local_cards import load_local_database, get_card_by_name
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.models.deck import Deck

# User's actual decklist
decklist = """
1x Aang, Swift Savior // Aang and La, Ocean's Fury
1x Abrade
1x Adarkar Wastes
1x Ally Encampment
1x An Offer You Can't Refuse
1x Arcane Denial
1x Arcane Signet
1x Azorius Signet
1x Balmor, Battlemage Captain
1x Banner of Kinship
1x Battlefield Forge
1x Bender's Waterskin
1x Blasphemous Act
1x Boros Charm
1x Boros Signet
1x Brainstorm
1x Bria, Riptide Rogue
1x Chasm Guide
1x Clifftop Retreat
1x Command Tower
1x Counterspell
1x Cyclonic Rift
1x Dovin's Veto
1x Evolving Wilds
1x Exotic Orchard
1x Expressive Iteration
1x Faithless Looting
1x Farewell
1x Fellwar Stone
1x Frantic Search
1x Frostcliff Siege
1x Gideon, Ally of Zendikar
1x Glacial Fortress
1x Hakoda, Selfless Commander
1x Impact Tremors
12x Island
1x Izzet Signet
1x Jeskai Ascendancy
1x Jwari Shapeshifter
1x Kindred Discovery
1x Kykar, Wind's Fury
1x Lantern Scout
1x Lightning Bolt
1x Makindi Patrol
6x Mountain
1x Mystic Monastery
1x Narset, Enlightened Exile
1x Narset's Reversal
1x Negate
1x Nexus of Fate
1x Obelisk of Urd
1x Opt
1x Patchwork Banner
1x Path of Ancestry
1x Path to Exile
5x Plains
1x Ponder
1x Preordain
1x Redirect Lightning
1x Reliquary Tower
1x Renewed Solidarity
1x Resolute Blademaster
1x Secluded Courtyard
1x Shivan Reef
1x Skullclamp
1x Sokka, Tenacious Tactician
1x Sol Ring
1x South Pole Voyager
1x Storm-Kiln Artist
1x Swiftfoot Boots
1x Swords to Plowshares
1x Talisman of Conviction
1x Talisman of Creativity
1x Talisman of Progress
1x Thought Vessel
1x Tuktuk Scrapper
1x Ty Lee, Chi Blocker
1x Unclaimed Territory
1x United Front
1x Veyran, Voice of Duality
1x Warleader's Call
1x Whirlwind of Thought
1x White Lotus Tile
"""

print("=" * 80)
print("ANALYZING USER'S ACTUAL AANG DECK")
print("=" * 80)

# Load card database
print("\nLoading card database...")
load_local_database()

# Parse decklist
print("\nParsing decklist...")
cards = []
card_names = []
for line in decklist.strip().split('\n'):
    if not line.strip() or 'x' not in line:
        continue
    parts = line.split('x ', 1)
    if len(parts) == 2:
        count = int(parts[0])
        name = parts[1].strip()

        card = get_card_by_name(name)
        if card:
            for _ in range(count):
                cards.append(card)
            card_names.append(name)
        else:
            print(f"  ⚠️  Could not find: {name}")

print(f"\n✓ Loaded {len(cards)} cards ({len(card_names)} unique)")

# Mark commander
for card in cards:
    if 'Aang' in card['name']:
        card['is_commander'] = True
        print(f"✓ Commander: {card['name']}")
        break

# Create deck object (not needed for analyzer, but good for structure)
# deck = Deck(deck_id="test_deck", name="Aang Ally Spellslinger", cards=cards)

print("\n" + "=" * 80)
print("ANALYZING SYNERGIES...")
print("=" * 80)

# Analyze synergies (pass cards list directly)
result = analyze_deck_synergies(cards, run_simulation=False)
synergies = []
if isinstance(result, dict) and 'two_way' in result:
    # New format - extract synergies from two_way dict
    # Structure: result['two_way'][card_pair_key] = {
    #   'card1': str,
    #   'card2': str,
    #   'synergies': {
    #     'category': [synergy1, synergy2, ...],
    #     ...
    #   }
    # }
    for card_pair_key, pair_data in result['two_way'].items():
        if 'synergies' in pair_data:
            # Extract all synergies from all categories
            for category, synergy_list in pair_data['synergies'].items():
                for synergy in synergy_list:
                    synergies.append(synergy)
else:
    # Old format - assume it's a list
    synergies = result if isinstance(result, list) else []

# Count by category
categories = {}
for syn in synergies:
    cat = syn.get('category', 'unknown')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(syn)

print(f"\n✅ Found {len(synergies)} total synergies")
print("\nBreakdown by category:")
for cat, syns in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"  {cat}: {len(syns)} synergies")

# Find specific high-value synergies
print("\n" + "=" * 80)
print("KEY SPELLSLINGER SYNERGIES DETECTED")
print("=" * 80)

important_synergies = []
for syn in synergies:
    name = syn.get('name', '')
    desc = syn.get('description', '').lower()

    # Look for our new synergies
    if any(keyword in name.lower() or keyword in desc for keyword in [
        'veyran', 'jeskai ascendancy', 'whirlwind', 'kindred discovery',
        'storm-kiln', 'kykar', 'narset\'s reversal', 'trigger doubling',
        'untap engine', 'spell draw'
    ]):
        important_synergies.append(syn)

if important_synergies:
    print(f"\n✓ Found {len(important_synergies)} spellslinger engine synergies:")
    for syn in important_synergies[:15]:  # Show first 15
        print(f"\n  • {syn.get('name', 'Unknown')}")
        print(f"    Value: {syn.get('value', syn.get('strength', 0))}")
        print(f"    {syn.get('description', 'No description')[:100]}")
else:
    print("\n❌ NO spellslinger engine synergies detected!")
    print("This means the new rules are NOT being called.")

# Check for infinite combo
print("\n" + "=" * 80)
print("CHECKING FOR INFINITE COMBO")
print("=" * 80)

infinite_combos = [s for s in synergies if s.get('value', s.get('strength', 0)) >= 50.0]
if infinite_combos:
    print(f"\n✓ Found {len(infinite_combos)} infinite combo(s):")
    for combo in infinite_combos:
        print(f"  • {combo.get('name', 'Unknown')}")
        print(f"    {combo.get('description', 'No description')}")
else:
    print("\n⚠️  No infinite combos detected (Expected: Narset's Reversal + Nexus of Fate)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total synergies: {len(synergies)}")
print(f"Spellslinger synergies: {len(important_synergies)}")
print(f"Infinite combos: {len(infinite_combos)}")
print("=" * 80)
