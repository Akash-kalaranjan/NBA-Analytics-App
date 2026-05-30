import pandas as pd
import time
from pathlib import Path
from nba_api.stats.endpoints import leaguegamelog

DATA_DIR = Path(__file__).parent

SEASON = "2025-26"

def pull_game_log():
    print("Pulling game log...")
    log = leaguegamelog.LeagueGameLog(
        season=SEASON,
        season_type_all_star="Regular Season"
    )
    df = log.get_data_frames()[0]
    print(f"  Rows: {len(df)}")
    return df

def calc_rest_days(df):
    print("Calculating rest days...")
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["TEAM_ID", "GAME_DATE"])
    df["REST_DAYS"] = df.groupby("TEAM_ID")["GAME_DATE"].diff().dt.days - 1
    df["REST_DAYS"] = df["REST_DAYS"].fillna(3).clip(upper=7)
    return df

def calc_score_margin(df):
    print("Calculating score margin...")
    # PLUS_MINUS is final margin from each team's perspective
    # We want absolute margin to identify blowouts
    df["SCORE_MARGIN"] = df["PLUS_MINUS"]
    df["IS_BLOWOUT"] = (df["PLUS_MINUS"].abs() >= 15).astype(int)
    df["IS_CLOSE_GAME"] = (df["PLUS_MINUS"].abs() <= 5).astype(int)
    return df

def main():
    df = pull_game_log()
    df = calc_rest_days(df)
    df = calc_score_margin(df)
    
    cols = ["GAME_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GAME_DATE", 
            "REST_DAYS", "SCORE_MARGIN", "IS_BLOWOUT", "IS_CLOSE_GAME", "WL"]
    df = df[cols]
    
    df.to_csv(DATA_DIR / "game_context.csv", index=False)
    print(f"\nSaved: {len(df)} rows to data/game_context.csv")
    print(df.head(5).to_string(index=False))

if __name__ == "__main__":
    main()