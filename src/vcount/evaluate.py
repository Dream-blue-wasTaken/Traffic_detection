"""Evaluation of counting performance against manual ground truth."""

from __future__ import annotations

from pathlib import Path
import json
import logging
import math
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def compute_count_metrics(auto_count: int, manual_count: int) -> dict:
    """Compute count-level accuracy and signed error."""
    diff = auto_count - manual_count
    if manual_count > 0:
        accuracy_pct = max(0.0, 100.0 - (abs(diff) / manual_count) * 100.0)
        signed_error_pct = (diff / manual_count) * 100.0
    else:
        accuracy_pct = 100.0 if auto_count == 0 else 0.0
        signed_error_pct = 0.0 if auto_count == 0 else 100.0

    return {
        "manual": manual_count,
        "auto": auto_count,
        "diff": diff,
        "accuracy_pct": round(accuracy_pct, 2),
        "signed_error_pct": round(signed_error_pct, 2),
    }


def match_events(
    auto_events: pd.DataFrame,
    gt_events: pd.DataFrame,
    tolerance_s: float = 2.0,
) -> dict:
    """Greedy nearest-time one-to-one matching between automated and ground truth crossing events."""
    if auto_events.empty and gt_events.empty:
        return {"tp": 0, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "matches": []}
    if auto_events.empty:
        return {"tp": 0, "fp": 0, "fn": len(gt_events), "precision": 0.0, "recall": 0.0, "f1": 0.0, "matches": []}
    if gt_events.empty:
        return {"tp": 0, "fp": len(auto_events), "fn": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "matches": []}

    auto_df = auto_events.copy().sort_values("timestamp_s").reset_index(drop=True)
    gt_df = gt_events.copy().sort_values("timestamp_s").reset_index(drop=True)

    matched_gt_indices = set()
    matched_auto_indices = set()
    matches = []

    # For each auto event, find candidate GT events with same direction and class within tolerance
    for a_idx, a_row in auto_df.iterrows():
        a_t = a_row["timestamp_s"]
        a_dir = str(a_row["direction"]).strip().lower()
        a_cls = str(a_row["class_name"]).strip().lower()

        best_gt_idx = None
        best_delta = float("inf")

        for g_idx, g_row in gt_df.iterrows():
            if g_idx in matched_gt_indices:
                continue
            g_t = g_row["timestamp_s"]
            g_dir = str(g_row["direction"]).strip().lower()
            g_cls = str(g_row["class_name"]).strip().lower()

            if a_dir == g_dir and a_cls == g_cls:
                delta = abs(a_t - g_t)
                if delta <= tolerance_s and delta < best_delta:
                    best_delta = delta
                    best_gt_idx = g_idx

        if best_gt_idx is not None:
            matched_gt_indices.add(best_gt_idx)
            matched_auto_indices.add(a_idx)
            matches.append({
                "auto_idx": a_idx,
                "gt_idx": best_gt_idx,
                "auto_class": a_cls,
                "gt_class": str(gt_df.loc[best_gt_idx, "class_name"]).strip().lower(),
                "direction": a_dir,
                "delta_t": round(best_delta, 3),
            })

    tp = len(matches)
    fp = len(auto_df) - len(matched_auto_indices)
    fn = len(gt_df) - len(matched_gt_indices)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matches": matches,
    }


def run_paired_statistics(auto_series: list[float], manual_series: list[float]) -> dict | None:
    """Run paired t-test, normality test, and confidence interval if n >= 5."""
    n = len(auto_series)
    if n < 5:
        return None

    auto_arr = np.array(auto_series, dtype=float)
    man_arr = np.array(manual_series, dtype=float)
    diffs = auto_arr - man_arr

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    # Shapiro-Wilk test on differences
    try:
        shapiro_stat, shapiro_p = stats.shapiro(diffs)
    except Exception:
        shapiro_stat, shapiro_p = None, None

    # Paired t-test
    t_stat, t_p = stats.ttest_rel(auto_arr, man_arr)

    # Bias-adjusted t-test (diff minus mean)
    adjusted_diffs = diffs - mean_diff
    adj_stat, adj_p = stats.ttest_1samp(adjusted_diffs, 0.0)

    # 95% Confidence Interval using t-distribution
    ci_low, ci_high = stats.t.interval(0.95, df=n - 1, loc=mean_diff, scale=stats.sem(diffs))

    return {
        "n": n,
        "mean_diff": round(mean_diff, 3),
        "std_diff": round(std_diff, 3),
        "shapiro_p": round(float(shapiro_p), 4) if shapiro_p is not None else None,
        "normal_distribution": (shapiro_p is not None and shapiro_p > 0.05),
        "paired_t_statistic": round(float(t_stat), 4),
        "paired_t_pvalue": round(float(t_p), 4),
        "bias_adjusted_pvalue": round(float(adj_p), 4),
        "ci_95_low": round(float(ci_low), 3),
        "ci_95_high": round(float(ci_high), 3),
    }


