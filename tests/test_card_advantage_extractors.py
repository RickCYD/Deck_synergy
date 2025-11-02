"""
Tests for Card Advantage Extractors

Tests all card advantage extraction functions with real MTG card examples.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.card_advantage_extractors import (
    extract_card_draw,
    extract_wheel_effects,
    extract_tutors,
    extract_mill_effects,
    extract_discard_effects,
    extract_looting_effects,
    extract_impulse_draw,
    extract_draw_payoffs,
    classify_card_advantage
)


def test_card_draw():
    """Test card draw extraction"""
    print("\n=== Testing Card Draw Extraction ===")

    test_cases = [
        {
            'name': 'Divination',
            'oracle_text': 'Draw two cards.',
            'expected': {
                'has_draw': True,
                'draw_types': ['fixed'],
                'draw_amount': 2
            }
        },
        {
            'name': 'Brainstorm',
            'oracle_text': 'Draw three cards, then put two cards from your hand on top of your library in any order.',
            'expected': {
                'has_draw': True,
                'draw_types': ['fixed'],
                'draw_amount': 3
            }
        },
        {
            'name': 'Rhystic Study',
            'oracle_text': 'Whenever an opponent casts a spell, you may draw a card unless that player pays {1}.',
            'expected': {
                'has_draw': True,
                'draw_types': ['conditional', 'repeatable', 'single'],
                'draw_amount': None
            }
        },
        {
            'name': 'Blue Sun\'s Zenith',
            'oracle_text': 'Target player draws X cards. Shuffle Blue Sun\'s Zenith into its owner\'s library.',
            'expected': {
                'has_draw': True,
                'draw_types': ['variable'],
                'draw_amount': None
            }
        },
        {
            'name': 'Consecrated Sphinx',
            'oracle_text': 'Flying\nWhenever an opponent draws a card, you may draw two cards.',
            'expected': {
                'has_draw': True,
                'draw_types': ['fixed', 'conditional', 'repeatable'],
                'draw_amount': 2
            }
        },
        {
            'name': 'Opt',
            'oracle_text': 'Scry 1.\nDraw a card.',
            'expected': {
                'has_draw': True,
                'draw_types': ['single'],
                'draw_amount': None
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_card_draw(card)

        if result['has_draw'] == test['expected']['has_draw']:
            if not test['expected']['has_draw']:
                print(f"✓ {test['name']}: Correctly identified no draw")
                passed += 1
            elif (set(result['draw_types']) == set(test['expected']['draw_types']) and
                  result['draw_amount'] == test['expected']['draw_amount']):
                print(f"✓ {test['name']}: {result['draw_types']}, amount={result['draw_amount']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected types={test['expected']['draw_types']}, amount={test['expected']['draw_amount']}")
                print(f"  Got types={result['draw_types']}, amount={result['draw_amount']}")
        else:
            print(f"✗ {test['name']}: Expected has_draw={test['expected']['has_draw']}, got {result['has_draw']}")

    print(f"\nCard Draw: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_wheel_effects():
    """Test wheel effect extraction"""
    print("\n=== Testing Wheel Effects ===")

    test_cases = [
        {
            'name': 'Wheel of Fortune',
            'oracle_text': 'Each player discards their hand, then draws seven cards.',
            'expected': {
                'is_wheel': True,
                'wheel_type': 'full_wheel',
                'cards_drawn': 7,
                'symmetrical': True
            }
        },
        {
            'name': 'Windfall',
            'oracle_text': 'Each player discards their hand, then draws cards equal to the greatest number of cards a player discarded this way.',
            'expected': {
                'is_wheel': True,
                'wheel_type': 'windfall',
                'cards_drawn': None,
                'symmetrical': True
            }
        },
        {
            'name': 'Wheel of Misfortune',
            'oracle_text': 'Each player secretly chooses a number 0 or greater, then all players reveal those numbers simultaneously and determine the highest and lowest numbers revealed this way. Wheel of Misfortune deals damage equal to the highest number to each player who chose that number. Each player who didn\'t choose the lowest number discards their hand, then draws seven cards.',
            'expected': {
                'is_wheel': True,
                'wheel_type': 'full_wheel',
                'cards_drawn': 7
            }
        },
        {
            'name': 'Teferi\'s Puzzle Box',
            'oracle_text': 'At the beginning of each player\'s draw step, that player puts the cards in their hand on the bottom of their library in any order, then draws that many cards.',
            'expected': {
                'is_wheel': False
            }
        },
        {
            'name': 'Prosperity',
            'oracle_text': 'Each player draws X cards.',
            'expected': {
                'is_wheel': True,
                'wheel_type': 'partial_wheel',
                'symmetrical': True
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_wheel_effects(card)

        if result['is_wheel'] == test['expected']['is_wheel']:
            if not test['expected']['is_wheel']:
                print(f"✓ {test['name']}: Correctly identified not a wheel")
                passed += 1
            elif result['wheel_type'] == test['expected']['wheel_type']:
                print(f"✓ {test['name']}: {result['wheel_type']}, draws={result['cards_drawn']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected type={test['expected']['wheel_type']}, got {result['wheel_type']}")
        else:
            print(f"✗ {test['name']}: Expected is_wheel={test['expected']['is_wheel']}, got {result['is_wheel']}")

    print(f"\nWheel Effects: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_tutors():
    """Test tutor extraction"""
    print("\n=== Testing Tutors ===")

    test_cases = [
        {
            'name': 'Demonic Tutor',
            'oracle_text': 'Search your library for a card, put that card into your hand, then shuffle.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'any',
                'destination': 'hand'
            }
        },
        {
            'name': 'Vampiric Tutor',
            'oracle_text': 'Search your library for a card, then shuffle and put that card on top of your library.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'any',
                'destination': 'top'
            }
        },
        {
            'name': 'Chord of Calling',
            'oracle_text': 'Convoke\nSearch your library for a creature card with mana value X or less, put it onto the battlefield, then shuffle.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'creature',
                'destination': 'battlefield',
                'restrictions': ['cmc_x_or_less']
            }
        },
        {
            'name': 'Mystical Tutor',
            'oracle_text': 'Search your library for an instant or sorcery card, reveal it, put it into your hand, then shuffle.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'instant_or_sorcery',
                'destination': 'hand'
            }
        },
        {
            'name': 'Rampant Growth',
            'oracle_text': 'Search your library for a basic land card, put that card onto the battlefield tapped, then shuffle.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'land',
                'destination': 'battlefield'
            }
        },
        {
            'name': 'Enlightened Tutor',
            'oracle_text': 'Search your library for an artifact or enchantment card, reveal it, put it into your hand, then shuffle.',
            'expected': {
                'is_tutor': True,
                'tutor_type': 'artifact',  # Will match artifact first
                'destination': 'hand'
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_tutors(card)

        if result['is_tutor'] == test['expected']['is_tutor']:
            if not test['expected']['is_tutor']:
                print(f"✓ {test['name']}: Correctly identified not a tutor")
                passed += 1
            elif (result['tutor_type'] == test['expected']['tutor_type'] and
                  result['destination'] == test['expected']['destination']):
                print(f"✓ {test['name']}: {result['tutor_type']} → {result['destination']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected {test['expected']['tutor_type']} → {test['expected']['destination']}")
                print(f"  Got {result['tutor_type']} → {result['destination']}")
        else:
            print(f"✗ {test['name']}: Expected is_tutor={test['expected']['is_tutor']}, got {result['is_tutor']}")

    print(f"\nTutors: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_mill_effects():
    """Test mill effect extraction"""
    print("\n=== Testing Mill Effects ===")

    test_cases = [
        {
            'name': 'Glimpse the Unthinkable',
            'oracle_text': 'Target player mills ten cards.',
            'expected': {
                'has_mill': True,
                'mill_targets': ['target_player'],
                'mill_amount': 10,
                'mill_type': 'fixed'
            }
        },
        {
            'name': 'Hedron Crab',
            'oracle_text': 'Landfall — Whenever a land enters the battlefield under your control, target player mills three cards.',
            'expected': {
                'has_mill': True,
                'mill_targets': ['target_player'],
                'mill_amount': 3,
                'mill_type': 'fixed',
                'repeatable': True
            }
        },
        {
            'name': 'Maddening Cacophony',
            'oracle_text': 'Each opponent mills eight cards. If this spell was kicked, instead each opponent mills half their library, rounded up.',
            'expected': {
                'has_mill': True,
                'mill_targets': ['each_opponent'],
                'mill_amount': 8,
                'mill_type': 'fixed'
            }
        },
        {
            'name': 'Traumatize',
            'oracle_text': 'Target player mills half their library, rounded down.',
            'expected': {
                'has_mill': True,
                'mill_targets': ['target_player'],
                'mill_type': 'variable'
            }
        },
        {
            'name': 'Bruvac the Grandiloquent',
            'oracle_text': 'If an opponent would mill one or more cards, they mill twice that many cards instead.',
            'expected': {
                'has_mill': False  # This is a mill modifier, not a mill effect itself
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_mill_effects(card)

        if result['has_mill'] == test['expected']['has_mill']:
            if not test['expected']['has_mill']:
                print(f"✓ {test['name']}: Correctly identified no mill")
                passed += 1
            elif (result['mill_targets'] == test['expected']['mill_targets'] and
                  result['mill_type'] == test['expected']['mill_type']):
                print(f"✓ {test['name']}: targets={result['mill_targets']}, type={result['mill_type']}, amount={result['mill_amount']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected targets={test['expected']['mill_targets']}, type={test['expected']['mill_type']}")
                print(f"  Got targets={result['mill_targets']}, type={result['mill_type']}")
        else:
            print(f"✗ {test['name']}: Expected has_mill={test['expected']['has_mill']}, got {result['has_mill']}")

    print(f"\nMill Effects: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_discard_effects():
    """Test discard effect extraction"""
    print("\n=== Testing Discard Effects ===")

    test_cases = [
        {
            'name': 'Thoughtseize',
            'oracle_text': 'Target player reveals their hand. You choose a nonland card from it. That player discards that card. You lose 2 life.',
            'expected': {
                'has_discard': True,
                'discard_targets': ['target_opponent'],
                'discard_amount': 1,
                'discard_type': 'choice'
            }
        },
        {
            'name': 'Hymn to Tourach',
            'oracle_text': 'Target player discards two cards at random.',
            'expected': {
                'has_discard': True,
                'discard_targets': ['target_opponent'],
                'discard_amount': 2,
                'discard_type': 'random'
            }
        },
        {
            'name': 'Dark Deal',
            'oracle_text': 'Each player discards all the cards in their hand, then draws that many cards minus one.',
            'expected': {
                'has_discard': True,
                'discard_targets': ['each_player'],
                'discard_type': 'hand'
            }
        },
        {
            'name': 'Liliana of the Veil',
            'oracle_text': '+1: Each player discards a card.\n−2: Target player sacrifices a creature.\n−6: Separate all permanents target player controls into two piles. That player sacrifices all permanents in the pile of their choice.',
            'expected': {
                'has_discard': True,
                'discard_targets': ['each_player'],
                'discard_amount': 1
            }
        },
        {
            'name': 'Bone Miser',
            'oracle_text': 'Whenever you discard a creature card, create a 2/2 black Zombie creature token.\nWhenever you discard a land card, add {B}{B}.\nWhenever you discard a noncreature, nonland card, draw a card.',
            'expected': {
                'has_discard': True,
                'discard_targets': ['self']
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_discard_effects(card)

        if result['has_discard'] == test['expected']['has_discard']:
            if not test['expected']['has_discard']:
                print(f"✓ {test['name']}: Correctly identified no discard")
                passed += 1
            elif result['discard_targets'] == test['expected']['discard_targets']:
                print(f"✓ {test['name']}: targets={result['discard_targets']}, type={result['discard_type']}, amount={result['discard_amount']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected targets={test['expected']['discard_targets']}")
                print(f"  Got targets={result['discard_targets']}, type={result['discard_type']}")
        else:
            print(f"✗ {test['name']}: Expected has_discard={test['expected']['has_discard']}, got {result['has_discard']}")

    print(f"\nDiscard Effects: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_looting_effects():
    """Test looting effect extraction"""
    print("\n=== Testing Looting Effects ===")

    test_cases = [
        {
            'name': 'Faithless Looting',
            'oracle_text': 'Draw two cards, then discard two cards.\nFlashback {2}{R}',
            'expected': {
                'is_looting': True,
                'draw_amount': 2,
                'discard_amount': 2,
                'net_advantage': 0
            }
        },
        {
            'name': 'Careful Study',
            'oracle_text': 'Draw two cards, then discard two cards.',
            'expected': {
                'is_looting': True,
                'draw_amount': 2,
                'discard_amount': 2,
                'net_advantage': 0
            }
        },
        {
            'name': 'Thrill of Possibility',
            'oracle_text': 'As an additional cost to cast this spell, discard a card.\nDraw two cards.',
            'expected': {
                'is_looting': False  # Cost comes before draw
            }
        },
        {
            'name': 'Chart a Course',
            'oracle_text': 'Draw two cards. Then discard a card unless you attacked this turn.',
            'expected': {
                'is_looting': True,
                'draw_amount': 2,
                'discard_amount': 1,
                'net_advantage': 1
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_looting_effects(card)

        if result['is_looting'] == test['expected']['is_looting']:
            if not test['expected']['is_looting']:
                print(f"✓ {test['name']}: Correctly identified not looting")
                passed += 1
            elif (result['draw_amount'] == test['expected']['draw_amount'] and
                  result['discard_amount'] == test['expected']['discard_amount']):
                print(f"✓ {test['name']}: draw={result['draw_amount']}, discard={result['discard_amount']}, net={result['net_advantage']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected draw={test['expected']['draw_amount']}, discard={test['expected']['discard_amount']}")
                print(f"  Got draw={result['draw_amount']}, discard={result['discard_amount']}")
        else:
            print(f"✗ {test['name']}: Expected is_looting={test['expected']['is_looting']}, got {result['is_looting']}")

    print(f"\nLooting Effects: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_impulse_draw():
    """Test impulse draw extraction"""
    print("\n=== Testing Impulse Draw ===")

    test_cases = [
        {
            'name': 'Light Up the Stage',
            'oracle_text': 'This spell costs {X} less to cast, where X is the total amount of damage your opponents have been dealt this turn.\nExile the top two cards of your library. Until the end of your next turn, you may play those cards.',
            'expected': {
                'has_impulse': True,
                'impulse_amount': 2,
                'duration': 'turn'
            }
        },
        {
            'name': 'Outpost Siege',
            'oracle_text': 'As Outpost Siege enters the battlefield, choose Khans or Dragons.\n• Khans — At the beginning of your upkeep, exile the top card of your library. Until end of turn, you may play that card.\n• Dragons — Whenever a creature you control leaves the battlefield, Outpost Siege deals 1 damage to any target.',
            'expected': {
                'has_impulse': True,
                'impulse_amount': 1,
                'duration': 'until_end_of_turn'
            }
        },
        {
            'name': 'Jeska\'s Will',
            'oracle_text': 'Choose one. If you control a commander as you cast this spell, you may choose both.\n• Add {R} for each card in target opponent\'s hand.\n• Exile the top three cards of your library. You may play them this turn.',
            'expected': {
                'has_impulse': True,
                'impulse_amount': 3,
                'duration': 'turn'
            }
        },
        {
            'name': 'Experimental Frenzy',
            'oracle_text': 'You may look at the top card of your library any time.\nYou may play lands and cast spells from the top of your library.\nYou can\'t play cards from your hand.\n{3}{R}: Destroy Experimental Frenzy.',
            'expected': {
                'has_impulse': False  # Not an exile effect
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_impulse_draw(card)

        if result['has_impulse'] == test['expected']['has_impulse']:
            if not test['expected']['has_impulse']:
                print(f"✓ {test['name']}: Correctly identified no impulse draw")
                passed += 1
            elif result['impulse_amount'] == test['expected']['impulse_amount']:
                print(f"✓ {test['name']}: amount={result['impulse_amount']}, duration={result['duration']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected amount={test['expected']['impulse_amount']}")
                print(f"  Got amount={result['impulse_amount']}, duration={result['duration']}")
        else:
            print(f"✗ {test['name']}: Expected has_impulse={test['expected']['has_impulse']}, got {result['has_impulse']}")

    print(f"\nImpulse Draw: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def test_draw_payoffs():
    """Test draw payoff extraction"""
    print("\n=== Testing Draw Payoffs ===")

    test_cases = [
        {
            'name': 'Niv-Mizzet, Parun',
            'oracle_text': 'This spell can\'t be countered.\nFlying\nWhenever you draw a card, Niv-Mizzet, Parun deals 1 damage to any target.\nWhenever a player casts an instant or sorcery spell, you draw a card.',
            'expected': {
                'is_draw_payoff': True,
                'trigger_type': 'any_draw',
                'payoff_effects': ['damage']
            }
        },
        {
            'name': 'The Locust God',
            'oracle_text': 'Flying\nWhenever you draw a card, create a 1/1 blue and red Insect creature token with flying and haste.\n{2}{U}{R}: Draw a card, then discard a card.\nWhen The Locust God dies, return it to its owner\'s hand at the beginning of the next end step.',
            'expected': {
                'is_draw_payoff': True,
                'trigger_type': 'any_draw',
                'payoff_effects': ['token']
            }
        },
        {
            'name': 'Psychosis Crawler',
            'oracle_text': 'Psychosis Crawler\'s power and toughness are each equal to the number of cards in your hand.\nWhenever you draw a card, each opponent loses 1 life.',
            'expected': {
                'is_draw_payoff': True,
                'trigger_type': 'any_draw',
                'payoff_effects': ['life_loss']
            }
        },
        {
            'name': 'Faerie Vandal',
            'oracle_text': 'Flash\nFlying\nWhenever you draw your second card each turn, put a +1/+1 counter on Faerie Vandal.',
            'expected': {
                'is_draw_payoff': True,
                'trigger_type': 'second_draw',
                'payoff_effects': ['counter']
            }
        },
        {
            'name': 'Shabraz, the Skyshark',
            'oracle_text': 'Partner with Brallin, Skyshark Rider\nFlying\nWhenever you draw a card, put a +1/+1 counter on Shabraz, the Skyshark and you gain 1 life.',
            'expected': {
                'is_draw_payoff': True,
                'trigger_type': 'any_draw',
                'payoff_effects': ['counter', 'life']
            }
        }
    ]

    passed = 0
    for test in test_cases:
        card = {'name': test['name'], 'oracle_text': test['oracle_text']}
        result = extract_draw_payoffs(card)

        if result['is_draw_payoff'] == test['expected']['is_draw_payoff']:
            if not test['expected']['is_draw_payoff']:
                print(f"✓ {test['name']}: Correctly identified no draw payoff")
                passed += 1
            elif (result['trigger_type'] == test['expected']['trigger_type'] and
                  set(result['payoff_effects']) == set(test['expected']['payoff_effects'])):
                print(f"✓ {test['name']}: trigger={result['trigger_type']}, effects={result['payoff_effects']}")
                passed += 1
            else:
                print(f"✗ {test['name']}: Expected trigger={test['expected']['trigger_type']}, effects={test['expected']['payoff_effects']}")
                print(f"  Got trigger={result['trigger_type']}, effects={result['payoff_effects']}")
        else:
            print(f"✗ {test['name']}: Expected is_draw_payoff={test['expected']['is_draw_payoff']}, got {result['is_draw_payoff']}")

    print(f"\nDraw Payoffs: {passed}/{len(test_cases)} tests passed ({100*passed//len(test_cases)}%)")
    return passed == len(test_cases)


def run_all_tests():
    """Run all card advantage extractor tests"""
    print("\n" + "="*60)
    print("CARD ADVANTAGE EXTRACTOR TEST SUITE")
    print("="*60)

    results = []

    results.append(("Card Draw", test_card_draw()))
    results.append(("Wheel Effects", test_wheel_effects()))
    results.append(("Tutors", test_tutors()))
    results.append(("Mill Effects", test_mill_effects()))
    results.append(("Discard Effects", test_discard_effects()))
    results.append(("Looting Effects", test_looting_effects()))
    results.append(("Impulse Draw", test_impulse_draw()))
    results.append(("Draw Payoffs", test_draw_payoffs()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\n{'='*60}")
    print(f"Overall: {total_passed}/{total_tests} test suites passed ({100*total_passed//total_tests}%)")
    print("="*60)

    return all(passed for _, passed in results)


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
