"""
High-value synergy rule tests
Validates detection for key two-card interactions:
- Tap/Untap engine (Isochron Scepter + Dramatic Reversal)
- Extra combat mana loop (Aggravated Assault + Neheb)
- Enchantress engine (Enchantress's Presence + Rancor)
- Spellslinger engine (Young Pyromancer + Opt)
- Fling finisher (Fling + Ball Lightning)
- Tribal synergy (Elvish Archdruid + Llanowar Elves)
"""

import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.synergy_engine.rules import (
    detect_tap_untap_engines,
    detect_extra_combat_synergy,
    detect_enchantress_effects,
    detect_spellslinger_payoffs,
    detect_fling_effects,
    detect_tribal_synergy,
)


def test_tap_untap_scepter_reversal():
    scepter = {
        'name': 'Isochron Scepter',
        'oracle_text': 'Imprint — When Isochron Scepter enters the battlefield, you may exile an instant card with mana value 2 from your hand. {2}, {T}: You may copy the exiled card.'
    }
    reversal = {
        'name': 'Dramatic Reversal',
        'type_line': 'Instant',
        'oracle_text': 'Untap all nonland permanents you control.'
    }
    res = detect_tap_untap_engines(scepter, reversal)
    print("Tap/Untap:", bool(res), (res or {}).get('name'))

def test_tap_untap_negative_basic_mana():
    # Dramatic Reversal + Sol Ring (basic mana ability only) should not count
    reversal = {
        'name': 'Dramatic Reversal',
        'type_line': 'Instant',
        'oracle_text': 'Untap all nonland permanents you control.'
    }
    sol_ring = {
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': '{T}: Add {C}{C}.'
    }
    res = detect_tap_untap_engines(reversal, sol_ring)
    print("Tap/Untap (negative):", bool(res))


def test_extra_combat_assault_neheb():
    assault = {
        'name': 'Aggravated Assault',
        'oracle_text': '{3}{R}{R}: Untap all creatures you control. After this main phase, there is an additional combat phase followed by an additional main phase.'
    }
    neheb = {
        'name': 'Neheb, the Eternal',
        'oracle_text': 'At the beginning of your postcombat main phase, add {R} for each 1 life your opponents have lost this turn.'
    }
    res = detect_extra_combat_synergy(assault, neheb)
    print("Extra Combat:", bool(res), (res or {}).get('name'))

def test_extra_combat_negative():
    assault = {
        'name': 'Aggravated Assault',
        'oracle_text': '{3}{R}{R}: Untap all creatures you control. After this main phase, there is an additional combat phase followed by an additional main phase.'
    }
    prism = {
        'name': 'Prophetic Prism',
        'type_line': 'Artifact',
        'oracle_text': 'When Prophetic Prism enters the battlefield, draw a card. {1}, {T}: Add one mana of any color.'
    }
    res = detect_extra_combat_synergy(assault, prism)
    print("Extra Combat (negative):", bool(res))


def test_enchantress_presence_rancor():
    presence = {
        'name': "Enchantress's Presence",
        'type_line': 'Enchantment',
        'oracle_text': 'Whenever you cast an enchantment spell, draw a card.'
    }
    rancor = {
        'name': 'Rancor',
        'type_line': 'Enchantment — Aura',
        'oracle_text': 'Enchant creature. Enchanted creature gets +2/+0 and has trample. When Rancor is put into a graveyard from the battlefield, return Rancor to its owner\'s hand.'
    }
    res = detect_enchantress_effects(presence, rancor)
    print("Enchantress:", bool(res), (res or {}).get('name'))

def test_enchantress_negative():
    presence = {
        'name': "Enchantress's Presence",
        'type_line': 'Enchantment',
        'oracle_text': 'Whenever you cast an enchantment spell, draw a card.'
    }
    opt = {
        'name': 'Opt',
        'type_line': 'Instant',
        'oracle_text': 'Scry 1. Draw a card.'
    }
    res = detect_enchantress_effects(presence, opt)
    print("Enchantress (negative):", bool(res))


def test_spellslinger_pyromancer_opt():
    yp = {
        'name': 'Young Pyromancer',
        'type_line': 'Creature — Human Shaman',
        'oracle_text': 'Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token.'
    }
    opt = {
        'name': 'Opt',
        'type_line': 'Instant',
        'oracle_text': 'Scry 1. Draw a card.'
    }
    res = detect_spellslinger_payoffs(yp, opt)
    print("Spellslinger:", bool(res), (res or {}).get('name'))

def test_spellslinger_negative():
    yp = {
        'name': 'Young Pyromancer',
        'type_line': 'Creature — Human Shaman',
        'oracle_text': 'Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token.'
    }
    sol_ring = {
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': '{T}: Add {C}{C}.'
    }
    res = detect_spellslinger_payoffs(yp, sol_ring)
    print("Spellslinger (negative):", bool(res))


def test_fling_ball_lightning():
    fling = {
        'name': 'Fling',
        'type_line': 'Instant',
        'oracle_text': 'As an additional cost to cast this spell, sacrifice a creature. Fling deals damage equal to the sacrificed creature\'s power to any target.'
    }
    ball = {
        'name': 'Ball Lightning',
        'type_line': 'Creature — Elemental',
        'oracle_text': 'Trample, haste. At the beginning of the end step, sacrifice Ball Lightning.'
    }
    res = detect_fling_effects(fling, ball)
    print("Fling:", bool(res), (res or {}).get('name'))

def test_fling_negative():
    fling = {
        'name': 'Fling',
        'type_line': 'Instant',
        'oracle_text': 'As an additional cost to cast this spell, sacrifice a creature. Fling deals damage equal to the sacrificed creature\'s power to any target.'
    }
    memnite = {
        'name': 'Memnite',
        'type_line': 'Artifact Creature — Construct',
        'power': '1',
        'oracle_text': ''
    }
    res = detect_fling_effects(fling, memnite)
    print("Fling (negative):", bool(res))


def test_tribal_archdruid_llanowar():
    archdruid = {
        'name': 'Elvish Archdruid',
        'type_line': 'Creature — Elf Druid',
        'card_types': {'main_types': ['Creature'], 'subtypes': ['Elf', 'Druid']},
        'oracle_text': 'Other Elf creatures you control get +1/+1.'
    }
    llanowar = {
        'name': 'Llanowar Elves',
        'type_line': 'Creature — Elf Druid',
        'card_types': {'main_types': ['Creature'], 'subtypes': ['Elf', 'Druid']},
        'oracle_text': '{T}: Add {G}.'
    }
    res = detect_tribal_synergy(archdruid, llanowar)
    print("Tribal:", bool(res), (res or {}).get('name'))

def test_tribal_negative():
    archdruid = {
        'name': 'Elvish Archdruid',
        'type_line': 'Creature — Elf Druid',
        'card_types': {'main_types': ['Creature'], 'subtypes': ['Elf', 'Druid']},
        'oracle_text': 'Other Elf creatures you control get +1/+1.'
    }
    goblin = {
        'name': 'Goblin Guide',
        'type_line': 'Creature — Goblin Scout',
        'card_types': {'main_types': ['Creature'], 'subtypes': ['Goblin', 'Scout']},
        'oracle_text': 'Haste. Whenever Goblin Guide attacks, defending player reveals the top card of their library.'
    }
    res = detect_tribal_synergy(archdruid, goblin)
    print("Tribal (negative):", bool(res))
