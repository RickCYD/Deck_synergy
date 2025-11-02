"""
Monte Carlo simulation for multi-color mana availability and spell playability.

This module integrates with the existing card/deck structures in the app and
uses Scryfall-enriched card dictionaries (as produced by src.api.scryfall).

Key features:
- Simulates opening hands and turn-by-turn draws.
- Plays up to one land per turn with a simple, color-aware heuristic.
- Optionally casts mana accelerants (mana rocks and ramp spells) to improve
  future mana availability.
- Tracks probability curves per turn for color coverage and for having at
  least one castable non-accelerant spell.

Notes and assumptions:
- Lands produce one mana per turn and multi-color lands are treated as a
  single flexible source that can produce one of their colors each turn.
- Lands that enter tapped (e.g., triomes, many duals) are not usable on the
  turn they enter but are available from the next turn onward.
- Mana rocks (artifacts with produced mana) are treated as +1 flexible source
  starting the turn after they are cast (commonly accurate for most rocks).
- Ramp/fetch spells like Cultivate put one land onto the battlefield tapped
  (usable next turn) and one basic land into hand for a future land drop.
- Casting decisions for accelerants are greedy by lowest CMC first.
- We ignore complex conditional untap rules and activation costs beyond CMC.
- We do not actually cast non-accelerant spells; we only check if at least
  one such spell in hand is currently castable with available sources.

This aims to provide a practical, fast simulation that yields insight into
color coverage and spell playability while keeping the logic straightforward.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Iterable

from src.models.deck import Deck
from src.utils.mana_extractors import classify_mana_land, extract_mana_colors


# -----------------------------
# Data models and parameters
# -----------------------------


COLORS: Tuple[str, ...] = ("W", "U", "B", "R", "G", "C")
K_MAX_SUGGEST: int = 3  # up to +3 sources per color for suggestion modeling


@dataclass
class SimulationParams:
    iterations: int = 50000
    max_turn: int = 10
    on_the_play: bool = True
    random_seed: Optional[int] = None
    # Treat lands with enters_tapped as tapped this turn (True) or usable (False)
    respect_enters_tapped: bool = True
    # Attempt to cast accelerators (mana rocks/ramp) greedily each turn
    use_accelerators: bool = True


@dataclass
class SimulationResult:
    # Probability (0..1) per turn index starting at 1
    p_color_coverage: Dict[int, float]
    p_playable_spell: Dict[int, float]
    # Optional diagnostics
    avg_lands_in_play: Dict[int, float]
    lands_in_hand_hist: Dict[int, Dict[int, int]]
    # Distributions and summaries
    opening_hand_land_hist: Dict[int, int]
    available_mana_hist: Dict[int, Dict[int, int]]  # turn -> mana -> hits
    lands_in_play_hist: Dict[int, Dict[int, int]]   # turn -> lands -> hits
    available_mana_summary: Dict[int, Dict[str, float]]  # turn -> metrics (min, max, mode, p50, p10, p90)
    mode_available_mana_curve: Dict[int, int]
    # Per-card earliest-castable turn histograms and probabilities by turn
    per_card_first_cast_turn_hist: Dict[str, Dict[int, int]]
    per_card_prob_by_turn: Dict[str, Dict[int, float]]
    # Color analytics per turn
    color_available_prob: Dict[int, Dict[str, float]]  # P(color available)
    color_limitation_rate: Dict[int, Dict[str, float]]  # Fraction of in-hand spells blocked by this color
    playable_fraction: Dict[int, float]  # Avg fraction of in-hand spells that are castable
    # For each color, histogram of minimal extra sources needed to make blocked spells castable
    color_need_k_hist: Dict[int, Dict[str, Dict[int, int]]]  # turn -> color -> k(1..K_MAX) -> count
    # Suggested extra sources per color by turn to unlock ~80% of color-limited spells
    color_suggest_k: Dict[int, Dict[str, int]]
    # Active colors in the deck identity (subset of WUBRG). UI should use this list for color lines.
    active_colors: List[str]
    params: SimulationParams


# -----------------------------
# Utility helpers
# -----------------------------


def _tokenize_mana_cost(mana_cost: str) -> List[str]:
    """Extract tokens inside braces from a Scryfall mana cost string.

    Example: "{2}{U}{U}" -> ["2", "U", "U"].
    Unrecognized tokens are returned as-is for upstream handling.
    """
    tokens: List[str] = []
    buf = []
    inside = False
    for ch in mana_cost or "":
        if ch == "{":
            inside = True
            buf = []
        elif ch == "}":
            if inside:
                token = "".join(buf).strip().upper()
                if token:
                    tokens.append(token)
            inside = False
        else:
            if inside:
                buf.append(ch)
    return tokens


def parse_mana_cost(mana_cost: str) -> Dict[str, int]:
    """Parse Scryfall-style mana cost to counts per color and generic.

    Supports basic symbols: W, U, B, R, G, C, digits for generic, and X (ignored).
    Hybrid/phyrexian and complex symbols are conservatively approximated by
    ignoring special semantics; unknown tokens are skipped.
    """
    counts: Dict[str, int] = {c: 0 for c in COLORS}
    counts["generic"] = 0

    for tok in _tokenize_mana_cost(mana_cost):
        if tok.isdigit():
            counts["generic"] += int(tok)
        elif tok in COLORS:  # W U B R G C
            counts[tok] += 1
        elif tok == "X":
            # Treat X as 0 for playability checks
            continue
        else:
            # Hybrid or unknown; best-effort: skip to avoid false positives.
            # Examples: RW, 2/U, WP, etc. These could be improved later.
            continue

    return counts


def expand_deck_cards(cards: List[Dict]) -> List[Dict]:
    """Expand the deck's card list by quantity into a flat list of card dicts."""
    expanded: List[Dict] = []
    for card in cards:
        qty = int(card.get("quantity", 1) or 1)
        for _ in range(qty):
            expanded.append(card)
    return expanded


