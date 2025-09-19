import argparse, sys, logging
from pathlib import Path
import datetime as dt
import pandas as pd

from moneygoal.io.avanza_csv import read_positions, read_transactions
from moneygoal.contrib import prepare_contribution_rows, mean_monthly_contribution
from moneygoal.sim.monte_carlo import time_to_goal_mc
from moneygoal.diagnostics import diagnostics_dict


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--positions", required=True)
    p.add_argument("--transactions", required=True)
    p.add_argument("--goal", type=float, required=True, help="Målbelopp i SEK")
    p.add_argument("--report", required=True)

    # Monte Carlo-parametrar
    p.add_argument("--paths", type=int, default=5000)
    p.add_argument("--vol", type=float, default=0.15)
    p.add_argument("--cagr", type=float, default=0.06)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--maxhorisont", type=int, default=600, help="Max månader")

    args = p.parse_args(argv)

    # --- CLI guards ---
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
        for e in errs:
            print(f"ARGERROR: {e}", file=sys.stderr)
        return 2


    # logging
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
        # Läs data
        df_pos = read_positions(args.positions)
        df_trx = read_transactions(args.transactions)

        # Nuvärde
        V0 = float(df_pos["Marknadsvärde"].sum())

        # Månadsspar (snitt)
        rows = prepare_contribution_rows(df_trx)
        mmc = mean_monthly_contribution(rows)
        logging.info(f"mean_monthly_contrib={mmc}")

        # Monte Carlo
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

        # Rapport (P10/P50/P90)
        def y_m(m: int) -> tuple[int, int]:
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

        # Konsolutskrift
        def fmt(m: int) -> str:
            return f"{m//12} år {m%12} mån"

        print(
            f"P10: {fmt(mc['p10'])}  |  "
            f"P50: {fmt(mc['p50'])}  |  "
            f"P90: {fmt(mc['p90'])}"
        )

        # Diagnostics (inkl. XIRR)
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
        # xirr
        diag.update(diagnostics_dict(df_trx, df_pos))  # {"xirr": ...}

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
        logging.exception("Run failed")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
