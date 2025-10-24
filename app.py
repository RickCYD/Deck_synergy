"""
MTG Commander Deck Synergy Visualizer
Main Dash application file
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_cytoscape as cyto
import json
import os
from pathlib import Path

# Import custom modules
from src.api.archidekt import fetch_deck_from_archidekt
from src.api.scryfall import fetch_card_details
from src.models.deck import Deck
from src.synergy_engine.analyzer import analyze_deck_synergies
from src.utils.graph_builder import build_graph_elements

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "MTG Commander Synergy Visualizer"

# Load Cytoscape layouts
cyto.load_extra_layouts()

# Define the app layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("MTG Commander Deck Synergy Visualizer",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Visualize card synergies in your Commander deck as an interactive graph",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '20px'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

    # Control Panel
    html.Div([
        html.Div([
            # Deck URL Input
            html.Div([
                html.Label("Archidekt Deck URL:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(
                    id='deck-url-input',
                    type='text',
                    placeholder='https://archidekt.com/decks/...',
                    style={'width': '100%', 'padding': '10px', 'marginBottom': '10px'}
                ),
                html.Button('Load Deck', id='load-deck-button', n_clicks=0,
                           style={'width': '100%', 'padding': '10px', 'backgroundColor': '#3498db',
                                  'color': 'white', 'border': 'none', 'cursor': 'pointer',
                                  'fontSize': '16px', 'fontWeight': 'bold'})
            ], style={'marginBottom': '20px'}),

            # Deck Selector
            html.Div([
                html.Label("Select Deck:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='deck-selector',
                    options=[],
                    placeholder='Select a loaded deck...',
                    style={'marginBottom': '10px'}
                )
            ], style={'marginBottom': '20px'}),

            # Status Messages
            html.Div(id='status-message', style={'padding': '10px', 'marginBottom': '10px'}),

            # Graph Layout Selector
            html.Div([
                html.Label("Graph Layout:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='layout-selector',
                    options=[
                        {'label': 'Cose (Force-directed)', 'value': 'cose'},
                        {'label': 'Circle', 'value': 'circle'},
                        {'label': 'Concentric', 'value': 'concentric'},
                        {'label': 'Grid', 'value': 'grid'},
                        {'label': 'Breadthfirst', 'value': 'breadthfirst'}
                    ],
                    value='cose',
                    style={'marginBottom': '10px'}
                )
            ])
        ], style={'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    ], style={'width': '25%', 'float': 'left', 'padding': '20px'}),

    # Main Content Area
    html.Div([
        # Graph Visualization
        html.Div([
            cyto.Cytoscape(
                id='card-graph',
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '600px'},
                elements=[],
                stylesheet=[
                    # Node styles
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'background-color': '#3498db',
                            'color': '#fff',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'width': '60px',
                            'height': '60px',
                            'border-width': '2px',
                            'border-color': '#2c3e50'
                        }
                    },
                    # Commander node style
                    {
                        'selector': 'node[type="commander"]',
                        'style': {
                            'background-color': '#e74c3c',
                            'width': '80px',
                            'height': '80px',
                            'font-size': '14px',
                            'font-weight': 'bold'
                        }
                    },
                    # Edge styles
                    {
                        'selector': 'edge',
                        'style': {
                            'width': 'data(weight)',
                            'line-color': '#95a5a6',
                            'curve-style': 'bezier',
                            'opacity': 0.6
                        }
                    },
                    # Selected node style
                    {
                        'selector': 'node:selected',
                        'style': {
                            'border-width': '4px',
                            'border-color': '#f39c12'
                        }
                    },
                    # Highlighted elements
                    {
                        'selector': '.highlighted',
                        'style': {
                            'opacity': 1,
                            'z-index': 999
                        }
                    },
                    # Dimmed elements
                    {
                        'selector': '.dimmed',
                        'style': {
                            'opacity': 0.2
                        }
                    }
                ]
            )
        ], style={'backgroundColor': '#ffffff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        # Information Panel
        html.Div(id='info-panel',
                style={'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px',
                       'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'minHeight': '200px'})
    ], style={'width': '70%', 'float': 'right', 'padding': '20px'}),

    # Hidden div to store deck data
    dcc.Store(id='deck-data-store'),
    dcc.Store(id='selected-node-store')
], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})


# Callback to load deck from URL
@app.callback(
    [Output('status-message', 'children'),
     Output('deck-selector', 'options'),
     Output('deck-data-store', 'data')],
    Input('load-deck-button', 'n_clicks'),
    State('deck-url-input', 'value'),
    State('deck-data-store', 'data'),
    prevent_initial_call=True
)
def load_deck(n_clicks, url, current_data):
    """Load deck from Archidekt URL and fetch card details from Scryfall"""
    if not url:
        return html.Div("Please enter a deck URL", style={'color': 'red'}), [], current_data

    try:
        # Update status
        status = html.Div("Loading deck...", style={'color': 'blue'})

        # Fetch deck from Archidekt
        deck_info = fetch_deck_from_archidekt(url)

        # Fetch detailed card info from Scryfall
        cards_with_details = fetch_card_details(deck_info['cards'])

        # Create deck object
        deck = Deck(
            deck_id=deck_info['id'],
            name=deck_info['name'],
            cards=cards_with_details
        )

        # Analyze synergies
        deck.synergies = analyze_deck_synergies(cards_with_details)

        # Save deck to file
        deck.save()

        # Update deck list
        deck_files = list(Path('data/decks').glob('*.json'))
        deck_options = [{'label': f.stem, 'value': str(f)} for f in deck_files]

        # Store deck data
        stored_data = current_data or {}
        stored_data[deck.name] = deck.to_dict()

        status = html.Div(f"Successfully loaded deck: {deck.name}", style={'color': 'green'})
        return status, deck_options, stored_data

    except Exception as e:
        return html.Div(f"Error loading deck: {str(e)}", style={'color': 'red'}), [], current_data


# Callback to update graph when deck is selected
@app.callback(
    Output('card-graph', 'elements'),
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def update_graph(deck_file):
    """Update graph visualization when a deck is selected"""
    if not deck_file:
        return []

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        # Build graph elements
        elements = build_graph_elements(deck_data)
        return elements

    except Exception as e:
        print(f"Error updating graph: {e}")
        return []


# Callback to update graph layout
@app.callback(
    Output('card-graph', 'layout'),
    Input('layout-selector', 'value')
)
def update_layout(layout_name):
    """Update graph layout"""
    return {'name': layout_name, 'animate': True}


# Callback for node/edge selection and highlighting
@app.callback(
    [Output('card-graph', 'stylesheet'),
     Output('info-panel', 'children')],
    [Input('card-graph', 'tapNodeData'),
     Input('card-graph', 'tapEdgeData')],
    State('card-graph', 'elements'),
    prevent_initial_call=True
)
def handle_selection(node_data, edge_data, elements):
    """Handle node and edge selection, update highlighting and info panel"""
    ctx = callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    # Base stylesheet
    base_stylesheet = [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'background-color': '#3498db',
                'color': '#fff',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '12px',
                'width': '60px',
                'height': '60px',
                'border-width': '2px',
                'border-color': '#2c3e50'
            }
        },
        {
            'selector': 'node[type="commander"]',
            'style': {
                'background-color': '#e74c3c',
                'width': '80px',
                'height': '80px',
                'font-size': '14px',
                'font-weight': 'bold'
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

    # Handle node selection
    if node_data:
        node_id = node_data['id']

        # Get connected edges
        connected_edges = [e for e in elements if 'source' in e['data'] and
                          (e['data']['source'] == node_id or e['data']['target'] == node_id)]
        connected_node_ids = set()
        for edge in connected_edges:
            connected_node_ids.add(edge['data']['source'])
            connected_node_ids.add(edge['data']['target'])

        # Add highlighting styles
        base_stylesheet.extend([
            {
                'selector': f'node[id="{node_id}"]',
                'style': {
                    'border-width': '4px',
                    'border-color': '#f39c12',
                    'opacity': 1
                }
            },
            {
                'selector': ', '.join([f'node[id="{nid}"]' for nid in connected_node_ids if nid != node_id]),
                'style': {'opacity': 1}
            },
            {
                'selector': ', '.join([f'edge[id="{e["data"]["id"]}"]' for e in connected_edges]),
                'style': {'opacity': 1, 'line-color': '#2ecc71', 'width': 'mapData(weight, 0, 10, 2, 8)'}
            },
            {
                'selector': f'node:not([id="{node_id}"]):not(' + ', '.join([f'[id="{nid}"]' for nid in connected_node_ids if nid != node_id]) + ')',
                'style': {'opacity': 0.2}
            } if connected_node_ids else {},
            {
                'selector': 'edge:not(' + ', '.join([f'[id="{e["data"]["id"]}"]' for e in connected_edges]) + ')',
                'style': {'opacity': 0.1}
            } if connected_edges else {}
        ])

        # Build info panel
        info_panel = html.Div([
            html.H3(node_data.get('label', 'Unknown Card'), style={'color': '#2c3e50'}),
            html.Hr(),
            html.Div([
                html.P([html.Strong("Type: "), node_data.get('card_type', 'N/A')]),
                html.P([html.Strong("Mana Cost: "), node_data.get('mana_cost', 'N/A')]),
                html.P([html.Strong("Colors: "), ', '.join(node_data.get('colors', []))]),
                html.P([html.Strong("Oracle Text: ")]),
                html.P(node_data.get('oracle_text', 'N/A'), style={'fontStyle': 'italic', 'padding': '10px', 'backgroundColor': '#ecf0f1'}),
            ]),
            html.Hr(),
            html.H4(f"Connected Cards ({len(connected_edges)} synergies):", style={'marginTop': '20px'}),
            html.Ul([
                html.Li(f"{e['data'].get('source_label', 'Unknown')} ↔ {e['data'].get('target_label', 'Unknown')} (Strength: {e['data'].get('weight', 0)})")
                for e in connected_edges
            ])
        ])

        return base_stylesheet, info_panel

    # Handle edge selection
    elif edge_data:
        edge_id = edge_data['id']

        # Add highlighting for selected edge
        base_stylesheet.extend([
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
                'selector': f'node:not([id="{edge_data["source}"]):not([id="{edge_data["target"]}"])',
                'style': {'opacity': 0.2}
            },
            {
                'selector': f'edge:not([id="{edge_id}"])',
                'style': {'opacity': 0.1}
            }
        ])

        # Build synergy info panel
        synergies = edge_data.get('synergies', {})

        info_panel = html.Div([
            html.H3(f"Synergy: {edge_data.get('source_label', 'Unknown')} ↔ {edge_data.get('target_label', 'Unknown')}",
                   style={'color': '#2c3e50'}),
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

        return base_stylesheet, info_panel

    return base_stylesheet, html.Div("Click on a card or synergy edge to see details")


if __name__ == '__main__':
    # Ensure data directory exists
    Path('data/decks').mkdir(parents=True, exist_ok=True)

    # Run the app
    app.run_server(debug=True, host='0.0.0.0', port=8050)
