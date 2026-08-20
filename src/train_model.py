import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "jalrakshak_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)
FEATURES = ["rainfall", "temperature", "humidity", "water_ph", "turbidity", "contamination_level", "diarrhea_cases", "population_density", "flood_risk"]

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}. Run src/generate_data.py first.")

dataset = pd.read_csv(DATA_FILE)
X, y = dataset[FEATURES], dataset["risk_level"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

joblib.dump(model, MODEL_DIR / "outbreak_model.pkl")
joblib.dump(FEATURES, MODEL_DIR / "features.pkl")

metrics = {
    "accuracy": round(float(accuracy), 4),
    "classes": model.classes_.tolist(),
    "confusion_matrix": confusion_matrix(y_test, predictions, labels=model.classes_).tolist(),
    "classification_report": classification_report(y_test, predictions, output_dict=True),
    "trained_at": pd.Timestamp.now().isoformat(),
}
(MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
pd.DataFrame({"feature": FEATURES, "importance": model.feature_importances_}).sort_values("importance", ascending=False).to_csv(MODEL_DIR / "feature_importance.csv", index=False)

print("MODEL TRAINED SUCCESSFULLY")
print(f"Accuracy: {accuracy:.2%}")
print(f"Model: {MODEL_DIR / 'outbreak_model.pkl'}")
print(f"Metrics: {MODEL_DIR / 'metrics.json'}")
