#!/usr/bin/env python3
"""
Test the unified card parser with real cards from the ally prowess deck.
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.core.card_parser import UnifiedCardParser

print("Loading database...")
load_local_database()
print("Database loaded!\n")

parser = UnifiedCardParser()

# Test cards from the ally prowess deck
test_cards = [
    ("Chasm Guide", "rally trigger"),
    ("Makindi Patrol", "rally trigger"),
    ("Lantern Scout", "rally trigger"),
    ("Bria, Riptide Rogue", "prowess"),
    ("Narset, Enlightened Exile", "prowess"),
    ("Jeskai Ascendancy", "spellslinger"),
    ("Kykar, Wind's Fury", "spellslinger + tokens"),
    ("Veyran, Voice of Duality", "magecraft"),
    ("Impact Tremors", "ETB trigger"),
    ("Gideon, Ally of Zendikar", "token creation"),
    ("Banner of Kinship", "anthem"),
    ("Brainstorm", "draw spell"),
    ("Lightning Bolt", "damage spell"),
]

print("=" * 80)
print("UNIFIED PARSER TEST RESULTS")
print("=" * 80)

for card_name, expected in test_cards:
    card = get_card_by_name(card_name)
    if not card:
        print(f"\n❌ {card_name}: NOT FOUND")
        continue

    abilities = parser.parse_card(card)

    print(f"\n{'─' * 80}")
    print(f"📋 {card_name} ({expected})")
    print(f"{'─' * 80}")

    # Show basic info
    print(f"CMC: {abilities.cmc}")
    print(f"Types: {abilities.creature_types if abilities.creature_types else 'N/A'}")
    print(f"Keywords: {abilities.keywords if abilities.keywords else 'N/A'}")

    # Show triggers
    if abilities.triggers:
        print(f"\nTriggers ({len(abilities.triggers)}):")
        for i, trigger in enumerate(abilities.triggers, 1):
            print(f"  {i}. Event: {trigger.event}")
            print(f"     Effect Type: {trigger.effect_type}")
            print(f"     Effect: {trigger.effect}")
            if trigger.value > 0:
                print(f"     Value: {trigger.value}")

    # Show static abilities
    if abilities.static_abilities:
        print(f"\nStatic Abilities ({len(abilities.static_abilities)}):")
        for i, static in enumerate(abilities.static_abilities, 1):
            print(f"  {i}. Type: {static.ability_type}")
            print(f"     Effect: {static.effect}")
            print(f"     Targets: {static.targets}")

    # Show flags
    flags = []
    if abilities.has_rally:
        flags.append("✓ Rally")
    if abilities.has_prowess:
        flags.append("✓ Prowess")
    if abilities.has_magecraft:
        flags.append("✓ Magecraft")
    if abilities.has_etb:
        flags.append("✓ ETB")
    if abilities.creates_tokens:
        flags.append("✓ Creates Tokens")
    if abilities.is_draw:
        flags.append("✓ Draw")
    if abilities.is_removal:
        flags.append("✓ Removal")

    if flags:
        print(f"\nFlags: {', '.join(flags)}")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

# Test specific expectations
test_cases = [
    ("Chasm Guide", lambda a: a.has_rally and any(t.effect == 'haste' for t in a.get_triggers('rally'))),
    ("Bria, Riptide Rogue", lambda a: a.has_prowess),
    ("Jeskai Ascendancy", lambda a: any('cast' in t.event for t in a.triggers)),
    ("Gideon, Ally of Zendikar", lambda a: a.creates_tokens),
    ("Banner of Kinship", lambda a: len(a.static_abilities) > 0),
]

passed = 0
failed = 0

for card_name, test_func in test_cases:
    card = get_card_by_name(card_name)
    if card:
        abilities = parser.parse_card(card)
        if test_func(abilities):
            print(f"✅ {card_name}")
            passed += 1
        else:
            print(f"❌ {card_name} - Test failed")
            failed += 1
    else:
        print(f"⚠️  {card_name} - Not found")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")

if failed == 0:
    print("\n🎉 All tests passed! Unified parser is working correctly.")
else:
    print(f"\n⚠️  {failed} tests failed. Parser needs adjustments.")
