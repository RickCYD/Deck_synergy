"""
MTG Commander Deck Synergy Visualizer
Main Dash application file
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context, ALL
import dash_cytoscape as cyto
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import custom modules
from src.api.archidekt import fetch_deck_from_archidekt
from src.api.scryfall import fetch_card_details
from src.models.deck import Deck
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.utils.graph_builder import build_graph_elements
from src.utils.card_rankings import (
    calculate_weighted_degree_centrality,
    get_deck_rankings_summary
)
from src.utils.card_roles import (
    ROLE_CATEGORIES,
    assign_roles_to_cards,
    summarize_roles
)

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "MTG Commander Synergy Visualizer"
server = app.server  # Expose Flask server for production (e.g., Gunicorn)

# Load Cytoscape layouts
cyto.load_extra_layouts()

# Get initial deck list
def get_deck_options():
    """Get list of saved decks for dropdown"""
    deck_files = list(Path('data/decks').glob('*.json'))
    # Filter out .gitkeep
    deck_files = [f for f in deck_files if f.name != '.gitkeep']
    return [{'label': f.stem, 'value': str(f)} for f in sorted(deck_files, key=lambda x: x.stat().st_mtime, reverse=True)]

initial_deck_options = get_deck_options()


def get_base_stylesheet() -> List[Dict[str, Any]]:
    """Base Cytoscape stylesheet used across callbacks."""
    return [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'shape': 'rectangle',
                'background-color': 'data(color_code)',
                'background-image': 'data(art_crop_url)',  # Just the artwork
                'background-fit': 'cover',
                'background-clip': 'node',
                'color': '#fff',
                'text-valign': 'bottom',
                'text-halign': 'center',
                'text-background-color': '#000',
                'text-background-opacity': 0.7,
                'text-background-padding': '3px',
                'font-size': '10px',
                'width': '90px',
                'height': '90px',
                'border-width': '4px',
                'border-color': 'data(border_color)',
                'text-outline-width': '1px',
                'text-outline-color': '#000'
            }
        },
        {
            'selector': 'node[is_multicolor]',
            'style': {
                'border-width': '3px',
                'border-color': 'data(border_color)',
                'outline-width': '3px',
                'outline-color': 'data(secondary_border)',
                'outline-opacity': 1
            }
        },
        {
            'selector': 'node[type="commander"]',
            'style': {
                'background-color': 'data(color_code)',
                'background-image': 'data(art_crop_url)',  # Just the artwork
                'background-fit': 'cover',
                'background-clip': 'node',
                'width': '110px',
                'height': '110px',
                'font-size': '12px',
                'font-weight': 'bold',
                'border-width': '5px',
                'border-color': 'data(border_color)'
            }
        },
        {
            'selector': 'node[type="commander"][is_multicolor]',
            'style': {
                'border-width': '4px',
                'outline-width': '4px',
                'outline-color': 'data(secondary_border)'
            }
        },
        {
            'selector': 'edge',
            'style': {
                'width': 'data(weight)',
                'line-color': '#95a5a6',
                'curve-style': 'bezier',
                'opacity': 0.6
            }
        }
    ]


def apply_role_filter_styles(
    stylesheet: List[Dict[str, Any]],
    active_filter: Optional[Dict[str, Any]],
    role_summary: Optional[Dict[str, Any]],
    elements: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Add highlighting rules for the active role filter."""
    if not active_filter or not role_summary or not elements:
        return stylesheet

    category_key = active_filter.get('category')
    role_key = active_filter.get('role')
    if not category_key or not role_key:
        return stylesheet

    category_data = role_summary.get(category_key)
    if not category_data:
        return stylesheet

    role_entry = category_data['roles'].get(role_key)
    if not role_entry:
        return stylesheet

    node_ids = set(role_entry.get('cards') or [])
    if not node_ids:
        return stylesheet

    # Dim everything first
    stylesheet.append({
        'selector': 'node',
        'style': {'opacity': 0.15}
    })

    node_selector = ', '.join([f'node[id="{node_id}"]' for node_id in sorted(node_ids)])
    stylesheet.append({
        'selector': node_selector,
        'style': {'opacity': 1}
    })

    stylesheet.append({
        'selector': 'edge',
        'style': {'opacity': 0.1}
    })

    highlight_edges = [
        f'edge[id="{element["data"]["id"]}"]'
        for element in elements
        if 'source' in element.get('data', {})
        and element['data']['source'] in node_ids
        and element['data']['target'] in node_ids
    ]
    if highlight_edges:
        stylesheet.append({
            'selector': ', '.join(highlight_edges),
            'style': {
                'opacity': 0.65,
                'line-color': '#3498db',
                'width': 'mapData(weight, 0, 10, 2, 8)'
            }
        })

    return stylesheet

