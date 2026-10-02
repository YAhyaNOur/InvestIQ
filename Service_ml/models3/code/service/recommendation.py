"""import joblib
import pandas as pd
import numpy as np
from pathlib import Path

from service.scoring import business_score


# ─────────────────────────────
# LOAD MODEL
# ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model_recommendation.joblib"

package = joblib.load(MODEL_PATH)

model = package["model"]
FEATURES = package["features"]
CAT_FEATURES = package["cat_features"]
ALLOWED_VALUES = package.get("allowed_values", {})


# ─────────────────────────────
# CLEAN INPUT
# ─────────────────────────────
def clean_input(df):
    df = df.copy()

    for col in CAT_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str)

            if col in ALLOWED_VALUES:
                df[col] = df[col].apply(
                    lambda x: x if x in ALLOWED_VALUES[col] else "Unknown"
                )

    return df


# ─────────────────────────────
# USER–ITEM SCORE
# ─────────────────────────────
def user_item_score(row, profile):

    score = 0

    # sector match
    if row.get("Sector") == profile.get("sector"):
        score += 0.4

    # risk match
    beta = row.get("Beta", 0.5)
    if profile.get("risk") == "low":
        score += (1 - beta)
    elif profile.get("risk") == "high":
        score += beta
    else:
        score += 0.5

    # budget signal (simple)
    score += 0.2

    return min(score, 1.0)


# ─────────────────────────────
# USER–USER SCORE
# ─────────────────────────────
def user_user_score(similar_df, company_id):

    if similar_df is None or similar_df.empty:
        return 0.0

    if "company_id" not in similar_df.columns:
        return 0.0

    return (similar_df["company_id"] == company_id).mean()"""



"""def hybrid_recommend_final(df_companies, profile, similar_df, user_id):

    df = df_companies.copy()

    # ───────── USER–ITEM
    df["user_item_score"] = df.apply(
        lambda r: user_item_score(r, profile),
        axis=1
    )

    # ───────── BUSINESS SCORE 
    df["business_score"] = df.apply(
        lambda r: business_score(r, profile), 
        axis=1
    )

    #  normalization
    min_b = df["business_score"].min()
    max_b = df["business_score"].max()

    if max_b - min_b == 0:
        df["business_score"] = 0.5
    else:
        df["business_score"] = (df["business_score"] - min_b) / (max_b - min_b)

    # ───────── USER–USER
    df["user_user_score"] = df.apply(
        lambda r: user_user_score(similar_df, r["company_id"]),
        axis=1
    )

    # ───────── ML SCORE
    df_clean = clean_input(df)
    df["ml_score"] = model.predict_proba(df_clean[FEATURES])[:, 1]

    # ───────── FINAL SCORE
    df["final_score"] = (
        0.45 * df["user_item_score"] +
        0.25 * df["business_score"] +
        0.20 * df["user_user_score"] +
        0.10 * df["ml_score"]
    ).clip(0, 1)

    # ───────── DECISION
    df["decision"] = df["final_score"].apply(lambda x:
        "STRONG BUY" if x > 0.75 else
        "BUY" if x > 0.55 else
        "HOLD" if x > 0.35 else "AVOID"
    )

    return df.sort_values("final_score", ascending=False)"""


"""def hybrid_recommend_final(df, profile, similar_df, model, features):

    df = df.copy()

    # ───── USER-ITEM
    df["user_item_score"] = df.apply(
        lambda r: user_item_score(r, profile), axis=1
    )

    # ───── BUSINESS
    df["business_score"] = df.apply(
        lambda r: business_score(r, profile), axis=1
    )

    # normalize
    df["business_score"] = (
        df["business_score"] - df["business_score"].min()
    ) / (df["business_score"].max() - df["business_score"].min() + 1e-9)

    # ───── USER-USER
    df["user_user_score"] = df.apply(
        lambda r: user_user_score(similar_df, r["company_id"]),
        axis=1
    )

    # ───── ML
    df["ml_score"] = get_ml_score(model, df, features)

    # ───── FINAL
    df["final_score"] = (
        0.4 * df["ml_score"] +
        0.3 * df["business_score"] +
        0.2 * df["user_item_score"] +
        0.1 * df["user_user_score"]
    )

    df["decision"] = df["final_score"].apply(lambda x:
        "STRONG BUY" if x > 0.75 else
        "BUY" if x > 0.55 else
        "HOLD" if x > 0.35 else "AVOID"
    )

    return df.sort_values("final_score", ascending=False)"""

