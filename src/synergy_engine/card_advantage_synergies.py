"""
Card Advantage Synergy Detection Rules

Detects synergies between card advantage effects:
- Card draw + draw payoffs
- Wheels + discard matters
- Tutors + combo pieces
- Mill + graveyard strategies
- Looting + reanimation
- Reanimation + big creatures/ETBs
- Flashback + discard outlets
- Extra turns + win conditions
- Cascade + cheap spells
- Treasure/Clue tokens + artifact matters
"""

from typing import Dict, List
from src.utils.card_advantage_extractors import classify_card_advantage
from src.synergy_engine.recursion_synergies import RECURSION_SYNERGY_RULES


def detect_draw_payoff_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between card draw effects and draw payoff cards.

    Examples:
    - Rhystic Study + Niv-Mizzet, Parun (draw = damage)
    - Wheel of Fortune + The Locust God (draw = tokens)
    - Consecrated Sphinx + Psychosis Crawler (draw = life loss)
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    # Extract card advantage mechanics
    card1_adv = classify_card_advantage(card1)
    card2_adv = classify_card_advantage(card2)

    # Check Card1 = draw, Card2 = payoff
    if card1_adv['card_draw']['has_draw'] and card2_adv['draw_payoffs']['is_draw_payoff']:
        draw_info = card1_adv['card_draw']
        payoff_info = card2_adv['draw_payoffs']

        # Calculate synergy strength
        strength = 1.0

        # Repeatable draw is stronger with payoffs
        if 'repeatable' in draw_info['draw_types']:
            strength += 2.0

        # Multiple card draw is stronger
        if draw_info['draw_amount'] and draw_info['draw_amount'] >= 3:
            strength += 1.0
        elif draw_info['draw_amount'] and draw_info['draw_amount'] == 2:
            strength += 0.5

        # Strong payoff effects
        payoff_effects = payoff_info['payoff_effects']
        if 'damage' in payoff_effects:
            strength += 1.5  # Damage is very strong
        if 'token' in payoff_effects:
            strength += 1.0  # Token generation is good
        if 'counter' in payoff_effects or 'life' in payoff_effects:
            strength += 0.5

        synergies.append({
            'category': 'Card Draw → Payoff',
            'card1_role': 'Draw Engine',
            'card2_role': 'Draw Payoff',
            'description': f"{card1_name} draws cards which triggers {card2_name}'s {', '.join(payoff_effects)} ability",
            'strength': strength,
            'combo_notes': f"Each draw triggers {card2_name}"
        })

    # Check Card2 = draw, Card1 = payoff (reverse)
    if card2_adv['card_draw']['has_draw'] and card1_adv['draw_payoffs']['is_draw_payoff']:
        draw_info = card2_adv['card_draw']
        payoff_info = card1_adv['draw_payoffs']

        strength = 1.0
        if 'repeatable' in draw_info['draw_types']:
            strength += 2.0
        if draw_info['draw_amount'] and draw_info['draw_amount'] >= 3:
            strength += 1.0

        payoff_effects = payoff_info['payoff_effects']
        if 'damage' in payoff_effects:
            strength += 1.5
        if 'token' in payoff_effects:
            strength += 1.0

        synergies.append({
            'category': 'Card Draw → Payoff',
            'card1_role': 'Draw Payoff',
            'card2_role': 'Draw Engine',
            'description': f"{card2_name} draws cards which triggers {card1_name}'s {', '.join(payoff_effects)} ability",
            'strength': strength,
            'combo_notes': f"Each draw triggers {card1_name}"
        })

    return synergies


