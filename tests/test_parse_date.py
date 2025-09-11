# tests/test_parse_date.py
import pytest
import pandas as pd
from moneygoal.io.avanza_csv import parse_date

def test_parse_date_basic():
    d = parse_date("2000-01-01")
    assert isinstance(d, pd.Timestamp)
    assert (d.year, d.month, d.day) == (2000, 1, 1)

def test_parse_date_invalid():
    with pytest.raises(ValueError):
        parse_date("01-01-2000")
