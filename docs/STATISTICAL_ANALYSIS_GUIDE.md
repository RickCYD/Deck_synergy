# Statistical Analysis Guide for Deck Simulations

## Is 100 Simulations Enough?

### The Short Answer

**It depends on your deck's consistency.** The new statistical analysis system now tells you exactly whether 100 simulations is sufficient for your specific deck.

### The Math Behind It

For a 100-card deck with 7 opening cards, there are **C(100,7) ≈ 16 billion** possible opening hands. However, thanks to the **Central Limit Theorem**, we don't need to test every combination. What matters is the **variance** in your results.

#### Key Statistical Concepts

1. **Coefficient of Variation (CV)** = Standard Deviation / Mean
   - CV < 0.10: Low variance, very consistent deck → 100 samples is sufficient
   - CV 0.10-0.20: Moderate variance → 200-300 samples recommended
   - CV 0.20-0.30: Moderate-high variance → 300-500 samples recommended
   - CV > 0.30: High variance → 500-1000+ samples, or deck has consistency issues

2. **Confidence Intervals (95% CI)**
   - Shows the range where the true mean likely falls
   - Narrower CI = more precise estimate
   - Example: "Total Damage: 45.2 ± 3.1" means true damage is likely between 42.1 and 48.3

3. **Margin of Error**
   - Half the width of the confidence interval
   - Expressed as absolute value and percentage
   - Lower percentage = more reliable results

## What's New

### Automatic Statistical Analysis

Every simulation now automatically calculates:

- **Mean** (average across all games)
- **Median** (middle value)
- **Standard Deviation** (how spread out the results are)
- **Min/Max** (range of outcomes)
- **95% Confidence Interval** (where the true mean likely is)
- **Coefficient of Variation** (relative consistency)
- **Percentiles** (10th, 25th, 50th, 75th, 90th)
- **Recommended Sample Size** (based on observed variance)

### Sample Output

```
================================================================================
STATISTICAL VALIDITY REPORT
================================================================================

Sample Size: 100 games
Overall Status: GOOD
Average CV: 0.156
Recommended N: 300

✓ Current sample size (100) provides reasonable estimates. Consider 300 for higher precision.

--------------------------------------------------------------------------------
PER-METRIC ANALYSIS
--------------------------------------------------------------------------------

📊 Total Damage (Combat + Drain)
   Mean: 45.23 ± 3.12 (6.9%)
   95% CI: [42.11, 48.35]
   Median: 44.80 | Std Dev: 15.63
   Range: [12.50, 78.20]
   CV: 0.345 | Recommended N: 450
   ⚠ Moderate-high variance (CV=0.35). Recommend 450 samples for reliable results.

📊 Peak Board Power
   Mean: 32.45 ± 1.87 (5.8%)
   95% CI: [30.58, 34.32]
   Median: 32.10 | Std Dev: 9.35
   Range: [18.00, 52.00]
   CV: 0.288 | Recommended N: 320
   ⚠ Moderate-high variance (CV=0.29). Recommend 320 samples.

📊 Cards Played
   Mean: 23.67 ± 0.89 (3.8%)
   95% CI: [22.78, 24.56]
   Median: 24.00 | Std Dev: 4.46
   Range: [14.00, 35.00]
   CV: 0.188 | Recommended N: 140
   ✓ Moderate variance (CV=0.19). Recommend 140 samples for 5% margin of error.
```

## How to Use

### Basic Usage (Automatic)

The statistical analysis runs automatically when you simulate a deck:

```python
from src.simulation.deck_simulator import simulate_deck_performance

results = simulate_deck_performance(
    deck_df=your_deck,
    commander_name="Your Commander",
    num_games=100,
    max_turns=10
)

# Access statistical report
stats = results['statistical_report']
print(stats['formatted_report'])
```

### Advanced: Test Different Sample Sizes

Use the new `test_sample_sizes.py` script to compare different sample sizes:

```bash
cd Simulation
python test_sample_sizes.py path/to/your/deck.txt --sample-sizes 50 100 300 500
```

This will:
1. Run simulations with 50, 100, 300, and 500 games
2. Show how confidence intervals narrow with more samples
3. Calculate the optimal sample size for your deck
4. Display statistical validity for each sample size

### Test Reproducibility

Run multiple independent batches to verify consistency:

```bash
python test_sample_sizes.py path/to/your/deck.txt --batches 5
```

This runs 5 independent batches of 100 games and shows how consistent the results are.

## Interpreting Results

### Overall Status Meanings

- **EXCELLENT**: Low variance (CV < 0.10), current sample size is sufficient
- **GOOD**: Moderate variance (CV 0.10-0.20), current size gives reasonable estimates
- **FAIR**: Moderate-high variance (CV 0.20-0.30), consider more samples
- **NEEDS IMPROVEMENT**: High variance (CV > 0.30), need more samples or deck has consistency issues

