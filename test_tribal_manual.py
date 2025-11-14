"""
Manual tests for tribal synergy detection (no pytest required)
"""

from src.synergy_engine.rules import (
    detect_tribal_synergy,
    detect_tribal_chosen_type_synergy,
    detect_tribal_same_type_synergy,
    detect_tribal_trigger_synergy
)
from src.utils.tribal_extractors import (
    extract_cares_about_chosen_type,
    extract_cares_about_same_type,
    extract_tribal_lords,
    extract_tribal_triggers,
    extract_is_changeling,
    get_creature_types
)


def test_extract_cares_about_chosen_type():
    """Test detection of 'choose a creature type' effects"""
    print("\n=== Test: Extract Cares About Chosen Type ===")

    # Door of Destinies
    card = {
        'name': 'Door of Destinies',
        'oracle_text': 'As Door of Destinies enters the battlefield, choose a creature type. Whenever you cast a spell of the chosen type, put a charge counter on Door of Destinies.'
    }
    result = extract_cares_about_chosen_type(card)
    print(f"Card: {card['name']}")
    print(f"Result: {result}")
    assert result['cares_about_chosen_type'] == True, "Should detect chosen type"
    assert 'choice' in result['patterns_matched'], "Should match 'choice' pattern"
    print("✓ PASSED")


def test_extract_tribal_lords():
    """Test detection of tribal lord effects"""
    print("\n=== Test: Extract Tribal Lords ===")

    # Goblin King
    card = {
        'name': 'Goblin King',
        'oracle_text': 'Other Goblins you control get +1/+1 and have mountainwalk.',
        'type_line': 'Creature — Goblin'
    }
    result = extract_tribal_lords(card)
    print(f"Card: {card['name']}")
    print(f"Result: {result}")
    assert result['is_tribal_lord'] == True, "Should be a tribal lord"
    assert 'Goblin' in result['creature_types'], "Should detect Goblin type"
    print("✓ PASSED")


def test_extract_tribal_triggers():
    """Test detection of tribal triggered abilities"""
    print("\n=== Test: Extract Tribal Triggers ===")

    card = {
        'name': 'Elvish Warmaster',
        'oracle_text': 'Whenever you cast an Elf spell, create a 1/1 green Elf Warrior creature token.',
        'type_line': 'Creature — Elf Warrior'
    }
    result = extract_tribal_triggers(card)
    print(f"Card: {card['name']}")
    print(f"Result: {result}")
    assert result['has_tribal_trigger'] == True, "Should have tribal trigger"
    assert result['trigger_type'] == 'cast', "Should be cast trigger"
    assert 'Elf' in result['creature_types'], "Should trigger on Elf"
    print("✓ PASSED")


def test_extract_is_changeling():
    """Test detection of Changeling creatures"""
    print("\n=== Test: Extract Is Changeling ===")

    card = {
        'name': 'Changeling Titan',
        'oracle_text': 'Changeling (This card is every creature type.)',
        'type_line': 'Creature — Shapeshifter'
    }
    result = extract_is_changeling(card)
    print(f"Card: {card['name']}")
    print(f"Is Changeling: {result}")
    assert result == True, "Should be a Changeling"
    print("✓ PASSED")


def test_get_creature_types():
    """Test extraction of creature types from type line"""
    print("\n=== Test: Get Creature Types ===")

    card = {
        'name': 'Llanowar Elves',
        'type_line': 'Creature — Elf Druid'
    }
    types = get_creature_types(card)
    print(f"Card: {card['name']}")
    print(f"Types: {types}")
    assert 'Elf' in types, "Should have Elf type"
    assert 'Druid' in types, "Should have Druid type"
    print("✓ PASSED")


