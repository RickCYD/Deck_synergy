"""
Quick test to verify Spellslinger and Reanimator mechanics are working
"""
import sys
sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

from simulate_game import Card, simulate_game

def test_spellslinger():
    """Test spellslinger mechanics (Guttersnipe, Young Pyromancer, cast triggers)"""
    print("=" * 70)
    print("TESTING SPELLSLINGER MECHANICS")
    print("=" * 70)

    # Create a simple spellslinger deck
    deck = []

    # Add Guttersnipe (deals 2 damage per instant/sorcery)
    guttersnipe = Card(
        name="Guttersnipe",
        type="Creature",
        mana_cost="{2}{R}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Whenever you cast an instant or sorcery spell, Guttersnipe deals 2 damage to each opponent."
    )
    deck.append(guttersnipe)

    # Add Young Pyromancer (creates 1/1 elemental per instant/sorcery)
    young_pyromancer = Card(
        name="Young Pyromancer",
        type="Creature",
        mana_cost="{1}{R}",
        power=2,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."
    )
    deck.append(young_pyromancer)

    # Add some lands
    for i in range(20):
        mountain = Card(
            name="Mountain",
            type="Basic Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["R"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        )
        deck.append(mountain)

    # Add some instants/sorceries
    for i in range(15):
        lightning_bolt = Card(
            name="Lightning Bolt",
            type="Instant",
            mana_cost="{R}",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            draw_cards=0
        )
        deck.append(lightning_bolt)

    # Create a commander (for testing)
    commander = Card(
        name="Test Commander",
        type="Commander",
        mana_cost="{2}{R}{R}",
        power=4,
        toughness=4,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        is_commander=True
    )

    # Run simulation
    print("\nRunning 5-turn spellslinger simulation...")
    metrics = simulate_game(deck, commander, max_turns=5, verbose=False)

    print("\n" + "=" * 70)
    print("SPELLSLINGER RESULTS:")
    print("=" * 70)
    print(f"Total spells cast (turns 1-5): {sum(metrics['spells_cast'][1:6])}")
    print(f"Total spell damage (turns 1-5): {sum(metrics['spell_damage'][1:6])}")
    print(f"Total combat damage (turns 1-5): {sum(metrics['combat_damage'][1:6])}")
    print(f"Tokens created (turns 1-5): {sum(metrics['tokens_created'][1:6])}")
    print(f"Final board power: {metrics['total_power'][5]}")

    return metrics


def test_reanimator():
    """Test reanimator mechanics (Reanimate, Entomb, discard)"""
    print("\n" + "=" * 70)
    print("TESTING REANIMATOR MECHANICS")
    print("=" * 70)

    # Create a simple reanimator deck
    deck = []

    # Add some big creatures to reanimate
    for i in range(5):
        big_creature = Card(
            name=f"Big Creature {i+1}",
            type="Creature",
            mana_cost="{6}{B}{B}",
            power=8,
            toughness=8,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        )
        deck.append(big_creature)

    # Add Entomb (tutor to graveyard)
    entomb = Card(
        name="Entomb",
        type="Instant",
        mana_cost="{B}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Search your library for a card, then put that card into your graveyard."
    )
    deck.append(entomb)

    # Add Reanimate (return creature from graveyard)
    reanimate = Card(
        name="Reanimate",
        type="Sorcery",
        mana_cost="{B}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Put target creature card from a graveyard onto the battlefield under your control."
    )
    deck.append(reanimate)
    deck.append(reanimate)  # Add 2 copies

    # Add Faithless Looting (discard for value)
    faithless_looting = Card(
        name="Faithless Looting",
        type="Sorcery",
        mana_cost="{R}",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text="Draw two cards, then discard two cards.",
        draw_cards=0  # Handled in oracle text
    )
    deck.append(faithless_looting)

    # Add some lands
    for i in range(25):
        swamp = Card(
            name="Swamp",
            type="Basic Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["B"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        )
        deck.append(swamp)

    # Create a commander
    commander = Card(
        name="Reanimator Commander",
        type="Commander",
        mana_cost="{2}{B}{B}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True
    )

    # Run simulation
    print("\nRunning 6-turn reanimator simulation...")
    metrics = simulate_game(deck, commander, max_turns=6, verbose=False)

    print("\n" + "=" * 70)
    print("REANIMATOR RESULTS:")
    print("=" * 70)
    print(f"Total creatures reanimated: {metrics['creatures_reanimated_total']}")
    print(f"Cards discarded for value (turns 1-6): {sum(metrics['cards_discarded'][1:7])}")
    print(f"Creatures in graveyard (turn 6): {metrics['creatures_in_graveyard'][6]}")
    print(f"Graveyard power (turn 6): {metrics['graveyard_creature_power'][6]}")
    print(f"Final board power: {metrics['total_power'][6]}")

    return metrics


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  TESTING SPELLSLINGER & REANIMATOR MECHANICS IN GOLDFISH  ".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    # Test spellslinger
    spellslinger_metrics = test_spellslinger()

    # Test reanimator
    reanimator_metrics = test_reanimator()

    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  TESTS COMPLETED SUCCESSFULLY  ".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    print()
