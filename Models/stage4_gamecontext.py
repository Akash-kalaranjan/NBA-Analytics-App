import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "data"

def load_data():
    players_df = pd.read_csv(DATA_DIR / "players_with_difficulty.csv")
    shots_df = pd.read_csv(DATA_DIR / "shot_quality_raw.csv")
    context_df = pd.read_csv(DATA_DIR / "game_context.csv")
    players_df = players_df[players_df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Players: {len(players_df)}")
    print(f"Shots: {len(shots_df)}")
    print(f"Game context: {len(context_df)}")
    return players_df, shots_df, context_df

def attach_context_to_shots(shots_df, context_df):
    """Join game context onto every shot."""
    print("\nAttaching game context to shots...")
    shots_df = shots_df.merge(
        context_df[["GAME_ID", "TEAM_ID", "REST_DAYS", 
                    "SCORE_MARGIN", "IS_BLOWOUT", "IS_CLOSE_GAME"]],
        on=["GAME_ID", "TEAM_ID"],
        how="left"
    )
    missing = shots_df["REST_DAYS"].isna().sum()
    print(f"  Shots with context: {len(shots_df) - missing}/{len(shots_df)}")
    return shots_df

def build_game_context_features(shots_df):
    """Aggregate shot+context data to player level."""
    print("\nBuilding game context features...")

    #  Time in game 
    # Early game: Q1 + Q2
    # Late game: Q4 with <= 5 minutes remaining
    shots_df["IS_EARLY_GAME"] = (shots_df["PERIOD"] <= 2).astype(int)
    shots_df["IS_LATE_GAME"] = (
        (shots_df["PERIOD"] == 4) & (shots_df["MINUTES_REMAINING"] <= 5)
    ).astype(int)

    # Clutch: close game in Q4
    shots_df["IS_CLUTCH"] = (
        (shots_df["IS_CLOSE_GAME"] == 1) & (shots_df["PERIOD"] == 4)
    ).astype(int)

    # Shot clock buckets
    shots_df["SHOT_CLOCK_SECONDS"] = (
        shots_df["MINUTES_REMAINING"] * 60 + shots_df["SECONDS_REMAINING"]
    )
    shots_df["IS_EARLY_CLOCK"] = (shots_df["SHOT_CLOCK_SECONDS"] >= 15).astype(int)
    shots_df["IS_LATE_CLOCK"] = (shots_df["SHOT_CLOCK_SECONDS"] <= 4).astype(int)

    # Home vs away
    shots_df["IS_HOME"] = (
        shots_df["TEAM_NAME"] == shots_df.apply(
            lambda r: r["HTM"] if r["HTM"] == r["TEAM_NAME"] else r["VTM"], axis=1
        )
    ).astype(int)

    # Simpler home flag using HTM column
    shots_df["IS_HOME"] = (shots_df["HTM"] == shots_df["TEAM_NAME"].map(
        shots_df.groupby("TEAM_NAME")["HTM"].agg(lambda x: x.mode()[0])
    )).astype(int)

    # Aggregate per player
    agg = shots_df.groupby("PLAYER_ID").agg(
        # Shooting % in each context
        FG_PCT_EARLY_GAME=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_EARLY_GAME"] == 1].mean()),
        FG_PCT_LATE_GAME=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_LATE_GAME"] == 1].mean()),
        FG_PCT_CLUTCH=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_CLUTCH"] == 1].mean()),
        FG_PCT_BLOWOUT=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_BLOWOUT"] == 1].mean()),
        FG_PCT_HOME=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_HOME"] == 1].mean()),
        FG_PCT_AWAY=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_HOME"] == 0].mean()),
        FG_PCT_EARLY_CLOCK=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_EARLY_CLOCK"] == 1].mean()),
        FG_PCT_LATE_CLOCK=("SHOT_MADE_FLAG", lambda x: x[shots_df.loc[x.index, "IS_LATE_CLOCK"] == 1].mean()),
        AVG_REST_DAYS=("REST_DAYS", "mean"),
        CLUTCH_ATTEMPTS=("IS_CLUTCH", "sum"),
        TOTAL_SHOTS=("SHOT_ATTEMPTED_FLAG", "sum")
    ).reset_index()

    print(f"  Aggregated: {len(agg)} players")
    return agg

def compute_context_score(players_df, context_agg):
    """Build situational performance score."""
    print("\nComputing context score...")

    df = players_df.merge(context_agg, on="PLAYER_ID", how="left")

    # Clutch performance vs blowout — does player elevate or shrink?
    df["CLUTCH_VS_BLOWOUT"] = df["FG_PCT_CLUTCH"] - df["FG_PCT_BLOWOUT"]

    # Late game vs early game
    df["LATE_VS_EARLY"] = df["FG_PCT_LATE_GAME"] - df["FG_PCT_EARLY_GAME"]

    # Home vs away consistency
    df["HOME_AWAY_CONSISTENCY"] = 1 - (df["FG_PCT_HOME"] - df["FG_PCT_AWAY"]).abs()

    # Shot clock discipline — early clock efficiency
    df["CLOCK_DISCIPLINE"] = df["FG_PCT_EARLY_CLOCK"] - df["FG_PCT_LATE_CLOCK"]

    # Fill nulls
    context_cols = ["CLUTCH_VS_BLOWOUT", "LATE_VS_EARLY", 
                    "HOME_AWAY_CONSISTENCY", "CLOCK_DISCIPLINE"]
    for col in context_cols:
        df[col] = df[col].fillna(0)

    # Scale and score
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[context_cols])
    scaled_df = pd.DataFrame(scaled, columns=context_cols)

    weights = {
        "CLUTCH_VS_BLOWOUT":      0.40,  # most important
        "LATE_VS_EARLY":          0.25,  # late game elevation
        "HOME_AWAY_CONSISTENCY":  0.20,  # consistent regardless of venue
        "CLOCK_DISCIPLINE":       0.15,  # disciplined shot selection
    }

    df["CONTEXT_SCORE"] = sum(
        scaled_df[col] * w for col, w in weights.items()
    )

    d = df["CONTEXT_SCORE"]
    df["CONTEXT_SCORE"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    return df

def print_results(df):
    qualified = df[(df["PTS"] >= 10) & (df["CLUTCH_ATTEMPTS"] >= 35) & (df["FGA"] >= 8)].copy()
    print("\n--- Top 15 Context Score (10+ PPG, 20+ clutch attempts) ---")
    top = qualified.nlargest(15, "CONTEXT_SCORE")[
        ["PLAYER_NAME", "CONTEXT_SCORE", "FG_PCT_CLUTCH", "FG_PCT_BLOWOUT",
         "FG_PCT_LATE_GAME", "FG_PCT_EARLY_GAME", "CLUTCH_ATTEMPTS", "PTS"]
    ].round(3)
    print(top.to_string(index=False))

    print("\n--- Clutch Kings (ranked by clutch FG%) ---")
    clutch = qualified.nlargest(15, "FG_PCT_CLUTCH")[
        ["PLAYER_NAME", "FG_PCT_CLUTCH", "CLUTCH_ATTEMPTS", "CONTEXT_SCORE", "PTS"]
    ].round(3)
    print(clutch.to_string(index=False))

def main():
    players_df, shots_df, context_df = load_data()
    shots_df = attach_context_to_shots(shots_df, context_df)
    context_agg = build_game_context_features(shots_df)
    df = compute_context_score(players_df, context_agg)
    df.to_csv(DATA_DIR / "players_with_context.csv", index=False)
    print_results(df)
    print("\n Stage 4 complete — saved to data/players_with_context.csv")

if __name__ == "__main__":
    main()