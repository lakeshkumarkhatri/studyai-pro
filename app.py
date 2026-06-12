import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import json
import time
import os
import datetime
import re
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="StudyAI Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  SESSION STATE BOOTSTRAP
# ─────────────────────────────────────────────
_defaults = {
    "study_data": None,
    "quiz_submitted": False,
    "system_status": "awaiting",
    "chat_history": [],
    "score_history": [],
    "dark_mode": False,
    "quiz_answers": {},
    "topic_hint": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  THEME TOKENS  ← single source of truth
# ─────────────────────────────────────────────
LIGHT = {
    "bg":           "#F8FAFC",
    "surface":      "#FFFFFF",
    "surface2":     "#F1F5F9",
    "surface3":     "#E2E8F0",
    "border":       "#CBD5E1",
    "input_bg":     "#FFFFFF",
    "input_border": "#CBD5E1",
    "text":         "#0F172A",
    "text_muted":   "#64748B",
    "text_on_accent":"#FFFFFF",
    "accent":       "#4F46E5",
    "accent2":      "#7C3AED",
    "accent_soft":  "#EEF2FF",
    "success":      "#16A34A",
    "success_soft": "#DCFCE7",
    "error":        "#DC2626",
    "error_soft":   "#FEE2E2",
    "warn":         "#D97706",
    "warn_soft":    "#FEF3C7",
    "tab_active":   "#4F46E5",
    "tab_inactive": "#64748B",
    "sidebar_bg":   "#FFFFFF",
    "shadow":       "rgba(0,0,0,0.08)",
}
DARK = {
    "bg":           "#0F172A",
    "surface":      "#1E293B",
    "surface2":     "#263147",
    "surface3":     "#334155",
    "border":       "#334155",
    "input_bg":     "#1E293B",
    "input_border": "#475569",
    "text":         "#F1F5F9",
    "text_muted":   "#94A3B8",
    "text_on_accent":"#FFFFFF",
    "accent":       "#818CF8",
    "accent2":      "#A78BFA",
    "accent_soft":  "#1E1B4B",
    "success":      "#4ADE80",
    "success_soft": "#052E16",
    "error":        "#F87171",
    "error_soft":   "#450A0A",
    "warn":         "#FCD34D",
    "warn_soft":    "#451A03",
    "tab_active":   "#818CF8",
    "tab_inactive": "#94A3B8",
    "sidebar_bg":   "#1E293B",
    "shadow":       "rgba(0,0,0,0.4)",
}
T = DARK if st.session_state.dark_mode else LIGHT

# ─────────────────────────────────────────────
#  CSS  ← every value driven by T, no hardcodes
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

/* ════════════════════════════════════
   BASE
════════════════════════════════════ */
html, body, .stApp {{
    background-color: {T['bg']} !important;
    color: {T['text']} !important;
    font-family: 'Inter', sans-serif;
}}
.block-container {{
    max-width: 1100px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    background-color: {T['bg']} !important;
}}

/* ════════════════════════════════════
   TYPOGRAPHY
════════════════════════════════════ */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Syne', sans-serif !important;
    color: {T['text']} !important;
    letter-spacing: -0.4px;
}}
p, li, span, label, div {{
    color: {T['text']};
}}
.stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: {T['text']} !important;
    line-height: 1.75;
}}
.stCaption, small {{
    color: {T['text_muted']} !important;
}}

/* ════════════════════════════════════
   HERO
════════════════════════════════════ */
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(110deg, {T['text']} 0%, {T['accent']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.3rem;
    line-height: 1.2;
}}
.hero-sub {{
    font-size: 1.05rem;
    color: {T['text_muted']} !important;
    text-align: center;
    margin-bottom: 0.3rem;
}}
.hero-badge {{
    text-align: center;
    font-size: 0.78rem;
    font-weight: 700;
    color: {T['accent']} !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}}

/* ════════════════════════════════════
   SIDEBAR
════════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background-color: {T['sidebar_bg']} !important;
    border-right: 1px solid {T['border']} !important;
}}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {{
    color: {T['text']} !important;
}}
/* Toggle label */
section[data-testid="stSidebar"] .stToggle label {{
    color: {T['text']} !important;
}}
/* Slider labels */
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectSlider label {{
    color: {T['text']} !important;
}}
section[data-testid="stSidebar"] [data-testid="stSelectSliderThumb"] {{
    background: {T['accent']} !important;
}}

