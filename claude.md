# Video-Based Vehicle Counting System — Implementation Spec

> This file is the single source of truth for building the project. Read it fully before writing code.
> Work in the order given in **Section 14 (Build Order)**. After each milestone, run the tests and the checks listed there before moving on.

---

## 1. Project Goal

Build a Python command-line tool that takes a **pre-recorded traffic video** and outputs:

1. **Vehicle counts per class** (car, motorcycle, bus, truck; bicycle optional)
2. **Per direction** (e.g. entry/exit, or left→right / right→left)
3. **Per flexible time interval** (e.g. every 1, 5 or 15 minutes of *video time*)
4. An **annotated output video** (boxes, track IDs, counting line, live counters)
5. An **evaluation report** comparing automated counts to manual ground truth
6. A **Streamlit web frontend** where the user uploads a video in the browser, sets the counting line, runs the counter, and sees/downloads the results (see Section 5.10)

This is a university project based on the paper:

> Majumder, M.; Wilmot, C. *Automated Vehicle Counting from Pre-Recorded Video Using You Only Look Once (YOLO) Object Detection Model.* J. Imaging 2023, 9, 131. https://doi.org/10.3390/jimaging9070131

### What we take from the paper (keep)
- Pipeline: **detect → track → count at a virtual line**.
- A user-drawn **mid-line** on the first frame, with **two auto-generated parallel lines** (left/right of it) used to decide direction: a vehicle that touches the first parallel line and then the mid-line is counted for that direction.
- **Directional counts** (entry/exit) with **flexible time intervals**, exported to a spreadsheet (CSV).
- Evaluation against manual counts, per site/day, with accuracy % = `100 − |auto − manual| / manual × 100`, plus a paired t-test and a check for systematic undercounting.
- Documented failure modes: fast vehicles, overlapping vehicles, bad camera angle, rain/low light.

### What we improve (differences from the paper)
| Paper (2023) | This project |
|---|---|
| YOLOv3 (Darknet weights converted to TensorFlow) | **Newer pretrained Ultralytics YOLO** (default `yolo26m.pt`; fallback `yolo11m.pt`) — no training needed |
| Kalman box tracker (SORT-like) | **ByteTrack** (built into Ultralytics); BoT-SORT as alternative for heavy occlusion |
| Counts vehicles only as one class | **Per-class counts** (car / motorcycle / bus / truck) |
| Interval derived from processing time (a workaround because YOLO ran slower than real time) | **Interval derived from video timestamps** (`frame_index / fps`) — exact and independent of processing speed |
| Manual typing of filenames, drag/drop into folder | Proper **CLI with arguments + YAML config** |
| Single hardware setup, 1h40m per video hour | Benchmark several model sizes, report FPS |

---

## 2. Tech Stack

- **Python 3.10+** (3.11 recommended)
- `ultralytics` (latest; YOLO26 / YOLO11 weights, built-in ByteTrack & BoT-SORT)
- `opencv-python` (video I/O, drawing, mouse line selection)
- `numpy`, `pandas`
- `PyYAML` (config)
- `scipy` (paired t-test), `matplotlib` (plots)
- `tqdm` (progress bar)
- `streamlit` (web frontend)
- `Pillow` (preview images for the line picker)
- Optional: `streamlit-drawable-canvas` (draw the line with the mouse in the browser)
- `pytest` (tests)

Optional: PyTorch with CUDA for GPU. The tool must also run on CPU (slower).

> **Version note:** Model names and tracker options change between Ultralytics releases. Before hard-coding anything, run `pip install -U ultralytics` and verify with `yolo checks`. Confirm that the weight file (`yolo26m.pt`) downloads. If it does not exist in the installed version, fall back to `yolo11m.pt` and make the model name a **config value**, never a hard-coded string.

> **License note:** Ultralytics is AGPL-3.0. Fine for a class project; mention it in the README.

---

## 3. Repository Layout

