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
POS_PATH = Path("data/raw/positions/positions.csv")
TRX_PATH = Path("data/raw/transactions/transactions.csv")
RESULT_SUMMARY = Path("result/time_to_goal_summary.csv")
RESULT_DIAG = Path("result/diagnostics.csv")
LOG_PATH = Path("logs/app.log")

# --- Setup ---
Path("data/raw/positions").mkdir(parents=True, exist_ok=True)
Path("data/raw/transactions").mkdir(parents=True, exist_ok=True)
RESULT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Basic logging once per process
if not logging.getLogger().handlers:
    logging.basicConfig(
        filename=str(LOG_PATH), level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

st.set_page_config(page_title=APP_TITLE, layout="centered")
st.title(APP_TITLE)
st.caption("Avanza-CSV → Tid till mål (P10/P50/P90) + XIRR. Inga externa datakällor.")

# --- Helpers ---
def save_uploaded_file(uf, target: Path) -> None:
    data = uf.getvalue()  # bytes
    target.write_bytes(data)

def months_to_ym(m: int) -> tuple[int, int]:
    return m // 12, m % 12

# --- Inputs ---
with st.form("inputs", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        trx_file = st.file_uploader("Transactions (CSV)", type=["csv"], accept_multiple_files=False)
    with col2:
        pos_file = st.file_uploader("Positions (CSV)", type=["csv"], accept_multiple_files=False)

    goal = st.number_input("Målbelopp (SEK)", min_value=1.0, step=1000.0, value=1_000_000.0)

    with st.expander("Avancerade parametrar", expanded=False):
        paths = st.number_input("Monte Carlo paths", min_value=100, step=100, value=5000)
        vol = st.number_input("Årsvolatilitet", min_value=0.0, step=0.01, value=0.15)
        cagr = st.number_input("CAGR (0–1)", min_value=0.0, max_value=1.0, step=0.01, value=0.06)
        seed = st.number_input("Seed", min_value=0, step=1, value=42)
        maxhor = st.number_input("Max horisont (mån)", min_value=1, step=12, value=600)

    run = st.form_submit_button("Kör")

# --- Actions ---
if run:
    # Guards
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
        for e in errs:
            st.error(e)
        st.stop()

    # Spara fasta filer
    save_uploaded_file(trx_file, TRX_PATH)
    save_uploaded_file(pos_file, POS_PATH)

    # Kör pipeline
    try:
        df_pos = read_positions(str(POS_PATH))
        df_trx = read_transactions(str(TRX_PATH))

        V0 = float(pd.to_numeric(df_pos["Marknadsvärde"]).sum())
        rows = prepare_contribution_rows(df_trx)
        mmc = float(mean_monthly_contribution(rows))

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

        p10y, p10m = months_to_ym(mc["p10"])
        p50y, p50m = months_to_ym(mc["p50"])
        p90y, p90m = months_to_ym(mc["p90"])

        # Skriv summary
        summary_df = pd.DataFrame({
            "percentile": ["P10","P50","P90"],
            "years": [p10y, p50y, p90y],
            "months": [p10m, p50m, p90m],
        })
        summary_df.to_csv(RESULT_SUMMARY, index=False, encoding="utf-8")

        # Diagnostics med XIRR
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
        # xirr
        diag.update(diagnostics_dict(df_trx, df_pos))

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
                present = [c for c in cols_order if c in new.columns]
                rest = [c for c in new.columns if c not in present]
                new = new.reindex(columns=present + rest)
            except Exception:
                new = pd.DataFrame([diag])
        else:
            new = pd.DataFrame([diag]).reindex(columns=cols_order, fill_value=pd.NA)

        new.to_csv(RESULT_DIAG, index=False, encoding="utf-8")

        # --- UI Output ---
        st.success("Körning klar")
        st.subheader("Tid till mål")
        st.write(f"P10: {p10y} år {p10m} mån  |  P50: {p50y} år {p50m} mån  |  P90: {p90y} år {p90m} mån")

        st.subheader("Diagnostics")
        st.write(f"Nuvärde (V0): {V0:,.2f} SEK".replace(",", " ").replace(".", ","))
        st.write(f"Snitt månadsspar: {mmc:,.2f} SEK/mån".replace(",", " ").replace(".", ","))
        st.write(f"XIRR: {diag['xirr']:.2%}")

        # Visa senaste diagnostics-rad
        try:
            last = pd.read_csv(RESULT_DIAG).tail(1)
            st.dataframe(last)
        except Exception:
            pass

        # Nedladdningar
        st.download_button("Ladda ner summary.csv", summary_df.to_csv(index=False).encode("utf-8"), file_name="time_to_goal_summary.csv")
        st.download_button("Ladda ner diagnostics.csv", Path(RESULT_DIAG).read_bytes(), file_name="diagnostics.csv")

    except Exception as e:
        logging.exception("UI-körning misslyckades")
        st.error(f"ERROR: {e}")

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
