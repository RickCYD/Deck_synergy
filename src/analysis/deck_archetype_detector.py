"""
Mathematically Rigorous Deck Archetype Detector

Uses multi-signal optimization approach combining:
- Synergy graph analysis (community detection, modularity)
- TF-IDF embeddings from oracle text
- Role distribution entropy
- Weighted scoring against archetype templates

This replaces arbitrary threshold-based detection with data-driven,
mathematically sound methods.
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter
import re
import numpy as np

# Graph analysis
import networkx as nx
from networkx.algorithms import community

# Machine learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# MTG-specific stop words to filter out generic text
MTG_STOP_WORDS = [
    'the', 'a', 'an', 'this', 'that', 'it', 'you', 'your', 'target',
    'choose', 'may', 'then', 'put', 'get', 'have', 'has', 'can', 'each',
    'any', 'all', 'other', 'one', 'two', 'three', 'until', 'end', 'of',
    'turn', 'step', 'phase', 'player', 'instead', 'if', 'unless', 'when',
    'whenever', 'at', 'as', 'enters', 'leaves', 'battlefield', 'card', 'cards'
]


# ============================================================================
# ARCHETYPE TEMPLATES
# ============================================================================

ARCHETYPE_TEMPLATES = {
    'Aristocrats': {
        'synergy_categories': ['death_trigger_synergy', 'sacrifice_synergy', 'token_synergy'],
        'tfidf_patterns': [r'sacrifice', r'dies', r'death trigger', r'whenever.*creature.*dies'],
        'required_roles': ['Sacrifice Outlet', 'Death Trigger', 'Aristocrat'],
        'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
    },
    'Tokens': {
        'synergy_categories': ['token_synergy', 'go_wide_synergy', 'anthem_synergy'],
        'tfidf_patterns': [r'create.*token', r'token.*creature', r'populate'],
        'required_roles': ['Token Generator', 'Token Doubler', 'Go-Wide'],
        'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
    },
    'Voltron': {
        'synergy_categories': ['equipment_synergy', 'aura_synergy', 'combat_synergy'],
        'tfidf_patterns': [r'equip', r'equipped', r'aura', r'enchant creature'],
        'required_roles': ['Equipment', 'Aura', 'Voltron'],
        'weights': {'synergies': 0.4, 'tfidf': 0.3, 'roles': 0.3}
    },
    'Spellslinger': {
        'synergy_categories': ['spell_synergy', 'prowess_synergy', 'storm_synergy'],
        'tfidf_patterns': [r'instant.*sorcery', r'spell.*cast', r'prowess', r'storm'],
        'required_roles': ['Spellslinger', 'Cantrip', 'Ritual'],
        'weights': {'synergies': 0.4, 'tfidf': 0.4, 'roles': 0.2}
    },
    'Go-Wide': {
        'synergy_categories': ['go_wide_synergy', 'token_synergy', 'anthem_synergy'],
        'tfidf_patterns': [r'creatures you control', r'each creature', r'\+1/\+1'],
        'required_roles': ['Go-Wide', 'Anthem', 'Token Generator'],
        'weights': {'synergies': 0.5, 'tfidf': 0.2, 'roles': 0.3}
    },
    'Counters': {
        'synergy_categories': ['counter_synergy', 'proliferate_synergy'],
        'tfidf_patterns': [r'\+1/\+1 counter', r'proliferate', r'counter.*creature'],
        'required_roles': ['Counter Synergy', 'Proliferate'],
        'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
    },
    'Reanimator': {
        'synergy_categories': ['reanimation_synergy', 'graveyard_synergy', 'discard_synergy'],
        'tfidf_patterns': [r'return.*graveyard', r'reanimate', r'unearth'],
        'required_roles': ['Reanimation', 'Self-Mill', 'Discard Outlet'],
        'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
    },
    'Ramp': {
        'synergy_categories': ['ramp_synergy', 'landfall_synergy'],
        'tfidf_patterns': [r'search.*land', r'mana.*add', r'landfall'],
        'required_roles': ['Ramp', 'Mana Dork', 'Land Ramp'],
        'weights': {'synergies': 0.4, 'tfidf': 0.3, 'roles': 0.3}
    }
}


# ============================================================================
# SIGNAL 1: SYNERGY GRAPH ANALYSIS
# ============================================================================

def extract_synergy_features(deck_synergies: Dict, cards: List[Dict]) -> Dict:
    """
    Extract graph-based features from synergy network using community detection.

    Mathematical approach:
    - Build graph G = (V, E, W) where V = cards, E = synergies, W = weights
    - Apply Louvain algorithm for community detection (modularity maximization)
    - Calculate modularity Q = (1/2m) Σ[A_ij - (k_i × k_j)/2m] δ(c_i, c_j)
    - Compute clustering coefficients

    Args:
        deck_synergies: Dictionary of synergies from synergy analyzer
        cards: List of card dictionaries

    Returns:
        dict: {
            'synergy_vector': {category: count},
            'modularity': float,
            'num_communities': int,
            'avg_clustering': float
        }
    """
    # Build networkx graph from synergies
    G = nx.Graph()

    # Add nodes (cards)
    for card in cards:
        G.add_node(card['name'])

    # Add edges (synergies) with weights
    edge_count = 0
    for synergy_key, synergy_data in deck_synergies.items():
        if '||' in synergy_key:
            parts = synergy_key.split('||')
            if len(parts) == 2:
                card1, card2 = parts
                weight = synergy_data.get('total_weight', 0)
                if weight > 0:
                    G.add_edge(card1, card2, weight=weight)
                    edge_count += 1

    # Count synergies by category
    synergy_vector = {}
    for synergy_data in deck_synergies.values():
        if isinstance(synergy_data, dict):
            synergies_dict = synergy_data.get('synergies', {})
            if isinstance(synergies_dict, dict):
                for category, synergies_list in synergies_dict.items():
                    if isinstance(synergies_list, list):
                        synergy_vector[category] = synergy_vector.get(category, 0) + len(synergies_list)

    # Community detection (Louvain algorithm)
    modularity = 0.0
    num_communities = 0

    if edge_count > 0 and len(G.nodes()) > 1:
        try:
            communities = community.louvain_communities(G, weight='weight', seed=42)
            modularity = community.modularity(G, communities, weight='weight')
            num_communities = len(communities)
        except Exception as e:
            # If community detection fails, use defaults
            print(f"Warning: Community detection failed: {e}")
            modularity = 0.0
            num_communities = 0

    # Average clustering coefficient
    avg_clustering = 0.0
    if len(G.nodes()) > 0:
        try:
            avg_clustering = nx.average_clustering(G, weight='weight')
        except Exception:
            avg_clustering = 0.0

    return {
        'synergy_vector': synergy_vector,
        'modularity': modularity,
        'num_communities': num_communities,
        'avg_clustering': avg_clustering
    }


# ============================================================================
# SIGNAL 2: TF-IDF EMBEDDINGS
# ============================================================================

def extract_tfidf_features(cards: List[Dict]) -> Dict:
    """
    Create TF-IDF embeddings from oracle text for deck strategy analysis.

    Mathematical approach:
    - TF-IDF(t,d) = TF(t,d) × IDF(t)
    - TF(t,d) = (count of term t in doc d) / (total terms in d)
    - IDF(t) = log(N / n_t) where N = total cards, n_t = cards with term t
    - Uses n-grams to capture phrases like "sacrifice a creature"

    Args:
        cards: List of card dictionaries

    Returns:
        dict: {
            'deck_centroid': np.ndarray (average TF-IDF vector),
            'top_terms': [(term, weight), ...],
            'variance': float (deck focus measure)
        }
    """
    # Collect oracle texts
    oracle_texts = []
    for card in cards:
        oracle = card.get('oracle_text', '')
        if oracle:
            oracle_texts.append(oracle)

    if len(oracle_texts) < 2:
        return {
            'deck_centroid': np.array([]),
            'top_terms': [],
            'variance': 0.0
        }

    try:
        # TF-IDF vectorization with MTG-specific configuration
        vectorizer = TfidfVectorizer(
            max_features=200,
            ngram_range=(1, 3),  # Capture phrases like "sacrifice a creature"
            stop_words=MTG_STOP_WORDS,
            lowercase=True,
            min_df=1,  # Allow terms that appear in at least 1 document
            max_df=0.95  # Ignore terms that appear in >95% of documents
        )

        tfidf_matrix = vectorizer.fit_transform(oracle_texts)

        # Deck centroid (average vector)
        deck_centroid = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

        # Top terms
        feature_names = vectorizer.get_feature_names_out()
        top_indices = deck_centroid.argsort()[-20:][::-1]
        top_terms = [(feature_names[i], deck_centroid[i]) for i in top_indices if deck_centroid[i] > 0]

        # Variance (deck focus measure)
        variance = float(np.var(tfidf_matrix.toarray()))

        return {
            'deck_centroid': deck_centroid,
            'top_terms': top_terms,
            'variance': variance
        }
    except Exception as e:
        print(f"Warning: TF-IDF extraction failed: {e}")
        return {
            'deck_centroid': np.array([]),
            'top_terms': [],
            'variance': 0.0
        }


# ============================================================================
# SIGNAL 3: ROLE DISTRIBUTION ENTROPY
# ============================================================================

def extract_role_features(cards: List[Dict]) -> Dict:
    """
    Analyze functional role distribution using Shannon entropy.

    Mathematical approach:
    - Shannon entropy: H(R) = -Σ P(role_i) log₂ P(role_i)
    - P(role_i) = n_i / Σn_j where n_i = count of role i
    - High entropy = diverse/unfocused deck
    - Low entropy = focused deck strategy

    Args:
        cards: List of card dictionaries

    Returns:
        dict: {
            'role_distribution': {role: count},
            'entropy': float (diversity measure),
            'primary_roles': [(role, count), ...]
        }
    """
    role_counts = Counter()

    for card in cards:
        roles = card.get('roles', [])
        if isinstance(roles, list):
            for role in roles:
                role_counts[role] += 1

    if len(role_counts) == 0:
        return {
            'role_distribution': {},
            'entropy': 0.0,
            'primary_roles': []
        }

    # Calculate Shannon entropy (diversity)
    total = sum(role_counts.values())
    probs = [count / total for count in role_counts.values()]
    entropy = -sum(p * np.log2(p) for p in probs if p > 0)

    return {
        'role_distribution': dict(role_counts),
        'entropy': entropy,
        'primary_roles': role_counts.most_common(5)
    }


# ============================================================================
# WEIGHTED SCORING FUNCTIONS
# ============================================================================

def calculate_synergy_match_score(synergy_vector: Dict, template_categories: List[str]) -> float:
    """
    Calculate cosine similarity between deck synergies and archetype template.

    Normalized by expected count (20 synergies = strong match).

    Args:
        synergy_vector: Dictionary of synergy counts by category
        template_categories: Required synergy categories for archetype

    Returns:
        float: Score in [0, 1]
    """
    total_relevant = sum(
        synergy_vector.get(cat, 0)
        for cat in template_categories
    )

    # Normalize by expected count (20 synergies = strong match)
    normalized = min(1.0, total_relevant / 20.0)
    return normalized


def calculate_tfidf_match_score(top_terms: List[Tuple[str, float]], template_patterns: List[str]) -> float:
    """
    Calculate weighted match score using regex patterns on TF-IDF terms.

    Args:
        top_terms: List of (term, weight) tuples from TF-IDF
        template_patterns: Regex patterns to match for archetype

    Returns:
        float: Score in [0, 1]
    """
    total_weight = 0.0
    matched_weight = 0.0

    for term, weight in top_terms:
        total_weight += weight
        for pattern in template_patterns:
            if re.search(pattern, term, re.IGNORECASE):
                matched_weight += weight
                break

    if total_weight > 0:
        return matched_weight / total_weight
    return 0.0


def calculate_role_match_score(role_distribution: Dict, required_roles: List[str]) -> float:
    """
    Calculate fraction of cards with required roles.

    Args:
        role_distribution: Dictionary of role counts
        required_roles: List of required roles for archetype

    Returns:
        float: Score in [0, 1]
    """
    total_cards = sum(role_distribution.values())
    relevant_cards = sum(
        role_distribution.get(role, 0)
        for role in required_roles
    )

    if total_cards > 0:
        return relevant_cards / total_cards
    return 0.0


# ============================================================================
# MAIN DETECTION FUNCTION
# ============================================================================

def detect_deck_archetype(cards: List[Dict], deck_synergies: Dict = None,
                         commander: Optional[Dict] = None, verbose: bool = False) -> Dict:
    """
    Detect deck archetype using multi-signal optimization.

    This is the main entry point that replaces the old threshold-based detection.

    Mathematical approach:
    1. Extract three independent signals (synergy graph, TF-IDF, roles)
    2. Score against each archetype template using weighted combination
    3. Select best match with confidence threshold
    4. Validate using statistical metrics (modularity, entropy)

    Args:
        cards: List of card dictionaries from the deck
        deck_synergies: Dictionary of synergies (optional, default {})
        commander: Commander card dictionary (optional)
        verbose: If True, print detailed analysis

    Returns:
        dict: {
            'primary_archetype': str,
            'secondary_archetype': str or None,
            'confidence': float (0-1),
            'scores': {archetype: score},
            'metrics': {
                'modularity': float,
                'entropy': float,
                'num_communities': int
            }
        }
    """
    if deck_synergies is None:
        deck_synergies = {}

    # Extract all features
    synergy_feats = extract_synergy_features(deck_synergies, cards)
    tfidf_feats = extract_tfidf_features(cards)
    role_feats = extract_role_features(cards)

    if verbose:
        print(f"\n{'='*60}")
        print(f"MATHEMATICALLY RIGOROUS ARCHETYPE DETECTION")
        print(f"{'='*60}")
        print(f"Analyzing deck with {len(cards)} cards")
        print(f"\nSignal 1: Synergy Graph Analysis")
        print(f"  Total synergies: {sum(synergy_feats['synergy_vector'].values())}")
        print(f"  Modularity: {synergy_feats['modularity']:.3f}")
        print(f"  Communities: {synergy_feats['num_communities']}")
        print(f"  Avg clustering: {synergy_feats['avg_clustering']:.3f}")

        print(f"\nSignal 2: TF-IDF Text Analysis")
        if len(tfidf_feats['top_terms']) > 0:
            print(f"  Top terms: {', '.join(t for t, w in tfidf_feats['top_terms'][:5])}")
            print(f"  Deck variance: {tfidf_feats['variance']:.3f}")
        else:
            print(f"  No TF-IDF features extracted")

        print(f"\nSignal 3: Role Distribution")
        print(f"  Shannon entropy: {role_feats['entropy']:.3f}")
        if len(role_feats['primary_roles']) > 0:
            print(f"  Primary roles: {', '.join(f'{r}({c})' for r, c in role_feats['primary_roles'][:3])}")

    # Score against each archetype template
    archetype_scores = {}

    for archetype, template in ARCHETYPE_TEMPLATES.items():
        # Calculate individual signal scores
        synergy_score = calculate_synergy_match_score(
            synergy_feats['synergy_vector'],
            template['synergy_categories']
        )

        tfidf_score = calculate_tfidf_match_score(
            tfidf_feats['top_terms'],
            template['tfidf_patterns']
        )

        role_score = calculate_role_match_score(
            role_feats['role_distribution'],
            template['required_roles']
        )

        # Weighted combination
        weights = template['weights']
        total_score = (
            synergy_score * weights['synergies'] +
            tfidf_score * weights['tfidf'] +
            role_score * weights['roles']
        )

        archetype_scores[archetype] = total_score

        if verbose:
            print(f"\n{archetype}:")
            print(f"  Synergy: {synergy_score:.3f} × {weights['synergies']} = {synergy_score * weights['synergies']:.3f}")
            print(f"  TF-IDF:  {tfidf_score:.3f} × {weights['tfidf']} = {tfidf_score * weights['tfidf']:.3f}")
            print(f"  Role:    {role_score:.3f} × {weights['roles']} = {role_score * weights['roles']:.3f}")
            print(f"  TOTAL:   {total_score:.3f}")

    # Get top 2 archetypes
    sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)

    primary = sorted_archetypes[0][0]
    primary_score = sorted_archetypes[0][1]

    secondary = None
    if len(sorted_archetypes) > 1 and sorted_archetypes[1][1] > 0.2:
        secondary = sorted_archetypes[1][0]

    # Confidence = primary score
    confidence = primary_score

    # Default to Generic if no strong match
    if confidence < 0.25:
        primary = 'Generic/Midrange'
        confidence = 0.5

    if verbose:
        print(f"\n{'='*60}")
        print(f"RESULT:")
        print(f"  Primary: {primary} (confidence: {confidence:.3f})")
        if secondary:
            print(f"  Secondary: {secondary} (score: {sorted_archetypes[1][1]:.3f})")
        print(f"{'='*60}\n")

    return {
        'primary_archetype': primary,
        'secondary_archetype': secondary,
        'confidence': confidence,
        'scores': archetype_scores,
        'archetype_scores': archetype_scores,  # For backwards compatibility
        'metrics': {
            'modularity': synergy_feats['modularity'],
            'entropy': role_feats['entropy'],
            'num_communities': synergy_feats['num_communities'],
            'avg_clustering': synergy_feats['avg_clustering'],
            'tfidf_variance': tfidf_feats['variance']
        }
    }


# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_detection_quality(archetype_info: Dict) -> Dict:
    """
    Validate archetype detection quality using statistical metrics.

    Metrics:
    - Modularity > 0.4 = good community structure
    - Confidence > 0.6 = strong archetype match
    - Entropy: balance between focus and diversity

    Args:
        archetype_info: Result from detect_deck_archetype

    Returns:
        dict: {
            'quality': 'excellent' | 'good' | 'fair' | 'poor',
            'confidence': float,
            'modularity': float,
            'recommendations': [str]
        }
    """
    metrics = archetype_info['metrics']
    confidence = archetype_info['confidence']

    recommendations = []

    # Modularity check (>0.4 = good community structure)
    if metrics['modularity'] < 0.3:
        recommendations.append("Low synergy modularity - deck may lack focused strategy")
    elif metrics['modularity'] > 0.5:
        recommendations.append("Excellent synergy clustering - well-focused deck")

    # Confidence check
    if confidence < 0.3:
        recommendations.append("Low archetype confidence - deck may be unfocused or Generic")
    elif confidence > 0.6:
        recommendations.append("High confidence - strong archetype identity")

    # Entropy check
    if metrics['entropy'] < 2.0:
        recommendations.append("Low role diversity - very focused strategy")
    elif metrics['entropy'] > 4.0:
        recommendations.append("High role diversity - deck may lack focus")

    # Determine quality
    if confidence > 0.6 and metrics['modularity'] > 0.4:
        quality = 'excellent'
    elif confidence > 0.4 and metrics['modularity'] > 0.3:
        quality = 'good'
    elif confidence > 0.25:
        quality = 'fair'
    else:
        quality = 'poor'

    return {
        'quality': quality,
        'confidence': confidence,
        'modularity': metrics['modularity'],
        'entropy': metrics['entropy'],
        'recommendations': recommendations
    }


# ============================================================================
# BACKWARDS COMPATIBILITY
# ============================================================================

class DeckArchetypeDetector:
    """
    Backwards compatibility wrapper for old API.

    The old code used DeckArchetypeDetector().detect_archetype(cards, commander).
    This wrapper redirects to the new function-based API.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def detect_archetype(self, cards: List[Dict], commander: Optional[Dict] = None) -> Dict:
        """
        Detect archetype using the old API (redirects to new implementation).

        Args:
            cards: List of card dictionaries
            commander: Optional commander card

        Returns:
            Dictionary with archetype info (old format)
        """
        # Call new function
        result = detect_deck_archetype(cards, {}, commander, self.verbose)

        # Add old fields for compatibility
        result['priorities'] = {}  # Old priority system deprecated
        result['deck_stats'] = {}  # Old stats deprecated

        return result
