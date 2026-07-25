"""Validation tools for sanitized agent-development handoffs."""

from .validator import ValidationError, validate_manifest

__all__ = ["ValidationError", "validate_manifest"]
__version__ = "0.1.0"
