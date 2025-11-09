import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from run_simulation import run_simulations
from simulate_game import Card, clean_produces_colors
import ast


def parse_etb_tapped_conditions(value):
    try:
        if not value or str(value).strip().lower() in ("", "nan", "none"):
            return {}
        return ast.literal_eval(value)
    except Exception:
        return {}


def load_deck(csv_path):
    df = pd.read_csv(csv_path)
    df["ETBTappedConditions"] = df["ETBTappedConditions"].apply(parse_etb_tapped_conditions)
    cards = []
    commander = None
    for _, row in df.iterrows():
        c = Card(
            name=row["Name"],
            type=row["Type"],
            mana_cost=row["ManaCost"],
            power=row["Power"],
            toughness=row["Toughness"],
            produces_colors=clean_produces_colors(row["ProducesColors"]),
            etb_tapped=str(row.get("ETBTapped", "")).lower() in ("true", "yes", "1"),
            etb_tapped_conditions=row.get("ETBTappedConditions", {}),
            mana_production=row["ManaProduction"],
            has_haste=row.get("HasHaste", False),
            has_flash=(
                (str(row.get("HasFlash", "")).lower() in ("true", "yes", "1"))
                or ("HasFlash" in row and bool(row.get("HasFlash", False)))
                or "flash" in str(row.get("OracleText", "")).lower()
            ),
            equip_cost=row.get("EquipCost", ""),
            power_buff=row.get("PowerBuff", 0),
            is_commander=str(row.get("Commander", "")).lower() in ("true", "yes"),
            oracle_text=row.get("OracleText", ""),
        )
        if c.is_commander:
            commander = c
        else:
            cards.append(c)
    return cards, commander


# Paths to two decks to compare
DECK1 = "deck.csv"
DECK2 = "deck2.csv"

def prepare_deck_results(deck_path):
    cards, commander = load_deck(deck_path)
    summary, dist, _ = run_simulations(cards, commander, num_games=500, max_turns=10)
    return summary, dist


summary1, dist1 = prepare_deck_results(DECK1)
summary2, dist2 = prepare_deck_results(DECK2)

# Combine summaries for plotting
metrics = ["Avg Lands in Play", "Avg Total Mana", "Avg Unspent Mana", "Avg Cards Played"]
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

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1("Deck Comparison Dashboard"),
        dcc.Graph(figure=fig_line),
        dcc.Graph(figure=fig_bar),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
