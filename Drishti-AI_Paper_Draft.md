# Drishti-AI: An Offline, Vernacular AI Platform for Quality, Maintenance and Demand Intelligence in Indian MSME Manufacturing

**Authors:** [Your Name], [Affiliation], [Email]

> Draft v1 — a systems/application paper. All reported metrics are measured on
> public datasets with held-out evaluation; this is an explicitly framed
> proof-of-concept, not a field-validated deployment (see Section IX).

---

## Abstract

Micro, small and medium enterprises (MSMEs) form the backbone of Indian
manufacturing, yet they are largely excluded from the AI-driven quality and
efficiency gains of Industry 4.0. Commercial machine-vision inspection systems
cost several lakh rupees, present English-only interfaces, and assume reliable
cloud connectivity — three assumptions that fail on a typical CNC or casting
shop floor. We present Drishti-AI, an integrated, fully-offline platform that
combines four capabilities behind one dashboard: (i) edge computer-vision
defect detection, (ii) a vernacular (Hindi) alert layer that renders each
result as a plain-language instruction for non-English-literate workers,
(iii) predictive maintenance from vibration/current sensor signals, and
(iv) weekly demand forecasting for procurement. On public datasets with
corrected, held-out evaluation, the defect detector (MobileNetV2) reaches
99.39% ± 0.24 test accuracy at 2.4 ms per image on CPU via ONNX Runtime; the
tool-wear model attains R² = 0.545 on tools unseen in training, doubling a
linear baseline; and the demand forecaster reaches 19.7% WAPE, beating naïve
(25.7%) and Prophet (30.4%) baselines. The central contribution is not a new
algorithm but an honest, reproducible integration tailored to an under-served
context, with a vernacular accessibility layer that, to our knowledge, no
existing Indian MSME quality tool provides.

**Keywords:** edge AI, defect detection, predictive maintenance, demand
forecasting, MSME manufacturing, vernacular NLP, Industry 4.0.

---

## I. Introduction

Indian MSMEs contribute a large share of manufacturing output and employment,
but adopt advanced quality and analytics tooling far less than large firms
[MSME-report], [Mittal2018]. Three barriers recur on the shop floor of a
typical CNC-machining or metal-casting MSME. First, **cost**: enterprise
vision-inspection systems are priced well beyond a small shop's budget.
Second, **language**: their interfaces assume English literacy, whereas many
machine operators read and act more reliably in Hindi or a regional language.
Third, **connectivity**: they assume dependable cloud access, which many
shops lack. The consequence is that defects are caught late, machines fail
without warning, and raw-material inventory is planned by intuition.

Drishti-AI ("drishti" — vision) targets these barriers directly with an
integrated, offline platform. Rather than a single model, it couples four
capabilities that a small shop would otherwise have to buy as separate
systems, and unifies them in one dashboard with a transparent ROI view.

**Contributions.**
1. An integrated, fully-offline architecture spanning quality inspection,
   worker-facing vernacular alerts, predictive maintenance, and demand
   forecasting, runnable on commodity hardware (a laptop and a USB webcam).
2. A **template-based Hindi alert layer** that converts model output into a
   plain-language instruction and corrective action — a zero-hallucination
   design chosen deliberately for a safety-relevant "reject this part"
   message. To our knowledge no existing Indian MSME quality tool pairs
   vision inspection with such a vernacular layer.
3. A **rigorous, reproducible evaluation** across four public datasets: a
   proper held-out split with multi-seed reporting for vision, a by-tool split
   for maintenance, and time-series cross-validation with prediction intervals
   and an ablation for forecasting — each compared against baselines.
4. An open dashboard integrating the modules, and a full reproducibility
   package (pinned dependencies, seeds, commands).

We are explicit throughout that this is a proof-of-concept validated on public
data, not a field-deployed product (Section IX).

---

## II. Related Work

**Surface-defect detection.** Deep CNNs are now standard for visual surface
inspection [Bhatt2021], [Tabernik2020], with lightweight backbones such as
MobileNet [Sandler2018], [Howard2017] enabling on-device inference. Public
benchmarks include the NEU steel-surface database [Song2013] and casting
datasets [Dabhi2020]. Our contribution is not a new detector but its honest
evaluation and integration into a worker-facing, offline pipeline.

