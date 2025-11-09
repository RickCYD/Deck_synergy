import random

def draw_starting_hand(deck_cards, commander_card):
    """
    Draw an opening hand from the deck (excluding the commander which is in command zone).
    Applies London Mulligan rules with one free mulligan.
    Returns a list representing the opening hand.
    """
    # Shuffle a copy of the deck list to simulate drawing
    deck = deck_cards[:]  # shallow copy
    random.shuffle(deck)
    
    def is_hand_acceptable(hand):
        """Decide if an opening hand is keepable based on land count."""
        land_count = sum(1 for card in hand if card.type == 'Land' )
        # Heuristic: Commander decks typically want a balanced land count
        # Require at least 2 lands and at most 4 lands in opening 7 (heuristic)
        if land_count < 3 or land_count > 5:
            return False
        return True
    
    
    hand = deck[:7]  # draw top 7
    mulligans_taken = 0
    # First mulligan is free in Commander
    if not is_hand_acceptable(hand):
        mulligans_taken += 1
        # Free mulligan (redraw 7, no bottom card)
        random.shuffle(deck)
        hand = deck[:7]
    # For subsequent mulligans (if the second hand is still bad)
    while not is_hand_acceptable(hand) and mulligans_taken < 7:
        mulligans_taken += 1
        random.shuffle(deck)
        new_hand = deck[:7]
        # Under London Mulligan, for mulligan number N, you will end up with 7-N cards in hand.
        # So we draw 7 and then bottom (i.e., remove) N cards from the hand.
        # We'll remove N cards that are least useful in opening hand context.
        # Determine how many to bottom (should equal mulligans_taken, since first mulligan was free, second mulligan => 1 card bottomed, etc.)
        num_to_bottom = 0 if mulligans_taken == 1 else mulligans_taken - 1  # since first mulligan is free
        if num_to_bottom > 0:
            # Simple heuristic: identify cards to bottom
            # If too many lands, bottom the extra lands; if too few lands, bottom high-cost spells.
            land_count = sum(1 for card in new_hand if card.type == 'Land')
            cards_to_bottom = []
            if land_count > 4:
                # bottom lands if we have way too many
                lands_in_hand = [card for card in new_hand if card.type == 'Land']
                cards_to_bottom = random.sample(lands_in_hand, min(num_to_bottom, len(lands_in_hand)))
            elif land_count < 2:
                # bottom high cost spells if mana is scarce (keep cheaper spells hoping to draw lands)
                nonlands = [card for card in new_hand if card.type != 'Land']
                nonlands.sort(key=lambda c: parse_mana_cost(c.mana_cost), reverse=True)  # sort by cost descending
                # parse_mana_cost will extract total mana value; we'll define it below.
                cards_to_bottom = nonlands[:num_to_bottom]
            else:
                # Otherwise, bottom the highest mana cost spells (default strategy).
                nonlands = [card for card in new_hand if card.type != 'Land']
                nonlands.sort(key=lambda c: parse_mana_cost(c.mana_cost), reverse=True)
                cards_to_bottom = nonlands[:num_to_bottom]
            # Remove those cards from hand
            for card in cards_to_bottom:
                new_hand.remove(card)
        hand = new_hand
        # Stop if this hand is acceptable or we have mulliganed down to very few cards
        if is_hand_acceptable(hand) or len(hand) <= 3:
            break
        for c in hand:
            deck.remove(c)  # remove from library if we bottomed it
    # Remove drawn cards from the deck so the remaining library can be used
    for card in hand:
        if card in deck:
            deck.remove(card)

    # Final opening hand ready
    return hand, deck

def parse_mana_cost(cost_str):
    """
    Helper to parse a mana cost string like '2WG' or '3' into a total mana value (converted mana cost).
    For simplicity, each numeric character adds that number, and each letter (color) adds 1.
    """
    if cost_str is None:
        return 0
    total = 0
    num_buffer = ''
    for ch in cost_str:
        if ch.isdigit():
            # accumulate multi-digit numbers
            num_buffer += ch
        else:
            # if there was a number before a letter, add it
            if num_buffer:
                total += int(num_buffer)
                num_buffer = ''
            if ch.isalpha():
                # each colored mana symbol counts as 1 towards total cost
                total += 1
    # If string ended in a number (unlikely in mana costs), add it
    if num_buffer:
        total += int(num_buffer)
    return total
