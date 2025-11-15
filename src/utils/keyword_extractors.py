"""MIGRATION NOTICE:
==================
This module uses legacy regex-based extraction. For new code, consider using
the unified parser instead:

    from src.core.card_parser import UnifiedCardParser

import warnings

# Optional: Import unified parser for recommended path
try:
    from src.core.card_parser import UnifiedCardParser
    _UNIFIED_PARSER_AVAILABLE = True
except ImportError:
    _UNIFIED_PARSER_AVAILABLE = False
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)

See UNIFIED_ARCHITECTURE_GUIDE.md for details.

The functions in this file are maintained for backward compatibility.

Creature Keyword Extractors
Extract and classify creature keywords and abilities from card text.
"""

import re
from typing import Dict, List, Set, Optional


# Comprehensive list of MTG creature keywords
CREATURE_KEYWORDS = {
    # Combat keywords
    'deathtouch': {'category': 'combat', 'description': 'Destroys any creature it damages'},
    'defender': {'category': 'combat', 'description': 'Cannot attack'},
    'double strike': {'category': 'combat', 'description': 'Deals first strike and regular combat damage'},
    'first strike': {'category': 'combat', 'description': 'Deals combat damage before creatures without first strike'},
    'flying': {'category': 'evasion', 'description': 'Can only be blocked by creatures with flying or reach'},
    'haste': {'category': 'combat', 'description': 'Can attack and tap immediately'},
    'hexproof': {'category': 'protection', 'description': 'Cannot be targeted by opponents'},
    'indestructible': {'category': 'protection', 'description': 'Cannot be destroyed'},
    'lifelink': {'category': 'combat', 'description': 'Damage dealt also causes you to gain that much life'},
    'menace': {'category': 'evasion', 'description': 'Must be blocked by two or more creatures'},
    'reach': {'category': 'combat', 'description': 'Can block creatures with flying'},
    'trample': {'category': 'combat', 'description': 'Excess damage can be dealt to defending player'},
    'vigilance': {'category': 'combat', 'description': "Doesn't tap when attacking"},
    'ward': {'category': 'protection', 'description': 'Counters spells/abilities that target it unless cost paid'},
    'shroud': {'category': 'protection', 'description': 'Cannot be targeted by any spells or abilities'},
    'protection': {'category': 'protection', 'description': 'Cannot be targeted/damaged/blocked by specified quality'},

    # Evasion keywords
    'fear': {'category': 'evasion', 'description': 'Cannot be blocked except by artifact or black creatures'},
    'intimidate': {'category': 'evasion', 'description': 'Cannot be blocked except by artifact or creatures that share a color'},
    'shadow': {'category': 'evasion', 'description': 'Can only block/be blocked by creatures with shadow'},
    'horsemanship': {'category': 'evasion', 'description': 'Can only be blocked by creatures with horsemanship'},
    'skulk': {'category': 'evasion', 'description': "Cannot be blocked by creatures with greater power"},
    'unblockable': {'category': 'evasion', 'description': 'Cannot be blocked'},

    # Triggered abilities
    'landfall': {'category': 'triggered', 'description': 'Triggers when a land enters under your control'},
    'constellation': {'category': 'triggered', 'description': 'Triggers when an enchantment enters under your control'},
    'prowess': {'category': 'triggered', 'description': 'Gets +1/+1 when you cast a noncreature spell'},
    'revolt': {'category': 'triggered', 'description': 'Triggers if a permanent left the battlefield this turn'},
    'rally': {'category': 'triggered', 'description': 'Triggers when a creature enters under your control'},
    'battalion': {'category': 'triggered', 'description': 'Triggers when attacking with 3+ creatures'},

    # Resource keywords
    'convoke': {'category': 'resource', 'description': 'Tap creatures to help pay casting cost'},
    'delve': {'category': 'resource', 'description': 'Exile cards from graveyard to reduce cost'},
    'improvise': {'category': 'resource', 'description': 'Tap artifacts to help pay casting cost'},
    'affinity': {'category': 'resource', 'description': 'Costs less for each permanent of specified type'},

    # Card advantage keywords
    'cascade': {'category': 'card_advantage', 'description': 'Exile cards until you find one that costs less, cast it'},
    'cycling': {'category': 'card_advantage', 'description': 'Discard and pay cost to draw a card'},
    'discover': {'category': 'card_advantage', 'description': 'Exile until you find cheaper card, cast or put in hand'},
    'draw': {'category': 'card_advantage', 'description': 'Draws cards'},

    # Token generation
    'fabricate': {'category': 'tokens', 'description': 'Create +1/+1 counters or servo tokens'},
    'embalm': {'category': 'tokens', 'description': 'Exile from graveyard to create token copy'},
    'eternalize': {'category': 'tokens', 'description': 'Exile from graveyard to create 4/4 token copy'},
    'populate': {'category': 'tokens', 'description': 'Create a copy of a token you control'},

    # +1/+1 counter keywords
    'modular': {'category': 'counters', 'description': 'Enters with +1/+1 counters, move them when it dies'},
    'persist': {'category': 'counters', 'description': 'Returns from graveyard with -1/-1 counter'},
    'undying': {'category': 'counters', 'description': 'Returns from graveyard with +1/+1 counter'},
    'evolve': {'category': 'counters', 'description': 'Gets +1/+1 counter when larger creature enters'},

    # Graveyard keywords
    'flashback': {'category': 'graveyard', 'description': 'Cast from graveyard for flashback cost'},
    'unearth': {'category': 'graveyard', 'description': 'Return from graveyard until end of turn'},
    'disturb': {'category': 'graveyard', 'description': 'Cast transformed from graveyard'},
    'escape': {'category': 'graveyard', 'description': 'Cast from graveyard by exiling cards'},

    # Other keywords
    'flash': {'category': 'timing', 'description': 'Can be cast at instant speed'},
    'split second': {'category': 'timing', 'description': 'Cannot be responded to while on stack'},
    'echo': {'category': 'cost', 'description': 'Must pay cost again next upkeep or sacrifice'},
    'fading': {'category': 'counters', 'description': 'Enters with counters, remove one each upkeep, sacrifice at 0'},
    'vanishing': {'category': 'counters', 'description': 'Like fading but uses time counters'},
    'suspend': {'category': 'timing', 'description': 'Exile with time counters, cast when last removed'},
}


