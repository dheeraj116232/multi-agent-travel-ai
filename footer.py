import streamlit as st

def render_footer():
    # Render CSS style
    st.markdown("""
<style>
/* ── Footer Styles ── */
.footer-wrapper {
    background-color: #030e1c;
    border-top: 1px solid #14243b;
    padding: 1.5rem 1rem 1rem 1rem;
    margin-top: 2.5rem;
    width: 100%;
    border-radius: 16px 16px 0 0;
    box-sizing: border-box;
}
.footer-badges {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-bottom: 1.2rem;
    justify-content: center;
}
.footer-badge {
    background: rgba(14, 26, 43, 0.5);
    border: 1px solid #1c324e;
    color: #94adc8 !important;
    font-size: 0.76rem;
    font-weight: 500;
    padding: 0.35rem 0.8rem;
    border-radius: 30px;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    transition: all 0.3s ease;
}
.footer-badge:hover {
    border-color: #4ea8f0;
    background: rgba(78, 168, 240, 0.1);
    color: #ffffff !important;
}
.badge-dot {
    width: 6px;
    height: 6px;
    background: #2ecc71;
    border-radius: 50%;
    margin-right: 6px;
    box-shadow: 0 0 8px #2ecc71, 0 0 3px #2ecc71;
    display: inline-block;
}
.badge-icon {
    width: 12px;
    height: 12px;
    color: #5a9bd4;
    margin-right: 5px;
    vertical-align: middle;
    transition: color 0.3s ease;
}
.footer-badge:hover .badge-icon {
    color: #ffffff;
}
.footer-container {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr;
    gap: 1.5rem;
    padding-bottom: 1.2rem;
}
.footer-col h4 {
    color: #ffffff !important;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0;
    margin-bottom: 0.6rem;
}
.footer-col ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
.footer-col li {
    padding: 0.25rem 0;
}
.footer-col li a {
    color: #94adc8 !important;
    font-size: 0.8rem;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    transition: all 0.3s ease;
}
.footer-col li a:hover {
    color: #ffffff !important;
    transform: translateX(3px);
}
.footer-link-icon {
    width: 12px;
    height: 12px;
    color: #5a9bd4;
    margin-right: 6px;
    vertical-align: middle;
    transition: color 0.3s ease;
}
.footer-col li a:hover .footer-link-icon {
    color: #4ea8f0;
}
.brand-col .footer-logo {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff !important;
    margin-top: 0;
    margin-bottom: 0.6rem;
    line-height: 1.2;
    display: flex;
    align-items: flex-start;
}
.logo-icon {
    width: 20px;
    height: 20px;
    color: #4ea8f0;
    margin-right: 6px;
    margin-top: 2px;
}
.brand-desc {
    color: #94adc8 !important;
    font-size: 0.8rem;
    line-height: 1.5;
    margin-bottom: 0.8rem;
    max-width: 320px;
}
.social-icons {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.social-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: 1px solid #1c324e;
    background: rgba(14, 26, 43, 0.3);
    color: #7aa8cc !important;
    text-decoration: none;
    transition: all 0.3s ease;
}
.social-icon:hover {
    background: #1a2e47;
    border-color: #4ea8f0;
    color: #ffffff !important;
    box-shadow: 0 0 10px rgba(78, 168, 240, 0.25);
    transform: translateY(-2px);
}
.footer-bottom-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid #14243b;
    margin-top: 1rem;
}
.footer-bottom-row .company-section {
    margin-top: 0;
}
.footer-bottom-row .company-section h4 {
    color: #ffffff !important;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0;
    margin-bottom: 0.5rem;
}
.footer-bottom-row .company-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
.footer-bottom-row .company-section li {
    padding: 0.25rem 0;
}
.footer-bottom-row .company-section li a {
    color: #94adc8 !important;
    font-size: 0.8rem;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    transition: all 0.3s ease;
}
.footer-bottom-row .company-section li a:hover {
    color: #ffffff !important;
    transform: translateX(3px);
}
.footer-bottom-row .company-section li a:hover .footer-link-icon {
    color: #4ea8f0;
}
.scroll-top-container {
    display: flex;
    justify-content: center;
    align-items: center;
}
.bottom-spacer {
    display: block;
}
.scroll-top-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #b0c4de;
    color: #030e1c !important;
    font-size: 1rem;
    font-weight: bold;
    text-decoration: none;
    cursor: pointer;
    box-shadow: 0 0 10px rgba(176,196,222,0.2);
    transition: all 0.3s ease;
}
.scroll-top-btn:hover {
    background-color: #cbdce9;
    transform: translateY(-3px);
    box-shadow: 0 0 15px rgba(203,220,233,0.4);
}

/* ── Mobile responsiveness adjustments for footer ── */
@media (max-width: 1024px) {
    .footer-badges {
        gap: 0.5rem !important;
    }
    .footer-badge {
        padding: 0.3rem 0.7rem !important;
        font-size: 0.72rem !important;
    }
}
@media (max-width: 768px) {
    .footer-container {
        grid-template-columns: 1fr !important;
        gap: 1.2rem !important;
    }
    .footer-badges {
        gap: 0.4rem !important;
    }
    .footer-badge {
        padding: 0.25rem 0.6rem !important;
        font-size: 0.7rem !important;
    }
    .footer-wrapper {
        padding: 1.2rem 0.8rem 0.8rem 0.8rem !important;
    }
    .brand-desc {
        max-width: 100% !important;
    }
    .footer-bottom-row {
        grid-template-columns: 1fr !important;
        gap: 1rem !important;
        align-items: center !important;
        text-align: center !important;
    }
    .footer-bottom-row .company-section {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .scroll-top-container {
        margin-top: 0.2rem;
    }
}
</style>
""", unsafe_allow_html=True)

    # Render HTML footer
    st.markdown("""
<div class="footer-wrapper">
<div class="footer-badges">
<span class="footer-badge">
<span class="badge-dot"></span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3.5c-.5-.5-2.5 0-4 1.5L13.5 8.5 5.3 6.7c-.9-.2-1.9.1-2.4.9l-.5.5c-.4.5-.4 1.2 0 1.6l7.9 3.9-3.9 3.9-3.2-.8c-.7-.2-1.4.1-1.8.6l-.4.4c-.4.4-.4 1.1 0 1.5l3.2 3.2c.4.4 1.1.4 1.5 0l.4-.4c.5-.4.8-1.1.6-1.8l-.8-3.2 3.9-3.9 3.9 7.9c.4.4 1.1.4 1.6 0l.5-.5c.8-.5 1.1-1.5.9-2.4z"/></svg>
Flight Search Agent
</span>
<span class="footer-badge">
<span class="badge-dot"></span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="9" y1="22" x2="9" y2="16"/><line x1="15" y1="22" x2="15" y2="16"/><line x1="9" y1="16" x2="15" y2="16"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M8 10h.01"/><path d="M16 10h.01"/></svg>
Hotel Search Agent
</span>
<span class="footer-badge">
<span class="badge-dot"></span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>
Itinerary Builder Agent
</span>
<span class="footer-badge">
<span class="badge-dot"></span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
Trip Summary Agent
</span>
</div>

<div class="footer-container">
<div class="footer-col brand-col">
<h3 class="footer-logo">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="logo-icon"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3.5c-.5-.5-2.5 0-4 1.5L13.5 8.5 5.3 6.7c-.9-.2-1.9.1-2.4.9l-.5.5c-.4.5-.4 1.2 0 1.6l7.9 3.9-3.9 3.9-3.2-.8c-.7-.2-1.4.1-1.8.6l-.4.4c-.4.4-.4 1.1 0 1.5l3.2 3.2c.4.4 1.1.4 1.5 0l.4-.4c.5-.4.8-1.1.6-1.8l-.8-3.2 3.9-3.9 3.9 7.9c.4.4 1.1.4 1.6 0l.5-.5c.8-.5 1.1-1.5.9-2.4z"/></svg>
AI Travel<br>System
</h3>
<p class="brand-desc">Four specialized AI agents working together to plan your perfect trip — flights, hotels, itinerary & summary.</p>
<div class="social-icons">
<a href="https://github.com/dheeraj116232" target="_blank" class="social-icon">
<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16" height="16" width="16" xmlns="http://www.w3.org/2000/svg"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>
</a>
<a href="https://www.instagram.com/dheeraj_ll6_/" target="_blank" class="social-icon">
<svg stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24" height="16" width="16" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
</a>
<a href="https://www.linkedin.com/in/dheerajkumar116232/" target="_blank" class="social-icon">
<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16" height="16" width="16" xmlns="http://www.w3.org/2000/svg"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854V1.146zm4.943 12.248V6.169H2.542v7.225h2.401zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248-.822 0-1.359.54-1.359 1.248 0 .694.521 1.248 1.327 1.248h.016zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016a5.54 5.54 0 0 0 .016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225h2.4z"></path></svg>
</a>
</div>
</div>

<div class="footer-col link-col">
<h4>EXPLORE</h4>
<ul>
<li>
<a href="/?page=home" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
Home
</a>
</li>
<li>
<a href="/?page=famous" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
Famous destinations
</a>
</li>
<li>
<a href="/?page=planner" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>
AI trip planner
</a>
</li>
<li>
<a href="/?page=feedback" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/><path d="M8 9h8"/><path d="M8 13h6"/></svg>
User feedback
</a>
</li>

<li>
<a href="/?page=history" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><polyline points="3 3 3 8 8 8"/><line x1="12" y1="7" x2="12" y2="12"/><line x1="12" y1="12" x2="16" y2="14"/></svg>
My trip history
</a>
</li>
<li>
<a href="/?page=planner" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 18 15 15"/></svg>
Download itinerary
</a>
</li>
</ul>
</div>

<div class="footer-col link-col">
<h4>TOP DESTINATIONS</h4>
<ul>
<li>
<a href="/?page=dest_kashmir" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
Kashmir, India
</a>
</li>
<li>
<a href="/?page=dest_tokyo" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
Tokyo, Japan
</a>
</li>
<li>
<a href="/?page=dest_paris" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
Paris, France
</a>
</li>
<li>
<a href="/?page=dest_dubai" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
Dubai, UAE
</a>
</li>
</ul>
</div>
</div>

<div class="footer-bottom-row">
<div class="company-section">
<h4>COMPANY</h4>
<ul>
<li>
<a href="#top" target="_self">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
About
</a>
</li>
<li>
<a href="mailto:dheerajl116232@gmail.com">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
Email
</a>
</li>
<li>
<a href="https://instagram.com/dheeraj_ll6_/" target="_blank">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
Instagram
</a>
</li>
<li>
<a href="https://linkedin.com/in/dheerajkumar116232/" target="_blank">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="footer-link-icon"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
LinkedIn
</a>
</li>
</ul>
</div>

<div class="scroll-top-container">
<a href="#top" target="_self" class="scroll-top-btn">↓</a>
</div>

<div class="bottom-spacer"></div>
</div>
</div>
""", unsafe_allow_html=True)
