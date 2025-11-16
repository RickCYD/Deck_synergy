# 🎯 Mathematically Rigorous Deck Archetype Detection Plan

**Problem**: Current implementation uses arbitrary thresholds (e.g., "5+ death triggers = Aristocrats"). This is unreliable and not mathematically sound.

**Goal**: Design an optimization-based, data-driven approach using:
- Already-calculated synergies (graph structure)
- Oracle text analysis (TF-IDF embeddings)
- Graph clustering algorithms
- Statistical validation

---

## 📚 Research Findings

### Proven Approaches from Literature:

1. **Latent Dirichlet Allocation (LDA)** - Used for MTG archetype detection
   - Treats decks as documents, cards as words
   - Discovers latent topics (archetypes) automatically
   - Returns probability distributions over cards per archetype

2. **TF-IDF + K-Means Clustering**
   - Convert card text to TF-IDF vectors
   - Cluster similar cards together
   - Identify deck strategy from card clusters

3. **Graph-Based Community Detection**
   - Use synergy network as graph
   - Apply algorithms: Louvain, Label Propagation
   - Detect communities of synergistic cards

4. **Hybrid Approach** (Recommended)
   - Combine multiple signals for robustness

---

## 🎯 Proposed Solution: Multi-Signal Archetype Detection

### Phase 1: Feature Extraction (Multiple Signals)

#### Signal 1: Synergy Graph Structure
**What we have**: Already-calculated synergies between cards

**Mathematical representation**:
```
G = (V, E, W)
where:
  V = set of cards in deck
  E = synergy relationships
  W(u,v) = synergy strength between cards u and v
```

**Metrics to extract**:
1. **Node centrality** - Which cards are central to synergies?
   - Degree centrality: `C_D(v) = deg(v) / (n-1)`
   - Betweenness centrality: `C_B(v) = Σ(σ_st(v) / σ_st)` for all s,t
   - Eigenvector centrality: `x_v = (1/λ) Σ a_vu * x_u`

2. **Community structure** - Which cards cluster together?
   - Louvain modularity maximization
   - Label propagation
   - Girvan-Newman edge betweenness

3. **Synergy type distribution**:
   - Count synergies by category (already categorized!)
   - Build feature vector: `f_synergy = [n_aristocrats, n_tokens, n_voltron, ...]`

**Algorithm**:
```python
def extract_synergy_features(deck_synergies):
    """
    Extract graph-based features from synergy network.

    Returns:
        dict: {
            'synergy_vector': [n_cat1, n_cat2, ...],  # Counts per synergy category
            'centrality_scores': {card: score},
            'community_labels': {card: cluster_id},
            'modularity': float  # Quality of clustering
        }
    """
    # Build networkx graph from synergies
    G = build_synergy_graph(deck_synergies)

    # Count synergies by category
    synergy_vector = count_synergies_by_category(deck_synergies)

    # Detect communities (Louvain algorithm)
    communities = community.louvain_communities(G, weight='strength')

    # Calculate modularity (quality metric)
    modularity = community.modularity(G, communities)

    return {
        'synergy_vector': synergy_vector,
        'communities': communities,
        'modularity': modularity
    }
```

#### Signal 2: TF-IDF Card Embeddings
**What we have**: Oracle text for every card

**Mathematical representation**:
```
TF-IDF(t,d) = TF(t,d) × IDF(t)

where:
  TF(t,d) = (count of term t in document d) / (total terms in d)
  IDF(t) = log(N / n_t)
  N = total number of cards
  n_t = number of cards containing term t
```

**Key terms to extract**:
- Mechanical keywords: "sacrifice", "token", "counter", "draw", "discard"
- Trigger patterns: "whenever", "when", "at the beginning"
- Effect patterns: "create", "destroy", "exile", "return"

**Algorithm**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_tfidf_features(cards):
    """
    Create TF-IDF embeddings for deck cards.

    Returns:
        dict: {
            'card_vectors': np.ndarray,  # TF-IDF vectors per card
            'deck_centroid': np.ndarray,  # Average deck vector
            'variance': float,  # How focused is the deck?
            'top_terms': [(term, weight), ...]  # Most important terms
        }
    """
    # Combine oracle text
    oracle_texts = [card.get('oracle_text', '') for card in cards]

    # TF-IDF vectorization with MTG-specific stop words
    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 3),  # Capture phrases like "sacrifice a creature"
        stop_words=MTG_STOP_WORDS  # Filter generic words
    )

    card_vectors = vectorizer.fit_transform(oracle_texts)

    # Deck centroid (average card vector)
    deck_centroid = card_vectors.mean(axis=0)

    # Get top terms
    feature_names = vectorizer.get_feature_names_out()
    top_indices = deck_centroid.argsort()[-20:][::-1]
    top_terms = [(feature_names[i], deck_centroid[i]) for i in top_indices]

    return {
        'card_vectors': card_vectors,
        'deck_centroid': deck_centroid,
        'top_terms': top_terms
    }
