import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "Data"

def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    path = DATA_DIR / f"players_final{suffix}.csv"
    print(f"Reading from: {path.resolve()}")
    df = pd.read_csv(path)
    df = df[df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)

    # Apply mins/games filter based on season type (data pre-filtered from build_dataset.py)
    if season_type == "Regular Season":
        df = df[(df["GP"] >= 20) & (df["MIN"] >= 12)].reset_index(drop=True)
    else:
        df = df[(df["GP"] >= 3) & (df["MIN"] >= 5)].reset_index(drop=True)

    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    return df

def compute_volume(df):
    features = ["USG_PCT", "FGA", "FTA", "MIN", "GP"]

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[features])
    scaled_df = pd.DataFrame(scaled, columns=features)

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

    df["VOLUME_SCORE"] = (df["VOLUME_SCORE"] * 100).round(1)
    return df

def print_results(df):
    top = df.nlargest(15, "VOLUME_SCORE")[
        ["PLAYER_NAME", "VOLUME_SCORE", "USG_PCT", "FGA", "MIN", "PTS"]
    ]
    print("\n--- Top 15 by Volume Score ---")
    print(top.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

def main(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    df = load_data(season_type)
    df = compute_volume(df)
    out_path = DATA_DIR / f"players_with_volume{suffix}.csv"
    df.to_csv(out_path, index=False)
    print_results(df)
    print(f"\n Stage 1 complete — saved to {out_path.name}")

if __name__ == "__main__":
    main()