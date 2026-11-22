"""
RescueAI: Model Benchmarks & Algorithmic Diagnostics (Page 4)
Compares all 4 trained supervised models on the held-out CrisisMMD test set (N=2,237),
provides an interactive 5x5 confusion matrix with cell drill-down, and a decision threshold sensitivity curve.
"""

import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
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
    CATEGORY_CONFIG, CATEGORY_NAMES
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
            Model Benchmarks &middot; Algorithmic Diagnostics
        </h1>
        <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">
            Rigorous evaluation on the held-out CrisisMMD test set (N=2,237) comparing Logistic Regression, Linear SVM, Naive Bayes, and Random Forest.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. Model Comparison Leaderboard Table
st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Held-Out Test Set Performance Leaderboard (N=2,237)</div>", unsafe_allow_html=True)

benchmarks_data = models_svc.benchmarks
if benchmarks_data:
    b_df = pd.DataFrame(benchmarks_data)
    display_b_df = pd.DataFrame({
        "Model": b_df["Model"],
        "Architecture": b_df["Type"],
        "Test Accuracy": b_df["Test Accuracy"].map(lambda x: f"{x:.2%}"),
        "Macro Precision": b_df["Macro Precision"].map(lambda x: f"{x:.4f}"),
        "Macro Recall": b_df["Macro Recall"].map(lambda x: f"{x:.4f}"),
        "Macro F1": b_df["Macro F1"].map(lambda x: f"{x:.4f}"),
        "Cat 0 Recall (Casualties)": b_df["Cat 0 Recall"].map(lambda x: f"{x:.1%}"),
        "Train Time": b_df["Train Time (s)"].map(lambda x: f"{x:.2f}s")
    })
    
    st.dataframe(
        display_b_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "Architecture": st.column_config.TextColumn("Architecture", width="medium"),
            "Test Accuracy": st.column_config.TextColumn("Test Accuracy", width="small"),
            "Macro Precision": st.column_config.TextColumn("Macro Precision", width="small"),
            "Macro Recall": st.column_config.TextColumn("Macro Recall", width="small"),
            "Macro F1": st.column_config.TextColumn("Macro F1", width="small"),
            "Cat 0 Recall (Casualties)": st.column_config.TextColumn("Cat 0 Recall (Casualties)", width="medium"),
            "Train Time": st.column_config.TextColumn("Train Time", width="small")
        }
    )

