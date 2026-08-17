import os
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords as nltk_stopwords
import json

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load model config
with open("models/main_model_config.json") as f:
    cfg = json.load(f)

umap_params = cfg["umap"]
hdbscan_params = cfg["hdbscan"]
vectorizer_params = cfg["vectorizer"]
bertopic_params = cfg["bertopic"]
custom_stopwords = cfg["custom_stopwords"]

vectorizer_params["ngram_range"] = tuple(vectorizer_params["ngram_range"])

# Load data and embeddings
path = "data/n_chunks_ai.csv"
df_ai = pd.read_csv(path, encoding="utf-8", low_memory=False)

embedding_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
# embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
# embeddings = np.load("models/embeddings_e5_large.npy")
embeddings = np.load("models/embeddings_qwen3_06b.npy")
print("Embeddings loaded.")

german_stopwords = set(nltk_stopwords.words("german"))
all_stopwords = list(german_stopwords.union(custom_stopwords))

umap_model = UMAP(**umap_params)
hdbscan_model = HDBSCAN(**hdbscan_params)

vectorizer = CountVectorizer(
    **vectorizer_params,
    stop_words=all_stopwords,
)

topic_model = BERTopic(
    embedding_model=embedding_model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer,
    verbose=True,
)

docs = df_ai["chunk_text"].tolist()

# Fit model
topics, probs = topic_model.fit_transform(docs, embeddings)

# Reduce topics to target number
topic_model.reduce_topics(docs, nr_topics=bertopic_params["nr_topics"])

# Assign topics to chunks
df_ai["topic"] = topic_model.topics_

# =========================
# Define topic labels
# =========================
topic_model.set_topic_labels({
    -1: "Outlier",
    0: "Digitalization & Strategy",
    1: "Regulation & Governance",
    2: "Research Funding",
    3: "Economy & Key Technologies",
    4: "Europe & EU",
    5: "Free Speech & Freedom of Press",
    6: "Military & Drones",
    7: "Labor Market & Qualification",
    8: "Justice & the Rule of Law",
    9: "Internal Security & Surveillance",
    10: "Healthcare & Nursing",
    11: "Agriculture & Food",
    12: "Anti-Money Laundering",
    13: "Mobility & Infrastructure"
})

topic_labels = dict(zip(topic_model.get_topic_info()["Topic"],
                        topic_model.custom_labels_))

# Save model
topic_model.save("models/topic_model")
# =========================
# Extract representative docs for qualitative validation
# Re-extract with nr_repr_docs=30 using internal BERTopic method,
# since nr_repr_docs is not exposed as a constructor parameter in v0.17.4
# =========================
doc_topic = pd.DataFrame({
    "Topic": topic_model.topics_,
    "ID": range(len(topic_model.topics_)),
    "Document": docs
})

repr_docs, _, _, _ = topic_model._extract_representative_docs(
    topic_model.c_tf_idf_,
    doc_topic,
    topic_model.topic_representations_,
    nr_samples=500,
    nr_repr_docs=30
)

topic_model.representative_docs_ = repr_docs

topic_names = topic_model.get_topic_info().set_index("Topic")["Name"].to_dict()

text_to_jahr = df_ai.set_index("chunk_text")["sitzung_jahr"].to_dict()
text_to_fraktion = df_ai.set_index("chunk_text")["redner_fraktion"].to_dict()
text_to_rolle = df_ai.set_index("chunk_text")["redner_rolle_lang"].to_dict()
text_to_rede_nr = df_ai.set_index("chunk_text")["rede_nr"].to_dict()
text_to_chunk_id = df_ai.set_index("chunk_text")["chunk_id"].to_dict()

rows = []
for topic_id, chunks in repr_docs.items():
    for chunk in chunks:
        rows.append({
            "topic": topic_id,
            "topic_name": topic_names[topic_id],
            "topic_label": topic_labels[topic_id],
            "chunk_text": chunk,
            "chunk_id": text_to_chunk_id.get(chunk, None),
            "rede_nr": text_to_rede_nr.get(chunk, None),
            "sitzung_jahr": text_to_jahr.get(chunk, None),
            "redner_fraktion": text_to_fraktion.get(chunk, None),
            "redner_rolle_lang": text_to_rolle.get(chunk, None)
        })

# Update model attribute so representative_docs_ reflects the expanded set
topic_model.representative_docs_ = repr_docs

# Export representative docs to CSV for close reading and label validation


pd.DataFrame(rows).to_csv(
    "data/representative_docs_30.csv",
    index=False,
    encoding="utf-8"
)
print("Representative docs exported.")

# =========================
# Map topic labels to chunks
# =========================
topic_labels = dict(zip(topic_model.get_topic_info()["Topic"],
                        topic_model.custom_labels_))
df_ai["topic_label"] = df_ai["topic"].map(topic_labels)

# Export chunk-level data with topic assignments
df_ai.to_csv(
    "data/n_Reden_KI_with_topics.csv",
    index=False,
    encoding="utf-8"
)

# =========================
# Hard aggregation: assign each speech its modal topic
# =========================
df_hard = (
    df_ai[df_ai["topic"] != -1]
    .groupby("rede_nr")["topic"]
    .agg(lambda x: x.mode()[0])
    .reset_index()
    .rename(columns={"topic": "topic_hard"})
)

# =========================
# Soft aggregation: topic share distribution per speech
# =========================
df_soft = (
    df_ai[df_ai["topic"] != -1]
    .groupby(["rede_nr", "topic"])
    .size()
    .reset_index(name="count")
)

df_soft["topic_share"] = df_soft.groupby("rede_nr")["count"].transform(
    lambda x: x / x.sum()
)

df_soft_pivot = df_soft.pivot(
    index="rede_nr",
    columns="topic",
    values="topic_share"
).fillna(0).reset_index()

# Merge speech-level metadata
meta = (
    df_ai.groupby("rede_nr")
    .first()[["rede_id", "sitzung_jahr", "redner_fraktion"]]
    .reset_index()
)

df_hard = df_hard.merge(meta, on="rede_nr")
df_soft_full = df_soft_pivot.merge(meta, on="rede_nr")

# Save aggregated outputs
df_hard.to_csv("data/KI_topics_hard.csv", index=False, encoding="utf-8")
df_soft_full.to_csv("data/KI_topics_soft.csv", index=False, encoding="utf-8")

# =========================
# Checks
# =========================
print(topic_model.get_topic_info())

hierarchical_topics = topic_model.hierarchical_topics(docs)

fig = topic_model.visualize_hierarchy(
    hierarchical_topics=hierarchical_topics,
    custom_labels=True
)
fig.show()