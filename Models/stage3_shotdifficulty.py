import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "data"

def load_data():
    efficiency_df = pd.read_csv(DATA_DIR / "players_with_efficiency.csv")
    shot_df = pd.read_csv(DATA_DIR / "shot_quality_raw.csv")
    efficiency_df = efficiency_df[efficiency_df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Players: {efficiency_df.shape[0]}")
    print(f"Shots: {shot_df.shape[0]}")
    return efficiency_df, shot_df

def aggregate_shot_difficulty(shot_df):
    print("\nAggregating shot data by player...")

    # Pull-up / self created shots
    pullup_keywords = ["Pull-Up", "Pullup", "Step Back", "Turnaround", "Fadeaway"]
    shot_df["IS_PULLUP"] = shot_df["ACTION_TYPE"].str.contains(
        "|".join(pullup_keywords), case=False, na=False
    ).astype(int)

    # Shot clock pressure
    shot_df["SHOT_CLOCK_SECONDS"] = (
        shot_df["MINUTES_REMAINING"] * 60 + shot_df["SECONDS_REMAINING"]
    )
    shot_df["IS_LATE_CLOCK"] = (shot_df["SHOT_CLOCK_SECONDS"] <= 4).astype(int)

    # Mid-range
    shot_df["IS_MIDRANGE"] = (
        shot_df["SHOT_ZONE_BASIC"] == "Mid-Range"
    ).astype(int)

    # Hard rim shots — player created (driving, cutting)
    hard_rim_keywords = ["Driving", "Cutting"]
    shot_df["IS_RESTRICTED_HARD"] = (
        (shot_df["SHOT_ZONE_BASIC"] == "Restricted Area") &
        (shot_df["ACTION_TYPE"].str.contains("|".join(hard_rim_keywords), case=False, na=False))
    ).astype(int)

    # Easy rim shots — assisted/passive (alley oop, putback, tip, plain layup/dunk)
    easy_rim_keywords = ["Alley Oop", "Putback", "Tip Layup", "Tip Dunk"]
    shot_df["IS_RESTRICTED_EASY"] = (
        (shot_df["SHOT_ZONE_BASIC"] == "Restricted Area") &
        (shot_df["ACTION_TYPE"].str.contains("|".join(easy_rim_keywords), case=False, na=False))
    ).astype(int)

    # Aggregate per player
    agg = shot_df.groupby("PLAYER_ID").agg(
        AVG_SHOT_DISTANCE=("SHOT_DISTANCE", "mean"),
        PCT_PULLUP=("IS_PULLUP", "mean"),
        PCT_LATE_CLOCK=("IS_LATE_CLOCK", "mean"),
        PCT_MIDRANGE=("IS_MIDRANGE", "mean"),
        PCT_RESTRICTED_HARD=("IS_RESTRICTED_HARD", "mean"),
        PCT_RESTRICTED_EASY=("IS_RESTRICTED_EASY", "mean"),
        TOTAL_SHOTS=("SHOT_ATTEMPTED_FLAG", "sum")
    ).reset_index()

    print(f"Aggregated: {len(agg)} players")
    return agg

def compute_shot_difficulty(efficiency_df, shot_agg):
    """
    Build SHOT_DIFFICULTY_SCORE from aggregated features.
    Higher = harder shots on average.
    """
    df = pd.merge(
    efficiency_df,
    shot_agg[["PLAYER_ID", "AVG_SHOT_DISTANCE", "PCT_PULLUP",
          "PCT_LATE_CLOCK", "PCT_MIDRANGE", "PCT_RESTRICTED_HARD",
          "PCT_RESTRICTED_EASY", "TOTAL_SHOTS"]],
    on="PLAYER_ID",
    how="left"
)

    features = {
        "AVG_SHOT_DISTANCE": 0.25,   # farther = harder
        "PCT_PULLUP":        0.30,   # self created = harder
        "PCT_MIDRANGE":      0.20,   # mid range = hardest shot in NBA
        "PCT_LATE_CLOCK":    0.10,   # rushed shots = harder
        "PCT_RESTRICTED_EASY":   -0.10,   # rim shots = easier (inverted)
        "PCT_RESTRICTED_HARD": 0.15,  # tough rim shots = harder
    }

    # Fill missing values
    for col in features:
        df[col] = df[col].fillna(df[col].median())

    # Scale to 0-1
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[list(features.keys())])
    scaled_df = pd.DataFrame(scaled, columns=list(features.keys()))

    # Weighted sum
    df["SHOT_DIFFICULTY_SCORE"] = sum(
        scaled_df[col] * weight
        for col, weight in features.items()
    )

    # Scale to 0-100
    d = df["SHOT_DIFFICULTY_SCORE"]
    df["SHOT_DIFFICULTY_SCORE"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    print(f"\nDifficulty range: {df['SHOT_DIFFICULTY_SCORE'].min()} – {df['SHOT_DIFFICULTY_SCORE'].max()}")
    return df

def compute_adjusted_efficiency(df):
    """
    Adjust efficiency score by shot difficulty.
    Hard shots + efficient = truly elite scorer.
    """
    scaler = MinMaxScaler()

    df["TS_X_DIFFICULTY"] = df["TS_PCT"] * (df["SHOT_DIFFICULTY_SCORE"] / 100)
    df["TS_X_DIFFICULTY_SCALED"] = scaler.fit_transform(df[["TS_X_DIFFICULTY"]])
    df["EFFICIENCY_SCORE_SCALED"] = scaler.fit_transform(df[["EFFICIENCY_SCORE"]])

    df["DIFFICULTY_ADJ_EFFICIENCY"] = (
        df["EFFICIENCY_SCORE_SCALED"] * 0.50 +
        df["TS_X_DIFFICULTY_SCALED"] * 0.50
    ) * 100

    df["DIFFICULTY_ADJ_EFFICIENCY"] = df["DIFFICULTY_ADJ_EFFICIENCY"].round(1)
    return df

def print_results(df):
    qualified = df[df["PTS"] >= 10].copy()

    print("\n--- Top 15 Hardest Shot Diets (10+ PPG) ---")
    hard = qualified.nlargest(15, "SHOT_DIFFICULTY_SCORE")[
        ["PLAYER_NAME", "SHOT_DIFFICULTY_SCORE", "AVG_SHOT_DISTANCE",
         "PCT_PULLUP", "PCT_MIDRANGE", "TS_PCT", "PTS"]
    ].round(3)
    print(hard.to_string(index=False))

    print("\n--- Top 15 Difficulty Adjusted Efficiency (10+ PPG) ---")
    adj = qualified.nlargest(15, "DIFFICULTY_ADJ_EFFICIENCY")[
        ["PLAYER_NAME", "DIFFICULTY_ADJ_EFFICIENCY", "EFFICIENCY_SCORE",
         "SHOT_DIFFICULTY_SCORE", "TS_PCT", "PTS"]
    ].round(3)
    print(adj.to_string(index=False))

def main():
    efficiency_df, shot_df = load_data()
    shot_agg = aggregate_shot_difficulty(shot_df)
    df = compute_shot_difficulty(efficiency_df, shot_agg)
    df = compute_adjusted_efficiency(df)
    df.to_csv(DATA_DIR / "players_with_difficulty.csv", index=False)
    print_results(df)
    print("\n Stage 3 complete — saved to data/players_with_difficulty.csv")

if __name__ == "__main__":
    main()