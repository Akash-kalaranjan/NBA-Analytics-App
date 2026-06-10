import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

DATA_DIR = Path(__file__).parent.parent / "Data"

def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    df = pd.read_csv(DATA_DIR / f"players_with_volume{suffix}.csv")
    df = df[df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    return df

def compute_expected_ts(df):
    df["FG3A_RATE"] = df["FG3A"] / df["FGA"]
    df["FTA_RATE"] = df["FTA"] / df["FGA"]

    # Drop rows with NaN values in the features needed for regression
    valid_idx = df[["USG_PCT", "FG3A_RATE", "FTA_RATE", "TS_PCT"]].notna().all(axis=1)
    df_valid = df[valid_idx].copy()

    X = df_valid[["USG_PCT", "FG3A_RATE", "FTA_RATE"]].values
    y = df_valid["TS_PCT"].values

    model = LinearRegression()
    model.fit(X, y)
    
    # Predict for all rows, leaving NaN for invalid rows
    df["EXPECTED_TS"] = np.nan
    df.loc[valid_idx, "EXPECTED_TS"] = model.predict(X)
    df["TS_ABOVE_EXPECTED"] = df["TS_PCT"] - df["EXPECTED_TS"]

    print(f"\nR² score: {model.score(X, y):.4f}")
    return df

def compute_efficiency_score(df):
    scaler = MinMaxScaler()

    df["TS_PCT_SCALED"] = scaler.fit_transform(df[["TS_PCT"]])
    df["TS_ABOVE_EXPECTED_SCALED"] = scaler.fit_transform(df[["TS_ABOVE_EXPECTED"]])

    df["EFFICIENCY_SCORE"] = (
        df["TS_PCT_SCALED"] * 0.60 +
        df["TS_ABOVE_EXPECTED_SCALED"] * 0.40
    ) * 100

    df["EFFICIENCY_SCORE"] = df["EFFICIENCY_SCORE"].round(1)
    return df

def print_results(df):
    qualified = df[df["PTS"] >= 10]
    top = qualified.nlargest(15, "EFFICIENCY_SCORE")[
        ["PLAYER_NAME", "EFFICIENCY_SCORE", "TS_PCT",
         "EXPECTED_TS", "TS_ABOVE_EXPECTED", "USG_PCT", "PTS"]
    ].round(3)
    print("\n--- Top 15 by Efficiency Score (10+ PPG) ---")
    print(top.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

def main(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    df = load_data(season_type)
    df = compute_expected_ts(df)
    df = compute_efficiency_score(df)
    out_path = DATA_DIR / f"players_with_efficiency{suffix}.csv"
    df.to_csv(out_path, index=False)
    print_results(df)
    print(f"\n Stage 2 complete — saved to {out_path.name}")

if __name__ == "__main__":
    main()