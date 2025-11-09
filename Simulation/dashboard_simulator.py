# Assuming we have summary and commander_turn_dist from the run_simulations function for a chosen deck
from __future__ import annotations

import argparse
import os

import dash
from dash import dcc, html, dash_table
import plotly.express as px
from simulate_game import Card, simulate_game, clean_produces_colors
from run_simulation import run_simulations
from deck_loader import (
    load_deck_from_csv,
    load_deck_from_scryfall,
    load_deck_from_scryfall_file,
    load_deck_from_archidekt,
)
import pandas as pd
import plotly.graph_objects as go
import numpy as np


def create_dashboard_app(archidekt_id: int | None = None) -> dash.Dash:
    """Create the Dash dashboard application.

    Parameters
    ----------
    archidekt_id: int | None
        Optional Archidekt deck ID.  If provided, the deck is loaded from
        Archidekt.  Otherwise the local ``cards.txt`` file is used.
    """

    if archidekt_id:
        cards, commander, deck_names = load_deck_from_archidekt(archidekt_id)
    else:
        # Default deck from local file
        cards, commander, deck_names = load_deck_from_scryfall_file(
            "cards.txt",
            "Sonic the Hedgehog",
        )

    summary, commander_turn_dist, creature_power_avg = run_simulations(
        cards, commander, num_games=1000, max_turns=10, log_dir="logs", verbose=True
    )

    app = dash.Dash(__name__)
    colours = ["W", "U", "B", "R", "G", "C", "Any"]

    # Prepare figures using Plotly Express or Graph Objects
    # Line chart for turn-by-turn average metrics (let's plot Lands, Total Mana, Unspent Mana as examples)
    fig_line = px.line(
        summary,
        x="Turn",
        y=[
            "Avg Lands in Play",
            "Avg Lands ETB Tapped",
            "Avg Total Mana",
            "Avg Unspent Mana",
            "Avg Cards Played",
            "Avg Total Power",
            "Avg Total Toughness",
        ],
        markers=True,
        labels={"value": "Amount", "Turn": "Turn"},
        title="Average Lands, Total Mana, and Unspent Mana by Turn",
    )

    # Additional figures for hand size and unplayable cards
    fig_hand = px.line(
        summary,
        x="Turn",
        y="Avg Hand Size",
        markers=True,
        labels={"Avg Hand Size": "Hand Size", "Turn": "Turn"},
        title="Average Hand Size by Turn",
    )

    summary["% Unplayable"] = (
        summary["Avg Unplayable Cards"] / summary["Avg Hand Size"] * 100
    ).round(2)

    fig_unplayable = go.Figure()
    fig_unplayable.add_bar(
        x=summary["Turn"], y=summary["% Unplayable"], name="% Unplayable"
    )
    fig_unplayable.add_scatter(
        x=summary["Turn"], y=summary["% Unplayable"], mode="lines+markers", name="Trend"
    )
    fig_unplayable.update_layout(
        title="Percentage of Unplayable Cards", xaxis_title="Turn", yaxis_title="% of Hand"
    )

    board_cols = {f"Board Mana {c}": c for c in colours}
    hand_cols = {f"Hand Mana {c}": c for c in colours}

    fig_board_mana = px.line(
        summary.rename(columns=board_cols),
        x="Turn",
        y=list(board_cols.values()),
        markers=True,
        labels={"value": "Mana Sources", "Turn": "Turn"},
        title="Mana Available on Board by Color",
    )

    fig_hand_mana = px.line(
        summary.rename(columns=hand_cols),
        x="Turn",
        y=list(hand_cols.values()),
        markers=True,
        labels={"value": "Lands in Hand", "Turn": "Turn"},
        title="Mana Available in Hand by Color",
    )

    # Prepare the bar data (commander_turn_dist is a pandas Series)
    dist_df = commander_turn_dist.reset_index()
    dist_df.columns = ["Turn", "Count"]

    # Compute the cumulative sum and cumulative percentage
    dist_df["Cumulative Count"] = dist_df["Count"].cumsum()
    total_games = dist_df["Count"].sum()
    dist_df["Cumulative %"] = (
        dist_df["Cumulative Count"] / total_games * 100
    ).round(2)

    # Create a bar + line combination using plotly.graph_objects
    fig_bar = go.Figure()

    # Bar chart for counts
    fig_bar.add_trace(
        go.Bar(
            x=dist_df["Turn"],
            y=dist_df["Count"],
            name="Number of Games",
            marker_color="rgba(66,135,245,0.8)",
        )
    )

    # Line chart for cumulative %
    fig_bar.add_trace(
        go.Scatter(
            x=dist_df["Turn"],
            y=dist_df["Cumulative %"],
            name="Cumulative %",
            yaxis="y2",
            mode="lines+markers",
            marker=dict(color="red"),
            line=dict(width=3),
        )
    )

    # Add secondary y-axis for cumulative percentage
    fig_bar.update_layout(
        title="Distribution and Cumulative % of Commander Cast Turn",
        xaxis_title="Turn",
        yaxis=dict(title="Number of Games"),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
        ),
        legend=dict(x=0.7, y=1.1, orientation="h"),
        bargap=0.1,
        template="plotly_white",
    )

    # Summary table (we'll show a few columns from summary)
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in summary.columns],
        data=summary.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"padding": "5px", "textAlign": "center"},
    )

    # Table showing average total power per creature
    creature_power_df = (
        pd.DataFrame(
            [{"Creature": k, "Avg Power": v} for k, v in creature_power_avg.items()]
        ).sort_values("Avg Power", ascending=False)
        if creature_power_avg
        else pd.DataFrame(columns=["Creature", "Avg Power"])
    )
    power_table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in creature_power_df.columns],
        data=creature_power_df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"padding": "5px", "textAlign": "center"},
    )

    deck_cards_table = dash_table.DataTable(
        columns=[{"name": "Card Name", "id": "name"}],
        data=[{"name": card.name} for card in cards],
        style_table={"overflowX": "auto"},
        style_cell={"padding": "5px", "textAlign": "center"},
    )

    # Layout of the app
    app.layout = html.Div(
        children=[
            html.H1("Commander Deck Simulation Dashboard"),
            html.Div(
                [
                    html.Label("Select Deck:"),
                    dcc.Dropdown(
                        id="deck-select",
                        options=[
                            {"label": "Deck 1 - Limit Break", "value": "deck1"},
                            # {'label': 'Deck 2 - Elves', 'value': 'deck2'},
                            # ... additional deck options
                        ],
                        value="deck1",
                    ),
                ],
                style={"width": "300px", "margin-bottom": "20px"},
            ),
            html.Div(
                [
                    dcc.Graph(
                        id="metrics-line-chart",
                        figure=fig_line,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    dcc.Graph(
                        id="hand-size-chart",
                        figure=fig_hand,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                ]
            ),
            html.Div(
                [
                    dcc.Graph(
                        id="unplayable-chart",
                        figure=fig_unplayable,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    dcc.Graph(
                        id="commander-dist-chart",
                        figure=fig_bar,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                ]
            ),
            html.Div(
                [
                    dcc.Graph(
                        id="board-mana-chart",
                        figure=fig_board_mana,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    dcc.Graph(
                        id="hand-mana-chart",
                        figure=fig_hand_mana,
                        style={"width": "48%", "display": "inline-block"},
                    ),
                ]
            ),
            html.H3("Turn-by-Turn Averages:"),
            table,
            html.H3("Average Creature Power"),
            power_table,
            html.H3("Deck Card Names"),
            deck_cards_table,
            # html.Div([html.Span(name, style={"margin-right": "10px"}) for name in deck_names],
            #  style={"margin-top": "20px", "display": "flex", "flex-wrap": "wrap"}),
        ]
    )

    return app


# Create default app for WSGI servers
_archidekt_id = int(os.environ.get("ARCHIDEKT_ID", "0")) or None
app = create_dashboard_app(_archidekt_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archidekt-id",
        type=int,
        help="Load deck data from the given Archidekt deck ID",
    )
    args = parser.parse_args()

    app = create_dashboard_app(args.archidekt_id)
    app.run(debug=True)


# We would also add callbacks to update figures and table when a new deck is selected.
# For brevity, the callback functions are not shown here.
# Essentially, on deck-select change, we would load the corresponding deck, run simulations (or fetch precomputed results),
# then update the fig_line, fig_bar, and table data accordingly.