```
vehicle-counter/
├── CLAUDE.md                  # this file
├── README.md                  # user-facing usage guide (write at the end)
├── requirements.txt
├── pyproject.toml             # optional, for `pip install -e .`
├── configs/
│   ├── default.yaml
│   └── example_site.yaml
├── data/
│   ├── videos/                # input videos (git-ignored)
│   ├── ground_truth/          # manual count CSVs
│   └── lines/                 # saved counting-line JSON per video
├── outputs/                   # git-ignored; one sub-folder per run
├── src/vcount/
│   ├── __init__.py
│   ├── config.py              # dataclasses + YAML loading + validation
│   ├── video_io.py            # open video, read metadata, write annotated video
│   ├── line_setup.py          # interactive mid-line selection, parallel lines, save/load
│   ├── detector_tracker.py    # wraps Ultralytics model.track()
│   ├── counter.py             # line-crossing logic, direction, dedup
│   ├── intervals.py           # time-bucket aggregation
│   ├── annotate.py            # drawing overlays
│   ├── exporter.py            # CSV / JSON writers
│   ├── pipeline.py            # ties everything together
│   ├── cli.py                 # argparse entry point
│   ├── app.py                 # Streamlit frontend (run: streamlit run src/vcount/app.py)
│   └── evaluate.py            # compare to ground truth, metrics, t-test, plots
├── scripts/
│   ├── benchmark_models.py    # run several models, record FPS + accuracy
│   └── make_ground_truth_template.py
└── tests/
    ├── test_counter.py
    ├── test_intervals.py
    ├── test_line_setup.py
    ├── test_evaluate.py
    └── fixtures/              # tiny synthetic data
```

---

## 4. Configuration (`configs/default.yaml`)

All tunables live here. CLI flags override YAML values.

```yaml
model:
  weights: "yolo26m.pt"      # fallback: yolo11m.pt ; sizes: n (fast) / s / m / l / x (accurate)
  device: "auto"             # "auto" | "cpu" | "cuda:0" | "mps"
  imgsz: 960                 # larger than 640 helps small/distant vehicles
  conf: 0.35                 # confidence threshold (tune on a validation clip)
  iou: 0.5                   # NMS IoU (ignored by NMS-free end-to-end models; keep for older models)
  half: true                 # FP16 on GPU
  classes:                   # COCO ids
    car: 2
    motorcycle: 3
    bus: 5
    truck: 7
  # bicycle: 1               # uncomment to count bicycles

tracker:
  type: "bytetrack"          # "bytetrack" | "botsort"
  yaml_override: null        # optional path to a customised tracker YAML
  track_buffer: 30           # frames to keep a lost track (raise to ~60 for heavy occlusion)

counting:
  line_file: null            # path to saved line JSON; if null, ask interactively on first frame
  parallel_offset_px: 60     # distance of the two parallel "gate" lines from the mid-line
  mode: "gated"              # "gated" (paper-style: gate line -> mid-line) | "simple" (mid-line only)
  min_track_frames: 3        # ignore tracks seen in fewer frames (kills flicker/ghost IDs)
  count_point: "bottom_center"  # "center" | "bottom_center" ; bottom_center is more stable in perspective views
  direction_labels:          # names for the two directions
    a_to_b: "entry"          # moving from side A (left) to side B (right)
    b_to_a: "exit"

intervals:
  length_seconds: 900        # 900 = 15 min ; 300 = 5 min ; 60 = 1 min

video:
  frame_stride: 1            # process every Nth frame (1 = all; keep 1 for accuracy)
  start_seconds: 0
  end_seconds: null          # null = until end
  resize_width: null         # optional downscale for speed

output:
  dir: "outputs"
  save_video: true
  video_codec: "mp4v"
  draw_boxes: true
  draw_trails: true
  csv: true
  json_summary: true
```

`config.py` must:
- Load YAML into typed `dataclass`es.
- Validate (e.g. `length_seconds > 0`, `frame_stride >= 1`, class ids are ints, tracker type is allowed).
- Raise clear `ValueError` messages that name the offending key.

---

## 5. Module Specifications

### 5.1 `video_io.py`
- `get_video_info(path) -> VideoInfo(fps, frame_count, width, height, duration_s)`.
  - If `fps` is 0 or NaN (corrupt metadata), raise a clear error telling the user to re-encode with `ffmpeg -i in.avi -c:v libx264 out.mp4`.
