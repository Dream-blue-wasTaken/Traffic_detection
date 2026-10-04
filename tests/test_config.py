import pytest
from vcount.config import Config, load_config, validate_config


def test_default_config_valid():
    cfg = load_config()
    assert cfg.model.weights == "yolo26m.pt"
    assert cfg.tracker.type == "bytetrack"
    assert cfg.counting.mode == "gated"
    assert cfg.intervals.length_seconds == 900
    assert cfg.video.frame_stride == 1


def test_load_default_yaml(tmp_path):
    cfg = load_config("configs/default.yaml")
    assert cfg.model.conf == 0.35
    assert cfg.intervals.length_seconds == 900


def test_invalid_interval_raises():
    cfg = Config()
    cfg.intervals.length_seconds = 0
    with pytest.raises(ValueError, match="intervals.length_seconds"):
        validate_config(cfg)


def test_invalid_frame_stride_raises():
    cfg = Config()
    cfg.video.frame_stride = 0
    with pytest.raises(ValueError, match="video.frame_stride"):
        validate_config(cfg)


def test_invalid_tracker_raises():
    cfg = Config()
    cfg.tracker.type = "unknown_tracker"
    with pytest.raises(ValueError, match="tracker.type"):
        validate_config(cfg)


def test_invalid_mode_raises():
    cfg = Config()
    cfg.counting.mode = "invalid_mode"
    with pytest.raises(ValueError, match="counting.mode"):
        validate_config(cfg)


def test_invalid_conf_raises():
    cfg = Config()
    cfg.model.conf = 1.5
    with pytest.raises(ValueError, match="model.conf"):
        validate_config(cfg)


def test_overrides_applied():
    overrides = {
        "model": {"conf": 0.42, "weights": "yolo11s.pt"},
        "counting": {"mode": "simple"},
    }
    cfg = load_config(overrides=overrides)
    assert cfg.model.conf == 0.42
    assert cfg.model.weights == "yolo11s.pt"
    assert cfg.counting.mode == "simple"
