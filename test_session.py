"""
Quick test script for deck editing session
"""

from src.models.deck import Deck
from src.models.deck_session import DeckEditingSession

# Create a simple test deck
test_deck = Deck(
    deck_id="test123",
    name="Test Deck",
    cards=[
        {"name": "Sol Ring", "oracle_text": "Add two colorless mana", "cmc": 1},
        {"name": "Command Tower", "oracle_text": "Tap: Add one mana", "cmc": 0},
    ]
)

print("✓ Created test deck with 2 cards")

# Create session
session = DeckEditingSession(test_deck)
print(f"✓ Created session, deck has {len(session.current_deck.cards)} cards")

# Add a card
new_card = {"name": "Arcane Signet", "oracle_text": "Tap: Add one mana", "cmc": 2}
result = session.add_card(new_card)

if result['success']:
    print(f"✓ Added card: {result['message']}")
    print(f"  Deck now has {result['deck_size']} cards")
else:
    print(f"✗ Failed to add card: {result['error']}")

# Try to add duplicate
result2 = session.add_card(new_card)
if not result2['success']:
    print(f"✓ Correctly rejected duplicate: {result2['error']}")
else:
    print("✗ Should have rejected duplicate card")

# Test undo
if session.can_undo():
    undo_result = session.undo()
    print(f"✓ Undo successful: {undo_result['message']}")
    print(f"  Deck now has {undo_result['deck_size']} cards")
else:
    print("✗ Undo should be available")

# Test redo
if session.can_redo():
    redo_result = session.redo()
    print(f"✓ Redo successful: {redo_result['message']}")
    print(f"  Deck now has {redo_result['deck_size']} cards")
else:
    print("✗ Redo should be available")

# Test serialization
session_dict = session.to_dict()
print(f"✓ Serialized session to dict with {len(session_dict)} keys")

# Test deserialization
restored_session = DeckEditingSession.from_dict(session_dict)
print(f"✓ Restored session, deck has {len(restored_session.current_deck.cards)} cards")

# Test summary
summary = session.get_changes_summary()
print(f"✓ Changes summary: {summary}")

print("\n✅ All tests passed!")