- `read_first_frame(path, start_seconds=0) -> np.ndarray`.
- `VideoWriterContext` (context manager) that opens `cv2.VideoWriter` and always releases it, even on exceptions.
- Accept `.mp4`, `.avi`, `.mov`, `.mkv`. Do **not** require manual conversion (the paper did).

### 5.2 `line_setup.py`
Responsible for the **counting line** and the **gate lines**.

Data model:
```python
@dataclass
class CountingLine:
    p1: tuple[float, float]   # (x, y) pixel coords of mid-line start
    p2: tuple[float, float]   # (x, y) pixel coords of mid-line end
    offset_px: float          # distance of the two gate lines
```

Functions:
- `select_line_interactive(frame) -> CountingLine`
  - Show the first frame in an OpenCV window with `cv2.setMouseCallback`.
  - Left click twice = two endpoints. Draw the line live. `r` resets, `Enter` or `Space` confirms, `Esc` aborts.
  - Show instruction text on the frame.
  - Must also work headless: if no display is available (`cv2.imshow` fails), raise an error telling the user to pass `--line x1,y1,x2,y2` or a `line_file`.
- `gate_lines(line) -> (line_A, line_B)`: two parallel lines offset by `±offset_px` along the normal vector of the mid-line.
- `save_line(line, path)` / `load_line(path)` as JSON.
- `side_of_line(point, line) -> float`: signed value using the 2D cross product:
  `(x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)`
  Positive = side B, negative = side A (document which is which and keep it consistent, including in tests).

### 5.3 `detector_tracker.py`
Thin wrapper around Ultralytics. **Use the built-in tracking API** rather than writing our own tracker.

```python
from ultralytics import YOLO

model = YOLO(cfg.model.weights)
results = model.track(
    source=video_path,
    stream=True,              # generator -> low memory
    persist=True,
    tracker="bytetrack.yaml", # or "botsort.yaml" or custom yaml
    conf=cfg.model.conf,
    iou=cfg.model.iou,
    imgsz=cfg.model.imgsz,
    classes=list(cfg.model.classes.values()),
    device=device,
    half=cfg.model.half,
    verbose=False,
    vid_stride=cfg.video.frame_stride,
)
```

Yield a lightweight per-frame structure so the rest of the code does not depend on Ultralytics types:

```python
@dataclass
class TrackedObject:
    track_id: int
    class_id: int
    class_name: str
    conf: float
    xyxy: tuple[float, float, float, float]

@dataclass
class FrameResult:
    frame_idx: int            # index in ORIGINAL video (account for vid_stride)
    timestamp_s: float        # frame_idx / fps
    frame: np.ndarray         # original BGR frame
    objects: list[TrackedObject]
```

Rules:
- `boxes.id` can be `None` when nothing is tracked in a frame → return an empty list.
- Auto-select device: CUDA if available, else MPS, else CPU.
- Provide `tracker_yaml_path()` that returns a custom YAML if `tracker.yaml_override` or `track_buffer` is set (write a temp YAML copied from the Ultralytics default with `track_buffer` changed).
- If the Ultralytics API differs in the installed version, adapt the wrapper but **do not change the `FrameResult` interface**.

### 5.4 `counter.py` — the core logic (most important module)

Maintain per-track state:
```python
@dataclass
class TrackState:
    first_seen_frame: int
    last_pos: tuple[float, float] | None
    gate_touched: str | None     # "A" or "B" — which gate line was reached first
    counted: bool                # True once counted (never count twice)
    n_frames: int
    class_votes: Counter         # class_id -> votes, final class = majority
```

**Count point:** `bottom_center` of box = `((x1+x2)/2, y2)` or `center`, per config.

**Class stabilization:** YOLO may flip a track between car/truck. Keep `class_votes` (weighted by confidence) and assign the count to the **majority class at the moment of counting**.

**Mode `simple`:** when the sign of `side_of_line` changes between the previous and current position of a track, and the track has ≥ `min_track_frames`, count it once. Direction: negative→positive = `a_to_b`, positive→negative = `b_to_a`.

