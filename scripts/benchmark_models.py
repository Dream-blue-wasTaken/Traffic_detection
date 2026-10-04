"""Benchmark script comparing YOLO models and trackers on speed and accuracy."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from vcount.config import load_config
from vcount.evaluate import evaluate_run
from vcount.line_setup import CountingLine, load_line
from vcount.pipeline import run_pipeline
from vcount.video_io import get_video_info


def run_benchmarks(
    video_path: str | Path,
    models: list[str],
    trackers: list[str],
    output_csv: str | Path = "outputs/benchmark.csv",
    gt_path: str | Path | None = None,
    line_file: str | Path | None = None,
) -> int:
    """Benchmark combinations of models and trackers on a test video."""
    video_p = Path(video_path)
    if not video_p.is_file():
        print(f"Error: Video not found: {video_p}")
        return 1

    info = get_video_info(video_p)

    line: CountingLine | None = None
    if line_file:
        line = load_line(line_file)
    else:
        # Default middle horizontal line
        line = CountingLine(
            p1=(0.0, info.height / 2.0),
            p2=(float(info.width), info.height / 2.0),
            offset_px=50.0,
        )

    results = []

    print(f"\nBenchmarking video: {video_p.name} ({info.frame_count} frames, {info.duration_s:.1f}s)")
    print(f"Models: {models}")
    print(f"Trackers: {trackers}\n")

    for model_name in models:
        for tracker_type in trackers:
            print(f"--> Running: {model_name} + {tracker_type}...")
            cfg = load_config(
                overrides={
                    "model": {"weights": model_name},
                    "tracker": {"type": tracker_type},
                    "output": {"save_video": False},  # measure pure inference/tracking speed
                }
            )

            t0 = time.time()
            try:
                res = run_pipeline(video_path=video_p, cfg=cfg, line=line)
                elapsed = time.time() - t0
                fps = res.summary.get("average_fps", 0.0)
                tot_count = res.total_vehicles

                accuracy_pct = None
                if gt_path and Path(gt_path).is_file():
                    metrics = evaluate_run(run_dir=res.output_dir, gt_file=gt_path)
                    accuracy_pct = metrics.get("total_count_metrics", {}).get("accuracy_pct")

                results.append({
                    "model": model_name,
                    "tracker": tracker_type,
                    "runtime_s": round(elapsed, 2),
                    "fps": round(fps, 2),
                    "total_counts": tot_count,
                    "accuracy_pct": accuracy_pct,
                    "output_dir": str(res.output_dir),
                })
                print(f"    Completed: {fps:.1f} FPS, Counts: {tot_count}, Accuracy: {accuracy_pct}%\n")
            except Exception as e:
                print(f"    FAILED: {e}\n")

    if not results:
        print("No benchmarks were successfully completed.")
        return 1

    df = pd.DataFrame(results)
    out_p = Path(output_csv)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_p, index=False)
    print(f"Saved benchmark results to: {out_p}")

    # Generate benchmark plot
    plot_path = out_p.parent / "benchmark_comparison.png"
    plt.figure(figsize=(9, 5))
    labels = [f"{r['model']}\n({r['tracker']})" for _, r in df.iterrows()]
    plt.bar(labels, df["fps"], color="#3B82F6", alpha=0.85, label="Processing FPS")
    plt.ylabel("Processing Speed (FPS)")
    plt.title("Model & Tracker Speed Benchmark")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Saved benchmark chart to: {plot_path}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Benchmark YOLO models & trackers on video.")
    parser.add_argument("--video", required=True, help="Path to input video clip")
    parser.add_argument("--models", nargs="+", default=["yolo26n.pt", "yolo26s.pt", "yolo11n.pt"], help="Models")
    parser.add_argument("--trackers", nargs="+", default=["bytetrack", "botsort"], help="Trackers")
    parser.add_argument("--output", default="outputs/benchmark.csv", help="Output CSV path")
    parser.add_argument("--gt", help="Ground truth CSV path")
    parser.add_argument("--line-file", help="Path to saved counting-line JSON")
    args = parser.parse_args()

    return run_benchmarks(
        video_path=args.video,
        models=args.models,
        trackers=args.trackers,
        output_csv=args.output,
        gt_path=args.gt,
        line_file=args.line_file,
    )


if __name__ == "__main__":
    main()
