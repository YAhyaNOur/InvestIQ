"""import numpy as np

def get_ml_score(model, df):

    df = df.copy()

   
    features = model.feature_names_

    features = [f for f in features if f in df.columns]

    X = df[features]

    # score proba
    df["ml_score"] = model.predict_proba(X)[:, 1]

    return df"""

import numpy as np

def get_ml_score(model, df, features):

    df = df.copy()

    # safe feature selection 
    X = df.reindex(columns=features, fill_value=0)

    # prediction probability
    proba = model.predict_proba(X)[:, 1]

    return proba

