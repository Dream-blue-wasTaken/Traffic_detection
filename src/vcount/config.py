"""Configuration dataclasses, YAML loader, and validation for vcount."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class ModelConfig:
    weights: str = "yolo26m.pt"
    device: str = "auto"
    imgsz: int = 960
    conf: float = 0.35
    iou: float = 0.5
    half: bool = True
    classes: dict[str, int] = field(
        default_factory=lambda: {
            "car": 2,
            "motorcycle": 3,
            "bus": 5,
            "truck": 7,
        }
    )


@dataclass
class TrackerConfig:
    type: str = "bytetrack"
    yaml_override: str | None = None
    track_buffer: int = 30


@dataclass
class CountingConfig:
    line_file: str | None = None
    parallel_offset_px: float = 60.0
    mode: str = "gated"
    min_track_frames: int = 3
    count_point: str = "bottom_center"
    direction_labels: dict[str, str] = field(
        default_factory=lambda: {
            "a_to_b": "entry",
            "b_to_a": "exit",
        }
    )
    dedup_enabled: bool = False
    dedup_frames: int = 5
    dedup_distance_px: float = 40.0


@dataclass
class IntervalsConfig:
    length_seconds: int = 900
    video_start_clock: str | None = None


@dataclass
class VideoConfig:
    frame_stride: int = 1
    start_seconds: float = 0.0
    end_seconds: float | None = None
    resize_width: int | None = None


@dataclass
class OutputConfig:
    dir: str = "outputs"
    save_video: bool = True
    video_codec: str = "mp4v"
    draw_boxes: bool = True
    draw_trails: bool = True
    csv: bool = True
    json_summary: bool = True


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    counting: CountingConfig = field(default_factory=CountingConfig)
    intervals: IntervalsConfig = field(default_factory=IntervalsConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def validate_config(cfg: Config) -> None:
    """Validate configuration parameters and raise ValueError mentioning the key if invalid."""
    # Model
    if not cfg.model.weights:
        raise ValueError("Invalid configuration for 'model.weights': cannot be empty")
    if cfg.model.imgsz <= 0:
        raise ValueError(f"Invalid configuration for 'model.imgsz': must be > 0, got {cfg.model.imgsz}")
    if not (0.0 < cfg.model.conf <= 1.0):
        raise ValueError(f"Invalid configuration for 'model.conf': must be in (0, 1], got {cfg.model.conf}")
    if not (0.0 < cfg.model.iou <= 1.0):
        raise ValueError(f"Invalid configuration for 'model.iou': must be in (0, 1], got {cfg.model.iou}")
    if not cfg.model.classes or not isinstance(cfg.model.classes, dict):
        raise ValueError("Invalid configuration for 'model.classes': must be a non-empty mapping of name to int ID")
    for name, cid in cfg.model.classes.items():
        if not isinstance(cid, int) or cid < 0:
            raise ValueError(f"Invalid configuration for 'model.classes.{name}': class id must be a non-negative int, got {cid}")

    # Tracker
    if cfg.tracker.type not in ("bytetrack", "botsort"):
        raise ValueError(
            f"Invalid configuration for 'tracker.type': must be 'bytetrack' or 'botsort', got '{cfg.tracker.type}'"
        )
    if cfg.tracker.track_buffer <= 0:
        raise ValueError(
            f"Invalid configuration for 'tracker.track_buffer': must be > 0, got {cfg.tracker.track_buffer}"
        )

    # Counting
    if cfg.counting.parallel_offset_px <= 0:
        raise ValueError(
            f"Invalid configuration for 'counting.parallel_offset_px': must be > 0, got {cfg.counting.parallel_offset_px}"
        )
    if cfg.counting.mode not in ("gated", "simple"):
        raise ValueError(
            f"Invalid configuration for 'counting.mode': must be 'gated' or 'simple', got '{cfg.counting.mode}'"
        )
    if cfg.counting.min_track_frames < 1:
        raise ValueError(
            f"Invalid configuration for 'counting.min_track_frames': must be >= 1, got {cfg.counting.min_track_frames}"
        )
    if cfg.counting.count_point not in ("bottom_center", "center"):
        raise ValueError(
            f"Invalid configuration for 'counting.count_point': must be 'bottom_center' or 'center', got '{cfg.counting.count_point}'"
        )
    if "a_to_b" not in cfg.counting.direction_labels or "b_to_a" not in cfg.counting.direction_labels:
        raise ValueError("Invalid configuration for 'counting.direction_labels': must define 'a_to_b' and 'b_to_a'")

    # Intervals
    if cfg.intervals.length_seconds <= 0:
        raise ValueError(
            f"Invalid configuration for 'intervals.length_seconds': must be > 0, got {cfg.intervals.length_seconds}"
        )

    # Video
    if cfg.video.frame_stride < 1:
        raise ValueError(
            f"Invalid configuration for 'video.frame_stride': must be >= 1, got {cfg.video.frame_stride}"
        )
    if cfg.video.start_seconds < 0:
        raise ValueError(
            f"Invalid configuration for 'video.start_seconds': must be >= 0, got {cfg.video.start_seconds}"
        )
    if cfg.video.end_seconds is not None and cfg.video.end_seconds <= cfg.video.start_seconds:
        raise ValueError(
            f"Invalid configuration for 'video.end_seconds': must be > start_seconds ({cfg.video.start_seconds}), got {cfg.video.end_seconds}"
        )


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge dictionary `override` into `base`."""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> Config:
    """Load configuration from a YAML file, apply any dictionary overrides, and validate."""
    raw_data: dict[str, Any] = {}
    if path is not None:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Configuration file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content:
                raw_data = content

    if overrides:
        raw_data = _deep_merge_dict(raw_data, overrides)

    model_kwargs = raw_data.get("model", {})
    tracker_kwargs = raw_data.get("tracker", {})
    counting_kwargs = raw_data.get("counting", {})
    intervals_kwargs = raw_data.get("intervals", {})
    video_kwargs = raw_data.get("video", {})
    output_kwargs = raw_data.get("output", {})

    cfg = Config(
        model=ModelConfig(**model_kwargs),
        tracker=TrackerConfig(**tracker_kwargs),
        counting=CountingConfig(**counting_kwargs),
        intervals=IntervalsConfig(**intervals_kwargs),
        video=VideoConfig(**video_kwargs),
        output=OutputConfig(**output_kwargs),
    )
    validate_config(cfg)
    return cfg
