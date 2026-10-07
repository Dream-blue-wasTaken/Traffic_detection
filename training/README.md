# 🛺 Auto-Rickshaw Model Training

Custom YOLO26 Nano model fine-tuned to detect **auto-rickshaws** in Indian traffic scenes. This model is used as an **ensemble** alongside the standard YOLO model (which detects cars, trucks, buses, motorcycles) for complete traffic vehicle counting.

---

## Training Summary

| Parameter | Value |
|---|---|
| **Base Model** | `yolo26n.pt` (YOLO26 Nano) |
| **Architecture** | 120 layers, 5.3 GFLOPs |
| **Parameters** | 2,375,031 (~2.4M) |
| **Model Size** | ~5 MB (base), ~20 MB (trained `best.pt`) |
| **Epochs** | 50 (with early stopping, patience=15) |
| **Input Resolution** | 640×640 |
| **Batch Size** | 64 |
| **Optimizer** | SGD (Ultralytics default) |
| **Hardware** | Google Colab T4 GPU (free tier) |
| **Training Time** | ~5–10 minutes |
| **Final mAP@50** | **0.995** |
| **Final mAP@50-95** | **0.731** |
| **Precision** | **0.988** |
| **Recall** | **1.000** |

---

## Dataset

| Detail | Value |
|---|---|
| **Source** | [Roboflow Universe](https://universe.roboflow.com/anushka-9azpf/auto-rickshaw-annotation/dataset/7) |
| **Workspace** | `anushka-9azpf` |
| **Project** | `auto-rickshaw-annotation` |
| **Version** | 7 |
| **Export Format** | YOLOv11 (YOLO-compatible bounding box format) |
| **Classes** | 1 — `auto-rickshaw` (class ID: 0) |
| **License** | CC BY 4.0 |

---

## Output Weights

After training, the best weights are saved at:
```
runs/detect/autorickshaw_yolo26n/weights/best.pt
```

**To integrate with the Traffic Detection project**, copy `best.pt` to:
```
Traffic_detection/models/best.pt
```

The Streamlit app automatically detects this file and enables the **🛺 Enable Auto-Rickshaw Detection** toggle in the sidebar.

---

## How Ensemble Detection Works

The project uses a **dual-model ensemble** approach:

1. **Primary Model** (e.g., `yolo26m.pt`): Detects standard COCO vehicle classes — cars, motorcycles, buses, trucks
2. **Auto-Rickshaw Model** (`models/best.pt`): Detects auto-rickshaws only

Both models run inference on every frame simultaneously. Detections are merged with **cross-model IoU suppression** — if a standard vehicle box overlaps heavily (IoU > 0.40) with an auto-rickshaw detection, the standard detection is suppressed to prevent double-counting.

Track IDs from the auto-rickshaw model are offset by +100,000 to avoid collision with the primary tracker's IDs.

---

## Files in This Folder

| File | Purpose | Run On |
|---|---|---|
| `Untitled0.ipynb` | Complete training + benchmark + inference notebook | Google Colab (T4 GPU) |
| `README.md` | This documentation | — |

---

## How to Reproduce Training

1. Open [Google Colab](https://colab.research.google.com) and set runtime to **T4 GPU**
2. Upload `Untitled0.ipynb` (or open it directly in Colab)
3. Install dependencies in the first cell:
   ```python
   !pip install --upgrade ultralytics roboflow pyyaml -q
   ```
4. Get your Roboflow API key from [Roboflow Settings](https://roboflow.com) → Settings → API Key
5. Paste the key into the `ROBOFLOW_API_KEY` variable
6. Run all cells — training takes ~5–10 minutes on T4
7. `best.pt` will auto-download to your computer
8. Place it in `Traffic_detection/models/best.pt`

---

## Benchmark Results

### Experiment C: Resolution Trade-off (Validation Set, T4 GPU)

| Resolution | mAP@50 | mAP@50-95 | Precision | Recall | Latency (ms) | Inference FPS |
|---|---|---|---|---|---|---|
| **640×640** | **0.995** | **0.731** | 0.988 | 1.000 | 8.91 | **112.2** |
| 960×960 | 0.995 | 0.690 | 0.973 | 1.000 | 20.87 | 47.9 |

> **640×640 is the recommended resolution** — nearly identical accuracy to 960 but **2.3× faster**. The mAP@50-95 is actually higher at 640 (0.731 vs 0.690).

### Experiment B: Tracker Speed Comparison (T4 GPU, Synthetic Video)

| Tracker | Resolution | Pipeline FPS | Total Time (s) |
|---|---|---|---|
| **ByteTrack** | **640px** | **71.5** | 2.10 |
| ByteTrack | 960px | 55.0 | 2.73 |
| BoT-SORT | 640px | 47.8 | 3.14 |
| BoT-SORT | 960px | 45.1 | 3.32 |

> **ByteTrack @ 640px is the fastest** configuration (71.5 FPS). BoT-SORT produces many "not enough matching points" warnings on simple scenes and is ~1.5× slower. ByteTrack is recommended for production use.

> ⚠️ Tracker benchmark used a synthetic test video (no real auto-rickshaws), so detection counts are 0. The FPS numbers reflect pure tracker overhead and are valid for speed comparison.

---

## Why YOLO26 Nano?

- **Smallest available model** (~2.4M params vs. 25M+ for medium/large)
- **Fast training** — minutes, not hours
- **Runs on CPU** at reasonable speed for ensemble inference
- **Transfer learning** from COCO pre-trained weights provides good feature backbone even with a small single-class dataset
