"""
Card Draw & Card Advantage Extractors

Extracts card advantage mechanics from MTG cards:
- Draw effects (draw X cards, conditional draw)
- Wheel effects (each player draws 7)
- Tutors (search library for card)
- Mill effects (put cards from library into graveyard)
- Discard effects (target/each opponent discards)
- Looting (draw then discard)
- Impulse draw (exile and may cast)
- Card draw payoffs (triggers when you draw)
"""

import re
from typing import Dict, List, Optional


def extract_card_draw(card: Dict) -> Dict:
    """
    Extract card draw mechanics from a card.

    Returns:
        {
            'has_draw': bool,
            'draw_types': List[str],  # 'fixed', 'variable', 'conditional', 'repeatable'
            'draw_amount': Optional[int],  # For fixed amounts
            'draw_conditions': List[str],  # Conditions for drawing
            'draw_triggers': List[str],  # What triggers the draw
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_draw': False,
        'draw_types': [],
        'draw_amount': None,
        'draw_conditions': [],
        'draw_triggers': [],
        'examples': []
    }

    if not text:
        return result

    # Skip cards that just say "draw a card" as part of cycling or other keywords
    if 'cycling' in text and text.count('draw') == 1:
        return result

    # Pattern: "draw X card(s)" - matches "draw a card", "draw two cards", "draws X cards", etc.
    # Also need to match number words: two, three, four, etc.
    draw_pattern = r'draws?\s+(?:a\s+card|(?:an?\s+)?(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+cards?)'

    matches = list(re.finditer(draw_pattern, text))

    if matches:
        result['has_draw'] = True

        for match in matches:
            amount_str = match.group(1) if match.group(1) else '1'
            example = match.group(0)
            result['examples'].append(example)

            # Convert number words to digits
            number_words = {
                'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }

            # Determine draw type
            if amount_str in ['x', 'X']:
                result['draw_types'].append('variable')
            elif amount_str in number_words:
                amount = number_words[amount_str]
                if amount == 1:
                    # Only mark as 'single' if not already marked as 'fixed' from a larger draw
                    if 'fixed' not in result['draw_types']:
                        result['draw_types'].append('single')
                else:
                    result['draw_types'].append('fixed')
                    if result['draw_amount'] is None or amount > result['draw_amount']:
                        result['draw_amount'] = amount
            elif amount_str.isdigit():
                amount = int(amount_str)
                if amount == 1:
                    # Only mark as 'single' if not already marked as 'fixed' from a larger draw
                    if 'fixed' not in result['draw_types']:
                        result['draw_types'].append('single')
                else:
                    result['draw_types'].append('fixed')
                    if result['draw_amount'] is None or amount > result['draw_amount']:
                        result['draw_amount'] = amount

    # Check for repeatable draw (triggers, activated abilities)
    repeatable_patterns = [
        r'whenever.*draws?\s+(?:a\s+card|cards?)',
        r'at\s+the\s+beginning.*draws?\s+(?:a\s+card|cards?)',
        r'\{.*\}:.*draws?\s+(?:a\s+card|cards?)',  # Activated ability
        r'whenever.*enters.*draws?\s+(?:a\s+card|cards?)'
    ]

    for pattern in repeatable_patterns:
        if re.search(pattern, text):
            if 'repeatable' not in result['draw_types']:
                result['draw_types'].append('repeatable')
            break

    # Extract draw conditions
    conditional_patterns = [
        (r'whenever\s+(?:a|an|one\s+or\s+more)\s+(.*?)\s+(?:enters|dies|attacks)', 'trigger'),
        (r'if\s+(?:a|an)\s+(.*?),\s+draw', 'condition'),
        (r'when.*\s+(enters|dies|attacks)', 'etb/ltb'),
        (r'at\s+the\s+beginning\s+of.*?(\w+\s+(?:step|phase|upkeep))', 'timing')
    ]

    for pattern, condition_type in conditional_patterns:
        match = re.search(pattern, text)
        if match:
            result['draw_conditions'].append(condition_type)
            if condition_type not in result['draw_triggers']:
                result['draw_triggers'].append(condition_type)

    # Check if it's conditional draw
    if 'if' in text or 'when' in text or 'whenever' in text:
        if 'conditional' not in result['draw_types']:
            result['draw_types'].append('conditional')

    # Remove duplicates
    result['draw_types'] = list(set(result['draw_types']))
    result['draw_conditions'] = list(set(result['draw_conditions']))
    result['draw_triggers'] = list(set(result['draw_triggers']))

    return result


def extract_wheel_effects(card: Dict) -> Dict:
    """
    Extract wheel effects (everyone draws 7 or discards hand and draws).

    Returns:
        {
            'is_wheel': bool,
            'wheel_type': str,  # 'full_wheel', 'partial_wheel', 'windfall'
            'cards_drawn': Optional[int],
            'symmetrical': bool,  # Does it affect all players equally?
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_wheel': False,
        'wheel_type': None,
        'cards_drawn': None,
        'symmetrical': True,
        'examples': []
    }

    if not text:
        return result

    # Full wheel: discard hand, draw 7
    # Pattern 1: Simple "Each player discards their hand, then draws seven cards"
    full_wheel_pattern1 = r'each\s+player\s+discards?\s+(?:their|his\s+or\s+her|all\s+the\s+cards\s+in\s+their)\s+hands?,\s+then\s+draws?\s+(\w+)\s+cards?'
    match = re.search(full_wheel_pattern1, text)
    if match:
        result['is_wheel'] = True
        result['wheel_type'] = 'full_wheel'
        amount_str = match.group(1)
        # Convert number words to digits
        number_words = {'seven': 7, 'six': 6, 'five': 5, 'four': 4, 'three': 3, 'two': 2, 'one': 1}
        if amount_str in number_words:
            result['cards_drawn'] = number_words[amount_str]
        elif amount_str.isdigit():
            result['cards_drawn'] = int(amount_str)
        result['examples'].append(match.group(0))
        return result

    # Pattern 2: Multi-line wheel with complex text in between (Wheel of Misfortune)
    # Look for: "discards their hand" + "draws seven cards" (with anything in between)
    if 'discards their hand' in text or 'discard their hand' in text:
        draw_match = re.search(r'draws?\s+(\w+)\s+cards?', text)
        if draw_match:
            amount_str = draw_match.group(1)
            number_words = {'seven': 7, 'six': 6, 'five': 5, 'four': 4, 'three': 3, 'two': 2, 'one': 1}
            if amount_str in number_words or amount_str.isdigit():
                result['is_wheel'] = True
                result['wheel_type'] = 'full_wheel'
                if amount_str in number_words:
                    result['cards_drawn'] = number_words[amount_str]
                elif amount_str.isdigit():
                    result['cards_drawn'] = int(amount_str)
                result['examples'].append('wheel effect')
                return result

    # Partial wheel: each player draws X
    partial_wheel_pattern = r'each\s+player\s+draws?\s+(\d+|[xX])\s+cards?'
    match = re.search(partial_wheel_pattern, text)

    if match:
        result['is_wheel'] = True
        result['wheel_type'] = 'partial_wheel'
        amount_str = match.group(1)
        if amount_str.isdigit():
            result['cards_drawn'] = int(amount_str)
        result['examples'].append(match.group(0))
        return result

    # Windfall: each player discards and draws equal to player with most cards
    if 'each player discards' in text and 'draws cards equal' in text:
        result['is_wheel'] = True
        result['wheel_type'] = 'windfall'
        result['examples'].append('windfall effect')
        return result

    # Asymmetrical wheel (you benefit more)
    asymmetric_patterns = [
        r'each\s+opponent\s+draws?\s+(\d+).*?you\s+draws?\s+(\d+)',
        r'you\s+draws?\s+(\d+).*?each\s+opponent\s+draws?\s+(\d+)'
    ]

    for pattern in asymmetric_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_wheel'] = True
            result['wheel_type'] = 'asymmetric_draw'
            result['symmetrical'] = False
            result['examples'].append(match.group(0))
            return result

    return result


