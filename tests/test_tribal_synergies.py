"""
Tests for tribal synergy detection
"""

import pytest
from src.synergy_engine.rules import (
    detect_tribal_synergy,
    detect_tribal_chosen_type_synergy,
    detect_tribal_same_type_synergy,
    detect_tribal_trigger_synergy
)
from src.utils.tribal_extractors import (
    extract_cares_about_chosen_type,
    extract_cares_about_same_type,
    extract_tribal_lords,
    extract_tribal_triggers,
    extract_is_changeling,
    get_creature_types
)


class TestTribalExtractors:
    """Test tribal extraction functions"""

    def test_extract_cares_about_chosen_type(self):
        """Test detection of 'choose a creature type' effects"""
        # Door of Destinies
        card = {
            'name': 'Door of Destinies',
            'oracle_text': 'As Door of Destinies enters the battlefield, choose a creature type. Whenever you cast a spell of the chosen type, put a charge counter on Door of Destinies.'
        }
        result = extract_cares_about_chosen_type(card)
        assert result['cares_about_chosen_type'] == True
        assert 'choice' in result['patterns_matched']

    def test_extract_cares_about_same_type(self):
        """Test detection of 'same type' effects"""
        # Adaptive Automaton
        card = {
            'name': 'Adaptive Automaton',
            'oracle_text': 'As Adaptive Automaton enters the battlefield, choose a creature type. Adaptive Automaton is the chosen type in addition to its other types. Other creatures you control of the chosen type get +1/+1.'
        }
        result = extract_cares_about_same_type(card)
        # Should also detect chosen type
        assert result['cares_about_same_type'] == False  # This specific card uses "chosen type" not "same type"

        # Metallic Mimic
        card2 = {
            'name': 'Metallic Mimic',
            'oracle_text': 'As Metallic Mimic enters the battlefield, choose a creature type. Metallic Mimic is the chosen type in addition to its other types. Each other creature you control of the chosen type enters the battlefield with an additional +1/+1 counter on it.'
        }
        result2 = extract_cares_about_same_type(card2)
        assert result2['cares_about_same_type'] == False  # Also uses "chosen type"

        # Card that actually uses "share a type"
        card3 = {
            'name': 'Test Card',
            'oracle_text': 'Creatures that share a creature type with this creature get +1/+1.'
        }
        result3 = extract_cares_about_same_type(card3)
        assert result3['cares_about_same_type'] == True
        assert 'shared_type' in result3['patterns_matched']

    def test_extract_tribal_lords(self):
        """Test detection of tribal lord effects"""
        # Goblin King
        card = {
            'name': 'Goblin King',
            'oracle_text': 'Other Goblins you control get +1/+1 and have mountainwalk.',
            'type_line': 'Creature — Goblin'
        }
        result = extract_tribal_lords(card)
        assert result['is_tribal_lord'] == True
        assert 'Goblin' in result['creature_types']
        assert result['buff_type'] in ['anthem', 'keyword_grant']

    def test_extract_tribal_triggers(self):
        """Test detection of tribal triggered abilities"""
        # Whenever you cast an Elf spell
        card = {
            'name': 'Elvish Warmaster',
            'oracle_text': 'Whenever you cast an Elf spell or put an Elf token onto the battlefield, create a 1/1 green Elf Warrior creature token.',
            'type_line': 'Creature — Elf Warrior'
        }
        result = extract_tribal_triggers(card)
        assert result['has_tribal_trigger'] == True
        assert result['trigger_type'] == 'cast'
        assert 'Elf' in result['creature_types']

    def test_extract_is_changeling(self):
        """Test detection of Changeling creatures"""
        card = {
            'name': 'Changeling Titan',
            'oracle_text': 'Changeling (This card is every creature type.)',
            'type_line': 'Creature — Shapeshifter'
        }
        result = extract_is_changeling(card)
        assert result == True

    def test_get_creature_types(self):
        """Test extraction of creature types from type line"""
        card = {
            'name': 'Llanowar Elves',
            'type_line': 'Creature — Elf Druid'
        }
        types = get_creature_types(card)
        assert 'Elf' in types
        assert 'Druid' in types


