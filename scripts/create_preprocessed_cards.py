"""
Generate cards-preprocessed.json from cards-minimal.json

This script pre-extracts synergy-relevant features from every card to enable
fast recommendation searches across the entire database.

Pre-computed features include:
- Synergy tags (ETB, sacrifice outlet, token generator, etc.)
- Role classifications (Ramp, Draw, Removal, etc.)
- Tribal affiliations (creature types)
- Mechanical themes (counters, graveyard, etc.)

This allows searching 35k+ cards instantly instead of parsing text repeatedly.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


# ============================================================================
# SYNERGY TAG EXTRACTION
# ============================================================================

def extract_synergy_tags(card: Dict) -> List[str]:
    """
    Extract pre-computed synergy tags from card text

    Returns list of tags like:
    - 'has_etb', 'flicker', 'sacrifice_outlet', 'token_gen'
    - 'graveyard_recursion', 'card_draw', 'ramp'
    - 'tribal_elf', 'tribal_goblin', etc.
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()
    tags = []

    # ETB triggers
    if re.search(r'enters the battlefield|when .* enters|whenever .* enters', text):
        tags.append('has_etb')

    # Flicker/Blink
    if re.search(r'exile.*return.*to the battlefield|exile.*return.*under.*control|\bblink\b|\bflicker\b', text):
        # Exclude reanimation
        if not re.search(r'return.*from.*graveyard.*to the battlefield', text):
            tags.append('flicker')

    # Sacrifice outlet
    sacrifice_patterns = [
        r'sacrifice a creature', r'sacrifice a permanent',
        r'sacrifice an artifact', r'sacrifice an enchantment',
        r'sacrifice.*you control', r'as an additional cost.*sacrifice'
    ]
    exclude_sac = [r'opponent.*sacrifice', r'sacrifice this', r'sacrifice .* land.*search']
    if any(re.search(p, text) for p in sacrifice_patterns):
        if not any(re.search(p, text) for p in exclude_sac):
            tags.append('sacrifice_outlet')

    # Death triggers - ONLY payoffs, not self-death triggers
    death_trigger_patterns = [
        r'whenever (?:a|another|one or more) creature',  # "whenever a creature dies"
        r'whenever.*creatures.*die',                       # "whenever one or more creatures die"
        r'when (?:a|another) creature.*dies',             # "when a creature dies"
        r'whenever (?:a|another) .*permanent.*dies',      # "whenever a permanent dies"
    ]
    self_death_patterns = [
        r'when (this|~) .*dies',                          # "when this creature dies"
        r'when (this|~) .*is put into.*graveyard',       # "when this is put into a graveyard"
        r'whenever (this|~) dies',                        # "whenever this dies"
    ]
    has_death_trigger = any(re.search(p, text) for p in death_trigger_patterns)
    is_self_death = any(re.search(p, text) for p in self_death_patterns)
    if has_death_trigger and not is_self_death:
        tags.append('death_trigger')

    # Token generation
    if re.search(r'create.*token|put.*token', text):
        tags.append('token_gen')

    # Card draw
    if re.search(r'draw (?:a|one|\d+) card|whenever .* draw|you may draw', text):
        tags.append('card_draw')

    # Ramp (mana production)
    produced_mana = card.get('produced_mana', [])
    if produced_mana or re.search(r'add \{[wubrgc]\}|add.*mana|search your library.*land', text):
        tags.append('ramp')

    # Mill effects (putting cards from library into graveyard)
    mill_patterns = [
        r'\bmill\b',  # Mill keyword (word boundary to avoid "Millstone" false positives)
        r'put.*top.*cards?.*library.*into.*graveyard',
        r'put.*cards?.*from.*library.*into.*graveyard',
        r'reveals? cards.*library.*puts?.*into.*graveyard',
        r'reveal.*top.*cards?.*library.*(?:put|place).*(?:rest|them|those).*into.*graveyard',  # "reveal top 4, put the rest into graveyard"
        r'reveal.*top.*cards?.*library.*(?:put|place).*into.*graveyard',  # variant
    ]
    if any(re.search(p, text) for p in mill_patterns):
        tags.append('mill')

    # Self-mill (you mill yourself, not opponent)
    # Must actually put cards from library into graveyard, not just reference library
    self_mill_patterns = [
        r'you mill',                                      # "you mill X"
        r'mills? you',                                    # "mills you"
        r'put.*from your library.*into your graveyard',  # "put cards from your library into your graveyard"
        r'from your library.*into your graveyard',       # variant
        r'reveal.*top.*cards? of your library.*(?:put|place).*(?:rest|them|those).*into your graveyard',  # "reveal top 4 of your library, put rest into your graveyard"
    ]
    if any(re.search(p, text) for p in self_mill_patterns):
        tags.append('self_mill')

    # Graveyard interaction (broader category)
    if re.search(r'from.*graveyard|in.*graveyard|graveyard to|exile.*graveyard', text):
        tags.append('graveyard')

    # Removal
    removal_patterns = [
        r'destroy target', r'exile target', r'return target.*to.*hand',
        r'-\d+/-\d+', r'deals? \d+ damage to', r'sacrifice target'
    ]
    if any(re.search(p, text) for p in removal_patterns):
        tags.append('removal')

    # Protection
    if re.search(r'\bhexproof\b|\bindestructible\b|\bshroud\b|prevents? all damage|protection from|\bward\b', text):
        tags.append('protection')

    # Counters theme
    if re.search(r'\+1/\+1 counter|counter.*on|put.*counter|remove.*counter|proliferate', text):
        tags.append('counters')

    # Untap mechanics
    if re.search(r'untap (target|another|all|up to)', text):
        tags.append('untap_others')

    # Tap for mana
    if re.search(r'\{t\}.*add.*mana|\{t\}:.*add \{[wubrgc]\}', text):
        tags.append('mana_ability')

    # Storm/spellslinger
    if re.search(r'instant or sorcery|cast.*instant|cast.*sorcery|whenever you cast', text):
        tags.append('spellslinger')

    # Tribal synergies
    tribal_types = extract_tribal_types(card)
    for creature_type in tribal_types:
        tags.append(f'tribal_{creature_type}')

    # Tribal payoffs (cares about creature types)
    if re.search(r'share a creature type|choose a creature type', text):
        tags.append('tribal_payoff')

    # Landfall
    if re.search(r'landfall|whenever a land enters', text):
        tags.append('landfall')

    # Equipment/Auras
    if 'equipment' in type_line:
        tags.append('equipment')
    if 'aura' in type_line and 'enchant creature' in text:
        tags.append('aura')

    # Equipment matters (cares about equipment)
    equipment_matters_patterns = [
        r'whenever.*equipped',
        r'equipped creature',
        r'attach.*equipment',
        r'when.*equipment.*attached',
        r'equipment.*costs?.*less',
        r'search.*library.*equipment',
        r'equipment you control'
    ]
    if any(re.search(p, text) for p in equipment_matters_patterns):
        tags.append('equipment_matters')

    # Artifact synergy
    if re.search(r'artifact you control|artifact card|artifact from|sacrifice an artifact', text):
        tags.append('artifact_synergy')

    # Enchantment synergy
    if re.search(r'enchantment you control|enchantment card|enchantment from', text):
        tags.append('enchantment_synergy')

    # ============================================================================
    # GLOBAL/SCALING SYNERGIES (count-based scaling)
    # ============================================================================

    # Artifact count scaling (Inspiring Statuary, Jhoira's Familiar, etc.)
    # Scales with total number of artifacts in deck
    if re.search(r'for each artifact you control|number of artifacts you control|artifact you control.*gets?|improvise', text):
        tags.append('scales_with_artifacts')

    # Equipment count scaling (Hammer of Nazahn, Heavenly Blademaster, etc.)
    # Scales with total number of equipment in deck
    if re.search(r'for each equipment|number of equipment|equipment you control.*gets?', text):
        tags.append('scales_with_equipment')

    # Instant/Sorcery count scaling (Sword of Once and Future, Aria of Flame, etc.)
    # Scales with instant/sorcery count in graveyard or deck
    if re.search(r'for each instant.*sorcery|instant.*sorcery.*in.*graveyard|prowess|magecraft', text):
        tags.append('scales_with_spells')

    # Permanent count scaling (Deadly Brew, Ulvenwald Mysteries, etc.)
    # Scales with total permanents you control
    if re.search(r'for each permanent|number of permanents|permanent you control.*gets?', text):
        tags.append('scales_with_permanents')

    # Creature count scaling
    if re.search(r'for each creature|number of creatures you control|creature you control.*gets?', text):
        tags.append('scales_with_creatures')

    # Land count scaling (but NOT just landfall)
    # Cards like Conduit of Worlds that care about land count
    if re.search(r'for each land|number of lands you control', text):
        tags.append('scales_with_lands')

    # ============================================================================
    # THREE-WAY SYNERGIES (requires multiple components)
    # ============================================================================

    # Graveyard recursion + type (e.g., Conduit of Worlds: lands + graveyard + ramp)
    if re.search(r'play.*land.*from.*graveyard|land.*from.*graveyard.*to.*battlefield', text):
        tags.append('recursion_land')

    # Artifact recursion (needs artifacts + graveyard + recursion)
    if re.search(r'artifact.*from.*graveyard', text):
        tags.append('recursion_artifact')

    # Creature recursion (needs creatures + graveyard + recursion)
    if re.search(r'creature.*from.*graveyard', text):
        tags.append('recursion_creature')

    # Spell recursion (needs instants/sorceries + graveyard + spellslinger)
    if re.search(r'instant.*sorcery.*from.*graveyard|flashback|retrace', text):
        tags.append('recursion_spell')

    # Equipment + creature synergy (voltron enablers like Ardenn)
    if re.search(r'attach.*equipment.*creature|move.*equipment', text):
        tags.append('equipment_enabler')

    return tags


