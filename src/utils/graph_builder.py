"""
Graph Builder Utility
Converts deck data into Cytoscape graph elements
"""

from typing import Dict, List

from src.utils.card_roles import slugify_role


def build_graph_elements(deck_data: Dict) -> List[Dict]:
    """
    Convert deck data into Cytoscape graph elements (nodes and edges)

    Args:
        deck_data: Dictionary containing deck information with cards and synergies

    Returns:
        List of Cytoscape elements (nodes and edges)
    """
    elements = []

    # Create nodes for each card
    cards = deck_data.get('cards', [])
    print(f"[GRAPH BUILDER] Creating nodes for {len(cards)} cards")

    for idx, card in enumerate(cards):
        try:
            if not card or not isinstance(card, dict):
                print(f"[GRAPH BUILDER] WARNING: Card {idx} is not a valid dict, skipping")
                continue

            if not card.get('name'):
                print(f"[GRAPH BUILDER] WARNING: Card {idx} has no name, skipping")
                continue

            node = create_card_node(card)

            # Validate node has required fields
            if not node.get('data') or not node['data'].get('id'):
                print(f"[GRAPH BUILDER] WARNING: Node for {card.get('name')} is invalid, skipping")
                continue

            elements.append(node)
        except Exception as e:
            print(f"[GRAPH BUILDER] ERROR: Failed to create node for card {card.get('name', 'Unknown')}: {e}")
            continue

    print(f"[GRAPH BUILDER] Created {len(elements)} nodes")

    # Create edges for synergies
    synergies = deck_data.get('synergies', {})
    print(f"[GRAPH BUILDER] Creating edges for {len(synergies)} synergies")

    edges_created = 0
    for synergy_key, synergy_data in synergies.items():
        try:
            if not synergy_key or not isinstance(synergy_data, dict):
                continue

            edge = create_synergy_edge(synergy_key, synergy_data)

            # Validate edge has required fields
            if not edge.get('data') or not edge['data'].get('source') or not edge['data'].get('target'):
                print(f"[GRAPH BUILDER] WARNING: Edge for {synergy_key} is invalid, skipping")
                continue

            elements.append(edge)
            edges_created += 1
        except Exception as e:
            print(f"[GRAPH BUILDER] ERROR: Failed to create edge for {synergy_key}: {e}")
            continue

    print(f"[GRAPH BUILDER] Created {edges_created} edges")
    print(f"[GRAPH BUILDER] Total elements: {len(elements)}")

    return elements


def create_card_node(card: Dict) -> Dict:
    """
    Create a Cytoscape node element from a card

    Args:
        card: Card dictionary

    Returns:
        Cytoscape node element
    """
    card_name = card.get('name', 'Unknown')

    # Determine node type and color
    node_type = 'commander' if card.get('is_commander', False) else 'card'
    roles = card.get('roles') or {}
    role_classes = []
    for category_key, role_keys in roles.items():
        for role_key in role_keys:
            role_classes.append(slugify_role(category_key, role_key))

    # Get card colors for visual representation
    colors = card.get('colors', [])
    color_code = get_color_code(colors)
    border_color = get_border_color(colors)
    secondary_border = get_secondary_border_color(colors)
    is_multicolor = len(colors) >= 2

    # Get image URLs
    # image_url = full card image (normal size)
    # art_crop_url = just the artwork (for graph background)
    image_uris = card.get('image_uris') or {}

    # Debug first card
    if card_name == "Wight of the Reliquary":
        print(f"\n[DEBUG GRAPH] ===== CARD DEBUG =====")
        print(f"[DEBUG GRAPH] Card: {card_name}")
        print(f"[DEBUG GRAPH] Has 'image_uris' key: {'image_uris' in card}")
        if 'image_uris' in card:
            print(f"[DEBUG GRAPH] image_uris value: {card['image_uris']}")
            print(f"[DEBUG GRAPH] image_uris type: {type(card['image_uris'])}")
        print(f"[DEBUG GRAPH] =====================\n")

    image_url = image_uris.get('normal', '') or image_uris.get('large', '') or ''
    art_crop_url = image_uris.get('art_crop', '') or image_url or ''

    if card_name == "Wight of the Reliquary":
        print(f"[DEBUG GRAPH] image_url result: '{image_url}'")
        print(f"[DEBUG GRAPH] art_crop_url result: '{art_crop_url}'")

    # Create node data - ensure no None values that could break Cytoscape
    node_data = {
        'id': card_name or 'Unknown',
        'label': card_name or 'Unknown',
        'type': node_type,

        # Card information
        'card_type': card.get('type_line') or 'Unknown',
        'mana_cost': card.get('mana_cost') or '',
        'cmc': card.get('cmc') or 0,
        'colors': colors or [],
        'color_identity': card.get('color_identity') or [],
        'oracle_text': card.get('oracle_text') or '',
        'power': card.get('power') or '',  # Convert None to empty string
        'toughness': card.get('toughness') or '',  # Convert None to empty string
        'loyalty': card.get('loyalty') or '',  # Convert None to empty string
        'rarity': card.get('rarity') or '',

        # Visual properties
        'color_code': color_code,
        'border_color': border_color,
        'secondary_border': secondary_border if is_multicolor else border_color,
        'is_multicolor': is_multicolor,

        # Categories from Archidekt
        'categories': card.get('categories') or [],
        'roles': roles or {}
    }

    # Only add image URLs if they're not empty (to avoid invalid CSS "background-image: " in Cytoscape)
    if image_url:
        node_data['image_url'] = image_url
    if art_crop_url:
        node_data['art_crop_url'] = art_crop_url

    classes = ' '.join([node_type] + role_classes) if role_classes else node_type

    return {
        'data': node_data,
        'classes': classes
    }


