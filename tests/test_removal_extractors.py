"""
Test suite for removal mechanics extractors
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.utils.removal_extractors import (
    extract_counterspell_mechanics,
    extract_destroy_mechanics,
    extract_exile_mechanics,
    extract_bounce_mechanics,
    classify_removal_type
)


def test_counterspell_mechanics():
    """Test counterspell extraction"""
    print("=" * 60)
    print("TESTING COUNTERSPELL MECHANICS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Counterspell',
            'oracle_text': 'Counter target spell.'
        },
        {
            'name': 'Mana Leak',
            'oracle_text': 'Counter target spell unless its controller pays {3}.'
        },
        {
            'name': 'Negate',
            'oracle_text': 'Counter target noncreature spell.'
        },
        {
            'name': 'Essence Scatter',
            'oracle_text': 'Counter target creature spell.'
        },
        {
            'name': 'Ionize',
            'oracle_text': 'Counter target spell. Ionize deals 2 damage to that spell\'s controller.'
        },
        {
            'name': 'Counterspell with Draw',
            'oracle_text': 'Counter target spell. Draw a card.'
        },
        {
            'name': 'Spell Pierce',
            'oracle_text': 'Counter target noncreature spell unless its controller pays {2}.'
        }
    ]

    for card in test_cards:
        mechanics = extract_counterspell_mechanics(card)
        print(f"\n{card['name']}:")
        print(f"  Text: {card['oracle_text']}")
        if mechanics:
            for m in mechanics:
                print(f"  ✓ Type: {m['type']} | Subtype: {m['subtype']} | {m['description']}")
        else:
            print("  ✗ No counterspell mechanics detected")

    print()


def test_destroy_mechanics():
    """Test destroy mechanics extraction"""
    print("=" * 60)
    print("TESTING DESTROY MECHANICS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Murder',
            'oracle_text': 'Destroy target creature.'
        },
        {
            'name': 'Doom Blade',
            'oracle_text': 'Destroy target nonblack creature.'
        },
        {
            'name': 'Wrath of God',
            'oracle_text': 'Destroy all creatures. They can\'t be regenerated.'
        },
        {
            'name': 'Naturalize',
            'oracle_text': 'Destroy target artifact or enchantment.'
        },
        {
            'name': 'Vindicate',
            'oracle_text': 'Destroy target permanent.'
        },
        {
            'name': 'Hero\'s Downfall',
            'oracle_text': 'Destroy target creature or planeswalker.'
        },
        {
            'name': 'Vanquish the Weak',
            'oracle_text': 'Destroy target creature with power 3 or less.'
        }
    ]

    for card in test_cards:
        mechanics = extract_destroy_mechanics(card)
        print(f"\n{card['name']}:")
        print(f"  Text: {card['oracle_text']}")
        if mechanics:
            for m in mechanics:
                is_wipe = ' [BOARD WIPE]' if m.get('is_board_wipe') else ''
                print(f"  ✓ Type: {m['type']} | Subtype: {m['subtype']} | Target: {m.get('target')}{is_wipe}")
        else:
            print("  ✗ No destroy mechanics detected")

    print()


def test_exile_mechanics():
    """Test exile mechanics extraction"""
    print("=" * 60)
    print("TESTING EXILE MECHANICS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Swords to Plowshares',
            'oracle_text': 'Exile target creature. Its controller gains life equal to its power.'
        },
        {
            'name': 'Oblivion Ring',
            'oracle_text': 'When Oblivion Ring enters the battlefield, exile target nonland permanent. When Oblivion Ring leaves the battlefield, return the exiled card to the battlefield.'
        },
        {
            'name': 'Cloudshift',
            'oracle_text': 'Exile target creature you control, then return it to the battlefield under your control.'
        },
        {
            'name': 'Flickerwisp',
            'oracle_text': 'When Flickerwisp enters the battlefield, exile another target permanent. Return that card to the battlefield under its owner\'s control at the beginning of the next end step.'
        },
        {
            'name': 'Rest in Peace',
            'oracle_text': 'When Rest in Peace enters the battlefield, exile all graveyards. If a card or token would be put into a graveyard from anywhere, exile it instead.'
        },
        {
            'name': 'Ashiok, Dream Render',
            'oracle_text': 'Spells and abilities your opponents control can\'t cause their controller to search their library. −1: Target player mills four cards, then exile each opponent\'s graveyard.'
        }
    ]

    for card in test_cards:
        mechanics = extract_exile_mechanics(card)
        print(f"\n{card['name']}:")
        print(f"  Text: {card['oracle_text'][:100]}...")
        if mechanics:
            for m in mechanics:
                perm = ' (Permanent)' if m.get('is_permanent') else ' (Temporary)'
                timing = f" [{m.get('return_timing', '')}]" if 'return_timing' in m else ''
                print(f"  ✓ Type: {m['type']} | Subtype: {m['subtype']}{perm}{timing}")
        else:
            print("  ✗ No exile mechanics detected")

    print()


def test_bounce_mechanics():
    """Test bounce/return to hand mechanics extraction"""
    print("=" * 60)
    print("TESTING BOUNCE MECHANICS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Unsummon',
            'oracle_text': 'Return target creature to its owner\'s hand.'
        },
        {
            'name': 'Cyclonic Rift',
            'oracle_text': 'Return target nonland permanent you don\'t control to its owner\'s hand. Overload {6}{U} (Return all nonland permanents you don\'t control to their owners\' hands.)'
        },
        {
            'name': 'Evacuation',
            'oracle_text': 'Return all creatures to their owners\' hands.'
        },
        {
            'name': 'Devastation Tide',
            'oracle_text': 'Return all nonland permanents to their owners\' hands.'
        },
        {
            'name': 'Condemn',
            'oracle_text': 'Put target attacking creature on the bottom of its owner\'s library. Its controller gains life equal to its toughness.'
        },
        {
            'name': 'Spin into Myth',
            'oracle_text': 'Put target creature on top of its owner\'s library, then fateseal 1.'
        },
        {
            'name': 'Ephemerate',
            'oracle_text': 'Exile target creature you control, then return it to the battlefield under its owner\'s control. Rebound'
        }
    ]

    for card in test_cards:
        mechanics = extract_bounce_mechanics(card)
        print(f"\n{card['name']}:")
        print(f"  Text: {card['oracle_text'][:100]}...")
        if mechanics:
            for m in mechanics:
                mass = ' [MASS]' if m.get('is_mass_effect') else ''
                dest = f" → {m.get('destination')}"
                print(f"  ✓ Type: {m['type']} | Subtype: {m['subtype']}{dest}{mass}")
        else:
            print("  ✗ No bounce mechanics detected")

    print()


def test_classify_removal():
    """Test full removal classification"""
    print("=" * 60)
    print("TESTING FULL REMOVAL CLASSIFICATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Anguished Unmaking',
            'oracle_text': 'Exile target nonland permanent. You lose 3 life.'
        },
        {
            'name': 'Cryptic Command',
            'oracle_text': 'Choose two — • Counter target spell. • Return target permanent to its owner\'s hand. • Tap all creatures your opponents control. • Draw a card.'
        },
        {
            'name': 'Supreme Verdict',
            'oracle_text': 'This spell can\'t be countered. Destroy all creatures.'
        }
    ]

    for card in test_cards:
        result = classify_removal_type(card)
        print(f"\n{result['card_name']}:")
        print(f"  Text: {card['oracle_text']}")
        print(f"  Total mechanics: {result['total_removal_mechanics']}")

        if result['counterspells']:
            print(f"  Counterspells: {len(result['counterspells'])}")
            for m in result['counterspells']:
                print(f"    - {m['subtype']}: {m['description']}")

        if result['destroy_effects']:
            print(f"  Destroy effects: {len(result['destroy_effects'])}")
            for m in result['destroy_effects']:
                print(f"    - {m['subtype']}: {m['description']}")

        if result['exile_effects']:
            print(f"  Exile effects: {len(result['exile_effects'])}")
            for m in result['exile_effects']:
                print(f"    - {m['subtype']}: {m['description']}")

        if result['bounce_effects']:
            print(f"  Bounce effects: {len(result['bounce_effects'])}")
            for m in result['bounce_effects']:
                print(f"    - {m['subtype']}: {m['description']}")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " REMOVAL MECHANICS EXTRACTOR TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_counterspell_mechanics()
    test_destroy_mechanics()
    test_exile_mechanics()
    test_bounce_mechanics()
    test_classify_removal()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
