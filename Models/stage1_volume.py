import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "data"

def load_data():
    path = DATA_DIR / "players_final.csv"
    print(f"Reading from: {path.resolve()}")
    df = pd.read_csv(path)
    df = df[df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    print(df.nlargest(3, 'FGA')[['PLAYER_NAME','FGA']].to_string())
    return df

def compute_volume(df):
    # Features that take in scoring opportunity
    features = ["USG_PCT", "FGA", "FTA", "MIN", "GP"]

    # Scale each feature to 0-1 range
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[features])
    scaled_df = pd.DataFrame(scaled, columns=features)

    # Weighted average (Emphasize usage and field goal attempts)
    weights = {
        "USG_PCT": 0.35,
        "FGA":     0.30,
        "FTA":     0.15,
        "MIN":     0.15,
        "GP":      0.05
    }

    df["VOLUME_SCORE"] = sum(
        scaled_df[col] * weight 
        for col, weight in weights.items()
    )
    
    # Scale final score to 0-100
    df["VOLUME_SCORE"] = (df["VOLUME_SCORE"] * 100).round(1)
    return df

def print_results(df):
    top = df.nlargest(15, "VOLUME_SCORE")[
        ["PLAYER_NAME", "VOLUME_SCORE", "USG_PCT", "FGA", "MIN", "PTS"]
    ]
    print("\n--- Top 15 by Volume Score ---")
    print(top.to_string(index=False))

def main():
    df = load_data()
    df = compute_volume(df)
    df.to_csv(DATA_DIR / "players_with_volume.csv", index=False)
    print_results(df)
    print("\n Stage 1 complete — saved to data/players_with_volume.csv")

if __name__ == "__main__":
    main()