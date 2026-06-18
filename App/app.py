import base64
import random
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from datetime import date
import subprocess


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH_REG = BASE_DIR / "Data" / "players_final_scores.csv"
DATA_PATH_PLAYOFFS = BASE_DIR / "Data" / "players_final_scores_playoffs.csv"
HERO_VIDEO_PATH = BASE_DIR / "App" / "Assets" / "hero-basketball.mp4.mp4"

st.html('<meta name="google-site-verification" content="p9RdibTQo_49SyVWhAZzwS3iosOJ-Vb_jUrXvL-gpA8" />')

st.set_page_config(
    page_title="NBA True Scoring Impact",
    layout="wide",
)

@st.cache_data(ttl=86400)
def load_data(season_type="Regular Season"):
    suffix = "_playoffs" if season_type == "Playoffs" else ""
    path = BASE_DIR / "Data" / f"players_final_scores{suffix}.csv"
    build_script = BASE_DIR / "build_dataset.py"

    # Rebuild if file is missing or from a previous day
    needs_rebuild = (
        not path.exists() or
        date.fromtimestamp(path.stat().st_mtime) < date.today()
    )

    if needs_rebuild:
        result = subprocess.run(["python", str(build_script)])
        if result.returncode != 0:
            st.warning("Data refresh , using cached data.")

    if season_type == "Playoffs":
        if path.exists():
            return pd.read_csv(path)
        st.warning("Playoff data not available yet — showing regular season.")
        return pd.read_csv(BASE_DIR / "Data" / "players_final_scores.csv")

    return pd.read_csv(path)


@st.cache_data
def load_hero_video():
    if not HERO_VIDEO_PATH.exists():
        return ""

    encoded_video = base64.b64encode(HERO_VIDEO_PATH.read_bytes()).decode()
    return f"data:video/mp4;base64,{encoded_video}"


hero_video = load_hero_video()  # doesn't need season_type, fine up here

with st.sidebar:
    season_label = st.radio("Season Type", ["Regular Season (2025-26)", "Playoffs (2025-26)"])
    season_type = "Playoffs" if season_label.startswith("Playoffs") else "Regular Season"

with st.spinner("Refreshing data from NBA API..."):
    df = load_data(season_type)

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

def color_rank_columns(df, exclude_cols):
    colors = ["#16a34a", "#ca8a04", "#ea580c", "#dc2626"]  # green, yellow, orange, red
    
    def rank_color(col):
        if col.name in exclude_cols:
            return [""] * len(col)

        numeric = pd.to_numeric(col, errors="coerce")
        if numeric.notna().sum() == 0:
            return [""] * len(col)

        ranks = numeric.rank(ascending=False, method="first")
        styles = []

        for rank in ranks:
            if pd.isna(rank) or rank > len(colors):
                styles.append("")
            else:
                color = colors[int(rank) - 1]
                styles.append(f"background-color: {color}; color: white")

        return styles
    
    return df.style.apply(rank_color, axis=0)


