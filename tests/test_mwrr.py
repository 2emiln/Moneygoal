import pandas as pd
from moneygoal.models.mwrr import xirr

def test_xirr_två_flöden_10pct():
    cf = [
        ("2020-01-01", -1000.0),
        ("2021-01-01",  1100.0),
    ]
    r = xirr(cf)
    assert abs(r - 0.10) < 1e-3  # ~10%

def test_xirr_månadsinsättningar():
    # 12 månader á 100, slutvärde 1300 ett år efter start
    dates = pd.date_range("2020-01-01", periods=12, freq="MS")
    cf = [(str(d.date()), -100.0) for d in dates]
    cf.append(("2021-01-01", 1300.0))
    r = xirr(cf)
    assert 0.05 < r < 0.25  # grovt intervall, robust mot små skillnader
