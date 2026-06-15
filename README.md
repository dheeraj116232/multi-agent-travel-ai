<div align="center">

# AI Multi-Agent Travel Planning System

An AI-powered travel planner that combines a LangGraph agent pipeline with a Streamlit web app to generate flight-aware, hotel-aware, day-by-day travel plans.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/LangGraph-Agent_Workflow-FF6B35?style=for-the-badge" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Streamlit-Web_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Persistence-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"/>
</p>

[![Tests](https://img.shields.io/badge/tests-pytest-blue)](#testing)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](#docker)
[![Status](https://img.shields.io/badge/status-portfolio_ready-brightgreen)](#production-readiness)
[![Last Commit](https://img.shields.io/github/last-commit/dheeraj116232/multi-agent-travel-ai)](https://github.com/dheeraj116232/multi-agent-travel-ai/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/dheeraj116232/multi-agent-travel-ai?style=social)](https://github.com/dheeraj116232/multi-agent-travel-ai/stargazers)
[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Render-46E3B7?style=for-the-badge)](https://multi-agent-travel-ai.onrender.com)

</div>

---

## 🚀 Live Demo

**Try it now → [https://tripnavigator-ai.onrender.com/](https://tripnavigator-ai.onrender.com/)**

> ⚠️ Hosted on Render free tier — the app may take **30–60 seconds to wake up** on first load. Just wait a moment and refresh if needed.

---

## Overview

This project turns a natural-language travel request into a complete travel plan. A sequential LangGraph workflow runs specialized agents for flight search, hotel search, itinerary creation, and final trip summarization. The Streamlit frontend adds a polished planner UI, themed navigation, trip history, feedback collection, and downloadable Markdown/PDF travel plans.

The code supports both a web interface and a CLI entrypoint, with PostgreSQL used for LangGraph checkpoints and saved trip history when `DATABASE_URL` is configured.

> 🌐 **Live app:** [https://tripnavigator-ai.onrender.com/](https://tripnavigator-ai.onrender.com/) — Try it directly in your browser, no setup needed.
> 📸 **Screenshots/demo video** — will be added in the next update.

---

## Features

| Feature | What it does |
|---|---|
| Multi-agent workflow | Runs flight, hotel, itinerary, and final-summary agents in sequence. |
| Streamlit planner UI | Provides Home, AI Trip Planner, Famous Destinations, Saved History, and Feedback sections. |
| Flight search | Uses AviationStack to fetch live flight-related data. |
| Hotel/travel search | Uses Tavily web search for hotel and travel context. |
| LLM itinerary generation | Uses Groq/Llama 3.3 70B by default, with OpenAI fallback when configured. |
| PostgreSQL persistence | Enables LangGraph checkpoints, saved trips, and feedback storage. |
| Downloadable plans | Auto-saves generated plans and supports Markdown and PDF downloads. |
| Rate limiting | Limits trip generation per user/session to control API usage. |
| Docker support | Includes Dockerfile and docker-compose profiles for development and production-style runs. |

---

## Architecture

```mermaid
graph TD
    A[User request] --> B[Flight Agent]
    B --> C[Hotel Agent]
    C --> D[Itinerary Agent]
    D --> E[Final Summary Agent]
    E --> F[Streamlit Results]
    F --> G[Markdown/PDF Download]
    F --> H[(PostgreSQL saved trips)]

    I[(PostgreSQL checkpointing)] -. optional .- B
    I -. optional .- C
    I -. optional .- D
    I -. optional .- E
```

The agent workflow is defined in [main.py](main.py). The Streamlit frontend is implemented in [frontend.py](frontend.py), with smaller UI helpers in [ui/](ui/). Core business logic lives in [core/](core/). External service integrations live in [tools/](tools/).

---

## Tech Stack

| Layer | Tools |
|---|---|
| Agent orchestration | LangGraph, LangChain |
| LLM providers | Groq `llama-3.3-70b-versatile`, optional OpenAI fallback |
| Frontend | Streamlit |
| Search APIs | Tavily, AviationStack |
| Persistence | PostgreSQL, LangGraph Postgres checkpointer |
| Export | Markdown files, FPDF2-generated PDFs |
| DevOps | Docker, docker-compose, pytest |

---

## Project Structure

```text
multi-agent-travel-ai/
├── main.py                    # LangGraph workflow and CLI entrypoint
├── frontend.py                # Streamlit web application
├── footer.py                  # Shared footer UI
├── config/
│   ├── settings.py            # Environment-driven settings
│   └── rate_limiter.py        # Per-user/session API call limiting
├── core/                      # Core agent logic and workflow helpers
├── tools/
│   ├── flight_tool.py         # AviationStack flight search
│   └── tavily_tool.py         # Tavily hotel/travel search
├── ui/
│   ├── sidebar.py             # Sidebar navigation and theme controls
│   ├── styles.py              # Shared UI styles
│   └── sections_*.py          # Modular UI section placeholders/helpers
├── tests/
│   └── test_core_functions.py # Rate limiter and core tests
├── images/                    # Destination image assets
├── Dockerfile                 # Container image for the Streamlit app
├── docker-compose.yml         # Development and production profiles
├── requirements.txt           # Python dependencies
├── TODO.md                    # Planned improvements and known gaps
├── .env.example               # Environment variable template
└── README.md
```

Generated folders such as `travel_plans/`, `logs/`, `__pycache__/`, virtual environments, and `.env` are intentionally ignored by Git.

---

## Getting Started

### Prerequisites

- Python 3.11 recommended
- PostgreSQL 14+ recommended for persistence
- API keys for at least one LLM provider:
  - Groq: `GROQ_API_KEY`
  - Optional fallback: `OPENAI_API_KEY`
- Tavily API key for hotel/travel web search
- AviationStack API key for flight lookup

### 1. Clone the Repository

```bash
git clone https://github.com/dheeraj116232/multi-agent-travel-ai.git
cd multi-agent-travel-ai
```

### 2. Create a Virtual Environment

```bash
python -m venv langgraph_env3
```

Windows:

```bash
langgraph_env3\Scripts\activate
```

macOS/Linux:

```bash
source langgraph_env3/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template and fill in your values:

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Required for full functionality:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/langgraph_memory_demo
```

`OPENAI_API_KEY` is optional and is used only when Groq is not configured.

### 5. Set Up PostgreSQL

Create the database used by `DATABASE_URL`:

```sql
CREATE DATABASE langgraph_memory_demo;
```

The app can start without `DATABASE_URL`, but persistent checkpoints, saved trip history, and feedback storage require PostgreSQL.

---

## Running the App

### Streamlit Web App

```bash
streamlit run frontend.py
```

Open `http://localhost:8501`.

### CLI Mode

```bash
python main.py
```

---

## Docker

Development profile:

```bash
docker compose --profile development up --build
```

Production-style profile:

```bash
docker compose --profile production up --build
```

The compose file reads environment variables from your shell or `.env` file and exposes the Streamlit app on port `8501` by default.

---

## Example Prompts

```text
Plan a complete 7-day Japan trip including flights, hotels, and sightseeing under Rs. 2 lakhs (~$2,400 USD).
```

```text
Plan a 5-day Paris trip for 2 people with a mid-range budget.
```

```text
Plan a complete 6-day Kashmir trip covering Srinagar houseboats and Gulmarg snow resorts.
```

---

## Testing

Run the unit tests:

```bash
pytest -q
```

Check Python syntax for the main app files:

```bash
python -m py_compile main.py frontend.py config/rate_limiter.py tools/flight_tool.py tools/tavily_tool.py
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `LLM provider is not configured` | Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env`. |
| No saved trip history | Set `DATABASE_URL` and ensure PostgreSQL is running. |
| Tavily search errors | Confirm `TAVILY_API_KEY` is valid. The app can continue with fallback text, but hotel quality will be lower. |
| Flight results missing | Confirm `AVIATIONSTACK_API_KEY` is valid and the API quota is available. |
| PDF generation fails | Ensure `fpdf2` is installed from `requirements.txt`. |
| Import errors from `core/` | Ensure `core/__init__.py` exists and dependencies are installed. |
| Docker healthcheck fails | Wait for Streamlit startup, then check `docker compose logs app` or `docker compose logs dev`. |

---

## Production Readiness

This repository is suitable as a strong portfolio or prototype-to-production foundation. It includes:

- Clear agent workflow boundaries
- Environment-based configuration
- PostgreSQL-backed persistence
- Docker support
- Basic tests
- Rate limiting
- Secret-safe `.gitignore`
- Download/export workflows

Before deploying to real users, add:

- Authentication and user-owned trip records
- CI/CD pipeline with automated tests
- Structured logging and monitoring
- Stronger error handling around third-party APIs
- Secrets management through a cloud provider or deployment platform
- Screenshots or a demo video in this README

---

## Security Notes

- Never commit `.env` or real API keys.
- Use `.env.example` only for placeholders.
- Rotate API keys if they were ever committed in old local history.
- Treat generated travel plans as user data; avoid committing `travel_plans/`.

---

## Contributing

Contributions are welcome.

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
```

Then open a pull request on GitHub.

---

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
