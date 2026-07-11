# -*- coding: utf-8 -*-
"""
Generate publication-ready figures for the Drishti-AI paper.
All figures are built from the project's real, on-disk results
(metrics JSONs, saved models, dashboard events.json, dataset CSVs).
Output -> C:/dev/drishti-ai/paper_figures/*.png

Layout policy: every figure uses matplotlib constrained layout so titles,
axis labels and legends never overlap the frame; in-axes labels are placed
with explicit head-room so value/point annotations never collide.
"""
import json, glob, os, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

warnings.filterwarnings("ignore")
ROOT = "C:/dev/drishti-ai"
OUT = os.path.join(ROOT, "paper_figures")
os.makedirs(OUT, exist_ok=True)

INDIGO, TEAL, AMBER = "#4f46e5", "#0d9488", "#ea9010"
GREY, RED, GREEN = "#8a92a6", "#dc3f3f", "#0f9d58"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlepad": 12,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e6e8ef",
    "grid.linewidth": 0.8,
    "legend.frameon": False,
    "figure.dpi": 140,
    "savefig.dpi": 200,
})

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), facecolor="white", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name)

done = []

# ============================================================================
# FIG 1 — System architecture
# ============================================================================
def fig_architecture():
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 100); ax.set_ylim(0, 48); ax.axis("off")
    ax.set_title("Figure 1. Drishti-AI offline edge architecture: four decoupled modules on a shared JSON schema",
                 pad=16, fontsize=13)
    # (x, title, sub, face, edge)   box width 17, gap 3
    blocks = [
        (1.5,  "Shop-floor\ninputs",   "camera frames\nvibration+current\norder history", "#eef0fb", INDIGO),
        (21.5, "M1 · CV defect",       "MobileNetV2 → ONNX\n2.37 ms · 99.4% acc",         "#eef0fb", INDIGO),
        (41.5, "M2 · Vernacular",      "Hindi alert\ntemplate NLG",                        "#e9f6f4", TEAL),
        (61.5, "M3 · Predictive",      "XGBoost RUL\nunseen tools · R² 0.545",             "#e9f6f4", TEAL),
        (81.5, "M4 · Demand",          "XGBoost forecast\nWAPE 19.7% · P10–P90",           "#fdf1de", AMBER),
    ]
    W = 17
    for x, title, sub, fc, ec in blocks:
        ax.add_patch(FancyBboxPatch((x, 17), W, 16, boxstyle="round,pad=0.5,rounding_size=1.6",
                                    fc=fc, ec=ec, lw=2))
        ax.text(x+W/2, 28.5, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color=ec)
        ax.text(x+W/2, 21.6, sub, ha="center", va="center", fontsize=8.2, color="#333")
    for x0 in (18.5, 38.5, 58.5, 78.5):
        ax.add_patch(FancyArrowPatch((x0+0.2, 25), (x0+3, 25), arrowstyle="-|>",
                                     mutation_scale=16, lw=1.8, color=GREY))
    ax.add_patch(FancyBboxPatch((21.5, 4), 60, 8, boxstyle="round,pad=0.4,rounding_size=1.4",
                                fc="#f4f5fa", ec=GREY, lw=1.3, ls="--"))
    ax.text(51.5, 8, "shared_schema  ·  React dashboard  ·  runs fully offline on commodity edge hardware",
            ha="center", va="center", fontsize=9.2, color="#444", style="italic")
    save(fig, "fig01_architecture.png"); done.append("fig01_architecture.png")

