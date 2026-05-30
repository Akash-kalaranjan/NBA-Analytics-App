from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "Data" / "players_final_scores.csv"


st.set_page_config(
    page_title="Leaderboard",
    layout="wide",
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


df = load_data()

st.title("Scoring Impact Leaderboard")

team_options = ["All"] + sorted(df["TEAM_ABBREVIATION"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filters")

    selected_team = st.selectbox("Team", team_options)
    min_ppg = st.slider("Minimum PPG", 0.0, float(df["PTS"].max()), 10.0, 0.5)
    min_minutes = st.slider("Minimum Minutes", 0.0, float(df["MIN"].max()), 15.0, 0.5)
    min_games = st.slider("Minimum Games Played", 0, int(df["GP"].max()), 20, 1)
    search = st.text_input("Search player")

filtered = df.copy()

if selected_team != "All":
    filtered = filtered[filtered["TEAM_ABBREVIATION"] == selected_team]

filtered = filtered[
    (filtered["PTS"] >= min_ppg)
    & (filtered["MIN"] >= min_minutes)
    & (filtered["GP"] >= min_games)
]

if search:
    filtered = filtered[
        filtered["PLAYER_NAME"].str.contains(search, case=False, na=False)
    ]

leaderboard = filtered.sort_values(
    "TRUE_SCORING_IMPACT",
    ascending=False,
).copy()

leaderboard.insert(0, "RANK", range(1, len(leaderboard) + 1))

st.caption(f"{len(leaderboard)} players match your filters")

st.dataframe(
    leaderboard[
        [
            "RANK",
            "PLAYER_NAME",
            "TEAM_ABBREVIATION",
            "PTS",
            "TS_PCT",
            "USG_PCT",
            "MIN",
            "GP",
            "TRUE_SCORING_IMPACT",
        ]
    ],
    width="stretch",
)