def extract_creature_keywords(card: Dict) -> List[Dict]:
    """
    Extract all creature keywords from a card.

    Args:
        card: Card dictionary with oracle_text and keywords

    Returns:
        List of keyword dictionaries with metadata
    """
    keywords_found = []
    oracle_text = card.get('oracle_text', '').lower()
    keywords_field = card.get('keywords', [])

    # First, check the keywords field (most reliable)
    for keyword in keywords_field:
        keyword_lower = keyword.lower()
        if keyword_lower in CREATURE_KEYWORDS:
            keywords_found.append({
                'keyword': keyword,
                'category': CREATURE_KEYWORDS[keyword_lower]['category'],
                'description': CREATURE_KEYWORDS[keyword_lower]['description'],
                'source': 'keywords_field'
            })

    # Then check oracle text for keywords that might not be in keywords field
    for keyword, metadata in CREATURE_KEYWORDS.items():
        # Skip if already found in keywords field
        if any(k['keyword'].lower() == keyword for k in keywords_found):
            continue

        # Check for keyword in oracle text
        patterns = [
            rf'\b{keyword}\b',  # Exact word match
            rf'{keyword} \(reminder text\)',  # With reminder text
        ]

        # Special patterns for specific keywords
        if keyword == 'protection':
            patterns.append(r'protection from \w+')
        elif keyword == 'ward':
            patterns.append(r'ward \{?\d*[wubrg]*\}?')
        elif keyword == 'affinity':
            patterns.append(r'affinity for \w+')

        for pattern in patterns:
            if re.search(pattern, oracle_text):
                keywords_found.append({
                    'keyword': keyword.title(),
                    'category': metadata['category'],
                    'description': metadata['description'],
                    'source': 'oracle_text'
                })
                break

    return keywords_found


