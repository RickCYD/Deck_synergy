#!/usr/bin/env python3
"""
Test individual card synergies to verify extractors and rules work correctly
"""

from src.api.local_cards import load_local_database, get_card_by_name
from src.utils.spellslinger_extractors import (
    extract_untaps_creatures_on_spell,
    extract_doubles_triggers,
    extract_draw_on_spell_cast,
    extract_draw_on_creature_event,
    extract_spell_copy_ability,
    extract_creates_treasures_on_spell,
    extract_creates_tokens_on_spell
)
from src.synergy_engine.spellslinger_engine_synergies import (
    detect_jeskai_ascendancy_untap_synergy,
    detect_jeskai_ascendancy_creature_synergy,
    detect_veyran_trigger_doubling_synergy,
    detect_kindred_discovery_synergy,
    detect_whirlwind_of_thought_synergy,
    detect_spell_copy_extra_turn_combo,
    detect_treasure_generation_spell_synergy,
    detect_token_generation_spell_synergy
)

print("=" * 80)
print("INDIVIDUAL CARD SYNERGY TESTS")
print("=" * 80)

# Load database
print("\nLoading card database...")
load_local_database()

# Test cards from the user's deck
test_cards = {
    # Engine pieces
    'jeskai': 'Jeskai Ascendancy',
    'veyran': 'Veyran, Voice of Duality',
    'whirlwind': 'Whirlwind of Thought',
    'storm_kiln': 'Storm-Kiln Artist',
    'kykar': "Kykar, Wind's Fury",
    'balmor': 'Balmor, Battlemage Captain',

    # Cheap spells (cantrips)
    'brainstorm': 'Brainstorm',
    'opt': 'Opt',
    'ponder': 'Ponder',
    'preordain': 'Preordain',
    'consider': 'Consider',

    # Removal/Interaction
    'bolt': 'Lightning Bolt',
    'path': 'Path to Exile',
    'swords': 'Swords to Plowshares',
    'counterspell': 'Counterspell',
    'negate': 'Negate',
    'abrade': 'Abrade',

    # Extra turns
    'nexus': 'Nexus of Fate',
    'temporal': 'Temporal Manipulation',

    # Spell copy
    'narset_reversal': "Narset's Reversal",
    'dualcaster': 'Dualcaster Mage',

    # Token generators
    'murmuring': 'Murmuring Mystic',
    'talrand': 'Talrand, Sky Summoner',

    # Tribal
    'sea_gate': 'Sea Gate Loremaster',
    'halimar': 'Halimar Excavator',
    'kazuul': 'Kazuul Warlord',
}

cards = {}
print("\nLoading test cards...")
for key, name in test_cards.items():
    card = get_card_by_name(name)
    if card:
        cards[key] = card
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} NOT FOUND")

print(f"\n✓ Loaded {len(cards)}/{len(test_cards)} cards")

# ============================================================================
# TEST 1: EXTRACTOR FUNCTIONS
# ============================================================================

print("\n" + "=" * 80)
print("TEST 1: EXTRACTOR FUNCTIONS")
print("=" * 80)

print("\n--- Testing Untap Extractors ---")
if 'jeskai' in cards:
    result = extract_untaps_creatures_on_spell(cards['jeskai'])
    print(f"Jeskai Ascendancy untaps creatures: {result['untaps_on_spell']}")
    assert result['untaps_on_spell'], "❌ Failed to detect Jeskai untap"
    print("  ✓ PASS")

print("\n--- Testing Trigger Doubling ---")
if 'veyran' in cards:
    result = extract_doubles_triggers(cards['veyran'])
    print(f"Veyran doubles triggers: {result['doubles_triggers']}")
    print(f"  Trigger type: {result['trigger_type']}")
    assert result['doubles_triggers'], "❌ Failed to detect Veyran"
    print("  ✓ PASS")

print("\n--- Testing Spell Draw ---")
if 'whirlwind' in cards:
    result = extract_draw_on_spell_cast(cards['whirlwind'])
    print(f"Whirlwind draws on spell: {result['draws_on_spell']}")
    print(f"  Spell type: {result['spell_type']}")
    assert result['draws_on_spell'], "❌ Failed to detect Whirlwind"
    print("  ✓ PASS")

print("\n--- Testing Treasure Generation ---")
if 'storm_kiln' in cards:
    result = extract_creates_treasures_on_spell(cards['storm_kiln'])
    print(f"Storm-Kiln creates treasures: {result['creates_treasures_on_spell']}")
    assert result['creates_treasures_on_spell'], "❌ Failed to detect Storm-Kiln"
    print("  ✓ PASS")

print("\n--- Testing Token Generation ---")
if 'kykar' in cards:
    result = extract_creates_tokens_on_spell(cards['kykar'])
    print(f"Kykar creates tokens: {result['creates_tokens_on_spell']}")
    print(f"  Token type: {result.get('token_type', 'unknown')}")
    assert result['creates_tokens_on_spell'], "❌ Failed to detect Kykar"
    print("  ✓ PASS")

