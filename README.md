# 🚗 Video-Based Vehicle Counting System (vcount)

An automated computer vision system for directional, per-class vehicle counting across flexible time intervals from pre-recorded traffic video. Built with **Ultralytics YOLO**, **ByteTrack / BoT-SORT**, and interactive visualization tools.

Inspired by and substantially improving upon the methodology in:
> Majumder, M.; Wilmot, C. *Automated Vehicle Counting from Pre-Recorded Video Using You Only Look Once (YOLO) Object Detection Model.* J. Imaging 2023, 9, 131. [https://doi.org/10.3390/jimaging9070131](https://doi.org/10.3390/jimaging9070131)

---

## 🌟 Key Features & Improvements Over the Paper

| Paper (2023) | This System (`vcount`) |
| :--- | :--- |
| YOLOv3 (Darknet weights converted to TensorFlow) | **Modern Pretrained YOLO** (`yolo26m.pt`, `yolo11m.pt`, `yolo26n.pt`) with zero training needed |
| Simple SORT-like Kalman box tracker | **ByteTrack / BoT-SORT** with low-confidence association handling heavy occlusions |
| Vehicle aggregated as a single class | **Multi-class granular counts** (cars, motorcycles, buses, trucks, bicycles) with confidence-weighted majority voting |
| Intervals derived from processing runtime (workaround) | **Exact interval aggregation based on video timestamps** (`frame_idx / fps`) |
| Manual typing of coordinates & file drag-and-drop | Full **CLI interface**, **YAML configurations**, and an interactive **Streamlit web application** |
| Fixed hardware benchmark | Automated **multi-model & multi-tracker benchmark script** recording FPS vs accuracy |
| Undercounting from vehicles detected late | **Fallback crossing logic** for tracks appearing between gate and mid-line |

---

## 🛠️ Repository Layout

```
├── configs/
│   ├── default.yaml              # Default configuration parameters
│   └── example_site.yaml         # Example highway camera setup
├── data/
│   ├── ground_truth/             # Manual ground truth CSVs & template
│   ├── lines/                    # Saved counting line configurations (JSON)
│   └── videos/                   # Input video storage (git-ignored)
├── outputs/                      # Generated run outputs (CSVs, MP4, JSON, charts)
├── src/vcount/
│   ├── __init__.py
│   ├── config.py                 # Dataclasses, YAML loading & validation
│   ├── video_io.py               # Video metadata & frame I/O context managers
│   ├── line_setup.py             # Mid-line & parallel gate lines geometry
│   ├── detector_tracker.py       # Ultralytics YOLO & ByteTrack streaming wrapper
│   ├── counter.py                # Core line crossing, direction, & dedup logic
│   ├── intervals.py              # Time-bucket aggregation (tidy long & wide pivot)
│   ├── annotate.py               # Visual overlay HUD, trails, and bounding boxes
│   ├── exporter.py               # CSV, events log, JSON summary & config exporter
│   ├── pipeline.py               # End-to-end execution pipeline
│   ├── cli.py                    # Command-line entry points
│   ├── app.py                    # Streamlit interactive web frontend
│   ├── ui_helpers.py             # Streamlit visual helpers & ZIP packager
│   └── evaluate.py               # Accuracy metrics, paired t-test, & Bland-Altman plots
├── scripts/
│   ├── benchmark_models.py       # Benchmark FPS and accuracy across models
│   └── make_ground_truth_template.py # Ground truth CSV generator
├── tests/                        # Comprehensive unit & smoke tests (30 passing)
├── pyproject.toml
└── requirements.txt
```

---

## 🚀 Installation

### 1. Clone & Set Up Python Environment
Requires Python 3.10+ (tested on Python 3.12 & 3.13):

```bash
git clone <repo-url>
cd traffic
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

*Note on GPU Acceleration:* PyTorch with CUDA is supported automatically. If a CUDA-enabled GPU is detected, `device: auto` defaults to `cuda:0` and FP16 half-precision. The system also runs out-of-the-box on CPU.

---

## 💻 Streamlit Web Application

Launch the browser interface:

```bash
streamlit run src/vcount/app.py
```

### Streamlit Features:
1. **Upload Video:** Drag and drop MP4, AVI, MOV, or MKV videos with instant resolution, FPS, and duration inspection.
2. **Interactive Line Placement:** Fine-tune mid-line endpoints with real-time visual feedback, gate-line distance sliders, and JSON import/export.
3. **Run with Live Progress:** Background threaded processing with real-time frame previews, progress bar, ETA, and live FPS metrics.
4. **Interactive Analytics:** View wide/tidy tables, stacked interval bar charts, play back annotated MP4 video, and download all artifacts (or a single `.zip`).
5. **Direct Evaluation:** Upload ground-truth data in the browser to compute accuracy %, signed bias, and view Bland-Altman plots.

---

## ⌨️ Command-Line Interface (CLI)

### 1. Run Vehicle Counter
```bash
# Basic run with coordinate line
python -m vcount.cli run --video data/videos/traffic_clip.mp4 --line "100,500,1180,500"

# Run with custom model, interval, and saved line file
python -m vcount.cli run \
  --video data/videos/traffic_clip.mp4 \
  --config configs/default.yaml \
  --line-file data/lines/site1.json \
  --model yolo26m.pt \
  --tracker bytetrack \
  --interval 300 \
  --conf 0.35
```

### 2. Interactive Line Picker
Open an OpenCV window on the first video frame to place the line with two mouse clicks:
```bash
python -m vcount.cli line --video data/videos/traffic_clip.mp4 --save data/lines/site1.json
```
- **Left click twice:** Place start and end points.
- **`r`:** Reset points.
- **`Enter` / `Space`:** Confirm and save.
- **`Esc`:** Cancel.

### 3. Evaluate Against Manual Ground Truth
```bash
python -m vcount.cli eval --run outputs/traffic_clip_20241005_120000 --gt data/ground_truth/site1.csv --tolerance-s 2.0
```

Outputs:
- `evaluation_report.md` (Accuracy %, Signed Error %, Precision, Recall, F1, Per-class breakdown)
- `evaluation_metrics.json`
- `eval_scatter.png` (Manual vs Automated scatter plot with $y=x$)
- `eval_bland_altman.png` (Bland–Altman agreement plot measuring systematic undercounting)

### 4. Benchmark Models & Trackers
```bash
python -m vcount.cli bench --video data/videos/clip.mp4 --models yolo26n.pt yolo26s.pt yolo26m.pt yolo11m.pt --trackers bytetrack botsort
```

---

## 📊 Ground Truth Format

Generate a ground-truth CSV template:
```bash
python scripts/make_ground_truth_template.py -o data/ground_truth/site1.csv --sample
```

Template format (`data/ground_truth/site1.csv`):
```csv
timestamp_s,class_name,direction
12.4,car,entry
15.1,motorcycle,exit
24.8,truck,entry
30.2,car,exit
45.0,bus,entry
```

---

## ⚙️ Configuration Reference (`configs/default.yaml`)

```yaml
model:
  weights: "yolo26m.pt"      # Options: yolo26n.pt, yolo26s.pt, yolo26m.pt, yolo11m.pt
  device: "auto"             # "auto" | "cpu" | "cuda:0" | "mps"
  imgsz: 960                 # Image resolution during inference
  conf: 0.35                 # Detection confidence threshold
  iou: 0.5                   # NMS IoU threshold
  half: true                 # FP16 acceleration on GPU
  classes:
    car: 2
    motorcycle: 3
    bus: 5
    truck: 7

tracker:
  type: "bytetrack"          # "bytetrack" | "botsort"
  track_buffer: 30           # Number of frames to retain lost tracks

counting:
  line_file: null            # Path to pre-saved line JSON
  parallel_offset_px: 60.0   # Gate lines offset in pixels
  mode: "gated"              # "gated" (gate -> mid-line) | "simple" (mid-line only)
  min_track_frames: 3        # Ghost track suppression
  count_point: "bottom_center" # "bottom_center" (stable for perspective) or "center"
  direction_labels:
    a_to_b: "entry"
    b_to_a: "exit"
  dedup_enabled: false       # De-duplication window for re-assigned IDs
  dedup_frames: 5
  dedup_distance_px: 40.0

intervals:
  length_seconds: 900        # 900 = 15 min, 300 = 5 min, 60 = 1 min
  video_start_clock: null    # Optional real-time clock: "2024-05-10 08:00:00"

output:
  dir: "outputs"
  save_video: true
  draw_boxes: true
  draw_trails: true
```

---

## 🔬 Edge Cases & Failure Modes

| Challenge | Root Cause | Mitigation in `vcount` |
| :--- | :--- | :--- |
| **Fast moving vehicles** | Few frames in view | `frame_stride: 1` processing; low `min_track_frames: 3`; fallback crossing trigger |
| **Heavy occlusion** | Vehicles block each other | ByteTrack low-score association stage; optional BoT-SORT; `bottom_center` point |
| **Camera perspective** | Tall vehicles cross early at top of box | `bottom_center` reference point (`(x1+x2)/2, y2`) grounded at the road surface |
| **Night / Low light / Rain** | Lower detection contrast | Configurable lower confidence (`conf: 0.25 - 0.30`); class stabilization voting |
| **ID flicker on occlusion** | ByteTrack creates new ID | Optional spatial-temporal de-duplication window (`dedup_frames` & `dedup_distance_px`) |
| **Parked vehicles** | High detections but no crossing | Ignored by design until mid-line sign change occurs |

---

## 🧪 Testing

Run all unit, integration, and smoke tests:
```bash
pytest -q
```
All 30 unit tests cover:
- Directional crossings (`entry` vs `exit`)
- Jitter suppression & anti-double-counting
- Majority class voting
- Gated mode standard & fallback logic
- Time intervals bucketing & empty intervals continuity
- Evaluation metrics, F1 matching, and paired t-tests
- Streamlit `AppTest` interface initialization
- Full pipeline synthetic video smoke test

---

## 📄 License
This university research project incorporates Ultralytics YOLO (licensed under AGPL-3.0).
