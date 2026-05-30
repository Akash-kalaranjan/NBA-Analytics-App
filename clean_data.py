import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def load_data():
    df = pd.read_csv(DATA_DIR / "player_stats_clean.csv")
    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    return df

def select_columns(df):
    cols = [
        # Identity
        "PLAYER_ID",
        "PLAYER_NAME", "TEAM_ABBREVIATION", "AGE_gen",

        # Volume / Opportunity
        "GP_gen", "MIN_gen", "USG_PCT",

        # Scoring
        "PTS", "FGM_gen", "FGA_gen", "FG_PCT_gen",
        "FG3M", "FG3A", "FG3_PCT",
        "FTM", "FTA", "FT_PCT",

        # Efficiency
        "TS_PCT", "EFG_PCT",

        # Playmaking context
        "AST", "TOV", "AST_PCT", "AST_TO", "TM_TOV_PCT",

        # Rebounding
        "REB", "OREB_PCT", "DREB_PCT",

        # Team impact
        "OFF_RATING", "DEF_RATING", "NET_RATING",
        "PLUS_MINUS", "PIE",

        # Pace context
        "PACE",
    ]

    df = df[cols].copy()
    print(f"Columns after selection: {df.shape[1]}")
    return df

def rename_columns(df):
    df = df.rename(columns={
        "AGE_gen": "AGE",
        "GP_gen": "GP",
        "MIN_gen": "MIN",
        "FGM_gen": "FGM",
        "FGA_gen": "FGA",
        "FG_PCT_gen": "FG_PCT",
    })
    return df

def main():
    df = load_data()
    df = select_columns(df)
    df = rename_columns(df)
    df.to_csv(DATA_DIR / "players_final.csv", index=False)
    print(f"\n Done!")
    print(f"   Final dataset: {df.shape}")
    print(f"   Saved → data/players_final.csv")
    print(f"\nFirst 5 players:")
    print(df[["PLAYER_NAME", "PTS", "TS_PCT", "USG_PCT"]].head())

if __name__ == "__main__":
    main()