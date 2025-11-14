"""
Synergy-Simulation Bridge

This module connects synergy detection with game simulation, ensuring that:
1. Synergy detection uses the unified parser (single source of truth)
2. Detected synergies influence simulation decisions
3. Triggers are automatically registered based on deck analysis
4. The complete pipeline works: parse → synergy → simulation

Key responsibilities:
- Adapt existing synergy rules to use unified parser
- Pre-analyze decks for synergies before simulation
- Convert synergy data to simulation-ready format
- Provide synergy-aware card priorities for AI decisions

Usage:
    from src.core.synergy_simulation_bridge import SynergyBridge

    bridge = SynergyBridge()
    synergies = bridge.analyze_deck_synergies(deck_cards)
    card_priorities = bridge.get_card_play_priorities(deck_cards, synergies)
"""

from typing import List, Dict, Any, Tuple, Set
import logging

from src.core.card_parser import UnifiedCardParser, CardAbilities

logger = logging.getLogger(__name__)


class SynergyBridge:
    """
    Bridge between synergy detection and game simulation.

    This class ensures synergies detected during deck analysis
    are used to improve simulation gameplay.
    """

    def __init__(self):
        """Initialize the synergy bridge with unified parser."""
        self.parser = UnifiedCardParser()
        self.synergy_cache = {}  # Cache parsed abilities
        logger.debug("SynergyBridge initialized")

    def parse_deck_abilities(self, deck_cards: List[Dict[str, Any]]) -> Dict[str, CardAbilities]:
        """
        Parse all cards in a deck using the unified parser.

        Args:
            deck_cards: List of raw card data dicts

        Returns:
            Dict mapping card name to CardAbilities
        """
        abilities_map = {}

        for card in deck_cards:
            card_name = card.get('name', 'Unknown')

            # Check cache first
            if card_name in self.synergy_cache:
                abilities_map[card_name] = self.synergy_cache[card_name]
                continue

            # Parse and cache
            abilities = self.parser.parse_card(card)
            self.synergy_cache[card_name] = abilities
            abilities_map[card_name] = abilities

        logger.info(f"Parsed {len(abilities_map)} unique cards from deck")
        return abilities_map

    def detect_deck_synergies(self, deck_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect all synergies in a deck using unified parser data.

        Args:
            deck_cards: List of raw card data dicts

        Returns:
            Dict with synergy statistics and card relationships
        """
        abilities_map = self.parse_deck_abilities(deck_cards)

        synergies = {
            'rally_synergies': [],
            'prowess_synergies': [],
            'spellslinger_synergies': [],
            'token_synergies': [],
            'total_synergies': 0,
            'synergy_score': 0.0,
        }

        # Detect Rally synergies (Ally + Token creation)
        rally_cards = [name for name, abilities in abilities_map.items() if abilities.has_rally]
        token_creators = [name for name, abilities in abilities_map.items() if abilities.creates_tokens]

        for rally_card in rally_cards:
            for token_card in token_creators:
                # Check if token creator creates Allies
                token_abilities = abilities_map[token_card]
                rally_abilities = abilities_map[rally_card]

                # Get rally triggers
                rally_triggers = rally_abilities.get_triggers('rally')

                for rally_trigger in rally_triggers:
                    synergies['rally_synergies'].append({
                        'card1': rally_card,
                        'card2': token_card,
                        'type': 'rally_token',
                        'value': 5.0,  # High synergy value
                        'description': f"{rally_card} rally triggers when {token_card} creates tokens"
                    })
                    synergies['total_synergies'] += 1

        # Detect Prowess synergies (Prowess + Cheap spells)
        prowess_cards = [name for name, abilities in abilities_map.items() if abilities.has_prowess]
        cheap_spells = []

        # Check CMC from card data and type
        for card in deck_cards:
            cmc = card.get('cmc', 99)
            type_line = card.get('type_line', '')
            card_name = card.get('name')

            # Non-creature spells with CMC <= 2
            if cmc <= 2 and 'Creature' not in type_line and card_name not in cheap_spells:
                cheap_spells.append(card_name)

        for prowess_card in prowess_cards:
            for spell in cheap_spells:
                if spell != prowess_card:
                    synergies['prowess_synergies'].append({
                        'card1': prowess_card,
                        'card2': spell,
                        'type': 'prowess_cheap_spell',
                        'value': 4.0,
                        'description': f"{prowess_card} gets +1/+1 when casting {spell}"
                    })
                    synergies['total_synergies'] += 1

        # Detect Spellslinger synergies (Spellslinger payoffs + Instants/Sorceries)
        spellslinger_payoffs = [
            name for name, abilities in abilities_map.items()
            if abilities.has_magecraft or any(
                'cast' in t.event and 'spell' in t.event
                for t in abilities.triggers
            )
        ]

        # Get instants/sorceries from card data
        instants_sorceries = []
        for card in deck_cards:
            type_line = card.get('type_line', '')
            card_name = card.get('name')
            if ('Instant' in type_line or 'Sorcery' in type_line) and card_name not in instants_sorceries:
                instants_sorceries.append(card_name)

        for payoff in spellslinger_payoffs:
            for spell in instants_sorceries:
                if spell != payoff:
                    synergies['spellslinger_synergies'].append({
                        'card1': payoff,
                        'card2': spell,
                        'type': 'spellslinger',
                        'value': 3.0,
                        'description': f"{payoff} triggers when casting {spell}"
                    })
                    synergies['total_synergies'] += 1

        # Detect Token synergies (Multiple token creators)
        if len(token_creators) >= 2:
            for i, card1 in enumerate(token_creators):
                for card2 in token_creators[i+1:]:
                    synergies['token_synergies'].append({
                        'card1': card1,
                        'card2': card2,
                        'type': 'token_multiplication',
                        'value': 3.0,
                        'description': f"{card1} and {card2} create tokens"
                    })
                    synergies['total_synergies'] += 1

        # Calculate overall synergy score
        if deck_cards:
            # Score based on synergies per card
            synergies_per_card = synergies['total_synergies'] / len(deck_cards)
            synergies['synergy_score'] = min(100.0, synergies_per_card * 10)

        logger.info(f"Detected {synergies['total_synergies']} synergies, score: {synergies['synergy_score']:.1f}")
        return synergies

    def get_card_play_priorities(self, deck_cards: List[Dict[str, Any]],
                                  synergies: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate play priority for each card based on synergies.

        Cards with more synergies should be played with higher priority.

        Args:
            deck_cards: List of raw card data dicts
            synergies: Optional pre-calculated synergies

        Returns:
            Dict mapping card name to priority score (0-100)
        """
        if synergies is None:
            synergies = self.detect_deck_synergies(deck_cards)

        priorities = {}

        # Count synergies per card
        synergy_counts = {}
        for synergy_type in ['rally_synergies', 'prowess_synergies', 'spellslinger_synergies', 'token_synergies']:
            for synergy in synergies.get(synergy_type, []):
                card1 = synergy['card1']
                card2 = synergy['card2']
                value = synergy['value']

                synergy_counts[card1] = synergy_counts.get(card1, 0) + value
                synergy_counts[card2] = synergy_counts.get(card2, 0) + value

        # Convert to priorities (0-100 scale)
        if synergy_counts:
            max_count = max(synergy_counts.values())
            for card, count in synergy_counts.items():
                priorities[card] = (count / max_count) * 100 if max_count > 0 else 50

        # Cards without synergies get base priority
        for card in deck_cards:
            card_name = card.get('name')
            if card_name not in priorities:
                priorities[card_name] = 50.0  # Neutral priority

        logger.debug(f"Calculated priorities for {len(priorities)} cards")
        return priorities

    def create_trigger_aware_deck(self, deck_cards: List[Dict[str, Any]]) -> Tuple[List[Dict], Dict]:
        """
        Prepare a deck for simulation with trigger awareness.

        This analyzes the deck and returns both the cards and metadata
        about triggers and synergies.

        Args:
            deck_cards: List of raw card data dicts

        Returns:
            Tuple of (deck_cards, metadata_dict)
        """
        # Parse all abilities
        abilities_map = self.parse_deck_abilities(deck_cards)

        # Detect synergies
        synergies = self.detect_deck_synergies(deck_cards)

        # Get priorities
        priorities = self.get_card_play_priorities(deck_cards, synergies)

        # Collect trigger statistics
        trigger_stats = {
            'rally_count': 0,
            'prowess_count': 0,
            'magecraft_count': 0,
            'etb_count': 0,
            'death_count': 0,
            'attack_count': 0,
        }

        for abilities in abilities_map.values():
            if abilities.has_rally:
                trigger_stats['rally_count'] += 1
            if abilities.has_prowess:
                trigger_stats['prowess_count'] += 1
            if abilities.has_magecraft:
                trigger_stats['magecraft_count'] += 1
            if abilities.has_etb:
                trigger_stats['etb_count'] += 1

            for trigger in abilities.triggers:
                if trigger.event == 'death':
                    trigger_stats['death_count'] += 1
                elif trigger.event == 'attack':
                    trigger_stats['attack_count'] += 1

        metadata = {
            'abilities_map': abilities_map,
            'synergies': synergies,
            'priorities': priorities,
            'trigger_stats': trigger_stats,
        }

        logger.info(f"Created trigger-aware deck: {synergies['total_synergies']} synergies, "
                   f"{sum(trigger_stats.values())} triggers")

        return deck_cards, metadata

    def get_synergy_value_between_cards(self, card1_name: str, card2_name: str,
                                        abilities_map: Dict[str, CardAbilities] = None) -> float:
        """
        Calculate synergy value between two specific cards.

        Args:
            card1_name: Name of first card
            card2_name: Name of second card
            abilities_map: Optional pre-parsed abilities

        Returns:
            Synergy value (0-10 scale)
        """
        if abilities_map is None:
            return 0.0

        if card1_name not in abilities_map or card2_name not in abilities_map:
            return 0.0

        abilities1 = abilities_map[card1_name]
        abilities2 = abilities_map[card2_name]

        synergy_value = 0.0

        # Helper: check if card is a creature (has creature types)
        is_creature1 = len(abilities1.creature_types) > 0
        is_creature2 = len(abilities2.creature_types) > 0

        # Rally + Token creation
        if abilities1.has_rally and abilities2.creates_tokens:
            synergy_value += 6.0

        if abilities2.has_rally and abilities1.creates_tokens:
            synergy_value += 6.0

        # Prowess + Cheap spell
        if abilities1.has_prowess and not is_creature2:
            synergy_value += 4.0

        if abilities2.has_prowess and not is_creature1:
            synergy_value += 4.0

        # Spellslinger + Instant/Sorcery
        has_spellslinger1 = abilities1.has_magecraft or any(
            'cast' in t.event and 'spell' in t.event for t in abilities1.triggers
        )
        has_spellslinger2 = abilities2.has_magecraft or any(
            'cast' in t.event and 'spell' in t.event for t in abilities2.triggers
        )

        if has_spellslinger1 and not is_creature2:
            synergy_value += 3.0

        if has_spellslinger2 and not is_creature1:
            synergy_value += 3.0

        # Token creation synergy (both create tokens)
        if abilities1.creates_tokens and abilities2.creates_tokens:
            synergy_value += 2.0

        return synergy_value

    def enhance_simulation_with_synergies(self, board_state, deck_metadata: Dict):
        """
        Enhance a BoardState with synergy awareness.

        This adds synergy information to the board state so simulation
        AI can make better decisions.

        Args:
            board_state: BoardState instance
            deck_metadata: Metadata from create_trigger_aware_deck()
        """
        # Add synergy data to board state
        board_state.synergy_priorities = deck_metadata.get('priorities', {})
        board_state.synergy_metadata = deck_metadata
        board_state.abilities_map = deck_metadata.get('abilities_map', {})

        logger.info("Enhanced BoardState with synergy awareness")

    def get_optimal_card_order(self, hand_cards: List[Dict[str, Any]],
                               board_state, deck_metadata: Dict) -> List[Dict[str, Any]]:
        """
        Determine optimal card play order based on synergies.

        Args:
            hand_cards: Cards currently in hand
            board_state: Current BoardState
            deck_metadata: Deck metadata with synergies

        Returns:
            Sorted list of cards (highest priority first)
        """
        priorities = deck_metadata.get('priorities', {})
        abilities_map = deck_metadata.get('abilities_map', {})

        # Calculate adjusted priorities based on board state
        adjusted_priorities = []

        for card in hand_cards:
            card_name = card.get('name')
            base_priority = priorities.get(card_name, 50.0)

            # Adjust based on current board
            board_bonus = 0.0

            if abilities_map and card_name in abilities_map:
                card_abilities = abilities_map[card_name]
                is_creature = len(card_abilities.creature_types) > 0

                # Bonus if we have creatures and this creates tokens (rally synergy)
                if card_abilities.creates_tokens and hasattr(board_state, 'creatures'):
                    if any('Ally' in getattr(c, 'type', '') for c in board_state.creatures):
                        board_bonus += 20.0  # Big bonus if we have rally cards out

                # Bonus if we have prowess creatures and this is a spell
                if not is_creature and hasattr(board_state, 'creatures'):
                    prowess_creatures = [
                        c for c in board_state.creatures
                        if 'prowess' in getattr(c, 'oracle_text', '').lower()
                    ]
                    if prowess_creatures:
                        board_bonus += 15.0 * len(prowess_creatures)

            final_priority = base_priority + board_bonus
            adjusted_priorities.append((card, final_priority))

        # Sort by priority (highest first)
        adjusted_priorities.sort(key=lambda x: x[1], reverse=True)

        return [card for card, _ in adjusted_priorities]


# =============================================================================
# HELPER FUNCTIONS FOR EXISTING CODE INTEGRATION
# =============================================================================

def analyze_deck_with_bridge(deck_cards: List[Dict[str, Any]]) -> Tuple[Dict, Dict]:
    """
    Analyze a deck using the synergy bridge.

    This is a convenience function for existing code that wants to
    use the unified architecture.

    Args:
        deck_cards: List of raw card data dicts

    Returns:
        Tuple of (synergies_dict, abilities_map)
    """
    bridge = SynergyBridge()
    deck_cards, metadata = bridge.create_trigger_aware_deck(deck_cards)

    return metadata['synergies'], metadata['abilities_map']


def create_simulation_ready_deck(deck_cards: List[Dict[str, Any]]) -> Tuple[List[Dict], Dict]:
    """
    Prepare a deck for simulation with full unified architecture support.

    This is the main entry point for integrating unified architecture
    with existing simulation code.

    Args:
        deck_cards: List of raw card data dicts

    Returns:
        Tuple of (deck_cards, metadata_dict)
    """
    bridge = SynergyBridge()
    return bridge.create_trigger_aware_deck(deck_cards)
