import os, sys
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


def test_attack_with_other_legendary_draws():
    def effect(board_state):
        board_state.draw_card(1)

    trig = TriggeredAbility(event="attack", effect=effect, requires_another_legendary=True)
    merry = Card(
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
        triggered_abilities=[trig],
        is_legendary=True,
    )
    pippin = Card(
        name="Pippin",
        type="Creature",
        mana_cost="",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_legendary=True,
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.library = [Card(name="Forest", type="Basic Land", mana_cost="", power=0, toughness=0, produces_colors=[], mana_production=1, etb_tapped=False, etb_tapped_conditions={}, has_haste=False)]

    board.creatures.extend([merry, pippin])

    board.attack(merry, verbose=False)
    assert len(board.hand) == 0
    board.attack(pippin, verbose=False)
    assert len(board.hand) == 1
