import os
from typing import Optional

class Settings:
    """Environment-specific configuration management."""
    
    def __init__(self):
        self.env = os.getenv("ENV", "development")
        self.debug = self.env == "development"
        
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "")
        
        # API settings
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.aviationstack_api_key = os.getenv("AVIATIONSTACK_API_KEY", "")
        
        # Rate limiting (3-4 calls per session)
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_calls = int(os.getenv("RATE_LIMIT_CALLS", "4"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO" if self.env == "production" else "DEBUG")

settings = Settings()