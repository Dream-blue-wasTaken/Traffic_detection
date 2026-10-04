"""Streamlit Web Application for Video-Based Vehicle Counting System."""

from __future__ import annotations

import io
import json
import logging
import tempfile
import threading
import time
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import streamlit as st
import torch
from PIL import Image
from ultralytics import YOLO

from vcount.config import Config, load_config
from vcount.detector_tracker import load_model, resolve_device
from vcount.evaluate import evaluate_run
from vcount.line_setup import CountingLine
from vcount.pipeline import RunResult, run_pipeline
from vcount.ui_helpers import create_results_zip, overlay_line_on_frame
from vcount.video_io import get_video_info, read_first_frame

logger = logging.getLogger(__name__)

# Try optional streamlit-drawable-canvas
try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_AVAILABLE = True
except ImportError:
    CANVAS_AVAILABLE = False


@st.cache_resource
def get_cached_model(weights: str) -> YOLO:
    """Cache loaded YOLO weights in memory across Streamlit reruns."""
    return load_model(weights)


def init_session_state() -> None:
    if "video_path" not in st.session_state:
        st.session_state.video_path = None
    if "video_info" not in st.session_state:
        st.session_state.video_info = None
    if "first_frame" not in st.session_state:
        st.session_state.first_frame = None
    if "counting_line" not in st.session_state:
        st.session_state.counting_line = None
    if "run_result" not in st.session_state:
        st.session_state.run_result = None
    if "worker_state" not in st.session_state:
        st.session_state.worker_state = {
            "status": "idle",
            "progress": 0.0,
            "eta_s": 0.0,
            "preview_frame": None,
            "error": None,
            "result": None,
            "stop_event": None,
        }