/* ════════════════════════════════════
   INPUT FIELDS
════════════════════════════════════ */
/* Text area */
.stTextArea textarea {{
    background-color: {T['input_bg']} !important;
    color: {T['text']} !important;
    border: 1.5px solid {T['input_border']} !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    caret-color: {T['accent']} !important;
}}
.stTextArea textarea:focus {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px {T['accent_soft']} !important;
}}
.stTextArea textarea::placeholder {{
    color: {T['text_muted']} !important;
    opacity: 0.7;
}}
/* Text input */
.stTextInput input {{
    background-color: {T['input_bg']} !important;
    color: {T['text']} !important;
    border: 1.5px solid {T['input_border']} !important;
    border-radius: 12px !important;
    caret-color: {T['accent']} !important;
}}
.stTextInput input:focus {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px {T['accent_soft']} !important;
}}
/* ── Chat input: every layer that Streamlit wraps it in ── */

/* The sticky bottom bar that holds the chat input */
div[data-testid="stBottom"],
div[data-testid="stBottom"] > div {{
    background-color: {T['bg']} !important;
    border-top: 1px solid {T['border']} !important;
    padding: 0.75rem 0 !important;
}}

/* Outer widget container */
div[data-testid="stChatInput"] {{
    background-color: {T['input_bg']} !important;
    border: 1.5px solid {T['input_border']} !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px {T['shadow']} !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}}
div[data-testid="stChatInput"]:focus-within {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px {T['accent_soft']}, 0 2px 12px {T['shadow']} !important;
}}

/* The inner form element */
div[data-testid="stChatInput"] form,
div[data-testid="stChatInput"] > div {{
    background-color: {T['input_bg']} !important;
    border-radius: 14px !important;
}}

/* The actual textarea */
div[data-testid="stChatInput"] textarea,
.stChatInput textarea {{
    background-color: {T['input_bg']} !important;
    color: {T['text']} !important;
    caret-color: {T['accent']} !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}}
div[data-testid="stChatInput"] textarea::placeholder {{
    color: {T['text_muted']} !important;
    opacity: 0.75;
}}

/* Send button inside chat input */
div[data-testid="stChatInput"] button {{
    background-color: {T['accent']} !important;
    color: {T['text_on_accent']} !important;
    border-radius: 10px !important;
    border: none !important;
    opacity: 1 !important;
}}
div[data-testid="stChatInput"] button:hover {{
    background-color: {T['accent2']} !important;
}}
div[data-testid="stChatInput"] button svg {{
    fill: {T['text_on_accent']} !important;
    stroke: {T['text_on_accent']} !important;
}}

/* ════════════════════════════════════
   FILE UPLOADER
════════════════════════════════════ */
.stFileUploader,
[data-testid="stFileUploadDropzone"] {{
    background-color: {T['surface']} !important;
    border: 1.5px dashed {T['input_border']} !important;
    border-radius: 12px !important;
}}
[data-testid="stFileUploadDropzone"] {{
    color: {T['text_muted']} !important;
}}
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span {{
    color: {T['text_muted']} !important;
}}

/* ════════════════════════════════════
   TABS
════════════════════════════════════ */
div[data-testid="stTabs"] [role="tablist"] {{
    background-color: {T['surface2']} !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid {T['border']} !important;
    gap: 2px;
}}
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: {T['tab_inactive']} !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    border: none !important;
    transition: all 0.15s ease !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    background: {T['surface']} !important;
    color: {T['tab_active']} !important;
    box-shadow: 0 1px 6px {T['shadow']} !important;
    border: none !important;
}}
button[data-baseweb="tab"]:hover {{
    color: {T['text']} !important;
    background: {T['surface3']} !important;
}}
/* Remove Streamlit's default blue underline */
button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {{
    color: {T['tab_active']} !important;
}}

/* ════════════════════════════════════
   RADIO (navigation)
════════════════════════════════════ */
div[data-testid="stHorizontalBlock"] label {{
    color: {T['text']} !important;
}}
.stRadio label {{
    color: {T['text']} !important;
}}
.stRadio div[role="radiogroup"] label {{
    background: {T['surface2']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    color: {T['text_muted']} !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.15s ease;
}}

/* ════════════════════════════════════
   BUTTONS
════════════════════════════════════ */
button[kind="primary"] {{
    background: linear-gradient(135deg, {T['accent']} 0%, {T['accent2']} 100%) !important;
    color: {T['text_on_accent']} !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    box-shadow: 0 4px 18px {T['shadow']} !important;
    transition: all 0.2s ease !important;
    width: 100%;
    margin-top: 0.5rem;
    letter-spacing: 0.2px;
}}
button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px {T['shadow']} !important;
}}
button[kind="secondary"],
.stButton button {{
    background: {T['surface2']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}}
button[kind="secondary"]:hover,
.stButton button:hover {{
    background: {T['surface3']} !important;
    border-color: {T['accent']} !important;
    color: {T['accent']} !important;
}}

/* ════════════════════════════════════
   FORMS (quiz)
════════════════════════════════════ */
[data-testid="stForm"] {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 14px !important;
    padding: 1.5rem !important;
}}
.stRadio label {{
    color: {T['text']} !important;
}}

