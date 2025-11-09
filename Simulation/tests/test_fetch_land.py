import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulate_game import Card
from boardstate import BoardState


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


def test_fetch_basic_land_enters_tapped():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    fetch = Card(
        name="Evolving Wilds",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        fetch_basic=True,
        fetch_land_tapped=True,
    )
    forest = Card(
        name="Forest",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["G"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    board.hand = [fetch]
    board.library = [forest]
    board.play_card(fetch, verbose=False)
    assert board.life_total == 19
    assert fetch in board.graveyard
    assert forest in board.lands_tapped
    assert forest.tapped is True


def test_fetch_dual_land_enters_untapped():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    fetch = Card(
        name="Polluted Delta",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        fetch_land_types=["Swamp", "Island"],
    )
    swamp = Card(
        name="Swamp",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["B"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    board.hand = [fetch]
    board.library = [swamp]
    board.play_card(fetch, verbose=False)
    assert board.life_total == 19
    assert fetch in board.graveyard
    assert swamp in board.lands_untapped
    assert swamp.tapped is False