def main():
    st.set_page_config(
        page_title="Traffic Vision — Vehicle Counting System",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()

    # Determine hardware acceleration
    detected_device = resolve_device("auto")
    device_badge = "🟢 GPU (CUDA)" if "cuda" in detected_device else ("🟡 Apple Silicon (MPS)" if "mps" in detected_device else "⚪ CPU")

    # Sidebar: Configurations
    st.sidebar.title("⚙️ System Settings")
    st.sidebar.caption(f"Hardware Engine: **{device_badge}**")

    model_options = ["yolo26m.pt", "yolo26s.pt", "yolo26n.pt", "yolo11m.pt", "yolo11n.pt"]
    default_model_idx = 0 if "cuda" in detected_device else 1
    selected_model = st.sidebar.selectbox("YOLO Model Weights", model_options, index=default_model_idx)

    selected_tracker = st.sidebar.selectbox("Tracker Backend", ["bytetrack", "botsort"], index=0)
    conf_threshold = st.sidebar.slider("Detection Confidence", min_value=0.10, max_value=0.85, value=0.35, step=0.05)
    img_size = st.sidebar.selectbox("Inference Resolution (px)", [640, 960, 1280], index=1)

    interval_minutes = st.sidebar.selectbox("Interval Length", [1, 5, 15, 30], index=1)
    counting_mode = st.sidebar.radio("Counting Algorithm", ["gated", "simple"], index=0)
    gate_offset = st.sidebar.slider("Gate Line Offset (px)", min_value=20.0, max_value=120.0, value=60.0, step=5.0)

    st.sidebar.subheader("Active Vehicle Classes")
    track_cars = st.sidebar.checkbox("Cars", value=True)
    track_motorcycles = st.sidebar.checkbox("Motorcycles", value=True)
    track_buses = st.sidebar.checkbox("Buses", value=True)
    track_trucks = st.sidebar.checkbox("Trucks", value=True)
    track_bicycles = st.sidebar.checkbox("Bicycles", value=False)

    limit_seconds = st.sidebar.number_input("Process First N Seconds (0 = full video)", min_value=0.0, max_value=7200.0, value=0.0, step=10.0)

    # Header
    st.title("🚗 Video-Based Vehicle Counting System")
    st.markdown(
        "Automated traffic analysis using **YOLO & ByteTrack** with virtual gated counting lines, "
        "flexible time intervals, and ground truth evaluation."
    )

    tab_upload, tab_line, tab_run, tab_results, tab_eval = st.tabs(
        ["1. Upload Video", "2. Set Counting Line", "3. Run Counter", "4. View Results", "5. Evaluation"]
    )

    # ------------------ TAB 1: UPLOAD ------------------
    with tab_upload:
        st.subheader("Step 1: Upload Traffic Video")
        uploaded_file = st.file_uploader(
            "Select a pre-recorded traffic video (MP4, AVI, MOV, MKV)",
            type=["mp4", "avi", "mov", "mkv"],
        )

        if uploaded_file is not None:
            # Check if this is a newly uploaded file
            curr_name = getattr(uploaded_file, "name", "temp_video.mp4")
            if (
                st.session_state.video_path is None
                or Path(st.session_state.video_path).name != curr_name
            ):
                temp_dir = tempfile.mkdtemp(prefix="vcount_upload_")
                save_dest = Path(temp_dir) / curr_name
                with open(save_dest, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    info = get_video_info(save_dest)
                    frame = read_first_frame(save_dest)
                    st.session_state.video_path = str(save_dest)
                    st.session_state.video_info = info
                    st.session_state.first_frame = frame
                    # Initialize default horizontal line
                    h, w = frame.shape[:2]
                    st.session_state.counting_line = CountingLine(
                        p1=(w * 0.1, h * 0.5),
                        p2=(w * 0.9, h * 0.5),
                        offset_px=gate_offset,
                    )
                    st.success(f"Successfully loaded '{curr_name}'!")
                except Exception as e:
                    st.error(f"Error reading video metadata: {e}")

        if st.session_state.video_info is not None:
            v_info = st.session_state.video_info
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Resolution", f"{v_info.width} x {v_info.height}")
            col_m2.metric("FPS", f"{v_info.fps:.2f}")
            col_m3.metric("Duration", f"{v_info.duration_s:.1f} s")
            col_m4.metric("Frames", f"{v_info.frame_count:,}")

            if st.session_state.first_frame is not None:
                rgb_f = cv2.cvtColor(st.session_state.first_frame, cv2.COLOR_BGR2RGB)
                st.image(rgb_f, caption="First Video Frame", use_container_width=True)

    # ------------------ TAB 2: LINE SETUP ------------------
    with tab_line:
        st.subheader("Step 2: Set Virtual Counting Line")
        if st.session_state.first_frame is None:
            st.info("Please upload a video in Step 1 first.")
        else:
            h, w = st.session_state.first_frame.shape[:2]
            col_cfg, col_preview = st.columns([1, 1.2])

            with col_cfg:
                col_d1, col_d2 = st.columns(2)
                dir_entry = col_d1.text_input("Direction A->B Name", value="entry")
                dir_exit = col_d2.text_input("Direction B->A Name", value="exit")

                # Presets
                preset = st.radio("Quick Presets", ["Custom", "Horizontal Middle", "Vertical Middle"], horizontal=True)
                if preset == "Horizontal Middle":
                    p1 = (w * 0.05, h * 0.5)
                    p2 = (w * 0.95, h * 0.5)
                elif preset == "Vertical Middle":
                    p1 = (w * 0.5, h * 0.05)
                    p2 = (w * 0.5, h * 0.95)
                else:
                    curr_l = st.session_state.counting_line or CountingLine(
                        p1=(w * 0.1, h * 0.5), p2=(w * 0.9, h * 0.5), offset_px=gate_offset
                    )
                    p1 = curr_l.p1
                    p2 = curr_l.p2

                col_p1x, col_p1y = st.columns(2)
                p1_x = col_p1x.slider("Start Point X (px)", 0.0, float(w), float(p1[0]), 5.0)
                p1_y = col_p1y.slider("Start Point Y (px)", 0.0, float(h), float(p1[1]), 5.0)

                col_p2x, col_p2y = st.columns(2)
                p2_x = col_p2x.slider("End Point X (px)", 0.0, float(w), float(p2[0]), 5.0)
                p2_y = col_p2y.slider("End Point Y (px)", 0.0, float(h), float(p2[1]), 5.0)

                line_obj = CountingLine(
                    p1=(p1_x, p1_y),
                    p2=(p2_x, p2_y),
                    offset_px=gate_offset,
                )
                st.session_state.counting_line = line_obj

                # JSON export and import
                col_btn1, col_btn2 = st.columns(2)
                line_json_str = json.dumps(line_obj.to_dict(), indent=2)
                col_btn1.download_button(
                    "💾 Download Line JSON",
                    data=line_json_str,
                    file_name="counting_line.json",
                    mime="application/json",
                )

                uploaded_line_file = col_btn2.file_uploader("Load Line JSON", type=["json"], key="line_uploader")
                if uploaded_line_file is not None:
                    try:
                        line_dict = json.load(uploaded_line_file)
                        st.session_state.counting_line = CountingLine.from_dict(line_dict)
                        st.success("Loaded line from JSON!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error loading JSON: {err}")

            with col_preview:
                preview_img = overlay_line_on_frame(
                    st.session_state.first_frame,
                    st.session_state.counting_line,
                    dir_a_to_b=dir_entry,
                    dir_b_to_a=dir_exit,
                )
                st.image(preview_img, caption="Counting Line & Gate Preview", use_container_width=True)

    # ------------------ TAB 3: RUN COUNTER ------------------
    with tab_run:
        st.subheader("Step 3: Execute Vehicle Counting")
        if st.session_state.video_path is None:
            st.info("Please upload a video and configure the counting line first.")
        else:
            w_state = st.session_state.worker_state
            is_running = w_state["status"] == "running"

            col_btn_start, col_btn_stop = st.columns([1, 1])

            def start_processing_job():
                # Build active classes mapping
                active_classes = {}
                if track_cars:
                    active_classes["car"] = 2
                if track_motorcycles:
                    active_classes["motorcycle"] = 3
                if track_buses:
                    active_classes["bus"] = 5
                if track_trucks:
                    active_classes["truck"] = 7
                if track_bicycles:
                    active_classes["bicycle"] = 1

                cfg = load_config(
                    overrides={
                        "model": {
                            "weights": selected_model,
                            "conf": conf_threshold,
                            "imgsz": img_size,
                            "classes": active_classes,
                        },
                        "tracker": {"type": selected_tracker},
                        "counting": {
                            "mode": counting_mode,
                            "parallel_offset_px": gate_offset,
                            "direction_labels": {"a_to_b": dir_entry, "b_to_a": dir_exit},
                        },
                        "intervals": {"length_seconds": interval_minutes * 60},
                        "video": {
                            "end_seconds": limit_seconds if limit_seconds > 0 else None,
                        },
                    }
                )

                stop_evt = threading.Event()
                w_state["status"] = "running"
                w_state["progress"] = 0.0
                w_state["eta_s"] = 0.0
                w_state["preview_frame"] = None
                w_state["error"] = None
                w_state["result"] = None
                w_state["stop_event"] = stop_evt

                def worker():
                    try:
                        cached_m = get_cached_model(selected_model)

                        def on_prog(frac: float, eta: float):
                            w_state["progress"] = frac
                            w_state["eta_s"] = eta

                        def on_prev(frame_bgr: np.ndarray):
                            w_state["preview_frame"] = frame_bgr

                        res = run_pipeline(
                            video_path=st.session_state.video_path,
                            cfg=cfg,
                            line=st.session_state.counting_line,
                            model=cached_m,
                            progress_cb=on_prog,
                            preview_cb=on_prev,
                            stop_event=stop_evt,
                        )
                        w_state["result"] = res
                        w_state["status"] = "completed"
                    except Exception as exc:
                        logger.exception("Pipeline execution failed")
                        w_state["error"] = str(exc)
                        w_state["status"] = "error"

                t = threading.Thread(target=worker, daemon=True)
                t.start()

            if col_btn_start.button("▶️ Start Counting Pipeline", disabled=is_running, type="primary"):
                start_processing_job()
                st.rerun()

            if col_btn_stop.button("⏹️ Stop Pipeline", disabled=not is_running):
                if w_state["stop_event"]:
                    w_state["stop_event"].set()
                w_state["status"] = "stopped"
                st.warning("Stopping pipeline... Partial results are being finalized.")

            # Live Status Elements
            progress_bar = st.progress(w_state["progress"])
            status_text = st.empty()
            col_live1, col_live2 = st.columns([1, 1.2])

            with col_live1:
                metric_ph = st.empty()
            with col_live2:
                preview_ph = st.empty()

            if is_running:
                status_text.info(
                    f"Processing in progress... {int(w_state['progress'] * 100)}% "
                    f"(ETA: {int(w_state['eta_s'])}s)"
                )
                if w_state["preview_frame"] is not None:
                    rgb_p = cv2.cvtColor(w_state["preview_frame"], cv2.COLOR_BGR2RGB)
                    preview_ph.image(rgb_p, caption="Live Detection Preview", use_container_width=True)

                time.sleep(0.6)
                st.rerun()
            elif w_state["status"] == "completed":
                progress_bar.progress(1.0)
                status_text.success("🎉 Processing completed successfully!")
                st.session_state.run_result = w_state["result"]
            elif w_state["status"] == "error":
                status_text.error(f"Execution Error: {w_state['error']}")

    # ------------------ TAB 4: VIEW RESULTS ------------------
    with tab_results:
        st.subheader("Step 4: Counting Results & Analytics")
        res: RunResult | None = st.session_state.run_result

        if res is None:
            st.info("Run the counter in Step 3 to see results and analytics.")
        else:
            # Metrics Row
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Vehicles", res.total_vehicles)

            dirs = list(res.totals.keys())
            dir1 = dirs[0] if len(dirs) > 0 else "entry"
            dir2 = dirs[1] if len(dirs) > 1 else "exit"
            cnt_dir1 = sum(res.totals.get(dir1, {}).values())
            cnt_dir2 = sum(res.totals.get(dir2, {}).values())

            m_col2.metric(f"Total {dir1.capitalize()}", cnt_dir1)
            m_col3.metric(f"Total {dir2.capitalize()}", cnt_dir2)
            m_col4.metric("Avg Speed", f"{res.summary.get('average_fps', 0.0):.1f} FPS")

            st.divider()

            # Breakdown Charts
            st.write("### Counts by Interval")
            col_tab, col_chart = st.columns([1, 1.2])

            with col_tab:
                st.dataframe(res.df_wide, use_container_width=True)

            with col_chart:
                chart_cols = [c for c in res.df_wide.columns if ("entry_" in c or "exit_" in c) and not c.endswith("_total")]
                if chart_cols:
                    st.bar_chart(res.df_wide.set_index("interval_start")[chart_cols])

            # Annotated Video Player
            if res.annotated_video_path and res.annotated_video_path.is_file():
                st.write("### Annotated Video Output")
                st.video(str(res.annotated_video_path))

            # Download Artifacts
            st.write("### Download Results")
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)

            d_col1.download_button(
                "📥 Interval Counts (CSV)",
                data=res.df_wide.to_csv(index=False),
                file_name="counts_by_interval.csv",
                mime="text/csv",
            )
            d_col2.download_button(
                "📥 Crossing Events (CSV)",
                data=pd.DataFrame([
                    {
                        "track_id": e.track_id,
                        "class_name": e.class_name,
                        "direction": e.direction,
                        "timestamp_s": e.timestamp_s,
                    }
                    for e in res.events
                ]).to_csv(index=False),
                file_name="events.csv",
                mime="text/csv",
            )
            d_col3.download_button(
                "📥 Summary (JSON)",
                data=json.dumps(res.summary, indent=2),
                file_name="summary.json",
                mime="application/json",
            )
            zip_buffer = create_results_zip(res.output_dir)
            d_col4.download_button(
                "📦 Download All (.ZIP)",
                data=zip_buffer,
                file_name=f"{res.output_dir.name}.zip",
                mime="application/zip",
            )

    # ------------------ TAB 5: EVALUATION ------------------
    with tab_eval:
        st.subheader("Step 5: Ground Truth Accuracy Evaluation")
        res = st.session_state.run_result

        if res is None:
            st.info("Run the counter in Step 3 before evaluating.")
        else:
            gt_upload = st.file_uploader("Upload Manual Ground Truth CSV", type=["csv"], key="eval_gt_upload")
            eval_tol = st.slider("Matching Time Tolerance (seconds)", 0.5, 5.0, 2.0, 0.5)

            if gt_upload is not None:
                tmp_gt = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                tmp_gt.write(gt_upload.getbuffer())
                tmp_gt.close()

                try:
                    eval_metrics = evaluate_run(
                        run_dir=res.output_dir,
                        gt_file=tmp_gt.name,
                        tolerance_s=eval_tol,
                    )
                    st.success("Evaluation complete!")

                    tot = eval_metrics.get("total_count_metrics", {})
                    ec1, ec2, ec3, ec4 = st.columns(4)
                    ec1.metric("Manual Count", tot.get("manual", 0))
                    ec2.metric("Automated Count", tot.get("auto", 0))
                    ec3.metric("Accuracy %", f"{tot.get('accuracy_pct', 0.0)}%")
                    ec4.metric("Signed Error %", f"{tot.get('signed_error_pct', 0.0)}%")

                    evt = eval_metrics.get("event_metrics")
                    if evt:
                        st.write("#### Event-Level Precision & Recall")
                        ev1, ev2, ev3 = st.columns(3)
                        ev1.metric("Precision", f"{evt.get('precision', 0.0):.3f}")
                        ev2.metric("Recall", f"{evt.get('recall', 0.0):.3f}")
                        ev3.metric("F1 Score", f"{evt.get('f1', 0.0):.3f}")

                    # Display evaluation plots if generated
                    plot_names = eval_metrics.get("plots", [])
                    for p_name in plot_names:
                        p_file = res.output_dir / p_name
                        if p_file.is_file():
                            st.image(str(p_file), caption=p_name, use_container_width=True)

                except Exception as err:
                    st.error(f"Evaluation failed: {err}")


if __name__ == "__main__":
    main()
