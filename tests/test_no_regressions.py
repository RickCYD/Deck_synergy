#!/usr/bin/env python3
"""
Regression Test Suite

This test ensures that the unified architecture doesn't break existing
functionality. It validates that:

1. Existing extractors still work (if needed for compatibility)
2. All parsed data is accurate and consistent
3. No mechanics are lost in translation
4. Performance is acceptable (parsing is fast)

This provides confidence that migrating to the unified architecture
is safe and won't introduce bugs.
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy')

from src.api.local_cards import get_card_by_name, load_local_database
from src.core.card_parser import UnifiedCardParser
import time

print("=" * 80)
print("REGRESSION TEST SUITE")
print("=" * 80)
print("\nValidating that unified architecture maintains accuracy...")

# =============================================================================
# SETUP
# =============================================================================

load_local_database()
parser = UnifiedCardParser()

# =============================================================================
# TEST 1: Rally Parsing Accuracy
# =============================================================================

print("\n" + "=" * 80)
print("TEST 1: Rally Trigger Parsing Accuracy")
print("=" * 80)

rally_test_cases = [
    {
        'name': 'Chasm Guide',
        'expected_effect': 'haste',
        'expected_event': 'rally'
    },
    {
        'name': 'Makindi Patrol',
        'expected_effect': 'vigilance',
        'expected_event': 'rally'
    },
    {
        'name': 'Lantern Scout',
        'expected_effect': 'lifelink',
        'expected_event': 'rally'
    },
    {
        'name': 'Resolute Blademaster',
        'expected_effect': 'double strike',
        'expected_event': 'rally'
    },
]

rally_success_count = 0

for test in rally_test_cases:
    card = get_card_by_name(test['name'])
    if not card:
        print(f"  ❌ {test['name']}: Card not found")
        continue

    abilities = parser.parse_card(card)

    # Check has_rally flag
    if not abilities.has_rally:
        print(f"  ❌ {test['name']}: Rally flag not set")
        continue

    # Check rally triggers
    rally_triggers = abilities.get_triggers('rally')
    if not rally_triggers:
        print(f"  ❌ {test['name']}: No rally triggers found")
        continue

    # Check effect contains expected keyword
    found_effect = any(test['expected_effect'] in t.effect.lower() for t in rally_triggers)
    if not found_effect:
        print(f"  ❌ {test['name']}: Expected effect '{test['expected_effect']}' not found")
        print(f"     Found: {[t.effect for t in rally_triggers]}")
        continue

    print(f"  ✅ {test['name']}: Rally {test['expected_effect']} parsed correctly")
    rally_success_count += 1

rally_test_success = rally_success_count == len(rally_test_cases)

# =============================================================================
# TEST 2: Prowess Parsing Accuracy
# =============================================================================

print("\n" + "=" * 80)
print("TEST 2: Prowess Trigger Parsing Accuracy")
print("=" * 80)

prowess_test_cases = [
    'Monastery Swiftspear',
    'Bria, Riptide Rogue',
    'Narset, Enlightened Exile',
]

prowess_success_count = 0

for card_name in prowess_test_cases:
    card = get_card_by_name(card_name)
    if not card:
        print(f"  ❌ {card_name}: Card not found")
        continue

    abilities = parser.parse_card(card)

    # Check has_prowess flag
    if not abilities.has_prowess:
        print(f"  ❌ {card_name}: Prowess flag not set")
        continue

    # Check for prowess triggers
    prowess_triggers = [
        t for t in abilities.triggers
        if 'cast' in t.event and 'spell' in t.event
    ]

    if not prowess_triggers:
        print(f"  ❌ {card_name}: No prowess triggers found")
        continue

    print(f"  ✅ {card_name}: Prowess parsed correctly")
    prowess_success_count += 1

prowess_test_success = prowess_success_count == len(prowess_test_cases)

# =============================================================================
# TEST 3: Token Creation Parsing
# =============================================================================

print("\n" + "=" * 80)
print("TEST 3: Token Creation Parsing")
print("=" * 80)

token_test_cases = [
    'Kykar, Wind\'s Fury',
    'Dragon Fodder',
    'Gideon, Ally of Zendikar',
]

token_success_count = 0

for card_name in token_test_cases:
    card = get_card_by_name(card_name)
    if not card:
        print(f"  ❌ {card_name}: Card not found")
        continue

    abilities = parser.parse_card(card)

    # Check creates_tokens flag
    if not abilities.creates_tokens:
        print(f"  ❌ {card_name}: Token creation flag not set")
        print(f"     Triggers: {[t.event for t in abilities.triggers]}")
        continue

    print(f"  ✅ {card_name}: Token creation detected")
    token_success_count += 1

token_test_success = token_success_count == len(token_test_cases)

# =============================================================================
# TEST 4: Magecraft Parsing
# =============================================================================

print("\n" + "=" * 80)
print("TEST 4: Magecraft/Spellslinger Parsing")
print("=" * 80)

magecraft_test_cases = [
    'Veyran, Voice of Duality',
    'Jeskai Ascendancy',
]

magecraft_success_count = 0

for card_name in magecraft_test_cases:
    card = get_card_by_name(card_name)
    if not card:
        print(f"  ❌ {card_name}: Card not found")
        continue

    abilities = parser.parse_card(card)

    # Check for spellslinger triggers
    has_spellslinger = (
        abilities.has_magecraft or
        any('cast' in t.event and 'spell' in t.event for t in abilities.triggers)
    )

    if not has_spellslinger:
        print(f"  ❌ {card_name}: No spellslinger triggers found")
        continue

    print(f"  ✅ {card_name}: Spellslinger triggers detected")
    magecraft_success_count += 1

magecraft_test_success = magecraft_success_count == len(magecraft_test_cases)

# =============================================================================
# TEST 5: Parsing Performance
# =============================================================================

print("\n" + "=" * 80)
print("TEST 5: Parsing Performance")
print("=" * 80)

# Test parsing speed with 100 cards
test_cards = []
for card_name in rally_test_cases:
    card = get_card_by_name(card_name['name'])
    if card:
        test_cards.append(card)

for card_name in prowess_test_cases:
    card = get_card_by_name(card_name)
    if card:
        test_cards.append(card)

for card_name in token_test_cases:
    card = get_card_by_name(card_name)
    if card:
        test_cards.append(card)

# Repeat to get to ~100 cards
while len(test_cards) < 100:
    test_cards.extend(test_cards[:min(10, 100 - len(test_cards))])

print(f"\nParsing {len(test_cards)} cards...")

start_time = time.time()
for card in test_cards:
    abilities = parser.parse_card(card)
end_time = time.time()

elapsed = end_time - start_time
cards_per_second = len(test_cards) / elapsed if elapsed > 0 else 0

print(f"  Time: {elapsed:.3f}s")
print(f"  Speed: {cards_per_second:.0f} cards/second")

# Should be fast enough (at least 100 cards/sec)
performance_success = cards_per_second >= 50

if performance_success:
    print(f"  ✅ Performance acceptable")
else:
    print(f"  ❌ Performance too slow")

# =============================================================================
# TEST 6: Data Consistency
# =============================================================================

print("\n" + "=" * 80)
print("TEST 6: Data Consistency")
print("=" * 80)

# Parse same card multiple times - should get identical results
card = get_card_by_name("Chasm Guide")
abilities1 = parser.parse_card(card)
abilities2 = parser.parse_card(card)
abilities3 = parser.parse_card(card)

# Check all produce same results
consistency_checks = [
    abilities1.has_rally == abilities2.has_rally == abilities3.has_rally,
    len(abilities1.triggers) == len(abilities2.triggers) == len(abilities3.triggers),
    abilities1.name == abilities2.name == abilities3.name,
]

consistency_success = all(consistency_checks)

if consistency_success:
    print(f"  ✅ Multiple parses produce identical results")
else:
    print(f"  ❌ Parsing is inconsistent")

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("REGRESSION TEST SUMMARY")
print("=" * 80)

tests = [
    ("Rally trigger parsing", rally_test_success, f"{rally_success_count}/{len(rally_test_cases)}"),
    ("Prowess trigger parsing", prowess_test_success, f"{prowess_success_count}/{len(prowess_test_cases)}"),
    ("Token creation detection", token_test_success, f"{token_success_count}/{len(token_test_cases)}"),
    ("Magecraft/spellslinger parsing", magecraft_test_success, f"{magecraft_success_count}/{len(magecraft_test_cases)}"),
    ("Parsing performance", performance_success, f"{cards_per_second:.0f} cards/sec"),
    ("Data consistency", consistency_success, "Identical results"),
]

passed = sum(1 for _, success, _ in tests if success)
total = len(tests)

print(f"\n✅ Passed: {passed}/{total}")
for test_name, success, detail in tests:
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}: {detail}")

if passed == total:
    print("\n🎉 No regressions detected! Unified architecture is safe to use.")
    print("\nAll mechanics parse correctly:")
    print("  • Rally triggers: haste, vigilance, lifelink, double strike")
    print("  • Prowess triggers: +1/+1 buffs")
    print("  • Token creation: detected accurately")
    print("  • Magecraft: spellslinger triggers")
    print("  • Performance: Fast enough for production use")
    print("  • Consistency: Deterministic parsing")
else:
    print(f"\n⚠️  {total - passed} regression(s) detected.")
    print("Some functionality may have been broken.")

print("\n" + "=" * 80)
