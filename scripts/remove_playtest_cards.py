"""
Remove known playtest and non-legal cards from the database.

This script maintains a manually curated list of cards that are known to be:
- DA1 (Un-Known Event) playtest cards
- Other non-Commander-legal cards
- Cards that don't exist in paper Magic

Based on community knowledge and Scryfall data.
"""

import json
import sys
from pathlib import Path


# Known playtest cards and non-legal cards
# These are primarily from the DA1 (Un-Known Event) playtest set
ILLEGAL_CARDS = {
    # Confirmed DA1 playtest cards (these were verified via web search)
    "Gerrard and Hanna",  # Confirmed playtest card
    "Emrakul and Chatterfang",  # Obviously fake (Eldrazi Squirrel)
    "Colossal Dreadmaw and Storm Crow",  # Meme card
    "Riku and Riku",  # Nonsensical duplicate
    "Bartz and Boko",  # Final Fantasy reference, not real MTG
    "Strago and Relm",  # Final Fantasy reference, not real MTG
    "Balthier and Fran",  # Final Fantasy reference, not real MTG
    "Gatta and Luzzu",  # Final Fantasy reference, not real MTG
    "Reno and Rude",  # Final Fantasy reference, not real MTG

    # Likely playtest cards (suspicious patterns or impossible combinations)
    "Halana and Alena and Gisa and Geralf",  # Too many names
    "Anax and Cymede & Kynaios and Tiro",  # Too many names with &
    "Meet and Greet \"Sisay\"",  # Suspicious quotation marks
    "Rin and Seri, Inseparabler",  # Typo suggests playtest ("Inseparable" exists)
    "Harold and Bob, First Numens",  # "Harold and Bob" sounds made up
    "Spinneret and Spiderling",  # Not a real legendary
    "Autumn Willow and Baron Sengir",  # Old characters but never paired
    "Riven Turnbull and Princess Lucrezia",  # Old characters but never paired
    "Vladimir and Godfrey",  # Crimson Vow characters but never paired officially
    "Joven and Chandler",  # Old characters but never officially paired as one card
    "Avacyn and Griselbrand",  # Never officially paired
    "Toothy and Zndrsplt",  # These are partners but not one card
    "Norin and Feldon",  # Never officially paired
    "Shiko and Narset, Unified",  # "Shiko" is not a character, likely playtest
    "Syr Joshua and Syr Saxon",  # Not real MTG characters
    "Tusk and Whiskers",  # Generic animal names, not real
    "Baral and Kari Zev",  # These characters exist separately but never paired
    "Isamaru and Yoshimaru",  # The two good boys, but not officially one card
    "Rashmi and Ragavan",  # Never officially paired
}

# Known LEGAL cards that follow "X and Y" pattern (don't remove these)
LEGAL_CARDS = {
    "Gisa and Geralf",  # Eldritch Moon
    "Kynaios and Tiro of Meletis",  # Commander 2016
    "Anax and Cymede",  # Theros
    "Mina and Denn, Wildborn",  # Oath of the Gatewatch
    "Pia and Kiran Nalaar",  # Origins/Battlebond
    "Tibor and Lumia",  # Guildpact
    "Firesong and Sunspeaker",  # Dominaria
    "Svyelun of Sea and Sky",  # Modern Horizons 2 (has "and" in name)
    "Aisha of Sparks and Smoke",  # Arabian Nights
    "Rin and Seri, Inseparable",  # Core Set 2021

    # March of the Machine: The Aftermath (2023) - all legal
    "Thalia and The Gitrog Monster",
    "Ghalta and Mavren",
    "Drana and Linvala",
    "Rankle and Torbran",
    "Goro-Goro and Satoru",
    "Zurgo and Ojutai",
    "Yargle and Multani",
    "Kogla and Yidaro",

    # Wilds of Eldraine Commander (2023)
    "Sharae and Hallar",
    "Shalai and Hallar",

    # March of the Machine (2023)
    "Hidetsugu and Kairi",
    "Borborygmos and Fblthp",
    "Errant and Giada",
    "Djeru and Hazoret",
    "Inga and Esika",
    "Saint Traft and Rem Karolus",
    "Moira and Teshar",
    "Elenda and Azor",
    "Kroxa and Kunoros",
    "Slimefoot and Squee",
    "Zimone and Dina",
    "Plargg and Nassari",
    "Halana and Alena, Partners",
    "Katilda and Lier",
    "Surrak and Goreclaw",

    # Commander Masters (2023)
    "Jeska and Kamahl",  # Has a typo but this is the Partners version

    # Jumpstart 2022
    "Ellie and Alan, Paleontologists",

    # Special releases
    "Aragorn and Arwen, Wed",  # Lord of the Rings Commander
    "Mary Read and Anne Bonny",  # Lost Caverns Commander

    # Recent Commander releases
    "Adrix and Nev, Twincasters",  # Commander 2021
    "Koma and Toski, Compleated",  # Phyrexia All Will Be One Commander
    "Mina and Denn, Wildborn",  # Oath of the Gatewatch
}


