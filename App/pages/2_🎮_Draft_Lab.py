import streamlit as st
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Draft Lab", page_icon="🎮", layout="wide")

# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
.draft-card {
    background: #1a1a2e;
    border: 1px solid #2d2d4e;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.on-clock {
    background: #1e3a1e;
    border: 1.5px solid #4caf50;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.ai-pick-flash {
    background: #1a1a2e;
    border-left: 3px solid #6c6cff;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    color: #bbb;
    margin-bottom: 6px;
}
.champion-banner {
    background: linear-gradient(135deg, #1a1a2e, #2d2d4e);
    border: 2px solid #f6a623;
    border-radius: 14px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 20px;
}
.champion-title {
    font-size: 13px;
    color: #f6a623;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.champion-name {
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
}
.fmvp-banner {
    background: #1a1a2e;
    border: 1.5px solid #6c6cff;
    border-radius: 10px;
    padding: 18px 24px;
    text-align: center;
    margin-bottom: 20px;
}
.fmvp-label {
    font-size: 12px;
    color: #6c6cff;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.fmvp-name {
    font-size: 22px;
    font-weight: 700;
    color: #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_draft_pool():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "..", "..", "Data", "players_final_scores.csv")
    df = pd.read_csv(csv_path)

    pool = df[[
        "PLAYER_ID",
        "PLAYER_NAME",
        "GP",
        "PTS",
        "TS_PCT",
        "TRUE_SCORING_IMPACT"
    ]].copy()

    pool = pool.rename(columns={"PTS": "PPG"})
    pool["PPG"] = pool["PPG"].round(1)
    pool["TS_PCT"] = (pool["TS_PCT"] * 100).round(1)
    pool["TRUE_SCORING_IMPACT"] = pool["TRUE_SCORING_IMPACT"].round(2)

    # Noisy signal — used internally by Auto logic only, never shown to user
    rng = np.random.default_rng(seed=42)
    noise = rng.uniform(-5, 5, size=len(pool))
    pool["ESTIMATED_IMPACT"] = (pool["TRUE_SCORING_IMPACT"] + noise).round(1)

    # Injury probability per game: 1 - (GP / 82)
    pool["INJURY_PROB"] = ((1 - pool["GP"] / 82) * 100).round(1)

    pool = pool.sort_values("PPG", ascending=False).reset_index(drop=True)
    return pool


# ─────────────────────────────────────────────
# DRAFT ORDER
# ─────────────────────────────────────────────
def generate_draft_order(n_teams: int, n_rounds: int, seed: int) -> list[int]:
    rng = np.random.default_rng(seed=seed)
    first_round = rng.permutation(n_teams).tolist()
    order = []
    for r in range(n_rounds):
        if r % 2 == 0:
            order.extend(first_round)
        else:
            order.extend(reversed(first_round))
    return order


# ─────────────────────────────────────────────
# Auto PICK LOGIC
# ─────────────────────────────────────────────
def ai_pick(available_pool: pd.DataFrame, rng: np.random.Generator) -> int:
    if len(available_pool) == 0:
        return None
    if rng.random() < 0.80 or len(available_pool) < 3:
        chosen = available_pool.iloc[0]
    else:
        chosen = available_pool.iloc[rng.integers(1, 3)]
    return int(chosen["PLAYER_ID"])


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_draft_state(pool: pd.DataFrame):
    N_TEAMS = 8
    N_ROUNDS = 8
    USER_TEAM_IDX = 0
    seed = int(pd.Timestamp.now().toordinal())

    st.session_state["draft_pool"] = pool.copy()
    st.session_state["available"] = pool.copy()
    st.session_state["user_team"] = []
    st.session_state["ai_teams"] = {i: [] for i in range(1, N_TEAMS)}
    st.session_state["draft_order"] = generate_draft_order(N_TEAMS, N_ROUNDS, seed)
    st.session_state["current_pick"] = 0
    st.session_state["round_num"] = 1
    st.session_state["n_rounds"] = N_ROUNDS
    st.session_state["n_teams"] = N_TEAMS
    st.session_state["user_team_idx"] = USER_TEAM_IDX
    st.session_state["draft_complete"] = False
    st.session_state["sim_complete"] = False
    st.session_state["auto_rng"] = np.random.default_rng(seed=seed)
    st.session_state["last_auto_picks"] = []
    st.session_state["draft_started"] = True


def pick_player(player_id: int):
    state = st.session_state
    available = state["available"]
    player_row = available[available["PLAYER_ID"] == player_id].iloc[0].to_dict()
    team_idx = state["draft_order"][state["current_pick"]]

    if team_idx == state["user_team_idx"]:
        state["user_team"].append(player_row)
    else:
        state["ai_teams"][team_idx].append(player_row)

    state["available"] = available[available["PLAYER_ID"] != player_id].reset_index(drop=True)
    state["current_pick"] += 1
    state["round_num"] = (state["current_pick"] // state["n_teams"]) + 1

    total_picks = state["n_teams"] * state["n_rounds"]
    if state["current_pick"] >= total_picks:
        state["draft_complete"] = True
        return

    state["last_auto_picks"] = []
    while state["current_pick"] < total_picks:
        next_team = state["draft_order"][state["current_pick"]]
        if next_team == state["user_team_idx"]:
            break

        chosen_id = ai_pick(state["available"], state["auto_rng"])
        if chosen_id is None:
            break

        auto_player = state["available"][state["available"]["PLAYER_ID"] == chosen_id].iloc[0].to_dict()
        state["auto_teams"][next_team].append(auto_player)
        state["available"] = state["available"][state["available"]["PLAYER_ID"] != chosen_id].reset_index(drop=True)
        state["last_auto_picks"].append((next_team, auto_player["PLAYER_NAME"]))

        state["current_pick"] += 1
        state["round_num"] = (state["current_pick"] // state["n_teams"]) + 1

    if state["current_pick"] >= total_picks:
        state["draft_complete"] = True


# ─────────────────────────────────────────────
# SIMULATION ENGINE
# ─────────────────────────────────────────────
def sigmoid(x: float) -> float:
    """Converts TSI strength difference into a win probability (0 to 1)."""
    return 1 / (1 + np.exp(-x / 15))
    # Dividing by 15 scales the TSI difference so that a gap of ~15 TSI points
    # gives roughly a 73% win probability — feels realistic without being deterministic


def game_strength(roster: list, rng: np.random.Generator) -> float:
    """
    For a single game, each player sits out with their injury probability.
    Team strength = sum of True TSI of healthy players + small noise.
    """
    healthy_tsi = [
        p["TRUE_SCORING_IMPACT"]
        for p in roster
        if rng.random() > p["INJURY_PROB"] / 100
    ]
    base = sum(healthy_tsi) if healthy_tsi else 0.0
    noise = rng.uniform(-0.05, 0.05) * base   # ±5% variance per game
    return base + noise


def simulate_series(roster_a: list, roster_b: list, wins_needed: int, rng: np.random.Generator) -> tuple[int, int]:
    """
    Simulate a best-of-(2*wins_needed - 1) series.
    Returns (wins_a, wins_b).
    """
    wins_a, wins_b = 0, 0
    while wins_a < wins_needed and wins_b < wins_needed:
        str_a = game_strength(roster_a, rng)
        str_b = game_strength(roster_b, rng)
        wp_a = sigmoid(str_a - str_b)
        if rng.random() < wp_a:
            wins_a += 1
        else:
            wins_b += 1
    return wins_a, wins_b


def run_simulation(user_team: list, auto_teams: dict, seed: int) -> dict:
    """
    Full simulation: regular season → playoffs → champion → FMVP.

    Returns a results dict with all data needed for display.
    """
    rng = np.random.default_rng(seed=seed)

    # Build unified team registry: team_id → roster
    # Team 0 = user, Teams 1-7 = Auto
    all_teams = {0: user_team}
    all_teams.update(auto_teams)
    team_labels = {0: "⛹️ Your Team"}
    for i in range(1, 8):
        team_labels[i] = f"🤖 Auto {i}"

    n_teams = len(all_teams)

    # ── REGULAR SEASON ────────────────────────
    # Each pair of teams plays one game (round-robin, 7 games per team)
    wins = {t: 0 for t in all_teams}
    losses = {t: 0 for t in all_teams}

    matchups = []
    team_ids = list(all_teams.keys())
    for i in range(n_teams):
        for j in range(i + 1, n_teams):
            t_a, t_b = team_ids[i], team_ids[j]
            str_a = game_strength(all_teams[t_a], rng)
            str_b = game_strength(all_teams[t_b], rng)
            wp_a = sigmoid(str_a - str_b)
            if rng.random() < wp_a:
                wins[t_a] += 1
                losses[t_b] += 1
                winner = t_a
            else:
                wins[t_b] += 1
                losses[t_a] += 1
                winner = t_b
            matchups.append((team_labels[t_a], team_labels[t_b], team_labels[winner]))

    # Standings: sort by wins descending
    standings = sorted(all_teams.keys(), key=lambda t: wins[t], reverse=True)
    standings_rows = [
        {
            "Seed": i + 1,
            "Team": team_labels[t],
            "W": wins[t],
            "L": losses[t],
            "Total TSI": round(sum(p["TRUE_SCORING_IMPACT"] for p in all_teams[t]), 1)
        }
        for i, t in enumerate(standings)
    ]

    # ── PLAYOFFS ──────────────────────────────
    # Top 4 advance: 1 vs 4, 2 vs 3 in semis; winners meet in finals
    # Best of 5 (first to 3 wins)
    s1, s2, s3, s4 = standings[:4]

    # Semifinal 1: seed 1 vs seed 4
    w1, w4 = simulate_series(all_teams[s1], all_teams[s4], wins_needed=3, rng=rng)
    semi1_winner = s1 if w1 > w4 else s4
    semi1_result = f"{team_labels[s1]} {w1}–{w4} {team_labels[s4]}"

    # Semifinal 2: seed 2 vs seed 3
    w2, w3 = simulate_series(all_teams[s2], all_teams[s3], wins_needed=3, rng=rng)
    semi2_winner = s2 if w2 > w3 else s3
    semi2_result = f"{team_labels[s2]} {w2}–{w3} {team_labels[s3]}"

    # Finals
    wf_a, wf_b = simulate_series(all_teams[semi1_winner], all_teams[semi2_winner], wins_needed=3, rng=rng)
    champion = semi1_winner if wf_a > wf_b else semi2_winner
    finals_result = f"{team_labels[semi1_winner]} {wf_a}–{wf_b} {team_labels[semi2_winner]}"

    # ── FMVP ──────────────────────────────────
    # Player on champion roster with highest True TSI
    champion_roster = all_teams[champion]
    fmvp = max(champion_roster, key=lambda p: p["TRUE_SCORING_IMPACT"])

    return {
        "standings": standings_rows,
        "semi1": semi1_result,
        "semi2": semi2_result,
        "finals": finals_result,
        "champion_label": team_labels[champion],
        "champion_id": champion,
        "fmvp_name": fmvp["PLAYER_NAME"],
        "fmvp_tsi": round(fmvp["TRUE_SCORING_IMPACT"], 2),
        "fmvp_ppg": fmvp["PPG"],
    }


# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────
def render_roster_sidebar(user_team: list, round_num: int, n_rounds: int):
    with st.sidebar:
        st.markdown("### ⛹️ Your Roster")
        st.caption(f"Round {round_num} of {n_rounds}")
        if not user_team:
            st.caption("No picks yet.")
        for p in user_team:
            st.markdown(
                f"**{p['PLAYER_NAME']}**  \n"
                f"<span style='font-size:12px;color:#aaa'>{p['PPG']} PPG · {p['TS_PCT']}% TS</span>",
                unsafe_allow_html=True
            )
            st.divider()


def render_draft_reveal(user_team: list, ai_teams: dict):
    """Shows rosters + TSI reveal before simulation runs."""
    st.success("✅ Draft Complete — True Scoring Impact revealed.")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### ⛹️ Your Team")
        if user_team:
            df_user = pd.DataFrame(user_team)[["PLAYER_NAME", "PPG", "TS_PCT", "TRUE_SCORING_IMPACT", "INJURY_PROB"]]
            df_user = df_user.rename(columns={
                "PLAYER_NAME": "Player",
                "TRUE_SCORING_IMPACT": "True TSI",
                "INJURY_PROB": "Injury Risk %"
            })
            st.dataframe(df_user, use_container_width=True, hide_index=True)
            team_tsi = sum(p["TRUE_SCORING_IMPACT"] for p in user_team)
            st.metric("Total Team TSI", f"{team_tsi:.1f}")

    with col2:
        st.markdown("### 🤖 Auto Teams")
        summary_rows = []
        for team_idx, roster in ai_teams.items():
            if roster:
                total = sum(p["TRUE_SCORING_IMPACT"] for p in roster)
                best = max(roster, key=lambda p: p["TRUE_SCORING_IMPACT"])
                summary_rows.append({
                    "Team": f"Auto {team_idx}",
                    "Total TSI": round(total, 1),
                    "Best Player": best["PLAYER_NAME"],
                    "Best TSI": round(best["TRUE_SCORING_IMPACT"], 2)
                })
        if summary_rows:
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def render_simulation_results(results: dict):
    """Renders regular season standings, playoff bracket, champion, and FMVP."""
    st.markdown("---")
    st.markdown("## 🏆 Season Results")

    # Champion banner
    st.markdown(f"""
    <div class="champion-banner">
        <div class="champion-title">🏆 Champion</div>
        <div class="champion-name">{results['champion_label']}</div>
    </div>
    """, unsafe_allow_html=True)

    # FMVP
    st.markdown(f"""
    <div class="fmvp-banner">
        <div class="fmvp-label">Finals MVP</div>
        <div class="fmvp-name">{results['fmvp_name']}</div>
        <div style="font-size:13px;color:#aaa;margin-top:4px;">
            {results['fmvp_ppg']} PPG &nbsp;·&nbsp; True TSI: {results['fmvp_tsi']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📊 Regular Season Standings")
        st.dataframe(
            pd.DataFrame(results["standings"]),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown("### 🎯 Playoff Results")
        st.markdown("**Semifinals**")
        st.markdown(f"- {results['semi1']}")
        st.markdown(f"- {results['semi2']}")
        st.markdown("**Finals**")
        st.markdown(f"- {results['finals']}")

    st.markdown("---")
    if st.button("🔄 Start New Draft"):
        for key in ["draft_started", "draft_complete", "sim_complete", "sim_results",
                    "available", "user_team", "ai_teams", "draft_order",
                    "current_pick", "round_num", "last_ai_picks", "ai_rng", "draft_pool"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
st.title("🎮 Draft Lab")
st.caption("Build your squad. TSI is hidden — draft on instinct and signals.")

pool = load_draft_pool()

# ── PRE-DRAFT SCREEN ──────────────────────────
if not st.session_state.get("draft_started", False):
    st.markdown("""
    **How it works:**
    - 8 teams · 8 rounds · snake draft
    - You see PPG and TS% only — True TSI is hidden until the draft ends
    - Injury risk affects game-night availability in the simulated season
    - Top 4 teams make the playoffs · Best of 5 series · Champion crowned
    """)
    st.info(f"📋 Draft pool: **{len(pool)} players** available")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏀 Start Draft", use_container_width=True, type="primary"):
            init_draft_state(pool)
            st.rerun()
    st.stop()


# ── SIMULATION RESULTS SCREEN ─────────────────
if st.session_state.get("sim_complete", False):
    render_draft_reveal(st.session_state["user_team"], st.session_state["ai_teams"])
    render_simulation_results(st.session_state["sim_results"])
    st.stop()


# ── DRAFT COMPLETE — REVEAL + SIM TRIGGER ─────
if st.session_state.get("draft_complete", False):
    render_draft_reveal(st.session_state["user_team"], st.session_state["ai_teams"])
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("▶️ Run Season Simulation", use_container_width=True, type="primary"):
            seed = int(pd.Timestamp.now().toordinal()) + 1   # +1 so it differs from draft seed
            results = run_simulation(
                st.session_state["user_team"],
                st.session_state["ai_teams"],
                seed=seed
            )
            st.session_state["sim_results"] = results
            st.session_state["sim_complete"] = True
            st.rerun()
    st.stop()


# ── ACTIVE DRAFT ──────────────────────────────
state = st.session_state
total_picks = state["n_teams"] * state["n_rounds"]

render_roster_sidebar(state["user_team"], state["round_num"], state["n_rounds"])

progress = state["current_pick"] / total_picks
st.progress(progress, text=f"Pick {state['current_pick'] + 1} of {total_picks} · Round {state['round_num']}")

if state.get("last_ai_picks"):
    st.markdown("**Recent Auto picks:**")
    for team_idx, name in state["last_ai_picks"]:
        st.markdown(
            f'<div class="ai-pick-flash">🤖 Auto {team_idx} drafted <strong>{name}</strong></div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="on-clock"><strong>⏱ You\'re on the clock</strong></div>', unsafe_allow_html=True)

search = st.text_input("🔍 Search players", placeholder="Type a name...", key="search_box")
available = state["available"].copy()

if search:
    available = available[available["PLAYER_NAME"].str.contains(search, case=False, na=False)]

st.markdown(f"**Available players** ({len(state['available'])} remaining) — sorted by PPG")

h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
h1.markdown("**Player**")
h2.markdown("**PPG**")
h3.markdown("**TS%**")
h4.markdown("**Inj. Risk**")
h5.markdown("")

display_pool = available.head(20)

for _, row in display_pool.iterrows():
    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
    c1.markdown(f"**{row['PLAYER_NAME']}**")
    c2.markdown(f"{row['PPG']}")
    c3.markdown(f"{row['TS_PCT']}%")
    c4.markdown(f"{row['INJURY_PROB']}%")
    with c5:
        if st.button("Draft", key=f"pick_{row['PLAYER_ID']}"):
            pick_player(int(row["PLAYER_ID"]))
            st.rerun()