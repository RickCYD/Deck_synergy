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

        self.wipes_survived = 0
        self.creatures_removed = 0
        self.reanimation_targets = []  # Creatures that died and could be reanimated

        # AI decision-making
        self.hold_back_removal = True  # Don't always cast removal immediately
        self.threat_threshold = 15  # Don't overextend if opponent power is high
        self.removal_spells = []  # Track removal spells in hand
        self.instant_spells = []  # Track instant-speed spells for reactive play

        # Command Tax tracking
        self.commander_cast_count = 0  # Times commander has been cast
        self.command_tax = 0  # Additional mana cost ({2} per previous cast)

        # Combat keywords and modifiers
        self.damage_multiplier = 1.0  # For damage doublers like Fiery Emancipation
        self.token_multiplier = 1  # For token doublers like Doubling Season

        # Cost reduction
        self.cost_reduction = 0  # Generic cost reduction
        self.affinity_count = 0  # Artifacts for affinity

        # Sacrifice tracking
        self.creatures_sacrificed = 0
        self.sacrifice_value = 0  # Total power sacrificed

        # Aristocrats mechanics tracking
        self.drain_damage_this_turn = 0  # Track drain separate from combat
        self.tokens_created_this_turn = 0  # Track token generation
        self.creatures_died_this_turn = 0  # PRIORITY 2: For Mahadi treasure generation

        # Landfall mechanics tracking
        self.lands_played_this_turn = 0  # Track lands played this turn
        self.landfall_triggers_this_turn = 0  # Track number of landfall triggers

    def _apply_equipped_keywords(self, creature):
        equipped = creature in self.equipment_attached.values()
        for kw in getattr(creature, "keywords_when_equipped", []):
            if kw.lower() == "first strike":
                creature.has_first_strike = bool(equipped)

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

    def _execute_triggers(self, event: str, card, verbose=False):
        """Execute triggered abilities on *card* that match *event*.

        The engine recognises events such as ``"etb"`` (enters the
        battlefield), ``"equip"`` when an equipment becomes attached, and
        ``"attack"`` whenever a creature attacks.
        """
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
                print(f"Trigger on {card.name}: {trig.description}")
            trig.effect(self)
            if event == "attack":
                key = (id(card), id(trig))
                self._attack_triggers_fired.add(key)

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

    def proliferate(self, verbose: bool = False) -> None:
        """Give each permanent with counters another of each kind."""

        battlefield = (
            self.lands_untapped
            + self.lands_tapped
            + self.creatures
            + self.artifacts
            + self.enchantments
            + self.planeswalkers
        )

        for permanent in battlefield:
            counters = getattr(permanent, "counters", {})
            for ctype, amount in list(counters.items()):
                if amount > 0:
                    permanent.add_counter(ctype)
                    if verbose:
                        print(f"{permanent.name} proliferates a {ctype} counter")

    def attack(self, creature, verbose=False):
        """Declare *creature* as an attacker and handle attack triggers."""
        if creature not in self.creatures:
            if verbose:
                print(f"{creature.name} is not on the battlefield.")
            return False
        if self.current_combat_turn != self.turn:
            self.current_combat_turn = self.turn
            self.current_attackers = []
            self._attack_triggers_fired.clear()
        self.current_attackers.append(creature)
        self._apply_equipped_keywords(creature)
        for atk in list(self.current_attackers):
            self._execute_triggers("attack", atk, verbose)
        return True

    def draw_card(self,num_cards, verbose=False):
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
        if verbose:
            print(
                f"Hand now has {len(self.hand)} card(s); Library size: {len(self.library)}"
            )

        return drawn


    def play_card(self, card, verbose=False, cast=True):
        """Play *card* using the appropriate method or simply put it into play."""

        if getattr(card, "is_commander", False) or card.type.lower() == "commander":
            method = getattr(self, "play_commander", None)
        else:
            method = getattr(self, f"play_{card.type.replace(' ', '_').lower()}", None)
        if not callable(method):
            if verbose:
                print(f"Card type {card.type} not supported for play.")
            return False

        if cast:
            success = method(card, verbose)
        else:
            # put card directly onto the battlefield ignoring mana costs
            if card.type in ("Land", "Basic Land"):
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
                lst = zone_lists.get(card.type)
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
                self._execute_triggers("etb", card, verbose)
                if card.type in ("Land", "Basic Land"):
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
        lands = [c for c in self.hand if c.type in ("Land", "Basic Land")]
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
        land = next((c for c in self.library if c.type == "Basic Land"), None)
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
        if verbose:
            print(f"→ {card.name} enters the battlefield (artifact)")
        return True

    # ------ Equipment is a type of Artifact in MTG, so we can use the same method.	
    # If you have equipments that are NOT mana rocks you can add:
    def play_equipment(self, card, verbose=False):
        return self.play_artifact(card, verbose)

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
        if getattr(card, "draw_cards", 0) > 0:
            self.draw_card(getattr(card, "draw_cards"), verbose=verbose)
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
        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False
        Mana_utils.pay(card.mana_cost, self.mana_pool)
        if card in self.hand:
            self.hand.remove(card)
        self.graveyard.append(card)
        if getattr(card, "draw_cards", 0) > 0:
            self.draw_card(getattr(card, "draw_cards"), verbose=verbose)
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

        for attacker in self.creatures[:]:
            # PRIORITY 3: Use effective power/toughness including anthem bonuses
            attack_power = self.get_effective_power(attacker)
            attacker_toughness = self.get_effective_toughness(attacker)

            # Check for evasion/unblockable
            is_unblockable = getattr(attacker, 'is_unblockable', False)
            has_flying = getattr(attacker, 'has_flying', False)
            has_menace = getattr(attacker, 'has_menace', False)
            has_lifelink = getattr(attacker, 'has_lifelink', False)
            has_deathtouch = getattr(attacker, 'has_deathtouch', False)

            if not target_opp['creatures'] or is_unblockable:
                # No blockers or unblockable, damage goes through
                damage = int(attack_power * self.damage_multiplier)
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

                # Combat damage with deathtouch
                if has_deathtouch or attack_power >= blocker_toughness:
                    # Blocker dies
                    target_opp['creatures'].remove(blocker)
                    if verbose:
                        death_reason = "deathtouch" if has_deathtouch else "damage"
                        print(f"{attacker.name} destroyed {blocker.name} ({death_reason})")

                if blocker_power >= attacker_toughness:
                    # Attacker dies
                    creatures_died.append(attacker)
                    if verbose:
                        print(f"{attacker.name} was destroyed by {blocker.name}")

                blocked_damage += attack_power
            else:
                # Unblocked
                damage = int(attack_power * self.damage_multiplier)
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
                commander_contribution = int(unblocked_damage * commander_power / total_power)
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
        lands = [c for c in hand if c.type in ('Land', 'Basic Land')]
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
        for instant in [c for c in self.hand if c.type == 'Instant']:
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
            if 'if you would create' in oracle and 'token' in oracle:
                if 'twice that many' in oracle or 'double' in oracle:
                    num_to_create *= 2
                    token_doubler_names.append(perm_name)
                    if verbose:
                        print(f"  → {perm_name} doubles tokens!")

        created_tokens = []

        for i in range(num_to_create):
            # Create token as a creature
            token = Card(
                name=token_name,
                type="Creature — Token",
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
                    # Put a counter on each creature
                    for creature in self.creatures:
                        creature.add_counter("+1/+1", 1)
                        counters_applied = True

                    if verbose:
                        print(f"  → {perm_name} added +1/+1 counters to {len(self.creatures)} creatures!")

        return counters_applied

    def trigger_death_effects(self, creature, verbose: bool = False):
        """
        Trigger all death-based effects when a creature dies.

        This handles aristocrats payoffs like:
        - Zulaport Cutthroat
        - Cruel Celebrant
        - Bastion of Remembrance
        - Mirkwood Bats
        """
        drain_total = 0

        # PRIORITY 2: Track creature deaths for Mahadi
        self.creatures_died_this_turn += 1

        # Count all permanents with death triggers
        for permanent in self.creatures + self.enchantments + self.artifacts:
            death_value = getattr(permanent, 'death_trigger_value', 0)
            oracle = getattr(permanent, 'oracle_text', '').lower()

            # Zulaport Cutthroat / Cruel Celebrant type effects
            if death_value > 0 and 'opponent' in oracle and 'loses' in oracle:
                # Each opponent loses X life
                drain_per_opp = death_value
                num_alive_opps = len([o for o in self.opponents if o['is_alive']])
                drain_total += drain_per_opp * num_alive_opps

                if verbose:
                    print(f"  → {permanent.name} drains {drain_per_opp} × {num_alive_opps} opponents = {drain_per_opp * num_alive_opps}")

            # Pitiless Plunderer - create treasure
            if 'treasure' in oracle and 'dies' in oracle:
                self.create_treasure(verbose=verbose)

        # Track total drain damage
        if drain_total > 0:
            self.drain_damage_this_turn += drain_total

            # Apply drain to opponents
            alive_opps = [o for o in self.opponents if o['is_alive']]
            if alive_opps:
                drain_per_opp = drain_total // len(alive_opps)
                for opp in alive_opps:
                    opp['life_total'] -= drain_per_opp

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

        return (power_bonus, toughness_bonus)

    def get_effective_power(self, creature) -> int:
        """
        Get the effective power of a creature including anthem bonuses.

        This includes:
        - Base power
        - Equipment buffs (already applied to creature.power)
        - +1/+1 counters (already applied to creature.power)
        - Anthem effects (calculated dynamically)
        """
        base_power = creature.power or 0
        power_bonus, _ = self.calculate_anthem_bonus(creature)
        return base_power + power_bonus

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
        _, toughness_bonus = self.calculate_anthem_bonus(creature)
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

            # Skip if no attack trigger
            if 'whenever you attack' not in oracle and 'whenever ~ attacks' not in oracle:
                continue

            # === Specific Named Cards ===

            # Adeline, Resplendent Cathar - Create tokens = # of opponents
            if 'adeline' in name:
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

            # Hero of Bladehold - Create 2 Soldier tokens
            elif 'hero of bladehold' in name:
                for _ in range(2):
                    self.create_token("Soldier", 1, 1, has_haste=False, keywords=['Battle cry'], verbose=verbose)
                    tokens_created += 1
                if verbose:
                    print(f"  → Hero of Bladehold created 2 Soldier tokens")

            # === Generic Token Creation ===
            # Parse oracle text for generic "create X token" triggers
            elif 'create' in oracle and 'token' in oracle:
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

    # ═══════════════════════════════════════════════════════════════════════
    # LANDFALL MECHANICS (Priority 3 Implementation)
    # ═══════════════════════════════════════════════════════════════════════

    def process_landfall_triggers(self, verbose: bool = False):
        """
        Process all landfall triggers after a land enters the battlefield.

        This handles specific landfall cards like:
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
            if 'landfall' not in oracle and 'land enters' not in oracle:
                continue

            triggered_count += 1

            # === SCUTE SWARM ===
            if 'scute swarm' in name:
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
            # Buff the strongest elemental
            target = max(elementals, key=lambda c: c.power or 0)
            target.add_counter("+1/+1", 1)

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
                plant.add_counter("+1/+1", 1)

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
        # Put a +1/+1 counter on the source permanent
        if hasattr(permanent, 'add_counter'):
            permanent.add_counter("+1/+1", 1)

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
