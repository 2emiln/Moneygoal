from __future__ import annotations
import datetime as dt
from typing import Iterable, Tuple, List

DateAmount = Tuple[dt.date, float]
__all__ = ["xirr"]

# --- Dagräkning: ACT/ACT (ISDA) ------------------------------------------------
def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def _yearfrac_act_act_isda(t0: dt.date, t1: dt.date) -> float:
    if t1 == t0:
        return 0.0
    sign = 1.0
    if t1 < t0:
        t0, t1 = t1, t0
        sign = -1.0

    # första delåret
    year_end0 = dt.date(t0.year, 12, 31)
    denom0 = 366.0 if _is_leap(t0.year) else 365.0
    if t1.year == t0.year:
        return sign * ((t1 - t0).days / denom0)

    frac = ((year_end0 - t0).days + 1) / denom0  # +1: inkluderar 31 dec (ISDA)

    # hela mellanår
    for y in range(t0.year + 1, t1.year):
        frac += 1.0

    # sista delåret
    year_start1 = dt.date(t1.year, 1, 1)
    denom1 = 366.0 if _is_leap(t1.year) else 365.0
    frac += (t1 - year_start1).days / denom1
    return sign * frac

def _years(t0: dt.date, t: dt.date) -> float:
    return _yearfrac_act_act_isda(t0, t)

# --- NPV och XIRR ----------------------------------------------------------------
def _npv(rate: float, cfs: List[DateAmount]) -> float:
    t0 = cfs[0][0]
    return sum(a / (1.0 + rate) ** _years(t0, d) for d, a in cfs)

def xirr(cashflows: Iterable[DateAmount]) -> float:
    """
    Årlig internränta för daterade kassaflöden.
    Kräver minst ett negativt och ett positivt flöde.
    """
    cfs = sorted(list(cashflows), key=lambda x: x[0])
    if not (any(a < 0 for _, a in cfs) and any(a > 0 for _, a in cfs)):
        raise ValueError("xirr kräver både negativa och positiva flöden")

    # Bisektion på [lo, hi] där f(lo)*f(hi) <= 0
    lo, hi = -0.999999, 10.0
    f_lo, f_hi = _npv(lo, cfs), _npv(hi, cfs)
    if f_lo * f_hi > 0:
        # expandera hi tills teckenväxling hittas eller ge upp
        for _ in range(60):
            hi *= 1.5
            f_hi = _npv(hi, cfs)
            if f_lo * f_hi <= 0:
                break

    # Om fortfarande ingen teckenväxling: försök sänka lo
    if f_lo * f_hi > 0:
        for _ in range(60):
            lo = (lo - 1.0) * 1.5 + 1.0  # går mot -inf men > -1
            if lo <= -0.9999999:
                lo = -0.9999999
            f_lo = _npv(lo, cfs)
            if f_lo * f_hi <= 0:
                break

    # Sista kontroll
    if f_lo * f_hi > 0:
        # fallback: returnera den av lo/hi som ger lägst |NPV|
        return lo if abs(f_lo) < abs(f_hi) else hi

    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, cfs)
        if abs(f_mid) < 1e-12 or (hi - lo) < 1e-12:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0