```

#### Signal 3: Functional Role Distribution
**What we have**: Card roles already assigned (from `src/utils/card_roles.py`)

**Mathematical representation**:
```
R = {role₁: n₁, role₂: n₂, ..., roleₖ: nₖ}

Normalized distribution:
P(role_i) = n_i / Σn_j

Shannon entropy (diversity):
H(R) = -Σ P(role_i) log₂ P(role_i)
```

**Metrics**:
1. **Role concentration** - Is deck focused or diverse?
2. **Primary roles** - Which roles dominate?
3. **Role ratios** - Classic deck building ratios

**Algorithm**:
```python
def extract_role_features(cards):
    """
    Analyze functional role distribution.

    Returns:
        dict: {
            'role_distribution': {role: count},
            'entropy': float,  # Role diversity (0=focused, high=diverse)
            'primary_roles': [(role, count), ...],
            'creature_spell_ratio': float
        }
    """
    role_counts = Counter()
    for card in cards:
        roles = card.get('roles', [])
        for role in roles:
            role_counts[role] += 1

    # Calculate entropy (diversity measure)
    total = sum(role_counts.values())
    probs = [count/total for count in role_counts.values()]
    entropy = -sum(p * np.log2(p) for p in probs if p > 0)

    return {
        'role_distribution': dict(role_counts),
        'entropy': entropy,
        'primary_roles': role_counts.most_common(5)
    }
```

---

### Phase 2: Archetype Classification (Optimization-Based)

#### Approach 1: Supervised Learning (Initial Recommendation)

**Training Data**: Use known deck archetypes
- Collect example decks from EDHREC, archidekt
- Label each with archetype
- Extract features (Signals 1-3)
- Train classifier

**Model Options**:
1. **Random Forest** - Handles non-linear relationships, feature importance
2. **XGBoost** - Better accuracy, handles imbalanced classes
3. **Neural Network** - Can learn complex patterns

**Algorithm**:
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

def train_archetype_classifier(training_decks, labels):
    """
    Train supervised classifier for archetype detection.

    Parameters:
        training_decks: List of deck dictionaries with features
        labels: List of archetype labels (Aristocrats, Tokens, etc.)

    Returns:
        trained_model: Classifier ready for prediction
        feature_importance: Which features matter most
    """
    # Extract features for each deck
    X = []
    for deck in training_decks:
        features = combine_all_signals(deck)
        X.append(features)

    X = np.array(X)
    y = np.array(labels)

    # Random Forest with class weights (handle imbalanced data)
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        class_weight='balanced',
        random_state=42
    )

    # Cross-validation
    scores = cross_val_score(clf, X, y, cv=5)
    print(f"Cross-val accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

    # Train on all data
    clf.fit(X, y)

    # Feature importance
    feature_importance = dict(zip(feature_names, clf.feature_importances_))

    return clf, feature_importance

def combine_all_signals(deck):
    """Combine all feature signals into single vector."""
    features = []

    # Signal 1: Synergy graph features
    synergy_feats = extract_synergy_features(deck['synergies'])
    features.extend(synergy_feats['synergy_vector'])
    features.append(synergy_feats['modularity'])

    # Signal 2: TF-IDF features
    tfidf_feats = extract_tfidf_features(deck['cards'])
    features.extend(tfidf_feats['deck_centroid'].toarray()[0])

    # Signal 3: Role features
    role_feats = extract_role_features(deck['cards'])
    features.append(role_feats['entropy'])
    features.extend([role_feats['role_distribution'].get(role, 0)
                     for role in STANDARD_ROLES])

    return np.array(features)
```

#### Approach 2: Unsupervised Learning (Fallback)

**When to use**: No labeled training data available

**Method**: Cluster decks, then interpret clusters

**Algorithm**:
```python
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

def unsupervised_archetype_detection(decks, n_clusters=8):
    """
    Cluster decks without labels, infer archetypes from clusters.

    Returns:
        cluster_assignments: Which cluster each deck belongs to
        cluster_characteristics: Top features per cluster
    """
    # Extract features for all decks
    X = np.array([combine_all_signals(deck) for deck in decks])

    # Hierarchical clustering (more interpretable than k-means)
    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage='ward'  # Minimize variance within clusters
    )

    labels = clustering.fit_predict(X)

    # Analyze each cluster
    cluster_characteristics = {}
    for cluster_id in range(n_clusters):
        cluster_decks = [decks[i] for i in range(len(decks)) if labels[i] == cluster_id]

        # Find common characteristics
        common_synergies = find_common_synergies(cluster_decks)
        common_terms = find_common_tfidf_terms(cluster_decks)
        common_roles = find_common_roles(cluster_decks)

        cluster_characteristics[cluster_id] = {
            'synergies': common_synergies,
            'terms': common_terms,
            'roles': common_roles,
            'inferred_archetype': infer_archetype_from_features(
                common_synergies, common_terms, common_roles
            )
        }

    return labels, cluster_characteristics
```

