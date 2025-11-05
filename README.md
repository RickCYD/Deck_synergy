# MTG Commander Deck Synergy Visualizer

An intelligent web application for analyzing and visualizing Magic: The Gathering Commander decks. Uses graph theory and machine learning concepts to identify card synergies, detect combo lines, and help optimize your deck building.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Features

### Deck Analysis
- **Multi-Level Synergy Detection**: Detects pairwise, three-way, and global synergies
- **69+ Synergy Tags**: Comprehensive tag system covering combat, ETB, graveyard, tokens, equipment, and more
- **Smart Card Recommendations**: AI-powered suggestions for deck improvements
- **Deck Scoring**: Total synergy score to compare deck cohesion
- **Card Role Classification**: Automatically identifies ramp, removal, card draw, etc.

### Visualization
- **Interactive Graph**: Cards as nodes, synergies as weighted edges
- **Dynamic Layouts**: Multiple layout algorithms (cose, circle, grid)
- **Click to Explore**: Click any card to see all its synergies
- **Top Cards Highlighting**: Visual emphasis on highest-synergy cards
- **Card Image Preview**: Hover or click to see full card images

### Deck Building
- **Archidekt Import**: Load decks directly from Archidekt URLs
- **Multi-Deck Management**: Save and switch between multiple decks
- **Commander Deck Builder**: Generate synergy-optimized decks from scratch
- **Weak Card Detection**: Identifies low-synergy cards to cut
- **Mana Curve Simulation**: Statistical analysis of mana consistency

### Advanced Features
- **Local Card Cache**: 34,000+ cards cached for instant loading
- **Tutor Validation**: Respects CMC, power, toughness restrictions
- **Trigger Detection**: Recognizes attack, death, cast, and other triggers
- **Combo Detection**: Identifies infinite combos and synergy chains

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Deck_synergy

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download card data (first time only)
python3 scripts/create_minimal_cards.py
```

### Running the App

```bash
# Start the development server
python app.py

# Open browser to http://localhost:8050
```

### Deploying to Heroku

```bash
# Login to Heroku
heroku login

# Create app (first time only)
heroku create my-deck-visualizer

# Deploy
git push heroku main
```

## 📖 Usage Guide

### 1. Load a Deck
- Paste an Archidekt deck URL in the input field
- Click "Load Deck"
- Wait for synergy analysis to complete (~15-30 seconds)

### 2. Explore Synergies
- **Click a card** to highlight its synergies
- **Hover over a card** to preview the full card image
- **View the right panel** for detailed synergy explanations
- **Check "Top Cards"** to see the most synergistic cards

### 3. Get Recommendations
- Click "Get Recommendations" for card suggestions
- Review synergy scores for each recommendation
- See which existing cards could be replaced

### 4. Analyze Deck Composition
- View role distribution (ramp, removal, card draw, etc.)
- Check mana curve simulation results
- Review total deck synergy score

## 🏗️ Project Structure

```
Deck_synergy/
├── app.py                          # Main Dash application
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku deployment config
│
├── src/
│   ├── api/
│   │   ├── archidekt.py           # Archidekt API integration
│   │   ├── scryfall.py            # Scryfall API integration
│   │   ├── local_cards.py         # Local card cache management
│   │   └── recommendations.py     # Card recommendation engine
│   │
│   ├── models/
│   │   └── deck.py                # Deck data model
│   │
│   ├── synergy_engine/
│   │   ├── analyzer.py            # Main synergy analysis orchestrator
│   │   ├── etb_synergies.py       # ETB/flicker synergies
│   │   ├── token_synergies.py     # Token generation/sacrifice
│   │   ├── equipment_synergies.py # Equipment/voltron synergies
│   │   ├── graveyard_synergies.py # Graveyard/recursion synergies
│   │   ├── card_advantage_synergies.py  # Card draw/tutors
│   │   ├── ramp_synergies.py      # Mana ramp synergies
│   │   ├── tribal_synergies.py    # Tribal synergies
│   │   └── combat_synergies.py    # Combat/damage synergies
│   │
│   ├── utils/
│   │   ├── graph_builder.py       # Cytoscape graph element builder
│   │   ├── card_roles.py          # Role classification system
│   │   ├── card_rankings.py       # Centrality-based rankings
│   │   ├── card_advantage_extractors.py  # Extract tutor/draw mechanics
│   │   └── deck_builder.py        # Commander deck builder
│   │
│   └── simulation/
│       └── mana_simulator.py      # Monte Carlo mana simulation
│
├── data/
│   ├── cards/
│   │   ├── cards-minimal.json     # Local card cache (34K cards)
│   │   ├── cards-preprocessed.json # Synergy tags + roles
│   │   └── oracle-cards.json      # Full Scryfall data (optional)
│   │
│   └── decks/                     # Saved deck analyses
│
├── scripts/
│   ├── create_minimal_cards.py    # Build local card cache
│   └── create_preprocessed_cards.py  # Build synergy tag database
│
└── docs/
    ├── ARCHITECTURE.md            # System design documentation
    ├── SYNERGY_RULES.md          # All synergy categories explained
    ├── USER_GUIDE.md             # Detailed usage guide
    └── FEATURES.md               # Feature list and roadmap
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom port
PORT=8050

