# ---------------------------------------------------------------
# Den här modulen extraherar och summerar "bidrag" till portföljen,
# definierat som insättningar (+) och uttag (−), per månad.
# Flöde:
#   1) prepare_contribution_rows: filtrerar transaktioner till
#      Insättning/Uttag, sätter tecken och skapar månadskolumn.
#   2) monthly_net_contributions: summerar netto per månad.
#   3) mean_monthly_contribution: tar medelvärde av månadssummorna.
# ---------------------------------------------------------------

import pandas as pd

CONTRIB_TYPES = {"Insättning", "Uttag"}

def prepare_contribution_rows(df_trx: pd.DataFrame) -> pd.DataFrame:
    
    """
    Filtrera till Insättning/Uttag, skapa teckensatt belopp och månadsnyckel.

    Varför behövs detta?
    - I råa transaktioner kan "Belopp" vara positivt/negativt beroende på export.
      Vi vill ha en entydig konvention: Insättning = +, Uttag = -.
    - Månadsnivå är praktisk för statistik (gruppering och medelvärde).

    Inputkrav:
        df_trx har kolumnerna: "Datum", "Typ", "Belopp".
        - "Datum" ska gå att tolkas som datum.
        - "Typ" ska innehålla "Insättning"/"Uttag" för relevanta rader.
        - "Belopp" ska gå att konvertera till float.

    Output:
        DataFrame med kolumner:
            - "Datum": pd.Timestamp
            - "Månad": "YYYY-MM" (sträng, enkel att gruppera på)
            - "Typ":   str
            - "Belopp_signed": float (Insättning +, Uttag -)
        Endast rader där Typ ∈ {"Insättning","Uttag"}.
    """
    # 1) Tom indata: returnera tom struktur med rätt kolumner och dtypes.
    if df_trx.empty:
        return df_trx.head(0).assign(Belopp_signed=pd.Series(dtype=float), Månad=pd.Series(dtype="period[M]"))
    
    # 2) Säkerställ obligatoriska kolumner finns.
    req = {"Datum","Typ","Belopp"}
    missing = req - set(df_trx.columns)
    if missing:
        raise KeyError(f"Saknar kolumner: {sorted(missing)}")

    # 3) Filtrera till endast Insättning/Uttag.
    out = df_trx[df_trx["Typ"].isin(CONTRIB_TYPES)].copy()

    # 4) Tvinga korrekta typer. Felaktiga format ger tidiga, tydliga fel.
    out["Datum"] = pd.to_datetime(out["Datum"])
    out["Belopp"] = out["Belopp"].astype(float)

    # 5) Sätt entydigt tecken:
    #    - Insättning → +|Belopp|
    #    - Uttag      → -|Belopp|
    sign = out["Typ"].map(lambda t: 1.0 if t == "Insättning" else -1.0)
    out["Belopp_signed"] = sign * out["Belopp"].abs()

    # 6) Skapa månadsnyckel som "YYYY-MM" för enkel gruppering.
    out["Månad"] = out["Datum"].dt.to_period("M").astype(str)

    # 7) Returnera en smal, ren tabell med bara det som behövs framåt.
    return out[["Datum","Månad","Typ","Belopp_signed"]]

def monthly_net_contributions(rows: pd.DataFrame) -> pd.Series:
    """
    Summera netto-bidrag per månad.

    Varför per månad?
    - Månadsnivån matchar vanligt sparbeteende och gör medelvärde tolkbart.

    Input:
        DataFrame från prepare_contribution_rows (kräver "Månad" och "Belopp_signed").

    Output:
        pd.Series med index = "YYYY-MM" och värde = summa Belopp_signed den månaden.
    """

    if rows.empty:
        return pd.Series(dtype=float)
    return rows.groupby("Månad", sort=True)["Belopp_signed"].sum()

def mean_monthly_contribution(rows: pd.DataFrame) -> float:
    """
    Beräkna medelvärdet av netto-bidrag per månad.

    Tolkning:
    - Ett robust genomsnitt över historiken. Påverkas av uttag lika mycket
      som av insättningar eftersom tecknen redan är normaliserade.

    Input:
        DataFrame från prepare_contribution_rows.

    Output:
        float: medel av månadsvis netto. Returnerar 0.0 vid avsaknad av data.
    """
    monthly = monthly_net_contributions(rows)
    return float(monthly.mean()) if not monthly.empty else 0.0
