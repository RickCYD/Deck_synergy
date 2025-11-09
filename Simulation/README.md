# MTG Simulator

This project provides a small engine for simulating games of Magic: The Gathering. It can load decks from CSV or by querying the Scryfall and Archidekt APIs, run multiple game simulations and display the results in interactive Dash dashboards.

## Setup

1. Ensure you have **Python 3.11+** installed.
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

Running the tests is a good way to verify the logic of the application:
```bash
pytest -q
```
All tests should pass.

## Loading Decks

Several helper functions in `deck_loader.py` make it easy to build `Card` objects from different sources.

* **From a text file** using Scryfall:

  ```python
  from deck_loader import load_deck_from_scryfall_file

  cards, commander, names = load_deck_from_scryfall_file(
      "cards.txt", "Najeela, the Blade-Blossom"
  )
  ```

  Each line in `cards.txt` is a card name. Prefixes like `2 Sol Ring` or suffixes such as `Sol Ring x2` are expanded automatically.

* **From an Archidekt deck**:

  ```python
  from deck_loader import load_deck_from_archidekt

  cards, commander, names = load_deck_from_archidekt(123456)
  ```

The returned `cards` list and `commander` object can be passed to the simulation function.

## Running Simulations

Use `run_simulations` to execute many games and collect averages:

```python
from run_simulation import run_simulations

summary, dist, creature_power = run_simulations(
    cards,
    commander,
    num_games=1000,
    max_turns=10,
    verbose=True,
    log_dir="logs",
)
```

`summary` is a `pandas.DataFrame` with average metrics per turn. `dist` contains the distribution of turns when the commander was first cast.

## Dashboards

`dashboard_simulator.py` starts a Dash application that shows plots for a single deck. It can load a deck from Archidekt or from the default `cards.txt` file:

```bash
python dashboard_simulator.py --archidekt-id 123456
```

`dashboard_compare.py` compares two CSV decks (`deck.csv` and `deck2.csv`) in a similar interactive dashboard.

## Development

* Unit tests live under the `tests/` directory and can be run with `pytest`.
* The engine logic is implemented in `boardstate.py`, `simulate_game.py`, and the helper modules in this repository.

## Deploying to PythonAnywhere

The repository includes a small Dash web application (`dashboard_simulator.py`)
that can be hosted on [PythonAnywhere](https://www.pythonanywhere.com/).
Follow these steps to get it running:

1. **Create an account** – Sign up for a free or paid account at
   [pythonanywhere.com](https://www.pythonanywhere.com/).  Confirm your e-mail
   address and log in.
2. **Open a Bash console** – From the dashboard, start a new Bash console and
   clone your copy of this repository:

   ```bash
   git clone <your fork URL>
   cd MTG
   ```

3. **Create a virtual environment** – Inside the console, create and activate a
   virtualenv, then install the requirements:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create a web app** – In the *Web* tab, add a new web app using *Manual
   configuration* with the same Python version as your virtualenv.

5. **Configure WSGI** – Edit the WSGI configuration file that PythonAnywhere
   provides and point it at this project:

   ```python
   import sys
   path = "/home/<your username>/MTG"
   if path not in sys.path:
       sys.path.append(path)

   from wsgi import application  # uses wsgi.py in this repo
   ```

6. **Reload the app** – Click the *Reload* button in the *Web* tab.  The Dash
   dashboard should now be available at your PythonAnywhere domain.

The default deck uses `cards.txt`.  To load a deck from Archidekt when the app
starts, set the `ARCHIDEKT_ID` environment variable in the *Web* tab.

## Triggered Abilities

`TriggeredAbility` objects now support conditional attack triggers.  Setting
`requires_haste` or `requires_flash` on a trigger ensures it only fires when the
attacking creature has the respective keyword.  The Oracle text parser recognises
phrases such as "Whenever a creature with haste attacks, draw a card" and will
populate these flags automatically.