def create_synergy_edge(synergy_key: str, synergy_data: Dict) -> Dict:
    """
    Create a Cytoscape edge element from synergy data

    Args:
        synergy_key: Key in format "Card1||Card2"
        synergy_data: Dictionary containing synergy information

    Returns:
        Cytoscape edge element
    """
    card1, card2 = synergy_key.split('||')

    edge_id = f"{card1}_{card2}".replace(' ', '_').replace(',', '').replace("'", '')

    weight = synergy_data.get('total_weight', 1.0)

    # Check if this is a verified combo
    has_verified_combo = synergy_data.get('has_verified_combo', False)

    edge_data = {
        'id': edge_id or f"edge_{hash(synergy_key)}",
        'source': card1 or 'Unknown',
        'target': card2 or 'Unknown',
        'source_label': card1 or 'Unknown',
        'target_label': card2 or 'Unknown',

        # Synergy weight
        'weight': round(weight, 1) if weight is not None else 1.0,

        # Synergy details
        'synergies': synergy_data.get('synergies') or {},
        'synergy_count': synergy_data.get('synergy_count') or 0,

        # Combo flag
        'has_verified_combo': has_verified_combo
    }

    # Add special class for combo edges
    edge_classes = 'synergy-edge'
    if has_verified_combo:
        edge_classes += ' verified-combo'

    return {
        'data': edge_data,
        'classes': edge_classes
    }


def get_color_code(colors: List[str]) -> str:
    """
    Get a hex color code based on MTG colors

    Args:
        colors: List of MTG color codes (W, U, B, R, G)

    Returns:
        Hex color code
    """
    # MTG color mapping
    color_map = {
        'W': '#F8F6D8',  # White
        'U': '#0E68AB',  # Blue
        'B': '#150B00',  # Black
        'R': '#D3202A',  # Red
        'G': '#00733E',  # Green
    }

    if not colors:
        return '#BCC3C7'  # Colorless (gray)

    if len(colors) == 1:
        return color_map.get(colors[0], '#BCC3C7')

    # Multi-color (gold)
    if len(colors) >= 2:
        return '#F4E15B'

    return '#BCC3C7'


def get_border_color(colors: List[str]) -> str:
    """
    Get border color for MTG cards - for multi-color, return first color

    Args:
        colors: List of MTG color codes (W, U, B, R, G)

    Returns:
        Hex color code for border
    """
    # MTG color mapping (brighter versions for borders)
    border_color_map = {
        'W': '#FFFACD',  # Bright white/cream
        'U': '#1E90FF',  # Bright blue
        'B': '#4B0082',  # Dark purple (better than pure black)
        'R': '#FF4500',  # Bright red-orange
        'G': '#32CD32',  # Bright green
    }

    if not colors:
        return '#BCC3C7'  # Colorless (gray)

    # For single color, use that color
    if len(colors) == 1:
        return border_color_map.get(colors[0], '#BCC3C7')

    # For multi-color, use first color (will be used for split border)
    return border_color_map.get(colors[0], '#F4E15B')


