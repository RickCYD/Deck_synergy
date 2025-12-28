"""
Extended Mechanics Module for MTG Simulation

This module implements additional game mechanics that were missing from the base simulation:
- Flicker/Blink effects (ETB abuse)
- Copy effects (Clone strategies)
- Modal spells (Flexible cards)
- Cascade/Suspend (Mana cheating)
- Persist/Undying (Aristocrat resilience)
- Convoke/Delve (Cost reduction)
- Flash timing (Instant-speed creatures)
- Flashback (Graveyard casting)
- Buyback/Retrace (Spell recursion)

All mechanics are designed for goldfish simulation (no opponent interaction).
"""

from __future__ import annotations

import re
import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Callable

if TYPE_CHECKING:
    from boardstate import BoardState
    from simulate_game import Card


# =============================================================================
# FLICKER/BLINK MECHANICS
# =============================================================================

def detect_flicker_ability(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card has flicker/blink ability from oracle text.

    Returns dict with:
        - has_flicker: bool
        - flicker_type: 'exile_return_immediate', 'exile_return_end_turn', 'exile_return_next_end'
        - targets: 'creature', 'permanent', 'artifact', etc.
        - is_etb_trigger: bool (triggers on ETB vs activated)
    """
    text = oracle_text.lower()
    result = {
        'has_flicker': False,
        'flicker_type': None,
        'targets': None,
        'is_etb_trigger': False,
        'is_activated': False,
    }

    # End of turn return patterns (Conjurer's Closet, Thassa) - check first before immediate
    end_turn_patterns = [
        r'at the beginning of[^.]*end step[^.]*exile[^.]*return',
        r'exile[^.]*return[^.]*at the beginning of the next end step',
        r'exile[^.]*return[^.]*at end of turn',
        r'exile[^.]*return it to the battlefield under your control at the beginning of the next end step',
    ]

    # Immediate return patterns (Ephemerate, Cloudshift, Restoration Angel)
    immediate_patterns = [
        r'exile[^.]*then return[^.]*to the battlefield',
        r'exile[^.]*return[^.]*to the battlefield immediately',
        r'exile[^.]*it returns to the battlefield',
        r'exile target[^.]*then return that card to the battlefield',
    ]

    # Next end step patterns (Ghostway, Eerie Interlude)
    next_end_patterns = [
        r'exile[^.]*return[^.]*to the battlefield at the beginning of your next end step',
    ]

    # Check end turn patterns FIRST (more specific)
    for pattern in end_turn_patterns:
        if re.search(pattern, text):
            result['has_flicker'] = True
            result['flicker_type'] = 'exile_return_end_turn'
            break

    # Then check immediate patterns
    if not result['has_flicker']:
        for pattern in immediate_patterns:
            if re.search(pattern, text):
                result['has_flicker'] = True
                result['flicker_type'] = 'exile_return_immediate'
                break

    if not result['has_flicker']:
        for pattern in next_end_patterns:
            if re.search(pattern, text):
                result['has_flicker'] = True
                result['flicker_type'] = 'exile_return_next_end'
                break

    # Detect target type
    if result['has_flicker']:
        if 'creature' in text and 'noncreature' not in text:
            result['targets'] = 'creature'
        elif 'permanent' in text:
            result['targets'] = 'permanent'
        elif 'artifact' in text:
            result['targets'] = 'artifact'
        else:
            result['targets'] = 'creature'  # Default

        # Check if ETB triggered
        if 'when' in text and 'enters' in text:
            result['is_etb_trigger'] = True

        # Check if activated ability
        if re.search(r'{\d}|{[wubrg]}', text) and ':' in text:
            result['is_activated'] = True

    return result


def flicker_permanent(board: 'BoardState', permanent: 'Card',
                      return_type: str = 'immediate', verbose: bool = False) -> bool:
    """
    Flicker a permanent: exile it and return it to the battlefield.

    Args:
        board: The current board state
        permanent: The card to flicker
        return_type: 'immediate', 'end_turn', or 'next_end'
        verbose: Print debug info

    Returns:
        True if successful, False otherwise
    """
    # Find which zone the permanent is in
    zone = None
    for zone_name, zone_list in [
        ('creatures', board.creatures),
        ('artifacts', board.artifacts),
        ('enchantments', board.enchantments),
        ('lands_untapped', board.lands_untapped),
        ('lands_tapped', board.lands_tapped),
    ]:
        if permanent in zone_list:
            zone = zone_name
            zone_list.remove(permanent)
            break

    if zone is None:
        if verbose:
            print(f"Cannot flicker {permanent.name}: not on battlefield")
        return False

    # Move to exile
    board.exile.append(permanent)

    if verbose:
        print(f"Flickered {permanent.name} (exiled)")

    # Handle return based on type
    if return_type == 'immediate':
        # Return immediately - triggers ETB again
        board.exile.remove(permanent)
        _return_permanent_to_battlefield(board, permanent, zone, verbose)

        # Track flicker for metrics
        if not hasattr(board, 'flicker_count'):
            board.flicker_count = 0
        board.flicker_count += 1

    elif return_type == 'end_turn':
        # Queue for end of turn return
        if not hasattr(board, 'pending_flicker_returns'):
            board.pending_flicker_returns = []
        board.pending_flicker_returns.append({
            'permanent': permanent,
            'zone': zone,
            'return_turn': board.turn,
        })

    elif return_type == 'next_end':
        # Queue for next end step
        if not hasattr(board, 'pending_flicker_returns'):
            board.pending_flicker_returns = []
        board.pending_flicker_returns.append({
            'permanent': permanent,
            'zone': zone,
            'return_turn': board.turn + 1,
        })

    return True


def _return_permanent_to_battlefield(board: 'BoardState', permanent: 'Card',
                                     original_zone: str, verbose: bool = False) -> None:
    """Return a permanent from exile to the battlefield and trigger ETB."""
    # Reset any temporary state
    if hasattr(permanent, 'counters'):
        permanent.counters = {}
    if hasattr(permanent, 'tapped'):
        permanent.tapped = False

    # Reset power/toughness to base
    if hasattr(permanent, 'base_power'):
        permanent.power = permanent.base_power
    if hasattr(permanent, 'base_toughness'):
        permanent.toughness = permanent.base_toughness

    # Add back to appropriate zone
    if 'creature' in original_zone or 'Creature' in getattr(permanent, 'type', ''):
        board.creatures.append(permanent)
        # Reset summoning sickness
        if hasattr(permanent, '_turns_on_board'):
            permanent._turns_on_board = 0
    elif 'artifact' in original_zone or 'Artifact' in getattr(permanent, 'type', ''):
        board.artifacts.append(permanent)
    elif 'enchantment' in original_zone or 'Enchantment' in getattr(permanent, 'type', ''):
        board.enchantments.append(permanent)
    elif 'land' in original_zone or 'Land' in getattr(permanent, 'type', ''):
        board.lands_untapped.append(permanent)

    if verbose:
        print(f"  → {permanent.name} returned to battlefield")

    # Trigger ETB effects
    board._process_special_etb_effects(permanent, verbose)
    board._execute_triggers("etb", permanent, verbose)


def process_end_of_turn_flicker_returns(board: 'BoardState', verbose: bool = False) -> int:
    """
    Process any pending flicker returns at end of turn.

    Returns the number of permanents returned.
    """
    if not hasattr(board, 'pending_flicker_returns'):
        return 0

    returned = 0
    remaining = []

    for entry in board.pending_flicker_returns:
        if entry['return_turn'] <= board.turn:
            permanent = entry['permanent']
            if permanent in board.exile:
                board.exile.remove(permanent)
                _return_permanent_to_battlefield(board, permanent, entry['zone'], verbose)
                returned += 1
        else:
            remaining.append(entry)

    board.pending_flicker_returns = remaining
    return returned


# =============================================================================
# COPY EFFECTS
# =============================================================================

def detect_copy_ability(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card has copy/clone ability from oracle text.

    Returns dict with:
        - has_copy: bool
        - copy_type: 'creature', 'spell', 'permanent', 'token'
        - is_etb: bool
        - makes_token: bool
    """
    text = oracle_text.lower()
    result = {
        'has_copy': False,
        'copy_type': None,
        'is_etb': False,
        'makes_token': False,
    }

    # Clone patterns (enters as copy)
    clone_patterns = [
        r'enters the battlefield as a copy of',
        r'you may have[^.]*enter the battlefield as a copy',
        r'enter as a copy of',
    ]

    # Token copy patterns
    token_copy_patterns = [
        r'create a token that\'s a copy of',
        r'create[^.]*token[^.]*copy of',
        r'populate',  # Copy a creature token
    ]

    # Spell copy patterns
    spell_copy_patterns = [
        r'copy target[^.]*spell',
        r'copy that spell',
        r'storm',
        r'whenever you cast[^.]*copy it',
    ]

    for pattern in clone_patterns:
        if re.search(pattern, text):
            result['has_copy'] = True
            result['copy_type'] = 'creature'
            result['is_etb'] = True
            break

    if not result['has_copy']:
        for pattern in token_copy_patterns:
            if re.search(pattern, text):
                result['has_copy'] = True
                result['copy_type'] = 'token'
                result['makes_token'] = True
                break

    if not result['has_copy']:
        for pattern in spell_copy_patterns:
            if re.search(pattern, text):
                result['has_copy'] = True
                result['copy_type'] = 'spell'
                break

    return result


def copy_creature(board: 'BoardState', source: 'Card', target: 'Card',
                  verbose: bool = False) -> Optional['Card']:
    """
    Create a copy of a creature (for Clone effects).

    The source becomes a copy of the target creature.

    Args:
        board: The current board state
        source: The card that will become a copy (e.g., Clone)
        target: The creature to copy
        verbose: Print debug info

    Returns:
        The modified source card, or None if failed
    """
    if target is None:
        if verbose:
            print(f"{source.name} has nothing to copy, entering as 0/0")
        return source

    # Copy relevant attributes
    source.power = target.power
    source.toughness = target.toughness
    source.base_power = target.base_power
    source.base_toughness = target.base_toughness

    # Copy keywords
    for keyword in ['has_haste', 'has_flying', 'has_trample', 'has_lifelink',
                    'has_deathtouch', 'has_vigilance', 'has_menace',
                    'has_first_strike', 'has_double_strike']:
        if hasattr(target, keyword):
            setattr(source, keyword, getattr(target, keyword))

    # Copy triggered abilities (important for ETB abuse)
    if hasattr(target, 'triggered_abilities'):
        source.triggered_abilities = list(target.triggered_abilities)

    # Copy oracle text for mechanic detection
    if hasattr(target, 'oracle_text'):
        source.oracle_text = target.oracle_text

    # Note: source keeps its own name for tracking purposes
    if verbose:
        print(f"{source.name} entered as a copy of {target.name} ({source.power}/{source.toughness})")

    return source


def create_token_copy(board: 'BoardState', target: 'Card',
                      verbose: bool = False) -> Optional['Card']:
    """
    Create a token that's a copy of target creature.

    Args:
        board: The current board state
        target: The creature to copy
        verbose: Print debug info

    Returns:
        The new token, or None if failed
    """
    from simulate_game import Card

    if target is None:
        return None

    # Create token with copied attributes
    token = Card(
        name=f"{target.name} (Token Copy)",
        type=target.type,
        mana_cost="",  # Tokens have no mana cost
        power=target.power,
        toughness=target.toughness,
        produces_colors=getattr(target, 'produces_colors', []),
        mana_production=getattr(target, 'mana_production', 0),
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=getattr(target, 'has_haste', False),
        has_flying=getattr(target, 'has_flying', False),
        has_trample=getattr(target, 'has_trample', False),
        has_lifelink=getattr(target, 'has_lifelink', False),
        has_deathtouch=getattr(target, 'has_deathtouch', False),
        oracle_text=getattr(target, 'oracle_text', ''),
    )

    # Copy triggered abilities
    if hasattr(target, 'triggered_abilities'):
        token.triggered_abilities = list(target.triggered_abilities)

    # Mark as token
    token.is_token = True

    # Apply token multiplier
    copies_to_create = getattr(board, 'token_multiplier', 1)

    for _ in range(copies_to_create):
        board.creatures.append(token)
        board.tokens_created_this_turn += 1

        if verbose:
            print(f"Created token copy of {target.name} ({token.power}/{token.toughness})")

        # Trigger ETB
        board._execute_triggers("etb", token, verbose)

    return token


# =============================================================================
# MODAL SPELLS
# =============================================================================

def detect_modal_spell(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card is a modal spell and parse its modes.

    Returns dict with:
        - is_modal: bool
        - num_modes: int
        - modes_to_choose: int
        - modes: List of mode descriptions
    """
    text = oracle_text.lower()
    result = {
        'is_modal': False,
        'num_modes': 0,
        'modes_to_choose': 1,
        'modes': [],
    }

    # Check for modal indicators
    modal_patterns = [
        r'choose one',
        r'choose two',
        r'choose three',
        r'choose one or more',
        r'choose one —',
        r'choose two —',
        r'• ',  # Bullet point indicates modal options
    ]

    for pattern in modal_patterns:
        if re.search(pattern, text):
            result['is_modal'] = True
            break

    if not result['is_modal']:
        return result

    # Determine how many modes to choose
    if 'choose two' in text:
        result['modes_to_choose'] = 2
    elif 'choose three' in text:
        result['modes_to_choose'] = 3
    elif 'choose one or more' in text:
        result['modes_to_choose'] = -1  # Variable

    # Parse individual modes (bullet points)
    mode_matches = re.findall(r'• ([^•]+?)(?=•|$)', text)
    if mode_matches:
        result['modes'] = [m.strip() for m in mode_matches]
        result['num_modes'] = len(result['modes'])

    return result


def evaluate_modal_choice(board: 'BoardState', modes: List[str],
                          num_to_choose: int) -> List[int]:
    """
    AI evaluation of which modal choices to make.

    Args:
        board: Current board state
        modes: List of mode descriptions
        num_to_choose: How many modes to select

    Returns:
        List of mode indices (0-based) to choose
    """
    if not modes:
        return []

    # Score each mode based on current board state
    scores = []

    for i, mode in enumerate(modes):
        mode_lower = mode.lower()
        score = 0

        # Creature-based evaluation
        if board.creatures:
            if 'destroy' in mode_lower and 'creature' in mode_lower:
                score += 5  # Removal is valuable in goldfish for clearing blockers
            if '+' in mode_lower and 'counter' in mode_lower:
                score += 8  # Counters are great in goldfish
            if 'draw' in mode_lower:
                score += 7  # Card draw is always good
            if 'damage' in mode_lower:
                score += 6  # Direct damage helps win faster
        else:
            # No creatures - prioritize card draw and damage
            if 'draw' in mode_lower:
                score += 10
            if 'damage' in mode_lower:
                score += 8
            if 'create' in mode_lower and 'token' in mode_lower:
                score += 9

        # Generic evaluations
        if 'each opponent' in mode_lower:
            score += 3  # Affects all opponents
        if 'life' in mode_lower and 'gain' in mode_lower:
            score += 2
        if 'search' in mode_lower or 'tutor' in mode_lower:
            score += 6

        scores.append((score, i))

    # Sort by score descending
    scores.sort(reverse=True)

    # Return top N indices
    actual_choices = min(num_to_choose, len(modes)) if num_to_choose > 0 else len(modes)
    return [idx for _, idx in scores[:actual_choices]]


def execute_modal_spell(board: 'BoardState', card: 'Card',
                        chosen_modes: List[int], verbose: bool = False) -> bool:
    """
    Execute a modal spell with the chosen modes.

    Args:
        board: Current board state
        card: The modal spell being cast
        chosen_modes: List of mode indices to execute
        verbose: Print debug info

    Returns:
        True if successful
    """
    oracle = getattr(card, 'oracle_text', '').lower()
    modes_info = detect_modal_spell(oracle)

    if not modes_info['is_modal']:
        return False

    if verbose:
        print(f"Casting modal spell {card.name}, choosing modes: {chosen_modes}")

    for mode_idx in chosen_modes:
        if mode_idx < len(modes_info['modes']):
            mode_text = modes_info['modes'][mode_idx]
            _execute_mode_effect(board, mode_text, verbose)

    return True


def _execute_mode_effect(board: 'BoardState', mode_text: str, verbose: bool = False) -> None:
    """Execute a single mode effect based on its text."""
    text = mode_text.lower()

    # Draw cards
    draw_match = re.search(r'draw (\w+) card', text)
    if draw_match:
        num_str = draw_match.group(1)
        num_map = {'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4}
        num = num_map.get(num_str, 1)
        board.draw_card(num, verbose=verbose)
        if verbose:
            print(f"  → Mode: Drew {num} card(s)")

    # Deal damage
    damage_match = re.search(r'deal[s]? (\d+) damage', text)
    if damage_match:
        damage = int(damage_match.group(1))
        board.drain_damage_this_turn += damage
        if verbose:
            print(f"  → Mode: Dealt {damage} damage")

    # Deal damage equal to creature/token count (e.g., Caesar's third mode)
    damage_count_match = re.search(r'deal[s]? damage equal to (?:the number of )?(\w+)', text)
    if damage_count_match and not damage_match:  # Don't double-count
        count_type = damage_count_match.group(1)
        damage = 0

        if 'creature token' in count_type or 'token' in count_type:
            # Count tokens you control
            damage = sum(1 for c in board.creatures if hasattr(c, 'token_type') and c.token_type)
        elif 'creature' in count_type:
            # Count all creatures you control
            damage = len(board.creatures)

        if damage > 0:
            board.drain_damage_this_turn += damage
            if verbose:
                print(f"  → Mode: Dealt {damage} damage (based on {count_type} count)")

    # Gain life
    life_match = re.search(r'gain (\d+) life', text)
    if life_match:
        life = int(life_match.group(1))
        board.gain_life(life, verbose=verbose)

    # Lose life (e.g., "you draw a card and you lose 1 life")
    lose_life_match = re.search(r'you lose (\d+) life', text)
    if lose_life_match:
        life_loss = int(lose_life_match.group(1))
        board.life -= life_loss
        if verbose:
            print(f"  → Mode: Lost {life_loss} life")

    # Create tokens (enhanced to handle "tapped and attacking" tokens)
    token_match = re.search(r'create (\w+) (\d+)/(\d+)', text)
    if token_match:
        num_str = token_match.group(1)
        power = int(token_match.group(2))
        toughness = int(token_match.group(3))
        num_map = {'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
        num = num_map.get(num_str, 1)

        # Check for special token properties
        has_haste = 'haste' in text
        enters_tapped = 'tapped' in text and 'attacking' not in text
        enters_attacking = 'tapped and attacking' in text or 'that are tapped and attacking' in text

        # Parse creature type if present
        token_type = None
        type_match = re.search(r'(\w+)\s+creature token', text)
        if type_match:
            token_type = type_match.group(1).title()

        # Parse color keywords
        colors = []
        for color_word in ['red', 'white', 'blue', 'black', 'green']:
            if color_word in text:
                colors.append(color_word)

        color_str = ' and '.join(colors) if colors else ''

        for _ in range(num):
            board.create_token(
                f"{color_str.title()} {token_type or 'Token'}".strip(),
                power,
                toughness,
                has_haste=has_haste,
                token_type=token_type,
                enters_tapped=enters_tapped,
                enters_attacking=enters_attacking,
                verbose=verbose
            )
        if verbose:
            attacking_str = " (tapped and attacking)" if enters_attacking else (" (tapped)" if enters_tapped else "")
            print(f"  → Mode: Created {num} {power}/{toughness} token(s){attacking_str}")

    # Add counters
    counter_match = re.search(r'put (\w+) \+1/\+1 counter', text)
    if counter_match and board.creatures:
        num_str = counter_match.group(1)
        num_map = {'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4}
        num = num_map.get(num_str, 1)
        # Put on best creature
        best = max(board.creatures, key=lambda c: (c.power or 0) + (c.toughness or 0))
        best.add_counter('+1/+1', num)
        if verbose:
            print(f"  → Mode: Put {num} +1/+1 counter(s) on {best.name}")


# =============================================================================
# CASCADE / SUSPEND
# =============================================================================

def detect_cascade(oracle_text: str) -> bool:
    """Check if a card has cascade."""
    return 'cascade' in oracle_text.lower()


def detect_suspend(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card has suspend and parse details.

    Returns dict with:
        - has_suspend: bool
        - suspend_cost: str (mana cost)
        - suspend_time: int (number of time counters)
    """
    text = oracle_text.lower()
    result = {
        'has_suspend': False,
        'suspend_cost': None,
        'suspend_time': 0,
    }

    # Pattern: Suspend N—{cost}
    suspend_match = re.search(r'suspend (\d+)—([^(]+)', text)
    if suspend_match:
        result['has_suspend'] = True
        result['suspend_time'] = int(suspend_match.group(1))
        result['suspend_cost'] = suspend_match.group(2).strip()

    return result


def resolve_cascade(board: 'BoardState', cascade_card: 'Card',
                    verbose: bool = False) -> Optional['Card']:
    """
    Resolve cascade: reveal cards until you hit one with lower CMC, cast it free.

    Args:
        board: Current board state
        cascade_card: The card that triggered cascade
        verbose: Print debug info

    Returns:
        The card cast from cascade, or None
    """
    from simulate_game import Card
    from convert_dataframe_deck import parse_mana_cost

    cascade_cmc = parse_mana_cost(cascade_card.mana_cost)

    if verbose:
        print(f"Cascade triggered! Looking for card with CMC < {cascade_cmc}")

    # Reveal cards until we find one with lower CMC
    revealed = []
    cascade_target = None

    while board.library:
        top_card = board.library.pop(0)
        revealed.append(top_card)

        # Check if this is a nonland card with lower CMC
        if 'Land' not in top_card.type:
            card_cmc = parse_mana_cost(top_card.mana_cost)
            if card_cmc < cascade_cmc:
                cascade_target = top_card
                if verbose:
                    print(f"  → Cascade found: {top_card.name} (CMC {card_cmc})")
                break

    # Put all other revealed cards on bottom of library in random order
    other_revealed = [c for c in revealed if c is not cascade_target]
    random.shuffle(other_revealed)
    board.library.extend(other_revealed)

    # Cast the cascade target for free if found
    if cascade_target:
        # Remove from revealed list since we're casting it
        if verbose:
            print(f"  → Casting {cascade_target.name} for free!")

        # Cast without paying mana cost
        board.play_card(cascade_target, verbose=verbose, cast=False)

        # Track cascade for metrics
        if not hasattr(board, 'cascade_casts'):
            board.cascade_casts = 0
        board.cascade_casts += 1

        return cascade_target

    if verbose:
        print("  → Cascade found no valid target")
    return None


def process_suspended_cards(board: 'BoardState', verbose: bool = False) -> int:
    """
    Process suspended cards at upkeep: remove time counter, cast if none left.

    Returns number of cards cast from suspend.
    """
    if not hasattr(board, 'suspended_cards'):
        board.suspended_cards = []
        return 0

    cast_count = 0
    remaining = []

    for entry in board.suspended_cards:
        entry['time_counters'] -= 1

        if verbose:
            print(f"Suspend: {entry['card'].name} has {entry['time_counters']} time counters remaining")

        if entry['time_counters'] <= 0:
            # Cast the spell!
            card = entry['card']
            if verbose:
                print(f"  → Suspend complete! Casting {card.name}")

            # Remove from exile
            if card in board.exile:
                board.exile.remove(card)

            # Cast for free
            board.play_card(card, verbose=verbose, cast=False)

            # Suspended creatures have haste
            if 'Creature' in card.type:
                card.has_haste = True

            cast_count += 1
        else:
            remaining.append(entry)

    board.suspended_cards = remaining
    return cast_count


def suspend_card(board: 'BoardState', card: 'Card',
                 time_counters: int, verbose: bool = False) -> bool:
    """
    Suspend a card: exile it with time counters.

    Args:
        board: Current board state
        card: Card to suspend
        time_counters: Number of time counters to put on it
        verbose: Print debug info

    Returns:
        True if successful
    """
    # Remove from hand
    if card in board.hand:
        board.hand.remove(card)

    # Move to exile
    board.exile.append(card)

    # Track in suspended cards list
    if not hasattr(board, 'suspended_cards'):
        board.suspended_cards = []

    board.suspended_cards.append({
        'card': card,
        'time_counters': time_counters,
    })

    if verbose:
        print(f"Suspended {card.name} with {time_counters} time counters")

    return True


# =============================================================================
# PERSIST / UNDYING
# =============================================================================

def detect_persist(oracle_text: str) -> bool:
    """Check if a card has persist."""
    return 'persist' in oracle_text.lower()


def detect_undying(oracle_text: str) -> bool:
    """Check if a card has undying."""
    return 'undying' in oracle_text.lower()


def handle_creature_death_persist_undying(board: 'BoardState', creature: 'Card',
                                          verbose: bool = False) -> bool:
    """
    Handle persist/undying when a creature dies.

    Returns True if creature returned to battlefield.
    """
    oracle = getattr(creature, 'oracle_text', '').lower()
    counters = getattr(creature, 'counters', {})

    # Check persist
    if detect_persist(oracle):
        # Persist: Return if no -1/-1 counters
        if counters.get('-1/-1', 0) == 0:
            if verbose:
                print(f"Persist triggers for {creature.name}!")

            # Reset creature state
            creature.power = creature.base_power
            creature.toughness = creature.base_toughness
            creature.counters = {'-1/-1': 1}  # Returns with -1/-1 counter
            creature.power -= 1
            creature.toughness -= 1

            # Return to battlefield
            if creature in board.graveyard:
                board.graveyard.remove(creature)
            board.creatures.append(creature)

            # Reset summoning sickness
            if hasattr(creature, '_turns_on_board'):
                creature._turns_on_board = 0

            # Track for metrics
            if not hasattr(board, 'persist_triggers'):
                board.persist_triggers = 0
            board.persist_triggers += 1

            if verbose:
                print(f"  → {creature.name} returned with -1/-1 counter ({creature.power}/{creature.toughness})")

            return True

    # Check undying
    if detect_undying(oracle):
        # Undying: Return if no +1/+1 counters
        if counters.get('+1/+1', 0) == 0:
            if verbose:
                print(f"Undying triggers for {creature.name}!")

            # Reset creature state
            creature.power = creature.base_power
            creature.toughness = creature.base_toughness
            creature.counters = {'+1/+1': 1}  # Returns with +1/+1 counter
            creature.power += 1
            creature.toughness += 1

            # Return to battlefield
            if creature in board.graveyard:
                board.graveyard.remove(creature)
            board.creatures.append(creature)

            # Reset summoning sickness
            if hasattr(creature, '_turns_on_board'):
                creature._turns_on_board = 0

            # Track for metrics
            if not hasattr(board, 'undying_triggers'):
                board.undying_triggers = 0
            board.undying_triggers += 1

            if verbose:
                print(f"  → {creature.name} returned with +1/+1 counter ({creature.power}/{creature.toughness})")

            return True

    return False


# =============================================================================
# CONVOKE / DELVE (Cost Reduction)
# =============================================================================

def detect_convoke(oracle_text: str) -> bool:
    """Check if a card has convoke."""
    return 'convoke' in oracle_text.lower()


def detect_delve(oracle_text: str) -> bool:
    """Check if a card has delve."""
    return 'delve' in oracle_text.lower()


def calculate_convoke_reduction(board: 'BoardState', card: 'Card') -> int:
    """
    Calculate how much mana convoke can reduce the cost by.

    Each untapped creature you control can tap to pay {1} or one mana of its color.

    Returns the maximum generic mana that can be reduced.
    """
    if not detect_convoke(getattr(card, 'oracle_text', '')):
        return 0

    # Count untapped creatures
    untapped_creatures = [c for c in board.creatures
                         if not getattr(c, 'tapped', False)]

    return len(untapped_creatures)


def calculate_delve_reduction(board: 'BoardState', card: 'Card') -> int:
    """
    Calculate how much mana delve can reduce the cost by.

    Each card exiled from graveyard pays {1}.

    Returns the maximum generic mana that can be reduced.
    """
    if not detect_delve(getattr(card, 'oracle_text', '')):
        return 0

    # Count cards in graveyard
    return len(board.graveyard)


def apply_convoke(board: 'BoardState', card: 'Card',
                  creatures_to_tap: int, verbose: bool = False) -> int:
    """
    Apply convoke: tap creatures to reduce mana cost.

    Args:
        board: Current board state
        card: The card being cast with convoke
        creatures_to_tap: Number of creatures to tap
        verbose: Print debug info

    Returns:
        Amount of mana reduced
    """
    if not detect_convoke(getattr(card, 'oracle_text', '')):
        return 0

    untapped = [c for c in board.creatures if not getattr(c, 'tapped', False)]
    actual_tap = min(creatures_to_tap, len(untapped))

    # Tap the creatures
    for i in range(actual_tap):
        untapped[i].tapped = True

    if verbose and actual_tap > 0:
        print(f"Convoke: Tapped {actual_tap} creature(s) to reduce cost")

    return actual_tap


def apply_delve(board: 'BoardState', card: 'Card',
                cards_to_exile: int, verbose: bool = False) -> int:
    """
    Apply delve: exile cards from graveyard to reduce mana cost.

    Args:
        board: Current board state
        card: The card being cast with delve
        cards_to_exile: Number of cards to exile
        verbose: Print debug info

    Returns:
        Amount of mana reduced
    """
    if not detect_delve(getattr(card, 'oracle_text', '')):
        return 0

    actual_exile = min(cards_to_exile, len(board.graveyard))

    # Exile the cards
    for _ in range(actual_exile):
        exiled = board.graveyard.pop(0)
        board.exile.append(exiled)

    if verbose and actual_exile > 0:
        print(f"Delve: Exiled {actual_exile} card(s) from graveyard to reduce cost")

    return actual_exile


def get_effective_mana_cost(board: 'BoardState', card: 'Card') -> str:
    """
    Calculate the effective mana cost after cost reductions.

    Considers:
    - Convoke (tap creatures)
    - Delve (exile from graveyard)
    - Generic cost reduction effects on board

    Returns:
        The modified mana cost string
    """
    from convert_dataframe_deck import parse_mana_cost

    base_cost = getattr(card, 'mana_cost', '')
    if not base_cost:
        return ''

    total_cmc = parse_mana_cost(base_cost)

    # Calculate reductions
    convoke_reduction = calculate_convoke_reduction(board, card)
    delve_reduction = calculate_delve_reduction(board, card)
    board_reduction = getattr(board, 'cost_reduction', 0)

    # Total reduction (can't reduce below colored mana requirements)
    # Extract colored symbols from mana cost
    colored_symbols = re.findall(r'[WUBRG]', base_cost.upper())
    min_cost = len(colored_symbols)

    max_reduction = total_cmc - min_cost
    total_reduction = min(convoke_reduction + delve_reduction + board_reduction, max_reduction)

    # Build new cost string
    new_generic = max(0, total_cmc - len(colored_symbols) - total_reduction)
    new_cost = (str(new_generic) if new_generic > 0 else '') + ''.join(colored_symbols)

    return new_cost if new_cost else '0'


# =============================================================================
# FLASH TIMING
# =============================================================================

def detect_flash(oracle_text: str, keywords: List[str] = None) -> bool:
    """
    Check if a card has flash.

    Args:
        oracle_text: Card's oracle text
        keywords: Card's keyword list

    Returns:
        True if card has flash
    """
    if keywords and 'Flash' in keywords:
        return True
    return 'flash' in oracle_text.lower()


def can_cast_at_instant_speed(card: 'Card') -> bool:
    """
    Determine if a card can be cast at instant speed.

    This includes:
    - Instants
    - Cards with flash
    - Cards that say "as though it had flash"
    """
    card_type = getattr(card, 'type', '')
    oracle = getattr(card, 'oracle_text', '').lower()

    if 'Instant' in card_type:
        return True

    if getattr(card, 'has_flash', False):
        return True

    if 'flash' in oracle:
        return True

    if 'as though it had flash' in oracle:
        return True

    return False


# =============================================================================
# FLASHBACK
# =============================================================================

def detect_flashback(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card has flashback and parse the cost.

    Returns dict with:
        - has_flashback: bool
        - flashback_cost: str (mana cost to cast from graveyard)
    """
    text = oracle_text.lower()
    result = {
        'has_flashback': False,
        'flashback_cost': None,
    }

    # Pattern: Flashback {cost}
    flashback_match = re.search(r'flashback[^{]*({[^}]+})+', text)
    if flashback_match:
        result['has_flashback'] = True
        # Extract the cost
        cost_match = re.findall(r'{([^}]+)}', flashback_match.group(0))
        result['flashback_cost'] = ''.join(cost_match)
    elif 'flashback' in text:
        result['has_flashback'] = True
        # Try to find cost after flashback
        cost_match = re.search(r'flashback[—-]?\s*([^\n(]+)', text)
        if cost_match:
            result['flashback_cost'] = cost_match.group(1).strip()

    return result


def get_flashback_cards(board: 'BoardState') -> List['Card']:
    """
    Get all cards in graveyard that can be cast with flashback.

    Returns list of (card, flashback_cost) tuples.
    """
    flashback_cards = []

    for card in board.graveyard:
        oracle = getattr(card, 'oracle_text', '')
        fb_info = detect_flashback(oracle)

        if fb_info['has_flashback']:
            flashback_cards.append((card, fb_info['flashback_cost']))

    return flashback_cards


def cast_flashback(board: 'BoardState', card: 'Card',
                   verbose: bool = False) -> bool:
    """
    Cast a spell using flashback from the graveyard.

    The spell is exiled after resolution instead of going to graveyard.

    Returns True if successful.
    """
    oracle = getattr(card, 'oracle_text', '')
    fb_info = detect_flashback(oracle)

    if not fb_info['has_flashback']:
        return False

    if card not in board.graveyard:
        return False

    if verbose:
        print(f"Casting {card.name} via Flashback (cost: {fb_info['flashback_cost']})")

    # Remove from graveyard
    board.graveyard.remove(card)

    # Cast the spell (simplified - just execute effects)
    if 'Instant' in card.type or 'Sorcery' in card.type:
        # Execute spell effects
        draw_cards = getattr(card, 'draw_cards', 0)
        if draw_cards:
            board.draw_card(draw_cards, verbose=verbose)

        damage = getattr(card, 'deals_damage', 0)
        if damage:
            board.drain_damage_this_turn += damage

        # Handle token creation
        if hasattr(card, 'creates_tokens') and card.creates_tokens:
            for token_info in card.creates_tokens:
                board.create_token(
                    token_info.get('type', 'Token'),
                    token_info.get('power', 1),
                    token_info.get('toughness', 1),
                    verbose=verbose
                )

    # Exile the card instead of returning to graveyard
    board.exile.append(card)

    # Track for metrics
    if not hasattr(board, 'flashback_casts'):
        board.flashback_casts = 0
    board.flashback_casts += 1

    if verbose:
        print(f"  → {card.name} exiled after flashback")

    return True


# =============================================================================
# BUYBACK / RETRACE
# =============================================================================

def detect_buyback(oracle_text: str) -> Dict[str, Any]:
    """
    Detect if a card has buyback and parse the cost.

    Returns dict with:
        - has_buyback: bool
        - buyback_cost: str (additional cost to return to hand)
    """
    text = oracle_text.lower()
    result = {
        'has_buyback': False,
        'buyback_cost': None,
    }

    buyback_match = re.search(r'buyback[^{]*({[^}]+})+', text)
    if buyback_match:
        result['has_buyback'] = True
        cost_match = re.findall(r'{([^}]+)}', buyback_match.group(0))
        result['buyback_cost'] = ''.join(cost_match)
    elif 'buyback' in text:
        result['has_buyback'] = True
        cost_match = re.search(r'buyback[—-]?\s*([^\n(]+)', text)
        if cost_match:
            result['buyback_cost'] = cost_match.group(1).strip()

    return result


def detect_retrace(oracle_text: str) -> bool:
    """Check if a card has retrace."""
    return 'retrace' in oracle_text.lower()


def cast_with_buyback(board: 'BoardState', card: 'Card',
                      verbose: bool = False) -> bool:
    """
    Cast a spell with buyback: it returns to hand instead of graveyard.

    Returns True if successful.
    """
    oracle = getattr(card, 'oracle_text', '')
    bb_info = detect_buyback(oracle)

    if not bb_info['has_buyback']:
        return False

    if verbose:
        print(f"Casting {card.name} with Buyback (returning to hand)")

    # Remove from hand
    if card in board.hand:
        board.hand.remove(card)

    # Execute spell effects
    if 'Instant' in card.type or 'Sorcery' in card.type:
        draw_cards = getattr(card, 'draw_cards', 0)
        if draw_cards:
            board.draw_card(draw_cards, verbose=verbose)

        damage = getattr(card, 'deals_damage', 0)
        if damage:
            board.drain_damage_this_turn += damage

        if hasattr(card, 'creates_tokens') and card.creates_tokens:
            for token_info in card.creates_tokens:
                board.create_token(
                    token_info.get('type', 'Token'),
                    token_info.get('power', 1),
                    token_info.get('toughness', 1),
                    verbose=verbose
                )

    # Return to hand instead of graveyard
    board.hand.append(card)

    # Track for metrics
    if not hasattr(board, 'buyback_casts'):
        board.buyback_casts = 0
    board.buyback_casts += 1

    if verbose:
        print(f"  → {card.name} returned to hand (buyback)")

    return True


def cast_retrace(board: 'BoardState', card: 'Card', land_to_discard: 'Card',
                 verbose: bool = False) -> bool:
    """
    Cast a spell using retrace: discard a land to cast from graveyard.

    Returns True if successful.
    """
    oracle = getattr(card, 'oracle_text', '')

    if not detect_retrace(oracle):
        return False

    if card not in board.graveyard:
        return False

    if land_to_discard not in board.hand:
        return False

    if 'Land' not in land_to_discard.type:
        return False

    if verbose:
        print(f"Casting {card.name} via Retrace (discarding {land_to_discard.name})")

    # Discard the land
    board.hand.remove(land_to_discard)
    board.graveyard.append(land_to_discard)

    # Remove from graveyard (temporarily)
    board.graveyard.remove(card)

    # Execute spell effects
    if 'Instant' in card.type or 'Sorcery' in card.type:
        draw_cards = getattr(card, 'draw_cards', 0)
        if draw_cards:
            board.draw_card(draw_cards, verbose=verbose)

        damage = getattr(card, 'deals_damage', 0)
        if damage:
            board.drain_damage_this_turn += damage

    # Card goes to graveyard after casting
    board.graveyard.append(card)

    # Track for metrics
    if not hasattr(board, 'retrace_casts'):
        board.retrace_casts = 0
    board.retrace_casts += 1

    return True


# =============================================================================
# INTEGRATION FUNCTIONS
# =============================================================================

def integrate_extended_mechanics(board_class):
    """
    Monkey-patch the BoardState class with extended mechanics.

    Call this once at module load to add all new methods.
    """
    # Add flicker methods
    board_class.flicker_permanent = lambda self, perm, ret_type='immediate', verbose=False: \
        flicker_permanent(self, perm, ret_type, verbose)
    board_class.process_end_of_turn_flicker_returns = lambda self, verbose=False: \
        process_end_of_turn_flicker_returns(self, verbose)

    # Add copy methods
    board_class.copy_creature = lambda self, source, target, verbose=False: \
        copy_creature(self, source, target, verbose)
    board_class.create_token_copy = lambda self, target, verbose=False: \
        create_token_copy(self, target, verbose)

    # Add cascade/suspend methods
    board_class.resolve_cascade = lambda self, card, verbose=False: \
        resolve_cascade(self, card, verbose)
    board_class.process_suspended_cards = lambda self, verbose=False: \
        process_suspended_cards(self, verbose)
    board_class.suspend_card = lambda self, card, time_counters, verbose=False: \
        suspend_card(self, card, time_counters, verbose)

    # Add persist/undying methods
    board_class.handle_creature_death_persist_undying = lambda self, creature, verbose=False: \
        handle_creature_death_persist_undying(self, creature, verbose)

    # Add convoke/delve methods
    board_class.calculate_convoke_reduction = lambda self, card: \
        calculate_convoke_reduction(self, card)
    board_class.calculate_delve_reduction = lambda self, card: \
        calculate_delve_reduction(self, card)
    board_class.apply_convoke = lambda self, card, creatures_to_tap, verbose=False: \
        apply_convoke(self, card, creatures_to_tap, verbose)
    board_class.apply_delve = lambda self, card, cards_to_exile, verbose=False: \
        apply_delve(self, card, cards_to_exile, verbose)
    board_class.get_effective_mana_cost = lambda self, card: \
        get_effective_mana_cost(self, card)

    # Add flashback methods
    board_class.get_flashback_cards = lambda self: get_flashback_cards(self)
    board_class.cast_flashback = lambda self, card, verbose=False: \
        cast_flashback(self, card, verbose)

    # Add buyback/retrace methods
    board_class.cast_with_buyback = lambda self, card, verbose=False: \
        cast_with_buyback(self, card, verbose)
    board_class.cast_retrace = lambda self, card, land_to_discard, verbose=False: \
        cast_retrace(self, card, land_to_discard, verbose)

    # Add modal spell methods
    board_class.evaluate_modal_choice = lambda self, modes, num_to_choose: \
        evaluate_modal_choice(self, modes, num_to_choose)
    board_class.execute_modal_spell = lambda self, card, chosen_modes, verbose=False: \
        execute_modal_spell(self, card, chosen_modes, verbose)


# =============================================================================
# REFLEXIVE TRIGGERS ("When you do" mechanics)
# =============================================================================

def detect_reflexive_trigger(oracle_text: str) -> Dict[str, Any]:
    """
    Detect reflexive triggers - triggers that occur "when you do" an optional action.

    Generic detection for patterns like:
    - "Whenever you attack, you may sacrifice a creature. When you do, ..."
    - "You may pay {X}. When you do, ..."
    - "You may exile a card. When you do, ..."

    Returns dict with:
        - has_reflexive: bool
        - trigger_condition: str (e.g., "whenever you attack")
        - optional_cost: str (e.g., "sacrifice a creature")
        - reflexive_effect: str (what happens "when you do")
        - is_modal: bool (if the reflexive effect is modal)
    """
    text = oracle_text.lower()
    result = {
        'has_reflexive': False,
        'trigger_condition': None,
        'optional_cost': None,
        'reflexive_effect': None,
        'is_modal': False,
    }

    # Pattern: "whenever/when X, you may Y. when you do, Z"
    reflexive_pattern = re.compile(
        r'(whenever|when)\s+([^.]+?),\s+you may\s+([^.]+?)\.\s+when you do,?\s+(.+?)(?:\.|$)',
        re.IGNORECASE | re.DOTALL
    )

    match = reflexive_pattern.search(text)
    if match:
        result['has_reflexive'] = True
        result['trigger_condition'] = match.group(2).strip()
        result['optional_cost'] = match.group(3).strip()
        result['reflexive_effect'] = match.group(4).strip()

        # Check if reflexive effect is modal
        if 'choose' in result['reflexive_effect'] and '•' in oracle_text:
            result['is_modal'] = True

    return result


def parse_optional_cost(cost_text: str) -> Dict[str, Any]:
    """
    Parse optional cost from text like "sacrifice another creature" or "pay {X}".

    Returns dict with:
        - cost_type: 'sacrifice', 'pay_mana', 'discard', 'exile', etc.
        - target: what is sacrificed/paid/etc.
        - quantity: how many (if specified)
    """
    text = cost_text.lower()
    result = {
        'cost_type': None,
        'target': None,
        'quantity': 1,
    }

    # Sacrifice costs
    if 'sacrifice' in text:
        result['cost_type'] = 'sacrifice'
        if 'another creature' in text:
            result['target'] = 'another_creature'
        elif 'a creature' in text or 'creature' in text:
            result['target'] = 'creature'
        elif 'a permanent' in text:
            result['target'] = 'permanent'
        elif 'artifact' in text:
            result['target'] = 'artifact'

    # Mana costs
    elif 'pay' in text:
        result['cost_type'] = 'pay_mana'
        # Extract mana amount if specified
        mana_match = re.search(r'\{(\d+)\}', text)
        if mana_match:
            result['quantity'] = int(mana_match.group(1))

    # Discard costs
    elif 'discard' in text:
        result['cost_type'] = 'discard'
        result['target'] = 'card'

    # Exile costs
    elif 'exile' in text:
        result['cost_type'] = 'exile'
        if 'card' in text:
            result['target'] = 'card'

    return result


def detect_modal_triggered_ability(oracle_text: str) -> Dict[str, Any]:
    """
    Extend modal detection to work with triggered abilities, not just spells.

    Detects patterns like:
    - "Whenever X, choose two — • A • B • C"
    - "When Y, choose one or more — • A • B"

    Returns same format as detect_modal_spell but for triggered abilities.
    """
    text = oracle_text.lower()
    result = {
        'is_modal_trigger': False,
        'trigger_event': None,
        'num_modes': 0,
        'modes_to_choose': 1,
        'modes': [],
    }

    # Check for triggered ability with modal choice
    trigger_modal_pattern = re.compile(
        r'(whenever|when|at)\s+([^,]+),\s+(choose\s+(?:one|two|three|one or more))\s*—?',
        re.IGNORECASE
    )

    match = trigger_modal_pattern.search(text)
    if match:
        result['is_modal_trigger'] = True
        result['trigger_event'] = match.group(2).strip()
        choice_text = match.group(3).strip()

        # Determine number of modes to choose
        if 'choose two' in choice_text:
            result['modes_to_choose'] = 2
        elif 'choose three' in choice_text:
            result['modes_to_choose'] = 3
        elif 'choose one or more' in choice_text:
            result['modes_to_choose'] = -1  # Variable
        else:
            result['modes_to_choose'] = 1

        # Parse individual modes (bullet points)
        mode_matches = re.findall(r'•\s*([^•]+?)(?=•|$)', oracle_text, re.DOTALL)
        if mode_matches:
            result['modes'] = [m.strip() for m in mode_matches]
            result['num_modes'] = len(result['modes'])

    return result


def execute_reflexive_trigger(board: 'BoardState', card: 'Card',
                              reflexive_info: Dict[str, Any], verbose: bool = False) -> bool:
    """
    Execute a reflexive trigger generically.

    Args:
        board: Current board state
        card: The card with the reflexive trigger
        reflexive_info: Output from detect_reflexive_trigger()
        verbose: Print debug output

    Returns:
        True if trigger executed successfully
    """
    if not reflexive_info['has_reflexive']:
        return False

    # Parse and evaluate optional cost
    cost_info = parse_optional_cost(reflexive_info['optional_cost'])

    # Decide whether to pay the cost (AI decision)
    should_pay_cost = False

    if cost_info['cost_type'] == 'sacrifice':
        # Check if we have something to sacrifice
        if cost_info['target'] == 'another_creature':
            # Need at least 2 creatures (one being the trigger source)
            sacrificeable = [c for c in board.creatures if c != card]
            if sacrificeable:
                should_pay_cost = True
                # Choose least valuable creature to sacrifice
                # For now, sacrifice smallest creature
                sacrifice_target = min(sacrificeable, key=lambda c: (getattr(c, 'power', 0) or 0))
        elif cost_info['target'] == 'creature':
            if len(board.creatures) > 0:
                should_pay_cost = True
                sacrifice_target = min(board.creatures, key=lambda c: (getattr(c, 'power', 0) or 0))

    # If we decided to pay the cost, execute it and the reflexive effect
    if should_pay_cost:
        # Pay the cost
        if cost_info['cost_type'] == 'sacrifice' and sacrifice_target:
            board.sacrifice_creature(sacrifice_target, verbose=verbose)
            if verbose:
                print(f"  → Paid optional cost: sacrificed {sacrifice_target.name}")

            # Execute the reflexive effect
            if reflexive_info['is_modal']:
                # The effect is modal - parse and execute
                modal_info = detect_modal_triggered_ability(card.oracle_text)
                if modal_info['is_modal_trigger']:
                    # Use existing modal choice evaluation
                    chosen_modes = evaluate_modal_choice(board, modal_info['modes'],
                                                        modal_info['modes_to_choose'])
                    if verbose:
                        print(f"  → Reflexive modal effect: choosing modes {chosen_modes}")

                    # Execute each chosen mode
                    for mode_idx in chosen_modes:
                        if mode_idx < len(modal_info['modes']):
                            mode_text = modal_info['modes'][mode_idx]
                            _execute_mode_effect(board, mode_text, verbose)
            else:
                # Non-modal reflexive effect - execute generically
                effect_text = reflexive_info['reflexive_effect']
                _execute_mode_effect(board, effect_text, verbose)

            return True

    return False


# =============================================================================
# METRIC TRACKING EXTENSIONS
# =============================================================================

def initialize_extended_metrics(board: 'BoardState') -> None:
    """Initialize tracking variables for extended mechanics."""
    board.flicker_count = 0
    board.cascade_casts = 0
    board.persist_triggers = 0
    board.undying_triggers = 0
    board.flashback_casts = 0
    board.buyback_casts = 0
    board.retrace_casts = 0
    board.suspended_cards = []
    board.pending_flicker_returns = []


def get_extended_metrics(board: 'BoardState') -> Dict[str, int]:
    """Get all extended mechanic metrics from the board state."""
    return {
        'flicker_count': getattr(board, 'flicker_count', 0),
        'cascade_casts': getattr(board, 'cascade_casts', 0),
        'persist_triggers': getattr(board, 'persist_triggers', 0),
        'undying_triggers': getattr(board, 'undying_triggers', 0),
        'flashback_casts': getattr(board, 'flashback_casts', 0),
        'buyback_casts': getattr(board, 'buyback_casts', 0),
        'retrace_casts': getattr(board, 'retrace_casts', 0),
        'suspended_cards_count': len(getattr(board, 'suspended_cards', [])),
        'pending_flicker_count': len(getattr(board, 'pending_flicker_returns', [])),
    }
