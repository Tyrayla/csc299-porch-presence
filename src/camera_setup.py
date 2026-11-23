"""Interactive shell menu for setting saved camera image orientation."""

import json

from .settings import CAMERA_SETTINGS_FILE, get_camera_rotation


def main() -> None:
    current = get_camera_rotation()
    print(f"Current saved image rotation: {current} degrees clockwise.")
    print("Choose 0, 90, 180, or 270 degrees clockwise; x cancels.")
    choice = input("Rotation: ").strip().lower()
    if choice == "x":
        print("Cancelled; camera rotation was not changed.")
        return
    try:
        rotation = int(choice)
    except ValueError:
        print("Enter one of: 0, 90, 180, 270, or x.")
        return
    if rotation not in (0, 90, 180, 270):
        print("Enter one of: 0, 90, 180, 270, or x.")
        return

    settings = {}
    if CAMERA_SETTINGS_FILE.is_file():
        settings = json.loads(CAMERA_SETTINGS_FILE.read_text(encoding="utf-8"))
    settings["rotation_degrees"] = rotation
    CAMERA_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CAMERA_SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Saved image rotation: {rotation} degrees clockwise.")
    print("Recapture the empty-porch reference before monitoring with this rotation.")


if __name__ == "__main__":
    main()
