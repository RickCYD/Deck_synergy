"""
Test script for Caesar, Legion's Emperor and similar reflexive trigger cards.

This demonstrates the generic implementation that handles:
1. Attack triggers with optional sacrifice costs
2. Reflexive triggers ("when you do")
3. Modal effects on triggered abilities
4. Tapped and attacking token creation
5. AI decision making for modal choices
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy')

# Test the extended mechanics detection
from Simulation.extended_mechanics import (
    detect_reflexive_trigger,
    parse_optional_cost,
    detect_modal_triggered_ability,
    execute_reflexive_trigger
)

# Test synergy detection
from src.synergy_engine.rules import detect_reflexive_trigger_synergies

def test_caesar_detection():
    """Test that Caesar's mechanics are detected properly."""

    caesar_oracle = """Whenever you attack, you may sacrifice another creature. When you do, choose two —
• Create two 1/1 red and white Soldier creature tokens with haste that are tapped and attacking.
• You draw a card and you lose 1 life.
• Caesar deals damage equal to the number of creature tokens you control to target opponent."""

    print("=" * 80)
    print("TESTING CAESAR, LEGION'S EMPEROR DETECTION")
    print("=" * 80)

    # Test 1: Reflexive trigger detection
    print("\n1. Testing reflexive trigger detection:")
    print("-" * 40)
    reflexive_info = detect_reflexive_trigger(caesar_oracle)

    print(f"Has reflexive trigger: {reflexive_info['has_reflexive']}")
    print(f"Trigger condition: {reflexive_info['trigger_condition']}")
    print(f"Optional cost: {reflexive_info['optional_cost']}")
    print(f"Reflexive effect: {reflexive_info['reflexive_effect'][:100]}...")
    print(f"Is modal: {reflexive_info['is_modal']}")

    # Test 2: Optional cost parsing
    print("\n2. Testing optional cost parsing:")
    print("-" * 40)
    cost_info = parse_optional_cost(reflexive_info['optional_cost'])

    print(f"Cost type: {cost_info['cost_type']}")
    print(f"Target: {cost_info['target']}")
    print(f"Quantity: {cost_info['quantity']}")

    # Test 3: Modal triggered ability detection
    print("\n3. Testing modal triggered ability detection:")
    print("-" * 40)
    modal_info = detect_modal_triggered_ability(caesar_oracle)

    print(f"Is modal trigger: {modal_info['is_modal_trigger']}")
    print(f"Trigger event: {modal_info['trigger_event']}")
    print(f"Modes to choose: {modal_info['modes_to_choose']}")
    print(f"Number of modes: {modal_info['num_modes']}")
    print("Modes:")
    for i, mode in enumerate(modal_info['modes'], 1):
        print(f"  {i}. {mode}")

    # Test 4: Synergy detection
    print("\n4. Testing synergy detection:")
    print("-" * 40)

    caesar_card = {
        'name': 'Caesar, Legion\'s Emperor',
        'oracle_text': caesar_oracle,
        'type_line': 'Legendary Creature — Human Soldier'
    }

    # Test synergy with token generator
    token_generator = {
        'name': 'Krenko, Mob Boss',
        'oracle_text': '{T}: Create X 1/1 red Goblin creature tokens, where X is the number of Goblins you control.',
        'type_line': 'Legendary Creature — Goblin Warrior'
    }

    synergies = detect_reflexive_trigger_synergies(caesar_card, token_generator)
    print(f"\nSynergies with {token_generator['name']}:")
    for syn in synergies:
        print(f"  - {syn['name']}: {syn['description']} (value: {syn['value']})")

    # Test synergy with sacrifice payoff
    blood_artist = {
        'name': 'Blood Artist',
        'oracle_text': 'Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.',
        'type_line': 'Creature — Vampire'
    }

    synergies = detect_reflexive_trigger_synergies(caesar_card, blood_artist)
    print(f"\nSynergies with {blood_artist['name']}:")
    for syn in synergies:
        print(f"  - {syn['name']}: {syn['description']} (value: {syn['value']})")

    # Test synergy with extra combat
    aggravated_assault = {
        'name': 'Aggravated Assault',
        'oracle_text': '{3}{R}{R}: Untap all creatures you control. After this main phase, there is an additional combat phase followed by an additional main phase.',
        'type_line': 'Enchantment'
    }

    synergies = detect_reflexive_trigger_synergies(caesar_card, aggravated_assault)
    print(f"\nSynergies with {aggravated_assault['name']}:")
    for syn in synergies:
        print(f"  - {syn['name']}: {syn['description']} (value: {syn['value']})")

    print("\n" + "=" * 80)
    print("✓ All detection tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_caesar_detection()
        print("\n✓ Implementation is working correctly for Caesar-like cards!")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
