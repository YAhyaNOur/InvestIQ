from fastapi import APIRouter
from fastapi.responses import JSONResponse
from service.db import get_engine
from service.recommendation import hybrid_recommend_final
from service.investor_profile import build_profile
from service.similar_user import get_similar_investors
import pandas as pd
import numpy as np
import json


router = APIRouter()
engine = get_engine()

def read_sql(query, params=None):
    with engine.connect() as connection:
        return pd.read_sql(
            query,
            connection,
            params=params
        )


class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return None if (np.isnan(obj) or np.isinf(obj)) else float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

    def encode(self, obj):
        return super().encode(self._clean(obj))

    def _clean(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: self._clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._clean(i) for i in obj]
        return obj


def safe_json_response(data: dict) -> JSONResponse:
    content = json.loads(json.dumps(data, cls=SafeEncoder))
    return JSONResponse(content=content)


@router.get("/investors")
def get_investors():
    df = pd.read_sql("SELECT * FROM investors")
    return safe_json_response({"investors": df.to_dict(orient="records")})


@router.get("/companies")
def get_companies():
    df = pd.read_sql("SELECT * FROM companies")
    return safe_json_response({"companies": df.to_dict(orient="records")})


@router.get("/recommend/{user_id}")
def recommend(user_id: int):

    # 1. Companies
    df_companies_raw = read_sql("SELECT * FROM companies")
    df_companies = df_companies_raw.rename(columns={
        "sector":               "Sector",
        "industry_group":       "Industry_Group",
        "region_std":           "Region_std",
        "beta":                 "Beta",
        "ebitda_margins":       "EBITDA Margins",
        "revenue_per_employee": "Revenue_per_Employee",
        "net_debt":             "Net_Debt",
    })

    # 2. Investor
    query = """
        SELECT u.full_name, u.email, i.*
        FROM users u
        JOIN investors i ON u.user_id = i.user_id
        WHERE i.user_id = %(user_id)s
    """
    df_inv = read_sql(
        query,
        params={"user_id": user_id}
    )
    if df_inv.empty:
        return JSONResponse(content={"error": "Investor not found"})

    investor_row = df_inv.iloc[0]

    # 3. Profile
    profile = build_profile(investor_row)
    print(f"[DEBUG] Profile: {profile}")

    # 4. Similar investors
    try:
        df_inv = read_sql(query, params={"user_id": user_id})
        df_investors = read_sql("SELECT * FROM investors")
        df_investors = df_investors.reset_index(drop=True)
        similar_df = get_similar_investors(
                current_investor_id=user_id,
                df=df_investors,
                top_n=5
            )
    except Exception as e:
        print(f"[DEBUG] Similar investors error: {e}")
        similar_df = pd.DataFrame()

    # 5. Recommendation
    result = hybrid_recommend_final(
        df_companies=df_companies,
        profile=profile,
        similar_df=similar_df,
        user_id=user_id
    )

    # 6. Ajouter name + email du owner de la startup
    if "company_id" in result.columns:
        company_owners = read_sql("""
            SELECT c.company_id, c.name, u.email as contact_email
            FROM companies c
            JOIN users u ON c.user_id = u.user_id
        """)

        print("=== company_owners ===")
        print(company_owners.head())
        print("=== result company_id sample ===")
        print(result["company_id"].head())

        company_owners = company_owners.set_index("company_id")

        result["name"] = result["company_id"].map(company_owners["name"])
        result["contact_email"] = result["company_id"].map(company_owners["contact_email"])

        print("=== contact_email après map ===")
        print(result["contact_email"].head())

    # 7. Retour sécurisé
    return safe_json_response({
        "user": str(investor_row.get("full_name") or "Investor"),
        "recommendations": result.to_dict(orient="records")
    })