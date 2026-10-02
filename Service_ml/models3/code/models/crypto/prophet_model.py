
import numpy as np
import pandas as pd
from datetime import timedelta
import warnings
warnings.filterwarnings("ignore")
def run_prophet(df: pd.DataFrame, horizon: int = 7, seuil: float = 0.01):

    from prophet import Prophet

    df_prophet = df[["date", "prix"]].copy()
    df_prophet.columns = ["ds", "y"]
    df_prophet["ds"] = pd.to_datetime(df_prophet["ds"])

    model = Prophet()
    model.fit(df_prophet)

    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)

    fc_future = forecast.tail(horizon)

    prix_actuel = float(df["prix"].iloc[-1]) if len(df) > 0 else 0
    prix_predit = float(fc_future["yhat"].iloc[-1]) if len(fc_future) > 0 else 0

    variation = 0 if prix_actuel == 0 else round((prix_predit / prix_actuel - 1) * 100, 2)

    trend_series = forecast["trend"].fillna(0)
    tendance_val = float(trend_series.iloc[-1] - trend_series.iloc[-horizon-1])

    signal = "BUY" if variation > seuil * 100 else "SELL"

    return {
        "model_name": "Prophet",
        "signal": signal,
        "prix_actuel": prix_actuel,
        "prix_predit": prix_predit,
        "variation": variation,
        "tendance": "haussière" if tendance_val > 0 else "baissière",
        "confiance": 70,
        "fc_future": fc_future.to_dict(orient="records")
    }