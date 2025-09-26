# --------------------------------------------------------------------
# Streamlit-app: Avanza-CSV → Tid till mål (P10/P50/P90) + XIRR
#
# - Användaren laddar upp två CSV: transactions och positions.
# - Vi sparar dem till fasta sökvägar i data/raw/.
# - Vi läser och normaliserar, räknar nuvärde (V0) och snitt månadsspar.
# - Vi kör Monte Carlo för tid till mål och skriver summary + diagnostics.
# - UI visar resultat och erbjuder nedladdning av CSV:er.
# --------------------------------------------------------------------

import streamlit as st
import pandas as pd
from pathlib import Path
import datetime as dt
import logging

from moneygoal.io.avanza_csv import read_positions, read_transactions
from moneygoal.contrib import prepare_contribution_rows, mean_monthly_contribution
from moneygoal.sim.monte_carlo import time_to_goal_mc
from moneygoal.diagnostics import diagnostics_dict

APP_TITLE = "Moneygoal PoC"
# Fasta målplatser för uppladdade filer enligt projektets kontrakt
POS_PATH = Path("data/raw/positions/positions.csv")
TRX_PATH = Path("data/raw/transactions/transactions.csv")
RESULT_SUMMARY = Path("result/time_to_goal_summary.csv")
RESULT_DIAG = Path("result/diagnostics.csv")
LOG_PATH = Path("logs/app.log")

