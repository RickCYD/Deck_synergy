Monte Carlo Mana and Spell Simulation
====================================

This module estimates, per turn, the probability that a deck:
- Has access to all colors in its color identity (color coverage), and
- Has at least one non-accelerant spell that is castable with available mana.

Where it lives
- Module: `src/simulation/mana_simulator.py`
- Script: `scripts/simulate_mana.py`

How it works (summary)
- Draw 7, then draw one per turn (on the play/draw configurable).
- Play up to one land per turn, preferring lands that add new color coverage.
- Optionally cast accelerants (mana rocks/ramp) greedily by lowest CMC.
- Lands enter tapped if classified as such; tapped lands become available next turn.
- Multi-color lands/rocks are flexible but provide only 1 mana per turn.
- Ramp like Cultivate adds one tapped land now (usable next turn) and one basic to hand.
- For each turn, compute:
  - P(colors): at least one source for each color in deck’s identity.
  - P(playable): at least one non-accelerant spell in hand can be cast this turn.

Run it via script
```
python -m scripts.simulate_mana data/decks/MyDeck_123456.json --iterations 100000 --turns 10
```

Programmatic usage
```
from src.models.deck import Deck
from src.simulation.mana_simulator import ManaSimulator, SimulationParams

deck = Deck.load("data/decks/MyDeck_123456.json")
params = SimulationParams(iterations=200000, max_turn=10, on_the_play=True)
sim = ManaSimulator(params)
result = sim.simulate_deck(deck)

print(result.p_color_coverage)  # {1: 0.42, 2: 0.67, ...}
print(result.p_playable_spell)  # {1: 0.31, 2: 0.52, ...}
```

Assumptions and caveats
- Ignores complex untap conditions; relies on land classification for "enters tapped".
- Treats mana rocks as +1 flexible source starting the turn after casting.
- Ramp detection is heuristic (searches for common land-fetch wording).
- Hybrid/phyrexian costs are conservatively approximated; "X" is treated as 0.
- Fetch lands (as permanents) are not explicitly modeled; ramp spells are.

Future extensions
- Smarter land selection using actual battlefield color gaps.
- Explicit modeling of fetch lands and activation costs of signets.
- Per-spell playability curves and conditional strategies.

