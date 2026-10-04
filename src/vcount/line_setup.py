"""Line setup, geometry calculations, gate lines generation, and interactive selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import math
import cv2
import numpy as np


@dataclass
class CountingLine:
    p1: tuple[float, float]  # (x, y) start point of mid-line
    p2: tuple[float, float]  # (x, y) end point of mid-line
    offset_px: float = 60.0  # distance of the two gate lines from mid-line

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CountingLine:
        return cls(
            p1=(float(data["p1"][0]), float(data["p1"][1])),
            p2=(float(data["p2"][0]), float(data["p2"][1])),
            offset_px=float(data.get("offset_px", 60.0)),
        )


def side_of_line(point: tuple[float, float], line: CountingLine | tuple[tuple[float, float], tuple[float, float]]) -> float:
    """Signed side of a 2D line using cross product.

    Formula: (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    Returns:
        > 0: Side B (positive side)
        < 0: Side A (negative side)
        == 0: Exactly on the line
    """
    if isinstance(line, CountingLine):
        (x1, y1), (x2, y2) = line.p1, line.p2
    else:
        (x1, y1), (x2, y2) = line
    px, py = point
    return float((x2 - x1) * (py - y1) - (y2 - y1) * (px - x1))


def signed_distance(point: tuple[float, float], line: CountingLine | tuple[tuple[float, float], tuple[float, float]]) -> float:
    """Signed perpendicular distance from point to the line.

    Positive for Side B, negative for Side A.
    """
    if isinstance(line, CountingLine):
        (x1, y1), (x2, y2) = line.p1, line.p2
    else:
        (x1, y1), (x2, y2) = line
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return 0.0
    return side_of_line(point, line) / length


def gate_lines(
    line: CountingLine,
) -> tuple[tuple[tuple[float, float], tuple[float, float]], tuple[tuple[float, float], tuple[float, float]]]:
    """Compute the two parallel gate lines (gate_A, gate_B) offset by ±offset_px.

    gate_A is at signed distance -offset_px (Side A).
    gate_B is at signed distance +offset_px (Side B).
    """
    (x1, y1), (x2, y2) = line.p1, line.p2
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        raise ValueError("Counting line endpoints cannot be identical")

    # Unit normal vector towards positive side (Side B): (-dy/L, dx/L)
    # Check: dx * ny - dy * nx = dx*(dx/L) - dy*(-dy/L) = (dx^2 + dy^2)/L = L > 0
    nx = -dy / length
    ny = dx / length

    # Gate B is shifted along +normal (Side B, +offset)
    b_p1 = (x1 + nx * line.offset_px, y1 + ny * line.offset_px)
    b_p2 = (x2 + nx * line.offset_px, y2 + ny * line.offset_px)

    # Gate A is shifted along -normal (Side A, -offset)
    a_p1 = (x1 - nx * line.offset_px, y1 - ny * line.offset_px)
    a_p2 = (x2 - nx * line.offset_px, y2 - ny * line.offset_px)

    return ((a_p1, a_p2), (b_p1, b_p2))


def save_line(line: CountingLine, path: str | Path) -> None:
    """Save CountingLine as JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(line.to_dict(), f, indent=2)


def load_line(path: str | Path) -> CountingLine:
    """Load CountingLine from JSON."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Line file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CountingLine.from_dict(data)


def parse_line_arg(line_str: str, offset_px: float = 60.0) -> CountingLine:
    """Parse 'x1,y1,x2,y2' string into a CountingLine."""
    parts = [float(v.strip()) for v in line_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Line specification must have 4 coordinates: 'x1,y1,x2,y2', got '{line_str}'")
    return CountingLine(p1=(parts[0], parts[1]), p2=(parts[2], parts[3]), offset_px=offset_px)


def select_line_interactive(
    frame: np.ndarray,
    offset_px: float = 60.0,
    window_name: str = "Select Counting Line",
) -> CountingLine:
    """Show frame in an interactive OpenCV window.

    Left click twice to place endpoints. 'r' to reset, 'Enter' or 'Space' to confirm, 'Esc' to cancel.
    Raises RuntimeError if headless or display is unavailable.
    """
    points: list[tuple[float, float]] = []
    temp_pos: tuple[float, float] | None = None

    def on_mouse(event: int, x: int, y: int, flags: int, param: any) -> None:
        nonlocal temp_pos
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 2:
                points.append((float(x), float(y)))
        elif event == cv2.EVENT_MOUSEMOVE:
            temp_pos = (float(x), float(y))

    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, on_mouse)
    except cv2.error as e:
        raise RuntimeError(
            "Failed to open interactive OpenCV window (headless environment?). "
            "Please pass line coordinates via --line x1,y1,x2,y2 or --line-file <path.json>"
        ) from e

    h, w = frame.shape[:2]
    selected_line: CountingLine | None = None

    while True:
        canvas = frame.copy()
        # Draw instructions header
        cv2.putText(
            canvas,
            "Click 2 points for mid-line | 'r': Reset | Enter/Space: Confirm | Esc: Abort",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            "Click 2 points for mid-line | 'r': Reset | Enter/Space: Confirm | Esc: Abort",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Draw current points / line
        if len(points) == 1 and temp_pos is not None:
            cv2.circle(canvas, (int(points[0][0]), int(points[0][1])), 6, (0, 255, 255), -1)
            cv2.line(canvas, (int(points[0][0]), int(points[0][1])), (int(temp_pos[0]), int(temp_pos[1])), (0, 255, 255), 2)
        elif len(points) == 2:
            p1_i = (int(points[0][0]), int(points[0][1]))
            p2_i = (int(points[1][0]), int(points[1][1]))
            cv2.line(canvas, p1_i, p2_i, (0, 255, 255), 3)
            cv2.circle(canvas, p1_i, 6, (0, 255, 0), -1)
            cv2.circle(canvas, p2_i, 6, (0, 0, 255), -1)

            curr_line = CountingLine(p1=points[0], p2=points[1], offset_px=offset_px)
            try:
                (g1_a, g2_a), (g1_b, g2_b) = gate_lines(curr_line)
                cv2.line(canvas, (int(g1_a[0]), int(g1_a[1])), (int(g2_a[0]), int(g2_a[1])), (255, 255, 255), 1, cv2.LINE_AA)
                cv2.line(canvas, (int(g1_b[0]), int(g1_b[1])), (int(g2_b[0]), int(g2_b[1])), (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(canvas, "Side A", (int(g1_a[0]), int(g1_a[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(canvas, "Side B", (int(g1_b[0]), int(g1_b[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            except ValueError:
                pass

        try:
            cv2.imshow(window_name, canvas)
            key = cv2.waitKey(20) & 0xFF
        except cv2.error as e:
            cv2.destroyAllWindows()
            raise RuntimeError(
                "Display error in OpenCV. Please provide line coordinates via --line or --line-file"
            ) from e

        if key in (13, 32):  # Enter or Space
            if len(points) == 2:
                selected_line = CountingLine(p1=points[0], p2=points[1], offset_px=offset_px)
                break
        elif key in (ord("r"), ord("R")):
            points.clear()
        elif key == 27:  # Esc
            cv2.destroyAllWindows()
            raise KeyboardInterrupt("Interactive line selection was cancelled by the user.")

    cv2.destroyAllWindows()
    if selected_line is None:
        raise ValueError("No line was selected")
    return selected_line
