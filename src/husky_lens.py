# =============================================================================
# src/husky_lens.py — HuskyLens AI Camera Interface
# =============================================================================
# Wraps the huskylensPythonLibrary to provide clean classification reads.
# Supports both UART (serial) and I2C connection modes.

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HuskyLensError(Exception):
    """Raised when HuskyLens communication fails."""
    pass


class HuskyLensReader:
    """
    Interface for reading object classification results from HuskyLens.

    HuskyLens must be pre-trained in 'Object Classification' mode before use.
    Each trained category is assigned a class ID (1, 2, 3...) which maps to
    waste categories defined in config.py.

    Usage:
        reader = HuskyLensReader(mode="UART", port="/dev/ttyUSB1")
        reader.connect()
        result = reader.get_detected_class()  # returns int ID or None
        reader.disconnect()
    """

    def __init__(self, mode: str = "UART", port: str = "/dev/ttyUSB1",
                 baud_rate: int = 115200, i2c_address: int = 0x32):
        """
        Args:
            mode:        "UART" or "I2C"
            port:        Serial port (UART mode only), e.g. "/dev/ttyUSB1"
            baud_rate:   Baud rate for UART connection
            i2c_address: I2C address (I2C mode only), default 0x32
        """
        self.mode = mode.upper()
        self.port = port
        self.baud_rate = baud_rate
        self.i2c_address = i2c_address
        self._hl = None  # huskylensPythonLibrary instance
        self._connected = False

    def connect(self) -> None:
        """Establish connection to HuskyLens. Raises HuskyLensError on failure."""
        try:
            from huskylensPythonLibrary import HuskyLensLibrary  # type: ignore
        except ImportError:
            raise HuskyLensError(
                "huskylensPythonLibrary not installed. "
                "Run: pip install huskylensPythonLibrary"
            )

        logger.info(f"Connecting to HuskyLens via {self.mode}...")

        try:
            if self.mode == "UART":
                self._hl = HuskyLensLibrary("SERIAL", self.port, self.baud_rate)
            elif self.mode == "I2C":
                self._hl = HuskyLensLibrary("I2C", address=self.i2c_address)
            else:
                raise HuskyLensError(f"Unknown mode '{self.mode}'. Use 'UART' or 'I2C'.")

            # Knock knock — confirm the device responds
            if not self._hl.knock():
                raise HuskyLensError("HuskyLens did not respond to knock. Check connection.")

            self._connected = True
            logger.info("HuskyLens connected successfully.")

        except Exception as e:
            raise HuskyLensError(f"Failed to connect to HuskyLens: {e}") from e

    def disconnect(self) -> None:
        """Clean up the HuskyLens connection."""
        self._connected = False
        self._hl = None
        logger.info("HuskyLens disconnected.")

    def is_connected(self) -> bool:
        return self._connected

    def get_detected_class(self) -> Optional[int]:
        """
        Poll HuskyLens for the currently detected object class.

        Returns:
            int: The class ID (1-based) of the highest-confidence detection.
            None: If no object is detected in the current frame.

        Raises:
            HuskyLensError: If the device is not connected or read fails.
        """
        if not self._connected or self._hl is None:
            raise HuskyLensError("HuskyLens is not connected. Call connect() first.")

        try:
            blocks = self._hl.blocks()

            if not blocks:
                return None

            # If multiple objects detected, take the one with the largest bounding box
            # (proxy for closest/most prominent object in frame)
            best = max(blocks, key=lambda b: b.width * b.height)
            class_id = best.ID

            logger.debug(f"HuskyLens detected class {class_id} "
                         f"(box: {best.width}x{best.height} @ {best.x},{best.y})")
            return int(class_id)

        except Exception as e:
            logger.warning(f"HuskyLens read error: {e}")
            return None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()


# =============================================================================
# Simulation stub — used when real hardware isn't available (demo / CI)
# =============================================================================

class MockHuskyLensReader:
    """
    Simulates HuskyLens output for testing without hardware.
    Cycles through class IDs on a timer so you can see the full flow.
    """

    _CYCLE = [1, 1, 1, 2, 2, 3, None, None]  # simulates realistic detection pattern

    def __init__(self):
        self._index = 0
        self._connected = False

    def connect(self):
        self._connected = True
        logger.info("[MOCK] HuskyLens connected (simulation mode).")

    def disconnect(self):
        self._connected = False

    def is_connected(self):
        return self._connected

    def get_detected_class(self) -> Optional[int]:
        time.sleep(0.4)  # simulate frame rate
        result = self._CYCLE[self._index % len(self._CYCLE)]
        self._index += 1
        logger.debug(f"[MOCK] HuskyLens returning class: {result}")
        return result

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
