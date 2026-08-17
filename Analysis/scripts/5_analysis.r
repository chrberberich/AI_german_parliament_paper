library(tidyverse)
library(scales)
library(zoo)
library(stringr)
library(glue)
library(slider)

# ── Colors ────────────────────────────────────────────────────────────────────
parteifarben <- c(
  "SPD"                   = "#E3000F",
  "CDU/CSU"               = "#000000",
  "BÜNDNIS 90/DIE GRÜNEN" = "#1AA037",
  "FDP"                   = "#FFEF00",
  "AfD"                   = "#0489DB",
  "DIE LINKE"             = "#BE3075",
  "Total"                = "#333333",
  "Government"             = "#888888"
)

EXCLUDE_FRAKTIONEN <- c("fraktionslos", "BSW")

# =============================================================================
# 1. Load and prepare half-year-handling datasets
# =============================================================================

parse_half_years <- function(data) {
  data |>
    mutate(
      session_date_parsed = ymd(sitzung_datum),
      month_extracted = month(session_date_parsed),
      half_year_numeric = sitzung_jahr + ifelse(month_extracted <= 6, 0.0, 0.5)
    ) |>
    filter(sitzung_jahr >= 2015 & sitzung_jahr <= 2025)
}

df_n <- read_csv(
  "data/normalized_speeches_full.csv",
  show_col_types = FALSE,
  col_types = cols(redner_id = col_character())
) |> parse_half_years()

ai_df_n <- read_csv(
  "data/n_speeches_ai.csv",
  show_col_types = FALSE,
  col_types = cols(redner_id = col_character())
) |> parse_half_years()

df_chunks <- read_csv(
  "data/n_chunks_ai.csv",
  show_col_types = FALSE
)

df <- read_csv(
  "data/n_Reden_KI_with_topics.csv",
  show_col_types = FALSE,
  col_types = cols(rede_id = col_character())
) |> parse_half_years()

# =============================================================================
# 2. Define topic colors
# =============================================================================
topic_levels <- sort(unique(df$topic_label))
other_topics <- topic_levels[topic_levels != "Outlier"]

topic_colors <- setNames(
  c(
    "grey70",
    scales::colour_ramp(
      c("#30123B", "#4777EF", "#1BD0D5", "#62FC6B", "#F5A11C", "#7A0403")
    )(seq(0, 1, length.out = length(other_topics)))
  ),
  c("Outlier", other_topics)
)

# =============================================================================
# 3. Absolute trend: AI mentions by parliamentary group and year
# =============================================================================
ki_trend <- df_n |>
  filter(ai_mention) |>
  count(redner_fraktion, sitzung_jahr, name = "anzahl_reden")

ki_Total <- df_n |>
  filter(ai_mention) |>
  count(sitzung_jahr, name = "anzahl_reden") |>
  mutate(redner_fraktion = "Total")

ki_plot <- bind_rows(ki_trend, ki_Total) |>
  filter(
    !redner_fraktion %in% EXCLUDE_FRAKTIONEN,
    sitzung_jahr < 2026
  )

p_abs <- ggplot(
  ki_plot,
  aes(
    x = sitzung_jahr,
    y = anzahl_reden,
    color = redner_fraktion,
    linetype = redner_fraktion,
    linewidth = redner_fraktion
  )
) +
  geom_line() +
  geom_vline(xintercept = 2018, linetype = "dotted", linewidth = 0.8) +
  geom_vline(xintercept = 2022, linetype = "dotted", linewidth = 0.8) +
  annotate(
    "text", x = 2018.15, y = Inf, label = "AI-Strategy",
    hjust = 0, vjust = 1.5, size = 3.5
  ) +
  annotate(
    "text", x = 2022.15, y = Inf, label = "ChatGPT",
    hjust = 0, vjust = 3.2, size = 3.5
  ) +
  scale_color_manual(values = parteifarben) +
  scale_linetype_manual(
    values = c(
      "Total" = "dashed",
      setNames(
        rep("solid", length(setdiff(names(parteifarben), "Total"))),
        setdiff(names(parteifarben), "Total")
      )
    )
  ) +
  scale_linewidth_manual(
    values = c(
      "Total" = 1.2,
      setNames(
        rep(0.8, length(setdiff(names(parteifarben), "Total"))),
        setdiff(names(parteifarben), "Total")
      )
    )
  ) +
  labs(
    title = "AI-mentions in Bundestag after parliamentary group",
    x = "Year",
    y = "Count speeches",
    color = NULL,
    linetype = NULL,
    linewidth = NULL
  ) +
  theme_minimal() +
  theme(legend.position = "right")

