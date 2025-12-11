"""
Comprehensive tests for extended mechanics in MTG simulation.

Tests cover:
- Flicker/Blink effects (Ephemerate, Restoration Angel, Conjurer's Closet)
- Copy effects (Clone, Spark Double, Populate)
- Modal spells (Cryptic Command, Boros Charm, Prismari Command)
- Cascade/Suspend (Bloodbraid Elf, Maelstrom Wanderer, Ancestral Vision)
- Persist/Undying (Kitchen Finks, Geralf's Messenger, Mikaeus)
- Convoke/Delve (Stoke the Flames, Treasure Cruise, Hogaak)
- Flash timing (Teferi, Mage of Zhalfir, Dictate of Heliod, Venser)
- Flashback (Faithless Looting, Deep Analysis, Lingering Souls)
- Buyback/Retrace (Capsize, Reiterate, Worm Harvest)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from mtg_abilities import TriggeredAbility
from simulate_game import Card
from boardstate import BoardState
from extended_mechanics import (
    # Detection functions
    detect_flicker_ability,
    detect_copy_ability,
    detect_modal_spell,
    detect_cascade,
    detect_suspend,
    detect_persist,
    detect_undying,
    detect_convoke,
    detect_delve,
    detect_flash,
    detect_flashback,
    detect_buyback,
    detect_retrace,
    # Execution functions
    flicker_permanent,
    process_end_of_turn_flicker_returns,
    copy_creature,
    create_token_copy,
    evaluate_modal_choice,
    execute_modal_spell,
    resolve_cascade,
    suspend_card,
    process_suspended_cards,
    handle_creature_death_persist_undying,
    apply_convoke,
    apply_delve,
    get_effective_mana_cost,
    cast_flashback,
    cast_with_buyback,
    cast_retrace,
    # Utilities
    initialize_extended_metrics,
    get_extended_metrics,
)


def create_dummy_commander():
    """Create a dummy commander for testing."""
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


def create_basic_creature(name: str, power: int = 2, toughness: int = 2,
                          mana_cost: str = "2", oracle_text: str = "") -> Card:
    """Helper to create basic creatures for testing."""
    return Card(
        name=name,
        type="Creature",
        mana_cost=mana_cost,
        power=power,
        toughness=toughness,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle_text,
    )


def create_instant_sorcery(name: str, card_type: str = "Instant",
                           mana_cost: str = "1U", oracle_text: str = "",
                           draw_cards: int = 0, deals_damage: int = 0) -> Card:
    """Helper to create instant/sorcery for testing."""
    return Card(
        name=name,
        type=card_type,
        mana_cost=mana_cost,
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        oracle_text=oracle_text,
        draw_cards=draw_cards,
        deals_damage=deals_damage,
    )


# =============================================================================
# FLICKER/BLINK TESTS
# =============================================================================

class TestFlickerBlink:
    """Test flicker/blink mechanics with Ephemerate, Restoration Angel, Conjurer's Closet."""

    def test_detect_ephemerate(self):
        """Test detection of Ephemerate's flicker ability."""
        oracle = "Exile target creature you control, then return it to the battlefield under its owner's control."
        result = detect_flicker_ability(oracle)
        assert result['has_flicker'] is True
        assert result['flicker_type'] == 'exile_return_immediate'
        assert result['targets'] == 'creature'

    def test_detect_restoration_angel(self):
        """Test detection of Restoration Angel's flicker ETB."""
        oracle = "Flash. Flying. When Restoration Angel enters the battlefield, you may exile target non-Angel creature you control, then return that card to the battlefield under your control."
        result = detect_flicker_ability(oracle)
        assert result['has_flicker'] is True
        assert result['is_etb_trigger'] is True

    def test_detect_conjurers_closet(self):
        """Test detection of Conjurer's Closet's end-step flicker."""
        oracle = "At the beginning of your end step, you may exile target creature you control, then return that card to the battlefield under your control."
        result = detect_flicker_ability(oracle)
        assert result['has_flicker'] is True
        assert result['flicker_type'] == 'exile_return_end_turn'

    def test_flicker_creature_etb_triggers(self):
        """Test that flickering a creature triggers ETB effects again."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        # Create creature with ETB draw
        etb_creature = create_basic_creature(
            "Mulldrifter",
            power=2,
            toughness=2,
            oracle_text="When Mulldrifter enters the battlefield, draw two cards."
        )

        etb_trigger_count = [0]

        def etb_effect(board_state):
            etb_trigger_count[0] += 1
            board_state.draw_card(2, verbose=False)

        etb_creature.triggered_abilities = [
            TriggeredAbility(event="etb", effect=etb_effect)
        ]

        # Add creature to battlefield
        board.creatures.append(etb_creature)

        # Add cards to library for drawing
        for i in range(10):
            board.library.append(create_basic_creature(f"Card {i}"))

        # Flicker the creature
        flicker_permanent(board, etb_creature, 'immediate', verbose=False)

        # ETB should have triggered again
        assert etb_trigger_count[0] >= 1
        assert board.flicker_count == 1

    def test_flicker_resets_counters(self):
        """Test that flickering resets counters on creature."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        creature = create_basic_creature("Test Creature")
        creature.counters = {'+1/+1': 3}
        creature.power = 5  # Base 2 + 3 counters

        board.creatures.append(creature)

        # Flicker
        flicker_permanent(board, creature, 'immediate', verbose=False)

        # Counters should be reset
        assert creature.counters == {} or creature.counters.get('+1/+1', 0) == 0
        assert creature.power == creature.base_power


