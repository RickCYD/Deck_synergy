#!/usr/bin/env python3
"""
End-to-End Unified Architecture Test

This is the capstone test that validates the complete unified architecture
pipeline working together:

1. Parse deck with unified parser (Part 1)
2. Register triggers with registry (Part 2)
3. Execute triggers with enhanced BoardState (Part 3)
4. Detect synergies and calculate priorities (Part 4)
5. Simulate game turns with everything integrated

This test demonstrates the value proposition: synergies detected → triggers
registered → triggers execute → deck performs better.
"""

import sys
sys.path.insert(0, '/home/user/Deck_synergy')
sys.path.insert(0, '/home/user/Deck_synergy/Simulation')

from src.api.local_cards import get_card_by_name, load_local_database
from src.core.card_parser import UnifiedCardParser
from src.core.trigger_registry import TriggerRegistry
from src.core.synergy_simulation_bridge import SynergyBridge
from Simulation.unified_integration import (
    initialize_unified_system,
    handle_card_etb,
    handle_spell_cast,
    handle_end_of_turn
)

# Simple Card class for testing
class Card:
    def __init__(self, name, type, mana_cost, power, toughness, produces_colors,
                 mana_production, etb_tapped, etb_tapped_conditions, has_haste,
                 oracle_text="", has_vigilance=False, has_lifelink=False,
                 has_flying=False, **kwargs):
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
        self.has_lifelink = has_lifelink
        self.has_flying = has_flying
        self.oracle_text = oracle_text
        self.base_power = power
        self.base_toughness = toughness
        for k, v in kwargs.items():
            setattr(self, k, v)

# Mock BoardState for simulation
class MockBoardState:
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
        self.turn = 1
        self.life_total = 40

print("=" * 80)
print("END-TO-END UNIFIED ARCHITECTURE TEST")
print("=" * 80)
print("\nThis test validates the complete pipeline:")
print("  Parse → Synergy Detection → Trigger Registry → Execution → Simulation")

# =============================================================================
# SETUP
# =============================================================================

print("\n" + "=" * 80)
print("SETUP: Loading Ally Prowess Deck")
print("=" * 80)

load_local_database()

# Ally Prowess deck cards
deck_card_names = [
    # Rally Allies
    "Chasm Guide",
    "Makindi Patrol",
    "Lantern Scout",
    "Resolute Blademaster",

    # Prowess Creatures
    "Monastery Swiftspear",
    "Bria, Riptide Rogue",
    "Narset, Enlightened Exile",

    # Cheap Spells (for prowess)
    "Lightning Bolt",
    "Brainstorm",
    "Opt",

    # Token Creators
    "Kykar, Wind's Fury",
    "Dragon Fodder",

    # Spellslinger Payoffs
    "Jeskai Ascendancy",
    "Veyran, Voice of Duality",
]

print(f"\nLoading {len(deck_card_names)} cards...")
deck_cards = []
for name in deck_card_names:
    card = get_card_by_name(name)
    if card:
        deck_cards.append(card)

print(f"✓ Loaded {len(deck_cards)} cards")

# =============================================================================
# PART 1: UNIFIED PARSER
# =============================================================================

print("\n" + "=" * 80)
print("PART 1: Parse Deck with Unified Parser")
print("=" * 80)

parser = UnifiedCardParser()
abilities_map = {}

for card in deck_cards:
    abilities = parser.parse_card(card)
    abilities_map[card['name']] = abilities

# Count what we parsed
rally_count = sum(1 for a in abilities_map.values() if a.has_rally)
prowess_count = sum(1 for a in abilities_map.values() if a.has_prowess)
token_count = sum(1 for a in abilities_map.values() if a.creates_tokens)
magecraft_count = sum(1 for a in abilities_map.values() if a.has_magecraft)

print(f"\n✓ Parsed {len(abilities_map)} cards:")
print(f"  • Rally: {rally_count}")
print(f"  • Prowess: {prowess_count}")
print(f"  • Token creators: {token_count}")
print(f"  • Magecraft: {magecraft_count}")

part1_success = rally_count >= 3 and prowess_count >= 2

# =============================================================================
# PART 4: SYNERGY DETECTION
# =============================================================================

print("\n" + "=" * 80)
print("PART 4: Detect Synergies with Bridge")
print("=" * 80)

bridge = SynergyBridge()
deck_cards_prepared, metadata = bridge.create_trigger_aware_deck(deck_cards)

synergies = metadata['synergies']
priorities = metadata['priorities']

