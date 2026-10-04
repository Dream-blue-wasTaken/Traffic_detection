import pytest
import numpy as np
import cv2
from vcount.video_io import VideoWriterContext, get_video_info, read_first_frame


def test_video_writer_and_info(tmp_path):
    video_path = tmp_path / "test_video.mp4"
    w, h, fps, num_frames = 320, 240, 25.0, 50

    with VideoWriterContext(video_path, fps=fps, width=w, height=h, codec="mp4v") as writer:
        for i in range(num_frames):
            frame = np.full((h, w, 3), (i * 5) % 255, dtype=np.uint8)
            writer.write(frame)

    assert video_path.exists()

    info = get_video_info(video_path)
    assert info.width == w
    assert info.height == h
    assert pytest.approx(info.fps, abs=1.0) == fps
    assert info.frame_count == num_frames
    assert pytest.approx(info.duration_s, abs=0.1) == 2.0

    first_frame = read_first_frame(video_path)
    assert first_frame.shape == (h, w, 3)
