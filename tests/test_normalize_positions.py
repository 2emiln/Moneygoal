import pandas as pd
from moneygoal.io.avanza_csv import normalize_positions

def test_normalize_positions_schema_typ():
    df = pd.DataFrame({
        "Kontonummer":["9552-3028640"],
        "Namn":["SBB Norden D"],
        "Kortnamn":["SBB D"],
        "Volym":[4000],
        "Marknadsvärde":["31800,00"],
        "GAV (SEK)":["22,65"],
        "GAV":["22,65"],
        "Valuta":["SEK"],
        "Land":["SE"],
        "ISIN":["SE0011844091"],
        "Marknad":["XSTO"],
        "Typ":["STOCK"],
    })
    out = normalize_positions(df)
    assert {"Marknadsvärde","Valuta","ISIN"}.issubset(out.columns)
    assert pd.api.types.is_float_dtype(out["Marknadsvärde"])