**Predictive maintenance and RUL.** Data-driven prognostics for machine health
are surveyed in [Lei2018], [Carvalho2019], [Zhao2019], typically extracting
time/frequency-domain features from vibration or current signals and
regressing remaining useful life. We follow this pattern with FFT/wavelet
features and gradient boosting [Chen2016], emphasising a by-tool split.

**Demand forecasting.** Classical decomposition models such as Prophet
[Taylor2018] compete with lag-feature machine-learning approaches; large-scale
competitions [Makridakis2020] found gradient-boosted trees on lag features
frequently competitive or superior on retail/industrial series. We adopt
XGBoost with lag features and report WAPE [Hyndman2006].

**Edge AI and Indic NLP.** Efficient on-device inference is enabled by
portable runtimes such as ONNX [ONNX] and TinyML tooling [Warden2019]. For the
vernacular layer, open Indic translation resources [Gala2023], [Kakwani2020]
would enable expansion beyond hand-written Hindi templates. Existing Industry
4.0 SME studies [Frank2019], [Mittal2018] motivate low-cost, accessible
tooling but do not provide an integrated, vernacular, offline system of the
kind proposed here.

---

## III. System Architecture

Drishti-AI comprises three parallel pipelines that converge on one dashboard.
The **quality pipeline** captures a part image, classifies pass/fail
(Module 1), and renders a Hindi alert (Module 2) for the operator. The
**uptime pipeline** ingests vibration/current sensor windows and predicts
remaining tool life (Module 3). The **inventory pipeline** ingests historical
order data and forecasts weekly demand per category (Module 4). Each module
emits events into a shared schema — a timestamp, a module id, an event type
(inspection / maintenance_alert / forecast), and a module-specific payload —
which the dashboard aggregates for management, alongside a transparent ROI
calculator. The laptop itself serves as the edge device for the prototype; a
USB webcam supplies images, satisfying the offline, no-cloud requirement.

---

## IV. Module 1 — Edge Defect Detection

### A. Data and method
We use the PILOT TECHNOCAST casting dataset [Dabhi2020] (7,348 grayscale
images, two classes: `def_front` defective and `ok_front` good; 6,633 train /
715 test). The classifier is MobileNetV2 [Sandler2018] pretrained on ImageNet
[Deng2009], adapted by two-phase transfer learning: the classifier head is
trained for 15 epochs (Adam [Kingma2015], lr 1e-3) with the backbone frozen,
then the top blocks are fine-tuned for 5 epochs (lr 1e-5). Inputs are 224×224;
batch size 32.

**Evaluation methodology (corrected).** A common pitfall is selecting the model
checkpoint on the test set. We instead carve a stratified 15% **validation**
split from the training folder, select the best epoch on validation, and
evaluate the test folder exactly once. We report mean ± standard deviation
over three seeds.

### B. Results
Table I compares architectures on the same split. MobileNetV2 attains
**99.39% ± 0.24** test accuracy, statistically indistinguishable from a
ResNet-50 that is ~10× larger, and is preferred for its efficiency. A
from-scratch SimpleCNN also reaching 99.4% indicates the dataset is highly
separable; we therefore do not over-interpret absolute accuracy.

**Table I. Architecture comparison (test set, evaluated once).**
| Model | Params | Test Acc | Macro-F1 |
|---|---|---|---|
| MobileNetV2 (ours) | 2.23 M | 99.39% ± 0.24 (3 seeds) | 99.35% |
| ResNet-50 | 23.51 M | 99.72% (1 seed) | 99.70% |
| SimpleCNN (scratch) | 0.29 M | 99.44% (1 seed) | 99.40% |

**Table II. Per-class metrics (representative median seed, acc 99.30%).**
| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| def_front | 0.9956 | 0.9934 | 0.9945 | 453 |
| ok_front | 0.9886 | 0.9924 | 0.9905 | 262 |

The confusion matrix [[450, 3], [2, 260]] shows 2–5 missed defects (false
negatives) across seeds; because a missed defect is costlier than a false
alarm, this is discussed as a limitation (Section IX).

**Table III. Inference latency (batch=1; 30 warm-up, 300 timed runs).**
| Configuration | Mean | p95 |
|---|---|---|
| PyTorch, RTX 5060 GPU | 8.07 ms | 12.98 ms |
| PyTorch, CPU | 12.39 ms | 13.99 ms |
| ONNX Runtime, CPU (edge target) | 2.37 ms | 3.64 ms |

