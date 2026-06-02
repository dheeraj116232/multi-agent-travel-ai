# Rate Limiting Module for AI Travel Planner - Per Session
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

class RateLimiter:
    """Session-based rate limiter - 3-4 total calls per user session."""
    
    def __init__(self, max_calls: int = 4):
        self.max_calls = max_calls
        self.calls = defaultdict(int)
        self.lock = Lock()
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to make an API call (session-based)."""
        with self.lock:
            if self.calls[user_id] >= self.max_calls:
                logger.warning(f"Rate limit exceeded for user {user_id}. Max {self.max_calls} calls reached.")
                return False
            
            self.calls[user_id] += 1
            remaining = self.max_calls - self.calls[user_id]
            logger.info(f"API call allowed for user {user_id}. {remaining} calls remaining.")
            return True
    
    def get_remaining_calls(self, user_id: str) -> int:
        """Get remaining calls for user."""
        with self.lock:
            return max(0, self.max_calls - self.calls[user_id])
    
    def reset_user(self, user_id: str):
        """Reset rate limit for a user (if needed)."""
        with self.lock:
            self.calls[user_id] = 0
            logger.info(f"Rate limit reset for user {user_id}")

# Global rate limiter instance - 3-4 calls per session
import os
MAX_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "4"))

rate_limiter = RateLimiter(max_calls=MAX_CALLS)

def check_rate_limit(user_id: str) -> bool:
    """Check rate limit before API calls."""
    return rate_limiter.is_allowed(user_id)

def get_rate_limit_info(user_id: str) -> dict:
    """Get rate limit information for a user."""
    return {
        "remaining": rate_limiter.get_remaining_calls(user_id),
        "limit": rate_limiter.max_calls
    }

def reset_rate_limit(user_id: str):
    """Reset rate limit for user."""
    rate_limiter.reset_user(user_id)