# Drishti-AI — Paper Structure & Placement Plan

**Blueprint only — no prose is drafted here (per instruction).** This maps every
table, figure, and citation to its section, in the exact order it should appear when
the manuscript is written. Data/figures come from `Drishti-AI_Paper_Materials.md` and
`paper_figures/`.

- **Figure 1 = the author's Drishti architecture diagram** (replaces the generated
  `fig01_architecture.png`; drop that placeholder from the paper).
- Citation style follows the supplied screenshot: **IEEE-style inline numbered brackets**,
  e.g. "...powers GitHub Copilot [1], [2]." Group consecutive cites as `[4], [5]`.
  Numbering below is a fixed master list `[1]–[48]`; renumber to order-of-first-appearance
  at final typesetting.

---

## 1. Section outline

1. Abstract
2. Introduction
3. Related Work
4. System Overview & Architecture
5. Datasets
6. Methods (M1–M4)
7. Experimental Setup
8. Results (M1–M4)
9. Discussion
10. Limitations
11. Conclusion & Future Work
12. References

---

## 2. Master figure map (paper reading order → source)

| Paper Fig | Content | Source file | Appears in |
|---|---|---|---|
| **Figure 1** | Drishti-AI system architecture | **author-provided diagram** | §4 |
| Figure 2 | Dataset composition (M1 class balance + M4 volume spread) | `fig14_dataset_overview.png` | §5 |
| Figure 3 | M1 training/validation accuracy | `fig02_m1_training_curves.png` | §8.1 |
| Figure 4 | M1 loss curves | `fig03_m1_loss_curves.png` | §8.1 |
| Figure 5 | M1 extended confusion matrix | `fig04_m1_confusion.png` | §8.1 |
| Figure 6 | M1 accuracy vs. parameters | `fig05_m1_tradeoff.png` | §8.1 |
| Figure 7 | M1 per-seed accuracy variance | `fig07_m1_seed_variance.png` | §8.1 |
| Figure 8 | M1 inference latency | `fig06_m1_latency.png` | §8.1 |
| Figure 9 | M1 Grad-CAM saliency | `module1_cv_defect/reports/gradcam.png` | §8.1 |
| Figure 10 | M3 predicted vs. actual RUL | `fig09_m3_pred_actual.png` | §8.2 |
| Figure 11 | M3 model vs. baselines | `fig08_m3_comparison.png` | §8.2 |
| Figure 12 | M4 WAPE vs. baselines | `fig10_m4_wape.png` | §8.3 |
| Figure 13 | M4 cross-validation stability | `fig11_m4_cv.png` | §8.3 |
| Figure 14 | M4 forecast with P10–P90 interval | `fig12_m4_forecast.png` | §8.3 |
| Figure 15 | M4 feature importance | `fig13_m4_importance.png` | §8.3 |

## 3. Master table map (paper reading order → source)

| Paper Table | Content | Source (Materials) | Appears in |
|---|---|---|---|
| **Table 1** | Claimed contributions | T17 | §2 |
| Table 2 | System overview (per module) | T1 | §4 |
| Table 3 | Datasets | T2 | §5 |
| Table 4 | M1 training configuration | T7 | §6 |
| Table 5 | M3 data & by-tool split | T9 | §6 |
| Table 6 | M3 training configuration | T10 | §6 |
| Table 7 | M4 feature set (18 features) | T14 | §6 |
| Table 8 | Evaluation metrics defined | T16 | §7 |
| Table 9 | Software & environment | T15 | §7 |
| Table 10 | M1 architecture comparison | T3 | §8.1 |
| Table 11 | M1 per-class report | T4 | §8.1 |
| Table 12 | M1 per-seed detail | T5 | §8.1 |
| Table 13 | M1 inference latency | T6 | §8.1 |
| Table 14 | M3 RUL vs. baselines | T8 | §8.2 |
| Table 15 | M4 forecaster vs. baselines | T11 | §8.3 |
| Table 16 | M4 supporting metrics | T12 | §8.3 |
| Table 17 | M4 cross-validation | T13 | §8.3 |
| Table 18 | Limitations & caveats | T18 | §9 |