**Mode `gated` (paper-style):**
1. Compute signed distance of the count point to the mid-line.
2. Gate A is at signed distance `−offset`, gate B at `+offset`.
3. When a track first crosses/touches a gate (distance magnitude ≥ offset on one side), record `gate_touched`.
4. When it subsequently crosses the mid-line (sign change) **and** `gate_touched` is the opposite side from its destination, count it. Direction is determined by which gate was touched first: touched A first → `a_to_b`; touched B first → `b_to_a`.
5. Set `counted = True`.
6. Fallback: if a track appears *between* the gate and mid-line (spawned mid-frame, no gate touched) and crosses the mid-line, count it using the sign change direction (log at DEBUG level that this was a fallback). This avoids systematic undercounting for vehicles that are first detected late — the paper's main error source.

**Anti-double-counting & anti-jitter:**
- `counted` flag per track ID.
- Add a small hysteresis band (±2 px) around the line so a track jittering on the line does not trigger twice.
- Because ByteTrack may assign a **new ID** to the same vehicle after occlusion, also implement an optional **de-duplication window**: if a count of the same class and direction happened within `dedup_frames` (default 5) frames and within `dedup_distance_px` (default 40 px) of the same crossing point, skip it. Make this configurable and **off by default**; evaluate whether it helps.

**Output of each crossing:** a `CountEvent` dataclass:
```python
@dataclass
class CountEvent:
    track_id: int
    class_name: str
    direction: str        # configured label (e.g. "entry")
    frame_idx: int
    timestamp_s: float
    position: tuple[float, float]
```

`Counter` public API:
```python
class LineCounter:
    def __init__(self, line: CountingLine, cfg: CountingConfig, class_names: dict[int, str]): ...
    def update(self, frame_result: FrameResult) -> list[CountEvent]: ...
    def totals(self) -> dict[str, dict[str, int]]   # {direction: {class: n}}
    def cleanup(self, frame_idx: int)               # drop state of tracks unseen for N frames (memory)
```

### 5.5 `intervals.py`
- `bucket_events(events, interval_s, duration_s) -> pandas.DataFrame`
- Interval index = `floor(timestamp_s / interval_s)`.
- Output **tidy long format** with columns:
  `interval_start, interval_end, direction, class_name, count`
  and also a **wide pivot** (one row per interval; columns like `entry_car, entry_truck, exit_car, ...` plus `entry_total`, `exit_total`, `total`).
- Include **empty intervals** as zero rows so the CSV is continuous.
- Time labels as `HH:MM:SS` of video time. If the user provides `--video-start-clock "2018-10-17 08:00:00"`, also add real clock-time columns.

### 5.6 `annotate.py`
Draw on a copy of the frame:
- Mid-line (yellow) and gate lines (white), same colours as the paper's figures for familiarity.
- Boxes colour-coded per class, label `"{class} #{id} {conf:.2f}"`.
- Trail of last ~30 count-points per track (optional).
- Top-left HUD: current counts per direction & class, current time `HH:MM:SS`, processing FPS.
- Flash the line (e.g. thicker for 5 frames) when a count event fires.

### 5.7 `exporter.py`
Write to `outputs/<video_stem>_<timestamp>/`:
- `counts_by_interval.csv` (wide)
- `counts_by_interval_long.csv`
- `events.csv` (every individual crossing: track_id, class, direction, frame, timestamp, x, y) — essential for debugging and for matching with ground truth
- `summary.json` (totals, config used, model name, video info, runtime, avg FPS, software versions)
- `annotated.mp4` (if enabled)
- `config_used.yaml` (exact config for reproducibility)

### 5.8 `pipeline.py`
```
load config -> read video info -> get/load line -> init model+tracker ->
for each frame_result:
    events = counter.update(frame_result)
    draw overlay, write frame
    (periodically) counter.cleanup()
-> bucket events -> export files -> print summary table
```
- Show a `tqdm` progress bar with ETA.
- **Frontend support:** `run_pipeline(video_path, cfg, line, progress_cb=None, preview_cb=None, stop_event=None) -> RunResult`.
  - `progress_cb(fraction: float, eta_s: float)` is called every ~10 frames.
  - `preview_cb(annotated_frame)` is called every ~15 frames so the UI can show a live preview.
  - `stop_event` (a `threading.Event`) lets the UI cancel a run; partial results are still saved.
  - `RunResult` holds the output directory path, the totals dict, the interval DataFrame, and the summary dict, so the UI never has to re-read files.
  - The CLI calls the same function with `progress_cb` wired to `tqdm`.
