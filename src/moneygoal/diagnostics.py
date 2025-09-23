import datetime as dt
import pandas as pd
from moneygoal.models.mwrr import xirr

def compute_xirr_from_frames(df_trx: pd.DataFrame, df_pos: pd.DataFrame) -> float:
    """
    Beräkna XIRR från två DataFrames:
      - df_trx: transaktioner (minst kolumnerna "Datum", "Typ", "Belopp")
      - df_pos: positioner (minst kolumnen "Marknadsvärde")

    Idé:
    1) Filtrera fram bara kassaflöden som faktiskt lämnar/kommer in i portföljen:
       "Insättning" och "Uttag".
    2) Sätt entydiga tecken för dessa:
       - Insättning = negativt (pengar IN i portföljen → utflöde för investeraren)
       - Uttag      = positivt (pengar UT från portföljen → inflöde till investeraren)
       Detta följer vanlig XIRR-konvention där startinsats är negativ och slutvärde positivt.
    3) Lägg till ett avslutande kassaflöde på dagens datum motsvarande nuvärdet
       (summa av Marknadsvärde). Detta representerar "försäljning idag".

    Skydd:
    - Kräver minst ett negativt och ett positivt flöde, annars kastas ValueError.
    """
    # 1) Ta bara insättningar/uttag
    df = df_trx[df_trx["Typ"].isin(["Insättning", "Uttag"])].copy()

    # 2) Normalisera tal och bygg tecken:
    #    - Belopp kan vara formaterat som text → gör numeriskt
    amt = pd.to_numeric(df["Belopp"]).abs()
    #    - Mappa transaktionstyp till tecken enligt XIRR-konventionen
    sign = df["Typ"].map({"Insättning": -1.0, "Uttag": 1.0})

    # 3) Bygg kassaflödeslista (datum, belopp)
    amounts = (sign.values * amt.values).tolist()
    dates = pd.to_datetime(df["Datum"]).dt.date.tolist()
    cfs = list(zip(dates, amounts))

    # 4) Lägg till nuvärdet som slutflöde idag
    ending_value = float(pd.to_numeric(df_pos["Marknadsvärde"]).sum())
    cfs.append((dt.date.today(), ending_value))

    # 5) Grundkrav: minst ett negativt och ett positivt flöde
    if not (any(a < 0 for _, a in cfs) and any(a > 0 for _, a in cfs)):
        raise ValueError("xirr kräver både negativa och positiva flöden")

    # 6) Beräkna XIRR
    return xirr(cfs)


def diagnostics_dict(df_trx: pd.DataFrame, df_pos: pd.DataFrame) -> dict:
    """
    Packa utvalda diagnosmått i en dict.
    Just nu endast XIRR, men utbyggbart med fler nycklar senare.
    """
    return {"xirr": compute_xirr_from_frames(df_trx, df_pos)}
