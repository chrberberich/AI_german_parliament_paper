import os
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations

from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import nltk
from nltk.corpus import stopwords as nltk_stopwords

from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary

import json
# ============================================================
# Setup
# ============================================================

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import TopicModel config 

with open("models/main_model_config.json") as f:
    cfg = json.load(f)

umap_params = cfg["umap"]
hdbscan_params = cfg["hdbscan"]
vectorizer_params = cfg["vectorizer"]
bertopic_params = cfg["bertopic"]
custom_stopwords = cfg["custom_stopwords"]

vectorizer_params["ngram_range"] = tuple(vectorizer_params["ngram_range"])



Path("robustness").mkdir(parents=True, exist_ok=True)

# ============================================================
# Load data & embeddings (identical to main script)
# ============================================================

df_ai = pd.read_csv("data/n_chunks_ai.csv", encoding="utf-8", low_memory=False)
docs = df_ai["chunk_text"].tolist()

embeddings_path = "models/embeddings_qwen3_06b.npy"
print("Loading cached embeddings...")
embeddings = np.load(embeddings_path)

# ============================================================
# Stopwords (identical to main script)
# ============================================================

german_stopwords = set(nltk_stopwords.words("german"))

all_stopwords = list(german_stopwords.union(custom_stopwords))

# ============================================================
# Helper functions
# ============================================================

def get_topic_words(topic_model, top_n=10):
    """Returns list of top-N words per topic (excluding outlier topic -1)."""
    topic_words = []
    for topic_id in sorted(topic_model.get_topics().keys()):
        if topic_id == -1:
            continue
        words = [w for w, _ in topic_model.get_topic(topic_id)[:top_n]]
        if words:
            topic_words.append(words)
    return topic_words


def compute_coherence(topic_model, docs, top_n=10):
    """
    Computes CV coherence score via Gensim.
    Tokenization: simple whitespace split, consistent with CountVectorizer.
    """
    tokenized_docs = [doc.lower().split() for doc in docs]
    dictionary = Dictionary(tokenized_docs)
    topic_words = get_topic_words(topic_model, top_n=top_n)

    if len(topic_words) < 2:
        return np.nan  # coherence not meaningful with fewer than 2 topics

    coherence_model = CoherenceModel(
        topics=topic_words,
        texts=tokenized_docs,
        dictionary=dictionary,
        coherence="c_v",
    )
    return coherence_model.get_coherence()


def compute_diversity(topic_model, top_n=10):
    """
    Topic diversity: proportion of unique words across all topics.
    Range [0, 1] — higher values indicate less redundancy between topics.
    """
    topic_words = get_topic_words(topic_model, top_n=top_n)
    if not topic_words:
        return np.nan
    all_words = [w for words in topic_words for w in words]
    return len(set(all_words)) / len(all_words)


# ============================================================
# 1. STABILITY ANALYSIS — 20 runs with varying seeds
#    (UMAP seed varies, all hyperparameters fixed as in main script)
# ============================================================

N_RUNS = 20
SEEDS = range(N_RUNS)
TOP_N = 10  # top-N words for coherence and diversity

run_results = []
all_labels = []

print(f"\n{'='*50}")
print(f"Stability analysis: {N_RUNS} runs")
print(f"{'='*50}")

for seed in SEEDS:
    print(f"Run {seed+1}/{N_RUNS} (seed={seed})...")

    umap_model = UMAP(
        **{**umap_params, "random_state": seed}
    )

    hdbscan_model = HDBSCAN(**hdbscan_params)

    vectorizer = CountVectorizer(
        **vectorizer_params,
        stop_words=all_stopwords,
    )

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        verbose=False,
    )


    topics, _ = topic_model.fit_transform(docs, embeddings)
    topic_model.reduce_topics(docs, nr_topics=bertopic_params["nr_topics"])
    topics = topic_model.topics_

    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    outlier_rate = sum(t == -1 for t in topics) / len(topics)
    coherence = compute_coherence(topic_model, docs, top_n=TOP_N)
    diversity = compute_diversity(topic_model, top_n=TOP_N)

    run_results.append({
        "seed": seed,
        "n_topics": n_topics,
        "outlier_rate": round(outlier_rate, 4),
        "coherence_cv": round(coherence, 4) if not np.isnan(coherence) else np.nan,
        "diversity": round(diversity, 4) if not np.isnan(diversity) else np.nan,
    })
    all_labels.append(topics)

    print(f"  -> Topics: {n_topics}, Outlier rate: {outlier_rate:.2%}, "
          f"Coherence: {coherence:.3f}, Diversity: {diversity:.3f}")

# ARI and NMI across all pairwise run combinations
aris = []
nmis = []

for i, j in combinations(range(N_RUNS), 2):
    aris.append(adjusted_rand_score(all_labels[i], all_labels[j]))
    nmis.append(normalized_mutual_info_score(all_labels[i], all_labels[j]))

