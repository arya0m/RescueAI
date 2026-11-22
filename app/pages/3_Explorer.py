"""
RescueAI: CrisisMMD v2.0 Dataset Explorer (Page 3)
Allows multi-split inspection, event filtering, category cross-tabulation,
top characteristic vocabulary analysis, and full message browsing.
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
APP_DIR = os.path.join(ROOT_DIR, "app")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)

from rescueai.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_DANGER, COLOR_OK,
    CATEGORY_CONFIG, CATEGORY_NAMES, DISASTER_EVENTS
)
try:
    from app.components import apply_custom_css, render_sidebar, get_services
    from app.theme import get_console_plotly_layout
except ModuleNotFoundError:
    from components import apply_custom_css, render_sidebar, get_services
    from theme import get_console_plotly_layout

apply_custom_css()
render_sidebar()

models_svc, data_svc = get_services()

st.markdown(
    f"""
    <div style="margin-bottom: 12px; border-bottom: 1px solid {COLOR_BORDER}; padding-bottom: 8px;">
        <h1 style="font-size: 20px; font-weight: 700; color: {COLOR_TEXT}; margin: 0 0 2px 0;">
            CrisisMMD v2.0 &middot; Dataset Explorer
        </h1>
        <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">
            Multimodal social media corpus across 7 major natural disasters (16,058 total annotations &middot; 5 humanitarian categories).
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Filter Bar
f_split, f_ev, f_cat, f_search = st.columns([1.2, 1.8, 1.8, 2.2])

with f_split:
    split_choice = st.selectbox(
        "Split",
        options=["test", "train", "dev", "all"],
        format_func=lambda x: {"test": "Test (2,237)", "train": "Train (11,584)", "dev": "Dev (2,237)", "all": "All (16,058)"}[x]
    )

with f_ev:
    ev_opts = ["all"] + list(DISASTER_EVENTS.keys())
    ev_choice = st.selectbox(
        "Disaster Event",
        options=ev_opts,
        format_func=lambda x: "All Disaster Events" if x == "all" else DISASTER_EVENTS[x]["display_name"]
    )

with f_cat:
    cat_opts = ["all"] + list(CATEGORY_NAMES.keys())
    cat_choice = st.selectbox(
        "Category",
        options=cat_opts,
        format_func=lambda x: "All Categories" if x == "all" else CATEGORY_NAMES[x]
    )

with f_search:
    search_q = st.text_input("Search tweet text", placeholder="Filter by keyword (e.g. boat, flood, trapped)...")

# Load Dataset Slice
if split_choice == "all":
    full_df = pd.concat([data_svc.df_train, data_svc.df_dev, data_svc.df_test], ignore_index=True)
elif split_choice == "train":
    full_df = data_svc.df_train.copy()
elif split_choice == "dev":
    full_df = data_svc.df_dev.copy()
else:
    full_df = data_svc.df_test.copy()

# Apply Filters
filtered_df = full_df.copy()
if ev_choice != "all":
    filtered_df = filtered_df[filtered_df["event_name"] == ev_choice]
if cat_choice != "all":
    filtered_df = filtered_df[filtered_df["target_label"].astype(int) == int(cat_choice)]
if search_q.strip():
    q_lower = search_q.strip().lower()
    filtered_df = filtered_df[filtered_df["tweet_text"].str.lower().str.contains(q_lower, na=False)]

# Summary Stat Pills
total_count = len(filtered_df)
c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
with c_stat1:
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Records Matching</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_TEXT};'>{total_count:,}</div></div>", unsafe_allow_html=True)
with c_stat2:
    pct_corpus = (total_count / 16058) * 100
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Share of Corpus</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_ACCENT};'>{pct_corpus:.1f}%</div></div>", unsafe_allow_html=True)
with c_stat3:
    n_events = filtered_df["event_name"].nunique() if total_count > 0 else 0
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Crises Covered</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_TEXT};'>{n_events} / 7</div></div>", unsafe_allow_html=True)
with c_stat4:
    n_classes = filtered_df["target_label"].nunique() if total_count > 0 else 0
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Categories Present</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_OK};'>{n_classes} / 5</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# Visual Distribution Row
col_dist, col_heat = st.columns([1.1, 1.4], gap="medium")

