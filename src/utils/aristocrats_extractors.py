"""
Aristocrats Detection Utilities
Shared between synergy engine and simulation for consistent detection

MIGRATION NOTICE:
==================
This module uses legacy regex-based extraction. For new code, consider using
the unified parser instead:

    from src.core.card_parser import UnifiedCardParser
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)

    # Check for death triggers:
    death_triggers = [t for t in abilities.triggers if t.event == 'death']

    # Check for sacrifice outlets:
    sac_outlets = [a for a in abilities.activated_abilities
                   if 'sacrifice' in a.cost.lower()]

See UNIFIED_ARCHITECTURE_GUIDE.md for details.

The functions in this file are maintained for backward compatibility.
"""

import re
import warnings

# Optional: Import unified parser for recommended path
try:
    from src.core.card_parser import UnifiedCardParser
    _UNIFIED_PARSER_AVAILABLE = True
except ImportError:
    _UNIFIED_PARSER_AVAILABLE = False


def detect_death_drain_trigger(oracle_text: str) -> int:
    """
    Detect death drain triggers (cards that drain life when creatures die).
    Returns the amount of life drained per death.

    Examples:
    - Zulaport Cutthroat: "Whenever ... creature ... dies, each opponent loses 1 life" -> 1
    - Cruel Celebrant: "Whenever ... creature ... dies, each opponent loses 1 life and you gain 1 life" -> 1
    - Nadier's Nightblade: "Whenever a token ... leaves the battlefield, each opponent loses 1 life" -> 1

    NOTE: This uses the same logic as the simulation's parse_death_triggers_from_oracle()
    """
    if not oracle_text:
        return 0

    lower = oracle_text.lower()

    # Pattern 1: "dies" + "opponent" + "loses/lose"
    if 'dies' in lower and 'opponent' in lower and ('lose' in lower or 'loses' in lower):
        # Try to extract the amount
        m = re.search(r'loses? (\d+) life', lower)
        if m:
            return int(m.group(1))
        return 1  # Default to 1 if amount not specified

    # Pattern 2: "leaves the battlefield" + "opponent" + "loses/lose" (e.g., Nadier's Nightblade)
    if 'leaves the battlefield' in lower and 'opponent' in lower and ('lose' in lower or 'loses' in lower):
        m = re.search(r'loses? (\d+) life', lower)
        if m:
            return int(m.group(1))
        return 1

    return 0


def is_sacrifice_outlet(oracle_text: str) -> bool:
    """
    Detect sacrifice outlets (cards that can sacrifice creatures for value).
    Returns True if the card is a sacrifice outlet.

    Examples:
    - Goblin Bombardment: "Sacrifice a creature: Goblin Bombardment deals 1 damage..." -> True
    - Viscera Seer: "Sacrifice a creature: Scry 1" -> True
    - Ashnod's Altar: "Sacrifice a creature: Add {C}{C}" -> True

    NOTE: This uses the same logic as the simulation's parse_sacrifice_outlet_from_oracle()
    """
    if not oracle_text:
        return False

    lower = oracle_text.lower()

    # Look for activated abilities that sacrifice creatures
    # Pattern: cost including "sacrifice" : effect
    if re.search(r'sacrifice [^:]*?creature[^:]*?:', lower):
        return True

    return False


def has_death_trigger(oracle_text: str) -> bool:
    """
    Detect if a card has ANY death trigger (not just drain).
    This is more general and includes cards like Pitiless Plunderer that create value on death.

    Examples:
    - Zulaport Cutthroat: has death trigger (drain)
    - Pitiless Plunderer: has death trigger (creates treasure)
    - Morbid Opportunist: has death trigger (draws card)

    Returns True if the card triggers on creature death.
    """
    if not oracle_text:
        return False

    lower = oracle_text.lower()

    # Exclude self-death triggers (not aristocrats payoffs)
    self_death_patterns = [
        r'when (this|~) .*dies',
        r'when (this|~) .*is put into.*graveyard',
        r'whenever (this|~) dies',
    ]

    if any(re.search(pattern, lower) for pattern in self_death_patterns):
        return False

    # General death trigger patterns
    death_trigger_patterns = [
        r'whenever (?:a|another|one or more) creature',  # "whenever a creature dies"
        r'whenever.*creatures.*die',                     # "whenever one or more creatures die"
        r'when (?:a|another) creature.*dies',           # "when a creature dies"
        r'whenever (?:a|another) .*permanent.*dies',    # "whenever a permanent dies"
    ]

    return any(re.search(pattern, lower) for pattern in death_trigger_patterns)


def creates_tokens(oracle_text: str) -> bool:
    """
    Detect if a card creates tokens.

    Examples:
    - Anim Pakal: "... create X 1/1 ... Gnome creature tokens" -> True
    - Bitterblossom: "... create a 1/1 ... Faerie Rogue creature token" -> True

    Returns True if the card creates tokens.
    """
    if not oracle_text:
        return False

    lower = oracle_text.lower()

    token_patterns = [
        r'create.*token',
        r'put.*token.*onto the battlefield',
    ]

    return any(re.search(pattern, lower) for pattern in token_patterns)


def get_aristocrats_classification(oracle_text: str) -> dict:
    """
    Classify a card's role in aristocrats strategy.

    Returns:
        {
            'death_drain_value': int,      # Amount of life drained per death (0 if none)
            'is_sacrifice_outlet': bool,   # Can sacrifice creatures
            'has_death_trigger': bool,     # Triggers on any creature death
            'creates_tokens': bool,        # Creates tokens
            'is_aristocrats_payoff': bool, # Is a payoff for aristocrats strategy
            'is_aristocrats_enabler': bool # Enables aristocrats strategy
        }
    """
    death_drain = detect_death_drain_trigger(oracle_text)
    sac_outlet = is_sacrifice_outlet(oracle_text)
    death_trigger = has_death_trigger(oracle_text)
    token_gen = creates_tokens(oracle_text)

    # Payoffs are cards that benefit from creatures dying
    is_payoff = death_drain > 0 or death_trigger

    # Enablers are cards that help trigger death effects
    is_enabler = sac_outlet or token_gen

    return {
        'death_drain_value': death_drain,
        'is_sacrifice_outlet': sac_outlet,
        'has_death_trigger': death_trigger,
        'creates_tokens': token_gen,
        'is_aristocrats_payoff': is_payoff,
        'is_aristocrats_enabler': is_enabler,
    }


# Convenience functions for backward compatibility with existing code
def detect_death_trigger_value(oracle_text: str) -> int:
    """Alias for detect_death_drain_trigger for backward compatibility"""
    return detect_death_drain_trigger(oracle_text)


def detect_sacrifice_outlet(oracle_text: str) -> bool:
    """Alias for is_sacrifice_outlet for backward compatibility"""
    return is_sacrifice_outlet(oracle_text)
