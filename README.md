# Moneygoal PoC (WIP)

Beräknar tid till mål (P10/P50/P90) från två Avanza-CSV och ett målbelopp. Ingen extern data. Courtage exkluderas.

## Indata
Lägg användarens filer och standardisera namnen:
- `data/raw/positions/positions.csv`
- `data/raw/transactions/transactions.csv`

## Körning
```bash
python -m moneygoal.cli \
  --positions data/raw/positions/positions.csv \
  --transactions data/raw/transactions/transactions.csv \
  --goal 1000000 \
  --report result/time_to_goal_summary.csv

## CLI
Exempel:
python -m moneygoal.cli ^
  --positions data/raw/positions/positions.csv ^
  --transactions data/raw/transactions/transactions.csv ^
  --goal 1000000 ^
  --paths 5000 --vol 0.15 --cagr 0.06 --seed 42 --maxhorisont 600 ^
  --report result/time_to_goal_summary.csv

Output:
- result/time_to_goal_summary.csv  (P10/P50/P90 i år+mån)
- result/diagnostics.csv           (xirr, parametrar, p10/p50/p90, asof)