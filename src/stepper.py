"""28BYJ-48 half-step control and saved angle calibration."""

import json
import time

from gpiozero import OutputDevice

from .settings import CALIBRATION_FILE, MOTOR_GPIO_PINS, STEP_DELAY_SECONDS


HALF_STEP_SEQUENCE = (
    (1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0),
    (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1), (1, 0, 0, 1),
)


def load_calibration() -> dict:
    if not CALIBRATION_FILE.exists():
        return {}
    try:
        data = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("calibration file must contain a JSON object")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Could not read stepper calibration {CALIBRATION_FILE}: {exc}") from exc


def save_calibration(data: dict) -> None:
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class Stepper:
    """Small half-step controller for a 28BYJ-48 driven by a ULN2003."""

    def __init__(self) -> None:
        self.coils = [OutputDevice(pin, initial_value=False) for pin in MOTOR_GPIO_PINS]
        self.index = 0
        # Logical coordinate only; it resets when the script starts. The motor
        # has no encoder, so this is not a measurement of its physical angle.
        self.position_steps = 0

    def _apply(self) -> None:
        for coil, value in zip(self.coils, HALF_STEP_SEQUENCE[self.index]):
            coil.value = bool(value)

    def move(self, steps: int) -> None:
        direction = 1 if steps >= 0 else -1
        try:
            for _ in range(abs(steps)):
                self.index = (self.index + direction) % len(HALF_STEP_SEQUENCE)
                self._apply()
                self.position_steps += direction
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
