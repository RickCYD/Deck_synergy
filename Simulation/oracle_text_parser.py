import re
import ast
import json
import os
from mtg_abilities import ActivatedAbility, TriggeredAbility

try:  # optional dependency for experimental GPT-based parsing
    from openai import OpenAI
except Exception:  # pragma: no cover - library may be absent in tests
    OpenAI = None


_WORD_NUM = {
    "one":1,"two":2,"three":3,"four":4,"five":5,
    "six":6,"seven":7,"eight":8,"nine":9,"ten":10,
}
_SPECIAL = {
    # mana rocks / fast mana
    "sol ring": 2,
    "mana crypt": 2,
    "mana vault": 3,
    "arcane signet": 1,
    "fellwar stone": 1,
    "chromatic lantern": 1,
    "commander's sphere": 1,
    "mind stone": 1,
    "gilded lotus": 3,
    # generic fall-back for signets/talismans – will be overwritten by Rule 2 if {W}{U} etc. present
    "signet": 2,
    "talisman": 1,
}

def parse_mana_production(oracle_text: str,
                          type_line: str = "",
                          card_name: str = "") -> int:
    """
    Return the *maximum* amount of mana a single activation produces.
    • counts {C}{C}, {R} or {G}→1, “Add three mana …”→3
    • ignores activation costs such as {T}, {1}
    """
    name_l = card_name.lower()

    # ─ Rule 0: explicit overrides ─
    for key, qty in _SPECIAL.items():
        if key in name_l:
            return qty

    text = oracle_text.lower()

    # ─ Rule 1: clauses that literally start with 'add' ─
    mana_clause_regex = re.compile(
        r"(?:^|[.:])\s*add\s+([^.]*)\.",          # capture up to next full stop
        flags=re.IGNORECASE | re.DOTALL)
    clauses = mana_clause_regex.findall(text)

    if clauses:
        total = 0
        for cl in clauses:
            # count {...} AFTER the word 'add'
            symbols = re.findall(r"{([^}]+)}", cl)
            if symbols:
                # duals like {R} or {G} → treat as one
                unique_syms = {s for s in symbols if s not in ("t",)}  # ignore {T}
                total += max(1, len(unique_syms))
            else:
                # textual amounts “one mana”, “… three mana of any one color”
                m = re.search(r"(one|two|three|four|five|six|seven|eight|nine|ten)\s+mana", cl)
                if m:
                    total += _WORD_NUM[m.group(1)]
                else:
                    total += 1                    # conservative default
        return total if total else 1

    # ─ Rule 2: basic lands & un-captured “Add {G}” lines ─
    if "land" in type_line and "add" in text:
        return 1

    # ─ Rule 3: textual 'add one mana' outside captured clause ─
    m = re.search(r"add\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+mana", text)
    if m:
        return _WORD_NUM[m.group(1)]

    # ─ Rule 4: generic presence of 'add' ⇒ assume 1 ─
    return 1 if "add" in text else 0


