# import os
# import pandas as pd
# import unicodedata
# import re
# import json

# os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# path = "data/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv"
# df = pd.read_csv(path, encoding="utf-8", low_memory=False)

# # Remove incomplete years
# df = df[~df["sitzung_jahr"].isin([2013, 2026])]

# # Normalize Unicode
# df["rede_text"] = df["rede_text"].dropna().apply(
#     lambda text: unicodedata.normalize("NFKC", text)
# )

# # Regex pattern for AI-related synonyms
# ki_synonyme_regex = [
#     r"(?i:künstliche\s+intelligenz)",
#     r"(?i:kuenstliche\s+intelligenz)",
#     r"(?i:artificial\s+intelligence)",
#     r"(?i:neural\s+networks?)",
#     r"(?<!\w)KI(?!\w)",
#     r"(?<!\w)AI(?!\w)",
#     r"(?<!\w)K\.I\.(?!\w)",
#     r"(?<!\w)A\.I\.(?!\w)",
# ]

# pattern_str = "(" + "|".join(ki_synonyme_regex) + ")"

# # Which terms matched the regex list?
# ki_variants_found = (
#     df["rede_text"]
#     .str.extractall(f"({pattern_str})", flags=re.IGNORECASE)[0]
#     .str.lower()
#     .drop_duplicates()
#     .sort_values()
#     .reset_index(drop=True)
# )

# print("AI-related terms found:")
# print(ki_variants_found)

# # Add boolean column for AI mentions
# df["ai_mention"] = df["rede_text"].str.contains(
#     pattern_str,
#     na=False,
#     regex=True
# )

# # Filter speeches containing AI-related terms
# df_ai = df[df["ai_mention"]]

# # Export full dataset
# output_path_all = "data/normalized_speeches_full.csv"
# df.to_csv(output_path_all, index=False, encoding="utf-8")

# # Export AI-related speeches only
# output_path_ai = "data/ai_related_speeches.csv"
# df_ai.to_csv(output_path_ai, index=False, encoding="utf-8")


# # Backup 

# df_ai_backup = pd.read_csv(path, encoding="utf-8", low_memory=False)

# # Addresses removed

# anrede_pattern = re.compile(
#     r"^(?:[^\u2013!]{0,50}\u2013\s*)?(?:[^!]{0,150}!\s*){1,3}",
#     re.IGNORECASE
# )

# df_ai["rede_text"] = df_ai["rede_text"].str.replace(anrede_pattern, "", regex=True)

# # remove thanks 

# dank_pattern = re.compile(
#     r"(?:Vielen\s+)?(?:Herzlichen|Besten|Vielen)\s+Dank\.?",
#     re.IGNORECASE
# )

# df_ai["rede_text"] = df_ai["rede_text"].str.replace(dank_pattern, "", regex=True)


# # Check about how much removed

# length_before = df_ai_backup["rede_text"].str.len()
# length_after = df_ai["rede_text"].str.len()

# difference = length_before - length_after

# print(difference.describe())
# print(f"\nSpeeches with >150 characters removed: {(difference > 150).sum()}")
# print(f"Speeches with >200 characters removed: {(difference > 200).sum()}")

# # --- descripitve statistics ---
# words = df_ai["rede_text"].str.split().str.len()

# print("\n=== Durchschnittliche Länge der KI-Reden (nach Bereinigung) ===")
# print(f"Wörter   – Mittelwert: {words.mean():.0f}, Median: {words.median():.0f}, SD: {words.std():.0f}")
# print(f"\nN Reden gesamt: {len(df_ai)}")

# # long_reden = df_ai.groupby("rede_nr").size()
# # print(long_reden[long_reden >= 3].describe())

# # Anzahl Wörter pro Rede berechnen (vor dem Chunking)
# rede_lengths = df_ai.groupby("rede_id")["rede_text"].apply(
#     lambda x: x.str.split().str.len().sum()
# )

# # Top 50 längste Reden
# top50 = rede_lengths.sort_values(ascending=False).head(50)

# print(top50)


