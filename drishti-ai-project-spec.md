# Drishti-AI — Complete Project Specification

**How to use this document:** This is the full, self-contained context for the Drishti-AI project, written to be loaded directly into Claude Code as project context. It assumes zero prior conversation history — everything decided, tested, or ruled out so far is captured here. Read Section 11 (Honesty & Scope Boundaries) before writing any claims into code comments, READMEs, or UI copy generated for this project.

**Submission deadline:** MSME Idea Hackathon 6.0, July 14, 2026 — idea-stage only (5 text fields + 1 architecture diagram, no code/demo required this round). Everything in this document is for the actual build, which is a separate, personal-learning track running in parallel.

---

## 1. Project Overview

**Name:** Drishti-AI ("Drishti" = Hindi/Sanskrit for vision/sight)

**One-line description:** A unified AI platform for Indian MSME (micro, small, medium enterprise) manufacturers — starting with CNC machining and casting shops — that bundles computer-vision defect detection, a vernacular-language alert layer, predictive maintenance, and demand forecasting into one system with one shared dashboard.

**Problem:** Small Indian manufacturing shops can't afford enterprise QC/vision-inspection systems (Cognex, Keyence — ₹5–15L+), which also run English-only interfaces and assume constant cloud connectivity. Defects get caught late, machines fail without warning, and inventory is managed by gut feel.

**Target user, primary:** CNC machining and metal-casting MSMEs in India (example clusters: Rajkot, Coimbatore, Ludhiana, Pune).

**Core differentiator:** the vernacular AI alert layer — no existing Indian QC tool pairs vision inspection with a Hindi/regional-language accessibility layer built for actual shop-floor workers, and none are priced for MSME budgets.

**Architecture at a glance:**

```
 CNC Part/Casting   Vibration/Current      Historical
      |             Sensor Data            Order Data
      v                   |                     |
 Camera Capture            v                     v
      |              MODULE 3:              MODULE 4:
      v              Predictive             Demand
 MODULE 1:            Maintenance           Forecasting
 Edge CV Defect         |                     |
 Detection              |                     |
      |                 |                     |
      v                 |                     |
 MODULE 2:              |                     |
 Vernacular AI          |                     |
 Alert Layer            |                     |
      |------------------\                   /
      |                   v                 v
      v              CENTRAL DASHBOARD <----'
 Shop-Floor              |
 Worker                  v
                    Shop Owner /
                    Management
```

All four modules are co-equal parts of one platform. Modules 1+2 and Module 3 and Module 4 are three parallel pipelines that converge on one dashboard. There is no "core vs. future" distinction in how this is pitched — see Section 10 for the internal build order, which is a separate, private decision.

---

## 2. Hackathon Submission — Final Field Text (reference only)

Included so Claude Code never contradicts the pitch language already submitted.

**Title:** Drishti-AI: A Vernacular AI Intelligence Platform for MSME Manufacturing

**Concept & Objective (submitted):**
> Objective: enable India's MSME machine shops to catch defects at the point of production, predict machine downtime before it happens, plan raw-material inventory intelligently, and make every insight usable by shop-floor workers regardless of English literacy — replacing four separate problems with one integrated system.
>
> Concept: a camera captures the finished part; an edge-deployed CNN (MobileNetV2, exported to TFLite/ONNX) classifies pass/fail and defect type in under 2 seconds, fully offline (Module 1). A vernacular AI layer converts this into a plain-language Hindi/regional-language alert and corrective action for the worker, not a raw error code (Module 2). In parallel, a predictive-maintenance module reads vibration/current sensor data through an LSTM/XGBoost pipeline to flag tool wear before failure (Module 3), and a demand-forecasting module applies XGBoost/Prophet to order history for raw-material and consumable planning (Module 4). All four feed one central dashboard, giving the shop owner a single view across quality, uptime, and inventory.

**Impact targets quoted in the submission** (treat as design targets to validate against, not proven results — see Section 11):
- 20–30% reduction in defect/rejection rate
- <2 second inference per part, fully offline
- ~1/10th the cost of enterprise vision-inspection systems

---

## 3. Module 1 — Edge CV Defect Detection (flagship, build first)

