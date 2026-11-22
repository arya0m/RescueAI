"""
RescueAI: About & Citation Page (Page 6)
System architecture, QCRI CrisisMMD v2.0 dataset citation, 8-to-5 label taxonomy,
and operational decision-support ethical advisory.
"""

import sys
import os
import streamlit as st

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
    from app.components import apply_custom_css, render_sidebar
except ModuleNotFoundError:
    from components import apply_custom_css, render_sidebar

apply_custom_css()
render_sidebar()

st.markdown(
    f"""
    <div style="margin-bottom: 12px; border-bottom: 1px solid {COLOR_BORDER}; padding-bottom: 8px;">
        <h1 style="font-size: 20px; font-weight: 700; color: {COLOR_TEXT}; margin: 0 0 2px 0;">
            About RescueAI &middot; Architecture & Citation
        </h1>
        <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">
            Operational Decision-Support System for High-Velocity Social Media Disaster Triage.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

col_info, col_arch = st.columns([1.2, 1.0], gap="medium")

with col_info:
    st.markdown(
        f"""
        <div class="ops-panel" style="margin-bottom: 12px; padding: 12px 14px;">
            <div style="font-size: 14px; font-weight: 700; color: {COLOR_TEXT}; margin-bottom: 4px;">
                Humanitarian Motivation & Information Overload
            </div>
            <div style="font-size: 12px; color: {COLOR_TEXT}; line-height: 1.5;">
                During catastrophic disasters (hurricanes, earthquakes, wildfires, and floods), thousands of messages are published every minute across social media platforms. Emergency coordinators struggle with severe information overload: critical life-safety pleas and utility failures frequently get lost among opinions, general banter, and media commentary.
                <br><br>
                <b>RescueAI</b> serves as an automated triage sieve: extracting linguistic features via Sublinear TF-IDF collocations and classifying inbound posts into five prioritized action categories using cost-sensitive supervised machine learning.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='label-upper' style='margin-bottom:6px;'>8-to-5 Scientific Label Taxonomy Consolidation</div>", unsafe_allow_html=True)
    taxonomy_table = """
| Class ID | Target Category Name | Original QCRI Labels Mapped | Operational Urgency |
|:---:|---|---|:---:|
| **0** | **Affected People & Medical Emergencies** | `affected_individuals`, `injured_or_dead_people`, `missing_or_found_people` | **High** |
| **1** | **Infrastructure Damage** | `infrastructure_and_utility_damage`, `vehicle_damage` | **High** |
| **2** | **Rescue & Volunteering** | `rescue_volunteering_or_donation_effort` | **Medium** |
| **3** | **Other Relevant Information** | `other_relevant_information` | **Low** |
| **4** | **Not Humanitarian / Irrelevant** | `not_humanitarian` | **None** |
    """
    st.markdown(taxonomy_table)

with col_arch:
    st.markdown(
        f"""
        <div class="ops-panel" style="margin-bottom: 12px; padding: 12px 14px;">
            <div style="font-size: 14px; font-weight: 700; color: {COLOR_TEXT}; margin-bottom: 6px;">
                End-to-End ML Pipeline Architecture
            </div>
            <div style="font-size: 11px; color: {COLOR_TEXT_MUTED}; line-height: 1.6;">
                1. <b>Text Normalization</b>: Regex cleaning, URL extraction, Twitter handle masking, punctuation stripping, lowercasing.<br>
                2. <b>Feature Extraction</b>: Sublinear TF-IDF ($1 + \\log(\\text{{tf}})$) with unigram &amp; bigram collocations (10,000 dimensions).<br>
                3. <b>Champion Classifier</b>: Balanced Multi-Class Logistic Regression ($C=0.5$) with Softmax activation and inverse frequency class weighting.<br>
                4. <b>Interpretability Engine</b>: Honest feature attribution ($w_i \\cdot x_i$) identifying class-specific evidence vs runner-up evidence.<br>
                5. <b>Human-in-the-Loop Thresholding</b>: Automated routing flags messages where confidence &lt; $t$ for manual operator review.<br>
                6. <b>Persistence Layer</b>: Standard library SQLite database (<code>data/rescueai.db</code>) synchronizing triage states and analyst audit feedback.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="ops-panel" style="margin-bottom: 12px; padding: 12px 14px; border-left: 3px solid {COLOR_DANGER};">
            <div style="font-size: 13px; font-weight: 700; color: {COLOR_DANGER}; margin-bottom: 4px;">
                Operational &amp; Ethical Disclaimer
            </div>
            <div style="font-size: 11px; color: {COLOR_TEXT}; line-height: 1.5;">
                RescueAI is an assistive decision-support classifier intended exclusively to prioritize high-volume social media streams for human emergency coordinators.
                <br><br>
                &bull; Predictions do <b>NOT</b> establish verified ground truth.<br>
                &bull; Social media feeds contain rumors, bot spam, and satire.<br>
                &bull; This system must <b>NOT</b> replace official emergency 911/999/112 dispatch protocols or automate physical resource deployment without human validation.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div class='label-upper' style='margin-top:10px; margin-bottom:6px;'>Academic References &amp; Dataset Citation</div>", unsafe_allow_html=True)
st.markdown("""
1. **Alam, F., Ofli, F., & Imran, M. (2018).** *CrisisMMD: Multimodal Twitter Datasets from Natural Disasters.* Proceedings of the 12th International AAAI Conference on Web and Social Media (ICWSM-18), Stanford, California.
2. **Imran, M., Castillo, C., Diaz, F., & Vieweg, S. (2015).** *Processing Social Media Messages in Mass Emergency: A Survey.* ACM Computing Surveys (CSUR), 47(4), 1-38.
3. **Pedregosa, F., et al. (2011).** *Scikit-learn: Machine Learning in Python.* Journal of Machine Learning Research (JMLR), 12, 2825-2830.
""")