# Define the app layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Label("Archidekt Deck URL:", style={'fontWeight': 'bold', 'marginBottom': '6px'}),
            html.Div([
                dcc.Input(
                    id='deck-url-input',
                    type='text',
                    placeholder='https://archidekt.com/decks/...',
                    style={'flex': '1', 'minWidth': '220px', 'padding': '10px'}
                ),
                html.Button(
                    'Load Deck',
                    id='load-deck-button',
                    n_clicks=0,
                    style={
                        'padding': '10px 16px',
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'border': 'none',
                        'fontSize': '15px',
                        'fontWeight': 'bold',
                        'cursor': 'pointer',
                        'borderRadius': '4px'
                    }
                )
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px'}),
            html.Div(id='status-message', style={'marginTop': '6px', 'color': '#7f8c8d'})
        ], style={'flex': '1 1 320px', 'minWidth': '260px'}),

        html.Div([
            html.Label("Select Deck:", style={'fontWeight': 'bold', 'marginBottom': '6px'}),
            dcc.Dropdown(
                id='deck-selector',
                options=initial_deck_options,
                placeholder='Select a loaded deck...',
                style={'width': '100%'}
            )
        ], style={'flex': '1 1 220px', 'minWidth': '220px'}),

        html.Div([
            html.Label("Role Filter:", style={'fontWeight': 'bold', 'marginBottom': '6px'}),
            dcc.Dropdown(
                id='role-filter-dropdown',
                placeholder='Filter by role...',
                clearable=False,
                style={'width': '100%'}
            ),
            html.Button(
                'Clear Role Filter',
                id='clear-role-filter-button',
                n_clicks=0,
                style={
                    'marginTop': '6px',
                    'padding': '8px',
                    'backgroundColor': '#bdc3c7',
                    'color': '#2c3e50',
                    'border': 'none',
                    'cursor': 'pointer',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'borderRadius': '4px',
                    'width': '100%'
                }
            ),
            html.Div(
                id='active-role-filter-display',
                style={'marginTop': '6px', 'color': '#7f8c8d', 'fontStyle': 'italic'}
            )
        ], style={'flex': '1 1 260px', 'minWidth': '240px'}),

        html.Div([
            dcc.Dropdown(
                id='layout-selector',
                options=[
                    {'label': 'Cose (Force-directed)', 'value': 'cose'},
                    {'label': 'Circle', 'value': 'circle'},
                    {'label': 'Concentric', 'value': 'concentric'},
                    {'label': 'Grid', 'value': 'grid'},
                    {'label': 'Breadthfirst', 'value': 'breadthfirst'}
                ],
                value='cose'
            )
        ], style={'display': 'none'})
    ], style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '16px',
        'alignItems': 'flex-end',
        'backgroundColor': '#ffffff',
        'padding': '18px 24px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
        'position': 'sticky',
        'top': 0,
        'zIndex': 100
    }),

    html.Div([
        html.Div([
            html.Div([
                html.H1("MTG Commander Deck Synergy Visualizer",
                        style={'color': '#2c3e50', 'marginBottom': '6px'}),
                html.P("Visualize card synergies in your Commander deck as an interactive graph",
                       style={'color': '#7f8c8d', 'marginBottom': '12px'})
            ], style={'marginBottom': '10px'}),
            html.Button(
                'View Top Cards in Graph',
                id='view-top-cards-button',
                n_clicks=0,
                style={
                    'padding': '8px 12px',
                    'backgroundColor': '#2ecc71',
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'borderRadius': '4px',
                    'alignSelf': 'flex-start',
                    'marginBottom': '12px'
                }
            ),
            html.Div(id='card-rankings-panel', style={'maxHeight': '160px', 'overflowY': 'auto', 'marginBottom': '16px'}),
            cyto.Cytoscape(
                id='card-graph',
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '650px'},
                elements=[],
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'shape': 'rectangle',
                            'background-color': 'data(color_code)',
                            'background-image': 'data(art_crop_url)',
                            'background-fit': 'cover',
                            'background-clip': 'node',
                            'color': '#fff',
                            'text-valign': 'bottom',
                            'text-halign': 'center',
                            'text-background-color': '#000',
                            'text-background-opacity': 0.7,
                            'text-background-padding': '3px',
                            'font-size': '10px',
                            'width': '90px',
                            'height': '90px',
                            'border-width': '4px',
                            'border-color': 'data(border_color)',
                            'border-style': 'solid',
                            'text-outline-width': '1px',
                            'text-outline-color': '#000'
                        }
                    },
                    {
                        'selector': 'node[is_multicolor]',
                        'style': {
                            'border-width': '3px',
                            'border-color': 'data(border_color)',
                            'outline-width': '3px',
                            'outline-color': 'data(secondary_border)',
                            'outline-opacity': 1
                        }
                    },
                    {
                        'selector': 'node[type="commander"]',
                        'style': {
                            'background-color': 'data(color_code)',
                            'background-image': 'data(art_crop_url)',
                            'background-fit': 'cover',
                            'background-clip': 'node',
                            'width': '110px',
                            'height': '110px',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'border-width': '5px',
                            'border-color': 'data(border_color)'
                        }
                    },
                    {
                        'selector': 'node[type="commander"][is_multicolor]',
                        'style': {
                            'border-width': '4px',
                            'outline-width': '4px',
                            'outline-color': 'data(secondary_border)'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'width': 'data(weight)',
                            'line-color': '#95a5a6',
                            'curve-style': 'bezier',
                            'opacity': 0.6
                        }
                    },
                    {
                        'selector': 'node:selected',
                        'style': {
                            'border-width': '4px',
                            'border-color': '#f39c12'
                        }
                    },
                    {
                        'selector': '.highlighted',
                        'style': {
                            'opacity': 1,
                            'z-index': 999
                        }
                    },
                    {
                        'selector': '.dimmed',
                        'style': {
                            'opacity': 0.2
                        }
                    }
                ]
            )
        ], style={
            'flex': '2 1 65%',
            'backgroundColor': '#ffffff',
            'borderRadius': '6px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'padding': '20px',
            'minWidth': '320px'
        }),

        html.Div(
            id='info-panel',
            style={
                'flex': '1 1 30%',
                'minWidth': '260px',
                'backgroundColor': '#ffffff',
                'borderRadius': '6px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'padding': '20px',
                'minHeight': '650px'
            }
        )
    ], style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '20px',
        'padding': '20px'
    }),

    dcc.Store(id='deck-data-store'),
    dcc.Store(id='selected-node-store'),
    dcc.Store(id='current-deck-file-store'),
    dcc.Store(id='role-filter-data'),
    dcc.Store(id='active-role-filter')
], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})