def is_land(card: Dict) -> bool:
    return "Land" in (card.get("type_line") or "")


def is_mana_rock(card: Dict) -> bool:
    # Artifact that produces mana
    if "Artifact" not in (card.get("type_line") or ""):
        return False
    produced = card.get("produced_mana") or []
    return bool(produced)


def is_ramp_spell(card: Dict) -> bool:
    # Sorcery/Instant mentioning searching for land and putting onto battlefield
    tline = (card.get("type_line") or "").lower()
    if not ("sorcery" in tline or "instant" in tline):
        return False
    text = (card.get("oracle_text") or "").lower()
    if not text:
        return False
    return (
        "search your library" in text
        and "land" in text
        and ("put" in text and "battlefield" in text)
    )


def card_produced_colors(card: Dict) -> Set[str]:
    """Colors a card can produce as mana (W,U,B,R,G,C).

    Prefers Scryfall's produced_mana, fallback to analyzer from oracle/type.
    For multi-color lands this returns multiple colors, indicating flexibility.
    """
    produced = set(card.get("produced_mana") or [])
    if produced:
        return {c for c in produced if c in COLORS}

    # Fallback: analyze land oracle/type text
    if is_land(card):
        classification = classify_mana_land(card)
        cls = classification.get("classification") if classification else None
        colors = set((cls or {}).get("colors") or [])
        return {c for c in colors if c in COLORS}

    # Default empty
    return set()


def enters_tapped_this_turn(card: Dict) -> bool:
    """Heuristic to determine if a land enters tapped on the turn it is played.

    Uses mana_extractors classification where available.
    """
    classification = classify_mana_land(card)
    cls = classification.get("classification") if classification else None
    if cls is not None:
        return bool(cls.get("enters_tapped", False))

    # Fallback: simple text search
    text = (card.get("oracle_text") or "").lower()
    return "enters the battlefield tapped" in text


# -----------------------------
# Allocation logic
# -----------------------------


