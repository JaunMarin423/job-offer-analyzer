"""Parse and normalize salaries so offers can be compared.

Salaries arrive as structured numbers (Jobicy) or free-form strings
(Remotive, local files), e.g. "$109k - $228k", "USD 50,000-70,000",
"€40k", "$30/hr". We normalize to an annual range in the stated currency.
No FX conversion is done (no paid API), so comparisons group by currency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_PERIOD_FACTORS = {
    "hourly": 2080.0, "hour": 2080.0,
    "daily": 260.0, "day": 260.0,
    "weekly": 52.0, "week": 52.0,
    "monthly": 12.0, "month": 12.0,
    "yearly": 1.0, "year": 1.0, "annual": 1.0,
}

_CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}
_CURRENCY_CODES = ("USD", "EUR", "GBP", "AUD", "CAD", "MXN", "COP", "BRL",
                   "ARS", "CLP", "PEN", "CHF", "INR")

_NUM = re.compile(r"(\d[\d.,]*)\s*([kK])?")


@dataclass
class SalaryInfo:
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "USD"
    period: str = "yearly"

    def _factor(self) -> float:
        return _PERIOD_FACTORS.get((self.period or "yearly").lower(), 1.0)

    def annual_min(self) -> Optional[float]:
        return self.min_amount * self._factor() if self.min_amount else None

    def annual_max(self) -> Optional[float]:
        return self.max_amount * self._factor() if self.max_amount else None

    def annual_midpoint(self) -> Optional[float]:
        lo, hi = self.annual_min(), self.annual_max()
        vals = [v for v in (lo, hi) if v]
        return sum(vals) / len(vals) if vals else None

    def format_annual(self) -> str:
        lo, hi = self.annual_min(), self.annual_max()
        if not lo and not hi:
            return ""
        if lo and hi and lo != hi:
            return f"{self.currency} {_k(lo)}–{_k(hi)}/yr"
        return f"{self.currency} {_k(hi or lo)}/yr"


def _k(amount: float) -> str:
    if amount >= 1000:
        return f"{amount / 1000:.0f}k"
    return f"{amount:.0f}"


def _detect_currency(text: str) -> str:
    upper = text.upper()
    for code in _CURRENCY_CODES:
        if re.search(rf"\b{code}\b", upper):
            return code
    for sym, code in _CURRENCY_SYMBOLS.items():
        if sym in text:
            return code
    return "USD"


def _detect_period(text: str) -> str:
    low = text.lower()
    if any(t in low for t in ("/hr", "per hour", "hour", "hora")):
        return "hourly"
    if any(t in low for t in ("/mo", "per month", "month", "mensual", "/mes")):
        return "monthly"
    if "week" in low or "semana" in low:
        return "weekly"
    if "/day" in low or "per day" in low:
        return "daily"
    return "yearly"


def _amount(num: str, suffix: str) -> float:
    value = float(num.replace(",", ""))
    if suffix:
        value *= 1000.0
    return value


def parse_salary_string(text: str) -> Optional[SalaryInfo]:
    """Best-effort parse of a free-form salary string into a SalaryInfo."""
    if not text or not text.strip():
        return None
    matches = _NUM.findall(text)
    amounts = [_amount(n, k) for n, k in matches if n.strip(".,")]
    amounts = [a for a in amounts if a >= 100]  # drop stray small numbers
    if not amounts:
        return None
    currency = _detect_currency(text)
    period = _detect_period(text)
    lo = min(amounts)
    hi = max(amounts)
    return SalaryInfo(min_amount=lo, max_amount=hi, currency=currency, period=period)
