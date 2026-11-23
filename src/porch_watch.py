"""Camera motion detector that tilts to the porch, captures, and alerts.

This detects visible motion and change from a reference photo. It does not
identify a person, package, or food item.
"""

from datetime import datetime
from pathlib import Path
import time

import cv2
from gpiozero import OutputDevice
from picamera2 import Picamera2

from .notifications import send_alert
from .settings import (
    CAMERA_FPS,
    CAMERA_SETTLE_SECONDS,
    CAMERA_SIZE,
    CAPTURE_IMAGE,
    EVENT_COOLDOWN_SECONDS,
    MOTION_CONFIRM_FRAMES,
    MOTION_FRACTION_THRESHOLD,
    MOTION_FRAME_INTERVAL,
    MOTION_PIXEL_THRESHOLD,
    MOTOR_GPIO_PINS,
    REFERENCE_IMAGE,
    SCENE_CHANGE_THRESHOLD,
    STEP_DELAY_SECONDS,
    STEPS_TO_PORCH,
)


HALF_STEP_SEQUENCE = (
    (1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0),
    (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1), (1, 0, 0, 1),
)


class Stepper:
    """Small half-step controller for a 28BYJ-48 driven by a ULN2003."""

    def __init__(self) -> None:
        self.coils = [OutputDevice(pin, initial_value=False) for pin in MOTOR_GPIO_PINS]
        self.index = 0

    def _apply(self) -> None:
        for coil, value in zip(self.coils, HALF_STEP_SEQUENCE[self.index]):
            coil.value = bool(value)

    def move(self, steps: int) -> None:
        direction = 1 if steps >= 0 else -1
        try:
            for _ in range(abs(steps)):
                self.index = (self.index + direction) % len(HALF_STEP_SEQUENCE)
                self._apply()
                time.sleep(STEP_DELAY_SECONDS)
        except KeyboardInterrupt:
            self.release()
            raise

    def release(self) -> None:
        for coil in self.coils:
            coil.off()

    def close(self) -> None:
        self.release()
        for coil in self.coils:
            coil.close()


def grayscale(frame):
    """Convert a camera frame to a small, blurred grayscale motion image."""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, (320, 240))
    return cv2.GaussianBlur(gray, (5, 5), 0)


def motion_fraction(previous, current) -> float:
    """Fraction of pixels whose brightness changed by more than the threshold."""
    delta = cv2.absdiff(previous, current)
    _, mask = cv2.threshold(delta, MOTION_PIXEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    return cv2.countNonZero(mask) / mask.size


def scene_difference(reference_path: Path, capture_path: Path) -> float:
    """Mean grayscale difference (0..255) between reference and captured scene."""
    reference = cv2.imread(str(reference_path), cv2.IMREAD_GRAYSCALE)
    capture = cv2.imread(str(capture_path), cv2.IMREAD_GRAYSCALE)
    if reference is None:
        raise FileNotFoundError(f"Reference image is missing or unreadable: {reference_path}")
    if capture is None:
        raise FileNotFoundError(f"Captured image is missing or unreadable: {capture_path}")
    if capture.shape != reference.shape:
        capture = cv2.resize(capture, (reference.shape[1], reference.shape[0]))
    return float(cv2.absdiff(reference, capture).mean())


def capture_jpeg(camera: Picamera2, path: Path) -> None:
    """Capture the current camera view to a JPEG file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = camera.capture_array("main")
    # Picamera2's RGB888 array is RGB; OpenCV's JPEG writer expects BGR.
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    if not cv2.imwrite(str(path), bgr):
        raise OSError(f"Could not save image: {path}")


def handle_event(camera: Picamera2, stepper: Stepper) -> None:
    print("Motion confirmed. Moving to porch view...")
    moved = False
    try:
        stepper.move(STEPS_TO_PORCH)
        moved = True
        time.sleep(CAMERA_SETTLE_SECONDS)
        capture_jpeg(camera, CAPTURE_IMAGE)

        score = scene_difference(REFERENCE_IMAGE, CAPTURE_IMAGE)
        changed = score >= SCENE_CHANGE_THRESHOLD
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if changed:
            message = f"Porch activity detected at {stamp}. Scene-change score: {score:.1f}."
            print(message)
            print(f"Photo saved: {CAPTURE_IMAGE}")
            send_alert(message)
        else:
            print(
                f"Motion at {stamp}, but the porch scene change ({score:.1f}) is below "
                f"the alert threshold ({SCENE_CHANGE_THRESHOLD:.1f}). Photo saved: {CAPTURE_IMAGE}"
            )
    finally:
        if moved:
            print("Returning to standby view...")
            stepper.move(-STEPS_TO_PORCH)
        stepper.release()


def main() -> None:
    if not REFERENCE_IMAGE.is_file():
        raise FileNotFoundError(
            f"No empty-porch reference at {REFERENCE_IMAGE}. "
            "Capture one first with: python3 -m src.capture_reference"
        )

    camera = Picamera2()
    config = camera.create_video_configuration(
        main={"size": CAMERA_SIZE, "format": "RGB888"},
        controls={"FrameRate": CAMERA_FPS},
    )
    stepper = Stepper()
    camera.configure(config)
    camera.start()
    time.sleep(2)

    print("Porch Presence is watching for motion. Press Ctrl+C to stop.")
    print(f"Motor input BCM pins: {MOTOR_GPIO_PINS}; movement: {STEPS_TO_PORCH} half-steps.")
    previous = None
    consecutive = 0
    last_event = 0.0
    try:
        while True:
            frame = camera.capture_array("main")
            current = grayscale(frame)
            if previous is not None:
                fraction = motion_fraction(previous, current)
                if fraction >= MOTION_FRACTION_THRESHOLD:
                    consecutive += 1
                else:
                    consecutive = 0

                now = time.monotonic()
                if consecutive >= MOTION_CONFIRM_FRAMES and now - last_event >= EVENT_COOLDOWN_SECONDS:
                    last_event = now
                    consecutive = 0
                    handle_event(camera, stepper)
                    # Re-prime the reference frame after the camera returns.
                    previous = None
                    continue
            previous = current
            time.sleep(MOTION_FRAME_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping Porch Presence.")
    finally:
        stepper.close()
        camera.stop()
        camera.close()


if __name__ == "__main__":
    main()
