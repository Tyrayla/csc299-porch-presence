"""Camera motion detector that tilts to the porch, captures, and alerts.

This detects visible motion and change from a reference photo. It does not
identify a person, package, or food item.
"""

from datetime import datetime
from pathlib import Path
import argparse
import time

import cv2
from picamera2 import Picamera2

from .notifications import send_alert
from .settings import (
    CAMERA_FPS,
    CAMERA_SETTLE_SECONDS,
    CAMERA_SIZE,
    CAPTURE_DIR,
    EVENT_COOLDOWN_SECONDS,
    MAX_SAVED_CAPTURES,
    MOTION_CONFIRM_FRAMES,
    MOTION_FRACTION_THRESHOLD,
    MOTION_FRAME_INTERVAL,
    MOTION_PIXEL_THRESHOLD,
    REFERENCE_IMAGE,
    SCENE_CHANGE_THRESHOLD,
    get_steps_to_porch,
)
from .stepper import Stepper


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


def prune_capture_history() -> None:
    """Keep only the newest configured number of event photos."""
    if MAX_SAVED_CAPTURES < 1:
        return
    photos = list(CAPTURE_DIR.glob("porch_*.jpg")) + list(CAPTURE_DIR.glob("capture_*.jpg"))
    photos.sort(key=lambda photo: photo.stat().st_mtime)
    for old_photo in photos[:-MAX_SAVED_CAPTURES]:
        try:
            old_photo.unlink()
        except OSError as exc:
            print(f"Could not remove old capture {old_photo}: {exc}")


def next_capture_path() -> Path:
    """Build a short, human-readable timestamped photo filename."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    candidate = CAPTURE_DIR / f"porch_{stamp}.jpg"
    suffix = 2
    while candidate.exists():
        candidate = CAPTURE_DIR / f"porch_{stamp}_{suffix}.jpg"
        suffix += 1
    return candidate


def handle_event(camera: Picamera2, stepper: Stepper, steps_to_porch: int) -> None:
    print("Motion confirmed. Moving to porch view...")
    moved = False
    try:
        stepper.move(steps_to_porch)
        moved = True
        time.sleep(CAMERA_SETTLE_SECONDS)
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        capture_path = next_capture_path()
        print(f"Capturing porch photo: {capture_path.name}", flush=True)
        capture_jpeg(camera, capture_path)
        print(f"Photo saved: {capture_path}", flush=True)
        prune_capture_history()

        score = scene_difference(REFERENCE_IMAGE, capture_path)
        changed = score >= SCENE_CHANGE_THRESHOLD
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if changed:
            message = f"Porch activity detected at {stamp}. Scene-change score: {score:.1f}."
            print(message)
            print(f"Photo saved: {capture_path}")
            send_alert(message)
        else:
            print(
                f"Motion at {stamp}, but the porch scene change ({score:.1f}) is below "
                f"the alert threshold ({SCENE_CHANGE_THRESHOLD:.1f}). Photo saved: {capture_path}"
            )
    finally:
        if moved:
            print("Returning to standby view...")
            stepper.move(-steps_to_porch)
        stepper.release()


def run_detector() -> None:
    steps_to_porch = get_steps_to_porch()
    if not REFERENCE_IMAGE.is_file():
        raise FileNotFoundError(
            f"No empty-porch reference at {REFERENCE_IMAGE}. "
            "Capture one first with: python3 -m src.capture_reference"
        )
    input("Check that the camera is physically at standby, then press Enter to start (Ctrl+C to cancel): ")

    camera = Picamera2()
    config = camera.create_video_configuration(
        main={"size": CAMERA_SIZE, "format": "RGB888"},
        controls={"FrameRate": CAMERA_FPS},
    )
    stepper = Stepper()
    camera.configure(config)
    camera.start()
    time.sleep(2)

    print(f"Porch Presence is watching; saved porch travel is {steps_to_porch} half-steps. Press Ctrl+C to stop.")
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
                    handle_event(camera, stepper, steps_to_porch)
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Porch Presence: stepper setup, reference capture, and motion monitoring"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--setup", action="store_true", help="open stepper angle setup")
    modes.add_argument("--reference", action="store_true", help="capture an empty-porch reference")
    modes.add_argument("--run", action="store_true", help="start motion monitoring directly")
    args = parser.parse_args()

    if args.setup:
        from .stepper_setup import main as setup_stepper

        setup_stepper()
        return
    if args.reference:
        from .capture_reference import main as capture_reference

        capture_reference()
        return
    if args.run:
        run_detector()
        return

    # Single interactive entry point for the full project workflow.
    while True:
        print("\nPorch Presence")
        print("1) Calibrate / jog the stepper")
        print("2) Capture empty-porch reference photo")
        print("3) Start motion monitoring")
        print("4) Quit")
        choice = input("Choose 1-4: ").strip()
        if choice == "1":
            from .stepper_setup import main as setup_stepper

            setup_stepper()
        elif choice == "2":
            from .capture_reference import main as capture_reference

            capture_reference()
        elif choice == "3":
            try:
                run_detector()
            except (FileNotFoundError, RuntimeError) as exc:
                print(f"Cannot start monitoring yet: {exc}")
        elif choice == "4":
            print("Goodbye.")
            break
        else:
            print("Enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
