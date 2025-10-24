# Architecture Documentation

## System Overview

The MTG Commander Deck Synergy Visualizer is a Python-based web application built with Dash (Plotly) that provides interactive graph visualization of Magic: The Gathering Commander decks.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (Dash Web Application)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  URL Input   │  │ Deck Selector│  │  Graph View  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                         (app.py)                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Dash Callbacks                             │ │
│  │  • load_deck()                                          │ │
│  │  • update_graph()                                       │ │
│  │  • handle_selection()                                   │ │
│  │  • update_layout()                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ API Services │  │ Data Models  │  │   Synergy    │      │
│  │              │  │              │  │    Engine    │      │
│  │ • Archidekt  │  │    • Deck    │  │  • Analyzer  │      │
│  │ • Scryfall   │  │              │  │    • Rules   │      │
│  │              │  │              │  │  • Categories│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                  │
│                           ▼                                  │
│                  ┌──────────────┐                           │
│                  │   Utilities  │                           │
│                  │              │                           │
│                  │ • Graph      │                           │
│                  │   Builder    │                           │
│                  └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Archidekt   │  │   Scryfall   │  │  Local JSON  │      │
│  │     API      │  │     API      │  │    Storage   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Application Layer (`app.py`)

**Responsibilities:**
- Initialize Dash application
- Define UI layout
- Implement callback functions for interactivity
- Coordinate between services

**Key Components:**

#### Layout Structure
```python
app.layout
├── Header
│   └── Title and description
├── Control Panel (Left Sidebar - 25%)
│   ├── Deck URL Input
│   ├── Load Deck Button
│   ├── Deck Selector Dropdown
│   ├── Status Messages
│   └── Layout Selector
└── Main Content (Right - 70%)
    ├── Cytoscape Graph
    └── Info Panel (Card/Synergy Details)
```

#### Callbacks

**1. `load_deck(n_clicks, url, current_data)`**
- Triggered by: Load Deck button click
- Inputs: Deck URL, current stored data
- Outputs: Status message, updated deck list, stored data
- Process:
  1. Parse Archidekt URL
  2. Fetch deck from Archidekt
  3. Fetch card details from Scryfall
  4. Analyze synergies
  5. Save deck to file
  6. Update UI

**2. `update_graph(deck_file)`**
- Triggered by: Deck selection
- Inputs: Selected deck file path
- Outputs: Graph elements
- Process:
  1. Load deck from JSON
  2. Build Cytoscape elements
  3. Return node and edge data

**3. `handle_selection(node_data, edge_data, elements)`**
- Triggered by: Node or edge click
- Inputs: Selected node/edge data, all elements
- Outputs: Updated stylesheet, info panel content
- Process:
  1. Determine what was clicked
  2. Calculate connected elements
  3. Apply highlighting/dimming styles
  4. Build detailed info panel

**4. `update_layout(layout_name)`**
- Triggered by: Layout selector change
- Inputs: Layout name
- Outputs: Layout configuration
- Process: Return layout config with animation

### 2. API Services (`src/api/`)

#### `archidekt.py`

**Purpose:** Fetch deck data from Archidekt.com

**Key Functions:**

```python
extract_deck_id(url: str) -> str
    Parse Archidekt URL and extract deck ID

fetch_deck_from_archidekt(url: str) -> Dict
    Fetch complete deck data from Archidekt API
    Returns: {id, name, cards[{name, quantity, categories, is_commander}]}
```

**API Endpoint:**
```
GET https://archidekt.com/api/decks/{deck_id}/
```

**Response Format:**
```json
{
  "name": "Deck Name",
  "cards": [
    {
      "card": {
        "oracleCard": {
          "name": "Card Name",
          "colorIdentity": ["U", "R"]
        }
      },
      "quantity": 1,
      "categories": ["Commander", "Ramp"]
    }
  ]
}
```

#### `scryfall.py`

**Purpose:** Fetch detailed card information from Scryfall.com

**Key Classes/Functions:**

```python
class ScryfallAPI:
    BASE_URL = "https://api.scryfall.com"
    RATE_LIMIT_DELAY = 0.1  # 100ms

    get_card_by_name(card_name: str) -> Dict
        Fetch card by exact name, with fuzzy search fallback

fetch_card_details(cards: List[Dict]) -> List[Dict]
    Batch fetch details for all cards
    Respects rate limiting
    Enriches cards with 30+ Scryfall fields
```