def can_pay_cost_with_sources(cost: Dict[str, int], sources: List[Set[str]]) -> bool:
    """Check if a mana cost is payable given a list of sources.

    - Each source can be used at most once.
    - A source with multiple colors can satisfy exactly one colored pip.
    - After satisfying colored pips, remaining sources can pay generic.
    - Colorless requirement 'C' consumes sources that can produce 'C' or any
      other mana (treating generic similarly), but if a spell explicitly
      requires 'C', we try to allocate 'C'-capable sources first.
    """
    # Clone inputs to avoid mutation
    remaining_sources = list(sources)

    # Build list of colored requirements (excluding generic)
    color_reqs: List[str] = []
    for c in COLORS:
        if c == "C":
            continue  # Handle explicit colorless later
        color_reqs.extend([c] * int(cost.get(c, 0) or 0))

    # Greedy assignment: satisfy the most constrained colors first.
    # Sort by the number of sources that can produce that color (ascending).
    color_reqs.sort(key=lambda col: sum(1 for s in remaining_sources if col in s))

    used_indices: Set[int] = set()
    for color in color_reqs:
        idx = _pick_source_for_color(color, remaining_sources, used_indices)
        if idx is None:
            return False
        used_indices.add(idx)

    # Handle explicit colorless 'C' (if any): try to allocate from sources that include 'C' first,
    # then from any remaining source if necessary (many effects allow generic mana to pay C,
    # but if strict 'C' is required, this is conservative; Scryfall 'C' is rare in costs).
    explicit_c = int(cost.get("C", 0) or 0)
    for _ in range(explicit_c):
        idx = _pick_source_for_color("C", remaining_sources, used_indices, prefer_exact=True)
        if idx is None:
            # Fall back to any unused source
            idx = _pick_any_unused_source(remaining_sources, used_indices)
        if idx is None:
            return False
        used_indices.add(idx)

    # Now check generic
    total_sources = len(remaining_sources)
    remaining_available = total_sources - len(used_indices)
    return remaining_available >= int(cost.get("generic", 0) or 0)


def _pick_source_for_color(
    color: str,
    sources: List[Set[str]],
    used_indices: Set[int],
    prefer_exact: bool = False,
) -> Optional[int]:
    """Pick an unused source index that can produce a given color.

    - If prefer_exact is True, prefer sources that explicitly include the color
      over flexible ones.
    - Break ties by choosing the least-flexible source (fewest colors) first.
    """
    candidates: List[Tuple[int, Set[str]]] = [
        (i, s) for i, s in enumerate(sources) if i not in used_indices and (color in s or color == "C")
    ]
    if not candidates:
        return None

    if prefer_exact and color != "C":
        exact = [(i, s) for i, s in candidates if color in s]
        if exact:
            candidates = exact

    # Choose the least flexible (fewest colors) to preserve flexible ones
    candidates.sort(key=lambda t: len(t[1]))
    return candidates[0][0]


def _pick_any_unused_source(sources: List[Set[str]], used_indices: Set[int]) -> Optional[int]:
    for i in range(len(sources)):
        if i not in used_indices:
            return i
    return None


# -----------------------------
# Simulation core
# -----------------------------


