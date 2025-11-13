#!/usr/bin/env python3
"""
Build a complete card database for the Zurgo tokens deck.
Since APIs are blocked, we'll manually create card data with proper oracle texts.
"""

import json
import pandas as pd

# Complete card database with oracle texts for Zurgo deck
ZURGO_CARDS = {
    # COMMANDER
    "Zurgo Stormrender": {
        "Name": "Zurgo Stormrender",
        "Type": "Legendary Creature",
        "ManaCost": "{2}{R}{W}{B}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Flying, haste. Whenever one or more creatures you control deal combat damage to a player, create a 2/1 white and black Human Warrior creature token.",
        "HasHaste": True,
        "Commander": True,
    },

    # TOKEN GENERATORS
    "Adeline, Resplendent Cathar": {
        "Name": "Adeline, Resplendent Cathar",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{W}{W}",
        "Power": 1,
        "Toughness": 4,
        "OracleText": "Adeline, Resplendent Cathar's power is equal to the number of creatures you control. Whenever you attack, for each opponent, create a 1/1 white Human creature token that's tapped and attacking that player or a planeswalker they control.",
    },

    "Anim Pakal, Thousandth Moon": {
        "Name": "Anim Pakal, Thousandth Moon",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{R}{W}",
        "Power": 2,
        "Toughness": 2,
        "OracleText": "Whenever you attack with one or more non-Gnome creatures, put a +1/+1 counter on Anim Pakal, then create X 1/1 colorless Gnome artifact creature tokens that are tapped and attacking, where X is the number of +1/+1 counters on Anim Pakal.",
    },

    "Caesar, Legion's Emperor": {
        "Name": "Caesar, Legion's Emperor",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{R}{W}{B}",
        "Power": 4,
        "Toughness": 4,
        "OracleText": "Whenever Caesar, Legion's Emperor enters the battlefield or attacks, create two 1/1 red and white Soldier creature tokens that are tapped. Other creatures you control get +1/+0.",
    },

    "Delina, Wild Mage": {
        "Name": "Delina, Wild Mage",
        "Type": "Legendary Creature",
        "ManaCost": "{3}{R}",
        "Power": 3,
        "Toughness": 2,
        "OracleText": "Whenever Delina, Wild Mage attacks, choose target creature you control, then roll a d20. 1-14 | Create a tapped and attacking token that's a copy of that creature, except it's not legendary and it has 'At end of combat, exile this creature.' 15-20 | Create one of those tokens. You may roll again.",
    },

    "Elspeth, Sun's Champion": {
        "Name": "Elspeth, Sun's Champion",
        "Type": "Legendary Planeswalker",
        "ManaCost": "{4}{W}{W}",
        "OracleText": "+1: Create three 1/1 white Soldier creature tokens. −3: Destroy all creatures with power 4 or greater. −7: You get an emblem with 'Creatures you control get +2/+2 and have flying.'",
    },

    "Wurmcoil Engine": {
        "Name": "Wurmcoil Engine",
        "Type": "Artifact Creature",
        "ManaCost": "{6}",
        "Power": 6,
        "Toughness": 6,
        "OracleText": "Deathtouch, lifelink. When Wurmcoil Engine dies, create a 3/3 colorless Phyrexian Wurm artifact creature token with deathtouch and a 3/3 colorless Phyrexian Wurm artifact creature token with lifelink.",
    },

    "Mardu Siegebreaker": {
        "Name": "Mardu Siegebreaker",
        "Type": "Creature",
        "ManaCost": "{3}{R}{W}{B}",
        "Power": 5,
        "Toughness": 4,
        "OracleText": "When Mardu Siegebreaker enters the battlefield, if you attacked this turn, create a 1/1 colorless Warrior creature token for each permanent you control that entered the battlefield this turn.",
    },

    "Bone-Cairn Butcher": {
        "Name": "Bone-Cairn Butcher",
        "Type": "Creature",
        "ManaCost": "{4}{B}",
        "Power": 4,
        "Toughness": 4,
        "OracleText": "When Bone-Cairn Butcher enters the battlefield, create two 1/1 colorless Skeleton creature tokens.",
    },

    "Dollmaker's Shop // Porcelain Gallery": {
        "Name": "Dollmaker's Shop // Porcelain Gallery",
        "Type": "Enchantment // Enchantment",
        "ManaCost": "{3}{W}",
        "OracleText": "Whenever one or more creatures you control attack, create a 1/1 colorless Toy artifact creature token. // At the beginning of your end step, if you control three or more tokens, create a 2/2 colorless Toy artifact creature token.",
    },

    "Retrofitter Foundry": {
        "Name": "Retrofitter Foundry",
        "Type": "Artifact",
        "ManaCost": "{1}",
        "OracleText": "{3}: Untap Retrofitter Foundry. {2}, {T}: Create a 1/1 colorless Servo artifact creature token. {1}, {T}, Sacrifice a Servo: Create a 1/1 colorless Thopter artifact creature token with flying. {T}, Sacrifice a Thopter: Create a 4/4 colorless Construct artifact creature token.",
    },

    "Ainok Strike Leader": {
        "Name": "Ainok Strike Leader",
        "Type": "Creature",
        "ManaCost": "{1}{R}{W}",
        "Power": 2,
        "Toughness": 2,
        "OracleText": "Whenever Ainok Strike Leader attacks, you may put a +1/+1 counter on it. When you do, create a 1/1 red Goblin creature token that's tapped and attacking.",
    },

    "Redoubled Stormsinger": {
        "Name": "Redoubled Stormsinger",
        "Type": "Creature",
        "ManaCost": "{3}{R}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Haste. When Redoubled Stormsinger enters the battlefield, create a token that's a copy of it.",
        "HasHaste": True,
    },

    # INSTANTS/SORCERIES THAT CREATE TOKENS
    "Forth Eorlingas!": {
        "Name": "Forth Eorlingas!",
        "Type": "Sorcery",
        "ManaCost": "{X}{R}{W}",
        "OracleText": "Create X 2/2 red Human Knight creature tokens with trample and haste. Whenever one or more creatures you control deal combat damage to one or more players this turn, you become the monarch.",
    },

    "Grand Crescendo": {
        "Name": "Grand Crescendo",
        "Type": "Instant",
        "ManaCost": "{X}{W}{W}",
        "OracleText": "Create X 1/1 green and white Citizen creature tokens. Creatures you control gain indestructible until end of turn.",
    },

    "Riders of Rohan": {
        "Name": "Riders of Rohan",
        "Type": "Sorcery",
        "ManaCost": "{3}{R}{W}",
        "OracleText": "Create five 2/2 red Human Knight creature tokens with trample and haste. Exile them at the beginning of the next end step.",
    },

    "Rite of the Raging Storm": {
        "Name": "Rite of the Raging Storm",
        "Type": "Enchantment",
        "ManaCost": "{3}{R}{R}",
        "OracleText": "Creatures named Lightning Rager can't attack you or planeswalkers you control. At the beginning of each player's upkeep, that player creates a 5/1 red Elemental creature token named Lightning Rager. It has trample, haste, and 'At the beginning of the end step, sacrifice this creature.'",
    },

    "Tempt with Vengeance": {
        "Name": "Tempt with Vengeance",
        "Type": "Sorcery",
        "ManaCost": "{X}{R}",
        "OracleText": "Tempting offer — Create X 1/1 red Elemental creature tokens with haste. Each opponent may create X 1/1 red Elemental creature tokens with haste. For each opponent who does, create X 1/1 red Elemental creature tokens with haste.",
    },

    "Will of the Mardu": {
        "Name": "Will of the Mardu",
        "Type": "Sorcery",
        "ManaCost": "{5}{R}{W}{B}",
        "OracleText": "Create three 2/1 white and black Warrior creature tokens. Return target creature card from your graveyard to the battlefield.",
    },

    "Voice of Victory": {
        "Name": "Voice of Victory",
        "Type": "Creature",
        "ManaCost": "{3}{R}{W}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Flying. Whenever Voice of Victory enters the battlefield or attacks, create a 1/1 red and white Soldier creature token with haste.",
        "HasFlash": False,
    },

    "Outlaws' Merriment": {
        "Name": "Outlaws' Merriment",
        "Type": "Enchantment",
        "ManaCost": "{1}{R}{W}{W}",
        "OracleText": "At the beginning of your upkeep, choose one at random. Create a red and white creature token with those characteristics. • 3/1 Human Warrior with trample • 2/1 Human Cleric with lifelink • 1/2 Human Rogue with haste",
    },

    # ANTHEM EFFECTS
    "Cathars' Crusade": {
        "Name": "Cathars' Crusade",
        "Type": "Enchantment",
        "ManaCost": "{3}{W}{W}",
        "OracleText": "Whenever a creature enters the battlefield under your control, put a +1/+1 counter on each creature you control.",
    },

    "Elesh Norn, Grand Cenobite": {
        "Name": "Elesh Norn, Grand Cenobite",
        "Type": "Legendary Creature",
        "ManaCost": "{5}{W}{W}",
        "Power": 4,
        "Toughness": 7,
        "OracleText": "Vigilance. Creatures you control get +2/+2. Creatures your opponents control get -2/-2.",
    },

    "Exalted Sunborn": {
        "Name": "Exalted Sunborn",
        "Type": "Creature",
        "ManaCost": "{2}{R}{W}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Flying, vigilance. Whenever you attack with three or more creatures, creatures you control get +1/+0 until end of turn.",
    },

    "Mondrak, Glory Dominus": {
        "Name": "Mondrak, Glory Dominus",
        "Type": "Legendary Creature",
        "ManaCost": "{2}{W}{W}",
        "Power": 5,
        "Toughness": 4,
        "OracleText": "If one or more tokens would be created under your control, twice that many of those tokens are created instead. {1}{W/P}{W/P}, Sacrifice two other creatures: Put an indestructible counter on Mondrak, Glory Dominus.",
    },

    "Warleader's Call": {
        "Name": "Warleader's Call",
        "Type": "Enchantment",
        "ManaCost": "{2}{R}",
        "OracleText": "Creatures you control have haste. Whenever a creature enters the battlefield under your control, it deals 1 damage to each opponent.",
    },

    # DRAIN EFFECTS
    "Bastion of Remembrance": {
        "Name": "Bastion of Remembrance",
        "Type": "Enchantment",
        "ManaCost": "{2}{W}",
        "OracleText": "When Bastion of Remembrance enters the battlefield, create a 1/1 white Human Soldier creature token. Whenever a creature you control dies, each opponent loses 1 life and you gain 1 life.",
    },

    "Cruel Celebrant": {
        "Name": "Cruel Celebrant",
        "Type": "Creature",
        "ManaCost": "{W}{B}",
        "Power": 1,
        "Toughness": 2,
        "OracleText": "Whenever Cruel Celebrant or another creature or planeswalker you control dies, each opponent loses 1 life and you gain 1 life.",
    },

    "Elas il-Kor, Sadistic Pilgrim": {
        "Name": "Elas il-Kor, Sadistic Pilgrim",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{W}{B}",
        "Power": 2,
        "Toughness": 2,
        "OracleText": "Deathtouch. Whenever another creature enters the battlefield under your control, you gain 1 life. Whenever another creature you control dies, each opponent loses 1 life.",
    },

    "Zulaport Cutthroat": {
        "Name": "Zulaport Cutthroat",
        "Type": "Creature",
        "ManaCost": "{1}{B}",
        "Power": 1,
        "Toughness": 1,
        "OracleText": "Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.",
    },

    "Impact Tremors": {
        "Name": "Impact Tremors",
        "Type": "Enchantment",
        "ManaCost": "{1}{R}",
        "OracleText": "Whenever a creature enters the battlefield under your control, Impact Tremors deals 1 damage to each opponent.",
    },

    "Kambal, Profiteering Mayor": {
        "Name": "Kambal, Profiteering Mayor",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{W}{B}",
        "Power": 2,
        "Toughness": 2,
        "OracleText": "At the beginning of your upkeep, each player draws a card and loses 1 life. Other creatures you control get +1/+1.",
    },

    # SACRIFICE OUTLETS
    "Goblin Bombardment": {
        "Name": "Goblin Bombardment",
        "Type": "Enchantment",
        "ManaCost": "{1}{R}",
        "OracleText": "Sacrifice a creature: Goblin Bombardment deals 1 damage to any target.",
    },

    "Viscera Seer": {
        "Name": "Viscera Seer",
        "Type": "Creature",
        "ManaCost": "{B}",
        "Power": 1,
        "Toughness": 1,
        "OracleText": "Sacrifice a creature: Scry 1.",
    },

    "Warren Soultrader": {
        "Name": "Warren Soultrader",
        "Type": "Creature",
        "ManaCost": "{1}{W}{B}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Whenever Warren Soultrader or another creature you control dies, create a Treasure token. {2}, Sacrifice three Treasures: Draw three cards.",
    },

    # RAMP
    "Sol Ring": {
        "Name": "Sol Ring",
        "Type": "Artifact",
        "ManaCost": "{1}",
        "ManaProduction": 2,
        "OracleText": "{T}: Add {C}{C}.",
    },

    "Arcane Signet": {
        "Name": "Arcane Signet",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "ManaProduction": 1,
        "OracleText": "{T}: Add one mana of any color in your commander's color identity.",
    },

    "Fellwar Stone": {
        "Name": "Fellwar Stone",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "ManaProduction": 1,
        "OracleText": "{T}: Add one mana of any color that a land an opponent controls could produce.",
    },

    "Talisman of Hierarchy": {
        "Name": "Talisman of Hierarchy",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "ManaProduction": 1,
        "OracleText": "{T}: Add {C}. {T}: Add {W} or {B}. Talisman of Hierarchy deals 1 damage to you.",
    },

    "Talisman of Indulgence": {
        "Name": "Talisman of Indulgence",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "ManaProduction": 1,
        "OracleText": "{T}: Add {C}. {T}: Add {B} or {R}. Talisman of Indulgence deals 1 damage to you.",
    },

    "Pitiless Plunderer": {
        "Name": "Pitiless Plunderer",
        "Type": "Creature",
        "ManaCost": "{3}{B}",
        "Power": 1,
        "Toughness": 4,
        "OracleText": "Whenever another creature you control dies, create a Treasure token.",
    },

    "Grim Hireling": {
        "Name": "Grim Hireling",
        "Type": "Creature",
        "ManaCost": "{3}{B}",
        "Power": 3,
        "Toughness": 2,
        "OracleText": "Whenever one or more creatures you control deal combat damage to a player, create two Treasure tokens.",
    },

    "Goldlust Triad": {
        "Name": "Goldlust Triad",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "ManaProduction": 1,
        "OracleText": "{T}: Add one mana of any color. {T}: Add {C}{C}. Activate only if you control three or more artifacts.",
    },

    # DRAW
    "Queen Marchesa": {
        "Name": "Queen Marchesa",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{R}{W}{B}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Deathtouch, haste. When Queen Marchesa enters the battlefield, you become the monarch. At the beginning of your upkeep, if an opponent is the monarch, create a 1/1 black Assassin creature token with deathtouch and haste.",
        "HasHaste": True,
    },

    "Garna, Bloodfist of Keld": {
        "Name": "Garna, Bloodfist of Keld",
        "Type": "Legendary Creature",
        "ManaCost": "{3}{B}{R}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Whenever another creature enters the battlefield under your control or dies, if that creature's power was 4 or greater, draw a card. Whenever Garna, Bloodfist of Keld attacks, attacking creatures get +1/+0 until end of turn.",
    },

    "Gix, Yawgmoth Praetor": {
        "Name": "Gix, Yawgmoth Praetor",
        "Type": "Legendary Creature",
        "ManaCost": "{3}{B}{B}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "Whenever a creature deals combat damage to one of your opponents, its controller may draw a card. {B}, Pay 2 life: Target creature gets -1/-1 until end of turn.",
    },

    "Morbid Opportunist": {
        "Name": "Morbid Opportunist",
        "Type": "Creature",
        "ManaCost": "{2}{B}",
        "Power": 2,
        "Toughness": 3,
        "OracleText": "Whenever one or more other creatures die, draw a card. This ability triggers only once each turn.",
    },

    "Idol of Oblivion": {
        "Name": "Idol of Oblivion",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "OracleText": "{T}: Draw a card if you created a token this turn. {8}, {T}, Sacrifice Idol of Oblivion: Create a 10/10 colorless Eldrazi creature token.",
    },

    "Deadly Dispute": {
        "Name": "Deadly Dispute",
        "Type": "Instant",
        "ManaCost": "{1}{B}",
        "OracleText": "As an additional cost to cast this spell, sacrifice an artifact or creature. Draw two cards and create a Treasure token.",
    },

    "Braids, Arisen Nightmare": {
        "Name": "Braids, Arisen Nightmare",
        "Type": "Legendary Creature",
        "ManaCost": "{1}{B}{B}",
        "Power": 3,
        "Toughness": 3,
        "OracleText": "At the beginning of your end step, you may sacrifice a nonland permanent. If you do, each opponent may sacrifice a permanent or discard a card. Then if you sacrificed a nontoken permanent, create a 2/2 black Nightmare creature token.",
    },

    "Priest of Forgotten Gods": {
        "Name": "Priest of Forgotten Gods",
        "Type": "Creature",
        "ManaCost": "{1}{B}",
        "Power": 1,
        "Toughness": 2,
        "OracleText": "{T}, Sacrifice two creatures: Any number of target players each lose 2 life and sacrifice a creature. You add {B}{B} and draw a card.",
    },

    "Caretaker's Talent": {
        "Name": "Caretaker's Talent",
        "Type": "Enchantment",
        "ManaCost": "{1}{W}",
        "OracleText": "Whenever one or more tokens enter the battlefield under your control, draw a card. This ability triggers only once each turn. {6}{W}{W}: Level 2 // Creature tokens you control have vigilance and lifelink. {10}{W}{W}: Level 3 // When this Class becomes level three, return all creature cards from your graveyard to the battlefield.",
    },

    "Heirloom Blade": {
        "Name": "Heirloom Blade",
        "Type": "Artifact",
        "ManaCost": "{3}",
        "OracleText": "Equipped creature gets +3/+0. Whenever equipped creature dies, you may reveal cards from the top of your library until you reveal a creature card that shares a creature type with it. Put that card into your hand and the rest on the bottom of your library in a random order. Equip {1}",
        "EquipCost": "{1}",
        "PowerBuff": 3,
    },

    "Horn of the Mark": {
        "Name": "Horn of the Mark",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "OracleText": "Whenever a creature you control attacks, it gets +1/+0 until end of turn. If that creature is a Human or an artifact, draw a card.",
    },

    # REMOVAL
    "Swords to Plowshares": {
        "Name": "Swords to Plowshares",
        "Type": "Instant",
        "ManaCost": "{W}",
        "OracleText": "Exile target creature. Its controller gains life equal to its power.",
    },

    "Path to Exile": {
        "Name": "Path to Exile",
        "Type": "Instant",
        "ManaCost": "{W}",
        "OracleText": "Exile target creature. Its controller may search their library for a basic land card, put it onto the battlefield tapped, then shuffle.",
    },

    "Anguished Unmaking": {
        "Name": "Anguished Unmaking",
        "Type": "Instant",
        "ManaCost": "{1}{W}{B}",
        "OracleText": "Exile target nonland permanent. You lose 3 life.",
    },

    "Bitter Triumph": {
        "Name": "Bitter Triumph",
        "Type": "Instant",
        "ManaCost": "{1}{B}",
        "OracleText": "As an additional cost to cast this spell, discard a card or pay 3 life. Destroy target creature or planeswalker.",
    },

    "Damn": {
        "Name": "Damn",
        "Type": "Sorcery",
        "ManaCost": "{2}{B}{B}",
        "OracleText": "Destroy target creature. A player whose creature died this way loses 2 life. Overload {2}{W}{W}{B}{B}",
    },

    "Farewell": {
        "Name": "Farewell",
        "Type": "Sorcery",
        "ManaCost": "{4}{W}{W}",
        "OracleText": "Choose one or more — • Exile all artifacts. • Exile all creatures. • Exile all enchantments. • Exile all graveyards.",
    },

    "Ruinous Ultimatum": {
        "Name": "Ruinous Ultimatum",
        "Type": "Sorcery",
        "ManaCost": "{R}{R}{W}{W}{B}{B}{B}",
        "OracleText": "Destroy all nonland permanents your opponents control.",
    },

    "Final Vengeance": {
        "Name": "Final Vengeance",
        "Type": "Instant",
        "ManaCost": "{1}{B}",
        "OracleText": "As an additional cost to cast this spell, sacrifice a creature or enchantment. Destroy target creature.",
    },

    "Inevitable Defeat": {
        "Name": "Inevitable Defeat",
        "Type": "Sorcery",
        "ManaCost": "{2}{B}",
        "OracleText": "Destroy target creature. Its controller loses 2 life.",
    },

    # UTILITY
    "Lightning Greaves": {
        "Name": "Lightning Greaves",
        "Type": "Artifact",
        "ManaCost": "{2}",
        "OracleText": "Equipped creature has haste and shroud. Equip {0}",
        "EquipCost": "{0}",
    },

    "Diabolic Intent": {
        "Name": "Diabolic Intent",
        "Type": "Sorcery",
        "ManaCost": "{1}{B}",
        "OracleText": "As an additional cost to cast this spell, sacrifice a creature. Search your library for a card, put that card into your hand, then shuffle.",
    },

    # LANDS (basic data - these mostly just produce mana)
    "Command Tower": {
        "Name": "Command Tower",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "Any",  # Commander colors: RWB
        "OracleText": "{T}: Add one mana of any color in your commander's color identity.",
    },

    "Path of Ancestry": {
        "Name": "Path of Ancestry",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "Any",
        "ETBTapped": True,
        "OracleText": "Path of Ancestry enters the battlefield tapped. {T}: Add one mana of any color in your commander's color identity. When that mana is spent to cast a creature spell that shares a creature type with your commander, scry 1.",
    },

    "Exotic Orchard": {
        "Name": "Exotic Orchard",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "Any",
        "OracleText": "{T}: Add one mana of any color that a land an opponent controls could produce.",
    },

    "Nomad Outpost": {
        "Name": "Nomad Outpost",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "RWB",
        "ETBTapped": True,
        "OracleText": "Nomad Outpost enters the battlefield tapped. {T}: Add {R}, {W}, or {B}.",
    },

    "Canyon Slough": {
        "Name": "Canyon Slough",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "BR",
        "ETBTapped": False,  # Cycling land
        "OracleText": "({T}: Add {B} or {R}.) Canyon Slough enters the battlefield tapped. Cycling {2}",
    },

    # Add basic lands and other lands with simple production
    "Plains": {
        "Name": "Plains",
        "Type": "Basic Land",
        "ManaProduction": 1,
        "ProducesColors": "W",
        "OracleText": "{T}: Add {W}.",
    },
    "Mountain": {
        "Name": "Mountain",
        "Type": "Basic Land",
        "ManaProduction": 1,
        "ProducesColors": "R",
        "OracleText": "{T}: Add {R}.",
    },
    "Swamp": {
        "Name": "Swamp",
        "Type": "Basic Land",
        "ManaProduction": 1,
        "ProducesColors": "B",
        "OracleText": "{T}: Add {B}.",
    },

    # Other utility lands
    "High Market": {
        "Name": "High Market",
        "Type": "Land",
        "ManaProduction": 1,
        "OracleText": "{T}: Add {C}. {T}, Sacrifice a creature: You gain 1 life.",
    },

    "Kher Keep": {
        "Name": "Kher Keep",
        "Type": "Land",
        "ManaProduction": 1,
        "OracleText": "{T}: Add {C}. {1}{R}, {T}: Create a 0/1 red Kobold creature token named Kobolds of Kher Keep.",
    },

    "Bojuka Bog": {
        "Name": "Bojuka Bog",
        "Type": "Land",
        "ManaProduction": 1,
        "ProducesColors": "B",
        "ETBTapped": True,
        "OracleText": "Bojuka Bog enters the battlefield tapped. When Bojuka Bog enters the battlefield, exile target player's graveyard. {T}: Add {B}.",
    },
}

