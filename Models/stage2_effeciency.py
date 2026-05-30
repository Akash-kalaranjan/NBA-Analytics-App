import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

DATA_DIR = Path(__file__).parent.parent / "data"

def load_data():
    df = pd.read_csv(DATA_DIR / "players_with_volume.csv")
    df = df[df["PLAYER_NAME"] != "Deni Avdija"]
    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    return df

def compute_expected_ts(df):
    
    #Use linear regression to predict expected TS% based on usage, 3pt rate, and free throw rate.
    # FG3A rate = how often they shoot 3s
    df["FG3A_RATE"] = df["FG3A"] / df["FGA"]
    # FTA rate = how often they get to the line
    df["FTA_RATE"] = df["FTA"] / df["FGA"]

    X = df[["USG_PCT", "FG3A_RATE", "FTA_RATE"]].values
    y = df["TS_PCT"].values

    model = LinearRegression()
    model.fit(X, y)

    df["EXPECTED_TS"] = model.predict(X)
    df["TS_ABOVE_EXPECTED"] = df["TS_PCT"] - df["EXPECTED_TS"]

    print(f"\nR² score: {model.score(X, y):.4f}")
    return df

def compute_efficiency_score(df):
    
    ## Combine raw efficiency (TS%) with efficiency above expectation.
    ## Players who beat their expected TS% get rewarded.
    
    scaler = MinMaxScaler()

    df["TS_PCT_SCALED"] = scaler.fit_transform(df[["TS_PCT"]])
    df["TS_ABOVE_EXPECTED_SCALED"] = scaler.fit_transform(df[["TS_ABOVE_EXPECTED"]])

    # 60% raw efficiency, 40% above expectation
    df["EFFICIENCY_SCORE"] = (
        df["TS_PCT_SCALED"] * 0.60 +
        df["TS_ABOVE_EXPECTED_SCALED"] * 0.40
    ) * 100

    df["EFFICIENCY_SCORE"] = df["EFFICIENCY_SCORE"].round(1)
    return df

def print_results(df):
    # Filter to meaningful scorers only
    qualified = df[df["PTS"] >= 10]
    top = qualified.nlargest(15, "EFFICIENCY_SCORE")[
        ["PLAYER_NAME", "EFFICIENCY_SCORE", "TS_PCT", 
         "EXPECTED_TS", "TS_ABOVE_EXPECTED", "USG_PCT", "PTS"]
    ].round(3)
    print("\n--- Top 15 by Efficiency Score (10+ PPG) ---")
    print(top.to_string(index=False))

def main():
    df = load_data()
    df = compute_expected_ts(df)
    df = compute_efficiency_score(df)
    df.to_csv(DATA_DIR / "players_with_efficiency.csv", index=False)
    print_results(df)
    print("\n Stage 2 complete — saved to data/players_with_efficiency.csv")

if __name__ == "__main__":
    main()
