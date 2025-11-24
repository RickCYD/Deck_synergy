"""
Quick diagnostic script to check what cards are missing from your Sokka deck
Run this to see which cards failed to load
"""

from src.api import local_cards
from src.api.scryfall import ScryfallAPI

# Load database
print("Loading card database...")
local_cards.load_local_database()
print(f"✓ Loaded {len(local_cards._local_db.cards_by_name)} cards\n")

# Your deck list
sokka_deck = """
Sokka, Tenacious Tactician
Banner of Kinship
Chasm Guide
Makindi Patrol
Obelisk of Urd
Resolute Blademaster
Warleader's Call
Bender's Waterskin
White Lotus Tile
Impact Tremors
Jwari Shapeshifter
Veyran, Voice of Duality
Aang, Swift Savior
Hakoda, Selfless Commander
Sokka, Lateral Strategist
South Pole Voyager
Ty Lee, Chi Blocker
Brainstorm
Expressive Iteration
Faithless Looting
Frantic Search
Frostcliff Siege
Jeskai Ascendancy
Kindred Discovery
Opt
Ponder
Preordain
Skullclamp
Whirlwind of Thought
Sokka's Charge
Bria, Riptide Rogue
Nexus of Fate
Octopus Form
Redirect Lightning
Lantern Scout
Boros Charm
Swiftfoot Boots
Take the Bait
Balmor, Battlemage Captain
Arcane Signet
Azorius Signet
Boros Signet
Fellwar Stone
Izzet Signet
Patchwork Banner
Sol Ring
Storm-Kiln Artist
Talisman of Conviction
Talisman of Creativity
Talisman of Progress
Thought Vessel
Narset, Enlightened Exile
Abrade
An Offer You Can't Refuse
Arcane Denial
Blasphemous Act
Counterspell
Cyclonic Rift
Dovin's Veto
Farewell
Invert Polarity
Lightning Bolt
Narset's Reversal
Negate
Path to Exile
Swords to Plowshares
Tuktuk Scrapper
United Front
Gideon, Ally of Zendikar
Kykar, Wind's Fury
Renewed Solidarity
""".strip().split('\n')

# Check each card
found = []
missing = []
scryfall_only = []

api = ScryfallAPI()

for card_name in sokka_deck:
    card_name = card_name.strip()
    if not card_name:
        continue

    # Check local database
    local_card = local_cards.get_card_by_name(card_name)

    if local_card:
        found.append(card_name)
        print(f"✓ {card_name}")
    else:
        print(f"✗ {card_name} (not in local database, checking Scryfall...)")

        # Try Scryfall
        try:
            scryfall_card = api.get_card_by_name(card_name)
            if scryfall_card:
                scryfall_only.append(card_name)
                print(f"  → Found on Scryfall (will load, but slower)")
            else:
                missing.append(card_name)
                print(f"  → NOT FOUND on Scryfall either!")
        except Exception as e:
            missing.append(card_name)
            print(f"  → ERROR: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"✓ Found in local database: {len(found)}/{len(sokka_deck)}")
print(f"⚠ Found only on Scryfall (slow): {len(scryfall_only)}")
print(f"✗ NOT FOUND anywhere: {len(missing)}")

if missing:
    print(f"\n❌ MISSING CARDS (deck won't load completely):")
    for card in missing:
        print(f"  - {card}")
    print("\nThese cards are likely from Secret Lair/Universes Beyond and not yet in Scryfall.")
    print("The deck will load without them, but analysis will be incomplete.")

if scryfall_only:
    print(f"\n⚠ SCRYFALL-ONLY CARDS (will load, but takes ~2 seconds each):")
    for card in scryfall_only:
        print(f"  - {card}")
    print(f"\nEstimated loading time: ~{len(scryfall_only) * 2} seconds extra")

print(f"\n✅ {len(found)} cards will load instantly from local database")