ggsave("Plots/ai_trend.png", p_abs, width = 12, height = 6, dpi = 300)

# =============================================================================
# 4. Relative trend: share of AI speeches in the full corpus
# =============================================================================
reden_Total <- df_n |>
  count(redner_fraktion, sitzung_jahr, name = "reden_Total")

reden_ki <- df_n |>
  filter(ai_mention) |>
  count(redner_fraktion, sitzung_jahr, name = "reden_ki")

ki_relativ <- reden_Total |>
  left_join(reden_ki, by = c("redner_fraktion", "sitzung_jahr")) |>
  mutate(
    redner_fraktion = coalesce(redner_fraktion, "Government"),
    reden_ki = replace_na(reden_ki, 0),
    anteil = reden_ki / reden_Total
  )

Total_relativ <- df_n |>
  count(sitzung_jahr, name = "reden_Total") |>
  left_join(
    df_n |> filter(ai_mention) |> count(sitzung_jahr, name = "reden_ki"),
    by = "sitzung_jahr"
  ) |>
  mutate(
    reden_ki = replace_na(reden_ki, 0),
    anteil = reden_ki / reden_Total,
    redner_fraktion = "Total"
  )

ki_plot_relativ <- bind_rows(ki_relativ, Total_relativ) |>
  filter(!redner_fraktion %in% EXCLUDE_FRAKTIONEN)

p_rel <- ggplot(
  ki_plot_relativ,
  aes(
    x = sitzung_jahr,
    y = anteil,
    color = redner_fraktion,
    linetype = redner_fraktion,
    linewidth = redner_fraktion
  )
) +
  geom_line() +
  geom_vline(xintercept = 2018, linetype = "dotted", linewidth = 0.8) +
  geom_vline(xintercept = 2022, linetype = "dotted", linewidth = 0.8) +
  annotate(
    "text", x = 2018.15, y = Inf, label = "AI-Strategy",
    hjust = 0, vjust = 1.5, size = 3.5
  ) +
  annotate(
    "text", x = 2022.15, y = Inf, label = "ChatGPT",
    hjust = 0, vjust = 3.2, size = 3.5
  ) +
  scale_color_manual(values = parteifarben) +
  scale_linetype_manual(
    values = c(
      "Total" = "dashed",
      setNames(
        rep("solid", length(setdiff(names(parteifarben), "Total"))),
        setdiff(names(parteifarben), "Total")
      )
    )
  ) +
  scale_linewidth_manual(
    values = c(
      "Total" = 1.2,
      setNames(
        rep(0.8, length(setdiff(names(parteifarben), "Total"))),
        setdiff(names(parteifarben), "Total")
      )
    )
  ) +
  scale_y_continuous(labels = percent_format(accuracy = 1)) +
  scale_x_continuous(
    breaks = seq(2015, 2025, by = 2),
    limits = c(2015, 2025)
  ) +
  labs(
    title = "Share of AI-mentions in Bundestag after parliamentary group",
    x = "Year",
    y = "Share of AI-mentions",
    color = NULL,
    linetype = NULL,
    linewidth = NULL
  ) +
  theme_minimal() +
  theme(legend.position = "right")

ggsave("Plots/ai_trend_relative.png", p_rel, width = 12, height = 6, dpi = 300)