/* ════════════════════════════════════
   NOTIFICATIONS (stNotification legacy)
════════════════════════════════════ */
div[data-testid="stNotification"] {{
    background-color: {T['surface']} !important;
    border-color: {T['border']} !important;
    color: {T['text']} !important;
}}

/* ════════════════════════════════════
   EXPANDER
════════════════════════════════════ */
details {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
}}
details summary {{
    color: {T['text']} !important;
    font-weight: 600;
    padding: 0.7rem 1rem;
}}
details > div {{
    background: {T['surface']} !important;
    color: {T['text']} !important;
    padding: 0.5rem 1rem 1rem;
}}

/* ════════════════════════════════════
   METRICS
════════════════════════════════════ */
[data-testid="metric-container"] {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 2px 8px {T['shadow']} !important;
}}
[data-testid="metric-container"] label {{
    color: {T['text_muted']} !important;
    font-size: 0.85rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {T['text']} !important;
    font-weight: 700 !important;
}}

/* ════════════════════════════════════
   DIVIDER
════════════════════════════════════ */
hr {{
    border-color: {T['border']} !important;
    opacity: 0.6;
}}

/* ════════════════════════════════════
   SPINNER
════════════════════════════════════ */
.stSpinner > div {{
    border-top-color: {T['accent']} !important;
}}

/* ════════════════════════════════════
   STATUS BOX
════════════════════════════════════ */
[data-testid="stStatusWidget"] {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    color: {T['text']} !important;
}}

/* ════════════════════════════════════
   CHAT MESSAGES
════════════════════════════════════ */
[data-testid="stChatMessage"] {{
    background-color: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.6rem !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {{
    color: {T['text']} !important;
}}
/* Avatar background */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
    background-color: {T['accent_soft']} !important;
    color: {T['accent']} !important;
    border: 1px solid {T['border']} !important;
}}

/* ════════════════════════════════════
   CHAT CONTAINER / stVerticalBlock
════════════════════════════════════ */
/* The scrollable container st.container(height=420) */
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: {T['surface2']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 14px !important;
}}

/* ════════════════════════════════════
   INFO / WARNING / SUCCESS / ERROR ALERTS
   (themed to match mode)
════════════════════════════════════ */
div[data-testid="stAlert"] {{
    background-color: {T['accent_soft']} !important;
    border: 1px solid {T['accent']} !important;
    border-left: 4px solid {T['accent']} !important;
    border-radius: 10px !important;
    color: {T['text']} !important;
}}
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
    color: {T['text']} !important;
}}
/* success */
div[data-testid="stAlert"][data-baseweb="notification"][kind="success"],
.stSuccess {{
    background-color: {T['success_soft']} !important;
    border-color: {T['success']} !important;
}}
/* warning */
div[data-testid="stAlert"][kind="warning"],
.stWarning {{
    background-color: {T['warn_soft']} !important;
    border-color: {T['warn']} !important;
}}
/* error */
div[data-testid="stAlert"][kind="error"],
.stError {{
    background-color: {T['error_soft']} !important;
    border-color: {T['error']} !important;
}}

