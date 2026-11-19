"""Briefly step a 28BYJ-48 motor through a ULN2003 driver board."""

from time import sleep

from gpiozero import OutputDevice

# BCM GPIO numbers. Match IN1, IN2, IN3, IN4 to this order on the driver board.
PINS = (17, 18, 27, 22)
STEP_DELAY_SECONDS = 0.004
TEST_STEPS = 256

# Eight-step half-step sequence for the four motor phases.
HALF_STEP_SEQUENCE = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)


def main() -> None:
    coils = [OutputDevice(pin, initial_value=False) for pin in PINS]
    step_index = 0

    def apply_step(index: int) -> None:
        for coil, state in zip(coils, HALF_STEP_SEQUENCE[index]):
            coil.value = bool(state)

    try:
        print("Stepping forward, then back. Keep the motor unloaded for this test.")
        apply_step(step_index)
        for direction in (1, -1):
            for _ in range(TEST_STEPS):
                step_index = (step_index + direction) % len(HALF_STEP_SEQUENCE)
                apply_step(step_index)
                sleep(STEP_DELAY_SECONDS)
            sleep(0.5)
        print("Motor test finished.")
    except KeyboardInterrupt:
        print("Motor test interrupted.")
    finally:
        for coil in coils:
            coil.off()
            coil.close()


if __name__ == "__main__":
    main()
