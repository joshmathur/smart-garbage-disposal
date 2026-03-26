#!/usr/bin/env python3
# =============================================================================
# main.py — Smart Garbage Disposal System
# York University k2i STEM Challenge, 2024
# =============================================================================
# Entry point. Reads waste classification from HuskyLens, debounces results,
# and sends servo open commands to the Micro:bit.
#
# Usage:
#   python main.py             # real hardware mode
#   python main.py --mock      # simulation mode (no hardware needed)
#   python main.py --mock --verbose

import sys
import time
import logging
import argparse

from config import SERVO_OPEN_DURATION_MS
from src.husky_lens import HuskyLensReader, MockHuskyLensReader
from src.microbit_controller import MicrobitController, MockMicrobitController
from src.classifier import WasteClassifier
import config


# =============================================================================
# Logging setup
# =============================================================================

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


# =============================================================================
# Core loop
# =============================================================================

def run(mock: bool = False) -> None:
    """
    Main detection loop.

    1. Poll HuskyLens for current object class.
    2. Run through WasteClassifier (debounce + ID → name mapping).
    3. If a category is confirmed, tell the Micro:bit to open that compartment.
    4. Wait for the compartment to auto-close before polling again.

    Args:
        mock: If True, use simulated hardware classes instead of real devices.
    """
    logger = logging.getLogger("main")

    # --- Instantiate hardware (or mocks) ---
    if mock:
        logger.info("Running in SIMULATION MODE — no hardware required.")
        husky = MockHuskyLensReader()
        microbit = MockMicrobitController()
    else:
        husky = HuskyLensReader(
            mode=config.HUSKY_MODE,
            port=config.HUSKY_LENS_PORT,
            baud_rate=config.BAUD_RATE,
            i2c_address=config.HUSKY_I2C_ADDRESS,
        )
        microbit = MicrobitController(
            port=config.MICROBIT_PORT,
            baud_rate=config.BAUD_RATE,
        )

    classifier = WasteClassifier()

    # --- Connect ---
    try:
        husky.connect()
        microbit.connect()
    except Exception as e:
        logger.error(f"Hardware initialisation failed: {e}")
        logger.error("Tip: run with --mock to test without hardware.")
        sys.exit(1)

    logger.info("System online. Watching for waste objects... (Ctrl+C to stop)\n")

    # --- Main loop ---
    try:
        while True:
            raw_id = husky.get_detected_class()
            category = classifier.update(raw_id)

            if category:
                logger.info(f"[DETECT] {category} — opening compartment")
                success = microbit.open_compartment(category)

                if success:
                    # Wait for the bin to stay open, then resume scanning
                    wait_s = SERVO_OPEN_DURATION_MS / 1000
                    logger.info(f"Compartment open. Resuming scan in {wait_s:.1f}s...")
                    time.sleep(wait_s)
                else:
                    logger.warning("Micro:bit did not confirm compartment open — skipping wait.")

    except KeyboardInterrupt:
        logger.info("\nShutdown requested.")

    finally:
        husky.disconnect()
        microbit.disconnect()
        logger.info("System shut down cleanly.")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Smart Garbage Disposal System — HuskyLens + Micro:bit backend"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in simulation mode without physical hardware",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    run(mock=args.mock)
