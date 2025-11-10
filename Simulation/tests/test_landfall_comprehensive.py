"""
Comprehensive tests for landfall mechanics.

Tests:
- Extra land drops (Azusa, Exploration)
- Scute Swarm token creation and copying
- Omnath variants (Rage, Creation, Roil)
- Avenger of Zendikar ETB and landfall
- Generic landfall effects (tokens, counters, life gain, damage)
- Land play tracking
"""

import os
import sys
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


def create_forest():
    return Card(
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


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Extra Land Drops
# ═══════════════════════════════════════════════════════════════════════

def test_extra_land_drops_azusa():
    """Test that Azusa allows playing 2 additional lands."""
    azusa = Card(
        name="Azusa, Lost but Seeking",
        type="Creature",
        mana_cost="2G",
        power=1,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="You may play two additional lands on each of your turns."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add Azusa to battlefield
    board.creatures.append(azusa)

    # Add 3 lands to hand
    for _ in range(3):
        board.hand.append(create_forest())

    # Should be able to play 3 lands (1 + 2 from Azusa)
    assert board.can_play_land() == True
    board.play_land(board.hand[0], verbose=False)
    assert board.lands_played_this_turn == 1

    assert board.can_play_land() == True
    board.play_land(board.hand[0], verbose=False)
    assert board.lands_played_this_turn == 2

    assert board.can_play_land() == True
    board.play_land(board.hand[0], verbose=False)
    assert board.lands_played_this_turn == 3

    # Should not be able to play a 4th land
    assert board.can_play_land() == False

    print("✓ Azusa extra land drops work correctly")


def test_extra_land_drops_exploration():
    """Test that Exploration allows playing 1 additional land."""
    exploration = Card(
        name="Exploration",
        type="Enchantment",
        mana_cost="G",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="You may play an additional land on each of your turns."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add Exploration to battlefield
    board.enchantments.append(exploration)

    # Add 2 lands to hand
    board.hand.append(create_forest())
    board.hand.append(create_forest())

    # Should be able to play 2 lands (1 + 1 from Exploration)
    assert board.get_extra_land_drops() == 1
    board.play_land(board.hand[0], verbose=False)
    assert board.lands_played_this_turn == 1

    assert board.can_play_land() == True
    board.play_land(board.hand[0], verbose=False)
    assert board.lands_played_this_turn == 2

    # Should not be able to play a 3rd land
    assert board.can_play_land() == False

    print("✓ Exploration extra land drops work correctly")


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Scute Swarm
# ═══════════════════════════════════════════════════════════════════════

def test_scute_swarm_insect_tokens():
    """Test Scute Swarm creates 1/1 Insect tokens with <6 lands."""
    scute = Card(
        name="Scute Swarm",
        type="Creature",
        mana_cost="2G",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Landfall — Whenever a land enters the battlefield under your control, create a 1/1 green Insect creature token. If you control six or more lands, create a token that's a copy of Scute Swarm instead."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(scute)

    # Add 4 lands to board
    for _ in range(4):
        board.lands_untapped.append(create_forest())

    # Play one more land (total 5 lands -> should create Insect)
    land = create_forest()
    board.hand.append(land)

    initial_creatures = len(board.creatures)
    board.play_card(land, verbose=False)

    # Should have created 1 additional creature (1/1 Insect)
    assert len(board.creatures) == initial_creatures + 1
    assert board.creatures[-1].name == "Insect"
    assert board.creatures[-1].power == 1
    assert board.creatures[-1].toughness == 1

    print("✓ Scute Swarm creates 1/1 Insect tokens correctly")


def test_scute_swarm_copy_tokens():
    """Test Scute Swarm creates copies of itself with 6+ lands."""
    scute = Card(
        name="Scute Swarm",
        type="Creature",
        mana_cost="2G",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Landfall — Whenever a land enters the battlefield under your control, create a 1/1 green Insect creature token. If you control six or more lands, create a token that's a copy of Scute Swarm instead."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(scute)

    # Add 6 lands to board
    for _ in range(6):
        board.lands_untapped.append(create_forest())

    # Play one more land (total 7 lands -> should create Scute copy)
    land = create_forest()
    board.hand.append(land)

    initial_creatures = len(board.creatures)
    board.play_card(land, verbose=False)

    # Should have created 1 additional Scute Swarm
    assert len(board.creatures) == initial_creatures + 1
    assert board.creatures[-1].name == "Scute Swarm"
    assert board.creatures[-1].power == 1
    assert board.creatures[-1].toughness == 1

    print("✓ Scute Swarm creates copy tokens correctly with 6+ lands")


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Omnath Variants
# ═══════════════════════════════════════════════════════════════════════

def test_omnath_locus_of_rage():
    """Test Omnath, Locus of Rage creates 5/5 Elementals on landfall."""
    omnath = Card(
        name="Omnath, Locus of Rage",
        type="Creature",
        mana_cost="3RRRGG",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Landfall — Whenever a land enters the battlefield under your control, create a 5/5 red and green Elemental creature token."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(omnath)

    land = create_forest()
    board.hand.append(land)

    initial_creatures = len(board.creatures)
    board.play_card(land, verbose=False)

    # Should have created a 5/5 Elemental
    assert len(board.creatures) == initial_creatures + 1
    assert board.creatures[-1].name == "Elemental"
    assert board.creatures[-1].power == 5
    assert board.creatures[-1].toughness == 5

    print("✓ Omnath, Locus of Rage creates 5/5 Elementals correctly")


def test_omnath_locus_of_creation():
    """Test Omnath, Locus of Creation triggers on multiple lands."""
    omnath = Card(
        name="Omnath, Locus of Creation",
        type="Creature",
        mana_cost="RGWU",
        power=4,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="When Omnath enters the battlefield or whenever you play your first land, draw a card. Landfall — You gain 4 life (second land). Landfall — Deal 4 damage (third land)."
    )

    azusa = Card(
        name="Azusa, Lost but Seeking",
        type="Creature",
        mana_cost="2G",
        power=1,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="You may play two additional lands on each of your turns."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(omnath)
    board.creatures.append(azusa)

    # Add library for card draw
    for _ in range(5):
        board.library.append(create_forest())

    # Add 3 lands to hand
    for _ in range(3):
        board.hand.append(create_forest())

    initial_life = board.life_total
    initial_hand = len(board.hand)
    initial_drain = board.drain_damage_this_turn

    # Play first land -> should draw a card
    land1 = board.hand[0]
    board.play_card(land1, verbose=False)
    assert len(board.hand) == initial_hand  # drew 1, played 1 = same

    # Play second land -> should gain 4 life
    land2 = board.hand[0]
    board.play_card(land2, verbose=False)
    assert board.life_total == initial_life + 4

    # Play third land -> should deal 4 damage
    land3 = board.hand[0]
    board.play_card(land3, verbose=False)
    assert board.drain_damage_this_turn == initial_drain + 4

    print("✓ Omnath, Locus of Creation triggers work correctly")


def test_avenger_of_zendikar_etb():
    """Test Avenger of Zendikar creates Plant tokens on ETB."""
    avenger = Card(
        name="Avenger of Zendikar",
        type="Creature",
        mana_cost="5GG",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="When Avenger of Zendikar enters the battlefield, create a 0/1 green Plant creature token for each land you control. Landfall — Put a +1/+1 counter on each Plant creature you control."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add 5 lands to board
    for _ in range(5):
        board.lands_untapped.append(create_forest())

    # Put Avenger onto the battlefield (simulate casting it)
    initial_creatures = len(board.creatures)

    # Manually place Avenger on battlefield and trigger ETB
    board.creatures.append(avenger)
    board._process_special_etb_effects(avenger, verbose=False)

    # Should have created 5 Plant tokens + Avenger itself
    assert len(board.creatures) == initial_creatures + 6

    # Count plants
    plants = [c for c in board.creatures if c.name == "Plant"]
    assert len(plants) == 5

    # Each plant should be 0/1
    for plant in plants:
        assert plant.power == 0
        assert plant.toughness == 1

    print("✓ Avenger of Zendikar ETB creates correct number of Plants")


def test_avenger_of_zendikar_landfall():
    """Test Avenger of Zendikar buffs Plants on landfall."""
    avenger = Card(
        name="Avenger of Zendikar",
        type="Creature",
        mana_cost="5GG",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="When Avenger of Zendikar enters the battlefield, create a 0/1 green Plant creature token for each land you control. Landfall — Put a +1/+1 counter on each Plant creature you control."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add 3 lands
    for _ in range(3):
        board.lands_untapped.append(create_forest())

    # Add Avenger and Plants to battlefield
    board.creatures.append(avenger)

    # Manually create some Plant tokens
    for _ in range(3):
        plant = Card(
            name="Plant",
            type="Creature — Plant",
            mana_cost="",
            power=0,
            toughness=1,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )
        board.creatures.append(plant)

    # Play a land -> should trigger landfall and buff all Plants
    land = create_forest()
    board.hand.append(land)
    board.play_card(land, verbose=False)

    # All plants should have +1/+1 counter
    plants = [c for c in board.creatures if c.name == "Plant"]
    for plant in plants:
        assert plant.counters.get("+1/+1", 0) == 1
        assert plant.power == 1  # 0 + 1
        assert plant.toughness == 2  # 1 + 1

    print("✓ Avenger of Zendikar landfall buffs Plants correctly")


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Generic Landfall Effects
# ═══════════════════════════════════════════════════════════════════════

def test_generic_landfall_life_gain():
    """Test generic landfall life gain effect."""
    life_gainer = Card(
        name="Test Life Gainer",
        type="Creature",
        mana_cost="2G",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Landfall — Whenever a land enters the battlefield under your control, you gain 2 life."
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)
    board.creatures.append(life_gainer)

    land = create_forest()
    board.hand.append(land)

    initial_life = board.life_total
    board.play_card(land, verbose=False)

    # Should have gained 2 life
    assert board.life_total == initial_life + 2

    print("✓ Generic landfall life gain works correctly")


def test_landfall_tracking():
    """Test that landfall triggers are tracked correctly."""
    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Reset turn tracking
    board.lands_played_this_turn = 0
    board.landfall_triggers_this_turn = 0

    # Play 2 lands
    for _ in range(2):
        land = create_forest()
        board.hand.append(land)
        board.play_card(land, verbose=False)

    assert board.lands_played_this_turn == 2
    assert board.landfall_triggers_this_turn == 2

    print("✓ Landfall tracking works correctly")


# ═══════════════════════════════════════════════════════════════════════
# Run All Tests
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE LANDFALL TESTS")
    print("="*70)

    print("\n--- Extra Land Drops ---")
    test_extra_land_drops_azusa()
    test_extra_land_drops_exploration()

    print("\n--- Scute Swarm ---")
    test_scute_swarm_insect_tokens()
    test_scute_swarm_copy_tokens()

    print("\n--- Omnath Variants ---")
    test_omnath_locus_of_rage()
    test_omnath_locus_of_creation()

    print("\n--- Avenger of Zendikar ---")
    test_avenger_of_zendikar_etb()
    test_avenger_of_zendikar_landfall()

    print("\n--- Generic Landfall ---")
    test_generic_landfall_life_gain()
    test_landfall_tracking()

    print("\n" + "="*70)
    print("ALL LANDFALL TESTS PASSED! ✓")
    print("="*70)
