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
