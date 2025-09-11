# Moneygoal PoC

Beräknar tid till mål (P10/P50/P90) från två Avanza-CSV och ett målbelopp. Ingen extern data. Courtage exkluderas.

## Syfte
Snabb PoC som kör lokalt, läser `positions.csv` och `transactions.csv`, och skriver ut P10/P50/P90 för tid till mål. Reproducerbar via seed och loggar.

## Krav och avgränsning
**In-scope**
- Indata: `positions.csv`, `transactions.csv` (Avanza-export).
- Motor: MWRR/XIRR med bounds/fallback (`src/moneygoal/models/mwrr.py`).
- Monte Carlo: Student-t; parametrar `paths`, `vol`, `seed`, `max_horizon_months`.
- UI: Streamlit med två filuppladdare + målbelopp.
- Tunn CLI.
- Artefakter: `result/time_to_goal_summary.csv`, `result/diagnostics.csv`, `logs/app.log`.
- ≥6 tester.

**Out-of-scope**
- Externa pris-API:er, andra filformat.
- Courtage/skatter i beräkningar.
- Deploy.

## Indata (datakontrakt)
**positions.csv**
- Separator `;`, decimalkomma.
- Kolumner inkluderar: **Marknadsvärde**, **Valuta**, **ISIN**.
- Facit: Summa **Marknadsvärde** = **738 273,18 SEK**.

**transactions.csv**
- Separator `;`, 13 kolumner.
- Datumintervall: **2014-01-27 – 2025-08-07**.
- `Belopp` med decimalkomma. **15 NaN** i `Belopp` ignoreras (Övrigt 9, Värdepappersöverföring 6).
- Typer (antal): Köp 288, Sälj 256, Utdelning 103, Insättning 52, Uttag 18, Ränta 22, Övrigt 26, Värdepappersöverföring 6, Utländsk källskatt 51.
- Summeringar (SEK): Insättning **+772 332,05**; Uttag **−363 546,05**; Utdelning **+150 424,25**.

## Utdata
- `result/time_to_goal_summary.csv` — P10/P50/P90 i år och månader.
- `result/diagnostics.csv` — parametrar, sanity checks, checksums.
- `logs/app.log` — körloggar.

## Installation
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt
```

## Körning
```bash
# CLI (tunn)
python -m moneygoal.cli   --positions data/raw/positions.csv   --transactions data/raw/transactions.csv   --goal 1000000   --report result/time_to_goal_summary.csv

# Streamlit-UI
streamlit run app/main.py
```

## Parametrar (default)
- `paths=5000` — antal simuleringar
- `vol=0.04` — antagen månadsvolatilitet
- `seed=42` — slumpfrö
- `max_horizon_months=360` — max simlängd
- `reinvest_dividends=false` — återinvestera utdelningar
- `cagr_choice="historik"` — antagande för CAGR om använt

Ändras via CLI-flaggor eller i UI.

## Metod (kort)
- MWRR/XIRR för kassaflöden med numerisk lösare, bounds och fallback.
- Monte Carlo med Student-t för månadsavkastning.
- Månadsspar = historiskt snitt över hela perioden.
- Ingen extern prisdata. Courtage exkluderas.

## Tester
Kör alla tester:
```bash
pytest -q
```
Täcker: parsing (`parse_date`, `parse_number`, schema), contributions (tecken och månadssummering), MWRR (konvergens/fallback), MC (determinism med seed), e2e-smoke (skapar utdata), valideringsfel (saknade kolumner).

## Projektstruktur
```
src/moneygoal/
  __init__.py
  cli.py
  io/
    __init__.py
    avanza_csv.py
  models/
    __init__.py
    mwrr.py
  sim/
    __init__.py
    monte_carlo.py
app/
  main.py
tests/
data/
  raw/
  processed/
result/
logs/
```

## Snabbstart
1. Lägg `data/raw/positions.csv` och `data/raw/transactions.csv` på plats.
2. Kör CLI-kommandot ovan.
3. Öppna `result/time_to_goal_summary.csv` och läs av P10/P50/P90.

## Kända begränsningar
Endast Avanza-CSV. Ingen skatt/courtagemodell. Ingen deploy. Ingen extern prisdata.

## Licens
MIT (eller valfritt).
