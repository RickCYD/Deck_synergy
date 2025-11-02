"""
Recursion & Graveyard Synergy Detection Rules

Detects synergies between recursion effects:
- Reanimation + big creatures/ETBs
- Reanimation + mill/entomb
- Flashback + discard outlets
- Extra turns + win conditions
- Cascade + cheap spells
- Treasure tokens + artifact matters
- Clue tokens + sacrifice payoffs
"""

import re
from typing import Dict, List
from src.utils.recursion_extractors import classify_recursion_mechanics


def detect_reanimation_big_creatures(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between reanimation and expensive/powerful creatures.

    Examples:
    - Reanimate + Griselbrand (big creature)
    - Animate Dead + Avacyn (expensive angel)
    - Living Death + expensive creatures
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    reanimate1 = card1_recursion['reanimation']
    reanimate2 = card2_recursion['reanimation']

    card1_type = card1.get('type_line', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 reanimates and card2 is a good target
    if reanimate1['has_reanimation'] and 'creature' in card1_recursion['reanimation']['targets']:
        if 'creature' in card2_type:
            # High CMC creatures are prime reanimation targets
            if card2_cmc >= 6:
                strength = 2.0
                if card2_cmc >= 8:
                    strength += 1.0  # Very expensive = better target
                if card2_cmc >= 10:
                    strength += 0.5  # Huge creatures

                # Check for powerful keywords/abilities
                card2_text = card2.get('oracle_text', '').lower()
                power_keywords = ['draw', 'flying', 'trample', 'when.*enters', 'annihilator', 'protection']
                if any(kw in card2_text for kw in power_keywords):
                    strength += 0.5

                synergies.append({
                    'category': 'Reanimation → Target',
                    'card1_role': 'Reanimation',
                    'card2_role': 'Reanimation Target',
                    'description': f"{card1_name} can reanimate {card2_name} (CMC {card2_cmc})",
                    'strength': strength,
                    'combo_notes': f"Cheat {card2_name} into play"
                })

    # Check reverse
    if reanimate2['has_reanimation'] and 'creature' in card2_recursion['reanimation']['targets']:
        if 'creature' in card1_type:
            if card1_cmc >= 6:
                strength = 2.0
                if card1_cmc >= 8:
                    strength += 1.0
                if card1_cmc >= 10:
                    strength += 0.5

                card1_text = card1.get('oracle_text', '').lower()
                power_keywords = ['draw', 'flying', 'trample', 'when.*enters', 'annihilator', 'protection']
                if any(kw in card1_text for kw in power_keywords):
                    strength += 0.5

                synergies.append({
                    'category': 'Reanimation → Target',
                    'card1_role': 'Reanimation Target',
                    'card2_role': 'Reanimation',
                    'description': f"{card2_name} can reanimate {card1_name} (CMC {card1_cmc})",
                    'strength': strength,
                    'combo_notes': f"Cheat {card1_name} into play"
                })

    return synergies


def detect_flashback_discard_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between flashback/graveyard casting and discard outlets.

    Examples:
    - Faithless Looting (flashback) + wheel effects
    - Flashback cards + Seasoned Pyromancer
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    flashback1 = card1_recursion['graveyard_casting']
    flashback2 = card2_recursion['graveyard_casting']

    # Check if either card has flashback/graveyard casting
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Discard outlet patterns
    discard_outlet_patterns = ['discard', 'wheel', 'draws? cards?.*discards?']

    card1_is_discard_outlet = any(pattern in card1_text for pattern in ['discard', 'wheel'])
    card2_is_discard_outlet = any(pattern in card2_text for pattern in ['discard', 'wheel'])

    if flashback1['has_graveyard_casting'] and card2_is_discard_outlet:
        strength = 1.5
        if 'flashback' in flashback1['casting_types']:
            strength += 0.5  # Flashback is the classic use case

        synergies.append({
            'category': 'Graveyard Casting → Enabler',
            'card1_role': 'Graveyard Spell',
            'card2_role': 'Discard Outlet',
            'description': f"{card2_name} discards {card1_name}, which can be cast from graveyard",
            'strength': strength,
            'combo_notes': f"Cast {card1_name} from graveyard after discarding"
        })

    if flashback2['has_graveyard_casting'] and card1_is_discard_outlet:
        strength = 1.5
        if 'flashback' in flashback2['casting_types']:
            strength += 0.5

        synergies.append({
            'category': 'Graveyard Casting → Enabler',
            'card1_role': 'Discard Outlet',
            'card2_role': 'Graveyard Spell',
            'description': f"{card1_name} discards {card2_name}, which can be cast from graveyard",
            'strength': strength,
            'combo_notes': f"Cast {card2_name} from graveyard after discarding"
        })

    return synergies


def detect_extra_turns_wincons(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between extra turns and win conditions.

    Examples:
    - Nexus of Fate + Wilderness Reclamation
    - Time Warp + powerful planeswalkers
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    turns1 = card1_recursion['extra_turns']
    turns2 = card2_recursion['extra_turns']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()
    card2_type = card2.get('type_line', '').lower()
    card1_type = card1.get('type_line', '').lower()

    # Win condition patterns
    wincon_patterns = ['planeswalker', 'win the game', 'loyalty', 'combat damage', 'commander damage']

    card2_is_wincon = any(pattern in card2_type or pattern in card2_text for pattern in wincon_patterns)
    card1_is_wincon = any(pattern in card1_type or pattern in card1_text for pattern in wincon_patterns)

    if turns1['has_extra_turns'] and card2_is_wincon:
        strength = 2.5
        if turns1['turn_type'] == 'infinite_potential':
            strength += 1.5  # Can go infinite
        if 'planeswalker' in card2_type:
            strength += 0.5  # Extra turns = extra activations

        synergies.append({
            'category': 'Extra Turns → Win Con',
            'card1_role': 'Extra Turns',
            'card2_role': 'Win Condition',
            'description': f"{card1_name} takes extra turns to enable {card2_name}",
            'strength': strength,
            'combo_notes': "Extra turns accelerate win condition"
        })

    if turns2['has_extra_turns'] and card1_is_wincon:
        strength = 2.5
        if turns2['turn_type'] == 'infinite_potential':
            strength += 1.5
        if 'planeswalker' in card1_type:
            strength += 0.5

        synergies.append({
            'category': 'Extra Turns → Win Con',
            'card1_role': 'Win Condition',
            'card2_role': 'Extra Turns',
            'description': f"{card2_name} takes extra turns to enable {card1_name}",
            'strength': strength,
            'combo_notes': "Extra turns accelerate win condition"
        })

    return synergies


def detect_cascade_cheap_spells(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between cascade and cheap powerful spells.

    Examples:
    - Bloodbraid Elf + Lightning Bolt
    - Maelstrom Wanderer + powerful 7-drops
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    cascade1 = card1_recursion['cascade']
    cascade2 = card2_recursion['cascade']

    card1_cmc = card1.get('cmc', 0)
    card2_cmc = card2.get('cmc', 0)

    # Check if card1 has cascade and card2 is a good target
    if cascade1['has_cascade']:
        # Good cascade targets: CMC less than cascade spell, powerful effect
        if card2_cmc < card1_cmc and card2_cmc > 0:
            # More valuable if it's a removal spell, draw spell, or has good value
            card2_text = card2.get('oracle_text', '').lower()
            value_keywords = ['destroy', 'exile', 'draw', 'damage', 'counter', 'tutor']

            strength = 1.0
            if any(kw in card2_text for kw in value_keywords):
                strength += 1.0  # High value spell

            if card2_cmc <= 2:
                strength += 0.5  # Cheap and efficient

            if strength >= 1.5:  # Only report if meaningful synergy
                synergies.append({
                    'category': 'Cascade → Target',
                    'card1_role': 'Cascade Spell',
                    'card2_role': 'Cascade Target',
                    'description': f"{card1_name} can cascade into {card2_name}",
                    'strength': strength,
                    'combo_notes': f"CMC {card1_cmc} → CMC {card2_cmc}"
                })

    # Check reverse
    if cascade2['has_cascade']:
        if card1_cmc < card2_cmc and card1_cmc > 0:
            card1_text = card1.get('oracle_text', '').lower()
            value_keywords = ['destroy', 'exile', 'draw', 'damage', 'counter', 'tutor']

            strength = 1.0
            if any(kw in card1_text for kw in value_keywords):
                strength += 1.0

            if card1_cmc <= 2:
                strength += 0.5

            if strength >= 1.5:
                synergies.append({
                    'category': 'Cascade → Target',
                    'card1_role': 'Cascade Target',
                    'card2_role': 'Cascade Spell',
                    'description': f"{card2_name} can cascade into {card1_name}",
                    'strength': strength,
                    'combo_notes': f"CMC {card2_cmc} → CMC {card1_cmc}"
                })

    return synergies


def detect_treasure_artifact_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between treasure/clue tokens and artifact matters cards.

    Examples:
    - Dockside Extortionist + Reckless Fireweaver
    - Smothering Tithe + Sai, Master Thopterist
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    tokens1 = card1_recursion['treasure_tokens']
    tokens2 = card2_recursion['treasure_tokens']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Artifact matters patterns
    artifact_matters_patterns = [
        'whenever.*artifact.*enters',
        'whenever you.*artifact',
        'artifacts you control',
        'sacrifice an artifact',
        'number of artifacts'
    ]

    card2_cares_artifacts = any(re.search(pattern, card2_text) for pattern in artifact_matters_patterns)
    card1_cares_artifacts = any(re.search(pattern, card1_text) for pattern in artifact_matters_patterns)

    if tokens1['generates_tokens'] and card2_cares_artifacts:
        strength = 2.0

        # Treasure tokens are artifacts
        if 'treasure' in tokens1['token_types']:
            strength += 0.5  # Treasure provides mana too

        # Repeatable is better
        if tokens1['generation_type'] == 'repeatable':
            strength += 1.0

        synergies.append({
            'category': 'Token Generation → Artifact Matters',
            'card1_role': 'Token Generator',
            'card2_role': 'Artifact Payoff',
            'description': f"{card1_name} creates {'/'.join(tokens1['token_types'])} tokens for {card2_name}",
            'strength': strength,
            'combo_notes': f"Token type: {', '.join(tokens1['token_types'])}"
        })

    if tokens2['generates_tokens'] and card1_cares_artifacts:
        strength = 2.0

        if 'treasure' in tokens2['token_types']:
            strength += 0.5

        if tokens2['generation_type'] == 'repeatable':
            strength += 1.0

        synergies.append({
            'category': 'Token Generation → Artifact Matters',
            'card1_role': 'Artifact Payoff',
            'card2_role': 'Token Generator',
            'description': f"{card2_name} creates {'/'.join(tokens2['token_types'])} tokens for {card1_name}",
            'strength': strength,
            'combo_notes': f"Token type: {', '.join(tokens2['token_types'])}"
        })

    return synergies


def detect_clue_sacrifice_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between clue tokens and sacrifice payoffs.

    Examples:
    - Tamiyo's Journal + Krark-Clan Ironworks
    - Ulvenwald Mysteries + Ashnod's Altar
    """
    synergies = []

    card1_name = card1.get('name', 'Unknown')
    card2_name = card2.get('name', 'Unknown')

    card1_recursion = classify_recursion_mechanics(card1)
    card2_recursion = classify_recursion_mechanics(card2)

    tokens1 = card1_recursion['treasure_tokens']
    tokens2 = card2_recursion['treasure_tokens']

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Sacrifice payoff patterns
    sac_patterns = [
        'sacrifice.*artifact',
        'whenever.*artifact.*sacrificed',
        'sacrifice an artifact'
    ]

    card2_sac_payoff = any(re.search(pattern, card2_text) for pattern in sac_patterns)
    card1_sac_payoff = any(re.search(pattern, card1_text) for pattern in sac_patterns)

    if tokens1['generates_tokens'] and 'clue' in tokens1['token_types'] and card2_sac_payoff:
        strength = 2.0
        if tokens1['generation_type'] == 'repeatable':
            strength += 1.0

        synergies.append({
            'category': 'Clue Tokens → Sacrifice',
            'card1_role': 'Clue Generator',
            'card2_role': 'Sacrifice Payoff',
            'description': f"{card1_name} creates clues to sacrifice for {card2_name}",
            'strength': strength,
            'combo_notes': "Clues provide card draw and sacrifice fodder"
        })

    if tokens2['generates_tokens'] and 'clue' in tokens2['token_types'] and card1_sac_payoff:
        strength = 2.0
        if tokens2['generation_type'] == 'repeatable':
            strength += 1.0

        synergies.append({
            'category': 'Clue Tokens → Sacrifice',
            'card1_role': 'Sacrifice Payoff',
            'card2_role': 'Clue Generator',
            'description': f"{card2_name} creates clues to sacrifice for {card1_name}",
            'strength': strength,
            'combo_notes': "Clues provide card draw and sacrifice fodder"
        })

    return synergies


# List of all recursion synergy detection functions
RECURSION_SYNERGY_RULES = [
    detect_reanimation_big_creatures,
    detect_flashback_discard_synergies,
    detect_extra_turns_wincons,
    detect_cascade_cheap_spells,
    detect_treasure_artifact_synergies,
    detect_clue_sacrifice_synergies
]
