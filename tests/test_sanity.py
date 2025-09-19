from moneygoal.sim.monte_carlo import time_to_goal_mc

def test_det_linear_matches_analytic():
    # 100k -> 200k med 2k/mån, cagr=0, vol=0 ⇒ exakt 50 mån
    r = time_to_goal_mc(100_000, 2_000, 0.0, 0.0, 360, 200, goal=200_000, seed=1)
    assert 49 <= r["p50"] <= 51

def test_goal_already_met_zero_months():
    r = time_to_goal_mc(1_000_000, 0, 0.0, 0.0, 360, 200, goal=1_000_000, seed=1)
    assert r == {"p10": 0, "p50": 0, "p90": 0}

def test_unreachable_without_growth_or_contrib():
    r = time_to_goal_mc(100_000, 0, 0.0, 0.0, 120, 200, goal=1_000_000, seed=1)
    assert r["p50"] > 120  # markerar “ej nått”

def test_seed_reproducible():
    r1 = time_to_goal_mc(100_000, 2_000, 0.06, 0.15, 600, 1000, goal=1_000_000, seed=42)
    r2 = time_to_goal_mc(100_000, 2_000, 0.06, 0.15, 600, 1000, goal=1_000_000, seed=42)
    assert r1 == r2
