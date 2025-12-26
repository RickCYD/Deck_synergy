"""
Helper functions for visualizing game-by-game simulation details.
"""

from dash import html, dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_fastest_slowest_viz(fastest_games, slowest_games):
    """
    Create visualization showing card plays from fastest and slowest games.

    Args:
        fastest_games: List of (win_turn, game_metrics) tuples for fastest games
        slowest_games: List of (win_turn, game_metrics) tuples for slowest games

    Returns:
        Dash HTML component with visualization
    """
    if not fastest_games and not slowest_games:
        return html.Div("No game data available. Run a simulation first.", style={'color': '#7f8c8d', 'padding': '20px'})

    children = []

    # Fastest Games Section
    if fastest_games:
        children.append(html.H5("🏆 Fastest 5 Games", style={'color': '#27ae60', 'marginBottom': '12px'}))
        for idx, (win_turn, metrics) in enumerate(fastest_games, 1):
            game_viz = create_single_game_viz(idx, win_turn, metrics, is_fast=True)
            children.append(game_viz)

    # Slowest Games Section
    if slowest_games:
        children.append(html.Hr(style={'margin': '24px 0'}))
        children.append(html.H5("🐢 Slowest 5 Games", style={'color': '#e67e22', 'marginBottom': '12px'}))
        for idx, (win_turn, metrics) in enumerate(slowest_games, 1):
            game_viz = create_single_game_viz(idx, win_turn, metrics, is_fast=False)
            children.append(game_viz)

    return html.Div(children, style={'backgroundColor': '#fff', 'padding': '16px', 'borderRadius': '6px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'})


def create_single_game_viz(game_num, win_turn, metrics, is_fast=True):
    """
    Create visualization for a single game showing turn-by-turn card plays.

    Args:
        game_num: Game number (1-5)
        win_turn: Turn number when game was won
        metrics: Game metrics dictionary
        is_fast: Whether this is a fast game (for coloring)

    Returns:
        Dash HTML component
    """
    color = '#27ae60' if is_fast else '#e67e22'
    bg_color = '#ecf9f2' if is_fast else '#fef5e7'

    # Extract turn-by-turn data
    played_card_names = metrics.get('played_card_names', [])  # List of lists per turn
    hand_size = metrics.get('hand_size', [])
    mana_available = metrics.get('total_mana', [])
    combat_damage = metrics.get('combat_damage', [])
    drain_damage = metrics.get('drain_damage', [])

    # Create turn-by-turn display
    turn_divs = []

    max_turns = min(win_turn, len(played_card_names) - 1) if played_card_names else 0

    for turn in range(1, max_turns + 1):
        if turn >= len(played_card_names):
            break

        cards_this_turn = played_card_names[turn] if played_card_names[turn] else []
        hand_this_turn = hand_size[turn] if turn < len(hand_size) else 0
        mana_this_turn = mana_available[turn] if turn < len(mana_available) else 0
        combat_this_turn = combat_damage[turn] if turn < len(combat_damage) else 0
        drain_this_turn = drain_damage[turn] if turn < len(drain_damage) else 0
        total_damage = combat_this_turn + drain_this_turn

        # Create card badges
        card_badges = []
        for card_name in cards_this_turn:
            if card_name:
                card_badges.append(
                    html.Span(
                        card_name,
                        style={
                            'backgroundColor': '#3498db',
                            'color': '#fff',
                            'padding': '4px 8px',
                            'borderRadius': '4px',
                            'marginRight': '6px',
                            'marginBottom': '4px',
                            'display': 'inline-block',
                            'fontSize': '11px',
                            'fontWeight': '500'
                        }
                    )
                )

        if not card_badges:
            card_badges = [html.Span("(no cards played)", style={'color': '#95a5a6', 'fontSize': '11px', 'fontStyle': 'italic'})]

        turn_div = html.Div([
            html.Div([
                html.Strong(f"Turn {turn}", style={'color': color, 'marginRight': '12px'}),
                html.Span(f"⚡ {mana_this_turn} mana", style={'marginRight': '12px', 'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Span(f"🎴 {hand_this_turn} cards", style={'marginRight': '12px', 'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Span(f"💥 {total_damage} dmg", style={'fontSize': '12px', 'color': '#e74c3c'}),
            ], style={'marginBottom': '6px'}),
            html.Div(card_badges, style={'display': 'flex', 'flexWrap': 'wrap'})
        ], style={
            'padding': '10px',
            'marginBottom': '8px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '4px',
            'borderLeft': f'3px solid {color}'
        })

        turn_divs.append(turn_div)

    # Game summary header
    result_text = f"Won on turn {win_turn}" if win_turn <= 10 else f"Didn't win (turn {win_turn})"

    game_header = html.Div([
        html.Div([
            html.Strong(f"Game #{game_num}", style={'fontSize': '14px', 'color': color}),
            html.Span(f" — {result_text}", style={'marginLeft': '8px', 'fontSize': '13px', 'color': '#34495e'})
        ]),
    ], style={'marginBottom': '12px', 'paddingBottom': '8px', 'borderBottom': f'2px solid {color}'})

    return html.Div([
        game_header,
        html.Div(turn_divs)
    ], style={
        'marginBottom': '16px',
        'padding': '12px',
        'backgroundColor': bg_color,
        'borderRadius': '6px',
        'border': f'1px solid {color}'
    })
