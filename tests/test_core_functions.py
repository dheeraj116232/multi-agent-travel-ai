import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.rate_limiter import RateLimiter, check_rate_limit, rate_limiter, get_rate_limit_info

def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter(max_calls=4)
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user1") == True

def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(max_calls=3)
    limiter.is_allowed("user1")
    limiter.is_allowed("user1")
    limiter.is_allowed("user1")
    # Fourth call should be blocked (exceeds limit of 3)
    assert limiter.is_allowed("user1") == False

def test_rate_limiter_different_users():
    limiter = RateLimiter(max_calls=2)
    assert limiter.is_allowed("user1") == True
    assert limiter.is_allowed("user2") == True
    assert limiter.get_remaining_calls("user1") == 1
    assert limiter.get_remaining_calls("user2") == 1

def test_get_rate_limit_info():
    limiter = RateLimiter(max_calls=4)
    info = get_rate_limit_info("test_user")
    assert info["limit"] == 4
    assert info["remaining"] == 3  # One call already made

def test_rate_limiter_reset():
    limiter = RateLimiter(max_calls=2)
    limiter.is_allowed("user1")
    limiter.is_allowed("user1")
    limiter.reset_user("user1")
    assert limiter.is_allowed("user1") == True