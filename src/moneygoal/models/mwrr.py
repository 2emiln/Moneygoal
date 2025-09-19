# src/moneygoal/models/mwrr.py
from __future__ import annotations
from datetime import datetime
from typing import Iterable, Tuple, Union

DateLike = Union[str, datetime]

def _to_dt(d: DateLike) -> datetime:
    return d if isinstance(d, datetime) else datetime.fromisoformat(str(d))

def _year_frac(d0: datetime, d1: datetime) -> float:
    return (d1 - d0).days / 365.2425  # enkel ACT/365.2425

def xnpv(rate: float, cashflows: Iterable[Tuple[DateLike, float]]) -> float:
    cfs = [( _to_dt(d), v ) for d, v in cashflows]
    t0 = min(d for d, _ in cfs)
    total = 0.0
    for d, v in cfs:
        t = _year_frac(t0, d)
        total += v / ((1.0 + rate) ** t)
    return total

def xirr(cashflows: Iterable[Tuple[DateLike, float]],
         bounds: Tuple[float, float] = (-0.99, 1.0),
         tol: float = 1e-6,
         maxiter: int = 200) -> float:
    # bisection, med enkel upp-bracketing av övre gränsen vid behov
    a, b = bounds
    fa = xnpv(a, cashflows)
    fb = xnpv(b, cashflows)

    # om ingen teckenväxling, skala upp b tills teckenväxling eller tak
    scale = 2.0
    tries = 0
    while fa * fb > 0 and b < 100.0 and tries < 20:
        b *= scale
        fb = xnpv(b, cashflows)
        tries += 1

    if fa * fb > 0:
        # sista försök: sänk a lite närmare -1
        a = -0.999
        fa = xnpv(a, cashflows)
        if fa * fb > 0:
            raise ValueError("Hittar ingen rot i rimligt intervall")

    # bisektion
    for _ in range(maxiter):
        m = 0.5 * (a + b)
        fm = xnpv(m, cashflows)
        if abs(fm) < tol or abs(b - a) < tol:
            return m
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)
