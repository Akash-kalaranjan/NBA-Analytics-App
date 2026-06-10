import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "Data"

def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    efficiency_df = pd.read_csv(DATA_DIR / f"players_with_efficiency{suffix}.csv")
    shot_df = pd.read_csv(DATA_DIR / f"shot_quality_raw{suffix}.csv")
    efficiency_df = efficiency_df[efficiency_df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Players: {efficiency_df.shape[0]}")
    print(f"Shots: {shot_df.shape[0]}")
    return efficiency_df, shot_df

def aggregate_shot_difficulty(shot_df):
    print("\nAggregating shot data by player...")

    pullup_keywords = ["Pull-Up", "Pullup", "Step Back", "Turnaround", "Fadeaway"]
    shot_df["IS_PULLUP"] = shot_df["ACTION_TYPE"].str.contains(
        "|".join(pullup_keywords), case=False, na=False
    ).astype(int)

    shot_df["SHOT_CLOCK_SECONDS"] = (
        shot_df["MINUTES_REMAINING"] * 60 + shot_df["SECONDS_REMAINING"]
    )
    shot_df["IS_LATE_CLOCK"] = (shot_df["SHOT_CLOCK_SECONDS"] <= 4).astype(int)

    shot_df["IS_MIDRANGE"] = (
        shot_df["SHOT_ZONE_BASIC"] == "Mid-Range"
    ).astype(int)

    hard_rim_keywords = ["Driving", "Cutting"]
    shot_df["IS_RESTRICTED_HARD"] = (
        (shot_df["SHOT_ZONE_BASIC"] == "Restricted Area") &
        (shot_df["ACTION_TYPE"].str.contains("|".join(hard_rim_keywords), case=False, na=False))
    ).astype(int)

    easy_rim_keywords = ["Alley Oop", "Putback", "Tip Layup", "Tip Dunk"]
    shot_df["IS_RESTRICTED_EASY"] = (
        (shot_df["SHOT_ZONE_BASIC"] == "Restricted Area") &
        (shot_df["ACTION_TYPE"].str.contains("|".join(easy_rim_keywords), case=False, na=False))
    ).astype(int)

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
    df = pd.merge(
        efficiency_df,
        shot_agg[["PLAYER_ID", "AVG_SHOT_DISTANCE", "PCT_PULLUP",
                  "PCT_LATE_CLOCK", "PCT_MIDRANGE", "PCT_RESTRICTED_HARD",
                  "PCT_RESTRICTED_EASY", "TOTAL_SHOTS"]],
        on="PLAYER_ID",
        how="left"
    )

    features = {
        "AVG_SHOT_DISTANCE":   0.25,
        "PCT_PULLUP":          0.30,
        "PCT_MIDRANGE":        0.20,
        "PCT_LATE_CLOCK":      0.10,
        "PCT_RESTRICTED_EASY": -0.10,
        "PCT_RESTRICTED_HARD": 0.15,
    }

    for col in features:
        df[col] = df[col].fillna(df[col].median())

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[list(features.keys())])
    scaled_df = pd.DataFrame(scaled, columns=list(features.keys()))

    df["SHOT_DIFFICULTY_SCORE"] = sum(
        scaled_df[col] * weight
        for col, weight in features.items()
    )

    d = df["SHOT_DIFFICULTY_SCORE"]
    df["SHOT_DIFFICULTY_SCORE"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    print(f"\nDifficulty range: {df['SHOT_DIFFICULTY_SCORE'].min()} – {df['SHOT_DIFFICULTY_SCORE'].max()}")
    return df

def compute_adjusted_efficiency(df):
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
    print(hard.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

    print("\n--- Top 15 Difficulty Adjusted Efficiency (10+ PPG) ---")
    adj = qualified.nlargest(15, "DIFFICULTY_ADJ_EFFICIENCY")[
        ["PLAYER_NAME", "DIFFICULTY_ADJ_EFFICIENCY", "EFFICIENCY_SCORE",
         "SHOT_DIFFICULTY_SCORE", "TS_PCT", "PTS"]
    ].round(3)
    print(adj.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

def main(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    efficiency_df, shot_df = load_data(season_type)
    shot_agg = aggregate_shot_difficulty(shot_df)
    df = compute_shot_difficulty(efficiency_df, shot_agg)
    df = compute_adjusted_efficiency(df)
    out_path = DATA_DIR / f"players_with_difficulty{suffix}.csv"
    df.to_csv(out_path, index=False)
    print_results(df)
    print(f"\n Stage 3 complete — saved to {out_path.name}")

if __name__ == "__main__":
    main()