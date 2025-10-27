"""
Test suite for board wipe extractors
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.utils.boardwipe_extractors import (
    extract_creature_wipes,
    extract_artifact_enchantment_wipes,
    extract_land_wipes,
    extract_token_wipes,
    extract_permanent_wipes,
    classify_board_wipe,
    get_wipe_severity
)


def test_creature_wipes():
    """Test creature board wipe extraction"""
    print("=" * 60)
    print("TESTING CREATURE BOARD WIPES")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Wrath of God',
            'oracle_text': 'Destroy all creatures. They can\'t be regenerated.'
        },
        {
            'name': 'Day of Judgment',
            'oracle_text': 'Destroy all creatures.'
        },
        {
            'name': 'Blasphemous Act',
            'oracle_text': 'This spell costs {1} less to cast for each creature on the battlefield. Blasphemous Act deals 13 damage to each creature.'
        },
        {
            'name': 'Toxic Deluge',
            'oracle_text': 'As an additional cost to cast this spell, pay X life. All creatures get -X/-X until end of turn.'
        },
        {
            'name': 'Cyclonic Rift',
            'oracle_text': 'Return target nonland permanent you don\'t control to its owner\'s hand. Overload {6}{U} (You may cast this spell for its overload cost. If you do, change "target" in its text to "each.")'
        },
        {
            'name': 'Terminus',
            'oracle_text': 'Put all creatures on the bottom of their owners\' libraries.'
        },
        {
            'name': 'Austere Command',
            'oracle_text': 'Choose two — • Destroy all artifacts. • Destroy all enchantments. • Destroy all creatures with mana value 3 or less. • Destroy all creatures with mana value 4 or greater.'
        }
    ]

    for card in test_cards:
        wipes = extract_creature_wipes(card)
        print(f"\n{card['name']}:")
        if wipes:
            for wipe in wipes:
                symmetry = "ONE-SIDED" if wipe['is_one_sided'] else "SYMMETRICAL"
                print(f"  ✓ {wipe['method'].upper()} | {wipe['scope']} | {symmetry}")
                print(f"     {wipe['description']}")
        else:
            print("  ✗ No creature wipes detected")

    print()


def test_artifact_enchantment_wipes():
    """Test artifact and enchantment wipe extraction"""
    print("=" * 60)
    print("TESTING ARTIFACT & ENCHANTMENT WIPES")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Vandalblast',
            'oracle_text': 'Destroy target artifact. Overload {4}{R} (You may cast this spell for its overload cost. If you do, destroy all artifacts you don\'t control.)'
        },
        {
            'name': 'Cleansing Nova',
            'oracle_text': 'Choose one — • Destroy all creatures. • Destroy all artifacts and enchantments.'
        },
        {
            'name': 'Bane of Progress',
            'oracle_text': 'When Bane of Progress enters the battlefield, destroy all artifacts and enchantments. Put a +1/+1 counter on Bane of Progress for each permanent destroyed this way.'
        },
        {
            'name': 'Tranquility',
            'oracle_text': 'Destroy all enchantments.'
        }
    ]

    for card in test_cards:
        wipes = extract_artifact_enchantment_wipes(card)
        print(f"\n{card['name']}:")
        if wipes:
            for wipe in wipes:
                symmetry = "ONE-SIDED" if wipe['is_one_sided'] else "SYMMETRICAL"
                print(f"  ✓ {wipe['type'].upper()} | {symmetry}")
                print(f"     {wipe['description']}")
        else:
            print("  ✗ No artifact/enchantment wipes detected")

    print()


def test_land_wipes():
    """Test land destruction extraction"""
    print("=" * 60)
    print("TESTING LAND DESTRUCTION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Armageddon',
            'oracle_text': 'Destroy all lands.'
        },
        {
            'name': 'Ruination',
            'oracle_text': 'Destroy all nonbasic lands.'
        },
        {
            'name': 'Worldfire',
            'oracle_text': 'Exile all permanents. Exile all cards from all hands and graveyards. Each player\'s life total becomes 1.'
        }
    ]

    for card in test_cards:
        wipes = extract_land_wipes(card)
        print(f"\n{card['name']}:")
        if wipes:
            for wipe in wipes:
                mass_ld = " [MASS LD]" if wipe.get('is_mass_land_destruction') else ""
                symmetry = "ONE-SIDED" if wipe['is_one_sided'] else "SYMMETRICAL"
                print(f"  ✓ {wipe['method'].upper()} | {symmetry}{mass_ld}")
                print(f"     {wipe['description']}")
        else:
            print("  ✗ No land wipes detected")

    print()


def test_permanent_wipes():
    """Test permanent wipe extraction"""
    print("=" * 60)
    print("TESTING PERMANENT WIPES")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Nevinyrral\'s Disk',
            'oracle_text': '{1}, {T}: Destroy all artifacts, creatures, and enchantments.'
        },
        {
            'name': 'Oblivion Stone',
            'oracle_text': '{4}, {T}: Put a fate counter on target permanent. {5}, {T}, Sacrifice Oblivion Stone: Destroy each nonland permanent without a fate counter on it, then remove all fate counters from all permanents.'
        },
        {
            'name': 'Apocalypse',
            'oracle_text': 'Exile all permanents. You discard your hand.'
        },
        {
            'name': 'Cyclonic Rift (Overloaded)',
            'oracle_text': 'Return all nonland permanents you don\'t control to their owners\' hands.'
        }
    ]

    for card in test_cards:
        wipes = extract_permanent_wipes(card)
        print(f"\n{card['name']}:")
        if wipes:
            for wipe in wipes:
                apocalypse = " [APOCALYPSE]" if wipe.get('is_apocalypse') else ""
                symmetry = "ONE-SIDED" if wipe['is_one_sided'] else "SYMMETRICAL"
                print(f"  ✓ {wipe['method'].upper()} | {symmetry}{apocalypse}")
                print(f"     {wipe['description']}")
        else:
            print("  ✗ No permanent wipes detected")

    print()


def test_comprehensive_classification():
    """Test full board wipe classification"""
    print("=" * 60)
    print("TESTING COMPREHENSIVE CLASSIFICATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Wrath of God',
            'oracle_text': 'Destroy all creatures. They can\'t be regenerated.'
        },
        {
            'name': 'Vandalblast (Overload)',
            'oracle_text': 'Destroy all artifacts you don\'t control.'
        },
        {
            'name': 'Cyclonic Rift (Overload)',
            'oracle_text': 'Return all nonland permanents you don\'t control to their owners\' hands.'
        },
        {
            'name': 'Apocalypse',
            'oracle_text': 'Exile all permanents. You discard your hand.'
        },
        {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
        }
    ]

    for card in test_cards:
        classification = classify_board_wipe(card)
        severity = get_wipe_severity(classification)

        print(f"\n{classification['card_name']}:")
        print(f"  Is Board Wipe: {classification['is_board_wipe']}")
        print(f"  Total Effects: {classification['total_wipe_effects']}")
        print(f"  One-Sided: {classification['is_one_sided']}")
        print(f"  Symmetrical: {classification['is_symmetrical']}")
        print(f"  Affects Lands: {classification['affects_lands']}")
        print(f"  Severity: {severity.upper()}")

        if classification['creature_wipes']:
            print(f"  Creature Wipes: {len(classification['creature_wipes'])}")
        if classification['artifact_enchantment_wipes']:
            print(f"  Artifact/Enchantment Wipes: {len(classification['artifact_enchantment_wipes'])}")
        if classification['permanent_wipes']:
            print(f"  Permanent Wipes: {len(classification['permanent_wipes'])}")

    print()


def test_one_sided_vs_symmetrical():
    """Test distinction between one-sided and symmetrical wipes"""
    print("=" * 60)
    print("TESTING ONE-SIDED vs SYMMETRICAL")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Day of Judgment (Symmetrical)',
            'oracle_text': 'Destroy all creatures.'
        },
        {
            'name': 'Vandalblast Overload (One-Sided)',
            'oracle_text': 'Destroy all artifacts you don\'t control.'
        },
        {
            'name': 'Cyclonic Rift Overload (One-Sided)',
            'oracle_text': 'Return all nonland permanents you don\'t control to their owners\' hands.'
        },
        {
            'name': 'Toxic Deluge (Symmetrical)',
            'oracle_text': 'As an additional cost to cast this spell, pay X life. All creatures get -X/-X until end of turn.'
        }
    ]

    for card in test_cards:
        classification = classify_board_wipe(card)
        print(f"\n{classification['card_name']}:")

        if classification['is_one_sided']:
            print("  ✓ ONE-SIDED (You keep your permanents)")
        elif classification['is_symmetrical']:
            print("  ✓ SYMMETRICAL (Affects all players equally)")
        else:
            print("  ✗ Not a board wipe")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " BOARD WIPE EXTRACTOR TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_creature_wipes()
    test_artifact_enchantment_wipes()
    test_land_wipes()
    test_permanent_wipes()
    test_comprehensive_classification()
    test_one_sided_vs_symmetrical()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
