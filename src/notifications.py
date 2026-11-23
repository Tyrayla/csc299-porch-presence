"""Console alerts plus optional Twilio SMS, enabled only when configured."""

from .settings import (
    ALERT_TO_NUMBER,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
)


def send_alert(message: str) -> None:
    """Print an alert and send SMS if all Twilio environment values are present."""
    print(f"ALERT: {message}")
    config = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, ALERT_TO_NUMBER)
    if not all(config):
        print("SMS is not configured; use the saved photo and this console alert for now.")
        return

    try:
        from twilio.rest import Client

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        sent = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=ALERT_TO_NUMBER,
        )
        print(f"SMS submitted to provider (message SID {sent.sid}).")
    except Exception as exc:
        # Don't stop camera monitoring because a network/SMS provider failed.
        print(f"SMS could not be sent ({exc}); the photo remains saved locally.")
