# Config (defaults)
inputs: positions=`data/raw/positions.csv`, transactions=`data/raw/transactions.csv`
outputs: report=`result/time_to_goal_summary.csv`, diagnostics=`result/diagnostics.csv`, log=`logs/app.log`
mc: paths=5000, vol=0.04, seed=42, max_horizon_months=360
policy: reinvest_dividends=false, cagr_choice="historik", no_external_data=true, exclude_courtage=true