**Objective:** classify a photographed part as pass/fail and identify defect type (surface scratch, burr, tool mark, pitted surface, etc.), running fully offline on an edge device.

**Datasets (both confirmed live, use both — casting first):**

| Dataset | Source | Size | Notes |
|---|---|---|---|
| Casting defect dataset | https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product | 7,348 images (512×512, grayscale), pre-split train/test, `def_front`/`ok_front` folders | Real data from PILOT TECHNOCAST, a Rajkot (Gujarat) foundry — genuinely Indian, genuinely industrial. Use this as the primary dataset; it's the strongest "indigenous" story. |
| NEU Surface Defect Database | https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database | 1,800 grayscale images, 200×200px, 6 classes (crazing, inclusion, patches, pitted surface, rolled-in scale, scratches), 300/class | Steel strip defects, not castings — use as a secondary/auxiliary dataset or for a multi-class defect-type demo beyond pass/fail. |

**Known domain-mismatch limitation (state this honestly in any README/report):** neither dataset is CNC-turned/milled parts — one is castings, one is steel strips. The model proves the *detection approach* works, not that it's validated on CNC-specific defect types yet.

**Scope limitation:** dimensional/tolerance deviation (out-of-spec diameter, depth) cannot be solved by image classification alone — that needs calibrated measurement (reference markers, stereo vision, or a laser scan). Keep Module 1's claim to surface/visual defects only.

**Model architecture:**
- Backbone: MobileNetV2, ImageNet-pretrained, transfer learning (freeze base layers initially, fine-tune top layers)
- Framework: PyTorch (see Section 9 for why — not TensorFlow, given the Windows GPU situation)
- Input: 224×224 (standard MobileNetV2 input; can go larger given GPU headroom — test 224 first, scale up if accuracy is the bottleneck rather than data)
- Output head: binary (pass/fail) or multi-class (defect type) depending on which dataset/labels used
- Export: to ONNX first (native PyTorch export), then ONNX → TFLite if TFLite specifically is needed for the edge-device target

**Training environment:** the user's laptop — Lenovo LOQ 15AHP10, RTX 5060 Laptop GPU (8GB VRAM). See Section 9 for the exact PyTorch install command; this is not optional, a plain `pip install torch` can silently produce a CPU-only or incompatible build on this GPU generation.

**Deliverable:** a trained `.onnx` (and optionally `.tflite`) model file, a evaluation script reporting accuracy/precision/recall/confusion matrix on the held-out test split, and an inference script that takes an image path and returns `{pass_fail, defect_type, confidence}` as JSON.

---

## 4. Module 2 — Vernacular AI Alert Layer (flagship, build second)

**Objective:** convert Module 1's structured output (`{pass_fail, defect_type, confidence}`) into a plain-language alert and corrective action in Hindi or another regional language, understandable by a shop-floor worker with no English literacy.

**Approach — templated generation over free generation (deliberate choice, not a fallback):** map each defect type to a pre-written Hindi sentence template with variable slots (confidence, part ID, etc.), rather than a free-generating LLM. This is a **better** engineering choice for this use case, not a compromise — zero hallucination risk on a "reject this part" safety-relevant message matters more than generative flexibility here.

