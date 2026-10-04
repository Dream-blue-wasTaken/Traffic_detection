"""Core line-crossing vehicle counter supporting simple and gated modes."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import logging
import math

from vcount.config import CountingConfig
from vcount.detector_tracker import FrameResult, TrackedObject
from vcount.line_setup import CountingLine, side_of_line, signed_distance

logger = logging.getLogger(__name__)


@dataclass
class CountEvent:
    track_id: int
    class_name: str
    direction: str  # e.g. "entry" or "exit"
    frame_idx: int
    timestamp_s: float
    position: tuple[float, float]


@dataclass
class TrackState:
    first_seen_frame: int
    last_seen_frame: int
    last_pos: tuple[float, float] | None = None
    last_non_zero_side: float = 0.0
    gate_touched: str | None = None  # "A" or "B"
    counted: bool = False
    n_frames: int = 0
    class_votes: Counter = field(default_factory=Counter)


def get_count_point(xyxy: tuple[float, float, float, float], mode: str = "bottom_center") -> tuple[float, float]:
    """Calculate the tracking reference point from bounding box coordinates."""
    x1, y1, x2, y2 = xyxy
    cx = (x1 + x2) / 2.0
    if mode == "center":
        cy = (y1 + y2) / 2.0
    else:  # "bottom_center"
        cy = y2
    return (cx, cy)


class LineCounter:
    """Manages track states and registers crossing events across a virtual counting line."""

    def __init__(
        self,
        line: CountingLine,
        cfg: CountingConfig,
        class_names: dict[int, str] | None = None,
    ):
        self.line = line
        self.cfg = cfg
        self.class_names = class_names or {}
        self.tracks: dict[int, TrackState] = {}
        self.events: list[CountEvent] = []

        self.dir_a_to_b = self.cfg.direction_labels.get("a_to_b", "entry")
        self.dir_b_to_a = self.cfg.direction_labels.get("b_to_a", "exit")

        # Running counts: {direction: {class_name: count}}
        self._counts: dict[str, dict[str, int]] = {
            self.dir_a_to_b: defaultdict(int),
            self.dir_b_to_a: defaultdict(int),
        }

    def _get_majority_class(self, track_state: TrackState, fallback_name: str) -> str:
        """Return the class name with the highest cumulative confidence votes."""
        if not track_state.class_votes:
            return fallback_name
        best_cid, _ = track_state.class_votes.most_common(1)[0]
        return self.class_names.get(best_cid, fallback_name)

    def _is_duplicate_event(self, event: CountEvent) -> bool:
        """Check if event is a duplicate within the dedup window."""
        if not self.cfg.dedup_enabled:
            return False

        ex, ey = event.position
        for prev in reversed(self.events[-50:]):
            if event.frame_idx - prev.frame_idx > self.cfg.dedup_frames:
                break
            if prev.direction == event.direction and prev.class_name == event.class_name:
                px, py = prev.position
                dist = math.hypot(ex - px, ey - py)
                if dist <= self.cfg.dedup_distance_px:
                    return True
        return False

    def update(self, frame_result: FrameResult) -> list[CountEvent]:
        """Update track states with detections from current frame and return newly fired CountEvents."""
        new_events: list[CountEvent] = []
        frame_idx = frame_result.frame_idx
        timestamp_s = frame_result.timestamp_s

        for obj in frame_result.objects:
            tid = obj.track_id
            pos = get_count_point(obj.xyxy, mode=self.cfg.count_point)
            curr_side = side_of_line(pos, self.line)
            curr_dist = signed_distance(pos, self.line)

            if tid not in self.tracks:
                initial_side = curr_side if abs(curr_dist) >= 1.5 else 0.0
                self.tracks[tid] = TrackState(
                    first_seen_frame=frame_idx,
                    last_seen_frame=frame_idx,
                    last_pos=pos,
                    last_non_zero_side=initial_side,
                    n_frames=1,
                )
            else:
                st = self.tracks[tid]
                st.last_seen_frame = frame_idx
                st.n_frames += 1

            st = self.tracks[tid]
            # Accumulate confidence votes for class stabilization
            st.class_votes[obj.class_id] += obj.conf

            # If already counted, update position and continue
            if st.counted:
                st.last_pos = pos
                continue

            last_pos = st.last_pos
            st.last_pos = pos

            # Need at least 2 points to check crossing
            if last_pos is None:
                continue

            # Need minimum number of frames to count
            if st.n_frames < self.cfg.min_track_frames:
                # Still check and record gate touch in gated mode
                if self.cfg.mode == "gated" and st.gate_touched is None:
                    if curr_dist <= -self.line.offset_px:
                        st.gate_touched = "A"
                    elif curr_dist >= self.line.offset_px:
                        st.gate_touched = "B"
                if abs(curr_dist) >= 1.5:
                    st.last_non_zero_side = curr_side
                continue

            # Update gate touch if in gated mode
            if self.cfg.mode == "gated" and st.gate_touched is None:
                if curr_dist <= -self.line.offset_px:
                    st.gate_touched = "A"
                elif curr_dist >= self.line.offset_px:
                    st.gate_touched = "B"

            # Check for mid-line crossing using last_non_zero_side and curr_side
            crossed = False
            last_side = st.last_non_zero_side

            if abs(curr_dist) >= 1.5:
                if last_side < 0 and curr_side > 0:
                    crossed = True
                elif last_side > 0 and curr_side < 0:
                    crossed = True

            if not crossed:
                if abs(curr_dist) >= 1.5:
                    st.last_non_zero_side = curr_side
                continue

            # Determine direction
            direction: str | None = None

            if self.cfg.mode == "simple":
                if last_side < 0 and curr_side > 0:
                    direction = self.dir_a_to_b
                elif last_side > 0 and curr_side < 0:
                    direction = self.dir_b_to_a

            elif self.cfg.mode == "gated":
                if st.gate_touched == "A" and curr_side > 0:
                    direction = self.dir_a_to_b
                elif st.gate_touched == "B" and curr_side < 0:
                    direction = self.dir_b_to_a
                elif st.gate_touched is None:
                    # Fallback for tracks that appeared between gate and mid-line
                    logger.debug(
                        f"Track {tid} counted via fallback (no gate reached before mid-line crossing)"
                    )
                    if last_side < 0 and curr_side > 0:
                        direction = self.dir_a_to_b
                    elif last_side > 0 and curr_side < 0:
                        direction = self.dir_b_to_a

            if direction is not None:
                majority_class = self._get_majority_class(st, obj.class_name)
                event = CountEvent(
                    track_id=tid,
                    class_name=majority_class,
                    direction=direction,
                    frame_idx=frame_idx,
                    timestamp_s=timestamp_s,
                    position=pos,
                )

                if not self._is_duplicate_event(event):
                    st.counted = True
                    self.events.append(event)
                    new_events.append(event)
                    self._counts[direction][majority_class] += 1
                    logger.info(
                        f"Counted {majority_class} #{tid} moving {direction} at frame {frame_idx} (t={timestamp_s:.2f}s)"
                    )
                else:
                    logger.debug(f"Track {tid} skipped as duplicate count within dedup window")
                    st.counted = True

        return new_events

    def totals(self) -> dict[str, dict[str, int]]:
        """Return running totals: {direction: {class_name: count}}."""
        return {
            d: dict(cls_counts)
            for d, cls_counts in self._counts.items()
        }

    @property
    def total_count(self) -> int:
        """Total count of all vehicles across all directions."""
        return sum(
            sum(c.values())
            for c in self._counts.values()
        )

    def cleanup(self, frame_idx: int, max_unseen_frames: int = 150) -> None:
        """Prune track states that have not been seen for max_unseen_frames to bound memory."""
        stale_ids = [
            tid
            for tid, st in self.tracks.items()
            if (frame_idx - st.last_seen_frame) > max_unseen_frames
        ]
        for tid in stale_ids:
            del self.tracks[tid]
