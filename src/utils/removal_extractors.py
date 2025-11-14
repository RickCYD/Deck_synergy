

MIGRATION NOTICE:
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

"""
Removal Mechanics Extractors
Extract and classify different types of removal spells from card text.
"""

import re
from typing import Dict, List, Optional


def extract_counterspell_mechanics(card: Dict) -> List[Dict]:
    """
    Extract counterspell mechanics from a card.

    Types of counterspells:
    - Unconditional counter (Counter target spell)
    - Conditional counter (Counter target noncreature spell, Counter unless...)
    - Counter with restrictions (Counter target spell with CMC <= X)
    - Counter with additional effects

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of counterspell mechanic dictionaries
    """
    mechanics = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return mechanics

    # Unconditional counter
    if re.search(r'\bcounter target spell\b(?!.*unless)', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'unconditional',
            'description': 'Counter target spell'
        })

    # Counter noncreature spell
    if re.search(r'counter target (noncreature|non-creature) spell', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'conditional_type',
            'description': 'Counter target noncreature spell',
            'restriction': 'noncreature'
        })

    # Counter creature spell
    if re.search(r'counter target creature spell', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'conditional_type',
            'description': 'Counter target creature spell',
            'restriction': 'creature'
        })

    # Counter instant/sorcery
    if re.search(r'counter target instant or sorcery', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'conditional_type',
            'description': 'Counter target instant or sorcery spell',
            'restriction': 'instant_sorcery'
        })

    # Counter with CMC restriction
    cmc_match = re.search(r'counter target spell.*(?:mana value|converted mana cost|cmc).*?(\d+)', oracle_text)
    if cmc_match:
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'cmc_restriction',
            'description': f'Counter target spell with CMC restriction',
            'cmc_value': int(cmc_match.group(1))
        })

    # Counter unless (soft counter)
    if re.search(r'counter.*unless', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'soft_counter',
            'description': 'Counter target spell unless controller pays'
        })

    # Counter with additional effect
    if re.search(r'counter target spell.*\. (draw|scry|create|put|exile)', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'counter_plus',
            'description': 'Counter target spell with additional effect'
        })

    # Redirect spell
    if re.search(r'change the target', oracle_text) or re.search(r'choose new targets', oracle_text):
        mechanics.append({
            'type': 'counterspell',
            'subtype': 'redirect',
            'description': 'Change or redirect spell targets'
        })

    return mechanics


def extract_destroy_mechanics(card: Dict) -> List[Dict]:
    """
    Extract destroy target mechanics from a card.

    Types of destroy effects:
    - Destroy target creature
    - Destroy target permanent
    - Destroy target artifact/enchantment
    - Destroy with restrictions (nonblack, CMC, etc.)
    - Destroy all (board wipes)

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of destroy mechanic dictionaries
    """
    mechanics = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return mechanics

    # Destroy target creature (unconditional)
    if re.search(r'destroy target creature(?!\s+with|\s+an|\s+unless)', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'creature_unconditional',
            'description': 'Destroy target creature',
            'target': 'creature'
        })

    # Destroy target creature with restriction
    restriction_match = re.search(r'destroy target (nonblack|non-black|nonwhite|non-white|nonblue|non-blue|nonred|non-red|nongreen|non-green) creature', oracle_text)
    if restriction_match:
        mechanics.append({
            'type': 'destroy',
            'subtype': 'creature_conditional',
            'description': f'Destroy target {restriction_match.group(1)} creature',
            'target': 'creature',
            'restriction': restriction_match.group(1).replace('non-', '')
        })

    # Destroy target creature with power/toughness restriction
    if re.search(r'destroy target creature with (power|toughness)', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'creature_conditional',
            'description': 'Destroy target creature with power/toughness restriction',
            'target': 'creature',
            'restriction': 'power_toughness'
        })

    # Destroy target artifact
    if re.search(r'destroy target artifact', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'artifact',
            'description': 'Destroy target artifact',
            'target': 'artifact'
        })

    # Destroy target enchantment
    if re.search(r'destroy target enchantment', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'enchantment',
            'description': 'Destroy target enchantment',
            'target': 'enchantment'
        })

    # Destroy target permanent
    if re.search(r'destroy target (nonland )?permanent', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'permanent',
            'description': 'Destroy target permanent',
            'target': 'permanent'
        })

    # Destroy target planeswalker
    if re.search(r'destroy target planeswalker', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'planeswalker',
            'description': 'Destroy target planeswalker',
            'target': 'planeswalker'
        })

    # Destroy all creatures (board wipe)
    if re.search(r'destroy all creatures', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'mass_creatures',
            'description': 'Destroy all creatures',
            'target': 'all_creatures',
            'is_board_wipe': True
        })

    # Destroy all permanents (mass removal)
    if re.search(r'destroy all (artifacts|enchantments|permanents)', oracle_text):
        mechanics.append({
            'type': 'destroy',
            'subtype': 'mass_removal',
            'description': 'Destroy all permanents of type',
            'is_board_wipe': True
        })

    return mechanics


