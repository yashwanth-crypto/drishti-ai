# Drishti-AI — Paper Materials Pack

**Pre-draft asset bundle: tables, figures, and references for a publishable paper.**
This file collects the empirical scaffolding to write the manuscript *before* prose is
written. Every number is drawn from the project's on-disk artifacts (metrics JSONs,
saved models, dataset CSVs, `events.json`), not re-typed from memory. Figures live in
`paper_figures/` and are generated reproducibly by `make_paper_figures.py`.

- **18 tables** (T1–T18)
- **14 figures** (F1–F14; 13 generated + 1 pre-existing Grad-CAM)
- **48 references** with URL or DOI (R1–R48)

> **Provenance note.** M1 = `module1_cv_defect`, M3 = `module3_predictive_maintenance`,
> M4 = `module4_demand_forecasting`. All splits are held-out; model selection is on
> validation, never on test. M1 architectures are each run over 3 seeds {1, 2, 42}.
> Standing honesty caveats are in **Table 18**.

---

## 1. Tables

### Table 1 — System overview (one row per module)
| Module | Task | Model | Dataset | Headline result | Deployment |
|---|---|---|---|---|---|
| M1 | Casting surface-defect classification | MobileNetV2 (transfer) | Casting product images [R41] | 99.39% ± 0.24 test acc | ONNX, 2.37 ms/img (CPU) |
| M2 | Vernacular (Hindi) operator alert | Rule-mapped template NLG | Derived from M1 output | Deterministic; 1 alert / inspection | Offline, no model |
| M3 | Remaining useful life (RUL) of CNC tools | XGBoost regressor | CNC milling, by-tool split [R42] | R² 0.545 on unseen tools | CPU, batch |
| M4 | Weekly demand forecast per category | XGBoost + quantile pair | Historical Product Demand [R43] | WAPE 19.7% (beats Prophet) | CPU, batch |

### Table 2 — Datasets
| Dataset | Module | Domain | Size | Split protocol | Source |
|---|---|---|---|---|---|
| Casting product image data | M1 | Submersible-pump impeller, grayscale 300×300 | ~7.3k images (def/ok) | Stratified train/val (0.15) + fixed test (n=715) | Kaggle [R41] |
| CNC milling (Piecuch & Żabiński) | M3 | Vibration + 3-phase current, per cutting pass | 968 passes, 14 physical tools | **By-tool** GroupShuffleSplit (9 train / 4 test; tool 11 dropped) | [R42] |
| Historical Product Demand | M4 | Multi-warehouse order lines | 1,048,575 orders → 2,160 products → 28 modelled categories | Temporal cut-off 2016-01-11, 52 held-out weeks | Kaggle [R43] |

### Table 3 — M1 architecture comparison (same split; test evaluated once; mean ± SD over 3 seeds)
| Model | Params (M) | Test accuracy (%) | Macro-F1 (%) | Per-seed accuracy (%) |
|---|---|---|---|---|
| **MobileNetV2 (ours)** | **2.23** | **99.39 ± 0.24** | **99.35 ± 0.26** | 99.72 / 99.30 / 99.16 |
| ResNet-50 | 23.51 | 99.67 ± 0.07 | 99.65 ± 0.07 | 99.58 / 99.72 / 99.72 |
| SimpleCNN (from scratch) | 0.29 | 99.35 ± 0.07 | 99.30 ± 0.07 | 99.30 / 99.30 / 99.44 |

*Takeaway:* MobileNetV2 matches a 10×-larger ResNet-50 within seed variance; a 0.29 M
scratch CNN also reaching 99.4% honestly indicates the casting set is highly separable.

### Table 4 — M1 per-class report (representative median seed s=2, acc 99.30%)
| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| def_front | 0.9956 | 0.9934 | 0.9945 | 453 |
| ok_front | 0.9886 | 0.9924 | 0.9905 | 262 |
| **Macro avg** | 0.9921 | 0.9929 | 0.9925 | 715 |
| **Weighted avg** | 0.9930 | 0.9930 | 0.9930 | 715 |

### Table 5 — M1 MobileNetV2 per-seed detail
| Seed | Best epoch (selected on val) | Val acc (%) | Test acc (%) | Confusion [[TN,FP],[FN,TP]]* | Missed defects (FN) |
|---|---|---|---|---|---|
| 1 | fine-tune | 99.30 | 99.72 | [[451, 2], [0, 262]] | 2 |
| 2 | fine-tune ep3 | 99.30 | 99.30 | [[450, 3], [2, 260]] | 3 |
| 42 | fine-tune | 99.30 | 99.16 | [[448, 5], [1, 261]] | 5 |

