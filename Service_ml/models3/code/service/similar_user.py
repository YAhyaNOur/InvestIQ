import pandas as pd
import numpy as np

"""def get_similar_investors(current_investor_id, df, top_n=5):
  
    if df.empty or "investor_id" not in df.columns:
        return pd.DataFrame()

    df = df.copy()

   
    df["preferred_sector"] = df.get("preferred_sector", pd.Series(dtype=str)).fillna("Other")
    df["region_std"] = df.get("region_std", pd.Series(dtype=str)).fillna("Other")

    # Current investor
    current = df[df["investor_id"] == current_investor_id]
    if current.empty:
        return pd.DataFrame()

    current_sector = current.iloc[0].get("preferred_sector", "Other")
    current_region = current.iloc[0].get("region_std", "Other")

    # Autres investors
    others = df[df["investor_id"] != current_investor_id].copy()
    if others.empty:
        return pd.DataFrame()

   
    def similarity(row):
        score = 0.0
        if row.get("preferred_sector") == current_sector:
            score += 0.6
        if row.get("region_std") == current_region:
            score += 0.4
        return score

    others["sim_score"] = others.apply(similarity, axis=1)

    return others.sort_values("sim_score", ascending=False).head(top_n)"""


import pandas as pd
import numpy as np


def get_similar_investors(current_investor_id, df, top_n=5):
    if df is None or df.empty:
        return pd.DataFrame()

    if "investor_id" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["preferred_sector"] = df.get("preferred_sector", pd.Series(dtype=str)).fillna("Other")
    df["region_std"] = df.get("region_std", pd.Series(dtype=str)).fillna("Other")

    current = df[df["investor_id"] == current_investor_id]
    if current.empty:
        return pd.DataFrame()

    current_sector = str(current.iloc[0].get("preferred_sector", "Other"))
    current_region = str(current.iloc[0].get("region_std", "Other"))

    others = df[df["investor_id"] != current_investor_id].copy()
    if others.empty:
        return pd.DataFrame()

    def similarity(row):
        score = 0.0
        if str(row.get("preferred_sector", "")) == current_sector:
            score += 0.6
        if str(row.get("region_std", "")) == current_region:
            score += 0.4
        return score

    others["sim_score"] = others.apply(similarity, axis=1)
    return others.sort_values("sim_score", ascending=False).head(top_n)