def parse_etb_triggers_from_oracle(text: str) -> list[TriggeredAbility]:
    """Extract simple ETB triggered abilities from oracle text."""
    if not text:
        return []
    lower = text.lower()
    triggers: list[TriggeredAbility] = []

    # Pattern: "When CARD enters the battlefield, draw a card" or similar
    m = re.search(
        r"when .* enters the battlefield, .*draw (?P<num>a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+) cards?",
        lower,
    )
    if m:
        num_map = {
            "a": 1,
            "an": 1,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        val = m.group("num")
        amount = num_map.get(val, int(val) if val.isdigit() else 1)

        def effect(board_state, n=amount):
            board_state.draw_card(n)

        triggers.append(TriggeredAbility(event="etb", effect=effect, description=f"draw {amount} card(s)"))

    m2 = re.search(r"when [^.]* enters the battlefield, proliferate", lower)
    if m2:
        def effect(board_state):
            board_state.proliferate()

        triggers.append(
            TriggeredAbility(event="etb", effect=effect, description="proliferate")
        )

    return triggers


def parse_attack_triggers_from_oracle(text: str) -> list[TriggeredAbility]:
    """Extract simple attack triggers from oracle text."""
    if not text:
        return []
    lower = text.lower()
    triggers: list[TriggeredAbility] = []
    m = re.search(
        r"whenever ([^.]*?) attacks, [^.]*draw (?P<num>a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+) cards?",
        lower,
    )
    if m:
        num_map = {
            "a": 1,
            "an": 1,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        val = m.group("num")
        amount = num_map.get(val, int(val) if val.isdigit() else 1)
        condition = m.group(1)
        requires_haste = "haste" in condition
        requires_flash = "flash" in condition

        def effect(board_state, n=amount):
            board_state.draw_card(n)

        triggers.append(
            TriggeredAbility(
                event="attack",
                effect=effect,
                description=f"draw {amount} card(s)",
                requires_haste=requires_haste,
                requires_flash=requires_flash,
            )
        )

    m2 = re.search(
        r"whenever [^.]*? attacks, [^.]*?put a \+1/\+1 counter on each creature you control with (?:flash or haste|haste or flash|flash|haste)",
        lower,
    )
    if m2:
        def effect(board_state):
            for creature in board_state.creatures:
                if getattr(creature, "has_haste", False) or getattr(creature, "has_flash", False):
                    creature.add_counter("+1/+1")

        triggers.append(
            TriggeredAbility(
                event="attack",
                effect=effect,
                description="Put +1/+1 counter on each hasty or flash creature",
            )
        )

    m3 = re.search(
        r"whenever you attack with [^.]*? and another legendary creature, draw a card",
        lower,
    )
    if m3:
        def effect(board_state):
            board_state.draw_card(1)

        triggers.append(
            TriggeredAbility(
                event="attack",
                effect=effect,
                description="draw 1 card",
                requires_another_legendary=True,
            )
        )

    m4 = re.search(r"whenever [^.]*? attacks, proliferate", lower)
    if m4:
        def effect(board_state):
            board_state.proliferate()

        triggers.append(
            TriggeredAbility(event="attack", effect=effect, description="proliferate")
        )

    return triggers


def parse_damage_triggers_from_oracle(text: str) -> list[TriggeredAbility]:
    """Extract simple damage triggers from oracle text."""
    if not text:
        return []
    lower = text.lower()
    triggers: list[TriggeredAbility] = []

    pattern = r"whenever a creature you control with (?:flash or haste|haste or flash|flash|haste) is dealt damage, create a tapped treasure token"
    if re.search(pattern, lower):
        def effect(board_state):
            creature = getattr(board_state, "last_damaged_creature", None)
            if creature and (getattr(creature, "has_haste", False) or getattr(creature, "has_flash", False)):
                from simulate_game import Card  # local import to avoid circular
                token = Card(
                    name="Treasure Token",
                    type="Artifact Token",
                    mana_cost="",
                    power=0,
                    toughness=0,
                    produces_colors=[],
                    mana_production=1,
                    etb_tapped=False,
                    etb_tapped_conditions={},
                    has_haste=False,
                )
                token.tapped = True
                board_state.artifacts.append(token)

        triggers.append(
            TriggeredAbility(
                event="damage",
                effect=effect,
                description="Create a tapped Treasure token",
            )
        )

    return triggers



def parse_etb_conditions_from_oracle(text: str) -> dict:
    conditions = {}
    if not text:
        return conditions

    lower_text = text.lower()

    if not any(phrase in lower_text for phrase in ["enters tapped", "enters the battlefield tapped"]):
        return conditions

    if all(keyword not in lower_text for keyword in ["unless", "if you don't"]):
        conditions["always_tapped"] = True
        return conditions

    number_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

    if re.search(
        r"enters (?:tapped|the battlefield tapped) unless you control two or more basic lands",
        lower_text,
    ):
        conditions["control_basic_lands"] = 2
        return conditions

    lands_match = re.search(
        r"enters (?:tapped|the battlefield tapped) unless you control (\w+|\d+) or more (?:other )?lands",
        lower_text,
    )
    if lands_match:
        num_str = lands_match.group(1)
        required_lands = number_map.get(num_str, int(num_str) if num_str.isdigit() else 0)
        if required_lands:
            conditions["control_lands"] = required_lands
            return conditions

    reveal_match = re.search(
        r"reveal a ([^.,]+?) or a ([^.,]+?) card from your hand.*?enters (?:tapped|the battlefield tapped)",
        lower_text,
        re.DOTALL,
    )
    if reveal_match:
        conditions["reveal"] = [
            reveal_match.group(1).strip().title(),
            reveal_match.group(2).strip().title(),
        ]
        return conditions

    single_reveal_match = re.search(
        r"reveal a ([^.,]+?) card from your hand.*?enters (?:tapped|the battlefield tapped)",
        lower_text,
        re.DOTALL,
    )
    if single_reveal_match:
        conditions["reveal"] = [single_reveal_match.group(1).strip().title()]
        return conditions

    permanents_match = re.search(
        r"enters (?:tapped|the battlefield tapped) unless you control (?:a|an) ([^.,]+?) or (?:a|an) ([^.,]+?)\b",
        lower_text,
    )
    if permanents_match:
        conditions["control"] = [
            permanents_match.group(1).strip().title(),
            permanents_match.group(2).strip().title(),
        ]
        return conditions

    single_permanent_match = re.search(
        r"enters (?:tapped|the battlefield tapped) unless you control (?:a|an) ([^.,]+?)\b",
        lower_text,
    )
    if single_permanent_match:
        conditions["control"] = [single_permanent_match.group(1).strip().title()]
        return conditions

    return conditions


def parse_etb_tapped_conditions(value):
    try:
        if not value or str(value).strip().lower() in ("", "nan", "none"):
            return {}
        return ast.literal_eval(value)
    except Exception:
        return {}


def parse_activated_abilities(value):
    """Parse a CSV cell describing activated abilities."""
    if not value or str(value).strip().lower() in ("", "nan", "none"):
        return []
    try:
        raw = ast.literal_eval(value)
    except Exception:
        return []
    abilities: list[ActivatedAbility] = []
    if isinstance(raw, (list, tuple)):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            abilities.append(
                ActivatedAbility(
                    cost=entry.get("cost", ""),
                    produces_colors=clean_produces_colors(entry.get("produces_colors", [])),
                    tap=bool(entry.get("tap", False)),
                )
            )
    return abilities


def parse_triggers_with_gpt(text: str) -> list[TriggeredAbility]:
    """Use OpenAI's GPT-4.1 model to extract triggered abilities.

    This experimental helper forwards *text* to the OpenAI API asking it to
    select the best matching triggers, effects and conditions supported by this
    codebase.  The model is provided with a small library of effect and
    condition names and is expected to respond with a JSON array describing the
    abilities.  Each entry should look like::

        {"event": "attack", "effect": "draw_cards", "amount": 1,
         "conditions": ["requires_haste"]}

    Only a minimal set of effects is currently supported.  If the OpenAI
    library is not available or any error occurs, an empty list is returned.
    """

    if not text or OpenAI is None:  # pragma: no cover - requires OpenAI library
        return []

    prompt = (
        "You are assisting a Magic: The Gathering simulator. Given the card\n"
        "text below, choose the most appropriate triggered abilities using the\n"
        "following library. Return ONLY a JSON array.\n\n"
        "Triggers: 'etb' for enters-the-battlefield or 'attack'.\n"
        "Effects: 'draw_cards' which draws N cards.\n"
        "Conditions: 'requires_haste' or 'requires_flash'.\n\n"
        f"Card text: {text}\n"
    )

    try:  # pragma: no cover - external API
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.responses.create(model="gpt-4.1", input=prompt)
        raw = resp.output_text
        data = json.loads(raw)
    except Exception:
        return []

    triggers: list[TriggeredAbility] = []
    for ability in data:
        event = ability.get("event")
        effect_name = ability.get("effect")
        amount = int(ability.get("amount", 1))
        conditions = ability.get("conditions", [])
        description = ability.get("description") or f"draw {amount} card(s)"

        if effect_name == "draw_cards":
            def effect(board_state, n=amount):
                board_state.draw_card(n)
        else:
            continue

        triggers.append(
            TriggeredAbility(
                event=event,
                effect=effect,
                description=description,
                requires_haste="requires_haste" in conditions,
                requires_flash="requires_flash" in conditions,
            )
        )

    return triggers


def parse_death_triggers_from_oracle(text: str) -> int:
    """
    Parse oracle text to detect death drain triggers.

    **SINGLE SOURCE OF TRUTH**: Uses shared_mechanics.py
    All detection logic is in shared_mechanics.detect_death_drain_value()
    """
    import sys
    from pathlib import Path

    # Add parent directory to import shared_mechanics
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from shared_mechanics import detect_death_drain_value
    return detect_death_drain_value(text)


def parse_sacrifice_outlet_from_oracle(text: str) -> bool:
    """
    Parse oracle text to detect sacrifice outlets.

    **SINGLE SOURCE OF TRUTH**: Uses shared_mechanics.py
    All detection logic is in shared_mechanics.detect_sacrifice_outlet()
    """
    import sys
    from pathlib import Path

    # Add parent directory to import shared_mechanics
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from shared_mechanics import detect_sacrifice_outlet
    return detect_sacrifice_outlet(text)
