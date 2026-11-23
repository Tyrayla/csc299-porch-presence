"""Interactive shell calibration for the camera's standby and porch angles."""

from .settings import CALIBRATION_FILE
from .stepper import Stepper, load_calibration, save_calibration


MAX_JOG_STEPS = 1024


HELP = """\
Commands:
  j N   jog N half-steps (examples: j 16, j -16); max magnitude 1024
  s     set the current camera angle as standby / logical zero
  p     save the current position as the porch view relative to standby
  b     move to standby (available after you set standby in this session)
  v     move to the saved porch view (after standby and porch are set)
  d     display current position and saved porch travel
  h     show this help
  q     quit and release the motor coils

The motor has no position sensor. At each new session, jog to the physical
standby angle and press s before using v or running the detector.
"""


def main() -> None:
    saved = load_calibration()
    stepper = Stepper()
    standby_set = False
    porch_steps = saved.get("porch_steps")

    print(f"Stepper angle setup (saving to {CALIBRATION_FILE})")
    print(HELP)
    print("The first jog starts from an unknown physical angle; use small steps.")
    try:
        while True:
            command = input("stepper> ").strip().lower()
            if not command:
                continue
            parts = command.split()
            action = parts[0]

            if action in {"q", "quit", "exit"}:
                break
            if action in {"h", "help", "?"}:
                print(HELP)
            elif action in {"j", "jog"}:
                if len(parts) != 2:
                    print("Usage: j 16   or   j -16")
                    continue
                try:
                    amount = int(parts[1])
                except ValueError:
                    print("Enter an integer step count, such as j 16 or j -16.")
                    continue
                if amount == 0 or abs(amount) > MAX_JOG_STEPS:
                    print(f"Choose a nonzero jog from -{MAX_JOG_STEPS} to {MAX_JOG_STEPS}.")
                    continue
                stepper.move(amount)
                print(f"Jogged {amount} half-steps; session position is {stepper.position_steps}.")
            elif action in {"s", "standby"}:
                stepper.position_steps = 0
                standby_set = True
                print("Current angle marked as standby (logical step 0 for this session).")
                if porch_steps is not None:
                    print(f"Saved porch travel remains {porch_steps} half-steps from standby.")
                    print("If you changed the standby angle, jog to the new porch view and press p to update it.")
            elif action in {"p", "porch"}:
                if not standby_set:
                    print("First jog to the standby angle and press s.")
                    continue
                if stepper.position_steps == 0:
                    print("Porch view cannot be the same as standby; jog to the porch angle first.")
                    continue
                porch_steps = stepper.position_steps
                saved["porch_steps"] = porch_steps
                save_calibration(saved)
                print(f"Saved porch view at {porch_steps} half-steps from standby.")
            elif action in {"b", "base", "standby_move"}:
                if not standby_set:
                    print("Jog to the standby angle and press s first.")
                    continue
                stepper.move(-stepper.position_steps)
                print("Moved to standby.")
            elif action in {"v", "view", "porch_move"}:
                if not standby_set:
                    print("Jog to the standby angle and press s first.")
                elif porch_steps is None:
                    print("No porch angle is saved yet; jog to porch view and press p.")
                else:
                    stepper.move(porch_steps - stepper.position_steps)
                    print("Moved to the saved porch view.")
            elif action in {"d", "status"}:
                print(f"Session position: {stepper.position_steps} half-steps")
                print(f"Standby marked this session: {'yes' if standby_set else 'no'}")
                print(f"Saved porch travel: {porch_steps if porch_steps is not None else 'not set'}")
            else:
                print("Unknown command. Enter h for help.")
    except KeyboardInterrupt:
        print("\nInterrupted; releasing motor coils.")
    finally:
        stepper.close()
    print("Stepper setup ended. The saved calibration file is local and git-ignored.")


if __name__ == "__main__":
    main()
