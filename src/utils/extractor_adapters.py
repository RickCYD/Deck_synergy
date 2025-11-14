"""
Backward Compatibility Adapters for Legacy Extractors

This module provides backward-compatible wrapper functions that use the
unified parser internally, allowing existing code to work without changes
while benefiting from the new unified architecture.

MIGRATION GUIDE:
- Old code using extractors will continue to work
- New code should use UnifiedCardParser directly
- These adapters will be deprecated in future versions

Usage:
    # Old way (still works):
    from src.utils.token_extractors import extract_token_creation
    result = extract_token_creation(card)

    # New way (recommended):
    from src.core.card_parser import UnifiedCardParser
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)
"""

import warnings
from typing import Dict, List, Optional, Any
from src.core.card_parser import UnifiedCardParser, CardAbilities

# Singleton parser instance for performance
_parser_instance = None


def _get_parser() -> UnifiedCardParser:
    """Get or create the singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = UnifiedCardParser()
    return _parser_instance


def _deprecation_warning(old_function: str, new_approach: str):
    """Issue a deprecation warning."""
    warnings.warn(
        f"{old_function} is deprecated. Use {new_approach} instead. "
        f"See UNIFIED_ARCHITECTURE_GUIDE.md for details.",
        DeprecationWarning,
        stacklevel=3
    )


# =============================================================================
# TOKEN EXTRACTION ADAPTERS
# =============================================================================

def extract_token_creation(card: Dict) -> Dict:
    """
    Extract token creation mechanics from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'creates_tokens': bool,
            'token_types': List[Dict],
            'creation_type': str,
            'repeatable': bool,
            'examples': List[str]
        }
    """
    _deprecation_warning(
        "extract_token_creation()",
        "UnifiedCardParser.parse_card() and check abilities.creates_tokens"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'creates_tokens': abilities.creates_tokens,
        'token_types': [],
        'creation_type': None,
        'repeatable': False,
        'examples': []
    }

    if not abilities.creates_tokens:
        return result

    # Extract token info from triggers
    for trigger in abilities.triggers:
        if trigger.effect_type and 'token' in trigger.effect_type:
            # Infer creation type from event
            if trigger.event == 'etb':
                result['creation_type'] = 'etb'
            elif 'cast' in trigger.event:
                result['creation_type'] = 'triggered'
                result['repeatable'] = True
            elif trigger.event == 'death':
                result['creation_type'] = 'dies'
            elif trigger.event == 'attack':
                result['creation_type'] = 'combat'

            # Add token type info (simplified)
            if trigger.metadata:
                token_info = {
                    'count': trigger.value if trigger.value else 1,
                    'power': '1',
                    'toughness': '1',
                    'type': trigger.metadata.get('token_type', 'Unknown'),
                    'colors': [],
                    'keywords': []
                }
                result['token_types'].append(token_info)

    # Check activated abilities for token creation
    for activated in abilities.activated_abilities:
        if activated.effect and 'token' in activated.effect.lower():
            result['creation_type'] = 'activated'
            result['repeatable'] = True

    return result


# =============================================================================
# ARISTOCRATS EXTRACTION ADAPTERS
# =============================================================================

def detect_death_drain_trigger(oracle_text: str) -> int:
    """
    Detect death drain triggers.

    DEPRECATED: Create card dict and use UnifiedCardParser.parse_card() instead.

    Returns the amount of life drained per death.
    """
    _deprecation_warning(
        "detect_death_drain_trigger()",
        "UnifiedCardParser.parse_card() and check death triggers"
    )

    # Create minimal card dict for parsing
    card = {'oracle_text': oracle_text}
    parser = _get_parser()
    abilities = parser.parse_card(card)

    # Look for death triggers with damage/drain effects
    for trigger in abilities.triggers:
        if trigger.event == 'death':
            if trigger.effect in ['damage', 'drain', 'life_loss']:
                return int(trigger.value) if trigger.value else 1

    return 0


def is_sacrifice_outlet(oracle_text: str) -> bool:
    """
    Detect sacrifice outlets.

    DEPRECATED: Create card dict and use UnifiedCardParser.parse_card() instead.

    Returns True if the card is a sacrifice outlet.
    """
    _deprecation_warning(
        "is_sacrifice_outlet()",
        "UnifiedCardParser.parse_card() and check activated_abilities"
    )

    card = {'oracle_text': oracle_text}
    parser = _get_parser()
    abilities = parser.parse_card(card)

    # Check for sacrifice in activated abilities
    for activated in abilities.activated_abilities:
        if activated.cost and 'sacrifice' in activated.cost.lower():
            if 'creature' in activated.cost.lower():
                return True

    return False


def has_death_trigger(oracle_text: str) -> bool:
    """
    Detect if a card has ANY death trigger.

    DEPRECATED: Create card dict and use UnifiedCardParser.parse_card() instead.

    Returns True if the card triggers on creature death.
    """
    _deprecation_warning(
        "has_death_trigger()",
        "UnifiedCardParser.parse_card() and check triggers"
    )

    card = {'oracle_text': oracle_text}
    parser = _get_parser()
    abilities = parser.parse_card(card)

    # Check for death triggers
    for trigger in abilities.triggers:
        if trigger.event == 'death':
            return True

    return False


# =============================================================================
# KEYWORD EXTRACTION ADAPTERS
# =============================================================================

def extract_keywords(card: Dict) -> Dict:
    """
    Extract keywords from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'keywords': Set[str],
            'grants_keywords': bool,
            'granted_keywords': Set[str]
        }
    """
    _deprecation_warning(
        "extract_keywords()",
        "UnifiedCardParser.parse_card() and use abilities.keywords"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'keywords': abilities.keywords.copy(),
        'grants_keywords': False,
        'granted_keywords': set()
    }

    # Check if card grants keywords to others
    for trigger in abilities.triggers:
        if trigger.effect in ['haste', 'vigilance', 'lifelink', 'double strike',
                              'flying', 'trample', 'menace', 'deathtouch']:
            result['grants_keywords'] = True
            result['granted_keywords'].add(trigger.effect)

    for static in abilities.static_abilities:
        if static.effect_type == 'keyword_grant':
            result['grants_keywords'] = True
            if static.metadata and 'keyword' in static.metadata:
                result['granted_keywords'].add(static.metadata['keyword'])

    return result


# =============================================================================
# ETB EXTRACTION ADAPTERS
# =============================================================================

def extract_etb_effects(card: Dict) -> Dict:
    """
    Extract ETB effects from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'has_etb': bool,
            'etb_effects': List[str],
            'value': float
        }
    """
    _deprecation_warning(
        "extract_etb_effects()",
        "UnifiedCardParser.parse_card() and check abilities.has_etb"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'has_etb': abilities.has_etb,
        'etb_effects': [],
        'value': 0.0
    }

    if not abilities.has_etb:
        return result

    # Collect ETB effects
    for trigger in abilities.triggers:
        if trigger.event == 'etb':
            if trigger.effect:
                result['etb_effects'].append(trigger.effect)
            result['value'] += trigger.value if trigger.value else 1.0

    return result


# =============================================================================
# TRIBAL EXTRACTION ADAPTERS
# =============================================================================

def extract_creature_types(card: Dict) -> Dict:
    """
    Extract creature types from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'creature_types': Set[str],
            'is_tribal': bool,
            'tribal_synergies': List[str]
        }
    """
    _deprecation_warning(
        "extract_creature_types()",
        "UnifiedCardParser.parse_card() and use abilities.creature_types"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'creature_types': abilities.creature_types.copy(),
        'is_tribal': len(abilities.creature_types) > 0,
        'tribal_synergies': []
    }

    # Check for tribal synergies in triggers/static abilities
    for trigger in abilities.triggers:
        if trigger.condition and any(
            tribal in trigger.condition.lower()
            for tribal in ['ally', 'human', 'elf', 'goblin', 'wizard']
        ):
            result['tribal_synergies'].append(trigger.condition)

    return result


# =============================================================================
# CARD ADVANTAGE EXTRACTION ADAPTERS
# =============================================================================

def extract_card_draw(card: Dict) -> Dict:
    """
    Extract card draw effects from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'draws_cards': bool,
            'draw_amount': int,
            'is_repeatable': bool
        }
    """
    _deprecation_warning(
        "extract_card_draw()",
        "UnifiedCardParser.parse_card() and check abilities.is_draw"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'draws_cards': abilities.is_draw,
        'draw_amount': 0,
        'is_repeatable': False
    }

    if not abilities.is_draw:
        return result

    # Find draw effects
    for trigger in abilities.triggers:
        if trigger.effect == 'draw':
            result['draw_amount'] = int(trigger.value) if trigger.value else 1
            result['is_repeatable'] = trigger.event != 'etb'

    for activated in abilities.activated_abilities:
        if activated.effect and 'draw' in activated.effect.lower():
            result['is_repeatable'] = True
            # Try to extract amount from effect text
            import re
            match = re.search(r'draw (\d+)', activated.effect.lower())
            if match:
                result['draw_amount'] = max(result['draw_amount'], int(match.group(1)))
            else:
                result['draw_amount'] = max(result['draw_amount'], 1)

    return result


# =============================================================================
# REMOVAL EXTRACTION ADAPTERS
# =============================================================================

def extract_removal_effects(card: Dict) -> Dict:
    """
    Extract removal effects from a card.

    DEPRECATED: Use UnifiedCardParser.parse_card() instead.

    Returns:
        {
            'is_removal': bool,
            'removal_type': str,
            'targets': str
        }
    """
    _deprecation_warning(
        "extract_removal_effects()",
        "UnifiedCardParser.parse_card() and check abilities.is_removal"
    )

    parser = _get_parser()
    abilities = parser.parse_card(card)

    result = {
        'is_removal': abilities.is_removal,
        'removal_type': None,
        'targets': 'single'
    }

    if not abilities.is_removal:
        return result

    oracle_text = card.get('oracle_text', '').lower()

    # Determine removal type
    if 'destroy' in oracle_text:
        result['removal_type'] = 'destroy'
    elif 'exile' in oracle_text:
        result['removal_type'] = 'exile'
    elif 'damage' in oracle_text:
        result['removal_type'] = 'damage'
    elif 'return' in oracle_text and ('hand' in oracle_text or 'library' in oracle_text):
        result['removal_type'] = 'bounce'

    # Determine target scope
    if 'all' in oracle_text or 'each' in oracle_text:
        result['targets'] = 'multiple'

    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def adapt_card_abilities_to_legacy_format(abilities: CardAbilities, card: Dict = None) -> Dict:
    """
    Convert CardAbilities to a legacy extractor-style dict.

    This is useful when you need to provide data in the old format
    but want to use the unified parser internally.

    Args:
        abilities: CardAbilities from unified parser
        card: Optional original card dict for additional context

    Returns:
        Dict with combined data from all legacy extractor formats
    """
    result = {
        # Token data
        'creates_tokens': abilities.creates_tokens,
        'token_types': [],

        # Keywords
        'keywords': abilities.keywords.copy(),

        # Creature types
        'creature_types': abilities.creature_types.copy(),

        # Flags
        'has_rally': abilities.has_rally,
        'has_prowess': abilities.has_prowess,
        'has_magecraft': abilities.has_magecraft,
        'has_etb': abilities.has_etb,
        'is_removal': abilities.is_removal,
        'is_draw': abilities.is_draw,
        'is_ramp': abilities.is_ramp,

        # Triggers
        'triggers': [
            {
                'event': t.event,
                'effect': t.effect,
                'value': t.value,
                'condition': t.condition
            }
            for t in abilities.triggers
        ],

        # Static abilities
        'static_abilities': [
            {
                'effect_type': s.effect_type,
                'value': s.value,
                'targets': s.targets
            }
            for s in abilities.static_abilities
        ],

        # Activated abilities
        'activated_abilities': [
            {
                'cost': a.cost,
                'effect': a.effect
            }
            for a in abilities.activated_abilities
        ]
    }

    return result


def migrate_extractor_usage(
    old_function_name: str,
    card: Dict,
    extract_field: str = None
) -> Any:
    """
    Generic migration helper for extractor functions.

    Args:
        old_function_name: Name of the old extractor function
        card: Card dict to parse
        extract_field: Optional field to extract from abilities

    Returns:
        Parsed abilities or specific field value
    """
    parser = _get_parser()
    abilities = parser.parse_card(card)

    if extract_field:
        return getattr(abilities, extract_field, None)

    return abilities


# =============================================================================
# MIGRATION UTILITIES
# =============================================================================

def get_unified_parser() -> UnifiedCardParser:
    """
    Get the unified parser instance.

    Use this function when you want to migrate to the unified architecture
    but need a parser instance.

    Returns:
        UnifiedCardParser instance
    """
    return _get_parser()


def check_extractor_compatibility(card: Dict) -> Dict[str, bool]:
    """
    Check which legacy extractors would return data for this card.

    Useful for migration testing to ensure compatibility.

    Args:
        card: Card dict to check

    Returns:
        Dict mapping extractor type to whether it would return data
    """
    parser = _get_parser()
    abilities = parser.parse_card(card)

    return {
        'token_creation': abilities.creates_tokens,
        'keywords': len(abilities.keywords) > 0,
        'etb_effects': abilities.has_etb,
        'creature_types': len(abilities.creature_types) > 0,
        'card_draw': abilities.is_draw,
        'removal': abilities.is_removal,
        'ramp': abilities.is_ramp,
        'rally': abilities.has_rally,
        'prowess': abilities.has_prowess,
        'magecraft': abilities.has_magecraft,
        'death_triggers': any(t.event == 'death' for t in abilities.triggers),
        'sacrifice_outlets': any(
            'sacrifice' in a.cost.lower() if a.cost else False
            for a in abilities.activated_abilities
        )
    }
