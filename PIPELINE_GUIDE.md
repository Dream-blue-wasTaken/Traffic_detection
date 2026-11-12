# Complete Technical Guide to the `vcount` Pipeline

This document provides an end-to-end technical explanation of how the vehicle detection, tracking, counting, and evaluation pipeline operates within the `vcount` architecture.

---

## 1. System Architecture Overview

The system processes video input through a multi-stage pipeline designed for high accuracy in dense and heterogenous traffic conditions (such as mixed car, motorcycle, truck, bus, and autorickshaw flows).

```
               [ Input Video Stream / File ]
                             │
                             ▼
              [ 1. Video I/O & Preprocessing ]
               - Stride sampling, resizing
               - Exact timestamp calculation: t = frame_idx / fps
                             │
                             ▼
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
 [ Primary COCO Model ]                 [ Specialized Model ]
 (YOLO26s/m/n for COCO)                 (models/best.pt)
 - Cars, Trucks, Buses, Bikes           - Filtered to class 0 (auto)
 - Raw track ID: [1, 2, ...]            - Offset track ID: [100001, ...]
         └───────────────────┬───────────────────┘
                             │
                             ▼
             [ 2. Cross-Model Suppression ]
              - Suppress COCO boxes overlapping autorickshaws
              - Criteria: IoU >= 0.20 or Containment >= 0.30
                             │
                             ▼
             [ 3. Multi-Object Tracking Engine ]
              - ByteTrack / BoT-SORT association
              - Kalman filter state estimation & track recovery
                             │
                             ▼
           [ 4. Directional Line-Crossing Engine ]
              - Geometry: Signed 2D cross product & distance
              - Modes: Simple Crossing or Gated Dual-Line
              - Confidence-weighted majority class voting
              - Spatio-temporal event deduplication
                             │
                             ▼
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
[ 5. Visual HUD ]   [ 6. Time Bucketing ]   [ 7. Exporters ]
- Annotated MP4     - 1m / 5m / 15m bins    - counts_by_interval.csv
- Trajectory trails - Wide & Long formats   - events.csv
- Live preview WS   - Clock sync            - summary.json
```

---

## 2. Video Ingestion & Temporal Preprocessing (`video_io.py`)

### 2.1 Metadata Extraction
When a video is supplied via CLI or uploaded to the web interface, `get_video_info()` opens the file with OpenCV's `cv2.VideoCapture` and inspects container properties:
- **Frame dimensions**: Width ($W$) and Height ($H$)
- **Frame rate**: Native frames per second ($\text{FPS}$)
- **Frame count**: Total frames in the stream ($N$)
- **Duration**: Total time in seconds, calculated as $T = \frac{N}{\text{FPS}}$

### 2.2 Temporal Sampling & Downscaling
To trade off between execution speed and fine-grained tracking accuracy:
- **Frame Stride** (`cfg.video.frame_stride`): If $\text{stride} > 1$, the pipeline decodes every $k$-th frame. The exact video timestamp for iteration $i$ is calculated using the original unskipped frame index:
  $$\text{frame\_idx} = i \times \text{stride}, \quad t = \frac{\text{frame\_idx}}{\text{FPS}}$$
- **Resize Scaling** (`cfg.video.resize_width`): If specified, frames are downsampled while preserving aspect ratio:
  $$\text{scale} = \frac{\text{resize\_width}}{W}, \quad H_{\text{new}} = \lfloor H \times \text{scale} \rfloor$$
- **Slice Window** (`start_seconds`, `end_seconds`): Frames outside $[t_{\text{start}}, t_{\text{end}}]$ are ignored, allowing fast evaluation on short video snippets.

---

## 3. Virtual Counting Line & Gate Geometry (`line_setup.py`)

Vehicle crossing detection relies on a reference mid-line and two virtual parallel gate lines.

```
       Side A  (signed distance < 0)
─────────────────────────────────────────────  Gate Line A  (offset = -δ)
                       ▲
                       │  Normal vector n
───────────────────────┼─────────────────────  Mid-Line (Counting Line)
                       │
─────────────────────────────────────────────  Gate Line B  (offset = +δ)
       Side B  (signed distance > 0)
```

### 3.1 Mid-Line Definition
The counting line is defined by two endpoints $P_1(x_1, y_1)$ and $P_2(x_2, y_2)$ oriented from $P_1$ to $P_2$:
$$\Delta x = x_2 - x_1, \quad \Delta y = y_2 - y_1, \quad L = \sqrt{\Delta x^2 + \Delta y^2}$$

### 3.2 2D Cross Product & Side Determination
For any object reference point $P(p_x, p_y)$, its position relative to the line is computed using the 2D cross product:
$$\text{Side}(P) = (x_2 - x_1)(p_y - y_1) - (y_2 - y_1)(p_x - x_1)$$