class ManaSimulator:
    def __init__(self, params: Optional[SimulationParams] = None):
        self.params = params or SimulationParams()
        if self.params.random_seed is not None:
            random.seed(self.params.random_seed)

    def simulate_deck(self, deck: Deck) -> SimulationResult:
        """Run Monte Carlo simulation for a Deck and return aggregated results."""
        cards = expand_deck_cards(deck.cards)
        return self.simulate_cards(cards, deck_color_identity=_infer_deck_colors(deck))

    def simulate_cards(
        self,
        cards: List[Dict],
        deck_color_identity: Optional[List[str]] = None,
    ) -> SimulationResult:
        if deck_color_identity is None:
            deck_color_identity = _infer_colors_from_cards(cards)

        needed_colors = [c for c in COLORS if c in set(deck_color_identity) and c != "C"]
        active_colors = [c for c in ['W','U','B','R','G'] if c in set(deck_color_identity)]
        max_turn = int(self.params.max_turn)

        color_coverage_hits = {t: 0 for t in range(1, max_turn + 1)}
        playable_spell_hits = {t: 0 for t in range(1, max_turn + 1)}
        lands_in_play_accum = {t: 0 for t in range(1, max_turn + 1)}
        # Histograms
        opening_hand_land_hist: Dict[int, int] = {}
        available_mana_hist: Dict[int, Dict[int, int]] = {t: {} for t in range(1, max_turn + 1)}
        lands_in_play_hist: Dict[int, Dict[int, int]] = {t: {} for t in range(1, max_turn + 1)}
        lands_in_hand_hist: Dict[int, Dict[int, int]] = {t: {} for t in range(1, max_turn + 1)}
        # Per-card earliest castable turn histograms
        per_card_first_cast_turn_hist: Dict[str, Dict[int, int]] = {}

        # Accumulators for color analytics
        color_available_hits: Dict[int, Dict[str, int]] = {t: {c: 0 for c in active_colors} for t in range(1, max_turn + 1)}
        color_block_counts: Dict[int, Dict[str, int]] = {t: {c: 0 for c in active_colors} for t in range(1, max_turn + 1)}
        spells_considered: Dict[int, int] = {t: 0 for t in range(1, max_turn + 1)}
        spells_castable: Dict[int, int] = {t: 0 for t in range(1, max_turn + 1)}
        color_need_k_hist: Dict[int, Dict[str, Dict[int, int]]] = {t: {c: {k: 0 for k in range(1, K_MAX_SUGGEST+1)} for c in active_colors} for t in range(1, max_turn + 1)}

        for _ in range(int(self.params.iterations)):
            # Shuffle library
            library = list(cards)
            random.shuffle(library)

            hand: List[Dict] = []
            battlefield_lands: List[Tuple[Dict, int]] = []  # (card, entered_turn)
            battlefield_rocks: List[Tuple[Dict, int]] = []  # (card, entered_turn)
            added_tapped_lands_this_turn: List[Tuple[Dict, int]] = []

            # Draw opening hand (7 cards)
            for _draw in range(7):
                if library:
                    hand.append(library.pop())

            # Opening hand land count
            opening_lands = sum(1 for c in hand if is_land(c))
            opening_hand_land_hist[opening_lands] = opening_hand_land_hist.get(opening_lands, 0) + 1

            # Track earliest castable turn per card name in this iteration
            first_cast_turn: Dict[str, int] = {}

            for turn in range(1, max_turn + 1):
                # Draw phase
                if not (self.params.on_the_play and turn == 1):
                    if library:
                        hand.append(library.pop())

                # Land play step
                land_to_play_idx = _choose_land_to_play(hand, needed_colors, self.params.respect_enters_tapped)
                if land_to_play_idx is not None:
                    land_card = hand.pop(land_to_play_idx)
                    if self.params.respect_enters_tapped and enters_tapped_this_turn(land_card):
                        # Will be usable next turn
                        added_tapped_lands_this_turn.append((land_card, turn))
                    else:
                        battlefield_lands.append((land_card, turn))

                # Available sources this turn (lands that are not entering tapped + old rocks)
                sources_this_turn = _collect_available_sources(
                    battlefield_lands,
                    battlefield_rocks,
                    turn,
                )

                # Try to cast accelerators greedily
                if self.params.use_accelerators:
                    sources_this_turn, cast_any = _cast_accelerators_greedily(
                        hand,
                        sources_this_turn,
                        battlefield_rocks,
                        added_tapped_lands_this_turn,
                        needed_colors,
                        turn,
                    )
                    # sources_this_turn reflects spent sources this turn

                # Check coverage and playability with current sources
                if needed_colors:
                    if _has_color_coverage(needed_colors, sources_this_turn):
                        color_coverage_hits[turn] += 1
                else:
                    # If colors not specified (colorless deck), treat as covered
                    color_coverage_hits[turn] += 1

                # Available mana distribution (post-accelerants casting this turn)
                avail = len(sources_this_turn)
                ah = available_mana_hist[turn]
                ah[avail] = (ah.get(avail, 0) + 1)

                # Lands in play histogram
                total_lands_now = len(battlefield_lands) + len(added_tapped_lands_this_turn)
                lh = lands_in_play_hist[turn]
                lh[total_lands_now] = (lh.get(total_lands_now, 0) + 1)
                # Lands in hand histogram (after plays and ramp this turn)
                lands_in_hand_now = sum(1 for c in hand if is_land(c))
                lhh = lands_in_hand_hist[turn]
                lhh[lands_in_hand_now] = (lhh.get(lands_in_hand_now, 0) + 1)

                if _has_playable_spell(hand, sources_this_turn):
                    playable_spell_hits[turn] += 1

                # Record lands in play at end of turn
                lands_in_play_accum[turn] += total_lands_now

                # Per-card earliest castable: which cards in hand are castable right now?
                castable_names = _castable_card_names(hand, sources_this_turn)
                for name in castable_names:
                    if name not in first_cast_turn:
                        first_cast_turn[name] = turn

                # Color availability (WUBRG)
                color_set = {col for s in sources_this_turn for col in (s & set(active_colors))}
                for col in active_colors:
                    if col in color_set:
                        color_available_hits[turn][col] += 1

                # Playable fraction and color limitation
                nonland_nonacc = [c for c in hand if not is_land(c) and not is_mana_rock(c) and not is_ramp_spell(c)]
                spells_considered[turn] += len(nonland_nonacc)
                spells_castable[turn] += sum(1 for c in nonland_nonacc if c.get("name") in castable_names)

                # For uncastable spells, attribute limiting colors
                for card in nonland_nonacc:
                    if card.get("name") in castable_names:
                        continue
                    limiting = _limiting_colors_for_card(card, sources_this_turn)
                    for col in limiting:
                        if col in active_colors:
                            color_block_counts[turn][col] += 1
                    # Minimal extra needed up to K_MAX for each WUBRG color
                    for col in active_colors:
                        kmin = _min_extra_needed_for_color(card, sources_this_turn, col, K_MAX_SUGGEST)
                        if kmin is not None:
                            color_need_k_hist[turn][col][kmin] += 1

                # End of turn: tapped lands from ramp enter battlefield for next turn
                if added_tapped_lands_this_turn:
                    battlefield_lands.extend(added_tapped_lands_this_turn)
                    added_tapped_lands_this_turn = []

            # Commit earliest-castable histogram for this iteration
            for name, t0 in first_cast_turn.items():
                d = per_card_first_cast_turn_hist.setdefault(name, {})
                d[t0] = d.get(t0, 0) + 1

        iters = float(self.params.iterations)

        # Summaries for available mana per turn
        available_mana_summary: Dict[int, Dict[str, float]] = {}
        mode_available_curve: Dict[int, int] = {}
        for t in range(1, max_turn + 1):
            hist = available_mana_hist[t]
            if not hist:
                continue
            keys_sorted = sorted(hist.keys())
            total = sum(hist.values())
            min_v = keys_sorted[0]
            max_v = keys_sorted[-1]
            mode_v = max(hist.items(), key=lambda kv: kv[1])[0]
            p10 = _percentile_from_hist(hist, 0.10, total)
            p50 = _percentile_from_hist(hist, 0.50, total)
            p90 = _percentile_from_hist(hist, 0.90, total)
            available_mana_summary[t] = {
                'min': float(min_v),
                'max': float(max_v),
                'mode': float(mode_v),
                'p10': float(p10),
                'p50': float(p50),
                'p90': float(p90),
            }
            mode_available_curve[t] = int(mode_v)

        # Per-card probabilities by turn (cumulative "by turn")
        per_card_prob_by_turn: Dict[str, Dict[int, float]] = {}
        for name, hist in per_card_first_cast_turn_hist.items():
            # Build cumulative
            cumulative = 0
            turn_probs: Dict[int, float] = {}
            for t in range(1, max_turn + 1):
                cumulative += hist.get(t, 0)
                turn_probs[t] = cumulative / iters
            per_card_prob_by_turn[name] = turn_probs

        # Derive per color suggestion k by turn: smallest k where CDF >= 0.8 of blocked-by-that-color cases
        color_suggest_k: Dict[int, Dict[str, int]] = {t: {} for t in range(1, max_turn + 1)}
        TARGET_CDF = 0.80
        for t in range(1, max_turn + 1):
            for col in active_colors:
                hist = color_need_k_hist[t][col]
                total = sum(hist.values())
                if total == 0:
                    color_suggest_k[t][col] = 0
                    continue
                acc = 0
                suggested = 0
                for k in range(1, K_MAX_SUGGEST+1):
                    acc += hist.get(k, 0)
                    if acc / total >= TARGET_CDF:
                        suggested = k
                        break
                if suggested == 0:
                    suggested = K_MAX_SUGGEST
                color_suggest_k[t][col] = suggested

        result = SimulationResult(
            p_color_coverage={t: color_coverage_hits[t] / iters for t in color_coverage_hits},
            p_playable_spell={t: playable_spell_hits[t] / iters for t in playable_spell_hits},
            avg_lands_in_play={t: lands_in_play_accum[t] / iters for t in lands_in_play_accum},
            lands_in_hand_hist=lands_in_hand_hist,
            opening_hand_land_hist=opening_hand_land_hist,
            available_mana_hist=available_mana_hist,
            lands_in_play_hist=lands_in_play_hist,
            available_mana_summary=available_mana_summary,
            mode_available_mana_curve=mode_available_curve,
            per_card_first_cast_turn_hist=per_card_first_cast_turn_hist,
            per_card_prob_by_turn=per_card_prob_by_turn,
            color_available_prob={t: {c: color_available_hits[t][c] / iters for c in active_colors} for t in range(1, max_turn + 1)},
            color_limitation_rate={t: {c: (color_block_counts[t][c] / max(1, spells_considered[t])) for c in active_colors} for t in range(1, max_turn + 1)},
            playable_fraction={t: (spells_castable[t] / max(1, spells_considered[t])) for t in range(1, max_turn + 1)},
            color_need_k_hist=color_need_k_hist,
            color_suggest_k=color_suggest_k,
            active_colors=active_colors,
            params=self.params,
        )
        return result


