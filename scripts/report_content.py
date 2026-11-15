"""Front matter and Chapters 1-3 of the KIIT project report."""

from __future__ import annotations

from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from report_kit import (
    BOLD,
    GREY,
    ITAL,
    LINE,
    NAVY,
    P,
    STYLES,
    bullets,
    chapter,
    data_table,
    figure,
    section,
    subsection,
)

TITLE = "Video-Based Vehicle Counting System Using YOLO Detection and Multi-Object Tracking"

STUDENTS = [
    ("Student Name 1", "Roll Number 1"),
    ("Student Name 2", "Roll Number 2"),
    ("Student Name 3", "Roll Number 3"),
]

GUIDE = "Prof. (Dr.) Guide Name"
GUIDE_DESIG = "Professor, School of Computer Science and Engineering"
MONTH = "November 2026"


def _rule(width: float = 14.0, thickness: float = 1.2) -> Table:
    t = Table([[""]], colWidths=[width * cm], rowHeights=[thickness])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    return t


# --------------------------------------------------------------------- cover
def cover() -> list:
    s: list = [Spacer(1, 0.4 * cm)]
    s.append(P("KALINGA INSTITUTE OF INDUSTRIAL TECHNOLOGY", "CoverBig"))
    s.append(P("(Deemed to be University)", "CoverMid"))
    s.append(P("School of Computer Science and Engineering", "CoverMid"))
    s.append(P("Bhubaneswar – 751024, Odisha, India", "CoverMid"))
    s.append(Spacer(1, 0.55 * cm))
    s.append(_rule(14.0, 1.2))
    s.append(Spacer(1, 0.55 * cm))
    s.append(P("A PROJECT REPORT ON", "CoverBold"))
    s.append(Spacer(1, 0.45 * cm))
    s.append(P(TITLE, "CoverBig"))
    s.append(Spacer(1, 0.45 * cm))
    s.append(
        P(
            "Submitted in partial fulfilment of the requirements for the award of the degree of",
            "CoverMid",
        )
    )
    s.append(Spacer(1, 0.25 * cm))
    s.append(P("BACHELOR OF TECHNOLOGY", "CoverBold"))
    s.append(P("in", "CoverMid"))
    s.append(P("COMPUTER SCIENCE AND ENGINEERING", "CoverBold"))
    s.append(Spacer(1, 0.5 * cm))
    s.append(_rule(10.0, 0.8))
    s.append(Spacer(1, 0.45 * cm))
    s.append(P("SUBMITTED BY", "CoverBold"))
    rows = [[Paragraph(n, STYLES["CoverMid"]), Paragraph(r, STYLES["CoverMid"])] for n, r in STUDENTS]
    t = Table(rows, colWidths=[8.4 * cm, 6.0 * cm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ]
        )
    )
    s.append(t)
    s.append(Spacer(1, 0.45 * cm))
    s.append(P("UNDER THE GUIDANCE OF", "CoverBold"))
    s.append(P(GUIDE, "CoverMid"))
    s.append(P(GUIDE_DESIG, "CoverMid"))
    s.append(Spacer(1, 0.6 * cm))
    s.append(_rule(14.0, 1.2))
    s.append(Spacer(1, 0.3 * cm))
    s.append(P(MONTH, "CoverBold"))
    return s


def certificate() -> list:
    s = [
        PageBreak(),
        P("CERTIFICATE", "FrontTitle"),
        Spacer(1, 0.6 * cm),
        P(
            "This is to certify that the project report entitled "
            f"<b>&ldquo;{TITLE}&rdquo;</b> submitted by "
            "<b>Student Name 1 (Roll Number 1)</b>, <b>Student Name 2 (Roll Number 2)</b> and "
            "<b>Student Name 3 (Roll Number 3)</b> is a record of bona fide work carried out by them "
            "under my supervision and guidance, in partial fulfilment of the requirements for the award of "
            "the degree of Bachelor of Technology in Computer Science and Engineering at the School of "
            "Computer Science and Engineering, Kalinga Institute of Industrial Technology, Bhubaneswar.",
        ),
        P(
            "The work presented in this report is original and has not been submitted elsewhere for the "
            "award of any other degree or diploma. The system described here was designed, implemented, "
            "tested and documented by the candidates themselves, and the results reported in Chapter 4 "
            "were obtained from runs of that system on the hardware described in Section 3.2.",
        ),
        Spacer(1, 2.0 * cm),
        Table(
            [
                [
                    Paragraph("__________________________<br/>Prof. (Dr.) Guide Name<br/>Project Guide", STYLES["BodyCenter"]),
                    Paragraph("__________________________<br/>Prof. (Dr.) Head of School<br/>School of CSE, KIIT", STYLES["BodyCenter"]),
                ]
            ],
            colWidths=[7.8 * cm, 7.8 * cm],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]),
        ),
        Spacer(1, 1.6 * cm),
        P("Bhubaneswar, Odisha<br/>November 2026", "BodyCenter"),
    ]
    return s


