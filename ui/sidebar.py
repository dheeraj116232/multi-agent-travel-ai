import streamlit as st


SIDEBAR_SECTIONS = [
    "🏠 Home",
    "🤖 AI Trip Planner",
    "🌍 Famous Destinations",
    "📜 Saved History",
    "📝 Feedback",
]


def ensure_session_state():
    if "theme" not in st.session_state:
        st.session_state.theme = "🌌 Premium Dark"
    if "user_id" not in st.session_state:
        st.session_state.user_id = "1"
    if "active_section" not in st.session_state:
        st.session_state.active_section = "🏠 Home"
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""
    if "collected_results" not in st.session_state:
        st.session_state.collected_results = None
    if "selected_dest" not in st.session_state:
        st.session_state.selected_dest = None


def render_sidebar(get_next_user_id):
    ensure_session_state()

    with st.sidebar:
        st.markdown("<div class='sidebar-title'>🌍 AI Travel Planner</div>", unsafe_allow_html=True)
        st.markdown("---")

        thread_id = st.text_input(
            "👤 User ID",
            value=st.session_state.user_id,
            help="Your session ID — keeps travel history across queries",
        )
        st.session_state.user_id = thread_id or get_next_user_id()

        st.markdown("<div class='sidebar-title'>🎨 Visual Theme</div>", unsafe_allow_html=True)
        theme_choice = st.selectbox(
            "Select Theme",
            options=["🌌 Premium Dark", "☀️ Elegant Light", "🕶️ Charcoal Grayscale"],
            index=0 if st.session_state.theme == "🌌 Premium Dark" else (1 if st.session_state.theme == "☀️ Elegant Light" else 2),
            label_visibility="collapsed",
        )
        if theme_choice != st.session_state.theme:
            st.session_state.theme = theme_choice
            st.rerun()

        st.markdown("<div class='sidebar-title'>Sections</div>", unsafe_allow_html=True)

        # Avoid calling st.rerun() inside an on_click callback.
        # Trigger rerun from the main script flow instead.
        for label in SIDEBAR_SECTIONS:
            if st.button(
                label,
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if st.session_state.active_section == label else "secondary",
            ):
                st.session_state.active_section = label
                st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)
                st.rerun()


