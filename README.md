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
- **⚡ Verified Combo Detection**: Integrates with Commander Spellbook's 40,000+ combo database
- **Local Card Cache**: 34,000+ cards cached for instant loading
- **Tutor Validation**: Respects CMC, power, toughness restrictions
- **Trigger Detection**: Recognizes attack, death, cast, and other triggers
- **Combo Explanations**: Step-by-step combo walkthroughs with prerequisites and results

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

### 5. Discover Verified Combos ⚡ NEW!
- **Automatic Detection**: Combos are detected when you load a deck
- **Visual Indicators**: Golden/orange edges connect combo pieces in the graph
- **Combo Badge**: Look for the ⚡ COMBO badge in synergy details
- **Full Explanations**: See combo results, prerequisites, and step-by-step instructions
- **Commander Spellbook Link**: Click through to see the combo on the official database

Example combo display:
```
⚡ COMBO

🃏 All Combo Pieces: Basalt Monolith, Rings of Brighthearth

🎯 Results:
  • Infinite colorless mana

📋 Prerequisites:
  • Both permanents on the battlefield
  • {3} available

🔄 Steps:
  1. Activate Basalt Monolith's untap ability...
  2. Rings triggers, pay {2} to copy...
  3. Resolve for infinite mana

🔗 View on Commander Spellbook
```

For more details, see [COMBO_DETECTION.md](docs/COMBO_DETECTION.md)

## 🏗️ Project Structure

> 🤖 **For AI Models & Developers:** See [AI_GUIDE.md](AI_GUIDE.md) for comprehensive navigation guide, entry points, and quick reference

```
Deck_synergy/
├── app.py                          # Main Dash application (3,387 lines)
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku deployment config
│
├── src/                           # Modern, organized source code
│   ├── api/                       # External API integrations
│   │   ├── archidekt.py          # Archidekt API integration
│   │   ├── scryfall.py           # Scryfall API integration
│   │   ├── local_cards.py        # Local card cache (34K+ cards)
│   │   ├── recommendations.py    # Card suggestion engine
│   │   └── commander_spellbook.py # ⚡ Commander Spellbook combo API
│   │
│   ├── models/                    # Data models
│   │   ├── card.py               # Card data structure
│   │   ├── deck.py               # Deck data model
│   │   └── synergy.py            # Synergy relationship model
│   │
│   ├── synergy_engine/            # Synergy detection system (12 files)
│   │   ├── analyzer.py           # Main orchestrator - START HERE
│   │   ├── rules.py              # 69+ synergy detection rules
│   │   ├── combo_detector.py     # ⚡ Verified combo detection
│   │   ├── card_advantage_synergies.py  # Draw/tutor synergies
│   │   ├── recursion_synergies.py       # Graveyard recursion
│   │   ├── three_way_synergies.py       # Multi-card combos
│   │   ├── categories.py                # Synergy categorization
│   │   ├── embedding_analyzer.py        # ML-based semantic analysis
│   │   └── ... (4 more files)
│   │
│   ├── utils/                     # Extractors & utilities (14 files)
│   │   ├── *_extractor.py        # Extract mechanics from card text
│   │   ├── graph_builder.py      # Build synergy graphs
│   │   ├── card_roles.py         # Role classification
│   │   ├── fuzzy_search.py       # Card name search
│   │   └── ... (10 more utilities)
│   │
│   └── simulation/                # Simulation wrappers
│       ├── runner.py             # High-level simulation runner
│       ├── metrics.py            # Deck power metrics
│       └── wrapper.py            # Interface to Simulation/
│
├── Simulation/                    # Game simulation engine (legacy)
│   ├── boardstate.py             # CORE: Board state & mechanics (194KB)
│   ├── simulate_game.py          # CORE: Game simulation loop
│   ├── oracle_text_parser.py     # Parse card abilities
│   ├── deck_loader.py            # Load cards from various formats
│   ├── turn_phases.py            # MTG turn phases
│   ├── mtg_abilities.py          # Ability data structures
│   └── tests/                    # Simulation tests (18 files)
│
├── data/
│   ├── cards/
│   │   ├── cards-minimal.json           # 34MB - All MTG cards
│   │   └── cards-preprocessed.json      # 17MB - Preprocessed with tags
│   └── decks/                           # Saved deck analyses
│
├── tests/                         # Synergy engine tests (10 files)
│
├── scripts/                       # Utility scripts (8 files)
│   ├── create_minimal_cards.py   # Build card database
│   ├── generate_embeddings.py    # ML embeddings
│   └── verify_and_filter_cards.py # Data validation
│
├── docs/                          # Comprehensive documentation (43 files)
│   ├── ARCHITECTURE.md           # System architecture
│   ├── DEVELOPER.md              # Developer setup
│   ├── USER_GUIDE.md             # User documentation
│   ├── SYNERGY_SYSTEM.md         # Synergy detection guide
│   ├── COMBO_DETECTION.md        # Combo finder docs
│   ├── archives/                 # Historical analyses
│   └── fixes/                    # Bug fix documentation
│
├── assets/                        # CSS and static files
│
├── README.md                      # This file - PROJECT OVERVIEW
├── AI_GUIDE.md                    # 🤖 AI navigation & development guide
├── QUICK_REFERENCE.md            # Quick command reference
├── RELEASE_NOTES.md              # Version history
├── PROVIDE_DECKLIST.md           # How to load a deck
└── READY_FOR_YOUR_DECK.md        # User instructions
```

### Key Files for Different Tasks

**Understanding the Project:**
- Start: `README.md` → `AI_GUIDE.md` → `docs/ARCHITECTURE.md`

**Synergy System:**
- Entry: `src/synergy_engine/analyzer.py`
- Rules: `src/synergy_engine/rules.py`
- Docs: `docs/SYNERGY_SYSTEM.md`

**Game Simulation:**
- Entry: `Simulation/simulate_game.py`
- Mechanics: `Simulation/boardstate.py`
- Docs: `docs/SIMULATION_ACCURACY_COMPLETE.md`

**Dashboard:**
- Main: `app.py` (search for `@app.callback`)
- Graph: `src/utils/graph_builder.py`

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

### For Developers & AI Models
- **[How to Use with AI](HOW_TO_USE_WITH_AI.md)**: 🎯 **NEW!** Learn how to effectively use AI coding assistants (Claude, ChatGPT, etc.) to improve this project
- **[AI Navigation Guide](AI_GUIDE.md)**: 🤖 **START HERE** - Comprehensive guide for AI models and developers to quickly understand and navigate the codebase
- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and data flow
- **[Development Guide](docs/DEVELOPMENT.md)**: Contributing and extending the app

### For Users
- **[User Guide](docs/USER_GUIDE.md)**: Detailed usage instructions
- **[Synergy Rules](docs/SYNERGY_RULES.md)**: Complete synergy category reference
- **[Combo Detection](docs/COMBO_DETECTION.md)**: How combo detection works

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
