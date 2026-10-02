import os
import pandas as pd
import numpy as np
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DATA_PROCESSED



def load_cleaned():
    return pd.read_csv(
        os.path.join(DATA_PROCESSED, "cleaned2.csv"),
        encoding="utf-8"
    )



# CLIP TARGET

def clip_target(df):
    if "Revenue (M USD)" in df.columns:
        upper_limit = df["Revenue (M USD)"].quantile(0.99)
        df["Revenue (M USD)"] = df["Revenue (M USD)"].clip(upper=upper_limit)
        print(f"[info] Revenue clipped à : {upper_limit:.2f}")
    return df



# AGE

def add_age_features(df, current_year=2026):
    if "Year Founded" in df.columns:
        df["Company_Age"] = (current_year - df["Year Founded"]).clip(lower=0)
    else:
        df["Company_Age"] = 0
    return df



# REGION

REGION_MAP = {
    # North America
    "united states": "North_America",
    "usa": "North_America",
    "canada": "North_America",
    "mexico": "North_America",

    # Europe
    "france": "Europe",
    "germany": "Europe",
    "united kingdom": "Europe",
    "uk": "Europe",
    "spain": "Europe",
    "italy": "Europe",
    "netherlands": "Europe",
    "sweden": "Europe",
    "switzerland": "Europe",
    "belgium": "Europe",
    "poland": "Europe",
    "denmark": "Europe",
    "norway": "Europe",
    "finland": "Europe",
    "austria": "Europe",
    "ireland": "Europe",
    "luxembourg": "Europe",
    "portugal": "Europe",
    "greece": "Europe",
    "cyprus": "Europe",

    # Asia
    "china": "Asia",
    "japan": "Asia",
    "south korea": "Asia",
    "india": "Asia",
    "singapore": "Asia",
    "hong kong": "Asia",
    "taiwan": "Asia",
    "malaysia": "Asia",
    "thailand": "Asia",
    "vietnam": "Asia",

    # Other
    "australia": "Other",
    "brazil": "Other",
    "argentina": "Other",
    "nigeria": "Other",
    "egypt": "Other",
    "morocco": "Other",
    "tunisia": "Other",
    "uae": "Other",
}

def add_region(df):
    if "Region" in df.columns:
        df["Region_std"] = (
            df["Region"]
            .astype(str)
            .str.lower()
            .str.strip()
            .map(REGION_MAP)
            .fillna("Other")
        )
        df.drop(columns=["Region"], inplace=True)
    else:
        df["Region_std"] = "Other"
    return df



# INDUSTRY GROUP

INDUSTRY_TO_GROUP = {
    "Software - Application": "Tech",
    "Software - Infrastructure": "Tech",
    "Information Technology Services": "Tech",
    "Semiconductors": "Tech",
    "Internet Retail": "Tech",

    "Biotechnology": "Healthcare",
    "Medical Devices": "Healthcare",
    "Pharmaceutical Retailers": "Healthcare",

    "Banks - Regional": "Finance",
    "Capital Markets": "Finance",
    "Insurance Brokers": "Finance",

    "Aerospace & Defense": "Industrials",
    "Auto Manufacturers": "Industrials",
    "Railroads": "Industrials",

    "Restaurants": "Consumer",
    "Apparel Retail": "Consumer",
    "Grocery Stores": "Consumer",

    "Oil & Gas E&P": "Energy",
    "Solar": "Energy",

    "REIT - Office": "Real_Estate",
    "REIT - Residential": "Real_Estate",

    "Advertising Agencies": "Communication",
    "Broadcasting": "Communication",
}

def add_industry_group(df):
    if "Industry" in df.columns:
        df["Industry"] = df["Industry"].astype(str).str.strip()
        df["Industry_Group"] = df["Industry"].map(INDUSTRY_TO_GROUP).fillna("Other")
        df.drop(columns=["Industry"], inplace=True)
    else:
        df["Industry_Group"] = "Other"
    return df



# SECTOR CLEAN

def fix_sector(df):
    df["Sector"] = df["Sector"].replace({
        "Software Engineering": "Technology",
        "IT Distribution": "Technology",
        "Hardware": "Technology"
    })
    rare = df["Sector"].value_counts()
    rare = rare[rare == 1].index
    df = df[~df["Sector"].isin(rare)]
    return df


# SAFE FEATURES

def add_safe_features(df):
    if "Revenue (M USD)" in df.columns and "Employees" in df.columns:
        df["Revenue_Per_Employee"] = df["Revenue (M USD)"] / (df["Employees"] + 1e-9)

    if "Total Debt (M)" in df.columns and "Total Cash (M)" in df.columns:
        df["Net_Debt"] = df["Total Debt (M)"] - df["Total Cash (M)"]

    if "Revenue (M USD)" in df.columns:
        df["Log_Revenue"] = np.log1p(df["Revenue (M USD)"].clip(lower=0))

    if "Employees" in df.columns:
        df["Log_Employees"] = np.log1p(df["Employees"].clip(lower=0))

    return df



# FINANCIAL FEATURES

