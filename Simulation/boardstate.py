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

        # Interaction tracking
        self.removal_probability = 0.15  # 15% chance per turn a creature gets removed
        self.board_wipe_probability = 0.08  # 8% chance per turn of board wipe
        self.wipes_survived = 0
        self.creatures_removed = 0
        self.reanimation_targets = []  # Creatures that died and could be reanimated

        # AI decision-making
        self.hold_back_removal = True  # Don't always cast removal immediately
        self.threat_threshold = 15  # Don't overextend if opponent power is high
        self.removal_spells = []  # Track removal spells in hand
        self.instant_spells = []  # Track instant-speed spells for reactive play

    def _apply_equipped_keywords(self, creature):
        equipped = creature in self.equipment_attached.values()
        for kw in getattr(creature, "keywords_when_equipped", []):
            if kw.lower() == "first strike":
                creature.has_first_strike = bool(equipped)

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

    def _trigger_landfall(self, verbose: bool = False) -> None:
        """Execute all "landfall" triggers for permanents you control.

        Called whenever a land enters the battlefield under your control.
        Iterates over all permanents currently on the battlefield (including
        the land that just entered) and runs any triggered abilities whose
        event is ``"landfall"``.
        """

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
        """Cast your commander from the command zone or hand."""
        if not Mana_utils.can_pay(card.mana_cost, self.mana_pool):
            if verbose:
                print(f"Not enough mana to play {card.name}")
            return False
        Mana_utils.pay(card.mana_cost, self.mana_pool)
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
        if verbose:
            print(f"Played commander: {card.name}")
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
            attack_power = attacker.power or 0

            if not target_opp['creatures']:
                # No blockers, damage goes through
                unblocked_damage += attack_power
                continue

            # Opponent blocks with a probability based on their creature count
            # More creatures = more likely to block
            block_prob = min(0.7, 0.3 + len(target_opp['creatures']) * 0.1)

            if random.random() < block_prob:
                # Choose a random blocker
                blocker = random.choice(target_opp['creatures'])
                blocker_power = blocker.power or 0
                blocker_toughness = blocker.toughness or 0
                attacker_toughness = attacker.toughness or 0

                # Combat damage
                if attack_power >= blocker_toughness:
                    # Blocker dies
                    target_opp['creatures'].remove(blocker)
                    if verbose:
                        print(f"{attacker.name} destroyed {blocker.name}")

                if blocker_power >= attacker_toughness:
                    # Attacker dies
                    creatures_died.append(attacker)
                    if verbose:
                        print(f"{attacker.name} was destroyed by {blocker.name}")

                blocked_damage += attack_power
            else:
                # Unblocked
                unblocked_damage += attack_power

        # Remove dead creatures
        for creature in creatures_died:
            if creature in self.creatures:
                self.creatures.remove(creature)
                self.graveyard.append(creature)
                self.reanimation_targets.append(creature)

        # Apply damage to opponent
        target_opp['life_total'] -= unblocked_damage

        # Track commander damage if commander dealt damage
        if self.commander in self.creatures:
            commander_damage = self.commander.power or 0
            if random.random() >= block_prob:  # If not blocked
                target_opp['commander_damage'] += commander_damage

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
            # Target the biggest threat (highest power)
            target = max(self.creatures, key=lambda c: c.power or 0)
            self.creatures.remove(target)
            self.graveyard.append(target)
            self.reanimation_targets.append(target)
            self.creatures_removed += 1

            if verbose:
                print(f"Opponent removed {target.name} from the battlefield!")

    def simulate_board_wipe(self, verbose: bool = False):
        """Simulate a board wipe that destroys all creatures."""
        import random

        if random.random() < self.board_wipe_probability:
            # Board wipe happens
            num_creatures = len(self.creatures)

            if num_creatures > 0:
                # Move all creatures to graveyard
                for creature in self.creatures[:]:
                    self.graveyard.append(creature)
                    self.reanimation_targets.append(creature)

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
            creature_power = creature.power or 0
            our_power = sum(c.power or 0 for c in self.creatures)

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