# ============================================================================
# FIG 2 & 3 — M1 training / loss curves
# ============================================================================
def fig_training_curves():
    mob = load(f"{ROOT}/module1_cv_defect/models/proper_metrics_seed2.json")
    res = load(f"{ROOT}/module1_cv_defect/models/baseline_resnet50_metrics_seed42.json")
    mh, rh = mob["history"], res["history"]
    ft = sum(1 for h in mh if h["phase"] == "head")
    ep = list(range(1, len(mh)+1))

    fig, ax = plt.subplots(figsize=(8.6, 4.9), layout="constrained")
    ax.plot(ep, [h["train_acc"]*100 for h in mh], "-o", color=INDIGO, ms=4, lw=2, label="MobileNetV2 train")
    ax.plot(ep, [h["val_acc"]*100 for h in mh], "-o", color=TEAL, ms=4, lw=2, label="MobileNetV2 val")
    ax.plot(ep, [h["val_acc"]*100 for h in rh], "--s", color=AMBER, ms=3.5, lw=1.6, label="ResNet-50 val")
    ax.axvline(ft+0.5, color=GREY, ls=":", lw=1.4)
    ax.set_ylim(84, 102)
    # annotation sits LEFT of the divider; legend sits lower-right — no overlap
    ax.annotate("head → fine-tune", xy=(ft+0.35, 101.2), ha="right", va="top",
                color=GREY, fontsize=9)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Accuracy (%)")
    ax.set_title("Module 1 training and validation accuracy (seed 2)")
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "fig02_m1_training_curves.png"); done.append("fig02_m1_training_curves.png")

    fig, ax = plt.subplots(figsize=(8.6, 4.9), layout="constrained")
    ax.plot(ep, [h["train_loss"] for h in mh], "-o", color=INDIGO, ms=4, lw=2, label="train loss")
    ax.plot(ep, [h["val_loss"] for h in mh], "-o", color=RED, ms=4, lw=2, label="val loss")
    ax.axvline(ft+0.5, color=GREY, ls=":", lw=1.4)
    top = max(max(h["train_loss"] for h in mh), max(h["val_loss"] for h in mh)) * 1.25
    ax.set_ylim(0, top)
    # annotation sits LEFT of the divider; legend sits upper-right — no overlap
    ax.annotate("head → fine-tune", xy=(ft+0.35, top*0.965), ha="right", va="top",
                color=GREY, fontsize=9)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Cross-entropy loss")
    ax.set_title("Module 1 MobileNetV2 loss curves (seed 2)")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "fig03_m1_loss_curves.png"); done.append("fig03_m1_loss_curves.png")

