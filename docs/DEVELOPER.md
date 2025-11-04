# Developer Documentation

Technical documentation for contributors to the MTG Commander Deck Synergy Visualizer.

## Architecture Overview

### Technology Stack

- **Frontend**: Dash (Plotly) - Python web framework
- **Visualization**: Cytoscape.js - Interactive graph library
- **Analysis**: Custom Python algorithms
- **Data**: Scryfall API + Local JSON database
- **Storage**: Local JSON files

### Module Structure

```
src/
├── api/              # External API integrations
├── models/           # Data models and state management
├── synergy_engine/   # Synergy detection logic
├── analysis/         # Deck analysis modules
├── utils/            # Helper utilities
└── simulation/       # Monte Carlo simulations
```

---

## Key Modules

### 1. Synergy Engine (`src/synergy_engine/`)

**analyzer.py** - Main synergy detection
- `analyze_deck_synergies()`: Full deck analysis (100+ rules)
- `analyze_card_pair()`: Pairwise synergy detection
- Returns weighted synergies by category

**incremental_analyzer.py** - Performance optimization
- `analyze_card_addition()`: Fast incremental analysis (11.4x faster)
- `analyze_card_removal()`: Instant synergy removal
- `merge_synergies()`: Combine synergy dictionaries

### 2. Analysis Modules (`src/analysis/`)

**weakness_detector.py** - Role-based deck analysis
- `DeckWeaknessAnalyzer`: Main class
- `analyze_deck()`: Returns composition score and weaknesses
- `categorize_card()`: Assigns roles to cards
- 100+ regex patterns for role detection

**impact_analyzer.py** - Recommendation impact
- `RecommendationImpactAnalyzer`: Main class
- `analyze_card_impact()`: Before/after comparison
- `analyze_batch_recommendations()`: Process multiple cards
- Simulates deck changes

**replacement_analyzer.py** - Smart card replacement
- `ReplacementAnalyzer`: Main class
- `identify_replacement_candidates()`: Find weak cards
- `find_replacements()`: Match alternatives
- Type-aware, CMC-aware matching

### 3. Models (`src/models/`)

**deck.py** - Deck data model
- `Deck` class with cards, synergies, metadata
- `copy()` method for deep copying
- JSON serialization

**deck_session.py** - Editing session with undo/redo
- `DeckEditingSession`: State management
- `add_card()`, `remove_card()`: Tracked operations
- `undo()`, `redo()`: Change history
- `save()`: Persist to disk
- `to_dict()`, `from_dict()`: Serialization

### 4. API Integrations (`src/api/`)

**archidekt.py** - Deck import
- `fetch_deck_from_archidekt()`: Load deck by URL
- Parses JSON response
- Extracts cards and metadata

**scryfall.py** - Card data
- `ScryfallAPI`: Main class
- `get_card_by_name()`: Single card lookup
- Rate limiting and caching

**local_cards.py** - Local database
- 35,398 cards cached locally
- `load_local_database()`: Load from JSON
- `get_card_by_name()`: Fast lookup
- No API calls needed

**recommendations.py** - Recommendation engine
- Preprocesses all cards
- Synergy-based scoring
- Color identity filtering

---

## Adding Features

### Adding New Synergy Rules

Edit `src/synergy_engine/analyzer.py`:

```python
def _detect_new_synergy(self, card1: Dict, card2: Dict) -> List[Dict]:
    """Detect new synergy pattern"""
    synergies = []
    
    # Check card properties
    if self._check_condition(card1, card2):
        synergies.append({
            'card1': card1['name'],
            'card2': card2['name'],
            'category': 'new_category',
            'weight': 3.0,
            'reason': "Why they synergize"
        })
    
    return synergies
```

Add to `analyze_card_pair()`:
```python
synergies.extend(self._detect_new_synergy(card1, card2))
```

### Adding New Callbacks

Pattern for Dash callbacks:

```python
@app.callback(
    [Output('component-id', 'property')],
    [Input('trigger-id', 'n_clicks')],
    [State('data-store', 'data')],
    prevent_initial_call=True
)
def handle_action(n_clicks, stored_data):
    """Callback description"""
    if not n_clicks:
        return dash.no_update
    
    # Process action
    result = process_data(stored_data)
    
    return result
```

