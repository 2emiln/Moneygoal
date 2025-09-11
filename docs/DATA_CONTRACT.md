# Data Contract
- positions.csv: sep `;`, decimalkomma; måste innehålla **Marknadsvärde**, **Valuta**, **ISIN**; inga `kr` eller tusentalsmellanrum; facit: ΣMarknadsvärde = **738 273,18 SEK**.
- transactions.csv: sep `;`, **13 kol**, datum **2014-01-27–2025-08-07**; `Belopp` med decimalkomma; **15 NaN i Belopp** ignoreras (Övrigt 9, VP-överf 6).
- Typer/summeringar: enligt README (räknas vid validering).
- Output: `result/time_to_goal_summary.csv`, `result/diagnostics.csv`; logg: `logs/app.log`.
