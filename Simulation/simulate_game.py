import random
from math import isnan
from convert_dataframe_deck import parse_mana_cost
from boardstate import Mana_utils, BoardState
from mtg_abilities import ActivatedAbility
from draw_starting_hand import draw_starting_hand
from turn_phases import (
    setup_phase,
    untap_phase,
    upkeep_phase,
    draw_phase,
    main_phase,
    combat_phase,
    end_phase,
)


# ───────────────────────────────────────────────────────── Card ──
class Card:
    def __init__(
        self,
        name,
        type,
        mana_cost,
        power,
        toughness,
        produces_colors,
        mana_production,
        etb_tapped,
        etb_tapped_conditions,
        has_haste,
        has_flash=False,
        has_trample=False,
        equip_cost="",
        power_buff=0,
        is_commander=False,
        is_legendary=False,
        keywords_when_equipped=None,
        has_first_strike=False,
        puts_land=False,
        draw_cards=0,
        deals_damage=0,  # Direct damage dealt by instant/sorcery
        activated_abilities=None,
        triggered_abilities=None,
        oracle_text="",
        counters=None,
        creates_tokens=None,
        monarch_on_damage=False,
        x_value=0,
        fetch_basic=False,
        fetch_land_types=None,
        fetch_land_tapped=False,
        # New keywords
        has_lifelink=False,
        has_deathtouch=False,
        has_vigilance=False,
        has_flying=False,
        has_menace=False,
        is_unblockable=False,
        # Token types
        token_type=None,  # 'Treasure', 'Food', 'Clue', etc.
        # Saga
        is_saga=False,
        saga_chapters=None,
        # Cost reduction
        has_affinity=False,
        cost_reduction=0,
        # Sacrifice
        sacrifice_outlet=False,
        death_trigger_value=0,
    ):
        self.name = name
        self.type = type
        self.mana_cost = safe_cost_str(mana_cost)
        self.power = power
        self.toughness = toughness
        self.produces_colors = produces_colors
        self.mana_production = mana_production
        self.etb_tapped = etb_tapped
        self.etb_tapped_conditions = etb_tapped_conditions
        self.has_haste = has_haste
        self.has_flash = has_flash
        self.has_trample = has_trample
        self.is_commander = is_commander
        self.is_legendary = is_legendary
        self.keywords_when_equipped = keywords_when_equipped or []
        self.has_first_strike = has_first_strike
        self.equip_cost = safe_cost_str(equip_cost)
        self.power_buff = int(power_buff or 0)
        self.puts_land = bool(puts_land)
        self.draw_cards = int(draw_cards or 0)
        self.deals_damage = int(deals_damage or 0)  # Direct damage from spell
        self.activated_abilities: list[ActivatedAbility] = activated_abilities or []
        self.triggered_abilities: list = triggered_abilities or []
        self.oracle_text = oracle_text or ""
        self.counters = counters or {}
        self.creates_tokens = creates_tokens or []
        self.monarch_on_damage = bool(monarch_on_damage)
        self.x_value = int(x_value or 0)
        self.base_power = power
        self.base_toughness = toughness
        self.fetch_basic = bool(fetch_basic)
        self.fetch_land_types = fetch_land_types or []
        self.fetch_land_tapped = bool(fetch_land_tapped)

        # New keywords
        self.has_lifelink = has_lifelink
        self.has_deathtouch = has_deathtouch
        self.has_vigilance = has_vigilance
        self.has_flying = has_flying
        self.has_menace = has_menace
        self.is_unblockable = is_unblockable

        # Token types
        self.token_type = token_type

        # Saga
        self.is_saga = is_saga
        self.saga_chapters = saga_chapters or []
        self.saga_current_chapter = 0

        # Cost reduction
        self.has_affinity = has_affinity
        self.cost_reduction = cost_reduction

        # Sacrifice
        self.sacrifice_outlet = sacrifice_outlet
        self.death_trigger_value = death_trigger_value

    def add_counter(self, counter_type: str, amount: int = 1) -> None:
        """Add *amount* of *counter_type* counters to the card.

        Currently only ``"+1/+1"`` counters modify power and toughness.
        """
        self.counters[counter_type] = self.counters.get(counter_type, 0) + amount
        if counter_type == "+1/+1":
            self.power = (self.power or 0) + amount
            self.toughness = (self.toughness or 0) + amount

    def remove_counter(self, counter_type: str, amount: int = 1) -> bool:
        """Remove up to *amount* of *counter_type* counters from the card.

        Returns ``True`` if any counters were removed.
        """
        current = self.counters.get(counter_type, 0)
        if current <= 0:
            return False

        remove = min(amount, current)
        self.counters[counter_type] = current - remove
        if self.counters[counter_type] <= 0:
            self.counters.pop(counter_type, None)

        if counter_type == "+1/+1":
            self.power = (self.power or 0) - remove
            self.toughness = (self.toughness or 0) - remove
        return True

    def take_damage(self, amount: int) -> int:
        """Mark combat damage on this card and return the damage dealt."""

        if self.toughness is None:
            return amount
        dealt = min(amount, self.toughness)
        self.toughness -= dealt
        return dealt


