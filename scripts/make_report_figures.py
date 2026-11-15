"""Generate the schematic figures used in the project report PDF.

Run with the Windows-side report environment:
    .report-venv/Scripts/python.exe scripts/make_report_figures.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle, Polygon, Rectangle

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report_assets")
os.makedirs(OUT, exist_ok=True)

NAVY = "#1f3864"
BLUE = "#2e5e8c"
LIGHT = "#dbe5f1"
PALE = "#eef3f9"
GOLD = "#b8962e"
GREY = "#5a5a5a"
GREEN = "#2f6b4f"
RED = "#a33a3a"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.linewidth": 0.0,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)


def box(ax, x, y, w, h, text, fc=PALE, ec=NAVY, size=10, bold=False, lw=1.2, radius=0.02):
    """Draw a rounded box with centred wrapped text."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.004,rounding_size={radius}",
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2,
        )
    )
    ax.text(
        x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
        fontweight="bold" if bold else "normal", color="#111111", zorder=3,
        linespacing=1.25,
    )


def arrow(ax, p1, p2, color=NAVY, lw=1.3, style="-|>", ls="-", rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            p1, p2, arrowstyle=style, mutation_scale=12, color=color,
            linewidth=lw, linestyle=ls, zorder=4,
            connectionstyle=f"arc3,rad={rad}",
        )
    )


