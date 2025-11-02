"""
Card Role Extraction Utilities
Determine functional roles for individual cards based on their rules text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set


def _compile(patterns: Sequence[str]) -> List[re.Pattern[str]]:
    """Compile a sequence of regex patterns with IGNORECASE."""
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def _lower_keywords(keywords: Iterable[str]) -> Set[str]:
    return {kw.lower() for kw in keywords if kw}


def _get_card_text(card: Mapping[str, Any]) -> str:
    """Return the oracle text for a card, joining split faces when needed."""
    text = card.get("oracle_text") or ""
    if text:
        return text.lower()

    faces = card.get("card_faces") or []
    if faces:
        lines = [
            face.get("oracle_text", "")
            for face in faces
            if face.get("oracle_text")
        ]
        return "\n".join(lines).lower()

    return ""


def _get_keywords(card: Mapping[str, Any]) -> Set[str]:
    """Return a set of lowercase keywords including split faces."""
    base_keywords = set(card.get("keywords") or [])
    for face in card.get("card_faces", []) or []:
        base_keywords.update(face.get("keywords") or [])
    return _lower_keywords(base_keywords)


def _get_subtypes(card: Mapping[str, Any]) -> Set[str]:
    subtypes = set()
    card_types = card.get("card_types") or {}
    for subtype in card_types.get("subtypes", []) or []:
        subtypes.add(subtype.lower())

    # Fall back to parsing the type line for extra resilience
    type_line = (card.get("type_line") or "").lower()
    if "—" in type_line:
        _, subtype_part = type_line.split("—", maxsplit=1)
        for subtype in subtype_part.split():
            subtypes.add(subtype.strip().lower())

    return subtypes


# Shared helper patterns ----------------------------------------------------

PROTECTION_PATTERNS = _compile(
    [
        r"\bhexproof\b",
        r"\bindestructible\b",
        r"\bshroud\b",
        r"prevents? all damage",
        r"protection from ",
        r"\bward\b",
        r"phase out",
        r"regenerate",
        r"shield counter",
    ]
)

CARD_DRAW_PATTERNS = _compile(
    [
        r"draw (?:a|one) card",
        r"draw \d+ cards",
        r"draw two cards",
        r"whenever .* draw",
        r"you may draw",
        r"investigate",
    ]
)

LAND_SEARCH_PATTERNS = _compile(
    [
        r"search your library.*land card",
        r"put (?:a|any number of) land card[s]? from your library",
        r"search your library.*basic land",
    ]
)

COLOR_CORRECTION_PATTERNS = _compile(
    [
        r"search your library for a basic land card",
        r"search your library for a plains, island, swamp, mountain, or forest card",
        r"search your library for a land card with a basic land type",
        r"search your library for up to two basic land cards",
        r"search .* for a basic land",
        r"search your library for a basic (plains|island|swamp|mountain|forest)",
    ]
)

ADDITIONAL_LAND_PATTERNS = _compile(
    [
        r"play an additional land",
        r"you may play an additional land",
        r"lands? you control (?:enter|enters) untapped",
    ]
)

MANA_PRODUCTION_PATTERNS = _compile(
    [
        r"add \{[wubrgc]\}",
        r"add one mana of any color",
        r"add two mana of any one color",
        r"add three mana",
        r"add an amount of mana",
    ]
)

TREASURE_TOKEN_PATTERNS = _compile(
    [
        r"treasure token",
        r"treasure artifact token",
    ]
)

TOKEN_CREATE_PATTERNS = _compile(
    [
        r"you create .* token",
        r"create .* token under your control",
        r"create (?:a|one|two|three|\d+) .* token",
        r"create .* creature token",
        r"create .* artifact token",
        r"create .* food token",
        r"create .* clue token",
        r"create .* treasure token",
    ]
)

OPPONENT_TOKEN_PATTERNS = _compile(
    [
        r"opponent[s]? .* create .* token",
        r"that player creates .* token",
        r"defending player creates .* token",
        r"its controller creates .* token",
        r"its controller creates .* treasure",
        r"controller creates .* token",
        r"controller creates .* treasure",
    ]
)

REMOVAL_PATTERNS = _compile(
    [
        r"destroy target",
        r"exile target",
        r"deal[s]? \d+ damage to target",
        r"deal[s]? damage to target creature",
        r"fight target",
        r"treat damage as though",
        r"counter target",
        r"return target .* to (?:its|their) owner's hand",
        r"tap target creature",
        r"gain control of target creature",
        r"target creature gets -",
    ]
)

RECURSION_PATTERNS = _compile(
    [
        r"return target .* from your graveyard",
        r"return .* card from your graveyard",
        r"you may cast .* from your graveyard",
        r"play .* from your graveyard",
        r"choose target .* card in your graveyard",
        r"put target .* from your graveyard",
        r"recover",  # keyword ability
        r"unearth",
        r"flashback",
        r"jump-start",
        r"escape",
        r"disturb",
        r"embalm",
        r"afterlife",
    ]
)

SCRY_PATTERNS = _compile(
    [
        r"\bscry\b",

    ]
)


SURVEIL_PATTERNS = _compile(
    [
        r"\bsurveil\b",
    ]
)


TOP_DECK_PATTERNS = _compile(
    [
        r"look at the top card of your library",
        r"reveal the top card of your library",
        r"the top card of your library",
        r"play with the top card of your library revealed",
    ]
)

KEYWORD_LIST = _lower_keywords(
    [
        "flying",
        "first strike",
        "double strike",
        "lifelink",
        "deathtouch",
        "trample",
        "menace",
        "reach",
        "vigilance",
        "haste",
        "hexproof",
        "indestructible",
        "prowess",
        "fear",
        "intimidate",
        "exalted",
        "unblockable",
        "ward",
    ]
)

TRIBAL_HINT_WORDS = _compile(
    [
        r"tribal",
        r"choose a creature type",
        r"for each creature type",
    ]
)

TYPE_SYNERGY_HINTS = {
    "creature": _compile(
        [
            r"creatures? you control",
            r"creature spells? you cast",
            r"whenever you cast a creature spell",
            r"noncreature spells you control get",
            r"creature card[s]? in your graveyard",
        ]
    ),
    "artifact": _compile(
        [
            r"artifact[s]? you control",
            r"whenever an artifact",
            r"artifact spells? you cast",
            r"artifact card[s]? in your graveyard",
        ]
    ),
    "enchantment": _compile(
        [
            r"enchantment[s]? you control",
            r"whenever you cast an enchantment",
            r"enchantment spell[s]? you cast",
            r"constellation",
        ]
    ),
    "instant_sorcery": _compile(
        [
            r"instant or sorcery spell",
            r"instant and sorcery spells",
            r"noncreature spell you cast",
            r"copy target instant",
            r"copy target sorcery",
        ]
    ),
    "land": _compile(
        [
            r"\blandfall\b",
            r"lands? you control",
            r"whenever a land enters the battlefield under your control",
            r"land card[s]? from your graveyard",
            r"play an additional land",
        ]
    ),
    "planeswalker": _compile(
        [
            r"planeswalker[s]? you control",
            r"planeswalker spell",
            r"loyalty ability",
        ]
    ),
}

SYNERGY_TYPE_HINTS = _compile(
    [
        r"artifact[s]? you control",
        r"enchantment[s]? you control",
        r"equipment you control",
        r"vehicle[s]? you control",
        r"planeswalker[s]? you control",
        r"land[s]? you control",
    ]
)

COST_MATTERS_PATTERNS = _compile(
    [
        r"converted mana cost",
        r"\bmana value\b",
        r"mana values?",
        r"costs? \{?[0-9x]+\}? less to cast",
        r"spells? you cast cost",
        r"for each spell with mana value",
        r"where X is the mana value",
    ]
)

TUTOR_PATTERNS = _compile(
    [
        r"search your library for",
        r"put it into your hand",
        r"put it onto the battlefield",
        r"then shuffle",
    ]
)


# Helper predicates ---------------------------------------------------------

def _creates_token_for_you(text: str) -> bool:
    return any(pattern.search(text) for pattern in TOKEN_CREATE_PATTERNS) and not any(
        pattern.search(text) for pattern in OPPONENT_TOKEN_PATTERNS
    )


def _creates_specific_token(text: str, token_keyword: str) -> bool:
    keyword_pattern = re.compile(rf"{token_keyword}\s+token", re.IGNORECASE)
    return keyword_pattern.search(text) is not None and _creates_token_for_you(text)


def _produces_mana(card: Mapping[str, Any], text: str) -> bool:
    if card.get("produced_mana"):
        return True

    if any(pattern.search(text) for pattern in MANA_PRODUCTION_PATTERNS):
        return True

    # Mana rocks / creatures often have reminder text with "Add {C}"
    return False


def _has_protection(keywords: Set[str], text: str) -> bool:
    if keywords & {"hexproof", "indestructible", "shroud", "ward"}:
        return True
    return any(pattern.search(text) for pattern in PROTECTION_PATTERNS)


def _has_card_draw(text: str) -> bool:
    return any(pattern.search(text) for pattern in CARD_DRAW_PATTERNS)


def _has_recursion(text: str) -> bool:
    return any(pattern.search(text) for pattern in RECURSION_PATTERNS)


def _has_removal(text: str) -> bool:
    return any(pattern.search(text) for pattern in REMOVAL_PATTERNS)


def _grants_keywords(text: str, keywords: Set[str]) -> bool:
    if any(pattern in text for pattern in [" gains ", " gain ", " have ", " has "]):
        for keyword in keywords:
            if keyword in text:
                return True
    return False


def _has_cost_matter(text: str) -> bool:
    return any(pattern.search(text) for pattern in COST_MATTERS_PATTERNS)


def _has_synergy_type(text: str) -> bool:
    return any(pattern.search(text) for pattern in SYNERGY_TYPE_HINTS)


def _has_tribal_support(text: str, subtypes: Set[str]) -> bool:
    if not subtypes:
        return False
    if any(pattern.search(text) for pattern in TRIBAL_HINT_WORDS):
        return True
    return any(subtype in text for subtype in subtypes)


def _text_mentions_patterns(text: str, patterns: Sequence[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


# Role matchers -------------------------------------------------------------

def match_protection(ctx: Dict[str, Any]) -> bool:
    return _has_protection(ctx["keywords"], ctx["text"])


def match_card_advantage_role(ctx: Dict[str, Any]) -> bool:
    text = ctx["text"]
    return _has_card_draw(text) or "clue token" in text or "investigate" in text


def match_color_correction(ctx: Dict[str, Any]) -> bool:
    """
    Match cards that fix colors by fetching basic lands.

    Examples:
    - Terramorphic Expanse (fetch land)
    - Evolving Wilds (fetch land)
    - Foreboding Landscape (produces mana + can fetch)

    These cards allow you to get the specific basic land type you need.
    """
    text = ctx["text"]
    type_line = ctx["type_line"]

    # Only lands can be color correction (not spells like Cultivate)
    if "land" not in type_line:
        return False

    # Check if it searches for basic land(s)
    if _text_mentions_patterns(text, COLOR_CORRECTION_PATTERNS):
        return True

    return False


def match_ramp(ctx: Dict[str, Any]) -> bool:
    """
    Match cards that provide mana acceleration (ramp).

    TRUE RAMP (includes):
    - Mana rocks (Sol Ring, Arcane Signet) - extra mana sources
    - Mana dorks (Llanowar Elves) - extra mana sources
    - Land fetch spells (Cultivate, Rampant Growth) - put extra lands on battlefield
    - Treasure token creators - create extra mana sources
    - Lands that give extra land drops (Exploration effects)

    NOT RAMP (excludes):
    - Regular lands (Forest, Command Tower) - normal 1 per turn
    - Fetch lands that sacrifice (Terramorphic Expanse, Fabled Passage) - 1 land → 1 land

    Key: Ramp = net GAIN in mana/lands, not just color fixing
    """
    text = ctx["text"]
    card = ctx["card"]
    type_line = ctx["type_line"]

    # If it's a land:
    if "land" in type_line:
        # Lands that let you play ADDITIONAL lands ARE ramp
        if _text_mentions_patterns(text, ADDITIONAL_LAND_PATTERNS):
            return True
        # Fetch lands that SACRIFICE themselves are NOT ramp (1 land → 1 land)
        # They're color correction only
        if "sacrifice" in text and _text_mentions_patterns(text, LAND_SEARCH_PATTERNS):
            return False
        # Other lands that search (like Golos activated ability) might be ramp
        # but for now, regular lands are NOT ramp
        return False

    # Non-land permanents that produce mana ARE ramp (mana rocks, mana dorks)
    if _produces_mana(card, text):
        return True

    # Spells that search for lands and put them on battlefield ARE ramp
    if _text_mentions_patterns(text, LAND_SEARCH_PATTERNS):
        return True

    # Effects that give extra land drops ARE ramp
    if _text_mentions_patterns(text, ADDITIONAL_LAND_PATTERNS):
        return True

    # Treasure tokens ARE ramp
    if _creates_specific_token(text, "treasure"):
        return True

    return False


def match_removal(ctx: Dict[str, Any]) -> bool:
    return _has_removal(ctx["text"])


def match_recursion(ctx: Dict[str, Any]) -> bool:
    return _has_recursion(ctx["text"])


def match_sacrifice(ctx: Dict[str, Any]) -> bool:
    text = ctx["text"]
    if "sacrifice" not in text:
        return False

    # Avoid counting effects that only force opponents to sacrifice
    if any(
        phrase in text
        for phrase in [
            "each opponent sacrifices",
            "target opponent sacrifices",
            "target player sacrifices",
            "defending player sacrifices",
        ]
    ):
        return False

    # Check for common sacrifice outlet wording
    return any(
        phrase in text
        for phrase in [
            "you may sacrifice",
            "sacrifice a creature",
            "sacrifice another creature",
            "sacrifice an artifact",
            "as an additional cost to cast this spell, sacrifice",
            "{t}: sacrifice",
            "sacrifice this artifact",
        ]
    )


def match_token_generation(ctx: Dict[str, Any]) -> bool:
    text = ctx["text"]
    return _creates_token_for_you(text)


def match_anthem(ctx: Dict[str, Any]) -> bool:
    text = ctx["text"]
    return any(
        phrase in text
        for phrase in [
            "creatures you control get +",
            "creature tokens you control get +",
            "other creatures you control get +",
            "creatures you control have",
            "creatures you control gain",
        ]
    )


def match_synergy_type(ctx: Dict[str, Any]) -> bool:
    return _has_synergy_type(ctx["text"])


def match_keyword_grant(ctx: Dict[str, Any]) -> bool:
    return _grants_keywords(ctx["text"], KEYWORD_LIST)


def match_cost_matters(ctx: Dict[str, Any]) -> bool:
    return _has_cost_matter(ctx["text"])


def match_tribal(ctx: Dict[str, Any]) -> bool:
    return _has_tribal_support(ctx["text"], ctx["subtypes"])


def match_creature_matters(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["creature"])


def match_artifact_matters(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["artifact"])


def match_enchantment_matters(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["enchantment"])


def match_instant_sorcery_matters(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["instant_sorcery"])


def match_land_matters(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["land"])


def match_planeswalker_synergy(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TYPE_SYNERGY_HINTS["planeswalker"])


def match_draw_engine(ctx: Dict[str, Any]) -> bool:
    return match_card_advantage_role(ctx)


def match_tutor_target(ctx: Dict[str, Any]) -> bool:
    text = ctx["text"]
    return "search your library" in text or _text_mentions_patterns(text, TUTOR_PATTERNS)


def match_recursion_loop(ctx: Dict[str, Any]) -> bool:
    return _has_recursion(ctx["text"])


def match_scry_synergy(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], SCRY_PATTERNS)


def match_surveil_synergy(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], SURVEIL_PATTERNS)


def match_top_deck_synergy(ctx: Dict[str, Any]) -> bool:
    return _text_mentions_patterns(ctx["text"], TOP_DECK_PATTERNS)


# Role definitions ----------------------------------------------------------

ROLE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "role_interaction": {
        "label": "Role & Function Interaction",
        "roles": [
            {"key": "protection", "label": "Protection", "matcher": match_protection},
            {
                "key": "card_advantage",
                "label": "Card Advantage",
                "matcher": match_card_advantage_role,
            },
            {"key": "ramp", "label": "Ramp", "matcher": match_ramp},
            {
                "key": "color_correction",
                "label": "Color Correction",
                "matcher": match_color_correction,
            },
            {"key": "removal", "label": "Removal", "matcher": match_removal},
            {"key": "recursion", "label": "Recursion", "matcher": match_recursion},
            {"key": "sacrifice", "label": "Sacrifice", "matcher": match_sacrifice},
            {
                "key": "token_generation",
                "label": "Token Generation",
                "matcher": match_token_generation,
            },
        ],
    },
    "benefits": {
        "label": "Benefits & Enhancement",
        "roles": [
            {"key": "anthem_effect", "label": "Anthem Effect", "matcher": match_anthem},
            {
                "key": "synergy_type",
                "label": "Synergy Type",
                "matcher": match_synergy_type,
            },
            {
                "key": "keyword_grant",
                "label": "Keyword Grant",
                "matcher": match_keyword_grant,
            },
            {
                "key": "cost_matters",
                "label": "Cost Matters",
                "matcher": match_cost_matters,
            },
            {"key": "tribal", "label": "Tribal", "matcher": match_tribal},
        ],
    },
    "type_synergy": {
        "label": "Type Synergy",
        "roles": [
            {
                "key": "creature_matters",
                "label": "Creature Matters",
                "matcher": match_creature_matters,
            },
            {
                "key": "artifact_matters",
                "label": "Artifact Matters",
                "matcher": match_artifact_matters,
            },
            {
                "key": "enchantment_matters",
                "label": "Enchantment Matters",
                "matcher": match_enchantment_matters,
            },
            {
                "key": "instant_sorcery_matters",
                "label": "Instant/Sorcery Matters",
                "matcher": match_instant_sorcery_matters,
            },
            {
                "key": "land_matters",
                "label": "Land Matters",
                "matcher": match_land_matters,
            },
            {
                "key": "planeswalker_synergy",
                "label": "Planeswalker Synergy",
                "matcher": match_planeswalker_synergy,
            },
        ],
    },
    "card_advantage": {
        "label": "Card Advantage Engine",
        "roles": [
            {"key": "draw_engine", "label": "Draw Engine", "matcher": match_draw_engine},
            {
                "key": "tutor_target",
                "label": "Tutor Target",
                "matcher": match_tutor_target,
            },
            {
                "key": "recursion_loop",
                "label": "Recursion Loop",
                "matcher": match_recursion_loop,
            },
            {
                "key": "scry_synergy",
                "label": "Scry Synergy",
                "matcher": match_scry_synergy,
            },
            {
                "key": "surveil_synergy",
                "label": "Surveil Synergy",
                "matcher": match_surveil_synergy,
            },
            {
                "key": "top_deck_synergy",
                "label": "Top Deck Synergy",
                "matcher": match_top_deck_synergy,
            },
        ],
    },
}


# Public API ----------------------------------------------------------------

def extract_roles_for_card(card: Mapping[str, Any]) -> Dict[str, List[str]]:
    """
    Determine the functional roles for a single card.

    Returns a mapping of category key -> list of role keys.
    """
    context = {
        "card": card,
        "text": _get_card_text(card),
        "keywords": _get_keywords(card),
        "type_line": (card.get("type_line") or "").lower(),
        "subtypes": _get_subtypes(card),
    }

    roles: Dict[str, List[str]] = {}
    for category_key, category_def in ROLE_CATEGORIES.items():
        matched_roles: List[str] = []
        for role_def in category_def["roles"]:
            matcher = role_def["matcher"]
            if matcher(context):
                matched_roles.append(role_def["key"])
        if matched_roles:
            roles[category_key] = matched_roles

    return roles


def assign_roles_to_cards(cards: Sequence[Dict[str, Any]]) -> None:
    """
    Mutate the provided cards in-place, adding a ``roles`` dictionary with the
    detected roles for each card.
    """
    for card in cards:
        card["roles"] = extract_roles_for_card(card)


def summarize_roles(cards: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """
    Build a summary structure counting how many cards fall into each role.
    """
    summary: Dict[str, Any] = {}
    for category_key, category_def in ROLE_CATEGORIES.items():
        summary[category_key] = {
            "label": category_def["label"],
            "roles": {
                role_def["key"]: {
                    "label": role_def["label"],
                    "cards": [],
                }
                for role_def in category_def["roles"]
            },
        }

    for card in cards:
        card_roles = card.get("roles") or {}
        card_name = card.get("name")
        if not card_name:
            continue
        for category_key, role_keys in card_roles.items():
            category_summary = summary.get(category_key)
            if not category_summary:
                continue
            for role_key in role_keys:
                role_entry = category_summary["roles"].get(role_key)
                if role_entry is not None:
                    role_entry["cards"].append(card_name)

    # Sort card lists for stable ordering
    for category_data in summary.values():
        for role_entry in category_data["roles"].values():
            role_entry["cards"].sort()

    return summary


def slugify_role(category_key: str, role_key: str) -> str:
    """
    Build a CSS-safe slug for the given category and role.
    """
    cat = category_key.replace(" ", "_").replace("/", "_").lower()
    role = role_key.replace(" ", "_").replace("/", "_").lower()
    return f"role-{cat}-{role}"


__all__ = [
    "ROLE_CATEGORIES",
    "assign_roles_to_cards",
    "extract_roles_for_card",
    "summarize_roles",
    "slugify_role",
]

