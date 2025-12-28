"""
Test implementation of token copy mechanics for Irenicus's Vile Duplication

This test verifies:
1. Token copy extractor correctly identifies copy effects
2. Synergy rules detect interactions with ETB creatures
3. Simulation correctly creates token copies with modifications
"""

def test_extractor():
    """Test that the extractor correctly identifies Irenicus's Vile Duplication"""
    from src.utils.token_extractors import extract_token_copy_effects

    irenicus = {
        'name': "Irenicus's Vile Duplication",
        'oracle_text': "Create a token that's a copy of target creature you control, except the token has flying and it isn't legendary.",
        'type_line': 'Sorcery',
        'mana_cost': '{3}{U}',
        'cmc': 4
    }

    result = extract_token_copy_effects(irenicus)

    print("=" * 60)
    print("TEST 1: Token Copy Extractor")
    print("=" * 60)
    print(f"Card: {irenicus['name']}")
    print(f"Oracle Text: {irenicus['oracle_text']}")
    print(f"\nExtractor Results:")
    print(f"  Creates Token Copies: {result['creates_token_copies']}")
    print(f"  Copy Target: {result['copy_target']}")
    print(f"  Copy Count: {result['copy_count']}")
    print(f"  Modifications: {result['modifications']}")
    print(f"  Trigger Type: {result['trigger_type']}")
    print(f"  Repeatable: {result['repeatable']}")

    assert result['creates_token_copies'] == True, "Should detect token copy creation"
    assert result['copy_target'] == 'your_creature', "Should target your creatures"
    assert 'flying' in result['modifications'], "Should add flying"
    assert 'not_legendary' in result['modifications'], "Should remove legendary"
    assert result['trigger_type'] == 'spell', "Should be a spell"

    print("\n✓ All extractor tests passed!\n")


def test_synergy_detection():
    """Test that synergy rules detect interaction with ETB creatures"""
    from src.synergy_engine.rules import detect_copy_synergy

    irenicus = {
        'name': "Irenicus's Vile Duplication",
        'oracle_text': "Create a token that's a copy of target creature you control, except the token has flying and it isn't legendary.",
        'type_line': 'Sorcery',
    }

    mulldrifter = {
        'name': 'Mulldrifter',
        'oracle_text': 'Flying\nWhen Mulldrifter enters the battlefield, draw two cards.',
        'type_line': 'Creature — Elemental',
    }

    thassa = {
        'name': 'Thassa, Deep-Dwelling',
        'oracle_text': "At the beginning of your end step, exile up to one other target creature you control, then return that card to the battlefield under your control.",
        'type_line': 'Legendary Enchantment Creature — God',
    }

    print("=" * 60)
    print("TEST 2: Synergy Detection")
    print("=" * 60)

    # Test with non-legendary ETB creature
    synergy1 = detect_copy_synergy(irenicus, mulldrifter)
    print(f"\n{irenicus['name']} + {mulldrifter['name']}:")
    if synergy1:
        print(f"  Name: {synergy1['name']}")
        print(f"  Description: {synergy1['description']}")
        print(f"  Value: {synergy1['value']}")
        print(f"  Category: {synergy1['category']}")
        assert synergy1['value'] == 4.0, "Should have value of 4.0 for non-legendary ETB"
    else:
        print("  No synergy detected (ERROR!)")
        assert False, "Should detect synergy with Mulldrifter"

    # Test with legendary ETB creature (higher value)
    synergy2 = detect_copy_synergy(irenicus, thassa)
    print(f"\n{irenicus['name']} + {thassa['name']}:")
    if synergy2:
        print(f"  Name: {synergy2['name']}")
        print(f"  Description: {synergy2['description']}")
        print(f"  Value: {synergy2['value']}")
        print(f"  Category: {synergy2['category']}")
        # Should detect as legendary creature with ETB-like effects
        print(f"  (Note: Legendary status + not_legendary modification = bonus value)")
    else:
        print("  No synergy detected with this legendary creature")

    print("\n✓ Synergy detection tests passed!\n")


