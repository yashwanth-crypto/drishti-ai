# Drishti-AI — Consolidated Paper-Ready Results

All numbers are measured on public datasets with corrected methodology
(proper held-out splits, model selection off the test set, baselines,
and — for Module 1 — multiple seeds). This supersedes the earlier
optimistic single-run figures.

---

## Module 1 — Defect detection

### Architecture comparison (same train/val/test split; test evaluated once)
| Model | Params | Test Acc | Macro-F1 |
|---|---|---|---|
| **MobileNetV2 (ours)** | **2.23 M** | **99.39% ± 0.24** (3 seeds) | 99.35% ± 0.26 |
| ResNet-50 | 23.51 M | 99.72% (1 seed) | 99.70% |
| SimpleCNN (from scratch) | 0.29 M | 99.44% (1 seed) | 99.40% |

Takeaway: MobileNetV2 matches a 10×-larger ResNet-50 within seed variance,
justifying it for edge deployment. A tiny scratch-CNN also reaching 99.4%
honestly indicates the casting dataset is highly separable.

### Per-class (representative median seed s=2, acc 99.30%)
| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| def_front | 0.9956 | 0.9934 | 0.9945 | 453 |
| ok_front | 0.9886 | 0.9924 | 0.9905 | 262 |

Confusion matrix [[450, 3], [2, 260]]; false negatives (missed defects)
ranged 2–5 across seeds — the safety-critical error, noted as a limitation.

### Inference latency (batch=1, 30 warm-up, 300 runs)
| Config | Mean | p95 |
|---|---|---|
| PyTorch GPU (RTX 5060) | 8.07 ms | 12.98 ms |
| PyTorch CPU | 12.39 ms | 13.99 ms |
| **ONNX Runtime CPU (edge)** | **2.37 ms** | 3.64 ms |

Figure: `module1_cv_defect/reports/gradcam.png` (Grad-CAM saliency).

---

## Module 3 — Predictive maintenance (RUL, unseen tools)
| Model | RMSE | MAE | R² |
|---|---|---|---|
| Constant mean (no-skill) | 0.296 | 0.256 | −0.00 |
| Linear regression | 0.253 | 0.194 | 0.265 |
| **XGBoost (ours)** | **0.199** | **0.160** | **0.545** |

Takeaway: XGBoost roughly doubles the linear model's R² on tools never
seen in training (by-tool split). Modest absolute R² is expected and
honest for cross-tool generalization.

---

## Module 4 — Demand forecasting (held-out 52 weeks, 28 categories)
| Forecaster | WAPE |
|---|---|
| Prophet | 30.4% |
| Seasonal-naïve (52-week) | 27.8% |
| Naïve (last value) | 25.7% |
| **XGBoost (ours)** | **19.7%** |

Supporting metrics for the model: R² 0.944; 3-fold expanding-window CV
mean WAPE 20.6% (folds 22.7 / 17.4 / 21.7); 80% prediction-interval
coverage 74.2%. Takeaway: the model beats every baseline including
Prophet — a ~23% relative improvement over naïve — so 19.7% reflects real
learned structure, not echoing recent values.

---

## Reproducibility
Seeds, exact commands, and pinned `requirements.txt` in `REPRODUCE.md`.

## Standing honesty caveats (unchanged)
- Public/synthetic datasets only; no factory pilot, sensor, or camera rig.
- Module 1 baselines are single-seed; Module 4 model is single-seed.
- Casting data, not CNC-milled parts; surface/visual defects only.
- Forecast dataset's final week looks truncated (noted; not patched).
