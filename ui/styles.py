import streamlit as st

# --- Design tokens -----------------------------------------------------
# One accent color, two palettes (light/dark). Keep it simple: slate
# neutrals + a single indigo accent, used consistently for anything
# interactive or "brand" (buttons, active badges, links).

LIGHT = {
    "bg": "#f7f8fa",
    "surface": "#ffffff",
    "surface_alt": "#f1f3f6",
    "border": "#e5e7eb",
    "text": "#161a20",
    "text_muted": "#6b7280",
    "accent": "#4f46e5",
    "accent_hover": "#4338ca",
    "accent_soft": "#eef2ff",
    "success": "#047857",
    "success_bg": "#ecfdf5",
    "success_border": "#a7f3d0",
    "warning": "#b45309",
    "warning_bg": "#fffbeb",
    "warning_border": "#fde68a",
    "danger": "#b91c1c",
    "danger_bg": "#fef2f2",
    "danger_border": "#fecaca",
    "shadow": "0 1px 2px rgba(16,24,40,0.06), 0 2px 6px rgba(16,24,40,0.05)",
}

DARK = {
    "bg": "#0d0f13",
    "surface": "#15181f",
    "surface_alt": "#1b1f28",
    "border": "#2a2f3a",
    "text": "#e8eaed",
    "text_muted": "#9aa1ac",
    "accent": "#818cf8",
    "accent_hover": "#a5b4fc",
    "accent_soft": "#1e1e3f",
    "success": "#34d399",
    "success_bg": "#0c2a20",
    "success_border": "#155e42",
    "warning": "#fbbf24",
    "warning_bg": "#2e2205",
    "warning_border": "#6b4e0a",
    "danger": "#f87171",
    "danger_bg": "#2e0f0f",
    "danger_border": "#6b1f1f",
    "shadow": "0 1px 2px rgba(0,0,0,0.35), 0 2px 8px rgba(0,0,0,0.35)",
}


def apply_executive_styles(dark_mode: bool = False):
    p = DARK if dark_mode else LIGHT

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, .stApp, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background-color: {p['bg']};
        }}

        /* Force readable text everywhere, regardless of Streamlit's own theme */
        .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
            color: {p['text']};
        }}
        .stApp .stCaption, .stApp small, [data-testid="stCaptionContainer"] {{
            color: {p['text_muted']} !important;
        }}

        h1, h2, h3 {{
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        hr {{
            border-color: {p['border']} !important;
            opacity: 1;
        }}

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background-color: {p['surface_alt']};
            border-right: 1px solid {p['border']};
        }}
        section[data-testid="stSidebar"] * {{
            color: {p['text']} !important;
        }}
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] small {{
            color: {p['text_muted']} !important;
        }}

        /* ---------- Buttons (broad selector — catches file uploader's
           internal button too, which Streamlit doesn't wrap in .stButton) ---------- */
        .stApp button {{
            background-color: {p['surface']};
            color: {p['text']} !important;
            border: 1px solid {p['border']};
            border-radius: 8px;
            font-weight: 500;
            box-shadow: none;
            transition: all 0.15s ease;
        }}
        .stApp button:hover:not(:disabled) {{
            border-color: {p['accent']};
            color: {p['accent']} !important;
        }}
        .stApp button:disabled {{
            opacity: 0.55;
        }}
        .stApp button[kind="primary"] {{
            background-color: {p['accent']};
            color: #ffffff !important;
            border: none;
        }}
        .stApp button[kind="primary"]:hover:not(:disabled) {{
            background-color: {p['accent_hover']};
            color: #ffffff !important;
        }}

        /* ---------- Cards / containers ---------- */
        div[data-testid="stExpander"] {{
            background-color: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 10px;
            box-shadow: {p['shadow']};
        }}

        /* ---------- Metric boxes ---------- */
        div[data-testid="stMetric"] {{
            background-color: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 10px;
            padding: 14px 16px;
            box-shadow: {p['shadow']};
        }}
        div[data-testid="stMetric"] * {{
            color: {p['text']} !important;
        }}
        div[data-testid="stMetricLabel"] * {{
            color: {p['text_muted']} !important;
            font-weight: 500 !important;
        }}

        /* ---------- Chat messages ---------- */
        div[data-testid="stChatMessage"] {{
            background-color: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 12px;
            box-shadow: {p['shadow']};
            padding: 4px 6px;
            margin-bottom: 10px;
        }}

        div[data-testid="stChatInput"] {{
            border-radius: 10px;
        }}
        div[data-testid="stChatInput"] textarea {{
            background-color: {p['surface']};
            color: {p['text']};
        }}
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {p['text_muted']};
            opacity: 1;
        }}

        /* ---------- File uploader ---------- */
        section[data-testid="stFileUploaderDropzone"] {{
            background-color: {p['surface']};
            border: 1.5px dashed {p['border']};
            border-radius: 10px;
        }}
        section[data-testid="stFileUploaderDropzone"] * {{
            color: {p['text']} !important;
        }}

        /* ---------- Pills / badges ---------- */
        .status-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.75rem;
            border: 1px solid {p['border']};
            background-color: {p['accent_soft']};
            color: {p['accent']};
        }}

        .conf-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.8rem;
            border: 1px solid;
            margin: 6px 0 2px 0;
        }}
        .conf-high {{
            background-color: {p['success_bg']};
            color: {p['success']};
            border-color: {p['success_border']};
        }}
        .conf-medium {{
            background-color: {p['warning_bg']};
            color: {p['warning']};
            border-color: {p['warning_border']};
        }}
        .conf-low {{
            background-color: {p['danger_bg']};
            color: {p['danger']};
            border-color: {p['danger_border']};
        }}
        .conf-none {{
            background-color: {p['surface_alt']};
            color: {p['text_muted']};
            border-color: {p['border']};
        }}

        /* ---------- Follow-up suggestion buttons ---------- */
        .followup-row .stButton > button {{
            background-color: {p['accent_soft']};
            border: 1px solid {p['border']};
            color: {p['accent']};
            font-size: 0.85rem;
            border-radius: 999px;
            padding: 4px 14px;
        }}
        .followup-row .stButton > button:hover {{
            background-color: {p['accent']};
            color: #ffffff;
            border-color: {p['accent']};
        }}
        </style>
    """, unsafe_allow_html=True)