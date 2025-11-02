"""
Test suite for mana land extractors
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.utils.mana_extractors import (
    extract_mana_colors,
    classify_basic_land,
    classify_fetch_land,
    classify_dual_land,
    classify_triome,
    classify_special_land,
    classify_mana_land
)


def test_basic_lands():
    """Test basic land classification"""
    print("=" * 60)
    print("TESTING BASIC LANDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Forest',
            'type_line': 'Basic Land — Forest',
            'oracle_text': '({T}: Add {G}.)'
        },
        {
            'name': 'Island',
            'type_line': 'Basic Land — Island',
            'oracle_text': '({T}: Add {U}.)'
        },
        {
            'name': 'Snow-Covered Mountain',
            'type_line': 'Basic Snow Land — Mountain',
            'oracle_text': '({T}: Add {R}.)'
        },
        {
            'name': 'Wastes',
            'type_line': 'Basic Land — Wastes',
            'oracle_text': '{T}: Add {C}.'
        }
    ]

    for card in test_cards:
        result = classify_basic_land(card)
        print(f"\n{card['name']}:")
        if result:
            print(f"  ✓ Type: {result['land_type']}")
            print(f"  ✓ Subtype: {result.get('subtype', 'N/A')}")
            print(f"  ✓ Colors: {result['colors']}")
            print(f"  ✓ Snow: {result['is_snow']}")
            print(f"  ✓ Enters Tapped: {result['enters_tapped']}")
        else:
            print("  ✗ Not classified as basic land")

    print()


def test_fetch_lands():
    """Test fetch land classification"""
    print("=" * 60)
    print("TESTING FETCH LANDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Polluted Delta',
            'type_line': 'Land',
            'oracle_text': '{T}, Pay 1 life, Sacrifice Polluted Delta: Search your library for an Island or Swamp card, put it onto the battlefield, then shuffle.'
        },
        {
            'name': 'Evolving Wilds',
            'type_line': 'Land',
            'oracle_text': 'Evolving Wilds enters the battlefield tapped. {T}, Sacrifice Evolving Wilds: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.'
        },
        {
            'name': 'Fabled Passage',
            'type_line': 'Land',
            'oracle_text': '{T}, Sacrifice Fabled Passage: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. Then if you control four or more lands, untap that land.'
        },
        {
            'name': 'Prismatic Vista',
            'type_line': 'Land',
            'oracle_text': '{T}, Pay 1 life, Sacrifice Prismatic Vista: Search your library for a basic land card, put it onto the battlefield, then shuffle.'
        }
    ]

    for card in test_cards:
        result = classify_fetch_land(card)
        print(f"\n{card['name']}:")
        if result:
            print(f"  ✓ Type: {result['land_type']}")
            print(f"  ✓ Subtype: {result.get('subtype', 'N/A')}")
            print(f"  ✓ Can Fetch: {result.get('can_fetch', 'N/A')}")
            print(f"  ✓ Enters Tapped: {result['enters_tapped']}")
            print(f"  ✓ Is Slow: {result.get('is_slow', False)}")
        else:
            print("  ✗ Not classified as fetch land")

    print()


def test_dual_lands():
    """Test dual land classification"""
    print("=" * 60)
    print("TESTING DUAL LANDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Tropical Island',
            'type_line': 'Land — Forest Island',
            'oracle_text': '({T}: Add {G} or {U}.)'
        },
        {
            'name': 'Steam Vents',
            'type_line': 'Land — Island Mountain',
            'oracle_text': 'As Steam Vents enters the battlefield, you may pay 2 life. If you don\'t, it enters the battlefield tapped. ({T}: Add {U} or {R}.)'
        },
        {
            'name': 'Glacial Fortress',
            'type_line': 'Land',
            'oracle_text': 'Glacial Fortress enters the battlefield tapped unless you control a Plains or an Island. {T}: Add {W} or {U}.'
        },
        {
            'name': 'Adarkar Wastes',
            'type_line': 'Land',
            'oracle_text': '{T}: Add {C}. {T}: Add {W} or {U}. Adarkar Wastes deals 1 damage to you.'
        },
        {
            'name': 'Izzet Boilerworks',
            'type_line': 'Land',
            'oracle_text': 'Izzet Boilerworks enters the battlefield tapped. When Izzet Boilerworks enters the battlefield, return a land you control to its owner\'s hand. {T}: Add {U}{R}.'
        },
        {
            'name': 'Tranquil Cove',
            'type_line': 'Land',
            'oracle_text': 'Tranquil Cove enters the battlefield tapped. When Tranquil Cove enters the battlefield, you gain 1 life. {T}: Add {W} or {U}.'
        },
        {
            'name': 'Temple of Enlightenment',
            'type_line': 'Land',
            'oracle_text': 'Temple of Enlightenment enters the battlefield tapped. When Temple of Enlightenment enters the battlefield, scry 1. {T}: Add {W} or {U}.'
        },
        {
            'name': 'Seachrome Coast',
            'type_line': 'Land',
            'oracle_text': 'Seachrome Coast enters the battlefield tapped unless you control two or fewer other lands. {T}: Add {W} or {U}.'
        }
    ]

    for card in test_cards:
        result = classify_dual_land(card)
        print(f"\n{card['name']}:")
        if result:
            print(f"  ✓ Type: {result['land_type']}")
            print(f"  ✓ Subtype: {result.get('subtype', 'N/A')}")
            print(f"  ✓ Colors: {result['colors']}")
            print(f"  ✓ Enters Tapped: {result['enters_tapped']}")
            if result['untap_conditions']:
                print(f"  ✓ Untap Conditions:")
                for cond in result['untap_conditions']:
                    print(f"     - {cond['description']}")
            if 'drawback' in result:
                print(f"  ⚠ Drawback: {result['drawback']}")
        else:
            print("  ✗ Not classified as dual land")

    print()


def test_triomes():
    """Test triome classification"""
    print("=" * 60)
    print("TESTING TRIOMES")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Savai Triome',
            'type_line': 'Land — Plains Mountain Forest',
            'oracle_text': '({T}: Add {R}, {G}, or {W}.) Savai Triome enters the battlefield tapped. Cycling {3}'
        },
        {
            'name': 'Ketria Triome',
            'type_line': 'Land — Island Mountain Forest',
            'oracle_text': '({T}: Add {U}, {R}, or {G}.) Ketria Triome enters the battlefield tapped. Cycling {3}'
        },
        {
            'name': 'Zagoth Triome',
            'type_line': 'Land — Swamp Island Forest',
            'oracle_text': '({T}: Add {B}, {U}, or {G}.) Zagoth Triome enters the battlefield tapped. Cycling {3}'
        }
    ]

    for card in test_cards:
        result = classify_triome(card)
        print(f"\n{card['name']}:")
        if result:
            print(f"  ✓ Type: {result['land_type']}")
            print(f"  ✓ Subtype: {result.get('subtype', 'N/A')}")
            print(f"  ✓ Colors: {result['colors']}")
            print(f"  ✓ Enters Tapped: {result['enters_tapped']}")
            print(f"  ✓ Has Cycling: {result.get('has_cycling', False)}")
        else:
            print("  ✗ Not classified as triome")

    print()


def test_special_lands():
    """Test special land classification"""
    print("=" * 60)
    print("TESTING SPECIAL LANDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Command Tower',
            'type_line': 'Land',
            'oracle_text': '{T}: Add one mana of any color in your commander\'s color identity.'
        },
        {
            'name': 'Opal Palace',
            'type_line': 'Land',
            'oracle_text': '{T}: Add {C}. {1}, {T}: Add one mana of any color in your commander\'s color identity. If you spend this mana to cast your commander, put a +1/+1 counter on it.'
        },
        {
            'name': 'Mutavault',
            'type_line': 'Land',
            'oracle_text': '{T}: Add {C}. {1}: Mutavault becomes a 2/2 creature with all creature types until end of turn. It\'s still a land.'
        },
        {
            'name': 'Nykthos, Shrine to Nyx',
            'type_line': 'Legendary Land',
            'oracle_text': '{T}: Add {C}. {2}, {T}: Choose a color. Add an amount of mana of that color equal to your devotion to that color.'
        }
    ]

    for card in test_cards:
        result = classify_special_land(card)
        print(f"\n{card['name']}:")
        if result:
            print(f"  ✓ Type: {result['land_type']}")
            print(f"  ✓ Subtype: {result.get('subtype', 'N/A')}")
            print(f"  ✓ Colors: {result['colors']}")
            print(f"  ✓ Enters Tapped: {result['enters_tapped']}")
            if 'special_ability' in result:
                print(f"  ✓ Special Ability: {result['special_ability']}")
        else:
            print("  ✗ Not classified as special land")

    print()


def test_comprehensive_classification():
    """Test full land classification"""
    print("=" * 60)
    print("TESTING COMPREHENSIVE CLASSIFICATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Forest',
            'type_line': 'Basic Land — Forest',
            'oracle_text': '({T}: Add {G}.)'
        },
        {
            'name': 'Scalding Tarn',
            'type_line': 'Land',
            'oracle_text': '{T}, Pay 1 life, Sacrifice Scalding Tarn: Search your library for an Island or Mountain card, put it onto the battlefield, then shuffle.'
        },
        {
            'name': 'Hallowed Fountain',
            'type_line': 'Land — Plains Island',
            'oracle_text': 'As Hallowed Fountain enters the battlefield, you may pay 2 life. If you don\'t, it enters the battlefield tapped. ({T}: Add {W} or {U}.)'
        },
        {
            'name': 'Indatha Triome',
            'type_line': 'Land — Plains Swamp Forest',
            'oracle_text': '({T}: Add {W}, {B}, or {G}.) Indatha Triome enters the battlefield tapped. Cycling {3}'
        },
        {
            'name': 'Command Tower',
            'type_line': 'Land',
            'oracle_text': '{T}: Add one mana of any color in your commander\'s color identity.'
        }
    ]

    for card in test_cards:
        result = classify_mana_land(card)
        print(f"\n{result['card_name']}:")
        print(f"  Is Land: {result['is_land']}")
        if result['classification']:
            cls = result['classification']
            print(f"  Land Type: {cls['land_type']}")
            print(f"  Subtype: {cls.get('subtype', 'N/A')}")
            print(f"  Colors: {cls['colors']}")
            print(f"  Enters Tapped: {cls['enters_tapped']}")
            if cls['untap_conditions']:
                print(f"  Untap Conditions: {len(cls['untap_conditions'])}")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " MANA LAND EXTRACTOR TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_basic_lands()
    test_fetch_lands()
    test_dual_lands()
    test_triomes()
    test_special_lands()
    test_comprehensive_classification()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
