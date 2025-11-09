#!/usr/bin/env python3
"""Quick test to verify simulation imports work in your venv"""

import sys
from pathlib import Path

print("Testing simulation imports in your environment...")
print("=" * 60)

# Add Simulation to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

try:
    print("1. Importing boardstate...")
    from boardstate import BoardState
    print("   ✓ boardstate imported successfully")

    print("2. Importing simulate_game...")
    from simulate_game import Card, simulate_game
    print("   ✓ simulate_game imported successfully")

    print("3. Importing run_simulation...")
    from run_simulation import run_simulations
    print("   ✓ run_simulations imported successfully")

    print("\n" + "=" * 60)
    print("SUCCESS! All imports work correctly.")
    print("The simulation integration should now work in your app.")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("FAILED! Check the error above.")
    print("=" * 60)
    sys.exit(1)