def test_detect_tribal_chosen_type_synergy():
    """Test synergy between 'chosen type' cards and creatures"""
    print("\n=== Test: Detect Tribal Chosen Type Synergy ===")

    card1 = {
        'name': 'Door of Destinies',
        'oracle_text': 'As Door of Destinies enters the battlefield, choose a creature type. Whenever you cast a spell of the chosen type, put a charge counter on Door of Destinies.',
        'type_line': 'Artifact'
    }
    card2 = {
        'name': 'Llanowar Elves',
        'oracle_text': '{T}: Add {G}.',
        'type_line': 'Creature — Elf Druid'
    }

    synergy = detect_tribal_chosen_type_synergy(card1, card2)
    print(f"Card1: {card1['name']}")
    print(f"Card2: {card2['name']}")
    print(f"Synergy: {synergy}")
    assert synergy is not None, "Should detect synergy"
    assert synergy['name'] == 'Chosen Type Synergy', "Should be Chosen Type Synergy"
    print("✓ PASSED")


def test_detect_changeling_synergy():
    """Test synergy between Changelings and tribal cards"""
    print("\n=== Test: Detect Changeling Synergy ===")

    changeling = {
        'name': 'Changeling Titan',
        'oracle_text': 'Changeling (This card is every creature type.)',
        'type_line': 'Creature — Shapeshifter'
    }
    tribal_lord = {
        'name': 'Goblin King',
        'oracle_text': 'Other Goblins you control get +1/+1 and have mountainwalk.',
        'type_line': 'Creature — Goblin'
    }

    synergy = detect_tribal_same_type_synergy(changeling, tribal_lord)
    print(f"Card1: {changeling['name']}")
    print(f"Card2: {tribal_lord['name']}")
    print(f"Synergy: {synergy}")
    assert synergy is not None, "Should detect changeling synergy"
    assert synergy['name'] == 'Changeling Synergy', "Should be Changeling Synergy"
    print("✓ PASSED")


def test_simulation_creature_types():
    """Test that the simulation can extract creature types"""
    print("\n=== Test: Simulation Creature Types ===")

    from Simulation.boardstate import BoardState

    deck = []
    commander = {'name': 'Test Commander', 'type_line': 'Creature — Elf Warrior'}

    board = BoardState(deck, commander)

    elf = {'name': 'Llanowar Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''}
    types = board._get_creature_types(elf)

    print(f"Card: {elf['name']}")
    print(f"Types extracted: {types}")
    assert 'Elf' in types, "Should extract Elf type"
    assert 'Druid' in types, "Should extract Druid type"
    print("✓ PASSED")


def test_simulation_choose_type():
    """Test that the simulation can choose a creature type"""
    print("\n=== Test: Simulation Choose Type ===")

    from Simulation.boardstate import BoardState

    # Create a deck with multiple Elves
    deck = [
        {'name': 'Llanowar Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
        {'name': 'Elvish Mystic', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
        {'name': 'Fyndhorn Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
        {'name': 'Goblin Guide', 'type_line': 'Creature — Goblin Warrior', 'oracle_text': ''},
    ]
    commander = {'name': 'Test Commander', 'type_line': 'Creature — Elf Warrior'}

    board = BoardState(deck, commander)

    # Choose a type for Door of Destinies
    chosen = board.choose_creature_type('Door of Destinies', verbose=True)

    print(f"Chosen type: {chosen}")
    print(f"Chosen types map: {board.chosen_creature_types}")

    assert chosen in ['Elf', 'Druid', 'Warrior', 'Goblin', 'Human'], "Should choose a valid type"
    assert 'Door of Destinies' in board.chosen_creature_types, "Should store the choice"
    print("✓ PASSED")


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Running Tribal Synergy Tests")
    print("="*60)

    tests = [
        test_extract_cares_about_chosen_type,
        test_extract_tribal_lords,
        test_extract_tribal_triggers,
        test_extract_is_changeling,
        test_get_creature_types,
        test_detect_tribal_chosen_type_synergy,
        test_detect_changeling_synergy,
        test_simulation_creature_types,
        test_simulation_choose_type,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
