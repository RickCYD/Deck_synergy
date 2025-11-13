#!/usr/bin/env python3
"""
Build a local card database from existing test files and CSV data.
This helps when Scryfall API is blocked.
"""

import json
import pandas as pd
import os

def build_card_database():
    """Extract all card data from existing CSV files and test data."""
    card_db = {}

    # Load from existing CSV files
    csv_files = [
        "Simulation/deck.csv",
        "Simulation/deck2.csv",
        "Simulation/deck_examples.csv",
    ]

    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"Loading {csv_file}...")
            try:
                df = pd.read_csv(csv_file)
                for _, row in df.iterrows():
                    name = row.get('Name', '')
                    if name and name not in card_db:
                        card_db[name] = {
                            'Name': name,
                            'Type': row.get('Type', ''),
                            'ManaCost': row.get('ManaCost', ''),
                            'Power': row.get('Power', 0),
                            'Toughness': row.get('Toughness', 0),
                            'ManaProduction': row.get('ManaProduction', 0),
                            'ProducesColors': row.get('ProducesColors', ''),
                            'HasHaste': row.get('HasHaste', False),
                            'HasFlash': row.get('HasFlash', False),
                            'ETBTapped': row.get('ETBTapped', False),
                            'ETBTappedConditions': row.get('ETBTappedConditions', '{}'),
                            'EquipCost': row.get('EquipCost', ''),
                            'PowerBuff': row.get('PowerBuff', 0),
                            'DrawCards': row.get('DrawCards', 0),
                            'PutsLand': row.get('PutsLand', False),
                            'OracleText': row.get('OracleText', ''),
                            'DeathTriggerValue': row.get('DeathTriggerValue', None),
                            'SacrificeOutlet': row.get('SacrificeOutlet', None),
                            'Commander': row.get('Commander', False),
                        }
                        print(f"  Added: {name}")
            except Exception as e:
                print(f"  Error loading {csv_file}: {e}")

    # Add common token-strategy cards manually
    token_cards = {
        'Jetmir, Nexus of Revels': {
            'Type': 'Legendary Creature',
            'ManaCost': '{1}{R}{G}{W}',
            'Power': 5,
            'Toughness': 4,
            'OracleText': 'Creatures you control get +1/+0 and vigilance as long as you control three or more creatures. Creatures you control also get +1/+0 and trample as long as you control six or more creatures. Creatures you control also get +1/+0 and double strike as long as you control nine or more creatures.',
        },
        'Anointed Procession': {
            'Type': 'Enchantment',
            'ManaCost': '{3}{W}',
            'OracleText': 'If an effect would create one or more tokens under your control, it creates twice that many of those tokens instead.',
        },
        'Doubling Season': {
            'Type': 'Enchantment',
            'ManaCost': '{4}{G}',
            'OracleText': 'If an effect would create one or more tokens under your control, it creates twice that many of those tokens instead. If an effect would put one or more counters on a permanent you control, it puts twice that many of those counters on that permanent instead.',
        },
        'Parallel Lives': {
            'Type': 'Enchantment',
            'ManaCost': '{3}{G}',
            'OracleText': 'If an effect would create one or more tokens under your control, it creates twice that many of those tokens instead.',
        },
        'Avenger of Zendikar': {
            'Type': 'Creature',
            'ManaCost': '{5}{G}{G}',
            'Power': 5,
            'Toughness': 5,
            'OracleText': 'When Avenger of Zendikar enters the battlefield, create a 0/1 green Plant creature token for each land you control. Landfall — Whenever a land enters the battlefield under your control, you may put a +1/+1 counter on each Plant creature you control.',
        },
        'Craterhoof Behemoth': {
            'Type': 'Creature',
            'ManaCost': '{5}{G}{G}{G}',
            'Power': 5,
            'Toughness': 5,
            'OracleText': 'Haste. When Craterhoof Behemoth enters the battlefield, creatures you control gain trample and get +X/+X until end of turn, where X is the number of creatures you control.',
        },
    }

    for name, data in token_cards.items():
        if name not in card_db:
            card_db[name] = {
                'Name': name,
                'Type': data.get('Type', ''),
                'ManaCost': data.get('ManaCost', ''),
                'Power': data.get('Power', 0),
                'Toughness': data.get('Toughness', 0),
                'OracleText': data.get('OracleText', ''),
                'ManaProduction': 0,
                'ProducesColors': '',
                'HasHaste': 'haste' in data.get('OracleText', '').lower() or 'Haste' in data.get('OracleText', ''),
                'HasFlash': False,
                'ETBTapped': False,
                'ETBTappedConditions': '{}',
                'EquipCost': '',
                'PowerBuff': 0,
                'DrawCards': 0,
                'PutsLand': False,
                'DeathTriggerValue': None,
                'SacrificeOutlet': None,
                'Commander': False,
            }
            print(f"  Added token card: {name}")

    print(f"\nTotal cards in database: {len(card_db)}")

    # Save to cache file
    cache_file = "local_card_cache.json"
    with open(cache_file, 'w') as f:
        json.dump(card_db, f, indent=2)

    print(f"Saved to {cache_file}")

    return card_db

if __name__ == "__main__":
    build_card_database()
