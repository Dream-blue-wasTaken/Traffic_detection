"""End-to-end vehicle counting pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
import logging
import threading
import time
import numpy as np
import pandas as pd
from ultralytics import YOLO

from vcount.annotate import FrameAnnotator
from vcount.config import Config
from vcount.counter import CountEvent, LineCounter
from vcount.detector_tracker import load_model, track_video
from vcount.exporter import export_results
from vcount.intervals import bucket_events
from vcount.line_setup import CountingLine, load_line, select_line_interactive
from vcount.video_io import VideoWriterContext, get_video_info, read_first_frame

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    output_dir: Path
    totals: dict[str, dict[str, int]]
    total_vehicles: int
    df_wide: pd.DataFrame
    df_long: pd.DataFrame
    summary: dict
    annotated_video_path: Path | None
    events: list[CountEvent]


def run_pipeline(
    video_path: str | Path,
    cfg: Config,
    line: CountingLine | None = None,
    model: YOLO | None = None,
    progress_cb: Callable[[float, float], None] | None = None,
    preview_cb: Callable[[np.ndarray], None] | None = None,
    stop_event: threading.Event | None = None,
) -> RunResult:
    """Execute the end-to-end detection, tracking, counting, annotation, and export pipeline."""
    video_p = Path(video_path)
    if not video_p.is_file():
        raise FileNotFoundError(f"Video file not found: {video_p}")

    info = get_video_info(video_p)

    # Resolve Counting Line
    if line is None:
        if cfg.counting.line_file:
            line = load_line(cfg.counting.line_file)
        else:
            first_frame = read_first_frame(video_p, start_seconds=cfg.video.start_seconds)
            line = select_line_interactive(first_frame, offset_px=cfg.counting.parallel_offset_px)

    # Initialize Model & Tracker
    if model is None:
        model = load_model(cfg.model.weights)

    class_names = {cid: name for name, cid in cfg.model.classes.items()}
    counter = LineCounter(line, cfg.counting, class_names=class_names)
    annotator = FrameAnnotator(line, cfg)

    # Prepare Output Directory
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(cfg.output.dir) / f"{video_p.stem}_{timestamp_str}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Setup Video Writer if enabled
    writer_ctx: VideoWriterContext | None = None
    annotated_video_path: Path | None = None
    first_frame_ref = read_first_frame(video_p, start_seconds=cfg.video.start_seconds)
    frame_h, frame_w = first_frame_ref.shape[:2]
    if cfg.video.resize_width is not None and cfg.video.resize_width > 0:
        scale = cfg.video.resize_width / float(frame_w)
        frame_w = cfg.video.resize_width
        frame_h = int(frame_h * scale)

    output_fps = info.fps / cfg.video.frame_stride

    if cfg.output.save_video:
        annotated_video_path = out_dir / "annotated.mp4"
        writer_ctx = VideoWriterContext(
            output_path=annotated_video_path,
            fps=output_fps,
            width=frame_w,
            height=frame_h,
            codec=cfg.output.video_codec,
        )

    # Tracking & Processing Loop
    total_expected_frames = int(info.frame_count / cfg.video.frame_stride) if info.frame_count > 0 else 1
    if cfg.video.end_seconds is not None:
        slice_duration = cfg.video.end_seconds - cfg.video.start_seconds
        total_expected_frames = max(1, int((slice_duration * info.fps) / cfg.video.frame_stride))

    start_time = time.time()
    processed_frames = 0
    fps_estimate = 0.0

    try:
        if writer_ctx:
            writer_ctx.__enter__()

        for frame_res in track_video(video_p, cfg, model=model):
            if stop_event is not None and stop_event.is_set():
                logger.info("Pipeline stop requested by user.")
                break

            processed_frames += 1
            now = time.time()
            elapsed = now - start_time
            if elapsed > 0:
                fps_estimate = processed_frames / elapsed

            # Update counter
            events = counter.update(frame_res)
            annotator.register_events(events)

            # Cleanup stale tracks every 100 frames
            if processed_frames % 100 == 0:
                counter.cleanup(frame_res.frame_idx)

            # Draw visual overlay
            annotated_frame = annotator.draw(frame_res, counter, fps_estimate=fps_estimate)

            if writer_ctx:
                writer_ctx.write(annotated_frame)

            # Callbacks for UI
            if preview_cb is not None and processed_frames % 15 == 0:
                preview_cb(annotated_frame)

            if progress_cb is not None and processed_frames % 10 == 0:
                fraction = min(1.0, processed_frames / float(total_expected_frames))
                rem_frames = max(0, total_expected_frames - processed_frames)
                eta_s = (rem_frames / fps_estimate) if fps_estimate > 0 else 0.0
                progress_cb(fraction, eta_s)

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by KeyboardInterrupt. Saving partial results...")
    finally:
        if writer_ctx:
            writer_ctx.__exit__(None, None, None)

    total_runtime = time.time() - start_time
    totals = counter.totals()
    total_vehicles = counter.total_count

    # Bucket into intervals
    all_dirs = [cfg.counting.direction_labels.get("a_to_b", "entry"), cfg.counting.direction_labels.get("b_to_a", "exit")]
    all_classes = list(cfg.model.classes.keys())
    effective_dur = (
        info.duration_s
        if cfg.video.end_seconds is None
        else (cfg.video.end_seconds - cfg.video.start_seconds)
    )

    df_wide, df_long = bucket_events(
        events=counter.events,
        interval_s=cfg.intervals.length_seconds,
        duration_s=effective_dur,
        all_directions=all_dirs,
        all_classes=all_classes,
        video_start_clock=cfg.intervals.video_start_clock,
    )

    # Export results
    summary = export_results(
        output_dir=out_dir,
        events=counter.events,
        df_wide=df_wide,
        df_long=df_long,
        totals=totals,
        cfg=cfg,
        video_info=info,
        runtime_s=total_runtime,
        processed_frames=processed_frames,
    )

    if progress_cb is not None:
        progress_cb(1.0, 0.0)

    return RunResult(
        output_dir=out_dir,
        totals=totals,
        total_vehicles=total_vehicles,
        df_wide=df_wide,
        df_long=df_long,
        summary=summary,
        annotated_video_path=annotated_video_path,
        events=counter.events,
    )
