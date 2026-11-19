"""Environment-backed hardware settings for the porch detector."""

import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip() or value.startswith("<"):
        raise RuntimeError(f"Set {name} to a confirmed hardware value before running.")
    return value.strip()


def _required_int(name: str) -> int:
    return int(_required(name))


def _required_float(name: str) -> float:
    return float(_required(name))


PIR_GPIO = _required_int("PIR_GPIO")
SERVO_GPIO = _required_int("SERVO_GPIO")
SERVO_IDLE_VALUE = _required_float("SERVO_IDLE_VALUE")
SERVO_VIEW_VALUE = _required_float("SERVO_VIEW_VALUE")
CAMERA_SETTLE_SECONDS = float(os.environ.get("CAMERA_SETTLE_SECONDS", "2.0"))
DIFF_THRESHOLD = float(os.environ.get("DIFF_THRESHOLD", "18.0"))
REFERENCE_IMAGE = os.environ.get("REFERENCE_IMAGE", "data/empty_porch.jpg")
CAPTURE_IMAGE = os.environ.get("CAPTURE_IMAGE", "data/latest_capture.jpg")
