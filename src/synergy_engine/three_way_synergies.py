"""
Three-Way Synergy Detection
Detects synergies that require 3 specific cards to work together
"""
from typing import Dict, List, Optional
import re


def detect_equipment_matters_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Equipment + Creature + Equipment Matters card
    Example: Sword of X + Equipped creature + Bruenor Battlehammer

    Pattern: Equipment + Creature + Card that cares about equipped creatures
    """
    equipment_patterns = [
        r'\bequipment\b',
        r'equip \{',
        r'attach.*to target creature',
        r'living weapon'
    ]

    equipment_matters_patterns = [
        r'equipped creature',
        r'whenever.*equipped',
        r'when.*becomes equipped',
        r'creatures you control with equipment',
        r'for each equipment.*attached'
    ]

    # Get card info
    cards = [card1, card2, card3]
    equipment_card = None
    creature_card = None
    matters_card = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()

        # Check if equipment
        if 'equipment' in card_type or any(re.search(p, card_text) for p in equipment_patterns):
            if not equipment_card:
                equipment_card = card
        # Check if creature
        elif 'creature' in card_type:
            if not creature_card:
                creature_card = card
        # Check if equipment matters
        if any(re.search(p, card_text) for p in equipment_matters_patterns):
            if not matters_card:
                matters_card = card

    # Need all three components
    if equipment_card and creature_card and matters_card and matters_card != equipment_card:
        return {
            'name': 'Equipment Engine',
            'description': f"{equipment_card['name']} equips {creature_card['name']}, {matters_card['name']} provides additional value for equipped creatures",
            'value': 5.0,
            'category': 'type_synergy',
            'subcategory': 'equipment_engine',
            'cards': [equipment_card['name'], creature_card['name'], matters_card['name']]
        }

    return None


def detect_token_aristocrats_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Token Generator + Sacrifice Outlet + Death Payoff
    Example: Tendershoot Dryad + Ashnod's Altar + Blood Artist

    Pattern: Token generator + Sac outlet + Death trigger payoff
    """
    token_patterns = [
        r'create.*token',
        r'create.*\d+/\d+.*token',
        r'token.*creature',
        r'at the beginning.*create.*token'
    ]

    sac_outlet_patterns = [
        r'sacrifice.*creature',
        r'sacrifice.*permanent',
        r'sacrifice a creature:',
        r'sacrifice a permanent:'
    ]

    death_payoff_patterns = [
        r'whenever.*creature.*dies',
        r'whenever.*permanent.*dies',
        r'when.*creature.*dies',
        r'whenever.*creature you control dies',
        r'whenever.*another creature dies'
    ]

    cards = [card1, card2, card3]
    token_gen = None
    sac_outlet = None
    death_payoff = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()

        if any(re.search(p, card_text) for p in token_patterns):
            if not token_gen:
                token_gen = card
        if any(re.search(p, card_text) for p in sac_outlet_patterns):
            if not sac_outlet:
                sac_outlet = card
        if any(re.search(p, card_text) for p in death_payoff_patterns):
            if not death_payoff:
                death_payoff = card

    if token_gen and sac_outlet and death_payoff:
        return {
            'name': 'Aristocrats Engine',
            'description': f"{token_gen['name']} creates tokens, {sac_outlet['name']} sacrifices them, {death_payoff['name']} triggers on each death",
            'value': 6.0,
            'category': 'role_interaction',
            'subcategory': 'aristocrats_engine',
            'cards': [token_gen['name'], sac_outlet['name'], death_payoff['name']]
        }

    return None


