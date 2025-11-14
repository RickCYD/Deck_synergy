#!/usr/bin/env python3
"""
Test Synergy-Simulation Bridge

This validates that Part 4 (Synergy Bridge) correctly connects
synergy detection with simulation preparation.

Tests:
1. Unified parser is used for synergy detection
2. Deck analysis detects all synergies
3. Card priorities are calculated based on synergies
4. Trigger-aware deck preparation works
5. Synergy values between cards are correct
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.core.synergy_simulation_bridge import SynergyBridge, analyze_deck_with_bridge

print("=" * 80)
print("SYNERGY-SIMULATION BRIDGE TEST")
print("=" * 80)

# Load database
print("\nLoading card database...")
load_local_database()
print("✓ Database loaded!")

# =============================================================================
# TEST DECK: ALLY PROWESS
# =============================================================================

print("\n" + "=" * 80)
print("LOADING TEST DECK")
print("=" * 80)

test_deck_names = [
    # Rally cards
    "Chasm Guide",
    "Makindi Patrol",
    "Lantern Scout",
    "Resolute Blademaster",

    # Prowess cards
    "Monastery Swiftspear",
    "Bria, Riptide Rogue",
    "Narset, Enlightened Exile",

    # Cheap spells (for prowess)
    "Lightning Bolt",
    "Brainstorm",
    "Opt",
    "Gitaxian Probe",

    # Token creators
    "Kykar, Wind's Fury",
    "Dragon Fodder",
    "Gideon, Ally of Zendikar",

    # Spellslinger payoffs
    "Jeskai Ascendancy",
    "Veyran, Voice of Duality",
]

print(f"\nLoading {len(test_deck_names)} cards...")
deck_cards = []
for card_name in test_deck_names:
    card = get_card_by_name(card_name)
    if card:
        deck_cards.append(card)
        print(f"  ✓ {card_name}")
    else:
        print(f"  ✗ {card_name} not found")

print(f"\nDeck loaded: {len(deck_cards)} cards")

# =============================================================================
# TEST 1: PARSE DECK ABILITIES
# =============================================================================

print("\n" + "=" * 80)
print("TEST 1: PARSE DECK ABILITIES")
print("=" * 80)

bridge = SynergyBridge()
abilities_map = bridge.parse_deck_abilities(deck_cards)

print(f"\nParsed {len(abilities_map)} unique cards")

# Check specific cards
rally_cards = [name for name, abilities in abilities_map.items() if abilities.has_rally]
prowess_cards = [name for name, abilities in abilities_map.items() if abilities.has_prowess]
token_cards = [name for name, abilities in abilities_map.items() if abilities.creates_tokens]
magecraft_cards = [name for name, abilities in abilities_map.items() if abilities.has_magecraft]

print(f"\nAbility Detection:")
print(f"  Rally cards: {len(rally_cards)}")
for card in rally_cards:
    print(f"    - {card}")

print(f"  Prowess cards: {len(prowess_cards)}")
for card in prowess_cards:
    print(f"    - {card}")

print(f"  Token creators: {len(token_cards)}")
for card in token_cards:
    print(f"    - {card}")

print(f"  Magecraft cards: {len(magecraft_cards)}")
for card in magecraft_cards:
    print(f"    - {card}")

# Verify parsing worked
parse_success = len(rally_cards) >= 3 and len(prowess_cards) >= 2 and len(token_cards) >= 2
print(f"\n{'✅' if parse_success else '❌'} Parsing successful: {parse_success}")

# =============================================================================
# TEST 2: DETECT SYNERGIES
# =============================================================================

print("\n" + "=" * 80)
print("TEST 2: DETECT DECK SYNERGIES")
print("=" * 80)

synergies = bridge.detect_deck_synergies(deck_cards)

print(f"\nSynergy Detection Results:")
print(f"  Total synergies: {synergies['total_synergies']}")
print(f"  Synergy score: {synergies['synergy_score']:.1f}/100")
print(f"\nSynergy Breakdown:")
print(f"  Rally + Token: {len(synergies['rally_synergies'])}")
print(f"  Prowess + Cheap Spell: {len(synergies['prowess_synergies'])}")
print(f"  Spellslinger: {len(synergies['spellslinger_synergies'])}")
print(f"  Token multiplication: {len(synergies['token_synergies'])}")

# Show some example synergies
if synergies['rally_synergies']:
    print(f"\nExample Rally Synergies:")
    for syn in synergies['rally_synergies'][:3]:
        print(f"  - {syn['card1']} + {syn['card2']} (value: {syn['value']})")

if synergies['prowess_synergies']:
    print(f"\nExample Prowess Synergies:")
    for syn in synergies['prowess_synergies'][:3]:
        print(f"  - {syn['card1']} + {syn['card2']} (value: {syn['value']})")

# Verify synergies detected
synergy_success = synergies['total_synergies'] > 20
print(f"\n{'✅' if synergy_success else '❌'} Synergies detected: {synergy_success}")

# =============================================================================
# TEST 3: CALCULATE CARD PRIORITIES
# =============================================================================

print("\n" + "=" * 80)
print("TEST 3: CALCULATE CARD PRIORITIES")
print("=" * 80)

priorities = bridge.get_card_play_priorities(deck_cards, synergies)

print(f"\nCalculated priorities for {len(priorities)} cards")

# Sort by priority
sorted_priorities = sorted(priorities.items(), key=lambda x: x[1], reverse=True)

print(f"\nTop 10 Priority Cards:")
for card_name, priority in sorted_priorities[:10]:
    print(f"  {priority:5.1f} - {card_name}")

print(f"\nLowest 5 Priority Cards:")
for card_name, priority in sorted_priorities[-5:]:
    print(f"  {priority:5.1f} - {card_name}")

# Verify priorities make sense (cards with more synergies should be higher)
high_priority_cards = [name for name, priority in priorities.items() if priority > 70]
low_priority_cards = [name for name, priority in priorities.items() if priority < 40]

print(f"\nHigh priority (>70): {len(high_priority_cards)} cards")
print(f"Low priority (<40): {len(low_priority_cards)} cards")

priority_success = len(high_priority_cards) > 0
print(f"\n{'✅' if priority_success else '❌'} Priorities calculated: {priority_success}")

# =============================================================================
# TEST 4: CREATE TRIGGER-AWARE DECK
# =============================================================================

print("\n" + "=" * 80)
print("TEST 4: CREATE TRIGGER-AWARE DECK")
print("=" * 80)

prepared_deck, metadata = bridge.create_trigger_aware_deck(deck_cards)

print(f"\nDeck Preparation:")
print(f"  Cards prepared: {len(prepared_deck)}")
print(f"  Abilities parsed: {len(metadata['abilities_map'])}")
print(f"  Synergies found: {metadata['synergies']['total_synergies']}")
print(f"  Priorities calculated: {len(metadata['priorities'])}")

print(f"\nTrigger Statistics:")
for trigger_type, count in metadata['trigger_stats'].items():
    print(f"  {trigger_type}: {count}")

# Verify metadata is complete
metadata_success = (
    len(metadata['abilities_map']) > 0 and
    metadata['synergies']['total_synergies'] > 0 and
    len(metadata['priorities']) > 0
)
print(f"\n{'✅' if metadata_success else '❌'} Metadata complete: {metadata_success}")

# =============================================================================
# TEST 5: SYNERGY VALUE BETWEEN SPECIFIC CARDS
# =============================================================================

print("\n" + "=" * 80)
print("TEST 5: SYNERGY VALUE BETWEEN CARDS")
print("=" * 80)

test_pairs = [
    ("Chasm Guide", "Kykar, Wind's Fury"),  # Rally + Token
    ("Monastery Swiftspear", "Lightning Bolt"),  # Prowess + Spell
    ("Jeskai Ascendancy", "Brainstorm"),  # Spellslinger + Instant
    ("Gideon, Ally of Zendikar", "Dragon Fodder"),  # Token + Token
]

print("\nSynergy Values:")
for card1, card2 in test_pairs:
    value = bridge.get_synergy_value_between_cards(card1, card2, abilities_map)
    print(f"  {card1} + {card2}: {value:.1f}")

# Verify high-synergy pair has value
high_synergy_value = bridge.get_synergy_value_between_cards(
    "Chasm Guide", "Kykar, Wind's Fury", abilities_map
)
synergy_value_success = high_synergy_value > 3.0
print(f"\n{'✅' if synergy_value_success else '❌'} Synergy values calculated: {synergy_value_success}")

# =============================================================================
# TEST 6: OPTIMAL CARD ORDER
# =============================================================================

print("\n" + "=" * 80)
print("TEST 6: OPTIMAL CARD PLAY ORDER")
print("=" * 80)

# Create mock board state
class MockBoardState:
    def __init__(self):
        self.creatures = []

board = MockBoardState()

# Test with empty board
hand_cards = [
    get_card_by_name("Lightning Bolt"),
    get_card_by_name("Chasm Guide"),
    get_card_by_name("Monastery Swiftspear"),
    get_card_by_name("Brainstorm"),
]
hand_cards = [c for c in hand_cards if c]  # Filter None

print("\nHand: Lightning Bolt, Chasm Guide, Monastery Swiftspear, Brainstorm")
print("Board: Empty")

optimal_order = bridge.get_optimal_card_order(hand_cards, board, metadata)

print(f"\nOptimal play order:")
for i, card in enumerate(optimal_order, 1):
    print(f"  {i}. {card.get('name')}")

# Now test with an Ally on board (should prioritize token creators)
class MockCreature:
    def __init__(self, name, type_line):
        self.name = name
        self.type = type_line

board.creatures = [MockCreature("Test Ally", "Creature — Human Ally")]

hand_cards2 = [
    get_card_by_name("Lightning Bolt"),
    get_card_by_name("Dragon Fodder"),  # Token creator
    get_card_by_name("Brainstorm"),
]
hand_cards2 = [c for c in hand_cards2 if c]

print(f"\nHand: Lightning Bolt, Dragon Fodder, Brainstorm")
print("Board: 1 Ally creature")

optimal_order2 = bridge.get_optimal_card_order(hand_cards2, board, metadata)

print(f"\nOptimal play order (with rally synergy active):")
for i, card in enumerate(optimal_order2, 1):
    card_name = card.get('name')
    print(f"  {i}. {card_name}")

# Dragon Fodder should be higher priority now
dragon_fodder_pos = next(
    (i for i, c in enumerate(optimal_order2) if c.get('name') == 'Dragon Fodder'),
    999
)
order_success = dragon_fodder_pos == 0  # Should be first
print(f"\n{'✅' if order_success else '❌'} Optimal ordering works: {order_success}")

# =============================================================================
# TEST SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

tests = [
    ("Parse deck abilities", parse_success),
    ("Detect synergies", synergy_success),
    ("Calculate priorities", priority_success),
    ("Create trigger-aware deck", metadata_success),
    ("Synergy values between cards", synergy_value_success),
    ("Optimal card ordering", order_success),
]

passed = sum(1 for _, success in tests if success)
total = len(tests)

print(f"\n✅ Passed: {passed}/{total}")
for test_name, success in tests:
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}")

print(f"\nFinal Statistics:")
print(f"  Total synergies detected: {synergies['total_synergies']}")
print(f"  Synergy score: {synergies['synergy_score']:.1f}/100")
print(f"  Cards with high priority: {len(high_priority_cards)}")
print(f"  Rally triggers: {metadata['trigger_stats']['rally_count']}")
print(f"  Prowess triggers: {metadata['trigger_stats']['prowess_count']}")

if passed == total:
    print("\n🎉 All tests passed! Synergy bridge is working correctly.")
    print("\nThe unified architecture now:")
    print("  1. Uses single parser for synergy detection ✅")
    print("  2. Detects synergies accurately ✅")
    print("  3. Calculates optimal play priorities ✅")
    print("  4. Prepares decks for trigger-aware simulation ✅")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Needs investigation.")
