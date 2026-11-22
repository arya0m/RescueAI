"""
RescueAI: Prediction History & SQLite Audit Log (Page 5)
Shared SQLite database audit log tracking all classified messages, user pins,
analyst triage tags (Reviewed, Flagged, Irrelevant), and agreement metrics.
"""

import sys
import os
import streamlit as st
import pandas as pd

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
from rescueai.database import (
    get_history_paginated, get_feedback_summary, get_all_triage_statuses,
    clear_history_entries
)
try:
    from app.components import apply_custom_css, render_sidebar, get_services, show_detail_dialog
except ModuleNotFoundError:
    from components import apply_custom_css, render_sidebar, get_services, show_detail_dialog

apply_custom_css()
render_sidebar()

models_svc, data_svc = get_services()

st.markdown(
    f"""
    <div style="margin-bottom: 12px; border-bottom: 1px solid {COLOR_BORDER}; padding-bottom: 8px;">
        <h1 style="font-size: 20px; font-weight: 700; color: {COLOR_TEXT}; margin: 0 0 2px 0;">
            Prediction History &middot; SQLite Audit Log
        </h1>
        <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">
            Shared SQLite storage (<code>data/rescueai.db</code>) synchronized across the Streamlit Console and FastAPI service.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Operational Metrics Cards
fb_summary = get_feedback_summary()
all_items, total_hist = get_history_paginated(page=1, size=5000)
user_items = [it for it in all_items if it.get("is_user")]

triage_map = get_all_triage_statuses()
rev_count = sum(1 for s in triage_map.values() if s == "reviewed")
flag_count = sum(1 for s in triage_map.values() if s == "flagged")

c_m1, c_m2, c_m3, c_m4 = st.columns(4)
with c_m1:
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Total Stored Predictions</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_TEXT};'>{total_hist:,}</div></div>", unsafe_allow_html=True)
with c_m2:
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>User Submissions / Pins</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_ACCENT};'>{len(user_items):,}</div></div>", unsafe_allow_html=True)
with c_m3:
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Reviewed / Flagged</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_OK};'>{rev_count} / {flag_count}</div></div>", unsafe_allow_html=True)
with c_m4:
    ag_rate = fb_summary.get("agreement_rate", 0.0)
    st.markdown(f"<div class='ops-panel-sub'><span class='label-upper'>Analyst AI Agreement</span><div class='mono' style='font-size:16px; font-weight:700; color:{COLOR_OK if ag_rate >= 0.7 else COLOR_ACCENT};'>{ag_rate:.1%}</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# Filter Bar
f_c_cat, f_c_user, f_c_q = st.columns([1.5, 1.2, 2.3])
with f_c_cat:
    cat_filt = st.selectbox(
        "Category Filter",
        options=["all"] + list(CATEGORY_NAMES.keys()),
        format_func=lambda x: "All Categories" if x == "all" else CATEGORY_NAMES[x]
    )
with f_c_user:
    source_filt = st.selectbox("Source Filter", options=["all", "user_only", "system_only"], format_func=lambda x: {"all": "All Sources", "user_only": "User Submissions Only", "system_only": "System Ingested"}[x])
with f_c_q:
    search_query = st.text_input("Search raw text", placeholder="Filter by keywords...")

# Apply Filters
filt_items = all_items
if cat_filt != "all":
    filt_items = [it for it in filt_items if it["predicted_label"] == int(cat_filt)]
if source_filt == "user_only":
    filt_items = [it for it in filt_items if it.get("is_user")]
elif source_filt == "system_only":
    filt_items = [it for it in filt_items if not it.get("is_user")]
if search_query.strip():
    sq = search_query.strip().lower()
    filt_items = [it for it in filt_items if sq in it["raw_text"].lower()]

# Data Table Display
if filt_items:
    table_data = []
    for it in filt_items:
        tid = str(it.get("id"))
        table_data.append({
            "Time": it["created_at"][11:19] if "T" in str(it["created_at"]) else str(it["created_at"])[:8],
            "Source": "User Pin" if it.get("is_user") else "System",
            "Event": it.get("event_name", "-") or "-",
            "Predicted Category": it["predicted_category"],
            "Confidence": float(it["confidence"]),
            "Urgency": it["urgency"],
            "Message Text": it["raw_text"],
            "_raw": it
        })
        
    df_history = pd.DataFrame(table_data)
    
    if "selected_hist_row" not in st.session_state:
        st.session_state.selected_hist_row = None

    selection_hist = st.dataframe(
        df_history[["Time", "Source", "Event", "Predicted Category", "Confidence", "Urgency", "Message Text"]],
        use_container_width=True,
        height=320,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Source": st.column_config.TextColumn("Source", width="small"),
            "Event": st.column_config.TextColumn("Event", width="medium"),
            "Predicted Category": st.column_config.TextColumn("Predicted Category", width="medium"),
            "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f", width="small"),
            "Urgency": st.column_config.TextColumn("Urgency", width="small"),
            "Message Text": st.column_config.TextColumn("Message Text", width="large")
        }
    )

    if selection_hist and selection_hist.selection and selection_hist.selection.rows:
        sel_idx = selection_hist.selection.rows[0]
        if st.session_state.selected_hist_row != sel_idx:
            st.session_state.selected_hist_row = sel_idx
            show_detail_dialog(table_data[sel_idx]["_raw"], models_svc)
    else:
        st.session_state.selected_hist_row = None

    # Export & Clear Controls
    c_exp, c_clr = st.columns([1, 1])
    with c_exp:
        csv_bytes = df_history[["Time", "Source", "Event", "Predicted Category", "Confidence", "Urgency", "Message Text"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export Filtered Audit Trail (CSV)",
            data=csv_bytes,
            file_name="rescueai_sqlite_audit_log.csv",
            mime="text/csv"
        )
    with c_clr:
        with st.expander("Database Maintenance", expanded=False):
            confirm_clr = st.checkbox("I confirm I want to clear all history records", key="clr_chk")
            if st.button("Clear Prediction History", type="secondary", disabled=not confirm_clr):
                n_del = clear_history_entries()
                st.success(f"Cleared {n_del} history entries from SQLite.")
                st.rerun()
else:
    st.info("No audit history records found matching current filters.")