---

## 4. Section-by-section sequence (tables, figures, citations in order)

### §1 Abstract
- Tables/Figures: none.
- Citations: none (convention).

### §2 Introduction
- **Table 1** (contributions) near the end of the section.
- Citations in order: MSME / Industry 4.0 motivation `[47]`; offline/edge-AI framing `[30]`;
  efficient CNN backbone rationale `[1]`; vernacular-NLP motivation `[48]`.

### §3 Related Work (four thematic paragraphs; citation-dense, screenshot style)
- Tables/Figures: none.
- Paragraph A — **Visual defect detection**: `[44]`, `[1]`, `[3]`, `[10]`.
- Paragraph B — **Predictive maintenance / RUL**: `[45]`, `[46]`, `[11]`, `[12]`.
- Paragraph C — **Demand forecasting**: `[31]`, `[34]`, `[36]`, `[35]`, `[32]`, `[33]`.
- Paragraph D — **Transfer learning, explainability & edge deployment**: `[16]`, `[17]`,
  `[18]`, `[2]`, `[28]`, `[29]`, `[30]`; vernacular alerting `[48]`.

### §4 System Overview & Architecture
- **Figure 1** (author's architecture diagram) — lead figure of the section.
- **Table 2** (system overview, one row per module).
- Citations: offline runtime / export path `[22]`, `[23]`, `[21]`.

### §5 Datasets
- **Table 3** (datasets), then **Figure 2** (dataset composition).
- Citations in order: casting images `[41]`; CNC milling `[42]`; product demand `[43]`.

### §6 Methods
- **§6.1 M1 — Defect detection**: **Table 4** (training config).
  Citations: MobileNetV2 `[1]`; ImageNet pretraining `[4]`; Adam `[9]`; BatchNorm `[7]`;
  Dropout `[8]`; transfer-learning basis `[16]`, `[17]`; Grad-CAM method `[18]`.
- **§6.2 M2 — Vernacular alert**: no table/figure. Citation: `[48]`.
- **§6.3 M3 — Predictive maintenance**: **Table 5** (data & split), **Table 6** (config).
  Citations: XGBoost `[11]`; gradient boosting `[12]`; time-series features `[40]`; RUL context `[45]`.
- **§6.4 M4 — Demand forecasting**: **Table 7** (feature set).
  Citations: XGBoost `[11]`; quantile regression for intervals `[32]`; WAPE `[35]`; Prophet baseline `[31]`.

### §7 Experimental Setup
- **Table 8** (metrics defined), **Table 9** (software & environment).
- Citations in order: PyTorch `[21]`; scikit-learn `[24]`; NumPy `[25]`; pandas `[26]`;
  Matplotlib `[27]`; multi-seed variance rationale `[39]`; PR-curve/imbalance note `[38]`.

### §8 Results
- **§8.1 M1** — order: **Table 10** (arch comparison) → **Figure 6** (acc vs params) →
  **Figure 7** (seed variance) → **Table 11** (per-class) → **Figure 5** (confusion) →
  **Table 12** (per-seed) → **Figure 3** (train/val acc) → **Figure 4** (loss) →
  **Table 13** (latency) → **Figure 8** (latency) → **Figure 9** (Grad-CAM).
  Citations: ResNet-50 reference model `[3]`; MobileNetV2 `[1]`; Grad-CAM `[18]`; imbalance `[38]`.
- **§8.2 M3** — order: **Table 14** (vs baselines) → **Figure 11** (comparison) →
  **Figure 10** (predicted vs actual). Citations: `[11]`, `[45]`.
- **§8.3 M4** — order: **Table 15** (vs baselines) → **Figure 12** (WAPE) →
  **Table 16** (supporting metrics) → **Table 17** (CV) → **Figure 13** (CV stability) →
  **Figure 14** (forecast + interval) → **Figure 15** (feature importance).
  Citations: Prophet `[31]`; WAPE `[35]`; quantile intervals `[32]`.

### §9 Discussion
- Tables/Figures: none (reference earlier ones).
- Citations: variance-aware benchmarking `[39]`; edge efficiency `[30]`, `[2]`.

### §10 Limitations
- **Table 18** (limitations & caveats).
- Citations: none.

### §11 Conclusion & Future Work
- Tables/Figures: none.
- Citations: forward-looking, optionally `[36]` (M5), `[30]` (edge).

### §12 References — `[1]–[48]` below.

---

## 5. Reference list (master numbering `[1]`–`[48]`, each with URL or DOI)

> Verify every DOI/URL against the publisher before camera-ready — especially datasets
> `[41]–[43]`; confirm the exact repository record for the CNC milling set `[42]`.

1. Sandler et al., "MobileNetV2," CVPR 2018. https://arxiv.org/abs/1801.04381 — DOI:10.1109/CVPR.2018.00474
2. Howard et al., "MobileNets," 2017. https://arxiv.org/abs/1704.04861
3. He et al., "Deep Residual Learning (ResNet)," CVPR 2016. DOI:10.1109/CVPR.2016.90 — https://arxiv.org/abs/1512.03385
4. Deng et al., "ImageNet," CVPR 2009. DOI:10.1109/CVPR.2009.5206848
5. Krizhevsky et al., "AlexNet," NeurIPS 2012. DOI:10.1145/3065386
6. Simonyan & Zisserman, "VGG," ICLR 2015. https://arxiv.org/abs/1409.1556
7. Ioffe & Szegedy, "Batch Normalization," ICML 2015. https://arxiv.org/abs/1502.03167
8. Srivastava et al., "Dropout," JMLR 2014. https://jmlr.org/papers/v15/srivastava14a.html
9. Kingma & Ba, "Adam," ICLR 2015. https://arxiv.org/abs/1412.6980
10. Tan & Le, "EfficientNet," ICML 2019. https://arxiv.org/abs/1905.11946
11. Chen & Guestrin, "XGBoost," KDD 2016. DOI:10.1145/2939672.2939785 — https://arxiv.org/abs/1603.02754
12. Friedman, "Greedy Function Approximation (Gradient Boosting)," Ann. Statist. 2001. DOI:10.1214/aos/1013203451
13. Breiman, "Random Forests," Machine Learning 2001. DOI:10.1023/A:1010933404324
14. Ke et al., "LightGBM," NeurIPS 2017. https://papers.nips.cc/paper/6907-lightgbm
15. Lundberg & Lee, "SHAP," NeurIPS 2017. https://arxiv.org/abs/1705.07874
16. Pan & Yang, "A Survey on Transfer Learning," IEEE TKDE 2010. DOI:10.1109/TKDE.2009.191
17. Yosinski et al., "How Transferable Are Features?," NeurIPS 2014. https://arxiv.org/abs/1411.1792
18. Selvaraju et al., "Grad-CAM," ICCV 2017. DOI:10.1109/ICCV.2017.74 — https://arxiv.org/abs/1610.02391
19. Zhou et al., "CAM," CVPR 2016. https://arxiv.org/abs/1512.04150
20. Simonyan et al., "Saliency Maps," 2013. https://arxiv.org/abs/1312.6034
21. Paszke et al., "PyTorch," NeurIPS 2019. https://arxiv.org/abs/1912.01703
22. ONNX: Open Neural Network Exchange. https://onnx.ai — https://github.com/onnx/onnx
23. ONNX Runtime. https://onnxruntime.ai
24. Pedregosa et al., "Scikit-learn," JMLR 2011. https://jmlr.org/papers/v12/pedregosa11a.html
25. Harris et al., "Array Programming with NumPy," Nature 2020. DOI:10.1038/s41586-020-2649-2
26. McKinney, "Data Structures for Statistical Computing (pandas)," SciPy 2010. DOI:10.25080/Majora-92bf1922-00a
27. Hunter, "Matplotlib," CiSE 2007. DOI:10.1109/MCSE.2007.55
28. Jacob et al., "Quantization for Integer-Arithmetic Inference," CVPR 2018. https://arxiv.org/abs/1712.05877
29. Hinton et al., "Distilling the Knowledge in a Neural Network," 2015. https://arxiv.org/abs/1503.02531
30. Warden & Situnayake, *TinyML*, O'Reilly 2019. https://www.oreilly.com/library/view/tinyml/9781492052036/
31. Taylor & Letham, "Forecasting at Scale (Prophet)," The American Statistician 2018. DOI:10.1080/00031305.2017.1380080
32. Koenker & Bassett, "Regression Quantiles," Econometrica 1978. DOI:10.2307/1913643
33. Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (3e), 2021. https://otexts.com/fpp3/
34. Makridakis et al., "The M4 Competition," Int. J. Forecasting 2020. DOI:10.1016/j.ijforecast.2019.04.014
35. Hyndman & Koehler, "Another Look at Measures of Forecast Accuracy," Int. J. Forecasting 2006. DOI:10.1016/j.ijforecast.2006.03.001
36. Makridakis et al., "The M5 Accuracy Competition," Int. J. Forecasting 2022. DOI:10.1016/j.ijforecast.2021.11.013
37. Sokolova & Lapalme, "A Systematic Analysis of Performance Measures for Classification," Inf. Proc. & Mgmt 2009. DOI:10.1016/j.ipm.2009.03.002
38. Saito & Rehmsmeier, "The Precision-Recall Plot on Imbalanced Data," PLoS ONE 2015. DOI:10.1371/journal.pone.0118432
39. Bouthillier et al., "Accounting for Variance in ML Benchmarks," MLSys 2021. https://arxiv.org/abs/2103.03098
40. Christ et al., "tsfresh," Neurocomputing 2018. DOI:10.1016/j.neucom.2018.03.067
41. Dabhi, R., "Casting Product Image Data for Quality Inspection," Kaggle. https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product
42. Piecuch & Żabiński, CNC milling tool-wear dataset. *[Confirm publisher/DOI record.]*
43. Zhao, F., "Forecasts for Product Demand," Kaggle. https://www.kaggle.com/datasets/felixzhao/productdemandforecasting
44. Tabernik et al., "Segmentation-Based Deep-Learning for Surface-Defect Detection," J. Intell. Manuf. 2020. DOI:10.1007/s10845-019-01476-x
45. Lei et al., "Machinery Health Prognostics: A Systematic Review," MSSP 2018. DOI:10.1016/j.ymssp.2017.11.016
46. Zhao et al., "Deep Learning for Machine Health Monitoring," MSSP 2019. DOI:10.1016/j.ymssp.2018.05.050
47. Lee et al., "A CPS Architecture for Industry 4.0 Manufacturing," Manufacturing Letters 2015. DOI:10.1016/j.mfglet.2014.12.001
48. Kakwani et al., "IndicNLPSuite," Findings of EMNLP 2020. https://aclanthology.org/2020.findings-emnlp.445/

---

## 6. Citation-style note (matches supplied screenshot)
- Bracketed numerals, placed **after** the claim, before the period: "...reaches 48% [14]."
- Multiple sources: "...new repair paradigms [1], [2]." (comma-separated, each bracketed).
- Ranges when ≥3 consecutive: "[1]–[3]".
- Every non-trivial factual/prior-work claim carries a cite; our own measured results do **not**
  (they point to a Table/Figure instead, e.g. "...99.4% test accuracy (Table 10)").

*Next step on your word: draft the prose section by section against this plan.*
