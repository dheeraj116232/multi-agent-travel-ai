import os
import logging

# Environment configuration
ENV = os.getenv("ENV", "development")

# App settings
DEBUG = ENV == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "4"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_file = f"logs/app.log" if ENV == "production" else None