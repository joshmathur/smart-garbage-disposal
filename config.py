# =============================================================================
# config.py — Smart Garbage Disposal System
# York University k2i STEM Challenge, 2024
# =============================================================================
# Central configuration for hardware ports, timing, and classification IDs.
# Edit these values to match your physical setup before running.

# --- Serial Ports ---
# On Windows, use "COM3", "COM4", etc. On Linux/Mac, use "/dev/ttyUSB0" etc.
MICROBIT_PORT = "/dev/ttyUSB0"     # USB serial port for Micro:bit
HUSKY_LENS_PORT = "/dev/ttyUSB1"   # Serial port for HuskyLens (if using UART mode)
BAUD_RATE = 115200

# --- HuskyLens Connection Mode ---
# "UART" — HuskyLens connected directly to host machine via USB/serial
# "I2C"  — HuskyLens connected to a Raspberry Pi via GPIO I2C pins
HUSKY_MODE = "UART"
HUSKY_I2C_ADDRESS = 0x32  # Default HuskyLens I2C address

# --- HuskyLens Class ID → Waste Category Mapping ---
# These IDs correspond to the order you trained objects in HuskyLens.
# Class 1 = first thing you trained, Class 2 = second, etc.
WASTE_CLASS_MAP = {
    1: "RECYCLABLE",  # Plastics, metals, glass, paper
    2: "COMPOST",     # Food scraps, organics
    3: "LANDFILL",    # General/non-sortable waste
}

# --- Servo Timing (milliseconds) ---
SERVO_OPEN_DURATION_MS = 3000   # How long a compartment stays open
SERVO_CLOSE_DELAY_MS = 500      # Delay before closing after object detected

# --- Serial Command Protocol ---
# Commands sent from host Python → Micro:bit
CMD_OPEN   = "OPEN"    # e.g. "OPEN:RECYCLABLE\n"
CMD_CLOSE  = "CLOSE"   # e.g. "CLOSE:RECYCLABLE\n"
CMD_PING   = "PING"    # Health check
# Responses received from Micro:bit → host Python
ACK_PREFIX = "ACK"     # e.g. "ACK:RECYCLABLE\n"
ERR_PREFIX = "ERR"

# --- Detection Confidence ---
# Minimum number of consecutive frames before triggering bin open.
# Helps avoid false positives from a single noisy frame.
DETECTION_THRESHOLD_FRAMES = 3
