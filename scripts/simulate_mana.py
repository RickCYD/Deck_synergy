"""
Example script to run the Monte Carlo mana/spell simulation on a saved deck.

Usage:
    python -m scripts.simulate_mana path/to/deck.json [--iterations 100000] [--turns 10]

The deck JSON should match the format produced by Deck.save(...).
"""

import argparse
from pathlib import Path

from src.models.deck import Deck
from src.simulation.mana_simulator import ManaSimulator, SimulationParams


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("deck_json", type=str, help="Path to saved deck JSON")
    parser.add_argument("--iterations", type=int, default=50000, help="Number of simulations")
    parser.add_argument("--turns", type=int, default=10, help="Max turn to simulate")
    parser.add_argument("--draw", action="store_true", help="Simulate on the draw (default: on the play)")
    args = parser.parse_args()

    deck_path = Path(args.deck_json)
    deck = Deck.load(str(deck_path))

    params = SimulationParams(
        iterations=args.iterations,
        max_turn=args.turns,
        on_the_play=not args.draw,
    )
    sim = ManaSimulator(params)
    result = sim.simulate_deck(deck)

    print(f"\nMonte Carlo results for '{deck.name}' ({deck.deck_id})")
    print(f"Iterations: {params.iterations}, Max turn: {params.max_turn}, On the play: {params.on_the_play}")
    print("Turn\tP(colors)\tP(playable)\tAvg lands")
    for t in range(1, params.max_turn + 1):
        pc = result.p_color_coverage.get(t, 0.0) * 100.0
        ps = result.p_playable_spell.get(t, 0.0) * 100.0
        la = result.avg_lands_in_play.get(t, 0.0)
        print(f"{t}\t{pc:5.1f}%\t\t{ps:5.1f}%\t\t{la:.2f}")


if __name__ == "__main__":
    main()

