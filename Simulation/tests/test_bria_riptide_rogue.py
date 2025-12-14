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


def test_bria_grants_prowess_to_all_creatures():
    """Test that Bria grants prowess to all creatures you control."""
    bria = Card(
        name="Bria, Riptide Rogue",
        type="Legendary Creature — Otter Rogue",
        mana_cost="{2}{U}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Prowess\nOther creatures you control have prowess.\nWhenever you cast a noncreature spell, target creature you control can't be blocked this turn.",
    )

    other_creature = Card(
        name="Other Creature",
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

    # Add cards to hand
    board.hand.extend([bria, other_creature, instant])

    # Play Bria
    board.play_card(bria, verbose=False)

    # Play another creature
    board.play_card(other_creature, verbose=False)

    # Cast noncreature spell to trigger prowess
    board.play_card(instant, verbose=False)

    # Apply prowess bonuses
    board.apply_prowess_bonus()

    # Both creatures should have prowess
    bria_prowess = board.get_prowess_power_bonus(bria)
    other_prowess = board.get_prowess_power_bonus(other_creature)

    assert bria_prowess > 0, f"Bria should have prowess bonus, got {bria_prowess}"
    assert other_prowess > 0, f"Other creature should have prowess from Bria, got {other_prowess}"


def test_bria_makes_creature_unblockable():
    """Test that Bria makes a creature unblockable when you cast a noncreature spell."""
    bria = Card(
        name="Bria, Riptide Rogue",
        type="Legendary Creature — Otter Rogue",
        mana_cost="{2}{U}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Prowess\nOther creatures you control have prowess.\nWhenever you cast a noncreature spell, target creature you control can't be blocked this turn.",
    )

    ally_creature = Card(
        name="Big Attacker",
        type="Creature — Human Ally",
        mana_cost="{3}{W}",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="",
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

    # Add cards to hand
    board.hand.extend([bria, ally_creature, artifact])

    # Play Bria
    board.play_card(bria, verbose=False)

    # Play another creature
    board.play_card(ally_creature, verbose=False)

    # Verify creature is not unblockable initially
    assert getattr(ally_creature, 'is_unblockable', False) == False

    # Cast noncreature spell (should make best attacker unblockable)
    board.play_card(artifact, verbose=False)

    # The best attacker (5/5) should now be unblockable
    # Bria's trigger chooses the creature with highest power
    assert ally_creature.is_unblockable == True, "Best attacker should be unblockable after casting noncreature spell"


def test_bria_triggers_on_noncreature_spell():
    """Test that Bria's ability triggers when you cast any noncreature spell."""
    bria = Card(
        name="Bria, Riptide Rogue",
        type="Legendary Creature — Otter Rogue",
        mana_cost="{2}{U}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Prowess\nOther creatures you control have prowess.\nWhenever you cast a noncreature spell, target creature you control can't be blocked this turn.",
    )

    enchantment = Card(
        name="Test Enchantment",
        type="Enchantment",
        mana_cost="{2}",
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

    # Add cards to hand
    board.hand.extend([bria, enchantment])

    # Play Bria
    board.play_card(bria, verbose=False)

    # Verify Bria is not unblockable initially
    assert getattr(bria, 'is_unblockable', False) == False

    # Cast noncreature spell (enchantment)
    board.play_card(enchantment, verbose=False)

    # Bria should now be unblockable (as the best attacker)
    assert bria.is_unblockable == True, "Bria should be unblockable after casting noncreature spell"


if __name__ == "__main__":
    test_bria_grants_prowess_to_all_creatures()
    test_bria_makes_creature_unblockable()
    test_bria_triggers_on_noncreature_spell()
    print("All Bria, Riptide Rogue tests passed!")