def evaluate_run(
    run_dir: str | Path,
    gt_file: str | Path,
    tolerance_s: float = 2.0,
    out_dir: str | Path | None = None,
) -> dict:
    """Run comprehensive evaluation on a completed run against ground truth."""
    r_dir = Path(run_dir)
    gt_p = Path(gt_file)
    target_out = Path(out_dir) if out_dir else r_dir

    if not gt_p.is_file():
        raise FileNotFoundError(f"Ground truth file not found: {gt_p}")

    events_csv = r_dir / "events.csv"
    if not events_csv.is_file():
        raise FileNotFoundError(f"events.csv not found in run directory: {r_dir}")

    auto_events = pd.read_csv(events_csv)
    gt_df = pd.read_csv(gt_p)

    # Detect if ground truth is event-level (has 'timestamp_s') or interval-level
    is_event_level = "timestamp_s" in gt_df.columns

    report_metrics: dict = {}

    if is_event_level:
        # Match events
        event_metrics = match_events(auto_events, gt_df, tolerance_s=tolerance_s)
        report_metrics["event_metrics"] = event_metrics

        # Aggregate totals for count metrics
        auto_total = len(auto_events)
        gt_total = len(gt_df)
        total_count_metrics = compute_count_metrics(auto_total, gt_total)
        report_metrics["total_count_metrics"] = total_count_metrics

        # Per direction and class metrics
        breakdown = {}
        all_dirs = set(auto_events["direction"].dropna().unique()) | set(gt_df["direction"].dropna().unique())
        all_cls = set(auto_events["class_name"].dropna().unique()) | set(gt_df["class_name"].dropna().unique())

        for d in all_dirs:
            for c in all_cls:
                a_sub = len(auto_events[(auto_events["direction"] == d) & (auto_events["class_name"] == c)])
                g_sub = len(gt_df[(gt_df["direction"] == d) & (gt_df["class_name"] == c)])
                breakdown[f"{d}_{c}"] = compute_count_metrics(a_sub, g_sub)

        report_metrics["breakdown"] = breakdown
    else:
        # Interval-level ground truth matching
        counts_csv = r_dir / "counts_by_interval.csv"
        if counts_csv.is_file():
            auto_intervals = pd.read_csv(counts_csv)
            auto_total = int(auto_intervals["total"].sum()) if "total" in auto_intervals.columns else len(auto_events)
        else:
            auto_total = len(auto_events)
        gt_total = int(gt_df["total"].sum()) if "total" in gt_df.columns else len(gt_df)
        report_metrics["total_count_metrics"] = compute_count_metrics(auto_total, gt_total)

    # Generate Evaluation Plots
    plots_saved = generate_evaluation_plots(target_out, auto_events, gt_df, is_event_level)
    report_metrics["plots"] = plots_saved

    # Save metrics JSON
    with open(target_out / "evaluation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report_metrics, f, indent=2)

    # Generate Markdown Report
    generate_markdown_report(target_out / "evaluation_report.md", report_metrics)

    return report_metrics


def generate_evaluation_plots(
    out_dir: Path,
    auto_events: pd.DataFrame,
    gt_df: pd.DataFrame,
    is_event_level: bool,
) -> list[str]:
    """Create and save evaluation plots: scatter with y=x, Bland-Altman, interval comparisons."""
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_plots = []

    # 1. Scatter Plot: Manual vs Automated per Class/Direction
    if is_event_level:
        dirs = list(set(auto_events["direction"].dropna()) | set(gt_df["direction"].dropna()))
        clss = list(set(auto_events["class_name"].dropna()) | set(gt_df["class_name"].dropna()))

        manual_vals = []
        auto_vals = []
        labels = []

        for d in dirs:
            for c in clss:
                m_cnt = len(gt_df[(gt_df["direction"] == d) & (gt_df["class_name"] == c)])
                a_cnt = len(auto_events[(auto_events["direction"] == d) & (auto_events["class_name"] == c)])
                if m_cnt > 0 or a_cnt > 0:
                    manual_vals.append(m_cnt)
                    auto_vals.append(a_cnt)
                    labels.append(f"{d}_{c}")

        if manual_vals:
            plt.figure(figsize=(6, 6))
            max_v = max(max(manual_vals), max(auto_vals), 1) + 2
            plt.plot([0, max_v], [0, max_v], "r--", label="y = x (Perfect agreement)")
            plt.scatter(manual_vals, auto_vals, c="blue", alpha=0.7, s=60)
            for i, txt in enumerate(labels):
                plt.annotate(txt, (manual_vals[i] + 0.1, auto_vals[i] + 0.1), fontsize=8)
            plt.xlabel("Manual Count")
            plt.ylabel("Automated Count")
            plt.title("Manual vs Automated Vehicle Counts")
            plt.xlim(0, max_v)
            plt.ylim(0, max_v)
            plt.legend()
            plt.tight_layout()
            scatter_path = out_dir / "eval_scatter.png"
            plt.savefig(scatter_path, dpi=200)
            plt.close()
            saved_plots.append(scatter_path.name)

            # 2. Bland-Altman Plot
            if len(manual_vals) >= 3:
                m_arr = np.array(manual_vals)
                a_arr = np.array(auto_vals)
                means = (m_arr + a_arr) / 2.0
                diffs = a_arr - m_arr
                mean_diff = np.mean(diffs)
                std_diff = np.std(diffs)

                plt.figure(figsize=(7, 4.5))
                plt.scatter(means, diffs, c="darkcyan", s=50)
                plt.axhline(mean_diff, color="black", linestyle="-", label=f"Mean diff: {mean_diff:.2f}")
                plt.axhline(mean_diff + 1.96 * std_diff, color="red", linestyle="--", label="+1.96 SD")
                plt.axhline(mean_diff - 1.96 * std_diff, color="red", linestyle="--", label="-1.96 SD")
                plt.xlabel("Mean of Automated and Manual Count")
                plt.ylabel("Difference (Automated - Manual)")
                plt.title("Bland–Altman Plot (Signed Error / Bias Analysis)")
                plt.legend()
                plt.tight_layout()
                bland_path = out_dir / "eval_bland_altman.png"
                plt.savefig(bland_path, dpi=200)
                plt.close()
                saved_plots.append(bland_path.name)

    return saved_plots


def generate_markdown_report(report_path: Path, metrics: dict) -> None:
    """Generate Markdown evaluation report document."""
    lines = [
        "# Video Counting System — Evaluation Report",
        "",
        "## 1. Overall Performance",
        "",
    ]

    total_m = metrics.get("total_count_metrics", {})
    if total_m:
        lines.extend([
            "| Metric | Value |",
            "| --- | --- |",
            f"| Manual Ground Truth Count | **{total_m.get('manual', 0)}** |",
            f"| Automated System Count | **{total_m.get('auto', 0)}** |",
            f"| Absolute Count Difference | {total_m.get('diff', 0)} |",
            f"| **Overall Accuracy** | **{total_m.get('accuracy_pct', 0.0)}%** |",
            f"| **Signed Error %** | **{total_m.get('signed_error_pct', 0.0)}%** |",
            "",
            "> **Interpretation:** Negative signed error indicates undercounting (consistent with paper findings); "
            "positive indicates overcounting/duplicate IDs.",
            "",
        ])

    evt = metrics.get("event_metrics")
    if evt:
        lines.extend([
            "## 2. Event-Level Performance (Nearest-Time Association)",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| True Positives (TP) | {evt.get('tp', 0)} |",
            f"| False Positives (FP) | {evt.get('fp', 0)} |",
            f"| False Negatives (FN) | {evt.get('fn', 0)} |",
            f"| **Precision** | **{evt.get('precision', 0.0):.3f}** |",
            f"| **Recall** | **{evt.get('recall', 0.0):.3f}** |",
            f"| **F1 Score** | **{evt.get('f1', 0.0):.3f}** |",
            "",
        ])

    breakdown = metrics.get("breakdown")
    if breakdown:
        lines.extend([
            "## 3. Breakdown per Direction & Class",
            "",
            "| Direction & Class | Manual | Auto | Diff | Accuracy % | Signed Error % |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for key, val in sorted(breakdown.items()):
            lines.append(
                f"| `{key}` | {val['manual']} | {val['auto']} | {val['diff']} | "
                f"{val['accuracy_pct']}% | {val['signed_error_pct']}% |"
            )
        lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