# =============================================================================
# COPY EFFECTS TESTS
# =============================================================================

class TestCopyEffects:
    """Test copy effects with Clone, Spark Double, Populate."""

    def test_detect_clone(self):
        """Test detection of Clone's copy ability."""
        oracle = "You may have Clone enter the battlefield as a copy of any creature on the battlefield."
        result = detect_copy_ability(oracle)
        assert result['has_copy'] is True
        assert result['copy_type'] == 'creature'
        assert result['is_etb'] is True

    def test_detect_spark_double(self):
        """Test detection of Spark Double's copy ability."""
        oracle = "You may have Spark Double enter the battlefield as a copy of a creature or planeswalker you control"
        result = detect_copy_ability(oracle)
        assert result['has_copy'] is True
        assert result['is_etb'] is True

    def test_detect_populate(self):
        """Test detection of Populate mechanic."""
        oracle = "Populate. (Create a token that's a copy of a creature token you control.)"
        result = detect_copy_ability(oracle)
        assert result['has_copy'] is True
        assert result['copy_type'] == 'token'
        assert result['makes_token'] is True

    def test_copy_creature_stats(self):
        """Test that copying a creature copies power/toughness."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        target = create_basic_creature("Big Creature", power=5, toughness=5)
        clone = create_basic_creature("Clone", power=0, toughness=0)

        board.creatures.append(target)

        # Copy the target
        copy_creature(board, clone, target, verbose=False)

        assert clone.power == 5
        assert clone.toughness == 5

    def test_copy_creature_keywords(self):
        """Test that copying copies keywords."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        target = create_basic_creature("Flying Creature", power=3, toughness=3)
        target.has_flying = True
        target.has_trample = True

        clone = create_basic_creature("Clone", power=0, toughness=0)

        copy_creature(board, clone, target, verbose=False)

        assert clone.has_flying is True
        assert clone.has_trample is True

    def test_create_token_copy(self):
        """Test creating token copies of creatures."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.tokens_created_this_turn = 0

        target = create_basic_creature("Token Target", power=4, toughness=4)
        target.has_haste = True

        board.creatures.append(target)

        # Create token copy
        create_token_copy(board, target, verbose=False)

        # Should have 2 creatures now (original + token)
        assert len(board.creatures) == 2
        assert board.tokens_created_this_turn >= 1


# =============================================================================
# MODAL SPELLS TESTS
# =============================================================================

class TestModalSpells:
    """Test modal spells with Cryptic Command, Boros Charm, Prismari Command."""

    def test_detect_cryptic_command(self):
        """Test detection of Cryptic Command's modal nature."""
        oracle = "Choose two — • Counter target spell. • Return target permanent to its owner's hand. • Tap all creatures your opponents control. • Draw a card."
        result = detect_modal_spell(oracle)
        assert result['is_modal'] is True
        assert result['modes_to_choose'] == 2
        assert result['num_modes'] == 4

    def test_detect_boros_charm(self):
        """Test detection of Boros Charm's modes."""
        oracle = "Choose one — • Boros Charm deals 4 damage to target player. • Permanents you control gain indestructible until end of turn. • Target creature gains double strike until end of turn."
        result = detect_modal_spell(oracle)
        assert result['is_modal'] is True
        assert result['modes_to_choose'] == 1
        assert result['num_modes'] == 3

    def test_detect_prismari_command(self):
        """Test detection of Prismari Command's modes."""
        oracle = "Choose two — • Prismari Command deals 2 damage to any target. • Target player draws two cards, then discards two cards. • Target player creates a Treasure token. • Destroy target artifact."
        result = detect_modal_spell(oracle)
        assert result['is_modal'] is True
        assert result['modes_to_choose'] == 2

    def test_evaluate_modal_choice_damage_priority(self):
        """Test that modal choice AI prioritizes damage in goldfish."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        modes = [
            "Deal 4 damage to target player",
            "Gain 4 life",
            "Create a 1/1 token"
        ]

        choices = evaluate_modal_choice(board, modes, 1)
        # Should pick damage or token creation over life gain
        assert 0 in choices or 2 in choices

    def test_execute_modal_draw(self):
        """Test executing a modal spell that draws cards."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        # Add cards to library
        for i in range(5):
            board.library.append(create_basic_creature(f"Card {i}"))

        initial_hand = len(board.hand)

        modal_card = create_instant_sorcery(
            "Modal Draw",
            oracle_text="Choose one — • Draw two cards. • Deal 3 damage."
        )

        execute_modal_spell(board, modal_card, [0], verbose=False)

        # Should have drawn cards
        assert len(board.hand) > initial_hand


