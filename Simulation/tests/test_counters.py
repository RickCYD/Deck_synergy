import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from run_simulation import run_simulations
from simulate_game import Card


def _basic_land(name: str) -> Card:
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


def test_add_and_remove_counters_updates_stats():
    creature = Card(
        name="TestCreature",
        type="Creature",
        mana_cost="",
        power=1,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    creature.add_counter("+1/+1")
    assert creature.power == 2
    assert creature.toughness == 2

    creature.remove_counter("+1/+1")
    assert creature.power == 1
    assert creature.toughness == 1
    assert creature.counters.get("+1/+1", 0) == 0


def test_power_summary_includes_counter_column():
    # minimal deck of lands to satisfy starting hand rules
    cards = [_basic_land(f"Forest{i}") for i in range(10)]
    commander = Card(
        name="Boss",
        type="Commander",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
    )
    summary, _, _, _ = run_simulations(cards, commander, num_games=1, max_turns=1, verbose=False)
    assert "Avg Power from Counters" in summary.columns
    assert summary["Avg Power from Counters"].iloc[0] == 0

