# User Guide - MTG Commander Deck Synergy Visualizer

Complete guide to using the Deck Synergy Visualizer to analyze and optimize your Commander decks.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Loading Decks](#loading-decks)
3. [Understanding the Synergy Graph](#understanding-the-synergy-graph)
4. [Analyzing Deck Weaknesses](#analyzing-deck-weaknesses)
5. [Getting Recommendations](#getting-recommendations)
6. [Smart Card Replacement](#smart-card-replacement)
7. [Deck Editing](#deck-editing)
8. [Advanced Tips](#advanced-tips)

---

## Getting Started

### Launching the App

```bash
python app.py
```

Open your browser to `http://localhost:8050`

### Interface Overview

The app has three main tabs:
- **Synergy Graph**: Visualize card relationships
- **Mana Simulation**: Analyze mana curve and availability
- **Deck Building**: Create new decks from scratch

---

## Loading Decks

### From Archidekt

1. Go to your deck on Archidekt.com
2. Copy the deck URL (e.g., `https://archidekt.com/decks/12345`)
3. Paste into the "Deck URL" field
4. Click "Load Deck"

### From Saved Decks

1. Use the "Select Deck" dropdown
2. Choose a previously loaded deck
3. Graph updates automatically

---

## Understanding the Synergy Graph

### Graph Elements

**Nodes (Cards)**
- Size = Importance (weighted centrality)
- Color = Card type or role
- Border = Commander has thicker border

**Edges (Synergies)**
- Thickness = Synergy strength (1-12+)
- Color: Gray → Tan → Orange → Red (weak to strong)

### Interacting

- Click cards to view details
- Use role filter dropdown
- Click "View Top Cards" to highlight best

---

## Analyzing Deck Weaknesses

### Role Distribution

**8 Key Roles Tracked:**
- Ramp (8-15 recommended)
- Card Draw (8-15)
- Removal (8-15)
- Board Wipes (2-5)
- Protection (3-8)
- Recursion (2-8)
- Threats (8-20)
- Utility (5-15)

### Status Indicators

- 🟢 Green = Good (in range)
- 🟡 Yellow = Low/High (needs adjustment)
- 🔴 Red = Critical (major gap)

---

## Getting Recommendations

### Impact Ratings

- 🔥 HIGH = Critical weakness or +5 score
- ⚡ MEDIUM = Moderate issue or +2-4 score
- ℹ️ LOW = Minor improvement or +0-1 score

### What You See

- Score improvement (65 → 70)
- Roles filled
- Weaknesses addressed
- Synergy reasons
- "➕ Add to Deck" button

---

## Smart Card Replacement

### Cards to Cut Button

Shows weak cards with:
- Priority (🔴 🟡 🔵)
- Synergy score
- Replacement suggestions
- "⇄ Swap" buttons

### Swap Process

1. Click "✂️ Cards to Cut"
2. Review suggestions
3. Click "⇄ Swap" on alternative
4. Card instantly replaced
5. Graph updates
6. Save when ready

---

## Deck Editing

### Add/Remove

- Add from recommendations
- Remove by clicking card
- Cannot remove commander

### Undo/Redo

- ↶ Undo last change
- ↷ Redo undone change
- Full change history

### Saving

- Click "💾 Save Deck" when changes made
- "⚠️ Unsaved changes" indicator shows
- Saves to `data/decks/*.json`

---

## Advanced Tips

### Maximize Synergy

1. Pick a clear theme
2. Balance all 8 roles
3. Check mana curve
4. Test with simulation

### Effective Swaps

1. Start with 🔴 HIGH priority
2. Address critical weaknesses first
3. Use undo if unsure
4. Save checkpoints frequently

### Performance

- Incremental adds are fast (0.14s)
- Undo/redo slower (full re-analysis ~2s)
- Save frequently to checkpoint

---

**Happy deck building! 🎴**