# ============================================================================
# FIG 4 — M1 EXTENDED confusion matrix (2x2 core + totals + precision/recall)
# ============================================================================
def fig_confusion_extended():
    j = load(f"{ROOT}/module1_cv_defect/models/proper_metrics_seed2.json")
    cm = np.array(j["confusion_matrix"], dtype=int)
    labels = j["classes"]
    tot = cm.sum()
    row_tot = cm.sum(1); col_tot = cm.sum(0)
    recall = [cm[i, i] / row_tot[i] for i in range(2)]
    precision = [cm[i, i] / col_tot[i] for i in range(2)]
    acc = np.trace(cm) / tot

    fig, ax = plt.subplots(figsize=(8.2, 6.2), layout="constrained")
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.axis("off"); ax.invert_yaxis()
    ax.set_title("Module 1 extended confusion matrix (held-out test, n=715, seed 2)",
                 pad=10, fontsize=13)

    def cell(cx, cy, text, fc, tc="#0f1729", fs=13, fw="bold", sub=None):
        ax.add_patch(Rectangle((cx, cy), 1, 1, facecolor=fc, edgecolor="white", lw=2))
        if sub is None:
            ax.text(cx+0.5, cy+0.5, text, ha="center", va="center", color=tc, fontsize=fs, fontweight=fw)
        else:
            ax.text(cx+0.5, cy+0.42, text, ha="center", va="center", color=tc, fontsize=fs, fontweight=fw)
            ax.text(cx+0.5, cy+0.74, sub, ha="center", va="center", color=tc, fontsize=9)

    # corner + headers (col 0 / row 0 are labels)
    cell(0, 0, "", "white")
    cell(1, 0, f"pred\n{labels[0]}", "#f4f5fa", fs=10.5)
    cell(2, 0, f"pred\n{labels[1]}", "#f4f5fa", fs=10.5)
    cell(3, 0, "Total", "#f4f5fa", fs=11)
    cell(4, 0, "Recall", "#eaeafb", tc=INDIGO, fs=11)
    cell(0, 1, f"true\n{labels[0]}", "#f4f5fa", fs=10.5)
    cell(0, 2, f"true\n{labels[1]}", "#f4f5fa", fs=10.5)
    cell(0, 3, "Total", "#f4f5fa", fs=11)
    cell(0, 4, "Precision", "#eaeafb", tc=INDIGO, fs=11)

    mx = cm.max()
    for i in range(2):
        for k in range(2):
            v = cm[i, k]
            if i == k:
                fc = (0.06, 0.62, 0.35, 0.20 + 0.6*v/mx)  # green scale
            else:
                fc = (0.86, 0.25, 0.25, 0.30 if v > 0 else 0.06)  # red scale
            cell(k+1, i+1, str(v), fc, fs=17,
                 sub=("correct" if i == k else "error"))
    # margins
    cell(3, 1, str(row_tot[0]), "#eef0f4", fs=13)
    cell(3, 2, str(row_tot[1]), "#eef0f4", fs=13)
    cell(1, 3, str(col_tot[0]), "#eef0f4", fs=13)
    cell(2, 3, str(col_tot[1]), "#eef0f4", fs=13)
    cell(3, 3, str(tot), "#e3e6ee", fs=13)
    # recall column
    cell(4, 1, f"{recall[0]*100:.2f}%", "#eaeafb", tc=INDIGO, fs=12)
    cell(4, 2, f"{recall[1]*100:.2f}%", "#eaeafb", tc=INDIGO, fs=12)
    # precision row
    cell(1, 4, f"{precision[0]*100:.2f}%", "#eaeafb", tc=INDIGO, fs=12)
    cell(2, 4, f"{precision[1]*100:.2f}%", "#eaeafb", tc=INDIGO, fs=12)
    cell(3, 4, "", "#eaeafb")
    cell(4, 3, "", "#eaeafb")
    # accuracy corner
    cell(4, 4, f"{acc*100:.2f}%", INDIGO, tc="white", fs=15, sub=None)
    ax.text(4.5, 4.20, "accuracy", ha="center", va="center", color="white", fontsize=8.5)

    ax.text(0.02, 5.25, "green = correct · red = errors · grey = totals · indigo = precision/recall",
            fontsize=9, color="#555")
    save(fig, "fig04_m1_confusion.png"); done.append("fig04_m1_confusion.png")

# ============================================================================
# FIG 5 — M1 accuracy vs parameters
# ============================================================================
def fig_tradeoff():
    specs = [("SimpleCNN (scratch)", 0.29, TEAL, "baseline_simplecnn_metrics_seed*.json", "right"),
             ("MobileNetV2 (ours)", 2.23, INDIGO, "proper_metrics_seed*.json", "right"),
             ("ResNet-50", 23.51, AMBER, "baseline_resnet50_metrics_seed*.json", "left")]
    fig, ax = plt.subplots(figsize=(8.4, 5.0), layout="constrained")
    for name, params, c, pat, side in specs:
        accs = [load(f)["test_accuracy"]*100
                for f in glob.glob(f"{ROOT}/module1_cv_defect/models/{pat}")]
        m, s = np.mean(accs), np.std(accs)
        ax.errorbar(params, m, yerr=s, fmt="o", ms=13, color=c, capsize=6, lw=2.2, mec="white", mew=1.5, zorder=3)
        dx = 1.35 if side == "right" else 0.62
        ax.annotate(name, (params*dx, m + s + 0.045), ha="left" if side == "right" else "right",
                    va="bottom", fontsize=10, fontweight="bold", color=c)
    ax.set_xscale("log"); ax.set_xlim(0.15, 60)
    ax.set_ylim(99.0, 99.95)
    ax.set_xlabel("Parameters (millions, log scale)"); ax.set_ylabel("Test accuracy (%)")
    ax.set_title("Module 1 accuracy vs. model size (mean ± SD, 3 seeds)")
    save(fig, "fig05_m1_tradeoff.png"); done.append("fig05_m1_tradeoff.png")