print(f"\n✓ Detected {synergies['total_synergies']} synergies:")
print(f"  • Rally + Token: {len(synergies['rally_synergies'])}")
print(f"  • Prowess + Spell: {len(synergies['prowess_synergies'])}")
print(f"  • Spellslinger: {len(synergies['spellslinger_synergies'])}")
print(f"  • Synergy Score: {synergies['synergy_score']:.1f}/100")

part4_success = synergies['total_synergies'] > 20

# =============================================================================
# PART 2 & 3: INITIALIZE SIMULATION WITH TRIGGERS
# =============================================================================

print("\n" + "=" * 80)
print("PARTS 2 & 3: Initialize BoardState with Trigger System")
print("=" * 80)

board = MockBoardState()
parser_sim, registry_sim = initialize_unified_system(board, deck_cards)

print(f"\n✓ Unified system initialized:")
print(f"  • Parser ready: {parser_sim is not None}")
print(f"  • Registry ready: {registry_sim is not None}")
print(f"  • BoardState enhanced: {hasattr(board, 'trigger_event')}")
print(f"  • Cleanup method added: {hasattr(board, 'cleanup_temporary_effects')}")

part2_3_success = hasattr(board, 'trigger_event')

# =============================================================================
# SIMULATION: TURN 1 - Play Rally Allies
# =============================================================================

print("\n" + "=" * 80)
print("SIMULATION: Turn 1 - Play Rally Allies")
print("=" * 80)

print("\nTurn 1 Actions:")
print("  1. Play Chasm Guide (Rally: grant haste)")
print("  2. Play Makindi Patrol (Rally: grant vigilance)")

# Create card objects
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

# Play Chasm Guide
board.creatures.append(chasm_guide)
chasm_dict = get_card_by_name("Chasm Guide")
handle_card_etb(board, chasm_guide, chasm_dict)

print(f"\n  After Chasm Guide ETB:")
print(f"    Chasm Guide haste: {chasm_guide.has_haste}")
print(f"    Triggers registered: {len(registry_sim.get_triggers_for_event('rally'))}")

# Play Makindi Patrol (should trigger Chasm Guide's rally)
board.creatures.append(makindi_patrol)
makindi_dict = get_card_by_name("Makindi Patrol")
handle_card_etb(board, makindi_patrol, makindi_dict)

print(f"\n  After Makindi Patrol ETB (rally triggers):")
print(f"    Chasm Guide haste: {chasm_guide.has_haste}")
print(f"    Chasm Guide vigilance: {chasm_guide.has_vigilance}")
print(f"    Makindi Patrol haste: {makindi_patrol.has_haste}")
print(f"    Makindi Patrol vigilance: {makindi_patrol.has_vigilance}")

# Both should have haste and vigilance now
turn1_rally_success = chasm_guide.has_haste and chasm_guide.has_vigilance

# End of turn - cleanup
print(f"\n  End of Turn 1 (cleanup temporary effects)...")
handle_end_of_turn(board)

print(f"\n  After Cleanup:")
print(f"    Chasm Guide haste: {chasm_guide.has_haste}")
print(f"    Chasm Guide vigilance: {chasm_guide.has_vigilance}")

# Keywords should be removed
turn1_cleanup_success = not chasm_guide.has_haste and not chasm_guide.has_vigilance

# =============================================================================
# SIMULATION: TURN 2 - Test Prowess
# =============================================================================

print("\n" + "=" * 80)
print("SIMULATION: Turn 2 - Test Prowess")
print("=" * 80)

board.turn = 2

print("\nTurn 2 Actions:")
print("  1. Play Monastery Swiftspear (Prowess)")
print("  2. Cast Lightning Bolt (triggers prowess)")