def extract_tutors(card: Dict) -> Dict:
    """
    Extract tutor effects (search library for cards).

    Returns:
        {
            'is_tutor': bool,
            'tutor_type': str,  # 'creature', 'instant', 'sorcery', 'artifact', 'enchantment', 'land', 'any'
            'restrictions': List[str],  # CMC restrictions, color restrictions, etc.
            'destination': str,  # 'hand', 'battlefield', 'top', 'graveyard'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_tutor': False,
        'tutor_type': None,
        'restrictions': [],
        'destination': None,
        'examples': []
    }

    if not text:
        return result

    # Main tutor pattern: "search your library for"
    if 'search your library for' not in text and 'search their library for' not in text:
        return result

    result['is_tutor'] = True

    # Determine tutor type by what it searches for
    # Check for combined types first (instant or sorcery, artifact or enchantment)
    card_types = {
        'instant_or_sorcery': r'instant\s+or\s+sorcery\s+card',
        'artifact_or_enchantment': r'artifact\s+or\s+enchantment\s+card',
        'creature': r'creature\s+card',
        'instant': r'instant\s+card',
        'sorcery': r'sorcery\s+card',
        'artifact': r'artifact\s+card',
        'enchantment': r'enchantment\s+card',
        'land': r'land\s+card',
        'planeswalker': r'planeswalker\s+card',
        'any': r'(?:a|any)\s+card'
    }

    for card_type, pattern in card_types.items():
        if re.search(pattern, text):
            result['tutor_type'] = card_type
            break

    # Extract restrictions
    restriction_patterns = [
        (r'with\s+(?:converted\s+)?mana\s+(?:cost|value)\s+(\d+)\s+or\s+less', 'cmc_restriction'),
        (r'with\s+mana\s+value\s+[xX]\s+or\s+less', 'cmc_x_or_less'),
        (r'with\s+(?:the\s+same|a different)\s+name', 'name_restriction'),
        (r'that\s+shares?\s+a\s+(?:creature\s+)?type', 'type_sharing'),
        (r'(?:basic|nonbasic)\s+land', 'land_type'),
        (r'(?:white|blue|black|red|green)', 'color_restriction')
    ]

    for pattern, restriction in restriction_patterns:
        if re.search(pattern, text):
            result['restrictions'].append(restriction)

    # Determine destination
    destination_patterns = [
        (r'(?:put|place)\s+(?:it|that\s+card|them)\s+into\s+your\s+hand', 'hand'),
        (r'(?:put|place)\s+(?:it|that\s+card)\s+onto\s+the\s+battlefield', 'battlefield'),
        (r'(?:put|place)\s+(?:it|that\s+card)\s+on\s+top\s+of\s+your\s+library', 'top'),
        (r'(?:put|place)\s+(?:it|that\s+card)\s+into\s+your\s+graveyard', 'graveyard'),
        (r'reveal\s+(?:it|that\s+card)', 'revealed')
    ]

    for pattern, destination in destination_patterns:
        if re.search(pattern, text):
            result['destination'] = destination
            break

    # Default to hand if no destination specified
    if not result['destination']:
        result['destination'] = 'hand'

    # Extract example
    match = re.search(r'search your library for.*?\.', text)
    if match:
        result['examples'].append(match.group(0))

    return result


def extract_mill_effects(card: Dict) -> Dict:
    """
    Extract mill effects (put cards from library into graveyard).

    Returns:
        {
            'has_mill': bool,
            'mill_targets': List[str],  # 'self', 'opponent', 'each_opponent', 'each_player', 'target_player'
            'mill_amount': Optional[int],
            'mill_type': str,  # 'fixed', 'variable', 'until'
            'repeatable': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_mill': False,
        'mill_targets': [],
        'mill_amount': None,
        'mill_type': None,
        'repeatable': False,
        'examples': []
    }

    if not text:
        return result

    # Mill patterns: "put X cards from library into graveyard" or "mills X"
    mill_patterns = [
        r'mills?\s+(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+cards?',
        r'mills?\s+(?:half\s+)?(?:their|your)',  # mills half their library
        r'(?:puts?|place)\s+(?:the\s+)?(?:top\s+)?(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+cards?\s+from.*?library.*?into.*?graveyard',
        r'from.*?library.*?into.*?graveyard\s+until'
    ]

    for pattern in mill_patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            result['has_mill'] = True

            for match in matches:
                result['examples'].append(match.group(0))

                # Determine mill amount and type
                if 'until' in match.group(0):
                    result['mill_type'] = 'until'
                elif 'half' in match.group(0):
                    result['mill_type'] = 'variable'
                else:
                    # Try to extract amount from the first capturing group if it exists
                    try:
                        amount_str = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                    except IndexError:
                        amount_str = None

                    if amount_str:
                        # Convert number words to digits
                        number_words = {
                            'two': 2, 'three': 3, 'four': 4, 'five': 5,
                            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                        }

                        if amount_str in ['x', 'X']:
                            result['mill_type'] = 'variable'
                        elif amount_str in number_words:
                            result['mill_type'] = 'fixed'
                            amount = number_words[amount_str]
                            if result['mill_amount'] is None or amount > result['mill_amount']:
                                result['mill_amount'] = amount
                        elif amount_str.isdigit():
                            result['mill_type'] = 'fixed'
                            amount = int(amount_str)
                            if result['mill_amount'] is None or amount > result['mill_amount']:
                                result['mill_amount'] = amount

    if not result['has_mill']:
        return result

    # Determine mill targets
    target_patterns = [
        (r'you\s+(?:put|mill)', 'self'),
        (r'target\s+(?:player|opponent)\s+(?:puts?|mills?)', 'target_player'),
        (r'each\s+opponent\s+(?:puts?|mills?)', 'each_opponent'),
        (r'each\s+player\s+(?:puts?|mills?)', 'each_player'),
        (r'(?:an|target)\s+opponent\s+(?:puts?|mills?)', 'opponent')
    ]

    for pattern, target in target_patterns:
        if re.search(pattern, text):
            result['mill_targets'].append(target)

    # Check if repeatable
    if re.search(r'whenever|at\s+the\s+beginning|\{.*\}:', text):
        result['repeatable'] = True

    # Remove duplicates
    result['mill_targets'] = list(set(result['mill_targets']))

    return result


