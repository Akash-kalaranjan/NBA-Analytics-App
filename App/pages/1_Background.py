from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "Data" / "players_final_scores.csv"

st.set_page_config(
    page_title="Background",
    layout="wide",
)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("Background")

tab1, tab2, tab3, tab4 = st.tabs(["EDA Graphs", "Report", "Model Formulas", "About"])

with tab1:
    st.subheader("EDA Graphs")
    st.subheader("Top 15 Scorers")
    top = df.nlargest(15, "PTS").sort_values("PTS")
    fig3 = px.bar(
        top,
        x="PTS",
        y="PLAYER_NAME",
        color="TS_PCT",
        orientation="h",
        title="Top 15 Scorers — colored by True Shooting %",
        labels={"PTS": "Points Per Game", "PLAYER_NAME": "Player", "TS_PCT": "True Shooting %"},
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    High PPG does not equal high efficiency. SGA and Jokić score fewer points than Luka on average but shoot far more efficiently. Jaylen Brown is the least efficient of the top scorers despite high volume. Even amongst the most reputable scorers who face tough defensive coverages and take harder shots than the average player, volume and efficiency alone are insufficient to determine true scoring value. This  emphasizes the importance of this model, as by incorporating shot difficulty and situational context, we can build a more complete picture of how good a scorer each player truly is.
    """)

    st.divider()

    st.subheader("Efficiency vs Usage Rate")
    fig1 = px.scatter(
        df,
        x="USG_PCT",
        y="TS_PCT",
        hover_name="PLAYER_NAME",
        color="PTS",
        size="MIN",
        title="Efficiency vs Usage Rate",
        labels={"USG_PCT": "Usage Rate", "TS_PCT": "True Shooting %"},
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    As usage rate increases, players tend to score more points, reflected by the brighter colors on the right side of the chart. This is consistent with higher opportunity leading to more shot attempts and higher PPG. Variance is highest among low usage players on the left side of the chart. This makes sense as low volume players have smaller shot samples, making their efficiency numbers less reliable. As usage increases, efficiency regresses toward the league mean and higher quality players remain efficient at high volume, but not astronomically above average due to the increased difficulty of shots and greater defensive attention they face. 


    Severe outliers in true shooting percentage, both above and below the mean, are concentrated among low usage players. High efficiency outliers at low usage likely benefit from offensive gravity created by teammates, and low efficiency outliers at low usage are likely poor scorers who rarely shoot for good reason. Neither extreme is reliable for evaluating true scoring ability, which further supports the need to adjust for usage when building a scoring impact model.
    """)

    st.divider()

    st.subheader("Distribution of Points Per Game")
    fig2 = px.histogram(
        df,
        x="PTS",
        nbins=30,
        title="Distribution of Points Per Game",
        labels={"PTS": "Points Per Game"},
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    The distribution of points per game is right skewed, with a heavy tail on the right side. Most NBA players hover around 5-15 PPG, making 20+ PPG scorers and especially 25-33 PPG scorers statistical outliers. This makes high volume scoring that much more impressive and valuable.
                
     Modern NBA offenses emphasize depth and ball movement, while defensive schemes have become increasingly versatile and complex. Despite this, a select few elite scorers consistently average high PPG, which speaks to the difficulty and rarity of what they do. A scoring model must account for this skew as the difference between a player going from 8 to 13 PPG is common, while the jump from 20 to 25 PPG represents a much rarer and more meaningful level of offensive ability.

    """)

    st.divider()

    st.subheader("Correlation Heatmap")
    cols = ["PTS", "TS_PCT", "USG_PCT", "MIN", "FGA", "FTA", "AST", "TOV"]
    corr = df[cols].corr().round(2)
    fig4 = px.imshow(
        corr,
        title="Correlation Heatmap — Key Scoring Stats",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        text_auto=True,
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown("""
    **FGA vs PTS (r = 0.98)** — Scoring is primarily a volume stat. More shot attempts directly translates to more points, highlighting the need to adjust for opportunity when evaluating scoring quality.

    **TOV vs USG% (r = 0.80)** — High usage players handle the ball more and turn it over more. This is a byproduct of opportunity, not necessarily a criticism.

    **TS% vs USG% (r = 0.0)** — Efficiency and usage have no linear relationship at the league level. Elite players who maintain high efficiency at high usage are genuinely beating the expected tradeoff.

    **OFF_RATING** — Weak correlations with most individual stats, confirming it captures team level context that box score stats alone do not explain.
    """)

with tab2:
    st.subheader("Report")
    report_path = BASE_DIR / "minireport.md"
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.warning("minireport.md not found.")

with tab3:
    st.subheader("Model Formulas")
    formulas_path = BASE_DIR / "formulas.md"
    if formulas_path.exists():
        st.markdown(formulas_path.read_text(encoding="utf-8"))
    else:
        st.warning("formulas.md not found.")

with tab4:
    st.subheader("About")
    about_path = BASE_DIR / "about.md"
    if about_path.exists():
        st.markdown(about_path.read_text(encoding="utf-8"))
    else:
        st.warning("about.md not found.")