# Optional: Enable debug mode
DEBUG=True
```

### Performance Tuning
- **Mana Simulations**: Adjust iterations in UI (default: 50,000)
- **Synergy Threshold**: Set minimum synergy strength to display
- **Cache Settings**: Use local cache for faster loading (enabled by default)

## 📊 Synergy System

The app uses a sophisticated multi-level synergy detection system:

### Pairwise Synergies (Strongest: +50 points)
Cards that directly enable each other:
- ETB triggers + Flicker effects
- Token generators + Sacrifice outlets
- Equipment + Equipment matters
- Attack triggers + Trigger doublers

### Three-Way Synergies (+30 points)
Requires multiple components:
- Land recursion (Conduit of Worlds) = lands + graveyard + ramp
- Equipment enablers (Ardenn) = equipment + creatures + equipment_matters

### Global Synergies (Scaled, capped at 10-20 points)
Cards that scale with deck composition:
- Inspiring Statuary scales with artifact count
- Hammer of Nazahn scales with equipment count
- Sword of Once and Future scales with instants/sorceries

### Local Synergies (0.1-0.5 per card)
Tag overlap between cards:
- Generic utility: 0.1 per card (ramp, removal, card draw)
- Strategic: 0.5 per card (equipment, tokens, graveyard)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Adding New Synergies
1. Add detection logic to appropriate synergy file in `src/synergy_engine/`
2. Add synergy tags to `scripts/create_preprocessed_cards.py`
3. Regenerate preprocessed database
4. Test with real decks
5. Submit PR with examples

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/ app.py
```

## 📝 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and data flow
- **[Synergy Rules](docs/SYNERGY_RULES.md)**: Complete synergy category reference
- **[User Guide](docs/USER_GUIDE.md)**: Detailed usage instructions
- **[Development Guide](docs/DEVELOPMENT.md)**: Contributing and extending the app

## 🐛 Troubleshooting

### Deck won't load
- Check internet connection (needs Archidekt/Scryfall access)
- Verify deck URL is from Archidekt
- Check browser console for errors

### Slow performance
- Large decks (100+ cards) take longer to analyze
- Reduce mana simulation iterations
- Ensure local cache is loaded (`cards-minimal.json` exists)

### Missing card images
- Regenerate `cards-minimal.json` with full image URIs
- Run: `python3 scripts/create_minimal_cards.py`

### Incorrect synergies
- Report issues with specific card examples
- Check `docs/SYNERGY_RULES.md` for expected behavior
- Submit PR with fix to synergy detection

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- **Scryfall** for comprehensive MTG card data API
- **Archidekt** for deck management and export
- **Plotly/Dash** for interactive visualization framework
- **Cytoscape.js** for graph rendering

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/username/Deck_synergy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/Deck_synergy/discussions)
- **Email**: your-email@example.com

---

Made with ❤️ for the MTG Commander community