- $\text{Side}(P) < 0$: Point lies on **Side A** (negative side).
- $\text{Side}(P) > 0$: Point lies on **Side B** (positive side).
- $\text{Side}(P) = 0$: Point is collinear with the line.

The perpendicular signed distance from $P$ to the line is:
$$d(P) = \frac{\text{Side}(P)}{L}$$

### 3.3 Parallel Gate Lines Generation
To establish directionality and prevent noise-induced false counts, two parallel gate lines ($G_A$ and $G_B$) are constructed at offset $\delta = \text{offset\_px}$:
- **Unit Normal Vector** towards Side B:
  $$\mathbf{n} = \left(-\frac{\Delta y}{L}, \frac{\Delta x}{L}\right)$$
- **Gate Line B** (Side B, offset $+\delta$):
  $$B_1 = P_1 + \delta \mathbf{n}, \quad B_2 = P_2 + \delta \mathbf{n}$$
- **Gate Line A** (Side A, offset $-\delta$):
  $$A_1 = P_1 - \delta \mathbf{n}, \quad A_2 = P_2 - \delta \mathbf{n}$$

---

## 4. Dual-Model Ensemble & Cross-Model Suppression (`detector_tracker.py`)

A key capability of the system is robust handling of non-standard vehicles (specifically Indian 3-wheeled autorickshaws) alongside standard traffic.

```
               [ Input Video Frame ]
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[ Primary YOLO Model ]          [ Fine-Tuned Model ]
(e.g., yolo26s.pt on COCO)      (models/best.pt)
Detects: car, bike, bus, truck  Detects: autorickshaw (class 0)
Track IDs: 1, 2, 3...           Track IDs: 100001, 100002...
        │                                 │
        │   ┌─────────────────────────────┘
        ▼   ▼
[ Cross-Model Suppression ]
Is primary box heavily overlapping (IoU >= 0.20) or
containing (IoMin >= 0.30) an autorickshaw detection?
   ├── YES ──> Drop primary box (prevents misclassifying auto as car/truck)
   └── NO  ──> Retain primary box
        │
        ▼
[ Merged Frame Detections ]
```

### 4.1 Primary Model
- Runs pre-trained weights (such as `yolo26s.pt` or `yolo11n.pt`).
- Tracks standard classes mapped in configuration: `car` (2), `motorcycle` (3), `bus` (5), `truck` (7).

### 4.2 Specialized Auto-Rickshaw Model
- Loads `models/best.pt`, trained on custom traffic datasets.
- Configured with `classes=[0]` to capture only the `auto` class (ignoring negative or background annotations).
- Operates at a dedicated confidence threshold (`autorickshaw_conf = 0.60`).
- To avoid ID collisions between the two tracker instances, its track IDs are offset by $+100{,}000$:
  $$\text{track\_id}_{\text{rickshaw}} = \text{track\_id}_{\text{raw}} + 100{,}000$$

### 4.3 Cross-Model Suppression Algorithm
Pre-trained COCO detectors frequently misclassify autorickshaws as cars, vans, or trucks. Standard NMS fails when two independent models run in parallel. The pipeline applies a suppression filter `boxes_overlap_or_contained()`:
1. **Intersection over Union (IoU)**:
   $$\text{IoU}(B_{\text{coco}}, B_{\text{auto}}) = \frac{\text{Area}(B_{\text{coco}} \cap B_{\text{auto}})}{\text{Area}(B_{\text{coco}} \cup B_{\text{auto}})} \ge 0.20$$
2. **Intersection over Minimum / Containment**:
   $$\text{Containment} = \frac{\text{Area}(B_{\text{coco}} \cap B_{\text{auto}})}{\min(\text{Area}(B_{\text{coco}}), \text{Area}(B_{\text{auto}}))} \ge 0.30$$
If either criterion is met, the COCO detection is discarded in favor of the specialized autorickshaw detection.

---

## 5. Multi-Object Tracking Engine (ByteTrack / BoT-SORT)

Tracking across frames is handled via Ultralytics' integrated tracker API:
- **Motion Prediction**: A Kalman filter predicts the bounding box location in frame $t$ based on state estimates from frame $t-1$.
- **Low-Confidence Association (ByteTrack)**: ByteTrack associates high-confidence detections first, then uses low-confidence detections to recover occluded or motion-blurred vehicles rather than throwing them away.
- **Track Buffer** (`cfg.tracker.track_buffer`): Defaults to 30–60 frames. A lost track is preserved in memory for up to 2 seconds before being deleted, preventing track ID fragmentation when a vehicle passes behind a signpost or larger vehicle.

