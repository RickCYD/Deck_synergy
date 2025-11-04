# MTG Card Embeddings for Synergy Analysis

This feature adds AI-powered semantic similarity analysis using Claude's embedding API to detect card synergies based on meaning rather than just rules.

## Overview

The embedding system creates vector representations of MTG cards and uses cosine similarity to find semantically related cards. This complements the rule-based synergy detection by finding cards that work well together even if they don't match specific synergy patterns.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `anthropic` package (v0.39.0) needed for Claude API access.

### 2. Set Up API Key

Create a `.env` file in the project root with your Claude API key:

```
ANTHROPIC_API_KEY=your-key-here
```

You can get an API key from: https://console.anthropic.com/

### 3. Generate Embeddings

Run the embedding generation script:

```bash
python scripts/generate_embeddings.py
```

**Note:** The script is currently limited to 500 cards for testing to control API costs. To process all cards, edit `scripts/generate_embeddings.py` and remove or increase the `test_limit` variable.

The script will:
- Load cards from `data/cards/cards-minimal.json`
- Create text representations of each card (name, type, oracle text, etc.)
- Generate embeddings using Claude's `voyage-3` model
- Calculate cosine similarities between all card pairs
- Save results to `data/cards/card-embeddings.json`

**Estimated time:** ~5-10 minutes for 500 cards

**Estimated cost:** ~$0.10 per 500 cards (varies by API pricing)

## Usage

### In the Web Application

1. Load the application:
   ```bash
   python app.py
   ```

2. Load a deck from Archidekt or select a saved deck

3. Toggle between synergy modes using the **Synergy Mode** switch:
   - **Rule-Based**: Uses hand-crafted synergy detection rules
   - **AI Embeddings**: Uses semantic similarity from embeddings

4. The following features will use the selected mode:
   - **Graph visualization**: Shows connections based on similarities
   - **🔍 Get Recommendations**: Suggests cards semantically similar to your deck
   - **✂️ Cards to Cut**: Identifies cards with low semantic similarity to the rest
   - **View Top Cards**: Ranks cards by average similarity to other deck cards

### Programmatic Usage

```python
from src.synergy_engine import embedding_analyzer

# Load embeddings
embedding_analyzer.load_embedding_analyzer()

# Get similar cards
similar = embedding_analyzer.get_similar_cards("Sol Ring", limit=10)

# Get recommendations for a deck
recommendations = embedding_analyzer.get_deck_recommendations(
    deck_cards=my_deck_cards,
    limit=20
)

# Score cards in the deck
scored = embedding_analyzer.score_deck_cards(my_deck_cards)

# Find top synergies
top_synergies = embedding_analyzer.get_top_embedding_synergies(
    my_deck_cards,
    top_n=10
)
```

## How It Works

### 1. Card Text Representation

Each card is converted to a comprehensive text string containing:
- Name
- Mana cost and CMC
- Type line
- Oracle text (abilities and rules text)
- Colors and color identity
- Power/toughness/loyalty
- Keywords
- Mana production

Example:
```
Name: Sol Ring | Mana Cost: {1} | CMC: 1.0 | Type: Artifact | Text: {T}: Add {C}{C}. | Colors: | Color Identity: | Produces: C
```

### 2. Embedding Generation

The text is passed to Claude's `voyage-3` embedding model, which creates a high-dimensional vector (typically 1024 dimensions) that captures the semantic meaning of the card.

### 3. Similarity Calculation

Cosine similarity is calculated between all card pairs:

```
similarity = (A · B) / (||A|| × ||B||)
```

Where:
- A and B are embedding vectors
- · is the dot product
- ||A|| and ||B|| are vector magnitudes
- Result ranges from -1 to 1 (typically 0.3 to 0.9 for MTG cards)

### 4. Synergy Detection

Cards with high cosine similarity (>0.6 by default) are considered synergistic. The system:
- Ranks recommendations by average similarity to deck cards
- Identifies low-performing cards with low average similarity
- Highlights strongest card pairs in the graph

## Data Format

The embeddings file (`data/cards/card-embeddings.json`) contains:

```json
{
  "metadata": {
    "total_cards": 500,
    "model": "voyage-3",
    "embedding_dimensions": 1024
  },
  "embeddings": [
    {
      "card_name": "Sol Ring",
      "text": "Name: Sol Ring | ...",
      "embedding": [0.123, -0.456, ...]
    }
  ],
  "similarities": {
    "Sol Ring": [
      {"card": "Mana Crypt", "similarity": 0.8542},
      {"card": "Arcane Signet", "similarity": 0.8123},
      ...
    ]
  }
}
```

## Performance Notes

- **File size**: ~10-20 MB per 500 cards (embeddings are large vectors)
- **Load time**: ~2-3 seconds at startup
- **Memory usage**: ~100-200 MB for 500 cards loaded in memory
- **Recommendation speed**: Near-instant (pre-computed similarities)

## Comparison: Rules vs Embeddings

### Rule-Based Synergies
**Pros:**
- Explicit, interpretable reasons
- No API costs
- Captures mechanical interactions (e.g., "ETB + flicker")
- Fast computation

**Cons:**
- Requires manual rule creation
- May miss subtle thematic synergies
- Limited to coded patterns

### Embedding-Based Synergies
**Pros:**
- Captures semantic/thematic relationships
- No manual rules needed
- Finds unexpected connections
- Handles new cards automatically

**Cons:**
- Requires API access and costs
- Less interpretable (why are these similar?)
- May surface false positives
- One-time generation cost

### Best Practice

Use **both** modes:
1. **Rules mode** for your main deck building (mechanical synergies)
2. **Embeddings mode** to discover alternative cards and thematic connections
3. Compare results to find cards that score high in both modes (strongest picks)

## Troubleshooting

### "Embeddings not available" warning

The embeddings file doesn't exist. Run:
```bash
python scripts/generate_embeddings.py
```

### "Out of memory" errors

Reduce the number of cards in the embeddings file or increase system RAM.

### API errors

- Check your API key in `.env`
- Verify account has credits: https://console.anthropic.com/
- Check rate limits (default: 50 requests/minute)

### Slow performance

- Embeddings are loaded at startup (one-time cost)
- Similarity lookups are pre-computed (very fast)
- If still slow, reduce the number of cards in embeddings

## Future Enhancements

- [ ] Fine-tune similarity thresholds per format (Commander, Modern, etc.)
- [ ] Weight different card attributes (oracle text > type line > name)
- [ ] Cluster cards by archetype using embedding distances
- [ ] Generate embedding-based deck descriptionsand themes
- [ ] Support for deck comparison using average embeddings
- [ ] Real-time embedding generation for custom cards

## Cost Estimation

Based on Claude API pricing (as of 2024):

- **Voyage-3 embeddings**: ~$0.0002 per 1K characters
- **Average card**: ~200 characters
- **500 cards**: ~100K characters = **$0.02**
- **All cards (~30K)**: ~$1.20

**Note:** Prices may vary. Check current pricing at https://www.anthropic.com/pricing

## License

This feature uses the Claude API which requires an Anthropic account and API key. The embedding data generated is derived from MTG card data and should only be used for personal deckbuilding purposes in compliance with Wizards of the Coast's fan content policy.
