import numpy as np


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

def compute_all_features(data, sector_stats):

    feat = {}

    # ======================
    # RAW INPUT
    # ======================
    sector = data.get("sector", "Other")
    region = str(data.get("region", "")).lower().strip()
    industry = str(data.get("industry", "")).strip()

    revenue = float(data.get("revenue", 0))
    employees = float(data.get("employees", 0))
    total_debt = float(data.get("total_debt", 0))
    total_cash = float(data.get("total_cash", 0))
    beta = float(data.get("beta", 0))
    current_ratio = float(data.get("current_ratio", 0))
    debt_to_equity = float(data.get("debt_to_equity", 0))
    revenue_growth = float(data.get("revenue_growth", 0))

    # ======================
    # DERIVED FEATURES
    # ======================
    net_debt = total_debt - total_cash
    revenue_per_employee = revenue / (employees + 1e-9)

    # ======================
    # REGION / INDUSTRY
    # ======================
    region_std = REGION_MAP.get(region, "Other")
    industry_group = INDUSTRY_TO_GROUP.get(industry, "Other")

    # ======================
    # Z-SCORE
    # ======================
    if sector in sector_stats:
        stats = sector_stats[sector]["employees"]
        employees_z = (employees - stats["mean"]) / (stats["std"] + 1e-9)
    else:
        employees_z = 0

    # ======================
    # FINAL FEATURES (ALL)
    # ======================
    feat = {
        "Sector": sector,
        "Region_std": region_std,

        # MODEL 1
        "Beta": beta,
        "Net_Debt": net_debt,
        "Revenue Growth": revenue_growth,

        # MODEL 2
        "Debt To Equity": debt_to_equity,
        "Total Debt (M)": total_debt,
        "Current Ratio": current_ratio,
        "Employees_Sector_Z": employees_z
    }

    return feat

FEATURES_MODEL_1 = [
    "Sector",
    "Region_std",
    "Beta",
    "Net_Debt",
    "Revenue Growth"
]


FEATURES_MODEL_2 = [
    "Sector",
    "Region_std",
    "Debt To Equity",
    "Total Debt (M)",
    "Current Ratio",
    "Employees_Sector_Z"
]




