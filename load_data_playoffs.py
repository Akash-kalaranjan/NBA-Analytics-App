import pandas as pd
import time
from nba_api.stats.endpoints import leaguedashplayerstats
from pathlib import Path

DATA_DIR = Path(__file__).parent / "Data"

SEASON = "2025-26" 
SEASON_TYPE = "Playoffs"

def fetch_general_stats():
    print("Fetching general player stats...")
    endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        per_mode_detailed="PerGame",
        season_type_all_star=SEASON_TYPE
    )
    time.sleep(1)
    df = endpoint.get_data_frames()[0]
    print(f"Rows fetched: {len(df)}")
    return df

def fetch_advanced_stats():
    print("Fetching advanced stats...")
    endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Advanced",
        season_type_all_star=SEASON_TYPE
    )
    time.sleep(1)
    df = endpoint.get_data_frames()[0]
    print(f"  Rows fetched: {len(df)}")
    return df

def fetch_shot_quality_stats():
    print("Fetching shot chart data...")
    from nba_api.stats.endpoints import shotchartdetail
    endpoint = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=0,
        season_nullable=SEASON,
        season_type_all_star=SEASON_TYPE,
        context_measure_simple="FGA"
    )
    time.sleep(2)
    df = endpoint.get_data_frames()[0]
    print(f"  Shots fetched: {len(df)}")
    return df

def fetch_player_shot_splits(general_df):
    print("Fetching player shot splits...")
    from nba_api.stats.endpoints import playerdashptshots
    player_ids = general_df["PLAYER_ID"].unique()
    all_data = []
    for i, player_id in enumerate(player_ids):
        try:
            endpoint = playerdashptshots.PlayerDashPtShots(
                player_id=int(player_id),
                team_id=0,
                season=SEASON,
                season_type_all_star=SEASON_TYPE
            )
            time.sleep(0.6)
            dfs = endpoint.get_data_frames()
            if len(dfs) > 0:
                df = dfs[0]
                df["PLAYER_ID"] = player_id
                all_data.append(df)
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(player_ids)} players fetched")
        except Exception as e:
            print(f"  Skipped player {player_id}: {e}")
            continue
    if not all_data:
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)

def fetch_on_off_splits():
    print("Fetching on/off court splits...")
    from nba_api.stats.endpoints import teamplayeronoffsummary
    from nba_api.stats.static import teams
    all_teams = teams.get_teams()
    all_data = []
    for team in all_teams:
        try:
            endpoint = teamplayeronoffsummary.TeamPlayerOnOffSummary(
                team_id=team["id"],
                season=SEASON,
                season_type_all_star=SEASON_TYPE
            )
            time.sleep(0.6)
            dfs = endpoint.get_data_frames()
            if len(dfs) >= 2:
                on_df = dfs[1].copy()
                on_df["ON_OFF"] = "ON"
                off_df = dfs[2].copy()
                off_df["ON_OFF"] = "OFF"
                all_data.extend([on_df, off_df])
            print(f"  Fetched: {team['abbreviation']}")
        except Exception as e:
            print(f"  Skipped {team['abbreviation']}: {e}")
            continue
    return pd.concat(all_data, ignore_index=True)

def merge_stats(general_df, advanced_df):
    merged = pd.merge(
        general_df,
        advanced_df,
        on=["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION"],
        suffixes=("_gen", "_adv")
    )
    return merged

def filter_minutes(df):
    filtered = df[(df["MIN_gen"] >= 12) & (df["GP_gen"] >= 3)].copy()
    filtered = filtered[filtered["PLAYER_NAME"] != "Deni Avdija"]
    print(f"  Players after filter: {len(filtered)}")
    return filtered

def main():
    general_df = fetch_general_stats()
    advanced_df = fetch_advanced_stats()
    shot_df = fetch_shot_quality_stats()
    split_df = fetch_player_shot_splits(general_df)
    merged_df = merge_stats(general_df, advanced_df)
    clean_df = filter_minutes(merged_df)
    onoff_df = fetch_on_off_splits()

    onoff_df.to_csv(DATA_DIR / "on_off_splits_playoffs.csv", index=False)
    merged_df.to_csv(DATA_DIR / "merged_stats_raw_playoffs.csv", index=False)
    clean_df.to_csv(DATA_DIR / "player_stats_clean_playoffs.csv", index=False)
    shot_df.to_csv(DATA_DIR / "shot_quality_raw_playoffs.csv", index=False)
    split_df.to_csv(DATA_DIR / "player_shot_splits_playoffs.csv", index=False)

    print("\nDone!")

if __name__ == "__main__":
    main()