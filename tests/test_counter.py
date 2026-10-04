import pytest
import numpy as np
from vcount.config import CountingConfig
from vcount.counter import LineCounter, CountEvent
from vcount.detector_tracker import FrameResult, TrackedObject
from vcount.line_setup import CountingLine


def make_frame_result(frame_idx: int, timestamp_s: float, objects: list[TrackedObject]) -> FrameResult:
    dummy_frame = np.zeros((10, 10, 3), dtype=np.uint8)
    return FrameResult(frame_idx=frame_idx, timestamp_s=timestamp_s, frame=dummy_frame, objects=objects)


def make_box(cx: float, cy: float, w: float = 20.0, h: float = 20.0) -> tuple[float, float, float, float]:
    # cx, cy center; bottom_center will be (cx, cy + h/2)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def test_left_to_right_crossing_simple():
    # Horizontal line along y=100 from x=0 to x=200
    # Line p1=(0, 100), p2=(200, 100).
    # Side A (negative): points with y < 100
    # Side B (positive): points with y > 100
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=30.0)
    cfg = CountingConfig(mode="simple", min_track_frames=2)
    counter = LineCounter(line, cfg, class_names={2: "car"})

    # Frame 0: y=50 (Side A)
    res0 = make_frame_result(0, 0.0, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 40.0, 20.0, 20.0))  # bottom y = 50
    ])
    # Frame 1: y=80 (Side A)
    res1 = make_frame_result(1, 0.1, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 70.0, 20.0, 20.0))  # bottom y = 80
    ])
    # Frame 2: y=130 (Side B) -> crossed A to B
    res2 = make_frame_result(2, 0.2, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 120.0, 20.0, 20.0))  # bottom y = 130
    ])

    events0 = counter.update(res0)
    events1 = counter.update(res1)
    events2 = counter.update(res2)

    assert len(events0) == 0
    assert len(events1) == 0
    assert len(events2) == 1
    assert events2[0].direction == "entry"
    assert events2[0].class_name == "car"
    assert events2[0].track_id == 1
    assert counter.total_count == 1
    assert counter.totals()["entry"]["car"] == 1


def test_right_to_left_crossing_simple():
    # Moving from Side B (y > 100) to Side A (y < 100)
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=30.0)
    cfg = CountingConfig(mode="simple", min_track_frames=2)
    counter = LineCounter(line, cfg, class_names={2: "car"})

    res0 = make_frame_result(0, 0.0, [
        TrackedObject(track_id=5, class_id=2, class_name="car", conf=0.85, xyxy=make_box(100.0, 140.0, 20.0, 20.0))  # bottom y = 150 (Side B)
    ])
    res1 = make_frame_result(1, 0.1, [
        TrackedObject(track_id=5, class_id=2, class_name="car", conf=0.85, xyxy=make_box(100.0, 110.0, 20.0, 20.0))  # bottom y = 120 (Side B)
    ])
    res2 = make_frame_result(2, 0.2, [
        TrackedObject(track_id=5, class_id=2, class_name="car", conf=0.85, xyxy=make_box(100.0, 70.0, 20.0, 20.0))  # bottom y = 80 (Side A)
    ])

    counter.update(res0)
    counter.update(res1)
    events = counter.update(res2)

    assert len(events) == 1
    assert events[0].direction == "exit"
    assert counter.totals()["exit"]["car"] == 1


def test_jitter_does_not_double_count():
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=30.0)
    cfg = CountingConfig(mode="simple", min_track_frames=2)
    counter = LineCounter(line, cfg, class_names={2: "car"})

    # Vehicle approaches, crosses once, then wanders back and forth
    positions = [80.0, 95.0, 115.0, 95.0, 110.0, 90.0]
    total_events = []
    for idx, pos_y in enumerate(positions):
        res = make_frame_result(idx, idx * 0.1, [
            TrackedObject(track_id=10, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, pos_y - 10, 20.0, 20.0))
        ])
        total_events.extend(counter.update(res))

    assert len(total_events) == 1
    assert counter.total_count == 1


