import pandas as pd
from deck_loader import _df_to_cards


def test_df_to_cards_etb_conditions_parsing():
    df = pd.DataFrame([
        {
            "Name": "Tapped Land",
            "Type": "Land",
            "ManaCost": "",
            "ETBTapped": True,
            "ETBTappedConditions": "{'control': ['Forest']}",
            "Commander": False,
        },
        {
            "Name": "NoCond Land",
            "Type": "Land",
            "ManaCost": "",
            "ETBTapped": True,
            "ETBTappedConditions": float('nan'),
            "Commander": False,
        },
        {
            "Name": "Boss",
            "Type": "Commander",
            "ManaCost": "2G",
            "Commander": True,
        },
    ])

    cards, commander, names = _df_to_cards(df)

    assert len(cards) == 2
    assert commander.name == "Boss"
    assert cards[0].etb_tapped_conditions == {"control": ["Forest"]}
    assert cards[1].etb_tapped_conditions == {}


def test_df_to_cards_has_flash_parsing():
    df = pd.DataFrame([
        {
            "Name": "Ambush Viper",
            "Type": "Creature",
            "ManaCost": "1G",
            "OracleText": "Flash",
        }
    ])

    cards, commander, names = _df_to_cards(df)

    assert len(cards) == 1
    assert cards[0].has_flash is True
