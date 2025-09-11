# Moneygoal PoC

Beräknar tid till mål (P10/P50/P90) från två Avanza-CSV och ett målbelopp. Ingen extern data. Courtage exkluderas.

## Syfte
- Snabb PoC för simulering av tid till mål baserat på historik och månadsspar.
- Reproducerbarhet via seed och tydliga artefakter.

## Krav och avgränsning
**In-scope**
- Indata: `positions.csv`, `transactions.csv` (Avanza-export).
- Motor: MWRR/XIRR med bounds/fallback (`src/sparkalk/models/mwrr.py`).
- Monte Carlo: Student-t, konfigurerbar `paths`, `vol`, `seed`, `max_horizon_months`.
- UI: Streamlit med två filuppladdare + målbelopp.
- Tunn CLI.
- Artefakter: `result/time_to_goal_summary.csv`, `result/diagnostics.csv`, `logs/app.log`.
- ≥6 tester.

**Out-of-scope**
- Externa pris-API:er, andra filformat.
- Courtage och skatter.
- Deploy.

## Indata (datakontrakt)
**positions.csv**
- Separator `;`, decimalkomma.
- Kolumner inkluderar: **Marknadsvärde**, **Valuta**, **ISIN**.
- Facit: Nuvärde (summa Marknadsvärde) = **738 273,18 SEK**.

**transactions.csv**
- Separator `;`, 13 kolumner.
- Datumintervall: 2014-01-27 – 2025-08-07.
- `Belopp` med decimalkomma. 15 NaN i `Belopp` ignoreras (Övrigt 9, Värdepappersöverföring 6).
- Typer (antal): Köp 288, Sälj 256, Utdelning 103, Insättning 52, Uttag 18, Ränta 22, Övrigt 26, Värdepappersöverföring 6, Utländsk källskatt 51.
- Summeringar (SEK): Insättning +772 332,05; Uttag −363 546,05; Utdelning +150 424,25.

## Utdata
- `result/time_to_goal_summary.csv` — P10/P50/P90 i år och månader.
- `result/diagnostics.csv` — parametrar, sanity checks, checksums.
- `logs/app.log` — körloggar.

## Installation
```bash
# valfritt: skapa venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Körning
```bash
python -m sparkalk.cli \
  --positions data/positions.csv \
  --transactions data/transactions.csv \
  --goal 1000000 \
  --report result/time_to_goal_summary.csv

streamlit run app/main.py
```
