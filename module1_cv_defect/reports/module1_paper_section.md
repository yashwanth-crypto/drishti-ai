# Module 1 — Paper-Ready Results (corrected)

_All models trained on the SAME proper split: a stratified 15% validation
set carved from the training folder for model selection; the 715-image
test folder is evaluated exactly once. This corrects the original
pipeline, which selected the checkpoint on the test set (optimistic)._

## Table M1-A — Architecture comparison
| Model | Params | Pretrained | Test Acc | Macro-F1 |
|---|---|---|---|---|
| **MobileNetV2 (ours)** | **2.23 M** | ImageNet | **99.39% ± 0.24** (3 seeds) | 99.35% ± 0.26 |
| ResNet-50 | 23.51 M | ImageNet | 99.72% (1 seed) | 99.70% |
| SimpleCNN (from scratch) | 0.29 M | none | 99.44% (1 seed) | 99.40% |

**Reading of this table (honest):** ResNet-50 is ~10× the parameters for
a +0.33-point accuracy gain that is within seed-to-seed variance.
MobileNetV2 therefore gives essentially equivalent accuracy at a fraction
of the size and latency, which is exactly why it is the edge choice. Note
also that a 0.29 M from-scratch CNN already reaches 99.4%: this casting
dataset is highly separable, so the high absolute accuracy should not be
over-interpreted as evidence of a hard task solved.

## Table M1-B — Per-class metrics (representative median seed, s=2; acc 99.30%)
| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| def_front | 0.9956 | 0.9934 | 0.9945 | 453 |
| ok_front | 0.9886 | 0.9924 | 0.9905 | 262 |

Confusion matrix (rows=true, cols=pred): [[450, 3], [2, 260]] — i.e. 3
defective parts passed as OK (false negatives) and 2 good parts flagged.
Across the 3 seeds the false-negative count ranged 2–5; missed defects are
the safety-critical error type and are discussed as a limitation.

## Table M1-C — Inference latency (batch=1, 30 warm-up discarded, 300 timed runs)
| Configuration | Mean | Median | p95 |
|---|---|---|---|
| PyTorch, RTX 5060 GPU | 8.07 ms | 7.84 ms | 12.98 ms |
| PyTorch, CPU | 12.39 ms | 12.46 ms | 13.99 ms |
| **ONNX Runtime, CPU (edge target)** | **2.37 ms** | 2.12 ms | 3.64 ms |

All configurations are far under the <2 s design target. The offline
edge-deployment path (ONNX on CPU) is the fastest at ~2.4 ms.

## Figure M1 — Grad-CAM (reports/gradcam.png)
Grad-CAM overlays on 8 test images (4 defect, 4 OK) show the network's
decisive regions fall on the casting surface/rim where defects occur, not
on the background or lighting — evidence the model keys on the part.

## Remaining honesty notes for this module
- Baselines (ResNet-50, SimpleCNN) are single-seed; multi-seed would
  tighten the comparison (main model is 3-seed).
- The old ONNX export in models/ came from the original (test-selected)
  checkpoint; regenerate it from the proper model before deployment.
- Dataset is castings, not CNC-turned/milled parts, and only surface/
  visual defects are claimed (no dimensional/tolerance detection).
