"""Notification adapter. SMS integration is pending provider confirmation."""


def send_alert(message: str, image_path: str | None = None) -> None:
    """Print a local alert until an SMS provider/API is selected and configured."""
    print(f"ALERT: {message}")
    if image_path:
        print(f"Captured image saved locally at: {image_path}")
    # TODO: connect the SMS provider after confirming which service the team used.
    # Load credentials from local environment variables; never commit them.