**API Endpoints:**
```
GET https://api.scryfall.com/cards/named?exact={name}
GET https://api.scryfall.com/cards/named?fuzzy={name}
```

**Enriched Card Data:**
- Basic: name, scryfall_id, mana_cost, cmc, type_line
- Colors: colors, color_identity, produced_mana
- Types: card_types, supertypes, subtypes
- Text: oracle_text, keywords
- Stats: power, toughness, loyalty
- Images: image_uris
- Metadata: rarity, set, legalities, prices, edhrec_rank

### 3. Data Models (`src/models/`)

#### `deck.py`

**Purpose:** Manage deck data with persistence

**Class: Deck**

```python
class Deck:
    Attributes:
        deck_id: str
        name: str
        cards: List[Dict]
        synergies: Dict
        metadata: Dict

    Methods:
        # Serialization
        to_dict() -> Dict
        to_json() -> str
        save(directory) -> Path

        # Deserialization
        from_dict(data) -> Deck
        from_json(json_str) -> Deck
        load(file_path) -> Deck

        # Queries
        get_commander() -> Dict
        get_cards_by_type(card_type) -> List[Dict]
        get_cards_by_color(colors) -> List[Dict]
        get_card_by_name(name) -> Dict

        # Synergies
        add_synergy(card1, card2, synergy_data)
        get_synergies_for_card(card_name) -> List[Dict]

        # Statistics
        get_deck_statistics() -> Dict
```

**Deck JSON Structure:**
```json
{
  "deck_id": "123456",
  "name": "My Commander Deck",
  "cards": [...],
  "synergies": {
    "Card A||Card B": {
      "card1": "Card A",
      "card2": "Card B",
      "total_weight": 5.2,
      "synergies": {
        "triggers": [...],
        "benefits": [...]
      }
    }
  },
  "metadata": {
    "created_at": "2025-10-24T...",
    "updated_at": "2025-10-24T..."
  }
}
```

### 4. Synergy Engine (`src/synergy_engine/`)

#### `categories.py`

**Purpose:** Define synergy categories and weights

**Structure:**
```python
SYNERGY_CATEGORIES = {
    'category_name': {
        'name': 'Display Name',
        'description': 'Description',
        'weight': 1.0,  # Importance multiplier
        'subcategories': {
            'subcat_name': 'Description'
        }
    }
}
```

**Categories:**
1. triggers (1.0)
2. mana_synergy (0.5)
3. role_interaction (0.8)
4. combo (2.0) - Highest weight
5. benefits (0.7)
6. type_synergy (0.6)
7. card_advantage (0.9)

#### `rules.py`

**Purpose:** Individual synergy detection rules

**Rule Function Pattern:**
```python
def detect_xxx_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Detect [specific type] synergies

    Returns:
        Synergy dict if found, None otherwise
        {
            'name': 'Synergy Name',
            'description': 'Why cards synergize',
            'value': 2.5,  # Base value
            'category': 'category_name',
            'subcategory': 'subcat_name'
        }
    """
```

**Detection Rules:**
1. `detect_etb_triggers()` - ETB and flicker
2. `detect_sacrifice_synergy()` - Sac outlets and fodder
3. `detect_mana_color_synergy()` - Color overlap
4. `detect_tribal_synergy()` - Creature types
5. `detect_card_draw_synergy()` - Draw engines
6. `detect_ramp_synergy()` - Ramp + high CMC
7. `detect_type_matters_synergy()` - Type-based effects
8. `detect_combo_potential()` - Combo indicators
9. `detect_protection_synergy()` - Protection effects
10. `detect_token_synergy()` - Token creation/payoffs
11. `detect_graveyard_synergy()` - Graveyard interactions

**ALL_RULES List:**
Contains all detection functions for iteration

#### `analyzer.py`

**Purpose:** Coordinate synergy analysis

**Key Functions:**