def detect_etb_flicker_payoff_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect ETB Creature + Flicker Effect + ETB Multiplier
    Example: Mulldrifter + Ephemerate + Panharmonicon

    Pattern: ETB creature + Flicker spell + ETB doubler/payoff
    """
    etb_patterns = [
        r'when.*enters.*battlefield',
        r'when.*enters',
        r'evoke'
    ]

    flicker_patterns = [
        r'exile.*return.*battlefield',
        r'exile.*return.*to the battlefield',
        r'blink',
        r'flicker',
        r'return.*to.*hand.*return.*to.*battlefield'
    ]

    etb_multiplier_patterns = [
        r'if.*permanent.*entering.*battlefield',
        r'whenever.*creature.*enters.*battlefield',
        r'whenever.*permanent.*enters',
        r'enters.*battlefield.*abilities.*trigger.*additional',
        r'panharmonicon'
    ]

    cards = [card1, card2, card3]
    etb_creature = None
    flicker = None
    multiplier = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()

        # ETB creature (must be creature with ETB)
        if 'creature' in card_type and any(re.search(p, card_text) for p in etb_patterns):
            if not etb_creature:
                etb_creature = card

        # Flicker effect
        if any(re.search(p, card_text) for p in flicker_patterns):
            if not flicker:
                flicker = card

        # ETB multiplier
        if any(re.search(p, card_text) for p in etb_multiplier_patterns):
            if not multiplier:
                multiplier = card

    if etb_creature and flicker and multiplier:
        return {
            'name': 'ETB Value Engine',
            'description': f"{flicker['name']} flickers {etb_creature['name']}, {multiplier['name']} multiplies the ETB triggers",
            'value': 5.5,
            'category': 'card_advantage',
            'subcategory': 'etb_engine',
            'cards': [etb_creature['name'], flicker['name'], multiplier['name']]
        }

    return None


def detect_mill_reanimate_target_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Mill/Entomb + Reanimate + Big Creature
    Example: Entomb + Animate Dead + Elesh Norn

    Pattern: Graveyard filler + Reanimation + High-value creature
    """
    mill_patterns = [
        r'mill',
        r'put.*from.*library.*graveyard',
        r'entomb',
        r'buried alive'
    ]

    reanimate_patterns = [
        r'return.*creature.*from.*graveyard.*battlefield',
        r'put.*creature.*from.*graveyard.*onto.*battlefield',
        r'reanimate',
        r'animate dead'
    ]

    cards = [card1, card2, card3]
    mill_card = None
    reanimate_card = None
    target = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cmc = card.get('cmc', 0)

        if any(re.search(p, card_text) for p in mill_patterns):
            if not mill_card:
                mill_card = card

        if any(re.search(p, card_text) for p in reanimate_patterns):
            if not reanimate_card:
                reanimate_card = card

        # High-value creature (CMC 6+, or legend, or powerful keywords)
        if 'creature' in card_type and cmc >= 6:
            if not target:
                target = card

    if mill_card and reanimate_card and target:
        return {
            'name': 'Reanimator Engine',
            'description': f"{mill_card['name']} puts {target['name']} in graveyard, {reanimate_card['name']} brings it back",
            'value': 6.5,
            'category': 'role_interaction',
            'subcategory': 'reanimator_engine',
            'cards': [mill_card['name'], reanimate_card['name'], target['name']]
        }

    return None


