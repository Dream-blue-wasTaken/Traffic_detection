import pytest
from vcount.counter import CountEvent
from vcount.intervals import bucket_events, format_seconds_to_hms


def test_format_seconds_to_hms():
    assert format_seconds_to_hms(0) == "00:00:00"
    assert format_seconds_to_hms(65) == "00:01:05"
    assert format_seconds_to_hms(3661) == "01:01:01"


def test_bucket_events_boundaries_and_empty_intervals():
    events = [
        # Exactly before 300s -> interval 0
        CountEvent(track_id=1, class_name="car", direction="entry", frame_idx=10, timestamp_s=299.99, position=(0, 0)),
        # Exactly at 300s -> interval 1
        CountEvent(track_id=2, class_name="truck", direction="exit", frame_idx=20, timestamp_s=300.0, position=(0, 0)),
        # In interval 3 (900s to 1200s) -> interval 2 is empty!
        CountEvent(track_id=3, class_name="car", direction="entry", frame_idx=30, timestamp_s=950.0, position=(0, 0)),
    ]

    # Total duration 1200s (4 intervals of 300s: 0, 1, 2, 3)
    df_wide, df_long = bucket_events(
        events=events,
        interval_s=300,
        duration_s=1200.0,
        all_directions=["entry", "exit"],
        all_classes=["car", "truck"],
    )

    # 4 intervals
    assert len(df_wide) == 4
    # Long format: 4 intervals * 2 directions * 2 classes = 16 rows
    assert len(df_long) == 16

    # Interval 0: entry_car = 1
    assert df_wide.iloc[0]["entry_car"] == 1
    assert df_wide.iloc[0]["exit_truck"] == 0
    assert df_wide.iloc[0]["total"] == 1

    # Interval 1: exit_truck = 1
    assert df_wide.iloc[1]["exit_truck"] == 1
    assert df_wide.iloc[1]["total"] == 1

    # Interval 2 is empty
    assert df_wide.iloc[2]["total"] == 0

    # Interval 3: entry_car = 1
    assert df_wide.iloc[3]["entry_car"] == 1
    assert df_wide.iloc[3]["total"] == 1

    # Grand total across all intervals equals sum of events
    assert df_wide["total"].sum() == len(events)
    assert df_wide["entry_total"].sum() == 2
    assert df_wide["exit_total"].sum() == 1


def test_video_start_clock():
    events = [
        CountEvent(track_id=1, class_name="car", direction="entry", frame_idx=1, timestamp_s=10.0, position=(0, 0)),
    ]
    df_wide, df_long = bucket_events(
        events=events,
        interval_s=60,
        duration_s=120.0,
        video_start_clock="2024-01-01 08:00:00",
    )
    assert "clock_start" in df_wide.columns
    assert df_wide.iloc[0]["clock_start"] == "2024-01-01 08:00:00"
    assert df_wide.iloc[1]["clock_start"] == "2024-01-01 08:01:00"
