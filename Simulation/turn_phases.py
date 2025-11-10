
def setup_phase(verbose=False):
    """
    Simulates the setup phase of a turn in a card game.
    In this phase, players may perform initial setup actions before the main phases begin.
    """
    if verbose:
        print("Setup Phase: Players prepare for their turn.")
    # Logic for setup actions would go here
    # For example, shuffling decks, drawing initial hands, etc.
    # This is a placeholder; actual game logic would depend on the game's rules

def untap_phase(boards_state, verbose=False):
    """Untap permanents and refresh their activated abilities."""
    tapped = boards_state.lands_tapped
    if tapped:
        boards_state.lands_untapped.extend(tapped)
        for card in tapped:
            card.tapped = False
            boards_state._add_abilities_from_card(card)
    boards_state.lands_tapped = []

    for perm in boards_state.artifacts + boards_state.creatures + boards_state.enchantments + boards_state.planeswalkers:
        if getattr(perm, "tapped", False):
            perm.tapped = False
            boards_state._add_abilities_from_card(perm)

    if verbose:
        if tapped:
            names = ", ".join(card.name for card in tapped)
            print(f"Untap Phase: Untapped {names}.")
        else:
            print("Untap Phase: No tapped cards to untap.")

def upkeep_phase(board_state, verbose=False):
    """
    Simulates the upkeep phase of a turn.

    This phase handles:
    - Saga advancement
    - "At the beginning of your upkeep" triggers
    - Upkeep token creation (Rite of the Raging Storm, etc.)
    - Upkeep card draw, life gain/loss
    - Other upkeep effects

    Parameters
    ----------
    board_state : BoardState
        The current board state
    verbose : bool
        If True, print detailed upkeep information

    Returns
    -------
    int
        Number of tokens created during upkeep
    """
    if verbose:
        print("Upkeep Phase: Processing triggers and effects")

    # Advance sagas (existing functionality)
    board_state.advance_sagas(verbose=verbose)

    # Process upkeep triggers (NEW!)
    tokens_created = board_state.process_upkeep_triggers(verbose=verbose)

    return tokens_created
def draw_phase(boards_state, verbose=False):
    """Simulates the draw phase of a turn.

    Parameters
    ----------
    boards_state : BoardState
        The board state to draw cards for.
    verbose : bool, optional
        If ``True`` prints debug information.

    Returns
    -------
    list
        The list of cards drawn during this phase.
    """
    if verbose:
        print("Draw Phase: Player draws a card from their library.")

    drawn = boards_state.draw_card(1, verbose=verbose)

    # Logic to draw a card would go here (placeholder)
    return drawn

def main_phase():
    """
    Simulates the main phase of a turn in a card game.
    In this phase, players can play lands, cast spells, and activate abilities.
    """
    print("Main Phase: Players can play lands, cast spells, and activate abilities.")
    # Logic for playing lands, casting spells, etc. would go here
    # This is a placeholder; actual game logic would depend on the game's rules

def combat_phase():
    """
    Simulates the combat phase of a turn in a card game.
    In this phase, players can declare attackers and blockers, and resolve combat damage.
    """
    print("Combat Phase: Players declare attackers and blockers, and resolve combat damage.")
    # Logic for declaring attackers, blockers, and resolving combat would go here
    # This is a placeholder; actual game logic would depend on the game's rules

def end_phase():
    """
    Simulates the end phase of a turn in a card game.
    In this phase, players may have effects that occur at the end of their turn.
    """
    print("End Phase: Check for end-of-turn effects and cleanup.")
    # Logic to handle end-of-turn effects would go here
    # For example, check for cards with "at the end of your turn" effects
    # This is a placeholder; actual game logic would depend on the game's rules
