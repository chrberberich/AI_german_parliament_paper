"""
compute_embeddings.py
---------------------
Computes and caches sentence embeddings for the AI chunks dataset.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import sys
import torch

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

path = "data/n_chunks_ai.csv"
df_ai = pd.read_csv(path, encoding="utf-8", low_memory=False)
docs = df_ai["chunk_text"].tolist()


embeddings_path = Path("models/embeddings_qwen3_06b.npy")

if embeddings_path.exists():
    answer = input("Embeddings already exist, but input changed. Recompute? [y/n]: ").strip().lower()
    if answer != "y":
        print("Skipping recomputation.")
        sys.exit(0)




# embedding_model = SentenceTransformer("BAAI/bge-m3")
embedding_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
# print("Computing embeddings...")
# embeddings = embedding_model.encode(
#     docs,
#     show_progress_bar=True,
#     normalize_embeddings=True,
#     prompt="Instruct: Represent this parliamentary speech chunk for topic clustering\nQuery: "  
# )

# embeddings_path = Path("models/embeddings_e5_large.npy")
# embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")

print("Computing embeddings...")

embeddings = embedding_model.encode(
    docs,
    show_progress_bar=True,
    normalize_embeddings=True,
    batch_size=1
)

np.save(embeddings_path, embeddings)
print(f"Saved embeddings to {embeddings_path}.")

del embedding_model
#torch müsste man auskommentieren könen?
torch.cuda.empty_cache()
