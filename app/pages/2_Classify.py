"""
RescueAI: Classify Message & AI Diagnostic Workbench (Page 2)
Provides real-time multi-model classification, Softmax probability distribution,
predictive term attribution, interactive token ablation, and quality audit logging.
"""

import sys
import os
import html
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
APP_DIR = os.path.join(ROOT_DIR, "app")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)

from rescueai.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_DANGER, COLOR_OK,
    CATEGORY_CONFIG, CATEGORY_NAMES
)
from rescueai.database import add_history_entry, add_feedback_entry
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
            Classify Message &middot; AI Diagnostic Workbench
        </h1>
        <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">
            Real-time multi-model inference, Softmax confidence calibration, linguistic feature attribution, and causal token ablation.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1-Click Operational Test Scenario Chips
PRESETS = [
    {
        "label": "Casualty Trap (Harvey)",
        "text": "URGENT: Flood waters rising fast in Houston bayou, family of 5 trapped in attic, need boat rescue immediately!",
    },
    {
        "label": "Bridge Collapse (Irma)",
        "text": "CRITICAL: Overseas Highway bridge section washed out near Key West, power lines severed, complete road cutoff",
    },
    {
        "label": "Relief Staging (Maria)",
        "text": "Red Cross boat crews deploying at San Juan harbor with clean drinking water, satellite phones, and medical kits",
    },
    {
        "label": "Wildfire Evac (California)",
        "text": "CalFire issues mandatory evacuation order for Santa Rosa Coffey Park sector as wind-driven firestorm advances",
    }
]

if "classify_text" not in st.session_state:
    st.session_state.classify_text = PRESETS[0]["text"]