# =============================================================================
# CASCADE / SUSPEND TESTS
# =============================================================================

class TestCascadeSuspend:
    """Test cascade/suspend with Bloodbraid Elf, Maelstrom Wanderer, Ancestral Vision."""

    def test_detect_cascade(self):
        """Test detection of cascade ability."""
        oracle = "Cascade (When you cast this spell, exile cards from the top of your library until you exile a nonland card that costs less. You may cast it without paying its mana cost. Put the exiled cards on the bottom in a random order.)"
        assert detect_cascade(oracle) is True

    def test_detect_suspend(self):
        """Test detection of suspend ability."""
        oracle = "Suspend 4—{U} (Rather than cast this card from your hand, pay {U} and exile it with four time counters on it. At the beginning of your upkeep, remove a time counter. When the last is removed, cast it without paying its mana cost.)"
        result = detect_suspend(oracle)
        assert result['has_suspend'] is True
        assert result['suspend_time'] == 4
        assert 'U' in result['suspend_cost'] or 'u' in result['suspend_cost'].lower()

    def test_resolve_cascade_finds_card(self):
        """Test that cascade finds and casts a lower CMC card."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        # Cascade card (CMC 4)
        bloodbraid = create_basic_creature(
            "Bloodbraid Elf",
            mana_cost="2RG",
            oracle_text="Cascade"
        )

        # Cards in library (mix of CMCs)
        board.library = [
            create_basic_creature("Land", mana_cost="", oracle_text=""),  # Land, skip
            create_basic_creature("High CMC", mana_cost="5UU"),  # CMC 7, too high
            create_basic_creature("Lightning Bolt", mana_cost="R"),  # CMC 1, valid!
        ]
        board.library[0].type = "Basic Land"

        cascade_result = resolve_cascade(board, bloodbraid, verbose=False)

        # Should have found Lightning Bolt
        assert cascade_result is not None
        assert cascade_result.name == "Lightning Bolt"
        assert board.cascade_casts == 1

    def test_suspend_card_and_process(self):
        """Test suspending a card and processing time counters."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        ancestral = create_instant_sorcery(
            "Ancestral Vision",
            card_type="Sorcery",
            mana_cost="",
            oracle_text="Suspend 4—{U}. Draw three cards.",
            draw_cards=3
        )

        board.hand.append(ancestral)

        # Suspend the card
        suspend_card(board, ancestral, 4, verbose=False)

        assert ancestral in board.exile
        assert len(board.suspended_cards) == 1
        assert board.suspended_cards[0]['time_counters'] == 4

        # Process 4 turns
        for _ in range(4):
            process_suspended_cards(board, verbose=False)

        # Card should have been cast
        assert len(board.suspended_cards) == 0


