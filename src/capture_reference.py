"""Capture the baseline photo while the camera points at the empty porch."""

import time

import cv2
from picamera2 import Picamera2

from .settings import CAMERA_SETTLE_SECONDS, CAMERA_SIZE, REFERENCE_IMAGE, get_steps_to_porch
from .stepper import Stepper


def main() -> None:
    print("Make sure the porch is empty and the camera mount starts at standby position.")
    answer = input("Move the camera to porch view and capture the empty-scene reference? [y/N] ")
    if answer.strip().lower() != "y":
        print("Cancelled.")
        return

    steps_to_porch = get_steps_to_porch()
    camera = Picamera2()
    camera.configure(camera.create_still_configuration(main={"size": CAMERA_SIZE, "format": "RGB888"}))
    stepper = Stepper()
    camera.start()
    time.sleep(2)
    moved = False
    try:
        stepper.move(steps_to_porch)
        moved = True
        time.sleep(CAMERA_SETTLE_SECONDS)
        frame = camera.capture_array()
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        REFERENCE_IMAGE.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(REFERENCE_IMAGE), bgr):
            raise OSError(f"Could not save reference image: {REFERENCE_IMAGE}")
        print(f"Saved empty-porch reference: {REFERENCE_IMAGE}")
    finally:
        if moved:
            stepper.move(-steps_to_porch)
        stepper.close()
        camera.stop()
        camera.close()


if __name__ == "__main__":
    main()
