import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    monthly_salary: float,
    regions: list[str],
    lifestyle: str,
    location_pref: str,
    apartment_sizes: list[str],
    transport: str,
    affordable_only: bool,
) -> pd.DataFrame:
    """
    Filter the dataset by user selections and compute affordability columns.

    Mirrors the Shiny reactive logic exactly, with one improvement:
    empty multi-selects mean "show all" (same as Shiny's "All" sentinel).
    """
    mask = pd.Series(True, index=df.index)

    if regions:
        mask &= df["Region"].isin(regions)

    mask &= df["Lifestyle"] == lifestyle

    if location_pref != "All":
        mask &= df["Location_Preference"] == location_pref

    if apartment_sizes:
        mask &= df["Apartment_Size"].isin(apartment_sizes)

    mask &= df["Transport_Mode"] == transport

    result = df[mask].copy()

    # ── Affordability calculations (same as Shiny) ──────────────────────────
    result["Affordability_Ratio"] = result["Total_Monthly_USD"] / monthly_salary
    result["Affordability_Percent"] = (result["Affordability_Ratio"] * 100).round(1)
    result["Affordability_Category"] = result["Affordability_Ratio"].apply(
        _classify_affordability
    )
    result["Min_Salary_Needed"] = (result["Total_Monthly_USD"] / 0.30).round(0).astype(int)

    if affordable_only:
        result = result[result["Affordability_Ratio"] <= 0.30]

    return result.reset_index(drop=True)


def _classify_affordability(ratio: float) -> str:
    if ratio <= 0.30:
        return "Affordable"
    if ratio <= 0.50:
        return "Moderate"
    return "Expensive"