*Rows/cols ordered (def_front, ok_front); "missed defects" = true-defect predicted OK,
the safety-critical error (Table 18).

### Table 6 — M1 inference latency (batch = 1, 30 warm-up, 300 timed runs; RTX 5060 / CPU)
| Configuration | Mean (ms) | p95 (ms) | vs < 2000 ms target |
|---|---|---|---|
| **ONNX Runtime CPU (edge target)** | **2.37** | 3.64 | 844× headroom |
| PyTorch GPU | 8.07 | 12.98 | 248× headroom |
| PyTorch CPU | 12.39 | 13.99 | 161× headroom |

### Table 7 — M1 training configuration
| Hyperparameter | Value |
|---|---|
| Backbone / init | MobileNetV2, ImageNet-pretrained |
| Head schedule | 15 epochs, Adam, lr 1e-3 (backbone frozen) |
| Fine-tune schedule | 5 epochs, Adam, lr 1e-5, top 20 layers unfrozen |
| Batch size / image size | 32 / 224×224 |
| Val split | 15%, stratified from train folder (test untouched) |
| Model selection | best **validation** accuracy; test scored once |
| Seeds | 1, 2, 42 |

### Table 8 — M3 RUL regression vs. baselines (by-tool split, unseen test tools)
| Model | RMSE ↓ | MAE ↓ | R² ↑ |
|---|---|---|---|
| Constant mean (no-skill) | 0.2955 | 0.2562 | −0.000 |
| Linear regression | 0.2534 | 0.1941 | 0.2647 |
| **XGBoost (ours)** | **0.1995** | **0.1602** | **0.5445** |

*Takeaway:* XGBoost roughly doubles the linear model's R² on tools never seen in
training; modest absolute R² is expected and honest for cross-tool generalization.

### Table 9 — M3 data & split
| Item | Value |
|---|---|
| Target | CycleToFailureNormalized (1.0 fresh → 0.0 failure) |
| Features | 130 (time-domain min/max/mean/std/skew/kurtosis per sensor channel + tool metadata) |
| Sensors | Spindle & axis accelerometers + 3-phase spindle/axis currents |
| Train tools (9) | 3, 4, 5, 6, 7, 8, 9, 102, 105 |
| Test tools (4, held out) | 2, 10, 101, 103 |
| Dropped | Tool 11 (single recorded cycle) |

### Table 10 — M3 training configuration
| Hyperparameter | Value |
|---|---|
| Estimator | XGBoost `XGBRegressor` |
| n_estimators / max_depth | 300 / 4 |
| learning_rate | 0.05 |
| subsample / colsample_bytree | 0.8 / 0.8 |
| Split | GroupShuffleSplit by tool, test_size 0.25, seed 42 |

### Table 11 — M4 forecaster vs. baselines (held-out 52 weeks, 28 categories)
| Forecaster | WAPE (%) ↓ | Rel. improvement vs. naïve |
|---|---|---|
| Prophet | 30.39 | −18.4% (worse) |
| Seasonal-naïve (52-week) | 27.77 | −8.2% (worse) |
| Naïve (last value) | 25.66 | — |
| **XGBoost (ours)** | **19.74** | **+23.1% (better)** |

### Table 12 — M4 supporting metrics (final held-out model)
| Metric | Value | Note |
|---|---|---|
| WAPE | 19.74% | weighted abs. % error, future weeks |
| R² | 0.9438 | held-out weeks |
| RMSE / MAE | 722,263 / 142,354 | units |
| 3-fold expanding-window CV WAPE | 20.60% | mean of folds (Table 13) |
| 80% prediction-interval coverage | 74.20% | target ~80% (slightly under) |

### Table 13 — M4 expanding-window cross-validation
| Fold | WAPE (%) |
|---|---|
| Fold 1 | 22.7 |
| Fold 2 | 17.4 |
| Fold 3 | 21.7 |
| **Mean** | **20.6** |
| Final held-out | 19.7 |

### Table 14 — M4 feature set (18 features)
| Group | Features |
|---|---|
| Lags | lag_1, lag_2, lag_3, lag_4, lag_8, lag_12, lag_52 |
| Rolling / smoothing | rolling_mean_4, rolling_std_4, rolling_mean_8, rolling_mean_13, ewma_4 |
| Trend | trend_1, trend_4 |
| Calendar | month, weekofyear, woy_sin, woy_cos |