# -----------------------------
# Internal helpers for simulation steps
# -----------------------------


def _infer_deck_colors(deck: Deck) -> List[str]:
    # Prefer commanders' color identity
    commanders = deck.get_commanders()
    colors: Set[str] = set()
    for cmd in commanders:
        for c in cmd.get("color_identity", []) or []:
            if c in COLORS:
                colors.add(c)
    if colors:
        return sorted(colors)
    return _infer_colors_from_cards(deck.cards)


def _infer_colors_from_cards(cards: Iterable[Dict]) -> List[str]:
    colors: Set[str] = set()
    for card in cards:
        for c in (card.get("color_identity") or card.get("colors") or []):
            if c in COLORS:
                colors.add(c)
    return sorted(colors)


def _choose_land_to_play(hand: List[Dict], needed_colors: List[str], respect_tapped: bool) -> Optional[int]:
    """Pick an index of a land in hand to play this turn.

    Heuristic: prefer a land that adds new color coverage; break ties by
    untapped this turn; then by number of colors the land can produce.
    """
    best_idx: Optional[int] = None
    best_score: Tuple[int, int, int] = (-1, -1, -1)

    have_colors: Set[str] = set()
    # We don't have current battlefield sources here; this heuristic is based solely on needed colors
    for idx, card in enumerate(hand):
        if not is_land(card):
            continue
        colors = card_produced_colors(card)
        if not colors:
            continue
        new_colors = sum(1 for c in colors if c in needed_colors and c not in have_colors)
        enters_tapped = enters_tapped_this_turn(card) if respect_tapped else False
        score = (
            new_colors,
            0 if not enters_tapped else -1,  # prefer untapped
            len(colors),
        )
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def _collect_available_sources(
    battlefield_lands: List[Tuple[Dict, int]],
    battlefield_rocks: List[Tuple[Dict, int]],
    turn: int,
) -> List[Set[str]]:
    sources: List[Set[str]] = []

    # Lands that are not entering tapped this turn
    for land_card, entered in battlefield_lands:
        # If the land entered this turn and is tapped, it wouldn't be in battlefield_lands yet
        colors = card_produced_colors(land_card)
        if colors:
            sources.append(colors)

    # Mana rocks from previous turns only (usable now)
    for rock_card, entered in battlefield_rocks:
        if entered < turn:
            colors = card_produced_colors(rock_card)
            if not colors:
                # Treat unknown rocks as colorless fixer (+1 generic)
                colors = {"C"}
            # For rocks that add any color (e.g., {W}{U}{B}{R}{G}), treat as flexible
            sources.append(set(colors) if colors else {"C"})

    return sources


