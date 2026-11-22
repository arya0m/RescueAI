"""
RescueAI: AI-Based Disaster Relief Message Classification System
Main application entry point with modular st.navigation routing.
"""

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(CURRENT_DIR) == "app":
    ROOT_DIR = os.path.dirname(CURRENT_DIR)
    APP_DIR = CURRENT_DIR
else:
    ROOT_DIR = CURRENT_DIR
    APP_DIR = os.path.join(ROOT_DIR, "app")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(1, APP_DIR)

import streamlit as st

try:
    from app.components import apply_custom_css, render_sidebar
except ModuleNotFoundError:
    from components import apply_custom_css, render_sidebar

st.set_page_config(
    layout="wide",
    page_title="RescueAI",
    initial_sidebar_state="collapsed"
)

apply_custom_css()
render_sidebar()

def page_path(name: str) -> str:
    return os.path.join(ROOT_DIR, "app", "pages", name)

pages = [
    st.Page(page_path("1_Console.py"), title="Console", default=True),
    st.Page(page_path("2_Classify.py"), title="Classify"),
    st.Page(page_path("3_Explorer.py"), title="Explorer"),
    st.Page(page_path("4_Models.py"), title="Models"),
    st.Page(page_path("5_History.py"), title="History"),
    st.Page(page_path("6_About.py"), title="About"),
]

pg = st.navigation(pages)
pg.run()
