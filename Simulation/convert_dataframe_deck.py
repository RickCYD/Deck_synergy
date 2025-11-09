import pandas as pd

def parse_mana_cost(cost_str):
    """
    Parses a mana cost string (like "3WG") into a total integer cost.
    E.g., "3WG" -> 5
    """
    if pd.isna(cost_str) or cost_str == '':
        return 0

    total = 0
    num = ''
    for ch in cost_str:
        if ch.isdigit():
            num += ch
        else:
            if num:
                total += int(num)
                num = ''
            if ch.isalpha():
                total += 1
    if num:
        total += int(num)
    return total

# Optional: You can add any other utility functions here

# If you want to test this script directly, you can use this block:
if __name__ == "__main__":
    # Test example
    test_costs = ["2WGR", "2RR", "G", "", None]
    for cost in test_costs:
        print(f"{cost}: {parse_mana_cost(cost)}")