- Handle `KeyboardInterrupt`: stop cleanly, still write partial results.
- If the video ends early or a frame is unreadable, log a warning and continue.

### 5.9 `cli.py`
```
python -m vcount.cli run   --video data/videos/site1.mp4 [--config configs/default.yaml]
                           [--line x1,y1,x2,y2 | --line-file path.json]
                           [--interval 300] [--model yolo26s.pt] [--tracker bytetrack]
                           [--conf 0.35] [--device cuda:0] [--no-video] [--start 0 --end 600]
python -m vcount.cli eval  --run outputs/<run_dir> --gt data/ground_truth/site1.csv [--tolerance-s 2]
python -m vcount.cli bench --video data/videos/clip.mp4 --models yolo26n.pt yolo26s.pt yolo26m.pt yolo11m.pt
python -m vcount.cli line  --video data/videos/site1.mp4 --save data/lines/site1.json   # just pick & save a line
```
Use `argparse` sub-commands; print helpful errors; exit code ≠ 0 on failure.

---

### 5.10 `app.py` — Streamlit frontend

**Goal:** the user opens a browser page, uploads a video, and gets the counts there. No command line needed. It must reuse `pipeline.run_pipeline()` — **no duplicated logic** in the UI.

Run with: `streamlit run src/vcount/app.py`

#### Page layout
Sidebar = settings. Main area = 4 steps shown in order (use `st.tabs` or sections):

**Sidebar settings**
- Model dropdown: `yolo26n.pt`, `yolo26s.pt`, `yolo26m.pt`, `yolo11m.pt` (read the list from config; default `yolo26s.pt` on CPU, `yolo26m.pt` if CUDA is available — show a note about which device was detected)
- Tracker: ByteTrack / BoT-SORT
- Confidence slider (0.10–0.80, default from config)
- Image size select (640 / 960 / 1280)
- Interval length select (1 / 5 / 15 / 30 min)
- Vehicle class checkboxes (car, motorcycle, bus, truck, bicycle)
- Counting mode (gated / simple), gate offset slider
- "Process only first N seconds" number input (default off) — lets users test quickly on a short segment

**Step 1 — Upload**
- `st.file_uploader` accepting mp4, avi, mov, mkv.
- Save the upload to a temp folder (`tempfile.mkdtemp()`), streaming to disk — do not hold the whole file in memory. Note Streamlit's default upload limit is 200 MB; set `server.maxUploadSize` in `.streamlit/config.toml` (e.g. 2000) and mention this in the README.
- After upload show: filename, resolution, FPS, duration, frame count (from `get_video_info`) and the first frame.
- If metadata is invalid, show a friendly error with the ffmpeg re-encode command.

**Step 2 — Set the counting line**
Browsers cannot use the OpenCV mouse window, so provide two input methods in tabs:
1. **Sliders (default, always works):** show the first frame with the line overlaid, updated live. Four sliders for `x1, y1, x2, y2` (as % of width/height) plus a "swap direction" toggle. Preview also draws the two gate lines. Add presets: "Horizontal middle", "Vertical middle".
2. **Draw on image (optional):** if `streamlit-drawable-canvas` is installed, let the user draw a line on the first frame; scale canvas coordinates back to video pixels. If not installed, hide this tab.
- Show text labels on the preview: which side is "entry" and which is "exit" (editable text inputs for the two direction labels).
- Button to download the line as JSON; uploader to load a saved line JSON.

**Step 3 — Run**
- "Start counting" button. Disable the button while running.
- Run the pipeline in a background `threading.Thread` and update the UI from `progress_cb` / `preview_cb` via `st.session_state` and `st.empty()` placeholders (do not call Streamlit functions from the worker thread; the worker only writes to a thread-safe queue/shared object, the main script reads it).
- Show: progress bar, ETA, current FPS, running totals (use `st.metric` for each class/direction), and a live preview image of the latest annotated frame.
- "Stop" button sets `stop_event`; partial results are kept and shown.
- Store results in `st.session_state` so a Streamlit rerun does not lose them.
- Cache the loaded YOLO model with `@st.cache_resource` keyed on (weights, device) so a second run does not reload it.

