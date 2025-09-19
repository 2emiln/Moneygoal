import datetime as dt
from moneygoal.models.mwrr import xirr

def test_xirr_one_period_10pct():
    cfs = [(dt.date(2020,1,1), -1000.0),
           (dt.date(2021,1,1),  1100.0)]
    r = xirr(cfs)
    assert abs(r - 0.10) < 1e-6

def test_xirr_multiple_flows_stable():
    cfs = [(dt.date(2020,1,1), -1000.0),
           (dt.date(2020,6,1),  -500.0),
           (dt.date(2021,1,1),   300.0),
           (dt.date(2022,1,1),  1500.0)]
    r = xirr(cfs)
    assert -0.5 < r < 0.5