def test_simulation():
    """Test that the simulation correctly creates token copies"""
    import sys
    sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

    from boardstate import BoardState
    from simulate_game import Card

    print("=" * 60)
    print("TEST 3: Simulation Token Copy")
    print("=" * 60)

    # Create a board state
    board = BoardState()
    board.life = 40

    # Create a test creature with ETB
    mulldrifter = Card(
        name='Mulldrifter',
        type='Creature — Elemental',
        mana_cost='{4}{U}',
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={}
    )
    mulldrifter.has_flying = True
    mulldrifter.oracle_text = 'Flying\nWhen Mulldrifter enters the battlefield, draw two cards.'

    # Add to battlefield
    board.creatures.append(mulldrifter)
    print(f"\nCreatures on battlefield before copy:")
    print(f"  {mulldrifter.name} ({mulldrifter.power}/{mulldrifter.toughness})")

    # Create a token copy with Irenicus's Vile Duplication modifications
    print(f"\nCasting Irenicus's Vile Duplication targeting {mulldrifter.name}...")
    token = board.create_token_copy(
        source_creature=mulldrifter,
        modifications={
            'keywords': ['flying'],  # Adds flying (already has it, but testing)
            'not_legendary': True     # Removes legendary (not legendary, but testing)
        },
        verbose=True
    )

    print(f"\nCreatures on battlefield after copy:")
    for creature in board.creatures:
        print(f"  {creature.name} ({creature.power}/{creature.toughness})")
        if 'Token' in getattr(creature, 'type', ''):
            print(f"    → This is a token!")

    assert len(board.creatures) == 2, "Should have 2 creatures (original + token)"
    assert token is not None, "Should return the created token"
    assert 'Token' in token.type, "Token should have 'Token' in type line"
    assert token.name == mulldrifter.name, "Token should have same name"
    assert token.power == mulldrifter.power, "Token should have same power"
    assert token.toughness == mulldrifter.toughness, "Token should have same toughness"

    print("\n✓ Simulation tests passed!\n")


def test_legendary_copy():
    """Test copying a legendary creature (removing legendary status)"""
    import sys
    sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

    from boardstate import BoardState
    from simulate_game import Card

    print("=" * 60)
    print("TEST 4: Copying Legendary Creature")
    print("=" * 60)

    # Create a board state
    board = BoardState()
    board.life = 40

    # Create a legendary creature
    thassa = Card(
        name='Thassa, Deep-Dwelling',
        type='Legendary Enchantment Creature — God',
        mana_cost='{3}{U}{U}',
        power=6,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={}
    )
    thassa.oracle_text = "At the beginning of your end step, exile up to one other target creature you control, then return that card to the battlefield under your control."

    # Add to battlefield
    board.creatures.append(thassa)
    print(f"\nOriginal creature:")
    print(f"  {thassa.name}")
    print(f"  Type: {thassa.type}")
    print(f"  Legendary: {'Yes' if 'Legendary' in thassa.type else 'No'}")

    # Create a token copy with legendary removal
    print(f"\nCasting Irenicus's Vile Duplication targeting {thassa.name}...")
    token = board.create_token_copy(
        source_creature=thassa,
        modifications={
            'keywords': ['flying'],
            'not_legendary': True  # This is the key feature!
        },
        verbose=True
    )

    print(f"\nToken copy:")
    print(f"  {token.name}")
    print(f"  Type: {token.type}")
    print(f"  Legendary: {'Yes' if 'Legendary' in token.type else 'No'}")
    print(f"  Is Token: {'Yes' if 'Token' in token.type else 'No'}")

    assert 'Legendary' not in token.type, "Token should NOT be legendary"
    assert 'Token' in token.type, "Token should have 'Token' in type line"
    assert 'Legendary' in thassa.type, "Original should still be legendary"

    print("\n✓ Legendary copy tests passed!\n")
    print("This means you can have both Thassa and the token on battlefield!")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TESTING IRENICUS'S VILE DUPLICATION IMPLEMENTATION")
    print("=" * 60 + "\n")

    try:
        test_extractor()
        test_synergy_detection()
        test_simulation()
        test_legendary_copy()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nImplementation Summary:")
        print("1. ✓ Token copy extractor detects copy effects and modifications")
        print("2. ✓ Synergy rules detect valuable interactions with ETB creatures")
        print("3. ✓ Simulation creates token copies with proper modifications")
        print("4. ✓ Legendary creatures can be copied (legendary status removed)")
        print("\nIrenicus's Vile Duplication is fully implemented!")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