**Step 4 — Results**
- Summary metrics: total vehicles, per direction, per class (`st.metric` cards).
- Table: counts by interval (`st.dataframe`) and a stacked bar chart per interval (`st.bar_chart` or matplotlib), with a dropdown to choose direction / class.
- Annotated video: `st.video(path)`. Browsers need H.264; if `mp4v` output does not play, re-encode with ffmpeg (`-c:v libx264 -pix_fmt yuv420p`) when ffmpeg is available, and otherwise offer the file as a download only.
- Download buttons: `counts_by_interval.csv`, `events.csv`, `summary.json`, annotated video, and a zip of everything.
- Expander "Settings used" showing the exact config.

**Optional Step 5 — Evaluate (nice to have)**
- Upload a ground-truth CSV (format in Section 6) and call `evaluate.py` functions to display accuracy %, signed error, precision/recall/F1 and the plots right in the page.

#### Frontend rules
- Never block the main script with a long loop that does not yield; use the thread + polling approach (`time.sleep(0.5)` + `st.rerun()`, or `st.fragment(run_every=...)` if available in the installed Streamlit version — check the docs).
- Every error shows `st.error` with a plain-language message; never a raw traceback.
- Clean temp files when a new video is uploaded.
- Keep `app.py` thin: all counting/IO logic stays in the other modules so it is unit-testable. UI helper functions (e.g. `overlay_line_on_frame`) go in `ui_helpers.py` if `app.py` grows past ~300 lines.
- Add a `.streamlit/config.toml` with `maxUploadSize` and a simple theme.
- Test with Streamlit's `AppTest` (`streamlit.testing.v1`): app loads, settings render, and with a tiny synthetic video the full flow completes (mark `@pytest.mark.slow`).

#### Deployment note (for the README)
Runs locally on the user's machine (this is where the GPU is). Hosting on Streamlit Community Cloud works for demos with `yolo26n.pt` on CPU only, but large uploads and long videos will be slow or hit limits.

---

## 6. Ground Truth Format (`data/ground_truth/<video>.csv`)

The user watches the video and logs every vehicle crossing manually. Provide `scripts/make_ground_truth_template.py` that creates an empty CSV with these columns:

```
timestamp_s,class_name,direction
12.4,car,entry
15.1,motorcycle,exit
```

Alternative aggregated format (also supported by `evaluate.py`): one row per interval with counts per class and direction — detect format automatically from the columns.

---

## 7. Evaluation (`evaluate.py`)

Inputs: a run directory (`events.csv`) + ground truth CSV.

### 7.1 Count-level metrics (mirrors the paper)
Per **class × direction** and **total**:
- Manual count, automated count
- **Accuracy %** = `100 − |auto − manual| / manual × 100` (guard against manual = 0)
- **Signed error %** = `(auto − manual) / manual × 100` → negative = undercounting. Report mean signed error to **test the paper's claim of consistent undercounting**.
- **MAPE** across classes.

Per **interval** (5/15 min): the same metrics, because the paper highlights interval counts.

### 7.2 Event-level metrics (stronger than the paper)
Match automated events to ground truth events by (same class, same direction, `|Δt| ≤ tolerance_s` default 2 s) with **greedy nearest-time matching** (one-to-one):
- TP, FP, FN
- **Precision, Recall, F1**
- Confusion matrix of class labels for matched events (car vs truck confusion is expected)

### 7.3 Statistics
If ≥ 5 paired observations (e.g. per-interval or per-video totals):
- **Paired t-test** (`scipy.stats.ttest_rel`) on manual vs automated
- Repeat on bias-adjusted differences (subtract mean difference) as the paper did to show only systematic bias remains
- **Shapiro–Wilk** normality test on the differences; warn if non-normal (the paper hit this issue)
- 95 % confidence interval of the mean difference using the **t-distribution** (`scipy.stats.t.interval`) — *not* the fixed 1.96 value the paper used with n = 10

### 7.4 Outputs
- `evaluation_report.md` (tables + short interpretation)
- `evaluation_metrics.json`
- Plots (matplotlib, saved as PNG): manual-vs-auto scatter with y = x line; Bland–Altman plot; per-interval bar chart; confusion matrix heatmap.

