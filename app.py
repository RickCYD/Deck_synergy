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
from src.utils.card_rankings import (
    calculate_weighted_degree_centrality,
    get_deck_rankings_summary
)

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "MTG Commander Synergy Visualizer"

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
                    options=initial_deck_options,
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
            ], style={'marginBottom': '20px'}),

            # Card Rankings Panel
            html.Div([
                html.Label("Top Cards (by Synergy):", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Button('View Top Cards in Graph', id='view-top-cards-button', n_clicks=0,
                           style={'width': '100%', 'padding': '8px', 'backgroundColor': '#2ecc71',
                                  'color': 'white', 'border': 'none', 'cursor': 'pointer',
                                  'fontSize': '14px', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(id='card-rankings-panel', style={'maxHeight': '400px', 'overflowY': 'auto'})
            ], id='rankings-container', style={'display': 'none'})
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
                    # Node styles - Perfect square nodes with card art and color-coded borders
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'shape': 'rectangle',
                            'background-color': 'data(color_code)',  # Fallback color
                            'background-image': 'data(art_crop_url)',  # Just the artwork, not full card
                            'background-fit': 'cover',
                            'background-clip': 'node',
                            'color': '#fff',
                            'text-valign': 'bottom',  # Position label at bottom
                            'text-halign': 'center',
                            'text-background-color': '#000',
                            'text-background-opacity': 0.7,
                            'text-background-padding': '3px',
                            'font-size': '10px',
                            'width': '90px',  # Perfect square
                            'height': '90px',  # Same as width
                            'border-width': '4px',
                            'border-color': 'data(border_color)',  # MTG color border
                            'border-style': 'solid',
                            'text-outline-width': '1px',
                            'text-outline-color': '#000'
                        }
                    },
                    # Multi-color cards - split border effect using outline
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
                    # Commander node style - Larger perfect square with thick border
                    {
                        'selector': 'node[type="commander"]',
                        'style': {
                            'background-color': 'data(color_code)',
                            'background-image': 'data(art_crop_url)',  # Just the artwork
                            'background-fit': 'cover',
                            'background-clip': 'node',
                            'width': '110px',  # Perfect square
                            'height': '110px',  # Same as width
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'border-width': '5px',
                            'border-color': 'data(border_color)'
                        }
                    },
                    # Commander multi-color - split border
                    {
                        'selector': 'node[type="commander"][is_multicolor]',
                        'style': {
                            'border-width': '4px',
                            'outline-width': '4px',
                            'outline-color': 'data(secondary_border)'
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
    dcc.Store(id='selected-node-store'),
    dcc.Store(id='current-deck-file-store')
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
     Output('current-deck-file-store', 'data')],
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def update_graph(deck_file):
    """Update graph visualization when a deck is selected"""
    if not deck_file:
        return [], None

    try:
        # Load deck data
        with open(deck_file, 'r') as f:
            deck_data = json.load(f)

        # Build graph elements
        elements = build_graph_elements(deck_data)
        return elements, deck_file

    except Exception as e:
        print(f"Error updating graph: {e}")
        return [], None


# Callback to update card rankings when deck is selected
@app.callback(
    [Output('card-rankings-panel', 'children'),
     Output('rankings-container', 'style')],
    Input('deck-selector', 'value'),
    prevent_initial_call=True
)
def update_card_rankings(deck_file):
    """Calculate and display card rankings when a deck is selected"""
    if not deck_file:
        return [], {'display': 'none'}

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

        return rankings_items, {'display': 'block', 'marginTop': '20px'}

    except Exception as e:
        print(f"Error calculating rankings: {e}")
        return [html.Div(f"Error: {str(e)}", style={'color': 'red'})], {'display': 'block'}


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
     Input('card-graph', 'tapEdgeData')],
    State('card-graph', 'elements'),
    prevent_initial_call=True
)
def handle_selection(node_data, edge_data, elements):
    """Handle node and edge selection, update highlighting and info panel"""
    ctx = callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    # Base stylesheet - Perfect square nodes with card art and color borders
    base_stylesheet = [
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
                'width': '90px',  # Perfect square
                'height': '90px',  # Same as width
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
                'width': '110px',  # Perfect square
                'height': '110px',  # Same as width
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

    # Handle node selection
    if node_data:
        node_id = node_data['id']
        print(f"Node clicked: {node_id}")

        # Get connected edges
        connected_edges = [e for e in elements if 'source' in e['data'] and
                          (e['data']['source'] == node_id or e['data']['target'] == node_id)]
        connected_node_ids = set()
        for edge in connected_edges:
            connected_node_ids.add(edge['data']['source'])
            connected_node_ids.add(edge['data']['target'])

        print(f"Connected edges: {len(connected_edges)}")
        print(f"Connected nodes: {connected_node_ids}")

        # Strategy: First dim everything, then brighten what we want to show
        # This avoids complex :not() selectors

        # Dim all nodes and edges first
        base_stylesheet.extend([
            {
                'selector': 'node',
                'style': {'opacity': 0.2}
            },
            {
                'selector': 'edge',
                'style': {'opacity': 0.1}
            }
        ])

        # Highlight the selected node with special styling
        base_stylesheet.append({
            'selector': f'node[id="{node_id}"]',
            'style': {
                'border-width': '4px',
                'border-color': '#f39c12',
                'opacity': 1
            }
        })

        # Highlight connected nodes
        connected_others = [nid for nid in connected_node_ids if nid != node_id]
        if connected_others:
            base_stylesheet.append({
                'selector': ', '.join([f'node[id="{nid}"]' for nid in connected_others]),
                'style': {'opacity': 1}
            })

        # Highlight connected edges
        if connected_edges:
            base_stylesheet.append({
                'selector': ', '.join([f'edge[id="{e["data"]["id"]}"]' for e in connected_edges]),
                'style': {'opacity': 1, 'line-color': '#2ecc71', 'width': 'mapData(weight, 0, 10, 2, 8)'}
            })

        # Build info panel with expandable synergy details
        synergy_items = []
        for e in connected_edges:
            edge_data_details = e['data']
            source_label = edge_data_details.get('source_label', 'Unknown')
            target_label = edge_data_details.get('target_label', 'Unknown')
            weight = edge_data_details.get('weight', 0)
            synergies = edge_data_details.get('synergies', {})

            # Determine the other card name (not the selected one)
            other_card = target_label if source_label == node_id else source_label

            # Build synergy details for this edge
            synergy_details = []
            for category, synergy_list in synergies.items():
                if synergy_list:
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

            # Create collapsible section using details/summary
            synergy_items.append(
                html.Details([
                    html.Summary([
                        html.Strong(f"↔ {other_card}"),
                        html.Span(f" (Strength: {weight:.2f})", style={'color': '#7f8c8d'})
                    ], style={'cursor': 'pointer', 'padding': '8px', 'backgroundColor': '#ecf0f1', 'borderRadius': '4px', 'marginBottom': '5px'}),
                    html.Div(synergy_details if synergy_details else [html.P("No detailed synergies available", style={'fontStyle': 'italic', 'color': '#95a5a6'})],
                            style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderLeft': '3px solid #3498db', 'marginBottom': '10px'})
                ], style={'marginBottom': '10px'})
            )

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
            html.H4(f"Synergies ({len(connected_edges)} connections):", style={'marginTop': '20px'}),
            html.Div(synergy_items if synergy_items else [html.P("No synergies found", style={'fontStyle': 'italic', 'color': '#95a5a6'})])
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
                'selector': f'node:not([id="{edge_data["source"]}"]):not([id="{edge_data["target"]}"])',
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