**Tools/options, in order of preference:**
1. **Pure template lookup** (Python dict mapping `defect_type` → Hindi sentence template) — simplest, zero dependency, zero risk, start here.
2. **AI4Bharat IndicTrans2** (https://ai4bharat.iitm.ac.in/ — open translation models covering all 22 Indian languages) — if the template approach needs to scale to many more languages/phrasings than are worth hand-writing, use this to translate English templates into additional regional languages, not to generate the alert text itself.
3. **Sarvam AI APIs** (translation/speech services) — paid, internet-dependent, only consider if offline operation is explicitly relaxed for this module.

**Given the RTX 5060 (8GB VRAM):** a 4-bit quantized 7–8B parameter local Indic LLM would fit comfortably if free-generation is ever wanted for a richer feature (e.g., a conversational Q&A layer for workers) — but this is explicitly out of scope for the core alert function, which should stay templated for reliability.

**Known gap:** technical shop-floor vocabulary (burr, flank wear, tolerance) doesn't always have a clean one-word Hindi equivalent — build a small custom glossary rather than relying on generic MT for these terms.

**Deliverable:** a function `generate_alert(defect_code, confidence, language='hi') -> str` returning a natural-language alert string, plus a small glossary/template file (JSON or YAML) that's easy to extend to more languages later.

---

## 5. Module 3 — Predictive Maintenance (stretch, build third)

**Objective:** predict tool wear or impending failure from vibration/current sensor signals, before the failure happens.

**Datasets, in order of preference:**

| Dataset | Source | Notes |
|---|---|---|
| A 2025 open milling dataset | Paper: https://www.nature.com/articles/s41597-025-04923-y | Vibration + current data for 14 cutting tools, tracked from initial state to failure, 968 milling cycles on 42CrMo4 material. Real, recent, matches the "vibration/current sensor" framing exactly. Dataset repository link is in the paper — check its data-availability section. **Preferred first choice.** |
| PHM 2010 CNC milling dataset | IEEE DataPort: https://ieee-dataport.org/documents/2010-phm-society-conference-data-challenge (also referenced as available on Kaggle — search "PHM 2010 milling data challenge" to confirm current Kaggle mirror) | Real remaining-useful-life data: dynamometer force, accelerometer vibration, acoustic emission signals from an actual CNC milling cutter. CC0 licensed per secondary sources. **Second choice**, well-established in the literature. |
| AI4I 2020 Predictive Maintenance Dataset | UCI: https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset (CC BY 4.0) | 10,000 samples, 5 failure modes, only 3.4% failure rate. **Synthetic, not real sensor data** — tabular (temperature/speed/torque/tool-wear), not raw signal. Usable as a quick tabular-ML warm-up, but see the caveat below before quoting any result from it. |

**Critical honesty caveat — do not skip this:** published results on AI4I 2020 routinely show F1-scores exceeding 0.995 across nearly every model tried, which researchers attribute to the dataset's unusual cleanliness rather than real-world difficulty. **Never report or imply a >99% accuracy figure from this dataset in any README, pitch material, or demo** — to anyone who knows this dataset, that reads as a red flag, not a strength.

**Model approach:**
- Raw-signal datasets (2025 dataset, PHM2010) need feature extraction first — FFT/wavelet transforms on the vibration/current signal windows — before any model sees them. This is real signal-processing work, not optional preprocessing.
- Feature-extracted data → gradient boosting (XGBoost/LightGBM) is the fastest path to a working model; an LSTM on raw/windowed sequences is a valid stretch goal given GPU availability, but start with gradient boosting.
- **"Live sensor streaming" claim:** build a replay script that feeds the static dataset row-by-row into whatever consumes it (dashboard, alert layer), simulating real-time input. This is standard practice for this kind of prototype — always describe it as *simulated* replay in any documentation, never as live capture.

**Deliverable:** feature-extraction script, trained model file, evaluation script (report RMSE/accuracy honestly per the caveat above), and the streaming-replay simulator script.

---

## 6. Module 4 — Demand/Inventory Forecasting (stretch, build fourth)

**Objective:** forecast raw-material/consumable demand from historical order data, to reduce overstock/understock.

**Datasets:**

| Dataset | Source | Notes |
|---|---|---|
| Product demand dataset (manufacturing-sourced) | https://www.kaggle.com/datasets/felixzhao/productdemandforecasting | Thousands of products, warehouse/category structure — sourced from a real manufacturing/distribution company. **Preferred** — better domain match than pure retail. |
| Store Item Demand Forecasting Challenge | https://www.kaggle.com/competitions/demand-forecasting-kernels-only | 10 stores × 50 items, ~913,000 daily rows over 5 years. Clean and well-documented, but retail, not manufacturing — use only if the above doesn't fit well, and frame results as "adaptable to procurement," not manufacturing-native. |

**Model approach:** XGBoost or Prophet on the time-series; this is the lightest-weight module technically (tabular/time-series, fully CPU-friendly, no GPU needed) — don't over-invest build time here relative to Modules 1–2.

**Deliverable:** trained forecasting model, evaluation script (MAPE/RMSE), and a simple forecast-query function.

---

## 7. Central Dashboard + Integration

**Purpose:** unify outputs from all four modules into one view — inspection logs and defect trends (Module 1/2), tool-wear/downtime alerts (Module 3), inventory/demand forecasts (Module 4) — plus an ROI calculator.

**Suggested schema (single source of truth all modules write to):**
```json
{
  "timestamp": "ISO8601",
  "module": "1|2|3|4",
  "event_type": "inspection|maintenance_alert|forecast",
  "payload": { "...module-specific fields..." }
}
```

**Suggested tech:** Streamlit is the fastest path given the ML stack is already Python-heavy (all four modules are Python/PyTorch/XGBoost) — avoids a second language/build system just for the UI. React is a valid alternative if a more polished/interactive UI matters more than build speed; the user has prior React + Claude API experience from an earlier project (a Tata Stock Predictor tool), so React is a comfortable fallback if Streamlit feels too limited.

**ROI calculator logic (minimum viable version):** `monthly_savings = (baseline_rejection_rate - projected_rejection_rate) * parts_per_month * cost_per_reworked_part`, plus a simple manual-inspector-hours-saved estimate. Keep this simple and transparent — a judge or user should be able to see exactly how the number was derived.

---

## 8. Design Targets vs. Validated Results (do not conflate these)

The submission quotes 20–30% defect reduction, <2 sec inference, ~1/10th enterprise cost. These are **design targets**, not measured outcomes. As each module is built:
- Report actual measured metrics on the datasets used (accuracy, F1, RMSE, MAPE, inference latency — measured, not estimated)
- Keep the 20–30%/cost claims labeled as projections in any generated documentation until there's real data to test them against
- Never let a generated README or report imply these targets have been achieved by the prototype

---

## 9. Development Environment

**Machine:** Lenovo LOQ 15AHP10 (Gen 10)
- CPU: AMD Ryzen 7 250 — 8 cores / 16 threads, up to 5.1GHz, Zen 4
- GPU: NVIDIA GeForce RTX 5060 Laptop — Blackwell architecture, 8GB GDDR7 VRAM, 3328 CUDA cores, compute capability sm_120
- RAM: 24GB (per user's configuration)
- Storage: 1TB SSD
- OS: Windows 11 Home

**Critical install step — PyTorch (do this exactly, do not `pip install torch` plain):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```
Stable PyTorch only added proper native support for this GPU's compute capability (sm_120 / Blackwell) starting at version 2.7.0, shipping prebuilt CUDA 12.8 wheels. A plain `pip install torch` can silently grab an older/incompatible build that falls back to CPU or throws a "no kernel image is available for execution on the device" error. Verify after install:
```python
import torch
print(torch.cuda.is_available(), torch.cuda.get_device_name(0))
```

**Do not use TensorFlow on native Windows for GPU training.** TensorFlow 2.10 was the last release with native-Windows GPU support; 2.11+ requires WSL2. Since this project needs TFLite only as an *export* target (not for training), the plan is: train in PyTorch (native Windows CUDA works fine) → export to ONNX → convert ONNX to TFLite only if the edge deployment target specifically requires the `.tflite` format. This avoids WSL2 entirely.

**Recommended Python version:** 3.10–3.12 (broad compatibility with all libraries below; avoid 3.13 unless specifically verifying support for each package first).

**Core libraries by module:**
- Module 1: `torch`, `torchvision`, `onnx`, `onnxruntime`, `pillow`, `opencv-python` (for camera capture code later), `scikit-learn` (metrics)
- Module 2: no ML framework required for the templated approach; `transformers` + `sentencepiece` only if IndicTrans2 is brought in
- Module 3: `numpy`, `scipy` (signal processing / FFT), `xgboost`, `scikit-learn`, optionally `torch` if an LSTM is attempted
- Module 4: `pandas`, `xgboost`, `prophet` (or `statsmodels` as a lighter alternative)
- Dashboard: `streamlit`, `pandas`, `plotly` (or the React alternative noted in Section 7)

---

## 10. Build Sequence (internal — do not surface this as "phases" in any pitch material)

This is purely an engineering sequencing decision based on realistic time and learning-curve constraints. It has no bearing on how the idea is described anywhere in the submission (see Section 1) — all four modules are one platform in every pitch-facing document.

1. **Module 1** (CV defect detection) — highest visual payoff, proves the core technical approach
2. **Module 2** (vernacular alert layer) — wires directly into Module 1's output, the key differentiator
3. **Module 3** (predictive maintenance) — independent pipeline, fully CPU-friendly, straightforward once 1+2 are solid
4. **Module 4** (demand forecasting) — lightest lift, do last
5. **Dashboard + integration** — after at least two modules produce real output to integrate

---

## 11. Honesty & Scope Boundaries — read before generating any documentation, README, or pitch copy

These constraints have been established and re-confirmed multiple times during scoping. They apply to any code comments, generated docs, or user-facing text this project produces:

- **All four modules are trained/validated on public or synthetic datasets, not the user's own shop's real-world data.** This is a proof-of-concept stage, explicitly framed as such — never claim "production-validated" or "field-tested" anywhere.
- **No real sensor hardware, camera rig, or edge device has been deployed or calibrated.** Any "live" or "real-time" language in docs must be clearly labeled as simulated (see Module 3's streaming replay).
- **Dimensional/tolerance defect detection is out of scope** for the current image-classification approach — only surface/visual defects are claimed.
- **AI4I 2020 accuracy figures are not to be quoted as evidence of real-world performance** — see Section 5's caveat.
- **No real-world accuracy, ROI, or cost-savings figure has been independently validated** — the 20–30%/<2sec/~10x-cheaper figures are design targets (Section 8), not measured results.
- **Data labeling at scale, physical camera/lighting calibration, and field testing are explicitly out of scope** for this build — they require a real pilot shop partnership, not something achievable in a coding session.
- Camera/edge-device integration code (Section 3, Module 1 deployment) uses a standard USB webcam via OpenCV, with the laptop itself serving as the "edge device" for the prototype stage — see Section 13. This genuinely satisfies the "offline, no cloud dependency" claim; a dedicated industrial camera or standalone board (Raspberry Pi/Jetson) is a later physical-deployment upgrade, not a prerequisite for building or testing Module 1.

---

## 12. Timeline

- **July 8–9, 2026:** hackathon submission finalized and filed (idea-stage only — 5 text fields + architecture diagram, both complete as of this document)
- **July 9 onward:** environment setup (Section 9) + Module 1 build begins
- Modules 2–4 and dashboard integration follow per Section 10's sequence, at whatever pace fits — nothing after the July 14 submission is deadline-critical, since the hackathon round itself required no code

---

## 13. Open Decisions / Inputs Still Needed

- ~~Camera/edge device model~~ — **RESOLVED:** standard USB webcam (or the laptop's built-in camera) via OpenCV `cv2.VideoCapture()`; the laptop itself is the "edge device" for the prototype stage. A dedicated industrial camera or standalone board (Raspberry Pi 4/5, ~$50–80, or an NVIDIA Jetson for more compute) is a future upgrade for a standalone demo unit, not a blocker for Module 1 now.
- **Target regional languages beyond Hindi** for Module 2 — not yet specified; templated approach makes adding languages incremental, so this can be decided later without a redesign.
- **Which defect classes to prioritize first** within Module 1 (pass/fail only vs. multi-class defect typing) — recommend starting with binary pass/fail on the casting dataset (simpler, faster to a working result), then extending to multi-class defect typing once that's solid.

---

## 14. Quick Reference — All Dataset & Resource URLs

| Resource | URL |
|---|---|
| Casting defect dataset | https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product |
| NEU Surface Defect Database | https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database |
| 2025 open milling dataset (paper) | https://www.nature.com/articles/s41597-025-04923-y |
| PHM 2010 CNC milling dataset | https://ieee-dataport.org/documents/2010-phm-society-conference-data-challenge |
| AI4I 2020 Predictive Maintenance | https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset |
| Product demand (manufacturing) | https://www.kaggle.com/datasets/felixzhao/productdemandforecasting |
| Store Item Demand Forecasting | https://www.kaggle.com/competitions/demand-forecasting-kernels-only |
| AI4Bharat (IndicTrans2 home) | https://ai4bharat.iitm.ac.in/ |
| PyTorch CUDA 12.8 wheels | https://download.pytorch.org/whl/cu128 |

---

*End of specification. This document is intended to be loaded as project context in Claude Code; it reflects every technical and framing decision made during the planning phase of Drishti-AI as of July 8, 2026.*
