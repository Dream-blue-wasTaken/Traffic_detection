"""Detector and tracker wrapper around Ultralytics YOLO with ByteTrack and BoT-SORT."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator
import logging
import tempfile
import cv2
import numpy as np
import torch
import yaml
from ultralytics import YOLO

from vcount.config import Config
from vcount.video_io import get_video_info

logger = logging.getLogger(__name__)


@dataclass
class TrackedObject:
    track_id: int
    class_id: int
    class_name: str
    conf: float
    xyxy: tuple[float, float, float, float]


@dataclass
class FrameResult:
    frame_idx: int  # index in ORIGINAL video
    timestamp_s: float  # frame_idx / fps
    frame: np.ndarray  # original BGR frame
    objects: list[TrackedObject]


def resolve_device(device_str: str) -> str:
    """Resolve 'auto', 'cpu', 'cuda:0', 'mps' to concrete available device."""
    if device_str == "auto":
        if torch.cuda.is_available():
            return "cuda:0"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return device_str


def get_tracker_yaml_path(
    tracker_type: str = "bytetrack",
    track_buffer: int = 30,
    yaml_override: str | None = None,
) -> str:
    """Return path to tracker YAML, creating a customized copy if track_buffer differs from default."""
    if yaml_override:
        p = Path(yaml_override)
        if not p.is_file():
            raise FileNotFoundError(f"Custom tracker YAML not found: {p}")
        return str(p)

    import ultralytics

    trackers_dir = Path(ultralytics.__file__).parent / "cfg" / "trackers"
    base_yaml = trackers_dir / f"{tracker_type}.yaml"
    if not base_yaml.is_file():
        base_yaml = trackers_dir / "bytetrack.yaml"

    with open(base_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data.get("track_buffer") != track_buffer:
        data["track_buffer"] = track_buffer
        tmp_dir = Path(tempfile.gettempdir()) / "vcount_trackers"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = tmp_dir / f"{tracker_type}_buf_{track_buffer}.yaml"
        with open(tmp_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        return str(tmp_file)

    return str(base_yaml)


def load_model(weights: str) -> YOLO:
    """Load YOLO model from weights file or pretrained identifier."""
    return YOLO(weights)


def track_video(
    video_path: str | Path,
    cfg: Config,
    model: YOLO | None = None,
) -> Generator[FrameResult, None, None]:
    """Track vehicles in video using Ultralytics YOLO model.track().

    Yields FrameResult for each processed frame.
    """
    video_p = Path(video_path)
    if not video_p.is_file():
        raise FileNotFoundError(f"Video not found: {video_p}")

    info = get_video_info(video_p)
    device = resolve_device(cfg.model.device)
    half = cfg.model.half if device != "cpu" else False

    if model is None:
        model = load_model(cfg.model.weights)

    tracker_yaml = get_tracker_yaml_path(
        tracker_type=cfg.tracker.type,
        track_buffer=cfg.tracker.track_buffer,
        yaml_override=cfg.tracker.yaml_override,
    )

    classes_to_track = list(cfg.model.classes.values())
    id_to_name = {cid: name for name, cid in cfg.model.classes.items()}

    logger.info(
        f"Starting tracking on {video_p.name} with model={cfg.model.weights}, device={device}, "
        f"half={half}, tracker={cfg.tracker.type}, stride={cfg.video.frame_stride}"
    )

    results_gen = model.track(
        source=str(video_p),
        stream=True,
        persist=True,
        tracker=tracker_yaml,
        conf=cfg.model.conf,
        iou=cfg.model.iou,
        imgsz=cfg.model.imgsz,
        classes=classes_to_track if classes_to_track else None,
        device=device,
        half=half,
        verbose=False,
        vid_stride=cfg.video.frame_stride,
    )

    stride = cfg.video.frame_stride
    for loop_i, r in enumerate(results_gen):
        original_frame_idx = loop_i * stride
        timestamp_s = original_frame_idx / info.fps if info.fps > 0 else 0.0

        if timestamp_s < cfg.video.start_seconds:
            continue
        if cfg.video.end_seconds is not None and timestamp_s > cfg.video.end_seconds:
            break

        frame = r.orig_img
        if frame is None:
            continue

        if cfg.video.resize_width is not None and cfg.video.resize_width > 0:
            h, w = frame.shape[:2]
            scale = cfg.video.resize_width / float(w)
            new_h = int(h * scale)
            frame = cv2.resize(frame, (cfg.video.resize_width, new_h))

        objects: list[TrackedObject] = []
        if r.boxes is not None and r.boxes.id is not None:
            ids = r.boxes.id.int().cpu().tolist()
            clss = r.boxes.cls.int().cpu().tolist()
            confs = r.boxes.conf.cpu().tolist()
            xyxys = r.boxes.xyxy.cpu().tolist()

            for tid, cid, cf, box in zip(ids, clss, confs, xyxys):
                cname = id_to_name.get(cid, model.names.get(cid, f"class_{cid}"))
                objects.append(
                    TrackedObject(
                        track_id=int(tid),
                        class_id=int(cid),
                        class_name=cname,
                        conf=float(cf),
                        xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                    )
                )

        yield FrameResult(
            frame_idx=original_frame_idx,
            timestamp_s=timestamp_s,
            frame=frame,
            objects=objects,
        )