# # --- descripitve statistics ---
# words = df_ai["rede_text"].str.split().str.len()

# print("\n=== Durchschnittliche Länge der KI-Reden (nach Bereinigung) ===")
# print(f"Wörter   – Mittelwert: {words.mean():.0f}, Median: {words.median():.0f}, SD: {words.std():.0f}")
# print(f"\nN Reden gesamt: {len(df_ai)}")

# rede_lengths = df_ai["rede_text"].str.split().str.len()

# top50 = df_ai.loc[rede_lengths.sort_values(ascending=False).head(50).index]

# print(top50[["rede_text"]])

# # Top 50 longest speeches (by word count)
# top50 = rede_lengths.sort_values(ascending=False).head(50)

# print(top50)

# word_counts = df_ai["rede_text"].str.split().apply(len)

# for threshold in [1500, 2000, 2500, 3000, 4000, 5000]:
#     n = (word_counts > threshold).sum()
#     print(f"> {threshold} Wörter: {n} Reden")



# # Export only Ai-related speeches after cleaning
# output_path_ai = "data/n_speeches_ai.csv"
# df_ai.to_csv(output_path_ai, index=False, encoding="utf-8")

# # =========================
# # Make chunks
# # =========================



# # chunk_words = 2000



# # def chunk_text_sentences(text, chunk_size=chunk_words):
# #     sentences = re.split(r'(?<=[.!?])\s+', text)
# #     chunks = []
# #     current_chunk = []
# #     current_len = 0
# #     for sent in sentences:
# #         sent_len = len(sent.split())
# #         if current_len + sent_len > chunk_size and current_chunk:
# #             chunks.append(" ".join(current_chunk))
# #             current_chunk = [sent]
# #             current_len = sent_len
# #         else:
# #             current_chunk.append(sent)
# #             current_len += sent_len
# #     if current_chunk:
# #         chunks.append(" ".join(current_chunk))
# #     return chunks

# # rows = []
# # for rede_nr, (_, row) in enumerate(df_ai.iterrows()):
# #     chunks = chunk_text_sentences(row["rede_text"])  # chunk_text_sentences, nicht chunk_text
# #     for chunk_nr, chunk in enumerate(chunks):
# #         rows.append({
# #             "rede_nr": rede_nr,
# #             "chunk_nr": chunk_nr,
# #             "chunk_id": f"{rede_nr}_{chunk_nr}",
# #             "chunk_text": chunk,
# #             "rede_id": row["rede_id"],
# #             "sitzung_jahr": row["sitzung_jahr"],
# #             "redner_fraktion": row["redner_fraktion"],
# #             "redner_rolle_lang": row["redner_rolle_lang"],
# #         })

# # df_ai = pd.DataFrame(rows)
# # # Filter chunks without AI mention
# # df_ai = df_ai[df_ai["chunk_text"].str.contains(pattern_str, na=False, regex=True)]

# # print(f"Speeches:  {rede_nr + 1}")
# # print(f"Chunks: {len(df_ai)}")

# # df_ai = pd.DataFrame(rows)

# # Save data set

# # output_path_ai_chunked = "data/n_chunks_ai.csv"
# # df_ai.to_csv(output_path_ai_chunked, index=False, encoding="utf-8")

# # with open("data/chunk_size.json", "w") as f:
# #     json.dump({"chunk_words": chunk_words}, f)


# # =========================
# # Make chunks
# # =========================
# CONTEXT_WORDS = 1000

# def extract_ki_context(text, pattern, context_words=CONTEXT_WORDS):
#     words = text.split()
#     if len(words) <= 2 * context_words:
#         return text
    
#     # Find all KI mentions in full text and map to word positions
#     ki_positions = []
#     for match in re.finditer(pattern, text, re.IGNORECASE):
#         # Count words before match start
#         word_pos = len(text[:match.start()].split())
#         ki_positions.append(word_pos)
    
#     if not ki_positions:
#         return text
    
#     intervals = []
#     for pos in ki_positions:
#         start = max(0, pos - context_words)
#         end = min(len(words), pos + context_words)
#         intervals.append((start, end))
    
