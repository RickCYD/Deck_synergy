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
from src.api import recommendations
from src.models.deck import Deck
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.synergy_engine import embedding_analyzer
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
from src.simulation.mana_simulator import ManaSimulator, SimulationParams
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "MTG Commander Synergy Visualizer"
server = app.server  # Expose Flask server for production (e.g., Gunicorn)

# Load Cytoscape layouts
cyto.load_extra_layouts()

# Load recommendation engine at startup
print("Loading recommendation engine...")
recommendations.load_recommendation_engine()

# Load embedding analyzer at startup (optional - will show warning if embeddings not available)
print("Loading embedding analyzer...")
embedding_analyzer.load_embedding_analyzer()

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
                # Don't set background-image in base style - causes issues with empty strings
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
            'selector': 'node[art_crop_url]',  # Only apply image if URL exists
            'style': {
                'background-image': 'data(art_crop_url)'
            }
        },
        {
            'selector': 'node[is_multicolor]',
            'style': {
                'border-width': '3px',
                'border-color': 'data(border_color)'
            }
        },
        {
            'selector': 'node[type="commander"]',
            'style': {
                'background-color': 'data(color_code)',
                # Background image handled by node[art_crop_url] selector above
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
                'border-width': '4px'
            }
        },
        # Base edge style
        {
            'selector': 'edge',
            'style': {
                'width': 2,
                'line-color': '#95a5a6',
                'curve-style': 'bezier',
                'opacity': 0.7,
                'label': 'data(weight)',
                'font-size': '9px',
                'color': '#2c3e50',
                'text-background-color': '#ffffff',
                'text-background-opacity': 0.85,
                'text-background-padding': '3px',
                'text-background-shape': 'roundrectangle',
                'text-border-color': '#bdc3c7',
                'text-border-width': 0.5,
                'text-border-opacity': 0.8
            }
        },
        # Weight-based colors - gray to red gradient
        {
            'selector': 'edge[weight < 3]',
            'style': {
                'line-color': '#95a5a6',  # Gray
                'width': 1.5
            }
        },
        {
            'selector': 'edge[weight >= 3][weight < 5]',
            'style': {
                'line-color': '#b3a59c',  # Light brown-gray
                'width': 2
            }
        },
        {
            'selector': 'edge[weight >= 5][weight < 7]',
            'style': {
                'line-color': '#d4a574',  # Tan/beige
                'width': 2.5
            }
        },
        {
            'selector': 'edge[weight >= 7][weight < 9]',
            'style': {
                'line-color': '#e67e22',  # Orange
                'width': 3
            }
        },
        {
            'selector': 'edge[weight >= 9][weight < 11]',
            'style': {
                'line-color': '#e74c3c',  # Red-orange
                'width': 4
            }
        },
        {
            'selector': 'edge[weight >= 11]',
            'style': {
                'line-color': '#c0392b',  # Dark red
                'width': 5
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
                'width': 3
            }
        })

    return stylesheet

