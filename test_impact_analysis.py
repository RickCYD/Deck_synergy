"""
Test Recommendation Impact Analysis
"""

from src.api import local_cards
from src.analysis.impact_analyzer import RecommendationImpactAnalyzer


def main():
    print("=" * 60)
    print("Recommendation Impact Analysis Test")
    print("=" * 60)

    # Load local card database
    if not local_cards.is_loaded():
        print("Loading local card database...")
        local_cards.load_local_database()
        print("✓ Local card database loaded\n")

    # Create a test deck with known weaknesses
    test_cards = [
        "Sol Ring", "Arcane Signet", "Cultivate", "Kodama's Reach",
        "Farseek", "Nature's Lore", "Three Visits", "Rampant Growth",
        "Llanowar Elves", "Birds of Paradise", "Noble Hierarch",
        # Lots of ramp (11 cards), but weak on removal and draw
        "Lightning Bolt", "Swords to Plowshares",  # Only 2 removal
        "Rhystic Study",  # Only 1 card draw
        "Craterhoof Behemoth", "Avenger of Zendikar",  # 2 threats
        "Eternal Witness", "Sun Titan"  # 2 utility
    ]

    cards = []
    print("Building test deck...")
    for card_name in test_cards:
        card = local_cards.get_card_by_name(card_name)
        if card:
            cards.append(card)

    # Add commander
    commander = local_cards.get_card_by_name("Atraxa, Praetors' Voice")
    if commander:
        commander = dict(commander)
        commander['is_commander'] = True
        cards.insert(0, commander)

    print(f"✓ Test deck created with {len(cards)} cards\n")

    # Test recommendations with different impact levels
    test_recommendations = [
        "Counterspell",  # Should have high impact (addresses protection weakness)
        "Wrath of God",  # Should have high impact (addresses board wipe weakness)
        "Mystic Remora",  # Should have high impact (addresses card draw weakness)
        "Beast Within",  # Should have medium impact (more removal)
        "Mana Vault",  # Should have low impact (already have lots of ramp)
        "Chromatic Lantern"  # Should have low impact (more ramp)
    ]

    # Analyze impact
    print("=" * 60)
    print("Analyzing Recommendation Impacts")
    print("=" * 60)

    analyzer = RecommendationImpactAnalyzer()

    for rec_name in test_recommendations:
        rec_card = local_cards.get_card_by_name(rec_name)
        if not rec_card:
            print(f"\n✗ Card not found: {rec_name}")
            continue

        print(f"\n{'─' * 60}")
        print(f"📝 {rec_name}")
        print(f"{'─' * 60}")

        impact = analyzer.analyze_card_impact(rec_card, cards)

        # Display impact details
        print(f"\n{analyzer.get_impact_icon(impact['impact_rating'])} Impact Rating: {impact['impact_rating'].upper()}")
        print(f"   Score Change: {impact['before_score']} → {impact['after_score']} ({impact['score_change']:+d})")

        if impact['roles_filled']:
            roles_text = ', '.join(r.replace('_', ' ').title() for r in impact['roles_filled'])
            print(f"   Roles Filled: {roles_text}")

        if impact['weaknesses_addressed']:
            print(f"\n   ⚠️  Weaknesses Addressed:")
            for w in impact['weaknesses_addressed']:
                resolved_text = " (RESOLVED!)" if w['resolved'] else ""
                print(f"      • [{w['severity'].upper()}] {w['improvement']}{resolved_text}")

        if impact['role_changes']:
            print(f"\n   📊 Role Changes:")
            for role, change in impact['role_changes'].items():
                status_change = ""
                if change['status_before'] != change['status_after']:
                    status_change = f" ({change['status_before']} → {change['status_after']})"

                print(f"      • {role.replace('_', ' ').title()}: {change['before']} → {change['after']}{status_change}")

        print(f"\n   💬 Summary: {analyzer.get_impact_summary_text(impact)}")

    # Test batch analysis
    print(f"\n\n{'=' * 60}")
    print("Testing Batch Analysis")
    print("=" * 60)

    recommendations = [local_cards.get_card_by_name(name) for name in test_recommendations if local_cards.get_card_by_name(name)]

    sorted_recs = analyzer.analyze_batch_recommendations(recommendations, cards)

    print("\nRecommendations sorted by impact:\n")
    for i, rec in enumerate(sorted_recs, 1):
        impact = rec.get('impact_analysis', {})
        rating = impact.get('impact_rating', 'unknown')
        score_change = impact.get('score_change', 0)
        icon = analyzer.get_impact_icon(rating)

        print(f"{i}. {icon} {rec['name']:<25} [{rating.upper()}] ({score_change:+d} score)")

    print(f"\n{'=' * 60}")
    print("✅ Test Complete!")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