```python
analyze_card_pair(card1, card2) -> List[Dict]
    Run all detection rules on a card pair
    Returns list of detected synergies

calculate_edge_weight(synergies) -> float
    Calculate total weighted value
    Formula: Σ(value × category_weight)

organize_synergies_by_category(synergies) -> Dict
    Group synergies by category

analyze_deck_synergies(cards, threshold=0.5) -> Dict
    Main analysis function
    Process:
        1. Generate all card pairs: C(n,2)
        2. For each pair, run all detection rules
        3. Calculate weights
        4. Filter by threshold
        5. Organize results

get_top_synergies(synergy_dict, top_n) -> List
    Get strongest synergies

get_synergies_for_card(card_name, synergy_dict) -> List
    Get all synergies for a specific card

get_synergy_statistics(synergy_dict) -> Dict
    Calculate analysis statistics
```

**Complexity:**
- Input: n cards
- Comparisons: C(n,2) = n(n-1)/2
- For 100 cards: 4,950 comparisons
- Each comparison runs 11 rules
- Total checks: ~54,450

### 5. Utilities (`src/utils/`)

#### `graph_builder.py`

**Purpose:** Convert deck data to Cytoscape elements

**Key Functions:**

```python
build_graph_elements(deck_data) -> List[Dict]
    Main function to build all elements
    Returns list of nodes and edges

create_card_node(card) -> Dict
    Create Cytoscape node
    Structure:
        {
            'data': {
                'id': card_name,
                'label': card_name,
                'type': 'commander' | 'card',
                ... all card properties ...
            },
            'classes': node_type
        }

create_synergy_edge(key, synergy_data) -> Dict
    Create Cytoscape edge
    Structure:
        {
            'data': {
                'id': unique_id,
                'source': card1_name,
                'target': card2_name,
                'weight': total_weight,
                'synergies': {...},
                ...
            }
        }

get_color_code(colors) -> str
    Convert MTG colors to hex codes
    W: #F8F6D8 (white)
    U: #0E68AB (blue)
    B: #150B00 (black)
    R: #D3202A (red)
    G: #00733E (green)
    Multi: #F4E15B (gold)
    Colorless: #BCC3C7 (gray)

calculate_node_sizes(elements) -> List[Dict]
    Scale nodes based on connection count

get_graph_statistics(elements) -> Dict
    Calculate graph metrics
```

### 6. Data Flow

#### Complete Flow: Loading a Deck

```
1. User enters URL and clicks "Load Deck"
   ↓
2. app.py: load_deck() callback triggered
   ↓
3. archidekt.py: fetch_deck_from_archidekt(url)
   - Extract deck ID from URL
   - GET request to Archidekt API
   - Parse response for deck name and card list
   ↓
4. scryfall.py: fetch_card_details(cards)
   - For each card:
     * GET request to Scryfall API (with rate limiting)
     * Parse and enrich card data
   ↓
5. models/deck.py: Create Deck object
   ↓
6. synergy_engine/analyzer.py: analyze_deck_synergies(cards)
   - For each card pair:
     * Run all detection rules (rules.py)
     * Calculate weights using categories.py
   - Filter by threshold
   - Organize results
   ↓
7. models/deck.py: deck.save()
   - Serialize to JSON
   - Write to data/decks/{name}_{id}.json
   ↓
8. app.py: Update UI
   - Show success message
   - Add deck to dropdown
   - Store in dcc.Store
```

#### Complete Flow: Displaying a Deck

```
1. User selects deck from dropdown
   ↓
2. app.py: update_graph() callback triggered
   ↓
3. Load deck JSON from file
   ↓
4. utils/graph_builder.py: build_graph_elements(deck_data)
   - Create nodes from cards
   - Create edges from synergies
   - Apply visual properties
   ↓
5. Return elements to Cytoscape component
   ↓
6. Cytoscape renders graph with selected layout
```

#### Complete Flow: Selecting a Card

```
1. User clicks on a card node
   ↓
2. app.py: handle_selection() callback triggered
   ↓
3. Identify clicked node and all connected edges
   ↓
4. Build updated stylesheet:
   - Highlight selected node
   - Highlight connected nodes
   - Brighten connected edges
   - Dim all other elements
   ↓
5. Build info panel:
   - Extract card properties
   - List all connections
   ↓
6. Update UI with new stylesheet and info panel
```

