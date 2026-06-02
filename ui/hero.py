import streamlit as st


def render_hero():
    st.markdown(
        """
<div class="hero-wrapper">
  <img class="hero-bg" src="https://static.vecteezy.com/system/resources/previews/022/084/998/non_2x/travel-abstract-background-with-transport-and-nature-trip-backdrop-generative-ai-photo.jpeg" alt="travel abstract background"/>
  <div class="hero-content">
    <div class="hero-badge">✦ Multi-Agent AI System</div>
    <div class="hero-title">✈️ AI Travel Booking System</div>
    <div class="hero-sub">Powered by 4 specialized AI agents that search, compare, optimize, and organize every detail of your journey automatically.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

