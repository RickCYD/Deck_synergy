"""
SINGLE SOURCE OF TRUTH for all card mechanics detection
Used by BOTH simulation AND synergy engine

This ensures consistency between what the synergy analyzer detects
and what the simulation actually uses.
"""

import re


# ====================================================================================
# ARISTOCRATS MECHANICS
# ====================================================================================

def detect_death_drain_value(oracle_text: str) -> int:
    """
    Detect death drain triggers (life loss on creature death).
    Returns the amount of life drained per death.

    Used by:
    - Simulation: Sets Card.death_trigger_value attribute
    - Synergy Engine: Detects aristocrats payoffs

    Examples:
    - Zulaport Cutthroat: "Whenever ... creature ... dies, each opponent loses 1 life" -> 1
    - Cruel Celebrant: "Whenever ... creature ... dies, each opponent loses 1 life and you gain 1 life" -> 1
    - Nadier's Nightblade: "Whenever a token ... leaves the battlefield, each opponent loses 1 life" -> 1
    """
    if not oracle_text:
        return 0

    lower = oracle_text.lower()

    # Pattern 1: "dies" + "opponent" + "loses/lose life"
    if 'dies' in lower and 'opponent' in lower and ('lose' in lower or 'loses' in lower):
        m = re.search(r'loses? (\d+) life', lower)
        if m:
            return int(m.group(1))
        return 1

    # Pattern 2: "leaves the battlefield" + "opponent" + "loses/lose life"
    if 'leaves the battlefield' in lower and 'opponent' in lower and ('lose' in lower or 'loses' in lower):
        m = re.search(r'loses? (\d+) life', lower)
        if m:
            return int(m.group(1))
        return 1

    return 0


def detect_sacrifice_outlet(oracle_text: str) -> bool:
    """
    Detect sacrifice outlets (can sacrifice creatures for value).
    Returns True if the card can sacrifice creatures.

    Used by:
    - Simulation: Sets Card.sacrifice_outlet attribute
    - Synergy Engine: Detects aristocrats enablers

    Examples:
    - Goblin Bombardment: "Sacrifice a creature: Goblin Bombardment deals 1 damage..." -> True
    - Viscera Seer: "Sacrifice a creature: Scry 1" -> True
    """
    if not oracle_text:
        return False

    lower = oracle_text.lower()

    # Pattern: "sacrifice [something with] creature" as activation cost
    if re.search(r'sacrifice [^:]*?creature[^:]*?:', lower):
        return True

    return False


# ====================================================================================
# TOKEN GENERATION
# ====================================================================================

def detect_token_generation(oracle_text: str) -> bool:
    """
    Detect if a card creates tokens.

    Used by:
    - Simulation: For token creation mechanics
    - Synergy Engine: For token synergies

    Examples:
    - Anim Pakal: "... create X 1/1 ... Gnome creature tokens" -> True
    - Bitterblossom: "... create a 1/1 ... Faerie Rogue creature token" -> True
    """
    if not oracle_text:
        return False

    lower = oracle_text.lower()
    return bool(re.search(r'create.*token|put.*token.*onto', lower))


# ====================================================================================
# COMPREHENSIVE CLASSIFICATION
# ====================================================================================

def classify_card_mechanics(oracle_text: str) -> dict:
    """
    Classify ALL mechanics for a card in one pass.
    This is the MASTER function that everything should use.

    Returns:
        {
            'death_drain_value': int,      # Amount of life drained per death (0 if none)
            'is_sacrifice_outlet': bool,   # Can sacrifice creatures
            'creates_tokens': bool,        # Creates tokens
        }

    This ensures CONSISTENCY between simulation and synergy detection.
    """
    return {
        'death_drain_value': detect_death_drain_value(oracle_text),
        'is_sacrifice_outlet': detect_sacrifice_outlet(oracle_text),
        'creates_tokens': detect_token_generation(oracle_text),
    }
