from __future__ import annotations

import logging
import time
from typing import Callable, Iterable, Tuple, Type, TypeVar

from core.errors import ProductionExternalAPIError

T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry_external_call(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    backoff_seconds: Tuple[int, int, int] = (1, 2, 4),
    retry_on: Iterable[Type[Exception]] = (ProductionExternalAPIError,),
    provider: str | None = None,
    operation: str | None = None,
    agent: str | None = None,
) -> T:
    """
    Retry wrapper for external calls.

    - Max attempts = retries (default 3). So total attempts = retries.
    - Exponential backoff: 1s, 2s, 4s for the first 3 retries (attempts 1..retries).
    - Logs each retry attempt.
    - Stops after max attempts.
    """
    last_exc: Exception | None = None

    attempt = 1
    while attempt <= retries:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc

            is_retryable = isinstance(exc, tuple(retry_on))
            if not is_retryable:
                raise

            if attempt >= retries:
                raise

            # Backoff: map attempt->backoff index (0..)
            idx = min(attempt - 1, len(backoff_seconds) - 1)
            sleep_s = backoff_seconds[idx]

            logger.warning(
                "External call failed; retrying",
                extra={
                    "provider": provider,
                    "operation": operation,
                    "agent": agent,
                    "attempt": attempt,
                    "sleep_seconds": sleep_s,
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                },
            )

            # small toast/streamlit isn't here; just sleep
            time.sleep(sleep_s)
            attempt += 1

    # defensive; should not reach
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_external_call: unreachable state")
