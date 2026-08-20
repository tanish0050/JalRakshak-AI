import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

n = 5000

data = {
    "rainfall": np.random.uniform(0, 300, n),
    "temperature": np.random.uniform(15, 45, n),
    "humidity": np.random.uniform(30, 100, n),
    "water_ph": np.random.uniform(4, 10, n),
    "turbidity": np.random.uniform(0, 100, n),
    "contamination_level": np.random.uniform(0, 100, n),
    "diarrhea_cases": np.random.randint(0, 200, n),
    "population_density": np.random.uniform(100, 5000, n),
    "flood_risk": np.random.uniform(0, 100, n)
}

df = pd.DataFrame(data)

risk_score = (
    df["rainfall"] * 0.15 +
    df["humidity"] * 0.20 +
    df["turbidity"] * 0.25 +
    df["contamination_level"] * 0.30 +
    df["diarrhea_cases"] * 0.40 +
    df["flood_risk"] * 0.20
)

df["outbreak_risk"] = risk_score / risk_score.max()

df["risk_level"] = pd.cut(
    df["outbreak_risk"],
    bins=[0, 0.33, 0.66, 1.0],
    labels=["Low", "Medium", "High"],
    include_lowest=True
)

# Project root = parent of src folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Create data folder
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Save CSV
OUTPUT_FILE = DATA_DIR / "jalrakshak_dataset.csv"
df.to_csv(OUTPUT_FILE, index=False)

print("\nSUCCESS! Dataset created.")
print("Saved at:", OUTPUT_FILE)
print("Total records:", len(df))
print("\nRisk distribution:")
print(df["risk_level"].value_counts())