import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from deck_loader import _df_to_cards
from oracle_text_parser import parse_attack_triggers_from_oracle, parse_damage_triggers_from_oracle
from boardstate import BoardState
from simulate_game import Card


def create_dummy_commander():
    return Card(
        name="Dummy Commander",
        type="Commander",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )


def test_parse_attack_draw_clause():
    text = "Whenever Test Creature attacks, draw a card."
    triggers = parse_attack_triggers_from_oracle(text)
    assert triggers
    assert triggers[0].event == "attack"
    assert "draw 1 card" in triggers[0].description


def test_parse_attack_haste_clause():
    text = "Whenever a creature with haste attacks, draw a card."
    triggers = parse_attack_triggers_from_oracle(text)
    assert triggers
    trig = triggers[0]
    assert trig.event == "attack"
    assert trig.requires_haste is True
    assert trig.requires_flash is False


def test_parse_attack_with_other_legendary():
    text = "Whenever you attack with Merry and another legendary creature, draw a card."
    triggers = parse_attack_triggers_from_oracle(text)
    assert triggers
    trig = triggers[0]
    assert trig.event == "attack"
    assert trig.requires_another_legendary is True


def test_parse_damage_trigger_clause():
    text = "Whenever a creature you control with flash or haste is dealt damage, create a tapped Treasure token."
    triggers = parse_damage_triggers_from_oracle(text)
    assert triggers
    assert triggers[0].event == "damage"


def test_df_to_cards_attack_trigger_parsing():
    df = pd.DataFrame([
        {
            "Name": "Aggressive Goblin",
            "Type": "Creature",
            "ManaCost": "1R",
            "OracleText": "Whenever Aggressive Goblin attacks, draw a card.",
        }
    ])
    cards, commander, names = _df_to_cards(df)
    trig = cards[0].triggered_abilities
    assert trig
    assert trig[0].event == "attack"


def test_attack_trigger_executes():
    trig = parse_attack_triggers_from_oracle(
        "Whenever This attacks, draw a card."
    )[0]
    attacker = Card(
        name="Attacker",
        type="Creature",
        mana_cost="1G",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        triggered_abilities=[trig],
    )
    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(attacker)
    board.library = [
        Card(name="Forest", type="Basic Land", mana_cost="", power=0, toughness=0,
             produces_colors=[], mana_production=1, etb_tapped=False,
             etb_tapped_conditions={}, has_haste=False),
        Card(name="Forest2", type="Basic Land", mana_cost="", power=0, toughness=0,
             produces_colors=[], mana_production=1, etb_tapped=False,
             etb_tapped_conditions={}, has_haste=False),
    ]
    board._execute_triggers("attack", attacker)
    assert len(board.hand) == 1


def test_attack_trigger_requires_haste():
    trig = parse_attack_triggers_from_oracle(
        "Whenever a creature with haste attacks, draw a card."
    )[0]
    hasty = Card(
        name="Hasty", type="Creature", mana_cost="", power=1, toughness=1,
        produces_colors=[], mana_production=0, etb_tapped=False,
        etb_tapped_conditions={}, has_haste=True, triggered_abilities=[trig]
    )
    slow = Card(
        name="Slow", type="Creature", mana_cost="", power=1, toughness=1,
        produces_colors=[], mana_production=0, etb_tapped=False,
        etb_tapped_conditions={}, has_haste=False, triggered_abilities=[trig]
    )
    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.library = [
        Card(name="Forest", type="Basic Land", mana_cost="", power=0, toughness=0,
             produces_colors=[], mana_production=1, etb_tapped=False,
             etb_tapped_conditions={}, has_haste=False),
        Card(name="Forest2", type="Basic Land", mana_cost="", power=0, toughness=0,
             produces_colors=[], mana_production=1, etb_tapped=False,
             etb_tapped_conditions={}, has_haste=False),
    ]
    board.creatures.extend([hasty, slow])
    board.attack(hasty, verbose=False)
    assert len(board.hand) == 1
    board.attack(slow, verbose=False)
    assert len(board.hand) == 1


def test_attack_trigger_requires_flash():
    trig = parse_attack_triggers_from_oracle(
        "Whenever a creature with flash attacks, draw a card."
    )[0]
    assert trig.requires_flash is True
    flasher = Card(
        name="Flashy", type="Creature", mana_cost="", power=1, toughness=1,
        produces_colors=[], mana_production=0, etb_tapped=False,
        etb_tapped_conditions={}, has_haste=False, has_flash=True,
        triggered_abilities=[trig]
    )
    normal = Card(
        name="Normal", type="Creature", mana_cost="", power=1, toughness=1,
        produces_colors=[], mana_production=0, etb_tapped=False,
        etb_tapped_conditions={}, has_haste=False, has_flash=False,
        triggered_abilities=[trig]
    )
    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.library = [Card(name="Forest", type="Basic Land", mana_cost="", power=0, toughness=0,
                          produces_colors=[], mana_production=1, etb_tapped=False,
                          etb_tapped_conditions={}, has_haste=False)]
    board.creatures.extend([flasher, normal])
    board.attack(flasher, verbose=False)
    assert len(board.hand) == 1
    board.attack(normal, verbose=False)
    assert len(board.hand) == 1
