"""Visual annotations: bounding boxes, track trails, counting lines, and HUD overlay."""

from __future__ import annotations

from collections import deque
import cv2
import numpy as np

from vcount.config import Config
from vcount.counter import CountEvent, LineCounter
from vcount.detector_tracker import FrameResult
from vcount.intervals import format_seconds_to_hms
from vcount.line_setup import CountingLine, gate_lines


# Distinct, visually appealing palette (BGR)
CLASS_COLORS = {
    "car": (255, 128, 0),        # Cyan/Blue
    "motorcycle": (0, 215, 255), # Amber / Gold
    "bus": (0, 165, 255),        # Orange
    "truck": (50, 205, 50),      # Lime Green
    "bicycle": (255, 0, 255),    # Magenta
}


class FrameAnnotator:
    """Manages trail history, flash states, and draws clean visual overlays."""

    def __init__(self, line: CountingLine, cfg: Config):
        self.line = line
        self.cfg = cfg
        self.trails: dict[int, deque[tuple[int, int]]] = {}
        self.flash_frames_remaining: int = 0
        self.gate_lines_cache: tuple | None = None
        try:
            self.gate_lines_cache = gate_lines(line)
        except ValueError:
            pass

    def register_events(self, events: list[CountEvent]) -> None:
        if events:
            self.flash_frames_remaining = 6

    def draw(
        self,
        frame_result: FrameResult,
        counter: LineCounter,
        fps_estimate: float = 0.0,
    ) -> np.ndarray:
        """Annotate frame with lines, boxes, trails, and HUD."""
        out = frame_result.frame.copy()
        h, w = out.shape[:2]

        # 1. Draw Gate lines and Mid-line
        if self.gate_lines_cache is not None:
            (g1_a, g2_a), (g1_b, g2_b) = self.gate_lines_cache
            cv2.line(
                out,
                (int(g1_a[0]), int(g1_a[1])),
                (int(g2_a[0]), int(g2_a[1])),
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )
            cv2.line(
                out,
                (int(g1_b[0]), int(g1_b[1])),
                (int(g2_b[0]), int(g2_b[1])),
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )

        # Mid-line (Yellow; thicker and brighter when flashing)
        mid_p1 = (int(self.line.p1[0]), int(self.line.p1[1]))
        mid_p2 = (int(self.line.p2[0]), int(self.line.p2[1]))
        if self.flash_frames_remaining > 0:
            line_thickness = 5
            line_color = (0, 255, 255)
            self.flash_frames_remaining -= 1
        else:
            line_thickness = 2
            line_color = (0, 215, 255)

        cv2.line(out, mid_p1, mid_p2, line_color, line_thickness, cv2.LINE_AA)
        cv2.circle(out, mid_p1, 4, (0, 255, 0), -1)
        cv2.circle(out, mid_p2, 4, (0, 0, 255), -1)

        # 2. Draw Trails & Detections
        active_ids = set()
        for obj in frame_result.objects:
            active_ids.add(obj.track_id)
            color = CLASS_COLORS.get(obj.class_name, (200, 200, 200))
            x1, y1, x2, y2 = [int(v) for v in obj.xyxy]
            cx, cy = int((x1 + x2) / 2), y2 if self.cfg.counting.count_point == "bottom_center" else int((y1 + y2) / 2)

            # Update trail
            if obj.track_id not in self.trails:
                self.trails[obj.track_id] = deque(maxlen=30)
            self.trails[obj.track_id].append((cx, cy))

            # Draw trail points
            if self.cfg.output.draw_trails:
                pts = list(self.trails[obj.track_id])
                for idx in range(1, len(pts)):
                    alpha = idx / len(pts)
                    thickness = max(1, int(2 * alpha))
                    cv2.line(out, pts[idx - 1], pts[idx], color, thickness, cv2.LINE_AA)

            # Draw bounding box
            if self.cfg.output.draw_boxes:
                cv2.rectangle(out, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
                # Label badge
                label = f"{obj.class_name} #{obj.track_id} {obj.conf:.2f}"
                (lw, lh), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                badge_y1 = max(0, y1 - lh - 6)
                badge_y2 = y1
                cv2.rectangle(out, (x1, badge_y1), (x1 + lw + 6, badge_y2), color, -1)
                cv2.putText(
                    out,
                    label,
                    (x1 + 3, badge_y2 - 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (0, 0, 0),
                    1,
                    cv2.LINE_AA,
                )

        # Clean old trails
        stale_trails = [tid for tid in self.trails if tid not in active_ids and len(self.trails[tid]) > 0]
        for tid in stale_trails:
            self.trails[tid].popleft()

        # 3. Draw HUD (Heads-Up Display)
        self._draw_hud(out, frame_result.timestamp_s, counter, fps_estimate)

        return out

    def _draw_hud(
        self,
        frame: np.ndarray,
        timestamp_s: float,
        counter: LineCounter,
        fps: float,
    ) -> None:
        """Render HUD card at top-left corner."""
        hud_w, hud_h = 280, 140
        overlay = frame.copy()
        cv2.rectangle(overlay, (12, 12), (12 + hud_w, 12 + hud_h), (20, 24, 33), -1)
        cv2.rectangle(overlay, (12, 12), (12 + hud_w, 12 + hud_h), (55, 65, 81), 1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        time_str = format_seconds_to_hms(timestamp_s)
        cv2.putText(
            frame,
            f"VCOUNT HUD  |  {time_str}  |  {fps:.1f} FPS",
            (22, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (240, 240, 240),
            1,
            cv2.LINE_AA,
        )
        cv2.line(frame, (22, 42), (12 + hud_w - 10, 42), (80, 90, 110), 1)

        totals = counter.totals()
        y = 62
        for dir_name, cls_map in totals.items():
            dir_total = sum(cls_map.values())
            dir_details = ", ".join(f"{c}:{n}" for c, n in cls_map.items()) if cls_map else "0"
            text = f"{dir_name.capitalize()}: {dir_total} ({dir_details})"
            cv2.putText(frame, text, (22, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
            y += 20

        cv2.line(frame, (22, y + 2), (12 + hud_w - 10, y + 2), (80, 90, 110), 1)
        cv2.putText(
            frame,
            f"Total Count: {counter.total_count}",
            (22, y + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
