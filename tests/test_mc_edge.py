import pytest
from moneygoal.sim.monte_carlo import time_to_goal_mc

def test_goal_already_reached():
    r = time_to_goal_mc(
        nuvarde=1_000_000, mean_monthly_contrib=0, cagr=0.0, vol=0.0,
        max_months=360, paths=1000, goal=1_000_000, seed=1
    )
    assert r == {"p10": 0, "p50": 0, "p90": 0}

def test_zero_contrib_zero_growth_unreachable():
    r = time_to_goal_mc(
        nuvarde=100_000, mean_monthly_contrib=0, cagr=0.0, vol=0.0,
        max_months=120, paths=500, goal=1_000_000, seed=2
    )
    # når ej målet → funktion returnerar max_months+1 i varje bana → percentiler > max_months
    assert r["p50"] > 120

def test_input_validation():
    with pytest.raises(ValueError):  # negativt nuvärde
        time_to_goal_mc(-1, 100, 0.05, 0.1, 360, 1000, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # negativt månadsspar
        time_to_goal_mc(0, -10, 0.05, 0.1, 360, 1000, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # cagr utanför [0,1]
        time_to_goal_mc(0, 0, 1.5, 0.1, 360, 1000, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # negativ vol
        time_to_goal_mc(0, 0, 0.05, -0.1, 360, 1000, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # för få paths
        time_to_goal_mc(0, 0, 0.05, 0.1, 360, 10, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # max_months < 1
        time_to_goal_mc(0, 0, 0.05, 0.1, 0, 1000, goal=1_000_000, seed=3)
    with pytest.raises(ValueError):  # goal <= 0
        time_to_goal_mc(0, 0, 0.05, 0.1, 360, 1000, goal=0, seed=3)

def test_monotonic_cagr():
    r_low = time_to_goal_mc(
        nuvarde=100_000, mean_monthly_contrib=2_000, cagr=0.03, vol=0.15,
        max_months=600, paths=4000, goal=1_000_000, seed=7
    )
    r_high = time_to_goal_mc(
        nuvarde=100_000, mean_monthly_contrib=2_000, cagr=0.06, vol=0.15,
        max_months=600, paths=4000, goal=1_000_000, seed=7
    )
    assert r_high["p50"] <= r_low["p50"]
