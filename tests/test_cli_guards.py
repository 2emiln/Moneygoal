import os
from moneygoal import cli

def test_bad_paths_returns_2():
    rc = cli.main([
        "--positions","data/raw/positions/missing.csv",
        "--transactions","data/raw/transactions/transactions.csv",
        "--goal","1000000",
        "--report","result/time_to_goal_summary.csv",
        "--paths","5000","--vol","0.15","--cagr","0.06","--seed","42","--maxhorisont","600",
    ])
    assert rc == 2

def test_bad_params_returns_2():
    rc = cli.main([
        "--positions","data/raw/positions/positions.csv",
        "--transactions","data/raw/transactions/transactions.csv",
        "--goal","-1",
        "--report","result/time_to_goal_summary.csv",
        "--paths","50","--vol","-0.1","--cagr","1.5","--seed","42","--maxhorisont","0",
    ])
    assert rc == 2

def test_ok_returns_0():
    assert os.path.isfile("data/raw/positions/positions.csv")
    assert os.path.isfile("data/raw/transactions/transactions.csv")
    rc = cli.main([
        "--positions","data/raw/positions/positions.csv",
        "--transactions","data/raw/transactions/transactions.csv",
        "--goal","1000000",
        "--report","result/time_to_goal_summary.csv",
        "--paths","5000","--vol","0.15","--cagr","0.06","--seed","42","--maxhorisont","600",
    ])
    assert rc == 0
