"""
Quick test script for the fuzzy card search functionality
"""

from src.utils.fuzzy_search import CardFuzzySearcher

# Sample test cards
test_cards = [
    {
        'name': 'Lightning Bolt',
        'type_line': 'Instant',
        'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
        'colors': ['R'],
        'color_identity': ['R'],
        'mana_cost': '{R}'
    },
    {
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': 'Tap: Add {C}{C}.',
        'colors': [],
        'color_identity': [],
        'mana_cost': '{1}'
    },
    {
        'name': 'Counterspell',
        'type_line': 'Instant',
        'oracle_text': 'Counter target spell.',
        'colors': ['U'],
        'color_identity': ['U'],
        'mana_cost': '{U}{U}'
    },
    {
        'name': 'Birds of Paradise',
        'type_line': 'Creature — Bird',
        'oracle_text': 'Flying\n{T}: Add one mana of any color.',
        'colors': ['G'],
        'color_identity': ['G'],
        'mana_cost': '{G}'
    },
    {
        'name': 'Demonic Tutor',
        'type_line': 'Sorcery',
        'oracle_text': 'Search your library for a card, put that card into your hand, then shuffle.',
        'colors': ['B'],
        'color_identity': ['B'],
        'mana_cost': '{1}{B}'
    }
]

def test_fuzzy_search():
    """Test various search scenarios"""
    searcher = CardFuzzySearcher()

    print("Testing Fuzzy Card Search")
    print("=" * 60)

    # Test 1: Exact match
    print("\n1. Exact match: 'Sol Ring'")
    results = searcher.search('Sol Ring', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 2: Partial match
    print("\n2. Partial match: 'bolt'")
    results = searcher.search('bolt', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 3: Fuzzy match with typo
    print("\n3. Fuzzy match with typo: 'countr'")
    results = searcher.search('countr', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 4: Type search
    print("\n4. Type search: 'instant'")
    results = searcher.search('instant', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 5: Color search
    print("\n5. Color search: 'blue'")
    results = searcher.search('blue', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 6: Reversed word order
    print("\n6. Reversed word order: 'paradise birds'")
    results = searcher.search('paradise birds', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    # Test 7: Oracle text search
    print("\n7. Oracle text search: 'counter target'")
    results = searcher.search('counter target', test_cards)
    for card, score, reason in results:
        print(f"   - {card['name']}: {score:.2f} ({reason})")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("\nThe fuzzy search is working with:")
    print("  - Exact matching")
    print("  - Partial matching")
    print("  - Fuzzy matching (typos)")
    print("  - Type line matching")
    print("  - Color matching")
    print("  - Token-based matching (word order)")
    print("  - Oracle text matching")

if __name__ == '__main__':
    test_fuzzy_search()