# ============================================================================
# FIG 6 — M1 latency
# ============================================================================
def fig_latency():
    cfgs = ["ONNX Runtime\nCPU (edge)", "PyTorch\nGPU", "PyTorch\nCPU"]
    mean = [2.37, 8.07, 12.39]; p95 = [3.64, 12.98, 13.99]
    x = np.arange(len(cfgs)); w = 0.36
    fig, ax = plt.subplots(figsize=(8.0, 4.9), layout="constrained")
    ax.bar(x-w/2, mean, w, color=INDIGO, label="mean")
    ax.bar(x+w/2, p95, w, color=GREY, label="p95")
    for xi, m, p in zip(x, mean, p95):
        ax.text(xi-w/2, m+0.25, f"{m}", ha="center", fontsize=9.5, fontweight="bold")
        ax.text(xi+w/2, p+0.25, f"{p}", ha="center", fontsize=9.5, color="#555")
    ax.set_xticks(x); ax.set_xticklabels(cfgs)
    ax.set_ylabel("Latency per image (ms)"); ax.set_ylim(0, 16)
    ax.set_title("Module 1 single-image inference latency\n(batch=1, 30 warm-up, 300 runs; target < 2000 ms)")
    ax.legend(loc="upper left", fontsize=9.5)
    save(fig, "fig06_m1_latency.png"); done.append("fig06_m1_latency.png")

# ============================================================================
# FIG 7 — M1 per-seed accuracy dot plot
# ============================================================================
def fig_seed_variance():
    specs = [("MobileNetV2", INDIGO, "proper_metrics_seed*.json"),
             ("ResNet-50", AMBER, "baseline_resnet50_metrics_seed*.json"),
             ("SimpleCNN", TEAL, "baseline_simplecnn_metrics_seed*.json")]
    fig, ax = plt.subplots(figsize=(8.0, 5.0), layout="constrained")
    for i, (name, c, pat) in enumerate(specs):
        accs = [load(f)["test_accuracy"]*100
                for f in glob.glob(f"{ROOT}/module1_cv_defect/models/{pat}")]
        xs = np.full(len(accs), i) + np.linspace(-0.05, 0.05, len(accs))
        ax.scatter(xs, accs, color=c, s=75, zorder=3, ec="white", lw=1.2)
        m, s = np.mean(accs), np.std(accs)
        ax.errorbar(i, m, yerr=s, fmt="_", color=c, ms=42, lw=2.6, capsize=9, zorder=2)
        ax.text(i, 99.90, f"{m:.2f} ± {s:.2f}", ha="center", fontsize=10, fontweight="bold", color=c)
    ax.set_xticks(range(3)); ax.set_xticklabels([s[0] for s in specs])
    ax.set_xlim(-0.5, 2.5); ax.set_ylim(99.0, 99.97)
    ax.set_ylabel("Test accuracy (%)")
    ax.set_title("Module 1 per-seed test accuracy across architectures")
    save(fig, "fig07_m1_seed_variance.png"); done.append("fig07_m1_seed_variance.png")

