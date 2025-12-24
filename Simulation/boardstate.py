from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ActivatedAbility:
    """Simple representation of an activated ability."""

    source: Any
    cost: str = ""
    effect: Callable[["BoardState"], Any] | None = None
    taps: bool = True
    usable: bool = True


class BoardState:
    def __init__(self, deck, commander, num_opponents=3):
        self.library = list(deck)
        self.hand = []
        self.graveyard = []
        self.exile = []
        self.lands_untapped = []
        self.lands_tapped = []
        self.artifacts = []
        self.creatures = []
        self.enchantments = []
        self.planeswalkers = []
        self.commander = commander
        self.command_zone = [commander]
        self.mana_pool = []
        self.turn_play_count = 0           # resets each new turn
        self.total_play_count = 0          # cumulative
        self.play_log: list[tuple[int, str]] = []  # (turn, card)
        self.turn_casts: list[Any] = []    # cards cast this turn
        self.turn = 1
        self.life_total = 40  # Commander starts at 40 life

        # Mapping of equipment to the creature it is attached to
        self.equipment_attached = {}

        # For triggers
        self.triggers = []    # List of Trigger objects (see below)
        self.pending_effects = []  # Other effects/stack, optional

        # Activated abilities currently usable
        self.available_abilities: list[ActivatedAbility] = []

        # Track the most recently damaged creature for damage triggers
        self.last_damaged_creature = None

        # Monarch tracking
        self.monarch = False
        self.monarch_trigger_turn = 0

        # Combat tracking
        self.current_attackers: list[Any] = []
        self.current_combat_turn = 0
        self._attack_triggers_fired: set[tuple[int, int]] = set()

        # Mobilize tracking - warriors to sacrifice at end of turn
        self.mobilize_tokens: list[Any] = []

        # Opponent modeling (for multiplayer Commander)
        self.num_opponents = num_opponents
        self.opponents = []
        for i in range(num_opponents):
            self.opponents.append({
                'name': f'Opponent_{i+1}',
                'life_total': 40,
                'creatures': [],
                'commander_damage': 0,
                'is_alive': True,
                'threat_level': 0.0,  # 0-1 scale
            })

        # Interaction tracking - Base rates (Option A: Reduced for more realistic gameplay)
        self.base_removal_probability = 0.05  # 5% chance per turn (down from 15%)
        self.base_board_wipe_probability = 0.03  # 3% chance per turn (down from 8%)

        # Option B & C: Strategy-aware adjustment
        deck_analysis = self._analyze_deck_strategy(deck)
        self.deck_archetype = deck_analysis['archetype']
        self.protection_count = deck_analysis['protection_count']

        # Apply archetype-based modifiers
        self.removal_probability = self.base_removal_probability * deck_analysis['removal_modifier']
        self.board_wipe_probability = self.base_board_wipe_probability * deck_analysis['wipe_modifier']

        # Synergy-aware AI: Check if commander has detailed archetype info
        self.archetype_priorities = {}
        self.primary_archetype = None
        self.secondary_archetype = None
        if hasattr(commander, 'deck_archetype') and commander.deck_archetype:
            archetype_data = commander.deck_archetype
            self.archetype_priorities = archetype_data.get('priorities', {})
            self.primary_archetype = archetype_data.get('primary_archetype', None)
            self.secondary_archetype = archetype_data.get('secondary_archetype', None)
            if self.primary_archetype:
                # Override the basic deck_archetype with the detected one for better accuracy
                self.deck_archetype = self.primary_archetype

        self.wipes_survived = 0
        self.creatures_removed = 0
        self.reanimation_targets = []  # Creatures that died and could be reanimated

        # AI decision-making
        self.hold_back_removal = True  # Don't always cast removal immediately
        self.threat_threshold = 15  # Don't overextend if opponent power is high
        self.removal_spells = []  # Track removal spells in hand
        self.instant_spells = []  # Track instant-speed spells for reactive play

        # Tribal effects tracking
        self.chosen_creature_types = {}  # Map of card name -> chosen creature type
        self.tribal_buffs = []  # List of active tribal buff effects
        self.tribal_triggers = []  # List of tribal triggered abilities

        # Command Tax tracking
        self.commander_cast_count = 0  # Times commander has been cast
        self.command_tax = 0  # Additional mana cost ({2} per previous cast)

        # Combat keywords and modifiers
        self.damage_multiplier = 1.0  # For damage doublers like Fiery Emancipation
        self.token_multiplier = 1  # For token doublers like Doubling Season

        # Cost reduction (Phase 3)
        self.cost_reduction = 0  # Generic cost reduction
        self.affinity_count = 0  # Artifacts for affinity
        self.spell_cost_reduction = 0  # Instant/sorcery cost reduction
        self.creature_cost_reduction = 0  # Creature cost reduction

        # Sacrifice tracking
        self.creatures_sacrificed = 0
        self.sacrifice_value = 0  # Total power sacrificed

        # Aristocrats mechanics tracking
        self.drain_damage_this_turn = 0  # Track drain separate from combat
        self.tokens_created_this_turn = 0  # Track token generation
        self.creatures_died_this_turn = 0  # PRIORITY 2: For Mahadi treasure generation

        # Life tracking for deck potential metrics
        self.life_gained_this_turn = 0  # Life gained this turn
        self.life_lost_this_turn = 0  # Life lost/paid this turn

        # Landfall mechanics tracking
        self.lands_played_this_turn = 0  # Track lands played this turn
        self.landfall_triggers_this_turn = 0  # Track number of landfall triggers

        # Spellslinger mechanics tracking
        self.spells_cast_this_turn = 0  # Storm count
        self.instant_sorcery_cast_this_turn = 0  # For cast triggers
        self.spell_damage_this_turn = 0  # Damage from cast triggers (Guttersnipe, etc.)
        self.prowess_bonus = {}  # Track prowess creatures: {creature: bonus}

        # Tap/Untap engine tracking
        self.untap_triggers = []  # List of untap effects (Jeskai Ascendancy, Seedborn Muse, etc.)
        self.tap_for_value_effects = []  # Effects that trigger when creatures tap

        # Trigger doubling tracking (Panharmonicon, Yarok, Veyran)
        self.trigger_multiplier = 1  # Default 1x, Panharmonicon/Yarok = 2x
        self.magecraft_multiplier = 1  # Default 1x, Veyran = 2x for magecraft/prowess

        # Spell copy tracking
        self.spell_copies_this_turn = 0  # Track spell copies created
        self.copy_effects = []  # List of copy effect sources

        # Anthem effects tracking (global +1/+1 bonuses)
        self.global_power_bonus = 0  # Global +X/+0
        self.global_toughness_bonus = 0  # Global +0/+X
        self.tribal_anthems = {}  # {creature_type: (power_bonus, toughness_bonus)}

        # Extra combat tracking (Phase 2)
        self.extra_combats_this_turn = 0  # Number of extra combats granted
        self.combats_taken_this_turn = 0  # Number of combats already taken

        # Card draw triggers tracking (Phase 2)
        self.draw_triggers = []  # List of "when you draw" effects
        self.cards_drawn_this_turn = 0  # Track draws for Niv-Mizzet, etc.

        # Energy counters (Phase 3)
        self.energy_counters = 0  # Energy counter pool
        self.energy_gained_this_turn = 0  # Track energy generation

        # Reanimator mechanics tracking
        self.creatures_reanimated = 0  # Total creatures brought back from graveyard
        self.creatures_reanimated_this_turn = 0  # For per-turn tracking
        self.cards_discarded_for_value = 0  # Discard outlets like Faithless Looting

        # Counter manipulation mechanics tracking
        self.proliferate_count = 0  # Total proliferate triggers
        self.proliferate_this_turn = 0  # Proliferate triggers this turn
        self.ozolith_counters = {}  # Stored counters from dead creatures (The Ozolith)
        self.counters_moved_to_ozolith = 0  # Total counters moved to Ozolith
        self.total_counters_on_creatures = 0  # Total +1/+1 counters on all creatures

        # Syr Konrad, the Grim tracking (PRIORITY FIX: +100-150 damage)
        self.syr_konrad_on_board = False  # Is Syr Konrad on the battlefield?
        self.syr_konrad_triggers_this_turn = 0  # Number of triggers this turn

        # Muldrotha, the Gravetide tracking (PRIORITY FIX P1: +10-15 casts)
        self.muldrotha_on_board = False  # Is Muldrotha on the battlefield?
        self.muldrotha_casts_this_turn = {
            'creature': False,
            'artifact': False,
            'enchantment': False,
            'land': False,
            'planeswalker': False
        }

        # Meren of Clan Nel Toth tracking (PRIORITY FIX P2: +5-7 reanimates)
        self.meren_on_board = False  # Is Meren on the battlefield?
        self.experience_counters = 0  # Experience counters for Meren
        self.meren_triggered_this_turn = False  # Has Meren's end step triggered this turn?

        # Y'shtola, Night's Blessed tracking
        self.yshtola_on_board = False  # Is Y'shtola, Night's Blessed on the battlefield?


    def _apply_equipped_keywords(self, creature):
        equipped = creature in self.equipment_attached.values()

        # Check equipment oracle text for keywords granted
        if equipped:
            for equipment, attached_creature in self.equipment_attached.items():
                if attached_creature is creature:
                    oracle = getattr(equipment, 'oracle_text', '').lower()
                    # Grant keywords from equipment
                    if 'double strike' in oracle:
                        creature.has_double_strike = True
                    if 'first strike' in oracle and 'double strike' not in oracle:
                        creature.has_first_strike = True
                    if 'vigilance' in oracle:
                        creature.has_vigilance = True
                    if 'trample' in oracle:
                        creature.has_trample = True

        # Apply keywords_when_equipped (legacy support)
        for kw in getattr(creature, "keywords_when_equipped", []):
            if kw.lower() == "first strike":
                creature.has_first_strike = bool(equipped)
            elif kw.lower() == "double strike":
                creature.has_double_strike = bool(equipped)

    def _analyze_deck_strategy(self, deck):
        """
        Analyze deck composition to detect archetype and adjust interaction rates.

        Options B & C: Strategy-aware simulation with archetype detection.

        Returns dict with:
            - archetype: Detected deck strategy
            - removal_modifier: Multiplier for removal probability (lower = fewer removals)
            - wipe_modifier: Multiplier for board wipe probability
            - protection_count: Number of protection spells detected
        """
        equipment_count = 0
        creature_count = 0
        protection_count = 0
        token_generators = 0
        go_wide_count = 0

        # Protection spell keywords to detect
        protection_keywords = [
            'hexproof', 'indestructible', 'protection from',
            'heroic intervention', 'clever concealment', 'teferi\'s protection',
            'boros charm', 'flawless maneuver', 'unbreakable formation',
            'mithril coat', 'lightning greaves', 'swiftfoot boots'
        ]

        for card in deck:
            card_type = getattr(card, 'type', '').lower()
            oracle_text = getattr(card, 'oracle_text', '').lower()
            name = getattr(card, 'name', '').lower()

            # Count equipment
            if 'equipment' in card_type:
                equipment_count += 1

            # Count creatures
            if 'creature' in card_type:
                creature_count += 1

            # Detect protection spells
            for keyword in protection_keywords:
                if keyword in oracle_text or keyword in name:
                    protection_count += 1
                    break

            # Detect token generators (go-wide strategy)
            if 'create' in oracle_text and 'token' in oracle_text:
                token_generators += 1

            # Detect anthems and +1/+1 effects (go-wide)
            if ('get +' in oracle_text or 'gets +' in oracle_text) and 'creatures you control' in oracle_text:
                go_wide_count += 1

        total_cards = len(deck)
        equipment_ratio = equipment_count / total_cards if total_cards > 0 else 0
        creature_ratio = creature_count / total_cards if total_cards > 0 else 0

        # Determine archetype
        archetype = 'unknown'
        removal_modifier = 1.0  # Default: use base rates
        wipe_modifier = 1.0

        # Voltron/Equipment deck (lots of equipment, few creatures)
        if equipment_ratio > 0.12 and creature_ratio < 0.25:
            archetype = 'voltron'
            # Voltron decks have fewer creatures, so removals hurt more
            # But they often run protection, so reduce removal significantly
            removal_modifier = 0.4  # 60% reduction (5% -> 2%)
            wipe_modifier = 0.5  # 50% reduction (3% -> 1.5%)

        # Go-wide/Token deck (many token generators)
        elif token_generators >= 5 or go_wide_count >= 3:
            archetype = 'go_wide'
            # Go-wide cares less about single removals, more about wipes
            removal_modifier = 1.2  # Slightly more removals
            wipe_modifier = 0.8  # But fewer wipes (they have board presence)

        # Creature-heavy aggro (lots of creatures, few equipment)
        elif creature_ratio > 0.30 and equipment_ratio < 0.08:
            archetype = 'aggro'
            removal_modifier = 1.0  # Standard rates
            wipe_modifier = 0.9

        # Midrange (balanced)
        elif creature_ratio > 0.20 and creature_ratio < 0.35:
            archetype = 'midrange'
            removal_modifier = 0.9
            wipe_modifier = 0.9

        # Combo/Control (few creatures)
        elif creature_ratio < 0.15:
            archetype = 'combo_control'
            # Combo decks don't care much about creature removal
            removal_modifier = 0.5
            wipe_modifier = 0.6

        # Apply protection spell bonus (each protection spell reduces removal)
        if protection_count > 0:
            protection_bonus = 0.9 ** protection_count  # Each spell reduces by 10%
            removal_modifier *= protection_bonus
            wipe_modifier *= protection_bonus

        return {
            'archetype': archetype,
            'removal_modifier': removal_modifier,
            'wipe_modifier': wipe_modifier,
            'protection_count': protection_count,
            'equipment_count': equipment_count,
            'creature_count': creature_count
        }

    def _mana_pool_str(self) -> str:
        """Return a readable representation of the current mana pool."""
        return ", ".join("".join(m) for m in self.mana_pool) or "Empty"

    

    @staticmethod
    def parse_mana_cost(cost_str):
        """
        Helper to parse a mana cost string like '2WG' or '3' into a total mana value (converted mana cost).
        For simplicity, each numeric character adds that number, and each letter (color) adds 1.
        """
        if cost_str is None:
            return 0
        total = 0
        num_buffer = ''
        for ch in cost_str:
            if ch.isdigit():
                # accumulate multi-digit numbers
                num_buffer += ch
            else:
                # if there was a number before a letter, add it
                if num_buffer:
                    total += int(num_buffer)
                    num_buffer = ''
                if ch.isalpha():
                    # each colored mana symbol counts as 1 towards total cost
                    total += 1
        # If string ended in a number (unlikely in mana costs), add it
        if num_buffer:
            total += int(num_buffer)
        return total

    def _add_abilities_from_card(self, card):
        """Add any activated abilities from *card* to the available list."""
        for ability in getattr(card, "activated_abilities", []):
            ability.source = card
            ability.usable = True
            if getattr(ability, "requires_equipped", False) and card not in self.equipment_attached:
                ability.usable = False
            if ability not in self.available_abilities:
                self.available_abilities.append(ability)

    def get_trigger_multiplier(self, event: str, card) -> int:
        """
        Get the trigger multiplier based on Panharmonicon, Yarok, Veyran, etc.

        Returns number of times to execute trigger (1, 2, or more).
        """
        multiplier = 1

        # Check for Panharmonicon (doubles artifact/creature ETB triggers)
        for artifact in self.artifacts:
            name = getattr(artifact, 'name', '').lower()
            if 'panharmonicon' in name:
                if event == 'etb':
                    card_type = getattr(card, 'type', '').lower()
                    if 'creature' in card_type or 'artifact' in card_type:
                        multiplier = 2
                        break

        # Check for Yarok (doubles permanents ETB triggers)
        for creature in self.creatures:
            name = getattr(creature, 'name', '').lower()
            if 'yarok' in name:
                if event == 'etb':
                    multiplier = 2
                    break

        # Check for Veyran (doubles magecraft/prowess triggers from spells)
        for creature in self.creatures:
            name = getattr(creature, 'name', '').lower()
            if 'veyran' in name:
                # Veyran doubles triggers from casting spells
                # This is handled separately in magecraft_multiplier
                pass

        return multiplier

    def _execute_triggers(self, event: str, card, verbose=False):
        """Execute triggered abilities on *card* that match *event*.

        The engine recognises events such as ``"etb"`` (enters the
        battlefield), ``"equip"`` when an equipment becomes attached, and
        ``"attack"`` whenever a creature attacks.
        """
        # Get trigger multiplier (Panharmonicon, Yarok, etc.)
        multiplier = self.get_trigger_multiplier(event, card)

        for trig in getattr(card, "triggered_abilities", []):
            if trig.event != event:
                continue

            if event == "attack":
                if getattr(trig, "requires_haste", False) and not getattr(card, "has_haste", False):
                    continue
                if getattr(trig, "requires_flash", False) and not getattr(card, "has_flash", False):
                    continue
                if getattr(trig, "requires_another_legendary", False):
                    others = [
                        c
                        for c in self.current_attackers
                        if c is not card and getattr(c, "is_legendary", False)
                    ]
                    if not others:
                        continue
                key = (id(card), id(trig))
                if key in self._attack_triggers_fired:
                    continue

            if verbose and trig.description:
                if multiplier > 1:
                    print(f"Trigger on {card.name}: {trig.description} (x{multiplier} from doubler)")
                else:
                    print(f"Trigger on {card.name}: {trig.description}")

            # Execute trigger multiplier times
            for i in range(multiplier):
                trig.effect(self)

            if event == "attack":
                key = (id(card), id(trig))
                self._attack_triggers_fired.add(key)

        # Check for global triggers (Kindred Discovery, etc.)
        if event == "etb" and 'Creature' in getattr(card, 'type', ''):
            self._check_kindred_discovery_etb(card, verbose)
        elif event == "attack":
            self._check_kindred_discovery_attack(card, verbose)

    def _check_kindred_discovery_etb(self, creature, verbose=False):
        """Check if Kindred Discovery should trigger when a creature enters."""
        for permanent in self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # GENERIC: "Choose a creature type. Whenever a creature of that type enters or attacks, draw a card"
            if 'choose a creature type' in oracle and 'enters or attacks' in oracle and 'draw a card' in oracle:
                # Simplified: Assume the chosen type matches (tribal decks)
                # In a real implementation, we'd track the chosen type
                self.draw_card(1, verbose=verbose)
                if verbose:
                    print(f"  → {permanent.name} triggers: Draw a card ({creature.name} entered)")

    def _check_kindred_discovery_attack(self, creature, verbose=False):
        """Check if Kindred Discovery should trigger when a creature attacks."""
        for permanent in self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # GENERIC: "Choose a creature type. Whenever a creature of that type enters or attacks, draw a card"
            if 'choose a creature type' in oracle and 'enters or attacks' in oracle and 'draw a card' in oracle:
                # Simplified: Assume the chosen type matches (tribal decks)
                self.draw_card(1, verbose=verbose)
                if verbose:
                    print(f"  → {permanent.name} triggers: Draw a card ({creature.name} attacked)")

    def deal_damage(self, creature, amount: int, verbose: bool = False) -> int:
        """Deal ``amount`` of damage to ``creature`` and handle damage triggers.

        Returns the actual damage marked on the creature after reduction.
        """

        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return 0

        dealt = creature.take_damage(amount)
        self.last_damaged_creature = creature

        battlefield = (
            self.lands_untapped
            + self.lands_tapped
            + self.creatures
            + self.artifacts
            + self.enchantments
            + self.planeswalkers
        )

        for permanent in battlefield:
            self._execute_triggers("damage", permanent, verbose)

        self.last_damaged_creature = None
        return dealt

    def combat_damage_to_player(self, creature, damage: int, verbose: bool = False) -> int:
        """Record combat damage dealt by *creature* to a player.

        Some spells or effects set ``monarch_trigger_turn`` for the current
        turn, causing the controller to become the monarch when combat damage
        is dealt. Returns the damage dealt for convenience.
        """

        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return 0

        if self.monarch_trigger_turn == self.turn:
            self.monarch = True

        if verbose:
            print(f"{creature.name} dealt {damage} damage to a player.")

        return damage

    def _process_special_etb_effects(self, card, verbose: bool = False):
        """
        Process special ETB effects for specific cards.

        Handles cards like:
        - Avenger of Zendikar (create plant tokens equal to lands)
        - Omnath, Locus of the Roil (ETB counter on elemental + damage)
        """
        oracle = getattr(card, 'oracle_text', '').lower()
        name = getattr(card, 'name', '').lower()

        # === AVENGER OF ZENDIKAR ===
        if 'avenger of zendikar' in name:
            # ETB: Create plant tokens equal to number of lands
            total_lands = len(self.lands_untapped) + len(self.lands_tapped)

            if total_lands > 0:
                for _ in range(total_lands):
                    # Create 0/1 Plant tokens
                    self.create_token("Plant", 0, 1, has_haste=False,
                                    apply_counters=True, verbose=False)

                if verbose:
                    print(f"  → Avenger of Zendikar created {total_lands} Plant tokens!")

        # === OMNATH, LOCUS OF THE ROIL (ETB) ===
        elif 'omnath, locus of the roil' in name or 'omnath, locus of roil' in name:
            # ETB: Put +1/+1 counter on target Elemental, that Elemental deals damage
            self.handle_omnath_roil_landfall(verbose=verbose)

        # === CLOUD, EX-SOLDIER ===
        # "When Cloud enters, attach up to one target Equipment you control to it."
        elif 'cloud' in name and 'ex-soldier' in name:
            # Find unattached equipment
            unattached_equipment = [eq for eq in self.artifacts if 'equipment' in getattr(eq, 'type', '').lower() and eq not in self.equipment_attached]
            if unattached_equipment:
                # Choose the best equipment (highest power buff)
                best_equipment = max(unattached_equipment, key=lambda eq: int(getattr(eq, 'power_buff', 0) or 0))
                # Attach without paying cost
                buff = int(getattr(best_equipment, "power_buff", 0) or 0)
                card.power = int(getattr(card, 'power', 0) or 0) + buff
                card.toughness = int(getattr(card, 'toughness', 0) or 0) + buff
                self.equipment_attached[best_equipment] = card
                self._apply_equipped_keywords(card)
                if verbose:
                    print(f"  → Cloud's ETB: Attached {best_equipment.name} to Cloud")

        # PRIORITY FIX (P1): ETB MILL TRIGGERS (Stitcher's Supplier, Eccentric Farmer, etc.)
        mill_value = getattr(card, 'mill_value', 0)
        if mill_value > 0 and 'enters' in oracle:
            self.mill_cards(mill_value, verbose=verbose)

    def _trigger_landfall(self, verbose: bool = False) -> None:
        """Execute all "landfall" triggers for permanents you control.

        Called whenever a land enters the battlefield under your control.
        Iterates over all permanents currently on the battlefield (including
        the land that just entered) and runs any triggered abilities whose
        event is ``"landfall"``.
        """
        self.landfall_triggers_this_turn += 1

        # First, process specific landfall card effects
        self.process_landfall_triggers(verbose=verbose)

        # Then, execute any custom triggered abilities
        battlefield = (
            self.lands_untapped
            + self.lands_tapped
            + self.creatures
            + self.artifacts
            + self.enchantments
            + self.planeswalkers
        )

        for permanent in battlefield:
            self._execute_triggers("landfall", permanent, verbose)

    def add_counters_with_doubling(self, permanent, counter_type: str, amount: int = 1, verbose: bool = False) -> int:
        """
        Add counters to a permanent, checking for counter doublers.

        This handles counter doublers like:
        - Hardened Scales: If you would put +1/+1 counters, put that many plus one
        - Branching Evolution: If you would put counters, put twice that many
        - Doubling Season: If you would put counters, put twice that many

        Returns the actual number of counters added.
        """
        if amount <= 0:
            return 0

        actual_amount = amount

        # Check for counter doublers on the battlefield
        for doubler in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(doubler, 'oracle_text', '').lower()
            doubler_name = getattr(doubler, 'name', '').lower()

            # Hardened Scales: +1/+1 counters get +1
            if 'hardened scales' in doubler_name or (
                'if you would put one or more +1/+1 counter' in oracle and 'put that many plus one' in oracle
            ):
                if counter_type == "+1/+1":
                    actual_amount += 1
                    if verbose:
                        print(f"  → {doubler.name}: +1/+1 counters increased by 1")

            # Branching Evolution / Doubling Season: Double all counters
            elif 'branching evolution' in doubler_name or 'doubling season' in doubler_name or (
                'if you would put one or more counter' in oracle and 'twice that many' in oracle
            ):
                actual_amount *= 2
                if verbose:
                    print(f"  → {doubler.name}: Counters doubled!")

            # Vorinclex, Monstrous Raider: Double counters you put
            elif 'vorinclex' in doubler_name and 'monstrous raider' in doubler_name:
                actual_amount *= 2
                if verbose:
                    print(f"  → {doubler.name}: Counters doubled!")

        # Actually add the counters
        if hasattr(permanent, 'add_counter'):
            permanent.add_counter(counter_type, actual_amount)
        elif hasattr(permanent, 'counters'):
            # Fallback for cards without add_counter method
            permanent.counters[counter_type] = permanent.counters.get(counter_type, 0) + actual_amount

        return actual_amount

    def proliferate(self, verbose: bool = False) -> int:
        """
        Give each permanent with counters another of each kind.

        Returns the total number of counters added.
        """
        battlefield = (
            self.lands_untapped
            + self.lands_tapped
            + self.creatures
            + self.artifacts
            + self.enchantments
            + self.planeswalkers
        )

        total_counters_added = 0

        for permanent in battlefield:
            counters = getattr(permanent, "counters", {})
            for ctype, amount in list(counters.items()):
                if amount > 0:
                    # Use the doubling-aware method
                    added = self.add_counters_with_doubling(permanent, ctype, 1, verbose=False)
                    total_counters_added += added
                    if verbose:
                        print(f"  → {permanent.name} proliferates {added} {ctype} counter(s)")

        # Track proliferate count
        self.proliferate_count += 1
        self.proliferate_this_turn += 1

        if verbose and total_counters_added > 0:
            print(f"✨ Proliferate added {total_counters_added} total counters!")

        return total_counters_added

    def _apply_global_effects(self, creature):
        """Apply global effects from artifacts and enchantments to a creature."""
        # Calculate anthem and lord bonuses
        power_bonus, toughness_bonus = self.calculate_anthem_bonuses(creature)

        # Store bonuses (these are temporary and recalculated each time)
        if not hasattr(creature, '_anthem_power'):
            creature._anthem_power = 0
        if not hasattr(creature, '_anthem_toughness'):
            creature._anthem_toughness = 0

        creature._anthem_power = power_bonus
        creature._anthem_toughness = toughness_bonus

        # Check for Akroma's Memorial - grants flying, first strike, vigilance, trample, haste, protection
        for permanent in self.artifacts + self.enchantments:
            name = getattr(permanent, 'name', '').lower()
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # Akroma's Memorial
            if 'akroma' in name and 'memorial' in name:
                creature.has_flying = True
                creature.has_first_strike = True
                creature.has_vigilance = True
                creature.has_trample = True
                creature.has_haste = True
                creature.has_protection_black = True
                creature.has_protection_red = True

            # Generic global effects: "creatures you control have [keyword]"
            if 'creatures you control have' in oracle or 'creatures you control get' in oracle:
                if 'flying' in oracle:
                    creature.has_flying = True
                if 'first strike' in oracle and 'double strike' not in oracle:
                    creature.has_first_strike = True
                if 'double strike' in oracle:
                    creature.has_double_strike = True
                if 'vigilance' in oracle:
                    creature.has_vigilance = True
                if 'trample' in oracle:
                    creature.has_trample = True
                if 'haste' in oracle:
                    creature.has_haste = True
                if 'lifelink' in oracle:
                    creature.has_lifelink = True

    def calculate_anthem_bonuses(self, creature):
        """
        Calculate global +X/+X bonuses from anthems and tribal lords.

        Returns (power_bonus, toughness_bonus).
        """
        power_bonus = self.global_power_bonus
        toughness_bonus = self.global_toughness_bonus

        # Check tribal anthems
        creature_types = getattr(creature, 'type', '').lower()
        for tribe_type, (p_bonus, t_bonus) in self.tribal_anthems.items():
            if tribe_type in creature_types:
                power_bonus += p_bonus
                toughness_bonus += t_bonus

        # Check for anthem effects from permanents
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Skip the creature itself
            if permanent is creature:
                continue

            # Intangible Virtue: Tokens get +1/+1
            if ('intangible virtue' in name) or ('token creatures you control get +1/+1' in oracle):
                if getattr(creature, 'is_token', False):
                    power_bonus += 1
                    toughness_bonus += 1

            # Spear of Heliod: Creatures you control get +1/+1
            if ('spear of heliod' in name) or ('creatures you control get +1/+1' in oracle):
                if 'creature' in creature_types:
                    power_bonus += 1
                    toughness_bonus += 1

            # Tribal lords (e.g., "Elf creatures you control get +1/+1")
            import re
            tribal_lord_pattern = r'(\w+) creatures you control get \+(\d+)/\+(\d+)'
            match = re.search(tribal_lord_pattern, oracle)
            if match:
                tribe = match.group(1).lower()
                p_boost = int(match.group(2))
                t_boost = int(match.group(3))
                if tribe in creature_types:
                    power_bonus += p_boost
                    toughness_bonus += t_boost

            # Generic anthem ("Creatures you control get +X/+X")
            generic_anthem_pattern = r'creatures you control get \+(\d+)/\+(\d+)'
            match = re.search(generic_anthem_pattern, oracle)
            if match:
                p_boost = int(match.group(1))
                t_boost = int(match.group(2))
                if 'creature' in creature_types:
                    power_bonus += p_boost
                    toughness_bonus += t_boost

        return (power_bonus, toughness_bonus)

    def attack(self, creature, verbose=False):
        """Declare *creature* as an attacker and handle attack triggers."""
        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return False

        # Check if creature is already tapped
        if getattr(creature, 'tapped', False):
            if verbose:
                print(f"{creature.name} is already tapped and cannot attack.")
            return False

        # Check if creature has vigilance (doesn't tap to attack)
        has_vigilance = getattr(creature, 'has_vigilance', False)

        if self.current_combat_turn != self.turn:
            self.current_combat_turn = self.turn
            self.current_attackers = []
            self._attack_triggers_fired.clear()

        self.current_attackers.append(creature)

        # Tap creature unless it has vigilance
        if not has_vigilance:
            creature.tapped = True
            if verbose:
                print(f"{creature.name} tapped to attack")

        self._apply_equipped_keywords(creature)
        self._apply_global_effects(creature)
        for atk in list(self.current_attackers):
            self._execute_triggers("attack", atk, verbose)
        return True

    def grant_extra_combat(self, verbose=False):
        """
        Grant an additional combat phase this turn.

        Used by: Combat Celebrant, Aggravated Assault, Relentless Assault, etc.
        """
        self.extra_combats_this_turn += 1
        if verbose:
            print(f"Granted extra combat phase (total: {self.extra_combats_this_turn})")

        return True

    def has_extra_combats_remaining(self):
        """Check if there are extra combat phases remaining this turn."""
        return self.combats_taken_this_turn < (1 + self.extra_combats_this_turn)

    def start_combat_phase(self, verbose=False):
        """Start a combat phase (tracks combat count for extra combats)."""
        self.combats_taken_this_turn += 1

        if verbose:
            combat_num = self.combats_taken_this_turn
            if combat_num == 1:
                print(f"=== Combat Phase ===")
            else:
                print(f"=== Extra Combat Phase #{combat_num - 1} ===")

    def detect_and_grant_extra_combats(self, verbose=False):
        """
        Detect cards that grant extra combats and apply them.

        Called after main combat phase.
        """
        extra_combats_granted = 0

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Combat Celebrant: Exert to take extra combat (once per turn)
            if 'combat celebrant' in name:
                # Check if we can exert (not exerted yet)
                if not getattr(permanent, 'exerted_this_turn', False):
                    self.grant_extra_combat(verbose=verbose)
                    permanent.exerted_this_turn = True
                    extra_combats_granted += 1
                    if verbose:
                        print(f"  → {permanent.name} exerted for extra combat")

            # Aggravated Assault: Pay mana for extra combat (simplified: once per turn if mana available)
            if 'aggravated assault' in name:
                # Simplified: If we have 5+ mana, take extra combat once
                if len(self.mana_pool) >= 5 and not getattr(permanent, 'activated_this_turn', False):
                    # Pay mana (simplified)
                    for _ in range(min(5, len(self.mana_pool))):
                        if self.mana_pool:
                            self.mana_pool.pop(0)
                    self.grant_extra_combat(verbose=verbose)
                    permanent.activated_this_turn = True
                    extra_combats_granted += 1
                    if verbose:
                        print(f"  → {permanent.name} activated for extra combat")

            # Relentless Assault / Seize the Day / World at War: One-shot extra combat
            if ('relentless assault' in name) or ('seize the day' in name) or ('world at war' in name):
                # These are instants/sorceries that grant extra combat when cast
                # This would be handled during spell casting, not here
                pass

        return extra_combats_granted

    def tap_creature(self, creature, verbose=False):
        """Tap a creature and trigger any tap-for-value effects."""
        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return False

        if getattr(creature, 'tapped', False):
            if verbose:
                print(f"{creature.name} is already tapped.")
            return False

        creature.tapped = True
        if verbose:
            print(f"Tapped {creature.name}")

        # Trigger any "when creature taps" effects
        for effect in self.tap_for_value_effects:
            effect(creature, verbose)

        return True

    def untap_creature(self, creature, verbose=False):
        """Untap a creature."""
        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return False

        if not getattr(creature, 'tapped', False):
            if verbose:
                print(f"{creature.name} is already untapped.")
            return False

        creature.tapped = False
        if verbose:
            print(f"Untapped {creature.name}")

        return True

    def untap_all_creatures(self, verbose=False):
        """Untap all creatures. Used for Seedborn Muse, etc."""
        count = 0
        for creature in self.creatures:
            if getattr(creature, 'tapped', False):
                creature.tapped = False
                count += 1

        if verbose and count > 0:
            print(f"Untapped {count} creatures")

        return count

    def trigger_on_spell_cast_untaps(self, spell, verbose=False):
        """Trigger untap effects when a noncreature spell is cast (Jeskai Ascendancy, etc.)."""
        # Check for Jeskai Ascendancy
        for enchantment in self.enchantments:
            oracle = getattr(enchantment, 'oracle_text', '').lower()
            name = getattr(enchantment, 'name', '').lower()

            if 'jeskai ascendancy' in name:
                # Untap all creatures
                count = self.untap_all_creatures(verbose=verbose)
                if verbose and count > 0:
                    print(f"  → Jeskai Ascendancy: Untapped {count} creatures")

                # +1/+1 until end of turn (tracked in prowess_bonus)
                for creature in self.creatures:
                    current_bonus = self.prowess_bonus.get(creature, 0)
                    self.prowess_bonus[creature] = current_bonus + 1

        # Check for other untap engines
        for artifact in self.artifacts:
            name = getattr(artifact, 'name', '').lower()

            if 'paradox engine' in name:
                # Untap all nonland permanents
                count = self.untap_all_creatures(verbose=verbose)
                if verbose and count > 0:
                    print(f"  → Paradox Engine: Untapped {count} creatures")

    def get_spell_copies(self, spell, verbose=False):
        """
        Get the number of times to copy a spell.

        Checks for copy effects like:
        - Fork (copies target instant/sorcery)
        - Dualcaster Mage (ETB copy target instant/sorcery)
        - Thousand-Year Storm (copy for each spell cast before it)
        - Swarm Intelligence (copy first instant/sorcery each turn)
        """
        num_copies = 0
        card_type = getattr(spell, 'type', '').lower()

        # Only copy instants and sorceries
        if 'instant' not in card_type and 'sorcery' not in card_type:
            return 0

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Thousand-Year Storm: Copy for each spell cast before it this turn
            if 'thousand-year storm' in name:
                copies = self.spells_cast_this_turn - 1  # Don't count current spell
                if copies > 0:
                    num_copies += copies
                    if verbose:
                        print(f"  → Thousand-Year Storm: Copying {copies} times")

            # Swarm Intelligence: Copy first instant/sorcery each turn
            if 'swarm intelligence' in name:
                if not getattr(permanent, '_copied_this_turn', False):
                    num_copies += 1
                    permanent._copied_this_turn = True
                    if verbose:
                        print(f"  → Swarm Intelligence: Copying spell")

            # Pyromancer's Goggles: Copy instant/sorcery if R paid
            if 'pyromancer' in name and 'goggles' in name:
                # Simplified: If we have mana, copy once per turn
                if not getattr(permanent, '_copied_this_turn', False) and len(self.mana_pool) > 0:
                    num_copies += 1
                    permanent._copied_this_turn = True
                    if verbose:
                        print(f"  → Pyromancer's Goggles: Copying spell")

        # Track total copies
        self.spell_copies_this_turn += num_copies

        return num_copies

    def resolve_spell_copy(self, spell, x_value=0, verbose=False):
        """
        Resolve a copy of a spell.

        Copies do NOT trigger cast effects (no Guttersnipe damage, etc.)
        but DO resolve their effects (damage, card draw, tokens, etc.)
        """
        oracle = getattr(spell, 'oracle_text', '').lower()

        # Card draw
        if getattr(spell, "draw_cards", 0) > 0:
            self.draw_card(getattr(spell, "draw_cards"), verbose=verbose)

        # Direct damage
        damage = getattr(spell, "deals_damage", 0)
        if damage > 0:
            self.spell_damage_this_turn += damage
            alive_opps = [opp for opp in self.opponents if opp['life_total'] > 0]
            if alive_opps:
                target_opp = alive_opps[0]
                target_opp['life_total'] -= damage
                if target_opp['life_total'] <= 0:
                    target_opp['is_alive'] = False
                if verbose:
                    print(f"    Copy deals {damage} damage to {target_opp['name']}")

        # Token creation
        if oracle and "create" in oracle and "token" in oracle:
            import re
            m_token = re.search(
                r"create (?P<num>x|\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (?P<stats>\d+/\d+)?[^.]*tokens?",
                oracle,
            )
            if m_token:
                num_map = {
                    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3,
                    "four": 4, "five": 5, "six": 6, "seven": 7,
                    "eight": 8, "nine": 9, "ten": 10, "x": x_value if x_value else 1,
                }
                val = m_token.group("num")
                token_count = num_map.get(val, int(val) if val.isdigit() else 1)
                stats = m_token.group("stats") if m_token.group("stats") else "1/1"

                keywords = []
                if "haste" in oracle:
                    keywords.append("haste")
                if "flying" in oracle:
                    keywords.append("flying")

                self.create_tokens(token_count, stats, keywords=keywords, verbose=verbose)
                if verbose:
                    print(f"    Copy created {token_count} {stats} token(s)")

        # Wheel effects
        if 'discard' in oracle and 'hand' in oracle and 'draw' in oracle:
            # Wheel of Fortune style: discard hand, draw 7
            if 'each player' in oracle or 'all players' in oracle or 'your hand' in oracle:
                self.wheel_effect(7, verbose=verbose)

        # Extra turn (INFINITE COMBO ALERT!)
        if 'extra turn' in oracle or 'another turn' in oracle:
            if verbose:
                print(f"    ⚠️  INFINITE COMBO DETECTED: Spell copy + extra turn!")
            # Don't actually take infinite turns in simulation (would hang)
            # Mark as infinite combo instead
            self.spell_damage_this_turn += 999  # Effectively a win

    def calculate_cost_reduction(self, card, verbose=False):
        """
        Calculate cost reduction for a spell.

        Checks for cost reducers like:
        - Goblin Electromancer (instant/sorcery cost {1} less)
        - Jace's Sanctum (instant/sorcery cost {1} less)
        - Animar (creature cost {1} less per counter)
        - Affinity (artifacts reduce cost)
        """
        reduction = 0
        card_type = getattr(card, 'type', '').lower()

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Goblin Electromancer: Instant/sorcery cost {1} less
            if ('goblin electromancer' in name) or ('instant and sorcery spells you cast cost' in oracle):
                if 'instant' in card_type or 'sorcery' in card_type:
                    reduction += 1
                    if verbose:
                        print(f"  → {permanent.name}: -{reduction} cost")

            # Jace's Sanctum: Instant/sorcery cost {1} less
            if 'jace' in name and 'sanctum' in name:
                if 'instant' in card_type or 'sorcery' in card_type:
                    reduction += 1

            # Baral, Chief of Compliance: Instant/sorcery cost {1} less
            if ('baral' in name) or ('instant and sorcery spells you cast cost {1} less' in oracle):
                if 'instant' in card_type or 'sorcery' in card_type:
                    reduction += 1

            # Animar: Creature spells cost {1} less per counter
            if 'animar' in name:
                if 'creature' in card_type:
                    counters = getattr(permanent, 'counters', {}).get('+1/+1', 0)
                    reduction += counters
                    if verbose and counters > 0:
                        print(f"  → Animar: -{counters} cost ({counters} counters)")

            # Primal Amulet / Primal Wellspring: Generic cost reduction
            if 'primal' in name and ('amulet' in name or 'wellspring' in name):
                if 'instant' in card_type or 'sorcery' in card_type:
                    reduction += 1

        # Affinity for artifacts
        if 'affinity for artifacts' in getattr(card, 'oracle_text', '').lower():
            artifact_count = len(self.artifacts)
            reduction += artifact_count
            if verbose and artifact_count > 0:
                print(f"  → Affinity: -{artifact_count} cost ({artifact_count} artifacts)")

        return reduction

    def gain_energy(self, amount, verbose=False):
        """
        Gain energy counters.

        Used by: Aether Hub, Glimmer of Genius, Harnessed Lightning, etc.
        """
        self.energy_counters += amount
        self.energy_gained_this_turn += amount
        if verbose:
            print(f"Gained {amount} energy (total: {self.energy_counters})")

        return amount

    def spend_energy(self, amount, verbose=False):
        """
        Spend energy counters.

        Returns True if successful, False if not enough energy.
        """
        if self.energy_counters >= amount:
            self.energy_counters -= amount
            if verbose:
                print(f"Spent {amount} energy (remaining: {self.energy_counters})")
            return True
        else:
            if verbose:
                print(f"Not enough energy (have {self.energy_counters}, need {amount})")
            return False

    def trigger_energy_payoffs(self, verbose=False):
        """
        Trigger effects that care about energy.

        Checks for:
        - Aetherworks Marvel (pay 6 energy, cast free spell)
        - Electrostatic Pummeler (pay 3 energy, double power)
        - Whirler Virtuoso (pay 3 energy, create Thopter)
        """
        for permanent in self.creatures + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Aetherworks Marvel: Pay 6 energy, cast free spell
            if 'aetherworks marvel' in name:
                if self.energy_counters >= 6:
                    if self.spend_energy(6, verbose=verbose):
                        # Simplified: Draw a card as proxy for "cast free spell"
                        self.draw_card(1, verbose=verbose)
                        if verbose:
                            print(f"  → Aetherworks Marvel: Cast free spell!")

            # Whirler Virtuoso: Pay 3 energy, create Thopter
            if 'whirler virtuoso' in name:
                # Create as many Thopters as we can afford
                while self.energy_counters >= 3:
                    if self.spend_energy(3, verbose=verbose):
                        self.create_token(
                            token_name="Thopter Token",
                            power=1,
                            toughness=1,
                            token_type="Thopter",
                            keywords=['Flying'],
                            verbose=verbose
                        )
                        if verbose:
                            print(f"  → Whirler Virtuoso: Created Thopter token")

            # Electrostatic Pummeler: Pay 3 energy, double power
            if 'electrostatic pummeler' in name and permanent in self.creatures:
                if self.energy_counters >= 3:
                    if self.spend_energy(3, verbose=verbose):
                        permanent.power = (permanent.power or 1) * 2
                        if verbose:
                            print(f"  → Electrostatic Pummeler: Power doubled to {permanent.power}!")

    def draw_card(self, num_cards, verbose=False):
        """
        Draws ``num_cards`` from the library to the hand and returns the cards
        drawn. If the library is empty, nothing is drawn.

        Parameters
        ----------
        num_cards : int
            Number of cards to draw.
        verbose : bool, optional
            If ``True`` print debug information.
        """
        if verbose:
            print(f"Drawing {num_cards} card(s) from library.")

        drawn = []
        for _ in list(range(num_cards)):
            if not self.library:
                if verbose:
                    print("Library is empty, cannot draw more cards.")
                break
            drawn_card = self.library.pop(0)
            self.hand.append(drawn_card)
            drawn.append(drawn_card)

            # Track draws for this turn
            self.cards_drawn_this_turn += 1

            # Trigger "when you draw" effects (Niv-Mizzet, etc.)
            self.trigger_draw_effects(verbose=verbose)

        if verbose:
            print(
                f"Hand now has {len(self.hand)} card(s); Library size: {len(self.library)}"
            )

        return drawn

    def trigger_draw_effects(self, verbose=False):
        """Trigger effects when a card is drawn (Niv-Mizzet, Psychosis Crawler, etc.)."""
        num_alive_opps = len([o for o in self.opponents if o['is_alive']])

        # Check for draw trigger permanents
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Niv-Mizzet: Deal 1 damage when you draw
            if ('niv-mizzet' in name) or ('whenever you draw a card' in oracle and 'deals' in oracle and 'damage' in oracle):
                damage = 1 * num_alive_opps
                self.spell_damage_this_turn += damage
                if verbose:
                    print(f"  → {permanent.name} deals {damage} damage (draw trigger)")

            # Psychosis Crawler: Each opponent loses 1 life when you draw
            if ('psychosis crawler' in name) or ('whenever you draw a card' in oracle and 'each opponent loses 1 life' in oracle):
                drain = 1 * num_alive_opps
                self.drain_damage_this_turn += drain
                if verbose:
                    print(f"  → {permanent.name} drains {drain} life (draw trigger)")

            # The Locust God: Create 1/1 Insect with flying when you draw
            if ('locust god' in name) or ('whenever you draw a card' in oracle and 'create' in oracle and 'insect' in oracle):
                self.create_token(
                    token_name="Insect Token",
                    power=1,
                    toughness=1,
                    token_type="Insect",
                    keywords=['Flying', 'Haste'],
                    verbose=verbose
                )
                if verbose:
                    print(f"  → {permanent.name} creates 1/1 Insect with flying and haste")

    def wheel_effect(self, num_cards=7, verbose=False):
        """
        Wheel effect: Discard hand, then draw cards.

        Used by: Wheel of Fortune, Windfall, Reforge the Soul, etc.
        """
        # Count cards discarded
        hand_size = len(self.hand)

        # Move hand to graveyard
        for card in list(self.hand):
            self.hand.remove(card)
            self.graveyard.append(card)

        if verbose:
            print(f"Discarded {hand_size} cards from hand")

        # Trigger discard payoffs (Bone Miser, Waste Not, etc.)
        self.trigger_discard_payoffs(hand_size, verbose=verbose)

        # Draw new hand
        self.draw_card(num_cards, verbose=verbose)

        if verbose:
            print(f"Wheeled: Discarded {hand_size}, drew {num_cards}")

        return hand_size

    def trigger_discard_payoffs(self, num_discarded, verbose=False):
        """Trigger effects when cards are discarded (Bone Miser, Waste Not, etc.)."""
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Bone Miser: Generate mana/tokens when you discard
            if 'bone miser' in name:
                # Simplified: Create treasure tokens equal to cards discarded
                for _ in range(min(num_discarded, 3)):  # Cap at 3 to avoid infinite
                    self.create_treasure(verbose=verbose)
                if verbose:
                    print(f"  → Bone Miser creates {min(num_discarded, 3)} Treasure tokens")

            # Waste Not: Various effects when opponent discards (simplified to self)
            if 'waste not' in name:
                # Simplified: Create 2/2 Zombie for each 2 cards discarded
                zombies = num_discarded // 2
                for _ in range(zombies):
                    self.create_token(
                        token_name="Zombie Token",
                        power=2,
                        toughness=2,
                        token_type="Zombie",
                        verbose=verbose
                    )
                if verbose and zombies > 0:
                    print(f"  → Waste Not creates {zombies} Zombie tokens")

            # Glint-Horn Buccaneer: Deal damage when you discard
            if ('glint-horn buccaneer' in name) or ('whenever you discard' in oracle and 'deals' in oracle and 'damage' in oracle):
                damage = num_discarded
                self.spell_damage_this_turn += damage
                if verbose:
                    print(f"  → {permanent.name} deals {damage} damage (discard trigger)")

    def gain_life(self, amount: int, verbose: bool = False):
        """
        Gain life and track it for metrics.

        Parameters
        ----------
        amount : int
            Amount of life to gain.
        verbose : bool, optional
            If ``True`` print debug information.
        """
        if amount > 0:
            self.life_total += amount
            self.life_gained_this_turn += amount
            if verbose:
                print(f"Gained {amount} life. Life total: {self.life_total}")

    def lose_life(self, amount: int, verbose: bool = False):
        """
        Lose or pay life and track it for metrics.

        Parameters
        ----------
        amount : int
            Amount of life to lose/pay.
        verbose : bool, optional
            If ``True`` print debug information.
        """
        if amount > 0:
            self.life_total -= amount
            self.life_lost_this_turn += amount
            if verbose:
                print(f"Lost {amount} life. Life total: {self.life_total}")

    def play_card(self, card, verbose=False, cast=True):
        """Play *card* using the appropriate method or simply put it into play."""

        if getattr(card, "is_commander", False) or card.type.lower() == "commander":
            method = getattr(self, "play_commander", None)
        else:
            # Extract main type before "—" (e.g., "Basic Land — Swamp" -> "Basic Land")
            main_type = card.type.split('—')[0].strip()

            # Normalize card types: strip supertypes to get base type
            # "Legendary Creature" -> "Creature"
            # "Artifact Creature" -> "Creature"
            # "Enchantment Creature" -> "Creature"
            # "Basic Land" -> "Land"
            if "Creature" in main_type:
                main_type = "Creature"
            elif "Land" in main_type:
                main_type = "Land"
            elif "Artifact" in main_type:
                main_type = "Artifact"
            elif "Enchantment" in main_type:
                main_type = "Enchantment"
            elif "Planeswalker" in main_type:
                main_type = "Planeswalker"
            elif "Instant" in main_type:
                main_type = "Instant"
            elif "Sorcery" in main_type:
                main_type = "Sorcery"

            method = getattr(self, f"play_{main_type.lower()}", None)
        if not callable(method):
            if verbose:
                print(f"Card type {card.type} not supported for play.")
            return False

        if cast:
            success = method(card, verbose)
        else:
            # put card directly onto the battlefield ignoring mana costs
            if 'Land' in card.type:
                if card in self.hand:
                    self.hand.remove(card)
                if card in self.library:
                    self.library.remove(card)
                if card in self.graveyard:
                    self.graveyard.remove(card)
                self.play_land(card, verbose)
                success = True
            else:
                zone_lists = {
                    "Creature": self.creatures,
                    "Commander": self.creatures,
                    "Artifact": self.artifacts,
                    "Equipment": self.artifacts,
                    "Enchantment": self.enchantments,
                    "Planeswalker": self.planeswalkers,
                }
                # Find the right zone for this card type (supports full type lines)
                lst = None
                for card_type_key, zone in zone_lists.items():
                    if card_type_key in card.type:
                        lst = zone
                        break
                if not lst:
                    success = False
                else:
                    if card in self.hand:
                        self.hand.remove(card)
                    if card in self.library:
                        self.library.remove(card)
                    if card in self.graveyard:
                        self.graveyard.remove(card)
                    lst.append(card)
                    card.tapped = False
                    if verbose:
                        print(f"Put {card.name} onto the battlefield")
                    success = True

        if success:
            if card in (
                self.lands_untapped
                + self.lands_tapped
                + self.creatures
                + self.artifacts
                + self.enchantments
                + self.planeswalkers
            ):
                self._add_abilities_from_card(card)
                # Process specific ETB effects for landfall cards
                self._process_special_etb_effects(card, verbose)

                # PRIORITY FIX: Detect Syr Konrad entering battlefield
                if 'creature' in card.type.lower() and 'syr konrad' in card.name.lower():
                    self.syr_konrad_on_board = True
                    if verbose:
                        print("⚡ Syr Konrad, the Grim is on the battlefield!")

                # PRIORITY FIX P1: Detect Muldrotha entering battlefield
                if 'creature' in card.type.lower() and 'muldrotha' in card.name.lower():
                    self.muldrotha_on_board = True
                    if verbose:
                        print("♻️  Muldrotha, the Gravetide enables graveyard casting!")

                # PRIORITY FIX P2: Detect Meren entering battlefield
                if 'creature' in card.type.lower() and 'meren' in card.name.lower():
                    self.meren_on_board = True
                    if verbose:
                        print("♻️  Meren of Clan Nel Toth enables end-step reanimation!")

                # Detect Y'shtola, Night's Blessed entering battlefield
                if 'creature' in card.type.lower() and "y'shtola" in card.name.lower() and "night's blessed" in card.name.lower():
                    self.yshtola_on_board = True
                    if verbose:
                        print("🌙 Y'shtola, Night's Blessed is on the battlefield!")

                self._execute_triggers("etb", card, verbose)

                # GENERIC: Check for "Whenever another Ally enters" triggers (like Wartime Protestors)
                if 'ally' in card.type.lower():
                    for creature in self.creatures:
                        if creature is card:
                            continue
                        oracle = getattr(creature, 'oracle_text', '').lower()
                        # "Whenever another Ally you control enters, put a +1/+1 counter on that creature and it gains haste"
                        if 'whenever another ally' in oracle and 'enters' in oracle and '+1/+1 counter' in oracle:
                            self.add_counters_with_doubling(card, "+1/+1", 1, verbose=False)
                            card.has_haste = True
                            if verbose:
                                print(f"  → {creature.name}: +1/+1 counter on {card.name}, gains haste")

                if 'Land' in card.type:
                    self._trigger_landfall(verbose)

        if success and cast:
            self.turn_play_count += 1
            self.total_play_count += 1
            self.play_log.append((self.turn, card))
            self.turn_casts.append(card)
            if verbose:
                print(f"Mana pool now: {self._mana_pool_str()}")
                print(
                    f"Hand size: {len(self.hand)} | Battlefield creatures: {len(self.creatures)} | Lands: {len(self.lands_untapped) + len(self.lands_tapped)}"
                )
        return success

    def untap_land_condition(self, card):
        conditions = card.etb_tapped_conditions

        # If there are no conditions defined, check default ETB tapped status
        if not conditions:
            # If etb_tapped is False, it always enters untapped
            return not getattr(card, 'etb_tapped', False)

        # "always_tapped" explicitly means it can never enter untapped
        if 'always_tapped' in conditions:
            return False

        # Control specific permanents (e.g., Forest or Plains)
        if 'control' in conditions:
            required = conditions['control']
            permanents_in_play = [c.name for c in self.lands_untapped + self.lands_tapped]
            if any(req in permanents_in_play for req in required):
                return True
            else:
                return False

        # Control at least a certain number of basic lands
        if 'control_basic_lands' in conditions:
            required_count = conditions['control_basic_lands']
            basic_lands_in_play = [c for c in self.lands_untapped + self.lands_tapped if c.type.lower() == 'basic land']
            return len(basic_lands_in_play) >= required_count

        # Control at least a certain total number of lands
        if 'control_lands' in conditions:
            required_total = conditions['control_lands']
            total_lands_in_play = len(self.lands_untapped + self.lands_tapped)
            return total_lands_in_play >= required_total

        # Reveal specific cards from hand (matching by name or type)
        if 'reveal' in conditions:
            required_reveals = conditions['reveal']
            hand_names_and_types = [c.name for c in self.hand] + [c.type for c in self.hand]
            return any(req in hand_names_and_types for req in required_reveals)

        # Default case: If no condition matches explicitly, lands enter tapped.
        return False

    def get_extra_land_drops(self) -> int:
        """
        Calculate how many extra lands can be played this turn.

        Checks for effects like:
        - Azusa, Lost but Seeking (play 2 additional lands)
        - Exploration (play 1 additional land)
        - Oracle of Mul Daya (play 1 additional land)

        Returns: Number of extra land drops available
        """
        extra_lands = 0

        # Check all permanents for extra land drop effects
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Azusa, Lost but Seeking: "You may play two additional lands"
            if 'azusa' in name or 'play two additional lands' in oracle:
                extra_lands += 2

            # Exploration, Burgeoning, Oracle of Mul Daya: "You may play an additional land"
            elif 'play an additional land' in oracle or 'play one additional land' in oracle:
                extra_lands += 1

            # Dryad of the Ilysian Grove: "You may play an additional land"
            elif 'additional land' in oracle and 'may play' in oracle:
                extra_lands += 1

        return extra_lands

    def can_play_land(self) -> bool:
        """Check if we can play a land this turn."""
        max_lands = 1 + self.get_extra_land_drops()
        return self.lands_played_this_turn < max_lands

    def choose_land_to_play(self):
        """Return the best land from hand based on simple heuristics."""
        lands = [c for c in self.hand if 'Land' in c.type]
        if not lands:
            return None

        has_fast_artifact = any(
            c.name.lower() in {"sol ring", "arcane signet"} for c in self.hand
        )

        if has_fast_artifact:
            for land in lands:
                if self.untap_land_condition(land):
                    return land

        if self.turn == 1:
            for land in lands:
                if not self.untap_land_condition(land):
                    return land

        for land in lands:
            if self.untap_land_condition(land):
                return land

        return lands[0]

    def play_land(self, card, verbose=True):
        """Play a land card. Check if it enters untapped based on conditions."""
        if card in self.hand:
            self.hand.remove(card)

        # Track land plays for the turn
        self.lands_played_this_turn += 1

        enters_untapped = self.untap_land_condition(card)

        if enters_untapped:
            self.lands_untapped.append(card)
            card.tapped = False
            if verbose:
                print(f"Played land untapped: {card.name}")
            if not getattr(card, 'activated_abilities', []) and not (
                getattr(card, 'fetch_basic', False)
                or getattr(card, 'fetch_land_types', [])
            ):
                mana_tuple = tuple(card.produces_colors or ['C'])
                if hasattr(self, 'mana_pool'):
                    self.mana_pool.append(mana_tuple)
                if verbose:
                    print(f"{card.name} produced mana: {','.join(mana_tuple)}")
        else:
            self.lands_tapped.append(card)
            card.tapped = True
            if verbose:
                print(f"Played land tapped: {card.name}")

        for ab in getattr(card, 'activated_abilities', []):
            self.available_abilities.append((card, ab))

        if verbose:
            print(f"Mana pool now: {self._mana_pool_str()}")

        if getattr(card, 'fetch_basic', False) or getattr(card, 'fetch_land_types', []):
            self.fetch_land(
                card,
                basic_only=getattr(card, 'fetch_basic', False),
                types=getattr(card, 'fetch_land_types', []),
                force_tapped=getattr(card, 'fetch_land_tapped', False),
                verbose=verbose,
            )

        return True


    def fetch_land(self, card, basic_only=False, types=None, force_tapped=False, verbose=False):
        """Pay 1 life, sacrifice *card*, search library for a land and put it onto the battlefield."""
        types = types or []
        self.life_total -= 1
        if card in self.lands_untapped:
            self.lands_untapped.remove(card)
        if card in self.lands_tapped:
            self.lands_tapped.remove(card)
        self.graveyard.append(card)
        if verbose:
            print(f"Sacrificed {card.name} to fetch a land. Life total: {self.life_total}")

        chosen = None
        for c in list(self.library):
            if c.type not in ("Land", "Basic Land"):
                continue
            if basic_only and c.type != "Basic Land":
                continue
            if types:
                match = False
                for t in types:
                    if t.lower() in c.name.lower():
                        match = True
                        break
                if not match:
                    continue
            chosen = c
            break

        if not chosen:
            return False

        self.play_card(chosen, verbose=verbose, cast=False)
        if force_tapped and chosen in self.lands_untapped:
            self.lands_untapped.remove(chosen)
            self.lands_tapped.append(chosen)
            chosen.tapped = True
        if verbose:
            state = "tapped" if chosen.tapped else "untapped"
            print(f"Fetched land {chosen.name} entering {state}")
        return True


    def search_basic_land(self, verbose=False):
        """Find the first basic land in library and put it onto the battlefield."""
        land = next((c for c in self.library if 'Basic Land' in c.type), None)
        if not land:
            return False
        success = self.play_card(land, verbose=verbose, cast=False)
        if verbose:
            print(f"Library size after search: {len(self.library)}")
        return success


    def play_creature(self, card, verbose=False):
        """
        Plays the given creature card. Pays mana, then moves it
        from hand to battlefield.
        """
        # 1.  Check mana first
        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}.")
            return False

        # 2.  Pay
        Mana_utils.pay(card.mana_cost, self.mana_pool)

        # 3.  Move card
        self.hand.remove(card)
        self.creatures.append(card)
        card.tapped = False

        # PRIORITY 2: Apply +1/+1 counter effects (Cathars' Crusade)
        self.apply_etb_counter_effects(card, verbose=verbose)

        # Apply drain from ETB triggers (Impact Tremors, Warleader's Call)
        drain_on_etb = self.calculate_etb_drain()
        if drain_on_etb > 0:
            self.drain_damage_this_turn += drain_on_etb
            if verbose:
                print(f"  → ETB drain: {drain_on_etb} damage (Impact Tremors/Warleader's Call)")

        # Door of Destinies: Add charge counter when casting creature of chosen type
        creature_type = getattr(card, 'type', '').lower()
        for artifact in self.artifacts:
            artifact_name = getattr(artifact, 'name', '').lower()
            if 'door of destinies' in artifact_name:
                chosen_type = getattr(artifact, 'chosen_type', 'ally').lower()
                if chosen_type in creature_type or 'ally' in creature_type:
                    if not hasattr(artifact, 'counters'):
                        artifact.counters = {}
                    artifact.counters['charge'] = artifact.counters.get('charge', 0) + 1
                    if verbose:
                        print(f"  → Door of Destinies: +1 charge counter (now {artifact.counters['charge']})")

        # Rally triggers: When an Ally enters, check for Rally abilities on all Allies
        if 'ally' in creature_type:
            self.trigger_rally_abilities(card, verbose=verbose)

        if verbose:
            print(f"Played creature: {card.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True

    
        
    # ─────────────────────── Artifact / Equipment ──
    def play_artifact(self, card, verbose=False):
        if card not in self.hand:
            raise ValueError(f"[BUG] {card.name} is not in hand during play_artifact")
        self.hand.remove(card)
        self.artifacts.append(card)
        Mana_utils.pay(card.mana_cost, self.mana_pool)

        # Y'shtola, Night's Blessed: Whenever you cast a noncreature spell with MV 3+
        if self.yshtola_on_board:
            from convert_dataframe_deck import parse_mana_cost
            cmc = parse_mana_cost(getattr(card, 'mana_cost', ''))
            if cmc >= 3:
                alive_opps = [o for o in self.opponents if o['is_alive']]
                for opp in alive_opps:
                    opp['life_total'] -= 2
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                self.gain_life(2, verbose=False)
                if verbose:
                    damage_dealt = 2 * len(alive_opps)
                    print(f"  🌙 Y'shtola triggers: {damage_dealt} damage to opponents, gained 2 life")

        # Trigger noncreature spell effects (Sokka, Bria, etc.)
        self.trigger_noncreature_spell_effects(card, verbose=verbose)
        self.apply_prowess_bonus()

        if verbose:
            print(f"→ {card.name} enters the battlefield (artifact)")
        return True

    # ------ Equipment is a type of Artifact in MTG, so we can use the same method.
    # If you have equipments that are NOT mana rocks you can add:
    def play_equipment(self, card, verbose=False):
        success = self.play_artifact(card, verbose)
        if success:
            # Handle Living Weapon: create 0/0 Germ token and auto-attach
            oracle = getattr(card, 'oracle_text', '').lower()
            if 'living weapon' in oracle:
                # Create 0/0 Germ token
                germ_token = self.create_token("Phyrexian Germ", 0, 0, has_haste=False, verbose=verbose)
                if germ_token:
                    # Auto-attach equipment to the token (no cost)
                    buff = int(getattr(card, "power_buff", 0) or 0)
                    germ_token.power = int(germ_token.power or 0) + buff
                    germ_token.toughness = int(germ_token.toughness or 0) + buff
                    self.equipment_attached[card] = germ_token
                    self._apply_equipped_keywords(germ_token)
                    if verbose:
                        print(f"  → Living Weapon: Created 0/0 Germ token and attached {card.name} to it")

            # Handle Sigarda's Aid: auto-attach equipment on ETB
            # Check if Sigarda's Aid is on battlefield
            has_sigardas_aid = any('sigarda' in getattr(perm, 'name', '').lower() and 'aid' in getattr(perm, 'name', '').lower()
                                  for perm in self.enchantments)
            if has_sigardas_aid and self.creatures and card not in self.equipment_attached:
                # Attach to the best creature (highest power)
                best_creature = max(self.creatures, key=lambda c: int(getattr(c, 'power', 0) or 0))
                buff = int(getattr(card, "power_buff", 0) or 0)
                best_creature.power = int(best_creature.power or 0) + buff
                best_creature.toughness = int(best_creature.toughness or 0) + buff
                self.equipment_attached[card] = best_creature
                self._apply_equipped_keywords(best_creature)
                if verbose:
                    print(f"  → Sigarda's Aid: Auto-attached {card.name} to {best_creature.name}")
        return success

    def equip_equipment(self, equipment, creature, verbose=False):
        """Attach an equipment to a creature after paying its equip cost."""
        if equipment not in self.artifacts:
            if verbose:
                print(f"{equipment.name} is not on the battlefield.")
            return False
        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return False

        cost = getattr(equipment, "equip_cost", "")
        if not Mana_utils.can_pay(cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to equip {equipment.name}")
            return False

        Mana_utils.pay(cost, self.mana_pool)
        buff = int(getattr(equipment, "power_buff", 0) or 0)
        old = self.equipment_attached.get(equipment)
        if old and old is not creature:
            old.power = int(old.power or 0) - buff
            old.toughness = int(old.toughness or 0) - buff
            self._apply_equipped_keywords(old)
        creature.power = int(creature.power or 0) + buff
        creature.toughness = int(creature.toughness or 0) + buff
        self.equipment_attached[equipment] = creature
        self._apply_equipped_keywords(creature)
        for ab in getattr(equipment, "activated_abilities", []):
            if getattr(ab, "requires_equipped", False):
                ab.usable = True
        self._execute_triggers("equip", equipment, verbose)
        if verbose:
            print(f"Equipped {equipment.name} to {creature.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True
    
    # ─────────────────────── Other card types ──
    def play_enchantment(self, card, verbose=False):
        """Cast an enchantment and move it to the battlefield."""
        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False
        Mana_utils.pay(card.mana_cost, self.mana_pool)
        if card in self.hand:
            self.hand.remove(card)
        self.enchantments.append(card)

        # Y'shtola, Night's Blessed: Whenever you cast a noncreature spell with MV 3+
        if self.yshtola_on_board:
            from convert_dataframe_deck import parse_mana_cost
            cmc = parse_mana_cost(getattr(card, 'mana_cost', ''))
            if cmc >= 3:
                alive_opps = [o for o in self.opponents if o['is_alive']]
                for opp in alive_opps:
                    opp['life_total'] -= 2
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                self.gain_life(2, verbose=False)
                if verbose:
                    damage_dealt = 2 * len(alive_opps)
                    print(f"  🌙 Y'shtola triggers: {damage_dealt} damage to opponents, gained 2 life")

        if verbose:
            print(f"Played enchantment: {card.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True


    def play_sorcery(self, card, verbose=True):
        """Cast a sorcery. It resolves and goes to the graveyard."""

        cost = getattr(card, "mana_cost", "")
        x_val = getattr(card, "x_value", 0)

        if "X" in cost:
            fixed_cost = cost.replace("X", "")
            temp_pool = self.mana_pool[:]
            if not Mana_utils.can_pay(fixed_cost, temp_pool):
                if verbose:
                    print(f"Not enough mana to play {card.name}")
                return False
            Mana_utils.pay(fixed_cost, temp_pool)
            if len(temp_pool) < x_val:
                if verbose:
                    print(f"Not enough mana to pay X for {card.name}")
                return False
            Mana_utils.pay(fixed_cost, self.mana_pool)
            for _ in range(x_val):
                if self.mana_pool:
                    self.mana_pool.pop(0)
        else:
            if not Mana_utils.can_pay(cost, self.mana_pool):
                if verbose:
                    print(f"Not enough mana to play {card.name}")
                return False
            Mana_utils.pay(cost, self.mana_pool)

        if card in self.hand:
            self.hand.remove(card)
        self.graveyard.append(card)

        # SPELLSLINGER: Trigger cast effects (Guttersnipe, Young Pyromancer, etc.)
        # NOTE: trigger_cast_effects now also handles Y'shtola's MV 3+ trigger
        self.trigger_cast_effects(card, verbose=verbose)

        # UNTAP ENGINES: Trigger untap effects on spell cast (Jeskai Ascendancy, Paradox Engine)
        self.trigger_on_spell_cast_untaps(card, verbose=verbose)

        # SPELL COPY: Check for copy effects (Fork, Dualcaster Mage, etc.)
        oracle = getattr(card, "oracle_text", "").lower()
        num_copies = self.get_spell_copies(card, verbose=verbose)
        for copy_num in range(num_copies):
            if verbose:
                print(f"  → Copy #{copy_num + 1} of {card.name}")
            self.resolve_spell_copy(card, x_val, verbose=verbose)

        # STORM: Check for storm mechanic
        if 'storm' in oracle:
            storm_count = self.spells_cast_this_turn - 1  # Don't count the storm spell itself
            if storm_count > 0:
                if verbose:
                    print(f"  → Storm triggers: Creating {storm_count} copies")
                for _ in range(storm_count):
                    self.resolve_spell_copy(card, x_val, verbose=verbose)

        if getattr(card, "draw_cards", 0) > 0:
            self.draw_card(getattr(card, "draw_cards"), verbose=verbose)

        # DIRECT DAMAGE: Deal damage from instant/sorcery
        damage = getattr(card, "deals_damage", 0)
        if damage > 0:
            self.spell_damage_this_turn += damage
            # Deal damage to opponents in goldfish mode
            alive_opps = [opp for opp in self.opponents if opp['life_total'] > 0]
            if alive_opps:
                # Apply damage to first alive opponent (target selection)
                # Note: For "each opponent" effects, damage would need to be marked differently
                target_opp = alive_opps[0]
                target_opp['life_total'] -= damage
                if target_opp['life_total'] <= 0:
                    target_opp['is_alive'] = False
                    if verbose:
                        print(f"  → {target_opp['name']} eliminated by {card.name} (dealt {damage} damage)!")
                if verbose:
                    print(f"  → {card.name} deals {damage} damage to {target_opp['name']}")

        # TOKEN CREATION: Parse oracle text for token creation
        oracle = getattr(card, "oracle_text", "").lower()
        if oracle and "create" in oracle and "token" in oracle:
            import re
            # Pattern: "Create X Y/Z tokens" or "Create five 2/2 tokens"
            m_token = re.search(
                r"create (?P<num>x|\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (?P<stats>\d+/\d+)?[^.]*tokens?",
                oracle,
            )
            if m_token:
                num_map = {
                    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3,
                    "four": 4, "five": 5, "six": 6, "seven": 7,
                    "eight": 8, "nine": 9, "ten": 10, "x": x_val if "X" in cost else 1,
                }
                val = m_token.group("num")
                if val == "x":
                    token_count = x_val if x_val > 0 else 1
                else:
                    token_count = num_map.get(val, int(val) if val.isdigit() else 1)

                stats = m_token.group("stats") if m_token.group("stats") else "1/1"

                # Extract keywords (haste, trample, flying, etc.)
                keywords = []
                if "haste" in oracle:
                    keywords.append("haste")
                if "trample" in oracle:
                    keywords.append("trample")
                if "flying" in oracle:
                    keywords.append("flying")
                if "vigilance" in oracle:
                    keywords.append("vigilance")
                if "lifelink" in oracle:
                    keywords.append("lifelink")

                # Create the tokens
                self.create_tokens(token_count, stats, keywords=keywords, verbose=verbose)
                if verbose:
                    kw_text = f" with {', '.join(keywords)}" if keywords else ""
                    print(f"  → {card.name} created {token_count} {stats} token(s){kw_text}")

        if getattr(card, "puts_land", False):
            self.search_basic_land(verbose)
        oracle = getattr(card, "oracle_text", "").lower()
        if oracle and "search" in oracle:
            import re
            num = 1
            zones = ""
            m = re.search(
                r"search your (?P<zones>[^.]*) for (?:up to )?(?P<num>\d+|one|two|three|four|five|a|an)?",
                oracle,
            )
            if m:
                zones = m.group("zones")
                val = m.group("num")
                if val:
                    num_map = {
                        "one": 1,
                        "two": 2,
                        "three": 3,
                        "four": 4,
                        "five": 5,
                        "a": 1,
                        "an": 1,
                    }
                    if val.isdigit():
                        num = int(val)
                    else:
                        num = num_map.get(val.lower(), 1)
            search_library = "library" in zones
            search_graveyard = "graveyard" in zones
            dest_battlefield = re.search(r"onto the battlefield", oracle) is not None
            for _ in range(num):
                source_zones = []
                if search_library:
                    source_zones.append(self.library)
                if search_graveyard:
                    source_zones.append(self.graveyard)
                chosen = None
                for zone in source_zones:
                    if zone:
                        chosen = zone.pop(0)
                        break
                if not chosen:
                    break
                if dest_battlefield:
                    self.play_card(chosen, verbose=verbose, cast=False)
                else:
                    self.hand.append(chosen)
                    if verbose:
                        print(f"Tutored {chosen.name} to hand")

        # REANIMATOR: Handle reanimation spells
        card_name = getattr(card, 'name', '').lower()
        if oracle:
            # Reanimate / Animate Dead / Necromancy / Exhume
            if ('return' in oracle and 'creature' in oracle and 'graveyard' in oracle and 'battlefield' in oracle) or \
               'animate dead' in card_name or 'reanimate' in card_name or 'necromancy' in card_name or 'exhume' in card_name:
                if verbose:
                    print(f"  → {card.name} is a reanimation spell!")
                self.reanimate_creature(verbose=verbose)

            # PRIORITY FIX: Living Death (mass reanimation - returns ALL creatures)
            elif 'living death' in card_name or ('each player' in oracle and 'exile all' in oracle and 'graveyard' in oracle):
                # Use the proper Living Death handler that returns ALL creatures
                # Note: Mana was already paid above, so we need to refund it and call the method
                # Actually, cast_living_death will handle mana, but we already paid, so skip calling it
                # Instead, inline the Living Death logic here since mana is already paid
                creatures_in_graveyard = [c for c in self.graveyard if 'creature' in c.type.lower()]
                if verbose and creatures_in_graveyard:
                    print(f"  💀 LIVING DEATH: Reanimating {len(creatures_in_graveyard)} creatures!")

                # Save creatures on battlefield that will die
                creatures_to_sacrifice = self.creatures[:]

                # Remove all creatures from graveyard first
                for creature in creatures_in_graveyard[:]:  # Use slice copy to avoid modification issues
                    if creature in self.graveyard:
                        self.graveyard.remove(creature)

                # Sacrifice all creatures on battlefield (trigger death effects including Syr Konrad)
                for creature in creatures_to_sacrifice:
                    self.trigger_death_effects(creature, verbose=verbose)
                self.creatures.clear()

                # Return all creatures from graveyard to battlefield
                for creature in creatures_in_graveyard:
                    self.creatures.append(creature)
                    creature._turns_on_board = 0  # Reset summoning sickness

                    # Trigger Syr Konrad on leaving graveyard
                    self.trigger_syr_konrad_on_leave_graveyard(creature, verbose=verbose)

                    # Trigger ETB effects
                    self._execute_triggers("etb", creature, verbose)

                total_power = sum(c.power or 0 for c in creatures_in_graveyard)
                if verbose:
                    print(f"  → Returned {len(creatures_in_graveyard)} creatures ({total_power} total power) to battlefield!")

            # Entomb / Buried Alive (tutor to graveyard)
            elif 'entomb' in card_name or ('search your library' in oracle and 'put' in oracle and 'graveyard' in oracle):
                if 'three' in oracle or 'buried alive' in card_name:
                    # Buried Alive: Tutor 3 creatures
                    for _ in range(3):
                        self.tutor_to_graveyard(verbose=verbose)
                else:
                    # Entomb: Tutor 1 card
                    self.tutor_to_graveyard(verbose=verbose)

            # Faithless Looting / Cathartic Reunion (discard for value)
            elif ('draw' in oracle and 'discard' in oracle) or 'faithless looting' in card_name or 'cathartic reunion' in card_name:
                import re
                draw_match = re.search(r'draw (\w+) card', oracle)
                discard_match = re.search(r'discard (\w+) card', oracle)

                num_draw = 0
                num_discard = 0

                if draw_match:
                    draw_word = draw_match.group(1)
                    num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'a': 1, 'an': 1}
                    num_draw = num_map.get(draw_word.lower(), int(draw_word) if draw_word.isdigit() else 0)

                if discard_match:
                    discard_word = discard_match.group(1)
                    num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'a': 1, 'an': 1}
                    num_discard = num_map.get(discard_word.lower(), int(discard_word) if discard_word.isdigit() else 0)

                if num_draw > 0 or num_discard > 0:
                    self.discard_for_value(num_cards=num_discard, draw_cards=num_draw, verbose=verbose)

        for spec in getattr(card, "creates_tokens", []):
            count = spec.get("number", 0)
            if isinstance(count, str) and count.lower() == "x":
                count = x_val
            token_args = spec.get("token", {})
            from simulate_game import Card as GameCard
            for _ in range(count):
                token = GameCard(**token_args)
                self.creatures.append(token)

        if getattr(card, "monarch_on_damage", False):
            self.monarch_trigger_turn = self.turn

        if verbose:
            print(f"Played sorcery: {card.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True



    def play_instant(self, card, verbose=False):
        """Cast an instant. It resolves and goes to the graveyard."""
        # Skip purely defensive cards in goldfish simulation - they do nothing
        card_name = getattr(card, 'name', '').lower()
        oracle = getattr(card, 'oracle_text', '').lower()
        defensive_cards = [
            "teferi's protection", "heroic intervention", "flawless maneuver",
            "clever concealment", "unbreakable formation", "make a stand",
            "rootborn defenses", "wrap in vigor", "faith's reward"
        ]
        if any(dc in card_name for dc in defensive_cards):
            if verbose:
                print(f"Skipping {card.name} (defensive card, useless in goldfish)")
            return False
        # Also skip if oracle text is purely defensive
        if ('your permanents' in oracle or 'you control' in oracle) and \
           ('indestructible' in oracle or 'hexproof' in oracle or 'protection from' in oracle) and \
           'damage' not in oracle and 'draw' not in oracle and 'token' not in oracle:
            if verbose:
                print(f"Skipping {card.name} (defensive card, useless in goldfish)")
            return False

        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False
        Mana_utils.pay(card.mana_cost, self.mana_pool)
        if card in self.hand:
            self.hand.remove(card)
        self.graveyard.append(card)

        # SPELLSLINGER: Trigger cast effects (Guttersnipe, Young Pyromancer, etc.)
        # NOTE: trigger_cast_effects now also handles Y'shtola's MV 3+ trigger
        self.trigger_cast_effects(card, verbose=verbose)

        # UNTAP ENGINES: Trigger untap effects on spell cast (Jeskai Ascendancy, Paradox Engine)
        self.trigger_on_spell_cast_untaps(card, verbose=verbose)

        # SPELL COPY: Check for copy effects (Fork, Dualcaster Mage, etc.)
        oracle = getattr(card, "oracle_text", "").lower()
        num_copies = self.get_spell_copies(card, verbose=verbose)
        for copy_num in range(num_copies):
            if verbose:
                print(f"  → Copy #{copy_num + 1} of {card.name}")
            self.resolve_spell_copy(card, x_val, verbose=verbose)

        # STORM: Check for storm mechanic
        if 'storm' in oracle:
            storm_count = self.spells_cast_this_turn - 1  # Don't count the storm spell itself
            if storm_count > 0:
                if verbose:
                    print(f"  → Storm triggers: Creating {storm_count} copies")
                for _ in range(storm_count):
                    self.resolve_spell_copy(card, x_val, verbose=verbose)

        if getattr(card, "draw_cards", 0) > 0:
            self.draw_card(getattr(card, "draw_cards"), verbose=verbose)

        # DIRECT DAMAGE: Deal damage from instant/sorcery
        damage = getattr(card, "deals_damage", 0)
        if damage > 0:
            self.spell_damage_this_turn += damage
            # Deal damage to opponents in goldfish mode
            alive_opps = [opp for opp in self.opponents if opp['life_total'] > 0]
            if alive_opps:
                # Apply damage to first alive opponent (target selection)
                # Note: For "each opponent" effects, damage would need to be marked differently
                target_opp = alive_opps[0]
                target_opp['life_total'] -= damage
                if target_opp['life_total'] <= 0:
                    target_opp['is_alive'] = False
                    if verbose:
                        print(f"  → {target_opp['name']} eliminated by {card.name} (dealt {damage} damage)!")
                if verbose:
                    print(f"  → {card.name} deals {damage} damage to {target_opp['name']}")

        # TOKEN CREATION: Parse oracle text for token creation
        oracle = getattr(card, "oracle_text", "").lower()
        x_val = getattr(card, "x_value", 0)
        cost = getattr(card, "mana_cost", "")
        if oracle and "create" in oracle and "token" in oracle:
            import re
            # Pattern: "Create X Y/Z tokens" or "Create five 2/2 tokens"
            m_token = re.search(
                r"create (?P<num>x|\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (?P<stats>\d+/\d+)?[^.]*tokens?",
                oracle,
            )
            if m_token:
                num_map = {
                    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3,
                    "four": 4, "five": 5, "six": 6, "seven": 7,
                    "eight": 8, "nine": 9, "ten": 10, "x": x_val if "X" in cost else 1,
                }
                val = m_token.group("num")
                if val == "x":
                    token_count = x_val if x_val > 0 else 1
                else:
                    token_count = num_map.get(val, int(val) if val.isdigit() else 1)

                stats = m_token.group("stats") if m_token.group("stats") else "1/1"

                # Extract keywords (haste, trample, flying, etc.)
                keywords = []
                if "haste" in oracle:
                    keywords.append("haste")
                if "trample" in oracle:
                    keywords.append("trample")
                if "flying" in oracle:
                    keywords.append("flying")
                if "vigilance" in oracle:
                    keywords.append("vigilance")
                if "lifelink" in oracle:
                    keywords.append("lifelink")

                # Create the tokens
                self.create_tokens(token_count, stats, keywords=keywords, verbose=verbose)
                if verbose:
                    kw_text = f" with {', '.join(keywords)}" if keywords else ""
                    print(f"  → {card.name} created {token_count} {stats} token(s){kw_text}")

        if verbose:
            print(f"Played instant: {card.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True

    def play_planeswalker(self, card, verbose=False):
        """Cast a planeswalker and move it to the battlefield."""
        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False
        Mana_utils.pay(card.mana_cost, self.mana_pool)
        if card in self.hand:
            self.hand.remove(card)
        self.planeswalkers.append(card)
        card.tapped = False

        # Y'shtola, Night's Blessed: Whenever you cast a noncreature spell with MV 3+
        if self.yshtola_on_board:
            from convert_dataframe_deck import parse_mana_cost
            cmc = parse_mana_cost(getattr(card, 'mana_cost', ''))
            if cmc >= 3:
                alive_opps = [o for o in self.opponents if o['is_alive']]
                for opp in alive_opps:
                    opp['life_total'] -= 2
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                self.gain_life(2, verbose=False)
                if verbose:
                    damage_dealt = 2 * len(alive_opps)
                    print(f"  🌙 Y'shtola triggers: {damage_dealt} damage to opponents, gained 2 life")

        if verbose:
            print(f"Played planeswalker: {card.name}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True

    def play_commander(self, card, verbose=False):
        """Cast your commander from the command zone or hand with command tax."""
        # Calculate total cost including command tax
        base_cost = card.mana_cost

        # Apply command tax ({2} per previous cast)
        tax_amount = self.commander_cast_count * 2

        # Check if we can pay base cost + tax
        if not Mana_utils.can_pay(base_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False

        # Pay base cost
        Mana_utils.pay(base_cost, self.mana_pool)

        # Pay command tax
        for _ in range(tax_amount):
            if not self.mana_pool:
                if verbose:
                    print(f"Not enough mana to pay command tax of {tax_amount}")
                return False
            self.mana_pool.pop(0)

        if card in self.command_zone:
            self.command_zone.remove(card)
        elif card in self.hand:
            self.hand.remove(card)
        else:
            if verbose:
                print(f"{card.name} is not available to be played")
            return False

        self.creatures.append(card)
        card.tapped = False
        self.commander_cast_count += 1

        if verbose:
            tax_msg = f" (+ {tax_amount} tax)" if tax_amount > 0 else ""
            print(f"Played commander: {card.name}{tax_msg}")
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True

    def play_basic_land(self, card, verbose=False):
        """Alias for playing a basic land."""
        return self.play_land(card, verbose)

    def activate_ability(self, card, ability, verbose=False):
        """Pay the cost of an activated ability and add its mana to the pool."""
        if getattr(ability, "requires_equipped", False) and not getattr(ability, "usable", True):
            if verbose:
                print(f"{card.name} is not equipped, ability unusable")
            return False
        if ability.tap and card not in self.lands_untapped:
            if verbose:
                print(f"{card.name} is already tapped")
            return False
        if not Mana_utils.can_pay(ability.cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to pay ability cost {ability.cost}")
            return False
        Mana_utils.pay(ability.cost, self.mana_pool)
        for col in ability.produces_colors or ['C']:
            self.mana_pool.append((col,))
        if ability.tap and card in self.lands_untapped:
            self.lands_untapped.remove(card)
            self.lands_tapped.append(card)
        if verbose:
            print(
                f"Activated {card.name} paying {ability.cost} to add {ability.produces_colors}"
            )
            print(f"Mana pool now: {self._mana_pool_str()}")
        return True


    def mana_sources_from_board(self, lands, artifacts, creatures):
        src = []
        for land in lands:
            # Lands with costed activated abilities do not provide coloured mana automatically
            if getattr(land, 'activated_abilities', []):
                zero_cost = [ab for ab in land.activated_abilities if not ab.cost and not ab.tap]
                if zero_cost:
                    for ab in zero_cost:
                        src.append(tuple(ab.produces_colors or ['C']))
                # otherwise these lands require activation and provide no free mana
                continue
            if not land.produces_colors:
                src.append(('C',))
            else:
                src.append(tuple(land.produces_colors))

        for art in artifacts:
            if art.name.lower() == 'sol ring':
                src += [('C',)] * 2
            elif art.name.lower() == 'arcane signet':
                src.append(('Any',))
            elif art.mana_production:
                for _ in range(int(art.mana_production)):
                    if not art.produces_colors:
                        src.append(('C',))
                    else:
                        src.append(tuple(art.produces_colors))

        for creature in creatures:
            if creature.mana_production and int(creature.mana_production) > 0:
                for _ in range(int(creature.mana_production)):
                    if not creature.produces_colors:
                        src.append(('C',))
                    else:
                        src.append(tuple(creature.produces_colors))

        return src

    # ─── play-logging helpers ──────────────────────────
    def cards_played_this_turn(self):
        return [c.name for t, c in self.play_log if t == self.turn]

    def cards_played_all_game(self):
        return [c.name for _, c in self.play_log]

    def cards_cast_this_turn(self):
        return [c.name for c in self.turn_casts]

    # ─────────────────────── Opponent Mechanics ──────────────────────────
    def generate_opponent_creatures(self, turn: int, verbose: bool = False):
        """Generate creatures for opponents based on turn number."""
        import random
        from simulate_game import Card

        # Each opponent gets creatures at a rate similar to the player
        for opp in self.opponents:
            if not opp['is_alive']:
                continue

            # Probability of adding a creature increases with turn number
            # Early game: 30% chance, Mid game: 50%, Late game: 70%
            base_prob = min(0.3 + (turn * 0.04), 0.7)

            if random.random() < base_prob:
                # Generate a creature with power/toughness appropriate for the turn
                # Early game: 2/2 or 3/3, Mid game: 3/3 to 5/5, Late game: 4/4 to 7/7
                power_range = (
                    max(2, turn // 3),
                    max(3, turn // 2 + 2)
                )
                power = random.randint(*power_range)
                toughness = random.randint(power - 1, power + 1)
                toughness = max(1, toughness)

                # Some creatures have keywords
                has_flying = random.random() < 0.25
                has_vigilance = random.random() < 0.15

                creature = Card(
                    name=f"{opp['name']}_creature_{len(opp['creatures'])+1}",
                    type="Creature",
                    mana_cost="",
                    power=power,
                    toughness=toughness,
                    produces_colors=[],
                    mana_production=0,
                    etb_tapped=False,
                    etb_tapped_conditions={},
                    has_haste=False,
                )
                opp['creatures'].append(creature)

                if verbose:
                    print(f"{opp['name']} gets a {power}/{toughness} creature")

    def calculate_threat_levels(self):
        """Calculate threat level for each opponent based on board state."""
        # Threat is based on total creature power
        all_powers = []
        for opp in self.opponents:
            if opp['is_alive']:
                total_power = sum(c.power or 0 for c in opp['creatures'])
                all_powers.append(total_power)

        if not all_powers or max(all_powers) == 0:
            return

        # Normalize threat levels
        max_power = max(all_powers)
        for opp in self.opponents:
            if opp['is_alive']:
                total_power = sum(c.power or 0 for c in opp['creatures'])
                opp['threat_level'] = total_power / max_power if max_power > 0 else 0

    def resolve_combat_with_blockers(self, verbose: bool = False):
        """Resolve combat with opponents having blockers."""
        import random

        if not self.creatures:
            return 0

        total_damage_dealt = 0
        life_gained = 0

        # Choose a random alive opponent to attack
        alive_opponents = [opp for opp in self.opponents if opp['is_alive']]
        if not alive_opponents:
            return 0

        # Attack the opponent with highest threat level (simple AI)
        target_opp = max(alive_opponents, key=lambda o: o.get('threat_level', 0))

        # Each creature attacks
        blocked_damage = 0
        unblocked_damage = 0
        creatures_died = []

        # Separate creatures by strike order (Phase 2 improvement)
        first_strike_creatures = []
        normal_strike_creatures = []

        for attacker in self.creatures[:]:
            has_first_strike = getattr(attacker, 'has_first_strike', False)
            has_double_strike = getattr(attacker, 'has_double_strike', False) or getattr(attacker, 'has_rally_double_strike', False)

            # Double strike creatures participate in both phases
            if has_double_strike:
                first_strike_creatures.append(attacker)
                normal_strike_creatures.append(attacker)
            elif has_first_strike:
                first_strike_creatures.append(attacker)
            else:
                normal_strike_creatures.append(attacker)

        # Process first strike damage first
        for strike_phase, attackers in [("first strike", first_strike_creatures), ("normal", normal_strike_creatures)]:
            for attacker in attackers:
                # PRIORITY 3: Use effective power/toughness including anthem bonuses
                attack_power = self.get_effective_power(attacker)
                attacker_toughness = self.get_effective_toughness(attacker)

                # Check for evasion/unblockable
                is_unblockable = getattr(attacker, 'is_unblockable', False)
                has_flying = getattr(attacker, 'has_flying', False)
                has_menace = getattr(attacker, 'has_menace', False)
                has_trample = getattr(attacker, 'has_trample', False)
                has_lifelink = getattr(attacker, 'is_lifelink', False) or getattr(attacker, 'has_rally_lifelink', False)
                has_deathtouch = getattr(attacker, 'has_deathtouch', False)
                has_double_strike = getattr(attacker, 'has_double_strike', False) or getattr(attacker, 'has_rally_double_strike', False)

                # GENERIC: Check for enchantments granting keywords to Allies
                attacker_type = getattr(attacker, 'type', '').lower()
                if 'ally' in attacker_type:
                    for enchantment in self.enchantments:
                        oracle = getattr(enchantment, 'oracle_text', '').lower()
                        # "Allies you control have double strike and lifelink"
                        if 'allies you control have' in oracle:
                            if 'double strike' in oracle:
                                has_double_strike = True
                            if 'lifelink' in oracle:
                                has_lifelink = True

                # Double strike: already handled by being in both phases
                # For damage calculation in each phase, treat as 1x
                damage_mult = 1

                if not target_opp['creatures'] or is_unblockable:
                    # No blockers or unblockable, damage goes through
                    damage = int(attack_power * self.damage_multiplier * damage_mult)
                    unblocked_damage += damage
                    if has_lifelink:
                        life_gained += damage
                    continue

                # Calculate block probability based on evasion
                base_block_prob = min(0.7, 0.3 + len(target_opp['creatures']) * 0.1)

                # Evasion reduces block chance
                if has_flying:
                    base_block_prob *= 0.5  # Flying is hard to block
                if has_menace:
                    base_block_prob *= 0.7  # Menace requires 2 blockers

                if random.random() < base_block_prob:
                    # Choose a random blocker
                    blocker = random.choice(target_opp['creatures'])
                    # Simplified: opponents don't get anthem bonuses (would need separate BoardState)
                    blocker_power = blocker.power or 0
                    blocker_toughness = blocker.toughness or 0

                    # Combat damage with deathtouch or trample
                    if has_deathtouch or attack_power >= blocker_toughness:
                        # Blocker dies
                        target_opp['creatures'].remove(blocker)
                        if verbose:
                            death_reason = "deathtouch" if has_deathtouch else "damage"
                            print(f"{attacker.name} destroyed {blocker.name} ({death_reason})")

                        # Trample: Excess damage tramples over
                        if has_trample:
                            excess_damage = max(0, attack_power - blocker_toughness)
                            unblocked_damage += int(excess_damage * self.damage_multiplier)
                            blocked_damage += int((attack_power - excess_damage) * self.damage_multiplier)
                            if verbose and excess_damage > 0:
                                print(f"  → {excess_damage} trample damage to {target_opp['name']}")
                        else:
                            blocked_damage += int(attack_power * self.damage_multiplier)
                    else:
                        # Blocker survives
                        blocked_damage += int(attack_power * self.damage_multiplier)

                    # Attacker takes damage from blocker (only in normal strike phase, not first strike)
                    if strike_phase == "normal" and blocker_power >= attacker_toughness:
                        # Attacker dies (unless it had first strike and already killed blocker)
                        if attacker not in creatures_died:
                            creatures_died.append(attacker)
                            if verbose:
                                print(f"{attacker.name} was destroyed by {blocker.name}")
                else:
                    # Unblocked
                    damage = int(attack_power * self.damage_multiplier * damage_mult)
                    unblocked_damage += damage
                    if has_lifelink:
                        life_gained += damage

        # Remove dead creatures (handle commander separately)
        for creature in creatures_died:
            if creature in self.creatures:
                self.creatures.remove(creature)
                if getattr(creature, 'is_commander', False):
                    self.command_zone.append(creature)
                else:
                    self.graveyard.append(creature)
                    self.reanimation_targets.append(creature)

                # ARISTOCRATS: Trigger full death effects!
                self.trigger_death_effects(creature, verbose=verbose)

        # Apply life gain from lifelink
        if life_gained > 0:
            self.life_total += life_gained
            if verbose:
                print(f"Gained {life_gained} life from lifelink")

        # Apply damage to opponent
        target_opp['life_total'] -= unblocked_damage

        # PRIORITY 2: Grim Hireling - create treasures when creatures deal combat damage
        if unblocked_damage > 0:
            for permanent in self.creatures + self.artifacts + self.enchantments:
                oracle = getattr(permanent, 'oracle_text', '').lower()
                name = getattr(permanent, 'name', '').lower()

                # Grim Hireling: "Whenever one or more creatures you control deal combat damage, create treasure"
                if 'grim hireling' in name or ('combat damage' in oracle and 'treasure' in oracle):
                    # Create treasures based on number of attacking creatures that dealt damage
                    num_attackers = len(self.creatures)
                    treasures_to_make = min(num_attackers, 3)  # Cap at 3 for balance
                    for _ in range(treasures_to_make):
                        self.create_treasure(verbose=verbose)

        # Track commander damage if commander dealt damage
        # Note: Commander damage should be tracked during the combat loop above
        # This is a simplified approach - assuming commander damage is proportional to unblocked damage
        if self.commander in self.creatures and unblocked_damage > 0:
            # PRIORITY 3: Use effective power including anthems
            commander_power = self.get_effective_power(self.commander)
            # Estimate commander contributed to damage based on its power vs total power
            total_power = sum(self.get_effective_power(c) for c in self.creatures)
            if total_power > 0:
                commander_contribution = round(unblocked_damage * commander_power / total_power)
                target_opp['commander_damage'] += commander_contribution

        total_damage_dealt = unblocked_damage

        if target_opp['life_total'] <= 0 or target_opp['commander_damage'] >= 21:
            target_opp['is_alive'] = False
            if verbose:
                reason = "commander damage" if target_opp['commander_damage'] >= 21 else "life loss"
                print(f"{target_opp['name']} has been eliminated by {reason}!")

        if verbose:
            print(f"Combat: {blocked_damage} damage blocked, {unblocked_damage} damage dealt to {target_opp['name']}")
            print(f"{target_opp['name']}'s life: {target_opp['life_total']}")

        return total_damage_dealt

    def simulate_removal(self, verbose: bool = False):
        """Simulate opponent removal spells targeting your creatures."""
        import random

        if not self.creatures:
            return

        # Each turn there's a chance one of your creatures gets removed
        if random.random() < self.removal_probability:
            # PRIORITY 3: Target the biggest threat (highest effective power including anthems)
            target = max(self.creatures, key=lambda c: self.get_effective_power(c))
            self.creatures.remove(target)

            # Commanders go back to command zone instead of graveyard
            if getattr(target, 'is_commander', False):
                self.command_zone.append(target)
                if verbose:
                    print(f"Opponent removed {target.name}! Returned to command zone.")
            else:
                self.graveyard.append(target)
                self.reanimation_targets.append(target)
                if verbose:
                    print(f"Opponent removed {target.name} from the battlefield!")

            self.creatures_removed += 1

            # ARISTOCRATS: Trigger death effects!
            self.trigger_death_effects(target, verbose=verbose)

    def simulate_board_wipe(self, verbose: bool = False):
        """Simulate a board wipe that destroys all creatures."""
        import random

        if random.random() < self.board_wipe_probability:
            # Board wipe happens
            num_creatures = len(self.creatures)

            if num_creatures > 0:
                # ARISTOCRATS: Board wipes trigger death effects for EACH creature!
                creatures_to_wipe = self.creatures[:]

                # Move all creatures to graveyard (except commander)
                for creature in creatures_to_wipe:
                    if getattr(creature, 'is_commander', False):
                        self.command_zone.append(creature)
                    else:
                        self.graveyard.append(creature)
                        self.reanimation_targets.append(creature)

                    # Trigger death effects for this creature
                    self.trigger_death_effects(creature, verbose=verbose)

                self.creatures.clear()
                self.wipes_survived += 1

                # Also destroy opponent creatures
                for opp in self.opponents:
                    opp['creatures'].clear()

                if verbose:
                    print(f"⚠️  BOARD WIPE! All {num_creatures} creatures destroyed!")

                return True

        return False

    def attempt_reanimation(self, verbose: bool = False):
        """Attempt to reanimate a creature from graveyard."""
        import random

        # Check if there are any reanimation spells/effects available
        # For simplicity, we'll check for high-value creatures in graveyard
        # and give a small chance to reanimate them

        if not self.reanimation_targets:
            return False

        # Reanimation probability based on turn and graveyard size
        reanimate_prob = min(0.05 + len(self.reanimation_targets) * 0.01, 0.15)

        if random.random() < reanimate_prob:
            # Reanimate the best creature (highest power)
            target = max(self.reanimation_targets, key=lambda c: c.power or 0)

            # Check if we have enough mana (rough estimate)
            if len(self.mana_pool) >= 4:  # Assume reanimation costs about 4 mana
                self.reanimation_targets.remove(target)
                if target in self.graveyard:
                    self.graveyard.remove(target)
                self.creatures.append(target)

                # Pay mana cost
                for _ in range(min(4, len(self.mana_pool))):
                    self.mana_pool.pop(0)

                if verbose:
                    print(f"♻️  Reanimated {target.name} from graveyard!")

                return True

        return False

    def reanimate_creature(self, target_creature=None, verbose: bool = False):
        """
        Reanimate a creature from the graveyard to the battlefield.

        This handles reanimation spells like:
        - Animate Dead
        - Reanimate
        - Necromancy
        - Living Death (mass reanimation)

        Args:
            target_creature: Specific creature to reanimate, or None to choose best
            verbose: Print output
        """
        # Get creatures in graveyard
        creatures_in_yard = [c for c in self.graveyard if 'creature' in getattr(c, 'type', '').lower()]

        if not creatures_in_yard:
            if verbose:
                print("  → No creatures in graveyard to reanimate")
            return False

        # Choose target (best creature by power if not specified)
        if target_creature is None:
            target = max(creatures_in_yard, key=lambda c: (c.power or 0) + (c.toughness or 0))
        else:
            target = target_creature

        # Move from graveyard to battlefield
        if target in self.graveyard:
            self.graveyard.remove(target)

        # PRIORITY FIX: Syr Konrad triggers when creature leaves graveyard
        self.trigger_syr_konrad_on_leave_graveyard(target, verbose=verbose)

        self.creatures.append(target)
        target.tapped = False

        # Track metrics
        self.creatures_reanimated += 1
        self.creatures_reanimated_this_turn += 1

        # Update reanimation targets list
        if target in self.reanimation_targets:
            self.reanimation_targets.remove(target)

        if verbose:
            print(f"♻️  Reanimated {target.name} ({target.power}/{target.toughness}) from graveyard!")

        # Trigger ETB effects
        self._execute_triggers("etb", target, verbose)

        # Apply drain from ETB triggers (Impact Tremors, Warleader's Call)
        drain_on_etb = self.calculate_etb_drain()
        if drain_on_etb > 0:
            self.drain_damage_this_turn += drain_on_etb
            if verbose:
                print(f"  → ETB drain: {drain_on_etb} damage (Impact Tremors/Warleader's Call)")

        return True

    def cast_living_death(self, spell, verbose: bool = False):
        """
        Cast Living Death: Mass reanimation spell.

        PRIORITY FIX: Living Death should return ALL creatures from graveyard,
        not just one. This is critical for graveyard decks.

        Living Death (Sorcery):
        Each player exiles all creature cards from their graveyard, then sacrifices
        all creatures they control, then puts all cards they exiled this way onto
        the battlefield.

        Args:
            spell: The Living Death card object
            verbose: Print detailed output
        """
        from boardstate import Mana_utils

        if not Mana_utils.can_pay(spell.mana_cost, self.mana_pool):
            return False

        # Pay mana cost
        Mana_utils.pay(spell.mana_cost, self.mana_pool)

        if verbose:
            print(f"\n💀 LIVING DEATH RESOLVES 💀")

        # Step 1: Exile all creatures from graveyard
        creatures_in_graveyard = [c for c in self.graveyard if 'creature' in c.type.lower()]
        for creature in creatures_in_graveyard:
            self.graveyard.remove(creature)

        if verbose:
            print(f"  → Exiled {len(creatures_in_graveyard)} creatures from graveyard")

        # Step 2: Sacrifice all creatures currently on battlefield
        creatures_to_sacrifice = self.creatures[:]
        for creature in creatures_to_sacrifice:
            # Trigger death effects (including Syr Konrad)
            self.trigger_death_effects(creature, verbose=verbose)

        self.creatures.clear()

        if verbose:
            print(f"  → Sacrificed {len(creatures_to_sacrifice)} creatures on battlefield")

        # Step 3: Return all exiled creatures to battlefield
        for creature in creatures_in_graveyard:
            self.creatures.append(creature)

            # Trigger Syr Konrad on leaving graveyard (even though they were exiled first)
            self.trigger_syr_konrad_on_leave_graveyard(creature, verbose=verbose)

            # Trigger ETB effects
            self._execute_triggers("etb", creature, verbose)

            # Reset summoning sickness
            creature._turns_on_board = 0

        total_power = sum(c.power or 0 for c in creatures_in_graveyard)

        if verbose:
            print(f"  → Returned {len(creatures_in_graveyard)} creatures ({total_power} total power)")
            if self.syr_konrad_on_board:
                print(f"  → Syr Konrad dealt {self.syr_konrad_triggers_this_turn * self.num_opponents} damage this turn")

        return True

    def attempt_muldrotha_casts(self, verbose: bool = False):
        """
        Try to cast permanents from graveyard with Muldrotha, the Gravetide.

        PRIORITY FIX P1: Muldrotha allows casting one permanent of each type
        from graveyard each turn. This is critical for graveyard value decks.

        Muldrotha ability: "During each of your turns, you may play up to one
        permanent card of each permanent type from your graveyard."

        Returns:
            int: Number of permanents cast from graveyard this attempt
        """
        if not self.muldrotha_on_board:
            return 0

        casts = 0
        permanent_types = ['creature', 'artifact', 'enchantment', 'land', 'planeswalker']

        for perm_type in permanent_types:
            # Skip if already cast this type this turn
            if self.muldrotha_casts_this_turn.get(perm_type, False):
                continue

            # Find best permanent of this type in graveyard
            candidates = [
                c for c in self.graveyard
                if perm_type in c.type.lower()
                and Mana_utils.can_pay(c.mana_cost, self.mana_pool)
            ]

            if not candidates:
                continue

            # Choose highest value card
            if perm_type == 'creature':
                best = max(candidates, key=lambda c: (c.power or 0) + (c.toughness or 0))
            elif perm_type == 'land':
                # For lands, prefer ones that produce colored mana
                colored_lands = [c for c in candidates if c.produces_colors and c.produces_colors != ['C']]
                best = colored_lands[0] if colored_lands else candidates[0]
            else:
                # For artifacts/enchantments, prefer higher mana cost (usually more powerful)
                from convert_dataframe_deck import parse_mana_cost
                best = max(candidates, key=lambda c: parse_mana_cost(c.mana_cost))

            # Cast from graveyard
            if self.play_card_from_graveyard(best, verbose):
                self.muldrotha_casts_this_turn[perm_type] = True
                casts += 1
                if verbose:
                    print(f"♻️  Muldrotha: Cast {best.name} from graveyard")

        return casts

    def play_card_from_graveyard(self, card, verbose: bool = False):
        """
        Cast a permanent from graveyard (Muldrotha, Conduit of Worlds, etc.).

        PRIORITY FIX P1: Allows casting from graveyard as if from hand.

        Args:
            card: Card object to cast from graveyard
            verbose: Print output

        Returns:
            bool: True if successfully cast, False otherwise
        """
        if card not in self.graveyard:
            return False

        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            return False

        # Remove from graveyard
        self.graveyard.remove(card)

        # Trigger Syr Konrad leaving graveyard
        if 'creature' in card.type.lower():
            self.trigger_syr_konrad_on_leave_graveyard(card, verbose=verbose)

        # Pay mana cost
        Mana_utils.pay(card.mana_cost, self.mana_pool)

        # Add to appropriate zone based on card type
        if 'creature' in card.type.lower():
            self.creatures.append(card)
            card._turns_on_board = 0  # Has summoning sickness
        elif 'artifact' in card.type.lower():
            self.artifacts.append(card)
        elif 'enchantment' in card.type.lower():
            self.enchantments.append(card)
        elif 'planeswalker' in card.type.lower():
            self.planeswalkers.append(card)
        elif 'land' in card.type.lower():
            # Playing land from graveyard counts as land drop
            if not getattr(card, 'etb_tapped', False):
                self.lands_untapped.append(card)
            else:
                self.lands_tapped.append(card)
                card.tapped = True

        # Trigger ETB effects
        self._execute_triggers("etb", card, verbose)

        if verbose:
            print(f"♻️  Cast {card.name} from graveyard")

        return True

    def has_zombie_on_board(self) -> bool:
        """
        Check if there's a Zombie creature on the battlefield.

        PRIORITY FIX P2: Needed for Gravecrawler recursion.
        """
        for creature in self.creatures:
            creature_type = getattr(creature, 'type', '').lower()
            oracle_text = getattr(creature, 'oracle_text', '').lower()
            name = getattr(creature, 'name', '').lower()

            # Check if it's a Zombie
            if 'zombie' in creature_type or 'zombie' in oracle_text:
                return True

            # Some creatures that create zombies or are zombies
            if any(z in name for z in ['gravecrawler', 'diregraf', 'undead', 'lich']):
                return True

        return False

    def attempt_gravecrawler_cast(self, verbose: bool = False):
        """
        Try to cast Gravecrawler from graveyard.

        PRIORITY FIX P2: Gravecrawler can be cast from graveyard if you control
        a Zombie. This provides infinite recursion value.

        Gravecrawler ability: "You may cast Gravecrawler from your graveyard
        as long as you control a Zombie."

        Returns:
            bool: True if Gravecrawler was cast, False otherwise
        """
        # Check if we control a Zombie
        if not self.has_zombie_on_board():
            return False

        # Find Gravecrawler in graveyard
        gravecrawler = None
        for card in self.graveyard:
            if 'gravecrawler' in card.name.lower():
                gravecrawler = card
                break

        if not gravecrawler:
            return False

        # Check if we can pay {B} (one black mana)
        if not Mana_utils.can_pay("{B}", self.mana_pool):
            return False

        # Cast from graveyard
        if self.play_card_from_graveyard(gravecrawler, verbose):
            if verbose:
                print(f"♻️  Gravecrawler cast from graveyard (zombie recursion)")
            return True

        return False

    def meren_end_step_trigger(self, verbose: bool = False):
        """
        Trigger Meren's end-step reanimation ability.

        PRIORITY FIX P2: Meren of Clan Nel Toth triggers at beginning of your
        end step to reanimate a creature from graveyard.

        Meren ability: "At the beginning of your end step, choose target creature
        card in your graveyard. If that card's mana value is less than or equal to
        the number of experience counters you have, return it to the battlefield.
        Otherwise, put it into your hand."

        Returns:
            bool: True if a creature was reanimated, False otherwise
        """
        if not self.meren_on_board:
            return False

        if self.meren_triggered_this_turn:
            return False

        # Find creatures in graveyard
        creatures_in_yard = [c for c in self.graveyard if 'creature' in c.type.lower()]

        if not creatures_in_yard:
            return False

        # Find best creature we can reanimate (CMC <= experience counters)
        from convert_dataframe_deck import parse_mana_cost

        reanimatable = []
        for creature in creatures_in_yard:
            cmc = parse_mana_cost(creature.mana_cost)
            if cmc <= self.experience_counters:
                reanimatable.append((creature, cmc))

        if not reanimatable:
            # If no creature fits, put highest value one in hand
            if creatures_in_yard:
                best = max(creatures_in_yard, key=lambda c: (c.power or 0) + (c.toughness or 0))
                if best in self.graveyard:
                    self.graveyard.remove(best)
                    self.hand.append(best)
                    self.meren_triggered_this_turn = True
                    if verbose:
                        print(f"♻️  Meren: Returned {best.name} to hand (CMC too high)")
                    return False
            return False

        # Choose best creature to reanimate (highest power + toughness)
        best_creature, cmc = max(reanimatable, key=lambda x: (x[0].power or 0) + (x[0].toughness or 0))

        # Reanimate it
        if self.reanimate_creature(target_creature=best_creature, verbose=False):
            self.meren_triggered_this_turn = True
            if verbose:
                print(f"♻️  Meren: Reanimated {best_creature.name} (CMC {cmc} <= {self.experience_counters} experience)")
            return True

        return False

    def tutor_to_graveyard(self, card_name: str = None, verbose: bool = False):
        """
        Tutor a card from library to graveyard.

        This handles graveyard tutors like:
        - Entomb
        - Buried Alive (gets 3 creatures)
        """
        if not self.library:
            return False

        # If specific card requested, find it
        if card_name:
            target = None
            for card in self.library:
                if card_name.lower() in getattr(card, 'name', '').lower():
                    target = card
                    break
        else:
            # Choose best creature to tutor
            creatures_in_library = [c for c in self.library if 'creature' in getattr(c, 'type', '').lower()]
            if creatures_in_library:
                target = max(creatures_in_library, key=lambda c: (c.power or 0) + (c.toughness or 0))
            else:
                target = None

        if target and target in self.library:
            self.library.remove(target)
            self.graveyard.append(target)

            # Add to reanimation targets
            if 'creature' in getattr(target, 'type', '').lower():
                if target not in self.reanimation_targets:
                    self.reanimation_targets.append(target)

            if verbose:
                print(f"  → Tutored {target.name} to graveyard")
            return True

        return False

    def discard_for_value(self, num_cards: int = 1, draw_cards: int = 0, verbose: bool = False):
        """
        Discard cards for value (like Faithless Looting).

        Args:
            num_cards: Number of cards to discard
            draw_cards: Number of cards to draw first
            verbose: Print output
        """
        # Draw first (Faithless Looting: draw 2, discard 2)
        if draw_cards > 0:
            self.draw_card(draw_cards, verbose=verbose)

        # Discard cards (prioritize lands and low-value spells, keep creatures)
        cards_discarded = 0
        for _ in range(min(num_cards, len(self.hand))):
            # Strategy: Discard lands first, then non-creatures
            discard_target = None

            # First priority: Extra lands
            lands_in_hand = [c for c in self.hand if 'land' in getattr(c, 'type', '').lower()]
            if len(lands_in_hand) > 3:  # Keep 3 lands, discard rest
                discard_target = lands_in_hand[0]

            # Second priority: Non-creature spells we can't cast
            if not discard_target:
                non_creatures = [c for c in self.hand if 'creature' not in getattr(c, 'type', '').lower() and 'land' not in getattr(c, 'type', '').lower()]
                if non_creatures:
                    discard_target = non_creatures[0]

            # Last resort: Discard anything
            if not discard_target and self.hand:
                discard_target = self.hand[0]

            if discard_target:
                self.hand.remove(discard_target)
                self.graveyard.append(discard_target)
                cards_discarded += 1

                # Track creatures for reanimation
                if 'creature' in getattr(discard_target, 'type', '').lower():
                    if discard_target not in self.reanimation_targets:
                        self.reanimation_targets.append(discard_target)

                if verbose:
                    print(f"  → Discarded {discard_target.name}")

        self.cards_discarded_for_value += cards_discarded
        return cards_discarded

    def activate_planeswalker(self, planeswalker, verbose: bool = False):
        """Activate a planeswalker ability."""
        import random

        if planeswalker not in self.planeswalkers:
            return False

        # Simple planeswalker simulation
        # Most planeswalkers have +1, -2, and ultimate abilities
        # We'll simulate the +1 (card advantage) or -2 (removal/value)

        ability_roll = random.random()

        if ability_roll < 0.6:
            # +1 ability: Usually card advantage
            self.draw_card(1, verbose=verbose)
            if verbose:
                print(f"{planeswalker.name} +1: Drew a card")
        elif ability_roll < 0.9:
            # -2 ability: Usually removal or tokens
            if self.creatures and random.random() < 0.5:
                # Buff a creature
                creature = random.choice(self.creatures)
                creature.add_counter("+1/+1", 2)
                if verbose:
                    print(f"{planeswalker.name} -2: Added +1/+1 counters to {creature.name}")
            else:
                # Create a token
                from simulate_game import Card
                token = Card(
                    name=f"{planeswalker.name}_token",
                    type="Creature",
                    mana_cost="",
                    power=2,
                    toughness=2,
                    produces_colors=[],
                    mana_production=0,
                    etb_tapped=False,
                    etb_tapped_conditions={},
                    has_haste=False,
                )
                self.creatures.append(token)
                if verbose:
                    print(f"{planeswalker.name} -2: Created a 2/2 token")

        return True

    # ─────────────────────── Token Mechanics ──────────────────────────
    def use_treasure_tokens(self, num_tokens: int, verbose: bool = False):
        """Sacrifice treasure tokens to add mana."""
        treasures = [c for c in self.artifacts if getattr(c, 'token_type', None) == 'Treasure']
        used = 0

        for treasure in treasures[:num_tokens]:
            self.artifacts.remove(treasure)
            self.mana_pool.append(('Any',))
            used += 1
            if verbose:
                print(f"Sacrificed Treasure token for mana")

        return used

    def use_food_token(self, verbose: bool = False):
        """Sacrifice food token to gain life."""
        foods = [c for c in self.artifacts if getattr(c, 'token_type', None) == 'Food']
        if foods:
            food = foods[0]
            self.artifacts.remove(food)
            self.life_total += 3
            if verbose:
                print(f"Sacrificed Food token, gained 3 life")
            return True
        return False

    def use_clue_token(self, verbose: bool = False):
        """Sacrifice clue token to draw a card."""
        clues = [c for c in self.artifacts if getattr(c, 'token_type', None) == 'Clue']
        if clues and len(self.mana_pool) >= 2:
            clue = clues[0]
            self.artifacts.remove(clue)
            # Pay 2 mana
            self.mana_pool.pop(0)
            self.mana_pool.pop(0)
            self.draw_card(1, verbose=verbose)
            if verbose:
                print(f"Sacrificed Clue token, drew a card")
            return True
        return False

    # ─────────────────────── Token Creation ──────────────────────────
    def create_tokens(self, count: int, stats: str = "1/1", creature_type: str = "Token", colors: str = "",
                     keywords: list = None, verbose: bool = False):
        """Create token creatures and add them to the battlefield.

        Args:
            count: Number of tokens to create
            stats: Power/Toughness as string (e.g. "1/1", "2/2")
            creature_type: Creature type (e.g. "Soldier", "Goblin")
            colors: Color identity (e.g. "W", "RG")
            keywords: List of keywords (e.g. ["haste", "flying"])
            verbose: Whether to print debug output
        """
        from simulate_game import Card  # Import here to avoid circular imports

        if keywords is None:
            keywords = []

        # Parse power/toughness
        if "/" in stats:
            power, toughness = stats.split("/")
            power = int(power)
            toughness = int(toughness)
        else:
            power = 1
            toughness = 1

        # Apply token multipliers (Anointed Procession, Doubling Season, etc.)
        actual_count = count * self.token_multiplier

        for i in range(actual_count):
            # Check for haste keyword
            has_haste = "haste" in [k.lower() for k in keywords]

            # Create token creature with all required arguments
            token = Card(
                name=f"{creature_type} Token",
                type=f"Creature — {creature_type}",
                mana_cost="",
                power=power,
                toughness=toughness,
                produces_colors=[],  # Tokens don't produce mana
                mana_production=0,  # Tokens don't produce mana
                etb_tapped=not has_haste,  # Tokens enter tapped unless they have haste
                etb_tapped_conditions={},  # No conditional ETB tapped
                has_haste=has_haste,
                oracle_text=f"Token creature with {', '.join(keywords) if keywords else 'no abilities'}",
            )

            # Add other keywords
            token.has_flying = "flying" in [k.lower() for k in keywords]
            token.has_vigilance = "vigilance" in [k.lower() for k in keywords]
            token.has_trample = "trample" in [k.lower() for k in keywords]
            token.has_lifelink = "lifelink" in [k.lower() for k in keywords]
            token.tapped = not has_haste  # Tokens enter tapped unless they have haste

            # Add to battlefield
            self.creatures.append(token)

            if verbose:
                print(f"Created {power}/{toughness} {creature_type} token" +
                     (f" with {', '.join(keywords)}" if keywords else ""))

        # Track token creation
        self.tokens_created_this_turn += actual_count

        return actual_count

    # ─────────────────────── Sacrifice Mechanics ──────────────────────────
    def sacrifice_creature(self, creature, verbose: bool = False):
        """Sacrifice a creature for value."""
        if creature not in self.creatures:
            return False

        # PRIORITY 3: Track effective power (including anthems) for sacrifice value
        sacrifice_power = self.get_effective_power(creature)

        self.creatures.remove(creature)
        self.creatures_sacrificed += 1
        self.sacrifice_value += sacrifice_power

        # Commander goes to command zone
        if getattr(creature, 'is_commander', False):
            self.command_zone.append(creature)
        else:
            self.graveyard.append(creature)
            self.reanimation_targets.append(creature)

        # Trigger death effects
        death_value = getattr(creature, 'death_trigger_value', 0)
        if death_value > 0:
            # Could be damage, card draw, etc - simplified as generic value
            if verbose:
                print(f"Death trigger from {creature.name}: {death_value} value")

        if verbose:
            print(f"Sacrificed {creature.name}")

        return True

    def find_sacrifice_outlet(self):
        """Find if there's a sacrifice outlet on board."""
        for permanent in self.creatures + self.artifacts + self.enchantments:
            if getattr(permanent, 'sacrifice_outlet', False):
                return permanent
        return None

    # ─────────────────────── Saga Mechanics ──────────────────────────
    def advance_sagas(self, verbose: bool = False):
        """Advance all sagas and trigger chapter abilities."""
        for saga in self.enchantments[:]:
            if not getattr(saga, 'is_saga', False):
                continue

            saga.saga_current_chapter += 1
            chapter = saga.saga_current_chapter

            if verbose:
                print(f"{saga.name} advanced to chapter {chapter}")

            # Trigger chapter ability
            chapters = getattr(saga, 'saga_chapters', [])
            if chapter <= len(chapters):
                effect = chapters[chapter - 1]
                # Execute chapter effect (simplified)
                if 'draw' in effect.lower():
                    self.draw_card(1, verbose=verbose)
                elif 'token' in effect.lower():
                    # Create a token
                    from simulate_game import Card
                    token = Card(
                        name="Saga Token",
                        type="Creature",
                        mana_cost="",
                        power=2,
                        toughness=2,
                        produces_colors=[],
                        mana_production=0,
                        etb_tapped=False,
                        etb_tapped_conditions={},
                        has_haste=False,
                    )
                    self.creatures.append(token)

            # Saga sacrifices itself after final chapter
            if chapter >= len(chapters):
                self.enchantments.remove(saga)
                self.graveyard.append(saga)
                if verbose:
                    print(f"{saga.name} completed and sacrificed")

    # ─────────────────────── AI Decision Making ──────────────────────────
    def prioritize_creature_for_casting(self, creature, verbose: bool = False):
        """
        Calculate a priority score for casting this creature.
        Higher score = higher priority to cast.

        Priority order (adjusted by deck archetype):
        1. Commander (highest priority)
        2. High-power legendary creatures (voltron targets)
        3. Creatures with attack triggers (draw, tokens)
        4. Creatures with ETB value (ramp, draw, tokens)
        5. Mana dorks
        6. Utility creatures
        7. Low-power creatures (weenies)

        SYNERGY-AWARE: Priorities are boosted based on detected deck archetype.
        """
        score = 100  # Base score
        oracle = getattr(creature, 'oracle_text', '').lower()

        # Priority 1: Commander
        if getattr(creature, 'is_commander', False):
            score += 1000
            if verbose:
                print(f"    Creature {creature.name}: Commander (+1000) = {score}")
            return score

        # SYNERGY-AWARE LOGIC: Apply archetype-specific priorities
        archetype_bonus = 0

        # Aristocrats archetype: Prioritize death triggers and sacrifice outlets
        if self.primary_archetype == 'Aristocrats':
            # Check for death triggers
            if 'dies' in oracle and ('opponent' in oracle or 'each player' in oracle):
                death_bonus = self.archetype_priorities.get('death_triggers', 850)
                archetype_bonus += death_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Aristocrats] Death trigger (+{death_bonus})")

            # Check for sacrifice outlets
            if 'sacrifice' in oracle and ':' in oracle:
                sac_bonus = self.archetype_priorities.get('sacrifice_outlets', 900)
                archetype_bonus += sac_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Aristocrats] Sacrifice outlet (+{sac_bonus})")

            # Token generators are valuable as fodder
            if 'create' in oracle and 'token' in oracle:
                token_bonus = self.archetype_priorities.get('token_generators_aristocrats', 750)
                archetype_bonus += token_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Aristocrats] Token generator (+{token_bonus})")

        # Tokens archetype: Prioritize token generators and doublers
        elif self.primary_archetype == 'Tokens':
            # Token doublers (highest priority)
            if 'twice that many' in oracle or 'double' in oracle and 'token' in oracle:
                double_bonus = self.archetype_priorities.get('token_doublers', 950)
                archetype_bonus += double_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Tokens] Token doubler (+{double_bonus})")

            # Token generators
            if 'create' in oracle and 'token' in oracle:
                gen_bonus = self.archetype_priorities.get('token_generators', 800)
                archetype_bonus += gen_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Tokens] Token generator (+{gen_bonus})")

            # Anthems (buff all creatures)
            if 'creatures you control get +' in oracle:
                anthem_bonus = self.archetype_priorities.get('token_anthems', 700)
                archetype_bonus += anthem_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Tokens] Anthem (+{anthem_bonus})")

        # Go-Wide archetype: Prioritize small creatures and anthems
        elif self.primary_archetype == 'Go-Wide':
            base_power = int(getattr(creature, 'power', 0) or 0)

            # Small creatures are good in go-wide
            if base_power <= 2:
                small_bonus = self.archetype_priorities.get('small_creatures', 700)
                archetype_bonus += small_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Go-Wide] Small creature (+{small_bonus})")

            # Anthems are critical
            if 'creatures you control get +' in oracle:
                anthem_bonus = self.archetype_priorities.get('anthem_effects', 850)
                archetype_bonus += anthem_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Go-Wide] Anthem (+{anthem_bonus})")

        # Counters archetype: Prioritize +1/+1 counters and proliferate
        elif self.primary_archetype == 'Counters':
            # Proliferate
            if 'proliferate' in oracle:
                prolif_bonus = self.archetype_priorities.get('proliferate', 900)
                archetype_bonus += prolif_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Counters] Proliferate (+{prolif_bonus})")

            # +1/+1 counter generation
            if '+1/+1 counter' in oracle:
                counter_bonus = self.archetype_priorities.get('counter_generators', 850)
                archetype_bonus += counter_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Counters] Counter generator (+{counter_bonus})")

            # Counter doublers
            if 'double' in oracle and 'counter' in oracle:
                double_bonus = self.archetype_priorities.get('counter_doublers', 950)
                archetype_bonus += double_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Counters] Counter doubler (+{double_bonus})")

        # Reanimator archetype: Prioritize mill/discard and big creatures
        elif self.primary_archetype == 'Reanimator':
            base_power = int(getattr(creature, 'power', 0) or 0)

            # Big creatures to reanimate
            if base_power >= 6:
                big_bonus = self.archetype_priorities.get('big_creatures', 650)
                archetype_bonus += big_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Reanimator] Big creature (+{big_bonus})")

            # Mill/discard outlets
            if 'mill' in oracle or 'discard' in oracle:
                mill_bonus = self.archetype_priorities.get('mill_effects', 700)
                archetype_bonus += mill_bonus
                if verbose:
                    print(f"    Creature {creature.name}: [Reanimator] Mill/discard (+{mill_bonus})")

        score += archetype_bonus

        # Priority 2: Legendary creatures with good stats (potential voltron targets)
        if getattr(creature, 'is_legendary', False):
            base_power = int(getattr(creature, 'power', 0) or 0)
            if base_power >= 3:
                legendary_bonus = 500 + (base_power * 10)
                score += legendary_bonus
                if verbose:
                    print(f"    Creature {creature.name}: Legendary with {base_power} power (+{legendary_bonus}) = {score}")

        # Priority 3: Attack triggers (card draw, tokens, treasures)
        if 'whenever' in oracle and 'attack' in oracle:
            if 'draw' in oracle:
                score += 300
                if verbose:
                    print(f"    Creature {creature.name}: Attack draw trigger (+300) = {score}")
            elif 'create' in oracle and 'token' in oracle:
                score += 250
                if verbose:
                    print(f"    Creature {creature.name}: Attack token trigger (+250) = {score}")
            elif 'treasure' in oracle:
                score += 200
                if verbose:
                    print(f"    Creature {creature.name}: Attack treasure trigger (+200) = {score}")
            else:
                score += 150
                if verbose:
                    print(f"    Creature {creature.name}: Attack trigger (+150) = {score}")

        # Priority 4: ETB value
        triggered_abilities = getattr(creature, 'triggered_abilities', [])
        for trigger in triggered_abilities:
            trigger_type = getattr(trigger, 'trigger_type', '')
            if trigger_type == 'etb':
                effect = getattr(trigger, 'effect', '')
                if 'draw' in effect:
                    score += 200
                    if verbose:
                        print(f"    Creature {creature.name}: ETB draw (+200) = {score}")
                elif 'create' in effect:
                    score += 150
                    if verbose:
                        print(f"    Creature {creature.name}: ETB token (+150) = {score}")
                elif 'search' in effect or 'tutor' in effect:
                    score += 180
                    if verbose:
                        print(f"    Creature {creature.name}: ETB tutor (+180) = {score}")
                else:
                    score += 100
                    if verbose:
                        print(f"    Creature {creature.name}: ETB trigger (+100) = {score}")

        # Priority 5: Mana dorks
        mana_production = int(getattr(creature, 'mana_production', 0) or 0)
        if mana_production > 0:
            score += 400  # Ramp is very valuable
            if verbose:
                print(f"    Creature {creature.name}: Mana dork (+400) = {score}")

        # Priority 6: Power matters (bigger creatures generally better)
        base_power = int(getattr(creature, 'power', 0) or 0)
        score += base_power * 5

        # Priority 7: Penalty for low power/toughness (weenies) - UNLESS it's a go-wide deck
        base_toughness = int(getattr(creature, 'toughness', 0) or 0)
        if base_power <= 1 and base_toughness <= 1 and self.primary_archetype != 'Go-Wide':
            score -= 50
            if verbose:
                print(f"    Creature {creature.name}: Weenie penalty (-50) = {score}")

        if verbose:
            print(f"    Creature {creature.name}: Final score = {score}")

        return score

    def get_best_creature_to_cast(self, verbose: bool = False):
        """
        Get the best creature from hand to cast, based on strategic priorities.
        Returns the creature with the highest priority score.
        """

        castable_creatures = [
            c for c in self.hand
            if "Creature" in c.type and Mana_utils.can_pay(c.mana_cost, self.mana_pool)
        ]

        if not castable_creatures:
            return None

        # Score each creature
        scored_creatures = [
            (c, self.prioritize_creature_for_casting(c, verbose=verbose))
            for c in castable_creatures
        ]

        # Sort by score (highest first)
        scored_creatures.sort(key=lambda x: x[1], reverse=True)

        best_creature, best_score = scored_creatures[0]

        if verbose:
            print(f"  AI: Best creature to cast: {best_creature.name} (score: {best_score})")
            if len(scored_creatures) > 1:
                print(f"      Other options:")
                for c, s in scored_creatures[1:]:
                    print(f"        - {c.name} (score: {s})")

        return best_creature

    def get_best_equipment_target(self, equipment, verbose: bool = False):
        """
        Get the best creature to attach equipment to.
        Prioritizes:
        1. Commander
        2. Legendary creatures with high power
        3. Creatures with attack triggers
        4. Creatures with keywords
        5. Highest power creature
        """
        if not self.creatures:
            return None

        scores = []
        for creature in self.creatures:
            score = 100  # Base score

            # Priority 1: Commander
            if getattr(creature, 'is_commander', False):
                score += 1000

            # Priority 2: Legendary creatures
            elif getattr(creature, 'is_legendary', False):
                score += 500

            # Priority 3: Creatures with attack triggers
            oracle = getattr(creature, 'oracle_text', '').lower()
            if 'whenever' in oracle and 'attack' in oracle:
                if 'draw' in oracle:
                    score += 300
                elif 'create' in oracle:
                    score += 200
                else:
                    score += 150

            # Priority 4: Keywords benefit from equipment
            if getattr(creature, 'has_first_strike', False):
                score += 50
            if getattr(creature, 'has_double_strike', False):
                score += 100
            if getattr(creature, 'has_trample', False):
                score += 30
            if getattr(creature, 'has_vigilance', False):
                score += 20

            # Priority 5: Current power (higher is better)
            current_power = int(getattr(creature, 'power', 0) or 0)
            score += current_power * 5

            scores.append((creature, score))

        # Sort by score (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)
        best_creature, best_score = scores[0]

        if verbose:
            print(f"  AI: Best equipment target for {equipment.name}: {best_creature.name} (score: {best_score})")

        return best_creature

    def should_hold_back_creature(self, creature, verbose: bool = False):
        """Decide if we should hold back a creature to avoid overextending."""
        import random

        # Calculate total opponent threat
        total_opp_power = sum(
            sum(c.power or 0 for c in opp['creatures'])
            for opp in self.opponents if opp['is_alive']
        )

        # If opponents have a lot of power, we might be facing a board wipe soon
        # Hold back our best creatures
        if total_opp_power > self.threat_threshold:
            # PRIORITY 3: Use effective power including anthems
            creature_power = self.get_effective_power(creature)
            our_power = sum(self.get_effective_power(c) for c in self.creatures)

            # Hold back if this is one of our best creatures and we already have board presence
            if creature_power >= 4 and our_power >= 8:
                if random.random() < 0.3:  # 30% chance to hold back
                    if verbose:
                        print(f"AI: Holding back {creature.name} to avoid overextending")
                    return True

        return False

    def should_mulligan(self, hand, verbose: bool = False):
        """Decide if we should mulligan this hand."""
        # Count lands
        lands = [c for c in hand if 'Land' in c.type]
        num_lands = len(lands)

        # Basic mulligan rules:
        # - 0-1 lands: mulligan
        # - 6-7 lands: mulligan
        # - 2-5 lands: keep
        if num_lands <= 1 or num_lands >= 6:
            if verbose:
                print(f"AI: Mulligan - {num_lands} lands is not keepable")
            return True

        return False

    def assess_primary_threat(self, verbose: bool = False):
        """Identify the most threatening opponent."""
        if not self.opponents:
            return None

        # Threat factors:
        # 1. Total creature power
        # 2. Number of creatures (wide board)
        # 3. Life total (low life = less threatening)

        max_threat = None
        max_threat_score = -1

        for opp in self.opponents:
            if not opp['is_alive']:
                continue

            power = sum(c.power or 0 for c in opp['creatures'])
            creature_count = len(opp['creatures'])
            life_factor = opp['life_total'] / 40.0  # Normalize life

            # Weighted threat score
            threat_score = (power * 0.6) + (creature_count * 2 * 0.3) + (life_factor * 5 * 0.1)

            if threat_score > max_threat_score:
                max_threat_score = threat_score
                max_threat = opp

        return max_threat

    def optimize_mana_usage(self, verbose: bool = False):
        """Try to use floating mana for activated abilities or instants."""
        import random

        # If we have leftover mana at end of turn, try to use it
        if len(self.mana_pool) == 0:
            return False

        # Try to activate abilities
        for ability in self.available_abilities:
            if ability.usable and Mana_utils.can_pay(ability.cost, self.mana_pool):
                # Use it with some probability
                if random.random() < 0.7:
                    card = ability.source
                    self.activate_ability(card, ability, verbose=verbose)
                    return True

        # Try to cast instant-speed spells
        for instant in [c for c in self.hand if 'Instant' in c.type]:
            if Mana_utils.can_pay(instant.mana_cost, self.mana_pool):
                if random.random() < 0.5:  # 50% chance to cast
                    self.play_instant(instant, verbose=verbose)
                    return True

        return False

    # ═══════════════════════════════════════════════════════════════════════
    # ARISTOCRATS MECHANICS (Priority 1 Implementation)
    # ═══════════════════════════════════════════════════════════════════════

    def create_token(self, token_name: str, power: int, toughness: int, has_haste: bool = False,
                     token_type: str = None, keywords: list = None, verbose: bool = False,
                     apply_counters: bool = True):
        """
        Create a creature token and add it to the battlefield.

        PRIORITY 2: Now supports token doublers (Mondrak, Doubling Season, etc.)

        Returns the created token Card object(s) - may be a list if doubled!
        """
        from simulate_game import Card

        # PRIORITY 2: Check for token doublers!
        num_to_create = 1
        token_doubler_names = []

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            perm_name = getattr(permanent, 'name', '')

            # Mondrak, Glory Dominus / Doubling Season / Parallel Lives / Anointed Procession
            # Check for token doubling effects with various phrasings
            is_token_doubler = False
            if 'token' in oracle:
                # Pattern 1: "if you would create" (Doubling Season, Parallel Lives)
                if 'if you would create' in oracle:
                    is_token_doubler = True
                # Pattern 2: "tokens would be created" (Mondrak, Anointed Procession)
                elif 'tokens would be created' in oracle or 'token would be created' in oracle:
                    is_token_doubler = True

            if is_token_doubler:
                if 'twice that many' in oracle or 'double' in oracle:
                    num_to_create *= 2
                    token_doubler_names.append(perm_name)
                    if verbose:
                        print(f"  → {perm_name} doubles tokens!")

        created_tokens = []

        for i in range(num_to_create):
            # Create token as a creature
            # Build type string including token_type if provided
            if token_type:
                type_line = f"Creature — {token_type} Token"
            else:
                type_line = "Creature — Token"

            token = Card(
                name=token_name,
                type=type_line,
                mana_cost="",
                power=power,
                toughness=toughness,
                produces_colors=[],
                mana_production=0,
                etb_tapped=False,
                etb_tapped_conditions={},
                has_haste=has_haste,
                token_type=token_type
            )

            # Apply keywords
            if keywords:
                for kw in keywords:
                    kw_lower = kw.lower()
                    if 'haste' in kw_lower:
                        token.has_haste = True
                    elif 'trample' in kw_lower:
                        token.has_trample = True
                    elif 'flying' in kw_lower:
                        token.has_flying = True
                    elif 'lifelink' in kw_lower:
                        token.has_lifelink = True

            # Add to battlefield
            self.creatures.append(token)
            created_tokens.append(token)

            # Trigger ETB effects
            self._execute_triggers("etb", token, verbose=verbose)

            # PRIORITY 2: Apply +1/+1 counters from Cathars' Crusade!
            if apply_counters:
                self.apply_etb_counter_effects(token, verbose=verbose)

            # Apply drain from ETB triggers (Impact Tremors, Warleader's Call)
            drain_on_etb = self.calculate_etb_drain()
            if drain_on_etb > 0:
                self.drain_damage_this_turn += drain_on_etb

        if verbose:
            if num_to_create > 1:
                print(f"Created {num_to_create}x {token_name} tokens ({power}/{toughness}) [DOUBLED!]")
            else:
                print(f"Created {token_name} token ({power}/{toughness})")

        return created_tokens if len(created_tokens) > 1 else created_tokens[0]

    def apply_etb_counter_effects(self, entering_creature, verbose: bool = False):
        """
        PRIORITY 2: Apply +1/+1 counters from ETB triggers like Cathars' Crusade.

        When a creature enters, check for effects that put counters on creatures.
        """
        counters_applied = False

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            perm_name = getattr(permanent, 'name', '')

            # Cathars' Crusade: "Whenever a creature enters, put a +1/+1 counter on each creature you control"
            if 'whenever a creature enters' in oracle or 'whenever a creature you control enters' in oracle:
                if '+1/+1 counter' in oracle:
                    # Put a counter on each creature (with doubling!)
                    for creature in self.creatures:
                        self.add_counters_with_doubling(creature, "+1/+1", 1, verbose=False)
                        counters_applied = True

                    if verbose:
                        print(f"  → {perm_name} added +1/+1 counters to {len(self.creatures)} creatures!")

        return counters_applied

    def remove_from_graveyard(self, card, verbose: bool = False):
        """
        Remove a card from graveyard and trigger Teval's ability if needed.

        This wrapper ensures we trigger "whenever cards leave your graveyard" effects.
        """
        if card in self.graveyard:
            self.graveyard.remove(card)

            # Check for Teval, the Balanced Scale
            for creature in self.creatures:
                if 'teval' in getattr(creature, 'name', '').lower() and 'balanced scale' in getattr(creature, 'name', '').lower():
                    # Create a 2/2 black Zombie Druid token
                    self.create_token("Zombie Druid", 2, 2, has_haste=False, verbose=verbose)
                    if verbose:
                        print(f"  → Teval created a 2/2 Zombie Druid token (card left graveyard)")
                    break  # Only trigger once per card leaving

    def mill_cards(self, num_cards: int, verbose: bool = False):
        """
        Mill cards from library to graveyard.

        PRIORITY FIX (P1): Aggressive mill to fill graveyard for recursion strategies.
        Also triggers Syr Konrad for each creature milled.

        Args:
            num_cards: Number of cards to mill
            verbose: Print output

        Returns:
            list: Cards that were milled
        """
        milled = []
        for _ in range(min(num_cards, len(self.library))):
            if not self.library:
                break
            card = self.library.pop(0)
            self.graveyard.append(card)
            milled.append(card)

        if verbose and milled:
            print(f"  → Milled {len(milled)} cards: {', '.join(c.name for c in milled[:3])}{' ...' if len(milled) > 3 else ''}")

        # Trigger Syr Konrad on mill
        self.trigger_syr_konrad_on_mill(milled, verbose)

        return milled

    def trigger_syr_konrad_on_mill(self, cards_milled: list, verbose: bool = False):
        """
        Trigger Syr Konrad when creatures are milled from library to graveyard.

        PRIORITY FIX: Syr Konrad, the Grim deals 1 damage to each opponent whenever
        a creature card is put into your graveyard from anywhere.
        """
        if not self.syr_konrad_on_board:
            return 0

        creature_count = sum(1 for card in cards_milled if 'creature' in card.type.lower())
        if creature_count > 0:
            # 1 damage per creature × 3 opponents in goldfish mode
            damage = creature_count * self.num_opponents
            self.drain_damage_this_turn += damage
            self.syr_konrad_triggers_this_turn += creature_count
            if verbose:
                print(f"⚡ Syr Konrad triggers {creature_count} times for {damage} damage (mill)")
            return damage
        return 0

    def trigger_syr_konrad_on_death(self, creature, verbose: bool = False):
        """
        Trigger Syr Konrad when a creature dies (goes from battlefield to graveyard).

        PRIORITY FIX: Syr Konrad deals damage when creatures die.
        """
        if not self.syr_konrad_on_board:
            return 0

        if 'creature' in creature.type.lower():
            damage = self.num_opponents  # 1 damage × number of opponents
            self.drain_damage_this_turn += damage
            self.syr_konrad_triggers_this_turn += 1
            if verbose:
                print(f"⚡ Syr Konrad triggers on {creature.name} death: {damage} damage")
            return damage
        return 0

    def trigger_syr_konrad_on_leave_graveyard(self, creature, verbose: bool = False):
        """
        Trigger Syr Konrad when a creature leaves the graveyard (reanimation/exile).

        PRIORITY FIX: Syr Konrad triggers when creatures leave graveyard.
        """
        if not self.syr_konrad_on_board:
            return 0

        if 'creature' in creature.type.lower():
            damage = self.num_opponents  # 1 damage × number of opponents
            self.drain_damage_this_turn += damage
            self.syr_konrad_triggers_this_turn += 1
            if verbose:
                print(f"⚡ Syr Konrad triggers on {creature.name} leaving graveyard: {damage} damage")
            return damage
        return 0

    def trigger_death_effects(self, creature, verbose: bool = False):
        """
        Trigger all death-based effects when a creature dies.

        This handles aristocrats payoffs like:
        - Zulaport Cutthroat
        - Cruel Celebrant
        - Bastion of Remembrance
        - Mirkwood Bats
        - The Ozolith (counter preservation)
        - Teysa Karlov (doubles death triggers!)
        """
        drain_total = 0

        # PRIORITY 2: Track creature deaths for Mahadi
        self.creatures_died_this_turn += 1

        # COUNTER MANIPULATION: The Ozolith - preserve counters
        self.handle_ozolith_on_death(creature, verbose=verbose)

        # PRIORITY FIX: Syr Konrad triggers on death
        self.trigger_syr_konrad_on_death(creature, verbose=verbose)

        # PRIORITY FIX P2: Meren experience counter gain
        if self.meren_on_board:
            self.experience_counters += 1
            if verbose:
                print(f"  → Meren: Gained experience counter (now {self.experience_counters})")

        # Check for death trigger doublers (Teysa Karlov, Parallel Lives for tokens, etc.)
        death_trigger_multiplier = 1
        for permanent in self.creatures + self.enchantments + self.artifacts:
            perm_name = getattr(permanent, 'name', '').lower()
            perm_oracle = getattr(permanent, 'oracle_text', '').lower()

            # Teysa Karlov: "If a creature dying causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time."
            if 'teysa karlov' in perm_name:
                death_trigger_multiplier = 2
                if verbose:
                    print(f"  → Teysa Karlov doubles death triggers!")
                break
            # Generic check for death trigger doublers
            elif 'dying causes' in perm_oracle and 'triggers an additional time' in perm_oracle:
                death_trigger_multiplier = 2
                if verbose:
                    print(f"  → {permanent.name} doubles death triggers!")
                break

        # Execute death triggers from all permanents
        for permanent in self.creatures + self.enchantments + self.artifacts:
            # NEW: Execute death triggers from triggered_abilities
            triggered_abilities = getattr(permanent, 'triggered_abilities', [])
            for ability in triggered_abilities:
                if ability.event == 'death':
                    # Execute death trigger (multiplied by Teysa!)
                    for _ in range(death_trigger_multiplier):
                        if verbose:
                            desc = ability.description
                            if death_trigger_multiplier > 1:
                                print(f"  → {permanent.name}: {desc} (doubled by Teysa!)")
                            else:
                                print(f"  → {permanent.name}: {desc}")

                        # Execute the trigger effect
                        try:
                            ability.effect(self)
                        except Exception as e:
                            if verbose:
                                print(f"    ⚠ Error executing death trigger: {e}")

            # LEGACY: Also support old death_trigger_value attribute for compatibility
            death_value = getattr(permanent, 'death_trigger_value', 0)
            # Handle case where death_value might be a list
            if isinstance(death_value, list):
                death_value = death_value[0] if death_value else 0
            death_value = int(death_value) if death_value else 0
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # Zulaport Cutthroat / Cruel Celebrant type effects (legacy support)
            if death_value > 0 and 'opponent' in oracle and 'loses' in oracle:
                # Each opponent loses X life (multiplied by death trigger doubler!)
                drain_per_opp = death_value * death_trigger_multiplier
                num_alive_opps = len([o for o in self.opponents if o['is_alive']])
                drain_total += drain_per_opp * num_alive_opps

                if verbose:
                    if death_trigger_multiplier > 1:
                        print(f"  → {permanent.name} drains {death_value} × {death_trigger_multiplier} (doubled!) × {num_alive_opps} opponents = {drain_per_opp * num_alive_opps}")
                    else:
                        print(f"  → {permanent.name} drains {drain_per_opp} × {num_alive_opps} opponents = {drain_per_opp * num_alive_opps}")

            # Pitiless Plunderer - create treasure (also doubled by Teysa!)
            # Skip if already handled by triggered_abilities
            if 'treasure' in oracle and 'dies' in oracle and not any(
                a.event == 'death' and 'Treasure' in a.description
                for a in getattr(permanent, 'triggered_abilities', [])
            ):
                treasures_to_create = 1 * death_trigger_multiplier
                for _ in range(treasures_to_create):
                    self.create_treasure(verbose=verbose)

        # Track total drain damage
        if drain_total > 0:
            self.drain_damage_this_turn += drain_total

            # Apply drain to opponents (evenly, with remainder to first opponent)
            alive_opps = [o for o in self.opponents if o['is_alive']]
            if alive_opps:
                drain_per_opp = drain_total // len(alive_opps)
                remainder = drain_total % len(alive_opps)

                for i, opp in enumerate(alive_opps):
                    # First opponent gets the remainder to avoid losing damage
                    opp_drain = drain_per_opp + (remainder if i == 0 else 0)
                    opp['life_total'] -= opp_drain

                    # Check if they died
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                        if verbose:
                            print(f"  → {opp['name']} eliminated by drain damage!")

        return drain_total

    def calculate_etb_drain(self) -> int:
        """
        Calculate drain damage from ETB triggers like Impact Tremors, Warleader's Call.

        Returns total drain damage per ETB.
        """
        drain = 0
        num_alive_opps = len([o for o in self.opponents if o['is_alive']])

        for permanent in self.enchantments + self.artifacts + self.creatures:
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # Impact Tremors / Warleader's Call
            if 'creature enters' in oracle or 'creature you control enters' in oracle:
                if 'deals 1 damage' in oracle or 'deal 1 damage' in oracle:
                    if 'each opponent' in oracle:
                        drain += 1 * num_alive_opps

        return drain

    def trigger_rally_abilities(self, entering_ally, verbose: bool = False):
        """
        Trigger Rally abilities when an Ally enters the battlefield.

        Rally abilities trigger on ALL Allies you control (including the one entering)
        when any Ally enters the battlefield.

        Common Rally effects:
        - Lantern Scout: Creatures you control gain lifelink until end of turn
        - Ondu Cleric: Gain life equal to the number of Allies you control
        - Kor Bladewhirl: Creatures you control gain first strike until end of turn
        - Chasm Guide: Creatures you control gain haste until end of turn
        """
        num_allies = sum(1 for c in self.creatures if 'ally' in getattr(c, 'type', '').lower())

        for ally in self.creatures:
            oracle = getattr(ally, 'oracle_text', '').lower()
            ally_name = getattr(ally, 'name', '').lower()

            # Check for Rally keyword or "whenever this creature or another ally enters"
            if 'rally' not in oracle and 'whenever' not in oracle:
                continue
            if 'ally' not in oracle and 'rally' not in oracle:
                continue

            # Ondu Cleric: "gain life equal to the number of Allies you control"
            if 'ondu cleric' in ally_name or ('gain life' in oracle and 'number of all' in oracle):
                life_gain = num_allies
                self.life_total += life_gain
                self.life_gained_this_turn += life_gain
                if verbose:
                    print(f"  → Rally: {ally.name} gains {life_gain} life ({num_allies} Allies)")

            # Lantern Scout: "creatures you control gain lifelink"
            elif 'lantern scout' in ally_name or ('gain lifelink' in oracle):
                # Mark creatures as having lifelink this turn (handled in combat)
                for creature in self.creatures:
                    creature.has_rally_lifelink = True
                if verbose:
                    print(f"  → Rally: {ally.name} grants lifelink to all creatures")

            # Kor Bladewhirl: "creatures you control gain first strike"
            elif 'kor bladewhirl' in ally_name or ('gain first strike' in oracle and 'rally' in oracle):
                for creature in self.creatures:
                    creature.has_rally_first_strike = True
                if verbose:
                    print(f"  → Rally: {ally.name} grants first strike to all creatures")

            # Chasm Guide: "creatures you control gain haste"
            elif 'chasm guide' in ally_name or ('gain haste' in oracle and 'rally' in oracle):
                for creature in self.creatures:
                    creature.tapped = False  # Haste means they can attack
                if verbose:
                    print(f"  → Rally: {ally.name} grants haste to all creatures")

            # Resolute Blademaster: "creatures you control gain double strike"
            elif 'resolute blademaster' in ally_name or ('gain double strike' in oracle and 'rally' in oracle):
                for creature in self.creatures:
                    creature.has_rally_double_strike = True
                if verbose:
                    print(f"  → Rally: {ally.name} grants double strike to all creatures")

    def handle_ozolith_on_death(self, creature, verbose: bool = False):
        """
        Handle The Ozolith when a creature dies.

        The Ozolith: "Whenever a creature you control leaves the battlefield,
        if it had counters on it, put those counters on The Ozolith."

        When creature dies, move its counters to self.ozolith_counters storage.
        """
        # Check if The Ozolith is on battlefield
        has_ozolith = False
        ozolith_card = None

        for artifact in self.artifacts:
            name = getattr(artifact, 'name', '').lower()
            oracle = getattr(artifact, 'oracle_text', '').lower()

            if 'ozolith' in name or 'the ozolith' in name:
                has_ozolith = True
                ozolith_card = artifact
                break

        if not has_ozolith:
            return

        # Get counters from dying creature
        creature_counters = getattr(creature, 'counters', {})

        if not creature_counters or sum(creature_counters.values()) == 0:
            return

        # Move counters to Ozolith storage
        for counter_type, amount in creature_counters.items():
            if amount > 0:
                self.ozolith_counters[counter_type] = self.ozolith_counters.get(counter_type, 0) + amount
                self.counters_moved_to_ozolith += amount

                if verbose:
                    print(f"  → The Ozolith: Stored {amount} {counter_type} counter(s) from {creature.name}")

    def move_ozolith_counters_to_creature(self, target_creature, verbose: bool = False):
        """
        Move counters from The Ozolith storage to a creature.

        At the beginning of combat, can move all Ozolith counters to target creature.
        """
        if not self.ozolith_counters:
            return False

        # Check if The Ozolith is still on battlefield
        has_ozolith = any(
            'ozolith' in getattr(artifact, 'name', '').lower()
            for artifact in self.artifacts
        )

        if not has_ozolith:
            return False

        # Move all counters to target
        for counter_type, amount in self.ozolith_counters.items():
            if amount > 0:
                # Use counter doubling if applicable
                actual_added = self.add_counters_with_doubling(
                    target_creature, counter_type, amount, verbose=verbose
                )

                if verbose:
                    print(f"  → The Ozolith: Moved {actual_added} {counter_type} counter(s) to {target_creature.name}")

        # Clear Ozolith storage
        self.ozolith_counters = {}
        return True

    def check_for_proliferate_triggers(self, verbose: bool = False):
        """
        Check for permanents that trigger proliferate.

        Common proliferate triggers:
        - Atraxa, Praetors' Voice: End step proliferate
        - Karn's Bastion: Activated ability
        - Evolution Sage: Landfall proliferate
        - Contagion Engine: Activated ability
        """
        should_proliferate = False

        for permanent in self.creatures + self.artifacts + self.enchantments + self.planeswalkers:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Atraxa: End step proliferate
            if 'atraxa' in name and 'end step' in oracle and 'proliferate' in oracle:
                should_proliferate = True
                if verbose:
                    print(f"  → {permanent.name} triggers proliferate!")
                break

            # Evolution Sage: Landfall proliferate
            if 'evolution sage' in name or ('landfall' in oracle and 'proliferate' in oracle):
                if self.lands_played_this_turn > 0:
                    should_proliferate = True
                    if verbose:
                        print(f"  → {permanent.name} triggers proliferate from landfall!")
                    break

            # Generic "whenever you..." proliferate triggers
            if 'proliferate' in oracle and ('whenever' in oracle or 'when' in oracle):
                # Simplified: Assume it triggers sometimes
                import random
                if random.random() < 0.3:  # 30% chance per turn
                    should_proliferate = True
                    if verbose:
                        print(f"  → {permanent.name} triggers proliferate!")
                    break

        if should_proliferate:
            self.proliferate(verbose=verbose)

        return should_proliferate

    def trigger_cast_effects(self, card, verbose: bool = False):
        """
        Trigger all cast-based effects when an instant or sorcery is cast.

        This handles spellslinger payoffs like:
        - Storm (Aetherflux Reservoir, Grapeshot)
        - Cast triggers (Guttersnipe, Young Pyromancer, Talrand)
        - Prowess/Magecraft (temporary power buffs)
        - Spell copy effects (Thousand-Year Storm)
        - Veyran trigger doubling
        """
        card_type = getattr(card, 'type', '').lower()

        # Only trigger for instants and sorceries
        if 'instant' not in card_type and 'sorcery' not in card_type:
            return

        # Increment spell counters
        self.spells_cast_this_turn += 1
        self.instant_sorcery_cast_this_turn += 1

        # Check if Veyran, Voice of Duality is on board (doubles magecraft triggers)
        veyran_on_board = False
        for permanent in self.creatures:
            name = getattr(permanent, 'name', '').lower()
            oracle = getattr(permanent, 'oracle_text', '').lower()
            if 'veyran' in name or (
                'casting or copying an instant or sorcery' in oracle and 'triggers an additional time' in oracle
            ):
                veyran_on_board = True
                if verbose:
                    print(f"  ⚡ Veyran, Voice of Duality is on board - doubling all magecraft triggers!")
                break

        # If Veyran is on board, triggers fire twice
        trigger_multiplier = 2 if veyran_on_board else 1

        spell_damage = 0
        tokens_created = 0
        cards_drawn = 0

        num_alive_opps = len([o for o in self.opponents if o['is_alive']])

        # Check all permanents for cast triggers
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Guttersnipe: Deal 2 damage to each opponent when you cast instant/sorcery
            if 'guttersnipe' in name or (
                'instant or sorcery' in oracle and 'deals 2 damage' in oracle and 'each opponent' in oracle
            ):
                # Veyran doubles this trigger
                damage = 2 * num_alive_opps * trigger_multiplier
                spell_damage += damage
                if verbose:
                    damage_text = f"{damage} damage"
                    if trigger_multiplier > 1:
                        damage_text += f" (doubled by Veyran)"
                    print(f"  → {permanent.name} deals {damage_text}")

            # Young Pyromancer: Create 1/1 Elemental when you cast instant/sorcery
            if 'young pyromancer' in name or (
                'instant or sorcery' in oracle and 'create a 1/1' in oracle and 'elemental' in oracle
            ):
                # Veyran doubles this trigger
                for _ in range(trigger_multiplier):
                    self.create_token(
                        token_name="Elemental Token",
                        power=1,
                        toughness=1,
                        token_type="Elemental",
                        verbose=verbose
                    )
                    tokens_created += 1
                if verbose:
                    tokens_text = f"{trigger_multiplier} Elemental token{'s' if trigger_multiplier > 1 else ''}"
                    print(f"  → {permanent.name} creates {tokens_text}")

            # Talrand, Sky Summoner: Create 2/2 Drake when you cast instant/sorcery
            if 'talrand' in name or (
                'instant or sorcery' in oracle and 'create a 2/2' in oracle and 'drake' in oracle
            ):
                # Veyran doubles this trigger
                for _ in range(trigger_multiplier):
                    self.create_token(
                        token_name="Drake Token",
                        power=2,
                        toughness=2,
                        token_type="Drake",
                        keywords=['Flying'],
                        verbose=verbose
                    )
                    tokens_created += 1
                if verbose:
                    tokens_text = f"{trigger_multiplier} Drake token{'s' if trigger_multiplier > 1 else ''}"
                    print(f"  → {permanent.name} creates {tokens_text} with flying")

            # Aetherflux Reservoir: Gain life equal to storm count
            if 'aetherflux reservoir' in name or (
                'cast a spell' in oracle and 'gain 1 life' in oracle and 'you\'ve cast' in oracle
            ):
                life_gained = self.spells_cast_this_turn
                self.life_total += life_gained
                if verbose:
                    print(f"  → {permanent.name} gains {life_gained} life (storm count: {self.spells_cast_this_turn})")

                # Check if we can activate the 50 damage ability
                if self.life_total >= 51:
                    # Deal 50 damage to target opponent
                    alive_opps = [o for o in self.opponents if o['is_alive']]
                    if alive_opps:
                        target = alive_opps[0]
                        target['life_total'] -= 50
                        spell_damage += 50
                        if verbose:
                            print(f"  → {permanent.name} ACTIVATED: Deal 50 damage to {target['name']}!")

                        # Check if they died
                        if target['life_total'] <= 0:
                            target['is_alive'] = False
                            if verbose:
                                print(f"  → {target['name']} eliminated by Aetherflux Reservoir!")

            # Archmage Emeritus: Draw a card when you cast/copy instant/sorcery
            if 'archmage emeritus' in name or (
                'instant or sorcery' in oracle and 'draw a card' in oracle and 'cast' in oracle
            ):
                self.draw_card(1, verbose=verbose)
                cards_drawn += 1
                if verbose:
                    print(f"  → {permanent.name} draws a card")

            # Storm-Kiln Artist: Create treasure when you cast/copy instant/sorcery
            if 'storm-kiln artist' in name or (
                'instant or sorcery' in oracle and 'create a treasure' in oracle and 'cast' in oracle
            ):
                # Veyran doubles this trigger
                for _ in range(trigger_multiplier):
                    self.create_treasure(verbose=verbose)
                if verbose:
                    treasures_text = f"{trigger_multiplier} Treasure token{'s' if trigger_multiplier > 1 else ''}"
                    print(f"  → {permanent.name} creates {treasures_text}")

            # Kykar, Wind's Fury: Create 1/1 Spirit token when you cast noncreature spell
            if 'kykar' in name or (
                'noncreature spell' in oracle and 'create a 1/1' in oracle and 'spirit' in oracle
            ):
                # Veyran doubles this trigger
                for _ in range(trigger_multiplier):
                    self.create_token(
                        token_name="Spirit Token",
                        power=1,
                        toughness=1,
                        token_type="Spirit",
                        keywords=['Flying'],
                        verbose=verbose
                    )
                    tokens_created += 1
                if verbose:
                    tokens_text = f"{trigger_multiplier} Spirit token{'s' if trigger_multiplier > 1 else ''}"
                    print(f"  → {permanent.name} creates {tokens_text} with flying")

            # Whirlwind of Thought: Draw a card when you cast noncreature spell
            if 'whirlwind of thought' in name or (
                'noncreature spell' in oracle and 'draw a card' in oracle and 'cast' in oracle
            ):
                # Veyran doubles this trigger
                for _ in range(trigger_multiplier):
                    self.draw_card(1, verbose=verbose)
                    cards_drawn += 1
                if verbose:
                    cards_text = f"{trigger_multiplier} card{'s' if trigger_multiplier > 1 else ''}"
                    print(f"  → {permanent.name} draws {cards_text}")

            # Jeskai Ascendancy: Untap creatures + +1/+1 buff when you cast noncreature spell
            if 'jeskai ascendancy' in name or (
                'noncreature spell' in oracle and 'untap' in oracle and 'creatures you control get +1/+1' in oracle
            ):
                # Untap all creatures
                for creature in self.creatures:
                    if hasattr(creature, 'tapped'):
                        creature.tapped = False

                # Apply +1/+1 until end of turn (temporary buff)
                # This is already handled by prowess-style bonuses, but Jeskai Ascendancy
                # is unique - it's a static buff until end of turn, not prowess
                for creature in self.creatures:
                    if creature not in self.prowess_bonus:
                        self.prowess_bonus[creature] = 0
                    self.prowess_bonus[creature] += 1

                if verbose:
                    print(f"  → {permanent.name} untaps all creatures and gives them +1/+1 until end of turn")

            # Primal Amulet / Primal Wellspring: Add charge counter, flip if 4+
            if 'primal amulet' in name:
                # Simplified: Just note we're getting cost reduction
                if verbose:
                    print(f"  → {permanent.name} adds charge counter")

        # Y'shtola, Night's Blessed: Whenever you cast a noncreature spell with MV 3+,
        # deal 2 damage to each opponent and gain 2 life
        # NOTE: This only handles instants/sorceries; artifacts/enchantments/planeswalkers are handled in their respective play_* functions
        if self.yshtola_on_board:
            from convert_dataframe_deck import parse_mana_cost
            cmc = parse_mana_cost(getattr(card, 'mana_cost', ''))
            if cmc >= 3:
                alive_opps = [o for o in self.opponents if o['is_alive']]
                for opp in alive_opps:
                    opp['life_total'] -= 2
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                self.gain_life(2, verbose=False)
                if verbose:
                    damage_dealt = 2 * len(alive_opps)
                    print(f"  🌙 Y'shtola, Night's Blessed triggers: dealt {damage_dealt} damage (2 to each opponent), gained 2 life")

        # Apply prowess/magecraft to all creatures
        self.apply_prowess_bonus()

        # Apply spell damage to opponents
        if spell_damage > 0:
            self.spell_damage_this_turn += spell_damage

            # Distribute damage to alive opponents (evenly, with remainder to first opponent)
            alive_opps = [o for o in self.opponents if o['is_alive']]
            if alive_opps:
                damage_per_opp = spell_damage // len(alive_opps)
                remainder = spell_damage % len(alive_opps)

                for i, opp in enumerate(alive_opps):
                    # First opponent gets the remainder to avoid losing damage
                    opp_damage = damage_per_opp + (remainder if i == 0 else 0)
                    opp['life_total'] -= opp_damage

                    # Check if they died
                    if opp['life_total'] <= 0:
                        opp['is_alive'] = False
                        if verbose:
                            print(f"  → {opp['name']} eliminated by spell damage!")

        return {
            'damage': spell_damage,
            'tokens': tokens_created,
            'cards_drawn': cards_drawn
        }

    def trigger_noncreature_spell_effects(self, card, verbose: bool = False):
        """
        Trigger effects when ANY noncreature spell is cast (instant, sorcery, artifact, enchantment, planeswalker).

        Uses ONLY generic oracle text parsing - no card-name-specific checks.

        Handles:
        - "Whenever you cast a noncreature spell, create a 1/1 [color] Ally creature token"
        - "Whenever you cast a noncreature spell, target creature you control can't be blocked this turn"
        - Prowess triggers for all creatures
        """
        card_type = getattr(card, 'type', '').lower()

        # Only trigger for noncreature spells
        if 'creature' in card_type and 'tribal' not in card_type:
            return

        tokens_created = 0

        # Check all creatures for noncreature spell triggers
        for creature in self.creatures:
            oracle = getattr(creature, 'oracle_text', '').lower()

            # GENERIC: "Whenever you cast a noncreature spell, create a 1/1 [color] Ally creature token"
            if 'whenever you cast a noncreature spell' in oracle and 'create' in oracle and 'ally' in oracle and 'token' in oracle:
                self.create_token(
                    token_name="Ally Token",
                    power=1,
                    toughness=1,
                    token_type="Ally",
                    verbose=verbose
                )
                tokens_created += 1
                if verbose:
                    print(f"  → {creature.name}: Created 1/1 Ally token")

            # GENERIC: "Whenever you cast a noncreature spell, target creature you control can't be blocked this turn"
            if 'whenever you cast a noncreature spell' in oracle and "can't be blocked" in oracle:
                if self.creatures:
                    # Choose the best attacker (highest power)
                    best_attacker = max(self.creatures, key=lambda c: self.get_effective_power(c))
                    best_attacker.is_unblockable = True
                    if verbose:
                        print(f"  → {creature.name}: {best_attacker.name} can't be blocked this turn")

        return {'tokens': tokens_created}

    def apply_prowess_bonus(self):
        """
        Apply prowess/magecraft bonuses to all creatures with those abilities.

        Prowess: +1/+1 until end of turn when you cast a noncreature spell
        Magecraft: Various effects when you cast/copy instant/sorcery

        Also handles creatures that grant prowess to others:
        - "Other Allies you control have prowess"
        - "Other creatures you control have prowess"
        """
        for creature in self.creatures:
            oracle = getattr(creature, 'oracle_text', '').lower()
            name = getattr(creature, 'name', '').lower()
            creature_type = getattr(creature, 'type', '').lower()

            has_prowess = False

            # Natural prowess on the creature itself
            if 'prowess' in oracle:
                has_prowess = True

            # Check all other permanents for prowess-granting effects
            for permanent in self.creatures:
                if permanent is creature:
                    continue
                perm_oracle = getattr(permanent, 'oracle_text', '').lower()

                # "Other Allies you control have prowess"
                if 'other allies you control have' in perm_oracle and 'prowess' in perm_oracle:
                    if 'ally' in creature_type:
                        has_prowess = True

                # "Other creatures you control have prowess"
                if 'other creatures you control have' in perm_oracle and 'prowess' in perm_oracle:
                    has_prowess = True

            if has_prowess:
                if creature not in self.prowess_bonus:
                    self.prowess_bonus[creature] = 0
                self.prowess_bonus[creature] += 1

            # Magecraft: Whenever you cast/copy instant/sorcery, +1/+1 until end of turn
            if 'magecraft' in oracle and ('+1/+1' in oracle or 'gets +' in oracle):
                if creature not in self.prowess_bonus:
                    self.prowess_bonus[creature] = 0
                self.prowess_bonus[creature] += 1

    def get_prowess_power_bonus(self, creature) -> int:
        """Get the current prowess power bonus for a creature."""
        return self.prowess_bonus.get(creature, 0)

    def reset_prowess_bonuses(self):
        """Reset prowess bonuses at end of turn."""
        self.prowess_bonus = {}

    def calculate_anthem_bonus(self, creature) -> tuple[int, int]:
        """
        Calculate the total power/toughness bonus from anthem effects.

        Returns (power_bonus, toughness_bonus).

        Handles anthem effects like:
        - Glorious Anthem: Creatures you control get +1/+1
        - Intangible Virtue: Tokens you control get +1/+1
        - Honor of the Pure: White creatures you control get +1/+1
        - Spear of Heliod: Creatures you control get +1/+1
        - Benalish Marshal: Creatures you control get +1/+1
        """
        power_bonus = 0
        toughness_bonus = 0

        creature_is_token = getattr(creature, 'token_type', None) is not None
        creature_name = getattr(creature, 'name', '').lower()

        # Check all permanents for anthem effects
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            perm_name = getattr(permanent, 'name', '').lower()

            # Skip self (creature doesn't buff itself)
            if permanent is creature:
                continue

            # Pattern 1: "Creatures you control get +X/+X"
            if 'creatures you control get +' in oracle or 'creature you control gets +' in oracle:
                # Parse the bonus (e.g., "+1/+1", "+2/+2")
                if '+1/+1' in oracle:
                    power_bonus += 1
                    toughness_bonus += 1
                elif '+2/+2' in oracle:
                    power_bonus += 2
                    toughness_bonus += 2
                elif '+3/+3' in oracle:
                    power_bonus += 3
                    toughness_bonus += 3

            # Pattern 2: "Tokens you control get +X/+X" (conditional on being a token)
            elif creature_is_token and ('tokens you control get +' in oracle or 'token creatures you control get +' in oracle):
                if '+1/+1' in oracle:
                    power_bonus += 1
                    toughness_bonus += 1
                elif '+2/+2' in oracle:
                    power_bonus += 2
                    toughness_bonus += 2

            # Pattern 3: "White creatures you control get +1/+1" (color-specific)
            elif 'white creatures you control get +' in oracle:
                # Simplified: assume most creatures benefit (proper implementation would check colors)
                if '+1/+1' in oracle:
                    power_bonus += 1
                    toughness_bonus += 1

            # Pattern 4: Door of Destinies - creatures of chosen type get +1/+1 per counter
            elif 'door of destinies' in perm_name or ('chosen type' in oracle and 'charge counter' in oracle):
                # Get charge counters on this permanent
                counters = getattr(permanent, 'counters', {}).get('charge', 0)
                if counters > 0:
                    # Check if creature matches chosen type (simplified: assume tribal match)
                    creature_type = getattr(creature, 'type', '').lower()
                    chosen_type = getattr(permanent, 'chosen_type', 'ally').lower()
                    if chosen_type in creature_type or 'ally' in creature_type:
                        power_bonus += counters
                        toughness_bonus += counters

            # Pattern 5: Obelisk of Urd - chosen creature type gets +2/+2
            elif 'obelisk of urd' in perm_name or ('creature type' in oracle and 'get +2/+2' in oracle):
                creature_type = getattr(creature, 'type', '').lower()
                chosen_type = getattr(permanent, 'chosen_type', 'ally').lower()
                if chosen_type in creature_type or 'ally' in creature_type:
                    power_bonus += 2
                    toughness_bonus += 2

            # Pattern 6: Banner of Kinship / Patchwork Banner - +1/+1 to creature type
            elif 'banner of kinship' in perm_name or 'patchwork banner' in perm_name:
                creature_type = getattr(creature, 'type', '').lower()
                chosen_type = getattr(permanent, 'chosen_type', 'ally').lower()
                if chosen_type in creature_type or 'ally' in creature_type:
                    power_bonus += 1
                    toughness_bonus += 1

        return (power_bonus, toughness_bonus)

    def get_effective_power(self, creature) -> int:
        """
        Get the effective power of a creature including anthem bonuses.

        This includes:
        - Base power
        - Equipment buffs (already applied to creature.power)
        - +1/+1 counters (already applied to creature.power)
        - Anthem effects (calculated dynamically)
        - Prowess/Magecraft bonuses (until end of turn)
        """
        base_power = creature.power or 0
        power_bonus, _ = self.calculate_anthem_bonuses(creature)
        prowess_bonus = self.prowess_bonus.get(creature, 0)
        return base_power + power_bonus + prowess_bonus

    def get_effective_toughness(self, creature) -> int:
        """
        Get the effective toughness of a creature including anthem bonuses.

        This includes:
        - Base toughness
        - Equipment buffs (already applied to creature.toughness)
        - +1/+1 counters (already applied to creature.toughness)
        - Anthem effects (calculated dynamically)
        """
        base_toughness = creature.toughness or 0
        _, toughness_bonus = self.calculate_anthem_bonuses(creature)
        return base_toughness + toughness_bonus

    def sacrifice_creature(self, creature, source_name: str = "sacrifice outlet", verbose: bool = False):
        """
        Sacrifice a creature and trigger death effects.

        Used for sacrifice outlets like:
        - Goblin Bombardment
        - Viscera Seer
        - Priest of Forgotten Gods
        """
        if creature not in self.creatures:
            return False

        # Remove from battlefield
        self.creatures.remove(creature)

        # Add to graveyard
        if getattr(creature, 'is_commander', False):
            self.command_zone.append(creature)
            if verbose:
                print(f"Sacrificed {creature.name} to {source_name} → command zone")
        else:
            self.graveyard.append(creature)
            self.reanimation_targets.append(creature)
            if verbose:
                print(f"Sacrificed {creature.name} to {source_name}")

        # Track sacrifice count
        self.creatures_sacrificed += 1

        # Trigger death effects (aristocrats payoffs!)
        drain = self.trigger_death_effects(creature, verbose=verbose)

        return True

    def create_treasure(self, verbose: bool = False):
        """Create a treasure token (artifact that taps for any color)."""
        from simulate_game import Card

        treasure = Card(
            name="Treasure Token",
            type="Artifact",
            mana_cost="",
            power=None,
            toughness=None,
            produces_colors=["Any"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            token_type="Treasure"
        )

        self.artifacts.append(treasure)

        if verbose:
            print(f"  → Created Treasure token")

        return treasure

    def simulate_attack_triggers(self, verbose: bool = False):
        """
        PRIORITY 2: Simulate "whenever you attack" triggers for token generation.

        Handles cards like:
        - Teval, the Balanced Scale (mill 3, return land, create tokens)
        - Adeline, Resplendent Cathar (create tokens = # of opponents)
        - Anim Pakal, Thousandth Moon (create X gnome tokens)
        - Brimaz, King of Oreskos (create 1/1 cat)
        - Hero of Bladehold (create 2 soldiers)
        - Generic attack triggers
        """
        tokens_created = 0

        if not self.creatures:
            return 0

        num_alive_opps = len([o for o in self.opponents if o['is_alive']])
        num_attacking = len(self.creatures)

        for creature in self.creatures[:]:  # Copy to avoid modification during iteration
            oracle = getattr(creature, 'oracle_text', '').lower()
            name = getattr(creature, 'name', '').lower()

            # Skip if no attack trigger (but Teval uses different trigger text)
            # Mobilize triggers when the creature attacks, so check for "mobilize" keyword
            if ('whenever you attack' not in oracle and
                'whenever ~ attacks' not in oracle and
                'whenever teval attacks' not in oracle and
                'mobilize' not in oracle):
                continue

            # === Specific Named Cards ===

            # TEVAL, THE BALANCED SCALE - Mill 3, return land from graveyard
            if 'teval' in name and 'balanced scale' in name:
                # Mill 3 cards
                self.mill_cards(3, verbose=verbose)
                if verbose:
                    print(f"  → Teval milled 3 cards")

                # Return a land card from graveyard to battlefield tapped
                land_cards = [c for c in self.graveyard if 'Land' in getattr(c, 'type', '')]
                if land_cards:
                    # Choose a land to return (prefer basic lands for consistency)
                    basic_lands = [c for c in land_cards if c.name in ['Forest', 'Swamp', 'Island', 'Mountain', 'Plains']]
                    land_to_return = basic_lands[0] if basic_lands else land_cards[0]

                    # Use the wrapper to trigger Teval's token creation
                    self.remove_from_graveyard(land_to_return, verbose=verbose)
                    self.lands_tapped.append(land_to_return)

                    if verbose:
                        print(f"  → Teval returned {land_to_return.name} from graveyard to battlefield tapped")

                    # Trigger landfall effects (for Ob Nixilis, etc.)
                    self._trigger_landfall(verbose=verbose)

            # Adeline, Resplendent Cathar - Create tokens = # of opponents
            elif 'adeline' in name:
                for _ in range(num_alive_opps):
                    self.create_token("Human Soldier", 1, 1, has_haste=True, verbose=verbose)
                    tokens_created += 1
                if verbose and num_alive_opps > 0:
                    print(f"  → Adeline created {num_alive_opps} Human tokens")

            # Anim Pakal, Thousandth Moon - Create X gnomes
            elif 'anim pakal' in name:
                num_gnomes = min(num_attacking, 5)  # Cap at 5
                for _ in range(num_gnomes):
                    self.create_token("Gnome Soldier", 1, 1, has_haste=True, verbose=verbose)
                    tokens_created += 1
                if verbose and num_gnomes > 0:
                    print(f"  → Anim Pakal created {num_gnomes} Gnome tokens")

            # Brimaz, King of Oreskos - Create 1/1 Cat token
            elif 'brimaz' in name:
                self.create_token("Cat Soldier", 1, 1, has_haste=False, verbose=verbose)
                tokens_created += 1
                if verbose:
                    print(f"  → Brimaz created 1 Cat token")

            # Wyleth, Soul of Steel - Draw cards equal to equipment/auras attached
            elif 'wyleth' in name and 'soul of steel' in name:
                equipment_count = sum(1 for eq, attached_creature in self.equipment_attached.items() if attached_creature is creature)
                if equipment_count > 0:
                    drawn = self.draw_card(equipment_count, verbose=verbose)
                    if verbose:
                        print(f"  → Wyleth drew {equipment_count} card(s) for equipment attached")

            # Cloud, Ex-SOLDIER - Draw for each equipped attacking creature, create treasures if 7+ power
            elif 'cloud' in name and 'ex-soldier' in name:
                # Count equipped attacking creatures (all attackers that have equipment)
                equipped_attackers = sum(1 for c in self.current_attackers if any(c is attached_creature for attached_creature in self.equipment_attached.values()))
                if equipped_attackers > 0:
                    drawn = self.draw_card(equipped_attackers, verbose=verbose)
                    if verbose:
                        print(f"  → Cloud drew {equipped_attackers} card(s) for equipped attacking creatures")

                # If Cloud has 7+ power, create 2 Treasures
                cloud_power = int(getattr(creature, 'power', 0) or 0)
                if cloud_power >= 7:
                    for _ in range(2):
                        self.create_treasure(verbose=verbose)
                    if verbose:
                        print(f"  → Cloud created 2 Treasure tokens (power {cloud_power} >= 7)")

            # Hero of Bladehold - Create 2 Soldier tokens
            elif 'hero of bladehold' in name:
                for _ in range(2):
                    self.create_token("Soldier", 1, 1, has_haste=False, keywords=['Battle cry'], verbose=verbose)
                    tokens_created += 1
                if verbose:
                    print(f"  → Hero of Bladehold created 2 Soldier tokens")

            # MOBILIZE - Parse "Mobilize N" keyword
            elif 'mobilize' in oracle:
                import re
                # Parse "Mobilize N" - creates N 1/1 red Warrior tokens that are sacrificed at end step
                match = re.search(r'mobilize (\d+)', oracle)
                if match:
                    mobilize_count = int(match.group(1))

                    # Create mobilize warriors (tapped and attacking)
                    for _ in range(mobilize_count):
                        warrior = self.create_token("Warrior", 1, 1, has_haste=True, verbose=verbose)
                        # Track this token to be sacrificed at end of turn
                        self.mobilize_tokens.append(warrior)
                        tokens_created += 1

                    if verbose and mobilize_count > 0:
                        print(f"  → {creature.name} mobilized {mobilize_count} Warrior token(s) (will sacrifice at end step)")

            # === Generic Token Creation ===
            # Parse oracle text for generic "create X token" triggers
            # Skip if mobilize (already handled above)
            elif 'create' in oracle and 'token' in oracle and 'mobilize' not in oracle:
                # Try to parse how many tokens
                num_tokens = 1  # Default

                # Look for patterns like "create a", "create one", "create two", etc.
                if 'create a ' in oracle or 'create one ' in oracle:
                    num_tokens = 1
                elif 'create two ' in oracle:
                    num_tokens = 2
                elif 'create three ' in oracle:
                    num_tokens = 3

                # Try to determine token type (generic)
                token_name = "Creature Token"
                token_power = 1
                token_toughness = 1

                # Common patterns: "1/1 white Soldier", "2/2 red Dragon", etc.
                if '1/1' in oracle:
                    token_power, token_toughness = 1, 1
                elif '2/2' in oracle:
                    token_power, token_toughness = 2, 2
                elif '3/3' in oracle:
                    token_power, token_toughness = 3, 3

                # Create the tokens
                for _ in range(num_tokens):
                    self.create_token(token_name, token_power, token_toughness, has_haste=False, verbose=verbose)
                    tokens_created += 1

                if verbose and num_tokens > 0:
                    print(f"  → {creature.name} created {num_tokens} {token_power}/{token_toughness} token(s)")

        return tokens_created

    def check_for_sacrifice_opportunities(self, verbose: bool = False):
        """
        Check if we should sacrifice creatures for value.

        Looks for sacrifice outlets and weak creatures to sac.
        """
        # Only sacrifice if we have:
        # 1. A sacrifice outlet
        # 2. Weak creatures (tokens, 1/1s)
        # 3. Death payoffs active

        has_sac_outlet = any(getattr(c, 'sacrifice_outlet', False)
                            for c in self.creatures + self.artifacts + self.enchantments)

        if not has_sac_outlet:
            return 0

        # Check for death payoffs
        death_payoffs = sum(1 for c in self.creatures + self.enchantments + self.artifacts
                          if getattr(c, 'death_trigger_value', 0) > 0)

        if death_payoffs == 0:
            return 0

        # Find weak creatures to sacrifice (tokens, low power)
        sacrificeable = [c for c in self.creatures
                        if (getattr(c, 'token_type', None) is not None or
                            (c.power or 0) <= 1)]

        if not sacrificeable:
            return 0

        # Sacrifice up to 2 weak creatures for value
        num_to_sac = min(2, len(sacrificeable))
        sac_count = 0

        for _ in range(num_to_sac):
            if sacrificeable:
                victim = sacrificeable.pop(0)
                self.sacrifice_creature(victim, "strategic sacrifice", verbose=verbose)
                sac_count += 1

        return sac_count

    def check_end_of_turn_treasures(self, creatures_died_this_turn: int, verbose: bool = False):
        """
        PRIORITY 2: Check for end-of-turn treasure generation (Mahadi, Smothering Tithe, etc.)

        Returns number of treasures created.
        """
        treasures_created = 0

        if creatures_died_this_turn == 0:
            return 0

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Mahadi, Emporium Master: "At beginning of end step, if creature died this turn, create treasures"
            if 'mahadi' in name or ('end' in oracle and 'creature died' in oracle and 'treasure' in oracle):
                # Create treasures equal to number of creatures that died (capped)
                num_treasures = min(creatures_died_this_turn, 5)  # Cap at 5
                for _ in range(num_treasures):
                    self.create_treasure(verbose=verbose)
                    treasures_created += 1

                if verbose and num_treasures > 0:
                    print(f"  → {permanent.name} created {num_treasures} Treasures (end of turn)")

        return treasures_created

    def sacrifice_mobilize_tokens(self, verbose: bool = False):
        """
        Sacrifice all mobilize warrior tokens at end of turn.

        Mobilize tokens are created tapped and attacking, then sacrificed at the beginning of the next end step.
        This triggers:
        - Death triggers (Zulaport Cutthroat, Cruel Celebrant, etc.)
        - Zurgo's "whenever a token leaves" drain trigger

        Returns number of tokens sacrificed.
        """
        sacs = 0

        # Sacrifice all tracked mobilize tokens
        for warrior in list(self.mobilize_tokens):
            if warrior in self.creatures:
                # Trigger Zurgo's "whenever a token leaves" BEFORE removing
                self.trigger_zurgo_token_leaves(warrior, was_attacking=True, verbose=verbose)

                # Sacrifice the warrior (triggers death effects)
                self.sacrifice_creature(warrior, "mobilize end-of-turn sacrifice", verbose=verbose)
                sacs += 1

        # Clear the list for next turn
        self.mobilize_tokens.clear()

        return sacs

    def trigger_zurgo_token_leaves(self, token, was_attacking: bool = True, verbose: bool = False):
        """
        Trigger Zurgo Stormrender's ability:
        "Whenever a creature token you control leaves the battlefield,
        draw a card if it was attacking. Otherwise, each opponent loses 1 life."

        Args:
            token: The token leaving the battlefield
            was_attacking: True if the token was attacking
        """
        # Check if Zurgo is on the battlefield
        zurgo = None
        for creature in self.creatures:
            if 'zurgo' in getattr(creature, 'name', '').lower() and 'stormrender' in getattr(creature, 'name', '').lower():
                zurgo = creature
                break

        if not zurgo:
            return

        # Zurgo's trigger: draw a card if attacking, otherwise drain 1 life per opponent
        if was_attacking:
            # Draw a card
            if self.library:
                drawn = self.library.pop(0)
                self.hand.append(drawn)
                if verbose:
                    print(f"  → Zurgo token-leave trigger: drew a card ({drawn.name})")
        else:
            # Each opponent loses 1 life
            num_alive_opps = len([o for o in self.opponents if o['is_alive']])
            if num_alive_opps > 0:
                if verbose:
                    print(f"  → Zurgo token-leave trigger: each opponent loses 1 life ({num_alive_opps} opponents)")

    # ═══════════════════════════════════════════════════════════════════════
    # UPKEEP TRIGGER SYSTEM (Priority 1 Implementation)
    # ═══════════════════════════════════════════════════════════════════════

    def process_upkeep_triggers(self, verbose: bool = False):
        """
        Process all "at the beginning of your upkeep" triggers.

        This handles cards like:
        - Rite of the Raging Storm (create 5/1 Elemental with haste)
        - Monarch (draw extra card at end of turn, tracked here)
        - Various enchantments and artifacts with upkeep triggers
        - Generic upkeep token creation, card draw, damage, etc.

        Returns number of tokens created during upkeep.
        """
        tokens_created = 0

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Skip if no upkeep trigger
            if 'beginning of' not in oracle or 'upkeep' not in oracle:
                continue

            # === Rite of the Raging Storm ===
            # "At the beginning of your upkeep, create a 5/1 red Elemental creature token with haste"
            if 'rite of the raging storm' in name:
                token = self.create_token("Elemental", 5, 1, has_haste=True, verbose=verbose)
                tokens_created += 1
                if verbose:
                    print(f"  → {permanent.name} created 5/1 Elemental token (upkeep)")

            # === Kemba, Kha Regent ===
            # "At the beginning of your upkeep, create a 2/2 white Cat creature token for each Equipment attached to Kemba, Kha Regent."
            elif 'kemba' in name and 'kha regent' in name:
                # Count equipment attached to this creature
                equipment_count = sum(1 for eq, creature in self.equipment_attached.items() if creature is permanent)
                for _ in range(equipment_count):
                    token = self.create_token("Cat", 2, 2, has_haste=False, verbose=verbose)
                    tokens_created += 1
                if verbose and equipment_count > 0:
                    print(f"  → {permanent.name} created {equipment_count}x 2/2 Cat token(s) (upkeep, one per equipment)")

            # === Generic Upkeep Token Creation ===
            # Parse oracle text for patterns like "create a X/X token" or "create X tokens"
            elif 'create' in oracle and 'token' in oracle:
                # Try to parse token stats
                import re

                # Pattern: "create a 1/1" or "create one 1/1"
                match = re.search(r'create (?:a|one|two|three) (\d+)/(\d+)', oracle)
                if match:
                    power = int(match.group(1))
                    toughness = int(match.group(2))

                    # Determine how many tokens
                    num_tokens = 1
                    if 'two' in oracle:
                        num_tokens = 2
                    elif 'three' in oracle:
                        num_tokens = 3

                    # Determine if haste
                    has_haste = 'haste' in oracle

                    for _ in range(num_tokens):
                        token = self.create_token(f"Token", power, toughness, has_haste=has_haste, verbose=verbose)
                        tokens_created += 1

                    if verbose:
                        print(f"  → {permanent.name} created {num_tokens}x {power}/{toughness} token(s) (upkeep)")

            # === Card Draw ===
            elif 'draw' in oracle and 'card' in oracle:
                # Parse how many cards
                import re
                match = re.search(r'draw (?:a|one|two|three|\d+) card', oracle)
                if match:
                    draw_text = match.group(0)
                    if 'a card' in draw_text or 'one card' in draw_text:
                        num_cards = 1
                    elif 'two card' in draw_text:
                        num_cards = 2
                    elif 'three card' in draw_text:
                        num_cards = 3
                    else:
                        # Try to extract number
                        num_match = re.search(r'\d+', draw_text)
                        num_cards = int(num_match.group(0)) if num_match else 1

                    drawn = self.draw_card(num_cards, verbose=verbose)
                    if verbose and drawn:
                        print(f"  → {permanent.name} drew {len(drawn)} card(s) (upkeep)")

            # === Life Gain/Loss ===
            elif 'gain' in oracle and 'life' in oracle:
                import re
                match = re.search(r'gain (\d+) life', oracle)
                if match:
                    life_gain = int(match.group(1))
                    self.life_gained_this_turn += life_gain
                    if verbose:
                        print(f"  → {permanent.name} gained {life_gain} life (upkeep)")

            elif 'lose' in oracle and 'life' in oracle and 'opponent' not in oracle:
                # Only if YOU lose life (not opponents)
                import re
                match = re.search(r'(?:you )?lose (\d+) life', oracle)
                if match:
                    life_loss = int(match.group(1))
                    self.life_lost_this_turn += life_loss
                    if verbose:
                        print(f"  → {permanent.name} lost {life_loss} life (upkeep)")

        return tokens_created

    def copy_creature_as_token(self, creature, make_nonlegendary=True, grant_haste=False, verbose=False):
        """
        Create a token copy of a creature with all its abilities and stats.
        Used for Helm of the Host, Miirym, token doublers with copy effects, etc.

        Args:
            creature: The creature to copy
            make_nonlegendary: Remove legendary status from the copy (default True)
            grant_haste: Grant haste to the token copy (default False)
            verbose: Print debug output

        Returns:
            The created token creature
        """
        from simulate_game import Card
        import copy as copy_module

        # Create a copy of the creature
        token = Card(
            name=f"{creature.name} Token",
            type=creature.type if not make_nonlegendary else creature.type.replace("Legendary ", ""),
            mana_cost="",  # Tokens have no mana cost
            power=creature.power,
            toughness=creature.toughness,
            produces_colors=getattr(creature, 'produces_colors', []),
            mana_production=getattr(creature, 'mana_production', 0),
            etb_tapped=False,  # Token copies enter untapped
            etb_tapped_conditions={},
            has_haste=grant_haste or getattr(creature, 'has_haste', False),
            has_flash=getattr(creature, 'has_flash', False),
            has_trample=getattr(creature, 'has_trample', False),
            has_first_strike=getattr(creature, 'has_first_strike', False),
            has_lifelink=getattr(creature, 'has_lifelink', False),
            has_deathtouch=getattr(creature, 'has_deathtouch', False),
            has_vigilance=getattr(creature, 'has_vigilance', False),
            has_flying=getattr(creature, 'has_flying', False),
            has_menace=getattr(creature, 'has_menace', False),
            is_unblockable=getattr(creature, 'is_unblockable', False),
            is_legendary=False if make_nonlegendary else getattr(creature, 'is_legendary', False),
            oracle_text=getattr(creature, 'oracle_text', ''),
        )

        # Copy triggered abilities (CRITICAL for Helm of the Host!)
        if hasattr(creature, 'triggered_abilities') and creature.triggered_abilities:
            token.triggered_abilities = copy_module.deepcopy(creature.triggered_abilities)

        # Copy +1/+1 counters
        if hasattr(creature, 'counters'):
            token.counters = copy_module.deepcopy(creature.counters)

        # Copy double strike
        if hasattr(creature, 'has_double_strike'):
            token.has_double_strike = creature.has_double_strike

        # Mark as token
        token.is_token = True
        token._turns_on_board = 0 if not grant_haste else 1  # Can attack if has haste

        # Add to battlefield
        self.creatures.append(token)

        if verbose:
            print(f"  → Created token copy of {creature.name} ({token.power}/{token.toughness})")
            if grant_haste:
                print(f"     Token has haste and can attack immediately")

        return token

    def process_beginning_of_combat_triggers(self, verbose: bool = False):
        """
        Process all "at the beginning of combat" triggers.

        This handles cards like:
        - Helm of the Host (create token copy of equipped creature)
        - Outlaws' Merriment (create random token)
        - Other combat-start triggers

        Returns number of tokens created during beginning of combat.
        """
        tokens_created = 0

        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Skip if no beginning of combat trigger
            if 'beginning of' not in oracle or 'combat' not in oracle:
                continue

            # === Helm of the Host ===
            # "At the beginning of combat on your turn, create a token that's a copy of equipped creature,
            # except the token isn't legendary. That token gains haste. Exile it at the beginning of the next end step."
            if 'helm of the host' in name:
                # Find what creature it's attached to
                equipped_creature = self.equipment_attached.get(permanent)
                if equipped_creature and equipped_creature in self.creatures:
                    # Create a non-legendary token copy with haste
                    token = self.copy_creature_as_token(
                        equipped_creature,
                        make_nonlegendary=True,
                        grant_haste=True,
                        verbose=verbose
                    )
                    tokens_created += 1

                    # Note: We don't implement the "exile at end step" part for simplicity
                    # This actually makes Helm of the Host STRONGER in simulation

                    if verbose:
                        print(f"  → Helm of the Host created token copy of {equipped_creature.name} (beginning of combat)")
                continue

            # === Ardenn, Intrepid Archaeologist ===
            # "At the beginning of combat on your turn, you may attach any number of Auras and Equipment you control to target permanent or player."
            if 'ardenn' in name and 'intrepid archaeologist' in name:
                # For simulation: attach all unattached equipment to the best creatures
                unattached_equipment = [eq for eq in self.artifacts if 'equipment' in getattr(eq, 'type', '').lower() and eq not in self.equipment_attached]

                if unattached_equipment and self.creatures:
                    # Prioritize creatures by power (highest first)
                    sorted_creatures = sorted(self.creatures, key=lambda c: int(getattr(c, 'power', 0) or 0), reverse=True)

                    for equipment in unattached_equipment:
                        if sorted_creatures:
                            target_creature = sorted_creatures[0]
                            # Move equipment without paying cost
                            buff = int(getattr(equipment, "power_buff", 0) or 0)
                            target_creature.power = int(target_creature.power or 0) + buff
                            target_creature.toughness = int(target_creature.toughness or 0) + buff
                            self.equipment_attached[equipment] = target_creature
                            self._apply_equipped_keywords(target_creature)

                            if verbose:
                                print(f"  → Ardenn moved {equipment.name} to {target_creature.name} (beginning of combat)")

            # === Outlaws' Merriment ===
            # "At the beginning of your combat on your turn, choose one at random:
            # - Create a 1/1 white Human, 1/1 red Mercenary with first strike, or 2/2 green Elf Druid"
            elif 'outlaws\' merriment' in name or 'outlaws merriment' in name:
                import random
                choice = random.choice([
                    ("Human Soldier", 1, 1, False),
                    ("Mercenary", 1, 1, False),  # Has first strike but we simplify
                    ("Elf Druid", 2, 2, False),
                ])

                token_name, power, toughness, has_haste = choice
                token = self.create_token(token_name, power, toughness, has_haste=has_haste, verbose=verbose)
                tokens_created += 1

                if verbose:
                    print(f"  → Outlaws' Merriment created {power}/{toughness} {token_name} token (beginning of combat)")

            # === Generic Beginning of Combat Token Creation ===
            elif 'create' in oracle and 'token' in oracle:
                # Similar parsing as upkeep
                import re
                match = re.search(r'create (?:a|one|two|three) (\d+)/(\d+)', oracle)
                if match:
                    power = int(match.group(1))
                    toughness = int(match.group(2))

                    num_tokens = 1
                    if 'two' in oracle:
                        num_tokens = 2
                    elif 'three' in oracle:
                        num_tokens = 3

                    has_haste = 'haste' in oracle

                    for _ in range(num_tokens):
                        token = self.create_token(f"Token", power, toughness, has_haste=has_haste, verbose=verbose)
                        tokens_created += 1

                    if verbose:
                        print(f"  → {permanent.name} created {num_tokens}x {power}/{toughness} token(s) (beginning of combat)")

        return tokens_created

    # ═══════════════════════════════════════════════════════════════════════
    # LANDFALL MECHANICS (Priority 3 Implementation)
    # ═══════════════════════════════════════════════════════════════════════

    def process_landfall_triggers(self, verbose: bool = False):
        """
        Process all landfall triggers after a land enters the battlefield.

        This handles specific landfall cards like:
        - Ob Nixilis, the Fallen (3 damage per land, grows)
        - Scute Swarm (create token copies)
        - Omnath variants (create elementals, gain life, draw cards, deal damage)
        - Avenger of Zendikar (buff plant tokens)
        - Generic landfall effects (tokens, counters, life gain)
        """
        triggered_count = 0

        # Check all permanents for landfall abilities
        for permanent in self.creatures + self.enchantments + self.artifacts:
            oracle = getattr(permanent, 'oracle_text', '').lower()
            name = getattr(permanent, 'name', '').lower()

            # Skip if no landfall trigger
            if 'landfall' not in oracle and 'land enters' not in oracle and 'whenever a land you control enters' not in oracle:
                continue

            triggered_count += 1

            # === OB NIXILIS, THE FALLEN ===
            if 'ob nixilis' in name and 'fallen' in name:
                # Deal 3 damage to target opponent
                alive_opps = [o for o in self.opponents if o['is_alive']]
                if alive_opps:
                    target = alive_opps[0]
                    target['life_total'] -= 3
                    self.drain_damage_this_turn += 3

                    if verbose:
                        print(f"  → Ob Nixilis dealt 3 damage to opponent (landfall)")

                # Put a +1/+1 counter on Ob Nixilis
                if hasattr(permanent, 'counters'):
                    permanent.counters += 1
                else:
                    permanent.counters = 1

                # Update power/toughness
                if hasattr(permanent, 'power') and permanent.power is not None:
                    permanent.power += 1
                if hasattr(permanent, 'toughness') and permanent.toughness is not None:
                    permanent.toughness += 1

                if verbose:
                    print(f"  → Ob Nixilis grew to {permanent.power}/{permanent.toughness}")

            # === SCUTE SWARM ===
            elif 'scute swarm' in name:
                self.handle_scute_swarm_landfall(permanent, verbose=verbose)

            # === OMNATH, LOCUS OF RAGE ===
            elif 'omnath, locus of rage' in name:
                self.handle_omnath_rage_landfall(verbose=verbose)

            # === OMNATH, LOCUS OF CREATION ===
            elif 'omnath, locus of creation' in name:
                self.handle_omnath_creation_landfall(verbose=verbose)

            # === OMNATH, LOCUS OF THE ROIL ===
            elif 'omnath, locus of the roil' in name or 'omnath, locus of roil' in name:
                self.handle_omnath_roil_landfall(verbose=verbose)

            # === AVENGER OF ZENDIKAR ===
            # Note: Avenger's main ability is ETB, landfall buffs existing plant tokens
            elif 'avenger of zendikar' in name:
                self.handle_avenger_landfall(verbose=verbose)

            # === GENERIC LANDFALL TOKEN CREATION ===
            elif 'create' in oracle and 'token' in oracle and 'landfall' in oracle:
                self.handle_generic_landfall_tokens(permanent, oracle, verbose=verbose)

            # === GENERIC LANDFALL COUNTERS ===
            elif '+1/+1 counter' in oracle and 'landfall' in oracle:
                self.handle_generic_landfall_counters(permanent, oracle, verbose=verbose)

            # === GENERIC LANDFALL LIFE GAIN ===
            elif 'gain' in oracle and 'life' in oracle and 'landfall' in oracle:
                self.handle_generic_landfall_life_gain(oracle, verbose=verbose)

            # PRIORITY FIX (P1): LANDFALL MILL (Hedron Crab, etc.)
            elif 'mill' in oracle and 'landfall' in oracle:
                mill_value = getattr(permanent, 'mill_value', 0)
                if mill_value > 0:
                    self.mill_cards(mill_value, verbose=verbose)

            # === GENERIC LANDFALL DAMAGE ===
            elif 'deals' in oracle and 'damage' in oracle and 'landfall' in oracle:
                self.handle_generic_landfall_damage(oracle, verbose=verbose)

        return triggered_count

    def handle_scute_swarm_landfall(self, scute_card, verbose: bool = False):
        """
        Scute Swarm: Landfall — Create a 1/1 green Insect token. If you control
        six or more lands, create a token that's a copy of Scute Swarm instead.
        """
        total_lands = len(self.lands_untapped) + len(self.lands_tapped)

        if total_lands >= 6:
            # Create a copy of Scute Swarm itself!
            from simulate_game import Card

            scute_copy = Card(
                name="Scute Swarm",
                type="Creature — Insect",
                mana_cost="2G",
                power=1,
                toughness=1,
                produces_colors=[],
                mana_production=0,
                etb_tapped=False,
                etb_tapped_conditions={},
                has_haste=False,
                oracle_text="Landfall — Whenever a land enters the battlefield under your control, create a 1/1 green Insect creature token. If you control six or more lands, create a token that's a copy of Scute Swarm instead."
            )

            self.creatures.append(scute_copy)

            # Apply ETB counter effects (like Cathars' Crusade)
            self.apply_etb_counter_effects(scute_copy, verbose=verbose)

            if verbose:
                print(f"  → Scute Swarm created a token COPY of itself! ({total_lands} lands)")
        else:
            # Create a 1/1 Insect token
            self.create_token("Insect", 1, 1, has_haste=False, verbose=verbose)

            if verbose:
                print(f"  → Scute Swarm created a 1/1 Insect token ({total_lands} lands)")

    def handle_omnath_rage_landfall(self, verbose: bool = False):
        """
        Omnath, Locus of Rage: Landfall — Create a 5/5 red and green Elemental token.
        """
        self.create_token("Elemental", 5, 5, has_haste=False, verbose=verbose)

        if verbose:
            print("  → Omnath, Locus of Rage created a 5/5 Elemental token!")

    def handle_omnath_creation_landfall(self, verbose: bool = False):
        """
        Omnath, Locus of Creation: Landfall — You gain 4 life.
        (Also: draw a card when playing first land, deal 4 damage when playing third land)
        """
        # Track landfall count for this Omnath
        lands_this_turn = self.lands_played_this_turn

        if lands_this_turn == 1:
            # First land: Draw a card
            self.draw_card(1, verbose=verbose)
            if verbose:
                print("  → Omnath, Locus of Creation: Drew a card (first land)")

        if lands_this_turn == 2:
            # Second land: Gain 4 life
            self.life_total += 4
            if verbose:
                print("  → Omnath, Locus of Creation: Gained 4 life (second land)")

        if lands_this_turn == 3:
            # Third land: Deal 4 damage to any target
            # Simplified: deal 4 damage to opponent
            alive_opps = [o for o in self.opponents if o['is_alive']]
            if alive_opps:
                target = alive_opps[0]
                target['life_total'] -= 4
                self.drain_damage_this_turn += 4
                if verbose:
                    print(f"  → Omnath, Locus of Creation: Dealt 4 damage to {target['name']} (third land)")

        if lands_this_turn >= 4:
            # Fourth+ land: All of the above
            if verbose:
                print("  → Omnath, Locus of Creation: Multiple triggers (4+ lands)!")

    def handle_omnath_roil_landfall(self, verbose: bool = False):
        """
        Omnath, Locus of the Roil: When Omnath enters or landfall triggers, put a +1/+1
        counter on target Elemental. That Elemental deals damage equal to its power to target.
        """
        # Find Elemental creatures to buff
        elementals = [c for c in self.creatures if 'elemental' in getattr(c, 'type', '').lower()]

        if elementals:
            # Buff the strongest elemental (with counter doubling!)
            target = max(elementals, key=lambda c: c.power or 0)
            self.add_counters_with_doubling(target, "+1/+1", 1, verbose=False)

            if verbose:
                print(f"  → Omnath, Locus of the Roil: Added +1/+1 counter to {target.name}")

            # Deal damage equal to its power
            damage = target.power or 0
            alive_opps = [o for o in self.opponents if o['is_alive']]
            if alive_opps and damage > 0:
                target_opp = alive_opps[0]
                target_opp['life_total'] -= damage
                self.drain_damage_this_turn += damage

                if verbose:
                    print(f"  → {target.name} deals {damage} damage to {target_opp['name']}")

    def handle_avenger_landfall(self, verbose: bool = False):
        """
        Avenger of Zendikar: Landfall — Put a +1/+1 counter on each Plant token you control.
        """
        # Find all Plant tokens
        plants = [c for c in self.creatures if 'plant' in getattr(c, 'name', '').lower()]

        if plants:
            for plant in plants:
                self.add_counters_with_doubling(plant, "+1/+1", 1, verbose=False)

            if verbose:
                print(f"  → Avenger of Zendikar: Added +1/+1 counters to {len(plants)} Plant tokens!")

    def handle_generic_landfall_tokens(self, permanent, oracle_text: str, verbose: bool = False):
        """
        Handle generic landfall token creation.

        Examples:
        - "Landfall — Create a 1/1 white Soldier token"
        - "Landfall — Create a 2/2 green Wolf token"
        """
        # Try to parse token stats
        import re

        # Look for "X/X [color] [type] token"
        token_pattern = r'(\d+)/(\d+)\s+(?:\w+\s+)?(\w+)\s+(?:creature\s+)?token'
        match = re.search(token_pattern, oracle_text)

        if match:
            power = int(match.group(1))
            toughness = int(match.group(2))
            token_type = match.group(3).capitalize()

            self.create_token(token_type, power, toughness, has_haste=False, verbose=verbose)

            if verbose:
                print(f"  → {permanent.name}: Created {power}/{toughness} {token_type} token (landfall)")
        else:
            # Default to 1/1 token
            self.create_token("Creature Token", 1, 1, has_haste=False, verbose=verbose)

    def handle_generic_landfall_counters(self, permanent, oracle_text: str, verbose: bool = False):
        """
        Handle generic landfall counter effects.

        Examples:
        - "Landfall — Put a +1/+1 counter on Scythe Leopard"
        - "Landfall — Put a +1/+1 counter on target creature"
        """
        # Put a +1/+1 counter on the source permanent (with doubling!)
        self.add_counters_with_doubling(permanent, "+1/+1", 1, verbose=False)

        if verbose:
            print(f"  → {permanent.name}: Added +1/+1 counter (landfall)")

    def handle_generic_landfall_life_gain(self, oracle_text: str, verbose: bool = False):
        """
        Handle generic landfall life gain.

        Examples:
        - "Landfall — You gain 1 life"
        - "Landfall — You gain 2 life"
        """
        import re

        # Look for "gain X life"
        life_pattern = r'gain (\d+) life'
        match = re.search(life_pattern, oracle_text)

        if match:
            life_gain = int(match.group(1))
            self.life_total += life_gain

            if verbose:
                print(f"  → Gained {life_gain} life (landfall)")

    def handle_generic_landfall_damage(self, oracle_text: str, verbose: bool = False):
        """
        Handle generic landfall damage.

        Examples:
        - "Landfall — This creature deals 1 damage to any target"
        - "Landfall — This creature deals 2 damage to each opponent"
        """
        import re

        # Look for "deals X damage"
        damage_pattern = r'deals (\d+) damage'
        match = re.search(damage_pattern, oracle_text)

        if match:
            damage = int(match.group(1))

            # Check if it's "each opponent"
            if 'each opponent' in oracle_text:
                alive_opps = [o for o in self.opponents if o['is_alive']]
                total_damage = damage * len(alive_opps)

                for opp in alive_opps:
                    opp['life_total'] -= damage

                self.drain_damage_this_turn += total_damage

                if verbose:
                    print(f"  → Dealt {damage} damage to each opponent (landfall)")
            else:
                # Deal to a single target
                alive_opps = [o for o in self.opponents if o['is_alive']]
                if alive_opps:
                    target = alive_opps[0]
                    target['life_total'] -= damage
                    self.drain_damage_this_turn += damage

                    if verbose:
                        print(f"  → Dealt {damage} damage (landfall)")

    # ═══════════════════════════════════════════════════════════════════════
    # TRIBAL EFFECTS MECHANICS
    # ═══════════════════════════════════════════════════════════════════════

    def choose_creature_type(self, card_name: str, verbose: bool = False) -> str:
        """
        Choose a creature type for a card that requires it.

        This method analyzes the deck to choose the most common creature type.

        Args:
            card_name: Name of the card choosing a type
            verbose: Whether to print debug output

        Returns:
            The chosen creature type as a string
        """
        # Count creature types in deck
        type_counts = {}

        # Check all creatures on battlefield
        for creature in self.creatures:
            creature_types = self._get_creature_types(creature)
            for ctype in creature_types:
                type_counts[ctype] = type_counts.get(ctype, 0) + 1

        # Check hand
        for card in self.hand:
            if 'creature' in card.get('type_line', '').lower():
                creature_types = self._get_creature_types(card)
                for ctype in creature_types:
                    type_counts[ctype] = type_counts.get(ctype, 0) + 1

        # Check library for creatures
        for card in self.library:
            if 'creature' in card.get('type_line', '').lower():
                creature_types = self._get_creature_types(card)
                for ctype in creature_types:
                    type_counts[ctype] = type_counts.get(ctype, 0) + 1

        # Choose the most common type, or default to "Human" if none found
        if type_counts:
            chosen_type = max(type_counts.items(), key=lambda x: x[1])[0]
        else:
            chosen_type = "Human"  # Default fallback

        # Store the chosen type
        self.chosen_creature_types[card_name] = chosen_type

        if verbose:
            print(f"  → {card_name} chose creature type: {chosen_type}")
            print(f"     (Type distribution: {dict(list(sorted(type_counts.items(), key=lambda x: -x[1]))[:5])})")

        return chosen_type

    def _get_creature_types(self, card: dict) -> list:
        """
        Extract creature types from a card.

        Args:
            card: Card dictionary

        Returns:
            List of creature type strings
        """
        type_line = card.get('type_line', '')

        # Check if it's a creature
        if 'creature' not in type_line.lower():
            return []

        # Check for changeling (has all types)
        oracle_text = card.get('oracle_text', '').lower()
        if 'changeling' in oracle_text or 'all creature types' in oracle_text:
            # For simulation purposes, treat changelings as matching any type
            return ['Changeling']

        # Parse subtypes from type line
        if '—' in type_line:
            try:
                _, subtypes_str = type_line.split('—', 1)
                subtypes = [s.strip() for s in subtypes_str.split() if s.strip()]
                return subtypes
            except ValueError:
                return []

        return []

    def apply_tribal_buff(self, card: dict, verbose: bool = False):
        """
        Apply tribal buff effects to creatures.

        This checks if a card grants buffs to specific creature types
        (e.g., "Goblins you control get +1/+1").

        Args:
            card: The card providing the buff
            verbose: Whether to print debug output
        """
        oracle_text = card.get('oracle_text', '').lower()
        card_name = card.get('name', 'Unknown')

        import re

        # Pattern for tribal anthem effects
        # Examples: "Goblins you control get +1/+1", "Elves you control have haste"
        buff_pattern = r'(\w+)s you control (?:get \+(\d+)/\+(\d+)|have (\w+))'
        matches = re.findall(buff_pattern, oracle_text)

        for match in matches:
            creature_type = match[0].capitalize()
            power_boost = int(match[1]) if match[1] else 0
            toughness_boost = int(match[2]) if match[2] else 0
            keyword = match[3] if match[3] else None

            buff_effect = {
                'source': card_name,
                'creature_type': creature_type,
                'power_boost': power_boost,
                'toughness_boost': toughness_boost,
                'keyword': keyword
            }

            self.tribal_buffs.append(buff_effect)

            if verbose:
                if keyword:
                    print(f"  → {card_name} grants {keyword} to {creature_type}s")
                else:
                    print(f"  → {card_name} grants +{power_boost}/+{toughness_boost} to {creature_type}s")

        # Pattern for "chosen type" effects
        chosen_pattern = r'creatures? of the chosen type (?:get \+(\d+)/\+(\d+)|have (\w+))'
        chosen_matches = re.findall(chosen_pattern, oracle_text)

        if chosen_matches:
            # Choose a type if not already chosen
            if card_name not in self.chosen_creature_types:
                self.choose_creature_type(card_name, verbose)

            chosen_type = self.chosen_creature_types.get(card_name, "Human")

            for match in chosen_matches:
                power_boost = int(match[0]) if match[0] else 0
                toughness_boost = int(match[1]) if match[1] else 0
                keyword = match[2] if match[2] else None

                buff_effect = {
                    'source': card_name,
                    'creature_type': chosen_type,
                    'power_boost': power_boost,
                    'toughness_boost': toughness_boost,
                    'keyword': keyword,
                    'is_chosen_type': True
                }

                self.tribal_buffs.append(buff_effect)

                if verbose:
                    if keyword:
                        print(f"  → {card_name} grants {keyword} to {chosen_type}s (chosen type)")
                    else:
                        print(f"  → {card_name} grants +{power_boost}/+{toughness_boost} to {chosen_type}s (chosen type)")

    def get_tribal_buffs_for_creature(self, creature: dict) -> tuple:
        """
        Calculate total tribal buffs for a creature.

        Args:
            creature: The creature to check

        Returns:
            Tuple of (power_boost, toughness_boost, keywords)
        """
        total_power = 0
        total_toughness = 0
        keywords = []

        creature_types = self._get_creature_types(creature)

        # Check if creature is a changeling (matches all types)
        is_changeling = 'Changeling' in creature_types

        for buff in self.tribal_buffs:
            buff_type = buff['creature_type']

            # Check if buff applies to this creature
            if is_changeling or buff_type in creature_types:
                total_power += buff['power_boost']
                total_toughness += buff['toughness_boost']
                if buff.get('keyword'):
                    keywords.append(buff['keyword'])

        return total_power, total_toughness, keywords

    def trigger_tribal_cast(self, card: dict, verbose: bool = False):
        """
        Trigger tribal cast abilities when a creature spell is cast.

        Examples: "Whenever you cast an Elf spell, draw a card"

        Args:
            card: The card being cast
            verbose: Whether to print debug output
        """
        if 'creature' not in card.get('type_line', '').lower():
            return

        creature_types = self._get_creature_types(card)
        card_name = card.get('name', 'Unknown')

        # Check all tribal triggers
        for trigger in self.tribal_triggers:
            if trigger.get('trigger_type') != 'cast':
                continue

            trigger_types = trigger.get('creature_types', [])
            trigger_source = trigger.get('source', 'Unknown')

            # Check if this creature matches the trigger
            matches = False
            if 'chosen' in trigger_types:
                # Check if any of this creature's types match a chosen type
                for chosen_type in self.chosen_creature_types.values():
                    if chosen_type in creature_types:
                        matches = True
                        break
            else:
                # Check for specific types
                for ctype in creature_types:
                    if ctype in trigger_types:
                        matches = True
                        break

            if matches:
                effect = trigger.get('effect', 'unknown')

                if verbose:
                    print(f"  → {trigger_source} triggered by casting {card_name}")

                # Apply the trigger effect
                if 'draw' in effect.lower():
                    self.draw_cards(1)
                    if verbose:
                        print(f"     Drew 1 card")
                elif 'damage' in effect.lower():
                    # Parse damage amount
                    import re
                    damage_match = re.search(r'(\d+) damage', effect)
                    if damage_match:
                        damage = int(damage_match.group(1))
                        alive_opps = [o for o in self.opponents if o['is_alive']]
                        if alive_opps:
                            alive_opps[0]['life_total'] -= damage
                            if verbose:
                                print(f"     Dealt {damage} damage")


class Mana_utils:
    
    def parse_req(cost_str):
        colours, generic, buf = [], 0, ''
        for ch in cost_str:
            if ch.isdigit():
                buf += ch
            else:
                if buf:
                    generic += int(buf); buf = ''
                if ch.isalpha():
                    colours.append(ch.upper())
        if buf:
            generic += int(buf)
        return colours, generic

    def pay(cost_str, pool):
        colours, generic = Mana_utils.parse_req(cost_str)
        for need in colours:
            for i,src in enumerate(pool):
                if need in src or 'Any' in src:
                    pool.pop(i)
                    break
        for _ in range(generic):
            if pool: pool.pop(0)

    def can_pay(cost_str, pool):
        colours, generic = Mana_utils.parse_req(cost_str)
        used = [False]*len(pool)
        def backtrack(i):
            if i == len(colours):
                return used.count(False) >= generic
            need = colours[i]
            for j,src in enumerate(pool):
                if used[j]: continue
                if need in src or 'Any' in src:
                    used[j] = True
                    if backtrack(i+1):
                        return True
                    used[j] = False
            return False
        return backtrack(0)
