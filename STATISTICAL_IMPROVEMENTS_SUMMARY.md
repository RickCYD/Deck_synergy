# Statistical Analysis Improvements - Summary

## Overview

This update addresses the critical question: **"Are 100 simulations enough?"**

The answer is now data-driven: **It depends on your deck's consistency, and the system now tells you exactly what you need.**

## Problem Statement

Previously, the simulation system:
- Only reported **averages** across games
- No **variance** or **confidence intervals**
- No way to determine if 100 games was **statistically sufficient**
- Impossible to know **margin of error** in results
- No **reproducibility** validation

With a 100-card deck and 7 opening cards, there are ~16 billion possible hands. Running 100 simulations samples only 0.00000062% of possibilities. But the Central Limit Theorem tells us we don't need to test every combination - **what matters is variance**.

## Solution Implemented

### 1. New Statistical Analysis Module (`Simulation/statistical_analysis.py`)

Provides comprehensive statistical tools:

- **Confidence Intervals** (95% CI) - Shows range where true mean likely falls
- **Coefficient of Variation** (CV = σ/μ) - Measures relative consistency
- **Percentiles** (10th, 25th, 50th, 75th, 90th) - Distribution analysis
- **Adaptive Sample Size Recommendations** - Tells you if you need more samples
- **Margin of Error** - Both absolute and percentage

### 2. Enhanced Simulation Runner (`Simulation/run_simulation.py`)

Now tracks per-game raw data for 7 key metrics:
- Total Damage (Combat + Drain)
- Total Mana Generated
- Cards Played
- Peak Board Power
- Drain Damage
- Tokens Created
- Cards Drawn

### 3. Automatic Statistical Reporting

Every simulation now automatically:
1. Calculates CV for all metrics
2. Determines if sample size is sufficient
3. Recommends optimal sample size based on observed variance
4. Provides confidence intervals for precision
5. Shows full distribution (min/25th/median/75th/max)

### 4. Testing Tools

**`Simulation/test_sample_sizes.py`** - Compare different sample sizes:
```bash
python test_sample_sizes.py deck.txt --sample-sizes 50 100 300 500
```

Shows how confidence intervals narrow with larger samples and recommends optimal N.

**Multiple Batch Testing** - Validate reproducibility:
```bash
python test_sample_sizes.py deck.txt --batches 5
```

Runs 5 independent batches and shows consistency.

### 5. Integration with Main Simulator

The main `deck_simulator.py` now:
- Automatically runs statistical analysis
- Prints formatted statistical report
- Includes stats in returned results dictionary
- No API changes (backward compatible)

## Interpretation Guide

### Overall Status Levels

| Status | CV Range | Meaning | Action |
|--------|----------|---------|--------|
| **EXCELLENT** | < 0.10 | Very consistent deck | 100 samples sufficient |
| **GOOD** | 0.10-0.20 | Reasonably consistent | 100 okay, 200-300 better |
| **FAIR** | 0.20-0.30 | Moderate variance | Need 300-500 samples |
| **NEEDS IMPROVEMENT** | > 0.30 | High variance | Need 500-1000+ or fix deck |

### CV by Deck Archetype

**Consistent Decks (CV 0.05-0.15):**
- Focused aggro/voltron strategies
- Strong mana curves
- Redundant effects
- → **100 simulations sufficient**

**Moderate Variance (CV 0.15-0.25):**
- Goodstuff/midrange decks
- Multiple win conditions
- Situational cards
- → **200-300 simulations recommended**

**High Variance (CV > 0.30):**
- Combo-dependent strategies
- Inconsistent mana bases
- Few tutors, many unique effects
- → **500+ simulations or improve deck consistency**

## Example Output

```
================================================================================
STATISTICAL VALIDITY REPORT
================================================================================

Sample Size: 100 games
Overall Status: GOOD
Average CV: 0.156
Recommended N: 300

✓ Current sample size (100) provides reasonable estimates.
  Consider 300 for higher precision.

--------------------------------------------------------------------------------
PER-METRIC ANALYSIS
--------------------------------------------------------------------------------

📊 Total Damage (Combat + Drain)
   Mean: 45.23 ± 3.12 (6.9%)
   95% CI: [42.11, 48.35]
   Median: 44.80 | Std Dev: 15.63
   Range: [12.50, 78.20]
   CV: 0.345 | Recommended N: 450
   ⚠ Moderate-high variance. Recommend 450 samples for reliable results.

📊 Peak Board Power
   Mean: 32.45 ± 1.87 (5.8%)
   95% CI: [30.58, 34.32]
   Median: 32.10 | Std Dev: 9.35
   Range: [18.00, 52.00]
   CV: 0.288 | Recommended N: 320
   ⚠ Moderate-high variance. Recommend 320 samples.
```

