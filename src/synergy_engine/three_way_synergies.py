"""
Three-Way Synergy Detection
Detects synergies that require 3 specific cards to work together
"""
from typing import Dict, List, Optional
import re

# Pre-compile all regex patterns for performance
# Equipment patterns
EQUIPMENT_PATTERNS = [
    re.compile(r'\bequipment\b'),
    re.compile(r'equip \{'),
    re.compile(r'attach.*to target creature'),
    re.compile(r'living weapon')
]

EQUIPMENT_MATTERS_PATTERNS = [
    re.compile(r'equipped creature'),
    re.compile(r'whenever.*equipped'),
    re.compile(r'when.*becomes equipped'),
    re.compile(r'creatures you control with equipment'),
    re.compile(r'for each equipment.*attached')
]

# Token/Aristocrats patterns - MORE SPECIFIC
TOKEN_PATTERNS = [
    re.compile(r'create (one|two|three|\d+|an?).*\d+/\d+.*token'),  # Must specify creating X/X tokens
    re.compile(r'at the beginning.*create.*\d+/\d+.*token'),  # Recurring token generation
    re.compile(r'create.*\d+/\d+.*creature token'),  # Explicit creature token creation
]

SAC_OUTLET_PATTERNS = [
    re.compile(r'sacrifice a creature\s*:'),  # Must be an activated ability (colon)
    re.compile(r'sacrifice (a|an) (permanent|artifact)\s*:'),  # Can sac artifacts/permanents
    re.compile(r'sacrifice.*creature.*:\s*(add|draw|deal|destroy|exile)'),  # Specific payoffs
]

DEATH_PAYOFF_PATTERNS = [
    re.compile(r'whenever (a|another|one or more) creature.*you control.*dies.*,\s*(you|target|each|draw|deal|create|gain|lose|put|return|destroy)'),  # Must have payoff
    re.compile(r'when.*creature.*dies.*,\s*(you|target|each|draw|deal|create|gain|lose|put|return|destroy)'),  # Shorter version
]

# ETB/Flicker patterns
ETB_PATTERNS = [
    re.compile(r'when.*enters.*battlefield.*(you|target|each|draw|deal|create|gain|put|destroy|exile|return|search)'),  # Must have payoff
    re.compile(r'evoke')
]

FLICKER_PATTERNS = [
    re.compile(r'exile (it|target|.*creature|.*permanent).*return.*battlefield'),  # Must exile and return
    re.compile(r'exile.*return.*to the battlefield under'),
    re.compile(r'blink'),
    re.compile(r'flicker')
]

ETB_MULTIPLIER_PATTERNS = [
    re.compile(r'if.*(artifact|creature|permanent).*enter(s|ing).*battlefield.*trigger'),
    re.compile(r'whenever.*(creature|permanent).*enters.*battlefield.*(you|target|each|draw|create|gain)'),  # Must have payoff
    re.compile(r'trigger(s|ed)?.*additional'),  # Panharmonicon effect
    re.compile(r'panharmonicon'),
    re.compile(r'yarok')
]

# Mill/Reanimate patterns
MILL_PATTERNS = [
    re.compile(r'mill \d+'),  # Must specify a number
    re.compile(r'put.*top.*cards.*from.*library.*into.*graveyard'),
    re.compile(r'entomb'),
    re.compile(r'buried alive')
]

REANIMATE_PATTERNS = [
    re.compile(r'return (target|a|up to) (creature|permanent).*card.*from.*graveyard.*to.*battlefield'),
    re.compile(r'put.*creature.*card.*from.*graveyard.*onto.*battlefield'),
    re.compile(r'reanimate'),
    re.compile(r'animate dead'),
    re.compile(r'living death')
]

# Spellslinger patterns
COST_REDUCER_PATTERNS = [
    re.compile(r'instant.*and.*sorcery.*cost.*less'),
    re.compile(r'instant.*sorcery.*spells.*cost.*\{'),
    re.compile(r'noncreature spells.*cost.*less')
]

CANTRIP_PATTERNS = [
    re.compile(r'draw (a|one|\d+) card'),
    re.compile(r'scry \d+'),
    re.compile(r'surveil \d+')
]

