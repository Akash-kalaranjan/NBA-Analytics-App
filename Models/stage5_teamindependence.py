import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "data"

def load_data():
    players_df = pd.read_csv(DATA_DIR / "players_with_context.csv")
    onoff_df = pd.read_csv(DATA_DIR / "on_off_splits.csv")
    players_df = players_df[players_df["PLAYER_NAME"] != "Deni Avdija"].reset_index(drop=True)
    print(f"Players: {len(players_df)}")
    print(f"On/off rows: {len(onoff_df)}")
    return players_df, onoff_df

def compute_team_independence(players_df, onoff_df):
    print("\nComputing team independence...")

    # Separate ON and OFF rows
    on_df = onoff_df[onoff_df["ON_OFF"] == "ON"][
        ["VS_PLAYER_ID", "NET_RATING", "OFF_RATING", "PLUS_MINUS"]
    ].rename(columns={
        "NET_RATING":  "NET_RATING_ON",
        "OFF_RATING":  "OFF_RATING_ON",
        "PLUS_MINUS":  "PLUS_MINUS_ON"
    })

    off_df = onoff_df[onoff_df["ON_OFF"] == "OFF"][
        ["VS_PLAYER_ID", "NET_RATING", "OFF_RATING", "PLUS_MINUS"]
    ].rename(columns={
        "NET_RATING":  "NET_RATING_OFF",
        "OFF_RATING":  "OFF_RATING_OFF",
        "PLUS_MINUS":  "PLUS_MINUS_OFF"
    })

    # Merge ON and OFF into one row per player
    impact_df = pd.merge(on_df, off_df, on="VS_PLAYER_ID", how="inner")

    # Deduplicate traded players by averaging across stints
    impact_df = impact_df.groupby("VS_PLAYER_ID").agg({
        "NET_RATING_ON":  "mean",
        "OFF_RATING_ON":  "mean",
        "PLUS_MINUS_ON":  "mean",
        "NET_RATING_OFF": "mean",
        "OFF_RATING_OFF": "mean",
        "PLUS_MINUS_OFF": "mean",
    }).reset_index()

    # Recalculate impact after averaging
    impact_df["NET_RATING_IMPACT"] = impact_df["NET_RATING_ON"] - impact_df["NET_RATING_OFF"]
    impact_df["OFF_RATING_IMPACT"] = impact_df["OFF_RATING_ON"] - impact_df["OFF_RATING_OFF"]

    print(f"  Players with on/off data: {len(impact_df)}")
    return impact_df

def compute_independence_score(players_df, impact_df):
    """
    Combine on/off impact with existing efficiency data.
    Players who score independently of team context score higher.
    """
    df = pd.merge(
        players_df,
        impact_df[["VS_PLAYER_ID", "NET_RATING_IMPACT", 
                   "OFF_RATING_IMPACT", "NET_RATING_ON", 
                   "NET_RATING_OFF"]],
        left_on="PLAYER_ID",
        right_on="VS_PLAYER_ID",
        how="left"
    )

    # Fill missing with median
    for col in ["NET_RATING_IMPACT", "OFF_RATING_IMPACT"]:
        df[col] = df[col].fillna(df[col].median())

    # Scale features
    scaler = MinMaxScaler()

    features = {
        "NET_RATING_IMPACT":  0.50,  # how much team improves with player on
        "OFF_RATING_IMPACT":  0.30,  # offensive impact specifically
        "NET_RATING_ON":      0.20,  # absolute team quality when on court
    }

    for col in features:
        df[col] = df[col].fillna(df[col].median())

    scaled = scaler.fit_transform(df[list(features.keys())])
    scaled_df = pd.DataFrame(scaled, columns=list(features.keys()))

    df["INDEPENDENCE_SCORE"] = sum(
        scaled_df[col] * weight
        for col, weight in features.items()
    )

    d = df["INDEPENDENCE_SCORE"]
    df["INDEPENDENCE_SCORE"] = ((d - d.min()) / (d.max() - d.min()) * 100).round(1)

    return df

def print_results(df):
    qualified = df[df["PTS"] >= 10].copy()

    print("\n--- Top 15 Team Independence Score (10+ PPG) ---")
    top = qualified.nlargest(15, "INDEPENDENCE_SCORE")[
        ["PLAYER_NAME", "INDEPENDENCE_SCORE", "NET_RATING_IMPACT",
         "OFF_RATING_IMPACT", "NET_RATING_ON", "PTS"]
    ].round(2)
    print(top.to_string(index=False))

    print("\n--- Biggest Team Lifters (NET_RATING_IMPACT) ---")
    lifters = qualified.nlargest(15, "NET_RATING_IMPACT")[
        ["PLAYER_NAME", "NET_RATING_IMPACT", "NET_RATING_ON",
         "NET_RATING_OFF", "INDEPENDENCE_SCORE", "PTS"]
    ].round(2)
    print(lifters.to_string(index=False))

def main():
    players_df, onoff_df = load_data()
    impact_df = compute_team_independence(players_df, onoff_df)
    df = compute_independence_score(players_df, impact_df)
    df.to_csv(DATA_DIR / "players_with_independence.csv", index=False)
    print_results(df)
    print("\n Stage 5 complete — saved to data/players_with_independence.csv")

if __name__ == "__main__":
    main()