"""Capture the empty-scene reference image using the Raspberry Pi camera."""

from pathlib import Path

from picamera2 import Picamera2
from gpiozero import Servo

from .settings import REFERENCE_IMAGE, SERVO_GPIO, SERVO_VIEW_VALUE


def main() -> None:
    servo = Servo(SERVO_GPIO)
    camera = Picamera2()
    camera.configure(camera.create_still_configuration())
    camera.start()
    try:
        servo.value = SERVO_VIEW_VALUE
        input("Point the camera at the empty porch, wait for the view to settle, then press Enter...")
        path = Path(REFERENCE_IMAGE)
        path.parent.mkdir(parents=True, exist_ok=True)
        camera.capture_file(str(path))
        print(f"Saved reference image to {path}")
    finally:
        camera.stop()
        servo.close()


if __name__ == "__main__":
    main()
