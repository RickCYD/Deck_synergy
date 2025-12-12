from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import contextlib
import random
import hashlib
import time
from typing import Iterable, List, Tuple, Dict

import pandas as pd

from simulate_game import Card, simulate_game
from statistical_analysis import (
    analyze_metric_distribution,
    summarize_simulation_validity,
    format_statistical_report,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _generate_deck_seed(cards: List[Card], commander_card: Card) -> int:
    """
    Generate a deterministic seed based on deck composition.

    This ensures the same deck always produces the same simulation results,
    providing consistent and reproducible statistics for deck power analysis.

    Args:
        cards: List of cards in the deck
        commander_card: Commander card

    Returns:
        Integer seed value (0-2^31)
    """
    # Create a deterministic string from deck composition
    card_names = sorted([card.name for card in cards])
    if commander_card:
        card_names.append(f"COMMANDER:{commander_card.name}")

    deck_string = "|".join(card_names)

    # Hash to get deterministic seed
    hash_obj = hashlib.md5(deck_string.encode('utf-8'))
    seed = int(hash_obj.hexdigest()[:8], 16)  # Use first 8 hex digits

    return seed


def _simulate_single_game(args: Tuple[List[Card], Card, int, bool, Path | None, int, int]):
    """Wrapper around :func:`simulate_game` to support multiprocessing."""
    cards, commander_card, max_turns, verbose, log_dir, game_index, deck_seed = args
    # Use deterministic seed based on deck composition + game index
    # This ensures the same deck always produces statistically consistent results
    # while each game within a run is different
    random.seed(deck_seed + game_index)
    if log_dir is not None and verbose:
        log_path = log_dir / f"game_{game_index + 1}.log"
        with open(log_path, "w") as fh, contextlib.redirect_stdout(fh):
            return simulate_game(cards, commander_card, max_turns, verbose=True)
    return simulate_game(cards, commander_card, max_turns, verbose=verbose)


def _aggregate_results(results: Iterable[dict], num_games: int, max_turns: int, calculate_statistics: bool = True):
    """Aggregate per game metrics into summary statistics.

    Parameters
    ----------
    results
        Iterable of per-game metric dictionaries
    num_games
        Number of games simulated
    max_turns
        Maximum turns per game
    calculate_statistics
        If True, calculate statistical validity metrics (CV, CI, etc.)

    Returns
    -------
    tuple
        (summary_df, commander_distribution, avg_creature_power, interaction_summary, statistical_report)
    """
    total_cards_played = [0] * (max_turns + 1)
    total_lands_played = [0] * (max_turns + 1)
    total_mana = [0] * (max_turns + 1)
    total_castable = [0] * (max_turns + 1)
    total_damage = [0] * (max_turns + 1)
    total_drain_damage = [0] * (max_turns + 1)  # NEW: Aristocrats drain
    total_tokens_created = [0] * (max_turns + 1)  # NEW: Token generation
    total_creatures_sacrificed = [0] * (max_turns + 1)  # NEW: Sacrifice outlets
    total_cards_drawn = [0] * (max_turns + 1)  # NEW: Card draw tracking
    total_life_gained = [0] * (max_turns + 1)  # NEW: Life gained tracking
    total_life_lost = [0] * (max_turns + 1)  # NEW: Life lost tracking
    total_unspent = [0] * (max_turns + 1)
    ramp_cards_played = [0] * (max_turns + 1)
    total_hand_size = [0] * (max_turns + 1)
    total_non_land = [0] * (max_turns + 1)
    total_castable_non_land = [0] * (max_turns + 1)
    total_uncastable_non_land = [0] * (max_turns + 1)
    total_power = [0] * (max_turns + 1)
    total_toughness = [0] * (max_turns + 1)
    total_counter_power = [0] * (max_turns + 1)
    total_lands_etb_tapped = [0] * (max_turns + 1)

    # New interaction metrics
    total_opponents_alive = [0] * (max_turns + 1)
    total_opponent_power = [0] * (max_turns + 1)
    total_graveyard_size = [0] * (max_turns + 1)
    total_creatures_removed = 0
    total_wipes_survived = 0
    games_won = 0
    win_turns: List[int] = []  # Track which turn each game was won

    COLOURS = ["W", "U", "B", "R", "G", "C", "Any"]
    total_board_mana = {c: [0] * (max_turns + 1) for c in COLOURS}
    total_hand_mana = {c: [0] * (max_turns + 1) for c in COLOURS}

    commander_cast_turns: List[int | None] = []
    total_creature_power: dict[str, float] = {}

    # Track per-game cumulative values for statistical analysis
    per_game_total_damage: List[float] = []
    per_game_total_mana: List[float] = []
    per_game_cards_played: List[float] = []
    per_game_total_power: List[float] = []
    per_game_drain_damage: List[float] = []
    per_game_tokens_created: List[float] = []
    per_game_cards_drawn: List[float] = []

    # Track card impact analysis - which cards lead to best outcomes
    card_impact_data: dict[str, list] = {}  # card_name -> list of game outcomes
    opening_hand_outcomes: list[tuple[list[str], dict]] = []  # (hand, outcome) pairs

    for metrics in results:
        for turn in range(1, max_turns + 1):
            total_lands_played[turn] += metrics["lands_played"][turn]
            total_mana[turn] += metrics["total_mana"][turn]
            total_castable[turn] += metrics["castable_spells"][turn]
            total_damage[turn] += metrics["combat_damage"][turn]
            total_drain_damage[turn] += metrics.get("drain_damage", [0] * (max_turns + 1))[turn]  # ARISTOCRATS
            total_tokens_created[turn] += metrics.get("tokens_created", [0] * (max_turns + 1))[turn]  # ARISTOCRATS
            total_creatures_sacrificed[turn] += metrics.get("creatures_sacrificed", [0] * (max_turns + 1))[turn]  # ARISTOCRATS
            total_cards_drawn[turn] += metrics.get("cards_drawn", [0] * (max_turns + 1))[turn]  # DECK POTENTIAL
            total_life_gained[turn] += metrics.get("life_gained", [0] * (max_turns + 1))[turn]  # DECK POTENTIAL
            total_life_lost[turn] += metrics.get("life_lost", [0] * (max_turns + 1))[turn]  # DECK POTENTIAL
            total_unspent[turn] += metrics["unspent_mana"][turn]
            ramp_cards_played[turn] += metrics["ramp_cards_played"][turn]
            total_cards_played[turn] += metrics["cards_played"][turn]
            total_hand_size[turn] += metrics["hand_size"][turn]
            total_non_land[turn] += metrics["non_land_cards"][turn]
            total_castable_non_land[turn] += metrics["castable_non_lands"][turn]
            total_uncastable_non_land[turn] += metrics["uncastable_non_lands"][turn]
            total_power[turn] += metrics.get("total_power", [0])[turn]
            total_toughness[turn] += metrics.get("total_toughness", [0])[turn]
            total_counter_power[turn] += metrics.get("power_from_counters", [0])[turn]
            total_lands_etb_tapped[turn] += metrics.get("lands_etb_tapped", [0])[turn]

            # New interaction metrics
            total_opponents_alive[turn] += metrics.get("opponents_alive", [0])[turn]
            total_opponent_power[turn] += metrics.get("opponent_total_power", [0])[turn]
            total_graveyard_size[turn] += metrics.get("creatures_in_graveyard", [0])[turn]

            for col in COLOURS:
                total_board_mana[col][turn] += metrics.get(f"board_mana_{col}", [0])[turn]
                total_hand_mana[col][turn] += metrics.get(f"hand_mana_{col}", [0])[turn]

        # Aggregate interaction metrics
        total_creatures_removed += metrics.get("creatures_removed_by_opponents", 0)
        total_wipes_survived += metrics.get("board_wipes_survived", 0)
        if metrics.get("game_won") is not None:
            games_won += 1
            win_turns.append(metrics["game_won"])

        for name, p in metrics.get("creature_power", {}).items():
            total_creature_power[name] = total_creature_power.get(name, 0) + p
        commander_cast_turns.append(metrics.get("commander_cast_turn"))

        # Calculate cumulative per-game values for statistics
        game_total_damage = sum(metrics["combat_damage"][1:max_turns+1])
        game_drain_damage = sum(metrics.get("drain_damage", [0] * (max_turns + 1))[1:max_turns+1])
        game_total_mana = sum(metrics["total_mana"][1:max_turns+1])
        game_cards_played = sum(metrics["cards_played"][1:max_turns+1])
        game_total_power = max(metrics.get("total_power", [0])[1:max_turns+1]) if metrics.get("total_power") else 0
        game_tokens_created = sum(metrics.get("tokens_created", [0] * (max_turns + 1))[1:max_turns+1])
        game_cards_drawn = sum(metrics.get("cards_drawn", [0] * (max_turns + 1))[1:max_turns+1])

        per_game_total_damage.append(game_total_damage + game_drain_damage)
        per_game_total_mana.append(game_total_mana)
        per_game_cards_played.append(game_cards_played)
        per_game_total_power.append(game_total_power)
        per_game_drain_damage.append(game_drain_damage)
        per_game_tokens_created.append(game_tokens_created)
        per_game_cards_drawn.append(game_cards_drawn)

        # Track card impact - correlate opening hand cards with game outcomes
        opening_hand = metrics.get("opening_hand_cards", [])
        if opening_hand:
            # Create outcome summary for this game
            game_outcome = {
                'total_damage': game_total_damage + game_drain_damage,
                'peak_power': game_total_power,
                'commander_turn': metrics.get("commander_cast_turn"),
                'total_mana': game_total_mana,
                'cards_drawn': game_cards_drawn,
            }

            # Store opening hand with its outcome
            opening_hand_outcomes.append((opening_hand, game_outcome))

            # Track each card's impact
            for card_name in opening_hand:
                if card_name not in card_impact_data:
                    card_impact_data[card_name] = []
                card_impact_data[card_name].append(game_outcome)

    avg_lands = [round(total_lands_played[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_mana = [round(total_mana[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_castable = [round(total_castable[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_damage = [round(total_damage[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_unspent = [round(total_unspent[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_ramp_card = [round(ramp_cards_played[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_cards_played = [round(total_cards_played[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_hand_size = [round(total_hand_size[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_non_land = [round(total_non_land[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_castable_non_land = [round(total_castable_non_land[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_uncastable_non_land = [round(total_uncastable_non_land[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_power = [round(total_power[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_counter_power = [round(total_counter_power[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_toughness = [round(total_toughness[t] / num_games, 2) for t in range(max_turns + 1)]
    pct_castable = [
        round((avg_castable_non_land[t] / avg_non_land[t]) * 100, 2) if avg_non_land[t] > 0 else 0
        for t in range(max_turns + 1)
    ]
    avg_lands_etb_tapped = [round(total_lands_etb_tapped[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_board_mana = {
        c: [round(total_board_mana[c][t] / num_games, 2) for t in range(max_turns + 1)]
        for c in COLOURS
    }
    avg_hand_mana = {
        c: [round(total_hand_mana[c][t] / num_games, 2) for t in range(max_turns + 1)]
        for c in COLOURS
    }
    avg_creature_power = {
        name: round(total_creature_power[name] / num_games, 2) for name in total_creature_power
    }

    # New averaged metrics
    avg_opponents_alive = [round(total_opponents_alive[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_opponent_power = [round(total_opponent_power[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_graveyard_size = [round(total_graveyard_size[t] / num_games, 2) for t in range(max_turns + 1)]

    # ARISTOCRATS: Average new metrics
    avg_drain_damage = [round(total_drain_damage[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_tokens_created = [round(total_tokens_created[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_creatures_sacrificed = [round(total_creatures_sacrificed[t] / num_games, 2) for t in range(max_turns + 1)]

    # DECK POTENTIAL: Average new metrics
    avg_cards_drawn = [round(total_cards_drawn[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_life_gained = [round(total_life_gained[t] / num_games, 2) for t in range(max_turns + 1)]
    avg_life_lost = [round(total_life_lost[t] / num_games, 2) for t in range(max_turns + 1)]

    # ARISTOCRATS: Combine combat + drain for total damage
    avg_total_damage = [round(avg_damage[t] + avg_drain_damage[t], 2) for t in range(max_turns + 1)]

    data = {
        "Turn": list(range(1, max_turns + 1)),
        "Avg Lands in Play": avg_lands[1:],
        "Avg Total Mana": avg_mana[1:],
        "Avg Castable Spells": avg_castable[1:],
        "Avg Combat Damage": avg_damage[1:],
        "Avg Drain Damage": avg_drain_damage[1:],  # NEW
        "Avg Total Damage": avg_total_damage[1:],  # NEW: Combat + Drain
        "Avg Tokens Created": avg_tokens_created[1:],  # NEW
        "Avg Creatures Sacrificed": avg_creatures_sacrificed[1:],  # NEW
        "Avg Cards Drawn": avg_cards_drawn[1:],  # NEW
        "Avg Life Gained": avg_life_gained[1:],  # NEW
        "Avg Life Lost": avg_life_lost[1:],  # NEW
        "Avg Unspent Mana": avg_unspent[1:],
        "Avg Ramp Cards Played": avg_ramp_card[1:],
        "Avg Cards Played": avg_cards_played[1:],
        "Avg Hand Size": avg_hand_size[1:],
        "Avg Non-Lands": avg_non_land[1:],
        "Avg Castable Non-Lands": avg_castable_non_land[1:],
        "Avg Uncastable Non-Lands": avg_uncastable_non_land[1:],
        "Avg Total Power": avg_power[1:],
        "Avg Power from Counters": avg_counter_power[1:],
        "Avg Total Toughness": avg_toughness[1:],
        "Castable %": pct_castable[1:],
        "Avg Lands ETB Tapped": avg_lands_etb_tapped[1:],
        "Avg Opponents Alive": avg_opponents_alive[1:],
        "Avg Opponent Power": avg_opponent_power[1:],
        "Avg Graveyard Size": avg_graveyard_size[1:],
    }

    # ==================================================================================
    # CARD IMPACT ANALYSIS - Which cards contribute most to wins
    # ==================================================================================

    # Calculate average performance across all games (baseline)
    baseline_damage = sum(per_game_total_damage) / len(per_game_total_damage) if per_game_total_damage else 0
    baseline_power = sum(per_game_total_power) / len(per_game_total_power) if per_game_total_power else 0
    baseline_mana = sum(per_game_total_mana) / len(per_game_total_mana) if per_game_total_mana else 0

    # Analyze impact of each card
    card_impact_analysis = []
    for card_name, outcomes in card_impact_data.items():
        if len(outcomes) < 3:  # Need at least 3 games for meaningful data
            continue

        avg_damage = sum(o['total_damage'] for o in outcomes) / len(outcomes)
        avg_power = sum(o['peak_power'] for o in outcomes) / len(outcomes)
        avg_mana = sum(o['total_mana'] for o in outcomes) / len(outcomes)

        # Commander cast turn (handle None values)
        cmd_turns = [o['commander_turn'] for o in outcomes if o['commander_turn'] is not None]
        avg_cmd_turn = sum(cmd_turns) / len(cmd_turns) if cmd_turns else None

        # Calculate impact score (how much better than baseline)
        damage_impact = ((avg_damage - baseline_damage) / baseline_damage * 100) if baseline_damage > 0 else 0
        power_impact = ((avg_power - baseline_power) / baseline_power * 100) if baseline_power > 0 else 0

        # Overall impact score (weighted: 60% damage, 40% power)
        overall_impact = (damage_impact * 0.6) + (power_impact * 0.4)

        card_impact_analysis.append({
            'card_name': card_name,
            'appearances': len(outcomes),
            'avg_damage': round(avg_damage, 2),
            'avg_peak_power': round(avg_power, 2),
            'avg_commander_turn': round(avg_cmd_turn, 2) if avg_cmd_turn else None,
            'damage_impact_%': round(damage_impact, 1),
            'power_impact_%': round(power_impact, 1),
            'overall_impact': round(overall_impact, 1),
        })

    # Sort by overall impact (best cards first)
    card_impact_analysis.sort(key=lambda x: x['overall_impact'], reverse=True)

    # Get top performers and worst performers (exclude basic lands)
    non_land_impacts = [c for c in card_impact_analysis if c['card_name'].lower() not in ['plains', 'island', 'swamp', 'mountain', 'forest']]
    top_impact_cards = non_land_impacts[:10] if len(non_land_impacts) >= 10 else non_land_impacts
    worst_impact_cards = non_land_impacts[-10:] if len(non_land_impacts) >= 10 else []

    # ==================================================================================
    # BEST & WORST OPENING HANDS
    # ==================================================================================

    # Sort all opening hands by their outcome
    sorted_hands = sorted(
        opening_hand_outcomes,
        key=lambda x: x[1]['total_damage'],
        reverse=True
    )

    best_opening_hands = sorted_hands[:5]  # Top 5 best
    worst_opening_hands = sorted_hands[-5:]  # Bottom 5 worst

    # ==================================================================================
    # DECK POWER SUMMARY
    # ==================================================================================

    import statistics

    deck_power_summary = {
        # Overall performance
        "Avg Total Damage": round(baseline_damage, 2),
        "Avg Peak Power": round(baseline_power, 2),
        "Avg Commander Cast Turn": round(sum(c for c in commander_cast_turns if c is not None) / len([c for c in commander_cast_turns if c is not None]), 2) if any(c is not None for c in commander_cast_turns) else None,

        # Consistency metrics
        "Damage Std Dev": round(statistics.stdev(per_game_total_damage), 2) if len(per_game_total_damage) > 1 else 0,
        "Power Std Dev": round(statistics.stdev(per_game_total_power), 2) if len(per_game_total_power) > 1 else 0,
        "Best Game Damage": round(max(per_game_total_damage), 2) if per_game_total_damage else 0,
        "Worst Game Damage": round(min(per_game_total_damage), 2) if per_game_total_damage else 0,
        "Best Game Power": round(max(per_game_total_power), 2) if per_game_total_power else 0,
        "Worst Game Power": round(min(per_game_total_power), 2) if per_game_total_power else 0,

        # Consistency score (lower is more consistent)
        "Consistency Score": round((statistics.stdev(per_game_total_damage) / baseline_damage * 100), 1) if baseline_damage > 0 and len(per_game_total_damage) > 1 else 0,
    }

    # Add interaction summary
    avg_win_turn = round(sum(win_turns) / len(win_turns), 1) if win_turns else None
    interaction_summary = {
        "Games Won": games_won,
        "Win Rate %": round((games_won / num_games) * 100, 2),
        "Avg Win Turn": avg_win_turn,
        "Avg Creatures Removed": round(total_creatures_removed / num_games, 2),
        "Avg Board Wipes Survived": round(total_wipes_survived / num_games, 2),

        # NEW: Meaningful metrics
        "Deck Power Summary": deck_power_summary,
        "Top Impact Cards": top_impact_cards,
        "Worst Impact Cards": worst_impact_cards,
        "Best Opening Hands": [
            {
                'hand': hand,
                'damage': outcome['total_damage'],
                'peak_power': outcome['peak_power'],
                'commander_turn': outcome['commander_turn']
            }
            for hand, outcome in best_opening_hands
        ],
        "Worst Opening Hands": [
            {
                'hand': hand,
                'damage': outcome['total_damage'],
                'peak_power': outcome['peak_power'],
                'commander_turn': outcome['commander_turn']
            }
            for hand, outcome in worst_opening_hands
        ],
    }
    for c in COLOURS:
        data[f"Board Mana {c}"] = avg_board_mana[c][1:]
        data[f"Hand Mana {c}"] = avg_hand_mana[c][1:]

    summary_df = pd.DataFrame(data)

    commander_cast_turns_clean = [t if t is not None else (max_turns + 1) for t in commander_cast_turns]
    commander_cast_series = pd.Series(commander_cast_turns_clean)
    turns = range(1, max_turns + 2)
    distribution = commander_cast_series.value_counts().reindex(turns, fill_value=0).sort_index()

    # Calculate statistical validity analysis
    statistical_report = None
    if calculate_statistics and num_games >= 10:
        key_metrics = {
            "Total Damage (Combat + Drain)": per_game_total_damage,
            "Total Mana Generated": per_game_total_mana,
            "Cards Played": per_game_cards_played,
            "Peak Board Power": per_game_total_power,
            "Drain Damage": per_game_drain_damage,
            "Tokens Created": per_game_tokens_created,
            "Cards Drawn": per_game_cards_drawn,
        }

        validity_summary = summarize_simulation_validity(key_metrics, num_games)
        statistical_report = {
            "summary": validity_summary,
            "formatted_report": format_statistical_report(validity_summary)
        }

    return summary_df, distribution, avg_creature_power, interaction_summary, statistical_report


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_simulations(
    cards: List[Card],
    commander_card: Card,
    num_games: int,
    max_turns: int = 10,
    verbose: bool = True,
    log_dir: str | Path | None = "logs",
    num_workers: int = 1,
    calculate_statistics: bool = True,
    use_random_seed: bool = True,
):
    """Run multiple game simulations and aggregate the results.

    Parameters
    ----------
    cards
        The deck to simulate.
    commander_card
        The commander for the deck.
    num_games
        Number of games to simulate.
    max_turns
        How many turns to simulate in each game.
    verbose
        If ``True`` prints a detailed log for each game.
    log_dir
        Directory where per-game logs are written. When provided, a file
        ``game_<n>.log`` will capture the output of the ``verbose`` logs for
        game ``n`` (1-indexed).
    num_workers
        When greater than ``1`` the simulations are executed in parallel using
        a :class:`~concurrent.futures.ProcessPoolExecutor`.
    calculate_statistics
        If ``True``, calculate statistical validity metrics (CV, confidence intervals, etc.).
        Adds a statistical report as the 5th return value.
    use_random_seed
        If ``True`` (default), use time-based random seeds for each simulation run.
        This ensures different opening hands and tests all card combinations.
        If ``False``, use deterministic seeds based on deck composition for
        reproducible results (useful for testing).

    Returns
    -------
    tuple
        (summary_df, commander_distribution, avg_creature_power, interaction_summary, statistical_report)
    """
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

    # Generate seed based on mode
    if use_random_seed:
        # Use time-based random seed for true randomization
        # This ensures different results each time you run the simulation
        deck_seed = int(time.time() * 1000000) % (2**31)  # Use microseconds for uniqueness
        print(f"[SIMULATION] Using RANDOM seed: {deck_seed} (tests all card combinations)")
    else:
        # Use deterministic seed from deck composition
        # This ensures the same deck always produces the same statistical results
        deck_seed = _generate_deck_seed(cards, commander_card)
        print(f"[SIMULATION] Using DETERMINISTIC seed: {deck_seed} (ensures consistent results for this deck)")

    args = [(cards, commander_card, max_turns, verbose, log_dir, i, deck_seed) for i in range(num_games)]

    if num_workers and num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            results = list(executor.map(_simulate_single_game, args))
    else:
        results = [_simulate_single_game(a) for a in args]

    return _aggregate_results(results, num_games, max_turns, calculate_statistics)