def extract_discard_effects(card: Dict) -> Dict:
    """
    Extract discard effects.

    Returns:
        {
            'has_discard': bool,
            'discard_targets': List[str],  # 'self', 'target_opponent', 'each_opponent', 'each_player'
            'discard_amount': Optional[int],
            'discard_type': str,  # 'fixed', 'variable', 'choice', 'random', 'hand'
            'is_optional': bool,
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_discard': False,
        'discard_targets': [],
        'discard_amount': None,
        'discard_type': None,
        'is_optional': False,
        'examples': []
    }

    if not text:
        return result

    # Discard pattern - updated to catch more variants including "that player discards"
    # Note: "that card" is included to catch "that player discards that card" (Thoughtseize)
    discard_pattern = r'(?:that\s+player\s+)?discards?\s+(?:that\s+card|a\s+card|(?:a\s+)?(?:creature|land|nonland|noncreature)\s+card|(?:their|your|his\s+or\s+her|all\s+the\s+cards\s+in\s+their)\s+hand|(\d+|[xX]|two|three|four|five|six|seven|eight|nine|ten)\s+cards?)'

    matches = list(re.finditer(discard_pattern, text))

    if not matches:
        return result

    result['has_discard'] = True

    for match in matches:
        result['examples'].append(match.group(0))

        # Determine discard amount and type
        if 'hand' in match.group(0):
            result['discard_type'] = 'hand'
        else:
            amount_str = match.group(1) if match.group(1) else '1'

            # Convert number words to digits
            number_words = {
                'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }

            if amount_str in ['x', 'X']:
                result['discard_type'] = 'variable'
            elif amount_str in number_words:
                result['discard_type'] = 'fixed'
                amount = number_words[amount_str]
                if result['discard_amount'] is None or amount > result['discard_amount']:
                    result['discard_amount'] = amount
            elif amount_str.isdigit():
                result['discard_type'] = 'fixed'
                amount = int(amount_str)
                if result['discard_amount'] is None or amount > result['discard_amount']:
                    result['discard_amount'] = amount

    # Check for choice or random
    if 'at random' in text:
        result['discard_type'] = 'random'
    elif 'you choose' in text:
        result['discard_type'] = 'choice'
    elif 'of your choice' in text or 'of their choice' in text:
        result['discard_type'] = 'choice'

    # Check if optional
    if 'may discard' in text:
        result['is_optional'] = True

    # Determine discard targets - updated to catch more patterns
    target_patterns = [
        # Check "whenever you discard" first for payoff cards (Bone Miser)
        (r'whenever\s+you\s+discard', 'self'),
        # Standard patterns
        (r'you\s+discards?', 'self'),
        (r'target\s+player.*?discards?', 'target_opponent'),
        (r'that\s+player\s+discards?', 'target_opponent'),
        (r'target\s+opponent\s+discards?', 'target_opponent'),
        (r'each\s+opponent\s+discards?', 'each_opponent'),
        (r'each\s+player\s+discards?', 'each_player'),
        (r'(?:an|target)\s+opponent\s+discards?', 'opponent')
    ]

    for pattern, target in target_patterns:
        if re.search(pattern, text):
            result['discard_targets'].append(target)

    # Remove duplicates
    result['discard_targets'] = list(set(result['discard_targets']))

    return result


def extract_looting_effects(card: Dict) -> Dict:
    """
    Extract looting effects (draw then discard).

    Returns:
        {
            'is_looting': bool,
            'draw_amount': int,
            'discard_amount': int,
            'net_advantage': int,  # draw - discard
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_looting': False,
        'draw_amount': 0,
        'discard_amount': 0,
        'net_advantage': 0,
        'examples': []
    }

    if not text:
        return result

    # Looting pattern: draw X, then discard Y
    # Updated to handle "Draw X. Then discard Y" (with period instead of comma)
    looting_pattern = r'draws?\s+(?:a\s+card|(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+cards?)[\s,.]+then\s+discards?\s+(?:a\s+card|(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+cards?)'

    match = re.search(looting_pattern, text)

    if match:
        result['is_looting'] = True
        result['examples'].append(match.group(0))

        draw_str = match.group(1) if match.group(1) else '1'
        discard_str = match.group(2) if match.group(2) else '1'

        # Convert number words to digits
        number_words = {
            'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        result['draw_amount'] = number_words.get(draw_str, int(draw_str) if draw_str.isdigit() else 1)
        result['discard_amount'] = number_words.get(discard_str, int(discard_str) if discard_str.isdigit() else 1)
        result['net_advantage'] = result['draw_amount'] - result['discard_amount']

    return result


def extract_impulse_draw(card: Dict) -> Dict:
    """
    Extract impulse draw effects (exile and may cast/play).

    Returns:
        {
            'has_impulse': bool,
            'impulse_amount': Optional[int],
            'duration': str,  # 'turn', 'until_end_of_turn', 'permanent'
            'card_types': List[str],  # What types can be cast
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'has_impulse': False,
        'impulse_amount': None,
        'duration': None,
        'card_types': [],
        'examples': []
    }

    if not text:
        return result

    # Check if this is an impulse draw effect by looking for exile + play/cast pattern
    # Pattern needs to be more flexible to catch different wordings

    # Must have "exile" and "may play" or "may cast" or "you may play"
    has_exile = 'exile' in text
    has_may_play = 'may play' in text or 'may cast' in text or 'you may play' in text

    if not (has_exile and has_may_play):
        return result

    result['has_impulse'] = True

    # Extract the amount of cards exiled
    # Pattern 1: "exile the top X cards"
    amount_pattern1 = r'exile\s+the\s+top\s+(\w+)\s+cards?'
    match = re.search(amount_pattern1, text)
    if match:
        amount_str = match.group(1)
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        if amount_str in number_words:
            result['impulse_amount'] = number_words[amount_str]
        elif amount_str.isdigit():
            result['impulse_amount'] = int(amount_str)
        result['examples'].append(match.group(0))

    # Pattern 2: "exile the top card"
    if result['impulse_amount'] is None:
        if 'exile the top card' in text:
            result['impulse_amount'] = 1
            result['examples'].append('exile the top card')

    # Determine duration
    if 'until the end of your next turn' in text:
        result['duration'] = 'turn'
    elif 'until end of turn' in text:
        result['duration'] = 'until_end_of_turn'
    elif 'this turn' in text:
        result['duration'] = 'turn'
    elif 'until' in text and 'leaves' in text:
        result['duration'] = 'permanent'
    else:
        result['duration'] = 'turn'

    # Determine card types that can be cast
    if 'may play those cards' in text or 'may play them' in text:
        result['card_types'].append('any')
    elif 'may play that card' in text or 'may play it' in text:
        result['card_types'].append('any')
    elif 'may cast' in text:
        result['card_types'].append('nonland')
    else:
        result['card_types'].append('any')

    return result


def extract_draw_payoffs(card: Dict) -> Dict:
    """
    Extract card draw payoff effects (triggers when you draw).

    Returns:
        {
            'is_draw_payoff': bool,
            'trigger_type': str,  # 'first_draw', 'second_draw', 'any_draw', 'multiple_draws'
            'payoff_effects': List[str],  # 'damage', 'life', 'token', 'counter', 'scry', 'other'
            'examples': List[str]
        }
    """
    text = card.get('oracle_text', '').lower()

    result = {
        'is_draw_payoff': False,
        'trigger_type': None,
        'payoff_effects': [],
        'examples': []
    }

    if not text:
        return result

    # Draw trigger patterns
    draw_trigger_patterns = [
        (r'whenever\s+you\s+draws?\s+your\s+second\s+card', 'second_draw'),  # Check second before first
        (r'whenever\s+you\s+draws?\s+your\s+first\s+card', 'first_draw'),
        (r'whenever\s+you\s+draws?\s+two\s+or\s+more\s+cards', 'multiple_draws'),
        (r'whenever\s+you\s+draws?\s+a\s+card', 'any_draw'),
        (r'whenever.*draws?\s+a\s+card', 'opponent_draw')
    ]

    for pattern, trigger in draw_trigger_patterns:
        match = re.search(pattern, text)
        if match:
            result['is_draw_payoff'] = True
            result['trigger_type'] = trigger
            result['examples'].append(match.group(0))
            break

    if not result['is_draw_payoff']:
        return result

    # Determine payoff effects
    payoff_patterns = [
        (r'deals?\s+\d+\s+damage', 'damage'),
        (r'gains?\s+\d+\s+life', 'life'),
        (r'(?:create|creates?)\s+a.*?token', 'token'),
        (r'(?:put|puts?)\s+a\s+\+1/\+1\s+counter', 'counter'),
        (r'scrys?\s+\d+', 'scry'),
        (r'loses?\s+\d+\s+life', 'life_loss')
    ]

    for pattern, effect in payoff_patterns:
        if re.search(pattern, text):
            result['payoff_effects'].append(effect)

    if not result['payoff_effects']:
        result['payoff_effects'].append('other')

    return result


def classify_card_advantage(card: Dict) -> Dict:
    """
    Main classification function that extracts all card advantage mechanics.

    Returns a comprehensive dictionary with all card advantage information.
    """
    return {
        'card_draw': extract_card_draw(card),
        'wheel_effects': extract_wheel_effects(card),
        'tutors': extract_tutors(card),
        'mill': extract_mill_effects(card),
        'discard': extract_discard_effects(card),
        'looting': extract_looting_effects(card),
        'impulse_draw': extract_impulse_draw(card),
        'draw_payoffs': extract_draw_payoffs(card)
    }
