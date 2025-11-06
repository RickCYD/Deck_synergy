"""
Synergy Categories Definition
Defines the different categories of card synergies
"""

from typing import Dict


# Synergy category definitions with weights
# Updated weights for 100 synergy rules system
SYNERGY_CATEGORIES = {
    'triggers': {
        'name': 'Triggers & Activated Abilities',
        'description': 'One card triggers or activates when the other does something',
        'weight': 1.2,  # Increased for better detection of triggered abilities
        'subcategories': {
            'etb_trigger': 'Enters-the-battlefield synergies',
            'etb': 'ETB synergies',
            'death_trigger': 'Death/sacrifice synergies',
            'combat_trigger': 'Combat-related triggers',
            'spell_trigger': 'Spell-casting triggers',
            'ability_activated': 'Activated ability synergies',
            'activated_ability': 'Activated ability synergies',
            'landfall': 'Landfall synergies'
        }
    },

    'mana_synergy': {
        'name': 'Mana & Color Synergy',
        'description': 'Cards that share colors or mana production/reduction',
        'weight': 0.6,  # Slightly increased for mana synergies
        'subcategories': {
            'color_match': 'Shared color identity',
            'mana_production': 'Mana production and use',
            'cost_reduction': 'Cost reduction effects',
            'color_matters': 'Color-specific effects'
        }
    },

    'role_interaction': {
        'name': 'Role & Function Interaction',
        'description': 'Cards that work well together based on their deck roles',
        'weight': 1.0,  # Increased for role synergies
        'subcategories': {
            'protection': 'Protection and hexproof synergies',
            'card_advantage': 'Card draw and tutoring',
            'ramp': 'Mana ramp synergies',
            'removal': 'Removal and board wipe synergies',
            'recursion': 'Graveyard recursion',
            'sacrifice': 'Sacrifice outlet and fodder',
            'token_generation': 'Token generation and payoffs',
            'tokens': 'Token synergies',
            'spell_copy': 'Spell copying synergies',
            'stax': 'Stax and tax effect synergies',
            'flash': 'Flash enabler synergies',
            'haste': 'Haste enabler synergies',
            'vigilance': 'Vigilance synergies',
            'tribal': 'Tribal synergies',
            'planeswalker': 'Planeswalker synergies',
            'enchantments': 'Enchantment synergies',
            'artifacts': 'Artifact synergies',
            'companion': 'Companion synergies'
        }
    },

    'combo': {
        'name': 'Combo & Infinite Interactions',
        'description': 'Cards that form combos or infinite loops',
        'weight': 2.5,  # Increased for powerful combo detection
        'subcategories': {
            'infinite_mana': 'Infinite mana combinations',
            'infinite_etb': 'Infinite ETB/LTB triggers',
            'infinite_damage': 'Infinite damage combinations',
            'infinite_mill': 'Infinite mill combinations',
            'two_card_combo': 'Two-card combos',
            'three_card_combo': 'Three-card combos',
            'counter_synergy': 'Counter doubling and synergies',
            'counters': 'Counter synergies',
            'copy_effects': 'Copy and clone effects',
            'storm': 'Storm and spell velocity',
            'energy': 'Energy generation and consumption',
            'stax': 'Stax packages',
            'sacrifice': 'Sacrifice engine combos',
            'etb': 'ETB combo synergies',
            'graveyard': 'Graveyard combo strategies',
            'infect': 'Infect/poison synergies',
            'lifegain': 'Lifegain synergies',
            'combat': 'Combat trick combos',
            'voltron': 'Voltron strategy synergies',
            'landfall': 'Landfall combos',
            'artifacts': 'Artifact combo synergies',
            'enchantments': 'Enchantment combo synergies',
            'mutate': 'Mutate synergies',
            'cascade': 'Cascade/discover synergies',
            'exile': 'Exile matters synergies',
            'discard': 'Discard synergies',
            'planeswalker': 'Planeswalker combo synergies'
        }
    },

    'benefits': {
        'name': 'Benefit & Enhancement',
        'description': 'One card benefits from or enhances the other',
        'weight': 0.85,  # Increased slightly for enhancement effects
        'subcategories': {
            'anthem_effect': 'Anthem/buff effects',
            'synergy_type': 'Type-based benefits (e.g., all artifacts)',
            'keyword_grant': 'Keyword ability granting',
            'cost_matters': 'CMC-based synergies',
            'tribal': 'Tribal synergies',
            'counter_synergy': '+1/+1 counter placement and payoffs',
            'combat': 'Combat enhancement'
        }
    },

    'type_synergy': {
        'name': 'Type Synergy',
        'description': 'Cards that care about specific card types',
        'weight': 0.75,  # Increased for type-based synergies
        'subcategories': {
            'creature_matters': 'Creature synergies',
            'artifact_matters': 'Artifact synergies',
            'artifacts': 'Artifact synergies',
            'enchantment_matters': 'Enchantment synergies',
            'enchantments': 'Enchantment synergies',
            'instant_sorcery_matters': 'Instant/sorcery synergies',
            'land_matters': 'Land synergies',
            'planeswalker_synergy': 'Planeswalker synergies',
            'planeswalker': 'Planeswalker synergies',
            'equipment_matters': 'Equipment synergies',
            'equipment': 'Equipment synergies',
            'tribal': 'Tribal type synergies'
        }
    },

    'card_advantage': {
        'name': 'Card Advantage Engine',
        'description': 'Cards that combine to generate card advantage',
        'weight': 1.1,  # Increased for card advantage importance
        'subcategories': {
            'draw_engine': 'Card draw engines',
            'tutor_target': 'Tutor and target synergies',
            'recursion_loop': 'Recursion loops',
            'scry_synergy': 'Scry synergies',
            'surveil_synergy': 'Surveil synergies',
            'top_deck_synergy': 'Top-deck synergies',
            'graveyard': 'Graveyard advantage'
        }
    }
}


def get_category_weight(category: str, subcategory: str = None) -> float:
    """
    Get the weight for a synergy category/subcategory

    Args:
        category: Main category name
        subcategory: Optional subcategory name

    Returns:
        Weight value (float)
    """
    if category not in SYNERGY_CATEGORIES:
        return 0.5  # Default weight

    base_weight = SYNERGY_CATEGORIES[category]['weight']

    # Could add subcategory-specific weights in the future
    return base_weight


def get_all_categories() -> Dict:
    """Get all synergy categories"""
    return SYNERGY_CATEGORIES


def get_category_info(category: str) -> Dict:
    """Get information about a specific category"""
    return SYNERGY_CATEGORIES.get(category, {})