"""import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from service.scoring import business_score

# ── Load Model ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model_recommendation.joblib"

package = joblib.load(MODEL_PATH)
model = package["model"]
FEATURES = package["features"]
CAT_FEATURES = package["cat_features"]
ALLOWED_VALUES = package.get("allowed_values", {})


def clean_input(df):
    df = df.copy()
    for col in CAT_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str)
            if col in ALLOWED_VALUES:
                df[col] = df[col].apply(
                    lambda x: x if x in ALLOWED_VALUES[col] else "Unknown"
                )
        else:
            df[col] = "Unknown"
    return df


def user_item_score(row, profile):
    score = 0.0
    company_sector = str(row.get("Sector", "")).strip()
    profile_sector = str(profile.get("sector", "")).strip()
    if company_sector and profile_sector and company_sector == profile_sector:
        score += 0.5

    company_region = str(row.get("Region_std", "")).strip()
    profile_region = str(profile.get("region", "")).strip()
    if company_region and profile_region and company_region == profile_region:
        score += 0.5

    return min(score, 1.0)


def user_user_score(similar_df, company_sector, company_region):
    if similar_df is None or similar_df.empty:
        return 0.0
    if "sim_score" not in similar_df.columns:
        return 0.0

    sector_match = similar_df.get("preferred_sector", pd.Series(dtype=str)) == company_sector
    region_match = similar_df.get("region_std", pd.Series(dtype=str)) == company_region

    if sector_match.any():
        return float(similar_df[sector_match]["sim_score"].mean()) * 0.8
    if region_match.any():
        return float(similar_df[region_match]["sim_score"].mean()) * 0.4
    return 0.0


def hybrid_recommend_final(df_companies, profile, similar_df, user_id):
    df = df_companies.copy()

    # 1. USER-ITEM — sector + region
    df["user_item_score"] = df.apply(
        lambda r: user_item_score(r, profile), axis=1
    )

    # 2. BUSINESS SCORE
    df["business_score"] = df.apply(
        lambda r: business_score(r, profile), axis=1
    )
    min_b = df["business_score"].min()
    max_b = df["business_score"].max()
    if max_b - min_b == 0:
        df["business_score"] = 0.5
    else:
        df["business_score"] = (df["business_score"] - min_b) / (max_b - min_b)

    # 3. USER-USER
    df["user_user_score"] = df.apply(
        lambda r: user_user_score(
            similar_df,
            str(r.get("Sector", "")),
            str(r.get("Region_std", ""))
        ),
        axis=1
    )

    # 4. ML SCORE
    try:
        df_clean = clean_input(df)
        # Ajouter colonnes manquantes avec 0
        for col in FEATURES:
            if col not in df_clean.columns:
                df_clean[col] = 0 if col not in CAT_FEATURES else "Unknown"
        df["ml_score"] = model.predict_proba(df_clean[FEATURES])[:, 1]
    except Exception as e:
        print(f"ML score error: {e}")
        df["ml_score"] = 0.5

    # 5. FINAL SCORE
    df["final_score"] = (
        0.40 * df["user_item_score"] +
        0.20 * df["business_score"] +
        0.20 * df["user_user_score"] +
        0.20 * df["ml_score"]
    ).clip(0, 1)
    

    # 6. DECISION
    df["decision"] = df["final_score"].apply(lambda x:
        "STRONG BUY" if x > 0.75 else
        "BUY"        if x > 0.55 else
        "HOLD"       if x > 0.35 else
        "AVOID"
    )

    return df.sort_values("final_score", ascending=False)"""
