# Reproducing Drishti-AI Results

All results in the paper are reproducible from this repository. Every
training script sets Python/NumPy/PyTorch seeds; the reported numbers use
the seeds below.

## 1. Environment

- Python 3.11, Windows 11, NVIDIA RTX 5060 (Blackwell / sm_120).
- Create a virtualenv and install pinned dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# PyTorch must come from the CUDA 12.8 index for Blackwell GPUs:
pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

CPU-only reproduction works too (drop the CUDA index); only training is slower.

## 2. Module 1 — Defect detection (seeds 42, 1, 2)

```powershell
cd module1_cv_defect
# proper train/val/test split, model selected on validation:
python src\train_proper.py --seed 42
python src\train_proper.py --seed 1
python src\train_proper.py --seed 2
python src\aggregate_results.py                 # -> reports/module1_results.md
# baselines on the same split:
python src\train_baseline.py --arch resnet50 --seed 42
python src\train_baseline.py --arch simplecnn --seed 42 --epochs 20
python src\aggregate_results.py                 # now includes baselines
# explainability + latency + ONNX export:
python src\gradcam.py --n 4 --out reports\gradcam.png
python src\benchmark_latency.py
python src\infer.py export --checkpoint models\casting_mobilenetv2_proper.pt ^
       --out models\casting_mobilenetv2_proper.onnx
```

## 3. Module 3 — Predictive maintenance

```powershell
cd module3_predictive_maintenance
python src\train.py                 # by-tool split (test tools 2,10,101,103)
python src\evaluate.py              # per-tool held-out metrics
python src\baselines_pdm.py         # constant-mean + linear baselines
```

## 4. Module 4 — Demand forecasting

```powershell
cd module4_demand_forecasting
python src\feature_extraction.py --data "data\Historical Product Demand.csv" ^
       --out data\weekly_category_features.csv
python src\train.py                 # point + P10/P90 quantile models + 3-fold CV
python src\evaluate.py              # per-category WAPE
python src\baselines_forecast.py    # naive, seasonal-naive, Prophet
```

## Notes
- Seeds fix data splits and model init, but exact CUDA kernel determinism
  is not enforced, so metrics may vary at the 3rd–4th decimal across runs.
- Datasets are NOT redistributed here; download links are in the paper /
  drishti-ai-project-spec.md and files go in each module's `data/` folder.