#     merged = [intervals[0]]
#     for start, end in intervals[1:]:
#         if start <= merged[-1][1]:
#             merged[-1] = (merged[-1][0], max(merged[-1][1], end))
#         else:
#             merged.append((start, end))
    
#     chunks = [" ".join(words[s:e]) for s, e in merged]
#     return " ".join(chunks)


# rows = []
# for rede_nr, (_, row) in enumerate(df_ai.iterrows()):
#     chunk_text = extract_ki_context(row["rede_text"], pattern_str)
#     rows.append({
#         "rede_nr": rede_nr,
#         "chunk_nr": 0,
#         "chunk_id": f"{rede_nr}_0",
#         "chunk_text": chunk_text,
#         "rede_id": row["rede_id"],
#         "sitzung_jahr": row["sitzung_jahr"],
#         "redner_fraktion": row["redner_fraktion"],
#         "redner_rolle_lang": row["redner_rolle_lang"],
#     })

# df_ai = pd.DataFrame(rows)

# print(f"Speeches:  {rede_nr + 1}")
# print(f"Chunks: {len(df_ai)}")


# #========================
# # Save data set
# #========================

# output_path_ai_chunked = "data/n_chunks_ai.csv"
# df_ai.to_csv(output_path_ai_chunked, index=False, encoding="utf-8")

# with open("data/chunk_size.json", "w") as f:
#     json.dump({"context_words": CONTEXT_WORDS}, f)

# # =========================
# # Checks
# # =========================

# # 1. Alle Chunks haben KI-Bezug
# ki_check = df_ai["chunk_text"].str.contains(pattern_str, na=False, regex=True)
# print(f"Chunks mit KI-Bezug: {ki_check.sum()} von {len(df_ai)}")

# # 2. Längenverteilung der Chunks
# word_counts = df_ai["chunk_text"].str.split().apply(len)
# print(f"\nChunk-Längen:")
# print(f"Mean: {word_counts.mean():.0f}, Median: {word_counts.median():.0f}, Max: {word_counts.max()}")

# # 3. Prüfe eine lange Rede ob Kontext korrekt extrahiert wurde
# long_rede = word_counts.idxmax()
# print(f"\nLängster Chunk (rede_nr {df_ai.loc[long_rede, 'rede_nr']}):")
# print(f"Wörter: {word_counts[long_rede]}")
# print(
#     f"KI-Bezug: {bool(re.search(pattern_str, df_ai.loc[long_rede, 'chunk_text'], re.IGNORECASE))}"
# )


import os
import pandas as pd
import unicodedata
import re
import json

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

path = "data/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv"
df = pd.read_csv(path, encoding="utf-8", low_memory=False)

# =========================
# CLEANING 
# =========================

def clean_text(text):
    if pd.isna(text):
        return text

    text = unicodedata.normalize("NFKC", text)

    # remove all unicode whitespace variants
    text = re.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000]", " ", text)

    # collapse ALL whitespace (THIS FIXES YOUR INDENTATION BUG)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


df = df.dropna(subset=["rede_text"])
df["rede_text"] = df["rede_text"].apply(clean_text)

# =========================
# Remove incomplete years
# =========================
df = df[~df["sitzung_jahr"].isin([2013, 2026])]

# =========================
# Regex pattern for AI-related synonyms
# =========================
ki_synonyme_regex = [
    r"(?i:künstliche\s+intelligenz)",
    r"(?i:kuenstliche\s+intelligenz)",
    r"(?i:artificial\s+intelligence)",
    r"(?i:neural\s+networks?)",
    r"(?<!\w)KI(?!\w)",
    r"(?<!\w)AI(?!\w)",
    r"(?<!\w)K\.I\.(?!\w)",
    r"(?<!\w)A\.I\.(?!\w)",
]

pattern_str = "(" + "|".join(ki_synonyme_regex) + ")"

# =========================
# AI detection
# =========================
ki_variants_found = (
    df["rede_text"]
    .str.extractall(pattern_str, flags=re.IGNORECASE)[0]
    .str.lower()
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)

