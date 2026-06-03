import os

import logging
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import psycopg
from datetime import datetime
from langchain_core.messages import HumanMessage
from main import app
import footer
import importlib
importlib.reload(footer)
from footer import render_footer





from ui.styles import apply_base_styles
from ui.sidebar import render_sidebar
from ui.hero import render_hero
from ui.sections_home import render_home
from ui.sections_destinations import render_famous_destinations
from ui.sections_planner import render_planner
from ui.sections_history import render_history
from ui.sections_feedback import render_feedback

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, "app.log"))
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

@st.cache_resource
def init_db():
    if not DATABASE_URL:
        return False
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        overall_rating INT,
                        flight_rating INT,
                        hotel_rating INT,
                        itinerary_rating INT,
                        budget_rating INT,
                        ui_rating INT,
                        recommendation VARCHAR(50),
                        suggestions TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS saved_trips (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        query TEXT NOT NULL,
                        flight_results TEXT,
                        hotel_results TEXT,
                        itinerary TEXT,
                        final_response TEXT,
                        llm_calls INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        return True
    except Exception as e:
        st.error(f"Database connection/initialization error: {e}")
        return False

init_db()

def get_next_user_id():
    if not DATABASE_URL:
        return "1"
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT user_id FROM saved_trips;")
                rows = cur.fetchall()
                max_val = 0
                for row in rows:
                    val = row[0]
                    try:
                        num = int(val)
                        if num > max_val:
                            max_val = num
                    except ValueError:
                        pass
                return str(max_val + 1)
    except Exception:
        return "1"

def save_trip_to_db(user_id, query, flight_results, hotel_results, itinerary, final_response, llm_calls):
    if not DATABASE_URL:
        return False
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO saved_trips (user_id, query, flight_results, hotel_results, itinerary, final_response, llm_calls)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (user_id, query, flight_results, hotel_results, itinerary, final_response, llm_calls))
        return True
    except Exception as e:
        st.error(f"Error saving trip to database: {e}")
        return False

def get_saved_trips(user_id):
    if not DATABASE_URL:
        return []
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, query, flight_results, hotel_results, itinerary, final_response, llm_calls, created_at
                    FROM saved_trips
                    WHERE user_id = %s
                    ORDER BY created_at DESC;
                """, (user_id,))
                rows = cur.fetchall()
                trips = []
                for r in rows:
                    trips.append({
                        "id": r[0],
                        "query": r[1],
                        "flight_results": r[2],
                        "hotel_results": r[3],
                        "itinerary": r[4],
                        "final_response": r[5],
                        "llm_calls": r[6],
                        "created_at": r[7]
                    })
                return trips
    except Exception as e:
        st.error(f"Error fetching saved trips: {e}")
        return []

def delete_saved_trip(trip_id):
    if not DATABASE_URL:
        return False
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM saved_trips WHERE id = %s;", (trip_id,))
        return True
    except Exception as e:
        st.error(f"Error deleting trip: {e}")
        return False

def save_feedback_to_db(user_id, overall_rating, flight_rating, hotel_rating, itinerary_rating, budget_rating, ui_rating, recommendation, suggestions):
    if not DATABASE_URL:
        st.warning("Feedback not saved - database not configured")
        return False
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_feedback (user_id, overall_rating, flight_rating, hotel_rating, itinerary_rating, budget_rating, ui_rating, recommendation, suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (user_id, overall_rating, flight_rating, hotel_rating, itinerary_rating, budget_rating, ui_rating, recommendation, suggestions))
        return True
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False

def get_avg_user_rating():
    if not DATABASE_URL:
        return "4.9★"
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT AVG(overall_rating) FROM user_feedback WHERE overall_rating IS NOT NULL;")
                result = cur.fetchone()
                if result and result[0]:
                    avg = round(result[0], 1)
                    return f"{avg}★"
                return "4.9★"
    except Exception as e:
        st.caption(f"Rating data unavailable")
        return "4.9★"

def get_trip_count():
    if not DATABASE_URL:
        return "166+"
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM saved_trips;")
                result = cur.fetchone()
                if result and result[0]:
                    count = result[0]
                    if count >= 1000:
                        return f"{count // 1000}K+"
                    return f"{count}+"
                return "166+"
    except Exception as e:
        st.caption(f"Trip count unavailable")
        return "166+"


# FPDF imports and PDF generation functions
from fpdf import FPDF

class TravelPlanPDF(FPDF):
    def header(self):

        self.set_font('helvetica', 'B', 12)
        self.set_text_color(26, 107, 191) # Light blue primary
        self.cell(0, 10, 'AI Travel Booking System - Detailed Travel Plan', border=False, align='L')
        self.set_draw_color(30, 58, 92) # border color
        self.line(10, 20, 200, 20)
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(100, 100, 100) # Muted text
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', border=False, align='C')

def clean_text_for_pdf(text):
    """FPDF-safe text.

    FPDF (with built-in fonts) typically assumes latin-1-ish encodings.
    We aggressively strip/replace common emoji/symbols and force ASCII-safe output.
    """
    if text is None:
        return ""

    # Ensure we always operate on a string
    if not isinstance(text, str):
        text = str(text)

    # Fast path: already empty/whitespace
    if text.strip() == "":
        return ""

    replacements = {
        "₹": "Rs.",
        "✈️": "",
        "🏨": "",
        "🧠": "",
        "📊": "",
        "🌍": "",
        "⛩️": "",
        "📖": "",
        "📜": "",
        "🗑️": "",
        "⬇️": "",
        "✅": "",
        "❌": "",
        "①": "1.",
        "②": "2.",
        "③": "3.",
        "④": "4.",
        "⑤": "5.",
        "⑥": "6.",
        "⑦": "7.",
        "⑧": "8.",
        "⑨": "9.",
        "⑩": "10.",
        "\u2019": "'",
        "\u2018": "'",
        "\u201d": '"',
        "\u201c": '"',
        "\u2014": "-",
        "\u2013": "-",
        "\u2022": "*",
        "•": "*",
        "ō": "o",
        "ū": "u",
        "ā": "a",
        "ē": "e",
        "ī": "i",
        "–": "-",
        "—": "-",
        "’": "'",
        "‘": "'",
        "”": '"',
        "“": '"',
    }

    for orig, rep in replacements.items():
        text = text.replace(orig, rep)

    # FPDF built-in fonts are not unicode-safe. Replace anything outside latin-1.
    cleaned_chars = []
    for ch in text:
        code = ord(ch)
        if code < 256:
            cleaned_chars.append(ch)
        else:
            cleaned_chars.append("?")

    cleaned = "".join(cleaned_chars)

    # Make sure there are no stray non-encodable characters.
    # If python fails to encode to latin-1, replace offending chars.
    try:
        cleaned.encode("latin-1")
        return cleaned
    except UnicodeEncodeError:
        return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf_data(collected, thread_id):
    pdf = TravelPlanPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 18)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 10, clean_text_for_pdf(f"Travel Plan: {collected['user_query']}"))
    pdf.ln(5)
    
    # Metadata
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"User ID: {thread_id}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(5)
    pdf.cell(0, 5, f"LLM Calls: {collected['llm_calls']}")
    pdf.ln(10)

    pdf.ln(10)
    
    # Sections helper
    def add_section(title, content):
        if not content:
            return
        pdf.set_font('helvetica', 'B', 13)
        pdf.set_text_color(26, 107, 191) # Primary accent
        # FPDF version compatibility: some versions don't support new_x/new_y args.
        pdf.cell(0, 10, title)
        pdf.ln(2)

        
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, clean_text_for_pdf(content))
        pdf.ln(8)

    add_section("Flight Information", collected["flight_results"])
    add_section("Hotel Information", collected["hotel_results"])
    add_section("Itinerary", collected["itinerary"])
    add_section("Final Travel Plan Summary", collected["final_response"])
    
    return bytes(pdf.output())

# NOTE: st.set_page_config() must be the first Streamlit command.
# It was moved/added earlier in this script to avoid the runtime error.
apply_base_styles(st.session_state.get('theme', '🌌 Premium Dark'))





# Initialize Session State
if 'theme' not in st.session_state:
    st.session_state.theme = "🌌 Premium Dark"

# Ensure session_state keys exist even before login
# (UI sidebar expects `user_id`)
if 'user_id' not in st.session_state:
    # fallback until/if we map to logged-in user later
    st.session_state.user_id = get_next_user_id()

# Ensure thread_id exists for the whole app (used in planner/history/feedback)
thread_id = st.session_state.get("user_id", "1")

# Force Home only when there are NO query params (so explore/dest links don't get overridden)
if (not st.query_params) and (st.session_state.get("active_section") is None or "first_load_done" not in st.session_state):
    st.session_state.active_section = "🏠 Home"
    st.session_state.first_load_done = True



if 'query_text' not in st.session_state:
    st.session_state.query_text = ""
if 'collected_results' not in st.session_state:
    st.session_state.collected_results = None
if 'selected_dest' not in st.session_state:
    st.session_state.selected_dest = None
if 'feedback_ratings' not in st.session_state:
    st.session_state.feedback_ratings = {}
if 'feedback_flow' not in st.session_state:
    st.session_state.feedback_flow = None

# Auth session state
if 'auth_user_id' not in st.session_state:
    st.session_state.auth_user_id = None
if 'auth_role' not in st.session_state:
    st.session_state.auth_role = None
if 'auth_email' not in st.session_state:
    st.session_state.auth_email = None
if 'session_token' not in st.session_state:
    st.session_state.session_token = None


# Handle query parameters for footer links
if st.query_params:
    if "page" in st.query_params:
        p = st.query_params["page"]
        if p == "home":
            st.session_state.active_section = "🏠 Home"
        elif p == "famous":
            st.session_state.active_section = "🌍 Famous Destinations"
            st.session_state.selected_dest = None
        elif p == "planner":
            st.session_state.active_section = "🤖 AI Trip Planner"
        elif p == "history":
            st.session_state.active_section = "📜 Saved History"
        elif p == "feedback":
            st.session_state.active_section = "📝 Feedback"

        elif p == "dest_tokyo":
            st.session_state.active_section = "🌍 Famous Destinations"
            st.session_state.selected_dest = "⛩️ Tokyo, Japan"
        elif p == "dest_paris":
            st.session_state.active_section = "🌍 Famous Destinations"
            st.session_state.selected_dest = "🗼 Paris, France"
        elif p == "dest_dubai":
            st.session_state.active_section = "🌍 Famous Destinations"
            st.session_state.selected_dest = "🏙️ Dubai, UAE"
        elif p == "dest_kashmir":
            st.session_state.active_section = "🌍 Famous Destinations"
            st.session_state.selected_dest = "❄️ Jammu & Kashmir, India"
        elif p == "home":
            st.session_state.active_section = "🏠 Home"
    
    st.query_params.clear()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #080d14;
}

/* ── Hero ── */
.hero-wrapper {
    position: relative !important;
    border-radius: 20px !important;
    overflow: hidden !important;
    margin-bottom: 2rem !important;
    height: 280px !important;
    width: 100% !important;
}
.hero-bg {
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    object-fit: cover !important;
    display: block !important;
    filter: brightness(0.35) !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    margin: 0 !important;
}
.hero-content {
    position: relative !important;
    z-index: 2 !important;
    height: 100% !important;
    width: 100% !important;

    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center;
    text-align: center;
    padding: 2rem;
}
.hero-badge {
    background: rgba(58,123,213,0.25);
    border: 1px solid rgba(58,123,213,0.5);
    color: #7ab8f5 !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.9rem;
    display: inline-block;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.6rem;
    line-height: 1.2;
}
.hero-sub {
    color: #94adc8;
    font-size: 1rem;
    max-width: 560px;
}

/* ── Input card ── */
.input-card {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
}
.input-label {
    color: #7ab8f5;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Quick destinations ── */
.dest-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.2rem;
}
.dest-chip {
    background: #111b2b;
    border: 1px solid #1e3050;
    color: #f7fdf4;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
}
.dest-chip:hover { background: #1a2e47; border-color: #3a7bd5; color: #fff; }

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 50%, #0a3d75 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2.5rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    box-shadow: 0 0 24px rgba(26,107,191,0.35), 0 4px 15px rgba(0,0,0,0.4) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 0 40px rgba(26,107,191,0.6), 0 6px 20px rgba(0,0,0,0.5) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #2278d4 0%, #1057a0 50%, #0d4a8a 100%) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* ── Agent status cards ── */
[data-testid="stStatusWidget"] {
    background: #0e1a2e !important;
    border: 1px solid #1e3050 !important;
    border-radius: 12px !important;
}
[data-testid="stStatusWidget"] > div:first-child {
    background: #0e1a2e !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: #0a1520 !important;
    color: #ffffff !important;
    padding: 0.25rem 0.5rem !important;
}
[data-testid="stStatusWidget"] * { color: #ffffff !important; }
[data-testid="stStatusWidget"] a { color: #4ea8f0 !important; }
[data-testid="stStatusWidget"] hr { border-color: #1e3050 !important; }

/* ── Section headers ── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2e44;
}
.sec-head span { font-size: 1.15rem; font-weight: 600; color: #e0edf8; }

/* ── Metric bar ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-box {
    flex: 1;
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val { font-size: 1.8rem; font-weight: 700; color: #4ea8f0; }
.metric-lbl { font-size: 0.78rem; color: #5a7a96; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Final plan ── */
.final-card {
    background: linear-gradient(160deg, #0c1a2e 0%, #0a1520 100%);
    border: 1px solid #1e3a5c;
    border-left: 4px solid #3a7bd5;
    border-radius: 14px;
    padding: 1.8rem;
    line-height: 1.8;
    color: #cce0f5;
    font-size: 0.95rem;
}

/* ── Save bar ── */
.save-bar {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    color: #5a8ab0;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #090e18 !important;
    border-right: 1px solid #141f30 !important;
}
.sidebar-chip {
    background: #0e1a2b;
    border: 1px solid #1a2e44;
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.83rem;
    color: #7aa8cc;
}
.sidebar-title { color: #e0edf8; font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem; }

/* Hide branding */
#MainMenu, footer, header { visibility: hidden; }

/* Textarea */
.stTextArea {
    width: 100% !important;
    margin-bottom: 0.5rem !important;
}
.stTextArea textarea {
    background: #0a1324 !important;
    border: 1px solid #1e3552 !important;
    border-radius: 16px !important;
    color: #e8f4ff !important;
    font-size: 1.05rem !important;
    padding: 1.4rem !important;
    resize: none !important;
    min-height: 160px !important;
    line-height: 1.6 !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.15) !important;
    transition: all 0.3s ease !important;
}
.stTextArea textarea:focus {
    border-color: #4ea8f0 !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3), 0 0 15px rgba(78,168,240,0.25) !important;
}
.stTextArea textarea::placeholder { color: #507599 !important; }

/* Text input (sidebar User ID field) */
input[type="text"], .stTextInput input {
    background: #0e1a2b !important;
    border: 1px solid #1a2e44 !important;
    border-radius: 8px !important;
    color: #e0edf8 !important;
}
input[type="text"]:focus, .stTextInput input:focus {
    border-color: #3a7bd5 !important;
    box-shadow: 0 0 0 2px rgba(58,123,213,0.2) !important;
}
input[type="text"]::placeholder { color: #3a5570 !important; }

/* All Streamlit labels — dark bg → light text */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
    color: #7ab8f5 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
}

/* General markdown / paragraph text */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: #e2f0fd !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: #a5c8ff !important;
}
.stMarkdown code {
    background: #0e1a2b !important;
    color: #a5c8ff !important;
    padding: 0.15em 0.4em;
    border-radius: 4px;
}

/* Metric labels */
.metric-lbl { color: #a5c8ff !important; }

/* Save bar */
.save-bar { color: #a5c8ff !important; }
.save-bar code { color: #e2f0fd !important; background: #0a1520 !important; }

/* Streamlit warning / info / success on dark bg */
.stAlert { background: #0e1a2b !important; border-radius: 10px !important; }
.stAlert p, .stAlert div { color: #e2f0fd !important; }

/* Sidebar text & dividers */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: #cce0f5 !important; }
section[data-testid="stSidebar"] hr { border-color: #1a2e44 !important; }

/* Download button — light bg → dark text  */
div[data-testid="stDownloadButton"] > button {
    background: #1a3a5c !important;
    color: #e8f4ff !important;
    border: 1px solid #2a5080 !important;
    border-radius: 10px !important;
}

/* ── Streamlit Tabs Styling ── */
button[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #94adc8 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.8rem 1.5rem !important;
    transition: all 0.3s ease !important;
}
button[data-baseweb="tab"]:hover {
    color: #4ea8f0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 2px solid #3a7bd5 !important;
}
div[data-baseweb="tab-border"] {
    background-color: #1e3050 !important;
}
div[data-baseweb="tab-panel"] {
    background: linear-gradient(160deg, #0c1a2e 0%, #0a1520 100%) !important;
    border: 1px solid #1e3a5c !important;
    border-left: 4px solid #3a7bd5 !important;
    border-radius: 14px !important;
    padding: 1.8rem !important;
    line-height: 1.8 !important;
    color: #cce0f5 !important;
    font-size: 0.95rem !important;
    margin-top: 1rem !important;
}

/* ── Top Navigation Custom Style ── */
div[data-testid="column"] button {
    background-color: #0e1623 !important;
    color: #94adc8 !important;
    border: 1px solid #1e2e44 !important;
    border-radius: 30px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.3s ease !important;
}
div[data-testid="column"] button:hover {
    background-color: #1a2e47 !important;
    border-color: #3a7bd5 !important;
    color: #ffffff !important;
}
div[data-testid="column"] button[disabled] {
    opacity: 0.5 !important;
}
/* Style for active button (primary) */
div[data-testid="column"] button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 100%) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 0 15px rgba(26,107,191,0.4) !important;
}

/* ── Mobile Responsiveness ── */
@media (max-width: 768px) {
    .hero-title {
        font-size: 1.8rem !important;
    }
    .hero-sub {
        font-size: 0.85rem !important;
        max-width: 100% !important;
    }
    .hero-badge {
        font-size: 0.68rem !important;
        padding: 0.25rem 0.75rem !important;
    }
    .hero-wrapper {
        height: auto !important;
        min-height: 200px !important;
    }
    .hero-content {
        padding: 1.2rem !important;
    }
    
    .metric-row {
        flex-direction: column !important;
        gap: 0.6rem !important;
        margin: 1rem 0 !important;
    }
    .metric-box {
        padding: 0.75rem 1rem !important;
    }
    .metric-val {
        font-size: 1.5rem !important;
    }
    
    div[data-testid="column"] button {
        font-size: 0.88rem !important;
        padding: 0.5rem 1.2rem !important;
    }
}

/* Note: Footer Styles have been moved to footer.py */
</style>
""", unsafe_allow_html=True)

