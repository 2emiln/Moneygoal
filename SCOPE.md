# Scope: Moneygoal PoC (11–23 sep 2025)

## Mål
Beräkna tid till mål (P10/P50/P90) från två Avanza-CSV + målbelopp.

## In-scope
- Indata: `positions.csv`, `transactions.csv` (Avanza export).
- Motor: MWRR/XIRR med bounds/fallback (`models/mwrr.py`).
- Monte Carlo: Student-t, seed, vol, maxhorisont.
- UI: Streamlit med 2 filuppladdare + målbelopp. Tunn CLI.
- Artefakter: `result/time_to_goal_summary.csv`, `result/diagnostics.csv`, `logs/app.log`.
- ≥6 tester: parsing, contributions, mwrr, MC determinism, e2e, validering.

## Out-of-scope
- Extern prisdata/APIs. 
- Andra filformat än Avanza-CSV.
- Courtage och skatter i beräkningar.
- Live-deploy.

## Indata/Utdata (kontrakt, sammanfattning)
- `positions.csv`: sep `;`, decimalkomma, kolumn “Marknadsvärde”, “Valuta”, “ISIN”.
- `transactions.csv`: sep `;`, 2014-01-27–2025-08-07, 13 kolumner, 15 NaN i “Belopp” ignoreras.
- Utdata: två CSV ovan + loggfil.

## Policy & begränsningar
- Ingen extern data. Courtage exkluderas. Reproducerbarhet med seed.

## Antaganden
- Filer är kompletta Avanza-exporter och läsbara.

## Definition of Done
- Alla tester gröna. Streamlit kör end-to-end och genererar utdata.
- README + Assumptions klara. Issues stängda med länk till tester.

## Spårbarhet
- Krav→issues: #1 Parser, #2 Contributions, #3 mwrr, #4 MC, #5 CLI, #6 UI, #7 Felhantering, #8 README.
- Issue→tester: test_* filer namnges därefter.

## Risker
- Felaktiga CSV-format; åtgärd: strikt validering och tydliga fel.