---

## 6. Directional Counting State Machine (`counter.py`)

### 6.1 Reference Point Calculation
The system tracks vehicles using their ground-contact position rather than the center:
- **`bottom_center`** (default):
  $$P_{\text{ref}} = \left(\frac{x_1 + x_2}{2}, y_2\right)$$
  This tracks the vehicle wheels on the road surface, minimizing perspective distortions caused by tall vehicle roofs.
- **`center`**:
  $$P_{\text{ref}} = \left(\frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2}\right)$$

### 6.2 Track State Lifecycle (`TrackState`)
For each track ID, the counter tracks:
- `first_seen_frame`, `last_seen_frame`: Temporal bounds.
- `last_pos`: Most recent position.
- `last_non_zero_side`: Whether the vehicle was last on Side A ($-1$) or Side B ($+1$).
- `gate_touched`: Records whether Gate A or Gate B was activated first.
- `counted`: Boolean flag preventing double-counting.
- `n_frames`: Number of frames observed. Must satisfy `n_frames >= min_track_frames` (default: 2 or 3) to filter transient false positives.
- `class_votes`: Accumulator recording confidence votes per class.

### 6.3 Counting Modes

#### Mode 1: Simple Intersection (`mode: "simple"`)
A count triggers when an active track switches sides across the mid-line:
- **Side A $\to$ Side B**: Direction labeled `a_to_b` (e.g., `"entry"`).
- **Side B $\to$ Side A**: Direction labeled `b_to_a` (e.g., `"exit"`).
- A deadband threshold ($|d(P)| \ge 1.5\,\text{px}$) prevents jitter from triggering multiple counts when a vehicle rests directly on the line.

#### Mode 2: Gated Directional (`mode: "gated"`)
Requires a vehicle to pass through a gate zone before crossing the mid-line:
1. **Gate Activation**: When $d(P) \le -\delta$, `gate_touched = "A"`. When $d(P) \ge +\delta$, `gate_touched = "B"`.
2. **Validated Crossing**:
   - `gate_touched == "A"` and vehicle transitions to Side B $\implies$ **Entry** (`a_to_b`).
   - `gate_touched == "B"` and vehicle transitions to Side A $\implies$ **Exit** (`b_to_a`).
3. **Mid-Zone Fallback**: If a vehicle first appears between the gate line and mid-line, the gate condition falls back to simple sign crossing so that late detections are not missed.

### 6.4 Confidence-Weighted Class Stabilization
Vehicles may be temporarily misclassified in a single frame due to occlusion or unusual angles. Instead of taking the class on the crossing frame, the counter aggregates cumulative confidence scores across every frame the vehicle was tracked:
$$\text{Class}_{\text{final}} = \arg\max_{c} \sum_{f=1}^{N} \text{conf}_{c, f}$$

### 6.5 Spatio-Temporal Event Deduplication
If `dedup_enabled` is set to `true`, newly registered events are checked against recent crossing events:
$$\Delta \text{frame} = \text{frame}_{\text{new}} - \text{frame}_{\text{prev}} \le \text{dedup\_frames}$$
$$\text{Distance} = \sqrt{(x_{\text{new}} - x_{\text{prev}})^2 + (y_{\text{new}} - y_{\text{prev}})^2} \le \text{dedup\_distance\_px}$$
If a duplicate event matches in direction and class within these thresholds, it is suppressed.

### 6.6 Memory Cleanup
Every 100 frames, stale tracks unobserved for $>150$ frames are evicted from memory to keep RAM usage bounded during long video streams.

---

## 7. Interval Aggregation & Time Bucketing (`intervals.py`)

Traffic counts are aggregated into fixed temporal intervals (e.g., 1-minute, 5-minute, or 15-minute bins):
$$\text{interval\_idx} = \left\lfloor \frac{t}{\Delta T} \right\rfloor$$

### 7.1 Clock Synchronization
If a real-world camera clock is supplied (`video_start_clock`, e.g., `"2026-10-17 08:00:00"`), timestamps are translated to ISO clock intervals:
$$\text{Clock}_{\text{start}} = \text{Base} + i \times \Delta T$$
$$\text{Clock}_{\text{end}} = \text{Base} + (i + 1) \times \Delta T$$

### 7.2 Output Formats
1. **Wide Pivot (`counts_by_interval.csv`)**:
   Columns formatted as `total_entry`, `car_entry`, `motorcycle_entry`, `total_exit`, etc. Suitable for spreadsheets, BI dashboards, and traffic engineering reports.