"""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from service.scoring import business_score

# ─────────────────────────────
# LOAD MODEL
# ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model_recommendation.joblib"

package = joblib.load(MODEL_PATH)

model = package["model"]
FEATURES = package["features"]
CAT_FEATURES = package["cat_features"]
ALLOWED_VALUES = package.get("allowed_values", {})


# ─────────────────────────────
# HELPER — nettoyer un float
# ─────────────────────────────
def safe_float(val, default=0.0):
    
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return default
        return v
    except Exception:
        return default


# ─────────────────────────────
# CLEAN INPUT
# ─────────────────────────────
def clean_input(df):
    df = df.copy()

    for col in CAT_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].apply(
                lambda x: x if x in ALLOWED_VALUES.get(col, []) else "Unknown"
            )
        else:
            df[col] = "Unknown"

    return df


# ─────────────────────────────
# USER-ITEM SCORE
# ─────────────────────────────
def user_item_score(row, profile):
    score = 0.0

    if str(row.get("Sector", "")).strip() == str(profile.get("sector", "")).strip():
        score += 0.5

    if str(row.get("Region_std", "")).strip() == str(profile.get("region", "")).strip():
        score += 0.5

    return min(score, 1.0)


# ─────────────────────────────
# USER-USER SCORE
# ─────────────────────────────
def user_user_score(similar_df, sector, region):
    if similar_df is None or similar_df.empty:
        return 0.0

    if "sim_score" not in similar_df.columns:
        return 0.0

    try:
        mask = (
            (similar_df.get("preferred_sector") == sector) |
            (similar_df.get("region_std") == region)
        )
        if mask.any():
            val = float(similar_df[mask]["sim_score"].mean()) * 0.5
            return safe_float(val, 0.0)
    except Exception:
        pass

    return 0.0


# ─────────────────────────────
# HYBRID ENGINE
# ─────────────────────────────
def hybrid_recommend_final(df_companies, profile, similar_df, user_id):

    df = df_companies.copy()

    # ── Reset index pour éviter "duplicate labels" ──────────────────────────
    df = df.reset_index(drop=True)
    if similar_df is not None and not similar_df.empty:
        similar_df = similar_df.reset_index(drop=True)

    # ───── USER-ITEM
    df["user_item_score"] = df.apply(
        lambda r: safe_float(user_item_score(r, profile)),
        axis=1
    )

    # ───── BUSINESS SCORE
    df["business_score"] = df.apply(
        lambda r: safe_float(business_score(r, profile)),
        axis=1
    )
    # Normalisation percentile — fillna 0.5 si tous identiques
    df["business_score"] = df["business_score"].rank(pct=True).fillna(0.5)

    # ───── USER-USER
    df["user_user_score"] = df.apply(
        lambda r: safe_float(user_user_score(
            similar_df,
            str(r.get("Sector", "")),
            str(r.get("Region_std", ""))
        )),
        axis=1
    )

    # ───── ML SCORE
    try:
        df_clean = clean_input(df)

        for col in FEATURES:
            if col not in df_clean.columns:
                df_clean[col] = "Unknown" if col in CAT_FEATURES else 0

        raw_proba = model.predict_proba(df_clean[FEATURES])[:, 1]

        # Remplacer NaN/inf avant rank
        raw_proba = np.where(np.isfinite(raw_proba), raw_proba, 0.5)

        df["ml_score"] = pd.Series(raw_proba, index=df.index).rank(pct=True).fillna(0.5)

    except Exception as e:
        print(f"ML score error: {e}")
        df["ml_score"] = 0.5

    # ───── FINAL SCORE
    df["final_score"] = (
        0.45 * df["ml_score"] +
        0.25 * df["business_score"] +
        0.20 * df["user_item_score"] +
        0.10 * df["user_user_score"]
    )

    # ── Nettoyage final — plus aucun NaN/inf ne passe ──────────────────────
    score_cols = ["ml_score", "business_score", "user_item_score",
                  "user_user_score", "final_score"]
    for col in score_cols:
        df[col] = df[col].apply(lambda x: safe_float(x, 0.0))

    df["final_score"] = df["final_score"].clip(0, 1)

    # ───── DECISION
    df["decision"] = df["final_score"].apply(
        lambda x:
            "STRONG BUY" if x > 0.75 else
            "BUY"        if x > 0.55 else
            "HOLD"       if x > 0.35 else
            "AVOID"
    )

    return df.sort_values("final_score", ascending=False)"""


import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from service.scoring import business_score

# ─────────────────────────────
# LOAD MODEL
# ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model_recommendation.joblib"

package = joblib.load(MODEL_PATH)

