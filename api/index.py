"""Vercel serverless entry point.

Vercel's Python runtime serves the ASGI ``app`` object exposed here. We add the
repository root to ``sys.path`` so the bundled ``jobranker`` package is importable
inside the function sandbox.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobranker.web import app  # noqa: E402

__all__ = ["app"]
