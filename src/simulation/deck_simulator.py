"""
Deck Simulator Integration
Integrates the Simulation engine with the deck synergy analyzer
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add Simulation directory to path
simulation_path = Path(__file__).parent.parent.parent / "Simulation"
if str(simulation_path) not in sys.path:
    sys.path.insert(0, str(simulation_path))

# Lazy imports - only import when functions are called
# This prevents import errors from breaking the entire module
_simulation_imports_loaded = False
_import_error = None

def _ensure_simulation_imports():
    """Ensure simulation modules are imported"""
    global _simulation_imports_loaded, _import_error, Card, simulate_game, run_simulations, parse_mana_cost
    global parse_death_triggers_from_oracle, parse_sacrifice_outlet_from_oracle

    if _simulation_imports_loaded:
        return True

    if _import_error is not None:
        raise _import_error

    try:
        from simulate_game import Card as _Card, simulate_game as _simulate_game
        from run_simulation import run_simulations as _run_simulations
        from convert_dataframe_deck import parse_mana_cost as _parse_mana_cost
        from oracle_text_parser import (
            parse_death_triggers_from_oracle as _parse_death,
            parse_sacrifice_outlet_from_oracle as _parse_sac
        )

        # Store in module namespace
        globals()['Card'] = _Card
        globals()['simulate_game'] = _simulate_game
        globals()['run_simulations'] = _run_simulations
        globals()['parse_mana_cost'] = _parse_mana_cost
        globals()['parse_death_triggers_from_oracle'] = _parse_death
        globals()['parse_sacrifice_outlet_from_oracle'] = _parse_sac

        _simulation_imports_loaded = True
        return True
    except Exception as e:
        _import_error = e
        raise ImportError(f"Failed to import simulation modules: {e}") from e


def convert_card_to_simulation_format(card_data: Dict):
    """
    Convert a card from the main app format to simulation Card format

    Args:
        card_data: Card dictionary from Scryfall/main app

    Returns:
        Card object for simulation
    """
    # Ensure imports are loaded
    _ensure_simulation_imports()

    # Extract basic info
    name = card_data.get('name', '')
    type_line = card_data.get('type_line', '')
    mana_cost = card_data.get('mana_cost', '')
    oracle_text = card_data.get('oracle_text', '')

    # Use the full type line - the simulation uses 'in' checks like "if 'Creature' in card.type"
    # This allows proper handling of multi-type cards like "Artifact Creature" or "Legendary Land"
    card_type = type_line if type_line else 'Unknown'

    # Extract power/toughness
    power = None
    toughness = None
    if 'power' in card_data and card_data['power'] not in [None, '', '*']:
        try:
            power = int(card_data['power'])
        except (ValueError, TypeError):
            power = 0
    if 'toughness' in card_data and card_data['toughness'] not in [None, '', '*']:
        try:
            toughness = int(card_data['toughness'])
        except (ValueError, TypeError):
            toughness = 0

    # Determine mana production
    mana_production = 0
    produces_colors = []

    if 'Land' in card_type:
        mana_production = 1
        # Try to get produced mana from card data
        if 'produced_mana' in card_data:
            produces_colors = card_data['produced_mana']
        else:
            # Parse from oracle text or name for basic lands
            if 'Plains' in name:
                produces_colors = ['W']
            elif 'Island' in name:
                produces_colors = ['U']
            elif 'Swamp' in name:
                produces_colors = ['B']
            elif 'Mountain' in name:
                produces_colors = ['R']
            elif 'Forest' in name:
                produces_colors = ['G']
            elif 'add' in oracle_text.lower():
                # Try to extract from oracle text
                produces_colors = ['Any']  # Default for now

    # Check for mana rocks (artifacts that produce mana)
    if 'Artifact' in card_type:
        # Check if it's a mana rock
        if 'add' in oracle_text.lower() and any(x in oracle_text.lower() for x in ['{t}', 'tap']):
            # Count how many mana it produces
            if 'Sol Ring' in name:
                mana_production = 2
                produces_colors = ['C']
            elif any(x in oracle_text for x in ['{T}: Add', 'Tap: Add']):
                mana_production = 1
                produces_colors = ['Any']

    # Check for mana dorks (creatures that produce mana)
    if 'Creature' in card_type:
        # Check for mana dorks
        if 'add' in oracle_text.lower() and any(x in oracle_text.lower() for x in ['{t}', 'tap']):
            mana_production = 1
            produces_colors = ['Any']

    # Check for keywords
    has_haste = 'haste' in oracle_text.lower() or 'haste' in type_line.lower()
    has_flash = 'flash' in oracle_text.lower()
    has_trample = 'trample' in oracle_text.lower()
    has_first_strike = 'first strike' in oracle_text.lower()

    # Check for ETB tapped
    etb_tapped = 'enters the battlefield tapped' in oracle_text.lower()

    # Check for ramp effects
    puts_land = 'search your library' in oracle_text.lower() and 'land' in oracle_text.lower()

    # Check for draw effects
    draw_cards = 0
    if 'draw' in oracle_text.lower():
        # Try to extract number
        import re
        match = re.search(r'draw (\d+)', oracle_text.lower())
        if match:
            draw_cards = int(match.group(1))
        elif 'draw a card' in oracle_text.lower():
            draw_cards = 1

    # Check for legendary
    is_legendary = 'legendary' in type_line.lower()

    # ARISTOCRATS: Parse death triggers and sacrifice outlets
    death_trigger_value = parse_death_triggers_from_oracle(oracle_text)
    sacrifice_outlet = parse_sacrifice_outlet_from_oracle(oracle_text)

    # DEBUG: Print aristocrats cards
    if death_trigger_value > 0 or sacrifice_outlet:
        print(f"  [ARISTOCRATS] {name}:")
        print(f"    death_trigger_value={death_trigger_value}")
        print(f"    sacrifice_outlet={sacrifice_outlet}")
        print(f"    oracle_text={oracle_text[:100] if oracle_text else 'MISSING'}...")

    # Create Card object
    return Card(
        name=name,
        type=card_type,
        mana_cost=mana_cost,
        power=power,
        toughness=toughness,
        produces_colors=produces_colors,
        mana_production=mana_production,
        etb_tapped=etb_tapped,
        etb_tapped_conditions={},
        has_haste=has_haste,
        has_flash=has_flash,
        has_trample=has_trample,
        has_first_strike=has_first_strike,
        is_legendary=is_legendary,
        puts_land=puts_land,
        draw_cards=draw_cards,
        oracle_text=oracle_text,
        death_trigger_value=death_trigger_value,
        sacrifice_outlet=sacrifice_outlet
    )


def simulate_deck_effectiveness(
    cards: List[Dict],
    commander: Optional[Dict] = None,
    num_games: int = 100,
    max_turns: int = 10,
    verbose: bool = False
) -> Dict:
    """
    Simulate a deck and return effectiveness metrics

    Args:
        cards: List of card dictionaries (Scryfall format)
        commander: Commander card dictionary (optional)
        num_games: Number of games to simulate
        max_turns: Maximum turns per game
        verbose: Print detailed logs

    Returns:
        Dictionary with simulation results including:
        - total_damage: List of average damage per turn
        - total_power: List of average power on board per turn
        - summary: Summary statistics
    """
    # Ensure simulation imports are loaded
    try:
        _ensure_simulation_imports()
    except ImportError as e:
        print(f"ERROR: Cannot run simulation - missing dependencies: {e}")
        return {
            'total_damage': [0] * (max_turns + 1),
            'total_power': [0] * (max_turns + 1),
            'summary': {
                'error': f'Simulation unavailable: {str(e)}',
                'total_damage_10_turns': 0,
                'avg_damage_per_turn': 0,
                'peak_power': 0,
                'commander_avg_cast_turn': None
            }
        }

    # Convert cards to simulation format
    sim_cards = []
    sim_commander = None

    for card in cards:
        try:
            sim_card = convert_card_to_simulation_format(card)
            if card.get('is_commander') or (commander and card.get('name') == commander.get('name')):
                sim_commander = sim_card
                sim_commander.is_commander = True
            else:
                sim_cards.append(sim_card)
        except Exception as e:
            print(f"Warning: Could not convert card {card.get('name', 'Unknown')}: {e}")
            continue

    # If no commander specified, try to find one
    if sim_commander is None and commander:
        sim_commander = convert_card_to_simulation_format(commander)
        sim_commander.is_commander = True

    # If still no commander, create a dummy one
    if sim_commander is None:
        print("Warning: No commander found, creating dummy commander")
        sim_commander = Card(
            name="Dummy Commander",
            type="Creature",
            mana_cost="{2}{G}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            is_commander=True,
            is_legendary=True
        )

    if not sim_cards:
        print("Error: No cards to simulate")
        return {
            'total_damage': [0] * (max_turns + 1),
            'total_power': [0] * (max_turns + 1),
            'summary': {
                'error': 'No cards to simulate'
            }
        }

    print(f"Running {num_games} simulations with {len(sim_cards)} cards...")

    # Run simulations
    try:
        summary_df, commander_cast_dist, avg_creature_power, interaction_summary, statistical_report = run_simulations(
            cards=sim_cards,
            commander_card=sim_commander,
            num_games=num_games,
            max_turns=max_turns,
            verbose=verbose,
            log_dir=None,  # Don't save logs
            num_workers=1,  # Single worker for compatibility
            calculate_statistics=True  # Enable statistical analysis
        )

        # Extract key metrics
        # ARISTOCRATS: Use total damage (combat + drain) instead of just combat
        total_damage = [0] + summary_df['Avg Total Damage'].tolist()
        combat_damage = [0] + summary_df['Avg Combat Damage'].tolist()
        drain_damage = [0] + summary_df['Avg Drain Damage'].tolist()
        total_power = [0] + summary_df['Avg Total Power'].tolist()
        avg_mana = [0] + summary_df['Avg Total Mana'].tolist()
        avg_opponents_alive = [0] + summary_df['Avg Opponents Alive'].tolist()
        avg_opponent_power = [0] + summary_df['Avg Opponent Power'].tolist()
        tokens_created = [0] + summary_df['Avg Tokens Created'].tolist()
        cards_drawn = [0] + summary_df['Avg Cards Drawn'].tolist()
        life_gained = [0] + summary_df['Avg Life Gained'].tolist()
        life_lost = [0] + summary_df['Avg Life Lost'].tolist()

        # Calculate total damage over first 10 turns
        total_damage_10_turns = sum(total_damage[:min(11, len(total_damage))])
        combat_damage_10_turns = sum(combat_damage[:min(11, len(combat_damage))])
        drain_damage_10_turns = sum(drain_damage[:min(11, len(drain_damage))])

        # Get commander cast turn stats
        commander_avg_turn = None
        if not commander_cast_dist.empty:
            weighted_sum = sum(turn * count for turn, count in commander_cast_dist.items())
            total_count = commander_cast_dist.sum()
            if total_count > 0:
                commander_avg_turn = weighted_sum / total_count

        # Print statistical report if available
        if statistical_report and statistical_report.get("formatted_report"):
            print("\n" + "=" * 80)
            print("STATISTICAL VALIDITY ANALYSIS")
            print("=" * 80)
            print(statistical_report["formatted_report"])

        return {
            'total_damage': total_damage,
            'combat_damage': combat_damage,  # NEW
            'drain_damage': drain_damage,  # NEW
            'total_power': total_power,
            'avg_mana': avg_mana,
            'avg_opponents_alive': avg_opponents_alive,
            'avg_opponent_power': avg_opponent_power,
            'tokens_created': tokens_created,  # NEW
            'cards_drawn': cards_drawn,  # NEW
            'life_gained': life_gained,  # NEW
            'life_lost': life_lost,  # NEW
            'summary': {
                'total_damage_10_turns': round(total_damage_10_turns, 2),
                'combat_damage_10_turns': round(combat_damage_10_turns, 2),  # NEW
                'drain_damage_10_turns': round(drain_damage_10_turns, 2),  # NEW
                'avg_damage_per_turn': round(total_damage_10_turns / max_turns, 2),
                'peak_power': round(max(total_power), 2) if total_power else 0,
                'commander_avg_cast_turn': round(commander_avg_turn, 2) if commander_avg_turn else None,
                'num_games_simulated': num_games,
                'total_tokens_created': round(sum(tokens_created), 1),  # NEW
                'total_cards_drawn': round(sum(cards_drawn), 1),  # NEW
                'total_life_gained': round(sum(life_gained), 1),  # NEW
                'total_life_lost': round(sum(life_lost), 1),  # NEW
                **interaction_summary  # Include new interaction metrics
            },
            'summary_df': summary_df,
            'commander_cast_distribution': commander_cast_dist,
            'creature_power': avg_creature_power,
            'interaction_summary': interaction_summary,
            'statistical_report': statistical_report  # NEW: Include statistical analysis
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error running simulation: {e}")
        return {
            'total_damage': [0] * (max_turns + 1),
            'total_power': [0] * (max_turns + 1),
            'summary': {
                'error': str(e)
            }
        }