model = package["model"]
FEATURES = package["features"]
CAT_FEATURES = package["cat_features"]
ALLOWED_VALUES = package.get("allowed_values", {})


# ─────────────────────────────
# HELPER — nettoyer un float
# ─────────────────────────────
def safe_float(val, default=0.0):
    """Remplace NaN / inf / -inf par default."""
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return default
        return v
    except Exception:
        return default


# ─────────────────────────────
# CLEAN INPUT
# ─────────────────────────────
def clean_input(df):
    df = df.copy()

    for col in CAT_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].apply(
                lambda x: x if x in ALLOWED_VALUES.get(col, []) else "Unknown"
            )
        else:
            df[col] = "Unknown"

    return df


# ─────────────────────────────
# USER-ITEM SCORE
# ─────────────────────────────
def user_item_score(row, profile):
    score = 0.0

    if str(row.get("Sector", "")).strip() == str(profile.get("sector", "")).strip():
        score += 0.5

    if str(row.get("Region_std", "")).strip() == str(profile.get("region", "")).strip():
        score += 0.5

    return min(score, 1.0)


# ─────────────────────────────
# USER-USER SCORE
# ─────────────────────────────
def user_user_score(similar_df, sector, region):
    if similar_df is None or similar_df.empty:
        return 0.0

    if "sim_score" not in similar_df.columns:
        return 0.0

    try:
        mask = (
            (similar_df.get("preferred_sector") == sector) |
            (similar_df.get("region_std") == region)
        )
        if mask.any():
            val = float(similar_df[mask]["sim_score"].mean()) * 0.5
            return safe_float(val, 0.0)
    except Exception:
        pass

    return 0.0


# ─────────────────────────────
# HYBRID ENGINE
# ─────────────────────────────
def hybrid_recommend_final(df_companies, profile, similar_df, user_id):

    df = df_companies.copy()

    # ── Reset index pour éviter "duplicate labels" ──────────────────────────
    df = df.reset_index(drop=True)
    if similar_df is not None and not similar_df.empty:
        similar_df = similar_df.reset_index(drop=True)

    # ───── USER-ITEM
    df["user_item_score"] = df.apply(
        lambda r: safe_float(user_item_score(r, profile)),
        axis=1
    )

    # ───── BUSINESS SCORE
    df["business_score"] = df.apply(
        lambda r: safe_float(business_score(r, profile)),
        axis=1
    )
    # Normalisation percentile — fillna 0.5 si tous identiques
    df["business_score"] = df["business_score"].rank(pct=True).fillna(0.5)

    # ───── USER-USER
    df["user_user_score"] = df.apply(
        lambda r: safe_float(user_user_score(
            similar_df,
            str(r.get("Sector", "")),
            str(r.get("Region_std", ""))
        )),
        axis=1
    )

    # ───── ML SCORE
    try:
        df_clean = clean_input(df)

        for col in FEATURES:
            if col not in df_clean.columns:
                df_clean[col] = "Unknown" if col in CAT_FEATURES else 0

        raw_proba = model.predict_proba(df_clean[FEATURES])[:, 1]

        # Remplacer NaN/inf avant rank
        raw_proba = np.where(np.isfinite(raw_proba), raw_proba, 0.5)

        df["ml_score"] = pd.Series(raw_proba, index=df.index).rank(pct=True).fillna(0.5)

    except Exception as e:
        print(f"ML score error: {e}")
        df["ml_score"] = 0.5

    # ───── FINAL SCORE
    df["final_score"] = (
        0.45 * df["ml_score"] +
        0.25 * df["business_score"] +
        0.20 * df["user_item_score"] +
        0.10 * df["user_user_score"]
    )

    # ── Nettoyage final — plus aucun NaN/inf ne passe ──────────────────────
    score_cols = ["ml_score", "business_score", "user_item_score",
                  "user_user_score", "final_score"]
    for col in score_cols:
        df[col] = df[col].apply(lambda x: safe_float(x, 0.0))

    df["final_score"] = df["final_score"].clip(0, 1)

    # ───── DECISION
    df["decision"] = df["final_score"].apply(
        lambda x:
            "STRONG BUY" if x > 0.75 else
            "BUY"        if x > 0.55 else
            "HOLD"       if x > 0.35 else
            "AVOID"
    )

    return df.sort_values("final_score", ascending=False)