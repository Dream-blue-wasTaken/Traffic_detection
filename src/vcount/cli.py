"""Command-line interface for vcount."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure src is on sys.path so direct execution works without editable install
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from tqdm import tqdm

from vcount.config import load_config
from vcount.evaluate import evaluate_run
from vcount.line_setup import load_line, parse_line_arg, save_line, select_line_interactive
from vcount.pipeline import run_pipeline
from vcount.video_io import read_first_frame


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def handle_line(args: argparse.Namespace) -> int:
    """Select and save a counting line for a video."""
    setup_logging(args.verbose)
    video_p = Path(args.video)
    if not video_p.is_file():
        print(f"Error: Video file not found: {video_p}", file=sys.stderr)
        return 1

    first_frame = read_first_frame(video_p, start_seconds=args.start)
    try:
        line = select_line_interactive(first_frame, offset_px=args.offset)
    except Exception as e:
        print(f"Line selection error: {e}", file=sys.stderr)
        return 1

    save_p = Path(args.save)
    save_line(line, save_p)
    print(f"Saved counting line to: {save_p}")
    return 0


def handle_run(args: argparse.Namespace) -> int:
    """Run full vehicle counting pipeline on a video."""
    setup_logging(args.verbose)

    overrides = {}
    if args.interval:
        overrides.setdefault("intervals", {})["length_seconds"] = args.interval
    if args.model:
        overrides.setdefault("model", {})["weights"] = args.model
    if args.tracker:
        overrides.setdefault("tracker", {})["type"] = args.tracker
    if args.conf is not None:
        overrides.setdefault("model", {})["conf"] = args.conf
    if args.device:
        overrides.setdefault("model", {})["device"] = args.device
    if args.no_video:
        overrides.setdefault("output", {})["save_video"] = False
    if args.start is not None:
        overrides.setdefault("video", {})["start_seconds"] = args.start
    if args.end is not None:
        overrides.setdefault("video", {})["end_seconds"] = args.end

    try:
        cfg = load_config(args.config, overrides=overrides)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Resolve line
    line = None
    if args.line:
        try:
            line = parse_line_arg(args.line, offset_px=cfg.counting.parallel_offset_px)
        except ValueError as e:
            print(f"Invalid line argument: {e}", file=sys.stderr)
            return 1
    elif args.line_file:
        try:
            line = load_line(args.line_file)
        except Exception as e:
            print(f"Could not load line file: {e}", file=sys.stderr)
            return 1

    # Setup progress bar
    pbar = tqdm(total=100, desc="Processing Video", unit="%")

    def on_progress(fraction: float, eta_s: float):
        target = int(fraction * 100)
        if target > pbar.n:
            pbar.update(target - pbar.n)
        pbar.set_postfix({"ETA": f"{int(eta_s)}s"})

    try:
        res = run_pipeline(
            video_path=args.video,
            cfg=cfg,
            line=line,
            progress_cb=on_progress,
        )
    finally:
        pbar.close()

    print("\n" + "=" * 60)
    print("VCOUNT PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Output Directory : {res.output_dir}")
    print(f"Total Vehicles   : {res.total_vehicles}")
    for d, cls_counts in res.totals.items():
        sub_total = sum(cls_counts.values())
        print(f"\n  Direction '{d}': {sub_total} vehicles")
        for cname, cnt in cls_counts.items():
            print(f"    - {cname}: {cnt}")
    print("=" * 60 + "\n")
    return 0


def handle_eval(args: argparse.Namespace) -> int:
    """Evaluate a run directory against a ground truth CSV."""
    setup_logging(args.verbose)
    try:
        metrics = evaluate_run(
            run_dir=args.run,
            gt_file=args.gt,
            tolerance_s=args.tolerance_s,
        )
    except Exception as e:
        print(f"Evaluation error: {e}", file=sys.stderr)
        return 1

    tot = metrics.get("total_count_metrics", {})
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Manual Ground Truth Count : {tot.get('manual', 0)}")
    print(f"Automated System Count    : {tot.get('auto', 0)}")
    print(f"Accuracy                  : {tot.get('accuracy_pct', 0)}%")
    print(f"Signed Error              : {tot.get('signed_error_pct', 0)}%")

    evt = metrics.get("event_metrics")
    if evt:
        print(f"Precision / Recall / F1   : {evt.get('precision'):.3f} / {evt.get('recall'):.3f} / {evt.get('f1'):.3f}")
    print("=" * 60 + "\n")
    return 0


def handle_bench(args: argparse.Namespace) -> int:
    """Run model/tracker benchmarks on a clip."""
    from scripts.benchmark_models import run_benchmarks
    setup_logging(args.verbose)
    return run_benchmarks(
        video_path=args.video,
        models=args.models,
        trackers=args.trackers,
        output_csv=args.output,
        gt_path=args.gt,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vcount", description="Vehicle Counting System using YOLO and ByteTrack")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. run command
    p_run = subparsers.add_parser("run", help="Run detection, tracking and counting on a video")
    p_run.add_argument("--video", required=True, help="Path to input video file")
    p_run.add_argument("--config", default="configs/default.yaml", help="Path to YAML configuration file")
    p_run.add_argument("--line", help="Line coordinates as 'x1,y1,x2,y2'")
    p_run.add_argument("--line-file", help="Path to saved counting-line JSON")
    p_run.add_argument("--interval", type=int, help="Interval length in seconds (e.g. 60, 300, 900)")
    p_run.add_argument("--model", help="YOLO weights file (e.g. yolo26s.pt, yolo11m.pt)")
    p_run.add_argument("--tracker", choices=["bytetrack", "botsort"], help="Tracker algorithm")
    p_run.add_argument("--conf", type=float, help="Confidence threshold (0.0 to 1.0)")
    p_run.add_argument("--device", help="Compute device ('cpu', 'cuda:0', 'mps')")
    p_run.add_argument("--no-video", action="store_true", help="Do not write annotated video output")
    p_run.add_argument("--start", type=float, default=0.0, help="Start time in seconds")
    p_run.add_argument("--end", type=float, help="End time in seconds")
    p_run.set_defaults(func=handle_run)

    # 2. line command
    p_line = subparsers.add_parser("line", help="Select and save a counting line interactively")
    p_line.add_argument("--video", required=True, help="Path to input video file")
    p_line.add_argument("--save", required=True, help="Destination JSON path for the counting line")
    p_line.add_argument("--offset", type=float, default=60.0, help="Gate lines offset in pixels")
    p_line.add_argument("--start", type=float, default=0.0, help="Frame position in seconds")
    p_line.set_defaults(func=handle_line)

    # 3. eval command
    p_eval = subparsers.add_parser("eval", help="Evaluate counting accuracy against ground truth")
    p_eval.add_argument("--run", required=True, help="Path to run output directory (containing events.csv)")
    p_eval.add_argument("--gt", required=True, help="Path to manual ground truth CSV")
    p_eval.add_argument("--tolerance-s", type=float, default=2.0, help="Time tolerance in seconds for matching")
    p_eval.set_defaults(func=handle_eval)

    # 4. bench command
    p_bench = subparsers.add_parser("bench", help="Benchmark model sizes and trackers on a clip")
    p_bench.add_argument("--video", required=True, help="Path to input video file")
    p_bench.add_argument("--models", nargs="+", default=["yolo26n.pt", "yolo26s.pt", "yolo11n.pt"], help="Models to benchmark")
    p_bench.add_argument("--trackers", nargs="+", default=["bytetrack", "botsort"], help="Trackers to benchmark")
    p_bench.add_argument("--output", default="outputs/benchmark.csv", help="Benchmark results CSV path")
    p_bench.add_argument("--gt", help="Optional ground truth CSV to measure accuracy")
    p_bench.set_defaults(func=handle_bench)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
