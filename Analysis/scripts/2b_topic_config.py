import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# best for 400er E5 und bge-M3, eventuel qwen 0.6

# umap_params = {
#     "n_neighbors": 10,
#     "n_components": 5,
#     "min_dist": 0.0,
#     "random_state": 123,
# }

# qwen 0.6b
# 42

umap_params = {
    "n_neighbors": 12, #15
    "n_components": 12, #15
    "min_dist": 0.0,
    "random_state": 123,
}

# umap_params = {
#     "n_neighbors": 10,
#     "n_components": 15,
#     "min_dist": 0.0,
#     "random_state": 123,
# }



hdbscan_params = {
    "min_cluster_size": 12,  #10
    "min_samples": 2,
    "cluster_selection_method": "eom",
}

# 42
vectorizer_params = {
    "ngram_range": [1, 1],
    "min_df": 3,
}

bertopic_params = {
    "nr_topics": 15,
}

custom_stopwords = [
     "ampel", "deutschland", "mehr", "müssen", "verfahren", "kollegen", "heute", "schon", "dafür",
    "bundeskanzler", "menschen", "geht", "ja", "liebe", "herr","damen", "herren", "deshalb",  
    "ganz", "milliarden", "danke", "aufmerksamkeit", "mal", "mehrheit", "bundestag", "land",
    "sagen", "sage", "drei", "immer", "europäischen", "gemeinsam", "endlich", "antrag", "brauchen",
    "jahren", "lassen", "gute", "afd", "cdu", "csu", "fraktionen", "koalition", "bündnis", "90",
    "bringen", "tun", "kolleginnen", "deutschen", "co", "wort", "regierung", 
    "karliczek", "scholz", "sowie", "sicherlich", "schön", "woche", "kollege", "ende", "altmaier",
    "unserer", "mitte", "gibt", "freue", "frau", "thema", "jahr", "geben", "machen", "wildberger",
    "fdp", "setzen", "sinne", "prozent", "bedanke", "bitte", "gut", "wer", "fraktion", "stimmt",
    "spd", "verantwortung", "19", "23", "stimmen", "grünen", "möchte", "letzten", "februar", 
    "landes", "bürgerinnen", "federführung", "nächsten", "wissen", "tag", "weihnachten", "digitalen",
    "ansatz","meldungen", "bundesregierung",
]

with open("models/main_model_config.json", "w") as f:
    json.dump({
        "umap": umap_params,
        "hdbscan": hdbscan_params,
        "custom_stopwords": custom_stopwords,
        "bertopic": bertopic_params,
        "vectorizer": vectorizer_params,
    }, f, indent=2)