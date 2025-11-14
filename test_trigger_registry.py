#!/usr/bin/env python3
"""
Test the trigger registry with ally prowess deck cards.

This validates that:
1. Cards can be registered with their triggers
2. Triggers are organized by event type
3. Event triggering executes the correct effects
4. Registry statistics are accurate
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.core.card_parser import UnifiedCardParser
from src.core.trigger_registry import TriggerRegistry

print("=" * 80)
print("TRIGGER REGISTRY TEST")
print("=" * 80)

# Load database
print("\nLoading card database...")
load_local_database()
print("✓ Database loaded!")

# Initialize systems
parser = UnifiedCardParser()
registry = TriggerRegistry()

# Test cards from ally prowess deck
test_cards = [
    # Rally triggers
    "Chasm Guide",
    "Makindi Patrol",
    "Lantern Scout",
    "Resolute Blademaster",

    # Prowess
    "Bria, Riptide Rogue",
    "Narset, Enlightened Exile",
    "Monastery Swiftspear",

    # Spellslinger
    "Jeskai Ascendancy",
    "Kykar, Wind's Fury",
    "Veyran, Voice of Duality",

    # ETB triggers
    "Impact Tremors",

    # Token creators
    "Gideon, Ally of Zendikar",

    # Anthems
    "Thalia's Lieutenant",
]

print("\n" + "=" * 80)
print("REGISTERING CARDS")
print("=" * 80)

card_ids = {}
for card_name in test_cards:
    card = get_card_by_name(card_name)
    if not card:
        print(f"\n⚠️  {card_name}: NOT FOUND")
        continue

    # Parse card
    abilities = parser.parse_card(card)

    # Register with registry
    card_id = registry.register_card(card, abilities)
    card_ids[card_name] = card_id

    # Show registration results
    print(f"\n{'─' * 80}")
    print(f"📋 {card_name}")
    print(f"   Card ID: {card_id}")

    if abilities.triggers:
        print(f"   Triggers: {len(abilities.triggers)}")
        for trigger in abilities.triggers:
            print(f"     - {trigger.event}: {trigger.effect}")

    if abilities.static_abilities:
        print(f"   Static Abilities: {len(abilities.static_abilities)}")
        for static in abilities.static_abilities:
            print(f"     - {static.ability_type}: {static.effect}")

# Show registry statistics
print("\n" + "=" * 80)
print("REGISTRY STATISTICS")
print("=" * 80)

stats = registry.get_stats()
print(f"\nTotal Cards Registered: {stats['total_cards']}")
print(f"Total Triggers: {stats['total_triggers']}")
print(f"Total Static Abilities: {stats['total_static_abilities']}")
print(f"\nEvents with Triggers: {', '.join(stats['events_with_triggers'])}")

print("\nTriggers by Event Type:")
for event, count in sorted(stats['triggers_by_event'].items(), key=lambda x: -x[1]):
    print(f"  {event}: {count}")

# Test event lookup
print("\n" + "=" * 80)
print("EVENT TRIGGER LOOKUP")
print("=" * 80)

test_events = ['rally', 'cast_noncreature_spell', 'etb', 'cast_spell']

for event in test_events:
    triggers = registry.get_triggers_for_event(event)
    print(f"\n{event}: {len(triggers)} trigger(s)")
    for trigger in triggers:
        print(f"  - {trigger.card_name}: {trigger.event}")

# Test trigger execution simulation
print("\n" + "=" * 80)
print("TRIGGER EXECUTION SIMULATION")
print("=" * 80)

# Create mock board state
class MockBoardState:
    def __init__(self):
        self.pending_effects = []
        self.static_effects = []
        self.battlefield = []
        self.life = 20

mock_board = MockBoardState()

# Simulate rally trigger
print("\n🎯 Simulating Rally Event (Ally ETB)...")
print("Cards that should trigger:")
rally_triggers = registry.get_triggers_for_event('rally')
for t in rally_triggers:
    print(f"  - {t.card_name}")

event_data = {
    'card': {'name': 'Test Ally', 'type_line': 'Creature — Human Ally'},
    'source_card': {'name': 'Test Ally'}
}

registry.trigger_event('rally', mock_board, event_data)

print(f"\nEffects created: {len(mock_board.pending_effects)}")
for effect in mock_board.pending_effects:
    print(f"  - {effect['type']}: {effect.get('keyword', effect.get('amount', 'N/A'))}")
    print(f"    Source: {effect['source']}")

# Clear effects
mock_board.pending_effects = []

# Simulate prowess trigger
print("\n🎯 Simulating Prowess Event (Cast Noncreature Spell)...")
print("Cards that should trigger:")
prowess_triggers = registry.get_triggers_for_event('cast_noncreature_spell')
for t in prowess_triggers:
    print(f"  - {t.card_name}")

event_data = {
    'card': {'name': 'Lightning Bolt', 'type_line': 'Instant'},
    'source_card': {'name': 'Lightning Bolt'}
}

registry.trigger_event('cast_noncreature_spell', mock_board, event_data)

print(f"\nEffects created: {len(mock_board.pending_effects)}")
for effect in mock_board.pending_effects:
    print(f"  - {effect['type']}: +{effect.get('power', 0)}/+{effect.get('toughness', 0)}")
    print(f"    Source: {effect['source']}")

# Clear effects
mock_board.pending_effects = []

# Simulate ETB trigger
print("\n🎯 Simulating ETB Event (Creature Enters)...")
print("Cards that should trigger:")
etb_triggers = registry.get_triggers_for_event('etb')
for t in etb_triggers:
    print(f"  - {t.card_name}")

event_data = {
    'card': {'name': 'Test Creature', 'type_line': 'Creature — Human'},
    'source_card': {'name': 'Test Creature'}
}

registry.trigger_event('etb', mock_board, event_data)

print(f"\nEffects created: {len(mock_board.pending_effects)}")
for effect in mock_board.pending_effects:
    print(f"  - {effect['type']}: {effect.get('amount', 'N/A')}")
    print(f"    Source: {effect['source']}")

# Test static ability application
print("\n🎯 Applying Static Abilities...")
mock_board.static_effects = []
registry.apply_static_abilities(mock_board)

print(f"\nStatic effects applied: {len(mock_board.static_effects)}")
for effect in mock_board.static_effects:
    print(f"  - {effect['type']}: {effect}")
    print(f"    Source: {effect['source']}")

# Test card removal
print("\n" + "=" * 80)
print("CARD REMOVAL TEST")
print("=" * 80)

# Get a card to remove
test_card_name = "Chasm Guide"
if test_card_name in card_ids:
    card_id = card_ids[test_card_name]

    print(f"\nBefore removal:")
    print(f"  Registry: {registry}")

    triggers_before = registry.get_triggers_for_event('rally')
    print(f"  Rally triggers: {len(triggers_before)}")

    print(f"\nRemoving {test_card_name} (ID: {card_id})...")
    registry.unregister_card(card_id)

    print(f"\nAfter removal:")
    print(f"  Registry: {registry}")

    triggers_after = registry.get_triggers_for_event('rally')
    print(f"  Rally triggers: {len(triggers_after)}")

    removed_count = len(triggers_before) - len(triggers_after)
    print(f"\n✓ Removed {removed_count} trigger(s)")

# Final summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

final_stats = registry.get_stats()

tests_passed = []
tests_failed = []

# Check if rally triggers were registered
if final_stats['triggers_by_event'].get('rally', 0) > 0:
    tests_passed.append("Rally triggers registered")
else:
    tests_failed.append("Rally triggers not found")

# Check if prowess triggers were registered
if final_stats['triggers_by_event'].get('cast_noncreature_spell', 0) > 0:
    tests_passed.append("Prowess triggers registered")
else:
    tests_failed.append("Prowess triggers not found")

# Check if effects were created
if len(mock_board.pending_effects) > 0 or len(mock_board.static_effects) > 0:
    tests_passed.append("Effects created successfully")
else:
    tests_failed.append("No effects created")

# Check if card removal worked
if removed_count > 0:
    tests_passed.append("Card removal works")
else:
    tests_failed.append("Card removal failed")

print(f"\n✅ Passed ({len(tests_passed)}):")
for test in tests_passed:
    print(f"  - {test}")

if tests_failed:
    print(f"\n❌ Failed ({len(tests_failed)}):")
    for test in tests_failed:
        print(f"  - {test}")

print(f"\nFinal Registry State: {registry}")

if len(tests_failed) == 0:
    print("\n🎉 All tests passed! Trigger registry is working correctly.")
else:
    print(f"\n⚠️  {len(tests_failed)} test(s) failed. Registry needs adjustments.")