## Key Improvements Summary

### Before
- ❌ Only averages reported
- ❌ No variance analysis
- ❌ Unknown reliability of results
- ❌ No guidance on sample size
- ❌ No reproducibility validation

### After
- ✅ Mean, median, std dev, min, max, percentiles
- ✅ Coefficient of variation for all metrics
- ✅ 95% confidence intervals with margin of error
- ✅ Adaptive sample size recommendations
- ✅ Multiple batch testing for reproducibility
- ✅ Statistical validity assessment

## Files Changed/Added

### New Files
1. **`Simulation/statistical_analysis.py`** - Core statistical functions
2. **`Simulation/test_sample_sizes.py`** - Testing and comparison tool
3. **`docs/STATISTICAL_ANALYSIS_GUIDE.md`** - Comprehensive user guide
4. **`STATISTICAL_IMPROVEMENTS_SUMMARY.md`** - This file

### Modified Files
1. **`Simulation/run_simulation.py`**
   - Added per-game metric tracking
   - Integrated statistical analysis
   - Returns statistical report as 5th value

2. **`src/simulation/deck_simulator.py`**
   - Updated to handle 5-value return
   - Prints statistical report automatically
   - Includes stats in results dictionary

## Usage Examples

### Basic (Automatic)
```python
from src.simulation.deck_simulator import simulate_deck_performance

results = simulate_deck_performance(deck_df, "Commander", num_games=100)

# Statistical report printed automatically
# Also available in results:
stats = results['statistical_report']
```

### Advanced Testing
```bash
# Compare sample sizes
cd Simulation
python test_sample_sizes.py ../deck.txt --sample-sizes 100 300 500

# Test reproducibility
python test_sample_sizes.py ../deck.txt --batches 5

# Both tests
python test_sample_sizes.py ../deck.txt --sample-sizes 100 300 --batches 3
```

## Impact

### For Users
- **Know if results are reliable** - CV and confidence intervals show precision
- **Optimize simulation time** - Don't run 1000 games if 100 is enough
- **Identify deck issues** - High CV reveals consistency problems
- **Compare decks fairly** - Understand when differences are significant

### For Developers
- **Reproducible results** - Validate simulation changes don't add variance
- **Algorithm validation** - Ensure new features work correctly across samples
- **Performance optimization** - Know minimum samples needed for testing

## Statistical Methods

### Confidence Intervals
- For n ≥ 30: Z-score (1.96 for 95%)
- For n < 30: Conservative t-distribution approximation
- Formula: CI = mean ± (Z × σ/√n)

### Sample Size Calculation
- Formula: n = (Z × CV / desired_error)²
- Default: 5% margin of error
- Accounts for observed variance

### Coefficient of Variation
- CV = σ / μ (standard deviation / mean)
- Dimensionless measure of relative variability
- Allows comparison across different metrics

## Limitations and Caveats

1. **Goldfish Mode**: No opponent interaction means variance may be lower than real games
2. **First 10 Turns Only**: Late-game variance not captured
3. **Deterministic Decisions**: Real games have more decision variance
4. **Perfect Information**: Algorithm knows full deck, humans don't

Despite these limitations, the statistical analysis **accurately measures simulation consistency** and helps determine **appropriate sample sizes for simulation purposes**.

## Future Enhancements

Potential additions:
- [ ] Per-turn variance analysis
- [ ] Mulligan impact on variance
- [ ] Opening hand quality distribution
- [ ] Turn-by-turn convergence plots
- [ ] Comparison mode (deck A vs deck B with statistical significance)
- [ ] Archetype-specific metrics
- [ ] Integration with web dashboard for visualization

## Conclusion

**Is 100 simulations enough?**

With this update, you can finally answer that question **with data**:

- ✅ CV < 0.10: **Yes, 100 is sufficient**
- ⚠️ CV 0.10-0.20: **100 is okay, 200-300 is better**
- ⚠️ CV 0.20-0.30: **Need 300-500 for reliability**
- ❌ CV > 0.30: **Need 500-1000+ or fix deck consistency**

The system now **tells you exactly what you need** for your specific deck.

---

**Date**: 2025-11-10
**Author**: Statistical Analysis System Improvements
**Version**: 1.0