def extract_keyword_abilities(card: Dict) -> Dict:
    """
    Extract keyword abilities with additional context.

    Args:
        card: Card dictionary

    Returns:
        Dictionary organizing keywords by category
    """
    keywords = extract_creature_keywords(card)

    categorized = {
        'combat': [],
        'evasion': [],
        'protection': [],
        'triggered': [],
        'resource': [],
        'card_advantage': [],
        'tokens': [],
        'counters': [],
        'graveyard': [],
        'timing': [],
        'cost': [],
        'other': []
    }

    for kw in keywords:
        category = kw.get('category', 'other')
        if category in categorized:
            categorized[category].append(kw)
        else:
            categorized['other'].append(kw)

    return categorized


def extract_granted_keywords(card: Dict) -> List[Dict]:
    """
    Extract keywords that a card grants to other creatures.

    Examples:
    - "Creatures you control have flying"
    - "Target creature gains haste until end of turn"

    Args:
        card: Card dictionary

    Returns:
        List of granted keyword dictionaries
    """
    granted_keywords = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return granted_keywords

    # Patterns for granting keywords
    grant_patterns = [
        (r'creatures you control have (\w+)', 'permanent_grant'),
        (r'target creature gains (\w+)', 'temporary_grant'),
        (r'(\w+) creatures you control have (\w+)', 'conditional_grant'),
        (r'creatures you control get .* and have (\w+)', 'buff_and_grant'),
        (r'other creatures you control have (\w+)', 'permanent_grant_others'),
    ]

    for pattern, grant_type in grant_patterns:
        matches = re.finditer(pattern, oracle_text)
        for match in matches:
            keyword = match.group(1) if match.lastindex == 1 else match.group(match.lastindex)

            if keyword in CREATURE_KEYWORDS:
                granted_keywords.append({
                    'keyword': keyword.title(),
                    'grant_type': grant_type,
                    'category': CREATURE_KEYWORDS[keyword]['category'],
                    'description': CREATURE_KEYWORDS[keyword]['description']
                })

    return granted_keywords


def classify_creature_abilities(card: Dict) -> Dict:
    """
    Comprehensive classification of all creature abilities.

    Args:
        card: Card dictionary

    Returns:
        Dictionary with complete ability classification
    """
    return {
        'card_name': card.get('name', 'Unknown'),
        'is_creature': 'creature' in card.get('type_line', '').lower(),
        'own_keywords': extract_creature_keywords(card),
        'keyword_categories': extract_keyword_abilities(card),
        'grants_keywords': extract_granted_keywords(card),
        'total_keywords': len(extract_creature_keywords(card)),
        'total_granted': len(extract_granted_keywords(card))
    }


def get_keyword_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Find keyword synergies between two cards.

    Examples:
    - Card 1 has flying, Card 2 grants flying
    - Card 1 grants lifelink, Card 2 has lifelink

    Args:
        card1: First card
        card2: Second card

    Returns:
        List of synergy dictionaries
    """
    synergies = []

    card1_keywords = {kw['keyword'].lower() for kw in extract_creature_keywords(card1)}
    card1_grants = {kw['keyword'].lower() for kw in extract_granted_keywords(card1)}

    card2_keywords = {kw['keyword'].lower() for kw in extract_creature_keywords(card2)}
    card2_grants = {kw['keyword'].lower() for kw in extract_granted_keywords(card2)}

    # Card 1 grants what Card 2 has
    for keyword in card1_grants & card2_keywords:
        synergies.append({
            'type': 'grants_to_has',
            'keyword': keyword.title(),
            'description': f"{card1.get('name')} grants {keyword} which {card2.get('name')} already has"
        })

    # Card 2 grants what Card 1 has
    for keyword in card2_grants & card1_keywords:
        synergies.append({
            'type': 'grants_to_has',
            'keyword': keyword.title(),
            'description': f"{card2.get('name')} grants {keyword} which {card1.get('name')} already has"
        })

    # Both grant same keyword (anthem effect stacking)
    for keyword in card1_grants & card2_grants:
        synergies.append({
            'type': 'both_grant',
            'keyword': keyword.title(),
            'description': f"Both cards grant {keyword} (anthem effects)"
        })

    return synergies