def acknowledgement() -> list:
    return [
        PageBreak(),
        P("ACKNOWLEDGEMENT", "FrontTitle"),
        Spacer(1, 0.4 * cm),
        P(
            "We would like to express our sincere gratitude to our project guide, "
            f"<b>{GUIDE}</b>, for the continuous support, technical direction and patient review that shaped "
            "this work. The regular discussions on evaluation methodology in particular helped us move from "
            "building a demonstration to building something that can be measured."
        ),
        P(
            "We thank the Head of the School and the faculty members of the School of Computer Science and "
            "Engineering, KIIT, for providing the academic environment and the computing facilities used for "
            "this project, and for the feedback offered during the review presentations."
        ),
        P(
            "We are grateful to the authors of the open-source tools on which this work rests, in particular "
            "Ultralytics for the YOLO implementations and the bundled ByteTrack and BoT-SORT trackers, and the "
            "OpenCV, FastAPI, React, NumPy, pandas and SciPy communities. Their permissively licensed work made "
            "an applied project of this kind feasible within a single semester."
        ),
        P(
            "Finally, we thank our families and friends for their encouragement throughout the semester, and "
            "our classmates for their willingness to sit through demonstrations and point out where the system "
            "behaved unexpectedly."
        ),
        Spacer(1, 1.2 * cm),
        P("Student Name 1, Student Name 2, Student Name 3", "BodyCenter"),
        P("Department of Computer Science and Engineering", "BodyCenter"),
        P("November 2026", "BodyCenter"),
    ]


def abstract() -> list:
    return [
        PageBreak(),
        P("ABSTRACT", "FrontTitle"),
        Spacer(1, 0.3 * cm),
        P(
            "Manual vehicle counting is still the standard method for collecting traffic volume data at "
            "intersections and highway sections, and it is expensive, slow and difficult to repeat. This "
            "project builds a complete, open-source pipeline that turns a single pre-recorded traffic video into "
            "directional, per-class vehicle counts over flexible time intervals. The pipeline detects vehicles "
            "with a modern pretrained Ultralytics YOLO model, associates detections across frames with ByteTrack "
            "or BoT-SORT, and counts each tracked vehicle once, when its reference point crosses a counting line "
            "drawn by the user on the first frame. Two parallel gate lines offset from the mid-line reproduce the "
            "direction logic of the base paper, while a fallback path counts vehicles that are first detected "
            "between the gate and the mid-line, which is a known source of systematic undercounting in "
            "line-counting systems."
        ),
        P(
            "The implementation is organised as a reusable Python package with a command-line interface and a "
            "browser frontend built with FastAPI and React. Video timestamps are derived from the frame index and "
            "the video frame rate rather than from processing time, so interval statistics are exact and "
            "independent of machine speed. Every run produces an annotated video, continuous interval counts in "
            "long and wide form, an event log, a JSON summary and the exact configuration used, which makes the "
            "results reproducible and auditable."
        ),
        P(
            "On a ten-second 768×432 traffic clip the system counted 16 vehicles (15 in the dominant direction, "
            "one against it) at 2.9 frames per second on a CPU-only laptop, and a fine-tuned single-class "
            "detector for auto-rickshaws, a class not present in COCO, reached mAP@50 of 0.995 on a held-out "
            "split. An evaluation module compares automated counts with manually logged ground truth and reports "
            "accuracy, signed error, precision, recall, F1, confidence intervals and a paired t-test. Because no "
            "manual ground truth exists for the traffic clip used here, count accuracy against manual reference "
            "is reported as pending; detector and tracker metrics are reported directly alongside it."
        ),
        Spacer(1, 0.25 * cm),
        P(
            "<b>Keywords:</b> vehicle counting, traffic monitoring, object detection, YOLO, multi-object "
            "tracking, ByteTrack, BoT-SORT, virtual line counting, video analytics, reproducibility.",
        ),
    ]


# ----------------------------------------------------------------- front lists
def _list_table(entries: list[tuple[str, int]], empty: str, width: float = 14.4) -> Table:
    rows = []
    if entries:
        for text, page in entries:
            rows.append([Paragraph(text, STYLES["TOC"]), Paragraph(str(page), STYLES["TOCPage"])])
    else:
        rows.append([Paragraph(empty, STYLES["TOC"]), Paragraph("", STYLES["TOCPage"])])
    t = Table(rows, colWidths=[width * cm, 1.6 * cm])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 2)]
    if entries:
        for i in range(len(rows) - 1):
            style.append(("LINEBELOW", (0, i), (-1, i), 0.25, LINE))
    t.setStyle(TableStyle(style))
    return t


