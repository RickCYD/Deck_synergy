#!/usr/bin/env python3
"""Test Nadier's Nightblade specifically"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from oracle_text_parser import parse_death_triggers_from_oracle

# Nadier's Nightblade oracle text
nadier_oracle = "Whenever a token you control leaves the battlefield, each opponent loses 1 life."

result = parse_death_triggers_from_oracle(nadier_oracle)

print(f"Nadier's Nightblade parsing test:")
print(f"Oracle: {nadier_oracle}")
print(f"Result: {result}")

# Nadier's Nightblade is specifically for tokens, not general death triggers
# The current parser looks for "dies" but Nadier says "leaves the battlefield"
# This is actually MORE general than dies, so it should be caught

if result == 0:
    print("\n⚠️ NOTE: Nadier's Nightblade not detected by current parser")
    print("This is because it uses 'leaves the battlefield' instead of 'dies'")
    print("This is a token-specific card that might need special handling")
else:
    print(f"\n✓ Nadier's Nightblade detected with drain value: {result}")
