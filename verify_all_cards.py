#!/usr/bin/env python3
"""
Verify EVERY card in the deck is properly simulated
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.simulation.deck_simulator import convert_card_to_simulation_format
import sys

print("Loading database...")
load_local_database()

deck_list = """
Banner of Kinship
Chasm Guide
Makindi Patrol
Obelisk of Urd
Resolute Blademaster
Warleader's Call
Bender's Waterskin
White Lotus Tile
Impact Tremors
Jwari Shapeshifter
Veyran, Voice of Duality
Hakoda, Selfless Commander
South Pole Voyager
Ty Lee, Chi Blocker
Brainstorm
Expressive Iteration
Faithless Looting
Frantic Search
Frostcliff Siege
Jeskai Ascendancy
Kindred Discovery
Opt
Ponder
Preordain
Skullclamp
Whirlwind of Thought
Bria, Riptide Rogue
Nexus of Fate
Redirect Lightning
Adarkar Wastes
Ally Encampment
Battlefield Forge
Clifftop Retreat
Command Tower
Evolving Wilds
Exotic Orchard
Glacial Fortress
Island
Mountain
Mystic Monastery
Path of Ancestry
Plains
Reliquary Tower
Secluded Courtyard
Shivan Reef
Unclaimed Territory
Lantern Scout
Boros Charm
Swiftfoot Boots
Balmor, Battlemage Captain
Arcane Signet
Azorius Signet
Boros Signet
Fellwar Stone
Izzet Signet
Patchwork Banner
Sol Ring
Storm-Kiln Artist
Talisman of Conviction
Talisman of Creativity
Talisman of Progress
Thought Vessel
Narset, Enlightened Exile
Abrade
An Offer You Can't Refuse
Arcane Denial
Blasphemous Act
Counterspell
Cyclonic Rift
Dovin's Veto
Farewell
Lightning Bolt
Narset's Reversal
Negate
Path to Exile
Swords to Plowshares
Tuktuk Scrapper
United Front
Gideon, Ally of Zendikar
Kykar, Wind's Fury
Renewed Solidarity
""".strip().split('\n')

print("\n" + "="*80)
print("CARD-BY-CARD SIMULATION VERIFICATION")
print("="*80)

total_cards = 0
working_correctly = 0
partially_working = 0
not_working = 0
cards_not_found = 0

for card_name in deck_list:
    card_name = card_name.strip()
    if not card_name:
        continue

    total_cards += 1

    # Get card from database
    card_data = get_card_by_name(card_name)
    if not card_data:
        print(f"\n❌ [{total_cards}] {card_name}")
        print(f"   ⚠️ CARD NOT FOUND IN DATABASE")
        cards_not_found += 1
        continue

    # Convert to simulation format
    try:
        sim_card = convert_card_to_simulation_format(card_data)
    except Exception as e:
        print(f"\n❌ [{total_cards}] {card_name}")
        print(f"   ⚠️ CONVERSION FAILED: {e}")
        not_working += 1
        continue

    oracle = card_data.get('oracle_text', '').lower()
    type_line = card_data.get('type_line', '')

    print(f"\n{'='*80}")
    print(f"[{total_cards}] {card_name}")
    print(f"{'='*80}")
    print(f"Type: {type_line}")
    print(f"Oracle: {oracle[:150]}{'...' if len(oracle) > 150 else ''}")
    print()

    issues = []
    features_working = []

    # Check if it's a creature
    if 'Creature' in type_line:
        if sim_card.power is not None:
            features_working.append(f"✅ Power: {sim_card.power}")
        else:
            issues.append(f"⚠️ Power not parsed (should be {card_data.get('power')})")

        if sim_card.toughness is not None:
            features_working.append(f"✅ Toughness: {sim_card.toughness}")
        else:
            issues.append(f"⚠️ Toughness not parsed")

    # Check keywords
    if 'haste' in oracle:
        if sim_card.has_haste:
            features_working.append("✅ Haste detected")
        else:
            issues.append("❌ Haste NOT detected")

    if 'flying' in oracle or 'flying' in type_line.lower():
        if hasattr(sim_card, 'has_flying') and sim_card.has_flying:
            features_working.append("✅ Flying detected")
        else:
            issues.append("❌ Flying NOT detected")

    if 'vigilance' in oracle:
        if hasattr(sim_card, 'has_vigilance') and sim_card.has_vigilance:
            features_working.append("✅ Vigilance detected")
        else:
            issues.append("❌ Vigilance NOT detected")

    # Check token generation
    if 'create' in oracle and 'token' in oracle:
        if hasattr(sim_card, 'creates_tokens') and sim_card.creates_tokens:
            features_working.append(f"✅ Token creation detected: {sim_card.creates_tokens}")
        else:
            issues.append("❌ TOKEN CREATION NOT DETECTED - WILL NOT WORK IN SIMULATION")

    # Check ETB triggers
    if 'enters the battlefield' in oracle or 'enters' in oracle:
        if 'create' in oracle:
            issues.append("❌ ETB token creation NOT implemented")
        if 'damage' in oracle and 'deals' in oracle:
            issues.append("❌ ETB damage trigger NOT implemented")
        if 'draw' in oracle:
            if sim_card.draw_cards > 0:
                features_working.append(f"✅ ETB draw detected: {sim_card.draw_cards}")
            else:
                issues.append("❌ ETB draw NOT detected")

    # Check whenever triggers
    if 'whenever' in oracle:
        if 'you cast' in oracle:
            issues.append("❌ 'Whenever you cast' trigger NOT implemented")
        if 'creature you control enters' in oracle or 'creature enters' in oracle:
            issues.append("❌ ETB creature trigger NOT implemented")
        if 'damage' in oracle:
            issues.append("❌ Damage trigger NOT implemented")

    # Check anthem effects
    if ('+' in oracle and '/' in oracle and 'creatures' in oracle) or 'get +' in oracle:
        issues.append("❌ ANTHEM/BUFF NOT implemented - creatures won't get bonus")

    # Check mana production
    if 'add' in oracle and ('{t}' in oracle or 'tap' in oracle.lower()):
        if sim_card.mana_production > 0:
            features_working.append(f"✅ Mana production: {sim_card.mana_production}")
        else:
            issues.append("❌ Mana production NOT detected")

    # Check direct damage
    if 'deals' in oracle and 'damage' in oracle:
        if hasattr(sim_card, 'deals_damage') and sim_card.deals_damage > 0:
            features_working.append(f"✅ Direct damage: {sim_card.deals_damage}")
        else:
            issues.append("❌ Direct damage NOT detected")

    # Check land
    if 'Land' in type_line:
        if sim_card.mana_production > 0:
            features_working.append(f"✅ Land mana production: {sim_card.mana_production}")
        else:
            issues.append("⚠️ Land mana production not set")

    # Print results
    if features_working:
        print("WORKING FEATURES:")
        for feature in features_working:
            print(f"  {feature}")

    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")

        if any('NOT implemented' in i or 'NOT DETECTED' in i for i in issues):
            not_working += 1
            print("\n🔴 STATUS: NOT WORKING - Card abilities will NOT function in simulation")
        else:
            partially_working += 1
            print("\n🟡 STATUS: PARTIALLY WORKING - Some abilities missing")
    else:
        if features_working:
            working_correctly += 1
            print("\n🟢 STATUS: WORKING CORRECTLY")
        else:
            print("\n⚪ STATUS: No special abilities to check")

print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"\nTotal cards checked: {total_cards}")
print(f"🟢 Working correctly: {working_correctly}")
print(f"🟡 Partially working: {partially_working}")
print(f"🔴 NOT working: {not_working}")
print(f"⚠️ Not found in database: {cards_not_found}")
print(f"\n❌ Cards with broken simulation: {not_working + partially_working}/{total_cards}")
print(f"✅ Success rate: {(working_correctly/total_cards*100):.1f}%")

print("\n" + "="*80)
print("CRITICAL ISSUES")
print("="*80)
print("""
The following card types are NOT properly simulated:
1. ❌ Token generation (Kykar, Storm-Kiln Artist, Gideon)
2. ❌ ETB damage triggers (Warleader's Call, Impact Tremors)
3. ❌ Anthem effects (Banner of Kinship, Obelisk of Urd, Warleader's Call)
4. ❌ "Whenever you cast" triggers (Kykar, Storm-Kiln, Balmor)
5. ❌ "Rally" triggers (Ally ETB effects)

This is why simulation shows:
- 0 tokens created (should be dozens)
- ~2 damage/turn (missing all ETB triggers and anthems)
- Low board power (missing +1/+1 buffs from anthems)
""")
