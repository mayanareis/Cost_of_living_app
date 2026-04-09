import streamlit as st
import pandas as pd
from pathlib import Path

from utils.data_loader import load_data, get_filter_options
from utils.filters import apply_filters
from utils.metrics import compute_kpis, generate_insights
from utils.charts import build_map, build_cost_breakdown, build_category_donut

LOGO1 = Path(__file__).parent / "Assets" / "LOGO1.png"  # dark ink — for light backgrounds
LOGO2 = Path(__file__).parent / "Assets" / "LOGO2.png"  # white ink — for dark sidebar
QUEEN_IMG = Path(__file__).parent / "Assets" / "queen.jpg"  # landing illustration


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _color_category(val: str) -> str:
    return {
        "Affordable": "background-color:#DCFCE7; color:#15803D; font-weight:600",
        "Moderate":   "background-color:#FEF9C3; color:#A16207; font-weight:600",
        "Expensive":  "background-color:#FEE2E2; color:#B91C1C; font-weight:600",
    }.get(val, "")


def section(label: str) -> None:
    """Left-border accent section header. No icons, no emojis."""
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:12px;margin:40px 0 18px 0;">
               <div style="width:3px;height:14px;background:#0A2342;border-radius:2px;flex-shrink:0;"></div>
               <span style="font-size:0.68rem;font-weight:700;color:#0A2342;
                            letter-spacing:0.12em;text-transform:uppercase;">{label}</span>
               <div style="flex:1;height:1px;background:#E2E8F0;"></div>
            </div>""",
        unsafe_allow_html=True,
    )


def sidebar_group(text: str) -> None:
    """Render a muted uppercase group label inside the dark sidebar."""
    st.markdown(
        f'<p style="font-size:9.5px;font-weight:700;letter-spacing:0.13em;'
        f'text-transform:uppercase;color:#64748B;margin:20px 0 6px 0;">{text}</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cost of Living Explorer",
    page_icon=str(LOGO1),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}
/* Hide Streamlit chrome we don't need — without touching the sidebar toggle */
#MainMenu                           { visibility: hidden; }
footer                              { visibility: hidden; }
[data-testid="stDecoration"]        { display: none; }
[data-testid="stStatusWidget"]      { display: none; }

/* Hide the Deploy / Share button inside the toolbar, but NOT the toolbar itself.
   stSidebarCollapsedControl lives inside stToolbar in Streamlit 1.35+,
   so hiding the entire toolbar removes the sidebar reopen button. */
[data-testid="stToolbarActionButton"]          { display: none !important; }
[data-testid="stToolbarActionButton"] + button { display: none !important; }

/* Explicitly guarantee the sidebar toggle is always visible and clickable */
[data-testid="stSidebarCollapsedControl"]      { display: flex !important; visibility: visible !important; }

/* ── Main content ── */
.block-container {
    padding-top: 5rem;        /* clears the ~60px fixed toolbar + breathing room */
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1440px;
}

/* ── Sidebar shell ── */
[data-testid="stSidebar"] {
    background: #0A2342 !important;
    border-right: none;
}

/* All text in sidebar: light by default so nothing disappears */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #CBD5E1; }

/* Widget labels — uppercase, muted */
[data-testid="stSidebar"] label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
}

/* Number input */
[data-testid="stSidebar"] input[type="number"] {
    background: #112D52 !important;
    border: 1px solid #1E3F6A !important;
    color: #E2E8F0 !important;
    border-radius: 6px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}

/* Selectbox + multiselect containers */
[data-testid="stSidebar"] [data-baseweb="select"] {
    background: #112D52 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #112D52 !important;
    border: 1px solid #1E3F6A !important;
    border-radius: 6px !important;
    color: #E2E8F0 !important;
    font-size: 13px !important;
}

/* Selected value text inside dropdowns */
[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #E2E8F0 !important;
}

/* Multiselect tags */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #1B4F87 !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] span { color: #fff !important; }

/* Dividers */
[data-testid="stSidebar"] hr {
    border: none;
    border-top: 1px solid #1B4F87;
    margin: 16px 0;
}

/* Checkbox */
[data-testid="stSidebar"] .stCheckbox label {
    font-size: 12px !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    color: #CBD5E1 !important;
    font-weight: 400 !important;
}

/* ── Hero ── */
.hero-eyebrow {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #1B6CA8;
    margin: 0 0 10px 0;
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 700;
    color: #0A2342;
    margin: 0 0 10px 0;
    line-height: 1.15;
    letter-spacing: -0.025em;
}
.hero-subtitle {
    font-size: 0.9rem;
    color: #64748B;
    font-weight: 400;
    line-height: 1.65;
    margin: 0;
    max-width: 520px;
}

/* ── KPI cards ── */
.kpi-card {
    background: #fff;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #0A2342;
    padding: 20px 18px 16px 18px;
    box-shadow: 0 1px 3px rgba(10,35,66,0.05), 0 1px 2px rgba(10,35,66,0.03);
    height: 100%;
    box-sizing: border-box;
}
.kpi-label {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 0 0 10px 0;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #0A2342;
    margin: 0;
    line-height: 1;
    letter-spacing: -0.025em;
}
.kpi-sub {
    font-size: 11px;
    color: #94A3B8;
    margin: 6px 0 0 0;
    font-weight: 400;
}
.kpi-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 8px;
    letter-spacing: 0.02em;
}
.badge-affordable { background:#DCFCE7; color:#15803D; }
.badge-moderate   { background:#FEF9C3; color:#A16207; }
.badge-expensive  { background:#FEE2E2; color:#B91C1C; }

/* ── Insight cards ── */
.insight-card {
    background: #fff;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    padding: 20px 20px 20px 18px;
    box-shadow: 0 1px 3px rgba(10,35,66,0.04);
    height: 100%;
    box-sizing: border-box;
}
.insight-headline {
    font-size: 0.825rem;
    font-weight: 600;
    color: #0A2342;
    margin: 0 0 6px 0;
    line-height: 1.4;
}
.insight-body {
    font-size: 0.775rem;
    color: #64748B;
    margin: 0;
    line-height: 1.6;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 90px 20px;
}
.empty-state-title {
    font-size: 1rem;
    font-weight: 600;
    color: #334155;
    margin: 0 0 8px 0;
}
.empty-state-body {
    font-size: 0.825rem;
    color: #94A3B8;
    line-height: 1.65;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: #0A2342;
    color: #fff;
    border: none;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 500;
    padding: 7px 16px;
    letter-spacing: 0.01em;
    margin-top: 10px;
    transition: background 0.15s;
}
[data-testid="stDownloadButton"] button:hover { background: #1B4F87; }

/* ── Dataframe ── */
.stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Data
# ─────────────────────────────────────────────────────────────────────────────
df_raw = load_data()
options = get_filter_options(df_raw)


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(str(LOGO2), use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Group 1: Salary ───────────────────────────────────────────────────────
    sidebar_group("Your Salary")
    annual_salary = st.number_input(
        "Annual Salary (USD)",
        min_value=0,
        max_value=10_000_000,
        value=0,
        step=5_000,
        format="%d",
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Group 2: Lifestyle ────────────────────────────────────────────────────
    sidebar_group("Lifestyle")
    lifestyle = st.selectbox("Lifestyle Type", options=options["lifestyles"])
    transport = st.selectbox("Transportation", options=options["transport_modes"])

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Group 3: Location ─────────────────────────────────────────────────────
    sidebar_group("Location")
    regions = st.multiselect(
        "Region",
        options=options["regions"],
        default=[],
        placeholder="All regions",
    )
    location_pref = st.selectbox(
        "City Location",
        options=["All"] + options["location_prefs"],
    )
    apartment_sizes = st.multiselect(
        "Apartment Size",
        options=options["apartment_sizes"],
        default=[],
        placeholder="All sizes",
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Group 4: Display options ──────────────────────────────────────────────
    sidebar_group("Display Options")
    affordable_only = st.checkbox("Affordable cities only  (≤ 30%)", value=False)

    st.markdown(
        '<p style="font-size:10px;color:#475569;text-align:center;'
        'margin-top:28px;line-height:1.7;">'
        'All costs in USD &middot; 2024 estimates</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<p class="hero-eyebrow">Business Intelligence &amp; Data Storytelling</p>
<h1 class="hero-title">Cost of Living Explorer</h1>
<p class="hero-subtitle">
    Compare the real cost of living across 24 global cities.
    Set your salary and preferences to instantly see where your income
    goes furthest — and what drives the difference.
</p>
<hr style="border:none;border-top:1px solid #E2E8F0;margin:22px 0 0 0;">
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Guard: no salary
# ─────────────────────────────────────────────────────────────────────────────
if annual_salary <= 0:
    # Text block — centered, generous vertical padding
    st.markdown("""
    <div style="text-align:center;padding:52px 0 28px 0;">
        <p style="font-size:1rem;font-weight:600;color:#0A2342;margin:0 0 8px 0;">
            Enter your annual salary to begin
        </p>
        <p style="font-size:0.825rem;color:#94A3B8;line-height:1.65;margin:0;">
            Input your salary in the sidebar and configure your lifestyle preferences.<br>
            Results update instantly as you adjust the filters.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # City skyline illustration — centred, max width constrained so it doesn't
    # stretch edge-to-edge on wide monitors
    _, img_col, _ = st.columns([1, 4, 1])
    with img_col:
        st.image(str(QUEEN_IMG), use_container_width=True)

    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Filter & compute
