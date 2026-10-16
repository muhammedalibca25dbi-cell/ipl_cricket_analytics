import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="IPL Cricket Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0B1220; color: #F1F5F9; }
    [data-testid="stSidebar"] { background-color: #111C2E; }
    [data-testid="stMetric"] {
        background-color: #17243A;
        border: 1px solid #30445F;
        padding: 18px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] { color: #B7C5D8; }
    h1, h2, h3 { color: #F8FAFC; }
    div[data-testid="stPlotlyChart"] {
        border: 1px solid #263750;
        border-radius: 10px;
        padding: 8px;
    }
    [data-testid="stExpander"] {
        border: 1px solid #263750;
        border-radius: 10px;
        background-color: #111C2E;
    }
</style>
""", unsafe_allow_html=True)

CHART_TEMPLATE = "plotly_dark"

# ---------------------------------------------------------
# Animated title card
# ---------------------------------------------------------
st.markdown("""
<style>
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(24px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes shimmer {
        0%   { transform: translateX(-120%) skewX(-20deg); }
        100% { transform: translateX(260%) skewX(-20deg); }
    }
    @keyframes floatIcon {
        0%, 100% { transform: translateY(0) rotate(-8deg); }
        50%      { transform: translateY(-10px) rotate(8deg); }
    }
    @keyframes underlineGrow {
        from { width: 0; }
        to   { width: 120px; }
    }

    .title-card {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        gap: 22px;
        padding: 28px 34px;
        margin-bottom: 22px;
        border-radius: 16px;
        border: 1px solid #30445F;
        background: linear-gradient(
            120deg, #0F1B30, #17304F, #0E3B43, #17243A
        );
        background-size: 300% 300%;
        animation: fadeSlideIn 0.8s ease-out both,
                   gradientShift 12s ease infinite;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }

    /* moving light sweep */
    .title-card::after {
        content: "";
        position: absolute;
        top: 0; left: 0;
        width: 35%; height: 100%;
        background: linear-gradient(
            90deg, transparent, rgba(255,255,255,0.10), transparent
        );
        animation: shimmer 4.5s ease-in-out infinite;
        pointer-events: none;
    }

    .title-card .tc-icon {
        font-size: 54px;
        animation: floatIcon 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.5));
    }

    .title-card .tc-title {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(90deg, #F8FAFC, #5EEAD4, #F8FAFC);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 6s linear infinite;
    }

    .title-card .tc-sub {
        margin: 6px 0 0 0;
        color: #B7C5D8;
        font-size: 0.95rem;
        animation: fadeSlideIn 1.2s ease-out 0.3s both;
    }

    .title-card .tc-line {
        height: 3px;
        margin-top: 12px;
        border-radius: 3px;
        background: linear-gradient(90deg, #25B889, #F4C542);
        animation: underlineGrow 1.2s ease-out 0.5s both;
    }
</style>
""", unsafe_allow_html=True)


def title_card(title, subtitle="", icon="🏏", badge=""):
    """Render an animated hero title card (badge pill + cricket ball)."""
    badge_html = f'<span class="tc-badge">{badge}</span>' if badge else ""
    html = (
        '<div class="title-card">'
        f'<div class="tc-icon">{icon}</div>'
        '<div>'
        f'{badge_html}'
        f'<h1 class="tc-title">{title}</h1>'
        f'<p class="tc-sub">{subtitle}</p>'
        '<div class="tc-line"></div>'
        '</div>'
        '<div class="tc-ball"></div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------
# Design themes (selectable from the sidebar)
# ---------------------------------------------------------
THEMES = {
    "Royal Gold": dict(
        bg="#0E1117", bg2="#262730", card="#1A1D24", border="#3A3F4B",
        text="#F5F5F5", muted="#A1A1AA", hcolor="#FFB400",
        accent="#FFB400", accent2="#FF7A00",
        hfont="'Bebas Neue', 'Oswald', sans-serif",
        hero="linear-gradient(135deg,#1F2937 0%,#2E3440 55%,#7A2E0A 100%)",
        scale="YlOrBr",
        colorway=["#FACC15", "#EF4444", "#22C55E", "#F97316", "#A855F7",
                  "#EC4899", "#14B8A6", "#E5E7EB"],
    ),
}

THEME_STATIC_CSS = """
<style>
.stApp {
    background: var(--bg);
    color: var(--text);
}
[data-testid="stSidebar"] {
    background: var(--bg2);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    font-family: var(--hfont);
    color: var(--hcolor);
    letter-spacing: 1px;
}
h1, h2, h3 {
    font-family: var(--hfont);
    color: var(--hcolor);
    letter-spacing: 0.6px;
}
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent2);
    border-radius: 14px;
}
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] {
    color: var(--accent);
    font-family: var(--hfont);
    letter-spacing: 1px;
}
div[data-testid="stPlotlyChart"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
}
[data-testid="stExpander"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
}

/* hero title card */
.title-card {
    background: var(--hero) !important;
    background-size: 300% 300% !important;
    border: 1px solid var(--accent2) !important;
    min-height: 170px;
    padding-right: 220px;
}
.title-card .tc-title {
    font-family: var(--hfont);
    font-size: 2.8rem;
    background: linear-gradient(90deg, var(--text), var(--accent), var(--text));
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.title-card .tc-sub { color: var(--muted); max-width: 520px; }
.title-card .tc-line {
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.tc-badge {
    display: inline-block;
    padding: 5px 14px;
    margin-bottom: 8px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #111;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    animation: fadeSlideIn 0.8s ease-out both;
}
.tc-ball {
    position: absolute;
    right: 48px;
    top: 50%;
    width: 104px;
    height: 104px;
    margin-top: -52px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 28%, #ff7b7b, #c1121f 55%, #6b0a12);
    box-shadow: inset -8px -10px 18px rgba(0,0,0,0.45),
                0 10px 30px rgba(0,0,0,0.5);
    animation: ballFloat 3.5s ease-in-out infinite;
}
.tc-ball::before {
    content: "";
    position: absolute;
    left: 50%; top: 6%; bottom: 6%;
    border-left: 2px dashed rgba(255,255,255,0.8);
    transform: translateX(-50%);
}
@keyframes ballFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50%      { transform: translateY(-12px) rotate(12deg); }
}
.title-card .tc-icon { display: none; }
</style>
"""


def build_theme_css(t):
    """Return the CSS that applies one design theme."""
    fonts = (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Bebas+Neue&family=Oswald:wght@500;700&"
        "family=Orbitron:wght@600;800&family=Teko:wght@500;700&"
        "family=Poppins:wght@600;700&family=Inter:wght@400;700&"
        "display=swap');"
    )
    variables = (
        ":root{"
        f"--bg:{t['bg']};--bg2:{t['bg2']};--card:{t['card']};"
        f"--border:{t['border']};--text:{t['text']};--muted:{t['muted']};"
        f"--hcolor:{t['hcolor']};--accent:{t['accent']};"
        f"--accent2:{t['accent2']};--hfont:{t['hfont']};"
        f"--hero:{t['hero']};"
        "}"
    )
    return f"<style>{fonts}{variables}</style>" + THEME_STATIC_CSS

# =========================================================
# 2. DATABASE CONNECTION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "ipl.db"


@st.cache_data
def load_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(str(DB_PATH)) as conn:
        df = pd.read_sql_query("SELECT * FROM matches_clean", conn)

    required_columns = [
        "season_year", "team1", "team2", "match_winner", "venue"
    ]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing database columns: {missing}")

    df["season_year"] = pd.to_numeric(df["season_year"], errors="coerce")
    df["win_by_runs"] = pd.to_numeric(df["win_by_runs"], errors="coerce")
    df["win_by_wickets"] = pd.to_numeric(
        df["win_by_wickets"], errors="coerce"
    )

    df["team1"] = df["team1"].fillna("Unknown")
    df["team2"] = df["team2"].fillna("Unknown")
    df["venue"] = df["venue"].fillna("Unknown venue")

    return df


try:
    matches = load_data()
except Exception as error:
    st.error(f"Unable to load IPL data: {error}")
    st.stop()


# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def apply_season_filter(data, season):
    if season == "All Seasons":
        return data.copy()
    return data[data["season_year"] == int(season)].copy()


def get_team_stats(data):
    """Calculate matches, wins, losses and win rate."""

    if data.empty:
        return pd.DataFrame(
            columns=["Team", "Matches", "Wins", "Losses",
                     "No Result", "Win Rate"]
        )

    first = data[["match_id", "team1", "match_winner"]].copy()
    first.columns = ["Match ID", "Team", "Winner"]

    second = data[["match_id", "team2", "match_winner"]].copy()
    second.columns = ["Match ID", "Team", "Winner"]

    team_long = pd.concat([first, second], ignore_index=True)
    team_long["Outcome"] = "No Result"

    has_winner = (
        team_long["Winner"].notna()
        & team_long["Winner"].astype(str).str.strip().ne("")
    )

    team_long.loc[has_winner, "Outcome"] = "Loss"
    team_long.loc[
        has_winner & (team_long["Team"] == team_long["Winner"]),
        "Outcome"
    ] = "Win"

    stats = (
        team_long.groupby("Team")
        .agg(
            Matches=("Match ID", "nunique"),
            Wins=("Outcome", lambda x: (x == "Win").sum()),
            Losses=("Outcome", lambda x: (x == "Loss").sum()),
            **{"No Result": ("Outcome",
                             lambda x: (x == "No Result").sum())}
        )
        .reset_index()
    )

    decisions = stats["Wins"] + stats["Losses"]
    stats["Win Rate"] = (
        stats["Wins"].div(decisions.where(decisions != 0))
        .mul(100)
        .fillna(0)
    )

    return stats.sort_values("Win Rate", ascending=False)


def get_venue_stats(data):
    """Calculate match counts and win types at each venue."""

    if data.empty:
        return pd.DataFrame(
            columns=["Venue", "Matches", "Batting First Wins",
                     "Chasing Wins", "Other Results"]
        )

    df = data.copy()
    df["Win Type"] = "Other Results"
    df.loc[df["win_by_runs"].fillna(0) > 0, "Win Type"] = \
        "Batting First Wins"
    df.loc[df["win_by_wickets"].fillna(0) > 0, "Win Type"] = \
        "Chasing Wins"

    stats = (
        df.groupby("venue")
        .agg(Matches=("match_id", "nunique"))
        .reset_index()
        .rename(columns={"venue": "Venue"})
    )

    results = (
        df.groupby(["venue", "Win Type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"venue": "Venue"})
    )

    stats = stats.merge(results, on="Venue", how="left")

    for col in ["Batting First Wins", "Chasing Wins", "Other Results"]:
        if col not in stats.columns:
            stats[col] = 0

    return stats


def wilson_interval(wins, total, z=1.96):
    """Approximate 95% Wilson confidence interval for a proportion."""

    if total <= 0:
        return 0.0, 0.0

    p = wins / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    margin = (
        z * (p * (1 - p) / total + z**2 / (4 * total**2))**0.5
        / denominator
    )
    return max(0, centre - margin) * 100, min(1, centre + margin) * 100


# ---------------------------------------------------------
# Per-chart filter helpers
# Call these INSIDE `with st.expander(...)`.
# Every widget gets its own key (prefix = chart id) so the
# filters of one chart never affect another chart.
# ---------------------------------------------------------

def chart_filters(df, key, seasons=False, teams=False, venues=False,
                  cities=False, match_types=False):
    """Render match-level filters for one chart and return filtered df."""

    flags = [
        seasons,
        teams,
        venues,
        cities and "city" in df.columns,
        match_types and "match_type" in df.columns,
    ]
    n = sum(flags)
    if n == 0:
        return df

    cols = st.columns(n)
    i = 0
    out = df

    if seasons:
        with cols[i]:
            years = out["season_year"].dropna().astype(int)
            if years.empty:
                st.caption("No seasons available")
            elif years.min() == years.max():
                st.caption(f"Season: {years.min()}")
            else:
                lo, hi = int(years.min()), int(years.max())
                sel = st.slider(
                    "Season range", lo, hi, (lo, hi),
                    key=f"{key}_seasons"
                )
                out = out[out["season_year"].between(sel[0], sel[1])]
        i += 1

    if teams:
        with cols[i]:
            options = sorted(
                set(out["team1"].dropna()) | set(out["team2"].dropna())
            )
            sel = st.multiselect(
                "Teams (matches involving)", options,
                key=f"{key}_teams"
            )
            if sel:
                out = out[
                    out["team1"].isin(sel) | out["team2"].isin(sel)
                ]
        i += 1

    if venues:
        with cols[i]:
            options = sorted(out["venue"].dropna().unique().tolist())
            sel = st.multiselect("Venues", options, key=f"{key}_venues")
            if sel:
                out = out[out["venue"].isin(sel)]
        i += 1

    if cities and "city" in df.columns:
        with cols[i]:
            options = sorted(out["city"].dropna().astype(str).unique())
            sel = st.multiselect("Cities", options, key=f"{key}_cities")
            if sel:
                out = out[out["city"].astype(str).isin(sel)]
        i += 1

    if match_types and "match_type" in df.columns:
        with cols[i]:
            options = sorted(
                out["match_type"].dropna().astype(str).unique()
            )
            sel = st.multiselect(
                "Match types", options, key=f"{key}_mtypes"
            )
            if sel:
                out = out[out["match_type"].astype(str).isin(sel)]
        i += 1

    return out


def count_slider(label, max_value, default, key, min_value=1):
    """Slider that does not crash when min == max."""

    max_value = int(max_value)
    if max_value <= min_value:
        st.caption(f"{label}: {min_value}")
        return min_value
    return st.slider(
        label, min_value, max_value,
        min(default, max_value), key=key
    )


def no_data(df, message="No data for the selected filters."):
    if df is None or len(df) == 0:
        st.info(message)
        return True
    return False


# =========================================================
# 4. SIDEBAR (GLOBAL SEASON BASE FILTER)
# =========================================================

st.sidebar.title("ANALYSIS CONTROLS")
st.sidebar.caption("Cricket data at a glance")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["IPL Overview", "Team Analysis", "Venue Analysis"]
)

st.sidebar.divider()

THEME = THEMES["Royal Gold"]
st.markdown(build_theme_css(THEME), unsafe_allow_html=True)

pio.templates["ipl_custom"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=THEME["text"]),
        colorway=THEME["colorway"],
    )
)
CHART_TEMPLATE = "plotly_dark+ipl_custom"

st.sidebar.divider()

season_values = sorted(
    matches["season_year"].dropna().astype(int).unique(),
    reverse=True
)

selected_season = st.sidebar.selectbox(
    "Global season (base for all charts)",
    ["All Seasons"] + [str(y) for y in season_values]
)

season_df = apply_season_filter(matches, selected_season)

st.sidebar.caption(f"Database: {len(matches):,} match records")
st.sidebar.caption(
    "Each chart also has its own 🔎 filters, shown above the chart."
)


# =========================================================
# 5. IPL OVERVIEW
# =========================================================

if page == "IPL Overview":

    title_card(
        "IPL Cricket Analytics",
        "Explore IPL match trends, team performance and venue statistics.",
        "🏏",
        badge="IPL Cricket Analytics · Overview"
    )
    st.subheader("IPL Overview")

    overview_teams = (
        set(season_df["team1"].dropna()) | set(season_df["team2"].dropna())
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Matches in Dataset", f"{len(matches):,}")
    k2.metric("Matches in Global Season",
              f"{season_df['match_id'].nunique():,}")
    k3.metric("Teams in Selection", len(overview_teams))

    # ---------- Chart 1: matches per season ----------
    st.subheader("IPL Seasons Show Different Match Volumes")

    with st.expander("🔎 Chart filters", expanded=False):
        d1 = chart_filters(
            season_df, "ov1",
            seasons=True, teams=True, cities=True, match_types=True
        )

    if not no_data(d1):
        season_counts = (
            d1.dropna(subset=["season_year"])
            .groupby("season_year")["match_id"]
            .nunique()
            .reset_index(name="Matches")
        )
        season_counts["Season"] = \
            season_counts["season_year"].astype(int).astype(str)

        fig1 = px.bar(
            season_counts, x="Season", y="Matches", text="Matches",
            color="Matches", color_continuous_scale=THEME["scale"],
            template=CHART_TEMPLATE,
            labels={"Matches": "Number of matches"},
            title="Matches Played in Each Season"
        )
        fig1.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Season", yaxis_title="Matches played",
            height=440
        )
        st.plotly_chart(fig1, use_container_width=True,
                        key="overview_season_bar")

    # ---------- Chart 2: trend line ----------
    st.subheader("The Match Schedule Changes Across Seasons")

    with st.expander("🔎 Chart filters", expanded=False):
        d2 = chart_filters(
            season_df, "ov2",
            seasons=True, teams=True, venues=True, cities=True
        )

    if not no_data(d2):
        trend = (
            d2.dropna(subset=["season_year"])
            .groupby("season_year")["match_id"]
            .nunique()
            .reset_index(name="Matches")
        )
        trend["Season"] = trend["season_year"].astype(int).astype(str)

        fig2 = px.line(
            trend, x="Season", y="Matches", markers=True,
            template=CHART_TEMPLATE, title="Season-by-Season Match Trend"
        )
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True,
                        key="overview_season_line")

    # ---------- Chart 3: top winning teams ----------
    st.subheader("A Small Group of Teams Records the Most Wins")

    with st.expander("🔎 Chart filters", expanded=False):
        d3 = chart_filters(
            season_df, "ov3",
            seasons=True, venues=True, cities=True, match_types=True
        )
        top_n_wins = count_slider(
            "Number of teams to show", 20, 10, "ov3_topn"
        )

    team_stats_ov = get_team_stats(d3)

    if not no_data(team_stats_ov):
        top_winners = (
            team_stats_ov.sort_values("Wins", ascending=False)
            .head(top_n_wins)
            .sort_values("Wins")
        )

        fig3 = px.bar(
            top_winners, x="Wins", y="Team", orientation="h",
            text="Wins", color="Wins", color_continuous_scale=THEME["scale"],
            template=CHART_TEMPLATE,
            title=f"Top {len(top_winners)} Teams by Total Wins"
        )
        fig3.update_layout(coloraxis_showscale=False, height=420)
        st.plotly_chart(fig3, use_container_width=True,
                        key="overview_team_wins")

    # ---------- Chart 4: venues ----------
    st.subheader("A Few Venues Host More IPL Matches")

    with st.expander("🔎 Chart filters", expanded=False):
        d4 = chart_filters(
            season_df, "ov4",
            seasons=True, teams=True, cities=True, match_types=True
        )
        top_n_venues = count_slider(
            "Number of venues to show", 30, 10, "ov4_topn"
        )

    if not no_data(d4):
        venue_counts = (
            d4.groupby("venue")["match_id"]
            .nunique()
            .reset_index(name="Matches")
            .sort_values("Matches", ascending=False)
            .head(top_n_venues)
            .sort_values("Matches")
        )

        fig4 = px.bar(
            venue_counts, x="Matches", y="venue", orientation="h",
            text="Matches", template=CHART_TEMPLATE,
            color="Matches", color_continuous_scale=THEME["scale"],
            title=f"Top {len(venue_counts)} Venues by Match Count"
        )
        fig4.update_layout(
            coloraxis_showscale=False, height=420, yaxis_title="Venue"
        )
        st.plotly_chart(fig4, use_container_width=True,
                        key="overview_venue_count")

    # ---------- Statistical finding ----------
    st.subheader("Statistical Finding")

    with st.expander("🔎 Chart filters", expanded=False):
        d5 = chart_filters(
            season_df, "ov5",
            seasons=True, venues=True, cities=True, match_types=True
        )
        stat_stats = get_team_stats(d5)
        min_matches_stat = count_slider(
            "Minimum matches per team",
            stat_stats["Matches"].max() if not stat_stats.empty else 1,
            10, "ov5_minm"
        )

    eligible = stat_stats[
        (stat_stats["Matches"] >= min_matches_stat)
        & (stat_stats["Wins"] + stat_stats["Losses"] > 0)
    ] if not stat_stats.empty else stat_stats

    if not no_data(eligible, "No teams meet the selected filters."):
        leader = eligible.sort_values("Win Rate", ascending=False).iloc[0]
        decided = int(leader["Wins"] + leader["Losses"])
        lower, upper = wilson_interval(int(leader["Wins"]), decided)

        st.info(
            f"Among teams with at least {min_matches_stat} matches, "
            f"{leader['Team']} has the highest observed win rate "
            f"at {leader['Win Rate']:.2f}%. "
            f"The approximate 95% Wilson confidence interval is "
            f"{lower:.2f}%–{upper:.2f}% "
            f"({int(leader['Wins'])} wins in {decided} decided matches)."
        )

    st.caption(
        "Win-rate interval uses the Wilson binomial method. "
        "It describes uncertainty in the observed win proportion; "
        "it is not proof that one team is better than another."
    )


# =========================================================
# 6. TEAM ANALYSIS
# =========================================================

elif page == "Team Analysis":

    title_card(
        "Team Analysis",
        "Compare IPL teams using interactive charts.",
        "🏆",
        badge="Teams Intelligence"
    )

    base_stats = get_team_stats(season_df)

    if base_stats.empty:
        st.warning("No team records are available for this season.")
        st.stop()

    eligible_kpi = base_stats[base_stats["Matches"] >= 10]
    if eligible_kpi.empty:
        eligible_kpi = base_stats
    best_team = eligible_kpi.sort_values(
        "Win Rate", ascending=False
    ).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Teams Analysed", len(base_stats))
    c2.metric("Highest Win Rate", f"{best_team['Win Rate']:.2f}%")
    c3.metric("Top Team", best_team["Team"])
    st.caption("KPIs use the global season (teams with 10+ matches).")

    # ---------- Chart 1: win rate ----------
    st.subheader("Some Teams Win a Higher Share of Their Matches")

    with st.expander("🔎 Chart filters", expanded=False):
        t1 = chart_filters(
            season_df, "tm1", seasons=True, venues=True, cities=True
        )
        s1_all = get_team_stats(t1)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_m1 = count_slider(
                "Minimum matches played",
                s1_all["Matches"].max() if not s1_all.empty else 1,
                10, "tm1_minm"
            )
        with fc2:
            sel_t1 = st.multiselect(
                "Select teams (optional)",
                sorted(s1_all["Team"].unique().tolist())
                if not s1_all.empty else [],
                key="tm1_teams"
            )

    s1 = s1_all[s1_all["Matches"] >= min_m1] if not s1_all.empty else s1_all
    if sel_t1:
        s1 = s1[s1["Team"].isin(sel_t1)]

    if not no_data(s1, "No teams meet the selected filters."):
        rate_data = s1.sort_values("Win Rate")
        avg_rate = (
            s1["Wins"].sum()
            / max(1, s1["Wins"].sum() + s1["Losses"].sum()) * 100
        )

        fig1 = px.bar(
            rate_data, x="Win Rate", y="Team", orientation="h",
            text=rate_data["Win Rate"].map(lambda x: f"{x:.1f}%"),
            color="Win Rate", color_continuous_scale=THEME["scale"],
            template=CHART_TEMPLATE, title="Team Win Rate (%)"
        )
        fig1.add_vline(
            x=avg_rate, line_dash="dash", line_color="#FF6B6B",
            annotation_text=f"Selected-team average: {avg_rate:.1f}%"
        )
        fig1.update_layout(
            coloraxis_showscale=False,
            height=max(380, len(rate_data) * 32),
            xaxis_title="Win rate (%)", yaxis_title="Team"
        )
        st.plotly_chart(fig1, use_container_width=True,
                        key="team_win_rate")

    # ---------- Chart 2: wins vs losses ----------
    st.subheader("Winning and Losing Records Differ Across Teams")

    with st.expander("🔎 Chart filters", expanded=False):
        t2 = chart_filters(
            season_df, "tm2", seasons=True, venues=True, cities=True
        )
        s2_all = get_team_stats(t2)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            min_m2 = count_slider(
                "Minimum matches played",
                s2_all["Matches"].max() if not s2_all.empty else 1,
                10, "tm2_minm"
            )
        with fc2:
            sel_t2 = st.multiselect(
                "Select teams (optional)",
                sorted(s2_all["Team"].unique().tolist())
                if not s2_all.empty else [],
                key="tm2_teams"
            )
        with fc3:
            results_shown = st.multiselect(
                "Results to show", ["Wins", "Losses"],
                default=["Wins", "Losses"], key="tm2_results"
            )

    s2 = s2_all[s2_all["Matches"] >= min_m2] if not s2_all.empty else s2_all
    if sel_t2:
        s2 = s2[s2["Team"].isin(sel_t2)]

    if not no_data(s2, "No teams meet the selected filters.") \
            and results_shown:
        result_data = s2.melt(
            id_vars=["Team"], value_vars=results_shown,
            var_name="Result", value_name="Count"
        )
        fig2 = px.bar(
            result_data, x="Team", y="Count", color="Result",
            barmode="group", text="Count",
            color_discrete_map={"Wins": "#25B889", "Losses": "#F06464"},
            template=CHART_TEMPLATE, title="Wins Compared with Losses"
        )
        fig2.update_layout(
            xaxis_title="Team", yaxis_title="Match count", height=430
        )
        st.plotly_chart(fig2, use_container_width=True,
                        key="team_wins_losses")

    # ---------- Chart 3: matches vs win rate ----------
    st.subheader("More Matches Do Not Automatically Mean a Higher Win Rate")

    with st.expander("🔎 Chart filters", expanded=False):
        t3 = chart_filters(
            season_df, "tm3", seasons=True, venues=True, cities=True
        )
        s3_all = get_team_stats(t3)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_m3 = count_slider(
                "Minimum matches played",
                s3_all["Matches"].max() if not s3_all.empty else 1,
                10, "tm3_minm"
            )
        with fc2:
            sel_t3 = st.multiselect(
                "Select teams (optional)",
                sorted(s3_all["Team"].unique().tolist())
                if not s3_all.empty else [],
                key="tm3_teams"
            )

    s3 = s3_all[s3_all["Matches"] >= min_m3] if not s3_all.empty else s3_all
    if sel_t3:
        s3 = s3[s3["Team"].isin(sel_t3)]

    if not no_data(s3, "No teams meet the selected filters."):
        avg3 = (
            s3["Wins"].sum()
            / max(1, s3["Wins"].sum() + s3["Losses"].sum()) * 100
        )
        fig3 = px.scatter(
            s3, x="Matches", y="Win Rate", size="Wins", color="Team",
            hover_data=["Wins", "Losses"], template=CHART_TEMPLATE,
            title="Matches Played Versus Win Rate (%)"
        )
        fig3.add_hline(
            y=avg3, line_dash="dash", line_color="#FF6B6B",
            annotation_text="Selected-team average"
        )
        fig3.update_layout(
            xaxis_title="Matches played",
            yaxis_title="Win rate (%)", height=430
        )
        st.plotly_chart(fig3, use_container_width=True,
                        key="team_matches_scatter")

    # ---------- Table: top teams ----------
    st.subheader("Top Teams by Win Rate")

    with st.expander("🔎 Chart filters", expanded=False):
        t4 = chart_filters(
            season_df, "tm4", seasons=True, venues=True, cities=True
        )
        s4_all = get_team_stats(t4)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_m4 = count_slider(
                "Minimum matches played",
                s4_all["Matches"].max() if not s4_all.empty else 1,
                10, "tm4_minm"
            )
        with fc2:
            top_n4 = count_slider(
                "Number of teams to show", 15, 5, "tm4_topn"
            )

    s4 = s4_all[s4_all["Matches"] >= min_m4] if not s4_all.empty else s4_all

    if not no_data(s4, "No teams meet the selected filters."):
        top_tbl = (
            s4.sort_values(
                ["Win Rate", "Wins", "Matches"],
                ascending=[False, False, False]
            )
            .head(top_n4)
            .reset_index(drop=True)
        )
        top_tbl.index = top_tbl.index + 1
        top_tbl.index.name = "Rank"

        disp = top_tbl[
            ["Team", "Matches", "Wins", "Losses", "Win Rate"]
        ].copy()
        disp["Win Rate"] = disp["Win Rate"].map(lambda x: f"{x:.2f}%")

        st.dataframe(disp, use_container_width=True)


# =========================================================
# 7. VENUE ANALYSIS
# =========================================================

elif page == "Venue Analysis":

    title_card(
        "Venue Analysis",
        "Explore match distribution and results across IPL venues.",
        "🏟️",
        badge="Venues Intelligence"
    )

    base_venues = get_venue_stats(season_df)

    if base_venues.empty:
        st.warning("No venue records are available for this season.")
        st.stop()

    busiest = base_venues.sort_values("Matches", ascending=False).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Venues Analysed", len(base_venues))
    c2.metric("Matches in Global Season", int(base_venues["Matches"].sum()))
    c3.metric("Busiest Venue", busiest["Venue"])

    # ---------- Chart 1: match counts ----------
    st.subheader("A Few Venues Host More IPL Matches")

    with st.expander("🔎 Chart filters", expanded=False):
        v1 = chart_filters(
            season_df, "vn1",
            seasons=True, teams=True, cities=True, match_types=True
        )
        vs1_all = get_venue_stats(v1)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_v1 = count_slider(
                "Minimum matches at venue",
                vs1_all["Matches"].max() if not vs1_all.empty else 1,
                5, "vn1_minm"
            )
        with fc2:
            sel_v1 = st.multiselect(
                "Select venues (optional)",
                sorted(vs1_all["Venue"].unique().tolist())
                if not vs1_all.empty else [],
                key="vn1_venues"
            )

    vs1 = vs1_all[vs1_all["Matches"] >= min_v1] \
        if not vs1_all.empty else vs1_all
    if sel_v1:
        vs1 = vs1[vs1["Venue"].isin(sel_v1)]

    if not no_data(vs1, "No venues meet the selected filters."):
        bar_data = vs1.sort_values("Matches", ascending=True)
        fig1 = px.bar(
            bar_data, x="Matches", y="Venue", orientation="h",
            text="Matches", color="Matches",
            color_continuous_scale=THEME["scale"], template=CHART_TEMPLATE,
            title="Match Count by Venue"
        )
        fig1.update_layout(
            coloraxis_showscale=False,
            height=max(400, len(bar_data) * 28),
            xaxis_title="Number of matches", yaxis_title="Venue"
        )
        st.plotly_chart(fig1, use_container_width=True,
                        key="venue_match_count")

    # ---------- Chart 2: batting first vs chasing ----------
    st.subheader("Venue Results Differ Between Batting First and Chasing")

    with st.expander("🔎 Chart filters", expanded=False):
        v2 = chart_filters(
            season_df, "vn2",
            seasons=True, teams=True, cities=True, match_types=True
        )
        vs2_all = get_venue_stats(v2)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            min_v2 = count_slider(
                "Minimum matches at venue",
                vs2_all["Matches"].max() if not vs2_all.empty else 1,
                5, "vn2_minm"
            )
        with fc2:
            sel_v2 = st.multiselect(
                "Select venues (optional)",
                sorted(vs2_all["Venue"].unique().tolist())
                if not vs2_all.empty else [],
                key="vn2_venues"
            )
        with fc3:
            win_types = st.multiselect(
                "Win types",
                ["Batting First Wins", "Chasing Wins"],
                default=["Batting First Wins", "Chasing Wins"],
                key="vn2_types"
            )

    vs2 = vs2_all[vs2_all["Matches"] >= min_v2] \
        if not vs2_all.empty else vs2_all
    if sel_v2:
        vs2 = vs2[vs2["Venue"].isin(sel_v2)]

    if not no_data(vs2, "No venues meet the selected filters.") \
            and win_types:
        res_data = vs2.melt(
            id_vars=["Venue"], value_vars=win_types,
            var_name="Win Type", value_name="Count"
        )
        fig2 = px.bar(
            res_data, x="Venue", y="Count", color="Win Type",
            barmode="group", template=CHART_TEMPLATE,
            color_discrete_map={
                "Batting First Wins": "#F4C542",
                "Chasing Wins": "#25B889"
            },
            title="Wins by Batting First Versus Chasing"
        )
        fig2.update_layout(
            xaxis_title="Venue", yaxis_title="Number of wins", height=450
        )
        st.plotly_chart(fig2, use_container_width=True,
                        key="venue_win_type")

    # ---------- Chart 3: outcome share donut ----------
    st.subheader("Chasing and Batting-First Wins Make Up Different Shares")

    with st.expander("🔎 Chart filters", expanded=False):
        v3 = chart_filters(
            season_df, "vn3",
            seasons=True, teams=True, venues=True,
            cities=True, match_types=True
        )

    vs3 = get_venue_stats(v3)

    if not no_data(vs3):
        outcome_summary = pd.DataFrame({
            "Result Type": [
                "Batting First Wins", "Chasing Wins", "Other Results"
            ],
            "Matches": [
                int(vs3["Batting First Wins"].sum()),
                int(vs3["Chasing Wins"].sum()),
                int(vs3["Other Results"].sum()),
            ]
        })
        fig3 = px.pie(
            outcome_summary, names="Result Type", values="Matches",
            hole=0.48, template=CHART_TEMPLATE,
            title="Distribution of Venue Match Outcomes"
        )
        fig3.update_traces(textinfo="label+percent")
        fig3.update_layout(height=420)
        st.plotly_chart(fig3, use_container_width=True,
                        key="venue_outcome_donut")

    # ---------- Table: venue summary ----------
    st.subheader("Venue Match Summary")

    with st.expander("🔎 Chart filters", expanded=False):
        v4 = chart_filters(
            season_df, "vn4",
            seasons=True, teams=True, cities=True, match_types=True
        )
        vs4_all = get_venue_stats(v4)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_v4 = count_slider(
                "Minimum matches at venue",
                vs4_all["Matches"].max() if not vs4_all.empty else 1,
                1, "vn4_minm"
            )
        with fc2:
            search = st.text_input(
                "Search venue name", key="vn4_search"
            )

    vs4 = vs4_all[vs4_all["Matches"] >= min_v4] \
        if not vs4_all.empty else vs4_all
    if search.strip() and not vs4.empty:
        vs4 = vs4[
            vs4["Venue"].str.contains(search.strip(), case=False, na=False)
        ]

    if not no_data(vs4, "No venues meet the selected filters."):
        tbl = vs4.sort_values(
            "Matches", ascending=False
        ).reset_index(drop=True)
        tbl.index = tbl.index + 1
        tbl.index.name = "Rank"
        st.dataframe(tbl, use_container_width=True)

    st.caption(
        "Batting-first wins are identified using win_by_runs > 0, "
        "and chasing wins using win_by_wickets > 0. "
        "Other results may include ties, no-results or records "
        "without a positive run/wicket margin."
    )


# =========================================================
# 8. FOOTER
# =========================================================

st.divider()
st.caption(
    "IPL Cricket Analytics | Source: local SQLite database | "
    "Each chart responds to its own filters."
)