#!/usr/bin/env python3
"""
Test BoardState integration with unified architecture.

This validates that Part 3 (Enhanced BoardState) works correctly with
Parts 1-2 (Unified Parser + Trigger Registry).

Tests:
1. BoardState enhancement adds all required methods
2. Trigger events execute correctly
3. Rally triggers grant keywords
4. Prowess triggers buff creatures
5. Temporary effects clean up at EOT
6. Card registration/unregistration works
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

from src.api.local_cards import get_card_by_name, load_local_database
from Simulation.unified_integration import initialize_unified_system, handle_card_etb, handle_spell_cast, handle_end_of_turn

# Simple Card class for testing
class Card:
    def __init__(self, name, type, mana_cost, power, toughness, produces_colors,
                 mana_production, etb_tapped, etb_tapped_conditions, has_haste,
                 oracle_text="", has_vigilance=False, has_flying=False, **kwargs):
        self.name = name
        self.type = type
        self.mana_cost = mana_cost
        self.power = power
        self.toughness = toughness
        self.produces_colors = produces_colors
        self.mana_production = mana_production
        self.etb_tapped = etb_tapped
        self.etb_tapped_conditions = etb_tapped_conditions
        self.has_haste = has_haste
        self.has_vigilance = has_vigilance
        self.has_flying = has_flying
        self.oracle_text = oracle_text
        for k, v in kwargs.items():
            setattr(self, k, v)

print("=" * 80)
print("BOARDSTATE INTEGRATION TEST")
print("=" * 80)

# Load database
print("\nLoading card database...")
load_local_database()
print("✓ Database loaded!")

# =============================================================================
# CREATE MOCK BOARDSTATE
# =============================================================================

class MockBoardState:
    """Minimal BoardState for testing."""
    def __init__(self):
        self.creatures = []
        self.hand = []
        self.library = []
        self.graveyard = []
        self.lands_untapped = []
        self.artifacts = []
        self.pending_effects = []
        self.num_opponents = 1
        self.opponents = [{'life_total': 40, 'creatures': [], 'is_alive': True}]

print("\nCreating mock board state...")
board = MockBoardState()

# =============================================================================
# INITIALIZE UNIFIED SYSTEM
# =============================================================================

print("\nInitializing unified architecture...")
parser, registry = initialize_unified_system(board, [])

# Verify enhancement
print(f"\n✓ BoardState enhanced:")
print(f"  - Has trigger_event: {hasattr(board, 'trigger_event')}")
print(f"  - Has grant_keyword_until_eot: {hasattr(board, 'grant_keyword_until_eot')}")
print(f"  - Has buff_creature_until_eot: {hasattr(board, 'buff_creature_until_eot')}")
print(f"  - Has cleanup_temporary_effects: {hasattr(board, 'cleanup_temporary_effects')}")
print(f"  - Has process_pending_effects: {hasattr(board, 'process_pending_effects')}")
print(f"  - Has trigger_registry: {board.trigger_registry is not None}")

# =============================================================================
# TEST 1: RALLY TRIGGERS
# =============================================================================

print("\n" + "=" * 80)
print("TEST 1: RALLY TRIGGERS (Grant Keywords)")
print("=" * 80)

# Create some Ally creatures
print("\nCreating Ally creatures...")

chasm_guide = Card(
    name="Chasm Guide",
    type="Creature — Ally",
    mana_cost="{3}{R}",
    power=3,
    toughness=2,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
    oracle_text="Rally — Whenever Chasm Guide or another Ally enters the battlefield under your control, creatures you control gain haste until end of turn."
)

makindi_patrol = Card(
    name="Makindi Patrol",
    type="Creature — Ally",
    mana_cost="{2}{W}",
    power=2,
    toughness=3,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
    has_vigilance=False,
    oracle_text="Rally — Whenever Makindi Patrol or another Ally enters the battlefield under your control, creatures you control gain vigilance until end of turn."
)

board.creatures = [chasm_guide, makindi_patrol]

# Register the Ally creatures
print("Registering Chasm Guide...")
chasm_dict = get_card_by_name("Chasm Guide")
handle_card_etb(board, chasm_guide, chasm_dict)

print("Registering Makindi Patrol...")
makindi_dict = get_card_by_name("Makindi Patrol")
handle_card_etb(board, makindi_patrol, makindi_dict)

print(f"\nRegistry stats: {registry.get_stats()}")

# Now play another Ally to trigger rally
print("\n🎯 Playing another Ally to trigger rally...")

new_ally = Card(
    name="Test Ally",
    type="Creature — Human Ally",
    mana_cost="{2}{W}",
    power=2,
    toughness=2,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
)

board.creatures.append(new_ally)

# This should trigger both rally effects
ally_dict = {'name': 'Test Ally', 'type_line': 'Creature — Human Ally', 'oracle_text': ''}
handle_card_etb(board, new_ally, ally_dict)

# Check results
print(f"\nCreatures after rally triggers:")
for creature in board.creatures:
    print(f"  - {creature.name}: haste={creature.has_haste}, vigilance={creature.has_vigilance}")

# Verify keywords were granted
rally_success = all(c.has_haste for c in board.creatures)
print(f"\n{'✅' if rally_success else '❌'} Rally haste granted: {rally_success}")

# =============================================================================
# TEST 2: PROWESS TRIGGERS
# =============================================================================

print("\n" + "=" * 80)
print("TEST 2: PROWESS TRIGGERS (Buff Creatures)")
print("=" * 80)

# Create a prowess creature
print("\nCreating prowess creature...")

monastery_swiftspear = Card(
    name="Monastery Swiftspear",
    type="Creature — Human Monk",
    mana_cost="{R}",
    power=1,
    toughness=2,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=True,
    oracle_text="Haste\nProwess (Whenever you cast a noncreature spell, this creature gets +1/+1 until end of turn.)"
)

board.creatures = [monastery_swiftspear]  # Reset creatures

# Register the prowess creature
print("Registering Monastery Swiftspear...")
swiftspear_dict = get_card_by_name("Monastery Swiftspear")
handle_card_etb(board, monastery_swiftspear, swiftspear_dict)

print(f"Initial stats: {monastery_swiftspear.power}/{monastery_swiftspear.toughness}")

# Cast a noncreature spell
print("\n🎯 Casting Lightning Bolt (noncreature spell)...")

lightning_bolt = Card(
    name="Lightning Bolt",
    type="Instant",
    mana_cost="{R}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
    oracle_text="Lightning Bolt deals 3 damage to any target."
)

bolt_dict = {'name': 'Lightning Bolt', 'type_line': 'Instant', 'oracle_text': 'Lightning Bolt deals 3 damage to any target.'}
handle_spell_cast(board, lightning_bolt, bolt_dict)

print(f"Stats after prowess trigger: {monastery_swiftspear.power}/{monastery_swiftspear.toughness}")

# Verify buff
prowess_success = monastery_swiftspear.power > 1
print(f"\n{'✅' if prowess_success else '❌'} Prowess buff applied: {prowess_success}")

# =============================================================================
# TEST 3: END OF TURN CLEANUP
# =============================================================================

print("\n" + "=" * 80)
print("TEST 3: END OF TURN CLEANUP")
print("=" * 80)

print("\nBefore cleanup:")
print(f"  Monastery Swiftspear: {monastery_swiftspear.power}/{monastery_swiftspear.toughness}")
print(f"  Temporary buffs: {len(board.temporary_buffs)}")
print(f"  Temporary keywords: {len(board.temporary_keywords)}")

# Clean up
print("\n🧹 Cleaning up temporary effects...")
handle_end_of_turn(board)

print(f"\nAfter cleanup:")
print(f"  Monastery Swiftspear: {monastery_swiftspear.power}/{monastery_swiftspear.toughness}")
print(f"  Temporary buffs: {len(board.temporary_buffs)}")
print(f"  Temporary keywords: {len(board.temporary_keywords)}")

# Verify cleanup
cleanup_success = monastery_swiftspear.power == 1 and monastery_swiftspear.toughness == 2
print(f"\n{'✅' if cleanup_success else '❌'} Cleanup successful: {cleanup_success}")

# =============================================================================
# TEST 4: TOKEN CREATION
# =============================================================================

print("\n" + "=" * 80)
print("TEST 4: TOKEN CREATION")
print("=" * 80)

# Create Kykar
print("\nCreating Kykar, Wind's Fury...")

kykar = Card(
    name="Kykar, Wind's Fury",
    type="Legendary Creature — Bird Wizard",
    mana_cost="{1}{U}{R}{W}",
    power=3,
    toughness=3,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
    has_flying=True,
    oracle_text="Flying\nWhenever you cast a noncreature spell, create a 1/1 white Spirit creature token with flying."
)

board.creatures = [kykar]
board.tokens_created_this_turn = 0

# Register Kykar
print("Registering Kykar...")
kykar_dict = get_card_by_name("Kykar, Wind's Fury")
handle_card_etb(board, kykar, kykar_dict)

creatures_before = len(board.creatures)
print(f"Creatures before spell: {creatures_before}")

# Cast a noncreature spell
print("\n🎯 Casting Brainstorm (noncreature spell)...")

brainstorm = Card(
    name="Brainstorm",
    type="Instant",
    mana_cost="{U}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False,
)

brainstorm_dict = {'name': 'Brainstorm', 'type_line': 'Instant', 'oracle_text': 'Draw three cards, then put two cards from your hand on top of your library in any order.'}
handle_spell_cast(board, brainstorm, brainstorm_dict)

creatures_after = len(board.creatures)
print(f"Creatures after spell: {creatures_after}")
print(f"Tokens created: {board.tokens_created_this_turn}")

# Verify token creation
token_success = creatures_after > creatures_before
print(f"\n{'✅' if token_success else '❌'} Token created: {token_success}")

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

tests = [
    ("Rally triggers grant keywords", rally_success),
    ("Prowess triggers buff creatures", prowess_success),
    ("Cleanup removes temporary effects", cleanup_success),
    ("Token creation works", token_success),
]

passed = sum(1 for _, success in tests if success)
total = len(tests)

print(f"\n✅ Passed: {passed}/{total}")
for test_name, success in tests:
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}")

print(f"\nFinal registry state: {registry}")

if passed == total:
    print("\n🎉 All integration tests passed! Part 3 complete.")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Needs investigation.")
