"""
RescueAI Streamlit Theme and Plotly Console Template.
Imports shared tokens from rescueai.constants.
"""

from rescueai.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_DANGER, COLOR_OK,
    CATEGORY_CONFIG, CATEGORY_NAMES
)

# Design token aliases
TEXT_PRIMARY = COLOR_TEXT
TEXT_SECONDARY = COLOR_TEXT_MUTED
BACKGROUND = COLOR_BG
SURFACE = COLOR_SURFACE
SURFACE_RAISED = COLOR_SURFACE_2
BORDER = COLOR_BORDER
ACCENT = COLOR_ACCENT
DANGER = COLOR_DANGER
OK = COLOR_OK

# Plotly dark console template
def get_console_plotly_layout(height: int = 240, title: str = "") -> dict:
    return dict(
        height=height,
        title=dict(
            text=f"<span style='font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:{COLOR_TEXT_MUTED};'>{title}</span>" if title else "",
            x=0.01,
            y=0.98,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=16, t=30 if title else 12, b=24),
        font=dict(family="IBM Plex Sans, sans-serif", size=11, color=COLOR_TEXT_MUTED),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLOR_BORDER,
            gridwidth=0.7,
            zeroline=False,
            tickfont=dict(color=COLOR_TEXT_MUTED, size=10, family="IBM Plex Mono"),
            linecolor=COLOR_BORDER,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLOR_BORDER,
            gridwidth=0.7,
            zeroline=False,
            tickfont=dict(color=COLOR_TEXT_MUTED, size=10, family="IBM Plex Mono"),
            linecolor=COLOR_BORDER,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLOR_TEXT, size=10),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