# Define the app layout
app.layout = html.Div([
    # Title Header - At the very top
    html.Div([
        html.Span(
            "MTG Commander Deck Synergy Visualizer",
            style={'fontWeight': '600', 'fontSize': '20px', 'color': '#2c3e50'}
        ),
        html.Span(
            " – Visualize card synergies in your Commander deck",
            style={'marginLeft': '8px', 'fontSize': '14px', 'color': '#7f8c8d'}
        )
    ], style={
        'padding': '16px 24px',
        'backgroundColor': '#ecf0f1',
        'borderBottom': '2px solid #bdc3c7'
    }),

    # Control Bar - URL, Deck Selector, and Role Filter in one row
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
            html.Div([
                dcc.Dropdown(
                    id='role-filter-dropdown',
                    placeholder='Filter by role...',
                    clearable=False,
                    style={'flex': '1', 'minWidth': '180px'}
                ),
                html.Button(
                    'Clear',
                    id='clear-role-filter-button',
                    n_clicks=0,
                    style={
                        'padding': '10px 16px',
                        'backgroundColor': '#e74c3c',
                        'color': 'white',
                        'border': 'none',
                        'cursor': 'pointer',
                        'fontSize': '14px',
                        'fontWeight': 'bold',
                        'borderRadius': '4px',
                        'marginLeft': '8px'
                    }
                )
            ], style={'display': 'flex', 'gap': '8px', 'alignItems': 'center'}),
            html.Div(
                id='active-role-filter-display',
                style={'marginTop': '6px', 'color': '#7f8c8d', 'fontStyle': 'italic', 'fontSize': '12px'}
            )
        ], style={'flex': '1 1 280px', 'minWidth': '260px'}),

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

    # View Top Cards Button - Above the graph/info panel area
    html.Div([
        html.Div([
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
                    'marginBottom': '12px'
                }
            ),
            html.Button(
                '✂️ Cards to Cut',
                id='cards-to-cut-button',
                n_clicks=0,
                style={
                    'padding': '8px 12px',
                    'backgroundColor': '#e74c3c',
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'borderRadius': '4px',
                    'marginBottom': '12px',
                    'marginLeft': '12px'
                }
            ),
            html.Button(
                '🔍 Get Recommendations',
                id='get-recommendations-button',
                n_clicks=0,
                style={
                    'padding': '8px 12px',
                    'backgroundColor': '#9b59b6',
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'borderRadius': '4px',
                    'marginBottom': '12px',
                    'marginLeft': '12px'
                }
            )
        ], style={'display': 'flex', 'gap': '12px'}),

        # Embedding Mode Switch
        html.Div([
            html.Label([
                html.Span('Synergy Mode: ', style={'fontWeight': 'bold', 'marginRight': '8px'}),
                dcc.RadioItems(
                    id='synergy-mode-switch',
                    options=[
                        {'label': ' Rule-Based', 'value': 'rules'},
                        {'label': ' AI Embeddings', 'value': 'embeddings'}
                    ],
                    value='rules',
                    inline=True,
                    style={'display': 'inline-block'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Div(
                id='synergy-mode-status',
                style={'fontSize': '11px', 'color': '#7f8c8d', 'marginTop': '4px', 'fontStyle': 'italic'}
            )
        ], style={'marginLeft': 'auto', 'paddingRight': '20px'}),
    ], style={'padding': '0 20px', 'marginTop': '16px', 'display': 'flex', 'alignItems': 'center'}),

    # Tabbed content: Synergy Graph and Mana Simulation
    dcc.Tabs(id='main-tabs', value='synergy', children=[
        dcc.Tab(label='Synergy Graph', value='synergy', children=[
            html.Div([
                # Graph Section - Left (3/4 of screen)
                html.Div([
                    cyto.Cytoscape(
                        id='card-graph',
                        layout={
                            'name': 'cose',
                            'animate': False,
                            'nodeRepulsion': 25000,
                            'idealEdgeLength': 250,
                            'edgeElasticity': 100,
                            'nestingFactor': 0.1,
                            'gravity': 1,
                            'numIter': 2500,
                            'initialTemp': 500,
                            'coolingFactor': 0.95,
                            'minTemp': 1.0,
                            'nodeOverlap': 100
                        },
                        style={'width': '100%', 'height': '650px'},
                        elements=[],
                        stylesheet=get_base_stylesheet()
                    )
                ], style={
                    'flex': '1 1 70%',
                    'backgroundColor': '#ffffff',
                    'borderRadius': '6px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'padding': '20px',
                    'minWidth': '500px',
                    'order': 1
                }),

                # Info Panel - Right (1/4 of screen)
                html.Div(
                    id='info-panel',
                    children=[
                        html.Div([
                            html.H3("Card Details", style={'color': '#2c3e50', 'marginBottom': '12px', 'fontSize': '16px', 'fontWeight': 'bold'}),
                            html.P(
                                "Click on a card in the graph to view its details and synergies here.",
                                style={'color': '#7f8c8d', 'fontSize': '13px', 'lineHeight': '1.6'}
                            )
                        ])
                    ],
                    style={
                        'flex': '0 0 28%',
                        'maxWidth': '350px',
                        'minWidth': '280px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '6px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'padding': '16px',
                        'height': '650px',
                        'maxHeight': '650px',
                        'overflowY': 'auto',
                        'overflowX': 'hidden',
                        'border': '1px solid #dee2e6',
                        'order': 2
                    }
                )
            ], style={
                'display': 'flex',
                'flexWrap': 'nowrap',
                'gap': '20px',
                'padding': '20px',
                'alignItems': 'flex-start'
            })
        ]),
        dcc.Tab(label='Mana Simulation', value='simulation', children=[
            html.Div([
                html.Div([
                    html.Label('Simulation Parameters', style={'fontWeight': 'bold'}),
                    html.Div([
                        html.Div([
                            html.Label('Iterations'),
                            dcc.Input(id='simulation-iterations-input', type='number', value=50000, min=1000, step=5000, style={'width': '120px'})
                        ]),
                        html.Div([
                            html.Label('Max Turn'),
                            dcc.Input(id='simulation-turns-input', type='number', value=10, min=1, max=20, step=1, style={'width': '100px'})
                        ]),
                        html.Div([
                            html.Label('Play/Draw'),
                            dcc.RadioItems(
                                id='simulation-play-draw-radio',
                                options=[{'label': 'On the Play', 'value': 'play'}, {'label': 'On the Draw', 'value': 'draw'}],
                                value='play', inline=True
                            )
                        ]),
                        html.Div([
                            dcc.Checklist(
                                id='simulation-respect-tapped',
                                options=[{'label': 'Respect enters tapped', 'value': 'tapped'}],
                                value=['tapped']
                            )
                        ]),
                        html.Div([
                            dcc.Checklist(
                                id='simulation-use-accelerators',
                                options=[{'label': 'Use accelerators (rocks/ramp)', 'value': 'accel'}],
                                value=['accel']
                            )
                        ]),
                        html.Div([
                            html.Label('Per-card turn'),
                            dcc.Input(id='per-card-turn-input', type='number', value=4, min=1, max=20, step=1, style={'width': '100px'})
                        ]),
                        html.Div([
                            html.Label('Per-card rows'),
                            dcc.Input(id='per-card-topn-input', type='number', value=25, min=5, max=100, step=5, style={'width': '100px'})
                        ])
                    ], style={'display': 'flex', 'gap': '18px', 'flexWrap': 'wrap', 'alignItems': 'center'})
                ], style={'backgroundColor': '#fff', 'padding': '12px 16px', 'borderRadius': '6px', 'boxShadow': '0 1px 2px rgba(0,0,0,0.08)'}),

                html.Div([
                    html.Button('Run Simulation', id='run-simulation-button', n_clicks=0, style={'padding': '10px 14px', 'backgroundColor': '#2980b9', 'color': '#fff', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold'}),
                    html.Span(id='simulation-status-message', style={'marginLeft': '12px', 'color': '#7f8c8d'})
                ], style={'marginTop': '12px'}),

                html.Div(id='simulation-summary', style={'marginTop': '8px', 'color': '#2c3e50'}),

                html.Div([
                    dcc.Graph(id='simulation-result-graph', figure={'data': [], 'layout': {'title': 'Simulation Results', 'xaxis': {'title': 'Turn'}, 'yaxis': {'title': 'Probability', 'range': [0, 1]}}}),
                ], style={'marginTop': '16px'}),

                html.Div([
                    dcc.Graph(id='simulation-mana-heatmap')
                ], style={'marginTop': '12px'}),

                html.Div([
                    dcc.Graph(id='simulation-opening-hand-hist')
                ], style={'marginTop': '12px'}),

                html.Div([
                    dcc.Graph(id='simulation-lands-in-hand-cdf')
                ], style={'marginTop': '12px'}),

                html.Div(id='simulation-result-table', style={'marginTop': '8px'}),

                html.Hr(),
                html.H4('Per-card castability by turn', style={'marginTop': '8px'}),
                html.Div(id='per-card-result-table', style={'marginTop': '8px'})
            ], style={'padding': '20px'})
        ])
    ]),

    dcc.Store(id='deck-data-store'),
    dcc.Store(id='selected-node-store'),
    dcc.Store(id='current-deck-file-store'),
    dcc.Store(id='role-filter-data'),
    dcc.Store(id='active-role-filter'),
    dcc.Store(id='synergy-mode-store', data='rules'),  # 'rules' or 'embeddings'
    dcc.Interval(id='status-clear-interval', interval=3000, n_intervals=0, disabled=True)
], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})


# Callback to show "Loading..." immediately when button clicked
@app.callback(
    Output('status-message', 'children', allow_duplicate=True),
    Input('load-deck-button', 'n_clicks'),
    prevent_initial_call=True
)
def show_loading_message(n_clicks):
    """Show loading message immediately when button is clicked"""
    return html.Div("Loading deck...", style={'color': '#3498db', 'fontWeight': 'bold'})


# Callback to load deck from URL
@app.callback(
    [Output('status-message', 'children'),
     Output('deck-selector', 'options'),
     Output('deck-data-store', 'data'),
     Output('deck-selector', 'value'),
     Output('status-clear-interval', 'disabled')],
    Input('load-deck-button', 'n_clicks'),
    State('deck-url-input', 'value'),
    State('deck-data-store', 'data'),
    prevent_initial_call=True
)
def load_deck(n_clicks, url, current_data):
    """Load deck from Archidekt URL and fetch card details from Scryfall"""
    if not url:
        return html.Div("Please enter a deck URL", style={'color': 'red'}), dash.no_update, current_data, None, True

    try:
        print(f"\n[DECK LOAD] Starting to load deck from URL: {url}")

        # Fetch deck from Archidekt
        print("[DECK LOAD] Step 1: Fetching from Archidekt...")
        deck_info = fetch_deck_from_archidekt(url)
        print(f"[DECK LOAD] Got deck: {deck_info['name']} with {len(deck_info['cards'])} cards")

        # Fetch detailed card info from Scryfall
        print("[DECK LOAD] Step 2: Fetching card details from Scryfall...")
        cards_with_details = fetch_card_details(deck_info['cards'])
        print(f"[DECK LOAD] Fetched details for {len(cards_with_details)} cards")

        # Annotate cards with functional roles
        print("[DECK LOAD] Step 3: Assigning roles...")
        assign_roles_to_cards(cards_with_details)

        # Create deck object
        print("[DECK LOAD] Step 4: Creating deck object...")
        deck = Deck(
            deck_id=deck_info['id'],
            name=deck_info['name'],
            cards=cards_with_details
        )

        # Analyze synergies
        print(f"[DECK LOAD] Step 5: Analyzing synergies for {len(cards_with_details)} cards...")
        print(f"[DECK LOAD] This may take 1-2 minutes for large decks. Please wait...")
        deck.synergies = analyze_deck_synergies(cards_with_details)
        print(f"[DECK LOAD] Synergy analysis complete! Found {len(deck.synergies)} synergies")

        # Save deck to file
        print("[DECK LOAD] Step 6: Saving deck to file...")
        deck_file_path = deck.save()
        print(f"[DECK LOAD] Deck saved to: {deck_file_path}")

        # Update deck list
        deck_files = list(Path('data/decks').glob('*.json'))
        deck_options = [{'label': f.stem, 'value': str(f)} for f in deck_files]

        # Store deck data
        stored_data = current_data or {}
        stored_data[deck.name] = deck.to_dict()

        print(f"[DECK LOAD] SUCCESS! Deck loaded: {deck.name}")
        status = html.Div(f"Successfully loaded deck: {deck.name}", style={'color': '#27ae60', 'fontWeight': 'bold'})
        # Automatically select the newly loaded deck and enable auto-clear interval
        return status, deck_options, stored_data, str(deck_file_path), False

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n[DECK LOAD ERROR] Failed to load deck!")
        print(f"[DECK LOAD ERROR] Error type: {type(e).__name__}")
        print(f"[DECK LOAD ERROR] Error message: {str(e)}")
        print(f"[DECK LOAD ERROR] Full traceback:\n{error_details}")
        return html.Div(f"Error loading deck: {str(e)}", style={'color': '#e74c3c', 'fontWeight': 'bold'}), dash.no_update, current_data, None, True


# Callback to auto-clear success message after 3 seconds
@app.callback(
    [Output('status-message', 'children', allow_duplicate=True),
     Output('status-clear-interval', 'disabled', allow_duplicate=True)],
    Input('status-clear-interval', 'n_intervals'),
    prevent_initial_call=True
)
def clear_status_message(n_intervals):
    """Clear status message after interval triggers"""
    return "", True  # Clear message and disable interval


# Callback for synergy mode switch
@app.callback(
    [Output('synergy-mode-store', 'data'),
     Output('synergy-mode-status', 'children')],
    Input('synergy-mode-switch', 'value'),
    prevent_initial_call=True
)
def update_synergy_mode(mode):
    """Update synergy mode and show status"""
    if mode == 'embeddings':
        if embedding_analyzer.is_loaded():
            status = "Using AI embeddings for semantic similarity"
            return mode, status
        else:
            status = "⚠️ Embeddings not available. Run: python scripts/generate_embeddings.py"
            return 'rules', status  # Fall back to rules mode
    else:
        status = "Using rule-based synergy detection"
        return mode, status


# Callback to update graph when deck is selected
@app.callback(
    [Output('card-graph', 'elements'),
     Output('current-deck-file-store', 'data'),
     Output('role-filter-data', 'data')],
    [Input('deck-selector', 'value'),
     Input('synergy-mode-store', 'data')],
    prevent_initial_call=True
)
def update_graph(deck_file, synergy_mode):
    """Update graph visualization when a deck is selected"""
    print(f"\n[UPDATE GRAPH] Called with deck_file: {deck_file}, synergy_mode: {synergy_mode}")

    if not deck_file:
        print("[UPDATE GRAPH] No deck file provided, using dash.no_update to preserve current state")
        return dash.no_update, dash.no_update, dash.no_update

    try:
        # Check if file exists before trying to load
        from pathlib import Path
        if not Path(deck_file).exists():
            print(f"[UPDATE GRAPH] WARNING: Deck file does not exist: {deck_file}")
            print(f"[UPDATE GRAPH] Using dash.no_update to preserve current state")
            return dash.no_update, dash.no_update, dash.no_update

        # Load deck data
        print(f"[UPDATE GRAPH] Loading deck from file: {deck_file}")
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        cards = deck_data.get('cards', [])
        synergies = deck_data.get('synergies', {})
        print(f"[UPDATE GRAPH] Loaded {len(cards)} cards and {len(synergies)} synergies")

        if cards:
            assign_roles_to_cards(cards)
        role_summary = summarize_roles(cards)

        # Build graph elements based on synergy mode
        print(f"[UPDATE GRAPH] Building graph elements using {synergy_mode} mode...")

        if synergy_mode == 'embeddings' and embedding_analyzer.is_loaded():
            # Use embedding-based graph
            elements = embedding_analyzer.build_embedding_graph(cards, min_similarity=0.6)
            print(f"[UPDATE GRAPH] Built {len(elements)} embedding-based graph elements")
        else:
            # Use rule-based graph
            elements = build_graph_elements(deck_data)
            print(f"[UPDATE GRAPH] Built {len(elements)} rule-based graph elements")

        print(f"[UPDATE GRAPH] SUCCESS - Graph updated!")

        return elements, deck_file, role_summary

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n[UPDATE GRAPH ERROR] Failed to update graph!")
        print(f"[UPDATE GRAPH ERROR] Error: {e}")
        print(f"[UPDATE GRAPH ERROR] Full traceback:\n{error_details}")
        return [], None, {}


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


# Simulation callback: runs Monte Carlo and updates outputs
@app.callback(
    [Output('simulation-result-graph', 'figure'),
     Output('simulation-status-message', 'children'),
     Output('simulation-result-table', 'children'),
     Output('simulation-mana-heatmap', 'figure'),
     Output('simulation-opening-hand-hist', 'figure'),
     Output('simulation-summary', 'children'),
     Output('per-card-result-table', 'children'),
     Output('simulation-lands-in-hand-cdf', 'figure')],
    Input('run-simulation-button', 'n_clicks'),
    [State('current-deck-file-store', 'data'),
     State('simulation-iterations-input', 'value'),
     State('simulation-turns-input', 'value'),
     State('simulation-play-draw-radio', 'value'),
     State('simulation-respect-tapped', 'value'),
     State('simulation-use-accelerators', 'value'),
     State('per-card-turn-input', 'value'),
     State('per-card-topn-input', 'value')],
    prevent_initial_call=True
)
def run_mana_simulation(n_clicks, deck_file, iterations, turns, play_or_draw, respect_tapped_vals, use_accel_vals, per_card_turn, per_card_topn):
    if not deck_file:
        return (
            dash.no_update,
            html.Span('Load or select a deck first.', style={'color': '#e74c3c'}),
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    try:
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)
    except Exception as e:
        return dash.no_update, html.Span(f'Failed to read deck file: {e}', style={'color': '#e74c3c'}), dash.no_update

    try:
        deck = Deck.from_dict(deck_data)
        params = SimulationParams(
            iterations=int(iterations or 50000),
            max_turn=int(turns or 10),
            on_the_play=(play_or_draw != 'draw'),
            respect_enters_tapped=('tapped' in (respect_tapped_vals or [])),
            use_accelerators=('accel' in (use_accel_vals or []))
        )
        sim = ManaSimulator(params)
        result = sim.simulate_deck(deck)

        # Build plotly figure
        x = list(range(1, params.max_turn + 1))
        y_color = [result.p_color_coverage.get(t, 0.0) for t in x]
        y_playable = [result.p_playable_spell.get(t, 0.0) for t in x]

        # Percentile band (available mana) overlay on a secondary y-axis
        p10s = [float(result.available_mana_summary.get(t, {}).get('p10', 0.0)) for t in x]
        p50s = [float(result.available_mana_summary.get(t, {}).get('p50', 0.0)) for t in x]
        p90s = [float(result.available_mana_summary.get(t, {}).get('p90', 0.0)) for t in x]

        # Color limitation rates (W/U/B/R/G) and playable fraction for saturation insights
        # Use deck's active colors from the simulation result
        colors = result.active_colors or []
        color_palette = {
            'W': '#f1c40f',  # yellow
            'U': '#3498db',  # blue
            'B': '#2c3e50',  # dark gray/black-ish
            'R': '#e74c3c',  # red
            'G': '#27ae60',  # green
        }
        color_lim_lines = {c: [float(result.color_limitation_rate.get(t, {}).get(c, 0.0)) for t in x] for c in colors}
        playable_fraction = [float(result.playable_fraction.get(t, 0.0)) for t in x]

        # Build a 2-row subplot: top — existing lines with percentile band; bottom — color limitation rates and playable fraction
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, specs=[[{"secondary_y": True}], [{}]])

        # Row 1: probabilities on primary y
        fig.add_trace(go.Scatter(x=x, y=y_color, mode='lines+markers', name='All Colors Available', line=dict(color='#1f77b4')), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=y_playable, mode='lines+markers', name='At Least One Spell Castable', line=dict(color='#2ca02c')), row=1, col=1, secondary_y=False)
        # Row 1: secondary y available mana percentiles band
        fig.add_trace(go.Scatter(x=x, y=p10s, mode='lines', line=dict(width=0, color='#e67e22'), name='Available Mana p10–p90', showlegend=True, hovertemplate='Turn %{x}<br>p10=%{y}<extra></extra>'), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=x, y=p90s, mode='lines', line=dict(width=0, color='#e67e22'), fill='tonexty', fillcolor='rgba(230,126,34,0.20)', name='Available Mana p10–p90', showlegend=False, hovertemplate='Turn %{x}<br>p90=%{y}<extra></extra>'), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=x, y=p50s, mode='lines+markers', name='Available Mana p50', line=dict(color='#e67e22')), row=1, col=1, secondary_y=True)

        # Row 2: color limitation rates per color
        for c in colors:
            fig.add_trace(go.Scatter(x=x, y=color_lim_lines[c], mode='lines+markers', name=f'Blocked by {c}', line=dict(color=color_palette[c], dash='dot')), row=2, col=1)
        # Row 2: playable fraction (how saturated the hand is overall)
        fig.add_trace(go.Scatter(x=x, y=playable_fraction, mode='lines+markers', name='% Cards Playable', line=dict(color='#7f8c8d')), row=2, col=1)

        # Layout and axes
        fig.update_layout(
            title={'text': 'Simulation Results<br><sup>Top: Probabilities (left) + Available mana percentiles (right) • Bottom: Color limitation rates and % playable</sup>'},
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        fig.update_xaxes(title_text='Turn', row=2, col=1)
        fig.update_yaxes(title_text='Probability', range=[0, 1], color='#1f77b4', row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text='Available mana', color='#e67e22', row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text='Color limitation / % playable', range=[0, 1], row=2, col=1)

        # Build simple table
        header = html.Tr([
            html.Th('Turn'),
            html.Th('% Have All Colors'),
            html.Th('% Have Playable Spell'),
            html.Th('Avg Lands in Play')
        ])
        rows = []
        for t in x:
            rows.append(html.Tr([
                html.Td(t),
                html.Td(f"{result.p_color_coverage.get(t, 0.0) * 100:.1f}%"),
                html.Td(f"{result.p_playable_spell.get(t, 0.0) * 100:.1f}%"),
                html.Td(f"{result.avg_lands_in_play.get(t, 0.0):.2f}")
            ]))
        table = html.Table([header] + rows, style={'width': '100%', 'backgroundColor': '#fff', 'borderCollapse': 'collapse'})

        # Heatmap for available mana distribution
        z_vals = []
        y_vals = []
        x_vals = x
        # Collect all mana keys to determine y-axis
        mana_keys = sorted({k for t in x for k in result.available_mana_hist.get(t, {}).keys()})
        for mk in mana_keys:
            y_vals.append(str(mk))
            row = []
            for t in x:
                hist = result.available_mana_hist.get(t, {})
                total = sum(hist.values()) or 1
                row.append((hist.get(mk, 0)) / total)
            z_vals.append(row)
        heatmap_fig = go.Figure(data=go.Heatmap(z=z_vals, x=x_vals, y=y_vals, colorscale='Blues'))
        heatmap_fig.update_layout(title='Available Mana Distribution (per turn)', xaxis_title='Turn', yaxis_title='Available mana', yaxis_type='category')

        # Opening hand lands histogram
        oh_hist = result.opening_hand_land_hist or {}
        oh_x = sorted(oh_hist.keys())
        oh_y = [oh_hist[k] / max(1, sum(oh_hist.values())) for k in oh_x]
        opening_fig = go.Figure(data=[go.Bar(x=oh_x, y=oh_y)])
        opening_fig.update_layout(title='Opening Hand Land Count (probability)', xaxis_title='Lands in opening 7', yaxis_title='Probability', yaxis=dict(range=[0,1]))

        # Summary text: min, max, mode curves for available mana
        min_curve = [int(result.available_mana_summary.get(t, {}).get('min', 0)) for t in x]
        max_curve = [int(result.available_mana_summary.get(t, {}).get('max', 0)) for t in x]
        mode_curve = [int(result.mode_available_mana_curve.get(t, 0)) for t in x]
        # Color status at focus turn (use per-card turn if provided, else last turn)
        t_focus = int(per_card_turn or params.max_turn)
        color_status_lines = []
        focus_colors = colors
        for c in focus_colors:
            avail = float(result.color_available_prob.get(t_focus, {}).get(c, 0.0))
            block = float(result.color_limitation_rate.get(t_focus, {}).get(c, 0.0))
            if avail > 0.9 and block < 0.05:
                status = 'saturated'
            elif avail < 0.6 or block > 0.15:
                status = 'missing'
            else:
                status = 'balanced'
            ksuggest = int(result.color_suggest_k.get(t_focus, {}).get(c, 0))
            suggest_str = f"; suggest +{ksuggest} {c} sources" if ksuggest > 0 and status != 'saturated' else ''
            color_status_lines.append(html.Span(f"{c}: {status} (P(avail)={avail:.2f}, block={block:.2f}{suggest_str})", style={'marginRight': '12px'}))

        summary = html.Div([
            html.Div(f"Mode curve (available mana): {mode_curve}"),
            html.Div(f"Min curve: {min_curve}"),
            html.Div(f"Max curve: {max_curve}"),
            html.Div([html.Strong(f"Color status at turn {t_focus}: "), *color_status_lines], style={'marginTop': '6px'})
        ])

        # Per-card table: probability castable by selected turn
        t_sel = int(per_card_turn or params.max_turn)
        topn = int(per_card_topn or 25)
        items = []
        for name, by_turn in result.per_card_prob_by_turn.items():
            p = by_turn.get(t_sel, 0.0)
            items.append((name, p))
        # Sort descending and take top N
        items.sort(key=lambda x: x[1], reverse=True)
        items = items[:topn]
        card_table = html.Table([
            html.Tr([html.Th('Card'), html.Th(f'% Castable by turn {t_sel}')])
        ] + [
            html.Tr([html.Td(name), html.Td(f"{p*100:.1f}%")]) for name, p in items
        ], style={'width':'100%', 'backgroundColor':'#fff', 'borderCollapse':'collapse'})

        status = html.Span(
            f"Done. Iterations: {params.iterations}, Max turn: {params.max_turn}, On the play: {params.on_the_play}",
            style={'color': '#2c3e50'}
        )

        # Lands-in-hand CDF at focus turn
        lih = result.lands_in_hand_hist.get(t_focus, {}) or {}
        total_lih = sum(lih.values()) or 1
        xs = sorted(lih.keys())
        cum = 0.0
        cdf_y = []
        for k in xs:
            cum += lih.get(k, 0) / total_lih
            cdf_y.append(cum)
        cdf_fig = go.Figure(data=[go.Scatter(x=xs, y=cdf_y, mode='lines+markers', line=dict(shape='hv'))])
        cdf_fig.update_layout(title=f'Lands in Hand CDF (turn {t_focus})', xaxis_title='Lands in hand', yaxis_title='Cumulative probability', yaxis=dict(range=[0,1]))

        return fig, status, table, heatmap_fig, opening_fig, summary, card_table, cdf_fig
    except Exception as e:
        return (dash.no_update,
                html.Span(f'Simulation error: {e}', style={'color': '#e74c3c'}),
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update)


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
    """Reorganize graph to highlight and center top 5 cards"""
    if not deck_file or not elements:
        return dash.no_update, dash.no_update, dash.no_update

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        # Get top 5 cards - CHANGED FROM 10 TO 5
        rankings_summary = get_deck_rankings_summary(deck_data, top_n=5)
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
                    # Get the weight to determine color
                    weight = element['data'].get('weight', 1)
                    # Keep weight-based coloring even when highlighting
                    if weight >= 11:
                        edge_color = '#c0392b'
                    elif weight >= 9:
                        edge_color = '#e74c3c'
                    elif weight >= 7:
                        edge_color = '#e67e22'
                    elif weight >= 5:
                        edge_color = '#d4a574'
                    elif weight >= 3:
                        edge_color = '#b3a59c'
                    else:
                        edge_color = '#95a5a6'

                    base_stylesheet.append({
                        'selector': f'edge[id="{edge_id}"]',
                        'style': {
                            'width': 6,
                            'line-color': edge_color,
                            'opacity': 0.9,
                            'z-index': 999
                        }
                    })

        # Use cose layout with optimized parameters for top cards view
        # The top cards will still be visually prominent due to size/color
        layout = {
            'name': 'cose',
            'animate': True,
            'animationDuration': 1000,
            'nodeRepulsion': 28000,
            'idealEdgeLength': 270,
            'edgeElasticity': 100,
            'nestingFactor': 0.1,
            'gravity': 1.5,
            'numIter': 2500,
            'initialTemp': 500,
            'coolingFactor': 0.95,
            'minTemp': 1.0,
            'nodeOverlap': 100
        }

        return base_stylesheet, layout, dash.no_update

    except Exception as e:
        print(f"Error highlighting top cards: {e}")
        return dash.no_update, dash.no_update, dash.no_update



# Callback for node/edge selection and highlighting
@app.callback(
    [Output('card-graph', 'stylesheet'),
     Output('info-panel', 'children'),
     Output('card-graph', 'layout', allow_duplicate=True)],
    [Input('card-graph', 'tapNodeData'),
     Input('card-graph', 'tapEdgeData'),
     Input('active-role-filter', 'data'),
     Input('get-recommendations-button', 'n_clicks'),
     Input('cards-to-cut-button', 'n_clicks'),
     Input('view-top-cards-button', 'n_clicks')],
    [State('card-graph', 'elements'),
     State('role-filter-data', 'data'),
     State('current-deck-file-store', 'data'),
     State('synergy-mode-store', 'data')],
    prevent_initial_call=True
)
def handle_selection(node_data, edge_data, active_filter, rec_clicks, cut_clicks, top_clicks, elements, role_summary, deck_file, synergy_mode):
    """Handle node/edge selection, role filter, recommendations, and update highlighting."""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    triggered_prop = ctx.triggered[0]['prop_id']

    # Handle recommendations button click
    if triggered_prop == 'get-recommendations-button.n_clicks':
        print(f"[DEBUG] Recommendations triggered in handle_selection callback, deck_file={deck_file}")

        if not deck_file:
            return dash.no_update, html.Div([
                html.P("⚠️ Please load a deck first before getting recommendations.",
                       style={'color': '#e74c3c', 'padding': '16px', 'textAlign': 'center'})
            ]), dash.no_update

        # Load deck from file and generate recommendations
        try:
            with open(deck_file, 'r') as f:
                deck_obj = json.load(f)

            # Get commander's color identity
            commander_colors = None
            for card in deck_obj.get('cards', []):
                if card.get('is_commander', False):
                    commander_colors = card.get('color_identity', [])
                    break

            # Get recommendations based on synergy mode
            print(f"[DEBUG] Generating recommendations using {synergy_mode} mode for {len(deck_obj.get('cards', []))} cards, colors={commander_colors}")

            if synergy_mode == 'embeddings' and embedding_analyzer.is_loaded():
                # Use embedding-based recommendations
                recommended_cards = embedding_analyzer.get_deck_recommendations(
                    deck_cards=deck_obj.get('cards', []),
                    available_cards=None,  # All cards in embeddings
                    limit=10
                )
                deck_scores = embedding_analyzer.score_deck_cards(deck_obj.get('cards', []))
                total_synergy = {
                    'total_score': sum(c['synergy_score'] for c in deck_scores),
                    'average_score': sum(c['synergy_score'] for c in deck_scores) / len(deck_scores) if deck_scores else 0,
                    'card_count': len(deck_scores)
                }
                # Convert embedding format to match UI expectations
                for card in recommended_cards:
                    card['recommendation_score'] = card.get('average_similarity', 0) * 100  # Scale for display
                    card['synergy_reasons'] = [f"Similar to {syn['with']} ({syn['similarity']:.3f})"
                                              for syn in card.get('top_synergies', [])]
            else:
                # Use rule-based recommendations
                rec_result = recommendations.get_recommendations(
                    deck_cards=deck_obj.get('cards', []),
                    color_identity=commander_colors,
                    limit=10,
                    include_deck_scores=True  # Score deck cards too
                )
                recommended_cards = rec_result.get('recommendations', [])
                deck_scores = rec_result.get('deck_scores', [])
                total_synergy = rec_result.get('total_deck_synergy', {})

            print(f"[DEBUG] Got {len(recommended_cards)} recommendations and scored {len(deck_scores)} deck cards")
            print(f"[DEBUG] Total deck synergy: {total_synergy}")

            # Build recommendations UI (detailed for side panel)
            rec_items = []
            for idx, card in enumerate(recommended_cards, 1):
                card_name = card.get('name', 'Unknown')
                score = card.get('recommendation_score', 0)
                type_line = card.get('type_line', '')
                mana_cost = card.get('mana_cost', '')
                oracle_text = card.get('oracle_text', '')
                synergy_reasons = card.get('synergy_reasons', [])
                cmc = card.get('cmc', 0)

                # Truncate oracle text if too long
                if len(oracle_text) > 200:
                    oracle_text = oracle_text[:200] + '...'

                # Get replacement suggestions (logic kept for future use)
                # TODO: Implement smart single-card replacement that considers:
                # - Card type matching (creature for creature, etc.)
                # - Mana curve balance
                # - Strategy alignment (voltron vs midrange vs combo)
                # - Before/after total deck synergy comparison
                could_replace = card.get('could_replace', [])

                rec_items.append(html.Div([
                    # Card name and score
                    html.Div([
                        html.Span(f"{idx}. ", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#7f8c8d'}),
                        html.Strong(card_name, style={'fontSize': '14px', 'color': '#2c3e50'}),
                        html.Span(f" ({score:.0f})", style={'fontSize': '11px', 'color': '#9b59b6', 'marginLeft': '4px'})
                    ], style={'marginBottom': '4px'}),

                    # Type line
                    html.Div(type_line, style={'fontSize': '11px', 'color': '#34495e', 'fontStyle': 'italic', 'marginBottom': '4px'}),

                    # Mana cost and CMC
                    html.Div([
                        html.Span(mana_cost if mana_cost else '—', style={'fontSize': '12px', 'color': '#7f8c8d', 'marginRight': '8px'}),
                        html.Span(f"CMC: {cmc}", style={'fontSize': '11px', 'color': '#95a5a6'})
                    ], style={'marginBottom': '6px'}),

                    # Replacement suggestions - HIDDEN FOR NOW
                    # Will be re-enabled once we implement smart card-type-aware replacement logic
                    # html.Div([...]) if could_replace else None,

                    # Synergy reasons
                    html.Div([
                        html.Strong("Why?", style={'fontSize': '11px', 'color': '#16a085'}),
                        html.Ul([
                            html.Li(reason, style={'fontSize': '10px', 'color': '#555', 'marginBottom': '2px'})
                            for reason in synergy_reasons[:3]  # Top 3 reasons
                        ], style={'marginTop': '2px', 'marginBottom': '6px', 'paddingLeft': '16px'})
                    ] if synergy_reasons else None),

                    # Oracle text
                    html.Div(oracle_text, style={
                        'fontSize': '10px',
                        'color': '#7f8c8d',
                        'fontStyle': 'italic',
                        'backgroundColor': '#f8f9fa',
                        'padding': '6px',
                        'borderRadius': '4px',
                        'marginTop': '6px'
                    }) if oracle_text else None

                ], style={
                    'marginBottom': '14px',
                    'paddingBottom': '14px',
                    'borderBottom': '2px solid #ecf0f1',
                    'paddingLeft': '4px',
                    'borderLeft': '3px solid #9b59b6'
                }))

            # Build weakest cards summary
            weakest_cards_section = None
            if deck_scores:
                # Show bottom 10 cards
                weakest_cards = deck_scores[:10]
                weakest_items = []
                for i, weak_card in enumerate(weakest_cards, 1):
                    weakest_items.append(html.Li([
                        html.Span(f"{weak_card['name']}", style={'fontWeight': 'bold', 'color': '#e74c3c'}),
                        html.Span(f" ({weak_card['synergy_score']:.0f})", style={'color': '#95a5a6', 'fontSize': '10px', 'marginLeft': '4px'})
                    ], style={'fontSize': '11px', 'marginBottom': '4px'}))

                weakest_cards_section = html.Div([
                    html.H5("⚠️ Weakest Cards in Your Deck", style={'marginTop': '20px', 'marginBottom': '8px', 'color': '#e74c3c', 'fontSize': '14px'}),
                    html.P("These cards have the lowest synergy with your deck:", style={'fontSize': '11px', 'color': '#7f8c8d', 'marginBottom': '8px'}),
                    html.Ol(weakest_items, style={'paddingLeft': '20px'})
                ], style={'backgroundColor': '#fef5f5', 'padding': '12px', 'borderRadius': '6px', 'borderLeft': '3px solid #e74c3c'})

            # Build total synergy display
            total_synergy_section = None
            if total_synergy:
                total_score = total_synergy.get('total_score', 0)
                avg_score = total_synergy.get('average_score', 0)
                card_count = total_synergy.get('card_count', 0)

                total_synergy_section = html.Div([
                    html.Div([
                        html.Span("📊 Deck Synergy Score: ", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#2c3e50'}),
                        html.Span(f"{total_score:.0f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#27ae60'}),
                    ], style={'marginBottom': '6px'}),
                    html.Div([
                        html.Span(f"Average: {avg_score:.1f} per card ", style={'fontSize': '12px', 'color': '#7f8c8d'}),
                        html.Span(f"({card_count} cards scored)", style={'fontSize': '11px', 'color': '#95a5a6'})
                    ])
                ], style={
                    'backgroundColor': '#e8f8f5',
                    'padding': '12px',
                    'borderRadius': '6px',
                    'marginBottom': '16px',
                    'borderLeft': '4px solid #27ae60'
                })

            recommendations_panel = html.Div([
                html.H4("🔍 Recommendations", style={'marginBottom': '12px', 'color': '#9b59b6', 'fontSize': '16px'}),
                total_synergy_section,
                html.Div(rec_items),
                weakest_cards_section
            ])

            return dash.no_update, recommendations_panel, dash.no_update

        except Exception as e:
            print(f"[DEBUG] Error generating recommendations: {e}")
            return dash.no_update, html.Div([
                html.P(f"⚠️ Error: {str(e)}",
                       style={'color': '#e74c3c', 'padding': '16px', 'fontSize': '12px'})
            ]), dash.no_update

    # Handle cards-to-cut button click
    if triggered_prop == 'cards-to-cut-button.n_clicks':
        print(f"[DEBUG] Cards to cut triggered, deck_file={deck_file}")

        if not deck_file:
            return dash.no_update, html.Div([
                html.P("⚠️ Please load a deck first before analyzing cards to cut.",
                       style={'color': '#e74c3c', 'padding': '16px', 'textAlign': 'center'})
            ]), dash.no_update

        # Load deck from file
        try:
            with open(deck_file, 'r') as f:
                deck_obj = json.load(f)

            cards = deck_obj.get('cards', [])

            # Calculate synergy scores based on mode
            print(f"[DEBUG] Calculating cards to cut using {synergy_mode} mode")

            if synergy_mode == 'embeddings' and embedding_analyzer.is_loaded():
                # Use embedding-based scoring
                scored_cards = embedding_analyzer.score_deck_cards(cards)
                # Convert to dict format for compatibility
                card_scores = {card['name']: card['synergy_score'] for card in scored_cards}
                bottom_cards = [(card['name'], card['synergy_score']) for card in scored_cards[:10]]
            else:
                # Use rule-based scoring
                synergies = deck_obj.get('synergies', [])
                card_scores = {}

                # Handle synergies as dict (canonical format) or list (legacy)
                if isinstance(synergies, dict):
                    synergy_list = list(synergies.values())
                else:
                    synergy_list = synergies

                for card in cards:
                    card_name = card.get('name')
                    if not card_name:
                        continue

                    # Skip lands - they don't have strategic synergies
                    card_type = card.get('type_line', '').lower()
                    if '//' not in card_type and 'land' in card_type:
                        continue

                    # Count synergies involving this card
                    score = 0
                    for synergy in synergy_list:
                        # Handle both dict and other data structures
                        if isinstance(synergy, dict):
                            if card_name in [synergy.get('card1'), synergy.get('card2')]:
                                score += synergy.get('total_weight', 1.0)

                    card_scores[card_name] = score

                # Get bottom 10 cards (least synergistic)
                sorted_cards = sorted(card_scores.items(), key=lambda x: x[1])
                bottom_cards = sorted_cards[:10]

            # Calculate deck statistics for context
            if card_scores:
                avg_synergy = sum(card_scores.values()) / len(card_scores)
                max_synergy = max(card_scores.values())
            else:
                avg_synergy = 0
                max_synergy = 0

            # Build cards-to-cut UI
            cut_items = []
            for idx, (card_name, score) in enumerate(bottom_cards, 1):
                # Find full card data
                card_data = next((c for c in cards if c.get('name') == card_name), {})

                type_line = card_data.get('type_line', '')
                mana_cost = card_data.get('mana_cost', '')
                oracle_text = card_data.get('oracle_text', '')
                cmc = card_data.get('cmc', 0)

                # Truncate oracle text
                if len(oracle_text) > 200:
                    oracle_text = oracle_text[:200] + '...'

                # Determine reason with meaningful context
                reasons = []
                if score == 0:
                    reasons.append("No synergies detected")
                else:
                    # Show absolute score with deck context
                    reasons.append(f"Synergy score: {score:.1f} (deck avg: {avg_synergy:.1f}, max: {max_synergy:.1f})")

                cut_items.append(html.Div([
                    # Card name and score
                    html.Div([
                        html.Span(f"{idx}. ", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#7f8c8d'}),
                        html.Strong(card_name, style={'fontSize': '14px', 'color': '#2c3e50'}),
                        html.Span(f" ({score:.1f})", style={'fontSize': '11px', 'color': '#e74c3c', 'marginLeft': '4px'})
                    ], style={'marginBottom': '4px'}),

                    # Type line
                    html.Div(type_line, style={'fontSize': '11px', 'color': '#34495e', 'fontStyle': 'italic', 'marginBottom': '4px'}),

                    # Mana cost and CMC
                    html.Div([
                        html.Span(mana_cost if mana_cost else '—', style={'fontSize': '12px', 'color': '#7f8c8d', 'marginRight': '8px'}),
                        html.Span(f"CMC: {cmc}", style={'fontSize': '11px', 'color': '#95a5a6'})
                    ], style={'marginBottom': '6px'}),

                    # Reasons for cutting
                    html.Div([
                        html.Strong("Why cut?", style={'fontSize': '11px', 'color': '#c0392b'}),
                        html.Ul([
                            html.Li(reason, style={'fontSize': '10px', 'color': '#555', 'marginBottom': '2px'})
                            for reason in reasons
                        ], style={'marginTop': '2px', 'marginBottom': '6px', 'paddingLeft': '16px'})
                    ]),

                    # Oracle text
                    html.Div(oracle_text, style={
                        'fontSize': '10px',
                        'color': '#7f8c8d',
                        'fontStyle': 'italic',
                        'backgroundColor': '#f8f9fa',
                        'padding': '6px',
                        'borderRadius': '4px',
                        'marginTop': '6px'
                    }) if oracle_text else None

                ], style={
                    'marginBottom': '14px',
                    'paddingBottom': '14px',
                    'borderBottom': '2px solid #ecf0f1',
                    'paddingLeft': '4px',
                    'borderLeft': '3px solid #e74c3c'
                }))

            cut_panel = html.Div([
                html.H4("✂️ Cards to Cut", style={'marginBottom': '12px', 'color': '#e74c3c', 'fontSize': '16px'}),
                html.P("These cards have the lowest synergy with the rest of your deck:", style={'fontSize': '11px', 'color': '#7f8c8d', 'marginBottom': '12px'}),
                html.Div(cut_items)
            ])

            # Create stylesheet highlighting low-synergy cards in red
            stylesheet = list(get_base_stylesheet())
            bottom_card_names = [name for name, _ in bottom_cards]

            # Highlight low-synergy cards in red
            for card_name in bottom_card_names:
                stylesheet.append({
                    'selector': f'node[label = "{card_name}"]',
                    'style': {
                        'border-color': '#e74c3c',
                        'border-width': '6px',
                        'background-color': '#e74c3c'
                    }
                })

            # Dim other cards
            for card in cards:
                if card.get('name') not in bottom_card_names:
                    stylesheet.append({
                        'selector': f'node[label = "{card.get("name")}"]',
                        'style': {
                            'opacity': 0.3
                        }
                    })

            # Create layout to highlight low-synergy cards
            layout = {
                'name': 'cose',
                'animate': True,
                'animationDuration': 1000,
                'nodeRepulsion': 35000,
                'idealEdgeLength': 250,
                'edgeElasticity': 120,
                'nestingFactor': 0.1,
                'gravity': 3,
                'numIter': 2500,
                'initialTemp': 600,
                'coolingFactor': 0.95,
                'minTemp': 1.0,
                'nodeOverlap': 100
            }

            return stylesheet, cut_panel, layout

        except Exception as e:
            print(f"[DEBUG] Error analyzing cards to cut: {e}")
            import traceback
            traceback.print_exc()
            return dash.no_update, html.Div([
                html.P(f"⚠️ Error: {str(e)}",
                       style={'color': '#e74c3c', 'padding': '16px', 'fontSize': '12px'})
            ]), dash.no_update

    # Handle view-top-cards button click
    if triggered_prop == 'view-top-cards-button.n_clicks':
        print(f"[DEBUG] View top cards triggered, deck_file={deck_file}")

        if not deck_file:
            return dash.no_update, html.Div([
                html.P("⚠️ Please load a deck first.",
                       style={'color': '#e74c3c', 'padding': '16px', 'textAlign': 'center'})
            ]), dash.no_update

        # Load deck from file
        try:
            with open(deck_file, 'r') as f:
                deck_obj = json.load(f)

            cards = deck_obj.get('cards', [])

            # Get top 10 cards by synergy ranking based on mode
            print(f"[DEBUG] Getting top cards using {synergy_mode} mode")

            if synergy_mode == 'embeddings' and embedding_analyzer.is_loaded():
                # Use embedding-based scoring
                scored_cards = embedding_analyzer.score_deck_cards(cards)
                # Get highest scoring cards (reverse order)
                top_scored = sorted(scored_cards, key=lambda x: x['synergy_score'], reverse=True)[:10]
                # Convert to format expected by UI
                top_cards = [{'name': card['name'], 'total_synergy': card['synergy_score']}
                           for card in top_scored]
            else:
                # Use rule-based ranking
                rankings_summary = get_deck_rankings_summary(deck_obj, top_n=10)
                top_cards = rankings_summary.get('top_cards', [])

            # Build top cards UI
            top_items = []
            for idx, card_info in enumerate(top_cards, 1):
                card_name = card_info.get('name', 'Unknown')
                rank_score = card_info.get('total_synergy', 0)

                # Find full card data
                card_data = next((c for c in cards if c.get('name') == card_name), {})

                type_line = card_data.get('type_line', '')
                mana_cost = card_data.get('mana_cost', '')
                oracle_text = card_data.get('oracle_text', '')
                cmc = card_data.get('cmc', 0)

                # Truncate oracle text
                if len(oracle_text) > 200:
                    oracle_text = oracle_text[:200] + '...'

                top_items.append(html.Div([
                    # Card name and score
                    html.Div([
                        html.Span(f"{idx}. ", style={'fontWeight': 'bold', 'fontSize': '14px', 'color': '#7f8c8d'}),
                        html.Strong(card_name, style={'fontSize': '14px', 'color': '#2c3e50'}),
                        html.Span(f" ({rank_score:.1f})", style={'fontSize': '11px', 'color': '#2ecc71', 'marginLeft': '4px'})
                    ], style={'marginBottom': '4px'}),

                    # Type line
                    html.Div(type_line, style={'fontSize': '11px', 'color': '#34495e', 'fontStyle': 'italic', 'marginBottom': '4px'}),

                    # Mana cost and CMC
                    html.Div([
                        html.Span(mana_cost if mana_cost else '—', style={'fontSize': '12px', 'color': '#7f8c8d', 'marginRight': '8px'}),
                        html.Span(f"CMC: {cmc}", style={'fontSize': '11px', 'color': '#95a5a6'})
                    ], style={'marginBottom': '6px'}),

                    # Why it's a top card
                    html.Div([
                        html.Strong("Why top card?", style={'fontSize': '11px', 'color': '#27ae60'}),
                        html.Ul([
                            html.Li(f"High synergy centrality (rank {idx})", style={'fontSize': '10px', 'color': '#555', 'marginBottom': '2px'}),
                            html.Li(f"Synergy score: {rank_score:.1f}", style={'fontSize': '10px', 'color': '#555', 'marginBottom': '2px'})
                        ], style={'marginTop': '2px', 'marginBottom': '6px', 'paddingLeft': '16px'})
                    ]),

                    # Oracle text
                    html.Div(oracle_text, style={
                        'fontSize': '10px',
                        'color': '#7f8c8d',
                        'fontStyle': 'italic',
                        'backgroundColor': '#f8f9fa',
                        'padding': '6px',
                        'borderRadius': '4px',
                        'marginTop': '6px'
                    }) if oracle_text else None

                ], style={
                    'marginBottom': '14px',
                    'paddingBottom': '14px',
                    'borderBottom': '2px solid #ecf0f1',
                    'paddingLeft': '4px',
                    'borderLeft': '3px solid #2ecc71'
                }))

            top_panel = html.Div([
                html.H4("⭐ Top Cards", style={'marginBottom': '12px', 'color': '#2ecc71', 'fontSize': '16px'}),
                html.P("These cards have the highest synergy with the rest of your deck:", style={'fontSize': '11px', 'color': '#7f8c8d', 'marginBottom': '12px'}),
                html.Div(top_items)
            ])

            # Create stylesheet highlighting top cards in green
            stylesheet = list(get_base_stylesheet())
            top_card_names = [card['name'] for card in top_cards]

            # Highlight top cards in green
            for card_name in top_card_names:
                stylesheet.append({
                    'selector': f'node[label = "{card_name}"]',
                    'style': {
                        'border-color': '#2ecc71',
                        'border-width': '6px',
                        'background-color': '#2ecc71'
                    }
                })

            # Dim other cards
            for card in cards:
                if card.get('name') not in top_card_names:
                    stylesheet.append({
                        'selector': f'node[label = "{card.get("name")}"]',
                        'style': {
                            'opacity': 0.3
                        }
                    })

            # Create layout to highlight top cards
            layout = {
                'name': 'cose',
                'animate': True,
                'animationDuration': 1000,
                'nodeRepulsion': 35000,
                'idealEdgeLength': 250,
                'edgeElasticity': 120,
                'nestingFactor': 0.1,
                'gravity': 3,
                'numIter': 2500,
                'initialTemp': 600,
                'coolingFactor': 0.95,
                'minTemp': 1.0,
                'nodeOverlap': 100
            }

            return stylesheet, top_panel, layout

        except Exception as e:
            print(f"[DEBUG] Error showing top cards: {e}")
            import traceback
            traceback.print_exc()
            return dash.no_update, html.Div([
                html.P(f"⚠️ Error: {str(e)}",
                       style={'color': '#e74c3c', 'padding': '16px', 'fontSize': '12px'})
            ]), dash.no_update

    if elements is None:
        if triggered_prop == 'active-role-filter.data':
            stylesheet = apply_role_filter_styles(get_base_stylesheet(), active_filter, role_summary, [])
            return stylesheet, dash.no_update, dash.no_update
        return dash.no_update, dash.no_update, dash.no_update

    base_stylesheet = get_base_stylesheet()
    base_stylesheet = apply_role_filter_styles(base_stylesheet, active_filter, role_summary, elements)

    if triggered_prop == 'active-role-filter.data':
        # Trigger layout reorganization for role filter
        layout = {
            'name': 'cose',
            'animate': True,
            'animationDuration': 1000,
            'nodeRepulsion': 30000,
            'idealEdgeLength': 280,
            'edgeElasticity': 100,
            'nestingFactor': 0.1,
            'gravity': 2,
            'numIter': 2500,
            'initialTemp': 500,
            'coolingFactor': 0.95,
            'minTemp': 1.0,
            'nodeOverlap': 100
        }
        return base_stylesheet, dash.no_update, layout

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
            # Highlight each connected edge individually while preserving weight-based color
            for edge in connected_edges:
                edge_id = edge["data"]["id"]
                weight = edge["data"].get("weight", 1)

                # Determine color based on weight
                if weight >= 11:
                    edge_color = '#c0392b'  # Dark red
                elif weight >= 9:
                    edge_color = '#e74c3c'  # Red-orange
                elif weight >= 7:
                    edge_color = '#e67e22'  # Orange
                elif weight >= 5:
                    edge_color = '#d4a574'  # Tan
                elif weight >= 3:
                    edge_color = '#b3a59c'  # Light brown-gray
                else:
                    edge_color = '#95a5a6'  # Gray

                stylesheet.append({
                    'selector': f'edge[id="{edge_id}"]',
                    'style': {
                        'opacity': 1,
                        'line-color': edge_color,
                        'width': max(weight * 0.4, 3)  # Scale width but ensure minimum visibility
                    }
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
                                html.Strong(f"{syn.get('name', 'Synergy')}: "),
                                f"{syn.get('description', 'N/A')} ",
                                html.Span(f"(+{syn.get('value', syn.get('strength', 0))})", style={'color': '#27ae60', 'fontWeight': 'bold'})
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

        # Trigger layout reorganization for card selection
        # Use cose layout with high repulsion to prevent overlap
        layout = {
            'name': 'cose',
            'animate': True,
            'animationDuration': 1000,
            'nodeRepulsion': 35000,
            'idealEdgeLength': 250,
            'edgeElasticity': 120,
            'nestingFactor': 0.1,
            'gravity': 3,
            'numIter': 2500,
            'initialTemp': 600,
            'coolingFactor': 0.95,
            'minTemp': 1.0,
            'nodeOverlap': 100
        }

        return stylesheet, info_panel, layout

    if edge_data:
        edge_id = edge_data['id']
        print(f"Edge clicked: {edge_id}")
        print(f"Edge data: {edge_data}")
        stylesheet.extend([
            {
                'selector': f'edge[id="{edge_id}"]',
                'style': {
                    'line-color': '#f39c12',
                    'width': 6,
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

        # Trigger layout reorganization for edge selection
        layout = {
            'name': 'cose',
            'animate': True,
            'animationDuration': 1000,
            'nodeRepulsion': 30000,
            'idealEdgeLength': 260,
            'edgeElasticity': 100,
            'nestingFactor': 0.1,
            'gravity': 2,
            'numIter': 2500,
            'initialTemp': 500,
            'coolingFactor': 0.95,
            'minTemp': 1.0,
            'nodeOverlap': 100
        }

        return stylesheet, info_panel, layout

    return base_stylesheet, html.Div("Click on a card or synergy edge to see details"), dash.no_update


if __name__ == '__main__':
    # Ensure data directory exists
    Path('data/decks').mkdir(parents=True, exist_ok=True)

    # Run the app
    app.run_server(debug=True, host='0.0.0.0', port=8050)
