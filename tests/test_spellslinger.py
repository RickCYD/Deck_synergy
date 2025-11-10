"""
Test the Spellslinger archetype synergy rules
Tests cast triggers, prowess/magecraft, storm, spell copy, cost reduction, flashback, and cantrips
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy')

from src.synergy_engine.rules import (
    detect_spellslinger_payoffs,
    detect_storm_synergy,
    detect_copy_synergy,
    detect_aetherflux_reservoir_synergy,
    detect_spell_cost_reduction,
    detect_flashback_synergy,
    detect_cantrip_synergy
)


def test_spellslinger_payoffs():
    """Test basic spellslinger cast triggers with cheap spells"""
    print("=" * 60)
    print("TESTING SPELLSLINGER PAYOFFS")
    print("=" * 60)

    # Young Pyromancer (cast trigger) + Lightning Bolt (cheap instant)
    young_pyromancer = {
        'name': 'Young Pyromancer',
        'type_line': 'Creature — Human Shaman',
        'oracle_text': 'whenever you cast an instant or sorcery spell, create a 1/1 red elemental creature token.',
        'cmc': 2,
        'keywords': []
    }

    lightning_bolt = {
        'name': 'Lightning Bolt',
        'type_line': 'Instant',
        'oracle_text': 'lightning bolt deals 3 damage to any target.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_spellslinger_payoffs(young_pyromancer, lightning_bolt)
    print(f"\n{young_pyromancer['name']} + {lightning_bolt['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Monastery Mentor (cast trigger) + Ponder (cheap sorcery)
    monastery_mentor = {
        'name': 'Monastery Mentor',
        'type_line': 'Creature — Human Monk',
        'oracle_text': 'prowess. whenever you cast a noncreature spell, create a 1/1 white monk creature token with prowess.',
        'cmc': 3,
        'keywords': ['prowess']
    }

    ponder = {
        'name': 'Ponder',
        'type_line': 'Sorcery',
        'oracle_text': 'look at the top three cards of your library, then put them back in any order. you may shuffle. draw a card.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_spellslinger_payoffs(monastery_mentor, ponder)
    print(f"\n{monastery_mentor['name']} + {ponder['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Archmage Emeritus (magecraft) + Brainstorm (cheap instant)
    archmage_emeritus = {
        'name': 'Archmage Emeritus',
        'type_line': 'Creature — Human Wizard',
        'oracle_text': 'magecraft — whenever you cast or copy an instant or sorcery spell, draw a card.',
        'cmc': 4,
        'keywords': []
    }

    brainstorm = {
        'name': 'Brainstorm',
        'type_line': 'Instant',
        'oracle_text': 'draw three cards, then put two cards from your hand on top of your library in any order.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_spellslinger_payoffs(archmage_emeritus, brainstorm)
    print(f"\n{archmage_emeritus['name']} + {brainstorm['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_storm_synergy():
    """Test storm mechanics with cheap enablers"""
    print("=" * 60)
    print("TESTING STORM SYNERGY")
    print("=" * 60)

    # Grapeshot (storm) + Seething Song (ritual)
    grapeshot = {
        'name': 'Grapeshot',
        'type_line': 'Instant',
        'oracle_text': 'grapeshot deals 1 damage to any target. storm (when you cast this spell, copy it for each spell cast before it this turn. you may choose new targets for the copies.)',
        'cmc': 2,
        'keywords': ['storm']
    }

    seething_song = {
        'name': 'Seething Song',
        'type_line': 'Instant',
        'oracle_text': 'add {r}{r}{r}{r}{r}.',
        'cmc': 3,
        'keywords': []
    }

    result = detect_storm_synergy(grapeshot, seething_song)
    print(f"\n{grapeshot['name']} + {seething_song['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Empty the Warrens (storm) + Gitaxian Probe (cheap cantrip)
    empty_warrens = {
        'name': 'Empty the Warrens',
        'type_line': 'Sorcery',
        'oracle_text': 'create two 1/1 red goblin creature tokens. storm',
        'cmc': 4,
        'keywords': ['storm']
    }

    gitaxian_probe = {
        'name': 'Gitaxian Probe',
        'type_line': 'Sorcery',
        'oracle_text': '({u/p} can be paid with either {u} or 2 life.) look at target player\'s hand. draw a card.',
        'cmc': 0,
        'keywords': []
    }

    result = detect_storm_synergy(empty_warrens, gitaxian_probe)
    print(f"\n{empty_warrens['name']} + {gitaxian_probe['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_copy_synergy():
    """Test spell copy effects"""
    print("=" * 60)
    print("TESTING SPELL COPY SYNERGY")
    print("=" * 60)

    # Dualcaster Mage (copy spell) + Counterspell (instant)
    dualcaster_mage = {
        'name': 'Dualcaster Mage',
        'type_line': 'Creature — Human Wizard',
        'oracle_text': 'flash. when dualcaster mage enters the battlefield, copy target instant or sorcery spell. you may choose new targets for the copy.',
        'cmc': 3,
        'keywords': ['flash']
    }

    counterspell = {
        'name': 'Counterspell',
        'type_line': 'Instant',
        'oracle_text': 'counter target spell.',
        'cmc': 2,
        'keywords': []
    }

    result = detect_copy_synergy(dualcaster_mage, counterspell)
    print(f"\n{dualcaster_mage['name']} + {counterspell['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Twincast (copy spell) + Cruel Ultimatum (sorcery)
    twincast = {
        'name': 'Twincast',
        'type_line': 'Instant',
        'oracle_text': 'copy target instant or sorcery spell. you may choose new targets for the copy.',
        'cmc': 2,
        'keywords': []
    }

    cruel_ultimatum = {
        'name': 'Cruel Ultimatum',
        'type_line': 'Sorcery',
        'oracle_text': 'target opponent sacrifices a creature, discards three cards, then loses 5 life. you return a creature card from your graveyard to your hand, draw three cards, then gain 5 life.',
        'cmc': 7,
        'keywords': []
    }

    result = detect_copy_synergy(twincast, cruel_ultimatum)
    print(f"\n{twincast['name']} + {cruel_ultimatum['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_aetherflux_reservoir_synergy():
    """Test Aetherflux Reservoir-like life gain on cast triggers"""
    print("=" * 60)
    print("TESTING AETHERFLUX RESERVOIR SYNERGY")
    print("=" * 60)

    # Aetherflux Reservoir (gains life on cast) + Lightning Bolt (cheap spell)
    aetherflux_reservoir = {
        'name': 'Aetherflux Reservoir',
        'type_line': 'Artifact',
        'oracle_text': 'whenever you cast a spell, you gain 1 life for each spell you\'ve cast this turn. pay 50 life: aetherflux reservoir deals 50 damage to any target.',
        'cmc': 4,
        'keywords': []
    }

    lightning_bolt = {
        'name': 'Lightning Bolt',
        'type_line': 'Instant',
        'oracle_text': 'lightning bolt deals 3 damage to any target.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_aetherflux_reservoir_synergy(aetherflux_reservoir, lightning_bolt)
    print(f"\n{aetherflux_reservoir['name']} + {lightning_bolt['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Aetherflux Reservoir + Bolas's Citadel (life gain payoff)
    bolas_citadel = {
        'name': "Bolas's Citadel",
        'type_line': 'Legendary Artifact',
        'oracle_text': 'you may look at the top card of your library any time. you may cast spells from the top of your library. if you cast a spell this way, pay life equal to its mana value rather than pay its mana cost. {t}, sacrifice ten nonland permanents: each opponent loses 10 life.',
        'cmc': 6,
        'keywords': []
    }

    result = detect_aetherflux_reservoir_synergy(aetherflux_reservoir, bolas_citadel)
    print(f"\n{aetherflux_reservoir['name']} + {bolas_citadel['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Sanguine Sacrament (gains life on cast) + Counterspell
    sanguine_sacrament = {
        'name': 'Sanguine Sacrament',
        'type_line': 'Instant',
        'oracle_text': 'you gain twice x life. put sanguine sacrament on the bottom of its owner\'s library.',
        'cmc': 3,
        'keywords': []
    }

    print()


def test_spell_cost_reduction():
    """Test spell cost reduction synergies"""
    print("=" * 60)
    print("TESTING SPELL COST REDUCTION")
    print("=" * 60)

    # Goblin Electromancer (cost reducer) + Shock (instant)
    goblin_electromancer = {
        'name': 'Goblin Electromancer',
        'type_line': 'Creature — Goblin Wizard',
        'oracle_text': 'instant and sorcery spells you cast cost {1} less to cast.',
        'cmc': 2,
        'keywords': []
    }

    shock = {
        'name': 'Shock',
        'type_line': 'Instant',
        'oracle_text': 'shock deals 2 damage to any target.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_spell_cost_reduction(goblin_electromancer, shock)
    print(f"\n{goblin_electromancer['name']} + {shock['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Baral, Chief of Compliance (cost reducer) + Cancel (sorcery)
    baral = {
        'name': 'Baral, Chief of Compliance',
        'type_line': 'Legendary Creature — Human Wizard',
        'oracle_text': 'instant and sorcery spells you cast cost {1} less to cast. whenever a spell or ability you control counters a spell, you may draw a card. if you do, discard a card.',
        'cmc': 2,
        'keywords': []
    }

    cancel = {
        'name': 'Cancel',
        'type_line': 'Instant',
        'oracle_text': 'counter target spell.',
        'cmc': 3,
        'keywords': []
    }

    result = detect_spell_cost_reduction(baral, cancel)
    print(f"\n{baral['name']} + {cancel['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_flashback_synergy():
    """Test flashback and rebound synergies"""
    print("=" * 60)
    print("TESTING FLASHBACK SYNERGY")
    print("=" * 60)

    # Faithless Looting (flashback) + Careful Study (discard enabler)
    faithless_looting = {
        'name': 'Faithless Looting',
        'type_line': 'Sorcery',
        'oracle_text': 'draw two cards, then discard two cards. flashback {2}{r}',
        'cmc': 1,
        'keywords': ['flashback']
    }

    careful_study = {
        'name': 'Careful Study',
        'type_line': 'Sorcery',
        'oracle_text': 'draw two cards, then discard two cards.',
        'cmc': 1,
        'keywords': []
    }

    result = detect_flashback_synergy(faithless_looting, careful_study)
    print(f"\n{faithless_looting['name']} + {careful_study['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Stitch in Time (rebound-like) + Young Pyromancer (spell trigger)
    distortion_strike = {
        'name': 'Distortion Strike',
        'type_line': 'Sorcery',
        'oracle_text': 'target creature gets +1/+0 until end of turn and can\'t be blocked this turn. rebound',
        'cmc': 1,
        'keywords': ['rebound']
    }

    young_pyromancer = {
        'name': 'Young Pyromancer',
        'type_line': 'Creature — Human Shaman',
        'oracle_text': 'whenever you cast an instant or sorcery spell, create a 1/1 red elemental creature token.',
        'cmc': 2,
        'keywords': []
    }

    result = detect_flashback_synergy(distortion_strike, young_pyromancer)
    print(f"\n{distortion_strike['name']} + {young_pyromancer['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


def test_cantrip_synergy():
    """Test cantrip synergies with spell velocity decks"""
    print("=" * 60)
    print("TESTING CANTRIP SYNERGY")
    print("=" * 60)

    # Opt (cantrip) + Monastery Mentor (spell velocity)
    opt = {
        'name': 'Opt',
        'type_line': 'Instant',
        'oracle_text': 'scry 1. draw a card.',
        'cmc': 1,
        'keywords': []
    }

    monastery_mentor = {
        'name': 'Monastery Mentor',
        'type_line': 'Creature — Human Monk',
        'oracle_text': 'prowess. whenever you cast a noncreature spell, create a 1/1 white monk creature token with prowess.',
        'cmc': 3,
        'keywords': ['prowess']
    }

    result = detect_cantrip_synergy(opt, monastery_mentor)
    print(f"\n{opt['name']} + {monastery_mentor['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Preordain (cantrip) + Grapeshot (storm)
    preordain = {
        'name': 'Preordain',
        'type_line': 'Sorcery',
        'oracle_text': 'scry 2, then draw a card.',
        'cmc': 1,
        'keywords': []
    }

    grapeshot = {
        'name': 'Grapeshot',
        'type_line': 'Instant',
        'oracle_text': 'grapeshot deals 1 damage to any target. storm',
        'cmc': 2,
        'keywords': ['storm']
    }

    result = detect_cantrip_synergy(preordain, grapeshot)
    print(f"\n{preordain['name']} + {grapeshot['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    # Gitaxian Probe (cantrip) + Archmage Emeritus (magecraft)
    gitaxian_probe = {
        'name': 'Gitaxian Probe',
        'type_line': 'Sorcery',
        'oracle_text': '({u/p} can be paid with either {u} or 2 life.) look at target player\'s hand. draw a card.',
        'cmc': 0,
        'keywords': []
    }

    archmage_emeritus = {
        'name': 'Archmage Emeritus',
        'type_line': 'Creature — Human Wizard',
        'oracle_text': 'magecraft — whenever you cast or copy an instant or sorcery spell, draw a card.',
        'cmc': 4,
        'keywords': []
    }

    result = detect_cantrip_synergy(gitaxian_probe, archmage_emeritus)
    print(f"\n{gitaxian_probe['name']} + {archmage_emeritus['name']}:")
    if result:
        print(f"  ✓ {result['name']} (value: {result['value']})")
        print(f"    {result['description']}")
        print(f"    Category: {result['category']}/{result['subcategory']}")
    else:
        print("  ✗ No synergy detected")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SPELLSLINGER ARCHETYPE TEST SUITE")
    print("=" * 60 + "\n")

    test_spellslinger_payoffs()
    test_storm_synergy()
    test_copy_synergy()
    test_aetherflux_reservoir_synergy()
    test_spell_cost_reduction()
    test_flashback_synergy()
    test_cantrip_synergy()

    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