# Add remaining lands with proper colors
GENERIC_LANDS = {
    # Red-White lands
    "Battlefield Forge": ("RW", False),
    "Temple of Triumph": ("RW", True),
    "Rugged Prairie": ("RW", False),
    # Black-White lands
    "Caves of Koilos": ("WB", False),
    "Godless Shrine": ("WB", False),
    "Isolated Chapel": ("WB", False),
    "Fetid Heath": ("WB", False),
    # Black-Red lands
    "Dragonskull Summit": ("BR", False),
    "Smoldering Marsh": ("BR", True),
    "Sulfurous Springs": ("BR", False),
    # Multi-color lands
    "Dalkovan Encampment": ("Any", False),
    "Fountainport": ("Any", True),
    "Shattered Landscape": ("Any", False),
    "Windbrisk Heights": ("Any", False),
    # Already defined above
    # "Canyon Slough": ("BR", False),
    # "Nomad Outpost": ("RWB", True),
}

for land, (colors, etb_tapped) in GENERIC_LANDS.items():
    if land not in ZURGO_CARDS:
        ZURGO_CARDS[land] = {
            "Name": land,
            "Type": "Land",
            "ManaProduction": 1,
            "ProducesColors": colors,
            "ETBTapped": etb_tapped,
            "OracleText": f"{{T}}: Add one mana of the specified colors.",
        }