2. **Tidy Long (`counts_by_interval_long.csv`)**:
   Normalized table with schema `(interval_index, start_time, end_time, direction, class_name, count)`. Pre-populated with explicit zeros for intervals with no traffic, ready for SQL ingestion or seaborn/ggplot analytics.

---

## 8. Visual Annotation & Telemetry (`annotate.py`)

When video output is enabled (`save_video: true`), each frame is synthesized with:
1. **Gate and Counting Lines**: Thin boundary lines for gates A and B; high-contrast yellow mid-line with green/red anchor endpoints.
2. **Line Crossing Flash**: Upon an event trigger, the mid-line thickness expands and brightens to pure yellow for 6 consecutive frames as visual feedback.
3. **Vehicle Bounding Boxes & Badges**: Distinct BGR colors per class (e.g., Cyan for Cars, Gold for Motorcycles, Lime Green for Trucks, Yellow for Autorickshaws). Labels show class name, track ID, and detection confidence.
4. **Trajectory Trails**: A double-ended queue (`deque(maxlen=30)`) renders the past 30 center coordinates with fading alpha-blended thickness.
5. **HUD (Heads-Up Display)**: A semi-transparent overlay at the top-left showing video playback time ($HH:MM:SS$), real-time processing FPS, per-direction breakdowns, and cumulative vehicle totals.

---

## 9. Performance Evaluation & Validation (`evaluate.py`)

Automated counts can be benchmarked against manual ground-truth logs (`data/ground_truth/*.csv`).

### 9.1 Temporal Event Matching
The evaluator executes a greedy nearest-time bipartite matching algorithm:
- Pairs each automated crossing event $(t_a, \text{dir}_a, \text{class}_a)$ with an unmatched ground truth event $(t_g, \text{dir}_g, \text{class}_g)$.
- Matches must satisfy:
  $$\text{dir}_a = \text{dir}_g, \quad \text{class}_a = \text{class}_g, \quad |t_a - t_g| \le \tau \quad (\tau = 2.0\,\text{s})$$

### 9.2 Metrics Computed
- **Total Count Accuracy**:
  $$\text{Accuracy} = \max\left(0, 100 - \frac{|N_{\text{auto}} - N_{\text{gt}}|}{N_{\text{gt}}} \times 100\right)$$
- **Signed Percentage Error**:
  $$\text{Error}_{\text{signed}} = \frac{N_{\text{auto}} - N_{\text{gt}}}{N_{\text{gt}}} \times 100$$
- **Event-Level Precision, Recall, and F1-Score**:
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
- **Statistical Plots**: Generates error scatter plots, cumulative count curves, and Bland-Altman agreement plots comparing manual vs. automated counts.

---

## 10. Web Application & Real-Time Telemetry (`server.py`)

The full-stack application connects the pipeline to a browser interface:

```
[ Browser / React UI ]
      │
      ├─ POST /api/upload ───────────> Saves video, caches first frame
      ├─ POST /api/line/preview ─────> Interactive line overlay preview
      ├─ POST /api/pipeline/start ───> Spawns pipeline background thread
      │
      ├─ WebSocket /ws/pipeline/{id} <── Stream real-time progress & live frames
      │
      ├─ GET /api/results/{id} ──────> JSON analytics, totals, interval records
      ├─ GET /api/download/{id}/* ───> CSVs, annotated MP4, ZIP bundle
      └─ POST /api/evaluate/{id} ────> Ground truth validation & metric plots
```

- **Threaded Execution**: Each run is queued as an asynchronous task with a cooperative cancellation event (`stop_event`).
- **Live Frame Streaming**: Video frames are downscaled to 720p, JPEG-compressed in memory, base64-encoded, and pushed to the client via WebSockets at $\sim 15\,\text{FPS}$ for real-time monitoring without browser lag.
- **Model Cache**: Heavy YOLO model weights are cached in memory under a thread lock (`MODEL_CACHE`) to eliminate disk re-load overhead between consecutive runs.

---

## 11. Output Artifact Directory Structure

Every execution produces a timestamped run folder under `outputs/<video_stem>_<timestamp>/`:

| File | Format | Description |
| :--- | :--- | :--- |
| `counts_by_interval.csv` | CSV (Wide) | Binned vehicle counts per class and direction across intervals |
| `counts_by_interval_long.csv` | CSV (Tidy) | Long-format interval counts including zero-count periods |
| `events.csv` | CSV | Raw log of every individual crossing event with frame, time, and coordinates |
| `config_used.yaml` | YAML | Full serialized configuration snapshot for reproducibility |
| `summary.json` | JSON | Summary statistics (total counts, runtime, average FPS, software versions) |
| `annotated.mp4` | Video (MP4) | Full annotated video with bounding boxes, trails, and HUD |

