import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from deck_loader import _df_to_cards
from oracle_text_parser import parse_etb_triggers_from_oracle
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


def test_df_to_cards_draw_property():
    df = pd.DataFrame([
        {
            "Name": "Divination",
            "Type": "Sorcery",
            "ManaCost": "2U",
            "DrawCards": 2,
        }
    ])
    cards, commander, names = _df_to_cards(df)
    assert cards[0].draw_cards == 2


def test_parse_etb_draw_clause():
    text = "When Test Card enters the battlefield, draw two cards."
    triggers = parse_etb_triggers_from_oracle(text)
    assert triggers
    assert "draw 2 card" in triggers[0].description


def test_play_sorcery_draws_cards():
    sorcery = Card(
        name="Divination",
        type="Sorcery",
        mana_cost="2U",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        draw_cards=2,
    )
    commander = create_dummy_commander()
    board = BoardState([], commander)
    # populate library with two cards
    board.library = [Card(name="CardA", type="Instant", mana_cost="", power=0, toughness=0, produces_colors=[], mana_production=0, etb_tapped=False, etb_tapped_conditions={}, has_haste=False) for _ in range(2)]
    board.hand.append(sorcery)
    board.mana_pool = [("U",), ("C",), ("C",)]
    board.play_card(sorcery, verbose=False)
    assert len(board.hand) == 2  # drew two new cards, sorcery left hand
    assert len(board.library) == 0
