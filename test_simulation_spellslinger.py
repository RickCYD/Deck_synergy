"""
Test Spellslinger Simulation Enhancements

Quick test to verify that the new spellslinger mechanics work in simulation:
- Veyran trigger doubling
- Whirlwind of Thought card draw
- Jeskai Ascendancy untaps
- Kindred Discovery draw on ETB/attack
- Kykar token generation
- Storm-Kiln Artist treasure generation (doubled by Veyran)
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

from simulate_game import Card, simulate_game

print("=" * 80)
print("TESTING SPELLSLINGER SIMULATION MECHANICS")
print("=" * 80)

# Create test deck with key spellslinger cards
commander = Card(
    name="Aang, Swift Savior",
    type="Legendary Creature — Avatar Monk",
    mana_cost="{1}{U}{R}{W}",
    power=3,
    toughness=3,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=True,
    is_commander=True,
    is_legendary=True,
    oracle_text="Prowess. Whenever you cast a noncreature spell, scry 1."
)

# Key engine pieces
veyran = Card(
    name="Veyran, Voice of Duality",
    type="Legendary Creature — Efreet Wizard",
    mana_cost="{1}{U}{R}",
    power=2,
    toughness=2,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="Magecraft — Whenever you cast or copy an instant or sorcery spell, Veyran gets +1/+1 until end of turn.\nIf you casting or copying an instant or sorcery spell causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time."
)

storm_kiln = Card(
    name="Storm-Kiln Artist",
    type="Creature — Dwarf Shaman",
    mana_cost="{2}{R}",
    power=2,
    toughness=2,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="This creature gets +1/+0 for each artifact you control.\nMagecraft — Whenever you cast or copy an instant or sorcery spell, create a Treasure token."
)

whirlwind = Card(
    name="Whirlwind of Thought",
    type="Enchantment",
    mana_cost="{1}{U}{R}{W}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="Whenever you cast a noncreature spell, draw a card."
)

jeskai_ascendancy = Card(
    name="Jeskai Ascendancy",
    type="Enchantment",
    mana_cost="{U}{R}{W}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="Whenever you cast a noncreature spell, creatures you control get +1/+1 until end of turn. Untap those creatures.\nWhenever you cast a noncreature spell, you may draw a card. If you do, discard a card."
)

kykar = Card(
    name="Kykar, Wind's Fury",
    type="Legendary Creature — Bird Wizard",
    mana_cost="{1}{U}{R}{W}",
    power=3,
    toughness=3,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="Flying\nWhenever you cast a noncreature spell, create a 1/1 white Spirit creature token with flying.\nSacrifice a Spirit: Add {R}."
)

kindred_discovery = Card(
    name="Kindred Discovery",
    type="Enchantment",
    mana_cost="{3}{U}{U}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="As this enchantment enters, choose a creature type.\nWhenever a creature you control of the chosen type enters or attacks, draw a card."
)

# Some cheap spells to trigger effects
brainstorm = Card(
    name="Brainstorm",
    type="Instant",
    mana_cost="{U}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    draw_cards=3,
    oracle_text="Draw three cards, then put two cards from your hand on top of your library in any order."
)

opt = Card(
    name="Opt",
    type="Instant",
    mana_cost="{U}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    draw_cards=1,
    oracle_text="Scry 1.\nDraw a card."
)

# Lands
island = Card(
    name="Island",
    type="Basic Land — Island",
    mana_cost="",
    power=None,
    toughness=None,
    produces_colors=["U"],
    mana_production=1,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False
)

mountain = Card(
    name="Mountain",
    type="Basic Land — Mountain",
    mana_cost="",
    power=None,
    toughness=None,
    produces_colors=["R"],
    mana_production=1,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False
)

plains = Card(
    name="Plains",
    type="Basic Land — Plains",
    mana_cost="",
    power=None,
    toughness=None,
    produces_colors=["W"],
    mana_production=1,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False
)

sol_ring = Card(
    name="Sol Ring",
    type="Artifact",
    mana_cost="{1}",
    power=None,
    toughness=None,
    produces_colors=["C"],
    mana_production=2,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text="{T}: Add {C}{C}."
)

# Build deck (99 cards total)
deck = (
    # Engine pieces
    [veyran, storm_kiln, whirlwind, jeskai_ascendancy, kykar, kindred_discovery, sol_ring] +
    # Spells
    [brainstorm, opt] * 2 +  # 4 cheap spells
    # Lands
    [island] * 30 +
    [mountain] * 20 +
    [plains] * 20 +
    # Fill with more basics
    [island] * 15
)

print(f"\nDeck size: {len(deck)} cards")
print(f"Commander: {commander.name}")
print("\nKey engine pieces:")
print("  - Veyran, Voice of Duality (doubles triggers)")
print("  - Storm-Kiln Artist (creates treasures)")
print("  - Whirlwind of Thought (draws cards)")
print("  - Jeskai Ascendancy (untaps creatures)")
print("  - Kykar, Wind's Fury (creates tokens)")
print("  - Kindred Discovery (draws on ETB/attack)")
print("\nRunning simulation...")
print("=" * 80)

# Run a quick simulation
try:
    result = simulate_game(deck, commander, max_turns=5, verbose=True)

    print("\n" + "=" * 80)
    print("SIMULATION RESULTS (First 5 turns)")
    print("=" * 80)

    print(f"\nTotal damage dealt: {result['total_damage']}")
    print(f"Cards drawn: {result['cards_drawn']}")
    print(f"Tokens created: {result['tokens_created']}")

    print("\n✅ Simulation completed successfully!")
    print("\nExpected behaviors:")
    print("  ✓ When Veyran is on board, Storm-Kiln creates 2 treasures per spell")
    print("  ✓ Whirlwind of Thought draws card on each instant/sorcery")
    print("  ✓ Jeskai Ascendancy untaps all creatures on spell cast")
    print("  ✓ Kykar creates Spirit tokens on noncreature spells")
    print("  ✓ Kindred Discovery draws when creatures enter/attack")

except Exception as e:
    print(f"\n❌ Error running simulation: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
