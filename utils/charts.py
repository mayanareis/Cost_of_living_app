import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Design tokens ─────────────────────────────────────────────────────────────
NAVY   = "#0A2342"
FONT   = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

CATEGORY_COLORS = {
    "Affordable": "#27AE60",
    "Moderate":   "#F39C12",
    "Expensive":  "#E74C3C",
}

COST_COLORS = {
    "Rent":           "#0A2342",
    "Utilities":      "#1B6CA8",
    "Transportation": "#48B2D4",
    "Groceries":      "#A8D5E2",
}

_LAYOUT = dict(
    font_family=FONT,
    font_color="#374151",
    paper_bgcolor="white",
    plot_bgcolor="white",
)


# ── Map ───────────────────────────────────────────────────────────────────────

def build_map(df: pd.DataFrame) -> go.Figure:
    """
    Scatter geo map — uses Plotly's built-in Natural Earth dataset.
    No external tile servers, no API tokens, works offline and across
    all Plotly versions. One marker per city (cheapest matching row).
    """
    city_df = (
        df.sort_values("Total_Monthly_USD")
        .groupby("City", as_index=False)
        .first()
    )

    city_df["hover_text"] = city_df.apply(
        lambda r: (
            f"<b>{r['City']}, {r['Country']}</b><br>"
            f"Monthly Cost:  <b>${r['Total_Monthly_USD']:,.0f}</b><br>"
            f"Income Used:   <b>{r['Affordability_Percent']:.1f}%</b><br>"
            f"Category:      <b>{r['Affordability_Category']}</b><br>"
            f"Min. Salary:   <b>${r['Min_Salary_Needed']:,} / yr</b>"
        ),
        axis=1,
    )

    fig = px.scatter_geo(
        city_df,
        lat="Latitude",
        lon="Longitude",
        color="Affordability_Category",
        color_discrete_map=CATEGORY_COLORS,
        size="Total_Monthly_USD",
        size_max=28,
        custom_data=["hover_text"],
        projection="natural earth",
        height=460,
        category_orders={"Affordability_Category": ["Affordable", "Moderate", "Expensive"]},
    )

    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        marker_opacity=0.85,
        marker_sizemin=8,
        marker_line=dict(width=0.8, color="white"),
    )

    fig.update_geos(
        showland=True,      landcolor="#F1F5F9",
        showocean=True,     oceancolor="#EBF5FB",
        showlakes=False,
        showcountries=True, countrycolor="#CBD5E1",  countrywidth=0.4,
        showcoastlines=True,coastlinecolor="#CBD5E1", coastlinewidth=0.4,
        showframe=False,
        showrivers=False,
        bgcolor="white",
    )

    fig.update_layout(
        **_LAYOUT,
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font_size=12,
            bgcolor="rgba(255,255,255,0)",
            itemsizing="constant",
        ),
        margin=dict(l=0, r=0, t=8, b=0),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E2E8F0",
            font_size=12,
            font_family=FONT,
        ),
    )

    return fig


# ── Cost Breakdown ────────────────────────────────────────────────────────────

def build_cost_breakdown(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal stacked bar. Label = City + Size only (location already filtered
    or shown in donut). Sorted cheapest → most expensive.
    """
    plot_df = df.copy()
    plot_df["Label"] = plot_df.apply(
        lambda r: f"{r['City']}  ·  {r['Apartment_Size']} {r['Location_Preference'].replace('Center','').replace('Outside','Out.').replace('City','City')}",
        axis=1,
    )
    plot_df = plot_df.sort_values("Total_Monthly_USD", ascending=True)

    components = [
        ("Rent",           "Rent_Monthly_USD"),
        ("Utilities",      "Utilities_Monthly_USD"),
        ("Transportation", "Transportation_Monthly_USD"),
        ("Groceries",      "Groceries_Monthly_USD"),
    ]

    fig = go.Figure()
    for label, col in components:
        fig.add_trace(go.Bar(
            name=label,
            y=plot_df["Label"],
            x=plot_df[col],
            orientation="h",
            marker_color=COST_COLORS[label],
            marker_line_width=0,
            hovertemplate=f"<b>{label}</b>: $%{{x:,.0f}}<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT,
        barmode="stack",
        height=max(320, len(plot_df) * 34 + 80),
        xaxis=dict(
            title=None,
            tickprefix="$",
            tickfont_size=11,
            gridcolor="#F1F5F9",
            gridwidth=1,
            showline=False,
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            automargin=True,
            tickfont_size=11,
            tickfont_color="#374151",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font_size=12,
            bgcolor="rgba(0,0,0,0)",
            traceorder="normal",
        ),
        margin=dict(l=8, r=16, t=40, b=8),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E2E8F0",
            font_size=12,
            font_family=FONT,
        ),
    )

    return fig


# ── Donut ─────────────────────────────────────────────────────────────────────

def build_category_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["Affordability_Category"].value_counts().reindex(
        ["Affordable", "Moderate", "Expensive"], fill_value=0
    )

    n_cities = len(df["City"].unique())

    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.65,
        marker_colors=[CATEGORY_COLORS[c] for c in counts.index],
        marker_line=dict(color="white", width=2),
        hovertemplate="<b>%{label}</b><br>%{value} cities · %{percent}<extra></extra>",
        textinfo="percent",
        textfont_size=12,
        textfont_color="white",
    ))

    fig.update_layout(
        **_LAYOUT,
        height=230,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.0,
            font_size=11,
            itemsizing="constant",
        ),
        annotations=[dict(
            text=f"<b>{n_cities}</b><br><span style='font-size:10px;color:#94A3B8;'>cities</span>",
            x=0.5, y=0.5,
            font=dict(size=18, family=FONT, color="#0A2342"),
            showarrow=False,
            align="center",
        )],
        margin=dict(l=0, r=60, t=0, b=0),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E2E8F0",
            font_size=12,
            font_family=FONT,
        ),
    )

    return fig