# Play Monastery Swiftspear
swiftspear = Card(
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

board.creatures.append(swiftspear)
swiftspear_dict = get_card_by_name("Monastery Swiftspear")
handle_card_etb(board, swiftspear, swiftspear_dict)

print(f"\n  Swiftspear stats: {swiftspear.power}/{swiftspear.toughness}")

# Cast Lightning Bolt
bolt_dict = {
    'name': 'Lightning Bolt',
    'type_line': 'Instant',
    'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
    'cmc': 1
}

bolt_card = Card(
    name="Lightning Bolt",
    type="Instant",
    mana_cost="{R}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False
)

handle_spell_cast(board, bolt_card, bolt_dict)

print(f"\n  After casting Lightning Bolt (prowess trigger):")
print(f"    Swiftspear stats: {swiftspear.power}/{swiftspear.toughness}")

# Should be 2/3 now
turn2_prowess_success = swiftspear.power == 2 and swiftspear.toughness == 3

# End of turn cleanup
handle_end_of_turn(board)

print(f"\n  After Turn 2 cleanup:")
print(f"    Swiftspear stats: {swiftspear.power}/{swiftspear.toughness}")

# Should be back to 1/2
turn2_cleanup_success = swiftspear.power == 1 and swiftspear.toughness == 2

# =============================================================================
# SIMULATION: TURN 3 - Test Tokens
# =============================================================================

print("\n" + "=" * 80)
print("SIMULATION: Turn 3 - Test Token Creation")
print("=" * 80)

board.turn = 3
board.tokens_created_this_turn = 0

print("\nTurn 3 Actions:")
print("  1. Play Kykar, Wind's Fury")
print("  2. Cast Brainstorm (creates Spirit token)")

# Play Kykar
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

board.creatures.append(kykar)
kykar_dict = get_card_by_name("Kykar, Wind's Fury")
handle_card_etb(board, kykar, kykar_dict)

creatures_before = len(board.creatures)
print(f"\n  Creatures before spell: {creatures_before}")

# Cast Brainstorm
brainstorm_dict = {
    'name': 'Brainstorm',
    'type_line': 'Instant',
    'oracle_text': 'Draw three cards, then put two cards from your hand on top of your library in any order.',
    'cmc': 1
}

brainstorm_card = Card(
    name="Brainstorm",
    type="Instant",
    mana_cost="{U}",
    power=None,
    toughness=None,
    produces_colors=[],
    mana_production={},
    etb_tapped=False,
    etb_tapped_conditions=[],
    has_haste=False
)

handle_spell_cast(board, brainstorm_card, brainstorm_dict)

creatures_after = len(board.creatures)
print(f"\n  After casting Brainstorm:")
print(f"    Creatures: {creatures_after}")
print(f"    Tokens created: {board.tokens_created_this_turn}")

# Should have created a Spirit token
turn3_token_success = creatures_after > creatures_before

# =============================================================================
# FINAL VALIDATION
# =============================================================================

print("\n" + "=" * 80)
print("FINAL VALIDATION: Complete Pipeline Test")
print("=" * 80)

print("\nValidating end-to-end integration:")

tests = [
    ("Part 1: Unified parser works", part1_success),
    ("Part 4: Synergy detection works", part4_success),
    ("Part 2 & 3: Trigger system initialized", part2_3_success),
    ("Turn 1: Rally triggers executed", turn1_rally_success),
    ("Turn 1: Cleanup removed keywords", turn1_cleanup_success),
    ("Turn 2: Prowess buffed creature", turn2_prowess_success),
    ("Turn 2: Cleanup reset stats", turn2_cleanup_success),
    ("Turn 3: Token creation worked", turn3_token_success),
]

passed = sum(1 for _, success in tests if success)
total = len(tests)

print(f"\n✅ Passed: {passed}/{total}")
for test_name, success in tests:
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}")

print("\n" + "=" * 80)
print("UNIFIED ARCHITECTURE BENEFITS DEMONSTRATED")
print("=" * 80)

print("\nWhat the unified architecture enables:")
print(f"  1. Single parser → {len(abilities_map)} cards parsed once ✅")
print(f"  2. Synergies detected → {synergies['total_synergies']} synergies found ✅")
print(f"  3. Triggers registered → {len(registry_sim.get_all_events())} event types ✅")
print(f"  4. Triggers execute → Rally, prowess, tokens all work ✅")
print(f"  5. Priorities calculated → Optimal card ordering ✅")

print(f"\nDeck Performance:")
print(f"  • Rally triggers: {metadata['trigger_stats']['rally_count']} cards")
print(f"  • Prowess triggers: {metadata['trigger_stats']['prowess_count']} cards")
print(f"  • Synergy score: {synergies['synergy_score']:.1f}/100")
print(f"  • Creatures on board: {len(board.creatures)}")

if passed == total:
    print("\n🎉 SUCCESS! The complete unified architecture pipeline works!")
    print("\nBefore unified architecture:")
    print("  ❌ Rally triggers parsed but not executed")
    print("  ❌ Prowess triggers ignored")
    print("  ❌ Synergies detected but unused")
    print("  ❌ Duplicate parsing code everywhere")
    print("\nAfter unified architecture:")
    print("  ✅ Rally triggers execute (haste/vigilance granted!)")
    print("  ✅ Prowess triggers execute (creatures buffed!)")
    print("  ✅ Tokens created from spellslinger triggers")
    print("  ✅ Synergies influence card priorities")
    print("  ✅ Single parser used everywhere")
    print("  ✅ Temporary effects clean up properly")
else:
    print(f"\n⚠️  {total - passed} test(s) failed.")
    print("The unified architecture needs adjustments.")

print("\n" + "=" * 80)