# =============================================================================
# 5. Topic shares over time (Smoothed Line Plot based on Half-Years)
# =============================================================================
reden_Total_halfyear <- df_n |> count(half_year_numeric, name = "reden_Total")

topic_halfyear <- df |>
  count(half_year_numeric, topic_label, name = "count") |>
  complete(half_year_numeric = seq(min(half_year_numeric), max(half_year_numeric), by = 0.5), topic_label, fill = list(count = 0)) |>
  left_join(reden_Total_halfyear, by = "half_year_numeric") |>
  mutate(
    reden_Total = replace_na(reden_Total, 0),
    share = ifelse(reden_Total == 0, 0, count / reden_Total)
  )

topic_smooth <- topic_halfyear |>
  arrange(topic_label, half_year_numeric) |>
  group_by(topic_label) |>
  mutate(
    share_smooth = slider::slide_dbl(share, mean, .before = 2, .after = 2, .complete = FALSE)
  ) |>
  ungroup()

p_line <- ggplot(topic_smooth, aes(x = half_year_numeric, y = share_smooth, color = topic_label)) +
  geom_line(linewidth = 0.9) +
  scale_y_continuous(labels = percent_format(accuracy = 0.01)) +
  scale_x_continuous(breaks = seq(2015, 2025, by = 2), limits = c(2015, 2025.5)) +
  scale_color_manual(values = topic_colors) +
  labs(title = "Share of AI Topics within the AI Discourse (Half-Yearly Moving Average +2/-2)", x = "Year", y = "Share of AI-mentions", color = NULL) +
  theme_minimal() + theme(legend.position = "right")

ggsave("Plots/temporal_dynamics_ai_topics_line.png", p_line, width = 12, height = 6, dpi = 600)

# =============================================================================
# 5b. Topic trend without rolling mean (Raw Half-Year Data)
# =============================================================================
p_line_raw <- ggplot(topic_halfyear, aes(x = half_year_numeric, y = share, color = topic_label)) +
  geom_line(linewidth = 0.9) +
  scale_y_continuous(labels = percent_format(accuracy = 0.01)) +
  scale_x_continuous(breaks = seq(2015, 2025, by = 2), limits = c(2015, 2025.5)) +
  scale_color_manual(values = topic_colors) +
  labs(title = "Raw Half-Yearly Share of AI Topics within the AI Discourse", x = "Year", y = "Share of AI-mentions", color = NULL) +
  theme_minimal() + theme(legend.position = "right")

ggsave("Plots/topic_trend_no_rolling_mean.png", p_line_raw, width = 12, height = 6, dpi = 600)

# =============================================================================
# 6. Topic Shares by Parliamentary Group over Time (Stratified Facet Plot)
# =============================================================================
topic_halfyear_fraktion <- df |>
  filter(!redner_fraktion %in% EXCLUDE_FRAKTIONEN) |>
  count(half_year_numeric, redner_fraktion, topic_label, name = "count")

topic_fraktion_complete <- topic_halfyear_fraktion |>
  complete(
    half_year_numeric = seq(min(half_year_numeric), max(half_year_numeric), by = 0.5),
    nesting(redner_fraktion, topic_label),
    fill = list(count = 0)
  ) |>
  group_by(half_year_numeric, redner_fraktion) |>
  mutate(
    share = if(sum(count) == 0) 0 else count / sum(count)
  ) |>
  ungroup()

topic_fraktion_smooth <- topic_fraktion_complete |>
  arrange(redner_fraktion, topic_label, half_year_numeric) |>
  group_by(redner_fraktion, topic_label) |>
  mutate(
    share_smooth = slider::slide_dbl(share, mean, .before = 2, .after = 2, .complete = FALSE),
    share_smooth = replace_na(share_smooth, 0)
  ) |>
  ungroup()

fraktion_order_plots <- c("CDU/CSU", "SPD", "FDP", "BÜNDNIS 90/DIE GRÜNEN", "DIE LINKE", "AfD")

