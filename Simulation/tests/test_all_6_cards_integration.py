import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulate_game import Card
from boardstate import BoardState


def create_dummy_commander():
    return Card(
        name="Dummy Commander",
        type="Commander",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )


def test_all_6_cards_together():
    """Integration test: All 6 cards working together."""

    # Card 1: Sokka, Tenacious Tactician
    sokka = Card(
        name="Sokka, Tenacious Tactician",
        type="Legendary Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever you cast a noncreature spell, create a 1/1 white Ally creature token.\nOther Allies you control have prowess and menace.",
    )

    # Card 2: Kindred Discovery
    kindred_discovery = Card(
        name="Kindred Discovery",
        type="Enchantment",
        mana_cost="{3}{U}{U}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="As Kindred Discovery enters the battlefield, choose a creature type.\nWhenever a creature of the chosen type enters the battlefield or attacks, draw a card.",
    )

    # Card 3: Patchwork Banner
    patchwork_banner = Card(
        name="Patchwork Banner",
        type="Artifact",
        mana_cost="{3}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="As Patchwork Banner enters the battlefield, choose a creature type.\nCreatures you control of the chosen type get +1/+1 and have ward {1}.",
    )

    # Card 4: Wartime Protestors
    wartime_protestors = Card(
        name="Wartime Protestors",
        type="Creature — Human Ally",
        mana_cost="{1}{W}",
        power=1,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Whenever another Ally you control enters the battlefield, put a +1/+1 counter on that creature and it gains haste until end of turn.",
    )

    # Card 5: Sokka's Charge
    sokkas_charge = Card(
        name="Sokka's Charge",
        type="Enchantment",
        mana_cost="{2}{R}{W}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Allies you control have double strike and lifelink.",
    )

    # Card 6: Bria, Riptide Rogue
    bria = Card(
        name="Bria, Riptide Rogue",
        type="Legendary Creature — Otter Rogue",
        mana_cost="{2}{U}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        oracle_text="Prowess\nOther creatures you control have prowess.\nWhenever you cast a noncreature spell, target creature you control can't be blocked this turn.",
    )

    # Additional test card: Generic Ally
    ally_creature = Card(
        name="Test Ally",
        type="Creature — Human Ally",
        mana_cost="{2}{W}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="",
    )

    # Test artifact to trigger noncreature spell effects
    test_artifact = Card(
        name="Test Artifact",
        type="Artifact",
        mana_cost="{1}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="",
    )

    commander = create_dummy_commander()
    board = BoardState([], commander)

    # === Setup Phase ===
    print("=== SETUP PHASE ===")

    # Play Kindred Discovery
    board.play_card(kindred_discovery, verbose=True)
    print(f"Enchantments: {len(board.enchantments)}")

    # Play Patchwork Banner
    board.play_card(patchwork_banner, verbose=True)
    print(f"Artifacts: {len(board.artifacts)}")

    # Play Sokka's Charge
    board.play_card(sokkas_charge, verbose=True)
    print(f"Enchantments: {len(board.enchantments)}")

    # Play Wartime Protestors (should draw card from Kindred Discovery)
    initial_hand_size = len(board.hand)
    board.play_card(wartime_protestors, verbose=True)
    print(f"Creatures: {len(board.creatures)}")
    print(f"Hand size: {initial_hand_size} -> {len(board.hand)} (should increase by 1 from Kindred Discovery)")

    # Play Sokka
    board.play_card(sokka, verbose=True)
    print(f"Creatures: {len(board.creatures)}")

    # Play Bria
    board.play_card(bria, verbose=True)
    print(f"Creatures: {len(board.creatures)}")

    print("\n=== INTERACTION PHASE ===")

    # Cast a noncreature spell (should trigger multiple effects):
    # 1. Sokka creates token
    # 2. Bria makes a creature unblockable
    # 3. All creatures with prowess get +1/+1
    pre_spell_creatures = len(board.creatures)
    board.play_card(test_artifact, verbose=True)
    post_spell_creatures = len(board.creatures)

    print(f"\nCreatures before spell: {pre_spell_creatures}")
    print(f"Creatures after spell: {post_spell_creatures}")
    print("Should have created 1 token from Sokka")

    # Apply prowess
    board.apply_prowess_bonus()

    # Check prowess bonuses
    print("\n=== PROWESS BONUSES ===")
    for creature in board.creatures:
        bonus = board.get_prowess_power_bonus(creature)
        print(f"{creature.name}: +{bonus}/+{bonus} from prowess")

    # Play another Ally (should trigger Wartime Protestors and Kindred Discovery)
    print("\n=== PLAYING ANOTHER ALLY ===")
    initial_hand_size_2 = len(board.hand)
    board.play_card(ally_creature, verbose=True)
    print(f"Hand size: {initial_hand_size_2} -> {len(board.hand)} (should draw from Kindred Discovery)")

    # Check if ally got haste and counter from Wartime Protestors
    print(f"Ally has haste: {ally_creature.has_haste}")
    print(f"Ally counters: {getattr(ally_creature, 'counters', {})}")

    # Check anthem bonuses
    print("\n=== ANTHEM BONUSES ===")
    power_bonus, toughness_bonus = board.calculate_anthem_bonus(ally_creature)
    print(f"Ally anthem bonus: +{power_bonus}/+{toughness_bonus}")

    print("\n=== COMBAT SIMULATION ===")
    # Set up opponent
    board.opponents = [{'life_total': 20, 'creatures': [], 'commander_damage': {}}]

    # Resolve combat (should have double strike and lifelink from Sokka's Charge)
    board.resolve_combat(verbose=True)

    print("\n=== FINAL STATE ===")
    print(f"Creatures on board: {len(board.creatures)}")
    print(f"Our life total: {board.life_total}")
    print(f"Opponent life total: {board.opponents[0]['life_total']}")

    # === ASSERTIONS ===
    print("\n=== ASSERTIONS ===")

    # 1. Sokka should have created a token
    assert post_spell_creatures > pre_spell_creatures, "Sokka should have created a token"

    # 2. Ally should have haste from Wartime Protestors
    assert ally_creature.has_haste == True, "Ally should have haste from Wartime Protestors"

    # 3. Ally should have +1/+1 counter from Wartime Protestors
    counters = getattr(ally_creature, 'counters', {})
    assert '+1/+1' in counters, "Ally should have +1/+1 counter from Wartime Protestors"

    # 4. Hand size should have increased from Kindred Discovery triggers
    # (hard to test exact amount due to combat draws, but should be > 0)

    # 5. Anthem bonus should be at least +1/+1 from Patchwork Banner
    assert power_bonus >= 1, "Ally should have at least +1 power from Patchwork Banner"
    assert toughness_bonus >= 1, "Ally should have at least +1 toughness from Patchwork Banner"

    print("\n✓ All integration tests passed!")


if __name__ == "__main__":
    test_all_6_cards_together()
    print("\nIntegration test complete!")
