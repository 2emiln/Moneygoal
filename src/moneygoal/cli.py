import argparse, sys, logging
from pathlib import Path
import datetime as dt
import pandas as pd

from moneygoal.io.avanza_csv import read_positions, read_transactions
from moneygoal.contrib import prepare_contribution_rows, mean_monthly_contribution
from moneygoal.sim.monte_carlo import time_to_goal_mc
from moneygoal.diagnostics import diagnostics_dict


def main(argv=None) -> int:
    """
    Pedagogik: Detta är CLI-ingången som
      1) läser in positions/transactions,
      2) beräknar nuvärde och genomsnittligt månadsspar,
      3) kör Monte Carlo för tid till mål (P10/P50/P90),
      4) skriver rapport och diagnostics,
      5) loggar utfallet och returnerar exit-kod.

    Return:
        0  → OK
        1  → Körtidsfel (fångat undantag)
        2  → Argumentfel (tidig validering)
    """
    # 1) Definiera CLI-argument
    p = argparse.ArgumentParser(description="Beräkna tid till ekonomiskt mål med Monte Carlo.")
    p.add_argument("--positions", required=True, help="Sökväg till positions.csv (Avanza-export).")
    p.add_argument("--transactions", required=True, help="Sökväg till transactions.csv (Avanza-export).")
    p.add_argument("--goal", type=float, required=True, help="Målbelopp i SEK.")
    p.add_argument("--report", required=True, help="Fil att skriva P10/P50/P90-rapport till (CSV).")

    # 2) Monte Carlo-parametrar med rimliga default
    p.add_argument("--paths", type=int, default=5000, help="Antal simuleringar.")
    p.add_argument("--vol", type=float, default=0.15, help="Årsvolatilitet (std) som andel, t.ex. 0.15 = 15%.")
    p.add_argument("--cagr", type=float, default=0.06, help="Antagen årlig avkastning (CAGR), 0–1.")
    p.add_argument("--seed", type=int, default=42, help="Slumptalsfrö för reproducerbarhet.")
    p.add_argument("--maxhorisont", type=int, default=600, help="Max simlängd i månader.")

    args = p.parse_args(argv)

    # 3) Tidig argumentvalidering: snabbare fel och tydligare felmeddelanden
    errs = []
    if not Path(args.positions).is_file():
        errs.append(f"--positions saknas: {args.positions}")
    if not Path(args.transactions).is_file():
        errs.append(f"--transactions saknas: {args.transactions}")
    if args.goal <= 0:
        errs.append("--goal måste vara > 0")
    if args.paths < 100:
        errs.append("--paths måste vara ≥ 100")
    if args.vol < 0:
        errs.append("--vol måste vara ≥ 0")
    if not (0.0 <= args.cagr <= 1.0):
        errs.append("--cagr måste ligga i [0,1]")
    if args.maxhorisont < 1:
        errs.append("--maxhorisont måste vara ≥ 1")

    if errs:
        # Samlad utskrift till stderr för enkel CLI-felsökning
        for e in errs:
            print(f"ARGERROR: {e}", file=sys.stderr)
        return 2

    # 4) Grundläggande fil-loggning: fångar körningar och parametrar
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("Run start")
    logging.info(f"positions={args.positions}")
    logging.info(f"transactions={args.transactions}")
    logging.info(f"goal={args.goal}")
    logging.info(
        f"paths={args.paths} vol={args.vol} cagr={args.cagr} seed={args.seed} maxhorisont={args.maxhorisont}"
    )

    try:
        # 5) Läs in och normalisera CSV via IO-lagret (se avanza_csv)
        df_pos = read_positions(args.positions)
        df_trx = read_transactions(args.transactions)

        # 6) Nuvärde: summan av Marknadsvärde över alla tillgångar
        V0 = float(df_pos["Marknadsvärde"].sum())

        # 7) Månadsspar: bygg rena rader för insättning/uttag och ta månatligt medel
        rows = prepare_contribution_rows(df_trx)
        mmc = mean_monthly_contribution(rows)
        logging.info(f"mean_monthly_contrib={mmc}")

        # 8) Monte Carlo-simulering av tid till mål
        #    Input: nuvärde, genomsnittligt månadsspar, CAGR, vol, maxmånader, paths, mål
        mc = time_to_goal_mc(
            nuvarde=V0,
            mean_monthly_contrib=mmc,
            cagr=args.cagr,
            vol=args.vol,
            max_months=args.maxhorisont,
            paths=args.paths,
            goal=args.goal,
            seed=args.seed,
        )

        # 9) Skriv en kompakt CSV-rapport med P10/P50/P90 i år och månader
        def y_m(m: int) -> tuple[int, int]:
            # Hjälpare: konvertera månader → (år, månader)
            return m // 12, m % 12

        p10y, p10m = y_m(mc["p10"])
        p50y, p50m = y_m(mc["p50"])
        p90y, p90m = y_m(mc["p90"])

        out = pd.DataFrame(
            {
                "percentile": ["P10", "P50", "P90"],
                "years": [p10y, p50y, p90y],
                "months": [p10m, p50m, p90m],
            }
        )
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.report, index=False, encoding="utf-8")

        # 10) Konsolutskrift: snabb mänsklig läsning i terminalen
        def fmt(m: int) -> str:
            return f"{m//12} år {m%12} mån"

        print(
            f"P10: {fmt(mc['p10'])}  |  "
            f"P50: {fmt(mc['p50'])}  |  "
            f"P90: {fmt(mc['p90'])}"
        )

        # 11) Diagnostics: skriv sammanfattning + XIRR till result/diagnostics.csv
        #     - Append-läge med header endast när filen skapas eller är tom.
        diag = {
            "asof": dt.date.today().isoformat(),
            "stage": "run",
            "V0": V0,
            "goal": args.goal,
            "mean_monthly_contrib": mmc,
            "paths": args.paths,
            "vol": args.vol,
            "cagr": args.cagr,
            "seed": args.seed,
            "maxhorisont": args.maxhorisont,
            "p10_months": mc["p10"],
            "p50_months": mc["p50"],
            "p90_months": mc["p90"],
            "positions_path": args.positions,
            "transactions_path": args.transactions,
        }
        # diagnostics_dict kan räkna t.ex. XIRR baserat på df_trx/df_pos
        diag.update(diagnostics_dict(df_trx, df_pos))  # t.ex. {"xirr": ...}

        diag_path = Path("result/diagnostics.csv")
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        exists = diag_path.exists()
        write_header = (not exists) or (diag_path.stat().st_size == 0)
        pd.DataFrame([diag]).to_csv(
            diag_path,
            mode="a" if exists else "w",
            header=write_header,
            index=False,
            encoding="utf-8",
        )

        logging.info("Run OK")
        return 0

    except Exception as e:
        # 12) Robust felhantering: logga stacktrace och skriv kort fel till stderr
        logging.exception("Run failed")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Standardmönster för CLI-moduler
    sys.exit(main())