def detect_wheel_discard_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between wheel effects and discard matters cards.

    Examples:
    - Wheel of Fortune + Bone Miser (wheel = mana/tokens/cards)
    - Windfall + Waste Not (opponents discard = value)
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_adv = classify_card_advantage(card1)
    card2_adv = classify_card_advantage(card2)

    # Check for wheel effect
    wheel1 = card1_adv['wheel_effects']
    wheel2 = card2_adv['wheel_effects']

    # Check for discard payoffs (cards that care when you/opponents discard)
    # This is approximated by checking oracle text for "whenever" + "discard"
    text1 = card1.get('oracle_text', '').lower()
    text2 = card2.get('oracle_text', '').lower()

    discard_matters1 = 'whenever' in text1 and 'discard' in text1
    discard_matters2 = 'whenever' in text2 and 'discard' in text2

    if wheel1['is_wheel'] and discard_matters2:
        strength = 2.0  # Wheels are strong with discard matters

        if wheel1['wheel_type'] == 'full_wheel':
            strength += 1.5  # Full wheel makes everyone discard
        elif wheel1['wheel_type'] == 'partial_wheel':
            strength += 1.0

        synergies.append({
            'category': 'Wheel → Discard Matters',
            'card1_role': 'Wheel Effect',
            'card2_role': 'Discard Payoff',
            'description': f"{card1_name} makes players discard, triggering {card2_name}",
            'strength': strength,
            'combo_notes': f"{wheel1['wheel_type']} with discard payoff"
        })

    if wheel2['is_wheel'] and discard_matters1:
        strength = 2.0

        if wheel2['wheel_type'] == 'full_wheel':
            strength += 1.5

        synergies.append({
            'category': 'Wheel → Discard Matters',
            'card1_role': 'Discard Payoff',
            'card2_role': 'Wheel Effect',
            'description': f"{card2_name} makes players discard, triggering {card1_name}",
            'strength': strength,
            'combo_notes': f"{wheel2['wheel_type']} with discard payoff"
        })

    return synergies


