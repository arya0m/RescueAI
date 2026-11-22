"""
RescueAI Operations Console: First Page (1440x900 viewport fit).
Features:
- Dual-Mode Map: 2017 CrisisMMD Replay OR World Live Disaster Map (USGS seismic & global natural disaster hotspots).
- Hub-and-Spoke incident networks, impact buffer zones, double-ring epicenters, and floating GIS legend (Image 2).
- Recent Disaster News Wire with 1-click live AI classification and instant map geolocating.
- High-density telemetry spike chart of message volume over time (Image 1).
- Functional AI engine with 1-click test chips, multi-model switcher, and automated event location detection.
- Structured operational message log with category badges and single-click inspection dialog.
"""

import sys
import os
import math
import html
import folium
import folium.plugins as plugins
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_folium import st_folium

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
APP_DIR = os.path.join(ROOT_DIR, "app")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)

from rescueai.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_DANGER, COLOR_OK,
    CATEGORY_CONFIG, CATEGORY_NAMES, DISASTER_EVENTS, DISASTER_SUB_INCIDENTS
)
from rescueai.database import (
    add_history_entry, get_user_pins, get_user_messages,
    get_all_triage_statuses, set_triage_status
)
from rescueai.news_service import LiveFeedService

try:
    from app.components import (
        apply_custom_css, render_sidebar, get_services, show_detail_dialog
    )
    from app.theme import get_console_plotly_layout
    from app.live_components import (
        render_live_stream_ticker, render_live_oscilloscope_graph,
        render_live_system_hud, inject_map_radar_pulse_css
    )
except ModuleNotFoundError:
    from components import (
        apply_custom_css, render_sidebar, get_services, show_detail_dialog
    )
    from theme import get_console_plotly_layout
    from live_components import (
        render_live_stream_ticker, render_live_oscilloscope_graph,
        render_live_system_hud, inject_map_radar_pulse_css
    )

apply_custom_css()
render_sidebar()

models_svc, data_svc = get_services()
news_svc = LiveFeedService()

# Session State Initialization (preventing duplicate triggers / rerun loops)
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "pending_user_msg" not in st.session_state:
    st.session_state.pending_user_msg = None
if "replay_playing" not in st.session_state:
    st.session_state.replay_playing = False
if "replay_step" not in st.session_state:
    st.session_state.replay_step = 0
if "replay_speed" not in st.session_state:
    st.session_state.replay_speed = 5
if "selected_log_row" not in st.session_state:
    st.session_state.selected_log_row = None
if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None
if "last_cluster_click" not in st.session_state:
    st.session_state.last_cluster_click = None
if "active_input_text" not in st.session_state:
    st.session_state.active_input_text = ""
if "selected_ai_model" not in st.session_state:
    st.session_state.selected_ai_model = "champion"
if "timeline_bucket" not in st.session_state:
    st.session_state.timeline_bucket = "day"
if "map_feed_mode" not in st.session_state:
    st.session_state.map_feed_mode = "World Live Disaster Map"

# Preset Operational Scenario Chips
PRESET_CHIPS = [
    {
        "label": "Casualty Trap (Harvey)",
        "text": "URGENT: Flood waters rising fast in Houston bayou, family of 5 trapped in attic, need boat rescue immediately!",
        "desc": "Medical & Life-Safety Emergency"
    },
    {
        "label": "Bridge Collapse (Irma)",
        "text": "CRITICAL: Overseas Highway bridge section washed out near Key West, power lines severed, complete road cutoff",
        "desc": "Infrastructure & Utility Failure"
    },
    {
        "label": "Relief Staging (Maria)",
        "text": "Red Cross boat crews deploying at San Juan harbor with clean drinking water, satellite phones, and medical kits",
        "desc": "Rescue & Supply Coordination"
    },
    {
        "label": "Wildfire Evac (California)",
        "text": "CalFire issues mandatory evacuation order for Santa Rosa Coffey Park sector as wind-driven firestorm advances",
        "desc": "Transit & Situation Advisory"
    }
]

# Main 2-Column Ops Console Layout ([3, 1] ratio)
col_left, col_right = st.columns([3, 1], gap="small")

