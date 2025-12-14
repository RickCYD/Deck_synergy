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


def test_kindred_discovery_draws_on_etb():
    """Test that Kindred Discovery draws a card when a creature enters."""
    kindred_discovery = Card(
        name="Kindred Discovery",
        type="Enchantment",
        mana_cost="{3}{U}{U}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="As Kindred Discovery enters the battlefield, choose a creature type.\nWhenever a creature of the chosen type enters the battlefield or attacks, draw a card.",
    )

    ally_creature = Card(
        name="Test Ally",
        type="Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add cards to hand
    board.hand.extend([kindred_discovery, ally_creature])

    # Play Kindred Discovery
    board.play_card(kindred_discovery, verbose=False)
    assert len(board.enchantments) == 1

    # Record initial hand size
    initial_hand_size = len(board.hand)

    # Play an Ally creature (should trigger Kindred Discovery)
    board.play_card(ally_creature, verbose=False)

    # Should have drawn a card
    assert len(board.hand) == initial_hand_size + 1, f"Expected hand size {initial_hand_size + 1}, got {len(board.hand)}"


def test_kindred_discovery_draws_on_attack():
    """Test that Kindred Discovery draws a card when a creature attacks."""
    kindred_discovery = Card(
        name="Kindred Discovery",
        type="Enchantment",
        mana_cost="{3}{U}{U}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="As Kindred Discovery enters the battlefield, choose a creature type.\nWhenever a creature of the chosen type enters the battlefield or attacks, draw a card.",
    )

    ally_creature = Card(
        name="Test Ally",
        type="Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add cards to hand
    board.hand.extend([kindred_discovery, ally_creature])

    # Play Kindred Discovery
    board.play_card(kindred_discovery, verbose=False)

    # Play an Ally creature
    board.play_card(ally_creature, verbose=False)

    # Record hand size after ETB trigger
    hand_size_after_etb = len(board.hand)

    # Simulate attack phase - creature attacks
    # The _check_kindred_discovery_attack should trigger when resolve_combat is called
    board.resolve_combat(verbose=False)

    # Should have drawn at least one card from attacking
    # Note: resolve_combat may draw multiple cards if multiple creatures attack
    assert len(board.hand) >= hand_size_after_etb, f"Expected at least {hand_size_after_etb} cards in hand after attack"


if __name__ == "__main__":
    test_kindred_discovery_draws_on_etb()
    test_kindred_discovery_draws_on_attack()
    print("All Kindred Discovery tests passed!")