# Callback to load deck from URL
@app.callback(
    [Output('status-message', 'children'),
     Output('deck-selector', 'options'),
     Output('deck-data-store', 'data'),
     Output('deck-selector', 'value')],
    Input('load-deck-button', 'n_clicks'),
    State('deck-url-input', 'value'),
    State('deck-data-store', 'data'),
    prevent_initial_call=True
)
def load_deck(n_clicks, url, current_data):
    """Load deck from Archidekt URL and fetch card details from Scryfall"""
    if not url:
        return html.Div("Please enter a deck URL", style={'color': 'red'}), [], current_data, None

    try:
        # Update status
        status = html.Div("Loading deck...", style={'color': 'blue'})

        # Fetch deck from Archidekt
        deck_info = fetch_deck_from_archidekt(url)

        # Fetch detailed card info from Scryfall
        cards_with_details = fetch_card_details(deck_info['cards'])

        # Annotate cards with functional roles
        assign_roles_to_cards(cards_with_details)

        # Create deck object
        deck = Deck(
            deck_id=deck_info['id'],
            name=deck_info['name'],
            cards=cards_with_details
        )

        # Analyze synergies
        deck.synergies = analyze_deck_synergies(cards_with_details)

        # Save deck to file
        deck_file_path = deck.save()

        # Update deck list
        deck_files = list(Path('data/decks').glob('*.json'))
        deck_options = [{'label': f.stem, 'value': str(f)} for f in deck_files]

        # Store deck data
        stored_data = current_data or {}
        stored_data[deck.name] = deck.to_dict()

        status = html.Div(f"Successfully loaded deck: {deck.name}", style={'color': 'green'})
        # Automatically select the newly loaded deck
        return status, deck_options, stored_data, str(deck_file_path)

    except Exception as e:
        return html.Div(f"Error loading deck: {str(e)}", style={'color': 'red'}), [], current_data, None


