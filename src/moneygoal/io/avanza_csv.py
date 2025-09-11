
from pathlib import Path
import pandas as pd


def parse_number(s: str) -> float:
    return float(
        str(s).strip()
              .replace("\u00A0", "")  # NBSP
              .replace(" ", "")
              .replace(",", ".")
    )

def parse_date(s: str) -> pd.Timestamp:
    s = str(s).strip()
    # strikt YYYY-MM-DD
    return pd.to_datetime(s, format="%Y-%m-%d")

#  normalisering av redan inlästa DataFrames
def normalize_positions(df: pd.DataFrame) -> pd.DataFrame:
    req = {"Marknadsvärde", "Valuta", "ISIN"}
    missing = req - set(df.columns)
    if missing:
        raise KeyError(f"Saknar kolumner i positions: {sorted(missing)}")
    out = df.copy()
    out["Marknadsvärde"] = out["Marknadsvärde"].map(parse_number)
    return out

def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns={
        "Typ av transaktion": "Typ",
        "Värdepapper/beskrivning": "Beskrivning",
    }).copy()
    req = {"Datum", "Typ", "Belopp"}
    missing = req - set(out.columns)
    if missing:
        raise KeyError(f"Saknar kolumner i transactions: {sorted(missing)}")
    out["Datum"] = out["Datum"].map(parse_date)
    out["Belopp"] = out["Belopp"].map(parse_number)
    return out

# tunna IO-wrappers (CSV -> normalize_*) 
def read_positions(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig")
    return normalize_positions(df)

def read_transactions(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig")
    return normalize_transactions(df)