# Save results
df_runs = pd.DataFrame(run_results)
df_runs.to_csv("robustness/stability_per_run.csv", index=False)

df_pairwise = pd.DataFrame({"ARI": aris, "NMI": nmis})
df_pairwise.to_csv("robustness/pairwise_ari_nmi.csv", index=False)

print(f"\n--- Stability results ---")
print(f"Topics:       M={df_runs['n_topics'].mean():.1f}, SD={df_runs['n_topics'].std():.2f}, "
      f"Range=[{df_runs['n_topics'].min()}, {df_runs['n_topics'].max()}]")
print(f"Outlier rate: M={df_runs['outlier_rate'].mean():.3f}, SD={df_runs['outlier_rate'].std():.4f}")
print(f"Coherence CV: M={df_runs['coherence_cv'].mean():.3f}, SD={df_runs['coherence_cv'].std():.4f}")
print(f"Diversity:    M={df_runs['diversity'].mean():.3f}, SD={df_runs['diversity'].std():.4f}")
print(f"ARI:          M={np.mean(aris):.3f}, SD={np.std(aris):.4f}")
print(f"NMI:          M={np.mean(nmis):.3f}, SD={np.std(nmis):.4f}")


# ============================================================
# 2. HYPERPARAMETER SENSITIVITY — min_cluster_size grid
#    (random_state fixed as in main script)
# ============================================================

MIN_CLUSTER_SIZES = [5, 10, 12, 15, 20, 30]

print(f"\n{'='*50}")
print(f"Hyperparameter sensitivity: min_cluster_size")
print(f"{'='*50}")

grid_results = []

for mcs in MIN_CLUSTER_SIZES:
    umap_model = UMAP(**umap_params) 
    hdbscan_model = HDBSCAN(
        **{**hdbscan_params, "min_cluster_size": mcs}
    )

    vectorizer = CountVectorizer(
    **{**vectorizer_params, "min_df": 1, "max_df": 1.0},
    stop_words=all_stopwords,
)

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        verbose=False,
    )

    topics, _ = topic_model.fit_transform(docs, embeddings)
    topic_model.reduce_topics(docs, nr_topics=bertopic_params["nr_topics"])
    topics = topic_model.topics_

    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    outlier_rate = sum(t == -1 for t in topics) / len(topics)
    coherence = compute_coherence(topic_model, docs, top_n=TOP_N)
    diversity = compute_diversity(topic_model, top_n=TOP_N)

    grid_results.append({
        "min_cluster_size": mcs,
        "n_topics": n_topics,
        "outlier_rate": round(outlier_rate, 4),
        "coherence_cv": round(coherence, 4) if not np.isnan(coherence) else np.nan,
        "diversity": round(diversity, 4) if not np.isnan(diversity) else np.nan,
        "is_main_model": mcs == hdbscan_params["min_cluster_size"],
    })

    print(f"  min_cluster_size={mcs:3d} -> Topics: {n_topics:3d}, Outlier: {outlier_rate:.2%}, "
          f"Coherence: {coherence:.3f}, Diversity: {diversity:.3f}"
          + (" <- main model" if mcs == hdbscan_params["min_cluster_size"] else ""))

df_grid = pd.DataFrame(grid_results)
df_grid.to_csv("robustness/min_cluster_size_sensitivity.csv", index=False)




# ============================================================
# 3. HYPERPARAMETER SENSITIVITY — n_neighbors grid
#    (min_cluster_size fixed as in main script)
# ============================================================
N_NEIGHBORS_LIST = [2, 5, 10, 12, 15, 30, 50]

print(f"\n{'='*50}")
print(f"Hyperparameter sensitivity: n_neighbors (UMAP)")
print(f"{'='*50}")

neighbor_results = []

for nn in N_NEIGHBORS_LIST:
    # Initialize UMAP with the current n_neighbors value
    # This controls the balance between local and global structure
    umap_model = UMAP(
        **{**umap_params, "n_neighbors": nn}
    )
    
    # Use fixed HDBSCAN and Vectorizer parameters from main config
    hdbscan_model = HDBSCAN(**hdbscan_params)
    
    vectorizer = CountVectorizer(
    **{**vectorizer_params, "min_df": 1, "max_df": 1.0},
    stop_words=all_stopwords,
)

    
    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        verbose=False,
    )
    
    topics, _ = topic_model.fit_transform(docs, embeddings)
    topic_model.reduce_topics(docs, nr_topics=bertopic_params["nr_topics"])
    topics = topic_model.topics_
    
    # Calculate metrics for robustness evaluation
    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    outlier_rate = sum(t == -1 for t in topics) / len(topics)
    coherence = compute_coherence(topic_model, docs, top_n=TOP_N)
    diversity = compute_diversity(topic_model, top_n=TOP_N)
    
    neighbor_results.append({
        "n_neighbors": nn,
        "n_topics": n_topics,
        "outlier_rate": round(outlier_rate, 4),
        "coherence_cv": round(coherence, 4) if not np.isnan(coherence) else np.nan,
        "diversity": round(diversity, 4) if not np.isnan(diversity) else np.nan,
        "is_main_model": nn == umap_params["n_neighbors"],
    })
    
    print(f"  n_neighbors={nn:3d} -> Topics: {n_topics:3d}, Outlier: {outlier_rate:.2%}, "
          f"Coherence: {coherence:.3f}, Diversity: {diversity:.3f}"
          + (" <- main model" if nn == umap_params["n_neighbors"] else ""))

