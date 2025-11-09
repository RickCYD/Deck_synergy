# Troubleshooting Guide

## Simulation and Deck Effectiveness Issues

### Problem: Deck Effectiveness shows zeros or "N/A" values

**Symptoms:**
- Deck Effectiveness panel shows all zeros
- Total Damage shows 0
- Numbers don't make sense
- Simulation appears to be broken

**Root Cause:**
Missing Python dependencies (`pandas` and `numpy`) required by the simulation engine.

**Solution:**
```bash
pip install pandas numpy
```

Or install all dependencies from requirements.txt:
```bash
pip install -r requirements.txt
```

**Verification:**
Run the diagnostic script to verify simulation is working:
```bash
python test_simulation.py
```

All tests should pass with ✓ marks.

### Problem: Cannot import simulation modules

**Symptoms:**
- Error: "No module named 'pandas'"
- Error: "No module named 'numpy'"
- ImportError when loading decks

**Solution:**
Install missing dependencies:
```bash
pip install pandas numpy
```

### Problem: Simulation takes too long

**Symptoms:**
- Deck loading hangs during "Running simulation" step
- Takes more than 2 minutes to load a deck

**Solution:**
The simulation runs 100 games by default. This is normal and should complete within 30-60 seconds for most decks. If it takes longer:
- Check system resources (CPU, memory)
- Reduce number of simulation games in `src/synergy_engine/analyzer.py` (line 133)
- Disable simulation by setting `run_simulation=False`

## General Issues

### Problem: Cards not found

**Symptoms:**
- Error: "Card not found"
- Some cards from Archidekt not loading

**Solution:**
1. Check card names for typos
2. Ensure local card database is up to date:
```bash
python scripts/create_minimal_cards.py
```

### Problem: Archidekt import fails

**Symptoms:**
- Error loading deck from URL
- Empty deck after import

**Solution:**
1. Verify the Archidekt URL is correct and public
2. Check internet connection
3. Try refreshing the Archidekt page and copying the URL again

## Getting Help

If you encounter issues not covered here:
1. Run the diagnostic: `python test_simulation.py`
2. Check the console output for error messages
3. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Diagnostic test output
