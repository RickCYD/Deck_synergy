# User Guide - MTG Commander Deck Synergy Visualizer

## Getting Started

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Deck_synergy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   Navigate to `http://localhost:8050`

---

## Step-by-Step Tutorial

### Step 1: Import Your First Deck

1. **Get your Archidekt deck URL:**
   - Go to [Archidekt.com](https://archidekt.com)
   - Open one of your Commander decks (or any public deck)
   - Copy the URL (e.g., `https://archidekt.com/decks/123456`)

2. **Load the deck:**
   - Paste the URL into the "Archidekt Deck URL" input field
   - Click the "Load Deck" button
   - Wait for the status message to turn green

3. **What's happening:**
   - The app fetches your deck list from Archidekt
   - For each card, it downloads complete information from Scryfall
   - It analyzes all possible card pairs for synergies
   - The deck is saved locally for future use

   **Note:** For a 100-card deck, this can take 30-60 seconds.

### Step 2: View Your Deck Graph

1. **Select your deck:**
   - After loading, your deck appears in the "Select Deck" dropdown
   - Click the dropdown and select your deck

2. **Explore the graph:**
   - Each circle (node) represents a card
   - Lines (edges) between cards represent synergies
   - Thicker lines = stronger synergies
   - Red nodes = your Commander(s)
   - Blue nodes = other cards

### Step 3: Understand the Visualization

#### Node Colors
- **Red (Large):** Commander card(s)
- **Blue:** Regular cards
- **Gold (if implemented):** Multi-color cards

#### Edge Thickness
- **Thin:** Weak synergy (weight 0.5-2.0)
- **Medium:** Moderate synergy (weight 2.0-4.0)
- **Thick:** Strong synergy (weight 4.0+)

#### Layout Options
Try different layouts to find the best view:
- **Cose (Default):** Groups related cards together
- **Circle:** All cards in a circle
- **Concentric:** Rings based on importance
- **Grid:** Organized rows and columns
- **Breadthfirst:** Tree-like hierarchy

### Step 4: Explore Card Synergies

#### Click on a Card

1. Click any card node
2. **What happens:**
   - The selected card gets an orange border
   - Connected cards remain bright
   - Unconnected cards fade (dimmed)
   - Connection lines turn green and get thicker

3. **Info Panel shows:**
   - Card name and type
   - Mana cost and colors
   - Full oracle text
   - List of all connected cards with synergy strengths

**Example:**
```
Click on "Rhystic Study"
→ See all cards that synergize with it
→ Read their synergy descriptions
```

#### Click on a Synergy Edge

1. Click any line between two cards
2. **What happens:**
   - The selected edge highlights in orange
   - Both connected cards highlight
   - Everything else fades

3. **Info Panel shows:**
   - Both card names
   - Total synergy strength
   - **Detailed synergy breakdown by category:**
     - Triggers & Activated Abilities
     - Mana & Color Synergy
     - Role Interaction
     - Combos
     - Benefits
     - Type Synergy
     - Card Advantage

**Example Info Panel:**
```
Synergy: Ashnod's Altar ↔ Grave Pact
Total Synergy Strength: 5.5

Synergy Categories:

Role Interaction:
  - Sacrifice Synergy: Ashnod's Altar can sacrifice
    permanents to trigger Grave Pact (Value: 2.5)

Type Synergy:
  - Artifact Synergy: Cards interact as artifacts (Value: 2.0)

Benefits:
  - Death Trigger Benefit: Grave Pact benefits when
    creatures die from Ashnod's Altar (Value: 3.0)
```

### Step 5: Find Key Cards and Synergies

#### Identify Hub Cards
Look for nodes with many connections:
- These are your deck's "engine" cards
- They synergize with many other cards
- Often worth protecting

#### Identify Strong Synergies
Look for thick edges:
- These are your most important card interactions
- May indicate combo potential
- Consider tutoring for these cards

#### Identify Weak Areas
Look for isolated nodes:
- Cards with few or no connections
- May be cuts if optimizing
- Or may serve specific roles (removal, etc.)

---

## Common Use Cases

### Use Case 1: Deck Analysis

**Goal:** Understand how your deck works

**Steps:**
1. Load your deck
2. View the full graph
3. Click on your Commander
   - See all cards that synergize with it
4. Look for clusters of connected cards
   - These are your deck's themes
5. Find the strongest synergies (thickest edges)
   - These are your key interactions

**Questions to Ask:**
- Does my Commander connect to many cards?
- Are there isolated cards that don't fit?
- What are my strongest synergies?
- Are there clusters representing different strategies?

### Use Case 2: Combo Discovery

**Goal:** Find combo potential in your deck

**Steps:**
1. Load your deck
2. Look for edges marked with "Combo" synergies
3. Click on these edges to see details
4. Look for cards that appear in multiple combo synergies

**Synergy Types to Look For:**
- "Infinite Mana"
- "Infinite ETB"
- "Infinite Damage"
- "Two-Card Combo"

**Example:**
If you see: `Palinchron ↔ Deadeye Navigator` with a thick edge marked "Combo", click it to see the infinite mana potential.

### Use Case 3: Deck Optimization

**Goal:** Make cuts or additions

**Steps:**
1. Load your deck
2. Identify cards with 0 or 1 connection
   - Potential cuts
3. Look at the synergy categories
   - Are you missing certain types?
4. Compare synergy strengths
   - Replace weak cards with stronger synergies

**Optimization Strategy:**
- **Cut:** Cards with fewest synergies (unless they're essential answers)
- **Keep:** Cards with many synergies or very strong specific synergies
- **Add:** Cards that would synergize with multiple existing cards

### Use Case 4: Comparing Strategies

**Goal:** Understand different deck builds

**Steps:**
1. Load multiple decks (same commander, different builds)
2. Switch between them using the dropdown
3. Compare:
   - Total number of synergies
   - Strongest synergies
   - Different card clusters
   - Which cards appear in all builds vs. specific ones

---

## Understanding Synergy Categories

### Triggers (Weight: 1.0)
**What it means:** One card triggers when the other does something

**Examples:**
- ETB triggers + Flicker effects
- Death triggers + Sacrifice outlets
- Spell triggers + Instant/sorcery spells

**Why it matters:** Triggers are the engine of many Commander decks

### Mana Synergy (Weight: 0.5)
**What it means:** Cards share colors or help with mana

**Examples:**
- Cards with overlapping colors
- Ramp spells + high CMC cards
- Cost reduction effects

**Why it matters:** Ensures smooth mana base and color consistency

### Role Interaction (Weight: 0.8)
**What it means:** Cards that fulfill complementary roles

**Examples:**
- Token creators + Token payoffs
- Sacrifice outlets + Sacrifice fodder
- Protection effects + Valuable creatures

**Why it matters:** Creates functional synergies for deck strategy

### Combo (Weight: 2.0)
**What it means:** Cards that can create infinite or game-winning interactions

**Examples:**
- Infinite mana combos
- Infinite ETB loops
- Two-card win conditions

**Why it matters:** Highest impact synergies, can win games

### Benefits (Weight: 0.7)
**What it means:** One card makes the other better

**Examples:**
- Anthem effects + Creatures
- Tribal lords + Tribal creatures
- Keyword granters + Creatures

**Why it matters:** Amplifies card effectiveness

### Type Synergy (Weight: 0.6)
**What it means:** Cards care about specific card types

**Examples:**
- "Whenever you cast an artifact..." + Artifacts
- "Artifacts you control..." + Artifacts
- Creature type matters

**Why it matters:** Build-around themes for decks

### Card Advantage (Weight: 0.9)
**What it means:** Cards that combine to generate card advantage

**Examples:**
- Multiple draw effects
- Tutor + Target synergies
- Recursion loops

**Why it matters:** Card advantage wins games

---

## Tips & Tricks

### Tip 1: Use Layouts Effectively
- **Cose:** Best for seeing natural clusters
- **Circle:** Good for counting total connections at a glance
- **Concentric:** Highlights the most connected cards (in center)

### Tip 2: Focus on Your Commander
First thing to do with any deck:
1. Click on your Commander
2. See how many cards synergize with it
3. A good Commander deck should have 20-40+ connections to the Commander

### Tip 3: Look for Disconnected Subgraphs
If you see groups of cards that only connect to each other (not the rest of the deck):
- You might have multiple strategies competing
- Consider focusing on one strategy
- Or these might be your different game plans

### Tip 4: Synergy Strength Isn't Everything
A card with only 1-2 synergies might still be essential:
- Board wipes
- Spot removal
- Ramp spells
- Protection

Don't cut these just because they have few synergies.

### Tip 5: Save Multiple Versions
When testing changes:
1. Load your original deck
2. Make changes on Archidekt
3. Load the updated version
4. Compare synergy counts and strengths

---

## Troubleshooting

### Problem: "Invalid Archidekt URL format"

**Solution:**
- Ensure URL is from Archidekt.com
- Format should be: `https://archidekt.com/decks/NUMBERS`
- Make sure the deck is public

### Problem: Deck loads but some cards missing

**Possible Causes:**
- Card name not found on Scryfall
- Network error during fetching

**Solution:**
- Check console output for specific errors
- Verify card names are spelled correctly on Archidekt
- Re-load the deck

### Problem: No synergies detected

**Possible Causes:**
- Very new deck with unrelated cards
- Very specific deck strategy not yet covered by rules

**Solutions:**
- Ensure deck has at least some known synergies
- Try a different deck to verify app is working
- Check that cards loaded correctly (click on nodes to see if data is there)

### Problem: Graph is too cluttered

**Solutions:**
1. Change layout (try Circle or Concentric)
2. Click on a single card to isolate its connections
3. (Future feature) Adjust synergy threshold to show only strongest

### Problem: App is slow

**Causes:**
- Large deck (100+ cards)
- First-time loading (Scryfall API calls)

**Solutions:**
- Be patient during initial load (30-60 seconds normal)
- Once saved, re-loading is instant
- Close other applications if performance is poor

---

## Advanced Features

### Synergy Filtering (Manual)
Currently, minimum synergy threshold is set in code.

To change (requires editing code):
1. Open `src/synergy_engine/analyzer.py`
2. Find `analyze_deck_synergies()` function
3. Change `min_synergy_threshold` parameter (default: 0.5)
4. Restart app

**Effects:**
- Lower threshold: More edges, more cluttered, but see all synergies
- Higher threshold: Cleaner graph, only strongest synergies

### Adding Custom Synergy Rules

To add your own synergy detection:

1. Open `src/synergy_engine/rules.py`
2. Create a new function:
   ```python
   def detect_my_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
       # Your detection logic
       if [condition]:
           return {
               'name': 'My Synergy',
               'description': 'Why cards synergize',
               'value': 2.0,
               'category': 'benefits',
               'subcategory': 'my_subcat'
           }
       return None
   ```
3. Add function to `ALL_RULES` list at bottom
4. Restart app and re-analyze decks

---

## Keyboard Shortcuts

Currently no keyboard shortcuts implemented.

**Future considerations:**
- Arrow keys to navigate nodes
- ESC to deselect
- Number keys to change layouts

---

## Exporting Data

### Current Capabilities
Decks are saved as JSON in `data/decks/`

**To access:**
1. Navigate to `data/decks/` folder
2. Find `{DeckName}_{DeckID}.json`
3. Open in text editor or JSON viewer

### JSON Structure
```json
{
  "deck_id": "123456",
  "name": "Deck Name",
  "cards": [...],
  "synergies": {
    "Card A||Card B": {
      "total_weight": 5.2,
      "synergies": {...}
    }
  }
}
```

### Future Export Features
- Export graph as image (PNG/SVG)
- Export synergy report as PDF
- Export to CSV for spreadsheet analysis

---

## Best Practices

### 1. Analyze Before Building
Load a deck idea before building it in paper/MTGO to:
- Verify synergies exist
- Find missing pieces
- Optimize card choices

### 2. Compare to Reference Decks
Load similar decks from EDHREC or competitive players:
- See what synergies you're missing
- Learn new interactions
- Discover tech cards

### 3. Iterative Optimization
Build → Load → Analyze → Adjust → Repeat

### 4. Focus on Strategy
Don't over-optimize for synergy count:
- Interaction is important (removal, counters)
- Ramp is essential
- Card draw is critical
- These may have fewer synergies but are still necessary

### 5. Document Your Findings
When you discover interesting synergies:
- Take screenshots
- Note them for gameplay
- Share with playgroup

---

## FAQ

**Q: Can I use decks from other sources (not Archidekt)?**
A: Currently only Archidekt is supported. Future versions may support Moxfield, TappedOut, etc.

**Q: Does this work for non-Commander formats?**
A: It can work for any deck, but synergy rules are optimized for Commander.

**Q: Are the synergy detections always accurate?**
A: No, they're heuristic-based. Some synergies may be missed, and some may be overestimated. Use as a guide, not absolute truth.

**Q: Can I share my deck visualizations?**
A: Currently no export feature. Future versions may add image export.

**Q: Does this account for banned cards?**
A: No, it doesn't filter banned cards. Check your format's ban list separately.

**Q: Can I run this online/share with friends?**
A: Currently it's a local application. Could be deployed to a server for shared access.

**Q: How often is Scryfall data updated?**
A: Data is fetched fresh each time you load a deck. Scryfall updates as new cards are released.

---

## Getting Help

**Issues or Bugs:**
- Report at: https://github.com/anthropics/claude-code/issues

**Feature Requests:**
- Same as above

**Questions:**
- Check documentation in `docs/` folder
- Review code comments

---

## Credits

**Built with:**
- Dash (Plotly)
- Dash Cytoscape
- Scryfall API
- Archidekt API

**Magic: The Gathering** is © Wizards of the Coast

---

## Changelog

**v1.0.0** (2025-10-24)
- Initial release
- Archidekt import
- Scryfall integration
- 7 synergy categories
- 11 detection rules
- Interactive graph visualization
- Deck persistence
