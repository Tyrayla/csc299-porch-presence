# CSC/CSE 299 Porch Presence Project

Starter code and notes for a Raspberry Pi porch activity detector. The planned system uses a PIR sensor to trigger a camera, compares the captured scene with an empty-porch reference, and sends a text alert if the scene changes. Optional package or food classification is a later stretch goal.

This repository is a project scaffold. Hardware setup, camera compatibility, GPIO pins, servo angles, and the SMS provider still need to be confirmed on the team's Raspberry Pi. The starter currently prints a local alert; it does not send SMS yet.

## Planned flow

1. A PIR sensor reports movement.
2. A servo moves the camera to the porch viewing angle.
3. The Raspberry Pi captures an image and compares it with a reference image.
4. If the image difference passes a configurable threshold, the program reports an alert locally.
5. After the team confirms the SMS provider and stores its credentials locally, the notification function can be connected to that service.

The project detects motion and scene changes. Image comparison alone does not identify people or determine that an object is a package or food.

## Requirements

- Raspberry Pi with Raspberry Pi OS
- Raspberry Pi Camera Module compatible with the OS camera stack
- PIR sensor and servo motor
- Breadboard, jumper wires, and appropriate power/wiring for the servo
- Network access if SMS notifications are added

Install the Raspberry Pi OS packages on the Pi:

```bash
sudo apt update
sudo apt install -y python3-opencv python3-gpiozero python3-picamera2
```

Package availability can vary with the Raspberry Pi OS release. Confirm the camera module and OS combination before wiring and running the program.

## Clone and update on the Pi

Clone this repository once:

```bash
git clone https://github.com/Tyrayla/csc299-porch-presence.git
cd csc299-porch-presence
```

After pushing changes from the development computer, update the Pi with:

```bash
git pull
```

## Configure the hardware

Set these environment variables in the Pi's shell before running the scripts. Replace each placeholder with the BCM pin and angle values confirmed by the team; do not commit real credentials or `.env` files.

```bash
export PIR_GPIO='<BCM pin>'
export SERVO_GPIO='<BCM pin>'
export SERVO_IDLE_VALUE='<servo value from 0.0 to 1.0>'
export SERVO_VIEW_VALUE='<servo value from 0.0 to 1.0>'
```

Servo positions, wiring, and power requirements depend on the actual motor and mount. Test movement without the camera attached first.

## Capture a reference and run

With the camera mounted in its final position and the porch empty, capture a reference image:

```bash
python3 -m src.capture_reference
```

Then start the detector:

```bash
python3 -m src.porch_watch
```

The default image-difference threshold is only a starting point. Tune it under the lighting and camera position used for the demonstration. The current notification function prints an alert locally; SMS integration is intentionally pending confirmation of the service/API.

## Project structure

- `src/porch_watch.py` - PIR-triggered camera capture and scene comparison
- `src/capture_reference.py` - captures the empty-scene reference image
- `src/settings.py` - reads GPIO and servo settings from environment variables
- `src/notifications.py` - local alert placeholder for later SMS integration

## Safety and privacy notes

- Do not commit API keys, phone numbers, passwords, or porch images.
- Keep the camera pointed only at the intended test area.
- Check servo power and wiring before attaching the camera mount.
- If scene comparison is unreliable, the fallback is a general PIR-triggered alert.