def test_min_track_frames_ignored_if_too_short():
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=30.0)
    cfg = CountingConfig(mode="simple", min_track_frames=4)
    counter = LineCounter(line, cfg, class_names={2: "car"})

    # Track appears at frame 0 (y=80), crosses at frame 1 (y=120) -> n_frames = 2 < 4
    res0 = make_frame_result(0, 0.0, [
        TrackedObject(track_id=99, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 70.0, 20.0, 20.0))
    ])
    res1 = make_frame_result(1, 0.1, [
        TrackedObject(track_id=99, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 110.0, 20.0, 20.0))
    ])
    assert len(counter.update(res0)) == 0
    assert len(counter.update(res1)) == 0
    assert counter.total_count == 0


def test_class_majority_voting():
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=30.0)
    cfg = CountingConfig(mode="simple", min_track_frames=3)
    counter = LineCounter(line, cfg, class_names={2: "car", 7: "truck"})

    # Votes: car (conf=0.8), car (conf=0.8), truck (conf=0.7) -> Majority should be car
    res0 = make_frame_result(0, 0.0, [
        TrackedObject(track_id=7, class_id=2, class_name="car", conf=0.8, xyxy=make_box(100.0, 60.0, 20.0, 20.0))
    ])
    res1 = make_frame_result(1, 0.1, [
        TrackedObject(track_id=7, class_id=2, class_name="car", conf=0.8, xyxy=make_box(100.0, 80.0, 20.0, 20.0))
    ])
    res2 = make_frame_result(2, 0.2, [
        TrackedObject(track_id=7, class_id=7, class_name="truck", conf=0.7, xyxy=make_box(100.0, 120.0, 20.0, 20.0))
    ])

    counter.update(res0)
    counter.update(res1)
    events = counter.update(res2)

    assert len(events) == 1
    assert events[0].class_name == "car"


def test_gated_mode_standard_and_fallback():
    # Offset is 50 px.
    # Side A: y < 100, Gate A is at y = 50 (dist = -50)
    # Side B: y > 100, Gate B is at y = 150 (dist = +50)
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=50.0)
    cfg = CountingConfig(mode="gated", min_track_frames=3)
    counter = LineCounter(line, cfg, class_names={2: "car"})

    # Track 1: Normal gated flow (touches Gate A at y <= 50, then crosses mid-line y=100)
    # Frame 0: y = 40 (gate A touched!)
    counter.update(make_frame_result(0, 0.0, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 30.0, 20.0, 20.0))
    ]))
    # Frame 1: y = 70
    counter.update(make_frame_result(1, 0.1, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 60.0, 20.0, 20.0))
    ]))
    # Frame 2: y = 110 (crosses to Side B)
    events1 = counter.update(make_frame_result(2, 0.2, [
        TrackedObject(track_id=1, class_id=2, class_name="car", conf=0.9, xyxy=make_box(100.0, 100.0, 20.0, 20.0))
    ]))
    assert len(events1) == 1
    assert events1[0].direction == "entry"

    # Track 2: Spawned between Gate A and mid-line (y=75), never touched Gate A, crosses to y=120
    # Should trigger fallback count
    counter.update(make_frame_result(3, 0.3, [
        TrackedObject(track_id=2, class_id=2, class_name="car", conf=0.9, xyxy=make_box(50.0, 65.0, 20.0, 20.0))
    ]))
    counter.update(make_frame_result(4, 0.4, [
        TrackedObject(track_id=2, class_id=2, class_name="car", conf=0.9, xyxy=make_box(50.0, 80.0, 20.0, 20.0))
    ]))
    counter.update(make_frame_result(5, 0.5, [
        TrackedObject(track_id=2, class_id=2, class_name="car", conf=0.9, xyxy=make_box(50.0, 90.0, 20.0, 20.0))
    ]))
    events2 = counter.update(make_frame_result(6, 0.6, [
        TrackedObject(track_id=2, class_id=2, class_name="car", conf=0.9, xyxy=make_box(50.0, 120.0, 20.0, 20.0))
    ]))
    assert len(events2) == 1
    assert events2[0].direction == "entry"
    assert counter.total_count == 2
