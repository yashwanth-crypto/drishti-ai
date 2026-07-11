# Module 1 — Consolidated Results

_Generated 2026-07-09 20:44_

All models trained on the SAME proper train/val/test split (model selected on validation, test evaluated once).

| Model | Seeds | Test Acc (mean ± std) | Range | Macro-F1 (mean ± std) |
|---|---|---|---|---|
| MobileNetV2 (proper split) | 3 (1,2,42) | 99.39% ± 0.24 | 99.16–99.72% | 99.35% ± 0.26 |
| ResNet-50 (baseline) | 3 (1,2,42) | 99.67% ± 0.07 | 99.58–99.72% | 99.65% ± 0.07 |
| SimpleCNN from scratch (baseline) | 3 (1,2,42) | 99.35% ± 0.07 | 99.30–99.44% | 99.30% ± 0.07 |

## Per-seed detail (MobileNetV2)

| Seed | Selected at | Val Acc | Test Acc | Confusion [[TN? layout]] |
|---|---|---|---|---|
| 1 | fine_tune epoch 4 | 99.70% | 99.72% | [[451, 2], [0, 262]] |
| 2 | fine_tune epoch 3 | 99.30% | 99.30% | [[450, 3], [2, 260]] |
| 42 | fine_tune epoch 2 | 99.30% | 99.16% | [[448, 5], [1, 261]] |

_Confusion matrix rows = true [def_front, ok_front], cols = predicted._