with col_dist:
    st.markdown("<div class='label-upper' style='margin-bottom:4px;'>Class Distribution in Filtered Slice</div>", unsafe_allow_html=True)
    if total_count > 0:
        counts = filtered_df["target_label"].astype(int).value_counts().reindex(range(5), fill_value=0)
        c_names = [CATEGORY_NAMES[i][:20] + ".." if len(CATEGORY_NAMES[i]) > 22 else CATEGORY_NAMES[i] for i in range(5)]
        c_colors = [CATEGORY_CONFIG[i]["color"] for i in range(5)]
        
        fig_bar = go.Figure(go.Bar(
            x=counts.values,
            y=c_names,
            orientation='h',
            marker=dict(color=c_colors),
            text=[f"{v:,} ({v/total_count:.1%})" for v in counts.values],
            textposition='auto',
            textfont=dict(family="IBM Plex Mono", size=10, color=COLOR_TEXT)
        ))
        b_layout = get_console_plotly_layout(height=180)
        b_layout["margin"] = dict(l=10, r=10, t=10, b=20)
        fig_bar.update_layout(b_layout)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    else:
        st.info("No records match current filters.")

with col_heat:
    st.markdown("<div class='label-upper' style='margin-bottom:4px;'>Category &times; Disaster Event Cross-Tabulation</div>", unsafe_allow_html=True)
    if total_count > 0:
        cross = pd.crosstab(
            filtered_df["event_name"].map(lambda x: DISASTER_EVENTS.get(x, {}).get("display_name", x)),
            filtered_df["target_label"].astype(int).map(CATEGORY_NAMES)
        )
        fig_heat = px.imshow(
            cross,
            text_auto=True,
            color_continuous_scale=[[0, "#151A21"], [0.5, "#3FB6A8"], [1, "#F2A33A"]],
            aspect="auto"
        )
        h_layout = get_console_plotly_layout(height=180)
        h_layout["margin"] = dict(l=10, r=10, t=10, b=20)
        fig_heat.update_layout(h_layout)
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

# Key Characteristic Vocabulary Chips
st.markdown("<div class='label-upper' style='margin-top:6px; margin-bottom:4px;'>Top Characteristic Vocabulary N-Grams</div>", unsafe_allow_html=True)
target_class_id = int(cat_choice) if cat_choice != "all" else 0
top_vocab = models_svc.get_top_terms_by_class(target_class_id, top_k=14)
if top_vocab:
    vocab_chips = []
    c_color = CATEGORY_CONFIG[target_class_id]["color"]
    for v in top_vocab:
        term = v["term"]
        score = v["weight"]
        vocab_chips.append(f"<span style='background:{c_color}22; border:1px solid {c_color}66; color:{c_color}; padding:2px 8px; border-radius:3px; font-size:11px; font-family:IBM Plex Mono;'>{term} ({score:+.2f})</span>")
    st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px;'>{' '.join(vocab_chips)}</div>", unsafe_allow_html=True)

# Paginated Messages Table
st.markdown("<div class='label-upper' style='margin-top:6px; margin-bottom:4px;'>Filtered Message Browser (Showing max 200 rows)</div>", unsafe_allow_html=True)
if not filtered_df.empty:
    browse_df = filtered_df[["tweet_id", "timestamp", "event_name", "target_label", "tweet_text"]].head(200).copy()
    browse_df["target_label"] = browse_df["target_label"].astype(int).map(CATEGORY_NAMES)
    browse_df["event_name"] = browse_df["event_name"].map(lambda x: DISASTER_EVENTS.get(x, {}).get("display_name", x))
    browse_df["Time"] = browse_df["timestamp"].str[11:19]
    browse_df = browse_df.rename(columns={
        "tweet_id": "Tweet ID",
        "event_name": "Event",
        "target_label": "Ground Truth Category",
        "tweet_text": "Message Text"
    })
    
    st.dataframe(
        browse_df[["Time", "Event", "Ground Truth Category", "Message Text", "Tweet ID"]],
        use_container_width=True,
        height=260,
        hide_index=True,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Event": st.column_config.TextColumn("Event", width="medium"),
            "Ground Truth Category": st.column_config.TextColumn("Ground Truth Category", width="medium"),
            "Message Text": st.column_config.TextColumn("Message Text", width="large"),
            "Tweet ID": st.column_config.TextColumn("Tweet ID", width="small")
        }
    )
    
    # CSV Export Button
    csv_bytes = filtered_df[["tweet_id", "timestamp", "event_name", "target_label", "tweet_text"]].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Filtered CSV",
        data=csv_bytes,
        file_name="crisismmd_filtered_export.csv",
        mime="text/csv"
    )
else:
    st.info("No messages match the chosen filters.")
