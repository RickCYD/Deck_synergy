import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mtg_abilities import ActivatedAbility
from simulate_game import Card
from boardstate import BoardState, Mana_utils


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


def test_sunscorched_divide_activation():
    ability = ActivatedAbility(cost="1", produces_colors=["R", "W"], tap=True)
    sunscorched = Card(
        name="Sunscorched Divide",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        activated_abilities=[ability],
    )
    wastes = Card(
        name="Wastes",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.play_card(wastes, verbose=False)
    board.play_card(sunscorched, verbose=False)

    board.mana_pool = board.mana_sources_from_board(board.lands_untapped, [], [])
    assert board.mana_pool == [("C",)]

    assert board.activate_ability(sunscorched, ability, verbose=False)
    assert ("R",) in board.mana_pool and ("W",) in board.mana_pool
    assert sunscorched in board.lands_tapped


def test_colored_activation_cost():
    ability = ActivatedAbility(cost="R", produces_colors=["W", "W"], tap=True)
    filter_land = Card(
        name="Rugged Prairie",
        type="Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        activated_abilities=[ability],
    )
    mountain = Card(
        name="Mountain",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=["R"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.play_card(mountain, verbose=False)
    board.play_card(filter_land, verbose=False)

    board.mana_pool = board.mana_sources_from_board(board.lands_untapped, [], [])
    assert board.mana_pool == [("R",)]

    assert board.activate_ability(filter_land, ability, verbose=False)
    assert board.mana_pool.count(("W",)) == 2
    assert filter_land in board.lands_tapped


def test_equipment_requires_equipped_activation():
    ability = ActivatedAbility(produces_colors=["R"], requires_equipped=True)
    equipment = Card(
        name="Simple Blade",
        type="Equipment",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        equip_cost="1",
        activated_abilities=[ability],
    )
    creature = Card(
        name="Grizzly Bears",
        type="Creature",
        mana_cost="",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    land = Card(
        name="Wastes",
        type="Basic Land",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.play_card(land, verbose=False)
    board.hand.append(creature)
    board.hand.append(equipment)
    board.play_card(creature, verbose=False)
    board.play_card(equipment, verbose=False)

    # mana pool from land
    board.mana_pool = board.mana_sources_from_board(board.lands_untapped, [], [])

    assert not board.activate_ability(equipment, ability, verbose=False)

    board.equip_equipment(equipment, creature, verbose=False)

    assert board.activate_ability(equipment, ability, verbose=False)
