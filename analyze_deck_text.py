#!/usr/bin/env python3
"""
Quick Deck Analyzer - Parse and analyze a deck from text format
Works around Archidekt API access issues
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.models.deck import Deck
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.analysis.weakness_detector import DeckWeaknessAnalyzer
import sys
import re

# Load the local card database
print("Loading card database...")
if not load_local_database():
    print("ERROR: Could not load card database")
    sys.exit(1)
print()


def parse_deck_text(deck_text):
    """Parse deck from text format (Archidekt export or similar)"""
    lines = deck_text.strip().split('\n')
    cards = []
    commander = None

    # Common category headers to skip
    category_headers = {
        'commander', 'anthem', 'artifact', 'burn', 'copy', 'creature', 'draw',
        'evasion', 'finisher', 'instant', 'land', 'lifegain', 'protection',
        'pump', 'ramp', 'recursion', 'removal', 'sorcery', 'tokens',
        'enchantment', 'planeswalker', 'utility', 'tribal', 'combo'
    }

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Skip category headers (lines with no number prefix)
        if not re.match(r'^\d+', line):
            # Check if it's a category header
            if line.lower() in category_headers:
                continue

        # Match patterns like:
        # "1 Card Name"
        # "1x Card Name"
        # "Card Name"
        match = re.match(r'(\d+)x?\s+(.+)', line)
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2).strip()

            # Get card data
            card = get_card_by_name(card_name)
            if card:
                # Mark commander
                if not commander and 'commander' in deck_text.lower():
                    # Look for commander in earlier lines
                    pass
                if quantity == 1 and not cards:  # First card
                    commander = card_name
                    card['is_commander'] = True

                for _ in range(quantity):
                    cards.append(card)
            else:
                # Only warn if it's not a category header
                if card_name.lower() not in category_headers:
                    print(f"Warning: Could not find card '{card_name}'")

    return cards, commander


def analyze_deck_from_text(deck_text, deck_name="Imported Deck"):
    """Analyze a deck from text format"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {deck_name}")
    print(f"{'='*70}\n")

    # Parse deck
    cards, commander = parse_deck_text(deck_text)

    if not cards:
        print("Error: No cards found in deck list")
        return

    print(f"✓ Loaded {len(cards)} cards")
    if commander:
        print(f"✓ Commander: {commander}")

    # Create Deck object
    deck = Deck(deck_id='text_import', name=deck_name, cards=cards)

    # Analyze synergies
    print("\n" + "="*70)
    print("SYNERGY ANALYSIS")
    print("="*70)

    synergy_results = analyze_deck_synergies(cards, run_simulation=False)  # Don't run simulation by default

    # Extract synergy list from results
    if isinstance(synergy_results, dict):
        two_way_synergies = synergy_results.get('two_way', {})
        synergies_list = list(two_way_synergies.values()) if two_way_synergies else []
    else:
        synergies_list = []

    if synergies_list:
        print(f"\n✓ Found {len(synergies_list)} synergies")

        # Show top synergies
        sorted_synergies = sorted(synergies_list, key=lambda x: x.get('strength', 0), reverse=True)

        print("\n🔥 Top 10 Synergies:")
        for i, syn in enumerate(sorted_synergies[:10], 1):
            strength = syn.get('strength', 0)
            category = syn.get('category', 'unknown')
            description = syn.get('description', 'No description')
            print(f"\n{i}. {syn.get('name', 'Unknown')} [Strength: {strength:.1f}]")
            print(f"   Category: {category}")
            print(f"   {description}")
    else:
        print("\n⚠️ No strong synergies detected")

    # Detect weaknesses
    print("\n" + "="*70)
    print("WEAKNESS ANALYSIS")
    print("="*70)

    try:
        analyzer = DeckWeaknessAnalyzer()
        weakness_analysis = analyzer.analyze_deck(cards)

        if weakness_analysis.get('weaknesses'):
            print(f"\n⚠️ Found {len(weakness_analysis['weaknesses'])} potential weaknesses:\n")
            for weakness in weakness_analysis['weaknesses']:
                print(f"• {weakness.get('role', 'Unknown')}: {weakness.get('description', '')}")

        # Show role distribution
        print("\n📊 Role Distribution:")
        role_dist = weakness_analysis.get('role_distribution', {})
        for role, count in sorted(role_dist.items()):
            status = "✓" if count >= 8 else "⚠️"
            print(f"  {status} {role.replace('_', ' ').title()}: {count}")

        # Show suggestions
        if weakness_analysis.get('suggestions'):
            print("\n💡 Suggestions:")
            for suggestion in weakness_analysis['suggestions'][:5]:
                print(f"  • {suggestion}")
    except Exception as e:
        print(f"\n⚠️ Could not analyze weaknesses: {e}")
        import traceback
        traceback.print_exc()

    # Basic stats
    print("\n" + "="*70)
    print("DECK STATISTICS")
    print("="*70)

    # Count card types
    creatures = sum(1 for c in cards if 'Creature' in c.get('type_line', ''))
    instants = sum(1 for c in cards if 'Instant' in c.get('type_line', ''))
    sorceries = sum(1 for c in cards if 'Sorcery' in c.get('type_line', ''))
    enchantments = sum(1 for c in cards if 'Enchantment' in c.get('type_line', ''))
    artifacts = sum(1 for c in cards if 'Artifact' in c.get('type_line', ''))
    planeswalkers = sum(1 for c in cards if 'Planeswalker' in c.get('type_line', ''))
    lands = sum(1 for c in cards if 'Land' in c.get('type_line', ''))

    print(f"\nCard Types:")
    print(f"  Lands: {lands}")
    print(f"  Creatures: {creatures}")
    print(f"  Instants: {instants}")
    print(f"  Sorceries: {sorceries}")
    print(f"  Enchantments: {enchantments}")
    print(f"  Artifacts: {artifacts}")
    print(f"  Planeswalkers: {planeswalkers}")

    # Mana curve
    print(f"\nMana Curve:")
    cmc_counts = {}
    for card in cards:
        if 'Land' not in card.get('type_line', ''):
            cmc = card.get('cmc', 0)
            cmc_counts[cmc] = cmc_counts.get(cmc, 0) + 1

    for cmc in sorted(cmc_counts.keys()):
        if cmc <= 7:
            bar = '█' * cmc_counts[cmc]
            print(f"  {int(cmc)}: {bar} ({cmc_counts[cmc]})")

    print("\n" + "="*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            deck_text = f.read()
        analyze_deck_from_text(deck_text, sys.argv[1])
    else:
        print("Usage:")
        print("  python analyze_deck_text.py decklist.txt")
        print("\nOr use interactively:")
        print("  python -c 'from analyze_deck_text import analyze_deck_from_text; analyze_deck_from_text(\"\"\"<paste deck here>\"\"\")'")