def add_financial_features(df):
    if "Total Debt (M)" in df.columns and "Revenue (M USD)" in df.columns:
        df["Debt_to_Revenue"] = df["Total Debt (M)"] / (df["Revenue (M USD)"] + 1e-9)

    if "Total Cash (M)" in df.columns and "Total Debt (M)" in df.columns:
        debt_safe = df["Total Debt (M)"].replace(0, np.nan)
        ratio = df["Total Cash (M)"] / debt_safe
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        ratio = ratio.fillna(ratio.median())
        lower = ratio.quantile(0.01)
        upper = ratio.quantile(0.99)
        ratio = ratio.clip(lower, upper)
        df["Cash_to_Debt"] = np.log1p(ratio)

    if "Revenue (M USD)" in df.columns and "Employees" in df.columns:
        df["Revenue_per_Employee"] = df["Revenue (M USD)"] / (df["Employees"] + 1e-9)

    if "Total Debt (M)" in df.columns:
        df["Debt_log"] = np.log1p(df["Total Debt (M)"].clip(lower=0))

    return df



# MISSING FEATURES

def create_missing_features(df):
    if "Total Cash (M)" in df.columns and "Total Debt (M)" in df.columns:
        df["Cash_Debt_Ratio"] = df["Total Cash (M)"] / (df["Total Debt (M)"].abs() + 1e-6)

    if "Total Debt (M)" in df.columns and "Employees" in df.columns:
        df["Debt_Per_Employee"] = df["Total Debt (M)"] / (df["Employees"] + 1e-9)

    if "Log_Revenue" in df.columns and "Log_Employees" in df.columns:
        df["Scale_Index"] = df["Log_Employees"] * df["Log_Revenue"]

    return df



# INTERACTIONS

def add_interaction_features(df):
    if "Revenue_Per_Employee" in df.columns:
        df["Efficiency_Index"] = df["Revenue_Per_Employee"]
    else:
        df["Efficiency_Index"] = df["Revenue (M USD)"] / (df["Employees"] + 1e-9)

    if "Company_Age" in df.columns and "Log_Revenue" in df.columns:
        df["Age_Size_Ratio"] = df["Company_Age"] / (df["Log_Revenue"] + 1e-9)
    else:
        df["Age_Size_Ratio"] = df["Company_Age"]

    if "Debt_to_Revenue" in df.columns and "Company_Age" in df.columns:
        df["Debt_Intensity"] = df["Debt_to_Revenue"] * df["Company_Age"]

    return df



def fit_sector_stats(train_df):
    """Calcule les stats sectorielles sur train_df uniquement."""
    stats = {}
    for col in ["Revenue (M USD)", "Employees", "Revenue_Per_Employee",
                "Total Debt (M)", "Net_Debt"]:
        if col in train_df.columns:
            stats[col] = {
                "mean":   train_df.groupby("Sector")[col].mean(),
                "std":    train_df.groupby("Sector")[col].std().fillna(1),
                "median": train_df.groupby("Sector")[col].median(),
            }
    return stats


def apply_sector_features(df, stats):
    """Applique les stats du train sur n'importe quel df via .map() uniquement."""
    df = df.copy()

    # Z-scores
    for col in ["Revenue (M USD)", "Employees", "Revenue_Per_Employee"]:
        if col in df.columns and col in stats:
            mean = df["Sector"].map(stats[col]["mean"])
            std  = df["Sector"].map(stats[col]["std"]).fillna(1)
            col_name = col.replace(" (M USD)", "").replace(" ", "_") + "_Sector_Z"
            df[col_name] = (df[col] - mean) / (std + 1e-9)

    # Debt_Sector_Z
    if "Total Debt (M)" in df.columns and "Total Debt (M)" in stats:
        mean = df["Sector"].map(stats["Total Debt (M)"]["mean"])
        std  = df["Sector"].map(stats["Total Debt (M)"]["std"]).fillna(1)
        df["Debt_Sector_Z"] = (df["Total Debt (M)"] - mean) / (std + 1e-9)

    # Revenue_Volatility
    if "Revenue (M USD)" in df.columns and "Revenue (M USD)" in stats:
        median = df["Sector"].map(stats["Revenue (M USD)"]["median"])
        df["Revenue_Volatility"] = df["Revenue (M USD)"] / (median + 1e-9)

    # Sector_Risk
    if "Net_Debt" in df.columns and "Net_Debt" in stats:
        df["Sector_Risk"] = df["Sector"].map(stats["Net_Debt"]["mean"])

    return df



# PIPELINE

def run_feature_engineering():
    print("=" * 50)
    print("FEATURE ENGINEERING PIPELINE")
    print("=" * 50)

    df = load_cleaned()
    df = clip_target(df)

    df = add_region(df)
    df = add_industry_group(df)
    df = fix_sector(df)

    df = add_age_features(df)
    df = add_safe_features(df)
    df = add_financial_features(df)
    df = create_missing_features(df)
    df = add_interaction_features(df)

   
    #stats = fit_sector_stats(df)
    #df = apply_sector_features(df, stats)

    out = os.path.join(DATA_PROCESSED, "featured2.csv")
    df.to_csv(out, index=False, encoding="utf-8")

    print(f"\n[SAVED] {out}")
    print(f"Shape  : {df.shape}")

    return df


if __name__ == "__main__":
    run_feature_engineering()