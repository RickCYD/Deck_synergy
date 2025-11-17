#!/usr/bin/env python3
"""
Quick Deck Analyzer - Parse and analyze a deck from text format
Works around Archidekt API access issues
"""

from src.api.local_cards import get_card_by_name
from src.models.deck import Deck
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.analysis.weakness_detector import detect_weaknesses
import sys
import re


def parse_deck_text(deck_text):
    """Parse deck from text format (Archidekt export or similar)"""
    lines = deck_text.strip().split('\n')
    cards = []
    commander = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Match patterns like:
        # "1 Card Name"
        # "1x Card Name"
        # "Card Name"
        match = re.match(r'(\d+)x?\s+(.+)', line)
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2).strip()
        else:
            quantity = 1
            card_name = line.strip()

        # Get card data
        card = get_card_by_name(card_name)
        if card:
            # First card is often commander in exports
            if not commander and quantity == 1:
                commander = card_name
                card['is_commander'] = True

            for _ in range(quantity):
                cards.append(card)
        else:
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
    deck = Deck(cards=cards, commander=commander, name=deck_name)

    # Analyze synergies
    print("\n" + "="*70)
    print("SYNERGY ANALYSIS")
    print("="*70)

    synergies = analyze_deck_synergies(deck)

    if synergies:
        print(f"\n✓ Found {len(synergies)} synergies")

        # Show top synergies
        sorted_synergies = sorted(synergies, key=lambda x: x.get('strength', 0), reverse=True)

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
        weaknesses = detect_weaknesses(deck)
        if weaknesses:
            print(f"\n⚠️ Found {len(weaknesses)} potential weaknesses:\n")
            for weakness in weaknesses:
                print(f"• {weakness.get('type', 'Unknown')}: {weakness.get('description', '')}")
                if 'suggestion' in weakness:
                    print(f"  Suggestion: {weakness.get('suggestion')}")
        else:
            print("\n✓ No major weaknesses detected")
    except Exception as e:
        print(f"\n⚠️ Could not analyze weaknesses: {e}")

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
