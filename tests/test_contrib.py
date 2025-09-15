import pandas as pd
from moneygoal.io.avanza_csv import parse_date
from moneygoal.contrib import prepare_contribution_rows, monthly_net_contributions, mean_monthly_contribution

def _trx(df):
    # helpers för att mata normalize_transactions-resultat-lik DF
    out = df.copy()
    out["Datum"] = out["Datum"].map(parse_date)
    return out

def test_contributions_signs():
    df = _trx(pd.DataFrame({
        "Datum": ["2025-01-15", "2025-01-20"],
        "Typ":   ["Insättning",  "Uttag"],
        "Belopp":[1000.0,        -200.0],
    }))
    rows = prepare_contribution_rows(df)
    assert set(rows["Typ"]) == {"Insättning","Uttag"}
    # Insättning ska vara positiv, Uttag negativ (oavsett originaltecken)
    assert rows.loc[rows["Typ"]=="Insättning","Belopp_signed"].item() == 1000.0
    assert rows.loc[rows["Typ"]=="Uttag","Belopp_signed"].item() == -200.0

def test_monthly_aggregation_and_mean():
    df = _trx(pd.DataFrame({
        "Datum": ["2025-01-10","2025-01-20","2025-02-05","2025-02-15"],
        "Typ":   ["Insättning","Uttag",     "Insättning","Uttag"],
        "Belopp":[2000.0,      -500.0,      1500.0,      -1000.0],
    }))
    rows = prepare_contribution_rows(df)
    monthly = monthly_net_contributions(rows)  # Serie per månad
    assert monthly.loc["2025-01"] == 1500.0    # 2000 - 500
    assert monthly.loc["2025-02"] == 500.0     # 1500 - 1000
    assert mean_monthly_contribution(rows) == 1000.0  # (1500+500)/2

def test_ignore_other_types():
    df = _trx(pd.DataFrame({
        "Datum": ["2025-01-01","2025-01-02","2025-01-03"],
        "Typ":   ["Köp","Sälj","Utdelning"],
        "Belopp":[-1000.0, 1200.0, 50.0],
    }))
    rows = prepare_contribution_rows(df)
    assert rows.empty
    assert mean_monthly_contribution(rows) == 0.0