def clean_produces_colors(value):
    import math

    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.lower() == "any":
            return ["Any"]
        # If comma-separated
        if "," in value:
            return [v.strip().upper() for v in value.split(",") if v.strip()]
        # BoardState.Handle known 2-color combos (like RW, GW, RG, etc.)
        if value.isalpha() and len(value) in [2, 3]:
            return list(value.upper())
        if value.isalpha() and len(value) == 1:
            return [value.upper()]
        return [value]
    if isinstance(value, (list, tuple)):
        return list(value)
    return [str(value)]


def safe_cost_str(cost):
    if cost is None or (isinstance(cost, float) and isnan(cost)):
        return ""
    return str(cost)


def simulate_game(deck_cards, commander_card, max_turns=10, verbose=True):
    """
    Simulates a game with the given deck and commander card.
    Args:
        deck_cards (list): List of ``Card`` objects representing the deck.
        commander_card (Card): The commander card to be used in the game.
        max_turns (int): Maximum number of turns to simulate.
        verbose (bool): If ``True`` prints a detailed turn by turn log.
    Returns:
        dict: A dictionary containing various metrics of the game simulation.
        When ``verbose`` is ``True`` the function also prints a turn by turn
        summary of all actions taken.
    """

    # Initialize board state
    board = BoardState(deck_cards, commander_card)
    board.lands_untapped, board.lands_tapped = [], []  # type: ignore
    board.hand = []
    board.library = deck_cards[:]

    random.shuffle(board.library)
    board.hand, board.library = draw_starting_hand(board.library, commander_card)

    crits = []
    commander_done = False
    metrics = {
        k: [0] * (max_turns + 1)
    for k in (
            "lands_played",
            "total_mana",
            "castable_spells",
            "combat_damage",
            "drain_damage",  # NEW: Track aristocrats drain damage separately
            "unspent_mana",
            "commander_cast_turn",
            "mana_spent",
            "ramp_cards_played",
            "cards_played",
            "hand_size",
            "unplayable_cards",
            "played_card_names",
            "hand_size",
            "non_land_cards",
            "castable_non_lands",
            "uncastable_non_lands",
            "total_power",
            "total_toughness",
            "power_from_counters",
            "lands_etb_tapped",
            "opponents_alive",
            "opponent_total_power",
            "creatures_in_graveyard",
            "tokens_created",  # NEW: Track token generation
            "creatures_sacrificed",  # NEW: Track sacrifice outlets
            "spells_cast",  # SPELLSLINGER: Storm count
            "spell_damage",  # SPELLSLINGER: Damage from cast triggers
            "prowess_creatures",  # SPELLSLINGER: Number of prowess creatures
            "creatures_reanimated_turn",  # REANIMATOR: Creatures reanimated this turn
            "graveyard_creature_power",  # REANIMATOR: Total power in graveyard
            "cards_discarded",  # REANIMATOR: Cards discarded for value
            "proliferate_triggers",  # COUNTERS: Proliferate triggers this turn
            "total_counters_on_creatures",  # COUNTERS: Total +1/+1 counters on creatures
            "ozolith_stored_counters",  # COUNTERS: Counters stored on The Ozolith
            "cards_drawn",  # DECK POTENTIAL: Total cards drawn this turn
            "life_gained",  # DECK POTENTIAL: Life gained this turn
            "life_lost",  # DECK POTENTIAL: Life lost/paid this turn
        )
    }

    # Track new interaction metrics
    metrics["creatures_removed_by_opponents"] = 0  # type: ignore
    metrics["board_wipes_survived"] = 0  # type: ignore
    metrics["creatures_reanimated_total"] = 0  # type: ignore
    metrics["game_won"] = None  # type: ignore

    # Track colour-specific mana availability
    COLOURS = ["W", "U", "B", "R", "G", "C", "Any"]
    for col in COLOURS:
        metrics[f"board_mana_{col}"] = [0] * (max_turns + 1)
        metrics[f"hand_mana_{col}"] = [0] * (max_turns + 1)

    def _count_pool(pool):
        counts = {c: 0 for c in COLOURS}
        for src in pool:
            if "Any" in src:
                counts["Any"] += 1
            else:
                for c in src:
                    counts[c] += 1
        return counts

    def _count_hand_lands(hand):
        counts = {c: 0 for c in COLOURS}
        for card in hand:
            if 'Land' in card.type:
                cols = card.produces_colors or ["C"]
                if "Any" in cols:
                    counts["Any"] += 1
                else:
                    for c in cols:
                        counts[c] += 1
        return counts

    metrics["creature_power"] = {}  # type: ignore

    metrics["commander_cast_turn"] = None  # type: ignore
    metrics["cards_played"] = [0] * (max_turns + 1)
    metrics["played_card_names"] = [[] for _ in range(max_turns + 1)]  # type: ignore

    for turn in range(1, max_turns + 1):
        board.turn = turn  # Update turn number in board state
        board.turn_play_count = 0  # Reset play count for this turn
        board.turn_casts = []  # Reset cast list for this turn
        board.lands_played_this_turn = 0  # Reset land plays for this turn
        board.landfall_triggers_this_turn = 0  # Reset landfall triggers

        # PRIORITY FIX P1: Reset Muldrotha graveyard casts for new turn
        board.muldrotha_casts_this_turn = {
            'creature': False,
            'artifact': False,
            'enchantment': False,
            'land': False,
            'planeswalker': False
        }

        # PRIORITY FIX P2: Reset Meren end-step trigger for new turn
        board.meren_triggered_this_turn = False

        if verbose:
            print(f"\n=== Turn {turn} ===")

        # At the start of each turn, move last turn's tapped lands to untapped
        untap_phase(board, verbose=verbose)

        # ---- upkeep phase: sagas + upkeep triggers ----
        upkeep_tokens = upkeep_phase(board, verbose=verbose)
        metrics["tokens_created"][turn] += upkeep_tokens

        # ---- draw phase: draw a card ----
        drawn = draw_phase(board, verbose=verbose)

        # Track cards drawn this turn
        metrics["cards_drawn"][turn] = len(drawn) if drawn else 0

        if verbose and drawn:
            print("Drawn:", ", ".join(c.name for c in drawn))
        if verbose:
            print("Hand:", ", ".join(c.name for c in board.hand) or "Empty")
        if (
            turn == 1
            and "sol ring" in [c.name.lower() for c in board.hand]
            and "arcane signet" in [c.name.lower() for c in board.hand]
        ):
            print(
                "Sol Ring and arcane signet found in starting hand "
                + str([c.name.lower() for c in board.hand]),
                str([c.mana_production for c in board.hand]),
            )

        # --- metrics after draw step before playing a land ---
        metrics["hand_size"][turn] = len(board.hand)
        non_lands = [c for c in board.hand if 'Land' not in c.type]
        metrics["non_land_cards"][turn] = len(non_lands)
        pre_pool = board.mana_sources_from_board(
            board.lands_untapped,
            board.artifacts,
            board.creatures,
        )
        castable_now = 0
        for c in non_lands:
            if Mana_utils.can_pay(c.mana_cost, pre_pool):
                castable_now += 1
        metrics["castable_non_lands"][turn] = castable_now
        metrics["uncastable_non_lands"][turn] = len(non_lands) - castable_now
        # ---- play ONE land (use simple heuristics for selection) ----

        best_land = board.choose_land_to_play()

        if best_land:
            board.play_card(best_land, verbose=verbose)
            metrics["lands_played"][turn] = metrics["lands_played"][turn - 1] + 1
            metrics["lands_etb_tapped"][turn] = (
                metrics["lands_etb_tapped"][turn - 1] + (1 if getattr(best_land, "tapped", False) else 0)
            )
        else:
            metrics["lands_played"][turn] = metrics["lands_played"][turn - 1]
            metrics["lands_etb_tapped"][turn] = metrics["lands_etb_tapped"][turn - 1]

        # Record hand size after playing a land
        metrics["hand_size"][turn] = len(board.hand)

        hand_counts = _count_hand_lands(board.hand)
        for col in COLOURS:
            metrics[f"hand_mana_{col}"][turn] = hand_counts[col]

        # ----- record mana pool BEFORE any spell casting -----
        pool_start = board.mana_sources_from_board(
            board.lands_untapped,
            board.artifacts,
            board.creatures,
        )
        metrics["total_mana"][turn] = len(pool_start)
        pool_counts = _count_pool(pool_start)
        for col in COLOURS:
            metrics[f"board_mana_{col}"][turn] = pool_counts[col]

        # Calculate how many spells are currently castable with this mana
        castable = 0
        if not commander_done:
            cols, gen = Mana_utils.parse_req(commander_card.mana_cost)
            cost_str = (str(gen) if gen > 0 else "") + "".join(cols)
            if Mana_utils.can_pay(cost_str, pool_start):
                castable += 1
        for c in board.hand:
            if 'Land' in c.type:
                continue
            if Mana_utils.can_pay(c.mana_cost, pool_start):
                castable += 1
        metrics["castable_spells"][turn] = castable

        # Count unplayable cards given current mana pool
        unplayable = 0
        for c in board.hand:
            if 'Land' in c.type:
                continue
            if not Mana_utils.can_pay(c.mana_cost, pool_start):
                unplayable += 1
        metrics["unplayable_cards"][turn] = unplayable

        # ---- main-phase: play all possible mana rocks and then commander ----
        pool = list(pool_start)
        board.mana_pool = pool

        mana_spent_this_turn = 0
        ramp_this_turn = 0
        # if turn >= 9 and not commander_done:
        #     print(list(c.name for c in board.hand), 'board.hand at turn', turn, 'without casting commander - ', pool, 'Mana pool')
        # Main-phase greedy loop: always try to play ALL rocks and commander as soon as enough mana
        # ---- main-phase greedy loop ------------------------------------
        while True:
            did_action = False

            commander_cost_str = safe_cost_str(commander_card.mana_cost)
            # --- 1) try to play ALL mana rocks without delaying commander ----------
            played_rock_this_pass = True
            while played_rock_this_pass:
                played_rock_this_pass = False
                can_cast_cmd_now = not commander_done and Mana_utils.can_pay(
                    commander_cost_str, board.mana_pool
                )

                for c in board.hand[:]:  # iterate over copy
                    if (
                        "Artifact" in c.type
                        and c.mana_production > 0
                        and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
                    ):

                        # simulate pool after playing c
                        sim_pool = board.mana_pool.copy()
                        Mana_utils.pay(c.mana_cost, sim_pool)
                        sim_pool.extend(
                            [("C",)] * c.mana_production
                            if c.name.lower() == "sol ring"
                            else [("Any",)] * c.mana_production
                        )

                        if (not can_cast_cmd_now) or Mana_utils.can_pay(
                            commander_cost_str, sim_pool
                        ):
                            if board.play_card(c, verbose=verbose):
                                ramp_this_turn += 1
                                board.mana_pool = sim_pool
                                if verbose:
                                    spent = parse_mana_cost(c.mana_cost)
                                    print(f"Spent {spent} mana on {c.name}")
                                    print(f"{c.name} produced {c.mana_production} mana")
                                mana_spent_this_turn += parse_mana_cost(c.mana_cost)
                                played_rock_this_pass = True
                                break  # restart while-loop with fresh hand copy

            # 2) try commander as soon as we can pay
            if not commander_done and Mana_utils.can_pay(
                commander_cost_str, board.mana_pool
            ):

                if board.play_card(commander_card, verbose=verbose):

                    commander_done = True
                    mana_spent_this_turn += parse_mana_cost(commander_card.mana_cost)
                    if verbose:
                        spent = parse_mana_cost(commander_card.mana_cost)
                        print(f"Spent {spent} mana on {commander_card.name}")
                    metrics["commander_cast_turn"] = turn
                    crits.append(commander_card)
                    # auto-equip any available equipment to commander
                    for eq in [
                        e
                        for e in board.artifacts
                        if "Equipment" in e.type and e not in board.equipment_attached
                    ]:
                        if Mana_utils.can_pay(eq.equip_cost, board.mana_pool):
                            if board.equip_equipment(
                                eq, commander_card, verbose=verbose
                            ):
                                mana_spent_this_turn += parse_mana_cost(eq.equip_cost)
                    metrics["creature_power"][commander_card.name] = int(
                        commander_card.power or 0
                    )
                    did_action = True
                    continue  # restart loop to see if we can play more

            # 3) play a ramp sorcery that puts a land into play
            ramp_spell = next(
                (
                    c
                    for c in board.hand
                    if "Sorcery" in c.type
                    and getattr(c, "puts_land", False)
                    and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
                ),
                None,
            )
            if ramp_spell:
                if board.play_card(ramp_spell, verbose=verbose):
                    ramp_this_turn += 1
                    if verbose:
                        spent = parse_mana_cost(ramp_spell.mana_cost)
                        print(f"Spent {spent} mana on {ramp_spell.name}")
                    did_action = True
                    continue

            # 4) play first castable creature (with AI decision-making)
            creature = next(
                (
                    c
                    for c in board.hand
                    if "Creature" in c.type
                    and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
                ),
                None,
            )
            if creature:
                # AI: Check if we should hold back this creature
                if board.should_hold_back_creature(creature, verbose=verbose):
                    did_action = False
                    break  # Don't play this creature, move to next phase

                if board.play_card(creature, verbose=verbose):
                    if creature.mana_production and int(creature.mana_production) > 0:
                        ramp_this_turn += 1
                    mana_spent_this_turn += parse_mana_cost(creature.mana_cost)
                    if verbose:
                        spent = parse_mana_cost(creature.mana_cost)
                        print(f"Spent {spent} mana on {creature.name}")
                    crits.append(creature)
                    # attempt to equip available equipments to this creature
                    for eq in [
                        e
                        for e in board.artifacts
                        if "Equipment" in e.type and e not in board.equipment_attached
                    ]:
                        if Mana_utils.can_pay(eq.equip_cost, board.mana_pool):
                            if board.equip_equipment(eq, creature, verbose=verbose):
                                mana_spent_this_turn += parse_mana_cost(eq.equip_cost)
                    metrics["creature_power"][creature.name] = int(creature.power or 0)
                    did_action = True
                    continue

            # PRIORITY FIX P1: Try Muldrotha graveyard casting if on board
            if board.muldrotha_on_board:
                muldrotha_casts = board.attempt_muldrotha_casts(verbose=verbose)
                if muldrotha_casts > 0:
                    if verbose:
                        print(f"♻️  Muldrotha enabled {muldrotha_casts} casts from graveyard")
                    did_action = True
                    continue

            # PRIORITY FIX P2: Try Gravecrawler recursion if we have a zombie
            if board.attempt_gravecrawler_cast(verbose=verbose):
                did_action = True
                continue

            # 4) play a piece of equipment and attach to first creature
            equipment = next(
                (
                    c
                    for c in board.hand
                    if "Equipment" in c.type
                    and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
                    and board.creatures
                ),
                None,
            )
            if equipment:
                if board.play_card(equipment, verbose=verbose):
                    mana_spent_this_turn += parse_mana_cost(equipment.mana_cost)
                    if verbose:
                        spent = parse_mana_cost(equipment.mana_cost)
                        print(f"Spent {spent} mana on {equipment.name}")
                    target = board.creatures[0]
                    if board.equip_equipment(equipment, target, verbose=verbose):
                        mana_spent_this_turn += parse_mana_cost(equipment.equip_cost)
                        if verbose:
                            cost = parse_mana_cost(equipment.equip_cost)
                            print(f"Equip cost {cost} for {equipment.name}")
                    metrics["creature_power"][target.name] = int(target.power or 0)
                    did_action = True
                    continue

            # nothing else to do → exit while
            if not did_action:
                break
        # --------------- end while --------------------------------------

        # After main phase, try to equip any remaining equipment if possible
        for eq in [
            e
            for e in board.artifacts
            if "Equipment" in e.type and e not in board.equipment_attached
        ]:
            if board.creatures and Mana_utils.can_pay(eq.equip_cost, board.mana_pool):
                if board.equip_equipment(eq, board.creatures[0], verbose=verbose):
                    mana_spent_this_turn += parse_mana_cost(eq.equip_cost)
                    if verbose:
                        cost = parse_mana_cost(eq.equip_cost)
                        print(f"Equip cost {cost} for {eq.name}")
                    metrics["creature_power"][board.creatures[0].name] = int(
                        board.creatures[0].power or 0
                    )

        # ----- AI: Optimize leftover mana usage -----
        # Try to use any floating mana before end of turn
        board.optimize_mana_usage(verbose=verbose)

        # ----- after casting, record unspent mana and spells cast -----
        metrics["unspent_mana"][turn] = len(pool)
        metrics["cards_played"][turn] = board.turn_play_count
        metrics["played_card_names"][turn] = board.cards_played_this_turn()
        metrics["mana_spent"][turn] = mana_spent_this_turn
        metrics["ramp_cards_played"][turn] = (
            metrics["ramp_cards_played"][turn - 1] + ramp_this_turn
        )
        metrics["unspent_mana"][turn] = len(board.mana_pool)

        # ─────────────────── GOLDFISH MODE: Opponents Disabled ───────────────────
        # Opponent generation disabled for deck potential measurement
        # This measures what the deck CAN DO, not realistic game simulation
        # board.generate_opponent_creatures(turn, verbose=verbose)
        # board.calculate_threat_levels()

        # Attempt reanimation if there are targets
        if board.reanimation_targets:
            board.attempt_reanimation(verbose=verbose)

        # Activate planeswalkers
        for pw in board.planeswalkers:
            board.activate_planeswalker(pw, verbose=verbose)

        # Reset per-turn tracking
        board.drain_damage_this_turn = 0
        board.tokens_created_this_turn = 0
        board.creatures_died_this_turn = 0  # PRIORITY 2: For Mahadi
        board.life_gained_this_turn = 0
        board.life_lost_this_turn = 0

        # SPELLSLINGER: Track spells cast this turn
        metrics["spells_cast"][turn] = board.spells_cast_this_turn
        metrics["spell_damage"][turn] = board.spell_damage_this_turn

        # Count prowess creatures
        prowess_count = 0
        for creature in board.creatures:
            oracle = getattr(creature, 'oracle_text', '').lower()
            if 'prowess' in oracle or 'magecraft' in oracle:
                prowess_count += 1
        metrics["prowess_creatures"][turn] = prowess_count

        # REANIMATOR: Track reanimation and graveyard value
        metrics["creatures_reanimated_turn"][turn] = board.creatures_reanimated_this_turn
        metrics["creatures_reanimated_total"] = board.creatures_reanimated
        metrics["cards_discarded"][turn] = board.cards_discarded_for_value

        # Calculate total power in graveyard (reanimation targets)
        graveyard_power = sum(
            getattr(c, 'power', 0) or 0
            for c in board.graveyard
            if 'creature' in getattr(c, 'type', '').lower()
        )
        metrics["graveyard_creature_power"][turn] = graveyard_power

        # Reset per-turn counters for next turn
        board.spells_cast_this_turn = 0
        board.spell_damage_this_turn = 0
        board.creatures_reanimated_this_turn = 0
        board.reset_prowess_bonuses()  # Prowess lasts until end of turn

        # Simulate opponent removal (before combat)
        board.simulate_removal(verbose=verbose)

        # ARISTOCRATS: Check for sacrifice opportunities before combat
        sacs = board.check_for_sacrifice_opportunities(verbose=verbose)
        metrics["creatures_sacrificed"][turn] += sacs

        # ---- BEGINNING OF COMBAT: Trigger beginning of combat effects ----
        combat_start_tokens = board.process_beginning_of_combat_triggers(verbose=verbose)
        metrics["tokens_created"][turn] += combat_start_tokens

        # ARISTOCRATS: Trigger attack-based token generation (Adeline, Anim Pakal)
        if board.creatures:
            tokens = board.simulate_attack_triggers(verbose=verbose)
            metrics["tokens_created"][turn] += tokens

        # trigger attack abilities for all creatures (assuming they attack)
        for creature in board.creatures:
            board._execute_triggers("attack", creature, verbose)

        # ─────────────────── GOLDFISH MODE: Unblocked Combat ───────────────────
        # In goldfish mode, all creatures attack and deal full damage (no blockers)
        # This measures deck's damage potential
        total_combat_damage = 0
        for creature in board.creatures:
            # Initialize turns on board tracking if needed
            if not hasattr(creature, '_turns_on_board'):
                creature._turns_on_board = 0

            # Only creatures without summoning sickness can attack
            can_attack = creature.has_haste or creature._turns_on_board >= 1

            if can_attack:
                power = getattr(creature, 'power', 0) or 0
                total_combat_damage += power
                if verbose:
                    print(f"    → {creature.name} attacks for {power} damage (turns_on_board={creature._turns_on_board})")

            # Increment turns on board for all creatures (not just attackers)
            creature._turns_on_board += 1

        if verbose and total_combat_damage > 0:
            print(f"Combat: {total_combat_damage} damage dealt (goldfish mode - no blockers)")

        metrics["combat_damage"][turn] = total_combat_damage

        # ARISTOCRATS: Track drain damage separately!
        metrics["drain_damage"][turn] = board.drain_damage_this_turn
        if verbose and board.drain_damage_this_turn > 0:
            print(f"💀 Drain damage this turn: {board.drain_damage_this_turn}")

        # DECK POTENTIAL: Track life metrics
        metrics["life_gained"][turn] = board.life_gained_this_turn
        metrics["life_lost"][turn] = board.life_lost_this_turn

        # Goldfish mode: No opponents, no board wipes
        # board.simulate_board_wipe(verbose=verbose)

        # PRIORITY 2: End-of-turn treasure generation (Mahadi, etc.)
        # PRIORITY FIX P2: Meren end-step reanimation trigger
        if board.meren_on_board:
            board.meren_end_step_trigger(verbose=verbose)

        board.check_end_of_turn_treasures(board.creatures_died_this_turn, verbose=verbose)

        # MOBILIZE: Sacrifice mobilize warrior tokens at end of turn
        mobilize_sacs = board.sacrifice_mobilize_tokens(verbose=verbose)
        metrics["creatures_sacrificed"][turn] += mobilize_sacs

        # COUNTER MANIPULATION: Check for proliferate triggers
        board.check_for_proliferate_triggers(verbose=verbose)

        # COUNTER MANIPULATION: Try to move Ozolith counters to a creature
        if board.ozolith_counters and board.creatures:
            # Move Ozolith counters to the biggest creature
            best_target = max(board.creatures, key=lambda c: (c.power or 0) + (c.toughness or 0))
            board.move_ozolith_counters_to_creature(best_target, verbose=verbose)

        # COUNTER MANIPULATION: Track counter metrics
        metrics["proliferate_triggers"][turn] = board.proliferate_this_turn

        # Count total +1/+1 counters on all creatures
        total_counters = sum(
            getattr(c, 'counters', {}).get('+1/+1', 0)
            for c in board.creatures
        )
        metrics["total_counters_on_creatures"][turn] = total_counters

        # Track Ozolith stored counters
        ozolith_total = sum(board.ozolith_counters.values())
        metrics["ozolith_stored_counters"][turn] = ozolith_total

        # Reset proliferate counter for next turn
        board.proliferate_this_turn = 0

        # ─────────────────── NEW: Track Interaction Metrics ───────────────────
        metrics["opponents_alive"][turn] = sum(1 for opp in board.opponents if opp['is_alive'])
        metrics["opponent_total_power"][turn] = sum(
            sum(c.power or 0 for c in opp['creatures'])
            for opp in board.opponents if opp['is_alive']
        )
        metrics["creatures_in_graveyard"][turn] = len(board.graveyard)
        metrics["creatures_removed_by_opponents"] = board.creatures_removed
        metrics["board_wipes_survived"] = board.wipes_survived

        # PRIORITY 3: total creature power/toughness including anthem bonuses
        metrics["total_power"][turn] = sum(
            board.get_effective_power(c) for c in board.creatures
        )
        metrics["total_toughness"][turn] = sum(
            board.get_effective_toughness(c) for c in board.creatures
        )
        metrics["power_from_counters"][turn] = sum(
            int(getattr(c, "counters", {}).get("+1/+1", 0)) for c in board.creatures
        )


        if verbose:
            print("Played:", ", ".join(metrics["played_card_names"][turn]) or "None")
            print(
                f"Mana spent: {mana_spent_this_turn} | Unspent: {metrics['unspent_mana'][turn]}"
            )
            print(f"Combat damage: {metrics['combat_damage'][turn]}")
            print("-" * 30)

    return metrics
