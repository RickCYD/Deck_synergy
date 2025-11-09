import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mtg_abilities import TriggeredAbility
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


def test_landfall_adds_counter_to_creature():
    landfall_creature = Card(
        name="Tireless Tracker",
        type="Creature",
        mana_cost="2G",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )

    def landfall_effect(board_state):
        landfall_creature.add_counter("+1/+1")

    landfall_creature.triggered_abilities.append(
        TriggeredAbility(event="landfall", effect=landfall_effect)
    )

    land = Card(
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

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(landfall_creature)
    board.hand.append(land)

    board.play_card(land, verbose=False)

    assert landfall_creature.power == 2
    assert landfall_creature.toughness == 2
    assert landfall_creature.counters.get("+1/+1", 0) == 1