## Technology Stack

### Backend
- **Python 3.8+**
- **Dash 2.14+** - Web framework
- **Dash Cytoscape 0.3+** - Graph visualization
- **Requests 2.31+** - HTTP requests
- **BeautifulSoup 4.12+** - HTML parsing (future use)

### Frontend (via Dash)
- **React** (underlying Dash)
- **Cytoscape.js** (graph rendering)
- **Plotly** (data visualization)

### Data Storage
- **JSON** - Local file storage
- **In-memory** - dcc.Store for session data

### External APIs
- **Archidekt API** - Deck data
- **Scryfall API** - Card data

## Design Patterns

### 1. Service Layer Pattern
Separate API interactions from business logic
- `src/api/*` - External service clients
- `src/synergy_engine/*` - Business logic
- `src/models/*` - Data models

### 2. Strategy Pattern
Synergy detection rules as pluggable strategies
- Each rule is an independent function
- Rules can be added/removed from ALL_RULES list

### 3. Builder Pattern
Graph construction separated from data representation
- `graph_builder.py` converts data to visualization format

### 4. Repository Pattern
Deck persistence abstracted in Deck class
- Save/load methods handle file I/O
- Data format encapsulated

## Performance Considerations

### Bottlenecks

1. **Scryfall API Calls**
   - 100ms per card (rate limiting)
   - 100-card deck = ~10 seconds
   - **Mitigation:** Cache in saved deck files

2. **Synergy Analysis**
   - O(n²) card pair generation
   - 100 cards = 4,950 comparisons
   - **Mitigation:** Pre-compute and save

3. **Graph Rendering**
   - Large graphs can be slow to render
   - **Mitigation:** Layout optimization, filtering

### Optimizations

1. **Caching:** Saved deck files contain pre-analyzed synergies
2. **Lazy Loading:** Decks loaded only when selected
3. **Efficient Data Structures:** Dictionary lookups for O(1) access
4. **Rate Limiting:** Prevents API overload
5. **Threshold Filtering:** Removes weak synergies from graph

## Security Considerations

1. **Input Validation:** URL parsing with regex patterns
2. **API Rate Limiting:** Respects external API limits
3. **File Path Sanitization:** Safe filename generation
4. **Error Handling:** Try/catch for all external calls
5. **No User Authentication:** Currently single-user local app

## Extensibility

### Adding New Synergy Rules

1. Create detection function in `rules.py`
2. Add to `ALL_RULES` list
3. Follow return format specification

### Adding New Data Sources

1. Create new module in `src/api/`
2. Implement fetch functions
3. Update `load_deck()` callback in `app.py`

### Adding New Visualizations

1. Add new Dash components to layout
2. Create new callbacks
3. Use stored deck data from dcc.Store

## Testing Strategy

### Unit Tests (Future)
- Test individual synergy rules
- Test API response parsing
- Test weight calculations

### Integration Tests (Future)
- Test full deck import flow
- Test synergy analysis pipeline
- Test graph generation

### Manual Testing
- Test with various deck archetypes
- Test edge cases (colorless decks, tribal decks, combo decks)
- Test UI interactions

## Deployment

### Local Development
```bash
python app.py
# Access at http://localhost:8050
```

### Production Deployment (Future)
- **Docker:** Containerize application
- **Cloud:** Deploy to Heroku, AWS, or similar
- **Considerations:**
  - Add authentication if public
  - Implement caching layer
  - Rate limit user requests
  - Monitor API usage

## Monitoring & Logging

### Current Logging
- Console output for API fetching progress
- Error messages printed to console

### Future Enhancements
- Structured logging with levels
- Log file rotation
- Error tracking (Sentry, etc.)
- Performance metrics
- API usage tracking

## Version Control

### Git Structure
```
main/master
└── feature branches
    └── claude/mtg-commander-deck-graph-*
```

### Commit Strategy
- Feature-based commits
- Descriptive commit messages
- Documentation included with features

---

## Maintenance & Updates

### Regular Tasks
1. Update dependency versions
2. Monitor Scryfall API changes
3. Add new synergy rules as mechanics evolve
4. Optimize performance based on usage

### Future Roadmap
See FEATURES.md "Future Feature Ideas" section
