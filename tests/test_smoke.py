"""End-to-end smoke tests on synthetic video."""

from pathlib import Path
import cv2
import numpy as np
import pytest

from vcount.config import load_config
from vcount.line_setup import CountingLine
from vcount.pipeline import run_pipeline
from vcount.video_io import VideoWriterContext


def create_synthetic_moving_box_video(path: Path, width: int = 320, height: int = 240, num_frames: int = 25):
    with VideoWriterContext(path, fps=25.0, width=width, height=height, codec="mp4v") as writer:
        for i in range(num_frames):
            frame = np.full((height, width, 3), 40, dtype=np.uint8)
            # Draw moving rectangle from top to bottom
            box_y = int((i / float(num_frames)) * (height - 40))
            cv2.rectangle(frame, (120, box_y), (180, box_y + 35), (200, 200, 200), -1)
            writer.write(frame)


@pytest.mark.slow
def test_pipeline_smoke_end_to_end(tmp_path):
    video_path = tmp_path / "smoke_clip.mp4"
    create_synthetic_moving_box_video(video_path, width=320, height=240, num_frames=20)

    cfg = load_config(
        overrides={
            "model": {"weights": "yolo26n.pt", "imgsz": 320, "conf": 0.25},
            "output": {"dir": str(tmp_path / "outputs"), "save_video": True},
            "intervals": {"length_seconds": 60},
        }
    )

    line = CountingLine(p1=(10.0, 120.0), p2=(310.0, 120.0), offset_px=30.0)

    result = run_pipeline(video_path=video_path, cfg=cfg, line=line)

    assert result.output_dir.is_dir()
    assert (result.output_dir / "counts_by_interval.csv").is_file()
    assert (result.output_dir / "events.csv").is_file()
    assert (result.output_dir / "summary.json").is_file()
    assert (result.output_dir / "config_used.yaml").is_file()
    assert result.summary["processed_frames"] > 0


def test_streamlit_app_loads():
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "src" / "vcount" / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception
    assert len(at.title) > 0
    assert "Vehicle Counting System" in at.title[0].value

