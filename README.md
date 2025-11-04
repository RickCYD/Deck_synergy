# MTG Commander Deck Synergy Visualizer

An intelligent deck analysis and optimization tool for Magic: The Gathering Commander decks. Visualize synergies, identify weaknesses, get smart recommendations, and optimize your deck with one-click card swaps.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🌟 Key Features

### 🎯 Deck Analysis
- **Synergy Visualization**: Interactive graph showing card relationships and synergy strengths
- **Weakness Detection**: Automatic analysis of 8 key deck roles (ramp, draw, removal, etc.)
- **Composition Scoring**: 0-100 score based on optimal EDH deck construction
- **Mana Curve Analysis**: Monte Carlo simulation for opening hand and mana availability

### 🔧 Deck Optimization
- **Smart Recommendations**: AI-powered card suggestions with impact analysis
- **Weakness-Based Filtering**: Recommendations prioritized by what your deck needs
- **Impact Scoring**: See exactly how each card improves your deck (+5 score, addresses critical weakness, etc.)
- **Smart Replacements**: Identifies weak cards and suggests optimal alternatives

### ✏️ Interactive Editing
- **One-Click Card Swaps**: Replace weak cards with better alternatives instantly
- **Add/Remove Cards**: Build and modify decks directly in the app
- **Undo/Redo**: Full change history with reversible actions
- **Persistent Storage**: Save decks to reload later

### 📊 Advanced Analysis
- **Role Distribution**: Tracks 8 critical deck roles with recommended ranges
- **Type-Aware Matching**: Replacement suggestions match card types and mana curve
- **Net Impact Calculation**: See before/after deck scores for every change
- **Strategy Alignment**: Understand how well your deck executes its game plan

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Deck_synergy

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open your browser to `http://localhost:8050`

### First Steps

1. **Load a Deck**
   - Paste an Archidekt deck URL
   - Or select from saved decks
   - Click "Load Deck"

2. **Analyze Synergies**
   - View the synergy graph
   - Click cards to see details
   - Filter by roles (Ramp, Draw, etc.)

3. **Get Recommendations**
   - Click "🔍 Get Recommendations"
   - See cards sorted by impact (🔥 HIGH, ⚡ MEDIUM, ℹ️ LOW)
   - Review which weaknesses each card addresses

4. **Optimize Your Deck**
   - Click "✂️ Cards to Cut"
   - See weak cards with priority ratings
   - Click "⇄ Swap" on suggested replacements
   - Save your improved deck

## 📖 User Guide

### Understanding the Interface

#### Main Tabs

**Synergy Graph Tab**
- Visualizes card relationships
- Node size indicates card importance
- Edge thickness shows synergy strength
- Colors represent card types/roles

**Mana Simulation Tab**
- Monte Carlo simulation (50,000 iterations)
- Opening hand analysis
- Mana availability by turn
- Probability curves

**Deck Building Tab**
- Build new Commander decks from scratch
- Select commander and requirements
- Automated deck construction
- Includes weakness analysis

#### Key Buttons

- **🔍 Get Recommendations**: AI-powered card suggestions
- **✂️ Cards to Cut**: Smart replacement analysis
- **📊 View Top Cards**: See most synergistic cards
- **💾 Save Deck**: Persist changes to file
- **↶ Undo** / **↷ Redo**: Reverse/reapply changes

### Workflow Examples

#### Improving a Budget Deck

1. Load your deck
2. Click "Cards to Cut"
3. Look for 🔴 HIGH priority replacements
4. Focus on cards that address critical weaknesses
5. Click "⇄ Swap" on affordable alternatives
6. Save your improved deck

#### Building Around a Commander

1. Go to "Deck Building" tab
2. Enter your commander name
3. Set deck requirements (lands, ramp, draw, removal)
4. Click "Build Deck"
5. Review weakness analysis
6. Swap out suggested cards as needed

#### Optimizing Mana Base

1. Run mana simulation
2. Check "Probability of having X mana on turn Y"
3. Adjust land count if probabilities are too low
4. Add ramp if you need faster mana
5. Re-simulate to verify improvements

## 🎓 Key Concepts

### Synergy Score
- Calculated based on 100+ synergy detection rules
- Considers card types, abilities, keywords, themes
- Higher score = stronger deck cohesion
- Average score per card shown in analysis

### Role Categories

| Role | Recommended Count | Description |
|------|------------------|-------------|
| **Ramp** | 8-15 (ideal: 10) | Mana acceleration (rocks, dorks, land ramp) |
| **Card Draw** | 8-15 (ideal: 10) | Card advantage engines |
| **Removal** | 8-15 (ideal: 10) | Targeted removal (creatures, artifacts, enchantments) |
| **Board Wipes** | 2-5 (ideal: 3) | Mass removal effects |
| **Protection** | 3-8 (ideal: 5) | Counterspells, hexproof, indestructible |
| **Recursion** | 2-8 (ideal: 4) | Graveyard interaction, reanimation |
| **Threats** | 8-20 (ideal: 12) | Win conditions, major threats |
| **Utility** | 5-15 (ideal: 8) | Support spells, toolbox cards |

