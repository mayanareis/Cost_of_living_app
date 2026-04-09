import pandas as pd


def compute_kpis(df: pd.DataFrame, monthly_salary: float) -> dict:
    """
    Derive the five headline numbers shown in KPI cards.
    Called only when df is non-empty.
    """
    counts = df["Affordability_Category"].value_counts()

    cheapest_row = df.loc[df["Total_Monthly_USD"].idxmin()]
    most_expensive_row = df.loc[df["Total_Monthly_USD"].idxmax()]

    # "Best city" = affordable city where salary surplus is largest
    affordable = df[df["Affordability_Category"] == "Affordable"]
    if not affordable.empty:
        best_row = affordable.loc[affordable["Total_Monthly_USD"].idxmin()]
        best_city = best_row["City"]
    else:
        best_city = cheapest_row["City"]

    return {
        "city_count": len(df["City"].unique()),
        "cost_range_low": int(df["Total_Monthly_USD"].min()),
        "cost_range_high": int(df["Total_Monthly_USD"].max()),
        "avg_affordability_pct": round(df["Affordability_Percent"].mean(), 1),
        "affordable_count": int(counts.get("Affordable", 0)),
        "moderate_count": int(counts.get("Moderate", 0)),
        "expensive_count": int(counts.get("Expensive", 0)),
        "min_salary_needed_overall": int(df["Min_Salary_Needed"].min()),
        "cheapest_city": cheapest_row["City"],
        "cheapest_cost": int(cheapest_row["Total_Monthly_USD"]),
        "most_expensive_city": most_expensive_row["City"],
        "most_expensive_cost": int(most_expensive_row["Total_Monthly_USD"]),
        "best_city": best_city,
    }


def generate_insights(df: pd.DataFrame, monthly_salary: float, annual_salary: float) -> list[dict]:
    """
    Return a list of insight dicts: {icon, headline, body}.
    Each insight is a self-contained observation about the filtered results.
    """
    insights = []
    kpis = compute_kpis(df, monthly_salary)

    # ── 1. Best city for salary ─────────────────────────────────────────────
    affordable = df[df["Affordability_Category"] == "Affordable"]
    if not affordable.empty:
        best = affordable.loc[affordable["Total_Monthly_USD"].idxmin()]
        surplus = monthly_salary - best["Total_Monthly_USD"]
        insights.append({
            "icon": "✅",
            "headline": f"{best['City']} is your best affordable match",
            "body": (
                f"At ${int(best['Total_Monthly_USD']):,}/month, you'd spend "
                f"{best['Affordability_Percent']:.1f}% of your monthly income — "
                f"leaving ${int(surplus):,}/month as discretionary savings."
            ),
        })
    else:
        cheapest = df.loc[df["Total_Monthly_USD"].idxmin()]
        shortfall = cheapest["Min_Salary_Needed"] - annual_salary
        insights.append({
            "icon": "⚠️",
            "headline": "No affordable cities match your current filters",
            "body": (
                f"The lowest-cost match is {cheapest['City']} at "
                f"${int(cheapest['Total_Monthly_USD']):,}/month. "
                f"You'd need ~${int(shortfall):,} more per year to hit the 30% threshold."
            ),
        })

    # ── 2. Cost spread ──────────────────────────────────────────────────────
    spread = kpis["most_expensive_cost"] - kpis["cheapest_cost"]
    if spread > 200:
        insights.append({
            "icon": "📊",
            "headline": f"${spread:,}/month separates the cheapest from the most expensive",
            "body": (
                f"{kpis['cheapest_city']} costs ${kpis['cheapest_cost']:,}/month vs "
                f"{kpis['most_expensive_city']} at ${kpis['most_expensive_cost']:,}/month. "
                "Location and apartment size are usually the biggest levers."
            ),
        })

    # ── 3. Primary cost driver ──────────────────────────────────────────────
    cost_components = {
        "Rent": df["Rent_Monthly_USD"].mean(),
        "Groceries": df["Groceries_Monthly_USD"].mean(),
        "Transportation": df["Transportation_Monthly_USD"].mean(),
        "Utilities": df["Utilities_Monthly_USD"].mean(),
    }
    top_driver = max(cost_components, key=cost_components.get)
    top_pct = round(cost_components[top_driver] / df["Total_Monthly_USD"].mean() * 100, 1)
    insights.append({
        "icon": "💡",
        "headline": f"{top_driver} is the biggest cost driver ({top_pct}% of total)",
        "body": (
            f"Across your filtered cities, {top_driver.lower()} averages "
            f"${cost_components[top_driver]:,.0f}/month — "
            "the single largest line item to optimize."
        ),
    })

    return insights
