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


def test_forth_eorlingas_tokens_and_monarch():
    commander = create_dummy_commander()
    board = BoardState([], commander)
    spell = Card(
        name="Forth Eorlingas!",
        type="Sorcery",
        mana_cost="XRR",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=(
            "Create X 2/2 red Human Knight creature tokens with trample and haste. "
            "Whenever one or more creatures you control deal combat damage to one or more players this turn, you become the monarch."
        ),

        creates_tokens=[
            {
                "number": "X",
                "token": {
                    "name": "Human Knight Token",
                    "type": "Creature",
                    "mana_cost": "",
                    "power": 2,
                    "toughness": 2,
                    "produces_colors": [],
                    "mana_production": 0,
                    "etb_tapped": False,
                    "etb_tapped_conditions": {},
                    "has_haste": True,
                    "has_flash": False,
                    "has_trample": True,
                },
            }
        ],
        monarch_on_damage=True,
        x_value=2,
    )

    board.hand.append(spell)
    board.mana_pool = [("R",), ("R",), ("C",), ("C",)]

    assert board.play_card(spell, verbose=False)
    assert len(board.creatures) == 2
    token = board.creatures[0]
    assert token.power == 2 and token.toughness == 2
    assert token.has_haste is True
    assert token.has_trample is True
    assert board.monarch is False

    board.combat_damage_to_player(token, 2)
    assert board.monarch is True

    board.monarch = False
    board.turn += 1
    board.combat_damage_to_player(token, 2)
    assert board.monarch is False