def get_secondary_border_color(colors: List[str]) -> str:
    """
    Get secondary border color for multi-color cards

    Args:
        colors: List of MTG color codes (W, U, B, R, G)

    Returns:
        Hex color code for secondary border, or None if single color
    """
    border_color_map = {
        'W': '#FFFACD',
        'U': '#1E90FF',
        'B': '#4B0082',
        'R': '#FF4500',
        'G': '#32CD32',
    }

    if len(colors) >= 2:
        return border_color_map.get(colors[1], '#F4E15B')

    return None


def filter_graph_by_card(elements: List[Dict], card_name: str) -> List[Dict]:
    """
    Filter graph elements to show only a specific card and its connections

    Args:
        elements: List of all graph elements
        card_name: Name of the card to focus on

    Returns:
        Filtered list of elements
    """
    # Find all connected edges
    connected_edges = []
    connected_cards = set([card_name])

    for element in elements:
        if 'source' in element.get('data', {}):
            edge_data = element['data']
            if edge_data['source'] == card_name or edge_data['target'] == card_name:
                connected_edges.append(element)
                connected_cards.add(edge_data['source'])
                connected_cards.add(edge_data['target'])

    # Get nodes for connected cards
    filtered_nodes = [
        element for element in elements
        if 'source' not in element.get('data', {}) and
        element['data']['id'] in connected_cards
    ]

    return filtered_nodes + connected_edges


def calculate_node_sizes(elements: List[Dict]) -> List[Dict]:
    """
    Calculate node sizes based on number of connections

    Args:
        elements: List of graph elements

    Returns:
        Updated elements with size information
    """
    # Count connections for each node
    connection_counts = {}

    for element in elements:
        if 'source' in element.get('data', {}):
            source = element['data']['source']
            target = element['data']['target']

            connection_counts[source] = connection_counts.get(source, 0) + 1
            connection_counts[target] = connection_counts.get(target, 0) + 1

    # Update node sizes
    for element in elements:
        if 'source' not in element.get('data', {}):
            node_id = element['data']['id']
            connections = connection_counts.get(node_id, 0)

            # Scale size based on connections (min 40, max 100)
            size = min(40 + (connections * 3), 100)
            element['data']['size'] = size
            element['data']['connections'] = connections

    return elements


def get_synergy_summary(synergy_data: Dict) -> str:
    """
    Create a human-readable summary of synergies

    Args:
        synergy_data: Synergy data dictionary

    Returns:
        Formatted summary string
    """
    summary_parts = []

    synergies = synergy_data.get('synergies', {})
    total_weight = synergy_data.get('total_weight', 0)

    summary_parts.append(f"Total Synergy Strength: {total_weight:.2f}")

    for category, synergy_list in synergies.items():
        category_name = category.replace('_', ' ').title()
        summary_parts.append(f"\n{category_name} ({len(synergy_list)}):")

        for synergy in synergy_list:
            summary_parts.append(f"  - {synergy.get('name', 'Unknown')}: {synergy.get('description', '')}")

    return '\n'.join(summary_parts)


def export_graph_data(elements: List[Dict], output_file: str):
    """
    Export graph data to a JSON file

    Args:
        elements: List of graph elements
        output_file: Path to output file
    """
    import json

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(elements, f, indent=2)


def get_graph_statistics(elements: List[Dict]) -> Dict:
    """
    Calculate statistics about the graph

    Args:
        elements: List of graph elements

    Returns:
        Dictionary with graph statistics
    """
    nodes = [e for e in elements if 'source' not in e.get('data', {})]
    edges = [e for e in elements if 'source' in e.get('data', {})]

    total_weight = sum(e['data'].get('weight', 0) for e in edges)
    avg_weight = total_weight / len(edges) if edges else 0

    # Find most connected nodes
    connection_counts = {}
    for edge in edges:
        source = edge['data']['source']
        target = edge['data']['target']
        connection_counts[source] = connection_counts.get(source, 0) + 1
        connection_counts[target] = connection_counts.get(target, 0) + 1

    most_connected = sorted(
        connection_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'total_synergy_weight': round(total_weight, 2),
        'average_synergy_weight': round(avg_weight, 2),
        'most_connected_cards': most_connected,
        'graph_density': round(len(edges) / (len(nodes) * (len(nodes) - 1) / 2), 3) if len(nodes) > 1 else 0
    }