def detect_cost_reducer_cantrip_payoff_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Cost Reducer + Cantrip + Storm/Spell Payoff
    Example: Baral + Brainstorm + Aetherflux Reservoir

    Pattern: Spell cost reducer + Cheap spell + Spell payoff
    """
    cost_reducer_patterns = [
        r'instant.*sorcery.*cost.*less',
        r'spells.*cost.*less',
        r'reduce.*cost.*instant',
        r'reduce.*cost.*sorcery'
    ]

    cantrip_patterns = [
        r'draw.*card',
        r'scry',
        r'surveil'
    ]

    spell_payoff_patterns = [
        r'whenever you cast.*instant',
        r'whenever you cast.*sorcery',
        r'whenever you cast.*spell',
        r'storm',
        r'for each instant.*sorcery',
        r'prowess',
        r'magecraft'
    ]

    cards = [card1, card2, card3]
    cost_reducer = None
    cantrip = None
    payoff = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cmc = card.get('cmc', 0)

        if any(re.search(p, card_text) for p in cost_reducer_patterns):
            if not cost_reducer:
                cost_reducer = card

        # Cheap instant/sorcery with draw
        if ('instant' in card_type or 'sorcery' in card_type) and cmc <= 2:
            if any(re.search(p, card_text) for p in cantrip_patterns):
                if not cantrip:
                    cantrip = card

        if any(re.search(p, card_text) for p in spell_payoff_patterns):
            if not payoff:
                payoff = card

    if cost_reducer and cantrip and payoff:
        return {
            'name': 'Spellslinger Engine',
            'description': f"{cost_reducer['name']} reduces cost of {cantrip['name']}, {payoff['name']} rewards each cast",
            'value': 5.5,
            'category': 'type_synergy',
            'subcategory': 'spellslinger_engine',
            'cards': [cost_reducer['name'], cantrip['name'], payoff['name']]
        }

    return None


def detect_tap_untap_combo_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Tap for Value + Untapper + Multiplier
    Example: Gilded Lotus + Seedborn Muse + Unwinding Clock

    Pattern: Tap ability + Untap effect + Additional untapper
    """
    tap_value_patterns = [
        r'\{t\}:.*add',
        r'\{t\}:.*draw',
        r'\{t\}:.*create',
        r'\{t\}:.*deal.*damage'
    ]

    untap_patterns = [
        r'untap.*permanent',
        r'untap.*creature',
        r'untap.*artifact',
        r'untap all',
        r'seedborn muse',
        r'unwinding clock'
    ]

    cards = [card1, card2, card3]
    tap_card = None
    untapper1 = None
    untapper2 = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()

        if any(re.search(p, card_text) for p in tap_value_patterns):
            if not tap_card:
                tap_card = card

        if any(re.search(p, card_text) for p in untap_patterns):
            if not untapper1:
                untapper1 = card
            elif not untapper2 and card != untapper1:
                untapper2 = card

    if tap_card and untapper1 and untapper2:
        return {
            'name': 'Tap/Untap Engine',
            'description': f"{tap_card['name']} taps for value, {untapper1['name']} and {untapper2['name']} keep untapping it",
            'value': 6.0,
            'category': 'role_interaction',
            'subcategory': 'tap_untap_engine',
            'cards': [tap_card['name'], untapper1['name'], untapper2['name']]
        }

    return None


def detect_draw_discard_madness_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Draw + Discard Outlet + Madness/Flashback Card
    Example: Wheel of Fortune + Containment Construct + Flashback spell

    Pattern: Draw spell + Discard synergy + Card that wants to be discarded
    """
    draw_patterns = [
        r'draw.*cards',
        r'each player draws',
        r'wheel'
    ]

    discard_synergy_patterns = [
        r'whenever.*discard',
        r'when.*discard',
        r'if.*card.*discarded',
        r'discard.*create',
        r'discard.*draw'
    ]

    madness_patterns = [
        r'madness',
        r'flashback',
        r'when.*discarded',
        r'disturb',
        r'retrace'
    ]

    cards = [card1, card2, card3]
    draw_card = None
    discard_synergy = None
    madness_card = None

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        keywords = [kw.lower() for kw in card.get('keywords', [])]

        if any(re.search(p, card_text) for p in draw_patterns):
            if not draw_card:
                draw_card = card

        if any(re.search(p, card_text) for p in discard_synergy_patterns):
            if not discard_synergy:
                discard_synergy = card

        if any(re.search(p, card_text) for p in madness_patterns) or \
           'madness' in keywords or 'flashback' in keywords:
            if not madness_card:
                madness_card = card

    if draw_card and discard_synergy and madness_card:
        return {
            'name': 'Discard Value Engine',
            'description': f"{draw_card['name']} draws cards, {discard_synergy['name']} rewards discarding, {madness_card['name']} gets value from being discarded",
            'value': 5.0,
            'category': 'card_advantage',
            'subcategory': 'discard_engine',
            'cards': [draw_card['name'], discard_synergy['name'], madness_card['name']]
        }

    return None


# List of all three-way synergy detection functions
THREE_WAY_SYNERGY_RULES = [
    detect_equipment_matters_three_way,
    detect_token_aristocrats_three_way,
    detect_etb_flicker_payoff_three_way,
    detect_mill_reanimate_target_three_way,
    detect_cost_reducer_cantrip_payoff_three_way,
    detect_tap_untap_combo_three_way,
    detect_draw_discard_madness_three_way
]
