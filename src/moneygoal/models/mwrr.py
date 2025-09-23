# -------------------------------------------------------------------
# Dagräkning ACT/ACT (ISDA)
# Idé: Andelen av ett år beräknas genom att räkna verkliga dagar och
# dela med årets faktiska längd (365 eller 366). Om perioden spänner
# över flera år delas den upp i: första delår, hela mellanår, sista delår.
# Referens: ISDA 2006 Definitions.
# -------------------------------------------------------------------

from __future__ import annotations
import datetime as dt
from typing import Iterable, Tuple, List

DateAmount = Tuple[dt.date, float]
__all__ = ["xirr"]

def _is_leap(y: int) -> bool:
    """Skottårsregel: vart 4:e år, ej sekelskifte, utom vart 400:e."""
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def _yearfrac_act_act_isda(t0: dt.date, t1: dt.date) -> float:
    """Årsfraktion enligt ACT/ACT (ISDA). Hanterar också t1 < t0."""
    if t1 == t0:
        return 0.0
    
    # Omvänd intervallordning: byt plats och kom ihåg tecknet.
    sign = 1.0
    if t1 < t0:
        t0, t1 = t1, t0
        sign = -1.0

    # Fall A: båda datumen ligger samma år → enkel kvot.
    year_end0 = dt.date(t0.year, 12, 31)
    denom0 = 366.0 if _is_leap(t0.year) else 365.0
    if t1.year == t0.year:
        return sign * ((t1 - t0).days / denom0)

    # Fall B: period över flera år.
    # 1) Första delåret: t0 → 31 dec (inklusive 31 dec enligt ISDA)
    frac = ((year_end0 - t0).days + 1) / denom0  # +1: inkluderar 31 dec (ISDA)

    # 2) Hela mellanår: varje helt år bidrar med exakt 1.0.
    for y in range(t0.year + 1, t1.year):
        frac += 1.0

    # 3) Sista delåret: 1 jan → t1, med årslängd för t1.year.
    year_start1 = dt.date(t1.year, 1, 1)
    denom1 = 366.0 if _is_leap(t1.year) else 365.0
    frac += (t1 - year_start1).days / denom1
    return sign * frac


def _years(t0: dt.date, t: dt.date) -> float:
    """Hjälpare: samma som _yearfrac_act_act_isda men med tydligare namn i NPV."""
    return _yearfrac_act_act_isda(t0, t)

# -------------------------------------------------------------------
# NPV och XIRR
# NPV: Diskontera varje kassaflöde med (1+r)^(årsfraktion från t0).
# XIRR: Hitta r som gör NPV ~ 0. Vi använder bisektion:
#   1) Skapa ett intervall [lo, hi] där NPV byter tecken.
#   2) Dela intervallet upprepade gånger tills precisionen är bra nog.
# Bisektion är robust men kan kräva att intervallet först "expanderas".
# -------------------------------------------------------------------

def _npv(rate: float, cfs: List[DateAmount]) -> float:
    """Nuvärde vid given ränta för daterade flöden. t0 = första datumet."""
    t0 = cfs[0][0]
    return sum(a / (1.0 + rate) ** _years(t0, d) for d, a in cfs)

def xirr(cashflows: Iterable[DateAmount]) -> float:
    """
    Beräkna årlig internränta (XIRR) för daterade kassaflöden.

    Krav:
        - Minst ett negativt och ett positivt flöde (annars saknas rot).
        - Datum i valfri ordning; sorteras internt stigande.

    Algoritm:
        1) Sortera flödena.
        2) Bygg ett startintervall [lo, hi] med teckenväxling i NPV.
           Starta med lo ≈ -1 och hi = 10.0. Expandera vid behov.
        3) Kör bisektion tills NPV nära 0 eller intervallet är litet.
        4) Om ingen teckenväxling hittas trots expansion:
           returnera den av lo/hi som ger lägst |NPV| (fallback).

    Precision:
        - Avbryter när |NPV| < 1e-12 eller intervallbredd < 1e-12.

    Obs:
        - lo kan inte gå ≤ -1 eftersom (1+rate) måste vara > 0.
        - Mycket extrema flöden kan ge orimligt stor hi; expansion bryts
          efter fast antal steg av robusthetsskäl.
    """
    # 1) Sortera och validera teckenblandning.

    cfs = sorted(list(cashflows), key=lambda x: x[0])
    if not (any(a < 0 for _, a in cfs) and any(a > 0 for _, a in cfs)):
        raise ValueError("xirr kräver både negativa och positiva flöden")

    # 2) Startintervall. lo nära -1 (men > -1), hi moderat hög.
    lo, hi = -0.999999, 10.0
    f_lo, f_hi = _npv(lo, cfs), _npv(hi, cfs)

    # 2a) Om ingen teckenväxling: expandera hi uppåt.
    if f_lo * f_hi > 0:
        for _ in range(60):
            hi *= 1.5
            f_hi = _npv(hi, cfs)
            if f_lo * f_hi <= 0:
                break

    # 2b) Fortfarande ingen teckenväxling: flytta lo närmare -1.
    if f_lo * f_hi > 0:
        for _ in range(60):
            # Transform som sänker lo men håller det > -1
            lo = (lo - 1.0) * 1.5 + 1.0  # går mot -inf men > -1
            if lo <= -0.9999999:
                lo = -0.9999999
            f_lo = _npv(lo, cfs)
            if f_lo * f_hi <= 0:
                break

    # 3) Sista kontroll: om fortfarande ingen rot inom [lo, hi] → fallback.
    if f_lo * f_hi > 0:
        # fallback: returnera den av lo/hi som ger lägst |NPV|
        return lo if abs(f_lo) < abs(f_hi) else hi

    # 4) Bisektion: halvera intervallet tills precision uppnås.
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, cfs)
        # Avbryt på tillräcklig NPV-noggrannhet eller litet intervall.
        if abs(f_mid) < 1e-12 or (hi - lo) < 1e-12:
            return mid
        # Behåll delintervall som innehåller teckenväxling.
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    # 5) Nödutgång om loopen nådde iterationsgränsen.
    return (lo + hi) / 2.0
