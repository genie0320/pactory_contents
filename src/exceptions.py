"""Custom domain exceptions for pactory_contents.

Clean, typed exceptions for backend operations without silent mock fallbacks.
"""

class PactoryError(Exception):
    """Base exception for all Pactory operations."""
    pass


class LLMServiceError(PactoryError):
    """Raised when an LLM service request fails or is unavailable."""
    pass


class ProofreaderError(PactoryError):
    """Raised when proofreading evaluation or rewriting fails."""
    pass