#### Approach 3: Hybrid Template Matching (Immediate Solution)

**Use synergies + TF-IDF to match against archetype templates**

**Algorithm**:
```python
def hybrid_archetype_detection(deck):
    """
    Match deck against archetype templates using multiple signals.
    Uses cosine similarity and weighted scoring.

    Returns:
        {
            'primary_archetype': str,
            'confidence': float (0-1),
            'scores': {archetype: score},
            'reasoning': str
        }
    """
    # Define archetype templates
    ARCHETYPE_TEMPLATES = {
        'Aristocrats': {
            'required_synergies': ['death_trigger_synergy', 'sacrifice_synergy'],
            'required_terms': ['sacrifice', 'dies', 'death trigger'],
            'required_roles': ['Sacrifice Outlet', 'Death Trigger'],
            'min_synergy_count': 10,  # Must have at least 10 relevant synergies
            'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
        },
        'Tokens': {
            'required_synergies': ['token_synergy', 'go_wide_synergy'],
            'required_terms': ['create.*token', 'token.*creature'],
            'required_roles': ['Token Generator', 'Token Doubler'],
            'min_synergy_count': 8,
            'weights': {'synergies': 0.5, 'tfidf': 0.3, 'roles': 0.2}
        },
        # ... other archetypes
    }

    # Extract all features
    synergy_feats = extract_synergy_features(deck['synergies'])
    tfidf_feats = extract_tfidf_features(deck['cards'])
    role_feats = extract_role_features(deck['cards'])

    # Score against each template
    scores = {}
    for archetype, template in ARCHETYPE_TEMPLATES.items():
        # Score 1: Synergy matching
        synergy_score = calculate_synergy_match_score(
            synergy_feats['synergy_vector'],
            template['required_synergies']
        )

        # Score 2: TF-IDF term matching
        tfidf_score = calculate_tfidf_match_score(
            tfidf_feats['top_terms'],
            template['required_terms']
        )

        # Score 3: Role matching
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

        scores[archetype] = total_score

    # Get best match
    best_archetype = max(scores, key=scores.get)
    confidence = scores[best_archetype]

    # Require minimum confidence
    if confidence < 0.3:
        return {
            'primary_archetype': 'Generic/Midrange',
            'confidence': 0.5,
            'scores': scores,
            'reasoning': 'No strong archetype match found'
        }

    return {
        'primary_archetype': best_archetype,
        'confidence': confidence,
        'scores': scores,
        'reasoning': generate_reasoning(best_archetype, synergy_feats, tfidf_feats, role_feats)
    }

def calculate_synergy_match_score(synergy_vector, required_synergies):
    """
    Calculate how well synergies match archetype requirements.
    Uses normalized counts.
    """
    total_relevant_synergies = sum(
        synergy_vector[cat]
        for cat in required_synergies
        if cat in synergy_vector
    )

    # Normalize by deck size (100 cards = ~4950 possible pairs)
    normalized_score = min(1.0, total_relevant_synergies / 20)

    return normalized_score

def calculate_tfidf_match_score(top_terms, required_terms):
    """
    Calculate how well top TF-IDF terms match archetype keywords.
    Uses regex matching and weighted by TF-IDF score.
    """
    import re

    total_match_weight = 0.0
    top_term_weight = sum(weight for term, weight in top_terms[:20])

    for term, weight in top_terms[:20]:
        for required_pattern in required_terms:
            if re.search(required_pattern, term, re.IGNORECASE):
                total_match_weight += weight
                break

    # Normalize by total weight of top terms
    if top_term_weight > 0:
        return total_match_weight / top_term_weight
    return 0.0

def calculate_role_match_score(role_distribution, required_roles):
    """
    Calculate how well role distribution matches archetype.
    """
    total_role_cards = sum(role_distribution.values())
    relevant_role_cards = sum(
        role_distribution.get(role, 0)
        for role in required_roles
    )

    if total_role_cards > 0:
        return relevant_role_cards / total_role_cards
    return 0.0
```

---

### Phase 3: Priority Score Optimization

**Goal**: Convert archetype detection into AI priority scores

**Mathematical formulation**:
```
For each card c in deck:
    priority(c) = base_priority(c) + Σ archetype_bonus(c, archetype_i, weight_i)

where:
    archetype_bonus(c, A, w) = w × relevance(c, A)
    relevance(c, A) = how important card c is to archetype A

Optimization objective:
    Maximize: game_outcome = f(priority_sequence)
    Subject to: priority scores ∈ [0, 1000]
```