### Impact Rating

**🔥 HIGH** - Addresses critical weaknesses or improves score by 5+
- Fills major gaps in deck composition
- Fixes severe imbalances
- Top priority for swaps

**⚡ MEDIUM** - Addresses moderate weaknesses or improves score by 2-4
- Fills minor gaps
- Improves specific roles
- Good value swaps

**ℹ️ LOW** - Minor improvement or score change of 0-1
- Marginal upgrades
- Fine-tuning
- Optional swaps

### Replacement Priority

**🔴 HIGH** - Very low synergy + oversaturated role
- Should be replaced immediately
- Actively hurting deck performance

**🟡 MEDIUM** - Low synergy OR oversaturated role
- Could be improved
- Not urgent but beneficial

**🔵 LOW** - Moderate synergy, room for improvement
- Minor upgrades available
- Consider if budget allows

## 🛠️ Advanced Features

### Performance Optimizations
- **Incremental Synergy Analysis**: 11.4x faster card additions (0.14s vs 1.62s)
- **Cached Recommendations**: Preloaded card database (35,398 cards)
- **Lazy Loading**: Graph updates only when needed

### File Formats

**Saved Decks** (`data/decks/*.json`)
```json
{
  "deck_id": "archidekt_12345",
  "name": "My Deck",
  "cards": [...],
  "synergies": {...},
  "metadata": {...}
}
```

## 📁 Project Structure

```
Deck_synergy/
├── app.py                          # Main Dash application (3500+ lines)
├── src/
│   ├── api/                        # External API integrations
│   │   ├── archidekt.py           # Deck import from Archidekt
│   │   ├── scryfall.py            # Card data from Scryfall
│   │   ├── local_cards.py         # Local card database
│   │   └── recommendations.py      # Recommendation engine
│   ├── models/                     # Data models
│   │   ├── deck.py                # Deck model
│   │   └── deck_session.py        # Editing session with undo/redo
│   ├── synergy_engine/            # Synergy detection
│   │   ├── analyzer.py            # Main synergy analyzer
│   │   ├── incremental_analyzer.py # Performance-optimized analysis
│   │   └── rules/                 # 100+ synergy detection rules
│   ├── analysis/                   # Deck analysis modules
│   │   ├── weakness_detector.py   # Role-based weakness detection
│   │   ├── impact_analyzer.py     # Recommendation impact analysis
│   │   └── replacement_analyzer.py # Smart card replacement
│   ├── utils/                      # Helper utilities
│   │   ├── graph_builder.py       # Cytoscape graph generation
│   │   ├── card_rankings.py       # Card importance scoring
│   │   ├── card_roles.py          # Role assignment
│   │   └── deck_builder.py        # Automated deck construction
│   └── simulation/                 # Monte Carlo simulations
│       └── mana_simulator.py      # Mana curve analysis
├── data/
│   ├── decks/                     # Saved deck files (JSON)
│   └── cards-minimal.json         # Local card database (35,398 cards)
└── docs/                          # Documentation
    ├── USER_GUIDE.md              # Detailed user guide
    ├── DEVELOPER.md               # Developer documentation
    └── ARCHITECTURE.md            # System architecture
```

## 🤝 Contributing

See [DEVELOPER.md](docs/DEVELOPER.md) for:
- Architecture overview
- Module documentation
- Adding new synergy rules
- Testing guidelines
- Code style guide

## 📝 Changelog

### Version 2.0.0 (Current)
- ✨ Smart card replacement analysis
- ✨ One-click card swapping
- ✨ Recommendation impact analysis
- ✨ Deck weakness detection
- ✨ Full deck editing with undo/redo
- ⚡ 11x performance improvement for incremental analysis
- 💾 Persistent deck storage

### Version 1.0.0
- 🎨 Synergy graph visualization
- 📊 Mana curve simulation
- 🎯 Basic recommendations
- 🏗️ Commander deck builder

## 🐛 Known Limitations

- Archidekt push not yet implemented (changes stay local)
- Full synergy re-analysis on undo/redo (could be optimized)
- No price data integration yet
- Internet connection required for Archidekt import

## 📚 Resources

- [User Guide](docs/USER_GUIDE.md) - Detailed workflows and examples
- [Developer Docs](docs/DEVELOPER.md) - Technical documentation
- [Architecture](docs/ARCHITECTURE.md) - System design overview

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Card data from [Scryfall API](https://scryfall.com)
- Deck imports from [Archidekt](https://archidekt.com)
- Built with [Dash](https://dash.plotly.com/) and [Cytoscape](https://js.cytoscape.org/)

---

**Made with ❤️ for the Commander community**
