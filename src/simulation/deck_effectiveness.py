"""
Deck Effectiveness Module for Dashboard Integration

This module provides dashboard-ready components for displaying
deck effectiveness metrics from goldfish simulation.

Usage in app.py:
    from src.simulation.deck_effectiveness import (
        create_effectiveness_section,
        run_effectiveness_analysis,
        get_effectiveness_figures,
    )
"""

from __future__ import annotations

import sys
import os
from typing import Any, Dict, List, Optional, Tuple

# Add Simulation directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Simulation'))

try:
    from simulation_integration import (
        run_enhanced_simulation,
        analyze_deck_mechanics,
        DeckEffectivenessScore,
        get_win_probability_chart_data,
        get_damage_progression_chart_data,
        get_effectiveness_gauge_data,
    )
    from win_metrics import WinMetrics, format_win_metrics_report, get_dashboard_metrics
    SIMULATION_AVAILABLE = True
except ImportError as e:
    SIMULATION_AVAILABLE = False
    print(f"Warning: Simulation modules not available: {e}")

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def run_effectiveness_analysis(
    deck_cards: List[Dict],
    commander_card: Dict,
    num_simulations: int = 100,
    max_turns: int = 10
) -> Dict[str, Any]:
    """
    Run effectiveness analysis on a deck.

    Args:
        deck_cards: List of card dicts from deck
        commander_card: Commander card dict
        num_simulations: Number of games to simulate
        max_turns: Max turns per game

    Returns:
        Dict with effectiveness metrics and dashboard data
    """
    if not SIMULATION_AVAILABLE:
        return {
            'error': 'Simulation modules not available',
            'effectiveness_score': 0,
            'win_metrics': None,
        }

    try:
        # Convert deck dicts to Card objects
        from simulate_game import Card

        def _safe_power_toughness(value) -> int:
            """Convert power/toughness string to int, handling special values."""
            if value is None:
                return 0
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                # Handle numeric strings
                if value.isdigit():
                    return int(value)
                # Handle negative numbers like "-1"
                if value.lstrip('-').isdigit():
                    return int(value)
                # Handle special values: *, X, *, 1+*, etc. -> treat as 0
                # These are variable and can't be known at simulation time
                return 0
            return 0

        def dict_to_card(d: Dict, is_commander: bool = False) -> Card:
            """Convert card dict to Card object."""
            return Card(
                name=d.get('name', 'Unknown'),
                type=d.get('type_line', d.get('type', 'Unknown')),
                mana_cost=d.get('mana_cost', ''),
                power=_safe_power_toughness(d.get('power')),
                toughness=_safe_power_toughness(d.get('toughness')),
                produces_colors=d.get('produces_colors', []),
                mana_production=d.get('mana_production', 0),
                etb_tapped=d.get('etb_tapped', False),
                etb_tapped_conditions=d.get('etb_tapped_conditions', {}),
                has_haste='Haste' in d.get('keywords', []) or 'haste' in d.get('oracle_text', '').lower(),
                has_flash='Flash' in d.get('keywords', []) or 'flash' in d.get('oracle_text', '').lower(),
                has_flying='Flying' in d.get('keywords', []),
                has_trample='Trample' in d.get('keywords', []),
                has_lifelink='Lifelink' in d.get('keywords', []),
                oracle_text=d.get('oracle_text', ''),
                is_commander=is_commander,
                draw_cards=d.get('draw_cards', 0),
                deals_damage=d.get('deals_damage', 0),
            )

        cards = [dict_to_card(c) for c in deck_cards]
        commander = dict_to_card(commander_card, is_commander=True)

        # Run simulation
        results = run_enhanced_simulation(
            cards,
            commander,
            num_simulations=num_simulations,
            max_turns=max_turns,
            verbose=False
        )

        return results

    except Exception as e:
        return {
            'error': str(e),
            'effectiveness_score': 0,
            'win_metrics': None,
        }


