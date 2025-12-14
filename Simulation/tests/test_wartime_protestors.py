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


def test_wartime_protestors_grants_counter_and_haste():
    """Test that Wartime Protestors puts +1/+1 counter on entering Allies and grants haste."""
    wartime_protestors = Card(
        name="Wartime Protestors",
        type="Creature — Human Ally",
        mana_cost="{1}{W}",
        power=1,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever another Ally you control enters the battlefield, put a +1/+1 counter on that creature and it gains haste until end of turn.",
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
        has_haste=False,  # Does NOT have haste naturally
        oracle_text="",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add cards to hand
    board.hand.extend([wartime_protestors, ally_creature])

    # Play Wartime Protestors first
    board.play_card(wartime_protestors, verbose=False)
    assert len(board.creatures) == 1

    # Play another Ally (should trigger Wartime Protestors)
    board.play_card(ally_creature, verbose=False)
    assert len(board.creatures) == 2

    # Verify the Ally got haste
    assert ally_creature.has_haste == True, f"Ally should have gained haste from Wartime Protestors"

    # Verify the Ally got a +1/+1 counter
    # Check if counters were added
    counters = getattr(ally_creature, 'counters', {})
    assert '+1/+1' in counters, f"Ally should have +1/+1 counter, got counters: {counters}"
    assert counters['+1/+1'] >= 1, f"Ally should have at least 1 +1/+1 counter, got {counters['+1/+1']}"


def test_wartime_protestors_does_not_trigger_on_self():
    """Test that Wartime Protestors does NOT trigger on itself entering."""
    wartime_protestors = Card(
        name="Wartime Protestors",
        type="Creature — Human Ally",
        mana_cost="{1}{W}",
        power=1,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever another Ally you control enters the battlefield, put a +1/+1 counter on that creature and it gains haste until end of turn.",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # Add card to hand
    board.hand.append(wartime_protestors)

    # Play Wartime Protestors (should NOT trigger on itself)
    board.play_card(wartime_protestors, verbose=False)

    # Verify Wartime Protestors did NOT get a counter from itself
    counters = getattr(wartime_protestors, 'counters', {})
    plus_one_counters = counters.get('+1/+1', 0)
    assert plus_one_counters == 0, f"Wartime Protestors should not trigger on itself, got {plus_one_counters} counters"


def test_wartime_protestors_does_not_trigger_on_non_allies():
    """Test that Wartime Protestors does NOT trigger on non-Ally creatures."""
    wartime_protestors = Card(
        name="Wartime Protestors",
        type="Creature — Human Ally",
        mana_cost="{1}{W}",
        power=1,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever another Ally you control enters the battlefield, put a +1/+1 counter on that creature and it gains haste until end of turn.",
    )

    non_ally = Card(
        name="Non-Ally Creature",
        type="Creature — Human Warrior",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
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
    board.hand.extend([wartime_protestors, non_ally])

    # Play Wartime Protestors
    board.play_card(wartime_protestors, verbose=False)

    # Play a non-Ally creature
    board.play_card(non_ally, verbose=False)

    # Verify the non-Ally did NOT get a counter or haste
    counters = getattr(non_ally, 'counters', {})
    plus_one_counters = counters.get('+1/+1', 0)
    assert plus_one_counters == 0, f"Non-Ally should not get counter from Wartime Protestors, got {plus_one_counters}"
    assert non_ally.has_haste == False, f"Non-Ally should not gain haste from Wartime Protestors"


if __name__ == "__main__":
    test_wartime_protestors_grants_counter_and_haste()
    test_wartime_protestors_does_not_trigger_on_self()
    test_wartime_protestors_does_not_trigger_on_non_allies()
    print("All Wartime Protestors tests passed!")