# Convert results to DataFrame and export to CSV
df_neighbors = pd.DataFrame(neighbor_results)
df_neighbors.to_csv("robustness/n_neighbors_sensitivity.csv", index=False)

# ============================================================
# 4. HYPERPARAMETER SENSITIVITY — n_components grid
#    (n_neighbors and min_cluster_size fixed as in main script)
# ============================================================
N_COMPONENTS_LIST = [2, 5, 10, 12, 15, 20]

print(f"\n{'='*50}")
print(f"Hyperparameter sensitivity: n_components (UMAP)")
print(f"{'='*50}")

components_results = []

for nc in N_COMPONENTS_LIST:
    umap_model = UMAP(
        **{**umap_params, "n_components": nc}
    )

    hdbscan_model = HDBSCAN(**hdbscan_params)
    
    vectorizer = CountVectorizer(
    **{**vectorizer_params, "min_df": 1, "max_df": 1.0},
    stop_words=all_stopwords,
)

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        verbose=False,
    )

    topics, _ = topic_model.fit_transform(docs, embeddings)
    topic_model.reduce_topics(docs, nr_topics=bertopic_params["nr_topics"])
    topics = topic_model.topics_

    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    outlier_rate = sum(t == -1 for t in topics) / len(topics)
    coherence = compute_coherence(topic_model, docs, top_n=TOP_N)
    diversity = compute_diversity(topic_model, top_n=TOP_N)

    components_results.append({
        "n_components": nc,
        "n_topics": n_topics,
        "outlier_rate": round(outlier_rate, 4),
        "coherence_cv": round(coherence, 4) if not np.isnan(coherence) else np.nan,
        "diversity": round(diversity, 4) if not np.isnan(diversity) else np.nan,
        "is_main_model": nc == umap_params["n_components"],
    })

    print(f"  n_components={nc:3d} -> Topics: {n_topics:3d}, Outlier: {outlier_rate:.2%}, "
          f"Coherence: {coherence:.3f}, Diversity: {diversity:.3f}"
          + (" <- main model" if nc == umap_params["n_components"] else ""))

df_components = pd.DataFrame(components_results)
df_components.to_csv("robustness/n_components_sensitivity.csv", index=False)

# ============================================================
# 5. SUMMARY — ready for paper reporting
# ============================================================

print(f"""
Stability analysis ({N_RUNS} runs, seeds {min(SEEDS)}–{max(SEEDS)}):
  Number of topics: M = {df_runs['n_topics'].mean():.1f} (SD = {df_runs['n_topics'].std():.2f})
  Outlier rate:     M = {df_runs['outlier_rate'].mean():.3f} (SD = {df_runs['outlier_rate'].std():.4f})
  Coherence CV:     M = {df_runs['coherence_cv'].mean():.3f} (SD = {df_runs['coherence_cv'].std():.4f})
  Diversity:        M = {df_runs['diversity'].mean():.3f} (SD = {df_runs['diversity'].std():.4f})
  ARI:              M = {np.mean(aris):.3f} (SD = {np.std(aris):.4f})
  NMI:              M = {np.mean(nmis):.3f} (SD = {np.std(nmis):.4f})

Hyperparameter sensitivity (min_cluster_size):
{df_grid[['min_cluster_size', 'n_topics', 'outlier_rate', 'coherence_cv', 'diversity', 'is_main_model']].to_string(index=False)}

Hyperparameter sensitivity (n_neighbors):
{df_neighbors[['n_neighbors', 'n_topics', 'outlier_rate', 'coherence_cv', 'diversity', 'is_main_model']].to_string(index=False)}

Hyperparameter sensitivity (n_components):
{df_components[['n_components', 'n_topics', 'outlier_rate', 'coherence_cv', 'diversity', 'is_main_model']].to_string(index=False)}

Saved files:
  robustness/stability_per_run.csv
  robustness/pairwise_ari_nmi.csv
  robustness/min_cluster_size_sensitivity.csv
  robustness/n_neighbors_sensitivity.csv
  robustness/n_components_sensitivity.csv
""")
