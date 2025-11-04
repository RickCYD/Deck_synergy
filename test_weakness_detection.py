"""
Test Deck Weakness Detection
"""

from src.api import local_cards
from src.analysis.weakness_detector import DeckWeaknessAnalyzer


def main():
    print("=" * 60)
    print("Deck Weakness Detection Test")
    print("=" * 60)

    # Load local card database
    if not local_cards.is_loaded():
        print("Loading local card database...")
        local_cards.load_local_database()
        print(f"✓ Local card database loaded")

    # Create a test deck with imbalanced composition
    test_cards = [
        "Sol Ring", "Arcane Signet", "Command Tower", "Cultivate", "Kodama's Reach",
        "Farseek", "Nature's Lore", "Three Visits", "Rampant Growth", "Skyshroud Claim",
        "Llanowar Elves", "Birds of Paradise", "Noble Hierarch", "Fyndhorn Elves", "Elvish Mystic",
        # Lots of ramp, but missing removal and card draw
        "Lightning Bolt", "Swords to Plowshares",  # Only 2 removal
        "Rhystic Study",  # Only 1 card draw
        # Add some threats
        "Craterhoof Behemoth", "Avenger of Zendikar", "Consecrated Sphinx", "Hullbreaker Horror",
        # Add utility
        "Eternal Witness", "Sun Titan", "Solemn Simulacrum"
    ]

    cards = []
    print("\nFetching test cards...")
    for card_name in test_cards:
        card = local_cards.get_card_by_name(card_name)
        if card:
            cards.append(card)
            print(f"  ✓ {card_name}")
        else:
            print(f"  ✗ {card_name} (not found)")

    # Add a commander
    commander = local_cards.get_card_by_name("Atraxa, Praetors' Voice")
    if commander:
        commander = dict(commander)
        commander['is_commander'] = True
        cards.insert(0, commander)
        print(f"  ✓ Commander: {commander['name']}")

    print(f"\n✓ Test deck created with {len(cards)} cards\n")

    # Analyze deck
    print("=" * 60)
    print("Running Weakness Analysis...")
    print("=" * 60)

    analyzer = DeckWeaknessAnalyzer()
    analysis = analyzer.analyze_deck(cards)

    # Display results
    print(f"\n{'='*60}")
    print(f"OVERALL SCORE: {analysis['overall_score']}/100")
    print(f"{'='*60}\n")

    print("ROLE DISTRIBUTION:")
    print("-" * 60)
    for role, data in sorted(analysis['role_distribution'].items(), key=lambda x: x[1]['count'], reverse=True):
        count = data['count']
        status = data['status']
        ranges = analyzer.RECOMMENDED_RANGES[role]
        status_symbol = {
            'critical': '🔴',
            'low': '🟡',
            'good': '🟢',
            'high': '🔵'
        }.get(status, '⚪')

        print(f"{status_symbol} {role.replace('_', ' ').title():<20} {count:>3} cards  (recommended: {ranges['min']}-{ranges['max']}, ideal: {ranges['ideal']})")
        if data['cards']:
            print(f"   Cards: {', '.join(data['cards'][:5])}{' ...' if len(data['cards']) > 5 else ''}")

    if analysis['weaknesses']:
        print(f"\n{'='*60}")
        print("⚠️  WEAKNESSES:")
        print("-" * 60)
        for weakness in analysis['weaknesses']:
            severity_symbol = {
                'high': '🔴 HIGH',
                'medium': '🟡 MEDIUM',
                'low': '⚪ LOW'
            }.get(weakness['severity'], '⚪')

            print(f"{severity_symbol:>12} | {weakness['message']}")

    if analysis['suggestions']:
        print(f"\n{'='*60}")
        print("💡 SUGGESTIONS:")
        print("-" * 60)
        for i, suggestion in enumerate(analysis['suggestions'], 1):
            print(f"{i}. {suggestion}")

    print(f"\n{'='*60}")
    print("✅ Test Complete!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
