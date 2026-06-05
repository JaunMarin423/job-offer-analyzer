"""Job sources: legal providers and manual file input."""

from .arbeitnow import fetch_arbeitnow
from .jobicy import fetch_jobicy
from .local import load_local
from .remoteok import fetch_remoteok
from .remotive import fetch_remotive

__all__ = [
    "load_local",
    "fetch_remotive",
    "fetch_remoteok",
    "fetch_arbeitnow",
    "fetch_jobicy",
]