def canvas(w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6 * h / w)
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------- Figure 2.1
def concept_figure():
    fig, ax = plt.subplots(figsize=(10, 3.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.9)
    ax.axis("off")

    titles = [
        ("(a) Detection", "Locate every vehicle\nin each frame"),
        ("(b) Tracking", "Assign a persistent ID\nand follow it over time"),
        ("(c) Counting", "Increment once when the\nID crosses the virtual line"),
    ]
    for i, (title, sub) in enumerate(titles):
        x0 = 0.25 + i * 3.28
        ax.add_patch(Rectangle((x0, 0.35), 3.0, 3.05, facecolor="#f7f9fc",
                               edgecolor=LIGHT, lw=1.2))
        ax.text(x0 + 1.5, 3.22, title, ha="center", va="center", fontsize=11.5,
                fontweight="bold", color=NAVY)
        ax.text(x0 + 1.5, 0.62, sub, ha="center", va="center", fontsize=8.8,
                color=GREY, style="italic")

        # road strip
        ax.add_patch(Rectangle((x0 + 0.2, 1.15), 2.6, 1.45, facecolor="#4a4a4a",
                               edgecolor="none", zorder=1))
        ax.plot([x0 + 0.2, x0 + 2.8], [1.55, 1.55], color="#e8e8e8", lw=0.8, ls="--", zorder=2)
        ax.plot([x0 + 0.2, x0 + 2.8], [2.2, 2.2], color="#e8e8e8", lw=0.8, ls="--", zorder=2)

        # cars
        car_x = [x0 + 0.55, x0 + 1.75]
        for j, (cx, cw) in enumerate(zip(car_x, [0.85, 0.95])):
            ax.add_patch(FancyBboxPatch((cx, 1.6), cw, 0.62,
                                        boxstyle="round,pad=0.02,rounding_size=0.08",
                                        facecolor=["#8fb8dc", "#c8d6a5"][j],
                                        edgecolor="none", zorder=2))
            ax.add_patch(Rectangle((cx + 0.16, 1.86), cw - 0.32, 0.24,
                                   facecolor="#e9f0f7", edgecolor="none", zorder=3))
            if i >= 1:
                ax.text(cx + cw / 2, 1.42, f"#{14 + j}", ha="center", va="center",
                        fontsize=7.6, color=GOLD, fontweight="bold")

        if i == 0:
            for cx, cw in zip(car_x, [0.85, 0.95]):
                ax.add_patch(Rectangle((cx - 0.04, 1.56), cw + 0.08, 0.7,
                                       facecolor="none", edgecolor="#3fa34d", lw=1.2, zorder=4))
        if i == 1:
            for cx, cw in zip(car_x, [0.85, 0.95]):
                ax.plot([cx + cw / 2, cx + cw / 2 + 0.3], [1.75, 1.45], color=GOLD, lw=0.9, zorder=3)
        if i == 2:
            ax.plot([x0 + 0.25, x0 + 2.75], [2.0, 2.0], color="#f2c318", lw=3.0, zorder=5)
            ax.text(x0 + 1.5, 2.12, "+1", ha="center", fontsize=9.5, color=GOLD,
                    fontweight="bold", zorder=6)

        if i < 2:
            arrow(ax, (x0 + 3.04, 1.88), (x0 + 3.24, 1.88), color=NAVY, lw=1.6)

    fig.savefig(os.path.join(OUT, "fig_concept.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 2.3
def gate_figure():
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    # road
    ax.add_patch(Polygon([[0.4, 0.35], [9.6, 0.35], [8.9, 4.3], [1.1, 4.3]],
                         closed=True, facecolor="#6b6b6b", edgecolor="none"))
    for y in (1.25, 2.3, 3.35):
        ax.plot([0.75, 9.25], [y, y], color="#f0f0f0", lw=1.0, ls=(0, (6, 5)), alpha=0.7)

    p1, p2 = (1.5, 2.55), (8.5, 2.55)
    # gate lines
    ax.plot([p1[0], p2[0]], [p1[1] + 1.05, p2[1] + 1.05], color="white", lw=2.0)
    ax.plot([p1[0], p2[0]], [p1[1] - 1.05, p2[1] - 1.05], color="white", lw=2.0)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#f2c318", lw=3.4, zorder=5)
    ax.plot(*p1, "o", color="#3fa34d", ms=8, zorder=6)
    ax.plot(*p2, "o", color="#c0392b", ms=8, zorder=6)

    ax.text(5.0, 2.7, "Mid-line (counting line)", ha="center", fontsize=9.5,
            color="#6b5600", fontweight="bold", zorder=7)
    ax.text(4.4, 3.72, "Gate line B  (offset = +δ)", fontsize=9, color="white", va="bottom",
            bbox=dict(fc="#6b6b6b", ec="none", pad=1.2))
    ax.text(6.05, 1.28, "Gate line A  (offset = −δ)", fontsize=9, color="white", va="top",
            bbox=dict(fc="#6b6b6b", ec="none", pad=1.2))
    ax.text(0.55, 4.0, "Side B  (d > 0)", fontsize=10, color=NAVY, fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.text(0.55, 0.55, "Side A  (d < 0)", fontsize=10, color=NAVY, fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.85))

    # normal vector
    ax.annotate("", xy=(2.15, 2.55), xytext=(2.15, 3.6),
                arrowprops=dict(arrowstyle="-|>", color="#3fa34d", lw=1.8))
    ax.text(2.28, 3.0, "n", fontsize=11, color=GREEN, fontweight="bold")
    ax.annotate("", xy=(1.75, 3.6), xytext=(2.15, 3.6),
                arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9, ls="--"))
    ax.text(1.45, 3.7, "δ", fontsize=10, color="#dddddd")

    # trajectory A -> B
    traj = [(3.0, 1.45), (3.55, 1.9), (4.1, 2.55), (4.65, 3.1), (5.3, 3.62)]
    ax.plot([p[0] for p in traj], [p[1] for p in traj], color="#3fa34d", lw=2.2, zorder=6)
    for p in traj[:4]:
        ax.plot(*p, "o", color="#3fa34d", ms=3.2, zorder=7)
    ax.annotate("", xy=(5.3, 3.62), xytext=(4.85, 3.32),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.2), zorder=8)
    ax.text(3.35, 0.72, "track path A → B\ncounted as entry", fontsize=8.8, color="#1d4d36",
            ha="center", fontweight="bold",
            bbox=dict(fc="#6b6b6b", ec="none", pad=1.5))

    # fallback zone
    ax.annotate("", xy=(7.6, 2.55), xytext=(7.6, 3.6),
                arrowprops=dict(arrowstyle="<->", color=GOLD, lw=1.2))
    ax.text(7.75, 3.05, "mid-zone\n(fallback)", fontsize=8.2, color=GOLD, va="center")

    ax.text(5.0, 5.15, "Gate A first  →  crosses mid-line  →  a_to_b (entry)",
            ha="center", fontsize=10.5, color=NAVY, fontweight="bold")
    fig.savefig(os.path.join(OUT, "fig_gate.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 3.1
def architecture_figure():
    fig, ax = canvas(10, 8.2)
    ax.set_ylim(0, 8.2)

    # input layer
    box(ax, 3.1, 7.35, 3.8, 0.62, "Traffic video input  (MP4 / AVI / MOV / MKV)", fc="#e7eef7", bold=True)
    arrow(ax, (5.0, 7.35), (5.0, 7.05))

    box(ax, 1.2, 6.35, 7.6, 0.62,
        "1 · Video ingestion, frame stride, resize and exact timestamps t = frame_idx / fps", fc=LIGHT)

    # detectors
    arrow(ax, (3.4, 6.35), (2.75, 6.02))
    arrow(ax, (6.6, 6.35), (7.25, 6.02))
    box(ax, 0.55, 5.22, 4.2, 0.78,
        "2a · Primary detector\nYOLO26s / YOLO11m (COCO)", fc="#fdf6e3", ec=GOLD, bold=True)
    box(ax, 5.25, 5.22, 4.2, 0.78,
        "2b · Specialised detector\nfine-tuned YOLO26n (auto-rickshaw)", fc="#fdf6e3", ec=GOLD, bold=True)

    arrow(ax, (2.65, 5.22), (4.2, 4.86))
    arrow(ax, (7.35, 5.22), (5.8, 4.86))
    box(ax, 1.2, 4.22, 7.6, 0.62,
        "3 · Detection fusion: cross-model IoU suppression, track-ID offset", fc=LIGHT)

    arrow(ax, (5.0, 4.22), (5.0, 3.92))
    box(ax, 1.2, 3.28, 7.6, 0.62,
        "4 · Multi-object tracking: ByteTrack / BoT-SORT + Kalman prediction", fc=LIGHT)

    arrow(ax, (5.0, 3.28), (5.0, 2.98))
    box(ax, 1.2, 2.30, 7.6, 0.66,
        "5 · Directional counting: gate geometry, crossing state machine,\nclass voting, hysteresis, de-duplication", fc="#eaf3ec", ec=GREEN)

    # outputs
    arrow(ax, (3.2, 2.30), (2.9, 2.0))
    arrow(ax, (5.0, 2.30), (5.0, 2.0))
    arrow(ax, (6.8, 2.30), (7.1, 2.0))
    box(ax, 0.45, 1.18, 2.9, 0.8, "Annotated video\nboxes, trails, HUD", fc="#f2f2f2", ec=GREY, size=9)
    box(ax, 3.55, 1.18, 2.9, 0.8, "Interval aggregation\n1 / 5 / 15 min buckets", fc="#f2f2f2", ec=GREY, size=9)
    box(ax, 6.65, 1.18, 2.9, 0.8, "CSV · JSON · config\nrun artefacts", fc="#f2f2f2", ec=GREY, size=9)

    arrow(ax, (5.0, 1.18), (5.0, 0.86))
    box(ax, 2.3, 0.30, 5.4, 0.56, "CLI  ·  FastAPI server  ·  React dashboard  ·  evaluation report", fc="#e7eef7", bold=True, size=9)

    ax.text(0.47, 7.83, "Offline analysis pipeline", fontsize=11, color=NAVY, fontweight="bold")
    fig.savefig(os.path.join(OUT, "fig_architecture.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 3.2
def deployment_figure():
    fig, ax = canvas(10, 5.2)
    ax.set_ylim(0, 5.2)

    box(ax, 0.35, 3.3, 2.4, 1.15, "Browser\nReact + TypeScript\nsingle-page UI", fc="#e8eef7", bold=True)
    box(ax, 3.55, 3.3, 2.9, 1.15, "FastAPI application\nREST endpoints\nWebSocket stream", fc="#eaf3ec", ec=GREEN, bold=True)
    box(ax, 7.25, 3.3, 2.4, 1.15, "Static bundle\n(Vite build)\nserved by FastAPI", fc="#f2f2f2", ec=GREY, size=9)

    box(ax, 3.55, 1.55, 2.9, 1.0, "Pipeline worker thread\nrun_pipeline() + stop_event", fc="#fdf6e3", ec=GOLD, bold=True, size=9)
    box(ax, 3.55, 0.25, 2.9, 0.85, "YOLO + tracker\n(model cache)", fc="#f7f7f7", ec=GREY, size=9)
    box(ax, 7.25, 1.55, 2.4, 1.0, "Run directory\nCSV · JSON · MP4", fc="#f7f7f7", ec=GREY, size=9)
    box(ax, 0.35, 1.55, 2.4, 1.0, "Uploaded video\n+ line JSON", fc="#f7f7f7", ec=GREY, size=9)

    arrow(ax, (2.75, 3.9), (3.55, 3.9), style="<|-|>")
    ax.text(3.15, 4.05, "HTTP", fontsize=8, color=GREY, ha="center")
    arrow(ax, (7.25, 3.7), (6.45, 3.7), style="<|-|>")
    ax.text(6.85, 3.85, "assets", fontsize=8, color=GREY, ha="center")

    arrow(ax, (5.0, 3.3), (5.0, 2.55), style="-|>")
    ax.text(5.1, 2.92, "start / cancel", fontsize=8, color=GREY)
    arrow(ax, (5.0, 1.55), (5.0, 1.1), style="<|-|>")
    arrow(ax, (6.45, 2.05), (7.25, 2.05), style="-|>", color=BLUE)
    ax.text(6.85, 2.2, "write", fontsize=7.5, color=GREY, ha="center")
    arrow(ax, (0.95, 3.3), (0.95, 2.55), style="-|>", color=BLUE)
    ax.text(1.15, 2.93, "upload", fontsize=7.5, color=GREY)
    arrow(ax, (2.75, 2.05), (3.55, 2.05), style="-|>", color=BLUE)
    ax.text(3.15, 2.2, "read", fontsize=7.5, color=GREY, ha="center")

    ax.text(0.35, 4.85, "Deployment view of the web application", fontsize=11, color=NAVY, fontweight="bold")
    fig.savefig(os.path.join(OUT, "fig_deployment.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 3.3
def sequence_figure():
    fig, ax = canvas(10, 6.6)
    ax.set_ylim(0, 6.6)

    people = [
        (0.9, "User"),
        (3.0, "React UI"),
        (5.2, "FastAPI"),
        (7.3, "Pipeline thread"),
        (9.05, "YOLO + tracker"),
    ]
    for x, name in people:
        box(ax, x - 0.72, 5.9, 1.44, 0.42, name, fc="#e7eef7", size=8.0, bold=True, radius=0.01)
        ax.plot([x, x], [5.85, 0.35], color="#9aa7b8", lw=0.8, ls=(0, (4, 4)))

    def msg(y, x1, x2, text, color=NAVY, ls="-"):
        arrow(ax, (x1, y), (x2, y), color=color, ls=ls)
        ax.text((x1 + x2) / 2, y + 0.1, text, ha="center", va="bottom", fontsize=7.6, color="#222222")

    msg(5.5, 0.9, 3.0, "select video file")
    msg(5.1, 3.0, 5.2, "POST /api/upload")
    msg(4.75, 5.2, 3.0, "metadata + first frame", color=GREEN)
    msg(4.35, 0.9, 3.0, "place line, set options")
    msg(3.95, 3.0, 5.2, "POST /api/pipeline/start")
    msg(3.6, 5.2, 7.3, "spawn worker")
    msg(3.25, 7.3, 9.3, "track(frame)", color=GOLD)
    msg(2.9, 9.3, 7.3, "FrameResult", color=GOLD)
    msg(2.5, 7.3, 5.2, "progress + JPEG preview (WS)", color=GREEN, ls="--")
    msg(2.1, 5.2, 3.0, "live metrics, ETA", color=GREEN, ls="--")
    msg(1.7, 7.3, 5.2, "complete + summary", color=GREEN)
    msg(1.3, 3.0, 5.2, "GET /api/results/{id}")
    msg(0.85, 5.2, 3.0, "tables, charts, downloads", color=GREEN)

    ax.text(0.45, 6.45, "Sequence of a counting run in the web dashboard", fontsize=11,
            color=NAVY, fontweight="bold")
    fig.savefig(os.path.join(OUT, "fig_sequence.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 4.1
def flow_figure():
    fig, ax = canvas(10, 9.4)
    ax.set_ylim(0, 9.4)

    box(ax, 2.6, 8.62, 4.8, 0.5, "Start: CLI command / web request", fc="#e7eef7", bold=True, size=9)
    arrow(ax, (5.0, 8.62), (5.0, 8.38))
    box(ax, 2.2, 7.88, 5.6, 0.5, "Load YAML config, validate, apply CLI overrides", fc=LIGHT, size=9)
    arrow(ax, (5.0, 7.88), (5.0, 7.64))
    box(ax, 2.2, 7.14, 5.6, 0.5, "Open video, read FPS / size / frame count", fc=LIGHT, size=9)
    arrow(ax, (5.0, 7.14), (5.0, 6.9))
    box(ax, 2.2, 6.3, 5.6, 0.6, "Load counting line JSON or pick interactively", fc=LIGHT, size=9)
    arrow(ax, (5.0, 6.3), (5.0, 6.06))
    box(ax, 2.2, 5.56, 5.6, 0.5, "Initialise model, tracker and LineCounter", fc=LIGHT, size=9)
    arrow(ax, (5.0, 5.56), (5.0, 5.32))
    box(ax, 2.3, 4.78, 5.4, 0.54, "Read next frame (streamed, never fully cached)", fc="#fdf6e3", ec=GOLD, size=9)
    arrow(ax, (5.0, 4.78), (5.0, 4.54))
    box(ax, 2.3, 3.98, 5.4, 0.56, "Detect + track → FrameResult", fc="#fdf6e3", ec=GOLD, size=9)
    arrow(ax, (5.0, 3.98), (5.0, 3.74))
    box(ax, 2.3, 3.18, 5.4, 0.56, "Update counter, collect CountEvents", fc="#eaf3ec", ec=GREEN, size=9)
    arrow(ax, (5.0, 3.18), (5.0, 2.94))
    box(ax, 2.3, 2.38, 5.4, 0.56, "Annotate frame, write to output video", fc="#eaf3ec", ec=GREEN, size=9)

    # loop decision
    diamond = Polygon([[8.6, 2.35], [9.45, 2.85], [8.6, 3.35], [7.75, 2.85]],
                      closed=True, facecolor="#ffffff", edgecolor=NAVY, lw=1.2)
    ax.add_patch(diamond)
    ax.text(8.6, 2.85, "more\nframes?", ha="center", va="center", fontsize=7.8, color=NAVY)
    arrow(ax, (7.7, 2.66), (7.75, 2.85), style="-|>", lw=1.0)

    # yes -> loop back to the frame reader
    ax.plot([9.45, 9.75, 9.75], [2.85, 2.85, 5.05], color=NAVY, lw=1.2, zorder=1)
    arrow(ax, (9.75, 5.05), (7.7, 5.05), color=NAVY, lw=1.2)
    ax.text(9.62, 3.95, "yes", fontsize=7.8, color=NAVY, rotation=90, va="center")

    # no branch
    ax.plot([8.6, 8.6], [2.35, 1.7], color=GREEN, lw=1.4)
    arrow(ax, (8.6, 1.7), (7.7, 1.7), color=GREEN, lw=1.4)
    ax.text(8.72, 2.05, "no", fontsize=7.8, color=GREEN)
    box(ax, 2.3, 1.4, 5.4, 0.6, "Bucket events into intervals (wide + long tables)", fc=LIGHT, size=9)
    arrow(ax, (5.0, 1.4), (5.0, 1.16))
    box(ax, 2.3, 0.6, 5.4, 0.56, "Write CSV / JSON / annotated MP4, print summary", fc="#e7eef7", bold=True, size=9)

    ax.text(0.35, 9.28, "End-to-end processing flow of run_pipeline()", fontsize=11,
            color=NAVY, fontweight="bold")
    fig.savefig(os.path.join(OUT, "fig_flow.png"))
    plt.close(fig)


if __name__ == "__main__":
    concept_figure()
    gate_figure()
    architecture_figure()
    deployment_figure()
    sequence_figure()
    flow_figure()
    print("figures written to", OUT)