# ==============================================================================
# LEFT COLUMN: Message Bar, Live World Map, Replay / Wire Controls, Triage Tabs
# ==============================================================================
with col_left:
    # 1. 1-Click Operational Test Scenario Chips
    st.markdown("<div class='label-upper' style='margin-bottom:4px;'>Operational Test Scenarios (1-Click AI Classification)</div>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    for chip, col in zip(PRESET_CHIPS, [c_p1, c_p2, c_p3, c_p4]):
        with col:
            if st.button(chip["label"], key=f"chip_{chip['label']}", help=chip["desc"], use_container_width=True):
                st.session_state.active_input_text = chip["text"]

    # 1b. Message Bar Form
    with st.form("message_input_form", clear_on_submit=False):
        user_text = st.text_area(
            "Disaster Message Input",
            value=st.session_state.active_input_text,
            placeholder="Paste or type a disaster message to classify, or select a scenario chip / recent news alert below...",
            height=60,
            max_chars=1000,
            label_visibility="collapsed"
        )
        
        c_mode, c_ev, c_model, c_sub = st.columns([2.0, 1.8, 1.8, 1.0])
        with c_mode:
            loc_mode = st.radio(
                "Location Mode",
                ["Click map", "Pick event", "Auto-detect", "None"],
                index=2,
                horizontal=True,
                label_visibility="collapsed"
            )
        with c_ev:
            chosen_event = None
            if loc_mode == "Pick event":
                event_options = list(DISASTER_EVENTS.keys())
                chosen_event = st.selectbox(
                    "Event",
                    event_options,
                    format_func=lambda x: DISASTER_EVENTS[x]["display_name"],
                    label_visibility="collapsed"
                )
        with c_model:
            model_options = {
                "champion": "Champion (Balanced LR)",
                "linear_svm": "Linear SVM (Calibrated)",
                "naive_bayes": "Naive Bayes (Fast)",
                "random_forest": "Random Forest (200 Trees)"
            }
            chosen_model = st.selectbox(
                "AI Model",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x],
                label_visibility="collapsed"
            )
            st.session_state.selected_ai_model = chosen_model
        with c_sub:
            submit_btn = st.form_submit_button("Classify", type="primary", use_container_width=True)

    # 1c. Batch CSV Expander
    with st.expander("Classify a CSV feed (max 5,000 rows)", expanded=False):
        csv_file = st.file_uploader("Upload CSV with 'text' column", type=["csv"], key="csv_upload")
        if csv_file is not None:
            try:
                upload_df = pd.read_csv(csv_file)
                text_col = next((c for c in ["text", "tweet_text", "message"] if c in upload_df.columns), None)
                if text_col:
                    raw_lines = upload_df[text_col].dropna().astype(str).tolist()
                    batch_res = models_svc.predict_batch(raw_lines, max_rows=5000)
                    st.success(f"Classified {batch_res['total_rows']} messages (Mean Confidence: {batch_res['mean_confidence']:.1%})")
                    for p in batch_res["predictions"]:
                        add_history_entry(
                            raw_text=p["text"],
                            clean_text=p["text"],
                            predicted_label=p["predicted_label"],
                            predicted_category=p["predicted_category"],
                            confidence=p["confidence"],
                            urgency=p["urgency"],
                            is_low_confidence=(p["confidence"] < 0.5),
                            is_user=True
                        )
                    st.rerun()
                else:
                    st.error("CSV must contain a 'text' or 'tweet_text' column.")
            except Exception as e:
                st.error(f"Failed to process CSV: {str(e)}")

    # Handle Form Submission directly with functional AI inference
    if submit_btn and user_text.strip():
        pred_res = models_svc.predict(user_text, model_name=chosen_model)
        
        auto_detected_ev = None
        if loc_mode == "Auto-detect":
            auto_detected_ev = models_svc.detect_event(user_text)
            
        if loc_mode == "Click map":
            st.session_state.pending_user_msg = {
                "raw_text": user_text,
                "clean_text": pred_res["clean_text"],
                "predicted_label": pred_res["predicted_label"],
                "predicted_category": pred_res["predicted_category"],
                "confidence": pred_res["confidence"],
                "urgency": pred_res["urgency"],
                "is_low_confidence": pred_res["is_low_confidence"],
                "probabilities": pred_res["probabilities"],
                "runner_up": pred_res["runner_up"],
                "is_user": True
            }
        elif (loc_mode == "Auto-detect" and auto_detected_ev) or (loc_mode == "Pick event" and chosen_event):
            target_ev = auto_detected_ev["event_id"] if auto_detected_ev else chosen_event
            ev_meta = DISASTER_EVENTS[target_ev]
            st.session_state.selected_event = target_ev
            add_history_entry(
                raw_text=user_text,
                clean_text=pred_res["clean_text"],
                predicted_label=pred_res["predicted_label"],
                predicted_category=pred_res["predicted_category"],
                confidence=pred_res["confidence"],
                urgency=pred_res["urgency"],
                is_low_confidence=pred_res["is_low_confidence"],
                runner_up_category=pred_res["runner_up"]["category"] if pred_res["runner_up"] else None,
                runner_up_confidence=pred_res["runner_up"]["confidence"] if pred_res["runner_up"] else None,
                lat=ev_meta["lat"],
                lon=ev_meta["lon"],
                is_user=True,
                event_name=target_ev
            )
            st.toast(f"AI matched location: {ev_meta['display_name']}")
            show_detail_dialog(pred_res, models_svc)
        else:  # Location: None
            add_history_entry(
                raw_text=user_text,
                clean_text=pred_res["clean_text"],
                predicted_label=pred_res["predicted_label"],
                predicted_category=pred_res["predicted_category"],
                confidence=pred_res["confidence"],
                urgency=pred_res["urgency"],
                is_low_confidence=pred_res["is_low_confidence"],
                runner_up_category=pred_res["runner_up"]["category"] if pred_res["runner_up"] else None,
                runner_up_confidence=pred_res["runner_up"]["confidence"] if pred_res["runner_up"] else None,
                is_user=True
            )
            show_detail_dialog(pred_res, models_svc)

    # Pending Map Click Notification Bar
    if st.session_state.pending_user_msg:
        c_warn, c_skip = st.columns([4, 1])
        with c_warn:
            st.warning("Click anywhere on the map to place this message pin at your coordinates.")
        with c_skip:
            if st.button("Skip location", key="skip_loc_btn"):
                pending = st.session_state.pending_user_msg
                add_history_entry(
                    raw_text=pending["raw_text"],
                    clean_text=pending["clean_text"],
                    predicted_label=pending["predicted_label"],
                    predicted_category=pending["predicted_category"],
                    confidence=pending["confidence"],
                    urgency=pending["urgency"],
                    is_low_confidence=pending["is_low_confidence"],
                    is_user=True
                )
                st.session_state.pending_user_msg = None
                show_detail_dialog(pending, models_svc)

    # Real-Time Inbound Emergency Dispatch Wire Marquee
    render_live_stream_ticker()

    # 2. Unified Real-World Operations Map Header
    c_maptitle, c_maptelemetry = st.columns([3, 2])
    with c_maptitle:
        st.markdown(
            "<div class='label-upper' style='margin-bottom:2px;'>Operational GIS Map &middot; Real-Time Satellite Telemetry</div>",
            unsafe_allow_html=True
        )
    with c_maptelemetry:
        st.markdown(
            f"""
            <div style='display:flex; justify-content:flex-end; align-items:center; gap:8px; font-family:"IBM Plex Mono", monospace; font-size:10px; color:{COLOR_TEXT_MUTED}; margin-top:2px;'>
                <span style='display:inline-block; width:7px; height:7px; border-radius:50%; background:{COLOR_OK}; box-shadow:0 0 6px {COLOR_OK};'></span>
                <span style='color:{COLOR_OK}; font-weight:700;'>LIVE TELEMETRY ACTIVE</span>
                <span>&middot;</span>
                <span>Maxar / Esri Satellite Orbital Imagery</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Center map based on selected event or global overview
    if st.session_state.selected_event and st.session_state.selected_event in DISASTER_EVENTS:
        ev_info = DISASTER_EVENTS[st.session_state.selected_event]
        center_lat, center_lon, zoom_lvl = ev_info["lat"], ev_info["lon"], 6
    else:
        center_lat, center_lon, zoom_lvl = 20.0, 10.0, 2

    # Exactly ONE unified photorealistic real-world orbital earth map
    folium_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_lvl,
        min_zoom=1,
        max_zoom=18,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr='Esri World Imagery, Maxar, Earthstar Geographics',
        control_scale=False
    )
    # Add crisp high-contrast country boundaries and place labels
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr='Esri Boundaries and Places',
        name="Labels & Borders",
        overlay=True,
        control=False
    ).add_to(folium_map)

    # Fullscreen control
    plugins.Fullscreen(position="topright").add_to(folium_map)

    # Inject real-time CSS radar waves into Leaflet DOM
    inject_map_radar_pulse_css(folium_map)

    # ==========================================================================
    # 1. VERIFIED GLOBAL DISASTER EPICENTERS (16 Real-World Disaster Hotspots)
    # ==========================================================================
    world_events = news_svc.get_world_map_events()
    for ge in world_events:
        g_lat, g_lon = ge["lat"], ge["lon"]
        g_type = ge["disaster_type"]
        g_sev = ge["severity"]
        g_urg = ge["urgency"]
        g_color = COLOR_DANGER if g_urg == "High" else (COLOR_ACCENT if g_urg == "Medium" else COLOR_OK)

        # Tactical badge label (compact and high contrast)
        if g_type == "earthquake":
            if "Magnitude" in g_sev:
                parts = g_sev.replace("Magnitude", "").strip().split()
                mag_text = f"M{parts[0]}" if parts else "M7+"
            elif "M" in g_sev:
                m_tokens = [p for p in g_sev.split() if p.startswith("M")]
                mag_text = m_tokens[0] if m_tokens else "QUAKE"
            else:
                mag_text = "QUAKE"
        elif g_type in ["hurricane", "cyclone"]:
            if "Category" in g_sev:
                cat_num = g_sev.split("Category")[1].strip().split()[0]
                mag_text = f"CAT {cat_num}"
            else:
                mag_text = "CYCLONE"
        elif g_type == "flood":
            mag_text = "FLOOD"
        elif g_type == "volcano":
            mag_text = "VOLCANO"
        else:
            mag_text = "WILDFIRE"

        # Concentric live animated radar wave ring
        folium.CircleMarker(
            location=[g_lat, g_lon],
            radius=16,
            color=g_color,
            weight=2.2,
            fill=True,
            fill_color=g_color,
            fill_opacity=0.28,
            className="epicenter-radar-pulse",
            tooltip=f"<b>{ge['title']}</b><br>Type: {g_type.title()} &middot; Severity: {g_sev}<br>Region: {ge['region']}<br>Source: {ge['source']}"
        ).add_to(folium_map)

        # Tactical monospace badge
        badge_icon_html = f"""
        <div style="font-family:'IBM Plex Mono', monospace; font-size:9px; font-weight:700; color:#FFFFFF; background:{g_color}; border:1.5px solid #FFFFFF; border-radius:3px; padding:1px 5px; box-shadow:0 0 10px {g_color}; text-align:center; white-space:nowrap; transform:translate(-50%, -50%); cursor:pointer;">
            {mag_text}
        </div>
        """
        folium.Marker(
            location=[g_lat, g_lon],
            icon=folium.DivIcon(html=badge_icon_html),
            popup=ge["title"]
        ).add_to(folium_map)

        # Impact buffer radius zone (dashed circle)
        zone_rad = ge.get("impact_radius_km", 75) * 1000
        folium.Circle(
            location=[g_lat, g_lon],
            radius=zone_rad,
            color=g_color,
            weight=1.5,
            dash_array="5, 6",
            fill=True,
            fill_color=g_color,
            fill_opacity=0.08,
            tooltip=f"{ge['title']} &middot; Impact Radius: {zone_rad/1000:.0f}km Buffer"
        ).add_to(folium_map)

        # Radiating spoke lines to localized ground sub-incidents
        for sub in ge.get("sub_incidents", []):
            sub_lat, sub_lon = sub["lat"], sub["lon"]
            sub_cat = sub.get("category", 0)
            sub_color = CATEGORY_CONFIG[sub_cat]["color"]

            folium.PolyLine(
                locations=[[g_lat, g_lon], [sub_lat, sub_lon]],
                color="#FFFFFF",
                weight=1.4,
                opacity=0.75,
                dash_array="4, 6",
                className="spoke-line-flow"
            ).add_to(folium_map)

            sub_tip = (
                f"<div style='font-family:sans-serif; font-size:11px;'>"
                f"<b>{sub['name']}</b><br>"
                f"<span style='color:{sub_color}; font-weight:600;'>{CATEGORY_NAMES[sub_cat]}</span><br>"
                f"<span>{sub['text']}</span>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[sub_lat, sub_lon],
                radius=5.5,
                color="#FFFFFF",
                weight=1.2,
                fill=True,
                fill_color=sub_color,
                fill_opacity=0.95,
                tooltip=folium.Tooltip(sub_tip)
            ).add_to(folium_map)

    # ==========================================================================
    # 2. BENCHMARK CRISISMMD EVENT HUBS (7 Historical Operational Zones)
    # ==========================================================================
    events_list = data_svc.get_events_summary()
    sel_ev = st.session_state.selected_event

    for ev in events_list:
        ev_id = ev["event_id"]
        ev_lat, ev_lon = ev["lat"], ev["lon"]
        is_sel = (sel_ev == ev_id)

        # Tactical hub ring
        folium.CircleMarker(
            location=[ev_lat, ev_lon],
            radius=18 if is_sel else 13,
            color="#F2A33A" if is_sel else "#6C9BD2",
            weight=2 if is_sel else 1.5,
            fill=True,
            fill_color="#F2A33A" if is_sel else "#16212C",
            fill_opacity=0.35 if is_sel else 0.15,
            className="epicenter-radar-pulse" if is_sel else None,
            tooltip=f"<b>{ev['display_name']} [CrisisMMD Benchmark Hub]</b><br>Type: {ev['disaster_type'].title()}<br>Messages: {ev['total_messages']}"
        ).add_to(folium_map)

        # Center dot
        folium.CircleMarker(
            location=[ev_lat, ev_lon],
            radius=5 if is_sel else 4,
            color="#FFFFFF",
            weight=1.5,
            fill=True,
            fill_color="#F2A33A" if is_sel else "#6C9BD2",
            fill_opacity=1.0,
            popup=ev_id
        ).add_to(folium_map)

        # Impact Zone Buffer Radius
        if is_sel or sel_ev is None:
            zone_radius_meters = 110000 if "wildfire" in ev["disaster_type"] else (150000 if "hurricane" in ev["disaster_type"] else 80000)
            folium.Circle(
                location=[ev_lat, ev_lon],
                radius=zone_radius_meters,
                color="#E5534B" if is_sel else "#2A3947",
                weight=1.2,
                dash_array="5, 6",
                fill=True,
                fill_color="#E5534B",
                fill_opacity=0.08 if is_sel else 0.02,
                tooltip=f"{ev['display_name']} &middot; Impact Radius: {zone_radius_meters/1000:.0f}km Buffer Zone"
            ).add_to(folium_map)

        # Radiating Spoke Lines to Localized Sub-Incidents
        sub_list = DISASTER_SUB_INCIDENTS.get(ev_id, [])
        for sub in sub_list:
            sub_lat, sub_lon = sub["lat"], sub["lon"]
            sub_cat = sub["category"]
            sub_color = CATEGORY_CONFIG[sub_cat]["color"]

            folium.PolyLine(
                locations=[[ev_lat, ev_lon], [sub_lat, sub_lon]],
                color="#8B97A6" if is_sel else "#425061",
                weight=1.2 if is_sel else 0.8,
                opacity=0.65 if is_sel else 0.35,
                dash_array="4, 6",
                className="spoke-line-flow"
            ).add_to(folium_map)

            sub_tip = (
                f"<div style='font-family:sans-serif; font-size:11px;'>"
                f"<b>{sub['name']}</b><br>"
                f"<span style='color:{sub_color}; font-weight:600;'>{CATEGORY_NAMES[sub_cat]}</span><br>"
                f"<span>{sub['text']}</span>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[sub_lat, sub_lon],
                radius=5.5 if is_sel else 4,
                color="#FFFFFF" if is_sel else sub_color,
                weight=1.5 if is_sel else 1.0,
                fill=True,
                fill_color=sub_color,
                fill_opacity=0.92,
                tooltip=folium.Tooltip(sub_tip)
            ).add_to(folium_map)

    # ==========================================================================
    # 3. USER CLASSIFIED PINS (Radiating Spoke to Nearest Epicenter Hub)
    # ==========================================================================
    user_pins = get_user_pins()
    for up in user_pins:
        p_label = up.get("predicted_label", 4)
        p_color = CATEGORY_CONFIG[p_label]["color"]
        up_text = html.escape(up.get("raw_text", "")[:45])
        u_lat, u_lon = up["lat"], up["lon"]

        nearest_ev_meta = min(
            DISASTER_EVENTS.values(),
            key=lambda item: abs(item["lat"] - u_lat) + abs(item["lon"] - u_lon)
        )
        folium.PolyLine(
            locations=[[nearest_ev_meta["lat"], nearest_ev_meta["lon"]], [u_lat, u_lon]],
            color=COLOR_ACCENT,
            weight=1.6,
            opacity=0.85
        ).add_to(folium_map)

        up_tooltip = f"""
        <div style="font-family:'IBM Plex Sans', sans-serif; font-size:11px;">
            <b style="color:{COLOR_ACCENT};">YOU [User Pin]</b>: {up.get('predicted_category')}<br>
            <span style="color:#8B97A6;">Confidence:</span> {up.get('confidence', 1.0):.1%}<br>
            <span>{up_text}...</span>
        </div>
        """
        folium.CircleMarker(
            location=[u_lat, u_lon],
            radius=8,
            color="#FFFFFF",
            fill=True,
            fill_color=p_color,
            fill_opacity=0.95,
            weight=2.5,
            tooltip=folium.Tooltip(up_tooltip)
        ).add_to(folium_map)

    # Display Exactly ONE Photorealistic Map Canvas
    map_output = st_folium(
        folium_map,
        width="100%",
        height=360,
        returned_objects=["last_clicked", "last_object_clicked", "last_object_clicked_popup"],
        key="unified_operations_map"
    )

    # Floating Operational GIS Map Legend (Unified Ops Replica)
    st.markdown(
        f"""
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:12px; background:#151A21; border:1px solid #262F3A; border-radius:4px; padding:5px 12px; margin-top:-6px; font-size:10px; color:{COLOR_TEXT_MUTED};">
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:10px; height:10px; border-radius:50%; border:2px solid {COLOR_ACCENT}; background:{COLOR_ACCENT}44;"></span>
                <span>Active Disaster Epicenter</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:14px; height:0px; border-top:1px dashed {COLOR_DANGER};"></span>
                <span>Impact Buffer Zone</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#E5534B;"></span>
                <span>Casualties / Medical</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#F2A33A;"></span>
                <span>Infrastructure Damage</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#3FB6A8;"></span>
                <span>Rescue & Supplies</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#6C9BD2;"></span>
                <span>Transit Advisory</span>
            </div>
            <div style="display:inline-flex; align-items:center; gap:5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#FFFFFF; border:1.5px solid {COLOR_ACCENT};"></span>
                <span>User Pin</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Map Click Handling
    if st.session_state.pending_user_msg and map_output.get("last_clicked"):
        click_data = map_output["last_clicked"]
        click_id = (round(float(click_data["lat"]), 4), round(float(click_data["lng"]), 4))
        if click_id != st.session_state.last_map_click:
            st.session_state.last_map_click = click_id
            click_lat = float(click_data["lat"])
            click_lon = float(click_data["lng"])
            pending = st.session_state.pending_user_msg
            
            add_history_entry(
                raw_text=pending["raw_text"],
                clean_text=pending["clean_text"],
                predicted_label=pending["predicted_label"],
                predicted_category=pending["predicted_category"],
                confidence=pending["confidence"],
                urgency=pending["urgency"],
                is_low_confidence=pending["is_low_confidence"],
                lat=click_lat,
                lon=click_lon,
                is_user=True
            )
            st.session_state.pending_user_msg = None
            show_detail_dialog(pending, models_svc)

    # Event Cluster Click Handling
    if map_output.get("last_object_clicked"):
        obj = map_output["last_object_clicked"]
        if isinstance(obj, dict) and "lat" in obj and "lng" in obj:
            obj_id = (round(float(obj["lat"]), 3), round(float(obj["lng"]), 3))
            if obj_id != st.session_state.last_cluster_click:
                st.session_state.last_cluster_click = obj_id
                o_lat, o_lng = float(obj["lat"]), float(obj["lng"])
                nearest_ev = min(
                    DISASTER_EVENTS.items(),
                    key=lambda item: abs(item[1]["lat"] - o_lat) + abs(item[1]["lon"] - o_lng)
                )
                dist = abs(nearest_ev[1]["lat"] - o_lat) + abs(nearest_ev[1]["lon"] - o_lng)
                if dist < 2.5 and st.session_state.selected_event != nearest_ev[0]:
                    st.session_state.selected_event = nearest_ev[0]
                    st.rerun()

    # 3. Test Set Replay Sub-Bar (Always active & docked below unified map)
    c_play, c_pause, c_step, c_spd, c_scrub, c_tag = st.columns([0.7, 0.7, 0.9, 1.1, 2.8, 2.2])
    with c_play:
        if st.button("Play", key="btn_replay_play", type="primary" if st.session_state.replay_playing else "secondary"):
            st.session_state.replay_playing = True
    with c_pause:
        if st.button("Pause", key="btn_replay_pause", type="primary" if not st.session_state.replay_playing else "secondary"):
            st.session_state.replay_playing = False
    with c_step:
        if st.button("Step +25", key="btn_replay_step"):
            st.session_state.replay_step = min(len(data_svc.test_cache), st.session_state.replay_step + 25)
    with c_spd:
        st.session_state.replay_speed = st.selectbox(
            "Speed", [1, 5, 20, 60],
            index=[1, 5, 20, 60].index(st.session_state.replay_speed),
            format_func=lambda x: f"{x}x",
            label_visibility="collapsed"
        )
    with c_scrub:
        total_replay = len(data_svc.test_cache)
        scrub_val = st.slider(
            "Replay position",
            min_value=0,
            max_value=total_replay,
            value=st.session_state.replay_step,
            label_visibility="collapsed"
        )
        if scrub_val != st.session_state.replay_step:
            st.session_state.replay_step = scrub_val
    with c_tag:
        st.markdown(
            """
            <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.07em; color:#8B97A6; padding-top:6px; text-align:right;">
                Replay &ndash; test set, 2017
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. Tabbed Triage Queue & Recent Disaster News Wire
    t_tab1, t_tab2 = st.tabs(["Message Log (Triage Queue)", "Recent Disaster News Wire (Live Feeds)"])

    with t_tab1:
        # Message Log Table
        user_msgs = get_user_messages()
        user_rows = []
        for um in user_msgs:
            cat_p = um["predicted_label"]
            user_rows.append({
                "Time": um["created_at"][11:19],
                "Event": um.get("event_name", "User Pin"),
                "Message": f"[YOU] {um['raw_text']}",
                "Category": CATEGORY_NAMES.get(cat_p, "Unknown"),
                "Confidence": float(um["confidence"]),
                "Status": "User",
                "_raw": um
            })
            
        test_slice = data_svc.test_cache
        if st.session_state.selected_event:
            test_slice = test_slice[test_slice["event_name"] == st.session_state.selected_event]
            
        if st.session_state.replay_step > 0:
            test_slice = test_slice.iloc[:st.session_state.replay_step]
            
        triage_map = get_all_triage_statuses()
        test_rows = []
        for _, tr in test_slice.iloc[::-1].head(120).iterrows():
            tid = str(tr["tweet_id"])
            test_rows.append({
                "Time": tr["timestamp"][11:19] if "T" in str(tr["timestamp"]) else str(tr["timestamp"])[:8],
                "Event": DISASTER_EVENTS.get(tr["event_name"], {}).get("display_name", tr["event_name"]),
                "Message": tr["tweet_text"],
                "Category": tr["predicted_category"],
                "Confidence": float(tr["confidence"]),
                "Status": triage_map.get(tid, "Unreviewed").title(),
                "_raw": dict(tr)
            })
            
        combined_log = user_rows + test_rows
        log_df = pd.DataFrame(combined_log)
        
        if not log_df.empty:
            display_df = log_df[["Time", "Event", "Message", "Category", "Confidence", "Status"]]
            
            selection_event = st.dataframe(
                display_df,
                use_container_width=True,
                height=240,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "Event": st.column_config.TextColumn("Event", width="medium"),
                    "Message": st.column_config.TextColumn("Message", width="large"),
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small")
                }
            )
            
            if selection_event and selection_event.selection and selection_event.selection.rows:
                sel_idx = selection_event.selection.rows[0]
                if st.session_state.selected_log_row != sel_idx:
                    st.session_state.selected_log_row = sel_idx
                    selected_msg_raw = combined_log[sel_idx]["_raw"]
                    show_detail_dialog(selected_msg_raw, models_svc)
            else:
                st.session_state.selected_log_row = None
        else:
            st.info("No messages match current event and replay filters.")

    with t_tab2:
        # Recent Disaster News Wire Cards
        st.markdown("<div class='label-upper' style='margin-bottom:6px;'>Real-Time Crisis Bulletins &middot; 1-Click AI Classification</div>", unsafe_allow_html=True)
        recent_news = news_svc.get_recent_news_wire()
        
        for n_item in recent_news:
            urg_color = COLOR_DANGER if n_item["urgency"] == "High" else (COLOR_ACCENT if n_item["urgency"] == "Medium" else COLOR_OK)
            
            with st.container():
                st.markdown(
                    f"""
                    <div class="ops-panel-sub" style="margin-bottom:6px; padding:8px 12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; color:{COLOR_TEXT}; font-size:13px;">{n_item['headline']}</span>
                            <span style="background:{urg_color}22; border:1px solid {urg_color}66; color:{urg_color}; padding:1px 6px; border-radius:3px; font-size:10px; font-weight:700; text-transform:uppercase;">
                                {n_item['urgency']} URGENCY
                            </span>
                        </div>
                        <div style="display:flex; gap:12px; font-size:11px; color:{COLOR_TEXT_MUTED}; margin-bottom:5px;">
                            <span class="mono">{n_item['time']}</span> &middot;
                            <span>{n_item['source']}</span> &middot;
                            <span style="color:{COLOR_ACCENT};">{n_item['region']}</span>
                        </div>
                        <div style="font-size:12px; color:{COLOR_TEXT}; line-height:1.4; margin-bottom:6px;">
                            {n_item['text']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                c_btn1, c_btn2, _ = st.columns([1.6, 1.4, 3])
                with c_btn1:
                    if st.button(f"Classify with AI", key=f"btn_news_ai_{n_item['id']}", type="primary"):
                        news_pred = models_svc.predict(n_item["text"], model_name=st.session_state.selected_ai_model)
                        add_history_entry(
                            raw_text=n_item["text"],
                            clean_text=news_pred["clean_text"],
                            predicted_label=news_pred["predicted_label"],
                            predicted_category=news_pred["predicted_category"],
                            confidence=news_pred["confidence"],
                            urgency=news_pred["urgency"],
                            is_low_confidence=news_pred["is_low_confidence"],
                            lat=n_item["lat"],
                            lon=n_item["lon"],
                            is_user=True,
                            event_name=n_item["region"]
                        )
                        st.toast(f"Classified & Mapped: {n_item['region']}")
                        show_detail_dialog(news_pred, models_svc)
                with c_btn2:
                    if st.button(f"Load to Input", key=f"btn_news_load_{n_item['id']}"):
                        st.session_state.active_input_text = n_item["text"]
                        st.rerun()

# ==============================================================================
# RIGHT COLUMN: Telemetry Spike Chart (Image 1) & Operational Panel
# ==============================================================================
with col_right:
    # 1. Event Scope Header
    sel_ev = st.session_state.selected_event
    if sel_ev and sel_ev in DISASTER_EVENTS:
        ev_meta = DISASTER_EVENTS[sel_ev]
        st.markdown(
            f"""
            <div class="ops-panel" style="margin-bottom:6px; padding:8px 10px;">
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <div style="font-size:14px; font-weight:700; color:{COLOR_TEXT};">{ev_meta['display_name']}</div>
                    <span style="font-size:10px; font-weight:600; text-transform:uppercase; color:{COLOR_ACCENT};">{ev_meta['disaster_type']}</span>
                </div>
                <div style="font-size:11px; color:{COLOR_TEXT_MUTED}; margin-top:2px;">Verified 2017 CrisisMMD Impact Zone</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Show all events", use_container_width=True, key="clear_ev_btn"):
            st.session_state.selected_event = None
            st.session_state.last_cluster_click = "CLEARED"
            st.rerun()
    else:
        st.markdown(
            f"""
            <div class="ops-panel" style="margin-bottom:6px; padding:8px 10px;">
                <div style="font-size:14px; font-weight:700; color:{COLOR_TEXT};">Global Operations Scope</div>
                <div style="font-size:11px; color:{COLOR_TEXT_MUTED}; margin-top:2px;">
                    16 Active Global Hotspots &middot; 7 Benchmark Hubs &middot; 2,237 Test Tweets
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Inbound Velocity Monitor with Live 60Hz Stream and 2017 History Switcher
    c_tel_hdr, c_tel_toggle = st.columns([1.3, 1.7])
    with c_tel_hdr:
        st.markdown("<div class='label-upper' style='margin-bottom:2px;'>Telemetry Graph</div>", unsafe_allow_html=True)
    with c_tel_toggle:
        if "telemetry_view_mode" not in st.session_state:
            st.session_state.telemetry_view_mode = "Live 60Hz Stream"
        t_view = st.radio(
            "Graph View",
            ["Live 60Hz Stream", "2017 History"],
            index=0 if st.session_state.telemetry_view_mode == "Live 60Hz Stream" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="telemetry_view_radio"
        )
        st.session_state.telemetry_view_mode = t_view

    if t_view == "Live 60Hz Stream":
        render_live_oscilloscope_graph(height=148)
    else:
        timeline_data = data_svc.get_timeline(event=sel_ev, bucket=st.session_state.timeline_bucket)
        if timeline_data:
            t_times = [b["time"][:10] for b in timeline_data]
            t_totals = [b["total"] for b in timeline_data]
            t_high_urg = [b["counts"].get("Affected People & Medical Emergencies", 0) + b["counts"].get("Infrastructure Damage", 0) for b in timeline_data]

            t_fig = go.Figure()
            t_fig.add_trace(go.Scatter(
                x=t_times,
                y=t_totals,
                name="Total Posts",
                mode='lines',
                line=dict(color="#A78BFA", width=1.8),
                fill='tozeroy',
                fillcolor="rgba(167, 139, 250, 0.12)"
            ))
            t_fig.add_trace(go.Scatter(
                x=t_times,
                y=t_high_urg,
                name="High Urgency",
                mode='lines',
                line=dict(color="#E5534B", width=1.4, dash="dot"),
            ))
            t_layout = get_console_plotly_layout(height=130)
            t_layout["margin"] = dict(l=15, r=10, t=10, b=18)
            t_layout["legend"] = dict(orientation="h", y=1.12, x=1, xanchor="right", font=dict(size=9, color=COLOR_TEXT_MUTED))
            t_fig.update_layout(t_layout)
            st.plotly_chart(t_fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    # Filtered test slice for stats
    current_slice = data_svc.test_cache
    if sel_ev:
        current_slice = current_slice[current_slice["event_name"] == sel_ev]

    total_in_view = len(current_slice)
    high_urg_count = len(current_slice[current_slice["urgency"] == "High"])
    mean_conf = float(current_slice["confidence"].mean()) if total_in_view > 0 else 0.0
    
    triage_all = get_all_triage_statuses()
    v_tids = set(current_slice["tweet_id"].astype(str))
    reviewed_in_view = sum(1 for tid in v_tids if triage_all.get(tid) == "reviewed")
    flagged_in_view = sum(1 for tid in v_tids if triage_all.get(tid) == "flagged")

    # 3. Grouped Stats Panel (Compact Divided Box)
    st.markdown(
        f"""
        <div class="ops-panel" style="margin-bottom:6px; padding:7px 10px;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid {COLOR_BORDER}; padding-bottom:4px;">
                <span class="label-upper">Messages In View</span>
                <span class="mono" style="font-weight:700; color:{COLOR_TEXT}; font-size:12px;">{total_in_view:,}</span>
            </div>
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid {COLOR_BORDER}; padding:4px 0;">
                <span class="label-upper">High Urgency</span>
                <span class="mono" style="font-weight:700; color:{COLOR_DANGER}; font-size:12px;">{high_urg_count}</span>
            </div>
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid {COLOR_BORDER}; padding:4px 0;">
                <span class="label-upper">Flagged / Reviewed</span>
                <span class="mono" style="font-weight:600; color:{COLOR_ACCENT}; font-size:11px;">{flagged_in_view} / {reviewed_in_view}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding-top:4px;">
                <span class="label-upper">Mean Confidence</span>
                <span class="mono" style="font-weight:700; color:{COLOR_TEXT}; font-size:12px;">{mean_conf:.1%}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Category Distribution Bars
    st.markdown("<div class='label-upper' style='margin-bottom:4px;'>Category Distribution</div>", unsafe_allow_html=True)
    cat_counts = current_slice["predicted_category"].value_counts()
    for cat_idx, cat_name in CATEGORY_NAMES.items():
        c_count = int(cat_counts.get(cat_name, 0))
        c_pct = (c_count / total_in_view * 100) if total_in_view > 0 else 0.0
        c_color = CATEGORY_CONFIG[cat_idx]["color"]
        short_name = cat_name if len(cat_name) <= 22 else cat_name[:20] + ".."
        
        st.markdown(
            f"""
            <div style="margin-bottom:3px;">
                <div style="display:flex; justify-content:space-between; font-size:10px; margin-bottom:1px;">
                    <span style="color:{COLOR_TEXT};">{short_name}</span>
                    <span class="mono" style="color:{COLOR_TEXT_MUTED};">{c_count} ({c_pct:.0f}%)</span>
                </div>
                <div style="height:3px; width:100%; background:{COLOR_BORDER}; border-radius:2px; overflow:hidden;">
                    <div style="height:100%; width:{c_pct}%; background:{c_color};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 5. Needs Review List (lowest-confidence high-urgency messages)
    st.markdown("<div class='label-upper' style='margin-top:6px; margin-bottom:3px;'>Needs Review (High Urgency)</div>", unsafe_allow_html=True)
    high_urg_msgs = current_slice[current_slice["urgency"] == "High"].sort_values("confidence", ascending=True).head(4)
    
    if not high_urg_msgs.empty:
        for idx_nr, row_nr in high_urg_msgs.iterrows():
            nr_tid = str(row_nr["tweet_id"])
            nr_text = row_nr["tweet_text"][:48] + "..."
            nr_conf = float(row_nr["confidence"])
            btn_label = f"[{nr_conf:.0%}] {nr_text}"
            if st.button(btn_label, key=f"nr_btn_{nr_tid}_{idx_nr}", use_container_width=True):
                show_detail_dialog(dict(row_nr), models_svc)
    else:
        st.caption("No urgent unreviewed items in view.")

    # 6. Live Cluster Health HUD
    render_live_system_hud()
