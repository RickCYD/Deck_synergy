import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mtg_abilities import TriggeredAbility
from simulate_game import Card
from boardstate import BoardState
from deck_loader import _df_to_cards
import pandas as pd


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


def test_etb_draw_trigger():
    def effect(board_state):
        board_state.draw_card(1)

    trigger = TriggeredAbility(event="etb", effect=effect, description="draw 1 card")
    drawer = Card(
        name="Elvish Visionary",
        type="Creature",
        mana_cost="1G",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        triggered_abilities=[trigger],
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    # Library needs a card to draw
    board.library = [Card(name="Forest", type="Basic Land", mana_cost="", power=0, toughness=0,
                          produces_colors=[], mana_production=1, etb_tapped=False,
                          etb_tapped_conditions={}, has_haste=False)]
    board.hand.append(drawer)
    board.mana_pool = [("G",), ("C",)]  # enough to pay 1G
    board.play_card(drawer, verbose=False)

    # After trigger, hand should contain drawn card (not the creature)
    assert any(c.name == "Forest" for c in board.hand)


def test_sonic_attack_adds_counters_to_hasty_creatures():
    sonic_text = (
        "Haste\nGotta Go Fast — Whenever Sonic the Hedgehog attacks, put a +1/+1 counter on each creature you control with flash or haste.\n"\
        "Whenever a creature you control with flash or haste is dealt damage, create a tapped Treasure token."
    )
    df = pd.DataFrame([
        {
            "Name": "Hasty Buddy",
            "Type": "Creature",
            "ManaCost": "",
            "Power": 2,
            "Toughness": 2,
            "HasHaste": True,
            "Commander": False,
            "OracleText": "",
        },
        {
            "Name": "Sonic the Hedgehog",
            "Type": "Creature",
            "ManaCost": "",
            "Power": 3,
            "Toughness": 3,
            "HasHaste": True,
            "Commander": False,
            "OracleText": sonic_text,
        },
        {
            "Name": "Boss",
            "Type": "Commander",
            "ManaCost": "",
            "Power": 0,
            "Toughness": 0,
            "Commander": True,
            "OracleText": "",
        },
    ])

    cards, commander, _ = _df_to_cards(df)
    board = BoardState(cards, commander)
    for c in cards:
        board.creatures.append(c)
        board._add_abilities_from_card(c)

    sonic = next(c for c in board.creatures if c.name == "Sonic the Hedgehog")
    buddy = next(c for c in board.creatures if c.name == "Hasty Buddy")

    board.attack(sonic, verbose=False)

    assert buddy.counters.get("+1/+1", 0) == 1
    assert sonic.counters.get("+1/+1", 0) == 1


def test_sonic_damage_creates_treasure_token():
    sonic_text = (
        "Haste\nGotta Go Fast — Whenever Sonic the Hedgehog attacks, put a +1/+1 counter on each creature you control with flash or haste.\n"\
        "Whenever a creature you control with flash or haste is dealt damage, create a tapped Treasure token."
    )
    df = pd.DataFrame([
        {
            "Name": "Hasty Buddy",
            "Type": "Creature",
            "ManaCost": "",
            "Power": 2,
            "Toughness": 2,
            "HasHaste": True,
            "Commander": False,
            "OracleText": "",
        },
        {
            "Name": "Sonic the Hedgehog",
            "Type": "Creature",
            "ManaCost": "",
            "Power": 3,
            "Toughness": 3,
            "HasHaste": True,
            "Commander": False,
            "OracleText": sonic_text,
        },
        {
            "Name": "Boss",
            "Type": "Commander",
            "ManaCost": "",
            "Power": 0,
            "Toughness": 0,
            "Commander": True,
            "OracleText": "",
        },
    ])

    cards, commander, _ = _df_to_cards(df)
    board = BoardState(cards, commander)
    for c in cards:
        board.creatures.append(c)
        board._add_abilities_from_card(c)

    buddy = next(c for c in board.creatures if c.name == "Hasty Buddy")

    board.deal_damage(buddy, 1)

    assert len(board.artifacts) == 1
    assert getattr(board.artifacts[0], "tapped", False) is True