class TestTribalSynergies:
    """Test tribal synergy detection"""

    def test_detect_tribal_chosen_type_synergy(self):
        """Test synergy between 'chosen type' cards and creatures"""
        # Door of Destinies + any creature
        card1 = {
            'name': 'Door of Destinies',
            'oracle_text': 'As Door of Destinies enters the battlefield, choose a creature type. Whenever you cast a spell of the chosen type, put a charge counter on Door of Destinies.',
            'type_line': 'Artifact'
        }
        card2 = {
            'name': 'Llanowar Elves',
            'oracle_text': '{T}: Add {G}.',
            'type_line': 'Creature — Elf Druid'
        }

        synergy = detect_tribal_chosen_type_synergy(card1, card2)
        assert synergy is not None
        assert synergy['name'] == 'Chosen Type Synergy'
        assert 'choose' in synergy['description'].lower()

    def test_detect_tribal_same_type_synergy(self):
        """Test synergy between 'same type' cards and creatures"""
        card1 = {
            'name': 'Test Lord',
            'oracle_text': 'Creatures that share a creature type with this creature get +1/+1.',
            'type_line': 'Creature — Elf Warrior'
        }
        card2 = {
            'name': 'Llanowar Elves',
            'oracle_text': '{T}: Add {G}.',
            'type_line': 'Creature — Elf Druid'
        }

        synergy = detect_tribal_same_type_synergy(card1, card2)
        assert synergy is not None
        assert synergy['name'] == 'Same Type Synergy'

    def test_detect_changeling_synergy(self):
        """Test synergy between Changelings and tribal cards"""
        changeling = {
            'name': 'Changeling Titan',
            'oracle_text': 'Changeling (This card is every creature type.)',
            'type_line': 'Creature — Shapeshifter'
        }
        tribal_lord = {
            'name': 'Goblin King',
            'oracle_text': 'Other Goblins you control get +1/+1 and have mountainwalk.',
            'type_line': 'Creature — Goblin'
        }

        synergy = detect_tribal_same_type_synergy(changeling, tribal_lord)
        assert synergy is not None
        assert synergy['name'] == 'Changeling Synergy'
        assert 'Changeling' in synergy['description']

    def test_detect_tribal_trigger_synergy(self):
        """Test synergy between tribal triggers and creatures"""
        trigger_card = {
            'name': 'Elvish Warmaster',
            'oracle_text': 'Whenever you cast an Elf spell, create a 1/1 green Elf Warrior creature token.',
            'type_line': 'Creature — Elf Warrior'
        }
        elf_card = {
            'name': 'Llanowar Elves',
            'oracle_text': '{T}: Add {G}.',
            'type_line': 'Creature — Elf Druid',
            'card_types': {'subtypes': ['Elf', 'Druid']}
        }

        synergy = detect_tribal_trigger_synergy(trigger_card, elf_card)
        assert synergy is not None
        assert synergy['name'] == 'Tribal Trigger Synergy'
        assert 'trigger' in synergy['description'].lower()

    def test_existing_tribal_synergy_still_works(self):
        """Ensure existing tribal synergy detection still works"""
        lord = {
            'name': 'Goblin King',
            'oracle_text': 'Other Goblins you control get +1/+1 and have mountainwalk.',
            'type_line': 'Creature — Goblin',
            'card_types': {'subtypes': ['Goblin']}
        }
        goblin = {
            'name': 'Goblin Guide',
            'oracle_text': 'Haste',
            'type_line': 'Creature — Goblin Warrior',
            'card_types': {'subtypes': ['Goblin', 'Warrior']}
        }

        synergy = detect_tribal_synergy(lord, goblin)
        assert synergy is not None
        assert 'Tribal Synergy' in synergy['name'] or 'Shared Tribe' in synergy['name']


class TestTribalSimulation:
    """Test tribal mechanics in simulation"""

    def test_creature_type_extraction(self):
        """Test that we can extract creature types correctly"""
        from Simulation.boardstate import BoardState

        # Create a simple deck
        deck = []
        commander = {'name': 'Test Commander', 'type_line': 'Creature — Elf Warrior'}

        board = BoardState(deck, commander)

        # Test creature type extraction
        elf = {'name': 'Llanowar Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''}
        types = board._get_creature_types(elf)

        assert 'Elf' in types
        assert 'Druid' in types

    def test_changeling_detection(self):
        """Test that changelings are detected correctly"""
        from Simulation.boardstate import BoardState

        deck = []
        commander = {'name': 'Test Commander', 'type_line': 'Creature — Human Warrior'}

        board = BoardState(deck, commander)

        changeling = {
            'name': 'Changeling Titan',
            'type_line': 'Creature — Shapeshifter',
            'oracle_text': 'Changeling (This card is every creature type.)'
        }

        types = board._get_creature_types(changeling)
        assert 'Changeling' in types

    def test_choose_creature_type(self):
        """Test that the simulation can choose a creature type"""
        from Simulation.boardstate import BoardState

        # Create a deck with multiple Elves
        deck = [
            {'name': 'Llanowar Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
            {'name': 'Elvish Mystic', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
            {'name': 'Fyndhorn Elves', 'type_line': 'Creature — Elf Druid', 'oracle_text': ''},
            {'name': 'Goblin Guide', 'type_line': 'Creature — Goblin Warrior', 'oracle_text': ''},
        ]
        commander = {'name': 'Test Commander', 'type_line': 'Creature — Elf Warrior'}

        board = BoardState(deck, commander)

        # Choose a type for Door of Destinies
        chosen = board.choose_creature_type('Door of Destinies', verbose=False)

        # Should choose Elf since there are more Elves in the deck
        assert chosen == 'Elf' or chosen in ['Elf', 'Druid', 'Warrior']
        assert 'Door of Destinies' in board.chosen_creature_types


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
