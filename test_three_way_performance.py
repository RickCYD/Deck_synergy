#!/usr/bin/env python
"""
Test script to measure three-way synergy performance improvements
"""
import time
from src.synergy_engine.three_way_synergies import THREE_WAY_SYNERGY_RULES
from src.synergy_engine.analyzer import analyze_three_way_synergies

# Create test cards with various patterns
test_cards = []

# Equipment + matters
test_cards.extend([
    {
        'name': 'Sword of Fire',
        'oracle_text': 'Equipped creature gets +2/+2',
        'type_line': 'Artifact — Equipment',
        'cmc': 3,
        'keywords': []
    },
    {
        'name': 'Bruenor',
        'oracle_text': 'Each equipped creature you control gets +2/+0',
        'type_line': 'Legendary Creature — Dwarf Warrior',
        'cmc': 3,
        'keywords': []
    },
    # Token aristocrats
    {
        'name': 'Tendershoot Dryad',
        'oracle_text': 'At the beginning of each upkeep, create a 1/1 green Saproling creature token',
        'type_line': 'Creature — Dryad',
        'cmc': 5,
        'keywords': []
    },
    {
        'name': 'Ashnod\'s Altar',
        'oracle_text': 'Sacrifice a creature: Add two colorless mana',
        'type_line': 'Artifact',
        'cmc': 3,
        'keywords': []
    },
    {
        'name': 'Blood Artist',
        'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life',
        'type_line': 'Creature — Vampire',
        'cmc': 2,
        'keywords': []
    },
    # ETB flicker
    {
        'name': 'Mulldrifter',
        'oracle_text': 'When Mulldrifter enters the battlefield, draw two cards',
        'type_line': 'Creature — Elemental',
        'cmc': 5,
        'keywords': ['evoke']
    },
    {
        'name': 'Ephemerate',
        'oracle_text': 'Exile target creature you control, then return it to the battlefield',
        'type_line': 'Instant',
        'cmc': 1,
        'keywords': []
    },
    {
        'name': 'Panharmonicon',
        'oracle_text': 'If an artifact or creature entering the battlefield causes a triggered ability to trigger, that ability triggers an additional time',
        'type_line': 'Artifact',
        'cmc': 4,
        'keywords': []
    },
    # Mill reanimator
    {
        'name': 'Entomb',
        'oracle_text': 'Search your library for a card and put that card into your graveyard',
        'type_line': 'Instant',
        'cmc': 1,
        'keywords': []
    },
    {
        'name': 'Animate Dead',
        'oracle_text': 'Enchant creature card in a graveyard. When Animate Dead enters the battlefield, return enchanted creature card to the battlefield',
        'type_line': 'Enchantment — Aura',
        'cmc': 2,
        'keywords': []
    },
    {
        'name': 'Elesh Norn',
        'oracle_text': 'Vigilance. Creatures you control get +2/+2',
        'type_line': 'Legendary Creature — Phyrexian Praetor',
        'cmc': 7,
        'keywords': []
    }
])

# Add generic creatures
for i in range(20):
    test_cards.append({
        'name': f'Creature {i}',
        'oracle_text': 'A test creature',
        'type_line': 'Creature — Test',
        'cmc': 3,
        'keywords': []
    })

print(f"\n{'='*60}")
print(f"Three-Way Synergy Performance Test")
print(f"{'='*60}")
print(f"\nTest deck size: {len(test_cards)} cards")
print(f"Expected triplets: {len(test_cards) * (len(test_cards) - 1) * (len(test_cards) - 2) // 6}")

# Test individual function performance
print(f"\n{'='*60}")
print(f"Testing individual detection function speed...")
print(f"{'='*60}")

card1, card2, card3 = test_cards[0], test_cards[1], test_cards[2]
iterations = 10000

start = time.time()
for _ in range(iterations):
    for func in THREE_WAY_SYNERGY_RULES:
        result = func(card1, card2, card3)
elapsed = time.time() - start

print(f"\n✓ Tested {iterations} iterations × {len(THREE_WAY_SYNERGY_RULES)} functions")
print(f"  Total time: {elapsed:.3f}s")
print(f"  Time per triplet check: {elapsed/iterations*1000:.3f}ms")
print(f"  Triplets per second: {iterations/elapsed:.0f}")

# Estimate full deck analysis time
total_triplets = len(test_cards) * (len(test_cards) - 1) * (len(test_cards) - 2) // 6
estimated_time = (elapsed / iterations) * total_triplets

print(f"\n{'='*60}")
print(f"Extrapolated Performance for {len(test_cards)}-card deck")
print(f"{'='*60}")
print(f"  Total triplets: {total_triplets:,}")
print(f"  Estimated time: {estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")

# Now test with actual analysis function
print(f"\n{'='*60}")
print(f"Running actual three-way analysis...")
print(f"{'='*60}")

start = time.time()
result = analyze_three_way_synergies(test_cards[:15], min_synergy_threshold=0.5)  # Use smaller subset
elapsed = time.time() - start

actual_triplets = 15 * 14 * 13 // 6
print(f"\n✓ Analyzed {actual_triplets:,} triplets in {elapsed:.2f}s")
print(f"  Found {len(result)} three-way synergies")
print(f"  Speed: {actual_triplets/elapsed:.0f} triplets/second")

# Extrapolate to full deck
full_deck_triplets = len(test_cards) * (len(test_cards) - 1) * (len(test_cards) - 2) // 6
extrapolated = (elapsed / actual_triplets) * full_deck_triplets

print(f"\n{'='*60}")
print(f"Extrapolated for {len(test_cards)}-card deck:")
print(f"{'='*60}")
print(f"  Estimated time: {extrapolated:.1f}s ({extrapolated/60:.1f} minutes)")

print(f"\n{'='*60}")
print(f"Conclusion")
print(f"{'='*60}")
if extrapolated < 30:
    print(f"✓ Analysis should complete within Heroku's 30s timeout")
else:
    print(f"⚠ Analysis may timeout on Heroku (30s limit)")
    print(f"  Needs: {extrapolated:.0f}s")
    print(f"  Over by: {extrapolated - 30:.0f}s")