---

## 8. Benchmark Script (`scripts/benchmark_models.py`)

Run the full pipeline on the same clip for a list of models (e.g. `yolo26n/s/m`, `yolo11m`) × trackers (`bytetrack`, `botsort`). Record per run: avg FPS, total processing time, counts, accuracy vs ground truth (if given). Output `benchmark.csv` and a comparison bar chart (FPS vs accuracy). Use `--no-video` internally to measure pure inference speed. This directly addresses the paper's "processing time per video hour" discussion.

---

## 9. Tests (`pytest`)

Use **synthetic** data — no real video needed.

- `test_counter.py`
  - A track moving left→right across the line is counted once as `a_to_b`.
  - Right→left is `b_to_a`.
  - A track jittering around the line does not double count.
  - Track with < `min_track_frames` is not counted.
  - Class majority voting: track labelled car,car,truck → counted as car.
  - `gated` mode: a track spawned between gate and mid-line is counted via fallback.
  - Each track ID is counted at most once, even if it crosses back and forth.
- `test_line_setup.py`: `side_of_line` sign convention, gate-line offsets for horizontal, vertical, and diagonal lines.
- `test_intervals.py`: events at boundaries (e.g. t = 299.99 vs 300.0 with 300 s intervals), empty intervals produced, pivot totals add up.
- `test_evaluate.py`: perfect match gives 100 % accuracy / F1 = 1; known under-count gives negative signed error; time-tolerance matching is one-to-one.
- `test_config.py`: invalid values raise `ValueError` naming the key.

Also add one **smoke test** (marked `@pytest.mark.slow`) that generates a tiny synthetic video with `cv2` (a coloured rectangle moving across the frame), runs the pipeline with `yolo26n.pt` and just checks that outputs are created and nothing crashes.

---

## 10. Edge Cases & Known Failure Modes (design for them)

These come from the paper's limitations section; handle or at least document each:

| Problem | Mitigation in this project |
|---|---|
| Fast vehicles seen for few frames | Process every frame (`frame_stride: 1`); `min_track_frames` default only 3; fallback counting for late-spawned tracks |
| Overlapping vehicles | ByteTrack low-confidence association; optional BoT-SORT; higher `imgsz`; warn in report when many tracks have short lifetimes |
| Camera too close / vehicle partly out of frame | `bottom_center` count point; document recommended camera placement in README |
| Rain / low light / dusk | Lower `conf` slightly (0.25–0.3) for such videos; report accuracy per condition in the evaluation |
| ID switches after occlusion | Optional dedup window; larger `track_buffer` |
| Variable frame rate / corrupt metadata | Use `CAP_PROP_POS_MSEC` or per-frame timestamps when available; otherwise `frame_idx / fps` and warn |
| Very large videos | Streaming generator, no frame accumulation; `cleanup()` of stale tracks |
| Vehicles parked in view (never cross the line) | Not counted by design; document it |
| Camera shake | Document; optional future work: stabilization |

---

## 11. Quality Requirements

- Type hints on all public functions; docstrings with short descriptions.
- Use `logging` (not `print`) except for the final summary table; `--verbose` flag sets DEBUG.
- No hard-coded paths; everything via config/CLI.
- Deterministic outputs for the same input + config (record versions of `ultralytics`, `torch`, `opencv` in `summary.json`).
- Run `ruff` (or `flake8`) and `black`; keep functions short and single-purpose.
- Never load the full video into memory.
- The tool must run end-to-end on CPU for a 1-minute 720p clip with `yolo26n.pt` in reasonable time.

---

## 12. Acceptance Criteria (definition of done)

1. `python -m vcount.cli run --video <clip> --line x1,y1,x2,y2` produces all output files listed in 5.7 without errors.
2. Counts are never duplicated for one track ID (unit tested).
3. Interval CSV is continuous and totals equal the sum of events.
4. `eval` produces the report with accuracy %, signed error, precision/recall/F1, paired t-test, and plots.
5. All unit tests pass (`pytest -q`); smoke test passes.
6. README explains install, usage, config options, ground-truth format, and known limitations.
7. `streamlit run src/vcount/app.py` lets the user upload a video, set the line, run the counter with a live progress bar, and view/download all results in the browser — using the same pipeline as the CLI.
8. Stretch goal (report it, don't promise it): ≥ 90 % total-count accuracy on a clear daylight video with a reasonable camera angle (the paper's reported level).