All configurations are far under the 2 s design target. Fig. 1 (Grad-CAM
[Selvaraju2017]) shows the network's decisive regions fall on the casting
surface/rim, not the background — evidence it keys on the part itself.

---

## V. Module 2 — Vernacular Alert Layer

Module 1's structured output `{pass_fail, defect_type, confidence}` is mapped
to a pre-written Hindi sentence template with variable slots, yielding a
label, a plain-language message, and a corrective action. We adopt templated
generation rather than a free-generating LLM by design: on a safety-relevant
"reject this part" message, zero hallucination risk outweighs generative
flexibility. Nine defect codes are covered, plus a small glossary of shop-floor
terms (e.g., burr, flank wear, tolerance) that lack a clean one-word Hindi
equivalent. The design is offline and deterministic; expansion to additional
Indian languages is incremental and could leverage open Indic MT [Gala2023].

---

## VI. Module 3 — Predictive Maintenance

### A. Data and method
We use an open CNC-milling wear dataset (14 tools tracked fresh-to-failure,
968 cycles). FFT and wavelet transforms convert raw vibration/current windows
into 125 time- and frequency-domain features, and an XGBoost regressor
[Chen2016] predicts the remaining-life fraction. Crucially, the split is
**by tool**: the model trains on 9 tools and is tested on 4 tools it has never
seen (2, 10, 101, 103). This measures cross-tool generalisation rather than
letting the model interpolate within a tool's own wear curve.

### B. Results
On the unseen tools, XGBoost roughly doubles the R² of a linear baseline and
far exceeds a constant-mean predictor (Table IV). The modest absolute R² is
honest for cross-tool generalisation, which is genuinely hard.

**Table IV. RUL prediction on unseen tools.**
| Model | RMSE | MAE | R² |
|---|---|---|---|
| Constant mean (no-skill) | 0.296 | 0.256 | −0.00 |
| Linear regression | 0.253 | 0.194 | 0.265 |
| XGBoost (ours) | 0.199 | 0.160 | 0.545 |

Live operation is demonstrated by a replay simulator that streams the static
dataset row-by-row; we describe this as simulated, not live capture.

---

## VII. Module 4 — Demand Forecasting

### A. Data and method
We use a public product-demand dataset (~1.05M orders, 2,160 products,
2011–2017), aggregated into weekly totals per product category (28 categories
with sufficient history). An XGBoost regressor predicts next-week demand from
18 features: lags (including a 52-week yearly lag), rolling means/std, an
exponentially-weighted average, short-term trend, and a cyclical week-of-year
encoding. Because weekly demand spans ~40 to ~25M units across categories, we
regress a signed-log target so a 10× swing is weighted comparably at every
scale. An ablation (Table V) drove two non-obvious choices: early stopping
hurt (its validation window was unrepresentative) and adding the category id
as a feature slightly hurt; both were dropped. Paired quantile models provide
an 80% (P10–P90) prediction interval.

**Table V. Module 4 ablation (held-out WAPE).**
| Configuration | WAPE |
|---|---|
| Base features, fixed trees | 20.5% |
| + category feature | 20.6% |
| + early stopping | 25.7% |
| + extra features (final) | 19.5% |

### B. Results
Evaluated on the 52 weeks after the training cutoff, the model attains 19.7%
WAPE, R² 0.944, and 20.6% mean WAPE under 3-fold expanding-window
cross-validation. It beats every baseline including Prophet (Table VI) — a
~23% relative improvement over naïve — indicating it captures real structure
rather than echoing recent values. The 80% interval covered 74% of actuals,
slightly under-calibrated and reported as such.

**Table VI. Forecast comparison (held-out 52 weeks, WAPE).**
| Forecaster | WAPE |
|---|---|
| Prophet | 30.4% |
| Seasonal-naïve (52-week) | 27.8% |
| Naïve (last value) | 25.7% |
| XGBoost (ours) | 19.7% |

---

## VIII. Integrated Dashboard

A React dashboard unifies the modules into five views — overview KPIs, a
quality-inspection log with the paired Hindi alert, per-tool remaining-life
charts, per-category forecasts with the prediction-interval band, and a
transparent ROI calculator. It is a static client-side application reading one
aggregated data file, so it runs offline and is trivially shareable.

---

## IX. Discussion, Limitations and Threats to Validity

