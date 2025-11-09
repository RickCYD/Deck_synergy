import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from boardstate import BoardState
from simulate_game import Card
from oracle_text_parser import parse_etb_triggers_from_oracle


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


def test_proliferate_action():
    c1 = Card(
        name="C1",
        type="Creature",
        mana_cost="",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    c1.add_counter("+1/+1")

    c2 = Card(
        name="C2",
        type="Artifact",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    c2.add_counter("charge")

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(c1)
    board.artifacts.append(c2)

    board.proliferate()

    assert c1.counters.get("+1/+1") == 2
    assert c2.counters.get("charge") == 2


def test_parse_etb_proliferate_clause():
    text = "When Test Card enters the battlefield, proliferate."
    triggers = parse_etb_triggers_from_oracle(text)
    assert triggers

    c1 = Card(
        name="C1",
        type="Creature",
        mana_cost="",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    c1.add_counter("+1/+1")

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(c1)

    triggers[0].effect(board)

    assert c1.counters.get("+1/+1") == 2