st.markdown("<div class='label-upper' style='margin-bottom:4px;'>Operational Presets (Click to Load Scenario)</div>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
for p, col in zip(PRESETS, [c1, c2, c3, c4]):
    with col:
        if st.button(p["label"], key=f"c2_preset_{p['label']}", use_container_width=True):
            st.session_state.classify_text = p["text"]

# Input controls
col_txt, col_opt = st.columns([3, 1])
with col_txt:
    msg_input = st.text_area(
        "Disaster Message Input",
        value=st.session_state.classify_text,
        height=85,
        placeholder="Type or paste a disaster relief message...",
        label_visibility="collapsed"
    )

with col_opt:
    model_choice = st.selectbox(
        "Algorithm",
        options=["champion", "linear_svm", "naive_bayes", "random_forest"],
        format_func=lambda x: {
            "champion": "Champion (Balanced LR)",
            "linear_svm": "Linear SVM (Calibrated)",
            "naive_bayes": "Multinomial Naive Bayes",
            "random_forest": "Random Forest (200 Trees)"
        }[x]
    )
    classify_clicked = st.button("Run AI Inference", type="primary", use_container_width=True)

# Run classification on button click or default load
if msg_input.strip():
    pred_res = models_svc.predict(msg_input, model_name=model_choice)
    pred_label = pred_res["predicted_label"]
    pred_cat = pred_res["predicted_category"]
    conf = pred_res["confidence"]
    urgency = pred_res["urgency"]
    probs = pred_res["probabilities"]
    cfg = CATEGORY_CONFIG[pred_label]

    # Save to history automatically
    if classify_clicked:
        add_history_entry(
            raw_text=msg_input,
            clean_text=pred_res["clean_text"],
            predicted_label=pred_label,
            predicted_category=pred_cat,
            confidence=conf,
            urgency=urgency,
            is_low_confidence=pred_res["is_low_confidence"],
            is_user=True
        )

    # Low-Confidence Advisory Alert Banner
    if pred_res["is_low_confidence"]:
        st.markdown(
            f"""
            <div style="background: rgba(229, 83, 75, 0.12); border: 1px solid {COLOR_DANGER}; border-radius: 4px; padding: 8px 12px; margin-bottom: 12px; font-size: 12px; color: {COLOR_TEXT};">
                <span style="font-weight: 700; color: {COLOR_DANGER}; text-transform: uppercase;">Low Confidence Alert:</span>
                Prediction confidence is below 50% or within 10% of runner-up class (<b>{pred_res['runner_up']['category']}</b>: {pred_res['runner_up']['confidence']:.1%}).
                Human verification required before dispatching emergency resources.
            </div>
            """,
            unsafe_allow_html=True
        )

    # Main Result Grid
    res_left, res_right = st.columns([1.5, 1.0], gap="medium")

    with res_left:
        # Category Banner
        st.markdown(
            f"""
            <div class="ops-panel" style="margin-bottom: 12px; padding: 12px 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="display: inline-flex; align-items: center; gap: 8px; background: {cfg['color']}22; border: 1px solid {cfg['color']}66; color: {cfg['color']}; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: 700;">
                        <span>{pred_cat}</span>
                        <span style="border-left: 1px solid {cfg['color']}66; padding-left: 6px; font-size: 10px; text-transform: uppercase;">{urgency} URGENCY</span>
                    </span>
                    <span class="mono" style="font-size: 15px; font-weight: 700; color: {COLOR_ACCENT};">
                        {conf:.1%} Confidence
                    </span>
                </div>
                <div style="font-size: 11px; color: {COLOR_TEXT_MUTED}; margin-bottom: 8px;">{cfg['description']}</div>
                <div style="font-size: 12px; color: {COLOR_TEXT}; background: {COLOR_SURFACE_2}; padding: 8px 10px; border-radius: 4px; border: 1px solid {COLOR_BORDER};">
                    <span style="color: {COLOR_TEXT_MUTED}; font-size: 11px; text-transform: uppercase;">Normalized Tokens:</span><br>
                    <span class="mono">{pred_res['clean_text']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Linguistic Term Attribution (Explainability)
        st.markdown("<div class='label-upper' style='margin-bottom: 6px;'>Key Predictive Terms (TF-IDF &times; Model Coefficients)</div>", unsafe_allow_html=True)
        terms = pred_res.get("terms", [])
        if terms:
            term_chips = []
            for t in terms:
                t_score = t["score"]
                t_word = html.escape(t["term"])
                if t_score > 0:
                    chip = f"<span class='term-hl-pred' title='Favors: {t['category']} (+{t_score:.3f})'>{t_word} (+{t_score:.2f})</span>"
                else:
                    chip = f"<span class='term-hl-runner' title='Favors: {t['category']} ({t_score:.3f})'>{t_word} ({t_score:.2f})</span>"
                term_chips.append(chip)
            st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px;'>{' '.join(term_chips)}</div>", unsafe_allow_html=True)
        else:
            st.caption("No strong vocabulary attributions identified for this input.")

        # Interactive Token Ablation Workbench
        words = pred_res["clean_text"].split()
        if len(words) > 1:
            st.markdown("<div class='label-upper' style='margin-top: 10px; margin-bottom: 4px;'>Causal Token Ablation (Drop Words to Test Impact)</div>", unsafe_allow_html=True)
            dropped = st.multiselect(
                "Select tokens to ablate from message:",
                options=list(dict.fromkeys(words)),
                key="c2_ablate_tokens"
            )
            if dropped:
                ab_res = models_svc.predict_ablate(msg_input, dropped)
                new_c = ab_res["ablated"]["confidence"]
                new_cat = ab_res["ablated"]["predicted_category"]
                delta = ab_res["confidence_delta"]
                delta_color = COLOR_DANGER if delta < 0 else COLOR_OK
                
                st.markdown(
                    f"""
                    <div class="ops-panel-sub" style="font-size: 12px; margin-top: 4px;">
                        Without <code>{', '.join(dropped)}</code> &rarr; 
                        Predicted: <b>{new_cat}</b> ({new_c:.1%}) &middot; 
                        <span style="color:{delta_color}; font-weight:600;">Delta: {delta:+.1%}</span>
                        {" (Category Changed!)" if ab_res["prediction_changed"] else ""}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with res_right:
        # Softmax Probability Distribution Chart
        st.markdown("<div class='label-upper' style='margin-bottom: 6px;'>Calibrated Probability Distribution</div>", unsafe_allow_html=True)
        cats = list(CATEGORY_NAMES.values())
        vals = [probs.get(c, 0.0) for c in cats]
        colors = [CATEGORY_CONFIG[i]["color"] for i in range(5)]
        
        p_fig = go.Figure(go.Bar(
            x=vals,
            y=[c if len(c) < 22 else c[:20] + ".." for c in cats],
            orientation='h',
            marker=dict(color=colors),
            text=[f"{v:.1%}" for v in vals],
            textposition='auto',
            textfont=dict(family="IBM Plex Mono", size=10, color=COLOR_TEXT)
        ))
        p_layout = get_console_plotly_layout(height=180)
        p_layout["xaxis"]["range"] = [0, 1.0]
        p_layout["margin"] = dict(l=10, r=10, t=10, b=20)
        p_fig.update_layout(p_layout)
        st.plotly_chart(p_fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

        # Cross-Model Comparative Predictions
        st.markdown("<div class='label-upper' style='margin-top: 10px; margin-bottom: 6px;'>Multi-Model Verification</div>", unsafe_allow_html=True)
        model_names = {
            "logistic_regression": "Logistic Regression",
            "linear_svm": "Linear SVM",
            "naive_bayes": "Naive Bayes",
            "random_forest": "Random Forest"
        }
        comp_rows = []
        for m_id, m_name in model_names.items():
            m_res = models_svc.predict(msg_input, model_name=m_id)
            comp_rows.append(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0; border-bottom:1px solid {COLOR_BORDER}; font-size:11px;">
                <span style="color:{COLOR_TEXT_MUTED};">{m_name}</span>
                <span class="mono" style="color:{CATEGORY_CONFIG[m_res['predicted_label']]['color']}; font-weight:600;">
                    {m_res['predicted_category'][:18]} ({m_res['confidence']:.0%})
                </span>
            </div>
            """)
        st.markdown(f"<div class='ops-panel-sub' style='padding:6px 10px;'>{''.join(comp_rows)}</div>", unsafe_allow_html=True)

        # Analyst Feedback & Audit Logging
        st.markdown("<div class='label-upper' style='margin-top: 10px; margin-bottom: 4px;'>Analyst Quality Feedback</div>", unsafe_allow_html=True)
        with st.container():
            f_col1, f_col2 = st.columns([1, 1.8])
            with f_col1:
                is_correct = st.radio("Correct?", ["Yes", "No"], horizontal=True, key="c2_fb_correct")
            with f_col2:
                user_label = None
                if is_correct == "No":
                    user_label = st.selectbox(
                        "True Category",
                        options=list(range(5)),
                        format_func=lambda x: CATEGORY_NAMES[x],
                        key="c2_fb_label"
                    )
            if st.button("Submit Feedback", key="c2_submit_fb", use_container_width=True):
                add_feedback_entry(
                    raw_text=msg_input,
                    predicted_label=pred_label,
                    is_correct=(is_correct == "Yes"),
                    user_label=user_label
                )
                st.success("Logged in SQLite audit database for ongoing quality evaluation.")