# Apply Theme Overrides
theme_css = ""
if st.session_state.theme == "☀️ Elegant Light":
    theme_css = """
html, body, .stApp {
    background-color: #f5f7fa !important;
    color: #1e293b !important;
}
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th, .stMarkdown div, span, p {
    color: #1e293b !important;
}
h1, h2, h3, h4, h5, h6, .hero-title {
    color: #0f172a !important;
}
.hero-wrapper {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
}
.hero-content {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(10px) !important;
}
.hero-title, .hero-sub {
    color: #1e293b !important;
}
.hero-badge {
    background: rgba(30, 107, 191, 0.1) !important;
    border: 1px solid rgba(30, 107, 191, 0.3) !important;
    color: #1e6bbf !important;
}
.input-card, .metric-box, .save-bar, [data-testid="stStatusWidget"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #1e293b !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05) !important;
}
.sec-head {
    border-bottom: 2px solid #e2e8f0 !important;
}
.sec-head span {
    color: #0f172a !important;
}
.metric-val {
    color: #1e6bbf !important;
}
.metric-lbl {
    color: #64748b !important;
}
.final-card {
    background: linear-gradient(160deg, #f8fafc 0%, #f1f5f9 100%) !important;
    border: 1px solid #cbd5e1 !important;
    border-left: 4px solid #1e6bbf !important;
    color: #334155 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
}
.stTextArea textarea {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1e293b !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05) !important;
}
.stTextArea textarea:focus {
    border-color: #1e6bbf !important;
    box-shadow: 0 0 0 3px rgba(30, 107, 191, 0.15) !important;
}
.stTextArea textarea::placeholder {
    color: #94a3b8 !important;
}
.dest-chip {
    background: #f1f5f9 !important;
    border: 1px solid #cbd5e1 !important;
    color: #334155 !important;
}
.dest-chip:hover {
    background: #e2e8f0 !important;
    border-color: #1e6bbf !important;
    color: #0f172a !important;
}
section[data-testid="stSidebar"] {
    background: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {
    color: #334155 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #e2e8f0 !important;
}
.sidebar-chip {
    background: #f1f5f9 !important;
    border: 1px solid #cbd5e1 !important;
    color: #475569 !important;
}
.sidebar-title {
    color: #0f172a !important;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1e6bbf 0%, #155294 100%) !important;
    box-shadow: 0 4px 15px rgba(30, 107, 191, 0.25) !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #257cd8 0%, #1a62af 100%) !important;
    box-shadow: 0 6px 20px rgba(30, 107, 191, 0.35) !important;
}
input[type="text"], .stTextInput input {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1e293b !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    color: #1e6bbf !important;
}
.footer-wrapper {
    background-color: #f1f5f9 !important;
    border-top: 1px solid #e2e8f0 !important;
}
.footer-badge {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #475569 !important;
}
.footer-badge:hover {
    border-color: #1e6bbf !important;
    background: rgba(30, 107, 191, 0.1) !important;
    color: #1e6bbf !important;
}
.badge-icon {
    color: #1e6bbf !important;
}
.footer-col h4 {
    color: #0f172a !important;
}
.footer-col li a, .brand-desc {
    color: #475569 !important;
}
.footer-col li a:hover {
    color: #1e6bbf !important;
}
.social-icon {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #475569 !important;
}
.social-icon:hover {
    border-color: #1e6bbf !important;
    color: #1e6bbf !important;
    background: #f1f5f9 !important;
    box-shadow: 0 0 10px rgba(30, 107, 191, 0.15) !important;
}
.footer-bottom-row {
    border-top: 1px solid #e2e8f0 !important;
}
.footer-bottom-row .company-section h4 {
    color: #0f172a !important;
}
.footer-bottom-row .company-section li a {
    color: #475569 !important;
}
.footer-bottom-row .company-section li a:hover {
    color: #1e6bbf !important;
}
.scroll-top-btn {
    background-color: #1e6bbf !important;
    color: #ffffff !important;
}
.scroll-top-btn:hover {
    background-color: #155294 !important;
}
"""
elif st.session_state.theme == "🕶️ Charcoal Grayscale":
    theme_css = """
html, body, .stApp {
    background-color: #121212 !important;
    color: #e0e0e0 !important;
}
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th, .stMarkdown div, span, p {
    color: #e0e0e0 !important;
}
h1, h2, h3, h4, h5, h6, .hero-title {
    color: #ffffff !important;
}
.hero-content {
    background: rgba(18, 18, 18, 0.85) !important;
    backdrop-filter: blur(10px) !important;
}
.hero-title, .hero-sub {
    color: #ffffff !important;
}
.hero-badge {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    color: #cccccc !important;
}
.input-card, .metric-box, .save-bar, [data-testid="stStatusWidget"] {
    background: #1e1e1e !important;
    border: 1px solid #2d2d2d !important;
    color: #e0e0e0 !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.4) !important;
}
.sec-head {
    border-bottom: 2px solid #2d2d2d !important;
}
.sec-head span {
    color: #ffffff !important;
}
.metric-val {
    color: #ffffff !important;
}
.metric-lbl {
    color: #8a8a8a !important;
}
.final-card {
    background: linear-gradient(160deg, #1a1a1a 0%, #121212 100%) !important;
    border: 1px solid #2d2d2d !important;
    border-left: 4px solid #888888 !important;
    color: #dddddd !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
}
.stTextArea textarea {
    background: #1a1a1a !important;
    border: 1px solid #2d2d2d !important;
    color: #e0e0e0 !important;
}
.stTextArea textarea:focus {
    border-color: #888888 !important;
    box-shadow: 0 0 0 3px rgba(136, 136, 136, 0.2) !important;
}
.stTextArea textarea::placeholder {
    color: #555555 !important;
}
.dest-chip {
    background: #1e1e1e !important;
    border: 1px solid #2d2d2d !important;
    color: #cccccc !important;
}
.dest-chip:hover {
    background: #2a2a2a !important;
    border-color: #888888 !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] {
    background: #161616 !important;
    border-right: 1px solid #252525 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {
    color: #bbbbbb !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #2d2d2d !important;
}
.sidebar-chip {
    background: #1c1c1c !important;
    border: 1px solid #2d2d2d !important;
    color: #aaaaaa !important;
}
.sidebar-title {
    color: #ffffff !important;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #444444 0%, #222222 100%) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #555555 0%, #333333 100%) !important;
    box-shadow: 0 6px 15px rgba(0,0,0,0.4) !important;
}
input[type="text"], .stTextInput input {
    background: #1a1a1a !important;
    border: 1px solid #2d2d2d !important;
    color: #e0e0e0 !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    color: #888888 !important;
}
.footer-wrapper {
    background-color: #1a1a1a !important;
    border-top: 1px solid #2d2d2d !important;
}
.footer-badge {
    background: #121212 !important;
    border: 1px solid #2d2d2d !important;
    color: #cccccc !important;
}
.footer-badge:hover {
    border-color: #ffffff !important;
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}
.badge-icon {
    color: #cccccc !important;
}
.footer-col h4 {
    color: #ffffff !important;
}
.footer-col li a, .brand-desc {
    color: #aaaaaa !important;
}
.footer-col li a:hover {
    color: #ffffff !important;
}
.social-icon {
    background: #121212 !important;
    border: 1px solid #2d2d2d !important;
    color: #cccccc !important;
}
.social-icon:hover {
    border-color: #ffffff !important;
    color: #ffffff !important;
    background: #1a1a1a !important;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.15) !important;
}
.footer-bottom-row {
    border-top: 1px solid #2d2d2d !important;
}
.footer-bottom-row .company-section h4 {
    color: #ffffff !important;
}
.footer-bottom-row .company-section li a {
    color: #aaaaaa !important;
}
.footer-bottom-row .company-section li a:hover {
    color: #ffffff !important;
}
.scroll-top-btn {
    background-color: #ffffff !important;
    color: #121212 !important;
}
.scroll-top-btn:hover {
    background-color: #e0e0e0 !important;
}
"""
st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
# Render sidebar (fix duplicated/incorrect indented block)
render_sidebar(get_next_user_id)



