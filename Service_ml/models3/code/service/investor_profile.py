def build_profile(row):
  
    if hasattr(row, 'to_dict'):
        row = row.to_dict()

    sector = (row.get("preferred_sector") or "Other").strip()
    region = (row.get("region_std") or "North_America").strip()
    risk   = (row.get("risk") or "medium").strip()

    return {
        "sector": sector,
        "region": region,
        "risk": risk,
        "min_return": float(row.get("min_return") or 0),
        "max_risk":   float(row.get("max_risk")   or 1),
        "budget":     float(row.get("budget")      or 0),
        "portfolio_value":  float(row.get("portfolio_value")  or 0),
        "active_companies": int(row.get("active_companies") or 0),
    }