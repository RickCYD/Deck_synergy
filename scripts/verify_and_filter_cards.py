"""
Verify card legalities by checking Scryfall API for suspicious cards.

Since we can't download the full oracle-cards.json, this script:
1. Identifies potentially illegal cards using heuristics
2. Queries Scryfall API to check their Commander legality
3. Removes non-legal cards from the database
4. Rebuilds the preprocessed database
"""

import json
import time
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error


def check_card_legality(card_name):
    """
    Check if a card is legal in Commander using Scryfall API.

    Returns: 'legal', 'restricted', 'banned', 'not_legal', or 'error'
    """
    try:
        # URL encode the card name
        encoded_name = urllib.parse.quote(card_name)
        url = f"https://api.scryfall.com/cards/named?exact={encoded_name}"

        # Add headers
        headers = {
            'User-Agent': 'DeckSynergy/1.0 (Card Legality Checker)',
            'Accept': 'application/json'
        }

        req = urllib.request.Request(url, headers=headers)

        # Respect Scryfall's rate limit (100ms between requests)
        time.sleep(0.1)

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            legalities = data.get('legalities', {})
            commander_legal = legalities.get('commander', 'not_legal')
            set_code = data.get('set', 'unknown')

            return {
                'legality': commander_legal,
                'set': set_code,
                'set_name': data.get('set_name', 'Unknown')
            }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Card doesn't exist
            return {'legality': 'not_legal', 'set': 'not_found', 'set_name': 'Card Not Found'}
        else:
            print(f"  HTTP Error {e.code} for {card_name}")
            return {'legality': 'error', 'set': 'error', 'set_name': 'Error'}

    except Exception as e:
        print(f"  Error checking {card_name}: {e}")
        return {'legality': 'error', 'set': 'error', 'set_name': 'Error'}


def identify_suspicious_cards(cards):
    """
    Identify cards that might be playtest/illegal cards using heuristics.
    """
    suspicious = []

    for card in cards:
        name = card.get('name', '')
        type_line = card.get('type_line', '')

        # Heuristic 1: Legendary creatures with "and" connecting two names
        # (Some are legal, but DA1 playtest cards follow this pattern)
        if ' and ' in name and 'Legendary Creature' in type_line:
            # Known legal patterns to exclude from checking
            known_legal = [
                'Gisa and Geralf',
                'Kynaios and Tiro',
                'Mina and Denn',
                'Anax and Cymede',
                'Kynaios and Tiro of Meletis',
                'Rin and Seri, Inseparable',
                'Thalia and The Gitrog Monster',
                'Adrix and Nev, Twincasters',
                'Inga and Esika',
                'Saint Traft and Rem Karolus'
            ]

            # Only check if not in known legal list
            if name not in known_legal:
                suspicious.append(card)
                continue

    return suspicious


def filter_illegal_cards():
    """Main function to filter out illegal cards"""

    project_root = Path(__file__).parent.parent
    minimal_file = project_root / 'data' / 'cards' / 'cards-minimal.json'

    print("Loading cards-minimal.json...")
    with open(minimal_file, 'r', encoding='utf-8') as f:
        all_cards = json.load(f)

    print(f"Loaded {len(all_cards)} cards\n")

    # Identify suspicious cards
    print("Identifying potentially illegal cards...")
    suspicious_cards = identify_suspicious_cards(all_cards)

    print(f"Found {len(suspicious_cards)} suspicious cards to verify\n")

    if not suspicious_cards:
        print("No suspicious cards found!")
        return True

    # Check each suspicious card
    print("Checking legality with Scryfall API...")
    print("(This may take a while due to rate limiting)\n")

    illegal_cards = []
    legal_cards = []
    error_cards = []

    for idx, card in enumerate(suspicious_cards, 1):
        name = card.get('name')
        print(f"[{idx}/{len(suspicious_cards)}] Checking: {name}")

        result = check_card_legality(name)
        legality = result['legality']
        set_info = result['set']
        set_name = result['set_name']

        if legality in ['legal', 'restricted']:
            print(f"  ✓ LEGAL - {set_name} ({set_info})")
            legal_cards.append(name)
        elif legality == 'error':
            print(f"  ? ERROR - Unable to verify")
            error_cards.append(name)
        else:
            print(f"  ✗ NOT LEGAL - {set_name} ({set_info}) - Status: {legality}")
            illegal_cards.append(name)

    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"Legal cards:    {len(legal_cards)}")
    print(f"Illegal cards:  {len(illegal_cards)}")
    print(f"Errors:         {len(error_cards)}")

    if illegal_cards:
        print(f"\nIllegal cards to be removed:")
        for name in illegal_cards:
            print(f"  - {name}")

    if error_cards:
        print(f"\nCards with errors (keeping for safety):")
        for name in error_cards:
            print(f"  - {name}")

    # Remove illegal cards
    if illegal_cards:
        print(f"\nRemoving {len(illegal_cards)} illegal cards...")

        # Backup
        backup_file = minimal_file.with_suffix('.json.backup')
        import shutil
        shutil.copy2(minimal_file, backup_file)
        print(f"Backup created: {backup_file}")

        # Filter out illegal cards
        filtered_cards = [c for c in all_cards if c.get('name') not in illegal_cards]

        # Write filtered cards
        with open(minimal_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_cards, f, separators=(',', ':'))

        print(f"Filtered database saved: {len(filtered_cards)} cards")

        # Rebuild preprocessed cards
        print(f"\nRebuilding cards-preprocessed.json...")
        sys.path.insert(0, str(project_root / 'scripts'))
        from create_preprocessed_cards import create_preprocessed_cards

        success = create_preprocessed_cards()

        if success:
            print("\n✅ Successfully removed illegal cards and rebuilt database!")
            return True
        else:
            print("\n❌ Error rebuilding preprocessed database")
            print("Restoring backup...")
            shutil.copy2(backup_file, minimal_file)
            return False
    else:
        print("\nNo illegal cards found - database is clean!")
        return True


if __name__ == '__main__':
    try:
        success = filter_illegal_cards()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
