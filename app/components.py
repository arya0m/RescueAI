"""
RescueAI Streamlit Shared Components, Cache Loaders, and Detail Dialog.
Imports shared ML services, constants, and SQLite database from rescueai.
"""

import os
import html
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Tuple

from rescueai.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_DANGER, COLOR_OK,
    CATEGORY_CONFIG, CATEGORY_NAMES, DISASTER_EVENTS
)
from rescueai.services import ModelService, DataService
from rescueai.database import (
    set_triage_status, add_feedback_entry, add_history_entry,
    get_user_pins, get_all_triage_statuses
)
try:
    from app.theme import get_console_plotly_layout
except ModuleNotFoundError:
    from theme import get_console_plotly_layout


def apply_custom_css():
    """Injects app/style.css."""
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_services() -> Tuple[ModelService, DataService]:
    """Loads and caches shared ModelService and DataService once at startup."""
    models_svc = ModelService(models_dir="models", reports_dir="reports")
    data_svc = DataService(data_dir="data/processed", models_service=models_svc)
    return models_svc, data_svc


def render_sidebar():
    """Renders narrow plain text sidebar with minimal navigation links."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 6px 0 14px 0; border-bottom: 1px solid {COLOR_BORDER}; margin-bottom: 14px;">
                <div style="font-size: 16px; font-weight: 700; letter-spacing: -0.02em; color: {COLOR_TEXT};">
                    RescueAI
                </div>
                <div style="font-size: 10px; color: {COLOR_TEXT_MUTED}; margin-top: 2px;">
                    Disaster Relief Message Triage
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


@st.dialog("Message Details", width="large")
def show_detail_dialog(msg_data: Dict[str, Any], models_svc: ModelService):
    """
    Renders detailed message drawer in an operations modal dialog.
    Includes full text, highlighted predictive terms, probability distribution,
    word ablation test, triage status actions, and analyst feedback.
    """
    tweet_id = str(msg_data.get("tweet_id", "user_entry"))
    raw_text = msg_data.get("tweet_text") or msg_data.get("raw_text", "")
    clean_text = msg_data.get("clean_text") or ""
    pred_label = int(msg_data.get("predicted_label", 4))
    pred_cat = CATEGORY_NAMES.get(pred_label, "Not Humanitarian / Irrelevant")
    conf = float(msg_data.get("confidence", 0.0))
    urgency = CATEGORY_CONFIG[pred_label]["urgency"]
    probs = msg_data.get("probabilities", {})
    is_user = msg_data.get("is_user", False)
    
    # Header badge row
    cat_cfg = CATEGORY_CONFIG[pred_label]
    badge_html = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="display:inline-flex; align-items:center; gap:8px; background:{cat_cfg['color']}22; border:1px solid {cat_cfg['color']}66; color:{cat_cfg['color']}; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:600;">
            <span>{html.escape(pred_cat)}</span>
            <span style="border-left:1px solid {cat_cfg['color']}66; padding-left:6px; font-size:10px; text-transform:uppercase;">{urgency} URGENCY</span>
        </span>
        <span class="mono" style="font-size:13px; font-weight:600; color:{COLOR_ACCENT};">
            Confidence: {conf:.1%}
        </span>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
    
    # Message body
    st.markdown(
        f"""
        <div class="ops-panel" style="margin-bottom:14px; font-size:14px; line-height:1.5;">
            {html.escape(raw_text)}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Feature attributions (highlighted key terms)
    terms = models_svc.explain_text(clean_text, pred_label)
    if terms:
        st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Key Predictive Terms</div>", unsafe_allow_html=True)
        term_spans = []
        for t in terms:
            t_term = html.escape(t["term"])
            t_score = t["score"]
            if t_score > 0:
                span = f"<span class='term-hl-pred' title='Contribution: +{t_score:.3f}'>{t_term} (+{t_score:.2f})</span>"
            else:
                span = f"<span class='term-hl-runner' title='Contribution: {t_score:.3f}'>{t_term} ({t_score:.2f})</span>"
            term_spans.append(span)
        st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px;'>{' '.join(term_spans)}</div>", unsafe_allow_html=True)
        
    # Probability distribution bar chart
    if probs:
        st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Class Probability Distribution</div>", unsafe_allow_html=True)
        cats = list(CATEGORY_NAMES.values())
        vals = [probs.get(c, 0.0) for c in cats]
        colors = [CATEGORY_CONFIG[i]["color"] for i in range(5)]
        
        fig = go.Figure(go.Bar(
            x=vals,
            y=[c if len(c) < 26 else c[:24] + "..." for c in cats],
            orientation='h',
            marker=dict(color=colors),
            text=[f"{v:.1%}" for v in vals],
            textposition='auto',
            textfont=dict(family="IBM Plex Mono", size=10, color=COLOR_TEXT)
        ))
        layout = get_console_plotly_layout(height=180)
        layout["xaxis"]["range"] = [0, 1.0]
        layout["margin"] = dict(l=10, r=10, t=10, b=20)
        fig.update_layout(layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    # Word ablation test
    words = clean_text.split()
    if len(words) > 1:
        st.markdown("<div class='label-upper' style='margin-top:8px; margin-bottom:4px;'>What Changes the Prediction? (Token Ablation)</div>", unsafe_allow_html=True)
        tokens_to_drop = st.multiselect(
            "Select words to remove to test impact:",
            options=list(dict.fromkeys(words)),
            key=f"ablate_{tweet_id}"
        )
        if tokens_to_drop:
            ablate_res = models_svc.predict_ablate(raw_text, tokens_to_drop)
            new_pred = ablate_res["ablated"]
            st.info(f"Without `{', '.join(tokens_to_drop)}`: **{new_pred['predicted_category']}** ({new_pred['confidence']:.1%}) — Delta: {ablate_res['confidence_delta']:+.1%}")

    st.markdown("---")
    
    # Status actions row
    c_stat, c_fb = st.columns([1, 1])
    with c_stat:
        st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Triage Status</div>", unsafe_allow_html=True)
        cur_status = msg_data.get("status", "unreviewed")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("Reviewed", key=f"btn_rev_{tweet_id}", type="primary" if cur_status == "reviewed" else "secondary"):
                set_triage_status(tweet_id, "reviewed")
                st.toast("Status updated: Reviewed")
                st.rerun()
        with col_s2:
            if st.button("Flag", key=f"btn_flag_{tweet_id}", type="primary" if cur_status == "flagged" else "secondary"):
                set_triage_status(tweet_id, "flagged")
                st.toast("Status updated: Flagged for follow-up")
                st.rerun()
        with col_s3:
            if st.button("Not Relevant", key=f"btn_irr_{tweet_id}", type="primary" if cur_status == "irrelevant" else "secondary"):
                set_triage_status(tweet_id, "irrelevant")
                st.toast("Status updated: Not relevant")
                st.rerun()

    # Analyst Feedback row
    with c_fb:
        st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Analyst Quality Feedback</div>", unsafe_allow_html=True)
        col_fb1, col_fb2 = st.columns([1, 2])
        with col_fb1:
            fb_correct = st.radio("Correct?", ["Yes", "No"], horizontal=True, key=f"fb_rad_{tweet_id}")
        with col_fb2:
            alt_class = None
            if fb_correct == "No":
                alt_class = st.selectbox(
                    "Select true class:",
                    options=list(range(5)),
                    format_func=lambda x: CATEGORY_NAMES[x],
                    key=f"fb_alt_{tweet_id}"
                )
        if st.button("Submit Feedback", key=f"btn_sub_fb_{tweet_id}"):
            add_feedback_entry(
                raw_text=raw_text,
                predicted_label=pred_label,
                is_correct=(fb_correct == "Yes"),
                tweet_id=tweet_id,
                user_label=alt_class
            )
            st.success("Feedback recorded in quality audit database.")
            st.caption("Feedback is saved for quality audit and does not retrain the model.")
