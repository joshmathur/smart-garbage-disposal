# =============================================================================
# microbit/main.py — MicroPython firmware for the Micro:bit
# Smart Garbage Disposal System, York University k2i STEM Challenge 2024
# =============================================================================
# Flash this onto the Micro:bit using the Micro:bit Python Editor or mu-editor.
# https://python.microbit.org/
#
# What this does:
#   - Listens on USB serial for commands from the host Python backend
#   - On "OPEN:<CATEGORY>", sweeps the corresponding servo to open position
#   - Holds it open for OPEN_DURATION_MS, then sweeps back to closed
#   - Replies "ACK:<CATEGORY>" on success, "ERR:<reason>" on failure
#   - Scrolls an icon on the LED matrix so you can see it's working
#
# Wiring:
#   Servo signal wires → Micro:bit edge connector pins:
#     Pin 0 → RECYCLABLE compartment servo
#     Pin 1 → COMPOST compartment servo
#     Pin 2 → LANDFILL compartment servo
#   Servo power (red) → 3.3V or external 5V supply
#   Servo ground      → GND

from microbit import *
import utime

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

OPEN_DURATION_MS = 3000   # ms to hold compartment open
SERVO_OPEN_DEG   = 90     # degrees: fully open position
SERVO_CLOSE_DEG  = 0      # degrees: fully closed position

# Map category name → Micro:bit pin object
CATEGORY_PINS = {
    "RECYCLABLE": pin0,
    "COMPOST":    pin1,
    "LANDFILL":   pin2,
}

# LED icons shown on the Micro:bit display for each category
ICONS = {
    "RECYCLABLE": Image.YES,       # ✓ recycling confirmed
    "COMPOST":    Image.HAPPY,     # 😊 organic waste
    "LANDFILL":   Image.SAD,       # 😟 landfill (encourage better sorting!)
    "IDLE":       Image.DIAMOND,
    "ERROR":      Image.NO,
}

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def set_servo(pin, degrees):
    """
    Write a servo angle using PWM.
    Micro:bit's write_analog maps 0-1023 to 0-3.3V.
    Standard servo pulse: 1ms (0°) → 2ms (180°) at ~50Hz (20ms period).
    Duty cycle = pulse_ms / 20ms * 1023
    """
    pulse_ms = 1.0 + (degrees / 180.0) * 1.0   # 1ms at 0°, 2ms at 180°
    duty = int((pulse_ms / 20.0) * 1023)
    pin.set_analog_period(20)        # 50Hz PWM
    pin.write_analog(duty)


def open_compartment(category):
    """Sweep servo open, show icon, wait, then close."""
    pin = CATEGORY_PINS.get(category)
    if pin is None:
        return False

    display.show(ICONS.get(category, ICONS["IDLE"]))
    set_servo(pin, SERVO_OPEN_DEG)
    utime.sleep_ms(OPEN_DURATION_MS)
    set_servo(pin, SERVO_CLOSE_DEG)
    utime.sleep_ms(300)        # let servo settle
    pin.write_digital(0)       # cut PWM signal to stop servo jitter
    display.show(ICONS["IDLE"])
    return True


def close_compartment(category):
    """Force-close a specific compartment."""
    pin = CATEGORY_PINS.get(category)
    if pin is None:
        return False
    set_servo(pin, SERVO_CLOSE_DEG)
    utime.sleep_ms(300)
    pin.write_digital(0)
    return True


def parse_command(line):
    """
    Parse a serial command string.

    Expected formats:
        "OPEN:RECYCLABLE"
        "CLOSE:COMPOST"
        "PING"

    Returns (command, argument) tuple. argument is None for PING.
    """
    line = line.strip().upper()
    if ":" in line:
        cmd, arg = line.split(":", 1)
        return cmd.strip(), arg.strip()
    return line, None


# -----------------------------------------------------------------------------
# Boot sequence
# -----------------------------------------------------------------------------

display.show(Image.ARROW_N)   # indicate startup
uart.init(baudrate=115200)    # match host baud rate
utime.sleep_ms(500)
display.show(ICONS["IDLE"])

# All servos to closed position on boot
for cat, pin in CATEGORY_PINS.items():
    set_servo(pin, SERVO_CLOSE_DEG)
    utime.sleep_ms(200)
    pin.write_digital(0)

# -----------------------------------------------------------------------------
# Main loop — serial command listener
# -----------------------------------------------------------------------------

while True:
    if uart.any():
        try:
            raw = uart.readline()
            if raw is None:
                continue

            line = raw.decode("utf-8").strip()
            if not line:
                continue

            cmd, arg = parse_command(line)

            if cmd == "PING":
                uart.write("ACK:PING\n")
                display.show(Image.HAPPY)
                utime.sleep_ms(200)
                display.show(ICONS["IDLE"])

            elif cmd == "OPEN":
                if arg in CATEGORY_PINS:
                    uart.write(f"ACK:{arg}\n")
                    open_compartment(arg)
                else:
                    uart.write(f"ERR:UNKNOWN_CATEGORY:{arg}\n")
                    display.show(ICONS["ERROR"])
                    utime.sleep_ms(500)
                    display.show(ICONS["IDLE"])

            elif cmd == "CLOSE":
                if arg in CATEGORY_PINS:
                    close_compartment(arg)
                    uart.write(f"ACK:CLOSED:{arg}\n")
                else:
                    uart.write(f"ERR:UNKNOWN_CATEGORY:{arg}\n")

            else:
                uart.write(f"ERR:UNKNOWN_COMMAND:{cmd}\n")

        except Exception as e:
            uart.write(f"ERR:EXCEPTION:{str(e)}\n")
            display.show(ICONS["ERROR"])
            utime.sleep_ms(500)
            display.show(ICONS["IDLE"])

    utime.sleep_ms(10)   # yield briefly to avoid busy-spinning
