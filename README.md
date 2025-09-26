# Moneygoal

Avanza‑CSV → tid till mål med Monte Carlo (P10/P50/P90) och XIRR (MWRR). Ingen extern marknadsdata.

## Innehåll

- [Översikt](#översikt)
- [Funktioner](#funktioner)
- [Installation](#installation)
- [Dataformat (Avanza‑CSV)](#dataformat-avanza-csv)
- [Struktur](#struktur)
- [Körning: CLI](#körning-cli)
- [Körning: Streamlit‑UI](#körning-streamlit-ui)
- [Utdatafiler](#utdatafiler)
- [Sanity‑checks](#sanity-checks)
- [Fil‑för‑fil (detalj)](#fil-för-fil-detalj)
- [Begränsningar](#begränsningar)
- [Roadmap](#roadmap)

## Översikt

Projektet räknar:

- **Tid till mål**: P10/P50/P90 i månader via Monte Carlo, givet nuvärde (V0), snittligt månadsspar och antaganden om CAGR/volatilitet.
- **XIRR (MWRR)**: pengar‑viktad årsavkastning från transaktioner + terminalt portföljvärde.

All logik är deterministisk vid `vol=0, cagr=0` för enkel sanity.

## Funktioner

- Läser Avanza‑exporter (`positions.csv`, `transactions.csv`).
- Normalisering av tal och datum (svenskt CSV).
- Contributions‑motor → snittligt månadsspar.
- Monte Carlo: lognormal månadsmodell, percentiler som månader.
- Diagnostics: XIRR med ACT/ACT (ISDA) och bisektion.
- CLI med tydliga flaggor, exit‑koder och logg.
- Streamlit‑UI som speglar CLI.

## Installation

```bash
pip install -e .
```

Kräver Python ≥ 3.11.

## Dataformat (Avanza‑CSV)

- Separator `;`, decimal `,`, encoding `utf-8-sig`.
- **positions.csv** måste innehålla: `Marknadsvärde`, `Valuta`, `ISIN`.
- **transactions.csv** måste innehålla: `Datum`, `Typ`, `Belopp`.
- Stödda typer i contributions: `Insättning`, `Uttag`. (Utdelning ignoreras i v1.)

## Struktur

```
src/moneygoal/
  io/avanza_csv.py       # CSV-inläsning och normalisering
  contrib.py             # Insättning/Uttag → månadsnetto och medel
  models/mwrr.py         # XIRR (ACT/ACT ISDA, bisektion)
  diagnostics.py         # Bygger kassaflöden och räknar XIRR
  sim/monte_carlo.py     # Tid-till-mål via Monte Carlo
  cli.py                 # Kommandoradsgränssnitt
app/app.py               # Streamlit-UI
result/                  # CSV-utdata
logs/                    # Loggar
```

## Körning: CLI

```bash
python -m moneygoal.cli \
  --positions data/raw/positions/positions.csv \
  --transactions data/raw/transactions/transactions.csv \
  --goal 1000000 \
  --report result/time_to_goal_summary.csv \
  --paths 5000 --vol 0.15 --cagr 0.06 --seed 42 --maxhorisont 600
```

- Konsol: `P10: X år Y mån | P50: ... | P90: ...`
- Exit‑koder: `0=OK`, `1=fel under körning`, `2=ogiltiga argument`.

## Körning: Streamlit‑UI

```bash
streamlit run app/app.py
```

1. Ladda upp båda CSV. 2) Ange mål och parametrar. 3) Klicka **Kör**. UI visar P10/P50/P90 och XIRR. Länkar för nedladdning av `result/*.csv`.

## Utdatafiler

- `result/time_to_goal_summary.csv`: `percentile, years, months`.
- `result/diagnostics.csv`: append‑logg med kolumner: `asof, stage, V0, goal, mean_monthly_contrib, paths, vol, cagr, seed, maxhorisont, p10_months, p50_months, p90_months, xirr, positions_path, transactions_path`.
- `logs/app.log`: körparametrar och status.

## Sanity‑checks

- Deterministiskt (`vol=0, cagr=0`): \(\text{mån} \approx \lceil (\text{goal} − V0)/\text{mmc} \rceil\)
- `V0 ≥ goal` ⇒ `P10=P50=P90=0`.
- XIRR: Insättning < 0, Uttag > 0, terminalt värde > 0 (idag). Dagräkning ACT/ACT (ISDA).

## Fil‑för‑fil (detalj)

### `src/moneygoal/io/avanza_csv.py`

**Syfte**: Läsa Avanza‑CSV och normalisera värden.

**Funktioner**

- `parse_number(s: str) -> float`\
  Tar bort NBSP/blanksteg, byter `,`→`.` och kastar till `float`.
- `parse_date(s: str) -> pd.Timestamp`\
  Strikt `YYYY-MM-DD` via `pd.to_datetime(..., format=...)`.
- `normalize_positions(df: pd.DataFrame) -> pd.DataFrame`\
  Validerar kolumner `{Marknadsvärde, Valuta, ISIN}` och mappar `Marknadsvärde` till `float`.
- `normalize_transactions(df: pd.DataFrame) -> pd.DataFrame`\
  Standardiserar kolumnnamn (t.ex. `Typ`, `Beskrivning`), kräver `{Datum, Typ, Belopp}`, mappar datum och belopp.
- `read_positions(path: str|Path) -> pd.DataFrame`\
  Läser CSV (`sep=';'`, `dtype=str`, `encoding='utf-8-sig'`) och anropar normalisering.
- `read_transactions(path: str|Path) -> pd.DataFrame`\
  Som ovan, för transaktioner.

**Edge**: saknade kolumner → `KeyError`. Fel format → `ValueError`/`ParserError`.

---

### `src/moneygoal/contrib.py`

**Syfte**: Derivera månadsvisa nettobidrag och deras medelvärde.

**Funktioner**

- `prepare_contribution_rows(df_trx: pd.DataFrame) -> pd.DataFrame`\
  Filtrerar `Typ ∈ {Insättning, Uttag}`. Säkerställer typer. Tecken: **Insättning = +**, **Uttag = −**, med `abs()` på CSV‑belopp för konsekvens. Lägger `Månad = YYYY-MM`. Returnerar `Datum, Månad, Typ, Belopp_signed`.
- `monthly_net_contributions(rows: pd.DataFrame) -> pd.Series`\
  Summa per `Månad` över `Belopp_signed`.
- `mean_monthly_contribution(rows: pd.DataFrame) -> float`\
  Medel av månadsnetto, `0.0` om tomt.

**Not**: här är tecknen ur sparperspektiv. XIRR använder motsatt konvention (kassaflöde).

---

### `src/moneygoal/models/mwrr.py`

**Syfte**: XIRR/MWRR för daterade kassaflöden.

**API**

- `xirr(cashflows: Iterable[tuple[date,float]]) -> float`

**Metod**

- Årsfraktion: ACT/ACT (ISDA), inkl. 31/12 i första delåret, leap‑år per ISDA.
- NPV: \(\sum a_i/(1+r)^{\text{yearfrac}(t_0,t_i)}\).
- Rot: bisektion på `r ∈ [−0.999999, 10]` med bracketing och fallback.
- Validerar att både negativa och positiva flöden finns.

**Begränsning**: hanterar inte multipla rötter explicit.

---

### `src/moneygoal/diagnostics.py`

**Syfte**: Bygga kassaflöden från DataFrames och räkna XIRR.

**Funktioner**

- `compute_xirr_from_frames(df_trx, df_pos) -> float`\
  Tar `Insättning`/`Uttag`, använder **absolutbelopp** från CSV, mappning: Insättning = −, Uttag = +. Lägger terminalt **positivt** flöde = `sum(Marknadsvärde)` idagens datum. Validerar +/− och anropar `xirr`.
- `diagnostics_dict(df_trx, df_pos) -> dict`\
  Returnerar `{"xirr": <float>}`.

---

### `src/moneygoal/sim/monte_carlo.py`

**Syfte**: Simulera månader till mål.

**API**

- `time_to_goal_mc(nuvarde, mean_monthly_contrib, cagr, vol, max_months, paths, goal, seed) -> {"p10","p50","p90"}`

**Metod**

- Månadsfaktor \~ lognormal:\
  `sigma = vol / sqrt(12)`, `mu = ln(1+CAGR)/12 − 0.5*sigma^2`.
- Uppdatering: `V = V*factor + mean_monthly_contrib` per månad (deterministisk faktor om `vol=0`).
- Stoppar bana när `V ≥ goal` eller `m == max_months`.
- Validerar inputs och kortsluter `{0,0,0}` om `nuvarde ≥ goal`.

---

### `src/moneygoal/cli.py`

**Syfte**: Kör pipeline och skriver ut artefakter.

**Flaggor** `--positions --transactions --goal --report [--paths --vol --cagr --seed --maxhorisont]`

**Flöde**

1. Guards: kontrollerar filbanor och intervall (goal>0, paths≥100, vol≥0, cagr∈[0,1], maxhorisont≥1). Fel ⇒ exit 2.
2. Läs CSV → `V0 = sum(Marknadsvärde)`.
3. `rows = prepare_contribution_rows(df_trx)` → `mmc = mean_monthly_contribution(rows)`.
4. `mc = time_to_goal_mc(...)` → skriv `result/time_to_goal_summary.csv`.
5. Bygg `diag` med parametrar + `mc` och `xirr = diagnostics_dict(df_trx, df_pos)["xirr"]`.
6. Append till `result/diagnostics.csv` (stabil kolumnordning). Logga status.
7. Print `P10/P50/P90` i år+mån.

**Exit‑koder**: `0` OK, `1` körfel, `2` ogiltiga argument.

---

### `app/app.py`

**Syfte**: Streamlit‑UI som speglar CLI.

**Flöde**

- Två uploaders (transactions/positions), målbelopp och avancerade parametrar.
- Sparar uppladdade filer till `data/raw/...` och kör pipeline i minnet.
- Visar P10/P50/P90 och XIRR. Låter ladda ned `result/*.csv`.
- Visar senaste diagnostics **vertikalt** (fält→värde).
- Underhåll: knapp för att rensa `diagnostics.csv`.

## Begränsningar

- Endast Avanza‑CSV. Ingen prisdata eller per‑värdepapper‑simulering.
- Utdelningar ingår inte i MC och inte som egna kassaflöden i XIRR (endast indirekt via V0).
- XIRR återger en möjlig rot; multipla rötter hanteras inte.

## Roadmap

- Toggle i UI/CLI för utdelningar: återinvestera vs. kontant mot mål.
- Diagnostics: summering av insättningar/uttag/netto.
- Känslighetsanalys: grid över `cagr, vol, paths` och seeds.

