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


def test_choose_land_with_sol_ring():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    sol = Card(
        name="Sol Ring",
        type="Artifact",
        mana_cost="1",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=2,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    untapped = Card(
        name="Plains",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["W"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    tapped = Card(
        name="Path of Ancestry",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["Any"],
        mana_production=1,
        etb_tapped=True,
        etb_tapped_conditions={"always_tapped": []},
        has_haste=False,
    )

    board.hand = [sol, untapped, tapped]
    board.turn = 1

    assert board.choose_land_to_play() is untapped


def test_choose_tapped_on_first_turn_without_fast_artifacts():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    untapped = Card(
        name="Plains",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["W"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    tapped = Card(
        name="Path of Ancestry",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["Any"],
        mana_production=1,
        etb_tapped=True,
        etb_tapped_conditions={"always_tapped": []},
        has_haste=False,
    )

    board.hand = [untapped, tapped]
    board.turn = 1

    assert board.choose_land_to_play() is tapped


def test_choose_conditional_land_when_conditions_met():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    rootbound = Card(
        name="Rootbound Crag",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["RG"],
        mana_production=1,
        etb_tapped=True,
        etb_tapped_conditions={"control": ["Mountain", "Forest"]},
        has_haste=False,
    )
    guildgate = Card(
        name="Gruul Guildgate",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["RG"],
        mana_production=1,
        etb_tapped=True,
        etb_tapped_conditions={"always_tapped": []},
        has_haste=False,
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

    board.lands_untapped.append(forest)
    board.hand = [rootbound, guildgate]
    board.turn = 2

    assert board.choose_land_to_play() is rootbound
