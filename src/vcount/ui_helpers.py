"""UI helper utilities for Streamlit application."""

from __future__ import annotations

import io
import math
import zipfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

from vcount.line_setup import CountingLine, gate_lines


def overlay_line_on_frame(
    frame: np.ndarray,
    line: CountingLine,
    dir_a_to_b: str = "entry",
    dir_b_to_a: str = "exit",
) -> Image.Image:
    """Draw mid-line, gate lines, and direction labels on a frame for UI preview."""
    canvas = frame.copy()
    p1 = (int(line.p1[0]), int(line.p1[1]))
    p2 = (int(line.p2[0]), int(line.p2[1]))

    # Gate lines
    try:
        (g1_a, g2_a), (g1_b, g2_b) = gate_lines(line)
        cv2.line(canvas, (int(g1_a[0]), int(g1_a[1])), (int(g2_a[0]), int(g2_a[1])), (240, 240, 240), 2, cv2.LINE_AA)
        cv2.line(canvas, (int(g1_b[0]), int(g1_b[1])), (int(g2_b[0]), int(g2_b[1])), (240, 240, 240), 2, cv2.LINE_AA)

        # Labels for Side A and Side B
        cv2.putText(
            canvas,
            f"Side A ({dir_a_to_b} ->)",
            (int(g1_a[0]) + 5, int(g1_a[1]) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            f"Side B (<- {dir_b_to_a})",
            (int(g1_b[0]) + 5, int(g1_b[1]) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    except ValueError:
        pass

    # Mid-line
    cv2.line(canvas, p1, p2, (0, 220, 255), 3, cv2.LINE_AA)
    cv2.circle(canvas, p1, 7, (0, 255, 0), -1)
    cv2.circle(canvas, p2, 7, (0, 0, 255), -1)

    # Convert BGR to RGB for PIL / Streamlit
    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def create_results_zip(output_dir: Path) -> io.BytesIO:
    """Bundle all files in the output directory into a downloadable zip file in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in output_dir.glob("*"):
            if f.is_file():
                zf.write(f, arcname=f.name)
    buf.seek(0)
    return buf
