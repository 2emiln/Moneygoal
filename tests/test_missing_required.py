import pandas as pd
import pytest
from moneygoal.io.avanza_csv import normalize_transactions, normalize_positions

def test_transactions_missing_required_raises():
    # Saknar "Belopp" efter rename ("Typ av transaktion" -> "Typ")
    df = pd.DataFrame({
        "Datum": ["2000-01-01"],
        "Typ av transaktion": ["Insättning"],
        # "Belopp" saknas
    })
    with pytest.raises(KeyError):
        normalize_transactions(df)

def test_positions_missing_required_raises():
    # Saknar "Marknadsvärde"
    df = pd.DataFrame({
        "Valuta": ["SEK"],
        "ISIN": ["SE0012345678"],
    })
    with pytest.raises(KeyError):
        normalize_positions(df)