def _cast_accelerators_greedily(
    hand: List[Dict],
    sources_this_turn: List[Set[str]],
    battlefield_rocks: List[Tuple[Dict, int]],
    added_tapped_lands_this_turn: List[Tuple[Dict, int]],
    needed_colors: List[str],
    turn: int,
) -> Tuple[List[Set[str]], bool]:
    """Attempt to cast accelerators (mana rocks and ramp spells) by lowest CMC.

    Returns updated sources_this_turn after paying costs, and whether any were cast.
    """
    # Collect candidates
    candidates: List[Tuple[int, Dict]] = []  # (cmc, card)
    for card in hand:
        if is_mana_rock(card) or is_ramp_spell(card):
            cmc = int(card.get("cmc", 0) or 0)
            candidates.append((cmc, card))

    if not candidates:
        return sources_this_turn, False

    # Sort by lowest CMC first
    candidates.sort(key=lambda t: t[0])

    any_cast = False
    # Mutable working copies
    remaining_sources = list(sources_this_turn)

    # We may cast multiple accelerants if mana allows
    for _, card in list(candidates):
        cost = parse_mana_cost(card.get("mana_cost", ""))
        if can_pay_cost_with_sources(cost, remaining_sources):
            # Spend mana: remove as many sources as required (colored first)
            remaining_sources = _spend_mana(remaining_sources, cost)
            # Move card from hand to battlefield effect
            hand.remove(card)
            if is_mana_rock(card):
                battlefield_rocks.append((card, turn))  # usable next turn
                any_cast = True
            elif is_ramp_spell(card):
                # Put one land into play tapped now (usable next turn) and one basic to hand
                land_color = _pick_fetch_color(needed_colors)
                tapped_land = _make_basic_land_card(land_color)
                added_tapped_lands_this_turn.append((tapped_land, turn))
                # Add a basic land to hand for a future land drop
                hand.append(_make_basic_land_card(land_color))
                any_cast = True

    return remaining_sources, any_cast