def get_effectiveness_figures(results: Dict[str, Any]) -> Dict[str, go.Figure]:
    """
    Create Plotly figures for effectiveness visualization.

    Args:
        results: Results from run_effectiveness_analysis

    Returns:
        Dict with figure names and Plotly Figure objects
    """
    figures = {}

    if 'error' in results:
        # Return empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {results['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return {'error': fig}

    # Get metrics
    win_metrics = results.get('win_metrics')
    effectiveness = results.get('effectiveness')
    dashboard_data = results.get('dashboard_data', {})

    # 1. Win Probability Chart
    win_fig = go.Figure()

    turns = [6, 8, 10]
    probs = [
        dashboard_data.get('win_probability_turn_6', 0),
        dashboard_data.get('win_probability_turn_8', 0),
        dashboard_data.get('win_probability_turn_10', 0),
    ]

    # Get confidence intervals
    ci_6 = dashboard_data.get('win_ci_turn_6', {'lower': 0, 'upper': 0})
    ci_8 = dashboard_data.get('win_ci_turn_8', {'lower': 0, 'upper': 0})
    ci_10 = dashboard_data.get('win_ci_turn_10', {'lower': 0, 'upper': 0})

    error_plus = [
        ci_6.get('upper', 0) - probs[0],
        ci_8.get('upper', 0) - probs[1],
        ci_10.get('upper', 0) - probs[2],
    ]
    error_minus = [
        probs[0] - ci_6.get('lower', 0),
        probs[1] - ci_8.get('lower', 0),
        probs[2] - ci_10.get('lower', 0),
    ]

    win_fig.add_trace(go.Bar(
        x=[f'Turn {t}' for t in turns],
        y=[p * 100 for p in probs],
        error_y=dict(
            type='data',
            symmetric=False,
            array=[e * 100 for e in error_plus],
            arrayminus=[e * 100 for e in error_minus],
        ),
        marker_color=['#3498db', '#2ecc71', '#27ae60'],
        name='Win Probability'
    ))

    win_fig.update_layout(
        title='Cumulative Win Probability by Turn (95% CI)',
        xaxis_title='Turn',
        yaxis_title='Probability of Winning By This Turn (%)',
        yaxis=dict(range=[0, 100]),
        showlegend=False,
        template='plotly_white'
    )

    figures['win_probability'] = win_fig

    # 2. Damage Progression Chart
    damage_fig = go.Figure()

    damage_data = dashboard_data.get('damage_by_turn', [])
    if damage_data:
        x = list(range(1, len(damage_data) + 1))

        damage_fig.add_trace(go.Scatter(
            x=x,
            y=damage_data,
            mode='lines+markers',
            name='Cumulative Damage',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8)
        ))

        # Add win threshold line
        damage_fig.add_hline(
            y=120,
            line_dash="dash",
            line_color="green",
            annotation_text="Win Threshold (120 damage)"
        )

    damage_fig.update_layout(
        title='Cumulative Damage Progression',
        xaxis_title='Turn',
        yaxis_title='Total Damage',
        template='plotly_white'
    )

    figures['damage_progression'] = damage_fig

    # 3. Effectiveness Gauge
    if effectiveness:
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=effectiveness.overall_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Deck Effectiveness Score"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': _get_score_color(effectiveness.overall_score)},
                'steps': [
                    {'range': [0, 40], 'color': '#ffcccc'},
                    {'range': [40, 70], 'color': '#ffffcc'},
                    {'range': [70, 100], 'color': '#ccffcc'},
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))

        gauge_fig.update_layout(template='plotly_white')
        figures['effectiveness_gauge'] = gauge_fig

    # 4. Component Scores Radar Chart
    if effectiveness:
        radar_fig = go.Figure()

        categories = ['Speed', 'Consistency', 'Power', 'Synergy']
        values = [
            effectiveness.speed_score,
            effectiveness.consistency_score,
            effectiveness.power_score,
            effectiveness.synergy_score,
        ]
        # Close the radar
        values.append(values[0])
        categories.append(categories[0])

        radar_fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Score Components',
            line_color='#3498db'
        ))

        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title='Effectiveness Components',
            template='plotly_white'
        )

        figures['component_radar'] = radar_fig

    # 5. Win Type Breakdown
    win_breakdown = dashboard_data.get('win_breakdown', {})
    if win_breakdown:
        labels = list(win_breakdown.keys())
        values = list(win_breakdown.values())

        # Only show if there are wins
        if sum(values) > 0:
            pie_fig = go.Figure(go.Pie(
                labels=[l.capitalize() for l in labels],
                values=values,
                hole=0.4,
                marker_colors=['#3498db', '#e74c3c', '#f39c12', '#9b59b6']
            ))

            pie_fig.update_layout(
                title='Win Condition Breakdown',
                template='plotly_white'
            )

            figures['win_breakdown'] = pie_fig

    # 6. Card Draw Over Time (NEW)
    cards_drawn = dashboard_data.get('avg_cards_drawn_per_turn', [])
    if cards_drawn:
        x = list(range(1, len(cards_drawn) + 1))

        card_draw_fig = go.Figure()
        card_draw_fig.add_trace(go.Scatter(
            x=x,
            y=cards_drawn,
            mode='lines+markers',
            name='Cards Drawn',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))

        card_draw_fig.update_layout(
            title='Average Cards Drawn Per Turn',
            xaxis_title='Turn',
            yaxis_title='Cards Drawn',
            template='plotly_white'
        )

        figures['card_draw'] = card_draw_fig

    # 7. Hand Size Over Time (NEW)
    hand_size = dashboard_data.get('avg_hand_size_per_turn', [])
    if hand_size:
        x = list(range(1, len(hand_size) + 1))

        hand_size_fig = go.Figure()
        hand_size_fig.add_trace(go.Scatter(
            x=x,
            y=hand_size,
            mode='lines+markers',
            name='Hand Size',
            line=dict(color='#2ecc71', width=2),
            marker=dict(size=6),
            fill='tozeroy'
        ))

        hand_size_fig.update_layout(
            title='Average Hand Size Per Turn',
            xaxis_title='Turn',
            yaxis_title='Cards in Hand',
            template='plotly_white'
        )

        figures['hand_size'] = hand_size_fig

    # 8. Castable vs Uncastable Cards (NEW)
    castable = dashboard_data.get('avg_castable_non_lands_per_turn', [])
    uncastable = dashboard_data.get('avg_uncastable_non_lands_per_turn', [])
    if castable and uncastable:
        x = list(range(1, len(castable) + 1))

        playability_fig = go.Figure()
        playability_fig.add_trace(go.Scatter(
            x=x,
            y=castable,
            mode='lines+markers',
            name='Castable',
            line=dict(color='#27ae60', width=2),
            marker=dict(size=6),
            stackgroup='one'
        ))
        playability_fig.add_trace(go.Scatter(
            x=x,
            y=uncastable,
            mode='lines+markers',
            name='Uncastable (Stuck)',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6),
            stackgroup='one'
        ))

        playability_fig.update_layout(
            title='Castable vs Uncastable Non-Land Cards',
            xaxis_title='Turn',
            yaxis_title='Number of Cards',
            template='plotly_white',
            hovermode='x unified'
        )

        figures['card_playability'] = playability_fig

    # 9. Castable Percentage Over Time (NEW)
    castable_pct = dashboard_data.get('avg_castable_percentage_per_turn', [])
    if castable_pct:
        x = list(range(1, len(castable_pct) + 1))

        castable_pct_fig = go.Figure()
        castable_pct_fig.add_trace(go.Scatter(
            x=x,
            y=castable_pct,
            mode='lines+markers',
            name='Castable %',
            line=dict(color='#9b59b6', width=3),
            marker=dict(size=8),
            fill='tozeroy'
        ))

        # Add reference lines
        castable_pct_fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="green",
            annotation_text="100% (Ideal)",
            annotation_position="right"
        )
        castable_pct_fig.add_hline(
            y=50,
            line_dash="dot",
            line_color="orange",
            annotation_text="50% (Problematic)",
            annotation_position="right"
        )

        castable_pct_fig.update_layout(
            title='Castable Card Percentage Over Time',
            xaxis_title='Turn',
            yaxis_title='Castable %',
            yaxis=dict(range=[0, 105]),
            template='plotly_white'
        )

        figures['castable_percentage'] = castable_pct_fig

    return figures