# =============================================================================
# PERSIST / UNDYING TESTS
# =============================================================================

class TestPersistUndying:
    """Test persist/undying with Kitchen Finks, Geralf's Messenger, Mikaeus."""

    def test_detect_persist(self):
        """Test detection of persist ability."""
        oracle = "Persist (When this creature dies, if it had no -1/-1 counters on it, return it to the battlefield under its owner's control with a -1/-1 counter on it.)"
        assert detect_persist(oracle) is True

    def test_detect_undying(self):
        """Test detection of undying ability."""
        oracle = "Undying (When this creature dies, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
        assert detect_undying(oracle) is True

    def test_persist_returns_creature(self):
        """Test that persist returns creature with -1/-1 counter."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        kitchen_finks = create_basic_creature(
            "Kitchen Finks",
            power=3,
            toughness=2,
            mana_cost="1WG",
            oracle_text="Persist"
        )
        kitchen_finks.base_power = 3
        kitchen_finks.base_toughness = 2
        kitchen_finks.counters = {}

        # Put in graveyard (simulating death)
        board.graveyard.append(kitchen_finks)

        # Handle death with persist
        result = handle_creature_death_persist_undying(board, kitchen_finks, verbose=False)

        assert result is True
        assert kitchen_finks in board.creatures
        assert kitchen_finks.counters.get('-1/-1', 0) == 1
        assert kitchen_finks.power == 2  # 3 - 1
        assert board.persist_triggers == 1

    def test_undying_returns_creature(self):
        """Test that undying returns creature with +1/+1 counter."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        messenger = create_basic_creature(
            "Geralf's Messenger",
            power=3,
            toughness=2,
            mana_cost="BBB",
            oracle_text="Undying"
        )
        messenger.base_power = 3
        messenger.base_toughness = 2
        messenger.counters = {}

        board.graveyard.append(messenger)

        result = handle_creature_death_persist_undying(board, messenger, verbose=False)

        assert result is True
        assert messenger in board.creatures
        assert messenger.counters.get('+1/+1', 0) == 1
        assert messenger.power == 4  # 3 + 1
        assert board.undying_triggers == 1

    def test_persist_does_not_trigger_with_counter(self):
        """Test that persist doesn't trigger if creature has -1/-1 counter."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        finks = create_basic_creature(
            "Kitchen Finks",
            oracle_text="Persist"
        )
        finks.counters = {'-1/-1': 1}  # Already has counter

        board.graveyard.append(finks)

        result = handle_creature_death_persist_undying(board, finks, verbose=False)

        assert result is False
        assert finks not in board.creatures


# =============================================================================
# CONVOKE / DELVE TESTS
# =============================================================================

class TestConvokeDelve:
    """Test convoke/delve with Stoke the Flames, Treasure Cruise, Hogaak."""

    def test_detect_convoke(self):
        """Test detection of convoke ability."""
        oracle = "Convoke (Your creatures can help cast this spell. Each creature you tap while casting this spell pays for {1} or one mana of that creature's color.)"
        assert detect_convoke(oracle) is True

    def test_detect_delve(self):
        """Test detection of delve ability."""
        oracle = "Delve (Each card you exile from your graveyard while casting this spell pays for {1}.)"
        assert detect_delve(oracle) is True

    def test_convoke_reduction(self):
        """Test that convoke correctly reduces costs."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        # Add 3 untapped creatures
        for i in range(3):
            c = create_basic_creature(f"Convoke Creature {i}")
            c.tapped = False
            board.creatures.append(c)

        stoke = create_instant_sorcery(
            "Stoke the Flames",
            mana_cost="2RR",
            oracle_text="Convoke. Deal 4 damage to any target."
        )

        reduction = board.creatures.__len__()  # 3 creatures = 3 reduction

        # Apply convoke
        actual = apply_convoke(board, stoke, 3, verbose=False)

        assert actual == 3
        # All creatures should be tapped
        for c in board.creatures:
            assert c.tapped is True

    def test_delve_reduction(self):
        """Test that delve correctly reduces costs."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        # Add 5 cards to graveyard
        for i in range(5):
            board.graveyard.append(create_basic_creature(f"Graveyard Card {i}"))

        cruise = create_instant_sorcery(
            "Treasure Cruise",
            mana_cost="7U",
            oracle_text="Delve. Draw three cards."
        )

        # Apply delve
        actual = apply_delve(board, cruise, 5, verbose=False)

        assert actual == 5
        assert len(board.graveyard) == 0
        assert len(board.exile) == 5

    def test_hogaak_both_mechanics(self):
        """Test card with both convoke and delve (Hogaak)."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        hogaak = create_basic_creature(
            "Hogaak, Arisen Necropolis",
            power=8,
            toughness=8,
            mana_cost="5BG",
            oracle_text="Convoke, delve. You can't spend mana to cast this spell."
        )

        # Add creatures and graveyard cards
        for i in range(3):
            c = create_basic_creature(f"Creature {i}")
            c.tapped = False
            board.creatures.append(c)

        for i in range(4):
            board.graveyard.append(create_basic_creature(f"GY Card {i}"))

        convoke_red = apply_convoke(board, hogaak, 3, verbose=False)
        delve_red = apply_delve(board, hogaak, 4, verbose=False)

        assert convoke_red == 3
        assert delve_red == 4
        # Total reduction = 7, which covers the CMC


