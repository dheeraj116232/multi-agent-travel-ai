from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

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

logger = get_app_logger("hotel_agent_api")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# We intentionally re-create TavilyClient per call (safer if key rotates/env changes).


def _detect_and_raise_for_response(response: Any) -> None:
    if response is None:
        raise EmptyAPIResponseError(
            "Tavily response is empty",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": True,
                "user_message": "⚠️ Hotel search service timed out.",
            },
        )

    # Tavily SDK returns dict like: {"results":[...]}
    if not isinstance(response, dict):
        raise MalformedAPIResponseError(
            "Tavily response is not a dict",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": True,
                "user_message": "⚠️ Hotel search service returned unexpected data. Please try again later.",
                "raw_snippet": str(response)[:300],
            },
        )

    results = response.get("results")
    if results is None:
        raise MalformedAPIResponseError(
            "Tavily response missing 'results'",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": True,
                "user_message": "⚠️ Hotel search service returned unexpected data. Please try again later.",
                "raw_snippet": str(response)[:300],
            },
        )

    if not results:
        raise EmptyAPIResponseError(
            "Tavily returned empty results",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": True,
                "user_message": "⚠️ No hotel results available right now. Proceeding without hotel recommendations.",
                "raw_snippet": str(response)[:300],
            },
        )


def tavily_search(query: str) -> str:
    """
    Returns a formatted hotel summary string.
    On failure, raises ProductionExternalAPIError (caller handles fallback).
    """
    api_key = os.getenv("TAVILY_API_KEY") or TAVILY_API_KEY
    if not api_key:
        raise InvalidAPIKeyError(
            "TAVILY_API_KEY missing",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": False,
                "user_message": "⚠️ Hotel search service authentication failed. Please try again later.",
            },
        )

    def _call() -> str:
        try:
            dynamic_client = TavilyClient(api_key=api_key)
            response = dynamic_client.search(query=query, max_results=5)
        except Exception as e:
            # Tavily SDK exceptions: we don't have a guaranteed status_code attribute,
            # so we inspect message for common patterns.
            msg = str(e).lower()

            if "429" in msg or "rate limit" in msg:
                raise APIRateLimitError(
                    "Tavily rate limit reached",
                    context={
                        "provider": "tavily",
                        "operation": "tavily_search",
                        "status_code": 429,
                        "retryable": True,
                        "user_message": "⚠️ API rate limit reached. Please wait a few minutes.",
                        "raw_snippet": msg[:300],
                    },
                ) from e

            if "401" in msg or "403" in msg or "invalid api key" in msg or "unauthorized" in msg:
                raise InvalidAPIKeyError(
                    "Tavily invalid API key",
                    context={
                        "provider": "tavily",
                        "operation": "tavily_search",
                        "status_code": None,
                        "retryable": False,
                        "user_message": "⚠️ Hotel search service authentication failed. Please try again later.",
                        "raw_snippet": msg[:300],
                    },
                ) from e

            # best-effort timeout detection
            if "timeout" in msg or "timed out" in msg or "deadline" in msg:
                raise APITimeoutError(
                    "Tavily request timed out",
                    context={
                        "provider": "tavily",
                        "operation": "tavily_search",
                        "retryable": True,
                        "user_message": "⚠️ Hotel search service timed out.",
                        "raw_snippet": msg[:300],
                    },
                ) from e

            # network problems
            if "connection" in msg or "network" in msg or "dns" in msg:
                raise NetworkConnectivityError(
                    "Tavily network connectivity failure",
                    context={
                        "provider": "tavily",
                        "operation": "tavily_search",
                        "retryable": True,
                        "user_message": "⚠️ Hotel search service is temporarily unavailable. Please try again later.",
                        "raw_snippet": msg[:300],
                    },
                ) from e

            # fallback: treat as external API error
            raise ProductionExternalAPIError(
                "Tavily request failed",
                context={
                    "provider": "tavily",
                    "operation": "tavily_search",
                    "retryable": True,
                    "user_message": "⚠️ Hotel search service is temporarily unavailable. Please try again later.",
                    "raw_snippet": msg[:300],
                },
            ) from e

        _detect_and_raise_for_response(response)

        results = []
        for i, r in enumerate(response["results"], 1):
            title = (r.get("title") or "Unknown").strip()
            url = r.get("url") or ""
            snippet = (r.get("content") or "").strip()

            # Keep only the first 300 characters to avoid wall-of-text
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

            results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

        joined = "\n\n".join(results).strip()
        if not joined:
            raise EmptyAPIResponseError(
                "Tavily produced empty formatted results",
                context={
                    "provider": "tavily",
                    "operation": "tavily_search",
                    "retryable": True,
                    "user_message": "⚠️ No hotel results available right now. Proceeding without hotel recommendations.",
                },
            )
        return joined

    try:
        return retry_external_call(
            lambda: _call(),
            retries=2,
            backoff_seconds=(1, 2),
            retry_on=(
                APITimeoutError,
                APIRateLimitError,
                InvalidAPIKeyError,
                NetworkConnectivityError,
                MalformedAPIResponseError,
                EmptyAPIResponseError,
                ProductionExternalAPIError,
            ),
            provider="tavily",
            operation="tavily_search",
            agent="hotel_agent",
        )
    except ProductionExternalAPIError as e:
        logger.error(
            "External API call failed after retries",
            extra={
                "agent": "hotel_agent",
                "provider": e.context.provider,
                "operation": e.context.operation,
                "status_code": e.context.status_code,
                "exception_type": type(e).__name__,
                "user_message": e.context.user_message,
                "raw_snippet": e.context.raw_snippet,
            },
        )
        raise
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected tavily_tool error")
        raise ProductionExternalAPIError(
            "Unexpected tavily tool failure",
            context={
                "provider": "tavily",
                "operation": "tavily_search",
                "retryable": False,
                "user_message": "⚠️ Hotel search service is temporarily unavailable. Please try again later.",
                "raw_snippet": str(e)[:300],
            },
        ) from e

