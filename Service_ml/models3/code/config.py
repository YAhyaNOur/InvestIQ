import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_RAW = os.path.join(BASE_DIR, "data", "raw", "dataset_final_merged.csv")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


TARGET_GROWTH = "Growth"
TARGET_RISK = "Risk"

CATEGORICAL_COLS = ["Industry_Group", "Sector", "Region_std"]

NUMERICAL_COLS = [
    "Year Founded", "Employees",
    "Revenue (M USD)", "Revenue Growth",
    "Profit Margins", "Gross Margins", "Operating Margins", "EBITDA Margins",
    "Total Cash (M)", "Total Debt (M)",
    "Debt To Equity", "Current Ratio", "Quick Ratio",
    "PE Ratio", "PB Ratio", "PS Ratio",
    "EV/EBITDA", "EV/Revenue",
    "ROE", "ROA", "Beta",
]

COLS_TO_DROP = ["Earnings Growth",  "Startup Name", "Exit Status"]

COLS_TO_FLAG = ["PE Ratio", "Debt To Equity"]

OUTLIER_QUANTILE_LOW = 0.01
OUTLIER_QUANTILE_HIGH = 0.99

TEST_SIZE = 0.2
RANDOM_STATE = 42

GROWTH_BINS = [-float("inf"), -0.029, 0.142, float("inf")]
GROWTH_LABELS = ["Faible", "Moyenne", "Forte"]