def _get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= 70:
        return '#28a745'  # Green
    elif score >= 40:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red


def create_effectiveness_summary_html(results: Dict[str, Any]) -> str:
    """
    Create HTML summary of effectiveness results.

    Args:
        results: Results from run_effectiveness_analysis

    Returns:
        HTML string for display
    """
    if 'error' in results:
        return f'<div style="color: red;">Error: {results["error"]}</div>'

    effectiveness = results.get('effectiveness')
    dashboard_data = results.get('dashboard_data', {})

    if not effectiveness:
        return '<div>No effectiveness data available</div>'

    avg_turn = effectiveness.avg_win_turn
    avg_turn_str = f'{avg_turn:.1f}' if avg_turn != float('inf') else 'N/A'

    html = f'''
    <div style="font-family: Arial, sans-serif; padding: 10px;">
        <h3 style="color: #2c3e50; margin-bottom: 10px;">Deck Effectiveness</h3>

        <div style="display: flex; gap: 20px; margin-bottom: 15px;">
            <div style="text-align: center; padding: 10px; background: {_get_score_color(effectiveness.overall_score)}20; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: {_get_score_color(effectiveness.overall_score)};">
                    {effectiveness.overall_score:.0f}
                </div>
                <div style="font-size: 12px; color: #7f8c8d;">Overall Score</div>
            </div>

            <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">
                    {avg_turn_str}
                </div>
                <div style="font-size: 12px; color: #7f8c8d;">Avg Win Turn</div>
            </div>

            <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">
                    {effectiveness.win_rate * 100:.0f}%
                </div>
                <div style="font-size: 12px; color: #7f8c8d;">Win Rate</div>
            </div>
        </div>

        <div style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 14px;">Cumulative Win Probability (95% CI)</h4>
            <div style="font-size: 11px; color: #6c757d; margin-bottom: 6px; font-style: italic;">
                Probability of winning by or before the specified turn
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr style="background: #f8f9fa;">
                    <td style="padding: 6px; border: 1px solid #dee2e6;">By Turn 6</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('win_probability_turn_6', 0) * 100:.1f}%
                    </td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #dee2e6;">By Turn 8</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('win_probability_turn_8', 0) * 100:.1f}%
                    </td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 6px; border: 1px solid #dee2e6;">By Turn 10</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('win_probability_turn_10', 0) * 100:.1f}%
                    </td>
                </tr>
            </table>
        </div>

        <div>
            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 14px;">Component Scores</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
                <div style="padding: 6px; background: #e8f4fd; border-radius: 4px;">
                    Speed: <strong>{effectiveness.speed_score:.0f}</strong>
                </div>
                <div style="padding: 6px; background: #e8f4fd; border-radius: 4px;">
                    Consistency: <strong>{effectiveness.consistency_score:.0f}</strong>
                </div>
                <div style="padding: 6px; background: #e8f4fd; border-radius: 4px;">
                    Power: <strong>{effectiveness.power_score:.0f}</strong>
                </div>
                <div style="padding: 6px; background: #e8f4fd; border-radius: 4px;">
                    Synergy: <strong>{effectiveness.synergy_score:.0f}</strong>
                </div>
            </div>
        </div>

        <div style="margin-top: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 14px;">Card Playability (Turn 6)</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr style="background: #f8f9fa;">
                    <td style="padding: 6px; border: 1px solid #dee2e6;">Avg Cards Drawn</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('avg_cards_drawn_per_turn', [0]*6)[5]:.1f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #dee2e6;">Avg Hand Size</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('avg_hand_size_per_turn', [0]*6)[5]:.1f}
                    </td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 6px; border: 1px solid #dee2e6;">Castable Cards</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right;">
                        {dashboard_data.get('avg_castable_non_lands_per_turn', [0]*6)[5]:.1f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #dee2e6;">Uncastable (Stuck)</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right; color: #e74c3c;">
                        {dashboard_data.get('avg_uncastable_non_lands_per_turn', [0]*6)[5]:.1f}
                    </td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 6px; border: 1px solid #dee2e6;">Castable %</td>
                    <td style="padding: 6px; border: 1px solid #dee2e6; text-align: right; font-weight: bold; color: {'#27ae60' if dashboard_data.get('avg_castable_percentage_per_turn', [0]*6)[5] >= 75 else '#e67e22' if dashboard_data.get('avg_castable_percentage_per_turn', [0]*6)[5] >= 50 else '#e74c3c'};">
                        {dashboard_data.get('avg_castable_percentage_per_turn', [0]*6)[5]:.1f}%
                    </td>
                </tr>
            </table>
        </div>
    </div>
    '''

    return html


# Convenience function for quick analysis
def analyze_deck_effectiveness(deck_file: str, num_simulations: int = 100) -> str:
    """
    Analyze deck effectiveness from a deck file.

    Args:
        deck_file: Path to deck JSON file
        num_simulations: Number of simulations to run

    Returns:
        Formatted report string
    """
    import json

    try:
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)
    except Exception as e:
        return f"Error loading deck: {e}"

    cards = deck_data.get('cards', [])
    commander = deck_data.get('commander', deck_data.get('commanders', [{}])[0])

    results = run_effectiveness_analysis(
        cards,
        commander,
        num_simulations=num_simulations
    )

    if 'error' in results:
        return f"Analysis error: {results['error']}"

    return results.get('report', 'No report available')
