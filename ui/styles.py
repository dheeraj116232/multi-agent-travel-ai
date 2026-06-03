import streamlit as st


def apply_base_styles(theme: str):
    st.markdown(
        """
<style>
html, body, .stApp { font-family: 'Inter', sans-serif; background-color: #080d14; }
section[data-testid="stSidebar"] { background: #090e18 !important; border-right: 1px solid #141f30 !important; }
#MainMenu, footer, header { visibility: hidden; }
.stTextArea textarea { width: 100% !important; margin-bottom: 0.5rem !important; background: #0a1324 !important; border: 1px solid #1e3552 !important; border-radius: 16px !important; color: #e8f4ff !important; font-size: 1.05rem !important; padding: 1.4rem !important; resize: none !important; min-height: 160px !important; line-height: 1.6 !important; }
div[data-testid="stButton"] > button { background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 50%, #0a3d75 100%) !important; color: #ffffff !important; border: none !important; border-radius: 12px !important; }
.sec-head { display: flex; align-items: center; gap: 0.6rem; margin: 2rem 0 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid #1e2e44; }
.sec-head span { font-size: 1.15rem; font-weight: 600; color: #e0edf8; }
</style>
""",
        unsafe_allow_html=True,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # Responsive utilities (used across the app)
    # ──────────────────────────────────────────────────────────────────────────
    # Streamlit renders inside a nested DOM; the rules below are scoped to
    # avoid breaking layout while preventing common mobile issues:
    # - horizontal scrolling
    # - images overflowing their containers
    # - long text breaking readability

    st.markdown(
        """
<style>
html, body { overflow-x: hidden !important; }
img { max-width: 100% !important; height: auto !important; }

/* Safer text wrapping to prevent overflow in cards/results */
.bb-wrap { overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
.bb-text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Card/stack helpers */
.bb-card {
  background: rgba(14, 22, 35, 0.75) !important;
  border: 1px solid rgba(30, 46, 68, 1) !important;
  border-radius: 14px !important;
  padding: 1rem !important;
}

.bb-stack { display: flex; flex-direction: column; gap: 0.75rem; }

/* Touch-friendly buttons */
.bb-touch-btn div[data-testid="baseButton-container"] > button,
.bb-touch-btn div[data-testid="stButton"] > button {
  min-height: 44px;
}

/* Mobile tweaks */
@media (max-width: 768px) {
  /* Make tab panels and markdown areas wrap */
  [data-testid="stMarkdown"], .stMarkdown { max-width: 100% !important; }
  .bb-card { padding: 0.9rem !important; }
}
</style>
""",
        unsafe_allow_html=True,
    )

    # Apply selected theme overrides (keep minimal to avoid breaking layout)
    theme_css = ""
    if theme == "☀️ Elegant Light":

        theme_css = """
.stApp { background-color: #f5f7fa !important; color: #1e293b !important; }
section[data-testid="stSidebar"] { background: #f8fafc !important; border-right: 1px solid #e2e8f0 !important; }
"""
    elif theme == "🕶️ Charcoal Grayscale":
        theme_css = """
.stApp { background-color: #121212 !important; color: #e0e0e0 !important; }
section[data-testid="stSidebar"] { background: #161616 !important; border-right: 1px solid #252525 !important; }
"""

    if theme_css:
        st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

