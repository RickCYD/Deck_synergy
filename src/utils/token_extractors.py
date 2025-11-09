"""
Token Generation Extractors

Extracts token-related mechanics from MTG cards:
- Token creation (type, power/toughness, quantity)
- Token doublers (effects that double token creation)
- Anthems (effects that buff all creatures/tokens)
- Token synergies (effects that trigger on token creation)
"""

import re
from typing import Dict, List, Optional, Tuple


def extract_token_creation(card: Dict) -> Dict:
    """
    Extract token creation mechanics from a card.

    Returns:
        {
            'creates_tokens': bool,
            'token_types': List[Dict],  # [{'count': int, 'power': str, 'toughness': str, 'type': str, 'keywords': List[str]}]
            'creation_type': str,  # 'etb', 'activated', 'triggered', 'dies', 'combat', 'upkeep'
            'repeatable': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'creates_tokens': False,
        'token_types': [],
        'creation_type': None,
        'repeatable': False,
        'examples': []
    }

    if not text:
        return result

    # Token creation patterns
    # Pattern: "create X Y token(s)" or "create a X Y token"
    token_pattern = r'creates?\s+(?:a\s+|an\s+|(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+)?(\d+/\d+)\s+(.*?)\s+(?:creature\s+)?tokens?'

    # Also match tokens without P/T (like Treasure, Food, Clue)
    artifact_token_pattern = r'creates?\s+(?:a\s+|an\s+|(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+)?(treasure|food|clue|blood|incubator|powerstone|map)s?\s+tokens?'

    matches = list(re.finditer(token_pattern, text))
    artifact_matches = list(re.finditer(artifact_token_pattern, text))

    if not matches and not artifact_matches:
        return result

    result['creates_tokens'] = True

    # Convert number words to digits
    number_words = {
        'a': 1, 'an': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }

    # Process creature tokens
    for match in matches:
        result['examples'].append(match.group(0))

        count_str = match.group(1) if match.group(1) else '1'
        pt = match.group(2)  # e.g., "1/1"
        type_info = match.group(3)  # e.g., "white soldier"

        # Parse count
        if count_str in ['x', 'X']:
            count = 'X'
        elif count_str in number_words:
            count = number_words[count_str]
        elif count_str.isdigit():
            count = int(count_str)
        else:
            count = 1

        # Parse P/T
        power, toughness = pt.split('/')

        # Parse type and keywords
        type_parts = type_info.split()
        colors = []
        types = []
        keywords = []

        for part in type_parts:
            if part in ['white', 'blue', 'black', 'red', 'green', 'colorless']:
                colors.append(part)
            elif part in ['flying', 'haste', 'vigilance', 'trample', 'lifelink', 'deathtouch',
                         'first strike', 'double strike', 'menace', 'reach', 'hexproof']:
                keywords.append(part)
            elif part not in ['creature', 'token', 'tokens', 'with', 'and']:
                types.append(part)

        token_info = {
            'count': count,
            'power': power,
            'toughness': toughness,
            'colors': colors,
            'types': types,
            'keywords': keywords
        }

        result['token_types'].append(token_info)

    # Process artifact tokens (Treasure, Food, etc.)
    for match in artifact_matches:
        result['examples'].append(match.group(0))

        count_str = match.group(1) if match.group(1) else '1'
        token_type = match.group(2)

        # Parse count
        if count_str in ['x', 'X']:
            count = 'X'
        elif count_str in number_words:
            count = number_words[count_str]
        elif count_str.isdigit():
            count = int(count_str)
        else:
            count = 1

        token_info = {
            'count': count,
            'power': None,
            'toughness': None,
            'colors': [],
            'types': [token_type],
            'keywords': []
        }

        result['token_types'].append(token_info)

    # Determine creation type
    creation_patterns = [
        (r'when.*enters.*battlefield', 'etb'),
        (r'when.*dies', 'dies'),
        (r'whenever.*attacks', 'combat'),
        (r'whenever.*deals?\s+damage', 'combat'),
        (r'at\s+the\s+beginning\s+of\s+your\s+upkeep', 'upkeep'),
        (r'at\s+the\s+beginning\s+of\s+(?:each\s+)?end\s+step', 'end_step'),
        (r'whenever', 'triggered'),
        (r'\{.*\}:', 'activated')
    ]

    for pattern, ctype in creation_patterns:
        if re.search(pattern, text):
            result['creation_type'] = ctype
            break

    if not result['creation_type']:
        result['creation_type'] = 'spell'

    # Check if repeatable
    repeatable_keywords = ['whenever', 'at the beginning', '{t}:', '{tap}:']
    result['repeatable'] = any(keyword in text for keyword in repeatable_keywords)

    return result


def extract_token_doublers(card: Dict) -> Dict:
    """
    Extract token doubling effects.

    Returns:
        {
            'is_token_doubler': bool,
            'doubler_type': str,  # 'all_tokens', 'creature_tokens', 'artifact_tokens', 'specific_type'
            'multiplier': int,  # Usually 2, but could be more
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_token_doubler': False,
        'doubler_type': None,
        'multiplier': 2,
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Token doubling patterns
    doubling_patterns = [
        # "If you would create tokens, create twice that many instead"
        (r'if\s+(?:an\s+effect\s+would\s+create|you\s+would\s+create).*?tokens?.*?twice\s+that\s+many', 'all_tokens'),
        (r'if.*tokens?.*would.*created.*twice', 'all_tokens'),

        # Specific type doublers
        (r'if.*creature\s+tokens?.*twice', 'creature_tokens'),
        (r'if.*artifact\s+tokens?.*twice', 'artifact_tokens'),

        # Doubling Season pattern
        (r'if.*would.*(?:put|create|enter).*doubling', 'all_permanents'),
    ]

    for pattern, dtype in doubling_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_token_doubler'] = True
            result['doubler_type'] = dtype
            result['examples'].append(match.group(0))
            break

    # Check for conditions
    if result['is_token_doubler']:
        condition_patterns = [
            (r'if.*under\s+your\s+control', 'your_control'),
            (r'if.*you\s+control', 'you_control'),
            (r'if.*opponent', 'not_opponent'),
        ]

        for pattern, condition in condition_patterns:
            if re.search(pattern, text):
                result['conditions'].append(condition)

    return result


def extract_anthems(card: Dict) -> Dict:
    """
    Extract anthem effects (global buffs).

    Returns:
        {
            'is_anthem': bool,
            'buff_type': str,  # 'static', 'activated', 'triggered'
            'targets': List[str],  # 'all_creatures', 'your_creatures', 'tokens', 'specific_type'
            'power_bonus': int,
            'toughness_bonus': int,
            'keyword_grants': List[str],
            'conditions': List[str],
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_anthem': False,
        'buff_type': None,
        'targets': [],
        'power_bonus': 0,
        'toughness_bonus': 0,
        'keyword_grants': [],
        'conditions': [],
        'examples': []
    }

    if not text:
        return result

    # Anthem patterns: "creatures you control get +X/+Y"
    anthem_patterns = [
        r'(creatures?\s+you\s+control|(?:each\s+)?other\s+creatures?\s+you\s+control)\s+(?:gets?|have?)\s+\+(\d+)/\+(\d+)',
        r'(tokens?\s+you\s+control)\s+(?:gets?|have?)\s+\+(\d+)/\+(\d+)',
        r'(.*?)\s+creatures?\s+you\s+control\s+(?:gets?|have?)\s+\+(\d+)/\+(\d+)',
    ]

    for pattern in anthem_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_anthem'] = True
            result['examples'].append(match.group(0))

            # Parse target
            target_text = match.group(1)
            if 'token' in target_text:
                result['targets'].append('tokens')
            elif 'other' in target_text:
                result['targets'].append('other_creatures')
            elif 'creature' in target_text:
                result['targets'].append('your_creatures')
            else:
                # Specific creature type mentioned
                result['targets'].append('specific_type')

            # Parse bonus - get last two groups (the +X/+Y)
            groups = match.groups()
            if len(groups) >= 2:
                try:
                    result['power_bonus'] = int(groups[-2])
                    result['toughness_bonus'] = int(groups[-1])
                except (ValueError, IndexError):
                    pass

            break

    if not result['is_anthem']:
        return result

    # Check for keyword grants
    keyword_grant_patterns = [
        (r'have\s+flying', 'flying'),
        (r'have\s+vigilance', 'vigilance'),
        (r'have\s+haste', 'haste'),
        (r'have\s+trample', 'trample'),
        (r'have\s+lifelink', 'lifelink'),
        (r'have\s+deathtouch', 'deathtouch'),
        (r'have\s+menace', 'menace'),
        (r'have\s+first\s+strike', 'first strike'),
    ]

    for pattern, keyword in keyword_grant_patterns:
        if re.search(pattern, text):
            result['keyword_grants'].append(keyword)

    # Determine buff type
    if re.search(r'\{.*\}:', text):
        result['buff_type'] = 'activated'
    elif re.search(r'whenever|at\s+the\s+beginning', text):
        result['buff_type'] = 'triggered'
    else:
        result['buff_type'] = 'static'

    # Check for conditions
    condition_patterns = [
        (r'as\s+long\s+as', 'conditional'),
        (r'during\s+your\s+turn', 'your_turn'),
        (r'during\s+combat', 'combat'),
    ]

    for pattern, condition in condition_patterns:
        if re.search(pattern, text):
            result['conditions'].append(condition)

    return result


def extract_token_synergies(card: Dict) -> Dict:
    """
    Extract effects that care about tokens/token creation.

    Returns:
        {
            'cares_about_tokens': bool,
            'synergy_type': str,  # 'creation_trigger', 'death_trigger', 'sacrifice_outlet', 'count_matters'
            'payoff_effects': List[str],  # 'damage', 'life', 'draw', 'scry', 'mana', 'counter'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'cares_about_tokens': False,
        'synergy_type': None,
        'payoff_effects': [],
        'examples': []
    }

    if not text:
        return result

    # Token creation triggers
    creation_trigger_pattern = r'whenever.*(?:tokens?.*(?:enters?|created)|created.*tokens?)'
    if re.search(creation_trigger_pattern, text):
        result['cares_about_tokens'] = True
        result['synergy_type'] = 'creation_trigger'
        result['examples'].append(re.search(creation_trigger_pattern, text).group(0))

    # Token death triggers
    death_trigger_pattern = r'whenever.*(?:tokens?|creatures?).*(?:dies?|put\s+into.*graveyard)'
    if re.search(death_trigger_pattern, text) and 'token' in text:
        result['cares_about_tokens'] = True
        result['synergy_type'] = 'death_trigger'

    # Sacrifice outlets
    sacrifice_pattern = r'sacrifice\s+(?:a\s+|an\s+)?(?:creature|token)'
    if re.search(sacrifice_pattern, text):
        result['cares_about_tokens'] = True
        result['synergy_type'] = 'sacrifice_outlet'

    # Count matters (power/effect based on token count)
    count_pattern = r'(?:power|toughness|damage|draw).*equal\s+to.*(?:creatures?|tokens?)'
    if re.search(count_pattern, text):
        result['cares_about_tokens'] = True
        result['synergy_type'] = 'count_matters'

    if not result['cares_about_tokens']:
        return result

    # Determine payoff effects
    payoff_patterns = [
        (r'deals?\s+\d+\s+damage', 'damage'),
        (r'gains?\s+\d+\s+life', 'life'),
        (r'draws?\s+(?:a\s+)?cards?', 'draw'),
        (r'scrys?\s+\d+', 'scry'),
        (r'add\s+\{[WUBRGC]\}', 'mana'),
        (r'(?:put|gets?)\s+(?:a\s+)?\+1/\+1\s+counter', 'counter'),
    ]

    for pattern, effect in payoff_patterns:
        if re.search(pattern, text):
            result['payoff_effects'].append(effect)

    return result


def extract_token_type_preferences(card: Dict) -> Dict:
    """
    Extract what specific token types a card cares about (for payoff cards).

    This distinguishes between:
    - Cards that care about specific token types (e.g., "whenever you create a Food token")
    - Cards that care about any tokens (e.g., "whenever you create a token")
    - Cards that care about creature tokens specifically

    Returns:
        {
            'cares_about_tokens': bool,
            'specific_token_types': List[str],  # ['food', 'treasure', 'clue', 'creature', etc.]
            'cares_about_any_tokens': bool,  # True if cares about tokens in general
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'cares_about_tokens': False,
        'specific_token_types': [],
        'cares_about_any_tokens': False,
        'examples': []
    }

    if not text:
        return result

    # Specific token type patterns
    specific_patterns = {
        'treasure': [
            r'whenever.*treasure.*token',
            r'treasure.*tokens?.*you\s+control',
            r'sacrifice.*treasure',
            r'for\s+each.*treasure'
        ],
        'food': [
            r'whenever.*food.*token',
            r'food.*tokens?.*you\s+control',
            r'sacrifice.*food',
            r'for\s+each.*food'
        ],
        'clue': [
            r'whenever.*clue.*token',
            r'clue.*tokens?.*you\s+control',
            r'sacrifice.*clue',
            r'for\s+each.*clue'
        ],
        'blood': [
            r'whenever.*blood.*token',
            r'blood.*tokens?.*you\s+control',
            r'sacrifice.*blood',
            r'for\s+each.*blood'
        ],
        'creature': [
            r'whenever.*creature.*token.*(?:enters|created)',
            r'creature.*tokens?.*you\s+control',
            r'for\s+each.*creature.*token'
        ]
    }

    # Check for specific token types
    for token_type, patterns in specific_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                result['cares_about_tokens'] = True
                if token_type not in result['specific_token_types']:
                    result['specific_token_types'].append(token_type)
                if match.group(0) not in result['examples']:
                    result['examples'].append(match.group(0))

    # Check for general token patterns
    general_patterns = [
        r'if.*would create.*tokens?.*creates twice that many',  # Token doublers
        r'whenever.*(?:you\s+)?create.*\b(?:a\s+|an\s+)?token\b(?!\s+named)',  # "create a token" but not "create a token named"
        r'tokens?.*you\s+control\s+(?:get|have)',
        r'for\s+each.*token.*you\s+control'
    ]

    for pattern in general_patterns:
        match = re.search(pattern, text)
        if match:
            # Check if this is really a general pattern (no specific type in context)
            match_text = match.group(0)
            has_specific_type = any(
                token_type in match_text
                for token_type in ['treasure', 'food', 'clue', 'blood', 'creature']
            )

            if not has_specific_type:
                result['cares_about_tokens'] = True
                result['cares_about_any_tokens'] = True
                if match.group(0) not in result['examples']:
                    result['examples'].append(match.group(0))

    # Also check for death triggers that care about creatures (which includes creature tokens)
    if not result['specific_token_types'] or 'creature' not in result['specific_token_types']:
        creature_death_patterns = [
            r'whenever.*creature.*dies',
            r'whenever.*creature.*put into.*graveyard'
        ]
        for pattern in creature_death_patterns:
            if re.search(pattern, text):
                result['cares_about_tokens'] = True
                if 'creature' not in result['specific_token_types']:
                    result['specific_token_types'].append('creature')

    return result


def classify_token_mechanics(card: Dict) -> Dict:
    """
    Main classification function that extracts all token mechanics.

    Returns a comprehensive dictionary with all token information.
    """
    return {
        'token_creation': extract_token_creation(card),
        'token_doublers': extract_token_doublers(card),
        'anthems': extract_anthems(card),
        'token_synergies': extract_token_synergies(card),
        'token_type_preferences': extract_token_type_preferences(card)
    }