def add_underrated_scores(source_df):
    result = source_df.copy()
    feature_cols = ["PTS", "USG_PCT", "MIN"]
    target_col = "TRUE_SCORING_IMPACT"

    model_df = result[feature_cols + [target_col]].dropna()
    x = model_df[feature_cols].to_numpy(dtype=float)
    y = model_df[target_col].to_numpy(dtype=float)

    x_with_intercept = np.column_stack([np.ones(len(x)), x])
    coefficients, *_ = np.linalg.lstsq(x_with_intercept, y, rcond=None)

    prediction_features = result[feature_cols].apply(pd.to_numeric, errors="coerce")
    valid_predictions = prediction_features.notna().all(axis=1)

    result["EXPECTED_IMPACT"] = pd.NA
    result.loc[valid_predictions, "EXPECTED_IMPACT"] = (
        np.column_stack(
            [
                np.ones(valid_predictions.sum()),
                prediction_features.loc[valid_predictions].to_numpy(dtype=float),
            ]
        )
        @ coefficients
    )

    result["UNDERRATED_SCORE"] = (
        result[target_col] - pd.to_numeric(result["EXPECTED_IMPACT"], errors="coerce")
    ).round(1)

    result["IMPACT_RANK"] = result[target_col].rank(ascending=False, method="min")
    result["PPG_RANK"] = result["PTS"].rank(ascending=False, method="min")
    result["RANK_GAP"] = (result["PPG_RANK"] - result["IMPACT_RANK"]).round(0)

    return result


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
        ["Home", "Leaderboard", "Player Profile", "Comparison Tool", "Stage Explorer", "Underrated Players"],
        key="nav_radio",
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

    st.divider()
    st.subheader("🏀 Today's Debate")

    top_150 = df.nlargest(150, "TRUE_SCORING_IMPACT")

    valid_pairs = [
        (i, j)
        for i in range(len(top_150))
        for j in range(i + 1, len(top_150))
        if abs(top_150.iloc[i]["TRUE_SCORING_IMPACT"] - top_150.iloc[j]["TRUE_SCORING_IMPACT"]) <= 7
    ]

    if valid_pairs:
        rng = random.Random(pd.Timestamp.now().toordinal())
        i, j = rng.choice(valid_pairs)
        p1 = top_150.iloc[i]
        p2 = top_150.iloc[j]
    else:
        debate_players = top_150.sample(2, random_state=pd.Timestamp.now().toordinal()).reset_index(drop=True)
        p1 = debate_players.iloc[0]
        p2 = debate_players.iloc[1]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {p1['PLAYER_NAME']}")
        st.caption(p1['TEAM_ABBREVIATION'])
        st.metric("True Impact", f"{p1['TRUE_SCORING_IMPACT']:.1f}")
        st.metric("PPG", f"{p1['PTS']:.1f}")
        st.metric("TS%", format_percent(p1['TS_PCT']))
        st.metric("Usage", format_percent(p1['USG_PCT']))

    with col2:
        st.markdown(f"### {p2['PLAYER_NAME']}")
        st.caption(p2['TEAM_ABBREVIATION'])
        st.metric("True Impact", f"{p2['TRUE_SCORING_IMPACT']:.1f}")
        st.metric("PPG", f"{p2['PTS']:.1f}")
        st.metric("TS%", format_percent(p2['TS_PCT']))
        st.metric("Usage", format_percent(p2['USG_PCT']))

    st.divider()

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
    total_players = len(ranked_df)
    player_rank = int(player["RANK"])
    percentile = (1 - (player_rank - 1) / total_players) * 100

    if percentile >= 95:
        tier = "Elite scoring impact"
    elif percentile >= 85:
        tier = "High-level scoring impact"
    elif percentile >= 70:
        tier = "Strong scoring contributor"
    elif percentile >= 50:
        tier = "Solid scoring contributor"
    else:
        tier = "Below league median scoring impact"

    st.subheader(f"{player['PLAYER_NAME']} - {player['TEAM_ABBREVIATION']}")

    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Rank", f"#{player_rank} of {total_players}")
    metric_col2.metric("League Percentile", f"{percentile:.1f}%")
    metric_col3.metric("Impact", f"{player['TRUE_SCORING_IMPACT']:.1f}")
    metric_col4.metric("PPG", f"{player['PTS']:.1f}")
    metric_col5.metric("TS%", format_percent(player["TS_PCT"]))

    st.info(f"{tier} based on True Scoring Impact ranking.")
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
            ).astype({"Value": "string"}),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Raw Stage Scores")
    st.dataframe(
        stage_data.reset_index(),
        hide_index=True,
        width="stretch",
    )