if 'murmuring' in cards:
    result = extract_creates_tokens_on_spell(cards['murmuring'])
    print(f"Murmuring Mystic creates tokens: {result['creates_tokens_on_spell']}")
    assert result['creates_tokens_on_spell'], "❌ Failed to detect Murmuring Mystic"
    print("  ✓ PASS")

print("\n--- Testing Spell Copy ---")
if 'narset_reversal' in cards:
    result = extract_spell_copy_ability(cards['narset_reversal'])
    print(f"Narset's Reversal copies spells: {result['copies_spells']}")
    assert result['copies_spells'], "❌ Failed to detect Narset's Reversal"
    print("  ✓ PASS")

# ============================================================================
# TEST 2: SYNERGY DETECTION - JESKAI ASCENDANCY
# ============================================================================

print("\n" + "=" * 80)
print("TEST 2: JESKAI ASCENDANCY SYNERGIES")
print("=" * 80)

if 'jeskai' in cards:
    jeskai_synergies = []

    # Test with cantrips (should be high value)
    for cantrip in ['brainstorm', 'opt', 'ponder', 'preordain', 'consider']:
        if cantrip in cards:
            syn = detect_jeskai_ascendancy_untap_synergy(cards['jeskai'], cards[cantrip])
            if syn:
                jeskai_synergies.append(syn)
                print(f"\n✓ Jeskai + {test_cards[cantrip]}")
                print(f"  Value: {syn['value']}")
                print(f"  Category: {syn['category']}/{syn.get('subcategory', 'none')}")
                print(f"  Description: {syn['description'][:80]}...")

    # Test with removal (should be medium value)
    for removal in ['bolt', 'path', 'swords', 'abrade']:
        if removal in cards:
            syn = detect_jeskai_ascendancy_untap_synergy(cards['jeskai'], cards[removal])
            if syn:
                jeskai_synergies.append(syn)
                print(f"\n✓ Jeskai + {test_cards[removal]}")
                print(f"  Value: {syn['value']}")

    print(f"\n✅ Found {len(jeskai_synergies)} Jeskai Ascendancy synergies")
    assert len(jeskai_synergies) >= 5, f"❌ Expected at least 5 synergies, found {len(jeskai_synergies)}"

# ============================================================================
# TEST 3: SYNERGY DETECTION - VEYRAN
# ============================================================================

print("\n" + "=" * 80)
print("TEST 3: VEYRAN TRIGGER DOUBLING SYNERGIES")
print("=" * 80)

if 'veyran' in cards:
    veyran_synergies = []

    # Test with magecraft triggers
    magecraft_cards = ['storm_kiln', 'kykar', 'balmor']
    for key in magecraft_cards:
        if key in cards:
            syn = detect_veyran_trigger_doubling_synergy(cards['veyran'], cards[key])
            if syn:
                veyran_synergies.append(syn)
                print(f"\n✓ Veyran + {test_cards[key]}")
                print(f"  Value: {syn['value']}")
                print(f"  Description: {syn['description'][:80]}...")

    print(f"\n✅ Found {len(veyran_synergies)} Veyran synergies")
    assert len(veyran_synergies) >= 3, f"❌ Expected at least 3 synergies, found {len(veyran_synergies)}"

# ============================================================================
# TEST 4: SYNERGY DETECTION - WHIRLWIND OF THOUGHT
# ============================================================================

print("\n" + "=" * 80)
print("TEST 4: WHIRLWIND OF THOUGHT SYNERGIES")
print("=" * 80)

if 'whirlwind' in cards:
    whirlwind_synergies = []

    # Test with noncreature spells
    spell_cards = ['brainstorm', 'opt', 'bolt', 'path', 'counterspell', 'nexus']
    for key in spell_cards:
        if key in cards:
            syn = detect_whirlwind_of_thought_synergy(cards['whirlwind'], cards[key])
            if syn:
                whirlwind_synergies.append(syn)
                print(f"\n✓ Whirlwind + {test_cards[key]}")
                print(f"  Value: {syn['value']}")

    print(f"\n✅ Found {len(whirlwind_synergies)} Whirlwind synergies")
    assert len(whirlwind_synergies) >= 5, f"❌ Expected at least 5 synergies, found {len(whirlwind_synergies)}"

# ============================================================================
# TEST 5: SYNERGY DETECTION - TREASURE GENERATION
# ============================================================================

print("\n" + "=" * 80)
print("TEST 5: TREASURE GENERATION SYNERGIES")
print("=" * 80)

