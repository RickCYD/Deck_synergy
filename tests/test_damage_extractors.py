"""
Test suite for damage & life drain extractors
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.utils.damage_extractors import (
    extract_direct_damage,
    extract_burn_effects,
    extract_drain_effects,
    extract_life_gain,
    extract_creature_damage,
    classify_damage_effect
)


def test_direct_damage():
    """Test direct damage extraction (single target)"""
    print("=" * 60)
    print("TESTING DIRECT DAMAGE (SINGLE TARGET)")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
        },
        {
            'name': 'Shock',
            'oracle_text': 'Shock deals 2 damage to any target.'
        },
        {
            'name': 'Murder',
            'oracle_text': 'Destroy target creature.'
        },
        {
            'name': 'Lava Spike',
            'oracle_text': 'Lava Spike deals 3 damage to target player or planeswalker.'
        },
        {
            'name': 'Flame Slash',
            'oracle_text': 'Flame Slash deals 4 damage to target creature.'
        },
        {
            'name': 'Banefire',
            'oracle_text': 'Banefire deals X damage to any target. If X is 5 or more, this spell can\'t be countered and the damage can\'t be prevented.'
        },
        {
            'name': 'Lightning Strike',
            'oracle_text': 'Lightning Strike deals 3 damage to any target.'
        }
    ]

    for card in test_cards:
        damages = extract_direct_damage(card)
        print(f"\n{card['name']}:")
        if damages:
            for dmg in damages:
                print(f"  ✓ {dmg['type'].upper()} - {dmg['subtype']}")
                print(f"    Amount: {dmg['amount']} | Target: {dmg['target']}")
                print(f"    {dmg['description']}")
        else:
            print("  ✗ No direct damage detected")

    print()


def test_burn_effects():
    """Test burn effects (multiple targets)"""
    print("=" * 60)
    print("TESTING BURN EFFECTS (MULTIPLE TARGETS)")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Earthquake',
            'oracle_text': 'Earthquake deals X damage to each creature without flying and each player.'
        },
        {
            'name': 'Blasphemous Act',
            'oracle_text': 'This spell costs {1} less to cast for each creature on the battlefield. Blasphemous Act deals 13 damage to each creature.'
        },
        {
            'name': 'Sulfuric Vortex',
            'oracle_text': 'At the beginning of each player\'s upkeep, Sulfuric Vortex deals 2 damage to that player.'
        },
        {
            'name': 'Pyroclasm',
            'oracle_text': 'Pyroclasm deals 2 damage to each creature.'
        },
        {
            'name': 'Chain Reaction',
            'oracle_text': 'Chain Reaction deals X damage to each creature, where X is the number of creatures on the battlefield.'
        },
        {
            'name': 'Manabarbs',
            'oracle_text': 'Whenever a player taps a land for mana, Manabarbs deals 1 damage to that player.'
        },
        {
            'name': 'Arc Lightning',
            'oracle_text': 'Arc Lightning deals 3 damage divided as you choose among one, two, or three targets.'
        }
    ]

    for card in test_cards:
        burns = extract_burn_effects(card)
        print(f"\n{card['name']}:")
        if burns:
            for burn in burns:
                flags = []
                if burn.get('is_multiplayer'):
                    flags.append('MULTIPLAYER')
                if burn.get('is_board_damage'):
                    flags.append('BOARD DAMAGE')
                if burn.get('is_symmetrical'):
                    flags.append('SYMMETRICAL')
                if burn.get('is_divided'):
                    flags.append('DIVIDED')

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  ✓ {burn['type'].upper()} - {burn['subtype']}{flag_str}")
                print(f"    Amount: {burn['amount']} | Target: {burn['target']}")
                print(f"    {burn['description']}")
        else:
            print("  ✗ No burn effects detected")

    print()


def test_drain_effects():
    """Test life drain effects (damage + life gain)"""
    print("=" * 60)
    print("TESTING DRAIN EFFECTS (DAMAGE + LIFE GAIN)")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Gray Merchant of Asphodel',
            'oracle_text': 'When Gray Merchant of Asphodel enters the battlefield, each opponent loses X life, where X is your devotion to black. You gain life equal to the life lost this way.'
        },
        {
            'name': 'Kokusho, the Evening Star',
            'oracle_text': 'Flying. When Kokusho, the Evening Star dies, each opponent loses 5 life. You gain life equal to the life lost this way.'
        },
        {
            'name': 'Zulaport Cutthroat',
            'oracle_text': 'Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Blood Artist',
            'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Exsanguinate',
            'oracle_text': 'Each opponent loses X life. You gain life equal to the life lost this way.'
        },
        {
            'name': 'Drain Life',
            'oracle_text': 'Spend only black mana on X. Drain Life deals X damage to any target. You gain life equal to the damage dealt, but not more life than the player\'s life total before the damage was dealt.'
        },
        {
            'name': 'Vampire Nighthawk',
            'oracle_text': 'Flying, deathtouch, lifelink'
        },
        {
            'name': 'Painful Quandary',
            'oracle_text': 'Whenever an opponent casts a spell, that player loses 5 life unless they discard a card.'
        }
    ]

    for card in test_cards:
        drains = extract_drain_effects(card)
        print(f"\n{card['name']}:")
        if drains:
            for drain in drains:
                flags = []
                if drain.get('is_multiplayer'):
                    flags.append('MULTIPLAYER')
                if drain.get('is_single_target'):
                    flags.append('SINGLE TARGET')
                if drain.get('gains_life'):
                    flags.append('GAINS LIFE')
                if drain.get('is_symmetrical'):
                    flags.append('SYMMETRICAL')
                if drain.get('is_scaling'):
                    flags.append('SCALING')
                if drain.get('is_keyword'):
                    flags.append('KEYWORD')

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  ✓ {drain['type'].upper()} - {drain['subtype']}{flag_str}")
                print(f"    Amount: {drain['amount']} | Target: {drain['target']}")
                print(f"    {drain['description']}")
        else:
            print("  ✗ No drain effects detected")

    print()


def test_life_gain():
    """Test life gain effects"""
    print("=" * 60)
    print("TESTING LIFE GAIN EFFECTS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Soul Warden',
            'oracle_text': 'Whenever another creature enters the battlefield, you gain 1 life.'
        },
        {
            'name': 'Essence Warden',
            'oracle_text': 'Whenever another creature enters the battlefield, you gain 1 life.'
        },
        {
            'name': 'Rhox Faithmender',
            'oracle_text': 'Lifelink. If you would gain life, you gain twice that much life instead.'
        },
        {
            'name': 'Ajani\'s Pridemate',
            'oracle_text': 'Whenever you gain life, put a +1/+1 counter on Ajani\'s Pridemate.'
        },
        {
            'name': 'Rest for the Weary',
            'oracle_text': 'Target player gains 4 life. If you control more lands than an opponent, you gain 8 life instead.'
        },
        {
            'name': 'Congregate',
            'oracle_text': 'Target player gains 2 life for each creature on the battlefield.'
        },
        {
            'name': 'Swords to Plowshares',
            'oracle_text': 'Exile target creature. Its controller gains life equal to its power.'
        },
        {
            'name': 'Feed the Pack',
            'oracle_text': 'At the beginning of your end step, you may sacrifice a nontoken creature. If you do, create X 2/2 green Wolf creature tokens, where X is the sacrificed creature\'s toughness.'
        }
    ]

    for card in test_cards:
        gains = extract_life_gain(card)
        print(f"\n{card['name']}:")
        if gains:
            for gain in gains:
                flags = []
                if gain.get('is_triggered'):
                    flags.append('TRIGGERED')
                if gain.get('is_repeatable'):
                    flags.append('REPEATABLE')
                if gain.get('is_scaling'):
                    flags.append('SCALING')
                if gain.get('is_variable'):
                    flags.append('VARIABLE')
                if gain.get('is_symmetrical'):
                    flags.append('SYMMETRICAL')

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  ✓ {gain['type'].upper()} - {gain['subtype']}{flag_str}")
                print(f"    Amount: {gain['amount']}")
                print(f"    {gain['description']}")
        else:
            print("  ✗ No life gain detected")

    print()


def test_creature_damage():
    """Test creature-based damage triggers"""
    print("=" * 60)
    print("TESTING CREATURE DAMAGE TRIGGERS")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Torbran, Thane of Red Fell',
            'oracle_text': 'If a red source you would deal damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead.'
        },
        {
            'name': 'Fiery Emancipation',
            'oracle_text': 'If a source you control would deal damage to a permanent or player, it deals triple that damage instead.'
        },
        {
            'name': 'Psychosis Crawler',
            'oracle_text': 'Psychosis Crawler\'s power and toughness are each equal to the number of cards in your hand. Whenever you draw a card, Psychosis Crawler deals damage equal to the number of cards in your hand to each opponent.'
        },
        {
            'name': 'Niv-Mizzet, Parun',
            'oracle_text': 'This spell can\'t be countered. Flying. Whenever you draw a card, Niv-Mizzet, Parun deals 1 damage to any target. Whenever a player casts an instant or sorcery spell, you draw a card.'
        },
        {
            'name': 'Omnath, Locus of Rage',
            'oracle_text': 'Landfall — Whenever a land enters the battlefield under your control, create a 5/5 red and green Elemental creature token. Whenever Omnath, Locus of Rage or another Elemental you control dies, Omnath deals 3 damage to any target.'
        },
        {
            'name': 'Sword of Fire and Ice',
            'oracle_text': 'Equipped creature gets +2/+2 and has protection from red and from blue. Whenever equipped creature deals combat damage to a player, Sword of Fire and Ice deals 2 damage to any target and you draw a card.'
        },
        {
            'name': 'Gisela, Blade of Goldnight',
            'oracle_text': 'Flying, first strike. If a source would deal damage to an opponent or a permanent an opponent controls, that source deals double that damage to that permanent or player instead. If a source would deal damage to you or a permanent you control, prevent half that damage, rounded up.'
        }
    ]

    for card in test_cards:
        damages = extract_creature_damage(card)
        print(f"\n{card['name']}:")
        if damages:
            for dmg in damages:
                flags = []
                if dmg.get('is_triggered'):
                    flags.append('TRIGGERED')
                if dmg.get('is_repeatable'):
                    flags.append('REPEATABLE')
                if dmg.get('is_variable'):
                    flags.append('VARIABLE')
                if dmg.get('is_combat'):
                    flags.append('COMBAT')

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  ✓ {dmg['type'].upper()} - {dmg['subtype']}{flag_str}")
                print(f"    Amount: {dmg.get('amount', 'N/A')}")
                print(f"    {dmg['description']}")
        else:
            print("  ✗ No creature damage detected")

    print()


def test_comprehensive_classification():
    """Test full damage effect classification"""
    print("=" * 60)
    print("TESTING COMPREHENSIVE CLASSIFICATION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
        },
        {
            'name': 'Gray Merchant of Asphodel',
            'oracle_text': 'When Gray Merchant of Asphodel enters the battlefield, each opponent loses X life, where X is your devotion to black. You gain life equal to the life lost this way.'
        },
        {
            'name': 'Blasphemous Act',
            'oracle_text': 'This spell costs {1} less to cast for each creature on the battlefield. Blasphemous Act deals 13 damage to each creature.'
        },
        {
            'name': 'Soul Warden',
            'oracle_text': 'Whenever another creature enters the battlefield, you gain 1 life.'
        },
        {
            'name': 'Zulaport Cutthroat',
            'oracle_text': 'Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Counterspell',
            'oracle_text': 'Counter target spell.'
        }
    ]

    for card in test_cards:
        classification = classify_damage_effect(card)

        print(f"\n{classification['card_name']}:")
        print(f"  Has Damage Effects: {classification['has_damage_effects']}")
        print(f"  Has Life Gain: {classification['has_life_gain']}")
        print(f"  Strategy: {classification['strategy'].upper()}")
        print(f"  Total Effects: {classification['total_effects']}")
        print(f"  Estimated Damage: {classification['estimated_damage']}")
        print(f"  Multiplayer Focused: {classification['is_multiplayer_focused']}")
        print(f"  Has Lifelink: {classification['has_lifelink']}")

        if classification['direct_damages']:
            print(f"  Direct Damages: {len(classification['direct_damages'])}")
        if classification['burn_effects']:
            print(f"  Burn Effects: {len(classification['burn_effects'])}")
        if classification['drain_effects']:
            print(f"  Drain Effects: {len(classification['drain_effects'])}")
        if classification['life_gains']:
            print(f"  Life Gains: {len(classification['life_gains'])}")
        if classification['creature_damages']:
            print(f"  Creature Damages: {len(classification['creature_damages'])}")

    print()


def test_aristocrats_package():
    """Test detection of aristocrats strategy cards"""
    print("=" * 60)
    print("TESTING ARISTOCRATS PACKAGE DETECTION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Blood Artist',
            'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Zulaport Cutthroat',
            'oracle_text': 'Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Cruel Celebrant',
            'oracle_text': 'Whenever Cruel Celebrant or another creature or planeswalker you control dies, each opponent loses 1 life and you gain 1 life.'
        },
        {
            'name': 'Falkenrath Noble',
            'oracle_text': 'Flying. Whenever Falkenrath Noble or another creature dies, target player loses 1 life and you gain 1 life.'
        }
    ]

    print("\nAristocrats Strategy Cards:")
    aristocrats_count = 0
    for card in test_cards:
        classification = classify_damage_effect(card)
        if classification['strategy'] == 'drain':
            aristocrats_count += 1
            print(f"  ✓ {card['name']}")
            print(f"    Strategy: {classification['strategy']}")
            print(f"    Drain Effects: {len(classification['drain_effects'])}")

    print(f"\nTotal Aristocrats Cards Detected: {aristocrats_count}/4")
    print()


def test_burn_strategy():
    """Test detection of burn strategy cards"""
    print("=" * 60)
    print("TESTING BURN STRATEGY DETECTION")
    print("=" * 60)

    test_cards = [
        {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
        },
        {
            'name': 'Earthquake',
            'oracle_text': 'Earthquake deals X damage to each creature without flying and each player.'
        },
        {
            'name': 'Sulfuric Vortex',
            'oracle_text': 'At the beginning of each player\'s upkeep, Sulfuric Vortex deals 2 damage to that player.'
        },
        {
            'name': 'Pyroclasm',
            'oracle_text': 'Pyroclasm deals 2 damage to each creature.'
        }
    ]

    print("\nBurn Strategy Cards:")
    burn_count = 0
    for card in test_cards:
        classification = classify_damage_effect(card)
        if classification['strategy'] == 'burn':
            burn_count += 1
            print(f"  ✓ {card['name']}")
            print(f"    Strategy: {classification['strategy']}")
            print(f"    Estimated Damage: {classification['estimated_damage']}")

    print(f"\nTotal Burn Cards Detected: {burn_count}/{len(test_cards)}")
    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " DAMAGE & LIFE DRAIN EXTRACTOR TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_direct_damage()
    test_burn_effects()
    test_drain_effects()
    test_life_gain()
    test_creature_damage()
    test_comprehensive_classification()
    test_aristocrats_package()
    test_burn_strategy()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
