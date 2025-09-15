import pandas as pd

CONTRIB_TYPES = {"Insättning", "Uttag"}

def prepare_contribution_rows(df_trx: pd.DataFrame) -> pd.DataFrame:
    """Filtrera till Insättning/Uttag, skapa Belopp_signed och Månad (YYYY-MM)."""
    if df_trx.empty:
        return df_trx.head(0).assign(Belopp_signed=pd.Series(dtype=float), Månad=pd.Series(dtype="period[M]"))
    req = {"Datum","Typ","Belopp"}
    missing = req - set(df_trx.columns)
    if missing:
        raise KeyError(f"Saknar kolumner: {sorted(missing)}")

    out = df_trx[df_trx["Typ"].isin(CONTRIB_TYPES)].copy()

    # Säkerställ typer
    out["Datum"] = pd.to_datetime(out["Datum"])
    out["Belopp"] = out["Belopp"].astype(float)

    # Sign-logik: Insättning positiv, Uttag negativ oavsett indata
    sign = out["Typ"].map(lambda t: 1.0 if t == "Insättning" else -1.0)
    out["Belopp_signed"] = sign * out["Belopp"].abs()

    # Månad som YYYY-MM sträng (enkelt att gruppera på)
    out["Månad"] = out["Datum"].dt.to_period("M").astype(str)

    return out[["Datum","Månad","Typ","Belopp_signed"]]

def monthly_net_contributions(rows: pd.DataFrame) -> pd.Series:
    """Summa per månad av Belopp_signed. Returnerar pd.Series index=YYYY-MM."""
    if rows.empty:
        return pd.Series(dtype=float)
    return rows.groupby("Månad", sort=True)["Belopp_signed"].sum()

def mean_monthly_contribution(rows: pd.DataFrame) -> float:
    """Medel av månatligt netto. 0.0 om tomt."""
    monthly = monthly_net_contributions(rows)
    return float(monthly.mean()) if not monthly.empty else 0.0