Our results support the central claim — that a low-cost, offline, vernacular
platform can deliver useful quality, uptime and inventory intelligence — but
several limitations bound the claim and are stated plainly.

- **Public data, no pilot.** All modules are trained and validated on public
  datasets, not a real shop's data; no sensor hardware, camera rig, or
  factory pilot is involved. Reported numbers are not field-validated.
- **Dataset difficulty.** The casting task is highly separable (a scratch CNN
  reaches 99.4%); absolute accuracy should not be read as evidence of a hard
  problem solved. The datasets are castings and steel, not CNC-milled parts.
- **Error asymmetry.** The detector misses 2–5 defects per test run; a missed
  defect is the costly error and would require a recall-oriented threshold in
  deployment.
- **Scope.** Only surface/visual defects are addressed; dimensional/tolerance
  inspection needs calibrated measurement, out of scope here.
- **Baseline coverage.** Module 1 baselines and the Module 4 model are
  single-seed; multi-seed would tighten those comparisons.
- **Forecast data boundary.** The demand dataset's final week appears
  truncated, which can distort the first forecast step; documented, not
  patched.
- **ROI figures are projections**, not measured savings.

---

## X. Conclusion and Future Work

Drishti-AI shows that four Industry-4.0 capabilities can be integrated into a
single offline, low-cost, vernacular system aimed squarely at Indian MSME
machine shops, with honest and reproducible results on public data. Future
work includes: a real pilot with camera/lighting calibration and labelled
shop data; live webcam capture and an automated data pipeline; multi-class
defect typing and additional regional languages via open Indic MT; and
recall-oriented thresholding for the safety-critical defect case.

---

## References
> Verify each entry's exact authors/venue/DOI before submission.

[Sandler2018] M. Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks," CVPR, 2018.
[Howard2017] A. G. Howard et al., "MobileNets: Efficient CNNs for Mobile Vision Applications," arXiv:1704.04861, 2017.
[Deng2009] J. Deng et al., "ImageNet: A Large-Scale Hierarchical Image Database," CVPR, 2009.
[Kingma2015] D. P. Kingma and J. Ba, "Adam: A Method for Stochastic Optimization," ICLR, 2015.
[Selvaraju2017] R. R. Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks," ICCV, 2017.
[Song2013] K. Song and Y. Yan, "A noise robust method for surface defects of hot-rolled steel strip (NEU)," Applied Surface Science, 2013.
[Tabernik2020] D. Tabernik et al., "Segmentation-based deep-learning approach for surface-defect detection," J. Intelligent Manufacturing, 2020.
[Bhatt2021] P. M. Bhatt et al., "Image-based surface defect detection using deep learning: A review," JCISE, 2021.
[Dabhi2020] R. Dabhi, "Casting Product Image Data for Quality Inspection," Kaggle, 2020.
[Lei2018] Y. Lei et al., "Machinery health prognostics: A systematic review," MSSP, 2018.
[Carvalho2019] T. P. Carvalho et al., "A systematic literature review of ML methods for predictive maintenance," Computers & Industrial Engineering, 2019.
[Zhao2019] R. Zhao et al., "Deep learning and its applications to machine health monitoring," MSSP, 2019.
[Chen2016] T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," KDD, 2016.
[Taylor2018] S. J. Taylor and B. Letham, "Forecasting at Scale (Prophet)," The American Statistician, 2018.
[Hyndman2006] R. J. Hyndman and A. B. Koehler, "Another look at measures of forecast accuracy," Int. J. Forecasting, 2006.
[Makridakis2020] S. Makridakis et al., "The M4 Competition," Int. J. Forecasting, 2020.
[ONNX] J. Bai et al., "ONNX: Open Neural Network Exchange," 2019.
[Warden2019] P. Warden and D. Situnayake, "TinyML," O'Reilly, 2019.
[Gala2023] J. Gala et al., "IndicTrans2: MT for all 22 Scheduled Indian Languages," TMLR / arXiv:2305.16307, 2023.
[Kakwani2020] D. Kakwani et al., "IndicNLPSuite / AI4Bharat," Findings of EMNLP, 2020.
[Frank2019] A. G. Frank et al., "Industry 4.0 technologies: Implementation patterns," Int. J. Production Economics, 2019.
[Mittal2018] S. Mittal et al., "Smart manufacturing for SMEs," Proc. IMechE Part B, 2018.
[MSME-report] Government of India, "MSME Annual Report" (cite the specific year used).