# --- Setup: skapa mappar och enkel fil-loggning en gång per process ---
Path("data/raw/positions").mkdir(parents=True, exist_ok=True)
Path("data/raw/transactions").mkdir(parents=True, exist_ok=True)
RESULT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Initiera logging om inga handlers finns (Streamlit kan köra multipla gånger)
if not logging.getLogger().handlers:
    logging.basicConfig(
        filename=str(LOG_PATH), level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

# Grundläggande sidkonfiguration och rubriker
st.set_page_config(page_title=APP_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption("Avanza-CSV → Tid till mål (P10/P50/P90) + XIRR. Inga externa datakällor.")

# --- Hjälpfunktioner ---
def save_uploaded_file(uf, target: Path) -> None:
    """Spara en uppladdad Streamlit-fil (uf) till target som bytes."""
    data = uf.getvalue()  # bytes från filuppladdaren
    target.write_bytes(data)

def months_to_ym(m: int) -> tuple[int, int]:
    """Konvertera antal månader till (år, månader)."""
    return m // 12, m % 12

# --- Inputs: formulär för filuppladdning och parametrar ---
with st.form("inputs", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        # Transactions = historik med Insättning/Uttag m.m.
        trx_file = st.file_uploader("Transactions (CSV)", type=["csv"], accept_multiple_files=False)
    with col2:
        # Positions = aktuella innehav med Marknadsvärde, Valuta, ISIN
        pos_file = st.file_uploader("Positions (CSV)", type=["csv"], accept_multiple_files=False)

    # Målbelopp i SEK (grundantagande: 1 000 000)
    goal = st.number_input("Målbelopp (SEK)", min_value=1.0, step=1000.0, value=1_000_000.0)

    # Avancerade parametrar: kontroll över MC och modellantaganden
    with st.expander("Avancerade parametrar", expanded=False):
        paths = st.number_input("Monte Carlo paths", min_value=100, step=100, value=5000)
        vol = st.number_input("Årsvolatilitet", min_value=0.0, step=0.01, value=0.15)
        cagr = st.number_input("CAGR (0–1)", min_value=0.0, max_value=1.0, step=0.01, value=0.06)
        seed = st.number_input("Seed", min_value=0, step=1, value=42)
        maxhor = st.number_input("Max horisont (mån)", min_value=1, step=12, value=600)

    # Kör-knapp submit: triggar validering och pipeline
    run = st.form_submit_button("Kör")

# --- Actions: validera input, spara filer, kör pipeline, skriv UI ---
if run:
    # 1) Enkla guards för att ge användaren tidiga, tydliga fel
    errs = []
    if trx_file is None:
        errs.append("Ladda upp transactions.csv")
    if pos_file is None:
        errs.append("Ladda upp positions.csv")
    if goal <= 0:
        errs.append("Målbelopp måste vara > 0")
    if paths < 100:
        errs.append("Paths måste vara ≥ 100")
    if vol < 0:
        errs.append("Vol måste vara ≥ 0")
    if not (0.0 <= cagr <= 1.0):
        errs.append("CAGR måste ligga i [0,1]")
    if maxhor < 1:
        errs.append("Max horisont måste vara ≥ 1")

    if errs:
        # Visa alla fel och avbryt exekvering
        for e in errs:
            st.error(e)
        st.stop()

    # 2) Spara uppladdade filer till standardiserade sökvägar
    save_uploaded_file(trx_file, TRX_PATH)
    save_uploaded_file(pos_file, POS_PATH)

    # 3) Kör end-to-end-pipeline med robust felhantering
    try:
        # a) Läs och normalisera båda CSV:erna
        df_pos = read_positions(str(POS_PATH))
        df_trx = read_transactions(str(TRX_PATH))

        # b) Nuvärde (V0): summa av Marknadsvärde
        V0 = float(pd.to_numeric(df_pos["Marknadsvärde"]).sum())

        # c) Månatligt snittbidrag: extrahera insättning/uttag → gruppera per månad → medel
        rows = prepare_contribution_rows(df_trx)
        mmc = float(mean_monthly_contribution(rows))

        # d) Monte Carlo: simulera tid till att nå mål (mått i månader)
        mc = time_to_goal_mc(
            nuvarde=V0,
            mean_monthly_contrib=mmc,
            cagr=float(cagr),
            vol=float(vol),
            max_months=int(maxhor),
            paths=int(paths),
            goal=float(goal),
            seed=int(seed),
        )

        # e) Konvertera månader till (år, mån) för P10/P50/P90
        p10y, p10m = months_to_ym(mc["p10"])
        p50y, p50m = months_to_ym(mc["p50"])
        p90y, p90m = months_to_ym(mc["p90"])

        # f) Skriv sammanfattning till result/time_to_goal_summary.csv
        summary_df = pd.DataFrame({
            "percentile": ["P10","P50","P90"],
            "years": [p10y, p50y, p90y],
            "months": [p10m, p50m, p90m],
        })
        summary_df.to_csv(RESULT_SUMMARY, index=False, encoding="utf-8")

        # g) Bygg diagnostics-rad med metadata + XIRR
        diag = {
            "asof": dt.date.today().isoformat(),
            "stage": "ui",
            "V0": V0,
            "goal": float(goal),
            "mean_monthly_contrib": mmc,
            "paths": int(paths),
            "vol": float(vol),
            "cagr": float(cagr),
            "seed": int(seed),
            "maxhorisont": int(maxhor),
            "p10_months": int(mc["p10"]),
            "p50_months": int(mc["p50"]),
            "p90_months": int(mc["p90"]),
            "positions_path": str(POS_PATH),
            "transactions_path": str(TRX_PATH),
        }
        # XIRR beräknas från transaktioner + nuvärde (se diagnostics_dict)
        diag.update(diagnostics_dict(df_trx, df_pos))

        # h) Append till diagnostics.csv och behåll kolumnordning om möjligt
        cols_order = [
            "asof","stage","V0","goal","mean_monthly_contrib",
            "paths","vol","cagr","seed","maxhorisont",
            "p10_months","p50_months","p90_months","xirr",
            "positions_path","transactions_path",
        ]

        if RESULT_DIAG.exists() and RESULT_DIAG.stat().st_size > 0:
            try:
                old = pd.read_csv(RESULT_DIAG)
                new = pd.concat([old, pd.DataFrame([diag])], ignore_index=True)
                # Prioritera kända kolumner först, lägg ev. nya sist
                present = [c for c in cols_order if c in new.columns]
                rest = [c for c in new.columns if c not in present]
                new = new.reindex(columns=present + rest)
            except Exception:
                # Om tidigare fil inte går att läsa, börja om med endast aktuell rad
                new = pd.DataFrame([diag])
        else:
            # Första skrivningen: använd målordning och fyll ev. saknade med Na
            new = pd.DataFrame([diag]).reindex(columns=cols_order, fill_value=pd.NA)

        new.to_csv(RESULT_DIAG, index=False, encoding="utf-8")

        # --- UI Output ---
        st.success("Körning klar")

        # Resultatsammanfattning i klartext
        st.subheader("Tid till mål")
        st.write(f"P10: {p10y} år {p10m} mån  |  P50: {p50y} år {p50m} mån  |  P90: {p90y} år {p90m} mån")

        # Nyckeltal och spårbarhet
        st.subheader("Diagnostics")
        # Visa V0 och månadsspar med svensk sifferstil (mellanslag, komma)
        st.write(f"Nuvärde (V0): {V0:,.2f} SEK".replace(",", " ").replace(".", ","))
        st.write(f"Snitt månadsspar: {mmc:,.2f} SEK/mån".replace(",", " ").replace(".", ","))
        st.write(f"XIRR: {diag['xirr']:.2%}")

        # Visa senaste diagnostics vertikalt
        try:
            last = pd.read_csv(RESULT_DIAG).tail(1)
            order = [
                "asof","stage","V0","goal","mean_monthly_contrib",
                "paths","vol","cagr","seed","maxhorisont",
                "p10_months","p50_months","p90_months","xirr",
                "positions_path","transactions_path",
            ]
            last = last[[c for c in order if c in last.columns]]
            kv = last.T.reset_index()
            kv.columns = ["fält", "värde"]
            st.subheader("Diagnostics (detalj)")
            st.dataframe(kv, use_container_width=True, hide_index=True)
        except Exception:
            pass    # UI ska inte krascha om läsningen fallerar

        # Nedladdningar: gör det enkelt att exportera resultat
        st.download_button(
            "Ladda ner summary.csv",
            summary_df.to_csv(index=False).encode("utf-8"),
            file_name="time_to_goal_summary.csv"
        )
        st.download_button(
            "Ladda ner diagnostics.csv",
            Path(RESULT_DIAG).read_bytes(),
            file_name="diagnostics.csv"
        )

    except Exception as e:
        # Logga stacktrace till fil och visa kort fel i UI
        logging.exception("UI-körning misslyckades")
        st.error(f"ERROR: {e}")

# --- Underhållssektion: liten verktygsknapp för att rensa diagnostics ---
st.divider()
with st.expander("Underhåll"):
    if st.button("Rensa diagnostics.csv"):
        try:
            if RESULT_DIAG.exists():
                RESULT_DIAG.unlink()
                st.success("Diagnostics rensad")
            else:
                st.info("Ingen diagnostics.csv att rensa")
        except Exception as e:
            st.error(f"Kunde inte radera: {e}")
