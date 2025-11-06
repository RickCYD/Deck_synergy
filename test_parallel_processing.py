#!/usr/bin/env python
"""
Test if multiprocessing can speed up two-way synergy analysis
"""
import time
import multiprocessing as mp
from itertools import combinations
from src.synergy_engine.analyzer import analyze_card_pair, calculate_edge_weight

# Create test cards
test_cards = []
for i in range(60):  # Use 60 cards for faster testing
    test_cards.append({
        'name': f'Card {i}',
        'oracle_text': 'Test card with keywords like draw, sacrifice, mill, create token',
        'type_line': 'Creature — Test',
        'cmc': 3,
        'keywords': []
    })

def process_pair(pair):
    """Process a single card pair"""
    card1, card2 = pair
    synergies = analyze_card_pair(card1, card2)
    if synergies:
        total_weight = calculate_edge_weight(synergies)
        if total_weight >= 0.5:
            return (card1['name'], card2['name'], total_weight)
    return None

print(f"\n{'='*60}")
print(f"Parallel Processing Test")
print(f"{'='*60}")
print(f"\nTest deck: {len(test_cards)} cards")
total_pairs = len(test_cards) * (len(test_cards) - 1) // 2
print(f"Total pairs: {total_pairs:,}")

# Test 1: Sequential processing
print(f"\n{'='*60}")
print(f"Test 1: Sequential Processing (Current)")
print(f"{'='*60}")

pairs = list(combinations(test_cards, 2))
start = time.time()
results_seq = []
for pair in pairs[:500]:  # Test first 500 pairs
    result = process_pair(pair)
    if result:
        results_seq.append(result)
elapsed_seq = time.time() - start

print(f"Processed 500 pairs in {elapsed_seq:.2f}s")
print(f"Speed: {500/elapsed_seq:.0f} pairs/second")
print(f"Found {len(results_seq)} synergies")

# Extrapolate to full deck
full_time_seq = (elapsed_seq / 500) * total_pairs
print(f"\nExtrapolated for {len(test_cards)}-card deck: {full_time_seq:.1f}s")

# Test 2: Check available CPU cores
print(f"\n{'='*60}")
print(f"Test 2: CPU Information")
print(f"{'='*60}")

cpu_count = mp.cpu_count()
print(f"CPU cores reported: {cpu_count}")
print(f"Note: On Heroku Eco/Basic, only 1 core is truly available")

# Test 3: Multiprocessing
print(f"\n{'='*60}")
print(f"Test 3: Multiprocessing (2 workers)")
print(f"{'='*60}")

start = time.time()
with mp.Pool(processes=2) as pool:
    results_par = pool.map(process_pair, pairs[:500])
    results_par = [r for r in results_par if r is not None]
elapsed_par = time.time() - start

print(f"Processed 500 pairs in {elapsed_par:.2f}s")
print(f"Speed: {500/elapsed_par:.0f} pairs/second")
print(f"Found {len(results_par)} synergies")

# Calculate speedup
speedup = elapsed_seq / elapsed_par
print(f"\nSpeedup: {speedup:.2f}x")

# Extrapolate to full deck
full_time_par = (elapsed_par / 500) * total_pairs
print(f"Extrapolated for {len(test_cards)}-card deck: {full_time_par:.1f}s")

# Test 4: Test with 4 workers
print(f"\n{'='*60}")
print(f"Test 4: Multiprocessing (4 workers)")
print(f"{'='*60}")

start = time.time()
with mp.Pool(processes=4) as pool:
    results_par4 = pool.map(process_pair, pairs[:500])
    results_par4 = [r for r in results_par4 if r is not None]
elapsed_par4 = time.time() - start

print(f"Processed 500 pairs in {elapsed_par4:.2f}s")
print(f"Speed: {500/elapsed_par4:.0f} pairs/second")
print(f"Found {len(results_par4)} synergies")

speedup4 = elapsed_seq / elapsed_par4
print(f"\nSpeedup: {speedup4:.2f}x")

full_time_par4 = (elapsed_par4 / 500) * total_pairs
print(f"Extrapolated for {len(test_cards)}-card deck: {full_time_par4:.1f}s")

print(f"\n{'='*60}")
print(f"Summary for 112-card deck (6,216 pairs)")
print(f"{'='*60}")

# Extrapolate to 112 cards
pairs_112 = 6216
time_112_seq = (elapsed_seq / 500) * pairs_112
time_112_par2 = (elapsed_par / 500) * pairs_112
time_112_par4 = (elapsed_par4 / 500) * pairs_112

print(f"Sequential:        {time_112_seq:.1f}s  {'✗ TIMEOUT' if time_112_seq > 30 else '✓ OK'}")
print(f"Parallel (2 core): {time_112_par2:.1f}s  {'✗ TIMEOUT' if time_112_par2 > 30 else '✓ OK'}")
print(f"Parallel (4 core): {time_112_par4:.1f}s  {'✗ TIMEOUT' if time_112_par4 > 30 else '✓ OK'}")

print(f"\n{'='*60}")
print(f"Conclusion")
print(f"{'='*60}")
print(f"Multiprocessing speedup: {speedup4:.2f}x")
if time_112_par4 < 30:
    print(f"✓ Parallel processing could solve the timeout!")
else:
    print(f"⚠ Parallel processing helps but not enough for Heroku")
    print(f"  Still need: background workers or rule optimization")