def extract_exile_mechanics(card: Dict) -> List[Dict]:
    """
    Extract exile target mechanics from a card.

    Types of exile effects:
    - Exile target creature/permanent
    - Exile temporarily (until leaves battlefield)
    - Exile with return clause
    - Exile from graveyard
    - Exile face down (manifest, morph)

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of exile mechanic dictionaries
    """
    mechanics = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return mechanics

    # Exile target creature (permanent)
    if re.search(r'exile target creature(?!.*return|.*until)', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'creature_permanent',
            'description': 'Exile target creature permanently',
            'target': 'creature',
            'is_permanent': True
        })

    # Exile target permanent
    if re.search(r'exile target (nonland )?permanent(?!.*return|.*until)', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'permanent_permanent',
            'description': 'Exile target permanent permanently',
            'target': 'permanent',
            'is_permanent': True
        })

    # Exile temporarily (flickering)
    if re.search(r'exile.*return.*(to the battlefield|under)', oracle_text):
        # Check if it's end of turn or immediate
        if re.search(r'return.*at the beginning of the next end step', oracle_text):
            mechanics.append({
                'type': 'exile',
                'subtype': 'temporary_eot',
                'description': 'Exile and return at end of turn',
                'target': 'varies',
                'is_permanent': False,
                'return_timing': 'end_of_turn'
            })
        elif re.search(r'return.*immediately', oracle_text) or re.search(r'then return', oracle_text):
            mechanics.append({
                'type': 'exile',
                'subtype': 'flicker',
                'description': 'Exile and return immediately (flicker)',
                'target': 'varies',
                'is_permanent': False,
                'return_timing': 'immediate'
            })

    # Exile until leaves battlefield
    if re.search(r'exile.*until.*leaves the battlefield', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'oblivion_ring',
            'description': 'Exile until source leaves battlefield',
            'target': 'varies',
            'is_permanent': False,
            'return_condition': 'source_leaves'
        })

    # Exile from graveyard
    if re.search(r'exile.*from.*graveyard', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'graveyard_hate',
            'description': 'Exile card from graveyard',
            'target': 'graveyard',
            'is_graveyard_hate': True
        })

    # Exile top cards of library (mill exile)
    if re.search(r'exile.*top.*cards? of.*library', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'mill_exile',
            'description': 'Exile cards from top of library',
            'target': 'library'
        })

    # Exile face down
    if re.search(r'exile.*face down', oracle_text):
        mechanics.append({
            'type': 'exile',
            'subtype': 'face_down',
            'description': 'Exile face down',
            'is_hidden': True
        })

    return mechanics


def extract_bounce_mechanics(card: Dict) -> List[Dict]:
    """
    Extract return to hand mechanics from a card.

    Types of bounce effects:
    - Return target creature to hand
    - Return target permanent to hand
    - Return all creatures to hand (mass bounce)
    - Return to owner's hand vs controller's hand
    - Return to top of library (pseudo-bounce)

    Args:
        card: Card dictionary with oracle_text

    Returns:
        List of bounce mechanic dictionaries
    """
    mechanics = []
    oracle_text = card.get('oracle_text', '').lower()

    if not oracle_text:
        return mechanics

    # Return target creature to hand
    if re.search(r'return target creature to (its owner\'?s|their owner\'?s) hand', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'creature',
            'description': 'Return target creature to hand',
            'target': 'creature',
            'destination': 'hand'
        })

    # Return target permanent to hand
    if re.search(r'return target (nonland )?permanent to (its owner\'?s|their owner\'?s) hand', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'permanent',
            'description': 'Return target permanent to hand',
            'target': 'permanent',
            'destination': 'hand'
        })

    # Return target artifact/enchantment to hand
    if re.search(r'return target (artifact|enchantment) to (its owner\'?s|their owner\'?s) hand', oracle_text):
        target_type = re.search(r'return target (artifact|enchantment)', oracle_text).group(1)
        mechanics.append({
            'type': 'bounce',
            'subtype': target_type,
            'description': f'Return target {target_type} to hand',
            'target': target_type,
            'destination': 'hand'
        })

    # Return all creatures to hand (mass bounce)
    if re.search(r'return all creatures to their owner\'?s? hands?', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'mass_creatures',
            'description': 'Return all creatures to hand',
            'target': 'all_creatures',
            'destination': 'hand',
            'is_mass_effect': True
        })

    # Return all nonland permanents (mass bounce)
    if re.search(r'return all (nonland )?permanents to their owner\'?s? hands?', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'mass_permanents',
            'description': 'Return all permanents to hand',
            'target': 'all_permanents',
            'destination': 'hand',
            'is_mass_effect': True
        })

    # Put on top of library (pseudo-bounce)
    if re.search(r'put target (creature|permanent) on top of (its owner\'?s|their) library', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'library_top',
            'description': 'Put target on top of library',
            'destination': 'library_top',
            'is_tempo': True
        })

    # Put on bottom of library
    if re.search(r'put target (creature|permanent) on the bottom of (its owner\'?s|their) library', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'library_bottom',
            'description': 'Put target on bottom of library',
            'destination': 'library_bottom'
        })

    # Return your own permanent to hand (self-bounce)
    if re.search(r'return (a|target) (creature|permanent) you (own|control) to (your|its owner\'?s) hand', oracle_text):
        mechanics.append({
            'type': 'bounce',
            'subtype': 'self_bounce',
            'description': 'Return your own permanent to hand',
            'target': 'own_permanent',
            'destination': 'hand',
            'is_self_target': True
        })

    return mechanics


def classify_removal_type(card: Dict) -> Dict:
    """
    Classify all removal mechanics in a card and return summary.

    Args:
        card: Card dictionary with oracle_text

    Returns:
        Dictionary with all removal mechanics found
    """
    return {
        'card_name': card.get('name', 'Unknown'),
        'counterspells': extract_counterspell_mechanics(card),
        'destroy_effects': extract_destroy_mechanics(card),
        'exile_effects': extract_exile_mechanics(card),
        'bounce_effects': extract_bounce_mechanics(card),
        'total_removal_mechanics': (
            len(extract_counterspell_mechanics(card)) +
            len(extract_destroy_mechanics(card)) +
            len(extract_exile_mechanics(card)) +
            len(extract_bounce_mechanics(card))
        )
    }