*Note:* product category was deliberately **excluded** — an ablation showed the categorical
feature hurt held-out WAPE. Point model uses fixed 300 trees (no early stopping); the
P10/P90 interval comes from a paired quantile-loss model (α = 0.1, 0.9).

### Table 15 — Software & environment (reproducibility)
| Component | Version / setting |
|---|---|
| Python | 3.x (venv, pinned `requirements.txt`) |
| Deep learning | PyTorch [R21]; export via ONNX / ONNX Runtime [R22][R23] |
| Gradient boosting | XGBoost [R11] |
| Classic ML / arrays | scikit-learn [R24], NumPy [R25], pandas [R26] |
| Forecasting baseline | Prophet [R31] |
| Plots | Matplotlib [R27] |
| Seeds | {1, 2, 42} (M1 arch); 42 (M3, M4) |
| Commands | see `REPRODUCE.md` |

### Table 16 — Evaluation metrics defined
| Metric | Definition | Used in |
|---|---|---|
| Accuracy / Macro-F1 | standard classification [R37] | M1 |
| Confusion / FN | true-defect → predicted-OK = safety-critical miss | M1 |
| RMSE / MAE / R² | regression error & explained variance | M3 |
| WAPE | Σ\|y−ŷ\| / Σ\|y\| (scale-free, volume-weighted) [R35] | M4 |
| Interval coverage | fraction of actuals inside P10–P90 | M4 |

### Table 17 — Claimed contributions (for Introduction bullet list)
| # | Contribution |
|---|---|
| C1 | A fully **offline**, four-module edge stack for Indian MSME manufacturing on a shared JSON schema. |
| C2 | Edge-suitable defect detector (2.23 M params, 2.37 ms/img) matching ResNet-50 within seed variance. |
| C3 | **Honest** RUL evaluation via by-tool splitting, isolating true cross-tool generalization (R² 0.545). |
| C4 | Demand forecaster beating Prophet and naïve/seasonal baselines (WAPE 19.7%) with calibrated intervals. |
| C5 | A vernacular (Hindi) alerting layer bridging model output to shop-floor operators. |

### Table 18 — Limitations & honesty caveats
| # | Caveat |
|---|---|
| L1 | Public/synthetic datasets only — no factory pilot, live sensor, or camera rig. |
| L2 | M1 casting set is highly separable (scratch CNN ≈ 99.4%); ceiling effect limits architecture claims. |
| L3 | M1 baselines and M4 model are single-seed for some runs; M1 architectures are 3-seed. |
| L4 | Safety-critical false negatives (2–5 missed defects/seed) remain; not yet cost-weighted. |
| L5 | M3 uses CNC-milled parts, not the casting parts of M1 — modules are not co-located on one line. |
| L6 | M4 source data's final weeks are truncated (documented; figures trim the artifact, model does not). |
| L7 | ROI figures are editable design-target projections, not measured deployment outcomes. |

---

## 2. Figures (in `paper_figures/`)

| # | File | Caption | Source data |
|---|---|---|---|
| F1 | *(use your existing architecture diagram)* — `fig01_architecture.png` is a generated placeholder only | Four-module offline edge architecture on a shared JSON schema. | schematic |
| F2 | `fig02_m1_training_curves.png` | M1 train/val accuracy vs. epoch (seed 2), with ResNet-50 val overlay; head→fine-tune marked. | `proper_metrics_seed2`, `baseline_resnet50` |
| F3 | `fig03_m1_loss_curves.png` | M1 MobileNetV2 train/val cross-entropy loss (seed 2). | `proper_metrics_seed2` |
| F4 | `fig04_m1_confusion.png` | M1 confusion matrix, held-out test n=715 (seed 2). | `proper_metrics_seed2` |
| F5 | `fig05_m1_tradeoff.png` | M1 accuracy vs. parameters (log x), mean ± SD over 3 seeds. | all M1 seed JSONs |
| F6 | `fig06_m1_latency.png` | M1 single-image latency: ONNX-CPU vs. PyTorch GPU/CPU (mean & p95). | benchmark |
| F7 | `fig07_m1_seed_variance.png` | M1 per-seed test accuracy across 3 architectures. | all M1 seed JSONs |
| F8 | `fig08_m3_comparison.png` | M3 RUL: RMSE, MAE, R² vs. constant/linear baselines. | `baseline_comparison_pdm` |
| F9 | `fig09_m3_pred_actual.png` | M3 predicted vs. actual RUL on unseen test tools (R² 0.545). | model + milling CSV |
| F10 | `fig10_m4_wape.png` | M4 WAPE vs. Prophet / seasonal / naïve baselines. | `baseline_comparison` |
| F11 | `fig11_m4_cv.png` | M4 expanding-window CV WAPE stability. | `model_metadata` |
| F12 | `fig12_m4_forecast.png` | M4 forecast with P10–P90 interval (representative category). | `events.json` |
| F13 | `fig13_m4_importance.png` | M4 XGBoost top-12 feature importance (gain). | saved model |
| F14 | `fig14_dataset_overview.png` | M1 test class balance + M4 category volume spread. | seed JSON + `events.json` |
| F15 | `module1_cv_defect/reports/gradcam.png` | M1 Grad-CAM saliency on a defect image (explainability). | pre-existing |

