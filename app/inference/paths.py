"""Locates the existing module code and model artifacts, and puts each
module's `src/` on sys.path so its internal imports (`from features import ...`,
`from dataset import ...`) resolve exactly as they do when run as scripts."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

M1_DIR = REPO_ROOT / "module1_cv_defect"
M2_DIR = REPO_ROOT / "module2_vernacular_alert"
M3_DIR = REPO_ROOT / "module3_predictive_maintenance"
M4_DIR = REPO_ROOT / "module4_demand_forecasting"

M1_CHECKPOINT = M1_DIR / "models" / "casting_mobilenetv2_proper.pt"
M3_MODEL = M3_DIR / "models" / "tool_wear_xgb.json"
M3_METADATA = M3_DIR / "models" / "model_metadata.json"
# Feature-space profile of the training set, used to spot images the model was
# never trained to judge. Built by module1_cv_defect/src/ood.py.
M1_OOD_STATS = M1_DIR / "models" / "ood_stats.npz"

M4_MODEL = M4_DIR / "models" / "demand_forecast_xgb.json"
M4_METADATA = M4_DIR / "models" / "model_metadata.json"
# Recorded weekly series. Gitignored -- rebuild with feature_extraction.py.
M4_HISTORY = M4_DIR / "data" / "weekly_category_demand.csv"

for src in (M1_DIR / "src", M3_DIR / "src", M4_DIR / "src"):
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