print("AI-related terms found:")
print(ki_variants_found)

df["ai_mention"] = df["rede_text"].str.contains(
    pattern_str,
    na=False,
    regex=True
)

df_ai = df[df["ai_mention"]]

# =========================
# Export raw
# =========================
df.to_csv("data/normalized_speeches_full.csv", index=False, encoding="utf-8")
df_ai.to_csv("data/ai_related_speeches.csv", index=False, encoding="utf-8")

# =========================
# Backup
# =========================
df_ai_backup = df_ai.copy()

# =========================
# Remove addresses / thanks
# =========================
anrede_pattern = re.compile(
    r"^(?:[^\u2013!]{0,50}\u2013\s*)?(?:[^!]{0,150}!\s*){1,3}",
    re.IGNORECASE
)

dank_pattern = re.compile(
    r"(?:Vielen\s+)?(?:Herzlichen|Besten|Vielen)\s+Dank\.?",
    re.IGNORECASE
)

df_ai["rede_text"] = df_ai["rede_text"].str.replace(anrede_pattern, "", regex=True)
df_ai["rede_text"] = df_ai["rede_text"].str.replace(dank_pattern, "", regex=True)

# =========================
# stats
# =========================
length_before = df_ai_backup["rede_text"].str.len()
length_after = df_ai["rede_text"].str.len()

difference = length_before - length_after

print(difference.describe())
print(f"Speeches >150 chars removed: {(difference > 150).sum()}")
print(f"Speeches >200 chars removed: {(difference > 200).sum()}")

words = df_ai["rede_text"].str.split().str.len()

print("\n=== KI-Reden Statistik ===")
print(f"Mittel: {words.mean():.0f}, Median: {words.median():.0f}, SD: {words.std():.0f}")

# =========================
# Chunking / Context extraction
# =========================

CONTEXT_WORDS = 1000

### grab numbers of truncations first

n_truncated = (df_ai["rede_text"].str.split().str.len() > 2 * CONTEXT_WORDS).sum()
print(f" N speeches will be truncated: {n_truncated}")



def extract_ki_context(text, pattern, context_words=CONTEXT_WORDS):
    words = text.split()

    if len(words) <= 2 * context_words:
        return text

    ki_positions = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        word_pos = len(text[:match.start()].split())
        ki_positions.append(word_pos)

    if not ki_positions:
        return text

    intervals = []
    for pos in ki_positions:
        start = max(0, pos - context_words)
        end = min(len(words), pos + context_words)
        intervals.append((start, end))

    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    chunks = [" ".join(words[s:e]) for s, e in merged]
    return " ".join(chunks)


rows = []
for i, (_, row) in enumerate(df_ai.iterrows()):
    chunk_text = extract_ki_context(row["rede_text"], pattern_str)

    rows.append({
        "rede_nr": i,
        "chunk_nr": 0,
        "chunk_id": f"{i}_0",
        "chunk_text": chunk_text,
        "rede_id": row["rede_id"],
        "sitzung_jahr": row["sitzung_jahr"],
        "sitzung_datum": row.get("sitzung_datum"),
        "wahlperiode": row["wahlperiode"],
        "redner_fraktion": row["redner_fraktion"],
        "redner_rolle_lang": row["redner_rolle_lang"],
    })

df_ai = pd.DataFrame(rows)

# =========================
# Save final
# =========================
df_ai.to_csv("data/n_chunks_ai.csv", index=False, encoding="utf-8")

with open("data/chunk_size.json", "w") as f:
    json.dump({
        "context_words": CONTEXT_WORDS,
        "n_truncated": int(n_truncated)
    }, f)

# =========================
# Checks
# =========================
ki_check = df_ai["chunk_text"].str.contains(pattern_str, na=False, regex=True)

print(f"Chunks mit KI-Bezug: {ki_check.sum()} / {len(df_ai)}")

word_counts = df_ai["chunk_text"].str.split().apply(len)

print(f"Mean: {word_counts.mean():.0f}, Median: {word_counts.median():.0f}, Max: {word_counts.max()}")

print("\nDone.")