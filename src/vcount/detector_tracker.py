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


def compute_box_iou(box1: tuple[float, float, float, float], box2: tuple[float, float, float, float]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes."""
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


def track_video(
    video_path: str | Path,
    cfg: Config,
    model: YOLO | None = None,
) -> Generator[FrameResult, None, None]:
    """Track vehicles in video using Ultralytics YOLO model.track().

    Supports ensemble tracking: simultaneously tracks standard vehicles
    (cars, motorcycles, buses, trucks) via the primary model and auto-rickshaws
    via the specialized fine-tuned model (if autorickshaw_weights is configured).
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

    # Check for ensemble auto-rickshaw model
    rickshaw_model: YOLO | None = None
    rickshaw_weights = getattr(cfg.model, "autorickshaw_weights", None)
    if rickshaw_weights and Path(rickshaw_weights).is_file():
        try:
            rickshaw_model = load_model(rickshaw_weights)
            logger.info(f"Loaded ensemble auto-rickshaw model from {rickshaw_weights}")
        except Exception as e:
            logger.warning(f"Could not load ensemble auto-rickshaw weights {rickshaw_weights}: {e}")

    logger.info(
        f"Starting tracking on {video_p.name} with model={cfg.model.weights}, device={device}, "
        f"half={half}, tracker={cfg.tracker.type}, stride={cfg.video.frame_stride}, "
        f"ensemble={'enabled' if rickshaw_model else 'disabled'}"
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

    rickshaw_gen = None
    if rickshaw_model is not None:
        rickshaw_conf = getattr(cfg.model, "autorickshaw_conf", 0.25)
        rickshaw_gen = rickshaw_model.track(
            source=str(video_p),
            stream=True,
            persist=True,
            tracker=tracker_yaml,
            conf=rickshaw_conf,
            iou=cfg.model.iou,
            imgsz=cfg.model.imgsz,
            classes=[0],
            device=device,
            half=half,
            verbose=False,
            vid_stride=cfg.video.frame_stride,
        )

    stride = cfg.video.frame_stride
    stream_iter = zip(results_gen, rickshaw_gen) if rickshaw_gen is not None else ((r, None) for r in results_gen)

    for loop_i, (r, r_rick) in enumerate(stream_iter):
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

        # 1. Collect Primary Model Detections (Cars, Bikes, Buses, Trucks)
        primary_objects: list[TrackedObject] = []
        if r.boxes is not None and r.boxes.id is not None:
            ids = r.boxes.id.int().cpu().tolist()
            clss = r.boxes.cls.int().cpu().tolist()
            confs = r.boxes.conf.cpu().tolist()
            xyxys = r.boxes.xyxy.cpu().tolist()

            for tid, cid, cf, box in zip(ids, clss, confs, xyxys):
                cname = id_to_name.get(cid, model.names.get(cid, f"class_{cid}"))
                primary_objects.append(
                    TrackedObject(
                        track_id=int(tid),
                        class_id=int(cid),
                        class_name=cname,
                        conf=float(cf),
                        xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                    )
                )

        # 2. Collect Ensemble Auto-Rickshaw Detections
        rickshaw_objects: list[TrackedObject] = []
        if r_rick is not None and r_rick.boxes is not None and r_rick.boxes.id is not None:
            r_ids = r_rick.boxes.id.int().cpu().tolist()
            r_confs = r_rick.boxes.conf.cpu().tolist()
            r_xyxys = r_rick.boxes.xyxy.cpu().tolist()

            for r_tid, r_cf, r_box in zip(r_ids, r_confs, r_xyxys):
                # Offset track_id by 100,000 to prevent ID collision with primary tracker
                rickshaw_objects.append(
                    TrackedObject(
                        track_id=int(r_tid) + 100000,
                        class_id=100,
                        class_name="autorickshaw",
                        conf=float(r_cf),
                        xyxy=(float(r_box[0]), float(r_box[1]), float(r_box[2]), float(r_box[3])),
                    )
                )

        # 3. Cross-Model Suppression: If a standard vehicle box heavily overlaps with an
        # auto-rickshaw (IoU > 0.40), suppress the standard vehicle (prevent misclassifying auto as car/bike)
        filtered_primary: list[TrackedObject] = []
        for p_obj in primary_objects:
            overlaps_with_rickshaw = any(
                compute_box_iou(p_obj.xyxy, r_obj.xyxy) > 0.40 for r_obj in rickshaw_objects
            )
            if not overlaps_with_rickshaw:
                filtered_primary.append(p_obj)

        final_objects = filtered_primary + rickshaw_objects

        yield FrameResult(
            frame_idx=original_frame_idx,
            timestamp_s=timestamp_s,
            frame=frame,
            objects=final_objects,
        )