/* ════════════════════════════════════
   SCROLLBAR
════════════════════════════════════ */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {T['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {T['border']}; border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: {T['text_muted']}; }}

/* ════════════════════════════════════
   SELECT SLIDER TRACK
════════════════════════════════════ */
[data-testid="stSelectSlider"] [data-testid="stTickBar"] {{
    color: {T['text_muted']} !important;
}}

/* ════════════════════════════════════
   DOWNLOAD BUTTON
════════════════════════════════════ */
[data-testid="stDownloadButton"] button {{
    background: {T['surface2']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
[data-testid="stDownloadButton"] button:hover {{
    border-color: {T['accent']} !important;
    color: {T['accent']} !important;
}}

/* ════════════════════════════════════
   CUSTOM COMPONENTS (HTML cards)
════════════════════════════════════ */
.summary-card {{
    background: {T['accent_soft']};
    border-left: 4px solid {T['accent']};
    border-radius: 0 12px 12px 0;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.5rem;
}}
.summary-card p {{
    color: {T['text']} !important;
    margin: 0;
}}
.mindmap-container {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 1rem;
    overflow-x: auto;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  GEMINI SETUP
# ─────────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    st.error("⚠️  `GEMINI_API_KEY` environment variable not set.")
    st.stop()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def safe_json_parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if there's any stray whitespace or markdown
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

def call_gemini_with_retry(prompt_parts, retries: int = 3, delay: float = 4.0):
    for attempt in range(retries):
        try:
            # ADD NATIVE JSON MODE HERE:
            return model.generate_content(
                prompt_parts,
                generation_config={
                    "response_mime_type": "application/json",
                }
            )
        except Exception as e:
            err = str(e).lower()
            if "quota" in err or "429" in err or "resource" in err:
                if attempt < retries - 1:
                    time.sleep(delay * (2 ** attempt))
                    continue
            raise e
    return None

def build_study_prompt(difficulty: str) -> str:
    return f"""
You are an expert AI study tutor. Analyse the provided content at {difficulty} difficulty.
Respond ONLY with a single valid JSON object — no markdown fences, no preamble.

{{
  "topic": "Short topic title (max 6 words)",
  "summary": "2-3 sentence executive summary of core concepts.",
  "explanation": "Detailed explanation (~200 words) breaking down key ideas with examples.",
  "flashcards": [
    {{"term": "Term", "definition": "Clear definition"}}
  ],
  "quiz": [
    {{"question": "Question?", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Why A is correct."}}
  ],
  "mind_map": {{
    "root": "Central topic",
    "branches": [
      {{
        "label": "Branch name",
        "children": ["Leaf 1", "Leaf 2"]
      }}
    ]
  }},
  "study_plan": [
    {{"day": "Day 1: Title", "tasks": ["Task 1", "Task 2", "Task 3"]}}
  ]
}}

Rules:
- flashcards: at least 5 items
- quiz: exactly 5 questions, each with exactly 4 options
- mind_map.branches: 4-6 branches, each with 2-4 children
- study_plan: exactly 3 days
"""

def render_mind_map(mind_map: dict) -> str:
    import math
    root = mind_map.get("root", "Topic")
    branches = mind_map.get("branches", [])
    W, H = 1200, 700
    cx, cy = W // 2, H // 2 - 30
    radius_branch, radius_leaf = 220, 130
    lines, nodes = [], []

    nodes.append(
        f'<ellipse cx="{cx}" cy="{cy}" rx="72" ry="33" fill="{T["accent"]}" opacity="0.95"/>'
        f'<text x="{cx}" y="{cy+5}" text-anchor="middle" fill="{T["text_on_accent"]}" '
        f'font-size="13" font-weight="700" font-family="Inter,sans-serif">{root[:22]}</text>'
    )
    n_branches = len(branches)
    for i, branch in enumerate(branches):
        angle = (2 * math.pi * i / n_branches) - math.pi / 2
        bx = cx + radius_branch * math.cos(angle)
        by = cy + radius_branch * math.sin(angle)
        lines.append(
            f'<line x1="{cx}" y1="{cy}" x2="{bx:.0f}" y2="{by:.0f}" '
            f'stroke="{T["accent"]}" stroke-width="2" opacity="0.4"/>'
        )
        label = branch.get("label", "")[:18]
        nodes.append(
            f'<ellipse cx="{bx:.0f}" cy="{by:.0f}" rx="60" ry="25" '
            f'fill="{T["surface2"]}" stroke="{T["accent"]}" stroke-width="1.5"/>'
            f'<text x="{bx:.0f}" y="{by:.0f}" text-anchor="middle" fill="{T["text"]}" '
            f'font-size="11" font-weight="600" font-family="Inter,sans-serif" dy="4">{label}</text>'
        )
        children = branch.get("children", [])
        n_c = len(children)
        for j, child in enumerate(children):
            spread = math.pi / 3
            ca = angle - spread/2 + (spread * j / max(n_c-1, 1)) if n_c > 1 else angle
            lx = bx + radius_leaf * math.cos(ca)
            ly = by + radius_leaf * math.sin(ca)
            lines.append(
                f'<line x1="{bx:.0f}" y1="{by:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" '
                f'stroke="{T["border"]}" stroke-width="1.5" opacity="0.9"/>'
            )
            nodes.append(
                f'<rect x="{lx-44:.0f}" y="{ly-15:.0f}" width="88" height="30" rx="7" '
                f'fill="{T["surface3"]}" stroke="{T["border"]}" stroke-width="1"/>'
                f'<text x="{lx:.0f}" y="{ly+5:.0f}" text-anchor="middle" fill="{T["text"]}" '
                f'font-size="10" font-family="Inter,sans-serif">{child[:17]}</text>'
            )
    return (
        f'<svg viewBox="-50 -50 {W+100} {H+100}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;background:{T["surface"]};border-radius:12px;">'
        f"{''.join(lines)}{''.join(nodes)}</svg>"
    )

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h3 style='color:{T['text']}'>⚙️ Settings</h3>", unsafe_allow_html=True)

    dm = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dm != st.session_state.dark_mode:
        st.session_state.dark_mode = dm
        st.rerun()

    st.markdown("---")
    difficulty = st.select_slider(
        "Learning Level",
        options=["Beginner", "Intermediate", "Advanced"],
        value="Intermediate",
    )
    st.markdown("---")

    status_map = {
        "awaiting": ("🟡", "Awaiting Input",   "Ready for your materials.",     T["text_muted"]),
        "building": ("🔵", "Building Module",  "AI is processing content.",     T["accent"]),
        "ready":    ("🟢", "Module Ready",     "Your study module is live!",    T["success"]),
    }
    dot, lbl, sub, color = status_map[st.session_state.system_status]
    st.markdown(f"""
    <div style="background:{T['surface2']};border-radius:10px;padding:12px 14px;
                border:1px solid {T['border']}">
        <span style="font-weight:700;color:{color}">{dot} {lbl}</span><br>
        <span style="font-size:0.82rem;color:{T['text_muted']}">{sub}</span>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.score_history:
        st.markdown(f"<p style='font-weight:600;color:{T['text']}'>📊 Recent Scores</p>",
                    unsafe_allow_html=True)
        for entry in reversed(st.session_state.score_history[-5:]):
            pct = round(entry["score"] / entry["total"] * 100)
            chip = T["success"] if pct >= 70 else T["warn"] if pct >= 50 else T["error"]
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:{T['surface2']};border-radius:8px;padding:6px 10px;
                        margin-bottom:4px;border:1px solid {T['border']}">
                <span style="font-size:0.82rem;color:{T['text_muted']};max-width:110px;
                             overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                    {entry['topic']}</span>
                <span style="font-weight:700;color:{chip};font-size:0.85rem">
                    {entry['score']}/{entry['total']}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;font-size:0.82rem;color:{T['text_muted']}'>
        Powered by <b style='color:{T['text']}'>Gemini</b><br>
        Built by <a href="https://lakeshkumar.vercel.app/" target="_blank"
            style="text-decoration:none;font-weight:700;color:{T['accent']}">
            Lakesh Kumar ↗</a>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────
st.markdown("<div class='hero-title'>🎓 StudyAI Pro</div>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Upload notes, PDFs, or whiteboard photos — get a full interactive study module.</p>",
            unsafe_allow_html=True)
st.markdown("<p class='hero-badge'>✦ AI-Powered · Gemini 1.5 · v2.0</p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  INPUT
# ─────────────────────────────────────────────
st.markdown(f"<h3 style='color:{T['text']}'>📥 Add Study Material</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"<p style='font-weight:600;color:{T['text']}'>📄 Upload File</p>",
                unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["pdf","png","jpg","jpeg"],
                                     label_visibility="collapsed")
with col2:
    st.markdown(f"<p style='font-weight:600;color:{T['text']}'>✍️ Paste Notes</p>",
                unsafe_allow_html=True)
    user_input = st.text_area("", height=160, label_visibility="collapsed",
                              placeholder="Paste your lecture notes, book excerpt, or code…")

analyze_button = st.button("⚡ Build Study Module", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
#  BUILD LOGIC
# ─────────────────────────────────────────────
if analyze_button:
    api_payload = None

    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
            if not text.strip():
                st.warning("⚠️ Couldn't extract text (scanned PDF?). Try pasting the content instead.")
            else:
                api_payload = f"Content:\n{text[:12000]}"
        else:
            api_payload = Image.open(uploaded_file)
    elif user_input and user_input.strip():
        if len(user_input.split()) < 1:
            st.warning("Please provide at least 1 word. A topic name alone isn't enough.")
            st.stop()
        api_payload = f"Content:\n{user_input[:12000]}"

    if api_payload is None:
        st.warning("⚠️ Please provide study material first.")
    else:
        st.session_state.system_status = "building"
        with st.status("🧠 Building your module…", expanded=True) as sw:
            for msg in ["📖 Reading content…", f"⚙️ Calibrating for **{difficulty}** level…",
                        "⚡ Extracting key concepts…", "🗺️ Generating mind map…",
                        "🎯 Composing quiz questions…"]:
                st.write(msg); time.sleep(0.45)

            try:
                response = call_gemini_with_retry([build_study_prompt(difficulty), api_payload])
                parsed = safe_json_parse(response.text)
                if parsed is None:
                    sw.update(label="❌ AI returned invalid JSON. Try again.", state="error")
                    st.session_state.system_status = "awaiting"
                    st.error("Could not parse AI response. Try adding more content.")
                else:
                    st.session_state.study_data    = parsed
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers   = {}
                    st.session_state.chat_history   = []
                    st.session_state.topic_hint     = parsed.get("topic", "Study Session")
                    st.session_state.system_status  = "ready"
                    sw.update(label="✅ Module ready!", state="complete", expanded=False)
            except Exception as e:
                st.session_state.system_status = "awaiting"
                sw.update(label="❌ Generation failed", state="error")
                err = str(e)
                if "429" in err or "quota" in err.lower():
                    st.error("🚦 Rate limit hit. Wait a minute and try again.")
                elif "api_key" in err.lower() or "credential" in err.lower():
                    st.error("🔑 Check your GEMINI_API_KEY environment variable.")
                else:
                    st.error(f"Error: {err}")

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state.study_data:
    data = st.session_state.study_data

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    h1, h2 = st.columns([3, 1], vertical_alignment="bottom")
    with h1:
        st.markdown(f"<h2 style='color:{T['text']}'>🎉 {data.get('topic','Module Ready')}</h2>",
                    unsafe_allow_html=True)
    with h2:
        export_text = (f"TOPIC\n{data.get('topic','')}\n\n"
                       f"SUMMARY\n{data.get('summary','')}\n\n"
                       f"EXPLANATION\n{data.get('explanation','')}")
        st.download_button("💾 Export Notes", data=export_text,
                           file_name="StudyAI_Notes.txt", mime="text/plain",
                           use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    selected_tab = st.radio(
    "",
    [
        "📖 Summary",
        "🗺️ Mind Map",
        "📇 Flashcards",
        "🎯 Quiz",
        "💬 Chat Tutor",
        "📅 Study Plan",
        "📊 Progress"
    ],
    horizontal=True,
    key="main_navigation"
)

    # ── Summary ──────────────────────────────
    if selected_tab == "📖 Summary":
        st.markdown(f"<div class='summary-card'><p>{data.get('summary','')}</p></div>",
                    unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{T['text']}'>🧠 Deep Dive</h3>", unsafe_allow_html=True)
        st.write(data.get("explanation", ""))

    # ── Mind Map ─────────────────────────────
    if selected_tab == "🗺️ Mind Map":
        st.markdown(f"<h3 style='color:{T['text']}'>🗺️ Visual Concept Map</h3>",
                    unsafe_allow_html=True)
        st.caption("Auto-generated from your material.")
        if "mind_map" in data:
            st.markdown(f"<div class='mindmap-container'>{render_mind_map(data['mind_map'])}</div>",
                        unsafe_allow_html=True)
            with st.expander("📋 Text outline"):
                mm = data["mind_map"]
                st.markdown(f"**{mm.get('root','')}**")
                for b in mm.get("branches", []):
                    st.markdown(f"&nbsp;&nbsp;├─ **{b.get('label','')}**")
                    for c in b.get("children", []):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ {c}")
        else:
            st.info("Mind map not available for this module.")

    # ── Flashcards ───────────────────────────
    if selected_tab == "📇 Flashcards":
        st.markdown(f"<h3 style='color:{T['text']}'>📇 Active Recall Flashcards</h3>",
                    unsafe_allow_html=True)
        csv_lines = ["Term,Definition"] + [
            f'"{fc["term"].replace(chr(34),chr(34)*2)}","{fc["definition"].replace(chr(34),chr(34)*2)}"'
            for fc in data.get("flashcards", [])
        ]
        st.download_button("⬇️ Export for Anki / Quizlet (.csv)",
                           data="\n".join(csv_lines),
                           file_name="StudyAI_Flashcards.csv", mime="text/csv")
        st.markdown("<br>", unsafe_allow_html=True)
        for fc in data.get("flashcards", []):
            with st.expander(f"❓  {fc.get('term','')}"):
                st.success(f"**Definition:** {fc.get('definition','')}")
        st.markdown("---")
        if st.button("➕ Generate 3 More Flashcards", key="more_fc"):
            with st.spinner("Generating…"):
                try:
                    res = call_gemini_with_retry(
                        f'Based on: {data.get("explanation","")}\n'
                        'Generate 3 MORE unique flashcards. Return ONLY a JSON array, no markdown:\n'
                        '[{"term":"Term","definition":"Def"}]'
                    )
                    new = safe_json_parse(res.text)
                    if isinstance(new, list):
                        st.session_state.study_data["flashcards"].extend(new)
                        st.rerun()
                    else:
                        st.error("Could not parse new flashcards. Try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Quiz ─────────────────────────────────
    if selected_tab == "🎯 Quiz":
        st.markdown(f"<h3 style='color:{T['text']}'>📝 Knowledge Check</h3>",
                    unsafe_allow_html=True)
        quiz = data.get("quiz", [])
        with st.form("quiz_form", clear_on_submit=False):
            for i, q in enumerate(quiz):
                st.markdown(f"**{i+1}. {q.get('question','')}**")
                opts = q.get("options", [])
                prev = st.session_state.quiz_answers.get(f"q_{i}")
                idx  = opts.index(prev) if prev in opts else None
                choice = st.radio("", opts, key=f"q_{i}_radio",
                                  index=idx, label_visibility="collapsed")
                st.session_state.quiz_answers[f"q_{i}"] = choice
                st.markdown("<br>", unsafe_allow_html=True)
            submit_quiz = st.form_submit_button("✅ Check Answers")

        if submit_quiz:
            st.session_state.quiz_submitted = True

        if st.session_state.quiz_submitted:
            score = 0
            st.markdown(f"<h3 style='color:{T['text']}'>📊 Results</h3>",
                        unsafe_allow_html=True)
            for i, q in enumerate(quiz):
                uc = st.session_state.quiz_answers.get(f"q_{i}")
                ca = q.get("answer", "")
                if uc == ca:
                    score += 1
                    st.success(f"**{i+1}. ✓ Correct!**")
                else:
                    st.error(f"**{i+1}. ✗** You chose: *{uc or 'Skipped'}*")
                    st.warning(f"Correct: **{ca}**")
                    st.info(f"💡 {q.get('explanation','')}")

            total = len(quiz)
            pct   = round(score / total * 100) if total else 0
            c1, c2 = st.columns(2)
            c1.metric("Score",    f"{score} / {total}")
            c2.metric("Accuracy", f"{pct}%")

            last = st.session_state.score_history[-1] if st.session_state.score_history else None
            if not (last and last["score"] == score and last["topic"] == st.session_state.topic_hint):
                st.session_state.score_history.append({
                    "timestamp": datetime.datetime.now().strftime("%b %d, %H:%M"),
                    "topic": st.session_state.topic_hint,
                    "score": score, "total": total, "difficulty": difficulty,
                })
            if pct == 100:   st.balloons()
            elif pct >= 70:  st.success("Great work! 🎉")
            else:            st.warning("Keep going — revisit the Summary and Flashcards.")

        st.markdown("---")
        if st.button("➕ Generate 3 More MCQs", key="more_quiz"):
            with st.spinner("Generating…"):
                try:
                    res = call_gemini_with_retry(
                        f'Based on: {data.get("explanation","")}\n'
                        'Generate 3 MORE unique MCQs. Return ONLY a JSON array, no markdown:\n'
                        '[{"question":"Q?","options":["A","B","C","D"],"answer":"A","explanation":"Why"}]'
                    )
                    new = safe_json_parse(res.text)
                    if isinstance(new, list):
                        st.session_state.study_data["quiz"].extend(new)
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers   = {}
                        st.rerun()
                    else:
                        st.error("Could not parse new questions. Try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Chat Tutor ───────────────────────────
    if selected_tab == "💬 Chat Tutor":
        st.markdown(f"<h3 style='color:{T['text']}'>💬 Your Personal AI Tutor</h3>",
                    unsafe_allow_html=True)
        st.caption("Ask follow-up questions, request examples, or dig deeper. Full context maintained.")

        # Styled voice tip — no default blue info box
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;
                    background:{T['surface2']};border:1px solid {T['border']};
                    border-left:4px solid {T['accent']};
                    border-radius:10px;padding:10px 14px;margin-bottom:1rem;">
            <span style="font-size:1.1rem">🎙️</span>
            <span style="font-size:0.88rem;color:{T['text_muted']}">
                <b style="color:{T['text']}">Voice input:</b>
                Use OS voice dictation —
                <span style="color:{T['accent']};font-weight:600">Win+H</span> on Windows,
                <span style="color:{T['accent']};font-weight:600">🎤 key</span> on mobile keyboard.
            </span>
        </div>""", unsafe_allow_html=True)

        # Scrollable chat history
        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown(f"""
                <div style="display:flex;flex-direction:column;align-items:center;
                            justify-content:center;height:280px;gap:8px;">
                    <span style="font-size:2.5rem;opacity:0.3">💬</span>
                    <p style="color:{T['text_muted']};font-size:0.9rem;margin:0;opacity:0.5">
                        No messages yet. Ask anything about your material.
                    </p>
                </div>""", unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if user_q := st.chat_input("Ask anything about your study material…"):
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_q)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        history_txt = "\n\n".join(
                            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content']}"
                            for m in st.session_state.chat_history[:-1]
                        )
                        prompt_chat = (
                            f"You are a patient expert tutor. Answer ONLY based on the study material.\n"
                            f"If unrelated, politely redirect.\n\n"
                            f"=== STUDY MATERIAL ===\n{data.get('explanation','')}\n\n"
                            f"=== CONVERSATION ===\n{history_txt}\n\n"
                            f"=== STUDENT QUESTION ===\n{user_q}"
                        )
                        try:
                            resp  = call_gemini_with_retry(prompt_chat)
                            reply = resp.text
                            st.markdown(reply)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": reply}
                            )
                        except Exception as e:
                            err = str(e)
                            if "429" in err or "quota" in err.lower():
                                st.error("🚦 Rate limit. Wait a moment and try again.")
                            else:
                                st.error(f"Error: {err}")

    # ── Study Plan ───────────────────────────
    if selected_tab == "📅 Study Plan":
        st.markdown(f"<h3 style='color:{T['text']}'>📅 3-Day Study Roadmap</h3>",
                    unsafe_allow_html=True)
        # Styled tip instead of st.info
        st.markdown(f"""
        <div style="background:{T['surface2']};border:1px solid {T['border']};
                    border-left:4px solid {T['success']};border-radius:10px;
                    padding:10px 14px;margin-bottom:1.2rem;">
            <span style="font-size:0.88rem;color:{T['text_muted']}">
                📚 <b style="color:{T['text']}">Spaced repetition approach</b> —
                don't cram. Follow this plan for lasting retention.
            </span>
        </div>""", unsafe_allow_html=True)
        plan = data.get("study_plan", [])
        if plan:
            day_colors = [T["accent"], T["success"], T["warn"]]
            for idx, day in enumerate(plan):
                col = day_colors[idx % len(day_colors)]
                tasks_html = "".join(
                    f'<p style="margin:0.25rem 0;color:{T["text"]}">🗓️ {t}</p>'
                    for t in day.get("tasks", [])
                )
                st.markdown(f"""
                <div style="border-left:4px solid {col};background:{T['surface']};
                            border-radius:0 12px 12px 0;padding:1.1rem 1.5rem;
                            margin-bottom:1rem;border:1px solid {T['border']}">
                    <p style="font-weight:700;color:{col};margin:0 0 0.5rem">{day.get('day','')}</p>
                    {tasks_html}
                </div>""", unsafe_allow_html=True)
        else:
            st.warning("Study plan not included in this module.")

    # ── Progress ─────────────────────────────
    if selected_tab == "📊 Progress":
        st.markdown(f"<h3 style='color:{T['text']}'>📊 Score History</h3>",
                    unsafe_allow_html=True)
        if not st.session_state.score_history:
            st.info("Complete a quiz to start tracking your progress here.")
        else:
            hist = st.session_state.score_history
            avg  = round(sum(e["score"]/e["total"]*100 for e in hist) / len(hist))
            best = max(hist, key=lambda e: e["score"]/e["total"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Sessions",    len(hist))
            c2.metric("Avg Accuracy", f"{avg}%")
            c3.metric("Best Score",  f"{best['score']}/{best['total']}")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-weight:600;color:{T['text']}'>All Attempts</p>",
                        unsafe_allow_html=True)
            for entry in reversed(hist):
                pct   = round(entry["score"] / entry["total"] * 100)
                bcol  = T["success"] if pct >= 70 else T["warn"] if pct >= 50 else T["error"]
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            background:{T['surface2']};border-radius:10px;padding:10px 14px;
                            margin-bottom:6px;border:1px solid {T['border']}">
                    <div>
                        <span style="font-weight:600;color:{T['text']}">{entry['topic']}</span>
                        <span style="font-size:0.78rem;color:{T['text_muted']};margin-left:8px">
                            {entry['timestamp']} · {entry['difficulty']}</span>
                    </div>
                    <span style="font-weight:700;color:{bcol};font-size:0.95rem">
                        {entry['score']}/{entry['total']} ({pct}%)</span>
                </div>""", unsafe_allow_html=True)
            if st.button("🗑️ Clear History", key="clear_history"):
                st.session_state.score_history = []
                st.rerun()