# ─────────────────────────────────────────────────────────────────────────────
monthly_salary = annual_salary / 12
filtered_df = apply_filters(
    df=df_raw,
    monthly_salary=monthly_salary,
    regions=regions,
    lifestyle=lifestyle,
    location_pref=location_pref,
    apartment_sizes=apartment_sizes,
    transport=transport,
    affordable_only=affordable_only,
)

if filtered_df.empty:
    st.markdown("""
    <div class="empty-state">
        <p class="empty-state-title">No results match these filters</p>
        <p class="empty-state-body">
            Try removing the affordable-only filter, broadening your region
            selection, or including additional apartment sizes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

kpis = compute_kpis(filtered_df, monthly_salary)


# ─────────────────────────────────────────────────────────────────────────────
#  KPI Cards
# ─────────────────────────────────────────────────────────────────────────────
section("Summary")

c1, c2, c3, c4, c5 = st.columns(5, gap="small")

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Cities Found</p>
        <p class="kpi-value">{kpis['city_count']}</p>
        <p class="kpi-sub">{len(filtered_df['Region'].unique())} region(s)</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Monthly Cost Range</p>
        <p class="kpi-value">${kpis['cost_range_low']:,}</p>
        <p class="kpi-sub">to ${kpis['cost_range_high']:,} / month</p>
    </div>""", unsafe_allow_html=True)