# Callback to update graph when deck is selected
@app.callback(
    [Output('card-graph', 'elements'),
     Output('current-deck-file-store', 'data'),
     Output('role-filter-data', 'data')],
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def update_graph(deck_file):
    """Update graph visualization when a deck is selected"""
    if not deck_file:
        return [], None, {}

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        cards = deck_data.get('cards', [])
        if cards:
            assign_roles_to_cards(cards)
        role_summary = summarize_roles(cards)

        # Build graph elements
        elements = build_graph_elements(deck_data)
        return elements, deck_file, role_summary

    except Exception as e:
        print(f"Error updating graph: {e}")
        return [], None, {}


# Callback to update card rankings when deck is selected
@app.callback(
    Output('card-rankings-panel', 'children'),
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def update_card_rankings(deck_file):
    """Calculate and display card rankings when a deck is selected."""
    if not deck_file:
        return []

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        # Get rankings
        rankings_summary = get_deck_rankings_summary(deck_data, top_n=10)

        # Build rankings display
        rankings_items = []
        for card_info in rankings_summary['top_cards']:
            rank_badge_style = {
                'display': 'inline-block',
                'width': '25px',
                'height': '25px',
                'borderRadius': '50%',
                'backgroundColor': card_info['color'],
                'color': 'white',
                'textAlign': 'center',
                'lineHeight': '25px',
                'fontWeight': 'bold',
                'marginRight': '10px',
                'fontSize': '12px'
            }

            card_item_style = {
                'padding': '10px',
                'marginBottom': '8px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '5px',
                'borderLeft': f'4px solid {card_info["color"]}',
                'cursor': 'pointer',
                'transition': 'all 0.2s'
            }

            rankings_items.append(
                html.Div([
                    html.Div([
                        html.Span(str(card_info['rank']), style=rank_badge_style),
                        html.Strong(card_info['name'], style={'fontSize': '14px'})
                    ]),
                    html.Div([
                        html.Span(f"Synergy: {card_info['total_synergy']} | ",
                                 style={'fontSize': '11px', 'color': '#7f8c8d'}),
                        html.Span(f"Connections: {card_info['connections']}",
                                 style={'fontSize': '11px', 'color': '#7f8c8d'})
                    ], style={'marginTop': '5px', 'marginLeft': '35px'})
                ], style=card_item_style, id={'type': 'ranking-card', 'index': card_info['rank']})
            )

        return rankings_items

    except Exception as e:
        print(f"Error calculating rankings: {e}")
        return [html.Div(f"Error: {str(e)}", style={'color': 'red'})]


@app.callback(
    [Output('role-filter-dropdown', 'options'),
     Output('role-filter-dropdown', 'disabled'),
     Output('role-filter-dropdown', 'value'),
     Output('active-role-filter-display', 'children')],
    [Input('role-filter-data', 'data'),
     Input('active-role-filter', 'data')],
    prevent_initial_call=False
)
def update_role_filter_dropdown(role_data, active_filter):
    """Populate the role filter dropdown and show the current selection."""
    if not role_data:
        return [], True, None, "No role filter active."

    options: List[Dict[str, Any]] = []
    has_available = False

    for category_key, category_def in ROLE_CATEGORIES.items():
        category_summary = role_data.get(category_key, {'roles': {}})
        role_entries = category_summary.get('roles', {})

        options.append({
            'label': category_def['label'],
            'value': f'header::{category_key}',
            'disabled': True
        })

        for role_def in category_def['roles']:
            role_key = role_def['key']
            role_label = role_def['label']
            cards = role_entries.get(role_key, {}).get('cards', []) or []
            count = len(cards)
            options.append({
                'label': f"  {role_label} ({count})",
                'value': f"{category_key}::{role_key}",
                'disabled': count == 0
            })
            if count > 0:
                has_available = True

    active_message = "No role filter active."
    if active_filter:
        category_key = active_filter.get('category')
        role_key = active_filter.get('role')
        if category_key and role_key:
            category_def = ROLE_CATEGORIES.get(category_key)
            category_label = category_def['label'] if category_def else category_key.replace('_', ' ').title()
            role_label = role_key.replace('_', ' ').title()
            if category_def:
                for role_def in category_def['roles']:
                    if role_def['key'] == role_key:
                        role_label = role_def['label']
                        break
            count = len(role_data.get(category_key, {}).get('roles', {}).get(role_key, {}).get('cards', [])) if role_data else 0
            active_message = f"Active Filter: {category_label} → {role_label} ({count} cards)"

    return options, not has_available, None, active_message


@app.callback(
    Output('active-role-filter', 'data', allow_duplicate=True),
    [Input('role-filter-dropdown', 'value'),
     Input('clear-role-filter-button', 'n_clicks')],
    State('active-role-filter', 'data'),
    prevent_initial_call=True
)
def set_active_role_filter(dropdown_value, clear_click, current_filter):
    """Update the active role filter when a dropdown value changes or clear is pressed."""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    trigger = ctx.triggered[0]['prop_id']
    if trigger == 'clear-role-filter-button.n_clicks':
        return None

    if dropdown_value:
        try:
            category_key, role_key = dropdown_value.split('::', 1)
        except ValueError:
            return dash.no_update

        if category_key == 'header':
            return dash.no_update

        if current_filter and current_filter.get('category') == category_key and current_filter.get('role') == role_key:
            return dash.no_update

        return {'category': category_key, 'role': role_key}

    return dash.no_update



@app.callback(
    Output('active-role-filter', 'data', allow_duplicate=True),
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def reset_role_filter_on_deck_change(_):
    """Clear the role filter whenever a new deck is selected."""
    return None


# Callback to update graph layout
@app.callback(
    Output('card-graph', 'layout'),
    Input('layout-selector', 'value')
)
def update_layout(layout_name):
    """Update graph layout"""
    return {'name': layout_name, 'animate': True}


# Callback to reorganize graph to highlight top cards
@app.callback(
    [Output('card-graph', 'stylesheet', allow_duplicate=True),
     Output('card-graph', 'layout', allow_duplicate=True),
     Output('card-graph', 'elements', allow_duplicate=True)],
    Input('view-top-cards-button', 'n_clicks'),
    [State('current-deck-file-store', 'data'),
     State('card-graph', 'elements')],
    prevent_initial_call=True
)
def view_top_cards_in_graph(n_clicks, deck_file, elements):
    """Reorganize graph to highlight and center top 10 cards"""
    if not deck_file or not elements:
        return dash.no_update, dash.no_update, dash.no_update

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        # Get top 10 cards
        rankings_summary = get_deck_rankings_summary(deck_data, top_n=10)
        top_card_names = [card['name'] for card in rankings_summary['top_cards']]

        # Create stylesheet with highlighting - keep card art visible
        base_stylesheet = [
            # Regular nodes (dimmed) - maintain square shape and art
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'shape': 'rectangle',
                    'background-color': 'data(color_code)',
                    'background-image': 'data(art_crop_url)',
                    'background-fit': 'cover',
                    'background-clip': 'node',
                    'color': '#fff',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-background-color': '#000',
                    'text-background-opacity': 0.7,
                    'text-background-padding': '3px',
                    'font-size': '8px',
                    'width': '60px',
                    'height': '60px',
                    'border-width': '2px',
                    'border-color': '#7f8c8d',
                    'text-outline-width': '1px',
                    'text-outline-color': '#000',
                    'opacity': 0.3
                }
            },
            # Commander node style (dimmed)
            {
                'selector': 'node[type="commander"]',
                'style': {
                    'background-image': 'data(art_crop_url)',
                    'background-fit': 'cover',
                    'width': '70px',
                    'height': '70px',
                    'font-size': '10px',
                    'opacity': 0.3
                }
            },
            # Regular edges (dimmed)
            {
                'selector': 'edge',
                'style': {
                    'width': 1,
                    'line-color': '#bdc3c7',
                    'curve-style': 'bezier',
                    'opacity': 0.1
                }
            }
        ]

        # Highlight top 10 cards - keep art, just add colored border
        for i, card_name in enumerate(top_card_names, 1):
            # Color gradient from red (rank 1) to orange (rank 10)
            border_colors = ['#e74c3c', '#e67e22', '#f39c12', '#f1c40f', '#2ecc71',
                           '#1abc9c', '#3498db', '#9b59b6', '#34495e', '#95a5a6']
            border_color = border_colors[min(i-1, 9)]

            # Size increases with rank (rank 1 is largest)
            size = max(120 - (i * 6), 80)

            base_stylesheet.append({
                'selector': f'node[id="{card_name}"]',
                'style': {
                    'background-image': 'data(art_crop_url)',  # Keep card art
                    'background-fit': 'cover',
                    'width': f'{size}px',
                    'height': f'{size}px',
                    'font-size': '12px',
                    'font-weight': 'bold',
                    'opacity': 1,
                    'border-width': '6px',
                    'border-color': border_color,  # Colored border shows ranking
                    'z-index': 1000 - i
                }
            })

        # Highlight edges between top cards
        for element in elements:
            if 'source' in element.get('data', {}):
                source = element['data']['source']
                target = element['data']['target']

                if source in top_card_names and target in top_card_names:
                    edge_id = element['data']['id']
                    base_stylesheet.append({
                        'selector': f'edge[id="{edge_id}"]',
                        'style': {
                            'width': 'mapData(weight, 0, 10, 2, 8)',
                            'line-color': '#2ecc71',
                            'opacity': 0.8,
                            'z-index': 999
                        }
                    })

        # Use cose layout instead of concentric (which has JS function issues in Dash)
        # The top cards will still be visually prominent due to size/color
        layout = {
            'name': 'cose',
            'animate': True,
            'animationDuration': 1000,
            'nodeRepulsion': 8000,
            'idealEdgeLength': 100,
            'edgeElasticity': 100
        }

        return base_stylesheet, layout, dash.no_update

    except Exception as e:
        print(f"Error highlighting top cards: {e}")
        return dash.no_update, dash.no_update, dash.no_update



# Callback for node/edge selection and highlighting
@app.callback(
    [Output('card-graph', 'stylesheet'),
     Output('info-panel', 'children')],
    [Input('card-graph', 'tapNodeData'),
     Input('card-graph', 'tapEdgeData'),
     Input('active-role-filter', 'data')],
    [State('card-graph', 'elements'),
     State('role-filter-data', 'data')],
    prevent_initial_call=True
)
def handle_selection(node_data, edge_data, active_filter, elements, role_summary):
    """Handle node/edge selection and update role-based highlighting."""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_prop = ctx.triggered[0]['prop_id']

    if elements is None:
        if triggered_prop == 'active-role-filter.data':
            stylesheet = apply_role_filter_styles(get_base_stylesheet(), active_filter, role_summary, [])
            return stylesheet, dash.no_update
        return dash.no_update, dash.no_update

    base_stylesheet = get_base_stylesheet()
    base_stylesheet = apply_role_filter_styles(base_stylesheet, active_filter, role_summary, elements)

    if triggered_prop == 'active-role-filter.data':
        return base_stylesheet, dash.no_update

    stylesheet = list(base_stylesheet)

    if node_data:
        node_id = node_data['id']
        print(f"Node clicked: {node_id}")

        connected_edges = [
            element for element in elements
            if 'source' in element.get('data', {})
            and (element['data']['source'] == node_id or element['data']['target'] == node_id)
        ]
        connected_node_ids = {
            edge['data']['source'] for edge in connected_edges
        }.union({
            edge['data']['target'] for edge in connected_edges
        })

        print(f"Connected edges: {len(connected_edges)}")
        print(f"Connected nodes: {connected_node_ids}")

        stylesheet.extend([
            {'selector': 'node', 'style': {'opacity': 0.2}},
            {'selector': 'edge', 'style': {'opacity': 0.1}}
        ])

        stylesheet.append({
            'selector': f'node[id="{node_id}"]',
            'style': {
                'border-width': '4px',
                'border-color': '#f39c12',
                'opacity': 1
            }
        })

        connected_others = [nid for nid in connected_node_ids if nid != node_id]
        if connected_others:
            stylesheet.append({
                'selector': ', '.join(f'node[id="{nid}"]' for nid in connected_others),
                'style': {'opacity': 1}
            })

        if connected_edges:
            stylesheet.append({
                'selector': ', '.join(f'edge[id="{edge["data"]["id"]}"]' for edge in connected_edges),
                'style': {'opacity': 1, 'line-color': '#2ecc71', 'width': 'mapData(weight, 0, 10, 2, 8)'}
            })

        synergy_items = []
        for edge in connected_edges:
            edge_data = edge['data']
            source_label = edge_data.get('source_label', 'Unknown')
            target_label = edge_data.get('target_label', 'Unknown')
            weight = edge_data.get('weight', 0)
            synergies = edge_data.get('synergies', {})

            other_card = target_label if source_label == node_id else source_label

            synergy_details = []
            for category, synergy_list in synergies.items():
                if not synergy_list:
                    continue
                synergy_details.append(
                    html.Div([
                        html.Strong(category.replace('_', ' ').title() + ':', style={'color': '#3498db'}),
                        html.Ul([
                            html.Li([
                                html.Strong(f"{syn['name']}: "),
                                f"{syn.get('description', 'N/A')} ",
                                html.Span(f"(+{syn.get('value', 0)})", style={'color': '#27ae60', 'fontWeight': 'bold'})
                            ]) for syn in synergy_list
                        ], style={'marginLeft': '10px', 'marginTop': '5px'})
                    ], style={'marginBottom': '10px'})
                )

            synergy_items.append(
                html.Details([
                    html.Summary([
                        html.Strong(f"↔ {other_card}"),
                        html.Span(f" (Strength: {weight:.2f})", style={'color': '#7f8c8d'})
                    ], style={
                        'cursor': 'pointer',
                        'padding': '8px',
                        'backgroundColor': '#ecf0f1',
                        'borderRadius': '4px',
                        'marginBottom': '5px'
                    }),
                    html.Div(
                        synergy_details if synergy_details else [
                            html.P("No detailed synergies available", style={'fontStyle': 'italic', 'color': '#95a5a6'})
                        ],
                        style={
                            'padding': '10px',
                            'backgroundColor': '#f8f9fa',
                            'borderLeft': '3px solid #3498db',
                            'marginBottom': '10px'
                        }
                    )
                ], style={'marginBottom': '10px'})
            )

        roles_list_items = []
        card_roles = node_data.get('roles') or {}
        for category_key, role_keys in card_roles.items():
            category_def = ROLE_CATEGORIES.get(category_key, {})
            category_label = category_def.get('label', category_key.replace('_', ' ').title())
            role_labels = []
            for role_key in role_keys:
                role_label = role_key.replace('_', ' ').title()
                for role_def in category_def.get('roles', []):
                    if role_def['key'] == role_key:
                        role_label = role_def['label']
                        break
                role_labels.append(role_label)
            if role_labels:
                roles_list_items.append(html.Li([
                    html.Strong(f"{category_label}: "),
                    ', '.join(role_labels)
                ]))

        info_children = [
            html.H3(node_data.get('label', 'Unknown Card'), style={'color': '#2c3e50'}),
            html.Hr(),
            html.Div([
                html.P([html.Strong("Type: "), node_data.get('card_type', 'N/A')]),
                html.P([html.Strong("Mana Cost: "), node_data.get('mana_cost', 'N/A')]),
                html.P([html.Strong("Colors: "), ', '.join(node_data.get('colors', []))]),
                html.P([html.Strong("Oracle Text: ")]),
                html.P(
                    node_data.get('oracle_text', 'N/A'),
                    style={'fontStyle': 'italic', 'padding': '10px', 'backgroundColor': '#ecf0f1'}
                ),
            ], style={'marginBottom': '10px'})
        ]

        if roles_list_items:
            info_children.extend([
                html.H4("Identified Roles", style={'marginTop': '10px'}),
                html.Ul(roles_list_items, style={'marginLeft': '20px'})
            ])

        info_children.extend([
            html.Hr(),
            html.H4(f"Synergies ({len(connected_edges)} connections):", style={'marginTop': '20px'}),
            html.Div(
                synergy_items if synergy_items else [
                    html.P("No synergies found", style={'fontStyle': 'italic', 'color': '#95a5a6'})
                ]
            )
        ])

        info_panel = html.Div(info_children)
        return stylesheet, info_panel

    if edge_data:
        edge_id = edge_data['id']
        stylesheet.extend([
            {
                'selector': f'edge[id="{edge_id}"]',
                'style': {
                    'line-color': '#f39c12',
                    'width': 'mapData(weight, 0, 10, 3, 10)',
                    'opacity': 1
                }
            },
            {
                'selector': f'node[id="{edge_data["source"]}"], node[id="{edge_data["target"]}"]',
                'style': {
                    'border-width': '4px',
                    'border-color': '#f39c12',
                    'opacity': 1
                }
            },
            {
                'selector': f'node:not([id="{edge_data["source"]}"]):not([id="{edge_data["target"]}"])',
                'style': {'opacity': 0.2}
            },
            {
                'selector': f'edge:not([id="{edge_id}"])',
                'style': {'opacity': 0.1}
            }
        ])

        synergies = edge_data.get('synergies', {})
        info_panel = html.Div([
            html.H3(
                f"Synergy: {edge_data.get('source_label', 'Unknown')} ↔ {edge_data.get('target_label', 'Unknown')}",
                style={'color': '#2c3e50'}
            ),
            html.Hr(),
            html.P([html.Strong("Total Synergy Strength: "), f"{edge_data.get('weight', 0):.2f}"]),
            html.Hr(),
            html.H4("Synergy Categories:", style={'marginTop': '20px'}),
            html.Div([
                html.Div([
                    html.H5(category.replace('_', ' ').title(), style={'color': '#3498db'}),
                    html.Ul([
                        html.Li([
                            html.Strong(f"{syn['name']}: "),
                            f"{syn.get('description', 'N/A')} (Value: {syn.get('value', 0)})"
                        ]) for syn in synergy_list
                    ])
                ], style={'marginBottom': '15px'})
                for category, synergy_list in synergies.items() if synergy_list
            ])
        ])

        return stylesheet, info_panel

    return base_stylesheet, html.Div("Click on a card or synergy edge to see details")


if __name__ == '__main__':
    # Ensure data directory exists
    Path('data/decks').mkdir(parents=True, exist_ok=True)

    # Run the app
    app.run_server(debug=True, host='0.0.0.0', port=8050)
