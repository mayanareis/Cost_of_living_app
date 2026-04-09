import pandas as pd
import streamlit as st
from pathlib import Path

REQUIRED_COLUMNS = {
    "City", "Country", "Region", "Lifestyle", "Location_Preference",
    "Apartment_Size", "Rent_Monthly_USD", "Utilities_Monthly_USD",
    "Transport_Mode", "Transportation_Monthly_USD", "Groceries_Monthly_USD",
    "Total_Monthly_USD", "Latitude", "Longitude",
}

DATA_PATH = Path(__file__).parent.parent / "Data" / "shiny_app_data.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and validate the cost-of-living dataset. Cached across sessions."""
    df = pd.read_csv(DATA_PATH)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}")

    # Coerce numeric columns — surface bad rows instead of silently dropping
    numeric_cols = [
        "Rent_Monthly_USD", "Utilities_Monthly_USD", "Transportation_Monthly_USD",
        "Groceries_Monthly_USD", "Total_Monthly_USD", "Latitude", "Longitude",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=numeric_cols + ["City", "Region", "Lifestyle"])

    # Normalize text fields so filter comparisons are reliable
    for col in ["Region", "Lifestyle", "Location_Preference", "Apartment_Size", "Transport_Mode"]:
        df[col] = df[col].str.strip()

    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """Return sorted unique values for every filter widget."""
    return {
        "regions": sorted(df["Region"].unique().tolist()),
        "lifestyles": sorted(df["Lifestyle"].unique().tolist()),
        "location_prefs": sorted(df["Location_Preference"].unique().tolist()),
        "apartment_sizes": sorted(df["Apartment_Size"].unique().tolist()),
        "transport_modes": sorted(df["Transport_Mode"].unique().tolist()),
    }
