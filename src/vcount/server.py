"""FastAPI Backend Server for Video-Based Vehicle Counting System."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

# Ensure src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Starlette 1.x / FastAPI compatibility shim
import starlette.routing
_orig_router_init = starlette.routing.Router.__init__
def _compat_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    return _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _compat_router_init

import cv2
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

setattr(FastAPI, "max_body_size", None)

from vcount.config import load_config
from vcount.detector_tracker import load_model, resolve_device
from vcount.evaluate import evaluate_run
from vcount.line_setup import CountingLine
from vcount.pipeline import RunResult, run_pipeline
from vcount.ui_helpers import create_results_zip, overlay_line_on_frame
from vcount.video_io import get_video_info, read_first_frame

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vcount.server")

app = FastAPI(
    title="Traffic Vision API",
    description="Backend API for Video-Based Vehicle Counting System",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
UPLOAD_DIR = Path("outputs/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory model cache
MODEL_CACHE: dict[str, Any] = {}
MODEL_CACHE_LOCK = threading.Lock()


def get_cached_yolo(weights: str):
    with MODEL_CACHE_LOCK:
        if weights not in MODEL_CACHE:
            logger.info("Loading YOLO weights into server memory cache: %s", weights)
            MODEL_CACHE[weights] = load_model(weights)
        return MODEL_CACHE[weights]


# In-memory metadata & jobs registry
VIDEOS: dict[str, dict[str, Any]] = {}


class JobState:

    def __init__(self, job_id: str, video_path: str):
        self.job_id = job_id
        self.video_path = video_path
        self.status: str = "queued"  # queued, running, completed, error, stopped
        self.progress: float = 0.0
        self.eta_s: float = 0.0
        self.preview_base64: str | None = None
        self.error: str | None = None
        self.stop_event = threading.Event()
        self.result: RunResult | None = None
        self.output_dir: Path | None = None
        self.created_at: float = time.time()


JOBS: dict[str, JobState] = {}


# Pydantic Schemas
class LinePreviewRequest(BaseModel):
    video_path: str
    p1: list[float] = Field(..., min_length=2, max_length=2)
    p2: list[float] = Field(..., min_length=2, max_length=2)
    offset_px: float = 30.0
    dir_a_to_b: str = "entry"
    dir_b_to_a: str = "exit"


class PipelineStartRequest(BaseModel):
    video_path: str
    p1: list[float] = Field(..., min_length=2, max_length=2)
    p2: list[float] = Field(..., min_length=2, max_length=2)
    offset_px: float = 30.0
    dir_a_to_b: str = "entry"
    dir_b_to_a: str = "exit"
    model_weights: str = "yolo26s.pt"
    tracker: str = "bytetrack"
    conf_threshold: float = 0.25
    img_size: int = 640
    interval_minutes: int = 5
    counting_mode: str = "simple"
    active_classes: dict[str, int] = {
        "car": 2,
        "motorcycle": 3,
        "bus": 5,
        "truck": 7,
    }
    enable_rickshaw: bool = False
    limit_seconds: float = 0.0


# ----------------------------------------------------
# 1. System Info & Model Catalog
# ----------------------------------------------------
@app.get("/api/system")
def get_system_info():
    device = resolve_device("auto")
    device_badge = (
        "GPU (CUDA)"
        if "cuda" in device
        else ("Apple Silicon (MPS)" if "mps" in device else "CPU")
    )

    standard_models = [
        "yolo26m.pt",
        "yolo26s.pt",
        "yolo26n.pt",
        "yolo11m.pt",
        "yolo11n.pt",
    ]
    has_rickshaw_model = Path("models/best.pt").is_file()

    # Check local weights available
    available_local_models = [m for m in standard_models if Path(m).is_file()]
    if not available_local_models:
        available_local_models = standard_models

    return {
        "device": device,
        "device_badge": device_badge,
        "models": standard_models,
        "available_local_models": available_local_models,
        "default_model": "yolo26s.pt",
        "has_rickshaw_model": has_rickshaw_model,
    }


# ----------------------------------------------------
# 2. Video Upload & Extraction
# ----------------------------------------------------
@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    vid_id = str(uuid.uuid4())[:8]
    sanitized_filename = Path(file.filename or f"video_{vid_id}.mp4").name
    dest_path = UPLOAD_DIR / f"{vid_id}_{sanitized_filename}"

    try:
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

        info = get_video_info(dest_path)
        first_frame = read_first_frame(dest_path)

        # Save first frame to disk for fast caching and preview
        first_frame_path = UPLOAD_DIR / f"{vid_id}_first_frame.jpg"
        cv2.imwrite(str(first_frame_path), first_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        video_record = {
            "video_id": vid_id,
            "filename": sanitized_filename,
            "video_path": str(dest_path.resolve()),
            "first_frame_path": str(first_frame_path.resolve()),
            "metadata": {
                "width": info.width,
                "height": info.height,
                "fps": round(info.fps, 2),
                "duration_s": round(info.duration_s, 2),
                "frame_count": info.frame_count,
            },
        }
        VIDEOS[vid_id] = video_record

        return {
            "success": True,
            "video_id": vid_id,
            "filename": sanitized_filename,
            "video_path": str(dest_path.resolve()),
            "first_frame_url": f"/api/video/{vid_id}/first-frame",
            "metadata": video_record["metadata"],
        }
    except Exception as e:
        logger.exception("Upload failed")
        if dest_path.is_file():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to process video: {e}")


@app.get("/api/video/{video_id}/first-frame")
def get_first_frame(video_id: str):
    record = VIDEOS.get(video_id)
    if not record or not Path(record["first_frame_path"]).is_file():
        # Check if file exists directly on disk
        candidates = list(UPLOAD_DIR.glob(f"{video_id}_first_frame.jpg"))
        if candidates:
            return FileResponse(candidates[0], media_type="image/jpeg")
        raise HTTPException(status_code=404, detail="Frame not found")

    return FileResponse(record["first_frame_path"], media_type="image/jpeg")


# ----------------------------------------------------
# 3. Interactive Line Preview
# ----------------------------------------------------
@app.post("/api/line/preview")
def preview_line(req: LinePreviewRequest):
    v_path = Path(req.video_path)
    if not v_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        first_frame = read_first_frame(v_path)
        line = CountingLine(
            p1=(req.p1[0], req.p1[1]),
            p2=(req.p2[0], req.p2[1]),
            offset_px=req.offset_px,
        )
        pil_img = overlay_line_on_frame(
            first_frame,
            line,
            dir_a_to_b=req.dir_a_to_b,
            dir_b_to_a=req.dir_b_to_a,
        )
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {"data_url": f"data:image/jpeg;base64,{b64}"}
    except Exception as e:
        logger.exception("Error generating line preview")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------
# 4. Pipeline Execution & Real-Time Tracking
# ----------------------------------------------------
@app.post("/api/pipeline/start")
def start_pipeline(req: PipelineStartRequest):
    v_path = Path(req.video_path)
    if not v_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")

    job_id = str(uuid.uuid4())[:8]
    job = JobState(job_id=job_id, video_path=str(v_path.resolve()))
    JOBS[job_id] = job

    # Build active classes mapping
    active_classes = req.active_classes
    rickshaw_weights = "models/best.pt" if req.enable_rickshaw else None

    cfg = load_config(
        overrides={
            "model": {
                "weights": req.model_weights,
                "conf": req.conf_threshold,
                "imgsz": req.img_size,
                "classes": active_classes,
                "autorickshaw_weights": rickshaw_weights,
            },
            "tracker": {"type": req.tracker},
            "counting": {
                "mode": req.counting_mode,
                "parallel_offset_px": req.offset_px,
                "direction_labels": {
                    "a_to_b": req.dir_a_to_b,
                    "b_to_a": req.dir_b_to_a,
                },
            },
            "intervals": {"length_seconds": req.interval_minutes * 60},
            "video": {
                "end_seconds": req.limit_seconds if req.limit_seconds > 0 else None,
            },
        }
    )

    line = CountingLine(
        p1=(req.p1[0], req.p1[1]),
        p2=(req.p2[0], req.p2[1]),
        offset_px=req.offset_px,
    )

    def worker():
        job.status = "running"
        try:
            model = get_cached_yolo(req.model_weights)

            last_preview_time = [0.0]

            def on_progress(frac: float, eta: float):
                job.progress = frac
                job.eta_s = eta

            def on_preview(frame_bgr: np.ndarray):
                # Rate limit preview encoding to ~15 fps to preserve CPU/GPU
                now = time.time()
                if now - last_preview_time[0] < 0.06:
                    return
                last_preview_time[0] = now

                h, w = frame_bgr.shape[:2]
                if w > 720:
                    scale = 720 / float(w)
                    frame_bgr = cv2.resize(frame_bgr, (720, int(h * scale)), interpolation=cv2.INTER_AREA)

                _, enc = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 65])
                job.preview_base64 = base64.b64encode(enc).decode("utf-8")

            res = run_pipeline(
                video_path=job.video_path,
                cfg=cfg,
                line=line,
                model=model,
                progress_cb=on_progress,
                preview_cb=on_preview,
                stop_event=job.stop_event,
            )

            job.result = res
            job.output_dir = res.output_dir
            job.status = "stopped" if job.stop_event.is_set() else "completed"
            job.progress = 1.0
            logger.info("Pipeline job %s finished with status: %s", job_id, job.status)
        except Exception as exc:
            logger.exception("Pipeline job %s failed: %s", job_id, exc)
            job.error = str(exc)
            job.status = "error"

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "running"}


@app.post("/api/pipeline/stop/{job_id}")
def stop_pipeline(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.stop_event.set()
    job.status = "stopped"
    return {"message": "Pipeline stop requested", "job_id": job_id}


@app.get("/api/pipeline/status/{job_id}")
def get_pipeline_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": round(job.progress, 4),
        "eta_s": round(job.eta_s, 1),
        "preview_base64": job.preview_base64,
        "error": job.error,
        "has_result": job.result is not None,
    }


@app.websocket("/ws/pipeline/{job_id}")
async def websocket_pipeline_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job = JOBS.get(job_id)
    if not job:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close()
        return

    try:
        while True:
            payload = {
                "job_id": job.job_id,
                "status": job.status,
                "progress": round(job.progress, 4),
                "eta_s": round(job.eta_s, 1),
                "preview_base64": job.preview_base64,
                "error": job.error,
                "has_result": job.result is not None,
            }
            await websocket.send_json(payload)

            if job.status in ("completed", "error", "stopped"):
                break

            await asyncio.sleep(0.08)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WebSocket error for job %s: %s", job_id, e)


# ----------------------------------------------------
# 5. Results & Analytics
# ----------------------------------------------------
@app.get("/api/results/{job_id}")
def get_results(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.result:
        raise HTTPException(status_code=400, detail="Job results not ready")

    res = job.result
    events_data = [
        {
            "track_id": e.track_id,
            "class_name": e.class_name,
            "direction": e.direction,
            "timestamp_s": round(e.timestamp_s, 2),
        }
        for e in res.events
    ]

    df_records = res.df_wide.to_dict(orient="records") if hasattr(res, "df_wide") and res.df_wide is not None else []

    annotated_video_available = bool(res.annotated_video_path and res.annotated_video_path.is_file())

    return {
        "job_id": job.job_id,
        "total_vehicles": res.total_vehicles,
        "totals": res.totals,
        "summary": res.summary,
        "intervals": df_records,
        "events": events_data,
        "annotated_video_available": annotated_video_available,
        "video_url": f"/api/download/{job_id}/video" if annotated_video_available else None,
        "output_dir": str(res.output_dir.name) if res.output_dir else None,
    }


# ----------------------------------------------------
# 6. File Downloads & Video Player
# ----------------------------------------------------
@app.get("/api/download/{job_id}/video")
def download_annotated_video(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.result or not job.result.annotated_video_path:
        raise HTTPException(status_code=404, detail="Annotated video not available")
    vid_path = job.result.annotated_video_path
    if not vid_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    return FileResponse(vid_path, media_type="video/mp4")


@app.get("/api/download/{job_id}/intervals-csv")
def download_intervals_csv(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Results not found")
    csv_bytes = job.result.df_wide.to_csv(index=False).encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={job_id}_counts_by_interval.csv"},
    )


@app.get("/api/download/{job_id}/events-csv")
def download_events_csv(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Results not found")

    events_df = pd.DataFrame([
        {
            "track_id": e.track_id,
            "class_name": e.class_name,
            "direction": e.direction,
            "timestamp_s": e.timestamp_s,
        }
        for e in job.result.events
    ])
    csv_bytes = events_df.to_csv(index=False).encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={job_id}_events.csv"},
    )


@app.get("/api/download/{job_id}/summary-json")
def download_summary_json(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Results not found")
    json_bytes = json.dumps(job.result.summary, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={job_id}_summary.json"},
    )


@app.get("/api/download/{job_id}/zip")
def download_zip(job_id: str):
    job = JOBS.get(job_id)
    if not job or not job.result or not job.result.output_dir:
        raise HTTPException(status_code=404, detail="Results not found")
    zip_buffer = create_results_zip(job.result.output_dir)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={job.result.output_dir.name}.zip"},
    )


# ----------------------------------------------------
# 7. Ground Truth Accuracy Evaluation
# ----------------------------------------------------
@app.post("/api/evaluate/{job_id}")
async def evaluate_job(
    job_id: str,
    file: UploadFile = File(...),
    tolerance_s: float = Form(2.0),
):
    job = JOBS.get(job_id)
    if not job or not job.result or not job.result.output_dir:
        raise HTTPException(status_code=404, detail="Completed run not found for this job ID")

    # Save uploaded ground truth CSV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_gt:
        content = await file.read()
        tmp_gt.write(content)
        tmp_gt_path = tmp_gt.name

    try:
        eval_metrics = evaluate_run(
            run_dir=job.result.output_dir,
            gt_file=tmp_gt_path,
            tolerance_s=tolerance_s,
        )

        plots = []
        plot_names = eval_metrics.get("plots", [])
        for p_name in plot_names:
            p_file = job.result.output_dir / p_name
            if p_file.is_file():
                plots.append({
                    "name": p_name,
                    "url": f"/api/evaluate/{job_id}/plot/{p_name}",
                })

        return {
            "success": True,
            "metrics": eval_metrics,
            "plots": plots,
        }
    except Exception as e:
        logger.exception("Evaluation failed")
        raise HTTPException(status_code=400, detail=f"Evaluation failed: {e}")
    finally:
        if os.path.exists(tmp_gt_path):
            os.remove(tmp_gt_path)


@app.get("/api/evaluate/{job_id}/plot/{plot_name}")
def get_evaluation_plot(job_id: str, plot_name: str):
    job = JOBS.get(job_id)
    if not job or not job.result or not job.result.output_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    p_file = job.result.output_dir / plot_name
    if not p_file.is_file():
        raise HTTPException(status_code=404, detail="Plot not found")

    return FileResponse(p_file, media_type="image/png")


# ----------------------------------------------------
# 8. Mount Built Frontend If Present
# ----------------------------------------------------
FRONTEND_DIST = Path("frontend/dist")
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")


def main():
    import uvicorn
    uvicorn.run("vcount.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