def _spend_mana(sources: List[Set[str]], cost: Dict[str, int]) -> List[Set[str]]:
    """Return a new list of sources after paying a cost with a greedy strategy."""
    remaining = list(sources)
    used: Set[int] = set()

    # Colored first (W, U, B, R, G)
    for color in ["W", "U", "B", "R", "G"]:
        for _ in range(int(cost.get(color, 0) or 0)):
            idx = _pick_source_for_color(color, remaining, used)
            if idx is None:
                return remaining  # Shouldn't happen if caller ensured can_pay_cost
            used.add(idx)

    # Explicit colorless 'C'
    for _ in range(int(cost.get("C", 0) or 0)):
        idx = _pick_source_for_color("C", remaining, used, prefer_exact=True)
        if idx is None:
            idx = _pick_any_unused_source(remaining, used)
        if idx is None:
            return remaining
        used.add(idx)

    # Generic
    generic = int(cost.get("generic", 0) or 0)
    for _ in range(generic):
        idx = _pick_any_unused_source(remaining, used)
        if idx is None:
            break
        used.add(idx)

    # Remove used sources
    new_sources = [s for i, s in enumerate(remaining) if i not in used]
    return new_sources


def _pick_fetch_color(needed_colors: List[str]) -> str:
    # Choose first needed color; default to 'G' then 'U' then any
    for c in needed_colors:
        return c
    return "G"


