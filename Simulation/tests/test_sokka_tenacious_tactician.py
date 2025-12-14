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


def test_sokka_creates_token_on_noncreature_spell():
    """Test that Sokka creates a 1/1 Ally token when you cast a noncreature spell."""
    sokka = Card(
        name="Sokka, Tenacious Tactician",
        type="Legendary Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever you cast a noncreature spell, create a 1/1 white Ally creature token.\nOther Allies you control have prowess and menace.",
    )

    artifact = Card(
        name="Test Artifact",
        type="Artifact",
        mana_cost="{1}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Directly add Sokka to board (bypass mana costs for testing)
    board.creatures.append(sokka)

    # Verify Sokka is on board
    assert len(board.creatures) == 1
    assert board.creatures[0].name == "Sokka, Tenacious Tactician"

    # Trigger noncreature spell effects (passing the artifact)
    board.trigger_noncreature_spell_effects(artifact, verbose=True)

    # Should have created a token
    assert len(board.creatures) == 2, f"Expected 2 creatures (Sokka + token), got {len(board.creatures)}"

    # Verify token properties
    token = [c for c in board.creatures if "Ally Token" in c.name][0]
    assert token.power == 1
    assert token.toughness == 1
    assert "Ally" in token.type


def test_sokka_grants_prowess_to_allies():
    """Test that Sokka grants prowess to other Allies."""
    sokka = Card(
        name="Sokka, Tenacious Tactician",
        type="Legendary Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever you cast a noncreature spell, create a 1/1 white Ally creature token.\nOther Allies you control have prowess and menace.",
    )

    other_ally = Card(
        name="Other Ally",
        type="Creature — Human Ally",
        mana_cost="{1}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="",
    )

    instant = Card(
        name="Test Instant",
        type="Instant",
        mana_cost="{1}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Draw a card.",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Directly add creatures to board (bypass mana costs)
    board.creatures.extend([sokka, other_ally])

    # Trigger noncreature spell effects (instant)
    board.trigger_noncreature_spell_effects(instant, verbose=False)

    # Apply prowess bonuses
    board.apply_prowess_bonus()

    # Other Ally should have prowess bonus
    prowess_bonus = board.get_prowess_power_bonus(other_ally)
    assert prowess_bonus > 0, f"Other Ally should have prowess bonus, got {prowess_bonus}"


def test_sokka_does_not_grant_prowess_to_non_allies():
    """Test that Sokka does NOT grant prowess to non-Ally creatures."""
    sokka = Card(
        name="Sokka, Tenacious Tactician",
        type="Legendary Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever you cast a noncreature spell, create a 1/1 white Ally creature token.\nOther Allies you control have prowess and menace.",
    )

    non_ally = Card(
        name="Non-Ally Creature",
        type="Creature — Human Warrior",
        mana_cost="{1}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="",
    )

    instant = Card(
        name="Test Instant",
        type="Instant",
        mana_cost="{1}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Draw a card.",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Directly add creatures to board (bypass mana costs)
    board.creatures.extend([sokka, non_ally])

    # Trigger noncreature spell effects (instant)
    board.trigger_noncreature_spell_effects(instant, verbose=False)

    # Apply prowess bonuses
    board.apply_prowess_bonus()

    # Non-Ally should NOT have prowess bonus (unless it naturally has prowess)
    prowess_bonus = board.get_prowess_power_bonus(non_ally)
    assert prowess_bonus == 0, f"Non-Ally should not have prowess bonus from Sokka, got {prowess_bonus}"


if __name__ == "__main__":
    test_sokka_creates_token_on_noncreature_spell()
    test_sokka_grants_prowess_to_allies()
    test_sokka_does_not_grant_prowess_to_non_allies()
    print("All Sokka tests passed!")