# =============================================================================
# FLASH TIMING TESTS
# =============================================================================

class TestFlashTiming:
    """Test flash timing with Teferi, Dictate of Heliod, Venser."""

    def test_detect_flash_keyword(self):
        """Test detection of flash keyword."""
        oracle = "Flash. Flying."
        assert detect_flash(oracle) is True

    def test_detect_flash_in_keywords(self):
        """Test detection of flash in keywords list."""
        assert detect_flash("", keywords=['Flash', 'Flying']) is True

    def test_teferi_mage_of_zhalfir(self):
        """Test Teferi giving flash to creatures."""
        oracle = "Flash. Creature cards you own that aren't on the battlefield have flash."
        assert detect_flash(oracle) is True

    def test_dictate_of_heliod(self):
        """Test Dictate of Heliod has flash."""
        oracle = "Flash. Creatures you control get +2/+2."
        assert detect_flash(oracle) is True

    def test_venser_shaper_savant(self):
        """Test Venser has flash."""
        venser = create_basic_creature(
            "Venser, Shaper Savant",
            power=2,
            toughness=2,
            oracle_text="Flash. When Venser enters the battlefield, return target spell or permanent to its owner's hand."
        )
        venser.has_flash = True

        from extended_mechanics import can_cast_at_instant_speed
        assert can_cast_at_instant_speed(venser) is True


# =============================================================================
# FLASHBACK TESTS
# =============================================================================

class TestFlashback:
    """Test flashback with Faithless Looting, Deep Analysis, Lingering Souls."""

    def test_detect_faithless_looting(self):
        """Test detection of Faithless Looting flashback."""
        oracle = "Draw two cards, then discard two cards. Flashback {2}{R}"
        result = detect_flashback(oracle)
        assert result['has_flashback'] is True
        assert '2' in result['flashback_cost'] or 'R' in result['flashback_cost']

    def test_detect_deep_analysis(self):
        """Test detection of Deep Analysis flashback."""
        oracle = "Target player draws two cards. Flashback—{1}{U}, Pay 3 life."
        result = detect_flashback(oracle)
        assert result['has_flashback'] is True

    def test_detect_lingering_souls(self):
        """Test detection of Lingering Souls flashback."""
        oracle = "Create two 1/1 white Spirit creature tokens with flying. Flashback {1}{B}"
        result = detect_flashback(oracle)
        assert result['has_flashback'] is True

    def test_cast_flashback_from_graveyard(self):
        """Test casting a spell using flashback."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        looting = create_instant_sorcery(
            "Faithless Looting",
            card_type="Sorcery",
            mana_cost="R",
            oracle_text="Draw two cards, then discard two cards. Flashback {2}{R}",
            draw_cards=2
        )

        # Put in graveyard
        board.graveyard.append(looting)

        # Add cards to library for drawing
        for i in range(5):
            board.library.append(create_basic_creature(f"Card {i}"))

        # Cast with flashback
        result = cast_flashback(board, looting, verbose=False)

        assert result is True
        assert looting not in board.graveyard
        assert looting in board.exile  # Exiled after flashback
        assert board.flashback_casts == 1

    def test_flashback_exiles_card(self):
        """Test that flashback exiles the card after casting."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        spell = create_instant_sorcery(
            "FB Spell",
            oracle_text="Deal 3 damage. Flashback {3}{R}",
            deals_damage=3
        )

        board.graveyard.append(spell)
        cast_flashback(board, spell, verbose=False)

        assert spell in board.exile
        assert spell not in board.graveyard


