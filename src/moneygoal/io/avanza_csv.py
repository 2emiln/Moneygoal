# -------------------------------------------------------------------
# Detta modulavsnitt innehåller funktioner för att läsa in och
# normalisera Avanzas CSV-filer (positions och transactions).
# Tanken är att:
#   - först läsa in all data som strängar,
#   - sedan konvertera till rätt datatyper (tal och datum),
#   - samt säkerställa att de kolumner vi förväntar oss finns.
# -------------------------------------------------------------------

from pathlib import Path
import pandas as pd


def parse_number(s: str) -> float:
    """
    Konvertera en sträng som innehåller ett svenskt formaterat tal till float.

    Steg:
    1. Gör om input till sträng och ta bort överflödiga mellanslag.
    2. Rensa bort NBSP (icke-brytande mellanslag) och vanliga mellanslag.
    3. Byt ut komma mot punkt (för att Python ska förstå decimaltal).
    4. Gör om resultatet till float.

    Exempel:
        "1 234,56" -> 1234.56
        "0,5"      -> 0.5
    """
    return float(
        str(s).strip()
              .replace("\u00A0", "")  # NBSP
              .replace(" ", "")
              .replace(",", ".")
    )

def parse_date(s: str) -> pd.Timestamp:
    """
    Konvertera en sträng på formatet YYYY-MM-DD till ett datumobjekt.

    Steg:
    1. Ta bort överflödiga mellanslag runt strängen.
    2. Använd pandas to_datetime med strikt format "%Y-%m-%d".
       - Om formatet inte stämmer kastas ett fel direkt.
    """
    s = str(s).strip()
    # strikt YYYY-MM-DD
    return pd.to_datetime(s, format="%Y-%m-%d")

#  normalisering av redan inlästa DataFrames
def normalize_positions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisera DataFrame som representerar positions.csv.

    Förväntade kolumner:
        - "Marknadsvärde"
        - "Valuta"
        - "ISIN"

    Steg:
    1. Kontrollera att alla dessa kolumner finns, annars kasta KeyError.
    2. Kopiera DataFrame (för att inte ändra originalet).
    3. Gör om kolumnen "Marknadsvärde" från text (svenskt format) till float.
    4. Returnera den normaliserade kopian.
    """

    req = {"Marknadsvärde", "Valuta", "ISIN"}
    missing = req - set(df.columns)
    if missing:
        raise KeyError(f"Saknar kolumner i positions: {sorted(missing)}")
    out = df.copy()
    out["Marknadsvärde"] = out["Marknadsvärde"].map(parse_number)
    return out

def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisera DataFrame som representerar transactions.csv.

    Viktigt:
    - Kolumnnamn kan variera, så vi byter ut:
        "Typ av transaktion" -> "Typ"
        "Värdepapper/beskrivning" -> "Beskrivning"

    Förväntade kolumner efter namnbytet:
        - "Datum"
        - "Typ"
        - "Belopp"

    Steg:
    1. Byt namn på kolumnerna till enhetliga rubriker.
    2. Kontrollera att de obligatoriska kolumnerna finns.
    3. Kopiera DataFrame.
    4. Gör om "Datum" till pd.Timestamp (med parse_date).
    5. Gör om "Belopp" till float (med parse_number).
    6. Returnera kopian.
    """

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
    """
    Läs in positions.csv från disk och normalisera den.

    Steg:
    1. Läs CSV som strängar (sep=";", dtype=str).
       - encoding="utf-8-sig" används för att hantera BOM om det finns.
    2. Skicka DataFrame vidare till normalize_positions().
    3. Returnera resultatet.
    """

    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig")
    return normalize_positions(df)

def read_transactions(path: str | Path) -> pd.DataFrame:
    """
    Läs in transactions.csv från disk och normalisera den.

    Steg:
    1. Läs CSV som strängar (sep=";", dtype=str).
       - encoding="utf-8-sig" används för att hantera BOM om det finns.
    2. Skicka DataFrame vidare till normalize_transactions().
    3. Returnera resultatet.
    """

    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8-sig")
    return normalize_transactions(df)