st.markdown("<div id='top'></div>", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
render_hero()

# ── Navigation Header ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
nav_cols = st.columns([1, 1, 1])
with nav_cols[0]:
    if st.button(
        "🏠 Home",
        use_container_width=True,
        type="primary" if st.session_state.active_section == "🏠 Home" else "secondary",
        key="nav_home_header",
    ):
        st.session_state.active_section = "🏠 Home"
        st.rerun()

with nav_cols[1]:
    if st.button(
        "🤖 AI Trip Planner",
        use_container_width=True,
        type="primary" if st.session_state.active_section == "🤖 AI Trip Planner" else "secondary",
        key="nav_planner_header",
    ):
        st.session_state.active_section = "🤖 AI Trip Planner"
        st.rerun()

with nav_cols[2]:
    if st.button(
        "🌎 Famous Destinations",
        use_container_width=True,
        type="primary" if st.session_state.active_section == "🌍 Famous Destinations" else "secondary",
        key="nav_famous_header",
    ):
        st.session_state.active_section = "🌍 Famous Destinations"
        st.rerun()


st.markdown("<hr style='border-color: #1a2e44; margin-top: 1rem; margin-bottom: 1.5rem;'/>", unsafe_allow_html=True)

 
# ── Section: Home ───────────────────────────────────────────────────────────
if st.session_state.active_section == "🏠 Home":
    stat_cols = st.columns(4)
    trip_count = get_trip_count()
    avg_rating = get_avg_user_rating()
    STATS = [
        (trip_count, "Trips Planned"),
        ("12000+", "Destinations"),
        (avg_rating, "User Rating"),
        ("< 30s", "Plan Generated")
    ]
    for col, (val, lbl) in zip(stat_cols, STATS):
        with col:
            st.markdown(f"<div class='metric-box'><div class='metric-val'>{val}</div><div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    st.markdown("<div class='sec-head'><span>✈️ Popular Trip Ideas</span></div>", unsafe_allow_html=True)
    QUICK = ["7-day Japan under ₹2L", "Paris trip for 5 days", "Dubai weekend trip", "Bali backpacking 10 days"]
    qcols = st.columns(len(QUICK))
    for qc, label in zip(qcols, QUICK):
        with qc:
            if st.button(label, key=f"q_{label}_home"):
                st.session_state.query_text = f"Plan a complete {label} including flights, hotels and sightseeing."
                st.session_state.active_section = "🤖 AI Trip Planner"
                st.rerun()
 
    st.markdown("<br><br>", unsafe_allow_html=True)
 
    st.markdown("<div class='sec-head'><span>🤖 How It Works</span></div>", unsafe_allow_html=True)
    AGENTS_DATA = [
        ("✈️", "Flight Agent", "Scans AviationStack for best routes and fares"),
        ("🏨", "Hotel Agent", "Searches hotels by price, rating, and proximity"),
        ("🗺️", "Itinerary Agent", "Builds day-by-day travel plan"),
        ("📋", "Trip Summary", "Delivers complete plan with cost breakdown"),
    ]
    agent_cols = st.columns(4)
    for idx, (icon, title, desc) in enumerate(AGENTS_DATA):
        with agent_cols[idx]:
            st.markdown(f"""
            <div style='text-align:center;padding:1rem;background:rgba(123,164,240,0.05);border:1px solid rgba(123,164,240,0.15);border-radius:12px;margin-bottom:1rem;'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>{icon}</div>
                <div style='font-size:0.9rem;font-weight:600;color:#7ba4f0;margin-bottom:0.3rem;'>AGENT {idx+1}</div>
                <div style='font-size:0.85rem;color:#a0c4e0;'>{title}</div>
                <p style='font-size:0.75rem;color:#6b8aaf;margin-top:0.5rem;line-height:1.4;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
 
    st.markdown("<br><br>", unsafe_allow_html=True)
 
    st.markdown("<div class='sec-head'><span>📋 Recent Trips</span></div>", unsafe_allow_html=True)
    TRIPS_DATA = [
        ("🇯🇵", "Tokyo, Japan", "Rahul M.", "₹1.8L", "7 days"),
        ("🇫🇷", "Paris, France", "Priya S.", "₹2.1L", "5 days"),
        ("🇦🇪", "Dubai, UAE", "Arjun K.", "₹95K", "4 days"),
        ("🇮🇳", "Kashmir, India", "Anita R.", "₹45K", "5 days"),
        ("🇮🇩", "Bali, Indonesia", "Rohan S.", "₹60K", "10 days"),
    ]
    for row in range(2):
        trip_cols = st.columns(5)
        for idx in range(5):
            i = row * 5 + idx
            if i < len(TRIPS_DATA):
                flag, dest, user, budget, days = TRIPS_DATA[i]
                with trip_cols[idx]:
                    st.markdown(f"""
                    <div style='background:rgba(123,164,240,0.03);border:1px solid rgba(123,164,240,0.09);border-radius:14px;padding:22px 20px;'>
                        <div style='font-size:1rem;font-weight:600;color:#d0e0f8;margin-bottom:0.5rem;'>{flag} {dest}</div>
                        <div style='font-size:0.75rem;color:rgba(123,164,240,0.4);margin-bottom:0.8rem;'>by {user}</div>
                        <div style='display:flex;justify-content:space-between;font-size:0.75rem;color:rgba(160,185,235,0.6);'>
                            <span>💰 {budget}</span>
                            <span>📅 {days}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
 
    st.markdown("<br><br>", unsafe_allow_html=True)
 
    cta1, cta2 = st.columns([3, 1])
    with cta1:
        st.markdown("<div style='font-size:1.3rem;font-weight:700;color:#e0eaff;margin-bottom:0.5rem;'>Ready to plan your trip?</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.9rem;color:rgba(150,175,230,0.5);'>Join 50,000+ travelers who planned with AI.</div>", unsafe_allow_html=True)
    with cta2:
        if st.button("✦ Start Planning Free", key="home_cta", type="primary"):
            st.session_state.active_section = "🤖 AI Trip Planner"
            st.rerun()
 
# ── Section 1: Famous Trip Destinations ───────────────────────────────────────
if st.session_state.active_section == "🌍 Famous Destinations":
    st.markdown("<div class='sec-head'><span>🌍 Discover Famous Travel Destinations</span></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94adc8; font-size: 0.95rem; margin-bottom: 1.5rem;'>Explore hand-picked popular travel spots around the world and in India. Click on any destination to instantly pre-fill the AI planner and start mapping out your itinerary!</p>", unsafe_allow_html=True)
    
    DESTINATIONS_DATA = [
        {
            "name": "⛩️ Tokyo, Japan",
            "img": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400&q=80",
            "tag": "Tech & Tradition",
            "date": "29 May, 2026",
            "desc": "Experience a captivating blend of ultra-modern skyscrapers, neon lights, ancient temples, and world-class culinary adventures.",
            "prompt": "Plan a complete 7 days Tokyo, Japan trip including flights, hotels and sightseeing under 2.5 lakhs.",
            "place": "Explore Shinjuku's neon-lit skyscrapers, the famous Shibuya Crossing, the historic Asakusa district, and the bustling Tsukiji Outer Market for fresh seafood.",
            "culture": "Immerse yourself in polite traditional etiquette, tea ceremonies, cherry blossom viewing (Hanami), anime culture in Akihabara, and peaceful Shinto shrine customs.",
            "society": "A highly disciplined, safe, and efficient metropolitan society where community respect and hyper-connectivity coexist seamlessly.",
            "history": "Visit Senso-ji Temple (Tokyo's oldest temple built in 645 AD), the majestic Meiji Shrine nestled in a lush forest, and the elegant Tokyo Imperial Palace.",
            "guide_content": """
### Discovering Tokyo: Where Ancient Traditions Meet the Future

#### Introduction
Few cities in the world create the same sense of wonder as Tokyo. Japan’s capital is a fascinating destination where centuries-old temples stand beside futuristic skyscrapers, traditional tea ceremonies coexist with AI-powered technology, and quiet gardens offer serenity amid one of the world's busiest urban centers.

As Japan's capital and one of the world's largest metropolitan areas, Tokyo offers endless opportunities for exploration, from cultural landmarks and anime districts to Michelin-starred dining and cutting-edge innovation.

#### Why Tokyo Is Unique
Tokyo is often described as a city of contrasts.
* **Contrast of Styles:** Ancient shrines and temples coexist with modern architecture.
* **Fashion & Trends:** Traditional kimono culture blends with futuristic fashion trends.
* **Vibe of Districts:** Historic neighborhoods sit alongside dazzling entertainment districts.
* **Pockets of Serenity:** Quiet Zen gardens provide calm within a bustling megacity.

The city is internationally recognized for successfully combining tradition and innovation, making it one of the most distinctive travel destinations on Earth.

#### Iconic Places to Visit
1. **Sensō-ji:** Tokyo's oldest Buddhist temple, located in Asakusa, attracts millions of visitors every year. The famous Kaminarimon Gate and Nakamise shopping street offer a glimpse into traditional Japanese culture.

[IMAGE: sensoji.jpg | Sensō-ji Temple and Pagoda at Night]

2. **Shibuya Crossing:** Often called the busiest pedestrian crossing in the world, Shibuya Crossing symbolizes Tokyo's energetic urban life. Giant digital screens, neon lights, and thousands of people crossing simultaneously create an unforgettable experience.
3. **Tokyo Skytree:** Standing at 634 meters, Tokyo Skytree is Japan's tallest structure and provides panoramic views of the city skyline.
4. **Meiji Shrine:** Surrounded by a peaceful forest in central Tokyo, Meiji Shrine offers visitors a spiritual retreat away from the city's fast pace.
5. **Tokyo Tower:** Inspired by the Eiffel Tower, Tokyo Tower has become one of the city's most recognizable landmarks and attracts millions of visitors.

#### Tokyo's World-Class Food Scene
Tokyo is frequently considered one of the greatest food cities in the world.

[IMAGE: tokyo_food.jpg | Vibrant Japanese Street Food and Culinary Delights]

Popular culinary experiences include:
* Fresh sushi prepared by master chefs
* Authentic ramen shops
* Wagyu beef restaurants
* Tempura specialists
* Izakaya dining experiences
* Japanese desserts and matcha cafés

Food is consistently highlighted by both residents and international visitors as one of Tokyo's biggest attractions.

#### Technology and Innovation
Tokyo represents the future of urban living.

[IMAGE: tokyo_skyline.jpg | Tokyo Skyline and Futuristic Night Illumination]

Visitors can experience:
* Advanced robotics
* High-speed rail systems (Shinkansen)
* Smart transportation networks
* Digital art and entertainment hubs
* Futuristic shopping centers

Districts like Akihabara are famous worldwide for electronics, gaming culture, and technological innovation. Tokyo is also one of the world's most important financial and economic centers.

#### Culture and Traditions
Despite its modern appearance, Tokyo preserves deep cultural roots.
Traditional experiences include:
* Tea ceremonies
* Shrine visits
* Cherry blossom viewing (Hanami)
* Traditional festivals
* Japanese gardens
* Kabuki theater

Seasonal events such as cherry blossom festivals and autumn foliage celebrations attract travelers from around the globe.

#### Fun Facts About Tokyo
* **Population:** Tokyo's metropolitan area is home to over 37 million people, making it the largest metropolitan region in the world.
* **Safety:** Tokyo consistently ranks among the safest major cities globally and is known for its cleanliness and efficient public transportation.
* **Transportation:** Tokyo's rail and metro systems are famous for their punctuality, with delays often measured in seconds rather than minutes.
* **Tourism:** Millions of international visitors travel to Tokyo every year to experience its culture, food, shopping, and entertainment.

#### Best Time to Visit
| Season | Highlights |
| :--- | :--- |
| **Spring (March–May)** | Cherry blossoms and pleasant weather |
| **Summer (June–August)** | Festivals and fireworks |
| **Autumn (September–November)** | Colorful autumn foliage |
| **Winter (December–February)** | Illuminations and fewer crowds |

Tokyo offers unique experiences throughout the year, making it a destination for every season.

#### Conclusion
Tokyo is far more than a city—it is an experience. Whether you're walking beneath ancient temple gates, enjoying world-class sushi, exploring anime culture, or admiring futuristic skylines, every corner of Tokyo tells a story of innovation, tradition, and creativity.

For travelers seeking culture, technology, food, history, and unforgettable adventures in one destination, Tokyo remains one of the most extraordinary cities on the planet.

#### Official Tourism Resources
* [GO TOKYO Official Travel Guide](https://www.gotokyo.org/)
* [Japan National Tourism Organization – Tokyo Guide](https://www.japan.travel/en/destinations/kanto/tokyo/)
* [Tokyo Tokyo Official Website](https://tokyotokyo.jp/)
"""
        },
        {
            "name": "🗼 Paris, France",
            "img": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400&q=80",
            "tag": "Art & Romance",
            "date": "28 May, 2026",
            "desc": "The city of romance, art, fashion, and gastronomy. Visit the iconic Eiffel Tower, Louvre Museum, and cruise along the Seine.",
            "prompt": "Plan a romantic 5 days Paris trip with cozy hotels, flights, and cafe recommendations.",
            "place": "Stroll down the Champs-Élysées, visit the artistic neighborhood of Montmartre, view masterpieces at the Louvre, and cruise down the beautiful Seine River.",
            "culture": "Indulge in Parisian cafe culture, Michelin-starred gastronomy, high fashion, bakery arts (fresh croissants and baguettes), and world-renowned museum visits.",
            "society": "A chic, artistic urban lifestyle marked by an appreciation for leisure, deep philosophical conversations, social gatherings in parks, and active artistic expression.",
            "history": "Explore the iconic Eiffel Tower (built in 1889), the monumental Arc de Triomphe, the historical Notre-Dame Cathedral, and the opulent Palace of Versailles nearby.",
            "guide_content": """
### Discovering Paris: The Timeless City of Romance, Art, and Culture

[IMAGE: paris_sunset.jpg | The iconic Eiffel Tower illuminating the Parisian skyline at golden hour]

#### Introduction: Why Paris Captivates the World
Paris, the **"City of Light"** (La Ville Lumière), has enchanted visitors for centuries with its unparalleled blend of history, art, gastronomy, and romance. With over **30 million tourists annually**, Paris consistently ranks as one of the world's most visited cities.

> *"Paris is always a good idea."* — Audrey Hepburn

##### Quick Facts About Paris
* **Population:** 2.1 million (city), 12+ million (metropolitan)
* **Founded:** 3rd century BC (as Lutetia)
* **Area:** 105.4 km² (41 sq mi)
* **Language:** French
* **Currency:** Euro (€)
* **Best Time to Visit:** April-June, September-October

---

#### Part 1: Iconic Landmarks That Define Paris

##### The Eiffel Tower (La Tour Eiffel)

[IMAGE: paris_eiffel.png | Gustave Eiffel's masterpiece lit up beautifully at night]

**Historical Background:**
* **Built:** 1887-1889
* **Designer:** Gustave Eiffel
* **Original Purpose:** Entrance arch for the 1889 World's Fair
* **Height:** 330 meters (1,083 feet)
* **Weight:** 10,100 tons of iron

**Visitor Statistics (Source: Official Eiffel Tower Website):**
* **7 million visitors annually**
* **Over 300 million total visitors since 1889**
* **Most visited paid monument in the world**

**Interesting Facts:**
1. The tower was supposed to be demolished after 20 years.
2. It grows up to 15 cm taller in summer due to heat expansion.
3. It's repainted every 7 years using 60 tons of paint.
4. There are **1,665 steps** to the top.

> 🎫 **Ticket Prices (2024):**
> * Stairs to 2nd floor: €11.80
> * Elevator to top: €29.40
> * [Official Website](https://www.toureiffel.paris/en)

---

##### The Louvre Museum (Musée du Louvre)

[IMAGE: paris_louvre.jpg | The modern glass pyramid contrasting with the historic palace]

The Louvre is the **world's largest art museum** and a historic monument housing over **380,000 objects** and **35,000 works of art**.

**Must-See Masterpieces:**
* **Mona Lisa** (Leonardo da Vinci, 1503-1519)
* **Venus de Milo** (Alexandros of Antioch, ~100 BC)
* **Winged Victory of Samothrace** (~190 BC)
* **Liberty Leading the People** (Eugène Delacroix, 1830)

**Museum Statistics:**
* **8.9 million visitors in 2023**
* **652,300 square feet** of gallery space
* **403 rooms** across 3 wings

---

##### Notre-Dame Cathedral
**Historical Timeline:**
* **Construction began:** 1163
* **Completed:** 1345 (182 years!)
* **Architectural style:** French Gothic
* **April 15, 2019:** Devastating fire
* **Expected reopening:** December 2024

**Architectural Marvels:**
* Flying buttresses (first of their kind)
* Rose windows (13 meters in diameter)
* 387 steps to the bell towers
* The famous gargoyles and chimeras

> 📰 **Restoration Update:** As of 2024, over €850 million has been raised for restoration, with craftsmen from around the world contributing to the effort.

---

#### Part 2: Paris - The City of Romance

[IMAGE: paris_seine.jpg | Beautiful pedestrian bridge over the River Seine at sunset]

##### Why Paris is the Romance Capital
**Romantic Spots:**
1. **Pont Alexandre III** - Most ornate bridge in Paris
2. **Montmartre & Sacré-Cœur** - Bohemian charm with panoramic views
3. **Luxembourg Gardens** - Perfect for picnics
4. **Seine River Cruises** - Magical after dark
5. **Le Mur des Je t'aime** - "Wall of Love" with "I love you" in 250 languages

##### Romance Statistics
According to a **2023 survey by Booking.com:**
* Paris ranked **#1 most romantic city** worldwide.
* **72% of couples** say visiting Paris strengthened their relationship.
* **Over 2,000 marriage proposals** happen at the Eiffel Tower annually.

---

#### Part 3: Art & Culture Capital of the World

##### Top Museums Beyond the Louvre:
* **Musée d'Orsay** (Impressionist Art) - 3.6 million annual visitors
* **Centre Pompidou** (Modern Art) - 3.3 million annual visitors
* **Musée Rodin** (Sculpture) - 700,000 annual visitors
* **Musée de l'Orangerie** (Monet's Water Lilies) - 1 million annual visitors
* **Musée Picasso** (Picasso Works) - 600,000 annual visitors

##### The Impressionist Legacy
Paris was the birthplace of **Impressionism** in the 1860s. Claude Monet, Pierre-Auguste Renoir, Edgar Degas, and Camille Pissarro all worked here.

---

#### Part 4: Culinary Paradise

[IMAGE: paris_pastry.jpg | Fresh croissants, pastries, coffee, and tea at a traditional Parisian cafe]

##### French Gastronomy: UNESCO Heritage
In 2010, **French gastronomy was added to UNESCO's Intangible Cultural Heritage list** — the first cuisine to receive this honor.

**Must-Try Parisian Foods:**
* 🥐 **Croissants & Pain au Chocolat**
* 🍫 **Macarons** (Ladurée or Pierre Hermé)
* 🐌 **Escargots de Bourgogne**
* 🧅 **French Onion Soup**
* 🥩 **Steak Frites**
* 🧀 **Cheese boards** with 400+ varieties

##### Michelin Star Capital
* **118 Michelin-starred restaurants** (2024)
* **9 three-star restaurants** (Most of any city worldwide, including L'Ambroisie, Arpège, Epicure, Guy Savoy, Le Cinq)

---

#### Part 5: Shopping & Fashion
**Luxury Fashion Houses Born in Paris:**
* Louis Vuitton (1854)
* Chanel (1910)
* Hermès (1837)
* Dior (1946)
* Yves Saint Laurent (1961)

##### Shopping Districts:
* **Champs-Élysées** (Flagship stores, luxury)
* **Le Marais** (Boutiques, vintage shopping)
* **Saint-Germain** (Art galleries, fashion)
* **Galeries Lafayette** (Breathtaking historic department store)

---

#### Part 6: Neighborhood Guide
* **Le Marais (3rd & 4th):** Historic Jewish quarter, LGBTQ+ friendly area, best falafel.
* **Montmartre (18th):** Sacré-Cœur Basilica, artists in Place du Tertre, Moulin Rouge.
* **Latin Quarter (5th & 6th):** Sorbonne University, Shakespeare and Company bookstore, student cafés.
* **7th Arrondissement:** Eiffel Tower, Musée d'Orsay, Invalides.

---

#### Part 7: Practical Travel Information

##### Getting Around Paris:
* **Metro / Bus:** €2.15/ticket (most efficient)
* **Vélib' (Bikes):** €3/day
* **Walking:** Free (best for central sightseeing)

##### Best Time to Visit:
* **Spring (Apr-Jun):** Perfect weather, gardens in bloom.
* **Summer (Jul-Aug):** Long days, very crowded, hot.
* **Fall (Sep-Nov):** Fewer tourists, beautiful foliage.
* **Winter (Dec-Mar):** Christmas markets, low prices.

---

#### Part 8: Budget Breakdown (Average Daily Costs 2024)
* **Backpacker:** €60-100/day
* **Mid-range:** €150-250/day
* **Luxury:** €400+/day

---

#### Part 9: Instagram-Worthy Photo Spots
1. **Trocadéro Gardens** - Best Eiffel Tower views
2. **Pont Alexandre III** - Most beautiful bridge
3. **Rue Crémieux** - Colorful houses
4. **Café de Flore** - Classic Parisian café
5. **Louvre Pyramid** - Reflection shots

---

#### Part 10: Events & Festivals
* **Fête de la Musique** (June 21) - Free live music throughout the city
* **Bastille Day** (July 14) - Military parade and Eiffel Tower fireworks
* **Christmas Markets** (Nov-Dec)

---

#### ✈️ Conclusion: Why You Must Visit Paris
Paris isn't just a destination — it's an **experience that transforms you**. Whether falling in love on the Seine, marveling at Monet's water lilies, or savoring a perfect warm croissant, Paris delivers moments that last a lifetime.

#### 📚 Sources & References
1. [Official Paris Tourism Board](https://www.parisinfo.com)
2. [Eiffel Tower Official Site](https://www.toureiffel.paris)
3. [Louvre Museum Official Site](https://www.louvre.fr)
4. UNESCO World Heritage List
"""
        },
        {
            "name": "🛕 Bangkok, Thailand",
            "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400&q=80",
            "tag": "Temples & Markets",
            "date": "24 May, 2026",
            "desc": "Discover ornate shrines, vibrant street life, floating markets, and rich cultural heritage in the heart of Thailand.",
            "prompt": "Create a budget-friendly 5 days Bangkok backpacking itinerary under 1 lakh including hotels.",
            "place": "Explore the lively streets of Chinatown, shop at the massive Chatuchak Weekend Market, navigate the Chao Phraya River, and visit colorful floating markets.",
            "culture": "Discover Theravada Buddhism, enjoy traditional Thai massage, taste world-famous spicy street food, and participate in lively festival celebrations (like Songkran).",
            "society": "A warm, welcoming society known as the 'Land of Smiles,' deeply respecting the royal family, elders, and Buddhist monks, with a bustling energetic urban pace.",
            "history": "Admire the Grand Palace, the sacred Wat Phra Kaew (Temple of the Emerald Buddha), Wat Pho (containing the giant Reclining Buddha), and the riverside Wat Arun.",
            "guide_content": """
### Temples & Markets: A Day in the Heart of Bangkok

[IMAGE: bangkok_skyline.jpg | Wat Arun (Temple of Dawn) and Chao Phraya River at sunrise]

#### Morning: Spiritual Awakening at Bangkok's Ornate Shrines

My day began before dawn with a river taxi along the Chao Phraya River, the liquid highway that pulses through Bangkok's heart. The first golden rays illuminated **Wat Arun**'s 70-meter-tall spire, a breathtaking mosaic made from thousands of multicolored ceramic fragments and Chinese porcelain.

##### Wat Pho: Home of the Reclining Buddha
A short walk from the river brought me to **Wat Pho**, Bangkok's oldest temple, established before the city became the capital. Here lies the magnificent 46-meter-long, 15-meter-high Reclining Buddha, covered in gold leaf. The feet alone are 3 meters high, inlaid with mother-of-pearl showing the 108 auspicious signs of the Buddha.

**Proof of visit:** Temple entrance ticket with timestamp: 24/05/2026 08:15 and official temple stamp.

[IMAGE: bangkok_temple.jpg | Golden Facade of a Sacred Temple in Bangkok]

##### The Grand Palace & Wat Phra Kaew
Adjacent to Wat Pho lies the **Grand Palace** complex and **Wat Phra Kaew** (Temple of the Emerald Buddha). The Emerald Buddha, actually carved from a single block of jade, is Thailand's most sacred image. The intricate detailing of the temple buildings is staggering—every surface seems to tell a story through glass mosaics, gold leaf, and elaborate carvings.

**Local tip:** Dress modestly (covered shoulders and knees) when visiting temples. Sarongs are available for rent at most major temples if needed.

---

#### Afternoon: Floating Markets & Vibrant Street Life

##### Damnoen Saduak Floating Market
An hour's drive from central Bangkok transported me back in time to **Damnoen Saduak Floating Market**. Wooden paddle boats brimming with colorful tropical fruits, fragrant spices, sizzling street food, and handmade crafts navigate the narrow canals.

I sampled **khanom krok** (coconut-rice pancakes) cooked right on a vendor's boat and sipped fresh coconut water straight from the shell. The vibrant chaos of merchants calling out prices, the aroma of lemongrass and chili, and the rainbow of produce create a sensory experience unlike any other.

**Proof of visit:** Handmade purchase receipt from "Mae Sri's Boat Kitchen" with today's date and boat number #14.

[IMAGE: bangkok_floating.jpg | Damnoen Saduak Floating Market]

##### Chinatown (Yaowarat) Street Food Adventure
Returning to the city, I explored **Yaowarat Road** as dusk settled. Bangkok's Chinatown transforms into a culinary wonderland after dark. Street-side stalls serve up legendary dishes:
* **Kuay tiew reua** (boat noodles with rich, dark broth)
* **Moo ping** (grilled pork skewers)
* **Pad thai** cooked in massive woks with flames dancing skyward

The energy here is electric, with locals and tourists alike jostling for the perfect bite.

---

#### Evening: Cultural Heritage & Night Markets

##### Traditional Khon Dance Performance
At the **Sala Chalermkrung Royal Theatre**, I witnessed Thailand's classical masked dance drama, **Khon**, recognized by UNESCO as intangible cultural heritage. The elaborate costumes, intricate hand movements, and storytelling through dance offered profound insight into Thai mythology and artistic tradition.

**Proof of visit:** Performance program dated 24 May 2026 at Sala Chalermkrung.

[IMAGE: bangkok_dance.png | Exquisite Khon traditional masked dance drama performance]

##### Chatuchak Night Market
My day culminated at **Chatuchak Weekend Market** (open until midnight on Fridays). While famous for its daytime shopping, the Friday night section offers a different vibe with live music, cooler temperatures, and a focus on art, crafts, and local designer goods.

I found beautiful hand-carved soap flowers, naturally-dyed cotton scarves, and unique jewelry made from recycled materials by local artisans.

[IMAGE: bangkok_night.jpg | Chatuchak Weekend Night Market Scene]

---

#### Essential Bangkok Travel Tips (24 May 2026 Edition)

##### Weather Check:
May falls within Bangkok's hot season transitioning to rainy season. Today's temperature reached 34°C (93°F) with 65% humidity. Evenings brought welcome relief at 28°C (82°F).

##### Transportation Insights:
* **River ferries** remain the most scenic (and often fastest) way to connect major temples.
* **BTS Skytrain** avoids traffic for north-south routes.
* **Tuk-tuks** are best for short, nostalgic rides—always negotiate price first!

##### Cultural Notes:
Today coincidentally aligned with **Visakha Bucha Day**, an important Buddhist holiday, explaining the larger-than-usual crowds at temples with devotees making merit. Many Thais were dressed in white and carrying lotus flowers and incense.

##### Currency & Costs:
* Temple entry fees: 100-500 THB (approximately $3-15 USD)
* Floating market boat tour: 500 THB/person
* Street food dishes: 40-100 THB ($1-3 USD)

---

#### Reflections on a Day of Contrasts

Bangkok masterfully balances sacred and secular, ancient and modern. Within mere kilometers, one transitions from the hushed reverence of centuries-old temples to the exuberant cacophony of markets where commerce feels like celebration.

The true magic lies in these contrasts—the golden serenity of a Buddha image beside the glittering chaos of a market stall, the scent of temple incense mingling with street food smoke, the respectful wai greeting next to enthusiastic price haggling.

This is a city that engages all senses while nourishing both body and spirit—a place where every corner holds either a shrine for contemplation or a market for connection.

---

**Proof of Journey Compilation:**
* Dated temple tickets with official stamps
* Floating market vendor receipts
* Performance program with date
* BTS Skytrain day pass dated 24/05/2026
* Currency exchange receipt showing Thai baht obtained today
"""
        },
        {
            "name": "🏛️ Rome, Italy",
            "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&q=80",
            "tag": "Empire & Art",
            "date": "18 May, 2026",
            "desc": "Step back in time to the Roman Empire. Explore the Colosseum, Vatican City, and indulge in exquisite Italian pasta and gelato.",
            "prompt": "Plan a 6 days historic tour of Rome, Italy including flights and central boutique hotels.",
            "place": "Toss a coin into the Trevi Fountain, climb the Spanish Steps, explore the Trastevere district, and wander the historic streets around Piazza Navona.",
            "culture": "Embrace the 'Slow Food' movement, enjoy espresso bars, open-air opera, Renaissance and Baroque artwork, and family gatherings over multiple-course meals.",
            "society": "A highly relational, family-focused lifestyle where life is lived out in public piazzas, rich with spirited conversations, football enthusiasm, and cultural pride.",
            "history": "Wander through the majestic Colosseum (completed in 80 AD), the Roman Forum ruins, the spectacular Pantheon dome, and the Vatican Museums (Sistine Chapel).",
            "guide_content": """
### Empire & Art: A Journey Through Rome's Timeless Grandeur  

[IMAGE: rome_colosseum_exterior.jpg | The Colosseum at sunset – where ancient echoes meet golden light]

#### Morning: The Colosseum & The Heart of Empire

My day began with the dawn light washing over the **Flavian Amphitheatre** – the Colosseum – a monument that needs no introduction. But no photograph can prepare you for its physical presence. Standing before its weathered travertine façade, I could almost hear the roar of 50,000 spectators and feel the tremors of history underfoot.

##### Inside the Arena
With a timed entry ticket (absolutely essential in 2026), I bypassed what would become a three-hour line and stepped directly onto the Arena Floor. Here, gladiators once fought for glory and survival. Our guide pointed out the **hypogeum** – the labyrinthine underground network of tunnels, cages, and lifts that revolutionized Roman spectacle.  

[IMAGE: rome_colosseum_interior.jpg | Inside the Colosseum's Arena Floor and Hypogeum]

**Proof of Visit:**  
Official Colosseum entry ticket: **"Biglietto Foro-Palatino-Colosseo"** – Ticket #RM-CC-891244 – 18/05/2026 – 09:00 Entry.

##### Palatine Hill: Where Rome Was Born
A short walk led to the **Palatine Hill**, the most prestigious of Rome's seven hills. This was the neighborhood of emperors. Wandering through the ruins of the **Domus Augustana** and the **Farnese Gardens**, I enjoyed breathtaking views over the **Roman Forum** – the political, legal, and commercial heart of the ancient world.

---

#### Afternoon: The Vatican – A Kingdom of Art & Spirit

Crossing the Tiber River into **Vatican City**, the world's smallest independent state, felt like stepping into another realm of power – not military, but spiritual and artistic.

##### The Vatican Museums: An Overwhelming Treasure Trove
The **Vatican Museums** are a marathon of beauty. I followed the recommended route, moving from the **Pio-Clementino Museum** (home to the *Laocoön and His Sons*) through the **Gallery of Maps** (a 120-meter-long cartographic masterpiece), to the stunning **Raphael Rooms**.

**Proof of Visit:**  
Vatican Museums timed entry wristband & digital audio guide receipt. Purchase ID: **VAT-2026-5-18-6842**.

##### The Sistine Chapel: Michelangelo's Divine Masterpiece
Nothing – no book, documentary, or replica – prepares you for the **Sistine Chapel**. The sheer scale of Michelangelo's frescoes is humbling. Craning my neck under the **Creation of Adam**, observing the profound terror of **The Last Judgment**, sitting in silence among hundreds of other awe-struck visitors… it was a profoundly moving experience. *(Note: Photography is strictly forbidden inside the Chapel.)*

[IMAGE: rome_vatican.png | St. Peter's Square – Bernini's embrace of columns and faith]

##### St. Peter's Basilica
Emerging into the sunlight of **St. Peter's Square**, framed by Bernini's colonnade, I entered the largest church in the world. The interior is a symphony of Renaissance and Baroque grandeur. I stood before Michelangelo's **Pietà**, its serene beauty belying the fact it was carved by a 24-year-old, and touched the bronze foot of **St. Peter's Statue**, worn smooth by centuries of devotion.

---

#### Evening: La Dolce Vita – Pasta, Gelato & Piazzas

##### A Roman Lunch: The Perfect Pasta
Exhausted from a morning of empire and an afternoon of art, I sought sustenance in Trastevere. At **Trattoria da Enzo**, I indulged in the holy trinity of Roman pasta:
1. **Cacio e Pepe** (Peccorino cheese and black pepper)
2. **Carbonara** (egg, guanciale, pecorino, pepper)
3. **Amatriciana** (tomato, guanciale, pecorino)

**Proof of Indulgence:**  
Restaurant receipt from "Trattoria da Enzo" with today's date and the glorious itemized list of pasta.

##### The Gelato Pilgrimage
No day in Rome is complete without gelato. I followed the local rule: avoid neon-colored, towering mounds. At **Gelateria del Teatro**, I savored two scoops: **Crema di Teatro** (their rich vanilla cream) and **Fichi e Miele** (fig and honey – seasonal perfection).

[IMAGE: rome_gelato.jpg | Decadent and colorful Italian gelato tubs in a Roman gelateria]

##### Piazza Navona & The Pantheon at Dusk
As evening fell, I wandered to **Piazza Navona**, built over Domitian's ancient stadium, now alive with artists, street performers, and the majesty of Bernini's **Fountain of the Four Rivers**.

A five-minute walk brought me to the **Pantheon**. Seeing this 2,000-year-old temple, with its perfect proportions and breathtaking oculus open to the sky, under the glow of evening lights, was the perfect capstone to a day of ancient wonders.

[IMAGE: rome_pantheon.jpg | The Pantheon – where Roman engineering meets divine geometry]

---

#### Practical Guide: Rome in May 2026

##### Weather & Crowds:
18 May fell on a Monday. The weather was ideal: **24°C (75°F)**, sunny with a light breeze. While still busy, May avoids the crushing heat and peak tourist numbers of July/August. The early morning and late afternoon are golden hours for photography and comfort.

##### Essential Tips for 2026:
1. **Book EVERYTHING in advance:** Colosseum, Vatican Museums, and even major churches now require timed tickets booked online weeks ahead.
2. **Roma Pass vs. Individual Tickets:** For this intensive two-day itinerary, individual pre-booked tickets were more cost-effective than the pass.
3. **Dress Code Matters:** Shoulders and knees must be covered for the Vatican Museums and all major churches. Carry a light scarf.
4. **Transport:** Rome's historic center is best explored on foot. The Metro (Line B for the Colosseum) is efficient for longer distances. I used a **72-hour ATAC public transport ticket**.

##### Costs & Currency (May 2026):
* Colosseum, Forum & Palatine Combo Ticket: €24 (with booking fee)
* Vatican Museums & Sistine Chapel: €21 (basic entry)
* Typical Roman Lunch: €25-40 per person
* Gelato: €3-5 for two scoops
* Public Transport 72-hr Ticket: €18

##### Cultural Note:
Today was surprisingly calm. A local guide mentioned that many Romans take short *ponti* (bridge holidays) in May, thinning the usual crowds slightly – a fortunate coincidence for my visit.

---

#### Final Reflections: The Eternal Layers

Rome isn't a city that lives in the past; it's a city built in **continuous layers**. The Baroque rests on the Renaissance, which was built upon the Medieval, which repurposed the Ancient. You see it everywhere: a column from a pagan temple embedded in a church wall, a modern café in a Renaissance palazzo, the Metro rushing beneath ancient aqueducts.

It's a city where the grandeur of empire and the sublime heights of human art exist not as distant history, but as the very fabric of daily life, best appreciated with a mouth full of perfect pasta and the promise of gelato just around the next millennia-old corner.

***Proxima Stopping:** Tomorrow, I delve deeper into the Baroque with a focus on Bernini and Borromini, before taking a day trip to the rolling hills of Tuscany.*

---

**Compiled Proof of Journey – 18 May 2026:**
* Colosseum/Forum/Palatine ticket with barcode and timestamp.
* Vatican Museums wristband & audio guide purchase confirmation email.
* Digital transport ticket validation history screenshot.
* Restaurant receipt from Trattoria da Enzo.
* Gelateria del Teatro loyalty stamp card (first stamp!).
"""
        },
        {
            "name": "🏙️ Dubai, UAE",
            "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400&q=80",
            "tag": "Modern Luxury",
            "date": "12 May, 2026",
            "desc": "Witness futuristic architectural marvels, luxury shopping, desert safaris, and the world's tallest building, Burj Khalifa.",
            "prompt": "Plan a luxury weekend trip to Dubai for 3 days including flight search and hotel stays.",
            "place": "Relax on Jumeirah Beach, visit the artificial Palm Jumeirah island, shop in the massive Dubai Mall, and witness the Dubai Marina skyline.",
            "culture": "Experience Arabian hospitality, traditional camel racing, falconry, gold and spice souk bargaining, and Bedouin desert camps.",
            "society": "A highly cosmopolitan city consisting largely of expatriates, fast-moving and success-oriented, balanced with traditional Emirati Islamic values.",
            "history": "Discover the Al Fahidi Historical Neighborhood (dating back to the 1890s), the Dubai Museum, and cross the Dubai Creek in a traditional Abra boat.",
            "guide_content": """
### Desert Dreams & Sky-High Ambition: A Journey Through Dubai  
**3 June 2026 | 🏙️ Dubai, United Arab Emirates**

[IMAGE: dubai_marina_day.jpg | Dubai Marina—where water meets impossible architecture. Captured during the daylight hours.]

---

#### Morning: Touching the Sky at Burj Khalifa

My day began with sunrise at the **Burj Khalifa**, the world’s tallest building at 828 meters. I booked the **"At the Top SKY"** experience (levels 148, 125, and 124) for 8:00 AM—beating both the crowds and the heat. The ascent in the double-decker elevator (10 meters per second!) felt like entering a silent sci-fi film.

**From Level 148:** The observation deck is aptly named "The Highest Outdoor Observatory in the World." Looking down, the city appeared as a meticulous scale model: the braided highways, the palm-shaped islands, and the vast desert meeting the turquoise Persian Gulf. The silence at this height was profound.

**Proof of Visit:** Digital ticket confirmation with QR code (#BKDXB2026-48921) and a commemorative stamped certificate from the Burj Khalifa Sky Lounge.

---

**Inside Tip:** Book the *first morning slot*. Not only is it cooler and less crowded, but the morning light is perfect for photography, and you can watch the city awaken below.

---

#### Afternoon Part 1: Futuristic Marvels & Luxury Aisles

##### The Dubai Mall & The Dubai Fountain
Descending from the clouds, I entered the **Dubai Mall**—not just a shopping center, but a city within a city. Beyond luxury boutiques, it houses an **aquarium tunnel** with sharks gliding overhead, an Olympic-sized ice rink, and a full-sized dinosaur skeleton.

[IMAGE: dubai_aquarium.png | Giant rays and sharks inside the massive Dubai Aquarium tunnel]

At 1:00 PM, I watched the **Dubai Fountain** perform from the waterfront promenade. Set on the 30-acre Burj Khalifa Lake, its jets shoot water 500 feet in the air, choreographed to everything from classical Arabic music to modern pop anthems.

**Proof of Experience:** Receipt from "Social House" restaurant in the Dubai Mall with a fountain-view table noted, dated 3/6/2026.

##### Architectural Safari: A Drive Through Innovation
I hired a driver for a two-hour "**Architecture Tour**." Highlights included:
* **The Museum of the Future:** Its torus shape, covered in Arabic calligraphy, appears to float impossibly above the ground.
* **Cayan Tower:** A stunning 75-story helical twist.
* **Burj Al Arab:** The iconic "sail-shaped" hotel on its own artificial island—a symbol of 90s Dubai ambition.

[IMAGE: dubai_museum.jpg | The Museum of the Future showing beautiful Arabic calligraphy]

---

#### Afternoon Part 2: The Desert Beckons

By 3:30 PM, I was in a 4x4 Land Cruiser, heading into the **Margham Desert**. The transformation from hyper-urban sprawl to endless, serene dunes within 45 minutes is a quintessential Dubai experience.

##### Red Dunes Safari
Our expert driver navigated the **"Red Dunes"** with thrilling dips and climbs—a rollercoaster on sand. We stopped at the crest of a towering dune to watch the sun begin its descent, painting the sands in shades of amber and gold.

**Proof of Adventure:** Safari wristband from **"Platinum Heritage"** with tour code #DBSAF0626-88 and GPS-tagged photo at the dunes.

[IMAGE: dubai_desert.jpg | Sunset over the red dunes of the Dubai desert with quad biking]

##### Arabian Nights Camp
As dusk fell, we arrived at a traditional Bedouin-style camp. The evening included:
* **Camel Riding** along the dune line.
* **Henna painting** and trying on traditional Kandura and Abaya.
* A lavish **BBQ buffet** under the stars, with live oud music and a mesmerizing **tanoura dance** performance.

---

#### Evening: Returning to the Galaxy of Lights

Returning to the city by 9:30 PM felt like re-entering a living circuit board. I ended the day at the **"Atmosphere"** lounge on the 122nd floor of the Burj Khalifa. Sipping a pomegranate mocktail while looking *across* at the flashing tips of other skyscrapers was a surreal bookend to a day that spanned from desert sands to cloud-piercing towers.

[IMAGE: dubai_marina_night.jpg | Downtown Dubai's glowing skyscraper skyline at night]

---

#### 🗺️ Dubai Travel Guide: June 2026 Edition

##### **Weather & What to Wear:**
* **Temperature:** High of 42°C (108°F) in the desert, a "cool" 38°C (100°F) in the city.
* **Advice:** Light, breathable fabrics are essential. A pashmina or jacket is needed for heavily air-conditioned malls and the Burj Khalifa observatory.
* **Sun Protection:** Non-negotiable. SPF 50+, sunglasses, and a hat.

##### **Key Logistics:**
1. **Transport:** The Dubai Metro (Red Line) is efficient and clean. For desert safaris and specific tours, pre-booked private transport is best. **Careem** (local ride-hailing app) is widely used.
2. **Bookings:** *Everything* requires advance booking—especially Burj Khalifa, desert safaris, and popular restaurants.
3. **Cultural Sensitivity:** Dubai is cosmopolitan but respectful. Modest dress is appreciated in public areas (covering shoulders and knees). Public displays of affection are discouraged.

##### **Cost Breakdown (Approx.):**
* Burj Khalifa "At the Top SKY": 799 AED (~$218 USD)
* Premium Desert Safari (Heritage Style): 650 AED (~$177 USD)
* Lunch at Dubai Mall (mid-range): 120 AED (~$33 USD)
* Dubai Metro Day Pass: 22 AED (~$6 USD)

**Proof of Expenditure:** Screenshot of Wise card spending summary for 3 June, showing AED transactions.

---

#### Final Reflection: The Dialogue Between Dunes and Steel

Dubai is a city of breathtaking **contrasts**. It’s where the eternal silence of the desert meets the digital hum of ambition. Within a single day, you can trace the arc of a civilization—from the timeless, nomadic traditions of the desert to a vision of the future carved in glass and steel.

It challenges the very idea of what's possible, asking not "why?" but **"why not?"** Whether you're standing in a Bedouin camp under a blanket of stars or atop the world's tallest building, you are participating in a grand, ongoing experiment—one built on sand, dreams, and relentless vision.

---

**Trip Documentation – 3 June 2026**
All proofs are stored digitally in my travel archive:
1. **Burj Khalifa:** Digital ticket & Sky Lounge certificate.
2. **Desert Safari:** Wristband, booking confirmation, and geotagged photos.
3. **Transport:** Nol Card travel history and Careem ride receipts.
4. **Dining:** Digital receipts from Social House and Atmosphere Lounge.
"""
        },
        {
            "name": "🏰 Rajasthan, India",
            "img": "https://media.istockphoto.com/id/805563154/photo/mehrangharh-fort-and-jaswant-thada-mausoleum-in-jodhpur-rajasthan-india.jpg?s=612x612&w=0&k=20&c=5r9UxPkz9mIkfAIFPLyTwqBQyqSO7mcAdQtcqGHOboA=",
            "tag": "Royal Heritage",
            "date": "29 May, 2026",
            "desc": "The land of kings. Explore majestic forts like Mehrangarh, golden sand deserts in Jaisalmer, and royal palaces in Udaipur.",
            "prompt": "Plan a royal 7 days Rajasthan tour covering Jaipur, Jodhpur, and Udaipur under 1.5 lakhs.",
            "place": "Explore Jaipur's Pink City, Udaipur's Lake Pichola palaces, Jodhpur's blue streets, and the golden sand dunes of the Thar Desert in Jaisalmer.",
            "culture": "Enjoy colorful traditional wear (Turbans and Ghagras), folk dances like Ghoomar, puppet shows, Rajasthani folk music, and spicy Lal Maas or Dal Baati Churma.",
            "society": "A proud, hospitality-driven society where Rajput traditions of honor are deeply cherished, celebrating vibrant festivals (like Pushkar Camel Fair) with community zeal.",
            "history": "Wander through Mehrangarh Fort in Jodhpur, Amer Fort in Jaipur, the sprawling City Palace in Udaipur, and the living Jaisalmer Fort.",
            "guide_content": """
### Land of Kings: A Regal Journey Through Rajasthan
**21-28 November 2026 | 🏰 Rajasthan, India**

[IMAGE: rajasthan_fort.jpg | The colossal Mehrangarh Fort rising majestically above the indigo-blue city of Jodhpur]

---

#### Chapter 1: Jodhpur - The Blue City & Mehrangarh's Majesty

##### Day 1: Arrival into Azure
I landed in Jodhpur to be greeted by a sea of indigo-blue houses cascading down the hillside—the origin of its nickname "Blue City." The color, traditionally used by Brahmins, now keeps homes cool and repels insects.

##### Day 2: Fortress of the Sun
Spent the morning exploring **Mehrangarh Fort**, one of India's largest and most magnificent structures. Perched 125 meters above the city, its massive gates bear historical battle scars. The museum inside contains an extraordinary collection of palanquins, royal cradles, and armor.

**Proof of Visit:** Mehrangarh Fort Museum entrance ticket #MGF-2026-1122 stamped at the main gate on 22/11/2026.

---

#### Chapter 2: Jaisalmer - The Golden City & Thar Desert Dunes

[IMAGE: rajasthan_camels.png | A camel caravan marching along the undulating golden dunes of the Thar Desert at sunset]

##### Day 3: The Living Fort
Traveled westward into the heart of the Thar Desert to **Jaisalmer**. The city's golden sandstone architecture makes it glow like a mirage. The **Jaisalmer Fort** is a rare "living fort," where nearly a quarter of the city's population still resides inside the medieval ramparts.

##### Day 4: Camel Caravan at Sunset
Rode camels into the undulating dunes of **Sam Sand Dunes** as the sun sank below the horizon, painting the sky in deep shades of crimson and orange. Slept under a canopy of stars in a desert safari camp, listening to traditional Rajasthani folk music.

**Proof of Visit:** Desert safari booking confirmation from Thar Nomad Safaris dated 24/11/2026.

---

#### Chapter 3: Udaipur - City of Lakes & Lake Palace

[IMAGE: rajasthan_lake_palace.png | The breathtaking white marble Lake Palace floating on Lake Pichola in Udaipur]

##### Day 5: Venice of the East
Arrived in **Udaipur**, the romantic city of lakes and white marble palaces. Took an afternoon boat cruise on Lake Pichola, gliding past the majestic **Lake Palace** which appears to float effortlessly on the water.

##### Day 6: The Royal City Palace
Explored the sprawling **City Palace** complex, a fusion of Rajasthani and Mughal architectural styles. The intricate peacock mosaics in the Mor Chowk and the panoramic views of the lake from the upper balconies were spectacular.

**Proof of Visit:** Lake Pichola boat cruise boarding pass dated 26/11/2026.

---

#### Chapter 4: Culture, Cuisine & Heritage

##### Folk Art & Performance
Witnessed a magical evening of folk performances at **Bagore-ki-Haveli**, featuring puppet shows and the famous **Bhavai dance**, where a female dancer balances a stack of nine brass pots on her head while dancing on broken glass.

[IMAGE: rajasthan_dance.jpg | Traditional Rajasthani Bhavai folk dancer balancing brass pots on her head]

##### The Royal Feast
No journey to Rajasthan is complete without tasting a traditional **Rajasthani Thali**. Indulged in a rich feast featuring *Dal Baati Churma*, *Ker Sangri* (desert beans and berries), *Gatte ki Sabji*, and piping hot *churma* drizzled with pure ghee.

[IMAGE: rajasthan_thali.png | A lavish Rajasthani Thali featuring Dal Baati Churma, Ker Sangri, and local delicacies]

**Proof of Indulgence:** Dinner receipt from Traditional Rajasthani Dining Hall in Udaipur dated 27/11/2026.

---

#### 🗺️ Rajasthan Travel Guide: November 2026 Edition

##### **Weather & Logistics:**
* **Temperature:** A pleasant 15°C to 28°C (59°F to 82°F) in winter, making November the absolute best month to visit.
* **Advice:** Pack warm layers for chilly desert nights, but light clothing for sunny afternoons.
* **Transport:** Hiring a private car and driver is the most reliable way to navigate the long distances between Jodhpur, Jaisalmer, and Udaipur.

##### **Cost Breakdown (Approx.):**
* Mehrangarh Fort Entry: 600 INR (~$7 USD)
* Luxury Thar Desert Camp & Safari: 4,500 INR/night (~$54 USD)
* Udaipur Boat Cruise: 800 INR (~$10 USD)
* Traditional Thali Dinner: 600 INR (~$7 USD)
"""
        },
        {
            "name": "🌴 Kerala, India",
            "img": "https://images.unsplash.com/photo-1593693411515-c20261bcad6e?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8a2VyYWxhJTIwdG91cmlzbXxlbnwwfHwwfHx8MA==",
            "tag": "Nature & Wellness",
            "date": "27 May, 2026",
            "desc": "Unwind in God's Own Country. Cruising tranquil backwaters in a houseboat, spice plantations in Munnar, and pristine beaches.",
            "prompt": "Plan a relaxing 5 days Kerala trip covering Munnar tea gardens and Alleppey houseboats.",
            "place": "Cruise the emerald backwaters of Alleppey, trek the misty tea plantations of Munnar, explore Wayanad wildlife sanctuaries, and relax on Kovalam beach.",
            "culture": "Witness the dramatic Kathakali dance-drama, experience authentic Ayurvedic healing therapies, learn Kalaripayattu martial arts, and taste banana-leaf Sadya meals.",
            "society": "A highly educated, progressive society with the highest literacy rate in India, deeply connected to farming and fishing, living in close harmony with the environment.",
            "history": "Explore Mattancherry Palace (built by the Portuguese in 1555), Bekal Fort overlooking the Arabian Sea, and the ancient Padmanabhaswamy Temple.",
            "guide_content": """
### Discovering the Magic of Kerala: God's Own Country
**27 May, 2026 | 🌴 Kerala, India**

[IMAGE: kerala_backwaters.jpg | Traditional kettuvallam houseboat cruising along the calm emerald backwaters of Alleppey]

---

#### 1. Introduction: Why Kerala is Truly Enchanting
Kerala, on India's tropical Malabar Coast, has enchanted visitors for centuries with its unique blend of nature, culture, and wellness.

> **The Proof:** National Geographic named Kerala one of the **"Ten Paradises of the World"** and it consistently ranks as one of India's top states for high social indicators and human development.

---

#### 2. The Emerald Embrace: Kerala's Natural Wonders

##### 2.1 Alleppey & The Backwaters: A Liquid Highway
* **Experience:** Cruise the emerald backwaters in a traditional *kettuvallam* (houseboat), try village canoe tours, and stay in waterfront homestays.
* **The Proof:** The **Kuttanad region** within the backwaters is known as "The Rice Bowl of Kerala" and is one of the very few places in the world where **farming is carried out below sea level**.

##### 2.2 Munnar: Rolling Hills of Tea & Spice

[IMAGE: kerala_tea_gardens.jpg | Rolling green tea estates of Munnar covered in misty morning clouds]

* **Experience:** Trek through tea estates, visit the tea museum, and explore spice plantations (cardamom, pepper, vanilla).
* **The Proof:** Munnar's **Kolukkumalai Tea Estate** is one of the **highest elevation organic tea estates in the world**.

##### 2.3 The Wild Heart: Wayanad's Sanctuaries
* **Experience:** Wildlife safari in **Wayanad Wildlife Sanctuary** (part of the Nilgiri Biosphere Reserve), and explore Edakkal Caves with ancient petroglyphs.
* **The Proof:** It serves as a critical **elephant corridor** and habitat for the endangered **Malabar giant squirrel**.

##### 2.4 Coastal Serenity: The Beaches of Kovalam & Varkala

[IMAGE: kerala_beach.jpg | Crescent-shaped Kovalam beach and sandy coastline in Kerala]

* **Experience:** Relax on Kovalam's crescent beach, climb the lighthouse, and view Varkala's cliffs.
* **The Proof:** **Kovalam** was among the first beaches in India to be developed as an international **tourist destination back in the 1930s**.

---

#### 3. A Living Culture: Art, Healing, and Flavor

##### 3.1 The Dramatic Arts: Kathakali & Kalaripayattu

[IMAGE: kerala_kathakali.jpg | A close-up of a Kathakali dancer performing with elaborate makeup and dress]

* **Experience:** Watch a Kathakali performance focusing on the elaborate makeup (*chutti*) and hand gestures (*mudras*), or witness a Kalaripayattu martial arts show.
* **The Proof:** **Kalaripayattu** is often cited as **one of the oldest surviving martial arts in the world**, which influenced kung fu and fight styles across Asia.

##### 3.2 The Science of Life: Authentic Ayurveda
* **Experience:** Unwind with wellness treatments at a Government-certified Ayurvedic centre, experiencing therapies like *Abhyangam* and *Pirozhichil*.
* **The Proof:** Kerala is the **global capital for authentic Ayurvedic treatment**, with an unbroken **1,000+ year** history of practice.

##### 3.3 A Feast on a Leaf: Sadya & Seafood
* **Experience:** Eat a traditional vegetarian **Sadya** served on a fresh banana leaf, and taste karimeen (pearl spot) pollichathu.
* **The Proof:** The **Sadya**, with its **24-28 dishes served in a specific order**, is listed as a culinary wonder and is central to Kerala's major festivals.

---

#### 4. A Progressive Tapestry: Society & Lifestyle
* **Discussion:** Kerala boasts the **highest literacy rate (over 96%)** in India, with high life expectancy and progressive gender parity.
* **The Proof:** UNESCO has praised Kerala's **"Total Literacy Campaign"** as a model for community-driven education. The state is also a pioneer in sustainable, community-run responsible tourism.

---

#### 5. Whispers of the Past: Historical Heritage

[IMAGE: kerala_heritage.jpg | A historic montage showing Mattancherry Palace, Bekal Fort, and Kerala's heritage sites]

##### 5.1 Mattancherry Palace (Dutch Palace)
* **Explore:** The stunning Ramayana murals and Portuguese-influenced architecture in Kochi.
* **The Proof:** Built by the **Portuguese in 1555** and gifted to the Raja of Kochi, its murals are among India's finest examples of traditional painting.

##### 5.2 Bekal Fort: Guardian of the Coast
* **Explore:** The massive keyhole-shaped sea fort with sweeping ocean views.
* **The Proof:** The largest fort in Kerala, its origins date back to the **17th century** under the Keladi Nayakas, later held by Hyder Ali and Tipu Sultan.

##### 5.3 Sree Padmanabhaswamy Temple
* **Explore:** The magnificent Dravidian architecture in Thiruvananthapuram.
* **The Proof:** One of the **108 Divya Desams** (holy abodes) of Vishnu, its vault treasures make it one of the wealthiest institutions in human history.

---

#### 🗺️ Kerala Travel Guide: May 2026 Edition

##### **Best Time to Visit:**
* **October to March:** Best for general sightseeing and pleasant weather.
* **June to September (Monsoon):** Best time for Ayurvedic rejuvenation and wellness therapies.

##### **Travel Tips:**
1. **Dress Codes:** Dress modestly (covered shoulders and knees) when visiting temples.
2. **Ayurveda:** Choose only Government-approved centers (holding Green Leaf or Olive Leaf certifications).
3. **Houseboats:** Book houseboats through licensed operators in Alleppey.
"""
        },
        {
            "name": "🏔️ Himachal Pradesh, India",
            "img": "https://media.istockphoto.com/id/1371289822/photo/himalayan-village-town-of-kalpa-with-kailash-mountain-snow-peaks-at-himachal-pradesh-india.jpg?s=612x612&w=0&k=20&c=ibz1ktqV34YlHk0FeSyBcoykG2IVViXNUxU2NLCGsg8=",
            "tag": "Himalayan Adventure",
            "date": "23 May, 2026",
            "desc": "Adventure in the Himalayas. Revel in snow-capped peaks in Kalpa, paragliding in Solang Valley, and scenic mountain towns.",
            "prompt": "Create an adventure itinerary for 6 days in Himachal Pradesh covering Manali and Solang Valley.",
            "place": "Take in the Kinnaur Kailash views in Kalpa, ski or paraglide in Solang Valley, hike to Jogini Falls, and explore Dharamshala's mountain trails.",
            "culture": "Discover Pahadi wood-and-stone architecture, hand-woven Kullu shawls, local apple orchard harvests, Himachali folk dances (Nati), and Tibetan Buddhist traditions.",
            "society": "A peaceful, warm mountain community living in close-knit villages, deeply spiritual, celebrating major local temple deities and mountain festivals.",
            "history": "Visit the majestic Kangra Fort (dating back to the ancient Trigarta Kingdom), Key Monastery in Spiti Valley, and the historic Viceregal Lodge in Shimla.",
            "guide_content": """
### Discovering the Magic of Himachal Pradesh
**23 May, 2026 | 🏔️ Himachal Pradesh, India**

[IMAGE: himachal_flags.jpg | A wide-angle shot of the Dhauladhar Range towering above McLeod Ganj, with colorful Tibetan prayer flags in the foreground]

---

#### 1. Introduction: Land of Snow, Spires, and Soul
Where Tibetan prayer flags flutter beside snow-laden deodars—welcome to the adventure capital of India.

> **The Proof:** Himachal has been ranked **#1 in India for sustainable tourism** by the Ministry of Tourism’s Responsible Tourism Initiative.

---

#### 2. The Adventure Playground

##### 2.1 Solang Valley: Paragliding Over Paradise
* **Activities:** Paragliding, skiing, zorbing, ATV rides, and ropeway adventures.
* **The Proof:** Home to the **Atal Bihari Vajpayee Institute of Mountaineering and Allied Sports (ABVIMAS)**, a premier mountaineering institute.

[IMAGE: himachal_paragliding.png | Paragliding in the clear blue skies over the breathtaking Solang Valley]

##### 2.2 Hiking the Himalayan Trails
* **Easy Trek:** Jogini Waterfall Trek from Old Manali—a peaceful 2-hour hike.
* **Moderate/Advanced Trek:** Hampta Pass & Chandratal Lake Trek, or the legendary Pin Parvati Pass.
* **The Proof:** The **Great Himalayan National Park (GHNP)** is a UNESCO World Heritage Site recognized for its stunning biodiversity and trekking corridors.

##### 2.3 Kalpa & Kinnaur: Where Nature Meets the Divine
* **Experience:** Stand before the Kinnaur Kailash peak at sunrise, and spot the mysterious Svayambhu (self-formed) Shiva Lingam on its face.
* **The Proof:** The **Kinner Kailash Parikrama** is one of the most challenging high-altitude pilgrimages in India, undertaken by devout Hindus and Buddhists alike.

---

#### 3. Spiritual Sanctuaries & Historic Fortresses

##### 3.1 Kangra Fort: Guardian of the Valley
* **History:** Built by the Rajput rulers of the Trigarta Kingdom, it’s the largest fort in the Himalayas.
* **The Proof:** It’s mentioned in **Alexander the Great’s war records**, and its stone construction survived the devastating 1905 Kangra earthquake.

[IMAGE: himachal_kangra_fort.png | The majestic and historic ruins of Kangra Fort overlooking the lush Kangra Valley]

##### 3.2 Key Monastery: The Citadel of Buddhism in Spiti
* **Experience:** Explore this 1,000-year-old Tibetan Buddhist monastery, housing ancient manuscripts, thangkas, and a school for young monks.
* **The Proof:** It is the largest and most important monastery in the Spiti Valley, and a key training center for Lamas.

[IMAGE: himachal_key_monastery.jpg | Key Monastery perched on a hill, with the stark, barren mountains of Spiti Valley behind it]

##### 3.3 Viceregal Lodge, Shimla: Echoes of the Raj
* **Experience:** Walk through the opulent rooms where the Indian Independence Act of 1947 was drafted.
* **The Proof:** The building is made entirely of **grey stone without the use of wood**, a unique architectural feat to prevent fire.

---

#### 4. Living Traditions: Culture, Craft, and Cuisine

##### 4.1 Architecture & Handicrafts
* **Kath-Kuni Architecture:** See the earthquake-resistant wooden and stone houses in Naggar and Malana.
* **Kullu Shawls:** Handwoven using unique patterns, each shawl tells a story.
* **The Proof:** Kullu Shawls hold a **Geographical Indication (GI) tag**, and the Kath-Kuni technique was studied by Japanese engineers for its seismic resilience after the Kobe earthquake.

##### 4.2 Festivals & Faith
* **Kullu Dussehra:** A seven-day festival where 300+ local deities are brought in palanquins to celebrate.
* **Losar (Tibetan New Year):** Witness masked Cham dances and ancient rituals in McLeod Ganj.
* **The Proof:** Kullu Dussehra was declared an **International Festival** by the state government in 2022, drawing global attention.

##### 4.3 A Taste of the Mountains
* **Must-Try Dishes:** Siddu (steamed bread), Madra (yogurt-based curry), Babru (Himachali kachori), and locally brewed apple cider.
* **The Proof:** Himachal Pradesh is India’s **#2 apple producer**, and the traditional Dham feast is prepared only by a special clan of Brahmin cooks (Botis).

[IMAGE: himachal_apples.jpg | Local apple orchard worker harvesting fresh, red Himachali apples]

---

#### 5. The Pahadi Life: Society & Lifestyle
* **The Warmth of the Hills:** Experience the tight-knit community in villages where life revolves around apple harvesting, shepherd migrations (Gaddis), and temple festivals.
* **The Proof:** Himachal Pradesh boasts the **second-highest literacy rate** in India and has been ranked as **India’s most peaceful state** by the National Crime Records Bureau.

---

#### 6. Traveler's Toolkit

##### **Best Time to Visit:**
* ☀️ **Summer (Mar–Jun):** Ideal for adventure, trekking, and sightseeing.
* ❄️ **Winter (Dec–Feb):** Perfect for snow in Manali, Solang, and Shimla.
* 🌧️ **Monsoon (Jul–Sept):** Lush green valleys, but landslides can occur.

##### **Getting Around:**
HRTC buses, self-drive cars, or private cabs (careful driving in mountain terrain is advised).

##### **Permits:**
Inner Line Permit (ILP) is required for foreign nationals traveling to Kinnaur, Spiti, and other tribal border areas.

---

#### 7. Suggested Itineraries
* **7-Day Adventure Trail:** Delhi $\rightarrow$ Shimla $\rightarrow$ Manali (Solang Valley) $\rightarrow$ Rohtang Pass/Atal Tunnel $\rightarrow$ Key Monastery (Spiti) $\rightarrow$ Kalpa $\rightarrow$ Back.
* **5-Day Spiritual & Scenic Loop:** Delhi $\rightarrow$ Dharamshala (McLeod Ganj) $\rightarrow$ Kangra Fort $\rightarrow$ Bir (Paragliding) $\rightarrow$ Jogindernagar $\rightarrow$ Back.
"""
        },
        {
            "name": "🏖️ Goa, India",
            "img": "https://media.gettyimages.com/id/521660572/photo/beach-in-goa-india.jpg?s=612x612&w=gi&k=20&c=WyNWDp1CxV5dhBOOt3LiQ61jZAKDlAAkR1nGI4rZ4hE=",
            "tag": "Coastal Life",
            "date": "19 May, 2026",
            "desc": "India's favorite beach destination. Relax on sandy beaches, enjoy water sports, historic churches, and vibrant nightlife.",
            "prompt": "Plan a 4 days Goa weekend beach vacation with resort stays and flight options.",
            "place": "Sunbathe on Calangute and Baga beaches, explore the Latin Quarter (Fontainhas) of Panaji, trek to Dudhsagar Falls, and visit spice farms.",
            "culture": "Experience a unique blend of Portuguese and Indian heritage, eat delicious Goan fish curry rice, enjoy feni drinks, and join colorful beach festivals.",
            "society": "A relaxed, laid-back coastal lifestyle locally referred to as 'Susegad,' highly welcoming to national and international travelers, artistic and peace-loving.",
            "history": "Visit the world-heritage Basilica of Bom Jesus (holding the remains of St. Francis Xavier), the 17th-century Fort Aguada, and Se Cathedral.",
            "guide_content": """
### Discovering the Magic of Goa: More Than Just Beaches & Nightlife

[IMAGE: goa_beach.jpg | A panoramic golden-hour view of a beautiful Goan beach with palm trees and a relaxed coastal atmosphere]

#### 1. Introduction: Beyond the Sun, Sand, and Sea
Introducing Goa not just as a destination, but as a feeling—the embodiment of 'Susegad'.

> **The Proof:** UNESCO recognition of Old Goa's churches and convents as a World Heritage Site, highlighting its global historical significance.

---

#### 2. The Coastal Canvas: Beaches for Every Mood

##### 2.1 The Lively North: Calangute, Baga & Anjuna
* **Vibe:** The epicenter of water sports, shacks, and vibrant nightlife.
* **The Proof:** Calangute is famously known as the "Queen of Beaches," and was one of the first beaches to be developed for tourism in the 1960s.

##### 2.2 The Serene South: Palolem, Agonda & Butterfly Beach
* **Vibe:** Pristine, crescent-shaped bays, quieter shacks, and a more bohemian atmosphere.
* **The Proof:** Palolem Beach is consistently ranked among Asia's most beautiful beaches by travel publications like *Condé Nast Traveller*.

##### 2.3 Beyond the Shore: Dudhsagar Falls & Spice Plantations
* **Experience:** Trek or take a jeep safari to the majestic Dudhsagar Falls and tour a traditional organic spice farm.
* **The Proof:** Dudhsagar Falls is one of India's tallest waterfalls at 310 meters (1017 feet). Goa's spice farms continue a centuries-old trade started during the Portuguese era.

[IMAGE: goa_waterfall.jpg | The powerful, milky cascade of Dudhsagar Falls in full flow during the monsoon, surrounded by dense green forest]

---

#### 3. A Living Heritage: Where Portugal Meets India

##### 3.1 The Sacred Heart: Basilica of Bom Jesus & Se Cathedral
* **Explore:** Marvel at the Baroque architecture of the Basilica, home to the sacred relics of St. Francis Xavier, and the grandeur of Se Cathedral.
* **The Proof:** The Basilica of Bom Jesus is a UNESCO World Heritage Site and contains the incorruptible body of St. Francis Xavier, a significant Catholic pilgrimage site.

[IMAGE: goa_church.jpg | The magnificent Basilica of Bom Jesus in Old Goa, showcasing Baroque style and laterite stone architecture]

##### 3.2 The Strategic Guardian: Fort Aguada
* **Explore:** Walk the ramparts of this 17th-century Portuguese fort with a panoramic view of the Arabian Sea.
* **The Proof:** Built in 1612, it was strategically crucial for Portuguese defense. Its freshwater spring provided water to ships, giving it its name ('água' means water in Portuguese).

##### 3.3 The Latin Soul: Fontainhas, Panjim
* **Experience:** Stroll through the winding, colorful streets of Asia's only Latin Quarter.
* **The Proof:** The neighborhood's distinct Portuguese-style architecture, street names, and use of Indo-Portuguese language preserve a unique cultural legacy recognized by UNESCO.

---

#### 4. The Art of 'Susegad': Culture, Cuisine & Celebration

##### 4.1 The Goan Way of Life: Understanding 'Susegad'
* **Experience:** It’s a philosophy of contentment, relaxation, and taking life as it comes.
* **The Proof:** The term comes from the Portuguese 'sossegado' (quiet). This mindset is reflected in Goa's low crime rate and its reputation as India's most laid-back state.

##### 4.2 A Symphony of Flavors: Goan Cuisine
* **Must-Try Dishes:** Fish Curry Rice (the staple), Pork Vindaloo, Chicken Xacuti, Bebinca (layered dessert), and the fiery local spirit Feni (made from cashew or coconut).
* **The Proof:** Goan cuisine is recognized as a unique fusion food category in India. Feni was granted a Geographical Indication (GI) tag in 2009, protecting its authenticity.

[IMAGE: goa_food.jpg | An inviting, top-down shot of a classic Goan fish thali on a banana leaf, featuring curry, rice, fried fish, and sol kadhi]

##### 4.3 Color, Rhythm & Celebration
* **Festivals:** Experience the fervor of Carnival (pre-Lenten festival), the spiritual grandeur of Feast of St. Francis Xavier, and the harvest joy of Shigmo.
* **The Proof:** Goa Carnival is the oldest in Asia, introduced by the Portuguese over 500 years ago and now a major tourist draw.

[IMAGE: goa_carnival.jpg | A dynamic, colorful photo of a Carnival parade float with elaborately dressed dancers on the streets of Panjim]

---

#### 5. Society & Lifestyle: The Heart of Coastal Harmony
* **A Tapestry of Communities:** A look at the harmonious blend of Goan Hindus, Catholics, and other communities, and their shared love for music, art, and football.
* **The Proof:** Goa is often cited as having the highest per capita income in India and one of the highest literacy rates, contributing to its progressive and welcoming society.

---

#### 6. Practical Traveler's Guide to Goa

##### **Best Time to Visit:**
* **Nov–Feb (Peak Season):** Perfect weather, clear blue skies.
* **Mar–May (Summer):** Warm, great for deals and water sports.
* **Jun–Sept (Monsoon):** Lush green scenery, waterfalls in full glory, less crowded.

##### **Getting Around:**
Rent a scooter/bike, use app-based taxi services, or hire a local taxi for sightseeing.

##### **Stay Like a Local:**
Choose beachfront shacks (South Goa), hostels (Anjuna/Vagator), heritage homestays (Fontainhas), or luxury resorts.

##### **Respectful Travel Tips:**
* Dress modestly when visiting churches and temples.
* Support local businesses and artisans.

---

#### 7. Beyond the Obvious: Unique Goa Itineraries

##### **The Heritage Trail:**
Panjim (Fontainhas) → Old Goa → Divar Island → Chandor (heritage mansions).

##### **The Nature & Adventure Trail:**
Dudhsagar Falls → Bhagwan Mahavir Wildlife Sanctuary → Netravali Bubble Lake → Spice Farm visit.

##### **The Ultimate Relaxation Loop:**
South Goa beaches (Agonda, Palolem) → Cabo de Rama Fort → Silent Noise headphone party.

---

#### 8. Conclusion: Let Goa Rewrite Your Definition of a Holiday
A final reflection on how Goa offers a unique cocktail of relaxation, adventure, history, and flavor.

> **Call to Action:** Pack your flip-flops, bring your appetite, and get ready to embrace the 'Susegad' life. Your dose of coastal magic awaits.
"""
        },
        {
            "name": "❄️ Jammu & Kashmir, India",
            "img": "https://thumbs.dreamstime.com/b/beautiful-mountain-view-sonamarg-mountain-jammu-kashmir-state-india-panoramic-beautiful-mountain-view-sonamarg-169815133.jpg",
            "tag": "Alpine Paradise",
            "date": "16 May, 2026",
            "desc": "Heaven on Earth. Enjoy shikara rides on Dal Lake in Srinagar, skiing in Gulmarg, and breathtaking views in Sonamarg.",
            "prompt": "Plan a complete 6 days Kashmir trip covering Srinagar houseboats and Gulmarg snow resorts.",
            "place": "Ride a traditional Shikara on Dal Lake in Srinagar, ski in Gulmarg, and hike the snow-melt rivers of Sonamarg and Pahalgam.",
            "culture": "Sip hot saffron Kahwa tea, listen to Sufiana music, shop for hand-knotted silk carpets and Pashmina shawls, and stay in floating wooden houseboats.",
            "society": "A resilient, incredibly warm and hospitable society where guests are treated like family, mostly agrarian, nomadic shepherds, and traditional hand-craftsmen.",
            "history": "Stroll the terraced Mughal Gardens (Shalimar and Nishat Bagh built by Emperor Jahangir), Hari Parbat Fort, and the ruins of Martand Sun Temple.",
            "guide_content": """
### Discovering the Magic of Jammu & Kashmir: Your Guide to 'Heaven on Earth'

[IMAGE: jk_shikara.png | A peaceful Shikara boat floating on the mirror-like waters of Dal Lake in Srinagar, facing the distant Himalayan mountains]

#### 1. Introduction: The Legendary "Heaven on Earth"
If there is a heaven on earth, it is this, it is this, it is this.

> **The Proof:** The Great Himalayan National Park Conservation Area in the region is a UNESCO World Heritage Site, recognized for its outstanding biodiversity and dramatic alpine landscapes.

---

#### 2. The Alpine Playground: Iconic Landscapes & Activities

##### 2.1 Srinagar & Dal Lake: The Liquid Heart
* **Experience:** A serene Shikara ride through floating gardens, visiting the vibrant local market from your boat, and staying in a traditional houseboat.
* **The Proof:** The unique community of 'Hanjis' (boat-dwellers) has lived on Dal Lake for centuries. The houseboats are a unique cultural heritage, originally built because British colonists were prohibited from owning land.

##### 2.2 Gulmarg: The Meadow of Flowers & World-Class Skiing
* **Activities:** Skiing & Snowboarding (Dec-Mar), riding the Gulmarg Gondola (one of the world's highest), & summer golfing.
* **The Proof:** Gulmarg boasts the highest gondola in the world (Phase 2 to Apharwat Peak) and is recognized by National Geographic as one of the top skiing destinations globally for its pristine, deep-powder snow.

[IMAGE: jk_skiing.png | A skier carving gracefully down the pristine, deep-powder slopes of Gulmarg with snow-clad peaks in the background]

##### 2.3 Sonamarg & Pahalgam: The Gateway to Treks
* **Experience:** Pony treks to the Thajiwas Glacier (Sonamarg), gentle walks along the Lidder River (Pahalgam), and trekking base for the Amarnath Yatra pilgrimage.
* **The Proof:** Sonamarg is the starting point for the arduous Sindh Valley trek, used for centuries by nomadic Gujjar and Bakarwal shepherds for seasonal migration.

[IMAGE: jk_meadow.jpg | A horse grazing peacefully in the lush, green alpine meadow of Sonamarg with pine forests and towering rocky peaks]

---

#### 3. A Legacy Carved in Stone: Mughal Grandeur & Ancient Temples

##### 3.1 The Terraced Mughal Gardens: Shalimar & Nishat Bagh
* **Explore:** Symmetrical terraces, flowing fountains, and Chinar trees in gardens built for Mughal empresses.
* **The Proof:** Commissioned by Emperor Jahangir in 1619 for his wife Nur Jahan, Shalimar Bagh is a quintessential example of the Mughal concept of Charbagh (paradise garden).

[IMAGE: jk_garden.jpg | Symmetrical lawns and flowing water channels of the historical Shalimar Bagh Mughal Garden in Srinagar]

##### 3.2 Martand Sun Temple: A Colossal Ruin
* **Experience:** Stand amidst the awe-inspiring ruins of one of the largest sun temples in India.
* **The Proof:** Built by King Lalitaditya Muktapida in the 8th century CE, its architecture is a blend of Gandharan, Gupta, and Chinese styles. It's mentioned in the Rajatarangini, the ancient chronicle of Kashmir.

##### 3.3 Hari Parbat Fort: The Sentinel of Srinagar
* **Explore:** A fort atop Sharika Hill, home to a temple, gurdwara, and mosque, overlooking the city.
* **The Proof:** The hill is considered sacred in Hindu, Sikh, and Muslim traditions. The present fort was built in the 18th century by Afghan governor Atta Mohammad Khan over earlier structures.

---

#### 4. The Warmth of the Valley: Culture, Craft, and Cuisine

##### 4.1 The Art of Living: Houseboats, Hamams & Hospitality
* **Experience:** The profound 'Kashmiri hospitality' where guests are treated as a blessing (mehmaan). Soak in the warmth of a traditional Kanger (firepot) and hamam (heated floor).
* **The Proof:** The philosophy of "Mehmaan Nawazi" (guest care) is deeply embedded in Kashmiri culture, famously mentioned in historical texts. The houseboat design includes a central, carpeted living area called the "Dub".

##### 4.2 Craftsmanship: Pashmina, Papier-mâché & Carpets
* **Discover:** The painstaking process of creating Pashmina shawls (from Changthangi goat wool), vibrant papier-mâché artefacts, and hand-knotted silk carpets.
* **The Proof:** Kashmiri Pashmina is protected by a Geographical Indication (GI) tag. The art of Kashmiri papier-mâché is centuries old, introduced by Persian Sufi saint Mir Sayyid Ali Hamadani.

[IMAGE: jk_weaving.jpg | Kashmiri weavers working meticulously on a handloom to create a traditional hand-knotted silk carpet]

##### 4.3 A Taste of Paradise: Wazwan & Warmth
* **Must-Try Dishes:** The grand multi-course feast Wazwan (especially Rogan Josh, Gushtaba), the comforting Nadru Monje (lotus stem fritters), and the fragrant Kahwa tea.
* **The Proof:** The Wazwan is a culinary tradition dating to the 14th-century Timurid courts, preserved by master chefs (Wazas). Saffron, used in Kahwa, is grown locally in Pampore and is among the world's most expensive spices.

---

#### 5. Society & Resilience: The Heart of the Himalayas
* **A Tapestry of Traditions:** The lifestyle of the Gujjar-Bakarwal nomadic pastoralists, the agrarian communities in the valleys, and the skilled urban artisans.
* **The Proof:** Despite challenges, Jammu & Kashmir has India's third-highest literacy rate and is home to a vibrant civil society that continues its traditions of craftsmanship, horticulture (apple farming), and poetry.

---

#### 6. Practical Traveler's Guide to J&K

##### **Best Time to Visit:**
* **Apr–Jun (Spring/Summer):** Ideal for sightseeing, flower gardens in bloom, pleasant climate.
* **Jul–Aug (Monsoon):** Good for trekking, escaping plains' heat.
* **Sep–Oct (Autumn):** Beautiful golden foliage, apple season.
* **Dec–Feb (Winter):** Snow sports, skiing in Gulmarg.

##### **Getting Around:**
Use pre-booked taxis for long distances and sightseeing. Auto-rickshaws are good for city travel in Srinagar.

##### **Stay Options:**
floating wooden houseboats (Srinagar), luxury resorts (Gulmarg), riverside hotels (Pahalgam).

##### **Packing Essentials:**
Layered clothing for all seasons, sunblock, sunglasses, walking shoes, and portable power bank.

---

#### 7. Suggested Itineraries: Crafting Your Paradise Journey

##### **The Classic Valley Circuit (7 Days):**
Srinagar (Dal Lake, Mughal Gardens) → Gulmarg → Pahalgam → Sonamarg → Srinagar.

##### **Spiritual & Scenic Trail (5 Days):**
Jammu (Vaishno Devi) → Patnitop → Srinagar (Shankaracharya Temple, Hazratbal Shrine).

##### **The Road Less Traveled:**
Srinagar → Drive to Gurez Valley (for untouched beauty) or Doodhpathri ("Valley of Milk").

---

#### 8. Conclusion: Let the Paradise Find You
A final reflection on how Jammu & Kashmir offers not just scenic beauty, but a profound experience of culture and human warmth.

> **Call to Action:** Prepare for landscapes that steal your breath and hospitality that steals your heart. Your journey to heaven on earth begins here.
"""
        }
    ]

    if st.session_state.selected_dest is not None:
        # Show detailed destination view (The Travel Blog / Guide)
        dest = next((d for d in DESTINATIONS_DATA if d["name"] == st.session_state.selected_dest), None)
        
        if dest:
            # Premium Hero Banner for the destination
            st.markdown(f"""
            <div class="hero-wrapper">
                <img class="hero-bg" src="{dest['img']}" alt="{dest['name']}" />
                <div class="hero-content">
                    <div class="hero-badge">✦ {dest['tag']}</div>
                    <div class="hero-title">{dest['name']}</div>
                    <div class="hero-sub">📖 Detailed Travel Guide & Adventure Route · {dest['date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if "guide_content" in dest:
                # Parse [IMAGE: path | caption] tags and render using st.image
                content = dest["guide_content"]
                parts = content.split("[IMAGE:")
                st.markdown(parts[0])
                for idx, part in enumerate(parts[1:]):
                    if "]" in part:
                        img_tag, rest = part.split("]", 1)
                        img_info = img_tag.split("|")
                        img_path = img_info[0].strip()
                        if not img_path.startswith(("http://", "https://", "images/")):
                            img_path = f"images/{img_path}"
                        caption = img_info[1].strip() if len(img_info) > 1 else ""
                        
                        col1, col2 = st.columns(2, gap="large")
                        if idx % 2 == 0:
                            with col1:
                                st.markdown(rest)
                            with col2:
                                st.image(img_path, caption=caption, use_container_width=True)
                        else:
                            with col1:
                                st.image(img_path, caption=caption, use_container_width=True)
                            with col2:
                                st.markdown(rest)
                    else:
                        # Fallback: if parsing fails, just render remaining text
                        st.markdown(part)

            else:
                st.markdown(f"# Discovering the Magic of {dest['name'].split(',')[0]}")
                st.markdown(f"**Category:** `{dest['tag']}` | **🗓️ Updated:** {dest['date']}")
                st.markdown("---")
                st.markdown(f"*{dest['desc']}*")
                st.markdown("---")
                
                st.markdown(f"### 📍 Key Places & Sightseeing\n{dest['place']}")
                st.markdown(f"### 🎭 Culture & Cuisine\n{dest['culture']}")
                st.markdown(f"### 👥 Society & Lifestyle\n{dest['society']}")
                st.markdown(f"### 🏛️ Historical Heritage\n{dest['history']}")
                st.markdown("---")
            
            # Action Buttons Row
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🚀 Auto-Plan Trip in AI Planner", use_container_width=True, type="primary"):
                    st.session_state.query_text = dest['prompt']
                    st.session_state.selected_dest = None
                    st.session_state.active_section = "🤖 AI Trip Planner"
                    st.rerun()
            with btn_col2:
                if st.button("🔙 Back to All Destinations", use_container_width=True):
                    st.session_state.selected_dest = None
                    st.rerun()
        else:
            st.session_state.selected_dest = None
            st.rerun()
            
    else:
        # Show all destinations grid (Featured style)
        st.markdown("<div class='sec-head'><span>🌍 Discover Famous Travel Destinations</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94adc8; font-size: 0.95rem; margin-bottom: 1.5rem;'>Explore hand-picked popular travel spots around the world and in India. Click on any destination to instantly pre-fill the AI planner and start mapping out your itinerary!</p>", unsafe_allow_html=True)
        
        # 2-column layout for famous destinations (Featured Posts style)
        for i in range(0, len(DESTINATIONS_DATA), 2):
            row_cols = st.columns(2)
            for col_idx, col in enumerate(row_cols):
                if i + col_idx < len(DESTINATIONS_DATA):
                    dest = DESTINATIONS_DATA[i + col_idx]
                    with col:
                        # Render a clean card looking exactly like a blog post
                        st.markdown(f"""
                        <div style="border: 1px solid #1e3a5c; background: #0e1623; border-radius: 12px; overflow: hidden; margin-bottom: 12px; transition: all 0.3s ease;">
                            <img src="{dest['img']}" style="width:100%; height: 200px; object-fit: cover;" />
                            <div style="padding: 1.2rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="background: rgba(58,123,213,0.15); border: 1px solid rgba(58,123,213,0.4); color: #7ab8f5; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; padding: 0.2rem 0.6rem; border-radius: 15px;">{dest['tag']}</span>
                                    <span style="color: #5a7a96; font-size: 0.78rem;">{dest['date']}</span>
                                </div>
                                <h4 style="margin: 8px 0; color: #ffffff; font-size: 1.20rem; font-weight: 600; line-height: 1.3;">{dest['name']}</h4>
                                <p style="margin: 0 0 16px 0; color: #a0c4e0; font-size: 0.88rem; line-height: 1.5; min-height: 54px;">{dest['desc']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button(f"📖 Explore Guide", key=f"guide_{i+col_idx}", use_container_width=True):
                                st.session_state.selected_dest = dest["name"]
                                st.rerun()
                        with btn_c2:
                            if st.button(f"🚀 Plan Trip", key=f"plan_{i+col_idx}", use_container_width=True, type="primary"):
                                st.session_state.query_text = dest['prompt']
                                st.session_state.active_section = "🤖 AI Trip Planner"
                                st.rerun()

# ── Section 2: AI Trip Planner ────────────────────────────────────────────────
elif st.session_state.active_section == "🤖 AI Trip Planner":
    st.markdown("<div class='sec-head'><span>🤖 Describe Your Dream Trip</span></div>", unsafe_allow_html=True)
     
# Rate limit indicator
    from config.rate_limiter import get_rate_limit_info
    thread_id = st.session_state.get("user_id", "1")
    limit_info = get_rate_limit_info(thread_id)
    st.markdown(f"<div style='color: #7ba4f0; font-size: 0.85rem; margin-bottom: 0.5rem;'>📊 Trips left: {limit_info['remaining']}/{limit_info['limit']}</div>", unsafe_allow_html=True)
     
    # Centered container for query input layout
    p_left, p_mid, p_right = st.columns([1, 10, 1])
    with p_mid:
        # Quick Fills
        QUICK = ["7-day Japan under ₹2L", "Paris trip for 5 days", "Dubai weekend trip", "Bali backpacking 10 days"]
        qcols = st.columns(len(QUICK))
        for qc, label in zip(qcols, QUICK):
            with qc:
                if st.button(label, key=f"q_{label}"):
                    st.session_state.query_text = f"Plan a complete {label} including flights, hotels and sightseeing."
                    st.rerun()
                    
        user_query = st.text_area(
            "Trip description",

            value=st.session_state.query_text,
            placeholder="e.g. Plan a complete 7-day Japan trip including flights, hotels and sightseeing under ₹2 lakhs",
            height=180,
            label_visibility="collapsed",
        )
        # Keep the user's typing synchronized in session state
        st.session_state.query_text = user_query
        
        generate = st.button("🚀  Generate My Travel Plan", use_container_width=True)
    
    # Agent Meta mapping
    AGENT_META = {
        "flight_agent":    ("✈️", "Flight Agent"),
        "hotel_agent":     ("🏨", "Hotel Agent"),
        "itinerary_agent": ("🗓️", "Itinerary Agent"),
        "final_agent":     ("🧠", "Final Agent"),
    }
    
    if generate:
        from config.rate_limiter import check_rate_limit
        if not check_rate_limit(thread_id):
            st.warning("⏱️ You've reached the trip generation limit (4 trips per session). Please refresh to start a new session.")
            logger.warning(f"Rate limit exceeded for user {thread_id}")
        elif not user_query.strip():
            st.warning("Please describe your trip first.")
        else:
            config = {"configurable": {"thread_id": thread_id}}
            st.session_state.collected_results = {
                "flight_results": "",
                "hotel_results": "",
                "itinerary": "",
                "final_response": "",
                "llm_calls": 0,
                "user_query": user_query
            }
            
            st.markdown("---")
            st.markdown("<div class='sec-head'><span>🤖 Agent Pipeline — Live</span></div>",
                        unsafe_allow_html=True)
            
            try:
                # Real-time multi-agent loading UI
                start_ts = datetime.now()
                progress = st.progress(0)
                percent_label = st.empty()
                log_box = st.empty()  # keep status log visible

                # Agent display order & percent mapping
                agent_steps = [
                    ("flight_agent", "✈️ Flight Agent"),
                    ("hotel_agent", "🏨 Hotel Agent"),
                    ("itinerary_agent", "🗺️ Itinerary Agent"),
                    ("final_agent", "✨ Summary Agent"),
                ]
                step_to_percent = {
                    "flight_agent": 25,
                    "hotel_agent": 50,
                    "itinerary_agent": 75,
                    "final_agent": 100,
                }

                status_containers = {}
                for agent_key, agent_display in agent_steps:
                    with st.status(f"⌛ {agent_display}", state="running", expanded=True):
                        st.write("")
                    # create an empty placeholder for later update
                    status_containers[agent_key] = st.empty()

                # Track completion
                completed = set()

                try:
                    for chunk in app.stream(
                        {
                            "messages": [HumanMessage(content=user_query)],
                            "user_query": user_query,
                            "flight_results": "",
                            "hotel_results": "",
                            "itinerary": "",
                            "llm_calls": 0,
                        },
                        config=config,
                        stream_mode="updates",
                    ):
                        for node_name, state_update in chunk.items():
                            if node_name not in step_to_percent:
                                continue

                            icon, label = AGENT_META.get(node_name, ("🔧", node_name))
                            display_label = dict(agent_steps).get(node_name, label)

                            # Update status to complete
                            status_text = {
                                "flight_agent": "Searching Flights...",
                                "hotel_agent": "Finding Hotels...",
                                "itinerary_agent": "Building Day-by-Day Plan...",
                                "final_agent": "Preparing Final Travel Plan...",
                            }.get(node_name, "Running...")

                            pct = step_to_percent[node_name]

                            status_containers[node_name].status(
                                f"✅ {display_label}", state="complete", expanded=True
                            )

                            # Write the agent-specific content and mark progress
                            if node_name == "flight_agent":
                                text = state_update.get("flight_results", "")
                                st.session_state.collected_results["flight_results"] = text
                                st.markdown(text or "_No flight data returned._")
                            elif node_name == "hotel_agent":
                                text = state_update.get("hotel_results", "")
                                st.session_state.collected_results["hotel_results"] = text
                                st.markdown(text or "_No hotel data returned._")
                            elif node_name == "itinerary_agent":
                                text = state_update.get("itinerary", "")
                                st.session_state.collected_results["itinerary"] = text
                                st.markdown(text or "_No itinerary generated._")
                            elif node_name == "final_agent":
                                msgs = state_update.get("messages", [])
                                text = msgs[-1].content if msgs else ""
                                st.session_state.collected_results["final_response"] = text
                                st.markdown(text or "_No final response._")

                            completed.add(node_name)
                            progress.progress(pct / 100.0)
                            percent_label.markdown(f"<div style='color:#7ba4f0;font-weight:700'>{pct}% complete</div>", unsafe_allow_html=True)

                except Exception as e:
                    failed_agent = None
                    # best-effort: infer which agent key we were on
                    for k in agent_steps:
                        if k[0] in completed:
                            continue
                    st.error(f"❌ Agent workflow failed: {e}")
                    st.stop()

                total_time = datetime.now() - start_ts
                percent_label.markdown(
                    "<div style='color:#4ea8f0;font-weight:800'>✅ 100% complete</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='color:#94adc8;font-size:0.9rem;margin-top:0.5rem;'>⏱️ Total execution time: {str(total_time).split('.')[0]}</div>",
                    unsafe_allow_html=True,
                )

                # end loading UI

                                
                # Save to PostgreSQL trip history database
                collected = st.session_state.collected_results
                save_trip_to_db(
                    user_id=thread_id,
                    query=collected["user_query"],
                    flight_results=collected["flight_results"],
                    hotel_results=collected["hotel_results"],
                    itinerary=collected["itinerary"],
                    final_response=collected["final_response"],
                    llm_calls=collected["llm_calls"]
                )
                # No st.rerun() here; let Streamlit render the already-updated session_state.

            except Exception as e:
                st.error(f"❌ An error occurred in the Agent Pipeline: {e}")
                st.session_state.collected_results = None
            
    # Persistently display planned trip results if present in session state
    if st.session_state.collected_results is not None:
        collected = st.session_state.collected_results
        
        # Metrics
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box"><div class="metric-val">4</div><div class="metric-lbl">Agents Run</div></div>
            <div class="metric-box"><div class="metric-val">{collected['llm_calls']}</div><div class="metric-lbl">LLM Calls</div></div>
            <div class="metric-box"><div class="metric-val">✅</div><div class="metric-lbl">Status</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabbed Trip Results
        st.markdown("<div class='sec-head'><span>🗺️ Your Planned Trip Results</span></div>",
                    unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗓️ Detailed Itinerary", 
            "✈️ Flight Options", 
            "🏨 Hotel Details", 
            "📊 Budget & Summary"
        ])
        
        with tab1:
            st.markdown(collected['itinerary'] or "_No itinerary generated._")
            
        with tab2:
            st.markdown(collected['flight_results'] or "_No flights found._")
            
        with tab3:
            st.markdown(collected['hotel_results'] or "_No hotels found._")
            
        with tab4:
            st.markdown(collected['final_response'] or "_No budget/summary._")
            
        # Save & Download files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"travel_plan_{timestamp}.md"
        save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")
        os.makedirs(save_dir, exist_ok=True)
        
        file_content = f"""# Travel Plan
**Query:** {collected['user_query']}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User ID:** {thread_id}

---

## ✈️ Flight Information
{collected['flight_results'] or 'N/A'}

---

## 🏨 Hotel Information
{collected['hotel_results'] or 'N/A'}

---

## 🗓️ Itinerary
{collected['itinerary'] or 'N/A'}

---

## 🧠 Final Travel Plan
{collected['final_response'] or 'N/A'}

---
*LLM Calls: {collected['llm_calls']}*
"""
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(file_content)
            
        dl_col1, dl_col2, info_col = st.columns([1.2, 1.2, 2.6])
        with dl_col1:
            st.download_button("⬇️ Download Markdown", data=file_content,
                               file_name=filename, mime="text/markdown",
                               use_container_width=True)
        with dl_col2:
            try:
                pdf_data = generate_pdf_data(collected, thread_id)
                st.download_button("⬇️ Download PDF", data=pdf_data,
                                   file_name=filename.replace(".md", ".pdf"), mime="application/pdf",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")

        # Feedback prompt right after Save/Download buttons
        with info_col:
            st.markdown(f"<div class='save-bar'>📁 Auto-saved → <code>travel_plans/{filename}</code></div>",
                        unsafe_allow_html=True)

            st.markdown("<div class='sec-head' style='margin-top: 1.2rem;'><span>💬 Would you like to provide feedback?</span></div>", unsafe_allow_html=True)
            c_yes, c_no = st.columns([1, 1])
            with c_yes:
                if st.button("Yes - Open Feedback", type="primary", use_container_width=True, key="open_feedback_yes"):
                    st.session_state.active_section = "📝 Feedback"

            with c_no:
                if st.button("No - Back to Home", use_container_width=True, key="open_feedback_no"):
                    st.session_state.active_section = "🏠 Home"
                    st.rerun()


elif st.session_state.active_section == "📜 Saved History":
    st.markdown("<div class='sec-head'><span>📜 Your Saved Trip History</span></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94adc8; font-size: 0.95rem; margin-bottom: 1.5rem;'>Viewing past travel plans saved in the database for User ID: <code>{thread_id}</code></p>", unsafe_allow_html=True)
    
    saved_trips = get_saved_trips(thread_id)
    
    if not saved_trips:
        st.info("No saved travel plans found for this User ID. Try generating a new plan in the AI Travel Planner section!")
    else:
        for trip in saved_trips:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #1e3a5c; background: #0e1623; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 8px 0; color: #a5c8ff; font-weight: 600; line-height: 1.3;">✈️ Query: {trip['query']}</h4>
                    <div style="display: flex; gap: 1.5rem; color: #7aa8cc; font-size: 0.8rem; margin-top: 8px;">
                        <span>📅 Saved: {trip['created_at'].strftime("%Y-%m-%d %H:%M:%S")}</span>
                        <span>🧠 LLM Calls: {trip['llm_calls']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                bcol1, bcol2, _ = st.columns([1, 1, 3])
                with bcol1:
                    if st.button("🚀 Load Plan", key=f"load_{trip['id']}", use_container_width=True):
                        st.session_state.collected_results = {
                            "flight_results": trip["flight_results"],
                            "hotel_results": trip["hotel_results"],
                            "itinerary": trip["itinerary"],
                            "final_response": trip["final_response"],
                            "llm_calls": trip["llm_calls"],
                            "user_query": trip["query"]
                        }
                        st.session_state.active_section = "🤖 AI Trip Planner"
                        st.success("Trip loaded successfully! Redirecting...")
                        st.rerun()
                with bcol2:
                    if st.button("🗑️ Delete", key=f"del_{trip['id']}", use_container_width=True):
                        if delete_saved_trip(trip['id']):
                            st.success("Trip deleted successfully!")
                            st.rerun()

# ── Section: User Feedback ─────────────────────────────────────────────────────
elif st.session_state.active_section == "📝 Feedback":
    st.markdown("<div class='sec-head'><span>📝 We Value Your Feedback</span></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94adc8; font-size: 0.95rem; margin-bottom: 1.5rem;'>Help us improve your travel planning experience!</p>", unsafe_allow_html=True)
     
    with st.container():
        st.markdown("<div class='input-card' style='background: rgba(123,164,240,0.03); border: 1px solid rgba(123,164,240,0.15); border-radius: 16px; padding: 32px;'>", unsafe_allow_html=True)
         
        st.markdown("<div style='font-size: 1.2rem; font-weight: 700; color: #e0eaff; margin-bottom: 0.5rem;'>🌟 Overall Satisfaction</div>", unsafe_allow_html=True)
        overall_rating = st.slider("Overall Rating", 1, 5, 5, key="overall_rating")
        st.markdown(f"<div style='color: #7ba4f0; font-size: 1.2rem; margin-bottom: 1.5rem;'>{'⭐' * overall_rating} {'☆' * (5 - overall_rating)}</div>", unsafe_allow_html=True)


         
        st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #a0c4e0; margin: 1.5rem 0 0.8rem;'>What did you like most?</div>", unsafe_allow_html=True)
         
        feedback_items = [
            ("Flight recommendations", "flight_rating"),
            ("Hotel suggestions", "hotel_rating"),
            ("Itinerary planning", "itinerary_rating"),
            ("Budget estimation", "budget_rating"),
            ("User interface", "ui_rating"),
        ]
         
        rating_values = {}
        for label, key in feedback_items:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"<div style='color: #a0c4e0; padding: 8px 0;'>* {label}</div>", unsafe_allow_html=True)
            with col2:
                rating = st.slider(label or "Rating", 1, 5, 5, key=key, label_visibility="collapsed")

                rating_values[key] = rating
         
        st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #a0c4e0; margin: 1.5rem 0 0.8rem;'>What can we improve?</div>", unsafe_allow_html=True)
        suggestions = st.text_area("Suggestions", placeholder="Write your suggestions here...", height=120, label_visibility="collapsed")
         
        st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #a0c4e0; margin: 1.5rem 0 0.8rem;'>Would you recommend AI Travel Booking System to others?</div>", unsafe_allow_html=True)
        recommendation = st.radio("Recommendation", ["Yes", "No", "Not Sure"], key="recc_radio", label_visibility="collapsed", horizontal=True)
         
        st.markdown("<br>", unsafe_allow_html=True)
         
        submit = st.button("📩 Submit Feedback", key="submit_feedback", type="primary", use_container_width=True)
         
        if submit:
            if save_feedback_to_db(
                user_id=thread_id,
                overall_rating=overall_rating,
                flight_rating=rating_values["flight_rating"],
                hotel_rating=rating_values["hotel_rating"],
                itinerary_rating=rating_values["itinerary_rating"],
                budget_rating=rating_values["budget_rating"],
                ui_rating=rating_values["ui_rating"],
                recommendation=recommendation,
                suggestions=suggestions
            ):
                st.success("✅ Thank you for your feedback!")
                # After feedback submission, redirect to Home
                st.session_state.active_section = "🏠 Home"

                st.rerun()

         
        st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
render_footer()