if page == "Comparison Tool":
    st.title("Comparison Tool")
    st.write("Compare 2 to 4 players and view team-level scoring profile averages.")

    st.subheader("Player Comparison")

    player_options = df["PLAYER_NAME"].sort_values().tolist()

    selected_players = st.multiselect(
        "Choose 2 to 4 players",
        player_options,
        default=player_options[:2],
        max_selections=4,
    )

    if len(selected_players) < 2:
        st.warning("Select at least 2 players to compare.")
    else:
        comparison_df = df[df["PLAYER_NAME"].isin(selected_players)].copy()

        headline_cols = [
            "PLAYER_NAME",
            "TEAM_ABBREVIATION",
            "PTS",
            "TS_PCT",
            "USG_PCT",
            "TRUE_SCORING_IMPACT",
        ]

        st.dataframe(
            color_rank_columns(
                comparison_df[headline_cols].sort_values(
                    "TRUE_SCORING_IMPACT",
                    ascending=False,
                ),
                exclude_cols=["PLAYER_NAME", "TEAM_ABBREVIATION"],
            ).format(
                {
                    "PTS": "{:.1f}",
                    "TS_PCT": "{:.1%}",
                    "USG_PCT": "{:.1%}",
                    "TRUE_SCORING_IMPACT": "{:.1f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )

        stage_comparison = comparison_df[
            ["PLAYER_NAME"] + list(STAGE_COLUMNS.values())
        ].rename(
            columns={
                "PLAYER_NAME": "Player",
                "VOLUME_SCORE": "Volume",
                "EFFICIENCY_SCORE": "Efficiency",
                "DIFFICULTY_ADJ_EFFICIENCY": "Shot Difficulty",
                "CONTEXT_SCORE": "Game Context",
                "INDEPENDENCE_SCORE": "Independence",
            }
        )

        stage_chart_data = stage_comparison.set_index("Player")

        st.subheader("Scoring Stage Comparison")
        st.bar_chart(stage_chart_data, height=420)

    st.divider()

    st.subheader("Team Averages")

    team_options = ["League Average"] + sorted(
        df["TEAM_ABBREVIATION"].dropna().unique().tolist()
    )

    selected_team = st.selectbox("Choose a team", team_options)

    if selected_team == "League Average":
        team_df = df.copy()
        team_label = "League Average"
    else:
        team_df = df[df["TEAM_ABBREVIATION"] == selected_team].copy()
        team_label = selected_team

    team_summary = {
        "Players": len(team_df),
        "Avg Impact": team_df["TRUE_SCORING_IMPACT"].mean(),
        "Avg PPG": team_df["PTS"].mean(),
        "Avg TS%": team_df["TS_PCT"].mean(),
        "Avg Usage": team_df["USG_PCT"].mean(),
    }

    team_col1, team_col2, team_col3, team_col4, team_col5 = st.columns(5)
    team_col1.metric("Players", f"{team_summary['Players']}")
    team_col2.metric("Avg Impact", f"{team_summary['Avg Impact']:.1f}")
    team_col3.metric("Avg PPG", f"{team_summary['Avg PPG']:.1f}")
    team_col4.metric("Avg TS%", format_percent(team_summary["Avg TS%"]))
    team_col5.metric("Avg Usage", format_percent(team_summary["Avg Usage"]))

    team_stage_average = pd.DataFrame(
        {
            "Stage": list(STAGE_COLUMNS.keys()),
            "Average Score": [
                team_df[column].mean()
                for column in STAGE_COLUMNS.values()
            ],
        }
    ).set_index("Stage")

    st.subheader(f"{team_label} Stage Averages")
    st.bar_chart(team_stage_average, height=360)

    if selected_team != "League Average":
        st.subheader(f"{selected_team} Players")

        team_players = team_df.sort_values(
            "TRUE_SCORING_IMPACT",
            ascending=False,
        )

        st.dataframe(
            team_players[
                [
                    "PLAYER_NAME",
                    "PTS",
                    "TS_PCT",
                    "USG_PCT",
                    "TRUE_SCORING_IMPACT",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    st.divider()
    st.subheader("Team Comparison")

    selected_teams = st.multiselect(
        "Choose 2 to 4 teams",
        sorted(df["TEAM_ABBREVIATION"].dropna().unique().tolist()),
        max_selections=4,
    )

    if len(selected_teams) < 2:
        st.warning("Select at least 2 teams to compare.")
    else:
        team_comparison_rows = []
        for team in selected_teams:
            team_data = df[df["TEAM_ABBREVIATION"] == team]
            row = {"Team": team}
            for label, col in STAGE_COLUMNS.items():
                row[label] = team_data[col].mean()
            team_comparison_rows.append(row)

        team_comparison_df = pd.DataFrame(team_comparison_rows).set_index("Team")

        st.subheader("Stage Averages by Team")
        st.bar_chart(team_comparison_df, height=420)

        st.subheader("Summary Stats by Team")
        summary_rows = []
        for team in selected_teams:
            team_data = df[df["TEAM_ABBREVIATION"] == team]
            summary_rows.append({
                "Team": team,
                "Players": len(team_data),
                "Avg Impact": round(team_data["TRUE_SCORING_IMPACT"].mean(), 1),
                "Avg PPG": round(float(team_data["PTS"].mean()), 1),
                "Avg TS%": round(team_data["TS_PCT"].mean() * 100, 1),
                "Avg Usage": round(team_data["USG_PCT"].mean() * 100, 1),
            })

        st.dataframe(
            color_rank_columns(
                pd.DataFrame(summary_rows).set_index("Team").reset_index(),
                exclude_cols=["Team"],
            ).format(
                {
                    "Players": "{:.0f}",
                    "Avg Impact": "{:.1f}",
                    "Avg PPG": "{:.1f}",
                    "Avg TS%": "{:.1f}%",
                    "Avg Usage": "{:.1f}%",
                }
            ),
            hide_index=True,
            width="stretch",
        )


if page == "Stage Explorer":
    st.title("Stage Explorer")
    st.write("Explore the top players in each scoring stage and how they rank on the leaderboard.")

    stage_options = {
        "Volume": "VOLUME_SCORE",
        "Efficiency": "EFFICIENCY_SCORE",
        "Shot Difficulty": "DIFFICULTY_ADJ_EFFICIENCY",
        "Game Context": "CONTEXT_SCORE",
        "Independence": "INDEPENDENCE_SCORE",
        "True Scoring Impact": "TRUE_SCORING_IMPACT",
    }

    stage_descriptions = {
        "Volume": "How much scoring load a player carries through points, shot attempts, and usage.",
        "Efficiency": "How efficiently a player scores compared with expected scoring efficiency.",
        "Shot Difficulty": "How well a player scores while taking harder shots.",
        "Game Context": "How scoring holds up across clutch, home/away, rest, and game-state situations.",
        "Independence": "How much a player's scoring impact holds up independent of team context.",
        "True Scoring Impact": "The final weighted scoring impact score across all model stages.",
    }

    with st.sidebar:
        st.header("Stage Explorer Filters")

        selected_stage = st.selectbox(
            "Stage",
            list(stage_options.keys()),
        )

        selected_team = st.selectbox(
            "Team",
            ["All"] + sorted(df["TEAM_ABBREVIATION"].dropna().unique().tolist()),
        )

        selected_players = st.multiselect(
            "Players",
            df["PLAYER_NAME"].sort_values().tolist(),
        )

        min_ppg = st.slider(
            "Minimum PPG",
            0.0,
            float(df["PTS"].max()),
            10.0,
            0.5,
        )

        min_games = st.slider(
            "Minimum Games Played",
            0,
            int(df["GP"].max()),
            20,
            1,
        )

    stage_column = stage_options[selected_stage]

    st.subheader(selected_stage)
    st.info(stage_descriptions[selected_stage])

    filtered = df.copy()

    if selected_team != "All":
        filtered = filtered[filtered["TEAM_ABBREVIATION"] == selected_team]

    if selected_players:
        filtered = filtered[filtered["PLAYER_NAME"].isin(selected_players)]

    filtered = filtered[
        (filtered["PTS"] >= min_ppg)
        & (filtered["GP"] >= min_games)
    ]

    stage_ranked = filtered.sort_values(stage_column, ascending=False).copy()
    stage_ranked.insert(0, "RANK", range(1, len(stage_ranked) + 1))

    st.caption(f"{len(stage_ranked)} players match your filters")

    chart_data = stage_ranked.head(15).set_index("PLAYER_NAME")[[stage_column]]

    st.subheader(f"Top Players by {selected_stage}")
    st.bar_chart(chart_data, height=420)

    st.dataframe(
        stage_ranked[
            [
                "RANK",
                "PLAYER_NAME",
                "TEAM_ABBREVIATION",
                "PTS",
                "GP",
                "TS_PCT",
                "USG_PCT",
                stage_column,
            ]
        ],
        hide_index=True,
        width="stretch",
    )

if page == "Underrated Players":
    st.title("Underrated Players")
    st.write("Discover players with strong scoring impact but lower raw points per game.")

    with st.sidebar:
        st.header("Underrated Filters")

        selected_team = st.selectbox(
            "Team",
            ["All"] + sorted(df["TEAM_ABBREVIATION"].dropna().unique().tolist()),
            key="underrated_team",
        )

        max_ppg = st.slider(
            "Maximum PPG",
            0.0,
            float(df["PTS"].max()),
            18.0,
            0.5,
        )

        min_impact = st.slider(
            "Minimum Impact Score",
            0.0,
            100.0,
            60.0,
            1.0,
        )

        min_games = st.slider(
            "Minimum Games Played",
            0,
            int(df["GP"].max()),
            20,
            1,
            key="underrated_games",
        )

        min_minutes = st.slider(
            "Minimum Minutes",
            0.0,
            float(df["MIN"].max()),
            15.0,
            0.5,
            key="underrated_minutes",
        )

    underrated = add_underrated_scores(df)

    if selected_team != "All":
        underrated = underrated[underrated["TEAM_ABBREVIATION"] == selected_team]

    underrated = underrated[
        (underrated["PTS"] <= max_ppg)
        & (underrated["TRUE_SCORING_IMPACT"] >= min_impact)
        & (underrated["GP"] >= min_games)
        & (underrated["MIN"] >= min_minutes)
    ].copy()

    underrated = underrated.sort_values(
        "UNDERRATED_SCORE",
        ascending=False,
    ).copy()

    underrated.insert(0, "RANK", range(1, len(underrated) + 1))

    st.info(
        "This page uses regression to find players whose actual scoring impact is higher than expected from their PPG, usage, and minutes."
    )

    st.caption(f"{len(underrated)} players match your filters")

    if underrated.empty:
        st.warning("No players match the current filters. Try lowering the impact threshold or raising maximum PPG.")
    else:
        top_underrated = underrated.head(15).set_index("PLAYER_NAME")[["UNDERRATED_SCORE"]]

        st.subheader("Top Underrated Scoring Profiles")
        st.bar_chart(top_underrated, height=420)

        underrated_table = underrated[
            [
                "RANK",
                "PLAYER_NAME",
                "TEAM_ABBREVIATION",
                "PTS",
                "MIN",
                "GP",
                "TS_PCT",
                "USG_PCT",
                "TRUE_SCORING_IMPACT",
                "EXPECTED_IMPACT",
                "RANK_GAP",
                "UNDERRATED_SCORE",
            ]
        ]

        st.dataframe(
            underrated_table.style.format(
                {
                    "PTS": "{:.1f}",
                    "MIN": "{:.1f}",
                    "TS_PCT": "{:.1%}",
                    "USG_PCT": "{:.1%}",
                    "TRUE_SCORING_IMPACT": "{:.1f}",
                    "EXPECTED_IMPACT": "{:.1f}",
                    "RANK_GAP": "{:.0f}",
                    "UNDERRATED_SCORE": "{:.1f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )

st.markdown("---")
st.caption("Data sourced from NBA.com via nba_api · For educational and portfolio purposes only · Not affiliated with the NBA")