---

## 13. Things Claude Code Must NOT Do

- Do not train or fine-tune any model — pretrained weights only.
- Do not write a custom tracker; use the Ultralytics-provided ones (a thin config wrapper is fine).
- Do not hard-code model names, class ids, or thresholds in logic code — read them from config.
- Do not count by processing-time intervals (the paper's workaround); use video timestamps.
- Do not silently swallow exceptions around model loading or video reading.
- Do not commit videos, weights, or `outputs/` to git (add to `.gitignore`).

---

## 14. Build Order (milestones)

1. **Scaffold**: repo layout, `requirements.txt`, `pyproject.toml`, `.gitignore`, config loading + validation + tests.
2. **Video I/O + line setup**: `video_io.py`, `line_setup.py`, geometry helpers + tests. Verify the interactive picker manually.
3. **Detector/tracker wrapper**: run on a short clip, print per-frame track IDs and classes. Confirm the `FrameResult` interface.
4. **Counter**: implement `simple` mode first with tests, then `gated` mode + fallback + hysteresis + class voting.
5. **Intervals + exporter**: bucketing, CSV/JSON outputs + tests.
6. **Annotation + full pipeline + CLI `run`**: produce the annotated video. Manually inspect it for correctness on a real clip.
7. **Evaluation**: ground-truth template script, `evaluate.py`, report + plots + tests.
8. **Benchmark script**: compare model sizes and trackers.
9. **Streamlit frontend**: add `progress_cb` / `preview_cb` / `stop_event` support to `pipeline.py` first (with a test), then build `app.py` step by step (upload → line setup → run → results). Test manually with a short real clip and with `AppTest`.
10. **Polish**: README (with screenshots/GIF placeholders), lint, final test run, example config.

After each milestone: run `pytest -q`, commit with a clear message, and summarize what was done and what is next.

---

## 15. Suggested Experiments for the Project Report

1. **Model size comparison:** n vs s vs m (FPS vs accuracy).
2. **Model generation comparison:** YOLOv3-era approach (paper) vs `yolo11m` vs `yolo26m`.
3. **Tracker comparison:** ByteTrack vs BoT-SORT in congested footage.
4. **Counting mode:** `simple` vs `gated` vs `gated + dedup`.
5. **Condition analysis:** daylight vs dusk vs rain; good vs poor camera angle.
6. **Bias analysis:** does our system still undercount, like the paper's? Show the signed-error plot.
7. **Interval flexibility:** same video reported at 1, 5, 15 minute intervals.

---

## 16. Reference Snippets

**Signed side of a line (cross product):**
```python
def side_of_line(px, py, x1, y1, x2, y2):
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
```

**Signed perpendicular distance (for gate lines):**
```python
import math
def signed_distance(px, py, x1, y1, x2, y2):
    length = math.hypot(x2 - x1, y2 - y1)
    return side_of_line(px, py, x1, y1, x2, y2) / length
```

**Count point from a box:**
```python
def count_point(xyxy, mode="bottom_center"):
    x1, y1, x2, y2 = xyxy
    return ((x1 + x2) / 2, y2) if mode == "bottom_center" else ((x1 + x2) / 2, (y1 + y2) / 2)
```

**Reading tracked results (Ultralytics):**
```python
for r in results:
    if r.boxes is None or r.boxes.id is None:
        objects = []
    else:
        ids  = r.boxes.id.int().cpu().tolist()
        cls  = r.boxes.cls.int().cpu().tolist()
        conf = r.boxes.conf.cpu().tolist()
        xyxy = r.boxes.xyxy.cpu().tolist()
```

**Docs to consult while implementing:**
- Ultralytics models: https://docs.ultralytics.com/models/
- Ultralytics tracking: https://docs.ultralytics.com/modes/track/
- ByteTrack paper: Zhang et al., ECCV 2022
- Base paper: https://doi.org/10.3390/jimaging9070131