topic_fraktion_smooth <- topic_fraktion_smooth |>
  filter(redner_fraktion %in% fraktion_order_plots) |>
  mutate(redner_fraktion = factor(redner_fraktion, levels = fraktion_order_plots))

p_area_facets <- ggplot(topic_fraktion_smooth, aes(x = half_year_numeric, y = share_smooth, fill = topic_label)) +
  geom_area(position = "fill", alpha = 0.85, color = "black", linewidth = 0.1) +
  geom_vline(xintercept = 2018.5, linetype = "dotted", linewidth = 0.6, color = "black") +
  geom_vline(xintercept = 2022.5, linetype = "dotted", linewidth = 0.6, color = "black") +
  facet_wrap(~ redner_fraktion, nrow = 2, axes = "all_x") +
  scale_y_continuous(labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = seq(2015, 2025, by = 2), limits = c(2015, 2025.5)) +
  scale_fill_manual(values = topic_colors) +
  labs(
    title = "Temporal Dynamics of AI Topics Stratified by Parliamentary Group",
    x = "Year", y = "Share of AI-mentions", fill = "AI Topics"
  ) +
  theme_minimal() +
  theme(
    legend.position   = "right",
    strip.text        = element_text(face = "bold", size = 11),
    panel.spacing     = unit(1.5, "lines"),
    panel.border      = element_rect(color = "gray80", fill = NA, linewidth = 0.5),
    axis.ticks.x      = element_line(color = "gray60"),
    axis.ticks.length = unit(0.15, "cm")
  ) +
  coord_cartesian(expand = FALSE)

ggsave("Plots/temporal_dynamics_ai_topics_stratified.png", p_area_facets, width = 16, height = 9, dpi = 300)

# =============================================================================
# 6b. Stacked area chart: temporal dynamics of AI topics
# =============================================================================
p_area <- ggplot(topic_smooth, aes(x = half_year_numeric, y = share_smooth, fill = topic_label)) +
  geom_area(position = "fill", alpha = 0.85, color = "black", linewidth = 0.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1)) +
  scale_x_continuous(breaks = seq(2015, 2025, by = 2), limits = c(2015, 2025.5)) +
  scale_fill_manual(values = topic_colors) +
  labs(title = "Temporal dynamics of AI topics in the Bundestag", x = "Year", y = "Share of AI-mentions", fill = NULL) +
  theme_minimal() +
  theme(legend.position = "right", panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8)) +
  coord_cartesian(expand = FALSE)

ggsave("Plots/temporal_dynamics_ai_topics.png", p_area, width = 12, height = 6, dpi = 600)

# =============================================================================
# 7. Heatmaps
# =============================================================================
df_heat <- df |>
  mutate(redner_fraktion = recode(
    redner_fraktion,
    "BÜNDNIS 90/DIE GRÜNEN" = "B'90/DIE GRÜNEN"
  ))

fraktion_order <- c("CDU/CSU", "SPD", "FDP", "B'90/DIE GRÜNEN", "DIE LINKE", "AfD")

