#!/usr/bin/env python3
"""
Find Sol Ring and Arcane Signet in the deck scoring
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.recommendations import RecommendationEngine

# User's deck (abbreviated - just need the key cards)
deck_cards = [
    {"name": "Teval, the Balanced Scale", "type_line": "Legendary Creature", "cmc": 3, "board": "commanders"},
    {"name": "Gossip's Talent", "type_line": "Enchantment", "cmc": 2},
    {"name": "Siegfried, Famed Swordsman", "type_line": "Legendary Creature", "cmc": 3},
    {"name": "Diregraf Captain", "type_line": "Creature", "cmc": 2},
    {"name": "Ob Nixilis, the Fallen", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Syr Konrad, the Grim", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Disciple of Bolas", "type_line": "Creature", "cmc": 4},
    {"name": "Frantic Search", "type_line": "Instant", "cmc": 3},
    {"name": "Kindred Discovery", "type_line": "Enchantment", "cmc": 4},
    {"name": "Kishla Skimmer", "type_line": "Creature", "cmc": 2},
    {"name": "Priest of Forgotten Gods", "type_line": "Creature", "cmc": 2},
    {"name": "Tatyova, Benthic Druid", "type_line": "Legendary Creature", "cmc": 5},
    {"name": "Teval's Judgment", "type_line": "Instant", "cmc": 2},
    {"name": "Treasure Cruise", "type_line": "Sorcery", "cmc": 8},
    {"name": "Welcome the Dead", "type_line": "Instant", "cmc": 4},
    {"name": "Eldrazi Monument", "type_line": "Artifact", "cmc": 5},
    {"name": "Living Death", "type_line": "Sorcery", "cmc": 5},
    {"name": "Wonder", "type_line": "Creature", "cmc": 4},
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
    {"name": "Dauthi Voidwalker", "type_line": "Creature", "cmc": 2},
    {"name": "Egon, God of Death // Throne of Death", "type_line": "Legendary Creature // Legendary Artifact", "cmc": 3},
    {"name": "Monster Manual // Zoological Study", "type_line": "Artifact // Sorcery", "cmc": 4},
    {"name": "Fanatic of Rhonas", "type_line": "Creature", "cmc": 2},
]

def main():
    print("=" * 80)
    print("FINDING SOL RING AND ARCANE SIGNET IN DECK SCORES")
    print("=" * 80)

    engine = RecommendationEngine()
    deck_scores = engine.score_deck_cards(deck_cards, exclude_lands=True)

    # Find Sol Ring and Arcane Signet
    for i, card in enumerate(deck_scores, 1):
        if card['name'] in ['Sol Ring', 'Arcane Signet']:
            print(f"\n{i}. {card['name']}")
            print(f"   Score: {card.get('synergy_score', 0):.1f}")
            print(f"   Type: {card.get('type_line', 'Unknown')}")
            reasons = card.get('synergy_reasons', [])
            if reasons:
                print(f"   Explanations:")
                for reason in reasons:
                    print(f"      • {reason}")
            else:
                print(f"   Explanations: None")

    print("\n" + "=" * 80)
    print("FULL BOTTOM 20 RANKINGS:")
    print("=" * 80)

    for i, card in enumerate(deck_scores[:20], 1):
        name = card['name']
        score = card.get('synergy_score', 0)
        is_ramp = '🔸 RAMP' if name in ['Sol Ring', 'Arcane Signet', 'Deathrite Shaman', 'Hedge Shredder',
                                         'Icetill Explorer', 'Millikin', 'Molt Tender', 'Seton, Krosan Protector',
                                         'Skull Prophet', 'Titans\' Nest', 'Wight of the Reliquary', 'Will of the Sultai',
                                         'Fanatic of Rhonas'] else ''
        print(f"{i:2d}. {name:40s} {score:6.1f}  {is_ramp}")

if __name__ == "__main__":
    main()
