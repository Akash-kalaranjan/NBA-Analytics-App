import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "Data"

def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    players_df = pd.read_csv(DATA_DIR / f"players_with_difficulty{suffix}.csv")
    shots_df = pd.read_csv(DATA_DIR / f"shot_quality_raw{suffix}.csv")
    context_df = pd.read_csv(DATA_DIR / f"game_context{suffix}.csv")
    players_df = players_df[players_df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Players: {len(players_df)}")
    print(f"Shots: {len(shots_df)}")
    print(f"Game context: {len(context_df)}")
    return players_df, shots_df, context_df

def attach_context_to_shots(shots_df, context_df):
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
    print("\nBuilding game context features...")

    shots_df["IS_EARLY_GAME"] = (shots_df["PERIOD"] <= 2).astype(int)
    shots_df["IS_LATE_GAME"] = (
        (shots_df["PERIOD"] == 4) & (shots_df["MINUTES_REMAINING"] <= 5)
    ).astype(int)

    shots_df["IS_CLUTCH"] = (
        (shots_df["IS_CLOSE_GAME"] == 1) & (shots_df["PERIOD"] == 4)
    ).astype(int)

    shots_df["SHOT_CLOCK_SECONDS"] = (
        shots_df["MINUTES_REMAINING"] * 60 + shots_df["SECONDS_REMAINING"]
    )
    shots_df["IS_EARLY_CLOCK"] = (shots_df["SHOT_CLOCK_SECONDS"] >= 15).astype(int)
    shots_df["IS_LATE_CLOCK"] = (shots_df["SHOT_CLOCK_SECONDS"] <= 4).astype(int)

    shots_df["IS_HOME"] = (shots_df["HTM"] == shots_df["TEAM_NAME"].map(
        shots_df.groupby("TEAM_NAME")["HTM"].agg(lambda x: x.mode()[0])
    )).astype(int)

    agg = shots_df.groupby("PLAYER_ID").agg(
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
    print("\nComputing context score...")

    df = players_df.merge(context_agg, on="PLAYER_ID", how="left")

    df["CLUTCH_VS_BLOWOUT"] = df["FG_PCT_CLUTCH"] - df["FG_PCT_BLOWOUT"]
    df["LATE_VS_EARLY"] = df["FG_PCT_LATE_GAME"] - df["FG_PCT_EARLY_GAME"]
    df["HOME_AWAY_CONSISTENCY"] = 1 - (df["FG_PCT_HOME"] - df["FG_PCT_AWAY"]).abs()
    df["CLOCK_DISCIPLINE"] = df["FG_PCT_EARLY_CLOCK"] - df["FG_PCT_LATE_CLOCK"]

    context_cols = ["CLUTCH_VS_BLOWOUT", "LATE_VS_EARLY",
                    "HOME_AWAY_CONSISTENCY", "CLOCK_DISCIPLINE"]
    for col in context_cols:
        df[col] = df[col].fillna(0)

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[context_cols])
    scaled_df = pd.DataFrame(scaled, columns=context_cols)

    weights = {
        "CLUTCH_VS_BLOWOUT":     0.40,
        "LATE_VS_EARLY":         0.25,
        "HOME_AWAY_CONSISTENCY": 0.20,
        "CLOCK_DISCIPLINE":      0.15,
    }

    df["CONTEXT_SCORE"] = sum(
        scaled_df[col] * w for col, w in weights.items()
    )

    d = df["CONTEXT_SCORE"]
    df["CONTEXT_SCORE"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    return df

def print_results(df):
    qualified = df[df["PTS"] >= 10].copy()
    print("\n--- Top 15 Context Score (10+ PPG, 35+ clutch attempts) ---")
    top = qualified.nlargest(15, "CONTEXT_SCORE")[
        ["PLAYER_NAME", "CONTEXT_SCORE", "FG_PCT_CLUTCH", "FG_PCT_BLOWOUT",
         "FG_PCT_LATE_GAME", "FG_PCT_EARLY_GAME", "CLUTCH_ATTEMPTS", "PTS"]
    ].round(3)
    print(top.to_string(index=False).encode("cp1252", errors="ignore").decode("cp1252"))

def main(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    players_df, shots_df, context_df = load_data(season_type)
    shots_df = attach_context_to_shots(shots_df, context_df)
    context_agg = build_game_context_features(shots_df)
    df = compute_context_score(players_df, context_agg)
    out_path = DATA_DIR / f"players_with_context{suffix}.csv"
    df.to_csv(out_path, index=False)
    print_results(df)
    print(f"\n Stage 4 complete — saved to {out_path.name}")

if __name__ == "__main__":
    main()