---

## 3. References (48, each with URL or DOI)

> Identifiers below are arXiv abstract URLs (stable) or DOIs for well-known works.
> **Verify every DOI/URL against the publisher before camera-ready** — especially the
> three datasets (R41–R43), which should be cited with their exact repository record.

**Architectures & deep learning**
- **R1.** Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks," CVPR 2018. https://arxiv.org/abs/1801.04381 — DOI:10.1109/CVPR.2018.00474
- **R2.** Howard et al., "MobileNets: Efficient CNNs for Mobile Vision," 2017. https://arxiv.org/abs/1704.04861
- **R3.** He et al., "Deep Residual Learning for Image Recognition," CVPR 2016. DOI:10.1109/CVPR.2016.90 — https://arxiv.org/abs/1512.03385
- **R4.** Deng et al., "ImageNet: A Large-Scale Hierarchical Image Database," CVPR 2009. DOI:10.1109/CVPR.2009.5206848
- **R5.** Krizhevsky, Sutskever, Hinton, "ImageNet Classification with Deep CNNs (AlexNet)," NeurIPS 2012. DOI:10.1145/3065386
- **R6.** Simonyan & Zisserman, "Very Deep CNNs (VGG)," ICLR 2015. https://arxiv.org/abs/1409.1556
- **R7.** Ioffe & Szegedy, "Batch Normalization," ICML 2015. https://arxiv.org/abs/1502.03167
- **R8.** Srivastava et al., "Dropout," JMLR 2014. https://jmlr.org/papers/v15/srivastava14a.html
- **R9.** Kingma & Ba, "Adam: A Method for Stochastic Optimization," ICLR 2015. https://arxiv.org/abs/1412.6980
- **R10.** Tan & Le, "EfficientNet," ICML 2019. https://arxiv.org/abs/1905.11946

**Gradient boosting & classic ML**
- **R11.** Chen & Guestrin, "XGBoost: A Scalable Tree Boosting System," KDD 2016. DOI:10.1145/2939672.2939785 — https://arxiv.org/abs/1603.02754
- **R12.** Friedman, "Greedy Function Approximation: A Gradient Boosting Machine," Ann. Statist. 2001. DOI:10.1214/aos/1013203451
- **R13.** Breiman, "Random Forests," Machine Learning 2001. DOI:10.1023/A:1010933404324
- **R14.** Ke et al., "LightGBM," NeurIPS 2017. https://papers.nips.cc/paper/6907-lightgbm
- **R15.** Lundberg & Lee, "A Unified Approach to Interpreting Model Predictions (SHAP)," NeurIPS 2017. https://arxiv.org/abs/1705.07874

**Transfer learning & explainability**
- **R16.** Pan & Yang, "A Survey on Transfer Learning," IEEE TKDE 2010. DOI:10.1109/TKDE.2009.191
- **R17.** Yosinski et al., "How Transferable Are Features in Deep Neural Networks?," NeurIPS 2014. https://arxiv.org/abs/1411.1792
- **R18.** Selvaraju et al., "Grad-CAM," ICCV 2017. DOI:10.1109/ICCV.2017.74 — https://arxiv.org/abs/1610.02391
- **R19.** Zhou et al., "Learning Deep Features for Discriminative Localization (CAM)," CVPR 2016. https://arxiv.org/abs/1512.04150
- **R20.** Simonyan et al., "Deep Inside CNNs: Saliency Maps," 2013. https://arxiv.org/abs/1312.6034

