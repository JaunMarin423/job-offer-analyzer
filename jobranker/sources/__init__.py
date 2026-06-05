"""Job sources: legal providers and manual file input."""

from .local import load_local
from .remotive import fetch_remotive

__all__ = ["load_local", "fetch_remotive"]
