import pytest
import math
from vcount.line_setup import (
    CountingLine,
    side_of_line,
    signed_distance,
    gate_lines,
    save_line,
    load_line,
    parse_line_arg,
)


def test_side_of_line_vertical():
    # Line going straight down from (100, 0) to (100, 200)
    line = CountingLine(p1=(100.0, 0.0), p2=(100.0, 200.0), offset_px=50.0)
    # Right of line: x = 150 -> Side B (positive)
    # cross product: (100-100)*(y - 0) - (200-0)*(150-100) = -200 * 50 = -10000 -> Note:
    # Let's check formula: (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    # x1=100, y1=0; x2=100, y2=200
    # For point (150, 100): (0)*(100) - (200)*(50) = -10000 < 0 (Side A)
    # For point (50, 100): (0)*(100) - (200)*(-50) = +10000 > 0 (Side B)
    # Point directly on line:
    assert side_of_line((100.0, 50.0), line) == 0.0
    # Consistent check:
    assert side_of_line((50.0, 100.0), line) > 0  # Side B
    assert side_of_line((150.0, 100.0), line) < 0  # Side A


def test_side_of_line_horizontal():
    # Line going from left to right: (0, 100) to (200, 100)
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=50.0)
    # (x2 - x1) = 200, (y2 - y1) = 0
    # For point below the line (100, 150): 200 * (150 - 100) - 0 = +10000 > 0 (Side B)
    # For point above the line (100, 50): 200 * (50 - 100) - 0 = -10000 < 0 (Side A)
    assert side_of_line((100.0, 150.0), line) > 0  # Side B
    assert side_of_line((100.0, 50.0), line) < 0   # Side A
    assert side_of_line((100.0, 100.0), line) == 0.0


def test_gate_lines_horizontal():
    line = CountingLine(p1=(0.0, 100.0), p2=(200.0, 100.0), offset_px=50.0)
    (a1, a2), (b1, b2) = gate_lines(line)

    # Gate B should be on Side B (positive distance)
    # gate A should be on Side A (negative distance)
    dist_b = signed_distance(b1, line)
    dist_a = signed_distance(a1, line)

    assert pytest.approx(dist_b, abs=1e-4) == 50.0
    assert pytest.approx(dist_a, abs=1e-4) == -50.0

    # For horizontal line (0, 100) to (200, 100), dx=200, dy=0, nx = 0, ny = 1
    # Gate B has y = 100 + 50 = 150
    # Gate A has y = 100 - 50 = 50
    assert pytest.approx(b1[1], abs=1e-4) == 150.0
    assert pytest.approx(a1[1], abs=1e-4) == 50.0


def test_gate_lines_diagonal():
    # Diagonal at 45 degrees
    line = CountingLine(p1=(0.0, 0.0), p2=(100.0, 100.0), offset_px=30.0)
    (a1, a2), (b1, b2) = gate_lines(line)

    dist_b = signed_distance(b1, line)
    dist_a = signed_distance(a1, line)

    assert pytest.approx(dist_b, abs=1e-4) == 30.0
    assert pytest.approx(dist_a, abs=1e-4) == -30.0

    # Normal distance from mid line
    hypot_offset = math.hypot(b1[0] - line.p1[0], b1[1] - line.p1[1])
    assert pytest.approx(hypot_offset, abs=1e-4) == 30.0


def test_save_load_json_roundtrip(tmp_path):
    line = CountingLine(p1=(12.5, 34.0), p2=(567.8, 910.1), offset_px=45.0)
    save_path = tmp_path / "test_line.json"
    save_line(line, save_path)
    loaded = load_line(save_path)

    assert loaded.p1 == line.p1
    assert loaded.p2 == line.p2
    assert loaded.offset_px == line.offset_px


def test_parse_line_arg():
    line = parse_line_arg("10,20,300,400", offset_px=55.0)
    assert line.p1 == (10.0, 20.0)
    assert line.p2 == (300.0, 400.0)
    assert line.offset_px == 55.0

    with pytest.raises(ValueError):
        parse_line_arg("10,20,300")
