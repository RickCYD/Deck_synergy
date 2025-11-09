import pandas as pd

from deck_loader import _df_to_cards
from run_simulation import run_simulations


def _build_simple_deck():
    data = [{"Name": f"Land{i}", "Type": "Land", "ManaCost": "", "Commander": False} for i in range(9)]
    data.append({"Name": "Boss", "Type": "Creature", "ManaCost": "1G", "Commander": True})
    df = pd.DataFrame(data)
    cards, commander, _ = _df_to_cards(df)
    return cards, commander


def test_parallel_simulation_consistency():
    cards, commander = _build_simple_deck()
    summary1, dist1, power1, interaction1 = run_simulations(
        cards, commander, num_games=2, max_turns=1, verbose=False, num_workers=1
    )
    summary2, dist2, power2, interaction2 = run_simulations(
        cards, commander, num_games=2, max_turns=1, verbose=False, num_workers=2
    )
    assert summary1.equals(summary2)
    assert dist1.equals(dist2)
    assert power1 == power2
    assert interaction1 == interaction2
