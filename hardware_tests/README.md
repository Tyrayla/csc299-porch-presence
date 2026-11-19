# Raspberry Pi 4 component check guide

These checks are for the camera and 28BYJ-48 stepper motor identified by the team. Test them separately before attaching the camera to the motor mount. The camera test saves one photo. The motor test rotates a short distance forward and back without a camera attached.

## Parts needed for these checks

- Raspberry Pi 4 Model B and power supply
- Raspberry Pi Camera Rev 1.3 and its 15-pin ribbon cable
- 28BYJ-48 5V stepper motor
- ULN2003-compatible stepper driver board (not visible in the team's motor photo; check the kit or Lab 8 materials)
- Jumper wires
- Regulated 5V source for the motor/driver, as specified by the driver board and lab instructions

The camera connects directly to the Pi CSI camera port, not the breadboard. The motor's five-wire plug connects to the matching socket on the stepper driver board, not directly to the Pi or breadboard.

## Camera connection

1. Shut down the Pi and unplug its power.
2. On a Pi 4, find the 15-pin port marked `CAMERA`, between the micro-HDMI ports and the audio jack.
3. Open the connector latch, insert the ribbon evenly, and close the latch. On the Pi connector, the metal contacts face away from the latch. The ribbon should be straight and not sharply bent.
4. Reconnect power. Run the test from the repository root:

   ```bash
   python3 hardware_tests/test_camera.py
   ```

5. Open `data/camera_test.jpg` on the Pi to confirm the photo is clear.

Raspberry Pi's camera instructions say to disconnect power before installing the ribbon. Use its camera-specific instructions for both connector ends if the ribbon has been detached from the camera board.

## 28BYJ-48 and ULN2003 wiring

**Use a ULN2003 driver board. Do not wire the motor coils directly to Pi GPIO.** The Pi's GPIO signals are 3.3V and are not 5V tolerant. The motor is rated 5V; follow the driver board and Lab 8 instructions for its motor supply.

With the Pi unplugged:

1. Plug the motor's white five-wire connector into the matching socket on the ULN2003 board. It fits in one orientation; do not force it.
2. Connect the four ULN2003 logic inputs to the Pi GPIO pins below. The Python test uses BCM numbering; physical header positions are listed for locating them.
3. Connect the driver's `GND` to Pi ground. Connect the driver's motor `VCC`/`+` to a regulated 5V supply approved for the driver/motor. If using a separate supply, connect its ground to both the driver GND and Pi GND so the control signals share a reference.
4. Double-check the driver board's labels and power connections before powering the Pi.

| Driver input | Pi BCM GPIO | Pi physical pin |
| --- | ---: | ---: |
| IN1 | 17 | 11 |
| IN2 | 18 | 12 |
| IN3 | 27 | 13 |
| IN4 | 22 | 15 |
| GND | GND | 6 |

Do not connect the motor supply's 5V to any Pi GPIO pin. Do not power the motor through a breadboard rail unless the instructor confirms that the rail and supply are suitable. The driver board is the interface between the GPIO signals and motor coils.

Run from the repository root:

```bash
python3 hardware_tests/test_stepper_28byj48.py
```

The shaft should turn a small amount and return approximately. Stepper motors do not report their actual position, so missed steps or power loss can make the return imperfect. Do not attach the camera until the motor test runs smoothly and the mount is stable.

## Install required packages if needed

On Raspberry Pi OS, the packages are normally available through apt:

```bash
sudo apt update
sudo apt install -y python3-gpiozero python3-picamera2
```

The camera software may already be installed. If a module is missing, check the Raspberry Pi OS version and course setup instructions before installing through another method.
