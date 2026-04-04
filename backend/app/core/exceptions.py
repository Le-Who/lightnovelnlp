"""
Custom exceptions for the application services.

These exceptions are framework-agnostic and should be caught
and converted to HTTP responses at the API layer.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for service layer errors."""

    pass


class RateLimitExceeded(ServiceError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ):
        self.message = message
        self.retry_after = retry_after  # seconds until retry is allowed
        super().__init__(self.message)


class APIKeyExhausted(ServiceError):
    """Raised when all API keys are exhausted or in cooldown."""

    def __init__(self, message: str = "All API keys exhausted"):
        self.message = message
        super().__init__(self.message)


class ExternalAPIError(ServiceError):
    """Raised when external API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
