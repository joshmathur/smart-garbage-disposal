# =============================================================================
# src/microbit_controller.py — Micro:bit Serial Controller
# =============================================================================
# Sends open/close servo commands to the Micro:bit over USB serial.
# The Micro:bit runs microbit/main.py (MicroPython) which receives these
# commands and actuates the physical bin compartment servos.

import time
import serial
import logging
from typing import Optional
from config import (
    MICROBIT_PORT, BAUD_RATE,
    CMD_OPEN, CMD_CLOSE, CMD_PING,
    ACK_PREFIX, ERR_PREFIX,
    SERVO_OPEN_DURATION_MS
)

logger = logging.getLogger(__name__)

# Compartment → Micro:bit servo pin mapping
# Match these to the physical pins you wired servos to on the Micro:bit
COMPARTMENT_PINS = {
    "RECYCLABLE": 0,
    "COMPOST":    1,
    "LANDFILL":   2,
}


class MicrobitError(Exception):
    """Raised when Micro:bit communication fails."""
    pass


class MicrobitController:
    """
    Manages the serial connection to the Micro:bit and sends
    servo open/close commands.

    The serial protocol is newline-terminated ASCII:
        Host → Micro:bit:  "OPEN:RECYCLABLE\n"
        Micro:bit → Host:  "ACK:RECYCLABLE\n"  (on success)
                           "ERR:UNKNOWN_CATEGORY\n"  (on failure)

    Usage:
        ctrl = MicrobitController()
        ctrl.connect()
        ctrl.open_compartment("RECYCLABLE")
        ctrl.disconnect()
    """

    def __init__(self, port: str = MICROBIT_PORT, baud_rate: int = BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self._serial: Optional[serial.Serial] = None

    def connect(self) -> None:
        """Open the serial connection to the Micro:bit."""
        logger.info(f"Connecting to Micro:bit on {self.port}...")
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=2.0
            )
            time.sleep(2)  # Allow Micro:bit to reset after serial connect

            # Confirm it's alive
            if not self.ping():
                raise MicrobitError("Micro:bit did not respond to PING.")

            logger.info("Micro:bit connected and responding.")

        except serial.SerialException as e:
            raise MicrobitError(f"Could not open serial port {self.port}: {e}") from e

    def disconnect(self) -> None:
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        logger.info("Micro:bit disconnected.")

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def ping(self) -> bool:
        """Send a health-check ping. Returns True if Micro:bit ACKs."""
        response = self._send_command(CMD_PING)
        return response is not None and ACK_PREFIX in response

    def open_compartment(self, category: str) -> bool:
        """
        Command the Micro:bit to open the servo for a given waste category.

        The Micro:bit will hold the compartment open for SERVO_OPEN_DURATION_MS
        (configured in microbit/main.py), then close it automatically.

        Args:
            category: One of "RECYCLABLE", "COMPOST", "LANDFILL"

        Returns:
            True if the Micro:bit acknowledged the command.
        """
        if category not in COMPARTMENT_PINS:
            logger.error(f"Unknown category '{category}'. "
                         f"Valid options: {list(COMPARTMENT_PINS.keys())}")
            return False

        logger.info(f"Opening {category} compartment (pin {COMPARTMENT_PINS[category]})")
        response = self._send_command(f"{CMD_OPEN}:{category}")

        if response and ACK_PREFIX in response:
            logger.info(f"Micro:bit ACK'd open for {category}")
            return True
        else:
            logger.warning(f"Unexpected response from Micro:bit: {response!r}")
            return False

    def close_compartment(self, category: str) -> bool:
        """
        Explicitly command the Micro:bit to close a compartment.
        Normally the Micro:bit closes automatically after a timeout,
        but this can be used for manual override.
        """
        if category not in COMPARTMENT_PINS:
            return False
        response = self._send_command(f"{CMD_CLOSE}:{category}")
        return response is not None and ACK_PREFIX in response

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _send_command(self, command: str) -> Optional[str]:
        """
        Write a newline-terminated command and read one line back.

        Returns:
            The response string, or None on timeout/error.
        """
        if not self.is_connected():
            raise MicrobitError("Micro:bit is not connected. Call connect() first.")

        try:
            payload = (command + "\n").encode("utf-8")
            self._serial.write(payload)
            self._serial.flush()
            logger.debug(f"Sent: {command!r}")

            raw = self._serial.readline()
            response = raw.decode("utf-8").strip()
            logger.debug(f"Received: {response!r}")
            return response if response else None

        except serial.SerialTimeoutException:
            logger.warning(f"Timeout waiting for Micro:bit response to '{command}'")
            return None
        except Exception as e:
            logger.error(f"Serial communication error: {e}")
            return None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()


# =============================================================================
# Simulation stub — used when real hardware isn't available (demo / CI)
# =============================================================================

class MockMicrobitController:
    """
    Simulates Micro:bit responses for testing without hardware.
    Prints commands to console so you can verify the full pipeline.
    """

    def __init__(self, *_, **__):
        self._connected = False

    def connect(self):
        self._connected = True
        logger.info("[MOCK] Micro:bit connected (simulation mode).")

    def disconnect(self):
        self._connected = False

    def is_connected(self):
        return self._connected

    def ping(self):
        return True

    def open_compartment(self, category: str) -> bool:
        open_duration_s = SERVO_OPEN_DURATION_MS / 1000
        logger.info(f"[MOCK] >>> OPEN servo for {category} "
                    f"(would stay open {open_duration_s:.1f}s)")
        time.sleep(0.1)  # simulate brief serial round-trip
        return True

    def close_compartment(self, category: str) -> bool:
        logger.info(f"[MOCK] >>> CLOSE servo for {category}")
        return True

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
