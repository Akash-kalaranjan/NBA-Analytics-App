import pandas as pd
from pathlib import Path

DATA_DIR = Path('Data')
source = DATA_DIR / 'player_stats_clean_playoffs.csv'
out = DATA_DIR / 'players_final_playoffs.csv'

cols = [
    'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'AGE_gen',
    'GP_gen', 'MIN_gen', 'USG_PCT', 'PTS', 'FGM_gen', 'FGA_gen', 'FG_PCT_gen',
    'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'TS_PCT', 'EFG_PCT',
    'AST', 'TOV', 'AST_PCT', 'AST_TO', 'TM_TOV_PCT', 'REB', 'OREB_PCT', 'DREB_PCT',
    'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'PLUS_MINUS', 'PIE', 'PACE'
]

df = pd.read_csv(source)
df = df[cols].copy()
df = df.rename(columns={
    'AGE_gen': 'AGE',
    'GP_gen': 'GP',
    'MIN_gen': 'MIN',
    'FGM_gen': 'FGM',
    'FGA_gen': 'FGA',
    'FG_PCT_gen': 'FG_PCT',
})

df.to_csv(out, index=False)
print(f'wrote {out} shape={df.shape}')