**Frameworks & tooling**
- **R21.** Paszke et al., "PyTorch: An Imperative Style, High-Performance Deep Learning Library," NeurIPS 2019. https://arxiv.org/abs/1912.01703
- **R22.** ONNX: Open Neural Network Exchange. https://onnx.ai — https://github.com/onnx/onnx
- **R23.** ONNX Runtime. https://onnxruntime.ai
- **R24.** Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 2011. https://jmlr.org/papers/v12/pedregosa11a.html
- **R25.** Harris et al., "Array Programming with NumPy," Nature 2020. DOI:10.1038/s41586-020-2649-2
- **R26.** McKinney, "Data Structures for Statistical Computing in Python (pandas)," SciPy 2010. DOI:10.25080/Majora-92bf1922-00a
- **R27.** Hunter, "Matplotlib: A 2D Graphics Environment," CiSE 2007. DOI:10.1109/MCSE.2007.55

**Edge / efficient inference**
- **R28.** Jacob et al., "Quantization and Training of NNs for Efficient Integer-Arithmetic Inference," CVPR 2018. https://arxiv.org/abs/1712.05877
- **R29.** Hinton et al., "Distilling the Knowledge in a Neural Network," 2015. https://arxiv.org/abs/1503.02531
- **R30.** Warden & Situnayake, *TinyML*, O'Reilly 2019. https://www.oreilly.com/library/view/tinyml/9781492052036/

**Forecasting**
- **R31.** Taylor & Letham, "Forecasting at Scale (Prophet)," The American Statistician 2018. DOI:10.1080/00031305.2017.1380080
- **R32.** Koenker & Bassett, "Regression Quantiles," Econometrica 1978. DOI:10.2307/1913643
- **R33.** Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (3e), 2021. https://otexts.com/fpp3/
- **R34.** Makridakis et al., "The M4 Competition," Int. J. Forecasting 2020. DOI:10.1016/j.ijforecast.2019.04.014
- **R35.** Hyndman & Koehler, "Another Look at Measures of Forecast Accuracy," Int. J. Forecasting 2006. DOI:10.1016/j.ijforecast.2006.03.001
- **R36.** Makridakis et al., "The M5 Accuracy Competition," Int. J. Forecasting 2022. DOI:10.1016/j.ijforecast.2021.11.013

**Evaluation & methodology**
- **R37.** Sokolova & Lapalme, "A Systematic Analysis of Performance Measures for Classification," Inf. Proc. & Mgmt 2009. DOI:10.1016/j.ipm.2009.03.002
- **R38.** Saito & Rehmsmeier, "The Precision-Recall Plot Is More Informative than the ROC Plot on Imbalanced Data," PLoS ONE 2015. DOI:10.1371/journal.pone.0118432
- **R39.** Bouthillier et al., "Accounting for Variance in Machine Learning Benchmarks," MLSys 2021. https://arxiv.org/abs/2103.03098
- **R40.** Christ et al., "Time Series FeatuRe Extraction (tsfresh)," Neurocomputing 2018. DOI:10.1016/j.neucom.2018.03.067

**Datasets (verify exact repository record before publication)**
- **R41.** Dabhi, R., "Casting Product Image Data for Quality Inspection," Kaggle. https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product
- **R42.** Piecuch & Żabiński, CNC milling tool-wear dataset (per-pass vibration + current features, 14 tools). *[Confirm publisher/DOI — Mendeley Data / journal record.]*
- **R43.** Zhao, F., "Forecasts for Product Demand," Kaggle. https://www.kaggle.com/datasets/felixzhao/productdemandforecasting

**Manufacturing defect detection & predictive maintenance**
- **R44.** Tabernik et al., "Segmentation-Based Deep-Learning Approach for Surface-Defect Detection," J. Intelligent Manufacturing 2020. DOI:10.1007/s10845-019-01476-x
- **R45.** Lei et al., "Machinery Health Prognostics: A Systematic Review," Mechanical Systems and Signal Processing 2018. DOI:10.1016/j.ymssp.2017.11.016
- **R46.** Zhao et al., "Deep Learning and Its Applications to Machine Health Monitoring," MSSP 2019. DOI:10.1016/j.ymssp.2018.05.050
- **R47.** Lee et al., "A Cyber-Physical Systems Architecture for Industry 4.0 Manufacturing," Manufacturing Letters 2015. DOI:10.1016/j.mfglet.2014.12.001
- **R48.** Kakwani et al., "IndicNLPSuite: Monolingual Corpora & Models for Indian Languages," Findings of EMNLP 2020. https://aclanthology.org/2020.findings-emnlp.445/

---

*Regenerate all figures:* `python make_paper_figures.py` (writes to `paper_figures/`).
