"""PIR-triggered porch capture and simple scene-change detection."""

from pathlib import Path
from time import sleep

import cv2
from gpiozero import MotionSensor, Servo
from picamera2 import Picamera2

from .notifications import send_alert
from .settings import (
    CAMERA_SETTLE_SECONDS,
    CAPTURE_IMAGE,
    DIFF_THRESHOLD,
    PIR_GPIO,
    REFERENCE_IMAGE,
    SERVO_GPIO,
    SERVO_IDLE_VALUE,
    SERVO_VIEW_VALUE,
)


def difference_score(reference_path: str, capture_path: str) -> float:
    """Return mean absolute grayscale pixel difference between two images."""
    reference = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    capture = cv2.imread(capture_path, cv2.IMREAD_GRAYSCALE)
    if reference is None:
        raise FileNotFoundError(f"Reference image not found or unreadable: {reference_path}")
    if capture is None:
        raise FileNotFoundError(f"Capture image not found or unreadable: {capture_path}")
    if capture.shape != reference.shape:
        capture = cv2.resize(capture, (reference.shape[1], reference.shape[0]))
    difference = cv2.absdiff(reference, capture)
    return float(difference.mean())


def main() -> None:
    reference_path = Path(REFERENCE_IMAGE)
    if not reference_path.is_file():
        raise FileNotFoundError(
            f"Create the empty-scene reference first with `python3 -m src.capture_reference`: {reference_path}"
        )

    capture_path = Path(CAPTURE_IMAGE)
    capture_path.parent.mkdir(parents=True, exist_ok=True)

    pir = MotionSensor(PIR_GPIO)
    servo = Servo(SERVO_GPIO)
    camera = Picamera2()
    camera.configure(camera.create_still_configuration())
    camera.start()

    print("Porch detector is running. Press Ctrl+C to stop.")
    try:
        servo.value = SERVO_IDLE_VALUE
        while True:
            pir.wait_for_motion()
            print("Motion detected; moving camera and capturing scene.")
            servo.value = SERVO_VIEW_VALUE
            sleep(CAMERA_SETTLE_SECONDS)
            camera.capture_file(str(capture_path))
            score = difference_score(str(reference_path), str(capture_path))
            print(f"Image difference score: {score:.2f}")

            if score >= DIFF_THRESHOLD:
                send_alert(
                    f"Porch scene change detected (difference score {score:.2f}).",
                    image_path=str(capture_path),
                )
            else:
                print("No scene change above the configured threshold.")

            servo.value = SERVO_IDLE_VALUE
            pir.wait_for_no_motion()
    except KeyboardInterrupt:
        print("Stopping porch detector.")
    finally:
        camera.stop()
        servo.close()
        pir.close()


if __name__ == "__main__":
    main()