build_heat <- function(data, exclude_topics = c("Outlier", "Mobility & Infrastructure")) {

  base_data_all <- data |>
    filter(!redner_fraktion %in% EXCLUDE_FRAKTIONEN,
           !is.na(redner_fraktion)) # |>
 # filter(!topic_label %in% exclude_topics)

  total_speeches_overall <- base_data_all |>
    distinct(rede_id) |>
    nrow()


  data_all_topics <- base_data_all |>
    mutate(topic_label = str_trim(topic_label))

  # Fraktionen: ALLE Topics bleiben drin
  total_per_fraktion <- data_all_topics |>
    distinct(rede_id, redner_fraktion) |>
    count(redner_fraktion, name = "total")

  heat <- data_all_topics |>
    distinct(rede_id, redner_fraktion, topic_label) |>
    count(redner_fraktion, topic_label, name = "count") |>
    complete(
      redner_fraktion = fraktion_order,
      topic_label,
      fill = list(count = 0)
    ) |>
    left_join(total_per_fraktion, by = "redner_fraktion") |>
    mutate(
      share = ifelse(total == 0, 0, count / total)
    ) |>
    select(-total)

  heat_avg <- heat |>
    group_by(topic_label) |>
    summarise(
      share = mean(share, na.rm = TRUE),
      .groups = "drop"
    ) |>
    mutate(
      redner_fraktion = "Mean",
      count = NA_integer_
    )

heat_total <- base_data_all |>
  distinct(rede_id, topic_label) |>
  count(topic_label, name = "count") |>
  mutate(
    share = count / total_speeches_overall,
    redner_fraktion = "Total Share",
    count = as.integer(count)
  ) |>
  select(topic_label, count, share, redner_fraktion)

  bind_rows(heat, heat_avg, heat_total) |>
    mutate(
      redner_fraktion = factor(
        redner_fraktion,
        levels = c("Total Share", "Mean", rev(fraktion_order))
      )
    )
}

plot_heat <- function(heat, title, filename) {
  p <- ggplot(heat, aes(x = topic_label, y = redner_fraktion, fill = share)) +
    geom_tile(color = NA) +
    geom_text(
      aes(
        label = percent(share, accuracy = 0.1),
        color = ifelse(share > 0.20, "white", "black")
      ),
      size = 2.8
    ) +
    geom_hline(yintercept = c(1.5, 2.5), color = "black", linewidth = 0.5) +
    scale_fill_gradientn(
      colors = c("#FFFDE7", "#FFCC02", "#FF6600", "#CC0000", "#7B0000"),
      values = scales::rescale(c(0, 0.08, 0.20, 0.32, 0.41)),
      limits = c(0, max(heat$share, na.rm = TRUE)),
      oob = scales::squish,
      labels = percent_format(accuracy = 0.1),
      name = NULL
    ) +
    scale_color_identity() +
    scale_y_discrete(limits = levels(heat$redner_fraktion)) +
    labs(title = title, x = NULL, y = NULL) +
    theme_minimal() +
    theme(
      axis.text.x = element_text(angle = 40, hjust = 1, size = 8),
      axis.text.y = element_text(size = 7),
      legend.position = "none",
      panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8),
      plot.title = element_text(size = 7)
    ) +
    coord_cartesian(expand = FALSE)

  ggsave(filename, p, width = 12, height = 5, dpi = 300)
  p
}

heat_agg <- build_heat(df_heat)

plot_heat(
  heat_agg,
  "Share of AI-related speeches per topic by parliamentary group",
  "Plots/ai_topics_group_heatmap.png"
)

# =============================================================================
# 8b. Heatmaps by analytical periods
# =============================================================================
df_heat <- df_heat |>
  mutate(
    analysis_period = case_when(
      sitzung_jahr >= 2015 & sitzung_jahr <= 2017 ~ "2015-2017",
      sitzung_jahr >= 2018 & sitzung_jahr <= 2022 ~ "2018-2022",
      sitzung_jahr >= 2023 & sitzung_jahr <= 2025 ~ "2023-2025",
      TRUE ~ NA_character_
    )
  )

periods <- c("2015-2017", "2018-2022", "2023-2025")
heat_plots <- list()

for (period in periods) {
  heat_period <- build_heat(df_heat |> filter(analysis_period == period))
  p <- plot_heat(
    heat_period,
    paste0(period),
    paste0("Plots/ai_topics_group_heatmap_", str_replace_all(period, "-", "_"), ".png")
  )
  heat_plots[[period]] <- p
}

saveRDS(heat_plots, "Plots/heat_plots.rds")

heat_plots[["2018-2022"]]
heat_plots[["2023-2025"]]

# =============================================================================
# 9. Export descriptive statistics
# =============================================================================
ai_df_n <- ai_df_n |>
  mutate(n_words = str_count(rede_text, "\\S+"))