# =============================================================================
# BUYBACK / RETRACE TESTS
# =============================================================================

class TestBuybackRetrace:
    """Test buyback/retrace with Capsize, Reiterate, Worm Harvest."""

    def test_detect_capsize(self):
        """Test detection of Capsize buyback."""
        oracle = "Buyback {3} (You may pay an additional {3} as you cast this spell. If you do, put this card into your hand as it resolves.) Return target permanent to its owner's hand."
        result = detect_buyback(oracle)
        assert result['has_buyback'] is True
        assert '3' in result['buyback_cost']

    def test_detect_reiterate(self):
        """Test detection of Reiterate buyback."""
        oracle = "Buyback {3} Copy target instant or sorcery spell. You may choose new targets for the copy."
        result = detect_buyback(oracle)
        assert result['has_buyback'] is True

    def test_detect_worm_harvest(self):
        """Test detection of Worm Harvest retrace."""
        oracle = "Create a 1/1 black and green Worm creature token for each land card in your graveyard. Retrace (You may cast this card from your graveyard by discarding a land card in addition to paying its other costs.)"
        assert detect_retrace(oracle) is True

    def test_cast_with_buyback_returns_to_hand(self):
        """Test that buyback returns spell to hand."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        capsize = create_instant_sorcery(
            "Capsize",
            mana_cost="1UU",
            oracle_text="Buyback {3}. Return target permanent to its owner's hand."
        )

        board.hand.append(capsize)

        result = cast_with_buyback(board, capsize, verbose=False)

        assert result is True
        assert capsize in board.hand  # Returned to hand
        assert board.buyback_casts == 1

    def test_cast_retrace_discards_land(self):
        """Test that retrace requires discarding a land."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        worm_harvest = create_instant_sorcery(
            "Worm Harvest",
            card_type="Sorcery",
            mana_cost="2BG",
            oracle_text="Retrace. Create tokens."
        )

        land = Card(
            name="Forest",
            type="Basic Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["G"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )

        board.graveyard.append(worm_harvest)
        board.hand.append(land)

        result = cast_retrace(board, worm_harvest, land, verbose=False)

        assert result is True
        assert land in board.graveyard
        assert land not in board.hand
        assert board.retrace_casts == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple mechanics."""

    def test_metrics_tracking(self):
        """Test that all extended metrics are tracked correctly."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        # Trigger various mechanics
        board.flicker_count = 2
        board.cascade_casts = 1
        board.persist_triggers = 3
        board.flashback_casts = 1

        metrics = get_extended_metrics(board)

        assert metrics['flicker_count'] == 2
        assert metrics['cascade_casts'] == 1
        assert metrics['persist_triggers'] == 3
        assert metrics['flashback_casts'] == 1

    def test_flicker_with_persist_creature(self):
        """Test flickering a creature with persist."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        initialize_extended_metrics(board)

        persist_creature = create_basic_creature(
            "Persist Flicker Target",
            power=3,
            toughness=3,
            oracle_text="Persist"
        )
        persist_creature.base_power = 3
        persist_creature.base_toughness = 3

        board.creatures.append(persist_creature)

        # Flicker should reset any -1/-1 counters
        persist_creature.counters = {'-1/-1': 1}
        persist_creature.power = 2

        flicker_permanent(board, persist_creature, 'immediate', verbose=False)

        # Counters should be reset by flicker
        assert persist_creature.counters.get('-1/-1', 0) == 0
        assert persist_creature.power == persist_creature.base_power


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
