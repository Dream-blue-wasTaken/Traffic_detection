import pytest
import pandas as pd
from vcount.evaluate import compute_count_metrics, match_events, run_paired_statistics


def test_compute_count_metrics_perfect():
    res = compute_count_metrics(auto_count=100, manual_count=100)
    assert res["accuracy_pct"] == 100.0
    assert res["signed_error_pct"] == 0.0
    assert res["diff"] == 0


def test_compute_count_metrics_undercount():
    # Auto = 80, Manual = 100 -> 20% undercounting
    res = compute_count_metrics(auto_count=80, manual_count=100)
    assert res["accuracy_pct"] == 80.0
    assert res["signed_error_pct"] == -20.0
    assert res["diff"] == -20


def test_match_events_one_to_one():
    # Auto has two events close to a single GT event
    auto_df = pd.DataFrame([
        {"timestamp_s": 10.1, "direction": "entry", "class_name": "car"},
        {"timestamp_s": 10.4, "direction": "entry", "class_name": "car"},
    ])
    gt_df = pd.DataFrame([
        {"timestamp_s": 10.0, "direction": "entry", "class_name": "car"},
    ])

    res = match_events(auto_df, gt_df, tolerance_s=1.0)
    # Only one can match GT (one-to-one)
    assert res["tp"] == 1
    assert res["fp"] == 1
    assert res["fn"] == 0
    assert pytest.approx(res["precision"], 0.01) == 0.5
    assert pytest.approx(res["recall"], 0.01) == 1.0
    assert pytest.approx(res["f1"], 0.01) == 0.6667


def test_paired_statistics_five_samples():
    auto = [10.0, 15.0, 20.0, 25.0, 30.0]
    manual = [11.0, 16.0, 21.0, 24.0, 31.0]
    stats = run_paired_statistics(auto, manual)

    assert stats is not None
    assert stats["n"] == 5
    assert "mean_diff" in stats
    assert "paired_t_pvalue" in stats
    assert "ci_95_low" in stats
    assert "ci_95_high" in stats