n_chunked_speeches <- df_chunks |>
  group_by(rede_id) |>
  summarise(anzahl_chunks = n(), .groups = "drop") |>
  filter(anzahl_chunks > 1) |>
  nrow()

descriptive_ai <- ai_df_n |>
  summarise(
    mean = mean(n_words, na.rm = TRUE),
    min = min(n_words, na.rm = TRUE),
    q1 = quantile(n_words, 0.25, na.rm = TRUE),
    median = median(n_words, na.rm = TRUE),
    q3 = quantile(n_words, 0.75, na.rm = TRUE),
    max = max(n_words, na.rm = TRUE),
    sd = sd(n_words, na.rm = TRUE),
    n = n()
  )

descriptive_chunks <- df_chunks |>
  mutate(n_words = str_count(chunk_text, "\\S+")) |>
  summarise(
    mean = mean(n_words, na.rm = TRUE),
    min = min(n_words, na.rm = TRUE),
    q1 = quantile(n_words, 0.25, na.rm = TRUE),
    median = median(n_words, na.rm = TRUE),
    q3 = quantile(n_words, 0.75, na.rm = TRUE),
    max = max(n_words, na.rm = TRUE),
    sd = sd(n_words, na.rm = TRUE),
    n = n()
  )

descriptive <- bind_rows(
  tibble(
    corpus = "AI-related speeches",
    n = descriptive_ai$n,
    mean = descriptive_ai$mean,
    sd = descriptive_ai$sd,
    min = descriptive_ai$min,
    q1 = descriptive_ai$q1,
    median = descriptive_ai$median,
    q3 = descriptive_ai$q3,
    max = descriptive_ai$max
  ),
  tibble(
    corpus = "Extracted AI contexts",
    n = descriptive_chunks$n,
    mean = descriptive_chunks$mean,
    sd = descriptive_chunks$sd,
    min = descriptive_chunks$min,
    q1 = descriptive_chunks$q1,
    median = descriptive_chunks$median,
    q3 = descriptive_chunks$q3,
    max = descriptive_chunks$max
  )
)

write_csv(descriptive, "data/descriptive.csv")

## descriptive statistics for N speeches per parliamentary group and period (All Speeches)
n_per_fraktion_phase_all <- df_heat |>
  filter(!is.na(analysis_period)) |>
  distinct(rede_id, redner_fraktion, analysis_period) |>
  count(redner_fraktion, analysis_period, name = "n") |>
  pivot_wider(names_from = analysis_period, values_from = n, values_fill = 0) |>
  mutate(
    redner_fraktion = factor(redner_fraktion, levels = fraktion_order)
  ) |>
  arrange(redner_fraktion) |>
  mutate(Total = `2015-2017` + `2018-2022` + `2023-2025`)

write_csv(n_per_fraktion_phase_all, "data/n_per_fraktion_phase_all.csv")

## descriptive statistics for N speeches per parliamentary group and period (AI Speeches Only)
n_per_fraktion_phase_ai <- ai_df_n |>
  mutate(
    analysis_period = case_when(
      sitzung_jahr >= 2015 & sitzung_jahr <= 2017 ~ "2015-2017",
      sitzung_jahr >= 2018 & sitzung_jahr <= 2022 ~ "2018-2022",
      sitzung_jahr >= 2023 & sitzung_jahr <= 2025 ~ "2023-2025",
      TRUE ~ NA_character_
    ),
    redner_fraktion = recode(redner_fraktion, "BÜNDNIS 90/DIE GRÜNEN" = "B'90/DIE GRÜNEN")
  ) |>
  filter(!is.na(analysis_period)) |>
  count(redner_fraktion, analysis_period, name = "n") |>
  pivot_wider(names_from = analysis_period, values_from = n, values_fill = 0) |>
  select(redner_fraktion, `2015-2017`, `2018-2022`, `2023-2025`) |>
  mutate(Total = `2015-2017` + `2018-2022` + `2023-2025`)

write_csv(n_per_fraktion_phase_ai, "data/n_per_fraktion_phase.csv")