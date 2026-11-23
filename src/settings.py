"""Configuration for the camera and 28BYJ-48/ULN2003 setup.

GPIO values are BCM numbers. The team's confirmed physical header pins
11, 12, 13, and 15 correspond to BCM GPIO17, GPIO18, GPIO27, and GPIO22.
"""

from pathlib import Path
import json
import os


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CAPTURE_DIR = Path(os.environ.get("CAPTURE_DIR", DATA_DIR / "captures"))
REFERENCE_IMAGE = Path(os.environ.get("REFERENCE_IMAGE", CAPTURE_DIR / "empty_porch.jpg"))
MAX_SAVED_CAPTURES = int(os.environ.get("MAX_SAVED_CAPTURES", "25"))
CALIBRATION_FILE = DATA_DIR / "stepper_calibration.json"

# Keep this order matched to ULN2003 IN1, IN2, IN3, IN4.
MOTOR_GPIO_PINS = (17, 18, 27, 22)
STEP_DELAY_SECONDS = float(os.environ.get("STEP_DELAY_SECONDS", "0.004"))


def get_steps_to_porch() -> int:
    """Read saved porch travel, unless a temporary shell override is set."""
    override = os.environ.get("STEPS_TO_PORCH")
    if override is not None:
        return int(override)
    if not CALIBRATION_FILE.is_file():
        raise RuntimeError(
            f"No saved stepper calibration at {CALIBRATION_FILE}. "
            "Run `python3 -m src.stepper_setup` and mark the porch position first."
        )
    try:
        data = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        return int(data["porch_steps"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"No valid porch_steps value in {CALIBRATION_FILE}. "
            "Run `python3 -m src.stepper_setup` and mark the porch position."
        ) from exc

CAMERA_SIZE = (640, 480)
CAMERA_FPS = 8
CAMERA_SETTLE_SECONDS = float(os.environ.get("CAMERA_SETTLE_SECONDS", "1.5"))

# Tune these after observing the system in its actual lighting.
MOTION_PIXEL_THRESHOLD = int(os.environ.get("MOTION_PIXEL_THRESHOLD", "25"))
MOTION_FRACTION_THRESHOLD = float(os.environ.get("MOTION_FRACTION_THRESHOLD", "0.025"))
MOTION_CONFIRM_FRAMES = int(os.environ.get("MOTION_CONFIRM_FRAMES", "3"))
MOTION_FRAME_INTERVAL = float(os.environ.get("MOTION_FRAME_INTERVAL", "0.25"))
EVENT_COOLDOWN_SECONDS = float(os.environ.get("EVENT_COOLDOWN_SECONDS", "15"))
SCENE_CHANGE_THRESHOLD = float(os.environ.get("SCENE_CHANGE_THRESHOLD", "12.0"))

# Optional Twilio SMS configuration. Leave unset for console-only alerts.
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
ALERT_TO_NUMBER = os.environ.get("ALERT_TO_NUMBER", "")
