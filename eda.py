import pandas as pd
import plotly.express as px
import webbrowser
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def load_data():
    df = pd.read_csv(DATA_DIR / "players_final.csv")
    print(f"Loaded: {df.shape[0]} players, {df.shape[1]} columns")
    return df

def basic_info(df):
    print("\n--- Basic Info ---")
    print(df.describe())

def top_scorers(df):
    top = df.nlargest(15, "PTS")[["PLAYER_NAME", "PTS", "TS_PCT", "USG_PCT"]]
    print("\n--- Top 15 Scorers ---")
    print(top.to_string(index=False))

def efficiency_vs_usage(df):
    fig = px.scatter(
        df,
        x="USG_PCT",
        y="TS_PCT",
        hover_name="PLAYER_NAME",
        color="PTS",
        size="MIN",
        title="Efficiency vs Usage Rate",
        labels={
            "USG_PCT": "Usage Rate",
            "TS_PCT": "True Shooting %",
        }
    )
    plot_path = DATA_DIR / "efficiency_vs_usage.html"
    fig.write_html(plot_path)
    webbrowser.open_new_tab(plot_path.as_uri())
    
def scoring_distribution(df):
    fig = px.histogram(
        df,
        x="PTS",
        nbins=30,
        title="Distribution of Points Per Game",
        labels={"PTS": "Points Per Game"}
    )
    plot_path = DATA_DIR / "scoring_distribution.html"
    fig.write_html(plot_path)
    webbrowser.open_new_tab(plot_path.as_uri())

def top_scorers_chart(df):
    top = df.nlargest(15, "PTS").sort_values("PTS")
    fig = px.bar(
        top,
        x="PTS",
        y="PLAYER_NAME",
        color="TS_PCT",
        orientation="h",
        title="Top 15 Scorers — colored by True Shooting %",
        labels={
            "PTS": "Points Per Game",
            "PLAYER_NAME": "Player",
            "TS_PCT": "True Shooting %"
        }
    )
    plot_path = DATA_DIR / "top_scorers.html"
    fig.write_html(plot_path)
    webbrowser.open_new_tab(plot_path.as_uri())

def correlation_heatmap(df):
    cols = ["PTS", "TS_PCT", "USG_PCT", "MIN", "FGA", "FG3A", "FTA", "AST", "TOV", "OFF_RATING", "PIE"]
    corr = df[cols].corr().round(2)
    
    fig = px.imshow(
        corr,
        title="Correlation Heatmap — Key Scoring Stats",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        text_auto=True
    )
    plot_path = DATA_DIR / "correlation_heatmap.html"
    fig.write_html(plot_path)
    webbrowser.open_new_tab(plot_path.as_uri())

def main():
    df = load_data()
    basic_info(df)
    top_scorers(df)
    efficiency_vs_usage(df)
    scoring_distribution(df)
    top_scorers_chart(df)
    correlation_heatmap(df)

if __name__ == "__main__":
    main()

