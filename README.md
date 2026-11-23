# CSC/CSE 299 Porch Presence

Camera-based porch activity demo for a Raspberry Pi 4B, Raspberry Pi Camera Rev 1.3, and 28BYJ-48 5V stepper motor with ULN2003 driver.

## What it does

1. Watches the forward-facing camera view for repeated frame-to-frame changes.
2. When motion is confirmed, moves the stepper a configured number of half-steps to point the camera toward the porch.
3. Captures a porch image and compares it with a saved empty-porch reference.
4. Prints an alert and saves the image when the scene-change score exceeds a threshold. If Twilio is configured, it also sends a text.
5. Moves the camera back to standby and continues watching.

This first version detects motion and image change. It does **not** identify a person or classify a package/food. Tree movement, lighting changes, and shadows can cause false detections; tune it in the intended location.

## Wiring used by the code

Use BCM GPIO numbering in software. These match the team's confirmed physical header pins:

| ULN2003 | Raspberry Pi header | BCM pin used in code |
| --- | ---: | ---: |
| IN1 | Physical 11 | GPIO17 |
| IN2 | Physical 12 | GPIO18 |
| IN3 | Physical 13 | GPIO27 |
| IN4 | Physical 15 | GPIO22 |
| `+` | Physical 2 (5V) | — |
| `−` | Physical 6 (GND) | — |

The camera uses the Pi's CSI camera ribbon connector. Do not power the motor through a GPIO signal pin. For a prototype, power down before changing wiring. If the Pi resets or becomes unstable, use a separate regulated 5V supply for the motor; join its ground to Pi ground.

**Mechanical constraint:** step count is open-loop; there is no position sensor or homing switch. The camera mount must start in the standby position and must not hit a hard stop. Ensure the camera ribbon has enough slack and never twists or snags as the mount moves. Test movement without the camera attached first. If the mechanism cannot move safely with the ribbon attached, use a fixed camera and remove the motor-driven camera movement from the demonstration.

## Install on Raspberry Pi OS

If the repo is already cloned on the Pi, update it first:

```bash
cd ~/csc299-porch-presence
git pull
```

If it is not cloned yet:

```bash
git clone https://github.com/Tyrayla/csc299-porch-presence.git
cd csc299-porch-presence
```

Then install the system packages:

```bash
sudo apt update
sudo apt install -y python3-opencv python3-gpiozero python3-picamera2
```

The Pi camera must already be detected by Raspberry Pi OS. Check it with:

```bash
rpicam-hello --list-cameras
```

## Capture the empty-porch reference

1. Mount the camera and motor safely. Start with the mechanism at the same standby position it will use while watching.
2. Make sure the porch is empty and lighting is representative.
3. Run:

```bash
python3 -m src.capture_reference
```

Confirm with `y`. The motor moves to the porch angle, saves `data/empty_porch.jpg`, then returns to standby. Inspect the reference photo before continuing.

## Run the system

From the repository root on the Pi:

```bash
python3 -m src.porch_watch
```

Stop with `Ctrl+C`. New event images are saved as `data/latest_capture.jpg` (each event overwrites the previous image). To save event history, change `CAPTURE_IMAGE` behavior in `src/porch_watch.py` to include a timestamp.

## Calibrate

The defaults are conservative starting values, not guaranteed settings. Change them for a temporary session by exporting variables before starting the program:

```bash
export STEPS_TO_PORCH=256
export MOTION_FRACTION_THRESHOLD=0.025
export SCENE_CHANGE_THRESHOLD=12.0
python3 -m src.porch_watch
```

- If motion is missed, lower `MOTION_FRACTION_THRESHOLD` slightly (for example, `0.015`).
- If it triggers from minor image noise, raise it (for example, `0.04`) or increase `MOTION_CONFIRM_FRAMES`.
- If normal lighting changes cause alerts, raise `SCENE_CHANGE_THRESHOLD`. If packages are missed in tests, lower it.
- Adjust `STEPS_TO_PORCH` in small increments. Do not guess a number that could drive the mount into a stop.
- Retake `data/empty_porch.jpg` if the camera angle or porch layout changes.

## Optional SMS

Console alerts work without an account. Optional text messages use Twilio's Python SDK. Twilio is a hosted service and may charge for phone numbers/messages; it is not an offline/open-source SMS network. Do not commit credentials.

Install the SDK in a virtual environment while allowing access to Raspberry Pi OS's apt-installed camera libraries:

```bash
sudo apt install -y python3-venv
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install twilio
```

Set provider credentials in the same terminal, then run the program:

```bash
export TWILIO_ACCOUNT_SID='your-account-sid'
export TWILIO_AUTH_TOKEN='your-auth-token'
export TWILIO_FROM_NUMBER='+15551234567'
export ALERT_TO_NUMBER='+15557654321'
python3 -m src.porch_watch
```

Replace the example phone numbers with numbers supported by your Twilio account. The program sends a text only when the scene-change threshold is reached. The image remains on the Pi; SMS does not attach it.

## Libraries and possible extensions

- **Picamera2/libcamera**: Raspberry Pi's supported camera interface, for camera frames and stills. [Raspberry Pi camera software docs](https://www.raspberrypi.com/documentation/accessories/camera-software.html)
- **OpenCV (`cv2`)**: resize, grayscale, blur, compare frames, and save images. Used here for simple motion and scene-change detection.
- **GPIO Zero**: control the four ULN2003 inputs from Python GPIO. The current program drives the 28BYJ-48 with a small half-step sequence.
- **Twilio Python SDK (optional)**: sends SMS through Twilio's hosted API. The SDK is open source; the messaging service itself is not free or self-hosted.
- **Object recognition (stretch goal)**: add an on-device TensorFlow Lite or OpenCV DNN object detector after the motion-and-photo pipeline works. A generic pretrained model may label people and some food classes, but generally does not provide a dependable “package” class. Reliable parcel recognition would need a suitable model and test images; treat it as optional.

## Privacy and credentials

- Aim the camera only at the test porch area and avoid capturing neighbors or public space.
- Do not commit captured images, API credentials, or phone numbers.
- The program currently stores one baseline and one latest event image locally.