with c3:
    avg_pct = kpis['avg_affordability_pct']
    if avg_pct <= 30:
        badge_cls, badge_lbl = "badge-affordable", "Affordable"
    elif avg_pct <= 50:
        badge_cls, badge_lbl = "badge-moderate", "Moderate"
    else:
        badge_cls, badge_lbl = "badge-expensive", "Expensive"
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Avg. Income Used</p>
        <p class="kpi-value">{avg_pct}%</p>
        <span class="kpi-badge {badge_cls}">{badge_lbl}</span>
    </div>""", unsafe_allow_html=True)

with c4:
    a, m, e = kpis['affordable_count'], kpis['moderate_count'], kpis['expensive_count']
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">City Breakdown</p>
        <div style="margin-top:8px;display:flex;flex-direction:column;gap:5px;">
            <div style="display:flex;align-items:center;gap:7px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#27AE60;flex-shrink:0;"></div>
                <span style="font-size:12px;color:#374151;font-weight:500;">{a} affordable</span>
            </div>
            <div style="display:flex;align-items:center;gap:7px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#F39C12;flex-shrink:0;"></div>
                <span style="font-size:12px;color:#374151;font-weight:500;">{m} moderate</span>
            </div>
            <div style="display:flex;align-items:center;gap:7px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#E74C3C;flex-shrink:0;"></div>
                <span style="font-size:12px;color:#374151;font-weight:500;">{e} expensive</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color:#27AE60;">
        <p class="kpi-label">Best Match</p>
        <p class="kpi-value" style="font-size:1.3rem;margin-top:4px;">{kpis['best_city']}</p>
        <p class="kpi-sub">lowest cost, affordable tier</p>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Map
# ─────────────────────────────────────────────────────────────────────────────
section("City Map")

map_fig = build_map(filtered_df)
st.plotly_chart(map_fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
#  Cost Breakdown
# ─────────────────────────────────────────────────────────────────────────────
section("Cost Breakdown by City")

col_chart, col_donut = st.columns([3, 1], gap="large")

with col_chart:
    breakdown_fig = build_cost_breakdown(filtered_df)
    st.plotly_chart(breakdown_fig, use_container_width=True, config={"displayModeBar": False})

with col_donut:
    st.markdown(
        '<p style="font-size:10px;font-weight:700;letter-spacing:0.10em;'
        'text-transform:uppercase;color:#94A3B8;margin:0 0 6px 0;">Affordability Mix</p>',
        unsafe_allow_html=True,
    )
    donut_fig = build_category_donut(filtered_df)
    st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
#  Results Table
# ─────────────────────────────────────────────────────────────────────────────
section("Full Results")

display_cols = {
    "City": "City",
    "Country": "Country",
    "Region": "Region",
    "Apartment_Size": "Size",
    "Location_Preference": "Location",
    "Rent_Monthly_USD": "Rent",
    "Utilities_Monthly_USD": "Utilities",
    "Transportation_Monthly_USD": "Transport",
    "Groceries_Monthly_USD": "Groceries",
    "Total_Monthly_USD": "Total / mo.",
    "Affordability_Percent": "% of Income",
    "Affordability_Category": "Category",
    "Min_Salary_Needed": "Min. Salary Needed",
}

table_df = (
    filtered_df[list(display_cols.keys())]
    .rename(columns=display_cols)
    .sort_values("Total / mo.")
    .reset_index(drop=True)
)

money_cols = ["Rent", "Utilities", "Transport", "Groceries", "Total / mo.", "Min. Salary Needed"]

st.dataframe(
    table_df.style
        .format({c: "${:,.0f}" for c in money_cols})
        .format({"% of Income": "{:.1f}%"})
        .map(_color_category, subset=["Category"]),
    use_container_width=True,
    height=420,
)

st.download_button(
    label="Download CSV",
    data=table_df.to_csv(index=False).encode("utf-8"),
    file_name="cost_of_living_results.csv",
    mime="text/csv",
)


# ─────────────────────────────────────────────────────────────────────────────
#  Key Insights
# ─────────────────────────────────────────────────────────────────────────────
section("Key Insights")

ACCENT_COLORS = ["#1B6CA8", "#27AE60", "#F39C12"]
insights = generate_insights(filtered_df, monthly_salary, annual_salary)
ins_cols = st.columns(len(insights), gap="small")

for col, ins, accent in zip(ins_cols, insights, ACCENT_COLORS):
    with col:
        st.markdown(f"""
        <div class="insight-card" style="border-left:3px solid {accent};">
            <p class="insight-headline">{ins['headline']}</p>
            <p class="insight-body">{ins['body']}</p>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #E2E8F0;margin-top:52px;padding:18px 0 4px 0;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <span style="font-size:10.5px;color:#94A3B8;letter-spacing:0.02em;">
        Cost of Living Explorer &nbsp;&middot;&nbsp; Data in USD &nbsp;&middot;&nbsp; 2024 estimates
    </span>
    <span style="font-size:10.5px;color:#CBD5E1;letter-spacing:0.01em;">
        Affordability threshold: 30% of monthly income
    </span>
</div>
""", unsafe_allow_html=True)
