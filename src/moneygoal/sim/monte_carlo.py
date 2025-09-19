from __future__ import annotations
import math
import random
from typing import Dict, Optional

def time_to_goal_mc(
    nuvarde: float,
    mean_monthly_contrib: float,
    cagr: float,
    vol: float,
    max_months: int,
    paths: int,
    goal: float,
    seed: Optional[int] = None,
) -> Dict[str, int]:
    """
    Returnerar {"p10": månader, "p50": månader, "p90": månader}.
    Modell: månadsfaktor ~ lognormal med
      sigma = vol / sqrt(12)
      mu = ln(1+CAGR)/12 - 0.5*sigma^2
    Om vol=0 används deterministisk månadsfaktor (1+CAGR)^(1/12).
    Stoppar bana när värde >= goal eller när max_months nåtts.
    """
    # --- validering ---
    if nuvarde < 0:
        raise ValueError("nuvarde måste vara ≥ 0")
    if mean_monthly_contrib < 0:
        raise ValueError("mean_monthly_contrib måste vara ≥ 0")
    if not (0.0 <= cagr <= 1.0):
        raise ValueError("cagr måste ligga i [0,1]")
    if vol < 0.0:
        raise ValueError("vol måste vara ≥ 0")
    if paths < 100:
        raise ValueError("paths måste vara ≥ 100")
    if max_months < 1:
        raise ValueError("max_months måste vara ≥ 1")
    if goal <= 0.0:
        raise ValueError("goal måste vara > 0")

    # snabbavslut
    if nuvarde >= goal:
        return {"p10": 0, "p50": 0, "p90": 0}

    rng = random.Random(seed)

    # --- simulering ---
    vals = []

    if vol <= 0.0:
        # deterministiskt scenario
        growth = (1.0 + cagr) ** (1.0 / 12.0) if cagr != 0.0 else 1.0
        for _ in range(paths):
            v = nuvarde
            m = 0
            while m < max_months and v < goal:
                v = v * growth + mean_monthly_contrib
                m += 1
            vals.append(m if v >= goal else max_months + 1)
    else:
        sigma = vol / (12.0 ** 0.5)
        mu = math.log(1.0 + cagr) / 12.0 - 0.5 * sigma * sigma
        for _ in range(paths):
            v = nuvarde
            m = 0
            while m < max_months and v < goal:
                z = rng.gauss(0.0, 1.0)  # N(0,1)
                factor = math.exp(mu + sigma * z)
                v = v * factor + mean_monthly_contrib
                m += 1
            vals.append(m if v >= goal else max_months + 1)

    vals.sort()

    def pct(p: int) -> int:
        # enkel percentil via index
        k = max(0, min(len(vals) - 1, int(round((p / 100.0) * (len(vals) - 1)))))
        return int(vals[k])

    return {"p10": pct(10), "p50": pct(50), "p90": pct(90)}
