"""
Test Smart Card Replacement Analysis
"""

from src.api import local_cards
from src.analysis.replacement_analyzer import ReplacementAnalyzer


def main():
    print("=" * 60)
    print("Smart Card Replacement Analysis Test")
    print("=" * 60)

    # Load local card database
    if not local_cards.is_loaded():
        print("Loading local card database...")
        local_cards.load_local_database()
        print("✓ Local card database loaded\n")

    # Create a test deck with some weak cards
    test_cards = [
        # Good ramp
        "Sol Ring", "Arcane Signet", "Cultivate", "Kodama's Reach",
        "Farseek", "Nature's Lore", "Three Visits",
        "Llanowar Elves", "Birds of Paradise",

        # Weak cards that should be flagged for replacement
        "Manalith",  # Weak ramp (3 CMC for just mana)
        "Divination",  # Weak draw (sorcery speed, only 2 cards)
        "Naturalize",  # Weak removal (limited to artifacts/enchantments)

        # Some good cards
        "Rhystic Study", "Swords to Plowshares", "Counterspell",
        "Craterhoof Behemoth", "Avenger of Zendikar",
        "Eternal Witness", "Sun Titan",

        # Medium cards
        "Lightning Bolt", "Beast Within"
    ]

    cards = []
    print("Building test deck...")
    for card_name in test_cards:
        card = local_cards.get_card_by_name(card_name)
        if card:
            cards.append(card)
            print(f"  ✓ {card_name}")

    # Add commander
    commander = local_cards.get_card_by_name("Atraxa, Praetors' Voice")
    if commander:
        commander = dict(commander)
        commander['is_commander'] = True
        cards.insert(0, commander)
        print(f"  ✓ Commander: {commander['name']}")

    print(f"\n✓ Test deck created with {len(cards)} cards\n")

    # Create mock deck scores (simulating synergy analysis)
    deck_scores = [
        {'name': 'Manalith', 'synergy_score': 25},  # Very low
        {'name': 'Divination', 'synergy_score': 35},  # Low
        {'name': 'Naturalize', 'synergy_score': 40},  # Low
        {'name': 'Lightning Bolt', 'synergy_score': 65},  # Medium
        {'name': 'Rhystic Study', 'synergy_score': 95},  # High
        {'name': 'Swords to Plowshares', 'synergy_score': 88},  # High
    ]

    # Test replacement candidate identification
    print("=" * 60)
    print("Identifying Replacement Candidates")
    print("=" * 60)

    analyzer = ReplacementAnalyzer()
    candidates = analyzer.identify_replacement_candidates(cards, deck_scores, limit=10)

    print(f"\nFound {len(candidates)} replacement candidates:\n")

    for i, candidate in enumerate(candidates, 1):
        card_name = candidate['card']['name']
        priority = candidate['replacement_priority']
        synergy = candidate['synergy_score']
        reasons = candidate['reasons']
        suggested = candidate['suggested_role']

        priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🔵'}.get(priority, '⚪')

        print(f"{i}. {priority_icon} {card_name:<25} [{priority.upper()}]")
        print(f"   Synergy: {synergy if synergy else 'N/A'}")
        print(f"   Reasons: {', '.join(reasons)}")
        if suggested:
            print(f"   Suggested role: {suggested.replace('_', ' ').title()}")
        print()

    # Test finding replacements for a specific card
    print("=" * 60)
    print("Finding Replacements for 'Manalith'")
    print("=" * 60)

    manalith = local_cards.get_card_by_name("Manalith")
    if manalith:
        # Create pool of potential replacements
        replacement_pool_names = [
            # Better ramp options
            "Chromatic Lantern",  # Same CMC, better effect
            "Coalition Relic",  # Better mana rock
            "Worn Powerstone",  # More mana
            "Talisman of Progress",  # Cheaper
            "Signets",  # Cheaper

            # Different roles (to test matching)
            "Harmonize",  # Card draw (different role)
            "Wrath of God",  # Board wipe (different role)
        ]

        replacement_pool = []
        for name in replacement_pool_names:
            card = local_cards.get_card_by_name(name)
            if card:
                replacement_pool.append(card)

        replacements = analyzer.find_replacements(
            manalith,
            cards,
            replacement_pool,
            limit=5
        )

        print(f"\nTop {len(replacements)} replacements for Manalith:\n")

        for i, rep in enumerate(replacements, 1):
            card_name = rep['card']['name']
            cmc = rep['card'].get('cmc', 0)
            type_match = "✓" if rep['type_match'] else "✗"
            cmc_diff = rep['cmc_diff']
            score_change = rep['net_impact']['score_change']
            match_score = rep['match_score']

            print(f"{i}. {card_name:<25} (CMC {cmc})")
            print(f"   Type Match: {type_match} | CMC Diff: {cmc_diff} | Match Score: {match_score:.1f}")
            print(f"   Net Impact: {score_change:+d} score ({rep['net_impact']['before_score']} → {rep['net_impact']['after_score']})")

            if rep['net_impact']['weaknesses_addressed']:
                print(f"   Weaknesses Fixed:")
                for w in rep['net_impact']['weaknesses_addressed']:
                    print(f"      • {w['message']}")

            print(f"   Summary: {analyzer.get_replacement_summary(rep)}")
            print()

    # Test finding replacements for a draw spell
    print("=" * 60)
    print("Finding Replacements for 'Divination'")
    print("=" * 60)

    divination = local_cards.get_card_by_name("Divination")
    if divination:
        # Better draw spells
        draw_pool_names = [
            "Mystic Remora",  # Much better
            "Fact or Fiction",  # Better instant speed
            "Night's Whisper",  # Cheaper
            "Read the Bones",  # Scry
            "Sign in Blood",  # Cheaper
        ]

        draw_pool = []
        for name in draw_pool_names:
            card = local_cards.get_card_by_name(name)
            if card:
                draw_pool.append(card)

        replacements = analyzer.find_replacements(
            divination,
            cards,
            draw_pool,
            limit=5
        )

        print(f"\nTop {len(replacements)} replacements for Divination:\n")

        for i, rep in enumerate(replacements, 1):
            card_name = rep['card']['name']
            print(f"{i}. {card_name}")
            print(f"   {analyzer.get_replacement_summary(rep)}")
            print()

    print("=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