def contents(records: dict) -> list:
    s = [PageBreak(), P("TABLE OF CONTENTS", "FrontTitle"), Spacer(1, 0.2 * cm)]
    rows = []
    entries = records.get("toc", [])
    if entries:
        for level, text, page in entries:
            style = STYLES["TOCBold"] if level == 0 else STYLES["TOC"]
            p = Paragraph(("&nbsp;" * 0) + text, style)
            p.leftIndent = {0: 0, 1: 14, 2: 30}.get(level, 0) * 1
            page_style = STYLES["TOCPageBold"] if level == 0 else STYLES["TOCPage"]
            rows.append([p, Paragraph(str(page), page_style)])
    else:
        rows.append([Paragraph("Generated on the next build pass.", STYLES["TOC"]), Paragraph("", STYLES["TOCPage"])])
    t = Table(rows, colWidths=[14.5 * cm, 1.5 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    s.append(t)
    return s


def list_of_figures(records: dict) -> list:
    return [
        PageBreak(),
        P("LIST OF FIGURES", "FrontTitle"),
        Spacer(1, 0.2 * cm),
        _list_table(records.get("fig", []), "Figures are listed after the first build pass."),
    ]


def list_of_tables(records: dict) -> list:
    return [
        PageBreak(),
        P("LIST OF TABLES", "FrontTitle"),
        Spacer(1, 0.2 * cm),
        _list_table(records.get("tab", []), "Tables are listed after the first build pass."),
    ]


# ------------------------------------------------------------------- chapter 1
def chapter1() -> list:
    s = chapter(1, "Introduction")
    s.append(section("1.1", "Introduction"))
    s.append(P(
        "Road traffic is measured in vehicles per unit time, separated by vehicle class and by direction of "
        "travel. Transport planners use these volumes to size intersections, time signals, estimate emissions "
        "and calibrate travel-demand models. In practice the measurement is still frequently made by a person "
        "watching a recording and clicking a tally counter, or by pneumatic tubes and inductive loops that are "
        "expensive to install and that fail silently when a lane is resurfaced."
    ))
    s.append(P(
        "Video is attractive because the sensor is already there. A camera mounted above a roadway records "
        "every vehicle that passes, needs no work on the road surface, and produces a record that can be "
        "reviewed later. The difficulty has always been the analysis: turning pixels into a defensible number. "
        "Classical approaches used background subtraction and blob tracking, which degrade quickly when the "
        "background is not static, when shadows move, or when vehicles overlap in congestion."
    ))
    s.append(P(
        "Recent object detectors based on convolutional and transformer backbones have changed the picture. A "
        "model trained on a large general dataset such as COCO already recognises cars, motorcycles, buses and "
        "trucks with high reliability in daylight footage, without any project-specific training. Pairing such a "
        "detector with a multi-object tracker produces a stable identity per vehicle across frames, and a "
        "vehicle that has an identity can be counted exactly once when it crosses a line chosen by the analyst. "
        "This report documents the design, implementation and evaluation of that pipeline as a complete tool."
    ))
    s.append(figure("../../outputs/uploads/a9d10de5_first_frame.jpg", "1.1",
                    "First frame of the traffic clip used for the reported runs: a fixed camera view of a "
                    "multi-lane road at a junction, with vehicles of several classes at different depths.", 14.6))
    s.append(P(
        "The system is deliberately built around a pretrained model. No detector is trained from scratch for "
        "the general four-class task, and no custom tracker is written: both choices keep the project focused on "
        "the parts that are actually specific to counting, namely line geometry, direction logic, identity "
        "management and interval aggregation, and they keep the result reproducible on a modest laptop."
    ))

    s.append(section("1.2", "Motivation"))
    s.append(P(
        "The immediate motivation is practical. A one-hour traffic survey recorded at 30 frames per second "
        "contains 108,000 frames. Reviewing it manually at even four times normal speed takes fifteen minutes "
        "of concentrated attention per hour of video, and the analyst must still classify every vehicle and "
        "note its direction. This is repetitive work that invites drift and fatigue, and the resulting counts "
        "cannot be audited afterwards because only the totals survive."
    ))
    s.append(P(
        "An automated pipeline addresses both problems. It processes every frame, so nothing is missed through "
        "inattention; it records an event for every counted vehicle with a timestamp and a pixel position, so "
        "any total can be traced back to individual crossings; and it produces the same numbers when run again "
        "on the same input, which manual counting does not. The cost is that the automated result must itself be "
        "validated, which is why this project treats evaluation as a first-class part of the deliverable rather "
        "than an afterthought."
    ))
    s.append(P(
        "There is also a research motivation. The base paper for this project reports a consistent "
        "under-counting bias and attributes part of it to vehicles that are detected too late to be associated "
        "with a counting line, and part to the fact that processing was slower than real time, which forced the "
        "authors to derive reporting intervals from processing time rather than from the video. Both issues are "
        "avoidable with a current pipeline, and demonstrating that is a useful, if modest, contribution."
    ))

    s.append(section("1.3", "Objectives"))
    s.append(P("The project sets out to achieve the following objectives:"))
    s.append(bullets([
        "Build an end-to-end pipeline that converts a pre-recorded traffic video into per-class, per-direction "
        "vehicle counts at a counting line defined by the user.",
        "Aggregate counts into fixed time intervals derived from video timestamps, with continuous interval "
        "coverage and both long and wide tabular exports.",
        "Produce an annotated output video in which every counted vehicle, its track identity, the counting "
        "geometry and the running totals are visible, so that results can be inspected rather than trusted.",
        "Provide a browser frontend that lets a user upload a video, place the counting line, run the pipeline "
        "with live progress and download all artefacts, using the same pipeline code as the command-line tool.",
        "Implement an evaluation module that compares automated counts with manually logged ground truth at "
        "both count level and event level, including accuracy, signed error, precision, recall, F1 and "
        "statistical tests.",
        "Keep the whole system reproducible: configuration-driven, versioned, and free of hard-coded paths, "
        "model names or thresholds.",
    ]))

    s.append(section("1.4", "Scope of the Project"))
    s.append(P(
        "The scope is a single fixed camera and a single counting line per run. The tool assumes that the "
        "camera does not move during the clip and that the road surface visible in the frame is the region of "
        "interest; it does not perform camera calibration, speed estimation or number-plate recognition. "
        "Vehicles that remain parked inside the frame are not counted, by design, because they never cross the "
        "line. The system reports counts, not trajectories, and it does not attempt to re-identify a vehicle "
        "across different cameras."
    ))
    s.append(P(
        "Four vehicle classes are counted by default, namely car, motorcycle, bus and truck, taken from the "
        "COCO class set, with bicycle available as an option. An additional single-class detector for "
        "auto-rickshaws is trained to show how a regionally important class that COCO does not contain can be "
        "added without changing the rest of the pipeline. The reported experiments use short clips rather than "
        "full survey days; the architecture streams frames and never holds a video in memory, so longer clips "
        "are a matter of processing time rather than of design."
    ))

    s.append(section("1.5", "Organisation of the Report"))
    s.append(P(
        "Chapter 2 introduces the basic concepts behind detection, tracking and line-based counting, and reviews "
        "the literature, including the paper on which the project is based. Chapter 3 states the problem and "
        "presents the requirements, the project plan, the design constraints and the system architecture. "
        "Chapter 4 describes the implementation, the testing strategy and the results obtained, with screenshots "
        "from the running system. Chapter 5 records the design, coding and testing standards adopted and gives a "
        "cost analysis. Chapter 6 concludes and lists future work, after which the references, individual "
        "contributions and the plagiarism report are appended."
    ))
    return s


# ------------------------------------------------------------------- chapter 2
def chapter2() -> list:
    s = chapter(2, "Basic Concepts and Literature Review")
    s.append(section("2.1", "Basic Concepts"))
    s.append(P(
        "The pipeline rests on three ideas that are worth separating: detecting objects in a single frame, "
        "associating those detections over time, and converting a track into a count. Each has its own failure "
        "modes, and most counting errors can be traced to one of the three rather than to the system as a whole."
    ))

    s.append(subsection("2.1.1", "Object Detection with YOLO"))
    s.append(P(
        "A single-stage detector predicts class probabilities and box coordinates directly from the feature map "
        "of an image in one forward pass, which is why it is fast enough for video. The YOLO family, introduced "
        "by Redmon et al. in 2016, framed detection as a regression problem over a grid and has since moved "
        "through several architectural generations. Contemporary versions use a CSP-style backbone, a "
        "feature-pyramid neck and a decoupled head, and the most recent releases remove the non-maximum "
        "suppression step by predicting a fixed set of non-overlapping boxes, which simplifies deployment and "
        "makes latency more predictable."
    ))
    s.append(P(
        "Two properties matter for this project. First, the models are trained on COCO, whose 80 classes "
        "include car, motorcycle, bus, truck and bicycle, so a usable detector is available without any "
        "project-specific training. Second, the models come in several sizes, from a few million to several "
        "tens of millions of parameters, which allows the same code to trade accuracy for speed depending on "
        "whether a GPU is present. Detection quality is measured by mean average precision, mAP@50 for a loose "
        "overlap threshold and mAP@50-95 averaged over thresholds from 0.5 to 0.95 in steps of 0.05."
    ))

    s.append(subsection("2.1.2", "Multi-Object Tracking"))
    s.append(P(
        "A tracker turns per-frame detections into trajectories. The classical formulation, used by SORT and "
        "its descendants, predicts each existing track forward with a Kalman filter, associates predictions with "
        "new detections using the Hungarian algorithm on an affinity matrix, and creates or deletes tracks "
        "according to confidence and age rules. DeepSORT added an appearance embedding to the affinity, which "
        "helps when vehicles cross, at the cost of a second network per detection."
    ))
    s.append(P(
        "ByteTrack observes that low-confidence detections are usually real objects rather than noise, and "
        "associates them in a second matching stage instead of discarding them. This improves recall in "
        "congestion at almost no computational cost. BoT-SORT extends the same idea with camera-motion "
        "compensation and a lightweight appearance model, and is the better choice when the camera shakes or "
        "when vehicles are occluded for long periods. Both are provided by the Ultralytics tracking API used "
        "here, so the project does not implement either."
    ))
    s.append(P(
        "Identity errors are the main threat to count correctness. A vehicle hidden behind a bus may be "
        "re-identified with a new track identifier when it reappears, which produces two counts for one vehicle; "
        "conversely, two vehicles that pass close together may share an identifier, which produces one count for "
        "two. The design must therefore ensure that no identifier is ever counted twice, and must offer an "
        "optional guard against near-duplicate crossings."
    ))

    s.append(subsection("2.1.3", "Virtual Line Counting and Direction"))
    s.append(P(
        "A virtual line reduces counting to a geometric predicate on a track's reference point. The base paper "
        "draws a mid-line on the first frame and generates two parallel lines on either side, forming a gate. A "
        "vehicle that first touches one gate and then crosses the mid-line is counted, and the gate it touched "
        "determines its direction. The gate requirement suppresses tracks that appear on the line itself, but it "
        "also causes the paper's undercounting: a vehicle first detected after it has already passed the gate is "
        "never counted."
    ))
    s.append(P(
        "The reference point within the bounding box also matters. The geometric centre is the obvious choice, "
        "but in a perspective view the centre of a tall vehicle sits above the road contact point and can cross "
        "the line at a different moment than the vehicle does. The bottom-centre point lies on the road surface "
        "and is therefore the default in this project. Figure 2.1 shows the three stages of the pipeline with "
        "the counting geometry."
    ))
    s.append(figure("fig_concept.png", "2.1",
                    "Conceptual pipeline: detections are associated into tracks, a reference point per track is "
                    "tested against the counting line, and crossings are aggregated into intervals."))

    s.append(subsection("2.1.4", "Interval Aggregation and Evaluation"))
    s.append(P(
        "Traffic data are reported per interval, typically every 5 or 15 minutes. Given an interval length L and "
        "an event timestamp t, the interval index is the floor of t divided by L. Aggregating by index produces "
        "a tidy table with one row per interval, direction and class, which can be pivoted into the wide form "
        "used by traffic engineers. Intervals with no events must still appear, otherwise a gap in the data is "
        "indistinguishable from a gap in the report."
    ))
    s.append(P(
        "Evaluation compares these numbers with manual counts. Count-level accuracy is "
        "100 − |auto − manual| / manual × 100 per class and direction; the signed error "
        "(auto − manual) / manual × 100 carries the direction of the mistake and is the right statistic for "
        "testing a claim of systematic bias. Event-level matching, which pairs each automated event with a "
        "manual event of the same class and direction within a time tolerance, yields precision, recall and F1 "
        "and separates missed vehicles from spurious ones."
    ))

    s.append(section("2.2", "Literature Review"))
    s.append(P(
        "Majumder and Wilmot [1] is the base paper. They count vehicles in pre-recorded video with a YOLOv3 "
        "detector, a SORT-like Kalman box tracker and a mid-line with two parallel gate lines, and they report "
        "directional counts per flexible interval, comparison with manual counts, a paired t-test and an "
        "analysis of undercounting. Their most useful contributions for this project are the gate geometry and "
        "the honesty of the evaluation; their main limitations are an older detector, single-class counting, "
        "manual file handling and intervals derived from processing time because inference was slower than "
        "real time."
    ))
    s.append(P(
        "Bewley et al. [2] introduced SORT, which established the predict-associate-update loop that later "
        "trackers still follow. Wojke et al. [3] added appearance features in DeepSORT, improving identity "
        "retention through occlusion at extra cost. Zhang et al. [4] proposed ByteTrack, whose two-stage "
        "association of high- and low-confidence detections is both simple and effective; it is the default "
        "tracker here. Aharon et al. [5] proposed BoT-SORT, which adds camera-motion compensation and a "
        "re-identification branch, and is offered as the alternative for difficult footage."
    ))
    s.append(P(
        "On the detection side, Redmon et al. [6] introduced YOLO and the single-stage formulation. The "
        "Ultralytics implementation [7] maintains the current generations and, importantly for reproducibility, "
        "packages training, validation, inference and tracking behind one interface with published pretrained "
        "weights. Jocher et al. are cited as the maintainers rather than as authors of a novel architecture, "
        "which is the accurate attribution."
    ))
    s.append(P(
        "Two further strands inform the design. Work on vision-based traffic monitoring consistently reports "
        "that counting errors concentrate at occlusion boundaries and at the frame edges, which motivates the "
        "bottom-centre reference point and the minimum-track-length rule used here. Work on reproducible "
        "research emphasises recording the exact configuration and software versions alongside results, which "
        "the exporter does by writing the configuration and a version block into every run directory."
    ))
    s.append(P(
        "Table 2.1 summarises how this project differs from the base paper. The comparison is deliberately "
        "narrow: it lists only the choices that change what the system can do or how its results can be trusted."
    ))
    s.extend(data_table(
        "2.1",
        "Comparison of the base paper with the present system.",
        ["Aspect", "Base paper [1]", "This project"],
        [
            ["Detector", "YOLOv3, Darknet weights converted to TensorFlow", "Pretrained Ultralytics YOLO (YOLO26 / YOLO11), four COCO classes"],
            ["Tracker", "Kalman box tracker, SORT-like", "ByteTrack (default) or BoT-SORT, via the Ultralytics API"],
            ["Classes counted", "All vehicles as one class", "Car, motorcycle, bus, truck; bicycle optional; custom auto-rickshaw model"],
            ["Counting geometry", "Mid-line with two parallel gate lines", "Same gate geometry, plus a fallback for late-spawned tracks"],
            ["Interval basis", "Processing time, because inference was slower than real time", "Video timestamps (frame index / fps), independent of machine speed"],
            ["Operation", "Manual file names, drag-and-drop folders", "YAML configuration, command line and browser frontend"],
            ["Validation", "Manual counts, paired t-test, undercount analysis", "Same, plus event-level precision, recall, F1 and per-interval metrics"],
            ["Reproducibility", "Not reported", "Config, software versions and event log written per run"],
        ],
        [3.0, 6.2, 6.8],
    ))

    s.append(subsection("2.2.1", "Research Gap"))
    s.append(P(
        "The gap this project addresses is not a missing algorithm; the components are all published and "
        "available. It is the absence of an integrated, inspectable and reproducible implementation of "
        "line-based counting on top of current detectors and trackers, with an evaluation path that a student "
        "or a small agency can actually run. The base paper demonstrates the method but predates the current "
        "tooling and does not publish code; commercial products exist but are closed. Building the open version, "
        "measuring it honestly and documenting where it fails is the contribution."
    ))
    return s


# ------------------------------------------------------------------- chapter 3
def chapter3() -> list:
    s = chapter(3, "Problem Statement and Requirement Specifications")
    s.append(P(
        "<b>Problem statement.</b> Given a pre-recorded traffic video from a stationary camera and a counting line drawn on its first "
        "frame, produce per-class, per-direction vehicle counts for each fixed time interval of video time, "
        "together with an annotated video that makes each count verifiable, and an evaluation of the counts "
        "against manual ground truth. The system must run without a GPU, must never count the same vehicle "
        "twice, and must expose enough configuration that a different site can be handled without editing code."
    ))
    s.append(P(
        "Stated as requirements, this decomposes into four problems. Detection must be accurate enough that "
        "small and distant vehicles are found, which argues for an input resolution above the default. "
        "Association must survive short occlusions, which argues for a tracker that uses low-confidence "
        "detections and a reasonable track buffer. Counting must be robust to a reference point that jitters "
        "around the line and to vehicles that are detected only after they have entered the counting zone. "
        "Reporting must be complete and traceable, which argues for continuous intervals, an event log and a "
        "recorded configuration."
    ))

    s.append(section("3.1", "Project Planning"))
    s.append(P(
        "The work was planned over ten weeks in the milestones shown in Table 3.1, following the build order in "
        "the project specification. Each milestone ended with the test suite passing and a short written "
        "summary, which kept regressions visible and made the final report a matter of assembling results "
        "rather than reconstructing them."
    ))
    s.extend(data_table(
        "3.1",
        "Project plan and milestone status.",
        ["Week", "Milestone", "Main deliverables", "Status"],
        [
            ["1", "Scaffold", "Repository layout, requirements, configuration dataclasses and validation tests", "Complete"],
            ["2", "Video input and line setup", "Video metadata, frame reader, interactive and headless line selection, geometry tests", "Complete"],
            ["3", "Detector and tracker wrapper", "Ultralytics wrapper yielding a stable per-frame interface, device selection", "Complete"],
            ["4", "Counter", "Simple and gated crossing logic, hysteresis, class voting, unit tests", "Complete"],
            ["5", "Intervals and export", "Time bucketing, wide and long CSVs, event log, JSON summary", "Complete"],
            ["6", "Annotation and pipeline", "Overlay drawing, full pipeline, command-line interface, annotated video", "Complete"],
            ["7", "Evaluation", "Ground-truth template, count and event metrics, statistics, report and plots", "Complete"],
            ["8", "Benchmark", "Model and tracker comparison harness", "Complete"],
            ["9", "Web frontend", "FastAPI service, WebSocket progress, React interface, upload and results", "Complete"],
            ["10", "Polish and documentation", "README, pipeline guide, lint, final test run, this report", "Complete"],
        ],
        [1.3, 3.6, 8.9, 2.2],
    ))

    s.append(section("3.2", "Project Analysis and Requirement Specifications"))
    s.append(P(
        "Requirements were elicited from the base paper, from the practical constraints of a semester project "
        "and from a small number of informal interviews with fellow students who had performed manual traffic "
        "surveys. The functional requirements are listed in Table 3.2 and the non-functional requirements in "
        "Table 3.3."
    ))
    s.extend(data_table(
        "3.2",
        "Functional requirements.",
        ["ID", "Requirement", "Acceptance"],
        [
            ["FR1", "Read common video containers and report metadata", "mp4, avi, mov and mkv accepted; fps, resolution and duration displayed"],
            ["FR2", "Accept a counting line interactively, by argument or from a saved file", "Line can be picked, typed or loaded, and is saved as JSON"],
            ["FR3", "Detect and track vehicles of the configured classes", "Stable track identifiers across frames; empty frames handled"],
            ["FR4", "Count each track at most once, with direction", "No duplicate counts for one identifier; direction label configurable"],
            ["FR5", "Aggregate counts into fixed video-time intervals", "Continuous interval table, zero rows included, totals consistent"],
            ["FR6", "Write an annotated video and machine-readable outputs", "Annotated mp4, wide and long CSVs, events CSV, summary JSON, config copy"],
            ["FR7", "Provide a browser interface over the same pipeline", "Upload, line placement, progress, live preview, results and downloads"],
            ["FR8", "Compare automated counts with ground truth", "Accuracy, signed error, precision, recall, F1, t-test, plots"],
            ["FR9", "Allow cancellation with partial results preserved", "Stop request ends the run and keeps outputs written so far"],
            ["FR10", "Support a custom class outside COCO", "A single-class model can be trained and added through configuration"],
        ],
        [1.2, 7.4, 7.4],
    ))
    s.extend(data_table(
        "3.3",
        "Non-functional requirements.",
        ["ID", "Category", "Requirement"],
        [
            ["NFR1", "Performance", "Process a one-minute 720p clip on a CPU-only machine with the smallest model in reasonable time; stream frames without loading the video into memory"],
            ["NFR2", "Portability", "Run on Windows, Linux and macOS with Python 3.10 or newer; use CUDA, MPS or CPU automatically"],
            ["NFR3", "Usability", "A new user can produce counts without editing code, using configuration, command-line flags or the browser interface"],
            ["NFR4", "Reliability", "Writer handles are released on error; a failed frame is logged and skipped rather than aborting the run"],
            ["NFR5", "Reproducibility", "The exact configuration and software versions are stored with every run; repeated runs on the same input give identical counts"],
            ["NFR6", "Maintainability", "Typed public functions with docstrings, single-purpose modules, logging instead of print"],
            ["NFR7", "Testability", "Counter, geometry, interval and evaluation logic tested without a real video or a model download"],
            ["NFR8", "Licensing", "Only open-source dependencies; AGPL obligations of the detector noted in the documentation"],
        ],
        [1.2, 2.8, 12.0],
    ))
    s.append(P(
        "The development and test environment is summarised in Table 3.4. The reported runs were produced on a "
        "CPU-only laptop, which is the pessimistic case for the project: the same code uses CUDA or MPS "
        "automatically when either is available, and the tracker throughput measurements in Section 4.3 were "
        "taken on a T4 GPU for comparison."
    ))
    s.extend(data_table(
        "3.4",
        "Hardware and software environment.",
        ["Item", "Specification"],
        [
            ["Operating system", "Windows 11 (development), Linux-compatible code base"],
            ["Processor and memory", "x86-64 laptop CPU, 16 GB RAM, no discrete GPU for the reported runs"],
            ["Python", "3.11 (project), 3.12 and 3.13 used for auxiliary tooling"],
            ["Core libraries", "ultralytics 8.4.173, torch 2.13.0+cpu, opencv-python 4.13.0, numpy, pandas, scipy, PyYAML"],
            ["Web stack", "FastAPI, Uvicorn, WebSocket; React 18 with Vite and TypeScript"],
            ["Reporting tools", "ReportLab, matplotlib, PyMuPDF"],
            ["Browser", "Google Chrome (testing)"],
        ],
        [4.2, 11.6],
    ))

    s.append(section("3.3", "System Design"))
    s.append(subsection("3.3.1", "Design Constraints"))
    s.append(P("The design is shaped by six constraints, each of which rules out an otherwise reasonable option."))
    s.append(bullets([
        "<b>Fixed camera.</b> No camera-motion model is assumed, so the counting geometry can be defined once on "
        "the first frame and reused for every subsequent frame. A moving camera would require per-frame "
        "homography, which is out of scope.",
        "<b>CPU-first execution.</b> The system must be usable without a GPU. This fixes the default model at a "
        "small or medium size and rules out architectures that need a second network per detection for "
        "appearance matching.",
        "<b>Streaming memory.</b> A one-hour 1080p video is several gigabytes. Frames are consumed from a "
        "generator and written one at a time; no stage holds more than a frame plus a bounded amount of track "
        "state.",
        "<b>Browser delivery.</b> The frontend runs in a browser, so video must be H.264 for inline playback and "
        "uploads are capped by the server configuration. OpenCV writes MPEG-4 Part 2 by default, which many "
        "browsers will not play, so a re-encode path is required.",
        "<b>Licensing.</b> Ultralytics is AGPL-3.0. The project is academic and open, so this is acceptable, but "
        "it is recorded in the README because it would matter for commercial deployment.",
        "<b>Geometry in pixels.</b> The counting line is defined in image coordinates, not in metres. The system "
        "therefore reports counts, not densities or speeds, and the line must be placed by a human who "
        "understands the scene.",
    ]))

    s.append(subsection("3.3.2", "System Architecture"))
    s.append(P(
        "The system is layered so that the counting logic has no dependency on the detector library, the web "
        "framework or the file format. Figure 3.1 shows the layers and the direction of data flow."
    ))
    s.append(figure("fig_architecture.png", "3.1",
                    "Layered system architecture. The counting, interval and evaluation modules depend only on "
                    "plain data structures, which allows them to be tested without a model or a video."))
    s.append(P(
        "The video and line layer reads metadata and frames, and resolves the counting geometry from an "
        "interactive picker, a coordinate argument or a saved JSON file. The perception layer wraps the "
        "Ultralytics model and tracker and converts each frame of results into a list of tracked objects with a "
        "plain box, class and confidence, so that the rest of the code never sees a library-specific type. The "
        "analysis layer contains the counter and the interval aggregator. The presentation layer contains the "
        "annotator, the exporter, the command-line interface and the web service. The evaluation layer reads a "
        "run directory and a ground-truth file and is independent of the rest."
    ))
    s.extend(data_table(
        "3.5",
        "Module responsibilities.",
        ["Module", "Responsibility", "Key interface"],
        [
            ["config", "Load, type and validate YAML configuration", "AppConfig, load_config()"],
            ["video_io", "Video metadata, first frame, writer context", "get_video_info(), VideoWriterContext"],
            ["line_setup", "Line capture, gate lines, geometry, JSON persistence", "CountingLine, side_of_line(), gate_lines()"],
            ["detector_tracker", "Wrap model.track() into frame results", "FrameResult, TrackedObject, iter_frames()"],
            ["counter", "Track state, crossing detection, direction, deduplication", "LineCounter.update(), totals()"],
            ["intervals", "Bucket events into continuous intervals", "bucket_events(), pivot_intervals()"],
            ["annotate", "Draw boxes, trails, lines and heads-up counters", "draw_frame()"],
            ["exporter", "Write CSVs, summary JSON and configuration copy", "export_run()"],
            ["pipeline", "Orchestrate a run and report progress", "run_pipeline(), RunResult"],
            ["evaluate", "Compare events with ground truth, statistics and plots", "evaluate_run(), write_report()"],
            ["server / app", "HTTP and WebSocket API, React interface", "/api/pipeline/start, /ws/pipeline/{id}"],
        ],
        [2.9, 8.2, 4.7],
    ))
    s.append(P(
        "Counting geometry is defined on a line through two points P1 and P2. For a point P the signed area "
        "value of the cross product determines the side,"
    ))
    s.append(P("side(P) = (x2 − x1)(py − y1) − (y2 − y1)(px − x1)", "BodyCenter"))
    s.append(P(
        "with negative values on side A and positive values on side B, and the signed perpendicular distance is "
        "that value divided by the length of the line. The two gate lines are parallel copies displaced by plus "
        "and minus the gate offset along the unit normal. Because the normal is perpendicular to the line "
        "direction, scaling it by the offset gives points at exactly that distance, as Figure 3.2 illustrates."
    ))
    s.append(figure("fig_gate.png", "3.2",
                    "Counting geometry: mid-line, two gate lines at ±δ along the unit normal, and the signed "
                    "distance of a vehicle reference point used for direction and hysteresis."))
    s.append(P(
        "In gated mode a track is counted when it has touched one gate and then crosses the mid-line towards the "
        "opposite side; the gate touched first determines the direction label. In simple mode only the sign "
        "change is required. In both modes a hysteresis band of 1.5 pixels around the line prevents a vehicle "
        "that jitters on the line from being counted twice, and a per-track flag makes a second count impossible "
        "even if the vehicle crosses back. If a track crosses the mid-line without ever having touched a gate, "
        "the gated mode falls back to the sign-change direction and logs that the fallback was used."
    ))
    s.append(P(
        "The class assigned to a count is not the class in the current frame. Each track accumulates confidence-"
        "weighted votes per class identifier as it is observed, and the majority class at the moment of counting "
        "is used. This suppresses the car-to-truck flicker that a detector produces on vans and pickups, which "
        "would otherwise appear as class confusion in the evaluation even though the vehicle was counted once."
    ))
    s.append(P("The per-frame procedure is summarised below."))
    s.append(bullets([
        "Read the next frame and its original index, and compute the timestamp as the index divided by the "
        "frame rate of the source video.",
        "Detect and track; convert the results into tracked objects with box, class, confidence and identifier, "
        "returning an empty list when nothing is tracked.",
        "For each object, compute the reference point, the signed side and the signed distance, and update or "
        "create its track state.",
        "Record a gate touch if the distance has reached the gate offset and none was recorded yet.",
        "Detect a crossing when the last non-zero side and the current side have opposite signs and the "
        "distance is outside the hysteresis band, then apply the mode-specific direction rule.",
        "Emit a count event with the majority class, append it to the event list, and mark the track as counted.",
        "Periodically discard the state of tracks that have not been seen for a bounded number of frames.",
    ]))
    s.append(P(
        "The interaction between a client and the service is shown in Figure 3.3. The upload is streamed to a "
        "temporary directory, the line preview is generated from the first frame, and the run is executed in a "
        "worker thread whose progress is pushed to the browser over a WebSocket. The same pipeline function is "
        "used by the command-line tool, so the two interfaces cannot diverge."
    ))
    s.append(figure("fig_sequence.png", "3.3",
                    "Sequence of interactions in the browser interface, from upload to result download."))
    s.append(P(
        "Deployment is deliberately simple, as Figure 3.4 shows: a single host runs the FastAPI service, which "
        "serves the compiled React bundle and owns the model, the video files and the output directory. The "
        "browser needs no plugin and no local installation. Because inference is the expensive step, the host is "
        "the machine with the GPU when one exists, and the model is cached for the lifetime of the process so "
        "that consecutive runs do not pay the load cost."
    ))
    s.append(figure("fig_deployment.png", "3.4",
                    "Deployment view: the browser talks to a single FastAPI host that serves the static bundle "
                    "and performs detection, tracking, counting and export."))
    return s
