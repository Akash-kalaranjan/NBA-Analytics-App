import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "Data"

WEIGHTS = {
    "VOLUME_SCORE":              0.275,
    "DIFFICULTY_ADJ_EFFICIENCY": 0.250,
    "EFFICIENCY_SCORE":          0.250,
    "CONTEXT_SCORE":             0.150,
    "INDEPENDENCE_SCORE":        0.075,
}

def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    df = pd.read_csv(DATA_DIR / f"players_with_independence{suffix}.csv")
    print(f"Loaded: {len(df)} players, {df.shape[1]} columns")
    return df

def compute_final_score(df):
    print("\nComputing True Scoring Impact Score...")

    # Check all features exist
    for col in WEIGHTS:
        if col not in df.columns:
            print(f"  WARNING: {col} not found — filling with 0")
            df[col] = 0.0

    # Scale each stage score to 0-1
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[list(WEIGHTS.keys())])
    scaled_df = pd.DataFrame(scaled, columns=list(WEIGHTS.keys()))

    # Weighted sum
    df["TRUE_SCORING_IMPACT"] = sum(
        scaled_df[col] * weight
        for col, weight in WEIGHTS.items()
    )

    # Scale to 0-100
    d = df["TRUE_SCORING_IMPACT"]
    df["TRUE_SCORING_IMPACT"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    return df

def print_results(df):
    qualified = df[df["PTS"] >= 10].copy()

    print("\n--- Top 25 True Scoring Impact (10+ PPG) ---")
    top = qualified.nlargest(25, "TRUE_SCORING_IMPACT")[
        ["PLAYER_NAME", "TRUE_SCORING_IMPACT", "VOLUME_SCORE",
         "EFFICIENCY_SCORE", "DIFFICULTY_ADJ_EFFICIENCY",
         "CONTEXT_SCORE", "INDEPENDENCE_SCORE", "PTS"]
    ].round(1)
    print(top.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

    print("\n--- Bottom 10 (10+ PPG) ---")
    bottom = qualified.nsmallest(10, "TRUE_SCORING_IMPACT")[
        ["PLAYER_NAME", "TRUE_SCORING_IMPACT", "PTS"]
    ].round(1)
    print(bottom.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

def main(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    df = load_data(season_type)
    df = compute_final_score(df)
    out_path = DATA_DIR / f"players_final_scores{suffix}.csv"
    df.to_csv(out_path, index=False)
    print_results(df)
    print(f"\n Final Model complete — saved to {out_path.name}")

if __name__ == "__main__":
    main()