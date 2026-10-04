"""Time-bucket aggregation for counting events into tidy long and wide pivot formats."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import pandas as pd

from vcount.counter import CountEvent


def format_seconds_to_hms(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def bucket_events(
    events: list[CountEvent],
    interval_s: int,
    duration_s: float,
    all_directions: list[str] | None = None,
    all_classes: list[str] | None = None,
    video_start_clock: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate individual CountEvents into fixed duration intervals.

    Returns:
        (df_wide, df_long): Continuous DataFrame tables including empty intervals.
    """
    if interval_s <= 0:
        raise ValueError(f"interval_s must be > 0, got {interval_s}")

    max_t = max([e.timestamp_s for e in events], default=0.0)
    effective_duration = max(duration_s, max_t)
    num_intervals = max(1, math.ceil(effective_duration / interval_s))

    directions = list(all_directions) if all_directions else sorted({e.direction for e in events} or ["entry", "exit"])
    classes = list(all_classes) if all_classes else sorted({e.class_name for e in events} or ["car", "truck"])

    base_clock: datetime | None = None
    if video_start_clock:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S"):
            try:
                base_clock = datetime.strptime(video_start_clock, fmt)
                break
            except ValueError:
                pass

    # 1. Build Tidy Long format with all interval x direction x class combinations
    long_rows: list[dict] = []
    # Count tally: (interval_idx, direction, class_name) -> count
    counts_map: dict[tuple[int, str, str], int] = {}
    for e in events:
        idx = min(int(e.timestamp_s // interval_s), num_intervals - 1)
        key = (idx, e.direction, e.class_name)
        counts_map[key] = counts_map.get(key, 0) + 1

    for idx in range(num_intervals):
        start_sec = idx * interval_s
        end_sec = min((idx + 1) * interval_s, effective_duration)
        start_hms = format_seconds_to_hms(start_sec)
        end_hms = format_seconds_to_hms(end_sec)

        clock_start_str = (base_clock + timedelta(seconds=start_sec)).strftime("%Y-%m-%d %H:%M:%S") if base_clock else None
        clock_end_str = (base_clock + timedelta(seconds=end_sec)).strftime("%Y-%m-%d %H:%M:%S") if base_clock else None

        for d in directions:
            for c in classes:
                cnt = counts_map.get((idx, d, c), 0)
                row = {
                    "interval_idx": idx,
                    "interval_start": start_hms,
                    "interval_end": end_hms,
                    "direction": d,
                    "class_name": c,
                    "count": cnt,
                }
                if clock_start_str and clock_end_str:
                    row["clock_start"] = clock_start_str
                    row["clock_end"] = clock_end_str
                long_rows.append(row)

    df_long = pd.DataFrame(long_rows)

    # 2. Build Wide Pivot format
    wide_rows: list[dict] = []
    for idx in range(num_intervals):
        start_sec = idx * interval_s
        end_sec = min((idx + 1) * interval_s, effective_duration)
        start_hms = format_seconds_to_hms(start_sec)
        end_hms = format_seconds_to_hms(end_sec)

        row = {
            "interval_idx": idx,
            "interval_start": start_hms,
            "interval_end": end_hms,
        }
        if base_clock:
            row["clock_start"] = (base_clock + timedelta(seconds=start_sec)).strftime("%Y-%m-%d %H:%M:%S")
            row["clock_end"] = (base_clock + timedelta(seconds=end_sec)).strftime("%Y-%m-%d %H:%M:%S")

        dir_totals: dict[str, int] = {d: 0 for d in directions}
        grand_total = 0

        for d in directions:
            for c in classes:
                col_name = f"{d}_{c}"
                cnt = counts_map.get((idx, d, c), 0)
                row[col_name] = cnt
                dir_totals[d] += cnt
                grand_total += cnt

        for d in directions:
            row[f"{d}_total"] = dir_totals[d]
        row["total"] = grand_total

        wide_rows.append(row)

    df_wide = pd.DataFrame(wide_rows)
    return df_wide, df_long