# Why Logistic Regression is Champion Card
st.markdown(
    f"""
    <div class="ops-panel" style="margin-top:8px; margin-bottom:14px; padding:10px 14px; border-left:3px solid {COLOR_ACCENT};">
        <div style="font-size:13px; font-weight:700; color:{COLOR_ACCENT}; margin-bottom:4px;">
            Scientific Rationale for Selecting Balanced Logistic Regression as Champion
        </div>
        <div style="font-size:12px; color:{COLOR_TEXT}; line-height:1.5;">
            While Calibrated Linear SVM achieved higher raw accuracy (52.88%), it severely underperformed on the safety-critical minority class, catching only <b>17.4% of casualty and medical emergency reports</b>. 
            Balanced Logistic Regression ($C=0.5$) achieved the <b>highest Macro F1-Score (0.4746)</b> and <b>48.48% casualty recall</b> (&sim;3&times; more lives triaged) with fully calibrated Softmax posterior probabilities.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 2. Interactive Confusion Matrix & Cell Drill-Down
col_cm, col_cell = st.columns([1.4, 1.2], gap="medium")

with col_cm:
    c_cm_m, c_cm_norm = st.columns([2, 1])
    with c_cm_m:
        cm_model = st.selectbox(
            "Confusion Matrix Model",
            options=["logistic_regression", "linear_svm", "naive_bayes", "random_forest"],
            format_func=lambda x: {
                "logistic_regression": "Logistic Regression (Champion)",
                "linear_svm": "Linear SVM (Calibrated)",
                "naive_bayes": "Multinomial Naive Bayes",
                "random_forest": "Random Forest (200 Trees)"
            }[x]
        )
    with c_cm_norm:
        cm_norm = st.checkbox("Normalize (%)", value=False)
        
    cm_data = models_svc.get_confusion_matrix_data(
        model_name=cm_model,
        normalize=cm_norm,
        test_df=data_svc.df_test
    )
    
    matrix = cm_data["matrix"]
    short_labels = ["Affected", "Infr. Damage", "Rescue", "Other Info", "Irrelevant"]
    
    cm_fig = px.imshow(
        matrix,
        x=short_labels,
        y=short_labels,
        labels=dict(x="Predicted Class", y="True Ground Truth", color="Frequency"),
        text_auto=".1%" if cm_norm else "d",
        color_continuous_scale=[[0, "#151A21"], [0.5, "#3FB6A8"], [1, "#E5534B"]],
        aspect="auto"
    )
    cm_layout = get_console_plotly_layout(height=260)
    cm_layout["margin"] = dict(l=20, r=10, t=10, b=20)
    cm_fig.update_layout(cm_layout)
    st.plotly_chart(cm_fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

with col_cell:
    st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Confusion Matrix Cell Tweet Drill-Down</div>", unsafe_allow_html=True)
    c_t_sel, c_p_sel = st.columns(2)
    with c_t_sel:
        true_c = st.selectbox("True Ground Truth", options=list(range(5)), format_func=lambda x: CATEGORY_NAMES[x])
    with c_p_sel:
        pred_c = st.selectbox("Model Prediction", options=list(range(5)), index=true_c, format_func=lambda x: CATEGORY_NAMES[x])
        
    cell_tweets = models_svc.get_confusion_cell_messages(
        model_name=cm_model,
        true_label=true_c,
        pred_label=pred_c,
        test_df=data_svc.df_test,
        size=4
    )
    
    total_cell = cell_tweets.get("total_count", 0)
    is_diag = (true_c == pred_c)
    status_label = "Correctly Classified" if is_diag else "Misclassified (Error Case)"
    status_color = COLOR_OK if is_diag else COLOR_DANGER
    
    st.markdown(
        f"""
        <div style="font-size:11px; margin-bottom:6px;">
            <span style="color:{status_color}; font-weight:700;">{status_label}</span>: 
            <span class="mono" style="color:{COLOR_TEXT};">{total_cell} messages</span> in test set
        </div>
        """,
        unsafe_allow_html=True
    )
    
    for item in cell_tweets.get("items", []):
        st.markdown(
            f"""
            <div class="ops-panel-sub" style="font-size:11px; margin-bottom:4px; line-height:1.4;">
                <span class="mono" style="color:{COLOR_TEXT_MUTED};">ID: {item['tweet_id']}</span> &middot;
                <span class="mono" style="color:{COLOR_ACCENT};">{item['confidence']:.1%} conf</span><br>
                <span>{html.escape(item['tweet_text'])}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# 3. Decision Threshold Sensitivity Analysis
st.markdown("<div class='label-upper' style='margin-top:10px; margin-bottom:4px;'>Human-in-the-Loop Decision Threshold Exploration (t)</div>", unsafe_allow_html=True)
c_thresh_s, c_thresh_info = st.columns([2, 3])

with c_thresh_s:
    t_val = st.slider(
        "Confidence Routing Threshold (t)",
        min_value=0.20,
        max_value=0.85,
        value=0.50,
        step=0.05,
        help="Messages with confidence < t are routed to human operators; retained messages are triaged automatically."
    )

thresh_res = models_svc.get_threshold_analysis(
    model_name=cm_model,
    t=t_val,
    test_df=data_svc.df_test
)

with c_thresh_info:
    st.markdown(
        f"""
        <div class="ops-panel-sub" style="font-size:12px; margin-top:14px;">
            At threshold <b>t = {t_val:.2f}</b>: 
            <span style="color:{COLOR_ACCENT}; font-weight:700;">{thresh_res['flagged_count']:,} messages ({thresh_res['flagged_percent']:.1f}%)</span> routed to human queue &middot; 
            Retained Automated Accuracy: <span style="color:{COLOR_OK}; font-weight:700;">{thresh_res['retained_accuracy']:.1%}</span> &middot; 
            Retained Macro F1: <span style="color:{COLOR_OK}; font-weight:700;">{thresh_res['retained_macro_f1']:.4f}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Threshold Curve Plot
threshold_steps = np.arange(0.20, 0.85, 0.05)
curve_data = [models_svc.get_threshold_analysis(cm_model, t, data_svc.df_test) for t in threshold_steps]

crv_t = [c["threshold"] for c in curve_data]
crv_flag = [c["flagged_percent"] for c in curve_data]
crv_acc = [c["retained_accuracy"] * 100 for c in curve_data]
crv_f1 = [c["retained_macro_f1"] * 100 for c in curve_data]

t_plot = go.Figure()
t_plot.add_trace(go.Scatter(x=crv_t, y=crv_acc, mode='lines+markers', name="Retained Accuracy (%)", line=dict(color=COLOR_OK, width=1.8)))
t_plot.add_trace(go.Scatter(x=crv_t, y=crv_f1, mode='lines+markers', name="Retained Macro F1 (%)", line=dict(color=COLOR_ACCENT, width=1.8)))
t_plot.add_trace(go.Scatter(x=crv_t, y=crv_flag, mode='lines', name="% Routed to Human Review", line=dict(color=COLOR_DANGER, width=1.5, dash="dash")))

# Current threshold vertical marker
t_plot.add_vline(x=t_val, line_width=1.5, line_dash="dot", line_color="#FFFFFF")

plot_layout = get_console_plotly_layout(height=160)
plot_layout["margin"] = dict(l=20, r=10, t=10, b=20)
plot_layout["legend"] = dict(orientation="h", y=1.15, x=1, xanchor="right", font=dict(size=10, color=COLOR_TEXT_MUTED))
t_plot.update_layout(plot_layout)
st.plotly_chart(t_plot, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
