from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExternalErrorContext:
    provider: Optional[str] = None
    operation: Optional[str] = None
    status_code: Optional[int] = None
    user_message: Optional[str] = None
    retryable: bool = True
    raw_snippet: Optional[str] = None


class ProductionExternalAPIError(Exception):
    """
    Base exception for external API failures.
    Always carry a user-friendly message and enough context for logs.
    """

    def __init__(self, message: str, *, context: ExternalErrorContext | dict):
        super().__init__(message)
        if isinstance(context, dict):
            self.context = ExternalErrorContext(**context)
        else:
            self.context = context


class APITimeoutError(ProductionExternalAPIError):
    pass


class APIRateLimitError(ProductionExternalAPIError):
    pass


class InvalidAPIKeyError(ProductionExternalAPIError):
    pass


class NetworkConnectivityError(ProductionExternalAPIError):
    pass


class MalformedAPIResponseError(ProductionExternalAPIError):
    pass


class EmptyAPIResponseError(ProductionExternalAPIError):
    pass


class ExternalAPIError(ProductionExternalAPIError):
    pass


class DatabaseUnavailableError(ProductionExternalAPIError):
    pass


def user_message_or_default(exc: ProductionExternalAPIError, default: str) -> str:
    return exc.context.user_message or default
