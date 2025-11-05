"""
Temporary patch to remove cards without legalities data from existing databases.

This script filters out cards that don't have legalities information in cards-minimal.json
and rebuilds cards-preprocessed.json without those cards.

For a proper fix, download fresh oracle-cards.json and rebuild:
1. Download from: https://scryfall.com/docs/api/bulk-data
2. Run: python scripts/create_minimal_cards.py
3. Run: python scripts/create_preprocessed_cards.py
"""

import json
import sys
from pathlib import Path


def patch_databases():
    """Remove cards without legalities data"""

    project_root = Path(__file__).parent.parent
    minimal_file = project_root / 'data' / 'cards' / 'cards-minimal.json'
    preprocessed_file = project_root / 'data' / 'cards' / 'cards-preprocessed.json'

    print("Loading cards-minimal.json...")
    with open(minimal_file, 'r', encoding='utf-8') as f:
        minimal_cards = json.load(f)

    print(f"Loaded {len(minimal_cards)} cards")

    # Filter out cards without legalities data
    # (These are likely from an incomplete/old data source)
    cards_without_legalities = []
    filtered_cards = []

    for card in minimal_cards:
        legalities = card.get('legalities', {})

        # If card has no legalities data at all, it's suspect
        if not legalities:
            cards_without_legalities.append(card.get('name'))
        else:
            filtered_cards.append(card)

    print(f"\nFound {len(cards_without_legalities)} cards without legalities data")

    if cards_without_legalities:
        print("\nSample cards being removed (first 20):")
        for name in cards_without_legalities[:20]:
            print(f"  - {name}")

    # Backup original files
    print(f"\nBacking up original files...")
    backup_minimal = minimal_file.with_suffix('.json.backup')
    backup_preprocessed = preprocessed_file.with_suffix('.json.backup')

    import shutil
    shutil.copy2(minimal_file, backup_minimal)
    print(f"  Backed up: {backup_minimal}")

    if preprocessed_file.exists():
        shutil.copy2(preprocessed_file, backup_preprocessed)
        print(f"  Backed up: {backup_preprocessed}")

    # Write filtered minimal cards
    print(f"\nWriting filtered cards-minimal.json...")
    with open(minimal_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_cards, f, separators=(',', ':'))

    print(f"  Kept {len(filtered_cards)} cards with legalities data")

    # Now rebuild preprocessed cards using the updated script
    print(f"\nRebuilding cards-preprocessed.json...")
    sys.path.insert(0, str(project_root / 'scripts'))

    from create_preprocessed_cards import create_preprocessed_cards

    success = create_preprocessed_cards()

    if success:
        print("\n✅ Patch completed successfully!")
        print(f"\nBackup files created:")
        print(f"  - {backup_minimal}")
        print(f"  - {backup_preprocessed}")
        print(f"\nRemoved {len(cards_without_legalities)} cards without legalities data")
        print(f"\nFor a permanent fix, download fresh oracle-cards.json:")
        print(f"  1. Visit: https://scryfall.com/docs/api/bulk-data")
        print(f"  2. Download 'Oracle Cards' JSON")
        print(f"  3. Save to: {project_root / 'data' / 'cards' / 'oracle-cards.json'}")
        print(f"  4. Run: python scripts/create_minimal_cards.py")
        print(f"  5. Run: python scripts/create_preprocessed_cards.py")
    else:
        print("\n❌ Error during preprocessing!")
        print("Restoring backups...")
        shutil.copy2(backup_minimal, minimal_file)
        if backup_preprocessed.exists():
            shutil.copy2(backup_preprocessed, preprocessed_file)
        print("Backups restored.")
        return False

    return True


if __name__ == '__main__':
    success = patch_databases()
    sys.exit(0 if success else 1)
