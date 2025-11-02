"""
Test suite for creature keyword extractors
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.utils.keyword_extractors import (
    extract_creature_keywords,
    extract_keyword_abilities,
    extract_granted_keywords,
    classify_creature_abilities,
    get_keyword_synergies
)


def test_basic_keywords():
    """Test basic keyword extraction"""
    print("=" * 60)
    print("TESTING BASIC KEYWORD EXTRACTION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Baneslayer Angel',
            'type_line': 'Creature — Angel',
            'keywords': ['Flying', 'First Strike', 'Lifelink', 'Protection'],
            'oracle_text': 'Flying, first strike, lifelink, protection from Demons and from Dragons'
        },
        {
            'name': 'Questing Beast',
            'type_line': 'Legendary Creature — Beast',
            'keywords': ['Vigilance', 'Deathtouch', 'Haste'],
            'oracle_text': 'Vigilance, deathtouch, haste'
        },
        {
            'name': 'Akroma, Angel of Fury',
            'type_line': 'Legendary Creature — Angel',
            'keywords': ['Flying', 'Trample', 'Protection', 'Haste'],
            'oracle_text': 'Flying, trample, protection from white and from blue, haste'
        },
        {
            'name': 'Grave Titan',
            'type_line': 'Creature — Giant',
            'keywords': ['Deathtouch'],
            'oracle_text': 'Deathtouch. Whenever Grave Titan enters the battlefield or attacks, create two 2/2 black Zombie creature tokens.'
        }
    ]

    for card in test_cards:
        keywords = extract_creature_keywords(card)
        print(f"\n{card['name']}:")
        print(f"  Keywords found: {len(keywords)}")
        for kw in keywords:
            print(f"  ✓ {kw['keyword']} ({kw['category']}) - from {kw['source']}")

    print()


def test_keyword_categories():
    """Test keyword categorization"""
    print("=" * 60)
    print("TESTING KEYWORD CATEGORIZATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Sephara, Sky\'s Blade',
            'type_line': 'Legendary Creature — Angel',
            'keywords': ['Flying', 'Lifelink', 'Indestructible'],
            'oracle_text': 'Flying, lifelink, indestructible. Other creatures you control with flying get +1/+1 and have indestructible.'
        }
    ]

    for card in test_cards:
        categorized = extract_keyword_abilities(card)
        print(f"\n{card['name']}:")
        for category, keywords in categorized.items():
            if keywords:
                print(f"  {category.upper()}:")
                for kw in keywords:
                    print(f"    - {kw['keyword']}: {kw['description']}")

    print()


def test_granted_keywords():
    """Test keyword granting extraction"""
    print("=" * 60)
    print("TESTING GRANTED KEYWORDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Sephara, Sky\'s Blade',
            'type_line': 'Legendary Creature — Angel',
            'keywords': ['Flying', 'Lifelink', 'Indestructible'],
            'oracle_text': 'Flying, lifelink, indestructible. Other creatures you control with flying get +1/+1 and have indestructible.'
        },
        {
            'name': 'Archetype of Courage',
            'type_line': 'Enchantment Creature — Human Soldier',
            'keywords': ['First Strike'],
            'oracle_text': 'Creatures you control have first strike. Creatures your opponents control lose first strike and can\'t have or gain first strike.'
        },
        {
            'name': 'Samut, Voice of Dissent',
            'type_line': 'Legendary Creature — Human Warrior',
            'keywords': ['Flash', 'Double Strike', 'Vigilance', 'Haste'],
            'oracle_text': 'Flash. Double strike, vigilance, haste. Other creatures you control have haste.'
        },
        {
            'name': 'Giver of Runes',
            'type_line': 'Creature — Kor Cleric',
            'keywords': [],
            'oracle_text': '{T}: Another target creature you control gains protection from colorless or from the color of your choice until end of turn.'
        }
    ]

    for card in test_cards:
        granted = extract_granted_keywords(card)
        print(f"\n{card['name']}:")
        if granted:
            print(f"  Grants {len(granted)} keyword(s):")
            for kw in granted:
                print(f"  ✓ {kw['keyword']} ({kw['grant_type']}) - {kw['description']}")
        else:
            print("  ✗ No keywords granted")

    print()


def test_comprehensive_classification():
    """Test full creature ability classification"""
    print("=" * 60)
    print("TESTING COMPREHENSIVE CLASSIFICATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Lyra Dawnbringer',
            'type_line': 'Legendary Creature — Angel',
            'keywords': ['Flying', 'First Strike', 'Lifelink'],
            'oracle_text': 'Flying, first strike, lifelink. Other Angels you control get +1/+1 and have lifelink.'
        },
        {
            'name': 'Lightning Bolt',
            'type_line': 'Instant',
            'keywords': [],
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
        }
    ]

    for card in test_cards:
        classification = classify_creature_abilities(card)
        print(f"\n{classification['card_name']}:")
        print(f"  Is Creature: {classification['is_creature']}")
        print(f"  Own Keywords: {classification['total_keywords']}")
        if classification['own_keywords']:
            for kw in classification['own_keywords']:
                print(f"    - {kw['keyword']}")
        print(f"  Grants Keywords: {classification['total_granted']}")
        if classification['grants_keywords']:
            for kw in classification['grants_keywords']:
                print(f"    - {kw['keyword']} ({kw['grant_type']})")

    print()


def test_keyword_synergies():
    """Test keyword synergy detection"""
    print("=" * 60)
    print("TESTING KEYWORD SYNERGIES")
    print("=" * 60)

    card1 = {
        'name': 'Serra Angel',
        'type_line': 'Creature — Angel',
        'keywords': ['Flying', 'Vigilance'],
        'oracle_text': 'Flying, vigilance'
    }

    card2 = {
        'name': 'Archetype of Imagination',
        'type_line': 'Enchantment Creature — Human Wizard',
        'keywords': ['Flying'],
        'oracle_text': 'Creatures you control have flying. Creatures your opponents control lose flying and can\'t have or gain flying.'
    }

    card3 = {
        'name': 'Odric, Lunarch Marshal',
        'type_line': 'Legendary Creature — Human Soldier',
        'keywords': [],
        'oracle_text': 'At the beginning of each combat, creatures you control gain first strike until end of turn if a creature you control has first strike. The same is true for flying, deathtouch, double strike, haste, hexproof, indestructible, lifelink, menace, reach, skulk, trample, and vigilance.'
    }

    print("\nTesting synergies:")
    print(f"\n{card1['name']} + {card2['name']}:")
    synergies = get_keyword_synergies(card1, card2)
    if synergies:
        for syn in synergies:
            print(f"  ✓ {syn['type']}: {syn['description']}")
    else:
        print("  ✗ No synergies detected")

    print(f"\n{card1['name']} + {card3['name']}:")
    synergies = get_keyword_synergies(card1, card3)
    if synergies:
        for syn in synergies:
            print(f"  ✓ {syn['type']}: {syn['description']}")
    else:
        print("  ✗ No synergies detected")

    print()


def test_evasion_keywords():
    """Test evasion keyword extraction"""
    print("=" * 60)
    print("TESTING EVASION KEYWORDS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Thassa\'s Oracle',
            'type_line': 'Creature — Merfolk Wizard',
            'keywords': [],
            'oracle_text': 'When Thassa\'s Oracle enters the battlefield, look at the top X cards of your library...'
        },
        {
            'name': 'Dauthi Voidwalker',
            'type_line': 'Creature — Dauthi Rogue',
            'keywords': ['Shadow'],
            'oracle_text': 'Shadow (This creature can block or be blocked by only creatures with shadow.)'
        },
        {
            'name': 'Invisible Stalker',
            'type_line': 'Creature — Human Rogue',
            'keywords': ['Hexproof'],
            'oracle_text': 'Hexproof. This creature can\'t be blocked.'
        },
        {
            'name': 'Falkenrath Reaver',
            'type_line': 'Creature — Vampire Warrior',
            'keywords': [],
            'oracle_text': 'This creature can\'t block.'
        }
    ]

    for card in test_cards:
        categorized = extract_keyword_abilities(card)
        print(f"\n{card['name']}:")
        if categorized['evasion']:
            for kw in categorized['evasion']:
                print(f"  ✓ {kw['keyword']} ({kw['description']})")
        else:
            print(f"  ✗ No evasion keywords")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " CREATURE KEYWORD EXTRACTOR TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_basic_keywords()
    test_keyword_categories()
    test_granted_keywords()
    test_comprehensive_classification()
    test_keyword_synergies()
    test_evasion_keywords()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
