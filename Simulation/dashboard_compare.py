import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from run_simulation import run_simulations
from deck_loader import load_deck_from_csv


def load_deck(path):
    # Utility wrapper to keep previous signature
    cards, commander, names = load_deck_from_csv(path)
    return cards, commander, names


# Paths to two decks to compare
DECK1 = "deck.csv"
DECK2 = "deck2.csv"

def prepare_deck_results(deck_path):
    cards, commander, names = load_deck(deck_path)
    summary, dist, _, _ = run_simulations(cards, commander, num_games=500, max_turns=10)
    return summary, dist, names


summary1, dist1, deck1_names = prepare_deck_results(DECK1)
summary2, dist2, deck2_names = prepare_deck_results(DECK2)

# Combine summaries for plotting
metrics = [
    "Avg Lands in Play",
    "Avg Lands ETB Tapped",
    "Avg Total Mana",
    "Avg Unspent Mana",
    "Avg Cards Played",
]
long1 = summary1.melt(id_vars="Turn", value_vars=metrics, var_name="Metric", value_name="Value")
long1["Deck"] = "Deck 1"
long2 = summary2.melt(id_vars="Turn", value_vars=metrics, var_name="Metric", value_name="Value")
long2["Deck"] = "Deck 2"
long_df = pd.concat([long1, long2])

fig_line = px.line(
    long_df,
    x="Turn",
    y="Value",
    color="Deck",
    facet_col="Metric",
    facet_col_wrap=2,
    markers=True,
    title="Deck Comparison - Turn Metrics",
)
fig_line.update_layout(height=600)

# Commander cast distribution comparison
bar_df1 = dist1.reset_index()
bar_df1.columns = ["Turn", "Count"]
bar_df1["Deck"] = "Deck 1"
bar_df2 = dist2.reset_index()
bar_df2.columns = ["Turn", "Count"]
bar_df2["Deck"] = "Deck 2"
bar_df = pd.concat([bar_df1, bar_df2])

fig_bar = px.bar(
    bar_df,
    x="Turn",
    y="Count",
    color="Deck",
    barmode="group",
    title="Commander Cast Turn Distribution",
)

colours = ["W", "U", "B", "R", "G", "C", "Any"]
board_cols = {f"Board Mana {c}": c for c in colours}
hand_cols = {f"Hand Mana {c}": c for c in colours}

board1 = summary1.melt(id_vars="Turn", value_vars=list(board_cols.keys()), var_name="Color", value_name="Value")
board1["Deck"] = "Deck 1"
board1["Color"] = board1["Color"].str.replace("Board Mana ", "")
board2 = summary2.melt(id_vars="Turn", value_vars=list(board_cols.keys()), var_name="Color", value_name="Value")
board2["Deck"] = "Deck 2"
board2["Color"] = board2["Color"].str.replace("Board Mana ", "")
board_df = pd.concat([board1, board2])

hand1 = summary1.melt(id_vars="Turn", value_vars=list(hand_cols.keys()), var_name="Color", value_name="Value")
hand1["Deck"] = "Deck 1"
hand1["Color"] = hand1["Color"].str.replace("Hand Mana ", "")
hand2 = summary2.melt(id_vars="Turn", value_vars=list(hand_cols.keys()), var_name="Color", value_name="Value")
hand2["Deck"] = "Deck 2"
hand2["Color"] = hand2["Color"].str.replace("Hand Mana ", "")
hand_df = pd.concat([hand1, hand2])

fig_board_mana = px.line(
    board_df,
    x="Turn",
    y="Value",
    color="Deck",
    facet_col="Color",
    facet_col_wrap=3,
    title="Mana Available on Board by Color",
    markers=True,
)

fig_hand_mana = px.line(
    hand_df,
    x="Turn",
    y="Value",
    color="Deck",
    facet_col="Color",
    facet_col_wrap=3,
    title="Mana Available in Hand by Color",
    markers=True,
)

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1("Deck Comparison Dashboard"),
        dcc.Graph(figure=fig_line),
        dcc.Graph(figure=fig_bar),
        dcc.Graph(figure=fig_board_mana),
        dcc.Graph(figure=fig_hand_mana),
        html.Div(
            [
                html.Div(
                    [html.H4("Deck 1"), html.Ul([html.Li(n) for n in deck1_names])],
                    style={"width": "45%", "display": "inline-block", "vertical-align": "top"},
                ),
                html.Div(
                    [html.H4("Deck 2"), html.Ul([html.Li(n) for n in deck2_names])],
                    style={"width": "45%", "display": "inline-block", "vertical-align": "top"},
                ),
            ],
            style={"display": "flex", "justify-content": "space-between"},
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
