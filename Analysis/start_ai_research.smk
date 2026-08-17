from pathlib import Path

PROJECT_ROOT = Path(workflow.basedir)
PYTHON       = PROJECT_ROOT / ".venv" / "bin" / "python"


rule all:
    input:
        "Plots/ai_trend.png",
        "Plots/ai_trend_relative.png",
        "Plots/temporal_dynamics_ai_topics_line.png",
        "Plots/temporal_dynamics_ai_topics.png",
        "Plots/ai_topics_group_heatmap.png",
        "data/descriptive.csv",
        "models/topic_model",
        "models/embeddings_qwen3_06b.npy",
        "data/representative_docs_30.csv",
        "robustness/stability_per_run.csv",
        "robustness/pairwise_ari_nmi.csv",
        "robustness/min_cluster_size_sensitivity.csv",
        "robustness/n_neighbors_sensitivity.csv",
        "robustness/n_components_sensitivity.csv",
        str(PROJECT_ROOT.parent / "AI_parliament_paper" / "AI_parliament.pdf")

rule download_data:
    input:
        script = PROJECT_ROOT / "scripts" / "1_download_data.py"
    output:
        csv = "data/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv"
    log:
        "logs/download_data.log"
    shell:
        "{PYTHON} {input.script} 2>&1 | tee {log}"


rule data_preprocessing:
    input:
        csv    = "data/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv",
        script = PROJECT_ROOT / "scripts" / "2a_data_preprocessing.py"
    output:
        full   = "data/normalized_speeches_full.csv",
        ai     = "data/ai_related_speeches.csv",
        chunks = "data/n_chunks_ai.csv",
        ch_size= "data/chunk_size.json"
    log:
        "logs/data_preprocessing.log"
    shell:
        "{PYTHON} {input.script} 2>&1 | tee {log}"

rule topic_config:
    input:
        csv    = "data/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv",
        script = PROJECT_ROOT / "scripts" / "2b_topic_config.py"
    output:
        config = "models/main_model_config.json"
    log:
        "logs/topic_config.log"
    shell:
        "{PYTHON} {input.script} 2>&1 | tee {log}"


rule compute_embeddings:
    input:
        chunks = "data/n_chunks_ai.csv",
        script = PROJECT_ROOT / "scripts" / "3_embeddings.py"
    output:
        embeddings = "models/embeddings_qwen3_06b.npy"
    log:
       "logs/compute_embeddings.log"
    shell:
        "{PYTHON} {input.script} 2>&1 | tee {log}"


rule topic_model:
    input:
        chunks     = "data/n_chunks_ai.csv",
        embeddings = "models/embeddings_qwen3_06b.npy",
        config     = "models/main_model_config.json",
        script     = PROJECT_ROOT / "scripts" / "4a_topic_model.py"
    output:
        model       = "models/topic_model",
        rep_docs_30 = "data/representative_docs_30.csv",
        with_topics = "data/n_Reden_KI_with_topics.csv",
        hard        = "data/KI_topics_hard.csv",
        soft        = "data/KI_topics_soft.csv",
    log:
       "logs/topic_model.log"
    shell:
       "{PYTHON} {input.script} 2>&1 | tee {log}"

rule robustness_check:
    input:
        chunks     = "data/n_chunks_ai.csv",
        embeddings = "models/embeddings_qwen3_06b.npy",
        config     = "models/main_model_config.json",
        script     = PROJECT_ROOT / "scripts" / "4b_robustness_check.py"
    output:
        stability  = "robustness/stability_per_run.csv",
        pairwise   = "robustness/pairwise_ari_nmi.csv",
        min_clus   = "robustness/min_cluster_size_sensitivity.csv",
        n_neighb   = "robustness/n_neighbors_sensitivity.csv",
        n_comp     = "robustness/n_components_sensitivity.csv"
    log:
       "logs/robustness_check.log"
    shell:
        "{PYTHON} {input.script} 2>&1 | tee {log}"

rule analysis:
    input:
        full        = "data/normalized_speeches_full.csv",
        with_topics = "data/n_Reden_KI_with_topics.csv",
        script      = PROJECT_ROOT / "scripts" / "5_analysis.r"
    output:
        trend       = "Plots/ai_trend.png",
        trend_rel   = "Plots/ai_trend_relative.png",
        topics_line = "Plots/temporal_dynamics_ai_topics_line.png",
        topics_area = "Plots/temporal_dynamics_ai_topics.png",
        heatmap     = "Plots/ai_topics_group_heatmap.png",
        descriptive = "data/descriptive.csv"
    log:
        "logs/analysis.log"
    shell:
        "Rscript {input.script} > {log} 2>&1"


rule render_paper:
    input:
        plot_trend   = "Plots/ai_trend.png",
        plot_rel     = "Plots/ai_trend_relative.png",
        plot_line    = "Plots/temporal_dynamics_ai_topics_line.png",
        plot_area    = "Plots/temporal_dynamics_ai_topics.png",
        heatmap      = "Plots/ai_topics_group_heatmap.png",
        descriptive  = "data/descriptive.csv",
        chunk_size   = "data/chunk_size.json",
        topics       = "models/topic_model",
        rep_docs_30  = "data/representative_docs_30.csv",
        stability    = "robustness/stability_per_run.csv",
        min_clus     = "robustness/min_cluster_size_sensitivity.csv",
        n_neighb     = "robustness/n_neighbors_sensitivity.csv",
        n_comp       = "robustness/n_components_sensitivity.csv",
        qmd          = PROJECT_ROOT.parent / "AI_parliament_paper" / "AI_parliament.qmd",
        bibber       = PROJECT_ROOT.parent / "AI_parliament_paper" / "references.bib",
        script       = PROJECT_ROOT / "scripts" / "6_render_AI_paper.py"
    output:
        pdf = str(PROJECT_ROOT.parent / "AI_parliament_paper" / "AI_parliament.pdf")
    log:
        "logs/render_paper.log"
    shell:
        "{PYTHON} {input.script} > {log} 2>&1"
