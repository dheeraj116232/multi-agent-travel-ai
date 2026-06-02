import streamlit as st


def render_planner(app, HumanMessage, check_rate_limit, get_rate_limit_info, logger, thread_id):
    st.markdown("<div class='sec-head'><span>🤖 AI Trip Planner</span></div>", unsafe_allow_html=True)
    st.write("Planner section moved into ui/sections_planner.py")