SPELL_PAYOFF_PATTERNS = [
    re.compile(r'whenever you cast.*instant.*sorcery'),
    re.compile(r'whenever you cast.*noncreature'),
    re.compile(r'whenever you cast (an|a) instant'),
    re.compile(r'whenever you cast (an|a) sorcery'),
    re.compile(r'storm'),
    re.compile(r'for each instant.*and.*sorcery'),
    re.compile(r'prowess'),
    re.compile(r'magecraft')
]

# Tap/Untap patterns
TAP_VALUE_PATTERNS = [
    re.compile(r'\{t\}:\s*add'),
    re.compile(r'\{t\}:\s*draw'),
    re.compile(r'\{t\}:\s*create'),
    re.compile(r'\{t\}:\s*deal \d+ damage')
]

UNTAP_PATTERNS = [
    re.compile(r'untap (up to )?(target|all|each|another).*permanent'),
    re.compile(r'untap (up to )?(target|all|each|another).*creature'),
    re.compile(r'untap (up to )?(target|all|each|another).*artifact'),
    re.compile(r'seedborn muse'),
    re.compile(r'unwinding clock'),
    re.compile(r'untap (all|each)'),
]

# Discard patterns
DRAW_PATTERNS = [
    re.compile(r'(draw|draws) (\d+|seven|that many) card'),
    re.compile(r'each player draws'),
    re.compile(r'wheel of fortune'),
    re.compile(r'wheel of misfortune')
]

DISCARD_SYNERGY_PATTERNS = [
    re.compile(r'whenever (you|a player) discard.*(create|draw|deal|add|put)'),  # Must have payoff
    re.compile(r'when.*you.*discard.*(create|draw|deal|add|put)'),
    re.compile(r'if.*card.*discarded.*(create|draw|deal)'),
]

MADNESS_PATTERNS = [
    re.compile(r'madness \{'),
    re.compile(r'flashback \{'),
    re.compile(r'when.*discarded.*(you may|return)'),
    re.compile(r'disturb \{'),
    re.compile(r'retrace')
]


def _check_patterns(text: str, patterns: List[re.Pattern]) -> bool:
    """Helper function to check if text matches any pattern"""
    return any(pattern.search(text) for pattern in patterns)


