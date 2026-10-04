"""Video I/O helpers: metadata extraction, first frame reading, and video writing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator
import math
import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@dataclass
class VideoInfo:
    fps: float
    frame_count: int
    width: int
    height: int
    duration_s: float


def get_video_info(path: str | Path) -> VideoInfo:
    """Read metadata from a video file.

    Raises FileNotFoundError if file is missing, ValueError if video cannot be opened
    or has invalid FPS / duration metadata.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Video file not found: {p}")

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {p}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    if fps is None or math.isnan(fps) or fps <= 0:
        raise ValueError(
            f"Corrupt or missing FPS ({fps}) in video metadata for '{p.name}'. "
            f"Please re-encode with: ffmpeg -i \"{p}\" -c:v libx264 \"{p.stem}_fixed.mp4\""
        )

    duration_s = (frame_count / fps) if frame_count > 0 else 0.0

    return VideoInfo(
        fps=float(fps),
        frame_count=frame_count,
        width=width,
        height=height,
        duration_s=duration_s,
    )


def read_first_frame(path: str | Path, start_seconds: float = 0.0) -> np.ndarray:
    """Read the first frame (or frame at start_seconds) from the video."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Video file not found: {p}")

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {p}")

    if start_seconds > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_seconds * 1000.0)

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise ValueError(f"Could not read any frame from video: {p}")

    return frame


class VideoWriterContext:
    """Context manager for OpenCV VideoWriter that guarantees proper resource cleanup."""

    def __init__(
        self,
        output_path: str | Path,
        fps: float,
        width: int,
        height: int,
        codec: str = "mp4v",
    ):
        self.output_path = Path(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        self.codec = codec
        self.writer: cv2.VideoWriter | None = None

    def __enter__(self) -> VideoWriterContext:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            (self.width, self.height),
        )
        if not self.writer.isOpened():
            # Fallback to mp4v or XVID if specific fourcc failed
            fallback_fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(
                str(self.output_path),
                fallback_fourcc,
                self.fps,
                (self.width, self.height),
            )
            if not self.writer.isOpened():
                raise RuntimeError(f"Failed to initialize VideoWriter for '{self.output_path}'")
        return self

    def write(self, frame: np.ndarray) -> None:
        if self.writer is not None and self.writer.isOpened():
            self.writer.write(frame)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.writer is not None:
            self.writer.release()
            self.writer = None
