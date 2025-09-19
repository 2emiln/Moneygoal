import math
from moneygoal.sim.monte_carlo import time_to_goal_mc

def test_mc_deterministic_matches_analytic():
    # Mål = 200 000. Start 100 000. Spar 2 000/mån. cagr=0, vol=0 ⇒ 50 månader.
    res = time_to_goal_mc(
        nuvarde=100_000, mean_monthly_contrib=2_000,
        cagr=0.0, vol=0.0, max_months=360, paths=100, seed=123,
        goal=200_000
    )
    assert 50 <= res["p50"] <= 52

def test_mc_reproducible_with_seed():
    r1 = time_to_goal_mc(100_000, 2_000, 0.06, 0.15, 600, 5000, seed=42, goal=1_000_000)
    r2 = time_to_goal_mc(100_000, 2_000, 0.06, 0.15, 600, 5000, seed=42, goal=1_000_000)
    assert r1 == r2

def test_mc_monotonic_contrib():
    r_lo = time_to_goal_mc(100_000, 1_000, 0.05, 0.10, 600, 3000, seed=7, goal=1_000_000)
    r_hi = time_to_goal_mc(100_000, 3_000, 0.05, 0.10, 600, 3000, seed=7, goal=1_000_000)
    assert r_hi["p50"] <= r_lo["p50"]
