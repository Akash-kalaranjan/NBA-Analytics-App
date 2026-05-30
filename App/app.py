import base64
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "Data" / "players_final_scores.csv"
HERO_VIDEO_PATH = BASE_DIR / "App" / "assets" / "hero-basketball.mp4.mp4"


st.set_page_config(
    page_title="NBA True Scoring Impact",
    layout="wide",
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_hero_video():
    if not HERO_VIDEO_PATH.exists():
        return ""

    encoded_video = base64.b64encode(HERO_VIDEO_PATH.read_bytes()).decode()
    return f"data:video/mp4;base64,{encoded_video}"


df = load_data()
hero_video = load_hero_video()

LINKEDIN_URL = "https://www.linkedin.com/in/akash-kalaranjan-9aa895255/"
YOUTUBE_URL = "https://www.youtube.com/channel/UC4UWs1H62Ao3QsYa4xEF-jA/"
STAGE_COLUMNS = {
    "Volume": "VOLUME_SCORE",
    "Efficiency": "EFFICIENCY_SCORE",
    "Shot Difficulty": "DIFFICULTY_ADJ_EFFICIENCY",
    "Game Context": "CONTEXT_SCORE",
    "Independence": "INDEPENDENCE_SCORE",
}


def format_percent(value):
    return f"{value * 100:.1f}%"


def build_stage_summary(player):
    stage_scores = {
        label: float(player[column])
        for label, column in STAGE_COLUMNS.items()
        if column in player and pd.notna(player[column])
    }
    strongest_stage = max(stage_scores, key=stage_scores.get)
    weakest_stage = min(stage_scores, key=stage_scores.get)

    return (
        f"{player['PLAYER_NAME']}'s profile is strongest in **{strongest_stage}** "
        f"and has the most room to grow in **{weakest_stage}**."
    )

st.markdown(
    """
    <style>
        .brand-shell {
            border-bottom: 1px solid rgba(120, 120, 120, 0.24);
            border-radius: 14px;
            margin-bottom: 1.4rem;
            min-height: 460px;
            overflow: hidden;
            padding: 3.4rem 0 4.2rem;
            position: relative;
            text-align: center;
        }

        .hero-video {
            height: 100%;
            inset: 0;
            object-fit: cover;
            opacity: 0.42;
            position: absolute;
            width: 100%;
            z-index: 0;
        }

        .hero-overlay {
            background:
                radial-gradient(circle at center, rgba(15, 23, 42, 0.54), rgba(3, 7, 18, 0.88) 72%),
                linear-gradient(180deg, rgba(3, 7, 18, 0.22), rgba(3, 7, 18, 0.84));
            inset: 0;
            position: absolute;
            z-index: 1;
        }

        .brand-content {
            position: relative;
            z-index: 2;
        }

        .brand-row {
            align-items: center;
            display: flex;
            gap: 1.6rem;
            justify-content: center;
            margin: 0 auto 1.7rem;
        }

        .brand-mark {
            align-items: center;
            background:
                radial-gradient(circle at 35% 28%, #fb923c 0 18%, transparent 19%),
                linear-gradient(135deg, #f97316 0%, #ea580c 52%, #9a3412 100%);
            border: 5px solid #0b0f19;
            border-radius: 50%;
            box-shadow:
                inset 0 0 0 3px #fbbf24,
                0 0 0 1px rgba(251, 191, 36, 0.55);
            color: #f9fafb;
            display: inline-flex;
            font-size: 2.4rem;
            font-weight: 800;
            height: 7rem;
            justify-content: center;
            letter-spacing: 0;
            position: relative;
            text-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
            width: 7rem;
        }

        .brand-mark::before,
        .brand-mark::after {
            content: "";
            inset: 14%;
            pointer-events: none;
            position: absolute;
        }

        .brand-mark::before {
            border-left: 4px solid rgba(17, 24, 39, 0.86);
            border-right: 4px solid rgba(17, 24, 39, 0.86);
            border-radius: 50%;
        }

        .brand-mark::after {
            border-top: 4px solid rgba(17, 24, 39, 0.86);
            border-bottom: 4px solid rgba(17, 24, 39, 0.86);
            border-radius: 50%;
            transform: rotate(-18deg);
        }

        .brand-mark span {
            position: relative;
            z-index: 1;
        }

        .brand-name {
            font-size: 7.2rem;
            font-weight: 800;
            letter-spacing: 0;
            line-height: 1;
            margin: 0;
        }

        .brand-clutch {
            background: linear-gradient(90deg, #38bdf8, #f97316);
            -webkit-background-clip: text;
            color: transparent;
        }

        .brand-highlight {
            background: linear-gradient(90deg, #f59e0b, #14b8a6);
            -webkit-background-clip: text;
            color: transparent;
        }

        .brand-copy {
            color: #9ca3af;
            display: block;
            font-size: 1.5rem;
            line-height: 1.6;
            margin: 1.45rem auto 1.2rem;
            max-width: 900px;
            text-align: center;
            width: 100%;
        }

        .brand-quote {
            color: #e5e7eb;
            display: block;
            font-size: 1.45rem;
            font-style: italic;
            font-weight: 600;
            margin: 0 auto 2rem;
            text-align: center;
            width: 100%;
        }

        .link-row {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
        }

        .link-pill {
            border: 1px solid rgba(249, 250, 251, 0.26);
            border-radius: 999px;
            color: #f9fafb !important;
            display: inline-block;
            font-size: 1.25rem;
            font-weight: 650;
            padding: 0.8rem 1.35rem;
            text-decoration: none !important;
        }

        .link-pill:hover {
            border-color: #14b8a6;
            color: #5eead4 !important;
        }

        @media (max-width: 900px) {
            .brand-shell {
                min-height: 480px;
                padding: 3.7rem 0 3.8rem;
            }

            .brand-row {
                align-items: center;
                flex-direction: column;
                gap: 1.25rem;
            }

            .brand-mark {
                font-size: 2rem;
                height: 6rem;
                width: 6rem;
            }

            .brand-name {
                font-size: 4.8rem;
            }

            .brand-copy {
                font-size: 1.3rem;
            }

            .brand-quote {
                font-size: 1.3rem;
            }

            .link-pill {
                font-size: 1.15rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    page = st.radio(
        "Navigation",
        ["Home", "Leaderboard", "Player Profile"],
    )

if page == "Home":
    st.markdown(
        f"""
        <section class="brand-shell">
            <video class="hero-video" autoplay muted loop playsinline>
                <source src="{hero_video}" type="video/mp4">
            </video>
            <div class="hero-overlay"></div>
            <div class="brand-content">
                <div class="brand-row">
                    <div class="brand-mark"><span>CA</span></div>
                    <h1 class="brand-name"><span class="brand-clutch">Clutch</span> <span class="brand-highlight">Analytics</span></h1>
                </div>
                <p class="brand-copy">
                    A scoring impact dashboard for finding who creates efficient offense,
                    who scales under difficult shot diets, and which players deserve more
                    attention than their raw points per game suggest.
                </p>
                <p class="brand-quote">"A brand new perspective of the same art"</p>
                <div class="link-row">
                    <a class="link-pill" href="{LINKEDIN_URL}" target="_blank">LinkedIn</a>
                    <a class="link-pill" href="{YOUTUBE_URL}" target="_blank">YouTube</a>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    col1.metric("Players", len(df))
    col2.metric("Teams", df["TEAM_ABBREVIATION"].nunique())

    st.subheader("Top Scorers by True Scoring Impact")

    top_players = df.sort_values("TRUE_SCORING_IMPACT", ascending=False).head(25)

    st.dataframe(
        top_players[
            [
                "PLAYER_NAME",
                "TEAM_ABBREVIATION",
                "PTS",
                "TS_PCT",
                "USG_PCT",
                "TRUE_SCORING_IMPACT",
            ]
        ],
        width="stretch",
    )

if page == "Leaderboard":
    st.title("Scoring Impact Leaderboard")

    team_options = ["All"] + sorted(df["TEAM_ABBREVIATION"].dropna().unique().tolist())

    with st.sidebar:
        st.header("Filters")

        selected_team = st.selectbox("Team", team_options)
        min_ppg = st.slider("Minimum PPG", 0.0, float(df["PTS"].max()), 10.0, 0.5)
        min_minutes = st.slider(
            "Minimum Minutes",
            0.0,
            float(df["MIN"].max()),
            15.0,
            0.5,
        )
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

if page == "Player Profile":
    st.title("Player Profile")
    st.write("Select a player to see their scoring impact profile and stage breakdown.")

    ranked_df = df.sort_values("TRUE_SCORING_IMPACT", ascending=False).reset_index(drop=True)
    ranked_df["RANK"] = ranked_df.index + 1

    player_names = ranked_df["PLAYER_NAME"].sort_values().tolist()
    selected_player = st.selectbox("Choose a player", player_names)

    player = ranked_df[ranked_df["PLAYER_NAME"] == selected_player].iloc[0]

    st.subheader(f"{player['PLAYER_NAME']} - {player['TEAM_ABBREVIATION']}")

    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Rank", f"#{int(player['RANK'])}")
    metric_col2.metric("Impact", f"{player['TRUE_SCORING_IMPACT']:.1f}")
    metric_col3.metric("PPG", f"{player['PTS']:.1f}")
    metric_col4.metric("TS%", format_percent(player["TS_PCT"]))
    metric_col5.metric("Usage", format_percent(player["USG_PCT"]))

    st.markdown(build_stage_summary(player))

    stage_data = pd.DataFrame(
        {
            "Stage": list(STAGE_COLUMNS.keys()),
            "Score": [player[column] for column in STAGE_COLUMNS.values()],
        }
    ).set_index("Stage")

    chart_col, table_col = st.columns([1.35, 1])

    with chart_col:
        st.subheader("Scoring Stage Breakdown")
        st.bar_chart(stage_data, height=360)

    with table_col:
        st.subheader("Player Snapshot")
        st.dataframe(
            pd.DataFrame(
                [
                    ["Team", player["TEAM_ABBREVIATION"]],
                    ["Games Played", int(player["GP"])],
                    ["Minutes", f"{player['MIN']:.1f}"],
                    ["Field Goal %", format_percent(player["FG_PCT"])],
                    ["Effective FG %", format_percent(player["EFG_PCT"])],
                    ["True Shooting %", format_percent(player["TS_PCT"])],
                    ["Usage %", format_percent(player["USG_PCT"])],
                    ["Net Rating", f"{player['NET_RATING']:.1f}"],
                ],
                columns=["Metric", "Value"],
            ),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Raw Stage Scores")
    st.dataframe(
        stage_data.reset_index(),
        hide_index=True,
        width="stretch",
    )