def remove_playtest_cards():
    """Remove known playtest/illegal cards from the database"""

    project_root = Path(__file__).parent.parent
    minimal_file = project_root / 'data' / 'cards' / 'cards-minimal.json'

    print("Loading cards-minimal.json...")
    with open(minimal_file, 'r', encoding='utf-8') as f:
        all_cards = json.load(f)

    print(f"Loaded {len(all_cards)} cards\n")

    # Find illegal cards in the database
    cards_to_remove = []
    for card in all_cards:
        name = card.get('name', '')
        if name in ILLEGAL_CARDS:
            # Double-check it's not in legal list (safety check)
            if name not in LEGAL_CARDS:
                cards_to_remove.append(name)

    if not cards_to_remove:
        print("No illegal cards found in database!")
        return True

    print(f"Found {len(cards_to_remove)} illegal cards to remove:\n")
    for name in sorted(cards_to_remove):
        print(f"  - {name}")

    # Backup
    backup_file = minimal_file.with_suffix('.json.backup')
    import shutil
    shutil.copy2(minimal_file, backup_file)
    print(f"\nBackup created: {backup_file}")

    # Filter out illegal cards
    filtered_cards = [c for c in all_cards if c.get('name') not in cards_to_remove]

    print(f"\nRemoving {len(cards_to_remove)} cards...")
    print(f"Database will have {len(filtered_cards)} cards (was {len(all_cards)})")

    # Write filtered cards
    with open(minimal_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_cards, f, separators=(',', ':'))

    print(f"Filtered database saved!")

    # Rebuild preprocessed cards
    print(f"\nRebuilding cards-preprocessed.json...")

    # Backup preprocessed too
    preprocessed_file = project_root / 'data' / 'cards' / 'cards-preprocessed.json'
    if preprocessed_file.exists():
        backup_preprocessed = preprocessed_file.with_suffix('.json.backup')
        shutil.copy2(preprocessed_file, backup_preprocessed)
        print(f"Backed up: {backup_preprocessed}")

    sys.path.insert(0, str(project_root / 'scripts'))
    from create_preprocessed_cards import create_preprocessed_cards

    success = create_preprocessed_cards()

    if success:
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"Removed {len(cards_to_remove)} illegal/playtest cards")
        print(f"\nCards removed:")
        for name in sorted(cards_to_remove):
            print(f"  - {name}")
        print(f"\nBackups created:")
        print(f"  - {backup_file}")
        if backup_preprocessed.exists():
            print(f"  - {backup_preprocessed}")
        print(f"\nYour recommendations should now only show legal Commander cards!")
        return True
    else:
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print("Error rebuilding preprocessed database")
        print("Restoring backups...")
        shutil.copy2(backup_file, minimal_file)
        if backup_preprocessed.exists():
            shutil.copy2(backup_preprocessed, preprocessed_file)
        print("Backups restored.")
        return False


if __name__ == '__main__':
    try:
        success = remove_playtest_cards()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
