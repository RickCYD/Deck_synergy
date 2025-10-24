# MTG Commander Deck Synergy Visualizer

A Dash-based web application for visualizing Magic: The Gathering Commander decks as interactive graphs, where cards are nodes and synergies between cards are edges.

## Features

- **Deck Import**: Import decks from Archidekt URLs
- **Card Data**: Automatic card information fetching from Scryfall
- **Synergy Analysis**: Intelligent detection of card synergies across multiple categories
- **Interactive Visualization**: Click cards to highlight connections, explore synergies
- **Deck Management**: Save and switch between multiple analyzed decks

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Deck_synergy

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python app.py
```

Then open your browser to `http://localhost:8050`

## Project Structure

```
Deck_synergy/
├── app.py                      # Main Dash application
├── src/
│   ├── api/                    # API integrations (Archidekt, Scryfall)
│   ├── models/                 # Data models
│   ├── synergy_engine/         # Synergy detection logic
│   └── utils/                  # Helper functions
├── data/
│   └── decks/                  # Stored deck JSON files
└── docs/                       # Documentation
```

## Documentation

See the `docs/` folder for detailed documentation on:
- Architecture and design
- Synergy categories and rules
- API usage
- Contributing guidelines

## License

MIT