def detect_tutor_combo_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between tutors and high-value targets.

    Examples:
    - Demonic Tutor + any combo piece
    - Chord of Calling + specific creature combos
    - Mystical Tutor + extra turn spells
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_adv = classify_card_advantage(card1)
    card2_adv = classify_card_advantage(card2)

    tutor1 = card1_adv['tutors']
    tutor2 = card2_adv['tutors']

    # Check if one card is a tutor
    if tutor1['is_tutor']:
        # Check if card2 is a high-value target
        card2_type = card2.get('type_line', '').lower()

        # Check if tutor can find this card type
        can_find = False
        tutor_type = tutor1['tutor_type']

        if tutor_type == 'any':
            can_find = True
        elif tutor_type == 'creature' and 'creature' in card2_type:
            can_find = True
        elif tutor_type == 'instant' and 'instant' in card2_type:
            can_find = True
        elif tutor_type == 'sorcery' and 'sorcery' in card2_type:
            can_find = True
        elif tutor_type == 'instant_or_sorcery' and ('instant' in card2_type or 'sorcery' in card2_type):
            can_find = True
        elif tutor_type == 'artifact' and 'artifact' in card2_type:
            can_find = True
        elif tutor_type == 'enchantment' and 'enchantment' in card2_type:
            can_find = True
        elif tutor_type == 'artifact_or_enchantment' and ('artifact' in card2_type or 'enchantment' in card2_type):
            can_find = True
        elif tutor_type == 'land' and 'land' in card2_type:
            can_find = True

        # Check CMC restrictions (transmute, etc.)
        if can_find:
            for restriction in tutor1['restrictions']:
                if restriction == 'cmc_exact_match':
                    # Transmute: must match tutor's CMC exactly
                    tutor_cmc = card1.get('cmc', 0)
                    target_cmc = card2.get('cmc', 0)
                    if tutor_cmc != target_cmc:
                        can_find = False
                        break

        # Check power/toughness restrictions if applicable
        if can_find and tutor_type == 'creature':
            for restriction in tutor1['restrictions']:
                if restriction.startswith('power_restriction_'):
                    max_power = int(restriction.split('_')[-1])
                    card2_power = card2.get('power', '')
                    if card2_power and card2_power != '*':
                        try:
                            if int(card2_power) > max_power:
                                can_find = False
                                break
                        except (ValueError, TypeError):
                            pass  # If power can't be converted, skip restriction
                elif restriction.startswith('toughness_restriction_'):
                    max_toughness = int(restriction.split('_')[-1])
                    card2_toughness = card2.get('toughness', '')
                    if card2_toughness and card2_toughness != '*':
                        try:
                            if int(card2_toughness) > max_toughness:
                                can_find = False
                                break
                        except (ValueError, TypeError):
                            pass  # If toughness can't be converted, skip restriction

        if can_find:
            strength = 0.5  # Base synergy for any tutor target

            # Higher value for tutors that put to hand or battlefield
            if tutor1['destination'] in ['hand', 'battlefield']:
                strength += 0.5

            # Higher value for expensive/powerful cards
            cmc = card2.get('cmc', 0)
            if cmc >= 6:
                strength += 1.0
            elif cmc >= 4:
                strength += 0.5

            # Check if card2 has combo potential (keywords that indicate power)
            text2 = card2.get('oracle_text', '').lower()
            combo_keywords = ['combo', 'infinite', 'extra turn', 'tutor', 'win the game', 'each opponent']
            if any(keyword in text2 for keyword in combo_keywords):
                strength += 1.5

            if strength >= 1.0:  # Only report if synergy is meaningful
                synergies.append({
                    'category': 'Tutor → Target',
                    'card1_role': 'Tutor',
                    'card2_role': 'Tutor Target',
                    'description': f"{card1_name} can fetch {card2_name}",
                    'strength': strength,
                    'combo_notes': f"Tutors {card2_name} to {tutor1['destination']}"
                })

    # Check reverse (card2 is tutor)
    if tutor2['is_tutor']:
        card1_type = card1.get('type_line', '').lower()

        can_find = False
        tutor_type = tutor2['tutor_type']

        if tutor_type == 'any':
            can_find = True
        elif tutor_type == 'creature' and 'creature' in card1_type:
            can_find = True
        elif tutor_type == 'instant' and 'instant' in card1_type:
            can_find = True
        elif tutor_type == 'sorcery' and 'sorcery' in card1_type:
            can_find = True
        elif tutor_type == 'instant_or_sorcery' and ('instant' in card1_type or 'sorcery' in card1_type):
            can_find = True
        elif tutor_type == 'artifact' and 'artifact' in card1_type:
            can_find = True
        elif tutor_type == 'enchantment' and 'enchantment' in card1_type:
            can_find = True
        elif tutor_type == 'artifact_or_enchantment' and ('artifact' in card1_type or 'enchantment' in card1_type):
            can_find = True
        elif tutor_type == 'land' and 'land' in card1_type:
            can_find = True

        if can_find:
            strength = 0.5

            if tutor2['destination'] in ['hand', 'battlefield']:
                strength += 0.5

            cmc = card1.get('cmc', 0)
            if cmc >= 6:
                strength += 1.0
            elif cmc >= 4:
                strength += 0.5

            text1 = card1.get('oracle_text', '').lower()
            combo_keywords = ['combo', 'infinite', 'extra turn', 'tutor', 'win the game', 'each opponent']
            if any(keyword in text1 for keyword in combo_keywords):
                strength += 1.5

            if strength >= 1.0:
                synergies.append({
                    'category': 'Tutor → Target',
                    'card1_role': 'Tutor Target',
                    'card2_role': 'Tutor',
                    'description': f"{card2_name} can fetch {card1_name}",
                    'strength': strength,
                    'combo_notes': f"Tutors {card1_name} to {tutor2['destination']}"
                })

    return synergies


