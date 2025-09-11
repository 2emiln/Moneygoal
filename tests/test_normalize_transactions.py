import pandas as pd
from moneygoal.io.avanza_csv import normalize_transactions

def test_normalize_transactions_schema_typ():
    df = pd.DataFrame({
        "Datum":["2025-08-07","2025-08-04"],
        "Konto":["Utdelningsportföljen","Utdelningsportföljen"],
        "Typ av transaktion":["Insättning","Utdelning"],
        "Värdepapper/beskrivning":["Överföring","AT&T"],
        "Antal":[None,200],
        "Kurs":[None,"0,2775"],
        "Belopp":["25000","534,81"],
        "Transaktionsvaluta":["SEK","SEK"],
        "Courtage":[None,None],
        "Valutakurs":["1","1"],
        "Instrumentvaluta":[None,"USD"],
        "ISIN":[None,"US00206R1023"],
        "Resultat":[None,None],
    })
    out = normalize_transactions(df)
    assert {"Datum","Typ","Belopp"}.issubset(out.columns)
    assert pd.api.types.is_datetime64_any_dtype(out["Datum"])
    assert pd.api.types.is_float_dtype(out["Belopp"])
