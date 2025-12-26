"""
Tests for equipment oracle text parsing and keyword granting.

These tests verify:
1. Equip cost extraction from oracle text
2. Power/toughness buff extraction
3. Keywords granted to equipped creatures (especially haste)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulate_game import Card
from boardstate import BoardState
from deck_loader import parse_equip_cost, parse_power_buff, parse_keywords_when_equipped


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


class TestEquipCostParsing:
    """Test equip cost extraction from oracle text."""

    def test_simple_equip_cost(self):
        """Test simple 'Equip {2}' pattern."""
        oracle = "Equipped creature gets +2/+2. Equip {2}"
        assert parse_equip_cost(oracle) == "{2}"

    def test_colored_equip_cost(self):
        """Test colored equip cost like 'Equip {1}{W}'."""
        oracle = "Equipped creature has lifelink. Equip {1}{W}"
        result = parse_equip_cost(oracle)
        assert "{1}" in result or "{W}" in result

    def test_zero_equip_cost(self):
        """Test zero equip cost."""
        oracle = "Equipped creature has haste. Equip {0}"
        assert parse_equip_cost(oracle) == "{0}"

    def test_no_equip_cost(self):
        """Test non-equipment card returns empty string."""
        oracle = "Draw two cards."
        assert parse_equip_cost(oracle) == ""

    def test_lightning_greaves(self):
        """Test Lightning Greaves oracle text."""
        oracle = "Equipped creature has haste and shroud. Equip {0}"
        assert parse_equip_cost(oracle) == "{0}"

    def test_swiftfoot_boots(self):
        """Test Swiftfoot Boots oracle text."""
        oracle = "Equipped creature has hexproof and haste. Equip {1}"
        assert parse_equip_cost(oracle) == "{1}"


class TestPowerBuffParsing:
    """Test power/toughness buff extraction."""

    def test_simple_buff(self):
        """Test '+2/+2' buff."""
        oracle = "Equipped creature gets +2/+2. Equip {2}"
        assert parse_power_buff(oracle) == 2

    def test_asymmetric_buff(self):
        """Test '+3/+0' buff."""
        oracle = "Equipped creature gets +3/+0. Equip {1}"
        assert parse_power_buff(oracle) == 3

    def test_no_buff(self):
        """Test equipment without stat buff."""
        oracle = "Equipped creature has haste. Equip {0}"
        assert parse_power_buff(oracle) == 0

    def test_sword_of_buff(self):
        """Test Sword-style '+2/+2' buff."""
        oracle = "Equipped creature gets +2/+2 and has protection from red and from white. Equip {2}"
        assert parse_power_buff(oracle) == 2


class TestKeywordsWhenEquippedParsing:
    """Test keywords granted to equipped creatures."""

    def test_haste(self):
        """Test haste extraction."""
        oracle = "Equipped creature has haste. Equip {0}"
        keywords = parse_keywords_when_equipped(oracle)
        assert "haste" in keywords

    def test_hexproof(self):
        """Test hexproof extraction."""
        oracle = "Equipped creature has hexproof. Equip {1}"
        keywords = parse_keywords_when_equipped(oracle)
        assert "hexproof" in keywords

    def test_multiple_keywords(self):
        """Test multiple keywords (Lightning Greaves)."""
        oracle = "Equipped creature has haste and shroud. Equip {0}"
        keywords = parse_keywords_when_equipped(oracle)
        assert "haste" in keywords
        assert "shroud" in keywords

    def test_swiftfoot_boots(self):
        """Test Swiftfoot Boots keywords."""
        oracle = "Equipped creature has hexproof and haste. Equip {1}"
        keywords = parse_keywords_when_equipped(oracle)
        assert "haste" in keywords
        assert "hexproof" in keywords

    def test_flying(self):
        """Test flying extraction."""
        oracle = "Equipped creature has flying. Equip {2}"
        keywords = parse_keywords_when_equipped(oracle)
        assert "flying" in keywords


class TestEquipmentKeywordGranting:
    """Test that equipment correctly grants keywords to creatures."""

    def test_equipment_grants_haste_from_oracle(self):
        """Test that equipment with 'haste' in oracle grants haste."""
        creature = Card(
            name="Test Creature",
            type="Creature",
            mana_cost="{1}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )
        equipment = Card(
            name="Lightning Greaves",
            type="Artifact Equipment",
            mana_cost="{2}",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            equip_cost="{0}",
            oracle_text="Equipped creature has haste and shroud. Equip {0}",
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

        # Before equipping, creature should not have haste (unless it naturally has it)
        assert not getattr(creature, "has_haste", False), "Creature should not have haste before equipping"

        # Equip the equipment to the creature
        board.equip_equipment(equipment, creature, verbose=False)

        # After equipping, creature should have haste
        assert getattr(creature, "has_haste", False), "Creature should have haste after equipping Lightning Greaves"

    def test_equipment_grants_hexproof(self):
        """Test that equipment with 'hexproof' in oracle grants hexproof."""
        creature = Card(
            name="Test Creature",
            type="Creature",
            mana_cost="{1}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )
        equipment = Card(
            name="Swiftfoot Boots",
            type="Artifact Equipment",
            mana_cost="{2}",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            equip_cost="{1}",
            oracle_text="Equipped creature has hexproof and haste. Equip {1}",
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

        # Equip the equipment to the creature
        board.equip_equipment(equipment, creature, verbose=False)

        # After equipping, creature should have hexproof
        assert getattr(creature, "has_hexproof", False), "Creature should have hexproof after equipping Swiftfoot Boots"
        assert getattr(creature, "has_haste", False), "Creature should have haste after equipping Swiftfoot Boots"

    def test_equipment_power_buff_applied(self):
        """Test that equipment power buff is applied correctly."""
        creature = Card(
            name="Test Creature",
            type="Creature",
            mana_cost="{1}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )
        equipment = Card(
            name="Sword of Test",
            type="Artifact Equipment",
            mana_cost="{2}",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            equip_cost="{2}",
            power_buff=2,  # +2/+2
            oracle_text="Equipped creature gets +2/+2. Equip {2}",
        )
        land1 = Card(name="Wastes", type="Basic Land", mana_cost="", power=0, toughness=0,
                     produces_colors=[], mana_production=1, etb_tapped=False, etb_tapped_conditions={}, has_haste=False)
        land2 = Card(name="Wastes", type="Basic Land", mana_cost="", power=0, toughness=0,
                     produces_colors=[], mana_production=1, etb_tapped=False, etb_tapped_conditions={}, has_haste=False)

        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.hand.extend([creature, equipment])
        board.play_card(land1, verbose=False)
        board.play_card(land2, verbose=False)
        board.play_card(creature, verbose=False)
        board.play_card(equipment, verbose=False)
        board.mana_pool = board.mana_sources_from_board(board.lands_untapped, [], [])

        initial_power = int(creature.power)
        initial_toughness = int(creature.toughness)

        # Equip the equipment to the creature
        board.equip_equipment(equipment, creature, verbose=False)

        # After equipping, creature should have +2/+2
        assert int(creature.power) == initial_power + 2, f"Power should be {initial_power + 2}, got {creature.power}"
        assert int(creature.toughness) == initial_toughness + 2, f"Toughness should be {initial_toughness + 2}, got {creature.toughness}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
