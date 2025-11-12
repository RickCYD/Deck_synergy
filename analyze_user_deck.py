#!/usr/bin/env python3
"""
Analyze the user's specific deck to verify contextual necessity scoring
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.recommendations import RecommendationEngine

# User's deck
deck_cards = [
    # Commander
    {"name": "Teval, the Balanced Scale", "type_line": "Legendary Creature", "cmc": 3, "board": "commanders"},

    # Blink
    {"name": "Gossip's Talent", "type_line": "Enchantment", "cmc": 2},

    # Creature
    {"name": "Siegfried, Famed Swordsman", "type_line": "Legendary Creature", "cmc": 3},

    # Drain
    {"name": "Diregraf Captain", "type_line": "Creature", "cmc": 2},
    {"name": "Ob Nixilis, the Fallen", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Syr Konrad, the Grim", "type_line": "Legendary Creature", "cmc": 5},

    # Draw
    {"name": "Disciple of Bolas", "type_line": "Creature", "cmc": 4},
    {"name": "Frantic Search", "type_line": "Instant", "cmc": 3},
    {"name": "Kindred Discovery", "type_line": "Enchantment", "cmc": 4},
    {"name": "Kishla Skimmer", "type_line": "Creature", "cmc": 2},
    {"name": "Priest of Forgotten Gods", "type_line": "Creature", "cmc": 2},
    {"name": "Tatyova, Benthic Druid", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Teval's Judgment", "type_line": "Instant", "cmc": 2},
    {"name": "Treasure Cruise", "type_line": "Sorcery", "cmc": 8},
    {"name": "Welcome the Dead", "type_line": "Instant", "cmc": 4},

    # Finisher
    {"name": "Eldrazi Monument", "type_line": "Artifact", "cmc": 5},
    {"name": "Living Death", "type_line": "Sorcery", "cmc": 5},
    {"name": "Wonder", "type_line": "Creature", "cmc": 4},

    # Mill
    {"name": "Aftermath Analyst", "type_line": "Creature", "cmc": 3},
    {"name": "Cemetery Tampering", "type_line": "Sorcery", "cmc": 2},
    {"name": "Dredger's Insight", "type_line": "Sorcery", "cmc": 3},
    {"name": "Eccentric Farmer", "type_line": "Creature", "cmc": 3},
    {"name": "Hedron Crab", "type_line": "Creature", "cmc": 1},
    {"name": "Nyx Weaver", "type_line": "Enchantment Creature", "cmc": 3},
    {"name": "Shigeki, Jukai Visionary", "type_line": "Legendary Creature", "cmc": 2},
    {"name": "Sidisi, Brood Tyrant", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Smuggler's Surprise", "type_line": "Instant", "cmc": 3},
    {"name": "Stitcher's Supplier", "type_line": "Creature", "cmc": 1},

    # Ramp
    {"name": "Arcane Signet", "type_line": "Artifact", "cmc": 2},
    {"name": "Deathrite Shaman", "type_line": "Creature", "cmc": 1},
    {"name": "Hedge Shredder", "type_line": "Creature", "cmc": 2},
    {"name": "Icetill Explorer", "type_line": "Creature", "cmc": 2},
    {"name": "Millikin", "type_line": "Artifact Creature", "cmc": 2},
    {"name": "Molt Tender", "type_line": "Creature", "cmc": 2},
    {"name": "Seton, Krosan Protector", "type_line": "Legendary Creature", "cmc": 3},
    {"name": "Skull Prophet", "type_line": "Creature", "cmc": 2},
    {"name": "Sol Ring", "type_line": "Artifact", "cmc": 1},
    {"name": "Titans' Nest", "type_line": "Enchantment", "cmc": 3},
    {"name": "Wight of the Reliquary", "type_line": "Creature", "cmc": 4},
    {"name": "Will of the Sultai", "type_line": "Instant", "cmc": 4},

    # Recursion
    {"name": "Afterlife from the Loam", "type_line": "Sorcery", "cmc": 2},
    {"name": "Colossal Grave-Reaver", "type_line": "Creature", "cmc": 7},
    {"name": "Conduit of Worlds", "type_line": "Artifact", "cmc": 3},
    {"name": "Dread Return", "type_line": "Sorcery", "cmc": 4},
    {"name": "Eternal Witness", "type_line": "Creature", "cmc": 3},
    {"name": "Gravecrawler", "type_line": "Creature", "cmc": 1},
    {"name": "Kotis, Sibsig Champion", "type_line": "Legendary Creature", "cmc": 4},
    {"name": "Life from the Loam", "type_line": "Sorcery", "cmc": 2},
    {"name": "Lost Monarch of Ifnir", "type_line": "Creature", "cmc": 5},
    {"name": "Meren of Clan Nel Toth", "type_line": "Legendary Creature", "cmc": 4},
    {"name": "Muldrotha, the Gravetide", "type_line": "Legendary Creature", "cmc": 6},
    {"name": "Phyrexian Reclamation", "type_line": "Enchantment", "cmc": 1},
    {"name": "The Scarab God", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Tortured Existence", "type_line": "Enchantment", "cmc": 1},

    # Removal
    {"name": "Amphin Mutineer", "type_line": "Creature", "cmc": 4},
    {"name": "An Offer You Can't Refuse", "type_line": "Instant", "cmc": 1},
    {"name": "Counterspell", "type_line": "Instant", "cmc": 2},
    {"name": "Deadly Brew", "type_line": "Sorcery", "cmc": 2},
    {"name": "Ghost Vacuum", "type_line": "Artifact", "cmc": 3},
    {"name": "Heritage Reclamation", "type_line": "Instant", "cmc": 3},
    {"name": "Into the Flood Maw", "type_line": "Instant", "cmc": 6},
    {"name": "Lethal Scheme", "type_line": "Instant", "cmc": 4},
    {"name": "Necromantic Selection", "type_line": "Sorcery", "cmc": 7},
    {"name": "Overwhelming Remorse", "type_line": "Instant", "cmc": 6},
    {"name": "Tear Asunder", "type_line": "Instant", "cmc": 2},

    # Stax
    {"name": "Dauthi Voidwalker", "type_line": "Creature", "cmc": 2},

    # Egon
    {"name": "Egon, God of Death // Throne of Death", "type_line": "Legendary Creature // Legendary Artifact", "cmc": 3},

    # Monster Manual
    {"name": "Monster Manual // Zoological Study", "type_line": "Artifact // Sorcery", "cmc": 4},

    # Fanatic
    {"name": "Fanatic of Rhonas", "type_line": "Creature", "cmc": 2},

    # Lands (36)
    {"name": "Cephalid Coliseum", "type_line": "Land", "cmc": 0},
    {"name": "Command Beacon", "type_line": "Land", "cmc": 0},
    {"name": "Command Tower", "type_line": "Land", "cmc": 0},
    {"name": "Contaminated Aquifer", "type_line": "Land", "cmc": 0},
    {"name": "Crypt of Agadeem", "type_line": "Land", "cmc": 0},
    {"name": "Darkwater Catacombs", "type_line": "Land", "cmc": 0},
    {"name": "Dreamroot Cascade", "type_line": "Land", "cmc": 0},
    {"name": "Drownyard Temple", "type_line": "Land", "cmc": 0},
    {"name": "Evolving Wilds", "type_line": "Land", "cmc": 0},
    {"name": "Exotic Orchard", "type_line": "Land", "cmc": 0},
    {"name": "Fabled Passage", "type_line": "Land", "cmc": 0},
    {"name": "Fetid Pools", "type_line": "Land", "cmc": 0},
    {"name": "Foreboding Landscape", "type_line": "Land", "cmc": 0},
    {"name": "Forest", "type_line": "Basic Land", "cmc": 0},
    {"name": "Golgari Rot Farm", "type_line": "Land", "cmc": 0},
    {"name": "Haunted Mire", "type_line": "Land", "cmc": 0},
    {"name": "Hinterland Harbor", "type_line": "Land", "cmc": 0},
    {"name": "Island", "type_line": "Basic Land", "cmc": 0},
    {"name": "Llanowar Wastes", "type_line": "Land", "cmc": 0},
    {"name": "Memorial to Folly", "type_line": "Land", "cmc": 0},
    {"name": "Myriad Landscape", "type_line": "Land", "cmc": 0},
    {"name": "Opulent Palace", "type_line": "Land", "cmc": 0},
    {"name": "Sunken Hollow", "type_line": "Land", "cmc": 0},
    {"name": "Swamp", "type_line": "Basic Land", "cmc": 0},
    {"name": "Temple of Malady", "type_line": "Land", "cmc": 0},
    {"name": "Terramorphic Expanse", "type_line": "Land", "cmc": 0},
    {"name": "Woodland Cemetery", "type_line": "Land", "cmc": 0},
]

def main():
    print("=" * 80)
    print("ANALYZING USER'S TEVAL DECK")
    print("=" * 80)

    engine = RecommendationEngine()

    # Count cards
    non_land_cards = [c for c in deck_cards if 'land' not in c.get('type_line', '').lower() and c.get('board', 'mainboard') != 'commanders']
    cmcs = [c['cmc'] for c in non_land_cards if c.get('cmc', 0) > 0]
    avg_cmc = sum(cmcs) / len(cmcs) if cmcs else 0

    print(f"\nDeck Composition:")
    print(f"  Total non-land cards: {len(non_land_cards)}")
    print(f"  Average CMC: {avg_cmc:.2f}")

    # Manual count of ramp
    ramp_cards = [
        "Arcane Signet", "Deathrite Shaman", "Hedge Shredder", "Icetill Explorer",
        "Millikin", "Molt Tender", "Seton, Krosan Protector", "Skull Prophet",
        "Sol Ring", "Titans' Nest", "Wight of the Reliquary", "Will of the Sultai",
        "Fanatic of Rhonas"  # Also ramp
    ]
    print(f"  Ramp sources: {len(ramp_cards)}")

    # Manual count of removal
    removal_cards = [
        "Amphin Mutineer", "An Offer You Can't Refuse", "Counterspell",
        "Deadly Brew", "Ghost Vacuum", "Heritage Reclamation", "Into the Flood Maw",
        "Lethal Scheme", "Necromantic Selection", "Overwhelming Remorse", "Tear Asunder"
    ]
    print(f"  Removal: {len(removal_cards)}")

    print("\n" + "=" * 80)
    print("EXPECTED CONTEXTUAL ANALYSIS:")
    print("=" * 80)

    if avg_cmc < 2.5:
        curve_profile = "LOW"
        optimal_ramp = 6
    elif avg_cmc < 3.5:
        curve_profile = "MEDIUM"
        optimal_ramp = 10
    else:
        curve_profile = "HIGH"
        optimal_ramp = 14

    print(f"\nCurve Profile: {curve_profile} (avg CMC: {avg_cmc:.2f})")
    print(f"Optimal Ramp: {optimal_ramp}")
    print(f"Current Ramp: {len(ramp_cards)}")

    if len(ramp_cards) < optimal_ramp - 2:
        ramp_status = "DEFICIT - needs more ramp!"
    elif len(ramp_cards) > optimal_ramp + 2:
        ramp_status = "EXCESS - can cut some ramp"
    else:
        ramp_status = "OPTIMAL"

    print(f"Ramp Status: {ramp_status}")

    print(f"\nOptimal Removal: 8 (for midrange strategy)")
    print(f"Current Removal: {len(removal_cards)}")

    if len(removal_cards) < 6:
        removal_status = "DEFICIT"
    elif len(removal_cards) > 10:
        removal_status = "EXCESS"
    else:
        removal_status = "OPTIMAL"

    print(f"Removal Status: {removal_status}")

    print("\n" + "=" * 80)
    print("SCORING DECK CARDS (with contextual necessity):")
    print("=" * 80)

    deck_scores = engine.score_deck_cards(deck_cards, exclude_lands=True)

    print(f"\nBOTTOM 10 CARDS (Potential Cuts):\n")

    for i, card in enumerate(deck_scores[:10], 1):
        name = card['name']
        score = card.get('synergy_score', 0)
        reasons = card.get('synergy_reasons', [])

        print(f"{i}. {name}")
        print(f"   Score: {score:.1f}")
        print(f"   Type: {card.get('type_line', 'Unknown')}")

        if reasons:
            print(f"   Reasons:")
            for reason in reasons[:5]:
                print(f"      • {reason}")
        else:
            print(f"   Reasons: (none - no synergy with graveyard strategy)")
        print()

    print("=" * 80)
    print("ANALYSIS:")
    print("=" * 80)

    print(f"""
This is a graveyard/self-mill deck with:
- Average CMC: {avg_cmc:.2f} ({curve_profile} curve)
- {len(ramp_cards)} ramp sources (optimal: {optimal_ramp}) - {ramp_status}
- {len(removal_cards)} removal spells - {removal_status}

Sol Ring and Arcane Signet are showing low scores because:
1. They have ZERO synergy with the graveyard/recursion theme
2. The deck has {len(ramp_cards)} ramp sources, which is {'slightly above' if len(ramp_cards) > optimal_ramp else 'at'} optimal for a {curve_profile.lower()} curve deck
3. Contextual necessity gives them a {'small penalty' if len(ramp_cards) > optimal_ramp + 2 else 'small bonus'} based on curve needs

However, Sol Ring is almost never actually worth cutting in Commander due to its raw power.
The system is technically correct that they have low synergy, but practical deck-building
wisdom says to keep Sol Ring almost always.
""")

if __name__ == "__main__":
    main()