### What to Do Based on Results

#### If CV < 0.10 (Excellent)
✓ Your deck is very consistent
✓ 100 simulations is sufficient
✓ Results are reliable

**Example**: Consistent voltron/equipment decks that reliably execute their strategy

#### If CV 0.10-0.20 (Good)
✓ Deck is reasonably consistent
⚠ Consider 200-300 samples for higher precision
✓ 100 samples gives ballpark estimates

**Example**: Most commander decks with focused strategies

#### If CV 0.20-0.30 (Fair)
⚠ Moderate variance in performance
⚠ Recommend 300-500 samples
⚠ 100 samples may miss important patterns

**Example**: Combo decks that sometimes "go off" and sometimes don't

#### If CV > 0.30 (High Variance)
❌ High variance in results
❌ Need 500-1000+ samples for reliable conclusions
❌ Consider deck consistency issues

**Possible causes**:
- Deck relies heavily on specific combos
- Mana base is inconsistent
- Critical cards are few and not redundant
- Heavy reliance on drawing specific answers

### Example Interpretations

#### Scenario 1: Consistent Aggro Deck
```
Overall Status: EXCELLENT
Avg CV: 0.08
Recommended N: 100

Total Damage CV: 0.07
Peak Power CV: 0.09
```

**Interpretation**: This deck is very consistent. It reliably deploys threats and deals similar damage across games. 100 simulations is sufficient.

#### Scenario 2: Combo Deck
```
Overall Status: FAIR
Avg CV: 0.28
Recommended N: 380

Total Damage CV: 0.45
Peak Power CV: 0.12
```

**Interpretation**: High damage variance but consistent power deployment suggests the deck sometimes assembles combos (high damage) and sometimes doesn't (low damage). Need 380+ samples to accurately measure combo success rate.

#### Scenario 3: Goodstuff/Midrange
```
Overall Status: GOOD
Avg CV: 0.15
Recommended N: 220

Total Damage CV: 0.18
Cards Drawn CV: 0.12
```

**Interpretation**: Moderate consistency typical of goodstuff decks. 100 games gives reasonable estimates, but 220+ would provide more precision.

## Technical Details

### Metrics Analyzed

The system tracks and analyzes these key metrics:

1. **Total Damage (Combat + Drain)** - Primary win condition metric
2. **Total Mana Generated** - Resource availability
3. **Cards Played** - Deck efficiency
4. **Peak Board Power** - Maximum board state
5. **Drain Damage** - Aristocrats/drain effects
6. **Tokens Created** - Token strategy effectiveness
7. **Cards Drawn** - Card advantage

### Statistical Methods

- **Confidence Intervals**: For n≥30, uses Z-score (1.96 for 95% CI). For n<30, uses conservative t-distribution approximation.
- **Sample Size Calculation**: n = (Z × CV / desired_error)²
- **Percentiles**: Calculated using linear interpolation
- **Outlier Detection**: Min/max show extreme cases

### Limitations

1. **Goldfish Mode**: Simulations assume no opponent interaction, so variance may be lower than real games
2. **First 10 Turns**: Only analyzes early game, which may miss late-game variance
3. **Perfect Mulligan**: Aggressive mulligan strategy reduces opening hand variance
4. **Deterministic Decisions**: Greedy casting algorithm is consistent, real games have more decision variance

## Best Practices

### For Accurate Results

1. **Start with 100 games** to get baseline CV
2. **Check the recommended N** in the statistical report
3. **Run multiple batches** (3-5) to verify consistency
4. **If CV > 0.30**, run 500+ games or investigate deck consistency
5. **Compare before/after** when testing deck changes

### For Comparing Decks

When comparing two decks:

1. Use the **same sample size** for both (use max recommended N)
2. Check if **confidence intervals overlap** - if they do, decks may be similar
3. Look at **CV values** - lower CV deck is more consistent
4. Run **multiple batches** to ensure differences aren't due to random variance

### For Deck Building

High CV in specific metrics indicates areas for improvement:

- **High Total Damage CV** → Inconsistent win conditions, need more redundancy
- **High Mana CV** → Mana base issues, need more ramp/fixing
- **High Cards Played CV** → Card draw inconsistency, need more draw sources
- **High Token CV** → Token strategy unreliable, need more token generators

## References

- Central Limit Theorem: Why we can use sample averages
- Coefficient of Variation: Measure of relative variability
- Confidence Intervals: Estimating population parameters
- Sample Size Determination: Statistical power analysis

## Changelog

### 2025-11-10: Initial Statistical Analysis System

- Added automatic CV, confidence interval, and percentile calculations
- Implemented adaptive sample size recommendations
- Created `statistical_analysis.py` module
- Updated `run_simulation.py` to track per-game metrics
- Added `test_sample_sizes.py` for comprehensive testing
- Integrated statistical reporting into `deck_simulator.py`