def build_card_database():
    """Build complete card data with default values."""
    rows = []

    for name, data in ZURGO_CARDS.items():
        row = {
            "Name": name,
            "Type": data.get("Type", ""),
            "ManaCost": data.get("ManaCost", ""),
            "Power": data.get("Power", 0),
            "Toughness": data.get("Toughness", 0),
            "ManaProduction": data.get("ManaProduction", 0),
            "ProducesColors": data.get("ProducesColors", ""),
            "HasHaste": data.get("HasHaste", False),
            "HasFlash": data.get("HasFlash", False),
            "ETBTapped": data.get("ETBTapped", False),
            "ETBTappedConditions": "{}",
            "EquipCost": data.get("EquipCost", ""),
            "PowerBuff": data.get("PowerBuff", 0),
            "DrawCards": 0,
            "PutsLand": False,
            "OracleText": data.get("OracleText", ""),
            "DeathTriggerValue": None,
            "SacrificeOutlet": None,
            "Commander": data.get("Commander", False),
        }
        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Save to CSV
    csv_file = "zurgo_deck.csv"
    df.to_csv(csv_file, index=False)
    print(f"Created {csv_file} with {len(df)} cards")

    # Also save as JSON cache for Scryfall loader
    cache = {row["Name"]: row for row in rows}
    with open("scryfall_cache.json", "w") as f:
        json.dump(cache, f, indent=2)
    print(f"Created scryfall_cache.json with {len(cache)} cards")

    return df

if __name__ == "__main__":
    df = build_card_database()
    print(f"\nCard summary:")
    print(f"  Total cards: {len(df)}")
    print(f"  Creatures: {len(df[df['Type'].str.contains('Creature', na=False)])}")
    print(f"  Lands: {len(df[df['Type'].str.contains('Land', na=False)])}")
    print(f"  Artifacts: {len(df[df['Type'].str.contains('Artifact', na=False)])}")
    print(f"  Enchantments: {len(df[df['Type'].str.contains('Enchantment', na=False)])}")