**Algorithm**:
```python
def optimize_priorities(deck, detected_archetypes):
    """
    Generate optimal priority scores based on detected archetypes.

    Uses linear combination with learned weights.
    """
    priorities = {}

    for card in deck['cards']:
        base_score = calculate_base_score(card)

        # Add archetype-specific bonuses
        archetype_bonuses = 0
        for archetype, weight in detected_archetypes['scores'].items():
            if weight > 0.3:  # Only use confident matches
                bonus = calculate_archetype_relevance(card, archetype)
                archetype_bonuses += bonus * weight

        priorities[card['name']] = base_score + archetype_bonuses

    # Normalize to [0, 1000] range
    max_priority = max(priorities.values())
    if max_priority > 0:
        priorities = {k: (v/max_priority)*1000 for k, v in priorities.items()}

    return priorities

def calculate_archetype_relevance(card, archetype):
    """
    How relevant is this card to the archetype?

    Uses synergy centrality + role matching.
    """
    relevance = 0.0

    # Check if card has archetype-specific roles
    card_roles = card.get('roles', [])
    archetype_roles = ARCHETYPE_TEMPLATES[archetype]['required_roles']

    role_overlap = len(set(card_roles) & set(archetype_roles))
    relevance += role_overlap * 100

    # Check if card participates in archetype synergies
    oracle = card.get('oracle_text', '').lower()
    for term in ARCHETYPE_TEMPLATES[archetype]['required_terms']:
        if re.search(term, oracle):
            relevance += 50

    return relevance
```

---

## 📊 Phase 4: Validation & Testing

### Statistical Validation

**Metrics to track**:
1. **Classification accuracy** (if using supervised learning)
2. **Silhouette score** (cluster quality)
   ```
   s(i) = (b(i) - a(i)) / max(a(i), b(i))
   where:
     a(i) = avg distance to points in same cluster
     b(i) = avg distance to points in nearest cluster
   ```
3. **Modularity** (synergy graph clustering quality)
   ```
   Q = (1/2m) Σ[A_ij - (k_i × k_j)/2m] δ(c_i, c_j)
   ```

**Algorithm**:
```python
from sklearn.metrics import silhouette_score

def validate_archetype_detection(decks, predictions):
    """
    Validate archetype detection quality.
    """
    # Extract feature vectors
    X = np.array([combine_all_signals(deck) for deck in decks])

    # Silhouette score (higher = better clustering)
    silhouette = silhouette_score(X, predictions)

    # If we have ground truth labels
    if ground_truth_available:
        from sklearn.metrics import accuracy_score, confusion_matrix
        accuracy = accuracy_score(ground_truth, predictions)
        confusion = confusion_matrix(ground_truth, predictions)

        return {
            'accuracy': accuracy,
            'silhouette': silhouette,
            'confusion_matrix': confusion
        }

    return {
        'silhouette': silhouette,
        'quality': 'good' if silhouette > 0.5 else 'poor'
    }
```

---

## 🎯 Implementation Roadmap

### Immediate (Week 1): Hybrid Template Matching
✅ **Pros**: Uses existing data, mathematically sound, no training needed
✅ **Implementation**:
1. Extract synergy categories from existing synergy detection
2. Implement TF-IDF on oracle texts
3. Template matching with weighted scoring
4. Priority score generation

### Short-term (Week 2-3): Supervised Learning
✅ **Pros**: Most accurate if training data available
📋 **Requirements**:
1. Collect ~50-100 example decks per archetype from EDHREC
2. Label them
3. Train Random Forest classifier
4. Cross-validate

### Long-term (Month 2+): Graph Neural Networks
✅ **Pros**: Leverages synergy graph structure directly
📋 **Requirements**:
1. Implement GNN (Graph Convolutional Network)
2. Train on large dataset
3. End-to-end optimization

---

## 📈 Success Criteria

**Quantitative**:
- Silhouette score > 0.5
- Classification accuracy > 80% (if supervised)
- Modularity > 0.4 (for synergy clustering)

**Qualitative**:
- Detected archetypes make sense to players
- AI plays decks according to strategy
- Improved simulation accuracy for specialized decks

---

## 🔧 Required Libraries

```python
# Graph analysis
import networkx as nx
from networkx.algorithms import community

# Machine learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import silhouette_score

# Numerical
import numpy as np
import pandas as pd
from scipy.stats import entropy
```

---

## 📚 References

1. **Latent Dirichlet Allocation for MTG**: Finding Magic archetypes (Medium article)
2. **Graph Clustering**: Louvain algorithm, modularity maximization
3. **TF-IDF**: Standard text mining technique
4. **Random Forest**: Breiman, 2001 - ensemble learning method

---

**Next Steps**: Implement Phase 1 (Hybrid Template Matching) with mathematical rigor, then validate and iterate.