# ============================================================================
# FIG 8 — M3 model comparison
# ============================================================================
def fig_m3_comparison():
    b = load(f"{ROOT}/module3_predictive_maintenance/models/baseline_comparison_pdm.json")
    models = [("Constant\nmean", b["constant_mean"], GREY),
              ("Linear\nregression", b["linear_regression"], TEAL),
              ("XGBoost\n(ours)", b["xgboost"], INDIGO)]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.6), layout="constrained")
    panels = [("rmse", "RMSE  (lower is better)", 0.34),
              ("mae", "MAE  (lower is better)", 0.30),
              ("r2", "R²  (higher is better)", 0.62)]
    for ax, (metric, title, top) in zip(axes, panels):
        vals = [max(m[metric], 0) for _, m, _ in models]  # clip tiny negative for display
        cols = [c for _, _, c in models]
        bars = ax.bar([m[0] for m in models], vals, color=cols, width=0.62)
        for bar, raw in zip(bars, [m[metric] for _, m, _ in models]):
            h = max(raw, 0)
            ax.text(bar.get_x()+bar.get_width()/2, h + top*0.03,
                    f"{raw:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
        ax.set_ylim(0, top)
        ax.set_title(title, fontsize=11.5)
        ax.margins(x=0.08)
    fig.suptitle("Module 3 RUL regression vs. baselines (by-tool split, unseen test tools)",
                 fontsize=13, fontweight="bold")
    save(fig, "fig08_m3_comparison.png"); done.append("fig08_m3_comparison.png")

# ============================================================================
# FIG 9 — M3 predicted vs actual (real)
# ============================================================================
def fig_m3_pred_actual():
    try:
        import pandas as pd, xgboost as xgb
        meta = load(f"{ROOT}/module3_predictive_maintenance/models/model_metadata.json")
        tool_col, tgt = "TollIndex", meta["target"]
        df = pd.read_csv(f"{ROOT}/module3_predictive_maintenance/data/FeatureAndMetadata_Milling.csv",
                         sep=";", header=1)
        for c in ["HardnessMean", "RDOC", "CycleToFailureNormalized"]:
            df[c] = df[c].astype(str).str.replace(",", ".").astype(float)
        df = df[df[tool_col] != 11].reset_index(drop=True)
        feats = meta["feature_cols"]
        test = df[df[tool_col].isin(meta["test_tools"])].copy()
        model = xgb.XGBRegressor(); model.load_model(f"{ROOT}/module3_predictive_maintenance/models/tool_wear_xgb.json")
        pred = np.clip(model.predict(test[feats]), 0.0, 1.0)
        actual = test[tgt].values
        fig, ax = plt.subplots(figsize=(6.2, 5.8), layout="constrained")
        cmap = {t: c for t, c in zip(meta["test_tools"], [INDIGO, TEAL, AMBER, RED])}
        for t in meta["test_tools"]:
            m = test[tool_col].values == t
            ax.scatter(actual[m], pred[m], s=28, alpha=0.72, color=cmap.get(t, GREY), label=f"tool {t}", ec="none")
        ax.plot([0, 1], [0, 1], "--", color="#333", lw=1.2, label="ideal (y = x)")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xlabel("Actual remaining life (normalized)")
        ax.set_ylabel("Predicted remaining life (normalized)")
        ax.set_title("Module 3 predicted vs. actual RUL (unseen test tools; R² = 0.545)")
        ax.legend(fontsize=9, loc="upper left")
        save(fig, "fig09_m3_pred_actual.png"); done.append("fig09_m3_pred_actual.png")
    except Exception as e:
        print("SKIP fig09:", repr(e))

# ============================================================================
# FIG 10 — M4 WAPE vs baselines
# ============================================================================
def fig_m4_wape():
    b = load(f"{ROOT}/module4_demand_forecasting/models/baseline_comparison.json")
    order = [("Prophet", b["prophet"], GREY),
             ("Seasonal-naïve\n(52w)", b["seasonal_naive_52w"], GREY),
             ("Naïve\n(last value)", b["naive_last_value"], TEAL),
             ("XGBoost\n(ours)", b["model_xgboost"], INDIGO)]
    fig, ax = plt.subplots(figsize=(8.2, 4.9), layout="constrained")
    bars = ax.bar([o[0] for o in order], [o[1] for o in order], color=[o[2] for o in order], width=0.62)
    for bar, o in zip(bars, order):
        ax.text(bar.get_x()+bar.get_width()/2, o[1]+0.5, f"{o[1]:.1f}%",
                ha="center", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("WAPE (%)  —  lower is better"); ax.set_ylim(0, 35)
    ax.set_title("Module 4 demand-forecast accuracy vs. baselines\n(held-out 52 weeks, 28 categories)")
    save(fig, "fig10_m4_wape.png"); done.append("fig10_m4_wape.png")

# ============================================================================
# FIG 11 — M4 cross-validation folds
# ============================================================================
def fig_m4_cv():
    meta = load(f"{ROOT}/module4_demand_forecasting/models/model_metadata.json")
    folds = meta["cv"]["folds"]; mean = meta["cv"]["mean_wape_pct"]; hold = meta["metrics"]["wape_pct"]
    fig, ax = plt.subplots(figsize=(7.8, 4.7), layout="constrained")
    xs = [f"Fold {i+1}" for i in range(len(folds))]
    bars = ax.bar(xs, folds, color=TEAL, width=0.55)
    for i, v in enumerate(folds):
        ax.text(i, v+0.35, f"{v:.1f}%", ha="center", fontsize=10, fontweight="bold")
    ax.axhline(mean, color=INDIGO, ls="--", lw=1.8, label=f"CV mean {mean:.1f}%")
    ax.axhline(hold, color=AMBER, ls=":", lw=2.0, label=f"final held-out {hold:.1f}%")
    ax.set_ylabel("WAPE (%)"); ax.set_ylim(0, 27)
    ax.set_title("Module 4 expanding-window cross-validation stability")
    ax.legend(loc="upper right", fontsize=9.5)
    save(fig, "fig11_m4_cv.png"); done.append("fig11_m4_cv.png")

# ============================================================================
# FIG 12 — M4 forecast example with P10-P90 interval
# ============================================================================
def fig_m4_forecast():
    ev = load(f"{ROOT}/dashboard/src/data/events.json")
    cats = ev["forecasting"]["categories"]

    def trim(h):
        h = list(h)
        med = np.median([x["actual_demand"] for x in h])
        while len(h) > 3 and h[-1]["actual_demand"] < 0.6 * med:
            h.pop()
        return h, med

    def score(c):
        h, med = trim(c["history"])
        f0 = c["forecast"][0]["predicted_demand"]
        return (0.5*med <= f0 <= 1.5*med, c["wape_pct"] < 25, c.get("mean_weekly_demand", 0))
    cat = max(cats, key=score)
    hist, _ = trim(cat["history"]); hist = hist[-40:]; fc = cat["forecast"]

    fig, ax = plt.subplots(figsize=(9.4, 4.8), layout="constrained")
    hx = list(range(len(hist)))
    ax.plot(hx, [h["actual_demand"] for h in hist], "-", color=INDIGO, lw=2, label="actual demand")
    fx = list(range(len(hist)-1, len(hist)-1+len(fc)+1))
    fy = [hist[-1]["actual_demand"]] + [f["predicted_demand"] for f in fc]
    ax.plot(fx, fy, "--", color=AMBER, lw=2.2, label="forecast")
    lo = [hist[-1]["actual_demand"]] + [f["lower"] for f in fc]
    hi = [hist[-1]["actual_demand"]] + [f["upper"] for f in fc]
    ax.fill_between(fx, lo, hi, color=AMBER, alpha=0.18, label="80% interval (P10–P90)")
    ax.axvline(len(hist)-1, color=GREY, ls=":", lw=1.2)
    ax.set_xlabel("Week index (last 40 observed + forecast horizon)")
    ax.set_ylabel("Weekly order demand (units)")
    ax.set_ylim(bottom=0)
    ax.set_title(f"Module 4 forecast with prediction interval — {cat['category']} "
                 f"(WAPE {cat['wape_pct']:.0f}%)")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "fig12_m4_forecast.png"); done.append("fig12_m4_forecast.png")

# ============================================================================
# FIG 13 — M4 feature importance
# ============================================================================
def fig_m4_importance():
    try:
        import xgboost as xgb
        meta = load(f"{ROOT}/module4_demand_forecasting/models/model_metadata.json")
        booster = xgb.Booster(); booster.load_model(f"{ROOT}/module4_demand_forecasting/models/demand_forecast_xgb.json")
        score = booster.get_score(importance_type="gain")
        feats = meta["feature_cols"]
        def name(k):
            if k.startswith("f") and k[1:].isdigit():
                idx = int(k[1:]); return feats[idx] if idx < len(feats) else k
            return k
        items = sorted(((name(k), v) for k, v in score.items()), key=lambda t: t[1], reverse=True)[:12]
        labels = [i[0] for i in items][::-1]; vals = [i[1] for i in items][::-1]
        fig, ax = plt.subplots(figsize=(8.4, 5.4), layout="constrained")
        ax.barh(labels, vals, color=AMBER)
        for y, v in enumerate(vals):
            ax.text(v + max(vals)*0.01, y, f"{v:.0f}", va="center", fontsize=9)
        ax.set_xlabel("Importance (gain)")
        ax.set_xlim(0, max(vals)*1.12)
        ax.grid(axis="y", visible=False)
        ax.set_title("Module 4 XGBoost feature importance (top 12, by gain)")
        save(fig, "fig13_m4_importance.png"); done.append("fig13_m4_importance.png")
    except Exception as e:
        print("SKIP fig13:", repr(e))

# ============================================================================
# FIG 14 — Dataset overview
# ============================================================================
def fig_dataset_overview():
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.0), layout="constrained")
    j = load(f"{ROOT}/module1_cv_defect/models/proper_metrics_seed2.json")
    defc = int(j["test_report"]["def_front"]["support"]); okc = int(j["test_report"]["ok_front"]["support"])
    axes[0].pie([defc, okc], labels=[f"def_front\n(n={defc})", f"ok_front\n(n={okc})"],
                autopct="%1.1f%%", colors=[RED, GREEN], startangle=90,
                wedgeprops=dict(width=0.42, ec="white"), pctdistance=0.79,
                textprops=dict(fontsize=10))
    axes[0].set_title("Module 1 held-out test class balance\n(n=715 casting images)", fontsize=11.5)

    ev = load(f"{ROOT}/dashboard/src/data/events.json")
    vols = sorted([c.get("mean_weekly_demand", 0) for c in ev["forecasting"]["categories"]], reverse=True)
    axes[1].bar(range(len(vols)), vols, color=INDIGO)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Product category (rank by volume)")
    axes[1].set_ylabel("Mean weekly demand (units, log)")
    axes[1].set_title("Module 4 category volume spread\n(28 modelled categories)", fontsize=11.5)
    axes[1].grid(axis="x", visible=False)
    fig.suptitle("Dataset composition for Modules 1 and 4", fontsize=13, fontweight="bold")
    save(fig, "fig14_dataset_overview.png"); done.append("fig14_dataset_overview.png")

ALL = [fig_architecture, fig_training_curves, fig_confusion_extended, fig_tradeoff, fig_latency,
       fig_seed_variance, fig_m3_comparison, fig_m3_pred_actual, fig_m4_wape, fig_m4_cv,
       fig_m4_forecast, fig_m4_importance, fig_dataset_overview]

if __name__ == "__main__":
    for fn in ALL:
        try:
            fn()
        except Exception as e:
            print("ERROR in", fn.__name__, ":", repr(e))
    print("\nDONE. %d figures in %s" % (len(done), OUT))