def detect_mill_graveyard_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between mill effects and graveyard strategies.

    Examples:
    - Hedron Crab + cards that care about graveyard
    - Mill + reanimation targets
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_adv = classify_card_advantage(card1)
    card2_adv = classify_card_advantage(card2)

    mill1 = card1_adv['mill']
    mill2 = card2_adv['mill']

    # Check for graveyard matters cards
    # NOTE: flashback, jump-start, retrace are SELF-RECURSION - they don't benefit from mill
    # Real graveyard payoffs: reanimation, delve, escape, threshold, delirium
    text1 = card1.get('oracle_text', '').lower()
    text2 = card2.get('oracle_text', '').lower()

    import re
    graveyard_payoff_patterns = [
        r'return.*from.*graveyard.*to.*(?:battlefield|hand)',  # Reanimation
        r'delve',  # Delve
        r'escape',  # Escape
        r'threshold',  # Threshold
        r'delirium',  # Delirium
        r'undergrowth',  # Undergrowth
        r'dredge',  # Dredge (replaces draws with mill + return)
        r'cards?\s+in\s+(?:your|a|all)\s+graveyard',  # Counts graveyard
        r'for\s+each.*in.*graveyard',  # Counts graveyard
    ]

    graveyard_matters1 = any(re.search(pattern, text1) for pattern in graveyard_payoff_patterns)
    graveyard_matters2 = any(re.search(pattern, text2) for pattern in graveyard_payoff_patterns)

    # Self-mill + graveyard matters
    if mill1['has_mill'] and 'self' in mill1['mill_targets'] and graveyard_matters2:
        strength = 1.5

        if mill1['repeatable']:
            strength += 1.0

        synergies.append({
            'category': 'Self-Mill → Graveyard Strategy',
            'card1_role': 'Self-Mill',
            'card2_role': 'Graveyard Payoff',
            'description': f"{card1_name} mills yourself, enabling {card2_name}",
            'strength': strength,
            'combo_notes': "Fills graveyard for synergies"
        })

    if mill2['has_mill'] and 'self' in mill2['mill_targets'] and graveyard_matters1:
        strength = 1.5

        if mill2['repeatable']:
            strength += 1.0

        synergies.append({
            'category': 'Self-Mill → Graveyard Strategy',
            'card1_role': 'Graveyard Payoff',
            'card2_role': 'Self-Mill',
            'description': f"{card2_name} mills yourself, enabling {card1_name}",
            'strength': strength,
            'combo_notes': "Fills graveyard for synergies"
        })

    return synergies


def detect_looting_reanimation_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between looting effects and reanimation.

    Examples:
    - Faithless Looting + Reanimate
    - Chart a Course + creature reanimation targets
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_adv = classify_card_advantage(card1)
    card2_adv = classify_card_advantage(card2)

    loot1 = card1_adv['looting']
    loot2 = card2_adv['looting']

    # Check for reanimation (simplified check)
    text1 = card1.get('oracle_text', '').lower()
    text2 = card2.get('oracle_text', '').lower()

    reanimate1 = 'return' in text1 and 'graveyard' in text1 and 'battlefield' in text1
    reanimate2 = 'return' in text2 and 'graveyard' in text2 and 'battlefield' in text2

    if loot1['is_looting'] and reanimate2:
        strength = 2.0  # Looting + reanimation is a classic combo

        synergies.append({
            'category': 'Looting → Reanimation',
            'card1_role': 'Loot Effect',
            'card2_role': 'Reanimation',
            'description': f"{card1_name} loots, putting creatures in graveyard for {card2_name} to reanimate",
            'strength': strength,
            'combo_notes': f"Net {loot1['net_advantage']:+d} cards while enabling reanimation"
        })

    if loot2['is_looting'] and reanimate1:
        strength = 2.0

        synergies.append({
            'category': 'Looting → Reanimation',
            'card1_role': 'Reanimation',
            'card2_role': 'Loot Effect',
            'description': f"{card2_name} loots, putting creatures in graveyard for {card1_name} to reanimate",
            'strength': strength,
            'combo_notes': f"Net {loot2['net_advantage']:+d} cards while enabling reanimation"
        })

    return synergies


# List of all card advantage synergy detection functions
CARD_ADVANTAGE_SYNERGY_RULES = [
    detect_draw_payoff_synergies,
    detect_wheel_discard_synergies,
    detect_tutor_combo_synergies,
    detect_mill_graveyard_synergies,
    detect_looting_reanimation_synergies
] + RECURSION_SYNERGY_RULES  # Add recursion/graveyard synergies (6 new rules)
