"""
Generate cards-minimal.json from oracle-cards.json

This script extracts only the fields needed for synergy detection, role assignment,
and graph visualization from the full Scryfall oracle database.

Reduces file size from 157MB to ~17MB (89% reduction).
"""

import json
import os
from pathlib import Path


def create_minimal_cards():
    """Extract minimal fields from oracle-cards.json"""

    # Paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / 'data' / 'cards' / 'oracle-cards.json'
    output_file = project_root / 'data' / 'cards' / 'cards-minimal.json'

    if not input_file.exists():
        print(f"Error: {input_file} not found!")
        print("Please download oracle-cards.json from Scryfall:")
        print("https://scryfall.com/docs/api/bulk-data")
        return False

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        full_cards = json.load(f)

    print(f"Loaded {len(full_cards)} cards")
    print("Extracting minimal fields...")

    # Extract only fields needed for:
    # - Synergy detection (oracle_text, type_line, keywords, etc.)
    # - Role assignment (oracle_text, type_line, mana_cost, etc.)
    # - Graph visualization (name, image_uris)
    # - Format legality validation (legalities)
    minimal_cards = []
    for card in full_cards:
        minimal = {
            # Core identification
            'name': card.get('name'),

            # Game mechanics (needed for synergies & roles)
            'oracle_text': card.get('oracle_text', ''),
            'type_line': card.get('type_line', ''),
            'mana_cost': card.get('mana_cost', ''),
            'cmc': card.get('cmc', 0),
            'colors': card.get('colors', []),
            'color_identity': card.get('color_identity', []),
            'keywords': card.get('keywords', []),

            # Stats (for creatures/planeswalkers)
            'power': card.get('power'),
            'toughness': card.get('toughness'),
            'loyalty': card.get('loyalty'),

            # Mana production (for ramp detection)
            'produced_mana': card.get('produced_mana', []),

            # Format legality (needed to filter non-Commander legal cards)
            'legalities': card.get('legalities', {}),

            # Visualization (for graph display and card preview)
            # Include all image formats: normal (full card), large, png, art_crop, border_crop, small
            'image_uris': card.get('image_uris', {})
        }
        minimal_cards.append(minimal)

    print(f"Writing to {output_file}...")
    # Use compact JSON formatting to reduce file size
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(minimal_cards, f, separators=(',', ':'))

    # Report file sizes
    input_size = input_file.stat().st_size / (1024 * 1024)  # MB
    output_size = output_file.stat().st_size / (1024 * 1024)  # MB
    reduction = (1 - output_size / input_size) * 100

    print("\n✅ Success!")
    print(f"Input:  {input_size:.1f} MB")
    print(f"Output: {output_size:.1f} MB")
    print(f"Reduction: {reduction:.1f}%")
    print(f"\nMinimal cards database created at:")
    print(f"{output_file}")

    return True


if __name__ == '__main__':
    success = create_minimal_cards()
    exit(0 if success else 1)
