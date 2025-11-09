import ast
import json
import re
from pathlib import Path

import pandas as pd
import requests
import re

from simulate_game import Card, clean_produces_colors
from mtg_abilities import ActivatedAbility, TriggeredAbility
from oracle_text_parser import (
    parse_mana_production,
    parse_etb_conditions_from_oracle,
    parse_etb_triggers_from_oracle,
    parse_attack_triggers_from_oracle,
    parse_damage_triggers_from_oracle,
    parse_activated_abilities,
    parse_etb_tapped_conditions,
)


def _safe_int(value) -> int:
    """Convert *value* to int, returning 0 on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0



def parse_fetch_land_ability(text: str) -> dict:
    """Parse fetch land characteristics from oracle text."""
    info = {"fetch_basic": False, "fetch_land_types": [], "fetch_land_tapped": False}
    if not text:
        return info
    lower = text.lower()
    if "pay 1 life" in lower and "sacrifice" in lower and "search your library" in lower and "land card" in lower:
        info["fetch_basic"] = "basic land card" in lower
        info["fetch_land_tapped"] = "tapped" in lower
        m = re.search(r"for (?:an?|one|up to one) ([^.,]+?) card", lower)
        if m:
            clause = m.group(1)
            clause = clause.replace("basic land", "")
            parts = re.split(r"or|,", clause)
            info["fetch_land_types"] = [p.strip().title() for p in parts if p.strip()]
    return info


def build_card_from_row(row):
    mana_prod = parse_mana_production(
        oracle_text=row["OracleText"],
        type_line=row["TypeLine"],
        card_name=row["Name"]
    )
    fetch = parse_fetch_land_ability(row.get("OracleText", ""))
    return Card(
        name   = row["Name"],
        type   = row["Type"],
        mana_cost = safe_cost_str(row["ManaCost"]),
        power  = row.get("Power"),
        toughness = row.get("Toughness"),
        produces_colors = clean_produces_colors(row.get("ProducesColors")),
        mana_production = mana_prod,
        etb_tapped = row.get("ETBTapped", False),
        etb_tapped_conditions = row.get("ETBTappedConditions", {}),
        has_haste = row.get("HasHaste", False),
        has_flash = row.get("HasFlash", False) or "flash" in row.get("OracleText", "").lower(),
        equip_cost = safe_cost_str(row.get("EquipCost")),
        power_buff = row.get("PowerBuff", 0),
        is_commander = row.get("IsCommander", False),
        is_legendary = row.get("IsLegendary", False) or "legendary" in str(row.get("TypeLine", "")).lower(),
        keywords_when_equipped = row.get("KeywordsWhenEquipped", []),
        puts_land = row.get("PutsLand", False),
        draw_cards = row.get("DrawCards", 0),
        activated_abilities = row.get("ActivatedAbilities") or [],
        triggered_abilities = row.get("TriggeredAbilities") or [],
        oracle_text = row["OracleText"],
        fetch_basic=fetch["fetch_basic"],
        fetch_land_types=fetch["fetch_land_types"],
        fetch_land_tapped=fetch["fetch_land_tapped"],
    )

# ---- internal helpers ----------------------------------------------------

def _df_to_cards(df: pd.DataFrame):
    # Ensure ETBTappedConditions is a dict; avoid parsing again
    if "ETBTappedConditions" not in df.columns:
        df["ETBTappedConditions"] = [{}] * len(df)
    else:
        df["ETBTappedConditions"] = df["ETBTappedConditions"].apply(
            parse_etb_tapped_conditions
        )

    # Activated abilities column is optional
    if "ActivatedAbilities" not in df.columns:
        df["ActivatedAbilities"] = [[]] * len(df)
    else:
        df["ActivatedAbilities"] = df["ActivatedAbilities"].apply(parse_activated_abilities)

    # Triggered abilities parsed from Oracle text
    if "OracleText" in df.columns:
        df["TriggeredAbilities"] = df["OracleText"].apply(
            lambda text: (
                parse_etb_triggers_from_oracle(text)
                + parse_attack_triggers_from_oracle(text)
                + parse_damage_triggers_from_oracle(text)
            )
        )
    else:
        df["TriggeredAbilities"] = [[]] * len(df)

    cards = []
    commander = None
    for _, row in df.iterrows():
        fetch = parse_fetch_land_ability(row.get("OracleText", ""))
        c = Card(
            name=row.get("Name", ""),
            type=row.get("Type", ""),
            mana_cost=row.get("ManaCost", ""),
            power=row.get("Power", 0),
            toughness=row.get("Toughness", 0),
            produces_colors=clean_produces_colors(row.get("ProducesColors", "")),
            etb_tapped=str(row.get("ETBTapped", "")).lower() in ("true", "yes", "1"),
            etb_tapped_conditions=row.get("ETBTappedConditions", {}),
            mana_production=row.get("ManaProduction", 0),
            has_haste=row.get("HasHaste", False),
            has_flash=(
                (isinstance(row.get("HasFlash", False), str) and row.get("HasFlash", "").strip().lower() in ("true", "yes", "1"))
                or (not isinstance(row.get("HasFlash", False), str) and bool(row.get("HasFlash", False)))
                or "flash" in str(row.get("OracleText", "")).lower()
            ),
            equip_cost=row.get("EquipCost", ""),
            power_buff=row.get("PowerBuff", 0),
            is_commander=str(row.get("Commander", "")).lower() in ("true", "yes"),
            is_legendary=(
                str(row.get("IsLegendary", "")).lower() in ("true", "yes", "1")
                or "legendary" in str(row.get("TypeLine", "")).lower()
            ),
            keywords_when_equipped=row.get("KeywordsWhenEquipped", []),
            puts_land=str(row.get("PutsLand", "")).lower() in ("true", "yes", "1"),
            draw_cards=_safe_int(row.get("DrawCards", 0)),
            activated_abilities=row.get("ActivatedAbilities", []),
            triggered_abilities=row.get("TriggeredAbilities", []),
            oracle_text=row.get("OracleText", ""),
            fetch_basic=fetch["fetch_basic"],
            fetch_land_types=fetch["fetch_land_types"],
            fetch_land_tapped=fetch["fetch_land_tapped"],
        )

        if c.is_commander:
            commander = c
        else:
            cards.append(c)

    names = [c.name for c in cards]
    if commander:
        names.append(commander.name)
    return cards, commander, names



# ---- CSV loader ----------------------------------------------------------

def load_deck_from_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    return _df_to_cards(df)



# ---- Scryfall helpers ----------------------------------------------------

SCRYFALL_CACHE_FILE = Path("scryfall_cache.json")


def _load_scryfall_cache() -> dict:
    if SCRYFALL_CACHE_FILE.exists():
        with open(SCRYFALL_CACHE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _save_scryfall_cache(cache: dict) -> None:
    with open(SCRYFALL_CACHE_FILE, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)


def fetch_cards_from_scryfall_bulk(names: list[str]) -> list[dict]:
    """Fetch card data for multiple names using the Scryfall collection API."""
    rows = []
    for i in range(0, len(names), 75):
        identifiers = [{"name": n} for n in names[i : i + 75]]
        resp = requests.post(
            "https://api.scryfall.com/cards/collection",
            json={"identifiers": identifiers},
            timeout=10,
        )
        resp.raise_for_status()

        payload = resp.json()
        data = payload.get("data", [])
        not_found = [nf.get("name") for nf in payload.get("not_found", []) if isinstance(nf, dict)]
        for card in data:
            type_line = card.get("type_line", "")
            oracle_text = card.get("oracle_text", "") or ""
            mana_production = parse_mana_production(
                oracle_text, type_line, card.get("name", "")
            )
            conditions = parse_etb_conditions_from_oracle(oracle_text)
            rows.append(
                {
                    "Name": card.get("name", ""),
                    "Type": type_line.split(" — ")[0],
                    "ManaCost": card.get("mana_cost", ""),
                    "Power": card.get("power", 0),
                    "Toughness": card.get("toughness", 0),
                    "ManaProduction": mana_production,
                    "ProducesColors": ",".join(card.get("produced_mana", []) or []),
                    "HasHaste": "haste" in oracle_text.lower(),
                    "HasFlash": "flash" in oracle_text.lower(),
                    "ETBTapped": "enters the battlefield tapped" in oracle_text.lower(),
                    "ETBTappedConditions": conditions,
                    "EquipCost": "",
                    "PowerBuff": 0,
                    "DrawCards": 0,
                    "PutsLand": 0,
                    "OracleText": oracle_text,
                }
            )


        # Fallback to individual lookups for any cards Scryfall could not find
        for name in not_found:
            try:
                rows.append(fetch_card_from_scryfall(name))
            except requests.HTTPError:
                # Ignore unknown names; they will raise later if actually needed
                continue
                
    return rows

def fetch_card_from_scryfall(name: str) -> dict:
    url = f"https://api.scryfall.com/cards/named?exact={name}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    type_line = data.get("type_line", "")
    oracle_text = data.get("oracle_text", "") or ""

    # Default mana production: lands provide 1. For other cards try to parse the
    # oracle text for an "Add {..}" clause to determine how many mana are
    # produced when tapped.
    mana_production = parse_mana_production(oracle_text, type_line, name)

    conditions = parse_etb_conditions_from_oracle(oracle_text)
    # print(f"Parsed conditions for {name}: {conditions}")
    info = {
        "Name": data.get("name", name),
        "Type": type_line.split(" — ")[0],
        "ManaCost": data.get("mana_cost", ""),
        "Power": data.get("power", 0),
        "Toughness": data.get("toughness", 0),
        "ManaProduction": mana_production,
        "ProducesColors": ",".join(data.get("produced_mana", []) or []),
        "HasHaste": "haste" in oracle_text.lower(),
        "HasFlash": "flash" in oracle_text.lower(),
        "ETBTapped": "enters the battlefield tapped" in oracle_text.lower(),
        "ETBTappedConditions": conditions,
        "EquipCost": "",
        "PowerBuff": 0,
        "DrawCards": 0,
        "PutsLand": 0,
        "OracleText": oracle_text,
    }
    return info


def load_deck_from_scryfall(card_names: list[str], commander_name: str):
    """Fetch card details from Scryfall using a local cache when possible."""
    cache = _load_scryfall_cache()

    needed = list(dict.fromkeys(card_names + [commander_name]))
    missing = [n for n in needed if n not in cache]

    if missing:
        fetched = fetch_cards_from_scryfall_bulk(missing)
        for info in fetched:
            cache[info["Name"]] = info
        _save_scryfall_cache(cache)

    rows = []
    for n in card_names:
        row = cache[n].copy()
        row["Commander"] = False
        rows.append(row)

    commander_row = cache[commander_name].copy()
    commander_row["Commander"] = True
    rows.append(commander_row)

    df = pd.DataFrame(rows)
    return _df_to_cards(df)


def load_names_from_file(path: str) -> list[str]:
    """Read card names from a simple text file.

    Blank lines and lines starting with ``#`` are ignored. Lines may begin with
    a quantity such as ``2 Sol Ring`` or end with a quantity like ``Sol Ring x2``.
    These counts are expanded so each card name appears the specified number of
    times in the returned list.
    """

    names: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            count = 1
            name = line

            # Handle prefixes like "2 Sol Ring" or "2x Sol Ring"
            m = re.match(r"(\d+)[xX]?\s+(.+)", line)
            if m:
                count = int(m.group(1))
                name = m.group(2).strip()
            else:
                # Handle suffixes like "Sol Ring x2" or "Sol Ring 2"
                m = re.match(r"(.+?)\s+x?(\d+)$", line)
                if m:
                    name = m.group(1).strip()
                    count = int(m.group(2))

            names.extend([name] * count)
    return names


def load_deck_from_scryfall_file(path: str, commander_name: str):
    """Load a deck from a file of card names using Scryfall."""
    names = load_names_from_file(path)
    return load_deck_from_scryfall(names, commander_name)


# ---- Archidekt helpers ---------------------------------------------------

def load_card_names_from_archidekt(deck_id: int) -> tuple[list[str], str]:
    """Return the list of card names and the commander name for an Archidekt deck."""
    url = f"https://archidekt.com/api/decks/{deck_id}/"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    names: list[str] = []
    commander_name = None

    for entry in data.get("cards", []):
        quantity = entry.get("quantity", 1)
        card_name = entry.get("card", {}).get("oracleCard", {}).get("name")
        if not card_name:
            continue
        if entry.get("category", {}).get("name", "").lower() == "commander":
            commander_name = card_name
            continue
        names.extend([card_name] * quantity)

    if commander_name is None:
        raise ValueError("Commander not found in deck data")

    return names, commander_name


def load_deck_from_archidekt(deck_id: int):
    """Load a deck directly from an Archidekt deck ID."""
    names, commander_name = load_card_names_from_archidekt(deck_id)
    return load_deck_from_scryfall(names, commander_name)

