"""Consolidate every Module 1 experiment result into ONE place.

Reads all per-seed proper-training metric files and any baseline metric
files, computes mean +/- std across seeds, and writes a single Markdown
results table (reports/module1_results.md) plus a plain-text log line.
This is the paper-ready record of what was actually run -- instead of
numbers scattered across many JSON files and console output.

Usage:
    python src/aggregate_results.py
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np

MODELS = Path("models")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)


def load(pattern):
    out = []
    for p in sorted(MODELS.glob(pattern)):
        out.append(json.load(open(p)))
    return out


def macro_f1(report):
    return report["macro avg"]["f1-score"]


def summarize(runs, label):
    accs = np.array([r["test_accuracy"] for r in runs])
    f1s = np.array([macro_f1(r["test_report"]) for r in runs])
    seeds = [r["seed"] for r in runs]
    return {
        "label": label, "seeds": seeds, "n": len(runs),
        "acc_mean": accs.mean(), "acc_std": accs.std(ddof=0),
        "acc_min": accs.min(), "acc_max": accs.max(),
        "f1_mean": f1s.mean(), "f1_std": f1s.std(ddof=0),
    }


def main():
    proper = load("proper_metrics_seed*.json")
    resnet = load("baseline_resnet50_metrics_seed*.json")
    cnn = load("baseline_simplecnn_metrics_seed*.json")

    rows = []
    if proper:
        rows.append(summarize(proper, "MobileNetV2 (proper split)"))
    if resnet:
        rows.append(summarize(resnet, "ResNet-50 (baseline)"))
    if cnn:
        rows.append(summarize(cnn, "SimpleCNN from scratch (baseline)"))

    lines = ["# Module 1 — Consolidated Results", "",
             f"_Generated {datetime.now():%Y-%m-%d %H:%M}_", "",
             "All models trained on the SAME proper train/val/test split "
             "(model selected on validation, test evaluated once).", "",
             "| Model | Seeds | Test Acc (mean ± std) | Range | Macro-F1 (mean ± std) |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['n']} ({','.join(map(str, r['seeds']))}) | "
            f"{r['acc_mean']*100:.2f}% ± {r['acc_std']*100:.2f} | "
            f"{r['acc_min']*100:.2f}–{r['acc_max']*100:.2f}% | "
            f"{r['f1_mean']*100:.2f}% ± {r['f1_std']*100:.2f} |"
        )

    # per-seed detail
    lines += ["", "## Per-seed detail (MobileNetV2)", "",
              "| Seed | Selected at | Val Acc | Test Acc | Confusion [[TN? layout]] |",
              "|---|---|---|---|---|"]
    for r in proper:
        lines.append(f"| {r['seed']} | {r['best_on']} | {r['val_acc']*100:.2f}% | "
                     f"{r['test_accuracy']*100:.2f}% | {r['confusion_matrix']} |")

    lines += ["", "_Confusion matrix rows = true [def_front, ok_front], cols = predicted._"]

    out_md = REPORTS / "module1_results.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    # append a one-line log entry
    log = Path("logs"); log.mkdir(exist_ok=True)
    with open(log / "module1_results_log.txt", "a", encoding="utf-8") as f:
        for r in rows:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M}  {r['label']}: "
                    f"test_acc={r['acc_mean']*100:.2f}%±{r['acc_std']*100:.2f} "
                    f"(seeds {r['seeds']})\n")

    print(f"Wrote {out_md}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
