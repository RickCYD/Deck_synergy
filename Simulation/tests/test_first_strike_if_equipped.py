import os, sys
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


def test_creature_gains_first_strike_when_equipped():
    creature = Card(
        name="Merry",
        type="Creature",
        mana_cost="",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        is_legendary=True,
        keywords_when_equipped=["first strike"],
    )
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
    board.hand.extend([creature, equipment])
    board.play_card(land, verbose=False)
    board.play_card(creature, verbose=False)
    board.play_card(equipment, verbose=False)
    board.mana_pool = board.mana_sources_from_board(board.lands_untapped, [], [])

    assert not getattr(creature, "has_first_strike", False)
    board.equip_equipment(equipment, creature, verbose=False)
    assert getattr(creature, "has_first_strike", False)
