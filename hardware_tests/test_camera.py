"""Capture one test image from the Raspberry Pi Camera Module."""

from pathlib import Path
from time import sleep

from picamera2 import Picamera2


def main() -> None:
    output_path = Path("data/camera_test.jpg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    camera = Picamera2()
    camera.configure(camera.create_still_configuration())
    camera.start()
    try:
        sleep(2)
        camera.capture_file(str(output_path))
        print(f"Camera capture saved to: {output_path.resolve()}")
    finally:
        camera.stop()


if __name__ == "__main__":
    main()
