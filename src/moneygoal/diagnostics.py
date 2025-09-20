import datetime as dt
import pandas as pd
from moneygoal.models.mwrr import xirr

def compute_xirr_from_frames(df_trx: pd.DataFrame, df_pos: pd.DataFrame) -> float:
    df = df_trx[df_trx["Typ"].isin(["Insättning", "Uttag"])].copy()
    amt = pd.to_numeric(df["Belopp"]).abs()
    sign = df["Typ"].map({"Insättning": -1.0, "Uttag": 1.0})
    amounts = (sign.values * amt.values).tolist()
    dates = pd.to_datetime(df["Datum"]).dt.date.tolist()
    cfs = list(zip(dates, amounts))
    cfs.append((dt.date.today(), float(pd.to_numeric(df_pos["Marknadsvärde"]).sum())))

    # kontroll: kräver minst ett negativt och ett positivt
    if not (any(a < 0 for _, a in cfs) and any(a > 0 for _, a in cfs)):
        raise ValueError("xirr kräver både negativa och positiva flöden")
    return xirr(cfs)


def diagnostics_dict(df_trx: pd.DataFrame, df_pos: pd.DataFrame) -> dict:
    return {"xirr": compute_xirr_from_frames(df_trx, df_pos)}
