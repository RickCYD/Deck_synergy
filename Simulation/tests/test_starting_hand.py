import random
from simulate_game import Card
from draw_starting_hand import draw_starting_hand


def create_dummy_card(name="Land"):
    return Card(
        name=name,
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


def test_draw_starting_hand_reduces_library():
    random.seed(0)
    deck = [create_dummy_card(f"Land{i}") for i in range(10)]
    commander = create_dummy_commander()
    hand, remaining = draw_starting_hand(deck, commander)
    assert len(remaining) < len(deck)
    for card in hand:
        assert card not in remaining
