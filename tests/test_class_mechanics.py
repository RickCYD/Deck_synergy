"""
Tests for Class enchantment mechanics

Tests both synergy detection and simulation functionality for Class enchantments.
"""

import pytest
from src.utils.class_extractors import (
    extract_class_levels,
    extract_cost_reduction_from_class,
    extract_damage_boost_from_class,
    extract_modal_triggers_from_class
)


def test_extract_class_levels_artist_talent():
    """Test extraction of levels from Artist's Talent."""
    card = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """(Gain the next level as a sorcery to add its ability.)
Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    result = extract_class_levels(card)

    assert result['is_class'] is True
    assert result['max_level'] == 3
    assert len(result['levels']) == 3

    # Check that abilities are detected
    assert result['has_triggers'] is True
    assert result['has_cost_reduction'] is True
    assert result['has_damage_boost'] is True
    assert result['has_modal_trigger'] is True


def test_extract_cost_reduction():
    """Test extraction of cost reduction from Class."""
    card = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """(Gain the next level as a sorcery to add its ability.)
Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    result = extract_cost_reduction_from_class(card)

    assert result['has_cost_reduction'] is True
    assert result['reduction_amount'] == 1
    assert 'noncreature' in result['spell_types']
    assert result['at_level'] == 2


def test_extract_damage_boost():
    """Test extraction of damage amplification from Class."""
    card = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """(Gain the next level as a sorcery to add its ability.)
Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    result = extract_damage_boost_from_class(card)

    assert result['has_damage_boost'] is True
    assert result['boost_amount'] == 2
    assert 'noncombat' in result['damage_types']
    assert result['source_restriction'] == 'sources_you_control'
    assert result['at_level'] == 3


def test_extract_modal_triggers():
    """Test extraction of modal triggers from Class."""
    card = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """(Gain the next level as a sorcery to add its ability.)
Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    result = extract_modal_triggers_from_class(card)

    assert result['has_modal_trigger'] is True
    assert result['trigger_event'] == 'cast_noncreature'
    assert result['modal_type'] == 'optional'
    assert 'discard_to_draw' in result['effects']
    assert result['at_level'] == 1


def test_non_class_enchantment():
    """Test that non-Class enchantments return False."""
    card = {
        'name': "Rhystic Study",
        'type_line': "Enchantment",
        'oracle_text': "Whenever an opponent casts a spell, you may draw a card unless that player pays {1}."
    }

    result = extract_class_levels(card)

    assert result['is_class'] is False
    assert result['max_level'] == 1
    assert len(result['levels']) == 0


def test_class_synergy_detection():
    """Test that Class synergies are detected correctly."""
    from src.synergy_engine.rules import detect_class_enchantment_synergies

    artist_talent = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    lightning_bolt = {
        'name': 'Lightning Bolt',
        'type_line': 'Instant',
        'oracle_text': 'Lightning Bolt deals 3 damage to any target.'
    }

    synergies = detect_class_enchantment_synergies(artist_talent, lightning_bolt)

    # Should detect cost reduction synergy
    cost_reduction_synergies = [s for s in synergies if 'Cost Reduction' in s['name']]
    assert len(cost_reduction_synergies) > 0

    # Should detect trigger synergy
    trigger_synergies = [s for s in synergies if 'Trigger' in s['name']]
    assert len(trigger_synergies) > 0


def test_class_damage_amplification_synergy():
    """Test damage amplification synergy detection."""
    from src.synergy_engine.rules import detect_class_enchantment_synergies

    artist_talent = {
        'name': "Artist's Talent",
        'type_line': "Enchantment — Class",
        'oracle_text': """Whenever you cast a noncreature spell, you may discard a card. If you do, draw a card.
{1}{R}: Level 2
Noncreature spells you cast cost {1} less to cast.
{3}{R}: Level 3
If a source you control would deal noncombat damage to an opponent or a permanent an opponent controls, it deals that much damage plus 2 instead."""
    }

    guttersnipe = {
        'name': 'Guttersnipe',
        'type_line': 'Creature — Goblin Shaman',
        'oracle_text': 'Whenever you cast an instant or sorcery spell, Guttersnipe deals 2 damage to each opponent.'
    }

    synergies = detect_class_enchantment_synergies(artist_talent, guttersnipe)

    # Should detect damage boost synergy
    damage_synergies = [s for s in synergies if 'Damage Boost' in s['name']]
    assert len(damage_synergies) > 0
    assert any(s['value'] >= 5.0 for s in damage_synergies)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