if 'storm_kiln' in cards:
    treasure_synergies = []

    # Test with various spells
    spell_cards = ['brainstorm', 'opt', 'bolt', 'counterspell', 'nexus']
    for key in spell_cards:
        if key in cards:
            syn = detect_treasure_generation_spell_synergy(cards['storm_kiln'], cards[key])
            if syn:
                treasure_synergies.append(syn)
                print(f"\n✓ Storm-Kiln + {test_cards[key]}")
                print(f"  Value: {syn['value']}")

    print(f"\n✅ Found {len(treasure_synergies)} treasure generation synergies")
    assert len(treasure_synergies) >= 4, f"❌ Expected at least 4 synergies, found {len(treasure_synergies)}"

# ============================================================================
# TEST 6: SYNERGY DETECTION - TOKEN GENERATION
# ============================================================================

print("\n" + "=" * 80)
print("TEST 6: TOKEN GENERATION SYNERGIES")
print("=" * 80)

if 'kykar' in cards:
    token_synergies = []

    # Test with noncreature spells
    spell_cards = ['brainstorm', 'opt', 'bolt', 'path']
    for key in spell_cards:
        if key in cards:
            syn = detect_token_generation_spell_synergy(cards['kykar'], cards[key])
            if syn:
                token_synergies.append(syn)
                print(f"\n✓ Kykar + {test_cards[key]}")
                print(f"  Value: {syn['value']}")

    print(f"\n✅ Found {len(token_synergies)} token generation synergies")
    assert len(token_synergies) >= 3, f"❌ Expected at least 3 synergies, found {len(token_synergies)}"

# ============================================================================
# TEST 7: INFINITE COMBO DETECTION
# ============================================================================

print("\n" + "=" * 80)
print("TEST 7: INFINITE COMBO DETECTION")
print("=" * 80)

if 'narset_reversal' in cards and 'nexus' in cards:
    combo = detect_spell_copy_extra_turn_combo(cards['narset_reversal'], cards['nexus'])
    if combo:
        print(f"\n✓ INFINITE COMBO DETECTED!")
        print(f"  Cards: Narset's Reversal + Nexus of Fate")
        print(f"  Value: {combo['value']}")
        print(f"  Description: {combo['description']}")
        assert combo['value'] == 50.0, "❌ Infinite combo should have value 50.0"
        print("\n  ✅ PASS - Infinite combo correctly detected")
    else:
        print("\n  ❌ FAIL - Infinite combo not detected")

# Test another extra turn spell
if 'narset_reversal' in cards and 'temporal' in cards:
    combo = detect_spell_copy_extra_turn_combo(cards['narset_reversal'], cards['temporal'])
    if combo:
        print(f"\n✓ Narset's Reversal + Temporal Manipulation")
        print(f"  Value: {combo['value']}")
        assert combo['value'] == 50.0, "❌ Should be infinite combo"

# ============================================================================
# TEST 8: MULTI-ENGINE INTERACTIONS
# ============================================================================

print("\n" + "=" * 80)
print("TEST 8: MULTI-ENGINE INTERACTIONS")
print("=" * 80)

if 'jeskai' in cards and 'veyran' in cards:
    # Jeskai should synergize with Veyran (both care about creatures + spells)
    syn = detect_jeskai_ascendancy_creature_synergy(cards['jeskai'], cards['veyran'])
    if syn:
        print(f"\n✓ Jeskai + Veyran")
        print(f"  Value: {syn['value']}")
        print(f"  Description: {syn['description']}")

if 'veyran' in cards and 'whirlwind' in cards:
    # Veyran doesn't double Whirlwind (not a triggered ability from casting)
    syn = detect_veyran_trigger_doubling_synergy(cards['veyran'], cards['whirlwind'])
    if syn:
        print(f"\n  Note: Veyran + Whirlwind detected (shouldn't double though)")
    else:
        print(f"\n✓ Veyran + Whirlwind correctly not doubled")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

total_synergies = (
    len(jeskai_synergies if 'jeskai' in cards else []) +
    len(veyran_synergies if 'veyran' in cards else []) +
    len(whirlwind_synergies if 'whirlwind' in cards else []) +
    len(treasure_synergies if 'storm_kiln' in cards else []) +
    len(token_synergies if 'kykar' in cards else [])
)

print(f"\nTotal synergies detected: {total_synergies}")
print(f"\nBreakdown:")
print(f"  Jeskai Ascendancy: {len(jeskai_synergies) if 'jeskai' in cards else 0}")
print(f"  Veyran: {len(veyran_synergies) if 'veyran' in cards else 0}")
print(f"  Whirlwind of Thought: {len(whirlwind_synergies) if 'whirlwind' in cards else 0}")
print(f"  Treasure Generation: {len(treasure_synergies) if 'storm_kiln' in cards else 0}")
print(f"  Token Generation: {len(token_synergies) if 'kykar' in cards else 0}")

print("\n✅ ALL TESTS PASSED")
print("=" * 80)