def extract_tribal_types(card: Dict) -> Set[str]:
    """Extract creature types from type line"""
    type_line = card.get('type_line', '').lower()

    # Only extract from creatures
    if 'creature' not in type_line:
        return set()

    # Parse subtypes after "—"
    if '—' not in type_line:
        return set()

    _, subtypes_part = type_line.split('—', maxsplit=1)
    subtypes = {st.strip() for st in subtypes_part.split()}

    # Common tribal types to track
    common_tribes = {
        'elf', 'elves', 'goblin', 'zombie', 'merfolk', 'vampire', 'dragon',
        'angel', 'demon', 'human', 'wizard', 'warrior', 'soldier', 'knight',
        'beast', 'elemental', 'spirit', 'artifact', 'sliver', 'dinosaur',
        'cat', 'dog', 'bird', 'snake', 'spider', 'insect', 'rat', 'wolf'
    }

    return subtypes & common_tribes


# ============================================================================
# ROLE CLASSIFICATION
# ============================================================================

def classify_roles(card: Dict, tags: List[str]) -> List[str]:
    """
    Classify card into functional roles

    Roles: ramp, draw, removal, protection, finisher, combo_piece, etc.
    """
    text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()
    cmc = card.get('cmc', 0)
    power = card.get('power')
    roles = []

    # Ramp
    if 'ramp' in tags:
        # Distinguish color correction from true ramp
        if re.search(r'search your library for a basic land', text):
            roles.append('color_correction')
        else:
            roles.append('ramp')

    # Card draw
    if 'card_draw' in tags:
        roles.append('draw')

    # Removal
    if 'removal' in tags:
        roles.append('removal')

    # Protection
    if 'protection' in tags:
        roles.append('protection')

    # Finisher (big creatures or win conditions)
    if power and power.isdigit() and int(power) >= 6:
        roles.append('finisher')
    if re.search(r'you win the game|opponent loses the game|combat damage.*player', text):
        roles.append('finisher')

    # Board wipe
    if re.search(r'destroy all|exile all|return all.*to.*hand|-\d+/-\d+ to all', text):
        roles.append('board_wipe')

    # Tutor
    if re.search(r'search your library for a card|search your library for.*creature|search your library for.*artifact', text):
        if 'land' not in text:  # Exclude ramp spells
            roles.append('tutor')

    # Recursion
    if re.search(r'return.*from.*graveyard.*to.*hand|return.*from.*graveyard.*to the battlefield', text):
        roles.append('recursion')

    # Combo piece (cards with combo keywords)
    combo_keywords = ['untap', 'infinite', 'copy', 'extra turn', 'extra combat']
    if any(kw in text for kw in combo_keywords):
        roles.append('combo_piece')

    # Stax/Tax
    if re.search(r'costs? \{?\d+\}? more|can\'t cast|can\'t activate|prevent', text):
        roles.append('stax')

    return roles