def _make_basic_land_card(color: str) -> Dict:
    # Minimal representation of a basic land
    subtype = {
        "W": "Plains",
        "U": "Island",
        "B": "Swamp",
        "R": "Mountain",
        "G": "Forest",
        "C": "Wastes",
    }.get(color, "Forest")
    mana_map = {
        "Plains": ["W"],
        "Island": ["U"],
        "Swamp": ["B"],
        "Mountain": ["R"],
        "Forest": ["G"],
        "Wastes": ["C"],
    }
    return {
        "name": subtype,
        "type_line": "Basic Land — " + subtype,
        "oracle_text": "",
        "produced_mana": mana_map.get(subtype, ["G"]),
        "quantity": 1,
    }


def _has_color_coverage(needed_colors: List[str], sources: List[Set[str]]) -> bool:
    available = set()
    for s in sources:
        available |= (s & set(needed_colors))
    return all(c in available for c in needed_colors)


def _has_playable_spell(hand: List[Dict], sources: List[Set[str]]) -> bool:
    # Consider non-land, non-accelerant spells
    for card in hand:
        if is_land(card) or is_mana_rock(card) or is_ramp_spell(card):
            continue
        cost = parse_mana_cost(card.get("mana_cost", ""))
        if can_pay_cost_with_sources(cost, sources):
            return True
    return False


def _castable_card_names(hand: List[Dict], sources: List[Set[str]]) -> Set[str]:
    names: Set[str] = set()
    for card in hand:
        if is_land(card):
            continue
        cost = parse_mana_cost(card.get("mana_cost", ""))
        if can_pay_cost_with_sources(cost, sources):
            name = card.get("name")
            if name:
                names.add(name)
    return names


def _limiting_colors_for_card(card: Dict, sources: List[Set[str]]) -> Set[str]:
    """Return colors that, if one extra source of that color were available,
    would make this card castable. Used to attribute color bottlenecks.
    """
    cost = parse_mana_cost(card.get("mana_cost", ""))
    # If already castable, no limiting colors
    if can_pay_cost_with_sources(cost, sources):
        return set()
    limiting: Set[str] = set()
    for col in ["W","U","B","R","G"]:
        trial_sources = list(sources) + [{col}]
        if can_pay_cost_with_sources(cost, trial_sources):
            limiting.add(col)
    return limiting


def _min_extra_needed_for_color(card: Dict, sources: List[Set[str]], color: str, k_max: int) -> Optional[int]:
    cost = parse_mana_cost(card.get("mana_cost", ""))
    if can_pay_cost_with_sources(cost, sources):
        return None
    for k in range(1, k_max + 1):
        trial_sources = list(sources) + [set([color]) for _ in range(k)]
        if can_pay_cost_with_sources(cost, trial_sources):
            return k
    return None


__all__ = [
    "SimulationParams",
    "SimulationResult",
    "ManaSimulator",
    "parse_mana_cost",
]


# -----------------------------
# Helpers: histogram percentiles
# -----------------------------


def _percentile_from_hist(hist: Dict[int, int], q: float, total: Optional[int] = None) -> int:
    """Approximate percentile from a discrete histogram.

    hist: value -> frequency
    q: quantile in [0,1]
    total: optional precomputed total frequency
    Returns an integer value at or above the q-quantile.
    """
    if not hist:
        return 0
    if total is None:
        total = sum(hist.values())
    target = q * total
    acc = 0
    for v in sorted(hist.keys()):
        acc += hist[v]
        if acc >= target:
            return int(v)
    return int(max(hist.keys()))
