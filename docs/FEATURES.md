# MTG Commander Deck Synergy Visualizer - Features Documentation

## Overview

This application provides an interactive graph visualization for Magic: The Gathering Commander decks, where cards are represented as nodes and synergies between cards are represented as weighted edges.

## Table of Contents

1. [Deck Import](#deck-import)
2. [Graph Visualization](#graph-visualization)
3. [Synergy Detection](#synergy-detection)
4. [Interactive Features](#interactive-features)
5. [Deck Management](#deck-management)

---

## 1. Deck Import

### Feature: Archidekt URL Import

**Description:** Import Commander decks directly from Archidekt.com by providing a deck URL.

**How to Use:**
1. Copy the URL of your deck from Archidekt (e.g., `https://archidekt.com/decks/123456`)
2. Paste the URL into the "Archidekt Deck URL" input field
3. Click the "Load Deck" button
4. Wait for the application to:
   - Fetch the deck list from Archidekt
   - Download detailed card information from Scryfall
   - Analyze synergies between all cards
   - Save the deck locally

**What Gets Imported:**
- All cards in the deck
- Card quantities
- Commander designation
- Archidekt categories (if any)

### Feature: Scryfall Card Data Integration

**Description:** For each card in the deck, the application fetches comprehensive data from Scryfall.

**Card Properties Retrieved:**
- **Basic Info:** Name, mana cost, converted mana cost (CMC), rarity
- **Type Info:** Type line, supertypes, main types, subtypes
- **Text:** Oracle text, keywords
- **Stats:** Power/toughness (creatures), loyalty (planeswalkers)
- **Colors:** Colors and color identity
- **Images:** Card images for future features
- **Mechanics:** Keywords, abilities, produced mana
- **Metadata:** EDHREC rank, legalities, prices

**Rate Limiting:**
The application respects Scryfall's rate limit (100ms between requests) to ensure responsible API usage.

---

## 2. Graph Visualization

### Feature: Cytoscape Graph Display

**Description:** Interactive graph visualization using Dash Cytoscape.

**Visual Elements:**

#### Nodes (Cards)
- **Regular Cards:** Blue circular nodes (60x60px)
- **Commander Cards:** Red circular nodes (80x80px) with bold labels
- **Node Label:** Card name
- **Node Size:** Can be scaled based on number of connections

#### Edges (Synergies)
- **Width:** Proportional to synergy strength (weight)
- **Color:**
  - Default: Gray (#95a5a6)
  - Selected: Orange/Green
- **Curve:** Bezier curves for better visualization
- **Opacity:** 0.6 (default), 1.0 (selected), 0.2 (dimmed)

### Feature: Multiple Layout Options

**Available Layouts:**

1. **Cose (Default):** Force-directed layout that groups related nodes
2. **Circle:** Arranges all nodes in a circle
3. **Concentric:** Arranges nodes in concentric circles
4. **Grid:** Arranges nodes in a grid pattern
5. **Breadthfirst:** Hierarchical tree-like layout

**How to Change Layout:**
Select a different layout from the "Graph Layout" dropdown menu. The graph will animate to the new layout.

---

## 3. Synergy Detection

### Feature: Multi-Category Synergy Analysis

**Description:** The application analyzes all possible card pairs and detects synergies across 7 main categories.

### Synergy Categories

#### 1. Triggers & Activated Abilities (Weight: 1.0)

**Subcategories:**
- **ETB Triggers:** Cards that enter the battlefield and cards that can repeatedly trigger ETBs
- **Death Triggers:** Cards that trigger on death and sacrifice outlets
- **Combat Triggers:** Combat-related synergies
- **Spell Triggers:** Spell-casting synergies
- **Ability Activated:** Activated ability interactions

**Example:**
- Card A: "When ~ enters the battlefield, draw a card"
- Card B: "Exile target creature, then return it to the battlefield"
- Synergy: Card B can repeatedly trigger Card A's ETB ability

#### 2. Mana & Color Synergy (Weight: 0.5)

**Subcategories:**
- **Color Match:** Shared color identity
- **Mana Production:** Mana production and consumption
- **Cost Reduction:** Cost reduction effects
- **Color Matters:** Color-specific effects

**Example:**
- Cards that share 2+ colors get a synergy score
- Cards that produce mana and high-CMC cards that need it

#### 3. Role & Function Interaction (Weight: 0.8)

**Subcategories:**
- **Protection:** Hexproof, indestructible, protection effects
- **Card Advantage:** Draw engines
- **Ramp:** Mana acceleration
- **Removal:** Removal synergies
- **Recursion:** Graveyard recursion
- **Sacrifice:** Sacrifice outlets and fodder
- **Token Generation:** Token creation and payoffs

**Example:**
- Card A creates tokens
- Card B benefits from tokens ("Whenever a token enters...")
- Synergy detected with high value

#### 4. Combo & Infinite Interactions (Weight: 2.0)

**Subcategories:**
- **Infinite Mana:** Infinite mana combinations
- **Infinite ETB:** Infinite ETB/LTB triggers
- **Infinite Damage:** Infinite damage combos
- **Infinite Mill:** Infinite mill combos
- **Two-Card Combo:** Direct two-card combos
- **Three-Card Combo:** Three-card combo pieces

**Note:** Combo detection is the highest weighted category due to its game-winning potential.

**Example:**
- Cards with "untap" and "mana" keywords may form infinite mana
- Cards with specific combo keywords get flagged

#### 5. Benefits & Enhancement (Weight: 0.7)

**Subcategories:**
- **Anthem Effect:** Global buffs (+1/+1 to all creatures)
- **Synergy Type:** Type-based benefits
- **Keyword Grant:** Granting keywords to other cards
- **Cost Matters:** CMC-based synergies
- **Tribal:** Creature type synergies

**Example:**
- Card A: "All creatures you control get +1/+1"
- Card B: Any creature
- Synergy: Card B benefits from Card A

#### 6. Type Synergy (Weight: 0.6)

**Subcategories:**
- **Creature Matters:** Cards that care about creatures
- **Artifact Matters:** Artifact synergies
- **Enchantment Matters:** Enchantment synergies
- **Instant/Sorcery Matters:** Spell synergies
- **Land Matters:** Landfall, land-based effects
- **Planeswalker Synergy:** Planeswalker interactions

**Example:**
- Card A: "Whenever you cast an artifact spell..."
- Card B: An artifact card
- Synergy detected

#### 7. Card Advantage Engine (Weight: 0.9)

**Subcategories:**
- **Draw Engine:** Card draw combinations
- **Tutor Target:** Tutors and their targets
- **Recursion Loop:** Graveyard loops
- **Scry Synergy:** Top-deck manipulation

**Example:**
- Multiple cards with draw abilities form a card advantage engine

### Feature: Weighted Synergy Scoring

**How Weights Work:**

Each detected synergy has:
1. **Base Value:** Assigned by the detection rule (1.0 - 5.0)
2. **Category Weight:** Multiplier based on category importance
3. **Final Weight:** Base Value × Category Weight

**Total Edge Weight:** Sum of all weighted synergies between two cards

**Formula:**
```
Edge Weight = Σ(Synergy Value × Category Weight)
```

**Example Calculation:**
- Synergy 1: ETB Trigger (value: 3.0, weight: 1.0) = 3.0
- Synergy 2: Color Match (value: 2.0, weight: 0.5) = 1.0
- Synergy 3: Tribal (value: 3.0, weight: 0.7) = 2.1
- **Total Edge Weight: 6.1**

### Feature: Minimum Synergy Threshold

**Default Threshold:** 0.5

Only synergies with a total weight ≥ 0.5 are included in the graph. This filters out very weak synergies and keeps the visualization clean.

---

## 4. Interactive Features

### Feature: Card Selection & Highlighting

**How to Use:**
Click on any card (node) in the graph.

**What Happens:**
1. **Selected Card:** Highlighted with orange border
2. **Connected Cards:** Remain at full opacity
3. **Connected Edges:** Turn green with increased width
4. **Non-connected Elements:** Dimmed to 20% opacity

**Info Panel Display:**
- Card name and type
- Mana cost and colors
- Oracle text
- List of all connected cards with synergy strengths

### Feature: Synergy Edge Selection

**How to Use:**
Click on any edge (line) between two cards.

**What Happens:**
1. **Selected Edge:** Highlighted in orange with increased width
2. **Connected Cards:** Highlighted with orange borders
3. **Other Elements:** Dimmed to 20% opacity

**Info Panel Display:**
- Names of both cards
- Total synergy strength
- Categorized list of all synergies
- Detailed description of each synergy with its value

**Synergy Information Includes:**
- Synergy name
- Description explaining why cards work together
- Synergy value
- Category and subcategory

### Feature: Dynamic Opacity & Highlighting

**Visual States:**

1. **Normal State:**
   - All nodes: opacity 1.0
   - All edges: opacity 0.6

2. **Selection State:**
   - Selected elements: opacity 1.0, highlighted borders/colors
   - Connected elements: opacity 1.0
   - Unconnected elements: opacity 0.2

3. **Hover State (Future):**
   - Could show tooltips with card info

---

## 5. Deck Management

### Feature: Deck Persistence

**Auto-Save Location:** `data/decks/`

**File Format:** JSON

**File Naming:** `{DeckName}_{DeckID}.json`

**What Gets Saved:**
- Deck ID and name
- All card data (with Scryfall details)
- All analyzed synergies
- Metadata (creation time, update time)

### Feature: Deck Selector Dropdown

**How to Use:**
1. After loading one or more decks, they appear in the dropdown
2. Select a deck from the "Select Deck" dropdown
3. Graph automatically updates to show the selected deck

**Multiple Deck Support:**
You can load multiple decks and switch between them without re-fetching data.

### Feature: Status Messages

**Real-time Feedback:**
- Blue: "Loading deck..." (in progress)
- Green: "Successfully loaded deck: {name}" (success)
- Red: "Error loading deck: {error}" (failure)

---

## Technical Features

### API Integration

**Archidekt API:**
- Endpoint: `https://archidekt.com/api/decks/{deck_id}/`
- Fetches: Deck name, cards, categories
- No authentication required

**Scryfall API:**
- Endpoint: `https://api.scryfall.com/cards/named`
- Fetches: Complete card data
- Rate limiting: 100ms between requests
- Fallback: Fuzzy search if exact name fails

### Data Models

**Deck Class:**
- Methods: save(), load(), to_json(), from_json()
- Helpers: get_commander(), get_cards_by_type(), get_synergies_for_card()
- Statistics: get_deck_statistics()

**Card Data:**
Stored as dictionaries with 30+ fields including type info, text, stats, images, etc.

**Synergy Data:**
Organized by card pairs with category-organized synergy lists.

### Performance Considerations

**Synergy Analysis Complexity:**
- For a 100-card deck: 4,950 card pair comparisons
- Each comparison runs ~11 detection rules
- Total: ~54,450 rule checks per deck
- Processing time: ~30-60 seconds for a typical deck

**Optimization:**
- Cached results in saved deck files
- Lazy loading of graph elements
- Efficient dictionary-based lookups

---

## Future Feature Ideas

1. **Card Image Display:** Show card images on hover or in info panel
2. **Synergy Filtering:** Filter graph by synergy category
3. **Combo Paths:** Highlight multi-card combo chains
4. **Statistics Dashboard:** Deck statistics and insights
5. **Export Options:** Export graph as image or PDF
6. **Comparison Mode:** Compare two decks side-by-side
7. **Custom Synergies:** Allow users to add custom synergy rules
8. **Community Synergies:** Share and import synergy rule packs

---

## Troubleshooting

### Common Issues

**1. "Invalid Archidekt URL format"**
- Ensure URL is in format: `https://archidekt.com/decks/{number}`
- Check that deck is public

**2. "Failed to fetch card from Scryfall"**
- Check internet connection
- Card name may be non-standard (check Scryfall directly)
- Wait and retry (may be rate limit)

**3. "No synergies detected"**
- Deck may have very few synergies
- Try lowering minimum threshold (requires code change)
- Some card types may not have detection rules yet

**4. Graph too cluttered**
- Use different layout (try Circle or Concentric)
- Filter by selecting a card to see only its connections
- Future: add synergy threshold filter UI

---

## Contributing

To add new synergy detection rules:

1. Open `src/synergy_engine/rules.py`
2. Create a new detection function following the pattern
3. Add it to the `ALL_RULES` list
4. Test with various card combinations

To add new synergy categories:

1. Open `src/synergy_engine/categories.py`
2. Add category to `SYNERGY_CATEGORIES` with appropriate weight
3. Update documentation

---

## Version History

**v1.0.0** (2025-10-24)
- Initial release
- Archidekt import
- Scryfall integration
- 7 synergy categories with 11 detection rules
- Interactive graph visualization
- Deck persistence