**Pattern-Matching Callbacks** (for dynamic buttons):
```python
@app.callback(
    Output(...),
    Input({'type': 'button-type', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_dynamic_buttons(n_clicks_list):
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = json.loads(button_id)
    # button_data['index'] has the card name
```

### Adding New Analysis Modules

1. Create file in `src/analysis/`
2. Define analyzer class
3. Implement analysis methods
4. Import in `app.py`
5. Integrate into UI/callbacks

Example structure:
```python
class NewAnalyzer:
    def __init__(self):
        # Setup
        pass
    
    def analyze(self, deck_cards: List[Dict]) -> Dict:
        """Main analysis method"""
        # Return results dictionary
        pass
```

---

## Testing

### Running Tests

```bash
# Run specific test
python test_weakness_detection.py
python test_impact_analysis.py
python test_replacement_analysis.py

# Run all tests
python -m pytest tests/
```

### Writing Tests

Create test file:
```python
from src.analysis.module import Analyzer

def main():
    print("Testing...")
    
    # Setup test data
    test_cards = [...]
    
    # Run analysis
    analyzer = Analyzer()
    result = analyzer.analyze(test_cards)
    
    # Verify results
    assert result['score'] > 0
    print("✅ Test passed")

if __name__ == '__main__':
    main()
```

---

## Performance Optimization

### Incremental Analysis

Instead of re-analyzing entire deck:
```python
# Slow (1.6s for 32 cards)
synergies = analyze_deck_synergies(all_cards)

# Fast (0.14s for adding 1 card)
new_synergies = analyze_card_addition(new_card, existing_cards, existing_synergies)
combined = merge_synergies(existing_synergies, new_synergies)
```

### Caching

Local card database avoids API calls:
```python
# Uses cache
from src.api import local_cards
card = local_cards.get_card_by_name(name)
```

### Lazy Loading

Only update graph when needed:
```python
if not changes_made:
    return dash.no_update
```

---

## Code Style

### Naming Conventions

- **Classes**: PascalCase (`DeckAnalyzer`)
- **Functions**: snake_case (`analyze_deck()`)
- **Constants**: UPPER_CASE (`MAX_CARDS`)
- **Private**: prefix underscore (`_internal_method()`)

### Docstrings

```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """
    Brief description
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When it's raised
    """
```

### Type Hints

Use whenever possible:
```python
def process_cards(cards: List[Dict[str, Any]]) -> Dict[str, float]:
    ...
```

---

## Git Workflow

### Branch Naming

- Features: `feature/description`
- Fixes: `fix/issue-description`
- Docs: `docs/update-description`

### Commit Messages

Format:
```
Type: Brief description (50 chars max)

Detailed explanation of changes (optional)
- Bullet points for specifics
- Why the change was needed
- Any breaking changes

Closes #issue-number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`

Example:
```
feat: Add budget-aware recommendations

- Integrate price data from Scryfall
- Add budget filter to recommendations
- Show budget alternatives for expensive cards

Performance impact: +0.5s for price lookups
```

---

## Debugging

### Enable Debug Logging

In `app.py`:
```python
app.run_server(debug=True)
```

### Print Debugging

All callbacks have debug prints:
```python
print(f"[DEBUG] Processing {len(cards)} cards...")
```

### Common Issues

**Callback Returns Mismatch**
- Check Output count matches return values
- Use `dash.no_update` for unchanged outputs

**Serialization Errors**
- Ensure all data in `dcc.Store` is JSON-serializable
- No numpy arrays or complex objects

**Performance Issues**
- Profile with `time.time()` checkpoints
- Use incremental analysis
- Check for unnecessary re-renders

---

## Contributing

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Run all tests
5. Update documentation
6. Submit PR with description

### Review Criteria

- Code quality and style
- Test coverage
- Documentation updates
- Performance impact
- Backward compatibility

---

## Resources

- [Dash Documentation](https://dash.plotly.com/)
- [Cytoscape.js Docs](https://js.cytoscape.org/)
- [Scryfall API](https://scryfall.com/docs/api)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Questions? Open an issue on GitHub!**
