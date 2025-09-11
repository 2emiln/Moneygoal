from __future__ import annotations
import argparse, sys, logging
from pathlib import Path
import pandas as pd
from moneygoal.io.avanza_csv import read_positions, read_transactions

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--positions", required=True)
    p.add_argument("--transactions", required=True)
    p.add_argument("--goal", required=True, type=float)
    p.add_argument("--report", required=True)
    args = p.parse_args(argv)

    # logging
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("Start E2E-smoke")
    logging.info(f"positions={args.positions}")
    logging.info(f"transactions={args.transactions}")
    logging.info(f"goal={args.goal}")

    try:
        df_pos = read_positions(args.positions)
        _ = read_transactions(args.transactions)

        V0 = float(df_pos["Marknadsvärde"].sum())

        # dummy-resultat för smoke
        out = pd.DataFrame(
            {"percentile": ["P10", "P50", "P90"], "years": [0, 0, 0], "months": [0, 0, 0]}
        )
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.report, index=False, encoding="utf-8")

        # diagnostics med header en gång
        diag_path = Path("result/diagnostics.csv")
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        diag_row = pd.DataFrame([{
            "stage": "smoke",
            "V0": V0,
            "goal": args.goal,
            "positions_path": args.positions,
            "transactions_path": args.transactions,
        }])
        exists = diag_path.exists()
        write_header = (not exists) or (diag_path.stat().st_size == 0)
        diag_row.to_csv(
            diag_path,
            mode="a" if exists else "w",
            header=write_header,
            index=False,
            encoding="utf-8",
        )

        logging.info("E2E-smoke OK")
        return 0
    except Exception as e:
        logging.exception("E2E-smoke failed")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
