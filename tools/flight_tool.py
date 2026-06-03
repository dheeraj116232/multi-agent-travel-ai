
# Example free API usage
# - AviationStack


# create api key
# https://aviationstack.com/ 
# pip install requests


    
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

from core.errors import (
    APIRateLimitError,
    APITimeoutError,
    EmptyAPIResponseError,
    InvalidAPIKeyError,
    MalformedAPIResponseError,
    NetworkConnectivityError,
    ProductionExternalAPIError,
)
from core.logger import get_app_logger
from core.retry import retry_external_call

load_dotenv()

# Silence unused warning in some linters if query is not used for provider params.
# (Declared inside search_flights; this module-level placeholder must not reference it.)
_query_placeholder = None


API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

logger = get_app_logger("flight_agent_api")


AVIATIONSTACK_URL = "http://api.aviationstack.com/v1/flights"


def _detect_and_raise_from_response(resp: requests.Response, data: Any) -> None:
    status_code = resp.status_code

    # 429 - rate limited
    if status_code == 429:
        raise APIRateLimitError(
            "AviationStack rate limit reached",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ API rate limit reached. Please wait a few minutes.",
            },
        )

    # invalid key -> many APIs return 401/403 or error message
    if status_code in (401, 403):
        raise InvalidAPIKeyError(
            "AviationStack invalid API key",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": False,
                "user_message": "⚠️ Flight service authentication failed. Please try again later.",
            },
        )

    # Other non-2xx
    if status_code < 200 or status_code >= 300:
        raise ProductionExternalAPIError(
            f"AviationStack request failed with status {status_code}",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
            },
        )

    # malformed/empty response
    if data is None:
        raise EmptyAPIResponseError(
            "AviationStack response is empty",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
            },
        )

    if not isinstance(data, dict):
        raise MalformedAPIResponseError(
            "AviationStack response is not a JSON object",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
            },
        )

    if "data" not in data:
        # sometimes APIs return {"error": ...} shape
        raise MalformedAPIResponseError(
            "AviationStack response missing 'data' field",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
                "raw_snippet": str(data)[:300],
            },
        )

    if not data.get("data"):
        raise EmptyAPIResponseError(
            "AviationStack returned empty data list",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "status_code": status_code,
                "retryable": True,
                "user_message": "⚠️ No flight results available right now. Proceeding with estimated flight information.",
                "raw_snippet": str(data)[:300],
            },
        )


def search_flights(query: str) -> str:
    """
    Returns a formatted flight summary string.
    On failure, raises ProductionExternalAPIError (caller handles fallback).
    """
    if not API_KEY:
        raise InvalidAPIKeyError(
            "AVIATIONSTACK_API_KEY missing",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "retryable": False,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
            },
        )

    params: Dict[str, Any] = {
        "access_key": API_KEY,
        "limit": 5,
    }

    def _call() -> str:
        try:
            # NOTE: AviationStack expects additional query params in real use.
            # Existing app passes only user_query; keep compatibility by not changing params.
            resp = requests.get(AVIATIONSTACK_URL, params=params, timeout=5)
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(
                "AviationStack request timed out",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkConnectivityError(
                "AviationStack connection error",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e
        except requests.exceptions.RequestException as e:
            raise NetworkConnectivityError(
                "AviationStack network/request error",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                    "raw_snippet": str(e)[:300],
                },
            ) from e

        # Parse JSON safely
        try:
            data = resp.json()
        except ValueError as e:
            raise MalformedAPIResponseError(
                "AviationStack returned invalid JSON",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "status_code": resp.status_code,
                    "retryable": True,
                    "user_message": "⚠️ Flight service returned unexpected data. Please try again later.",
                    "raw_snippet": (resp.text or "")[:300],
                },
            ) from e

        _detect_and_raise_from_response(resp, data)

        flights = []
        for flight in data.get("data", [])[:5]:
            airline = flight.get("airline", {}).get("name", "Unknown")
            departure = flight.get("departure", {}).get("airport", "Unknown")
            arrival = flight.get("arrival", {}).get("airport", "Unknown")
            status = flight.get("flight_status", "Unknown")
            flights.append(
                f"""
Airline: {airline}
Departure: {departure}
Arrival: {arrival}
Status: {status}
"""
            )

        # If parsing yields nothing after validation, treat as empty
        joined = "\n".join(flights).strip()
        if not joined:
            raise EmptyAPIResponseError(
                "AviationStack produced empty formatted flights",
                context={
                    "provider": "aviationstack",
                    "operation": "search_flights",
                    "retryable": True,
                    "user_message": "⚠️ No flight results available right now. Proceeding with estimated flight information.",
                },
            )

        return joined

    # Retry external call; retry only ProductionExternalAPIError subclasses
    try:
        return retry_external_call(
            lambda: _call(),
            retries=2,
            backoff_seconds=(1, 2),
            retry_on=(
                ProductionExternalAPIError,
                APITimeoutError,
                APIRateLimitError,
                InvalidAPIKeyError,
                NetworkConnectivityError,
                MalformedAPIResponseError,
                EmptyAPIResponseError,
            ),
            provider="aviationstack",
            operation="search_flights",
            agent="flight_agent",
        )
    except ProductionExternalAPIError as e:
        # Log structured error
        logger.error(
            "External API call failed after retries",
            extra={
                "agent": "flight_agent",
                "provider": e.context.provider,
                "operation": e.context.operation,
                "status_code": e.context.status_code,
                "exception_type": type(e).__name__,
                "user_message": e.context.user_message,
                "raw_snippet": e.context.raw_snippet,
            },
        )
        # Re-raise so agent can fallback based on type
        raise
    except Exception as e:
        logger.exception("Unexpected flight_tool error")
        raise ProductionExternalAPIError(
            "Unexpected flight tool failure",
            context={
                "provider": "aviationstack",
                "operation": "search_flights",
                "retryable": False,
                "user_message": "⚠️ Flight service is temporarily unavailable. Please try again later.",
                "raw_snippet": str(e)[:300],
            },
        ) from e
