"""Export run results: CSVs, events log, JSON summary, and configuration snapshot."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
import cv2
import pandas as pd
import torch
import ultralytics
import yaml

from vcount.config import Config
from vcount.counter import CountEvent
from vcount.video_io import VideoInfo


def export_results(
    output_dir: str | Path,
    events: list[CountEvent],
    df_wide: pd.DataFrame,
    df_long: pd.DataFrame,
    totals: dict[str, dict[str, int]],
    cfg: Config,
    video_info: VideoInfo,
    runtime_s: float,
    processed_frames: int,
) -> dict:
    """Save all artifacts into output_dir.

    Returns the summary dictionary.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. counts_by_interval.csv
    df_wide.to_csv(out_path / "counts_by_interval.csv", index=False)

    # 2. counts_by_interval_long.csv
    df_long.to_csv(out_path / "counts_by_interval_long.csv", index=False)

    # 3. events.csv
    events_data = [
        {
            "track_id": e.track_id,
            "class_name": e.class_name,
            "direction": e.direction,
            "frame_idx": e.frame_idx,
            "timestamp_s": round(e.timestamp_s, 3),
            "x": round(e.position[0], 2),
            "y": round(e.position[1], 2),
        }
        for e in events
    ]
    df_events = pd.DataFrame(events_data)
    if df_events.empty:
        df_events = pd.DataFrame(
            columns=["track_id", "class_name", "direction", "frame_idx", "timestamp_s", "x", "y"]
        )
    df_events.to_csv(out_path / "events.csv", index=False)

    # 4. config_used.yaml
    with open(out_path / "config_used.yaml", "w", encoding="utf-8") as f:
        yaml.dump(asdict(cfg), f, sort_keys=False)

    # 5. summary.json
    avg_fps = (processed_frames / runtime_s) if runtime_s > 0 else 0.0
    total_vehicles = sum(sum(cls_cnt.values()) for cls_cnt in totals.values())

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_vehicles": total_vehicles,
        "totals": totals,
        "runtime_s": round(runtime_s, 2),
        "processed_frames": processed_frames,
        "average_fps": round(avg_fps, 2),
        "video_info": {
            "fps": video_info.fps,
            "frame_count": video_info.frame_count,
            "width": video_info.width,
            "height": video_info.height,
            "duration_s": round(video_info.duration_s, 2),
        },
        "model_weights": cfg.model.weights,
        "tracker_type": cfg.tracker.type,
        "software_versions": {
            "ultralytics": ultralytics.__version__,
            "torch": torch.__version__,
            "opencv": cv2.__version__,
        },
    }

    with open(out_path / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary
