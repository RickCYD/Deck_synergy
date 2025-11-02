"""
Tests for Recursion Extractors

Tests all recursion extraction functions with real MTG card examples.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.recursion_extractors import (
    extract_reanimation,
    extract_recursion_to_hand,
    extract_graveyard_casting,
    extract_extra_turns,
    extract_cascade,
    extract_treasure_tokens,
    classify_recursion_mechanics
)


def test_reanimation():
    """Test reanimation extraction"""
    print("\n=== Testing Reanimation Extraction ===")

    test_cases = [
        {
            'name': 'Reanimate',
            'oracle_text': 'Put target creature card from a graveyard onto the battlefield under your control. You lose life equal to its mana value.',
            'expected': {
                'has_reanimation': True,
                'reanimation_type': 'single',
                'targets': ['creature'],
                'source': 'any_graveyard'
            }
        },
        {
            'name': 'Animate Dead',
            'oracle_text': 'Enchant creature card in a graveyard\nWhen Animate Dead enters the battlefield, if it\'s on the battlefield, it loses "enchant creature card in a graveyard" and gains "enchant creature put onto the battlefield with Animate Dead." Return enchanted creature card to the battlefield under your control and attach Animate Dead to it.',
            'expected': {
                'has_reanimation': True,
                'targets': ['creature']
            }
        },
        {
            'name': 'Living Death',
            'oracle_text': 'Each player exiles all creature cards from their graveyard, then sacrifices all creatures they control, then puts all cards they exiled this way onto the battlefield.',
            'expected': {
                'has_reanimation': True,
                'reanimation_type': 'mass'
            }
        },
        {
            'name': 'Eternal Witness',
            'oracle_text': 'When Eternal Witness enters the battlefield, you may return target card from your graveyard to your hand.',
            'expected': {
                'has_reanimation': False  # This is recursion to hand, not reanimation
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_reanimation(card)

        if result['has_reanimation'] == test['expected']['has_reanimation']:
            if not test['expected']['has_reanimation']:
                print(f"✓ {test['name']}: Correctly identified not reanimation")
                passed += 1
            else:
                print(f"✓ {test['name']}: type={result['reanimation_type']}, targets={result['targets']}, source={result['source']}")
                passed += 1
        else:
            print(f"✗ {test['name']}: Expected has_reanimation={test['expected']['has_reanimation']}, got {result['has_reanimation']}")

    print(f"\nReanimation: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_recursion_to_hand():
    """Test recursion to hand extraction"""
    print("\n=== Testing Recursion to Hand ===")

    test_cases = [
        {
            'name': 'Eternal Witness',
            'oracle_text': 'When Eternal Witness enters the battlefield, you may return target card from your graveyard to your hand.',
            'expected': {
                'has_recursion': True,
                'targets': ['any']
            }
        },
        {
            'name': 'Regrowth',
            'oracle_text': 'Return target card from your graveyard to your hand.',
            'expected': {
                'has_recursion': True,
                'recursion_type': 'single'
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_recursion_to_hand(card)

        if result['has_recursion'] == test['expected']['has_recursion']:
            print(f"✓ {test['name']}: type={result['recursion_type']}, targets={result['targets']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected has_recursion={test['expected']['has_recursion']}, got {result['has_recursion']}")

    print(f"\nRecursion to Hand: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_graveyard_casting():
    """Test graveyard casting extraction"""
    print("\n=== Testing Graveyard Casting ===")

    test_cases = [
        {
            'name': 'Faithless Looting',
            'oracle_text': 'Draw two cards, then discard two cards.\nFlashback {2}{R}',
            'keywords': ['Flashback'],
            'expected': {
                'has_graveyard_casting': True,
                'casting_types': ['flashback']
            }
        },
        {
            'name': 'Uro, Titan of Nature\'s Wrath',
            'oracle_text': 'When Uro enters the battlefield or attacks, sacrifice it unless it escaped.\nWhenever Uro enters the battlefield or attacks, you gain 3 life and draw a card, then you may put a land card from your hand onto the battlefield.\nEscape—{G}{G}{U}{U}, Exile five other cards from your graveyard.',
            'keywords': ['Escape'],
            'expected': {
                'has_graveyard_casting': True,
                'casting_types': ['escape']
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text'], 'keywords': test.get('keywords', [])}
        result = extract_graveyard_casting(card)

        if result['has_graveyard_casting'] == test['expected']['has_graveyard_casting']:
            print(f"✓ {test['name']}: types={result['casting_types']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected has_graveyard_casting={test['expected']['has_graveyard_casting']}, got {result['has_graveyard_casting']}")

    print(f"\nGraveyard Casting: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_extra_turns():
    """Test extra turns extraction"""
    print("\n=== Testing Extra Turns ===")

    test_cases = [
        {
            'name': 'Time Warp',
            'oracle_text': 'Target player takes an extra turn after this one.',
            'expected': {
                'has_extra_turns': True,
                'turn_type': 'single'
            }
        },
        {
            'name': 'Nexus of Fate',
            'oracle_text': 'Take an extra turn after this one.\nIf Nexus of Fate would be put into a graveyard from anywhere, reveal Nexus of Fate and shuffle it into its owner\'s library instead.',
            'expected': {
                'has_extra_turns': True,
                'turn_type': 'single'
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_extra_turns(card)

        if result['has_extra_turns'] == test['expected']['has_extra_turns']:
            print(f"✓ {test['name']}: type={result['turn_type']}, restrictions={result['restrictions']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected has_extra_turns={test['expected']['has_extra_turns']}, got {result['has_extra_turns']}")

    print(f"\nExtra Turns: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_cascade():
    """Test cascade extraction"""
    print("\n=== Testing Cascade ===")

    test_cases = [
        {
            'name': 'Bloodbraid Elf',
            'oracle_text': 'Haste\nCascade',
            'keywords': ['Cascade'],
            'expected': {
                'has_cascade': True,
                'cascade_count': 1
            }
        },
        {
            'name': 'Maelstrom Wanderer',
            'oracle_text': 'Creatures you control have haste.\nCascade, cascade',
            'keywords': ['Cascade'],
            'expected': {
                'has_cascade': True,
                'cascade_count': 2
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text'], 'keywords': test.get('keywords', [])}
        result = extract_cascade(card)

        if result['has_cascade'] == test['expected']['has_cascade']:
            print(f"✓ {test['name']}: count={result['cascade_count']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected has_cascade={test['expected']['has_cascade']}, got {result['has_cascade']}")

    print(f"\nCascade: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_treasure_tokens():
    """Test treasure/clue/food token extraction"""
    print("\n=== Testing Token Generation ===")

    test_cases = [
        {
            'name': 'Dockside Extortionist',
            'oracle_text': 'When Dockside Extortionist enters the battlefield, create X Treasure tokens, where X is the number of artifacts your opponents control.',
            'expected': {
                'generates_tokens': True,
                'token_types': ['treasure'],
                'generation_type': 'etb'
            }
        },
        {
            'name': 'Tireless Tracker',
            'oracle_text': 'Whenever a land enters the battlefield under your control, investigate.\nWhenever you sacrifice a Clue, put a +1/+1 counter on Tireless Tracker.',
            'expected': {
                'generates_tokens': True,
                'token_types': ['clue'],
                'generation_type': 'repeatable'
            }
        },
        {
            'name': 'Gilded Goose',
            'oracle_text': 'Flying\nWhen Gilded Goose enters the battlefield, create a Food token.\n{1}{G}, {T}, Sacrifice a Food: Add one mana of any color.',
            'expected': {
                'generates_tokens': True,
                'token_types': ['food'],
                'generation_type': 'etb'
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_treasure_tokens(card)

        if result['generates_tokens'] == test['expected']['generates_tokens']:
            print(f"✓ {test['name']}: types={result['token_types']}, generation={result['generation_type']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected generates_tokens={test['expected']['generates_tokens']}, got {result['generates_tokens']}")

    print(f"\nToken Generation: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def main():
    """Run all tests"""
    print("="*60)
    print("RECURSION EXTRACTOR TEST SUITE")
    print("="*60)

    results = []
    results.append(test_reanimation())
    results.append(test_recursion_to_hand())
    results.append(test_graveyard_casting())
    results.append(test_extra_turns())
    results.append(test_cascade())
    results.append(test_treasure_tokens())

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    test_names = ['Reanimation', 'Recursion to Hand', 'Graveyard Casting', 'Extra Turns', 'Cascade', 'Token Generation']
    for name, result in zip(test_names, results):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(results)
    total_tests = len(results)
    print(f"\n{'='*60}")
    print(f"Overall: {total_passed}/{total_tests} test suites passed ({100*total_passed//total_tests}%)")
    print("="*60)

    return total_passed == total_tests


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
