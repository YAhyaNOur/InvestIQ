import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def load_crypto_data(ticker: str = "BTC-USD", jours: int = 1095) -> pd.DataFrame:
    """
    Télécharge les données historiques depuis Yahoo Finance.
    
    Args:
        ticker : symbole Yahoo Finance ex: "BTC-USD", "ETH-USD"
        jours  : nombre de jours d'historique (365 | 730 | 1095)
    
    Returns:
        DataFrame avec colonnes : date, prix
    """
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=jours)

    print(f" Téléchargement {ticker} depuis Yahoo Finance...")

    try:
        raw = yf.download(
            ticker,
            start    = start_date.strftime("%Y-%m-%d"),
            end      = end_date.strftime("%Y-%m-%d"),
            progress = False,
            auto_adjust = True
        )
    except Exception as e:
        raise ValueError(f"Erreur téléchargement {ticker} : {e}")

    if raw.empty:
        raise ValueError(f"Aucune donnée trouvée pour {ticker}")

    #  le prix de clôture
    df = raw[["Close"]].copy()
    df.columns = ["prix"]
    df = df.reset_index().rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"])

    # Supprimer les NA
    df = df.dropna(subset=["prix"]).reset_index(drop=True)

    print(f" {len(df)} jours chargés "
          f"({df['date'].min().strftime('%d/%m/%Y')} → "
          f"{df['date'].max().strftime('%d/%m/%Y')})")
    print(f"   Prix actuel {ticker} : ${df['prix'].iloc[-1]:,.2f}")

    return df