# ============================================================================
# FILTERING FOR COMMANDER PLAYABILITY
# ============================================================================

def is_commander_playable(card: Dict) -> bool:
    """
    Filter out cards not legal/relevant in Commander

    Excludes:
    - Non-Commander legal cards
    - Tokens
    - Basic lands (too generic)
    - Conspiracies, schemes, vanguards
    """
    type_line = card.get('type_line', '').lower()
    name = card.get('name', '').lower()

    # Exclude tokens
    if 'token' in type_line:
        return False

    # Exclude basic lands
    if 'basic land' in type_line:
        return False

    # Exclude special card types
    exclude_types = ['conspiracy', 'scheme', 'vanguard', 'phenomenon', 'plane']
    if any(t in type_line for t in exclude_types):
        return False

    # Exclude silver-bordered / un-set cards (heuristic: unusual punctuation)
    if '?' in name or '!' in name:
        return False

    return True


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def create_preprocessed_cards():
    """Generate preprocessed card database"""

    # Paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / 'data' / 'cards' / 'cards-minimal.json'
    output_file = project_root / 'data' / 'cards' / 'cards-preprocessed.json'

    if not input_file.exists():
        print(f"Error: {input_file} not found!")
        print("Run: python scripts/create_minimal_cards.py")
        return False

    print(f"Loading {input_file.name}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        minimal_cards = json.load(f)

    print(f"Loaded {len(minimal_cards)} cards")
    print("Preprocessing cards for recommendations...")

    preprocessed = []
    commander_playable = 0

    for idx, card in enumerate(minimal_cards, 1):
        # Filter out non-Commander playable cards
        if not is_commander_playable(card):
            continue

        commander_playable += 1

        # Extract features
        tags = extract_synergy_tags(card)
        roles = classify_roles(card, tags)

        # Create preprocessed entry
        preprocessed_card = {
            # Core identity
            'name': card.get('name'),
            'type_line': card.get('type_line'),
            'oracle_text': card.get('oracle_text', ''),

            # Mana info
            'mana_cost': card.get('mana_cost', ''),
            'cmc': card.get('cmc', 0),
            'colors': card.get('colors', []),
            'color_identity': card.get('color_identity', []),

            # Pre-computed features for fast searching
            'synergy_tags': tags,
            'roles': roles,

            # Stats (for filtering)
            'power': card.get('power'),
            'toughness': card.get('toughness'),

            # Image for display
            'image_uri': card.get('image_uris', {}).get('art_crop') if card.get('image_uris') else None
        }

        preprocessed.append(preprocessed_card)

        if idx % 5000 == 0:
            print(f"  Processed {idx}/{len(minimal_cards)} cards...")

    print(f"\nFiltered to {commander_playable} Commander-playable cards")
    print(f"Writing to {output_file}...")

    # Use compact JSON formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(preprocessed, f, separators=(',', ':'))

    # Report stats
    input_size = input_file.stat().st_size / (1024 * 1024)
    output_size = output_file.stat().st_size / (1024 * 1024)

    print("\n✅ Success!")
    print(f"Input:  {len(minimal_cards)} cards ({input_size:.1f} MB)")
    print(f"Output: {len(preprocessed)} cards ({output_size:.1f} MB)")
    print(f"Filtered out: {len(minimal_cards) - len(preprocessed)} cards")

    # Sample statistics
    all_tags = set()
    all_roles = set()
    for card in preprocessed[:1000]:  # Sample first 1000
        all_tags.update(card['synergy_tags'])
        all_roles.update(card['roles'])

    print(f"\nUnique synergy tags: {len(all_tags)}")
    print(f"Unique roles: {len(all_roles)}")
    print(f"\nPreprocessed database created at:")
    print(f"{output_file}")

    return True


if __name__ == '__main__':
    success = create_preprocessed_cards()
    exit(0 if success else 1)
