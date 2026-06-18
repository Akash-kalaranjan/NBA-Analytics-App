import pandas as pd
import numpy as np
from pathlib import Path
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    playerdashptshots,
    teamplayeronoffdetails,
    leaguegamefinder
)
import time
from nba_api.stats.static import teams


try:
    from .stage1_volume import main as stage1
    from .stage2_effeciency import main as stage2
    from .stage3_shotdifficulty import main as stage3
    from .stage4_gamecontext import main as stage4
    from .stage5_teamindependence import main as stage5
    from .final_model import main as final
except ImportError:
    from stage1_volume import main as stage1
    from stage2_effeciency import main as stage2
    from stage3_shotdifficulty import main as stage3
    from stage4_gamecontext import main as stage4
    from stage5_teamindependence import main as stage5
    from final_model import main as final

DATA_DIR = Path(__file__).parent.parent / "Data"
SEASON = "2025-26"

NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
}


# ── Fetch Functions ───────────────────────────────────────────────────────────

def fetch_player_stats(season_type):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    print(f"\nFetching player stats ({season_type})...")

    base = None
    for attempt in range(5):
        try:
            base = leaguedashplayerstats.LeagueDashPlayerStats(
                season=SEASON,
                season_type_all_star=season_type,
                per_mode_detailed="PerGame",
                measure_type_detailed_defense="Base"
            ).get_data_frames()[0]
            break
        except Exception:
            print(f"  Base timeout, retrying ({attempt + 1}/5)...")
            time.sleep(5)

    if base is None:
        raise RuntimeError("Failed to fetch base player stats after 5 attempts")

    advanced = None
    for attempt in range(5):
        try:
            advanced = leaguedashplayerstats.LeagueDashPlayerStats(
                season=SEASON,
                season_type_all_star=season_type,
                per_mode_detailed="PerGame",
                measure_type_detailed_defense="Advanced"
            ).get_data_frames()[0]
            break
        except Exception:
            print(f"  Advanced timeout, retrying ({attempt + 1}/5)...")
            time.sleep(5)

    if advanced is None:
        raise RuntimeError("Failed to fetch advanced player stats after 5 attempts")

    df = pd.merge(base, advanced, on="PLAYER_ID", suffixes=("", "_adv"))
    df = df[df["PLAYER_NAME"] != "Deni Avdija"]
    if season_type == "Regular Season":
        df = df[(df["GP"] >= 20) & (df["MIN"] >= 12)].reset_index(drop=True)
    else:
        df = df[(df["GP"] >= 3) & (df["MIN"] >= 5)].reset_index(drop=True)
    path = DATA_DIR / f"players_final{suffix}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} players -> {path.name}")

def fetch_shot_data(season_type):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    print(f"\nFetching shot data ({season_type})...")
    from nba_api.stats.endpoints import shotchartdetail
    
    df = None
    for attempt in range(5):
        try:
            df = shotchartdetail.ShotChartDetail(
                team_id=0,
                player_id=0,
                season_nullable=SEASON,
                season_type_all_star=season_type,
                context_measure_simple="FGA"
            ).get_data_frames()[0]
            break
        except Exception:
            print(f"  Timeout, retrying ({attempt + 1}/5)...")
            time.sleep(5)
    
    if df is None:
        raise RuntimeError("Failed to fetch shot data after 5 attempts")
    
    path = DATA_DIR / f"shot_quality_raw{suffix}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved {len(df)} shots -> {path.name}")

def fetch_game_context(season_type):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    print(f"\nFetching game context ({season_type})...")
    
    games = None
    for attempt in range(5):
        try:
            games = leaguegamefinder.LeagueGameFinder(
                season_nullable=SEASON,
                season_type_nullable="Playoffs" if season_type == "Playoffs" else "Regular Season"
            ).get_data_frames()[0]
            break
        except Exception:
            print(f"  Timeout, retrying ({attempt + 1}/5)...")
            time.sleep(5)
    
    if games is None:
        raise RuntimeError("Failed to fetch game context after 5 attempts")
    
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"])
    games = games.sort_values(["TEAM_ID", "GAME_DATE"]).reset_index(drop=True)
    games["REST_DAYS"] = games.groupby("TEAM_ID")["GAME_DATE"].diff().dt.days.fillna(3)
    games["SCORE_MARGIN"] = games["PLUS_MINUS"]
    games["IS_BLOWOUT"] = (games["SCORE_MARGIN"].abs() >= 20).astype(int)
    games["IS_CLOSE_GAME"] = (games["SCORE_MARGIN"].abs() <= 5).astype(int)
    path = DATA_DIR / f"game_context{suffix}.csv"
    games.to_csv(path, index=False)
    print(f"  Saved {len(games)} game rows → {path.name}")


def build(season_type):
    print(f"\n{'='*50}")
    print(f"  BUILDING: {season_type}")
    print(f"{'='*50}")
    fetch_player_stats(season_type)
    fetch_shot_data(season_type)
    fetch_game_context(season_type)
    stage1(season_type)
    stage2(season_type)
    stage3(season_type)
    stage4(season_type)
    stage5(season_type)
    final(season_type)
    print(f"\n  {season_type} build complete.")

if __name__ == "__main__":
    build("Regular Season")
    build("Playoffs")
    print("\n=== Full dataset rebuild complete ===")