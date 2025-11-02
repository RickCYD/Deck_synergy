"""
Test the new damage/drain/burn synergy rules
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.synergy_engine.rules import (
    detect_aristocrats_synergy,
    detect_burn_synergy,
    detect_lifegain_payoffs,
    detect_damage_based_card_draw,
    detect_creature_damage_synergy
)


def test_aristocrats_synergy():
    """Test aristocrats combo detection"""
    print("=" * 60)
    print("TESTING ARISTOCRATS SYNERGY")
    print("=" * 60)

    # Blood Artist (drain effect) + Ashnod's Altar (sacrifice outlet)
    blood_artist = {
        'name': 'Blood Artist',
        'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.'
    }

    ashnods_altar = {
        'name': "Ashnod's Altar",
        'oracle_text': 'Sacrifice a creature: Add {C}{C}.'
    }

    result = detect_aristocrats_synergy(blood_artist, ashnods_altar)
    print(f"\n{blood_artist['name']} + {ashnods_altar['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Zulaport Cutthroat + Sengir, the Dark Baron (both drain effects)
    zulaport = {
        'name': 'Zulaport Cutthroat',
        'oracle_text': 'Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.'
    }

    sengir = {
        'name': 'Sengir, the Dark Baron',
        'oracle_text': 'Whenever another creature dies, put two +1/+1 counters on Sengir, the Dark Baron. Whenever another player loses the game, you gain life equal to that player\'s life total as the turn began. Partner'
    }

    result = detect_aristocrats_synergy(zulaport, sengir)
    print(f"\n{zulaport['name']} + {sengir['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Blood Artist + Bitterblossom (token generation)
    bitterblossom = {
        'name': 'Bitterblossom',
        'oracle_text': 'At the beginning of your upkeep, you lose 1 life and create a 1/1 black Faerie Rogue creature token with flying.'
    }

    result = detect_aristocrats_synergy(blood_artist, bitterblossom)
    print(f"\n{blood_artist['name']} + {bitterblossom['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_burn_synergy():
    """Test burn synergy detection"""
    print("=" * 60)
    print("TESTING BURN SYNERGY")
    print("=" * 60)

    # Torbran (damage amplifier) + Lightning Bolt (damage dealer)
    torbran = {
        'name': 'Torbran, Thane of Red Fell',
        'oracle_text': 'If a red source you control would deal damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead.'
    }

    lightning_bolt = {
        'name': 'Lightning Bolt',
        'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
    }

    result = detect_burn_synergy(torbran, lightning_bolt)
    print(f"\n{torbran['name']} + {lightning_bolt['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Sulfuric Vortex + Manabarbs (both multiplayer burn)
    sulfuric_vortex = {
        'name': 'Sulfuric Vortex',
        'oracle_text': 'At the beginning of each player\'s upkeep, Sulfuric Vortex deals 2 damage to that player.'
    }

    manabarbs = {
        'name': 'Manabarbs',
        'oracle_text': 'Whenever a player taps a land for mana, Manabarbs deals 1 damage to that player.'
    }

    result = detect_burn_synergy(sulfuric_vortex, manabarbs)
    print(f"\n{sulfuric_vortex['name']} + {manabarbs['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_lifegain_synergy():
    """Test lifegain synergy detection"""
    print("=" * 60)
    print("TESTING LIFEGAIN SYNERGY")
    print("=" * 60)

    # Ajani's Pridemate (lifegain payoff) + Soul Warden (lifegain source)
    pridemate = {
        'name': "Ajani's Pridemate",
        'oracle_text': 'Whenever you gain life, put a +1/+1 counter on Ajani\'s Pridemate.'
    }

    soul_warden = {
        'name': 'Soul Warden',
        'oracle_text': 'Whenever another creature enters the battlefield, you gain 1 life.'
    }

    result = detect_lifegain_payoffs(pridemate, soul_warden)
    print(f"\n{pridemate['name']} + {soul_warden['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_damage_draw_engine():
    """Test damage/draw engine detection"""
    print("=" * 60)
    print("TESTING DAMAGE/DRAW ENGINE")
    print("=" * 60)

    # Niv-Mizzet (draws when dealing damage, deals damage when drawing) + Psychosis Crawler
    niv_mizzet = {
        'name': 'Niv-Mizzet, Parun',
        'oracle_text': 'This spell can\'t be countered. Flying. Whenever you draw a card, Niv-Mizzet, Parun deals 1 damage to any target. Whenever a player casts an instant or sorcery spell, you draw a card.'
    }

    psychosis_crawler = {
        'name': 'Psychosis Crawler',
        'oracle_text': 'Psychosis Crawler\'s power and toughness are each equal to the number of cards in your hand. Whenever you draw a card, Psychosis Crawler deals damage equal to the number of cards in your hand to each opponent.'
    }

    result = detect_damage_based_card_draw(niv_mizzet, psychosis_crawler)
    print(f"\n{niv_mizzet['name']} + {psychosis_crawler['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_combat_damage_synergy():
    """Test combat damage synergy detection"""
    print("=" * 60)
    print("TESTING COMBAT DAMAGE SYNERGY")
    print("=" * 60)

    # Sword of Fire and Ice (combat damage trigger) + Coat of Arms (power boost)
    sword = {
        'name': 'Sword of Fire and Ice',
        'oracle_text': 'Equipped creature gets +2/+2 and has protection from red and from blue. Whenever equipped creature deals combat damage to a player, Sword of Fire and Ice deals 2 damage to any target and you draw a card.'
    }

    coat = {
        'name': 'Coat of Arms',
        'oracle_text': 'Each creature gets +1/+1 for each other creature on the battlefield that shares at least one creature type with it.'
    }

    result = detect_creature_damage_synergy(sword, coat)
    print(f"\n{sword['name']} + {coat['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def run_all_tests():
    """Run all synergy tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " DAMAGE/DRAIN/BURN SYNERGY TEST SUITE ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    test_aristocrats_synergy()
    test_burn_synergy()
    test_lifegain_synergy()
    test_damage_draw_engine()
    test_combat_damage_synergy()

    print("=" * 60)
    print("ALL SYNERGY TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
