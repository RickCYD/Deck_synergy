"""
Generate embeddings for MTG cards using Claude API
Creates vector embeddings from card data and calculates cosine similarities
"""

import json
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def concatenate_card_info(card: Dict) -> str:
    """
    Create a comprehensive string representation of a card
    Includes all relevant card information for embedding

    Args:
        card: Card dictionary from minimal cards data

    Returns:
        Concatenated string representation
    """
    parts = []

    # Card name
    if card.get('name'):
        parts.append(f"Name: {card['name']}")

    # Mana cost and CMC
    if card.get('mana_cost'):
        parts.append(f"Mana Cost: {card['mana_cost']}")
    if card.get('cmc') is not None:
        parts.append(f"CMC: {card['cmc']}")

    # Type line
    if card.get('type_line'):
        parts.append(f"Type: {card['type_line']}")

    # Oracle text (most important for synergies)
    if card.get('oracle_text'):
        parts.append(f"Text: {card['oracle_text']}")

    # Colors and color identity
    if card.get('colors'):
        parts.append(f"Colors: {', '.join(card['colors'])}")
    if card.get('color_identity'):
        parts.append(f"Color Identity: {', '.join(card['color_identity'])}")

    # Power/Toughness/Loyalty
    if card.get('power'):
        parts.append(f"Power: {card['power']}")
    if card.get('toughness'):
        parts.append(f"Toughness: {card['toughness']}")
    if card.get('loyalty'):
        parts.append(f"Loyalty: {card['loyalty']}")

    # Keywords
    if card.get('keywords'):
        parts.append(f"Keywords: {', '.join(card['keywords'])}")

    # Mana production
    if card.get('produced_mana'):
        parts.append(f"Produces: {', '.join(card['produced_mana'])}")

    return " | ".join(parts)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def generate_embeddings_batch(cards: List[Dict], client: Anthropic, batch_size: int = 100) -> List[Dict]:
    """
    Generate embeddings for a batch of cards using Claude API

    Args:
        cards: List of card dictionaries
        client: Anthropic client
        batch_size: Number of cards to process at once

    Returns:
        List of dicts with card_name, text, and embedding
    """
    results = []
    total = len(cards)

    print(f"Generating embeddings for {total} cards...")

    for i in range(0, total, batch_size):
        batch = cards[i:i + batch_size]
        batch_end = min(i + batch_size, total)

        print(f"Processing batch {i//batch_size + 1} ({i+1}-{batch_end}/{total})...")

        for card in batch:
            # Skip cards without names or with invalid data
            if not card.get('name'):
                continue

            # Create text representation
            card_text = concatenate_card_info(card)

            try:
                # Generate embedding using Claude's best embedding model
                # Note: Using voyage-3 which is Claude's recommended embedding model
                response = client.embeddings.create(
                    model="voyage-3",
                    input=card_text
                )

                embedding = response.embeddings[0]

                results.append({
                    'card_name': card['name'],
                    'text': card_text,
                    'embedding': embedding
                })

            except Exception as e:
                print(f"Error generating embedding for {card.get('name', 'Unknown')}: {e}")
                continue

        print(f"  Completed {len(results)}/{total} embeddings")

    return results


def calculate_all_similarities(embeddings_data: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Calculate cosine similarity between all card pairs

    Args:
        embeddings_data: List of dicts with card_name, text, and embedding

    Returns:
        Dict mapping card names to list of similar cards with scores
    """
    similarities = {}
    total = len(embeddings_data)

    print(f"\nCalculating similarities between {total} cards...")

    for i, card_data in enumerate(embeddings_data):
        card_name = card_data['card_name']
        card_embedding = card_data['embedding']

        # Calculate similarity with all other cards
        card_similarities = []

        for j, other_data in enumerate(embeddings_data):
            if i == j:
                continue  # Skip self-comparison

            other_name = other_data['card_name']
            other_embedding = other_data['embedding']

            similarity = cosine_similarity(card_embedding, other_embedding)

            card_similarities.append({
                'card': other_name,
                'similarity': round(similarity, 4)
            })

        # Sort by similarity (highest first)
        card_similarities.sort(key=lambda x: x['similarity'], reverse=True)

        similarities[card_name] = card_similarities

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{total} cards")

    print(f"Completed similarity calculations for all {total} cards")

    return similarities


def main():
    """Main execution function"""
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please add your Claude API key to a .env file:")
        print("  ANTHROPIC_API_KEY=your-key-here")
        return

    # Initialize Claude client
    client = Anthropic(api_key=api_key)

    # Load card data
    cards_file = Path(__file__).parent.parent / 'data' / 'cards' / 'cards-minimal.json'

    if not cards_file.exists():
        print(f"ERROR: {cards_file} not found")
        return

    print(f"Loading cards from {cards_file}...")
    with open(cards_file, 'r', encoding='utf-8') as f:
        cards = json.load(f)

    print(f"Loaded {len(cards)} cards")

    # Filter out tokens and cards without oracle text (for better embeddings)
    valid_cards = []
    for card in cards:
        # Skip tokens and cards without names
        if not card.get('name') or not card.get('type_line'):
            continue

        # Skip most tokens (but keep cards with oracle text)
        type_line = card.get('type_line', '').lower()
        if 'token' in type_line and not card.get('oracle_text'):
            continue

        # Skip cards with no meaningful data
        if not card.get('oracle_text') and not card.get('keywords'):
            continue

        valid_cards.append(card)

    print(f"Filtered to {len(valid_cards)} valid cards (excluding tokens and empty cards)")

    # For testing, limit to first 500 cards (remove this limit for production)
    # This helps with API costs during development
    test_limit = 500
    if len(valid_cards) > test_limit:
        print(f"\n⚠️  LIMITING TO FIRST {test_limit} CARDS FOR TESTING")
        print(f"To process all cards, remove the test_limit in the script")
        valid_cards = valid_cards[:test_limit]

    # Generate embeddings
    embeddings_data = generate_embeddings_batch(valid_cards, client)

    if not embeddings_data:
        print("ERROR: No embeddings were generated")
        return

    print(f"\nSuccessfully generated {len(embeddings_data)} embeddings")

    # Calculate similarities
    similarities = calculate_all_similarities(embeddings_data)

    # Create output structure
    output = {
        'metadata': {
            'total_cards': len(embeddings_data),
            'model': 'voyage-3',
            'embedding_dimensions': len(embeddings_data[0]['embedding']) if embeddings_data else 0
        },
        'embeddings': embeddings_data,
        'similarities': similarities
    }

    # Save to JSON file
    output_file = Path(__file__).parent.parent / 'data' / 'cards' / 'card-embeddings.json'

    print(f"\nSaving embeddings to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Successfully saved embeddings for {len(embeddings_data)} cards")
    print(f"   File: {output_file}")
    print(f"   Size: {output_file.stat().st_size / (1024*1024):.2f} MB")

    # Print some example similarities
    print("\n=== Example Similarities ===")
    first_card = embeddings_data[0]['card_name']
    top_similar = similarities[first_card][:5]

    print(f"\nTop 5 cards similar to '{first_card}':")
    for item in top_similar:
        print(f"  {item['similarity']:.4f} - {item['card']}")


if __name__ == "__main__":
    main()