def categorize_cards_for_three_way(cards: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Pre-categorize cards by their potential roles in three-way synergies.
    This significantly speeds up three-way detection by filtering cards upfront.

    Returns:
        Dictionary mapping category names to lists of cards
    """
    categorized = {
        'equipment': [],
        'equipment_matters': [],
        'creature': [],
        'token_gen': [],
        'sac_outlet': [],
        'death_payoff': [],
        'etb_creature': [],
        'flicker': [],
        'etb_multiplier': [],
        'mill': [],
        'reanimate': [],
        'big_creature': [],
        'cost_reducer': [],
        'cantrip': [],
        'spell_payoff': [],
        'tap_value': [],
        'untapper': [],
        'draw': [],
        'discard_synergy': [],
        'madness': []
    }

    for card in cards:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cmc = card.get('cmc', 0)
        keywords = [kw.lower() for kw in card.get('keywords', [])]

        # Skip lands
        if '//' not in card_type and 'land' in card_type:
            continue
        if 'error' in card:
            continue

        # Categorize by potential roles
        if 'equipment' in card_type or _check_patterns(card_text, EQUIPMENT_PATTERNS):
            categorized['equipment'].append(card)
        if _check_patterns(card_text, EQUIPMENT_MATTERS_PATTERNS):
            categorized['equipment_matters'].append(card)
        if 'creature' in card_type:
            categorized['creature'].append(card)
            if cmc >= 6:
                categorized['big_creature'].append(card)
        if _check_patterns(card_text, TOKEN_PATTERNS):
            categorized['token_gen'].append(card)
        if _check_patterns(card_text, SAC_OUTLET_PATTERNS):
            categorized['sac_outlet'].append(card)
        if _check_patterns(card_text, DEATH_PAYOFF_PATTERNS):
            categorized['death_payoff'].append(card)
        if 'creature' in card_type and _check_patterns(card_text, ETB_PATTERNS):
            categorized['etb_creature'].append(card)
        if _check_patterns(card_text, FLICKER_PATTERNS):
            categorized['flicker'].append(card)
        if _check_patterns(card_text, ETB_MULTIPLIER_PATTERNS):
            categorized['etb_multiplier'].append(card)
        if _check_patterns(card_text, MILL_PATTERNS):
            categorized['mill'].append(card)
        if _check_patterns(card_text, REANIMATE_PATTERNS):
            categorized['reanimate'].append(card)
        if _check_patterns(card_text, COST_REDUCER_PATTERNS):
            categorized['cost_reducer'].append(card)
        if ('instant' in card_type or 'sorcery' in card_type) and cmc <= 2 and _check_patterns(card_text, CANTRIP_PATTERNS):
            categorized['cantrip'].append(card)
        if _check_patterns(card_text, SPELL_PAYOFF_PATTERNS):
            categorized['spell_payoff'].append(card)
        if _check_patterns(card_text, TAP_VALUE_PATTERNS):
            categorized['tap_value'].append(card)
        if _check_patterns(card_text, UNTAP_PATTERNS):
            categorized['untapper'].append(card)
        if _check_patterns(card_text, DRAW_PATTERNS):
            categorized['draw'].append(card)
        if _check_patterns(card_text, DISCARD_SYNERGY_PATTERNS):
            categorized['discard_synergy'].append(card)
        if 'madness' in keywords or 'flashback' in keywords or _check_patterns(card_text, MADNESS_PATTERNS):
            categorized['madness'].append(card)

    return categorized


def detect_equipment_matters_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Equipment + Creature + Equipment Matters card
    Example: Sword of X + Equipped creature + Bruenor Battlehammer

    Pattern: Equipment + Creature + Card that cares about equipped creatures
    """
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cards_data.append({
            'card': card,
            'text': card_text,
            'type': card_type,
            'is_equipment': 'equipment' in card_type or _check_patterns(card_text, EQUIPMENT_PATTERNS),
            'is_creature': 'creature' in card_type,
            'matters': _check_patterns(card_text, EQUIPMENT_MATTERS_PATTERNS)
        })

    # Find components
    equipment_card = next((d['card'] for d in cards_data if d['is_equipment']), None)
    creature_card = next((d['card'] for d in cards_data if d['is_creature'] and not d['is_equipment']), None)
    matters_card = next((d['card'] for d in cards_data if d['matters'] and d['card'] != equipment_card), None)

    # Need all three components and ensure they're unique
    if equipment_card and creature_card and matters_card and \
       len({equipment_card['name'], creature_card['name'], matters_card['name']}) == 3:
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
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        cards_data.append({
            'card': card,
            'text': card_text,
            'is_token_gen': _check_patterns(card_text, TOKEN_PATTERNS),
            'is_sac_outlet': _check_patterns(card_text, SAC_OUTLET_PATTERNS),
            'is_death_payoff': _check_patterns(card_text, DEATH_PAYOFF_PATTERNS)
        })

    # Find components
    token_gen = next((d['card'] for d in cards_data if d['is_token_gen']), None)
    sac_outlet = next((d['card'] for d in cards_data if d['is_sac_outlet']), None)
    death_payoff = next((d['card'] for d in cards_data if d['is_death_payoff']), None)

    # Ensure all three cards are unique
    if token_gen and sac_outlet and death_payoff and \
       len({token_gen['name'], sac_outlet['name'], death_payoff['name']}) == 3:
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
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        has_etb = _check_patterns(card_text, ETB_PATTERNS)
        cards_data.append({
            'card': card,
            'text': card_text,
            'type': card_type,
            'is_etb_creature': 'creature' in card_type and has_etb,
            'is_flicker': _check_patterns(card_text, FLICKER_PATTERNS),
            'is_multiplier': _check_patterns(card_text, ETB_MULTIPLIER_PATTERNS)
        })

    # Find components
    etb_creature = next((d['card'] for d in cards_data if d['is_etb_creature']), None)
    flicker = next((d['card'] for d in cards_data if d['is_flicker']), None)
    multiplier = next((d['card'] for d in cards_data if d['is_multiplier']), None)

    # Ensure all three cards are unique
    if etb_creature and flicker and multiplier and \
       len({etb_creature['name'], flicker['name'], multiplier['name']}) == 3:
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
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cmc = card.get('cmc', 0)
        cards_data.append({
            'card': card,
            'text': card_text,
            'type': card_type,
            'cmc': cmc,
            'is_mill': _check_patterns(card_text, MILL_PATTERNS),
            'is_reanimate': _check_patterns(card_text, REANIMATE_PATTERNS),
            'is_big_creature': 'creature' in card_type and cmc >= 6
        })

    # Find components
    mill_card = next((d['card'] for d in cards_data if d['is_mill']), None)
    reanimate_card = next((d['card'] for d in cards_data if d['is_reanimate']), None)
    target = next((d['card'] for d in cards_data if d['is_big_creature']), None)

    # Ensure all three cards are unique
    if mill_card and reanimate_card and target and \
       len({mill_card['name'], reanimate_card['name'], target['name']}) == 3:
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
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        card_type = card.get('type_line', '').lower()
        cmc = card.get('cmc', 0)
        is_cheap_spell = ('instant' in card_type or 'sorcery' in card_type) and cmc <= 2
        has_draw = _check_patterns(card_text, CANTRIP_PATTERNS)
        cards_data.append({
            'card': card,
            'text': card_text,
            'type': card_type,
            'cmc': cmc,
            'is_cost_reducer': _check_patterns(card_text, COST_REDUCER_PATTERNS),
            'is_cantrip': is_cheap_spell and has_draw,
            'is_payoff': _check_patterns(card_text, SPELL_PAYOFF_PATTERNS)
        })

    # Find components
    cost_reducer = next((d['card'] for d in cards_data if d['is_cost_reducer']), None)
    cantrip = next((d['card'] for d in cards_data if d['is_cantrip']), None)
    payoff = next((d['card'] for d in cards_data if d['is_payoff']), None)

    # Ensure all three cards are unique
    if cost_reducer and cantrip and payoff and \
       len({cost_reducer['name'], cantrip['name'], payoff['name']}) == 3:
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
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        cards_data.append({
            'card': card,
            'text': card_text,
            'is_tap_value': _check_patterns(card_text, TAP_VALUE_PATTERNS),
            'is_untapper': _check_patterns(card_text, UNTAP_PATTERNS)
        })

    # Find components
    tap_card = next((d['card'] for d in cards_data if d['is_tap_value']), None)
    untappers = [d['card'] for d in cards_data if d['is_untapper']]

    # Ensure all three cards are unique
    if tap_card and len(untappers) >= 2 and \
       len({tap_card['name'], untappers[0]['name'], untappers[1]['name']}) == 3:
        return {
            'name': 'Tap/Untap Engine',
            'description': f"{tap_card['name']} taps for value, {untappers[0]['name']} and {untappers[1]['name']} keep untapping it",
            'value': 6.0,
            'category': 'role_interaction',
            'subcategory': 'tap_untap_engine',
            'cards': [tap_card['name'], untappers[0]['name'], untappers[1]['name']]
        }

    return None


def detect_draw_discard_madness_three_way(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect Draw + Discard Outlet + Madness/Flashback Card
    Example: Wheel of Fortune + Containment Construct + Flashback spell

    Pattern: Draw spell + Discard synergy + Card that wants to be discarded
    """
    # Cache card attributes
    cards_data = []
    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()
        keywords = [kw.lower() for kw in card.get('keywords', [])]
        has_madness_keyword = 'madness' in keywords or 'flashback' in keywords
        has_madness_text = _check_patterns(card_text, MADNESS_PATTERNS)
        cards_data.append({
            'card': card,
            'text': card_text,
            'is_draw': _check_patterns(card_text, DRAW_PATTERNS),
            'is_discard_synergy': _check_patterns(card_text, DISCARD_SYNERGY_PATTERNS),
            'is_madness': has_madness_keyword or has_madness_text
        })

    # Find components
    draw_card = next((d['card'] for d in cards_data if d['is_draw']), None)
    discard_synergy = next((d['card'] for d in cards_data if d['is_discard_synergy']), None)
    madness_card = next((d['card'] for d in cards_data if d['is_madness']), None)

    # Ensure all three cards are unique
    if draw_card and discard_synergy and madness_card and \
       len({draw_card['name'], discard_synergy['name'], madness_card['name']}) == 3:
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
