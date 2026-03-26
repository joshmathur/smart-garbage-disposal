# =============================================================================
# src/classifier.py — Waste Category Classifier
# =============================================================================
# Converts raw HuskyLens class IDs into named waste categories.
# Also handles the debounce logic so a single noisy frame doesn't trigger
# a bin open — requires N consecutive detections of the same class.

import logging
from typing import Optional
from config import WASTE_CLASS_MAP, DETECTION_THRESHOLD_FRAMES

logger = logging.getLogger(__name__)


class WasteClassifier:
    """
    Maps HuskyLens class IDs to waste category names and applies frame-based
    debouncing to filter out false positives.

    Args:
        class_map:         Dict of {int class_id: str category_name}
        threshold_frames:  Consecutive detections required to confirm a result

    Usage:
        clf = WasteClassifier()
        category = clf.update(raw_class_id)
        # category is non-None only after N consecutive matching frames
    """

    def __init__(self,
                 class_map: dict = None,
                 threshold_frames: int = DETECTION_THRESHOLD_FRAMES):
        self.class_map = class_map or WASTE_CLASS_MAP
        self.threshold = threshold_frames
        self._consecutive_count = 0
        self._last_class_id: Optional[int] = None

    def update(self, class_id: Optional[int]) -> Optional[str]:
        """
        Feed in the latest raw class ID from HuskyLens.

        Returns:
            str: Category name (e.g. "RECYCLABLE") once threshold is reached.
            None: If no detection, unknown class, or threshold not yet met.
        """
        if class_id is None:
            self._reset()
            return None

        if class_id not in self.class_map:
            logger.warning(f"Unknown class ID {class_id} — not in class map. "
                           f"Did you update WASTE_CLASS_MAP in config.py?")
            self._reset()
            return None

        if class_id == self._last_class_id:
            self._consecutive_count += 1
        else:
            # New class detected — restart count
            self._last_class_id = class_id
            self._consecutive_count = 1

        logger.debug(f"Class {class_id} seen {self._consecutive_count}/{self.threshold} frames")

        if self._consecutive_count >= self.threshold:
            category = self.class_map[class_id]
            logger.info(f"Confirmed detection: {category} (class ID {class_id})")
            self._reset()  # reset so same object doesn't re-trigger immediately
            return category

        return None

    def _reset(self):
        self._consecutive_count = 0
        self._last_class_id = None

    @property
    def category_names(self) -> list:
        """All valid category names in this classifier."""
        return list(self.class_map.values())
