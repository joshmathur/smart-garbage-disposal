# =============================================================================
# tests/test_classifier.py
# =============================================================================
# Run with: python -m pytest tests/ -v

import pytest
from src.classifier import WasteClassifier


CLASS_MAP = {1: "RECYCLABLE", 2: "COMPOST", 3: "LANDFILL"}


def make_clf(threshold=3):
    return WasteClassifier(class_map=CLASS_MAP, threshold_frames=threshold)


class TestDebounce:

    def test_no_detection_returns_none(self):
        clf = make_clf()
        assert clf.update(None) is None

    def test_single_frame_not_enough(self):
        clf = make_clf(threshold=3)
        assert clf.update(1) is None

    def test_two_frames_not_enough(self):
        clf = make_clf(threshold=3)
        clf.update(1)
        assert clf.update(1) is None

    def test_three_consecutive_confirms(self):
        clf = make_clf(threshold=3)
        clf.update(1)
        clf.update(1)
        result = clf.update(1)
        assert result == "RECYCLABLE"

    def test_resets_on_class_change(self):
        clf = make_clf(threshold=3)
        clf.update(1)
        clf.update(1)
        clf.update(2)  # class changed — counter resets
        assert clf.update(2) is None  # only 2 frames of class 2 so far

    def test_resets_after_confirmation(self):
        """After a confirmed result, same class should need threshold frames again."""
        clf = make_clf(threshold=2)
        clf.update(1)
        clf.update(1)  # confirms
        assert clf.update(1) is None  # counter was reset, back to 1 frame

    def test_none_resets_counter(self):
        clf = make_clf(threshold=3)
        clf.update(1)
        clf.update(1)
        clf.update(None)   # reset
        clf.update(1)
        assert clf.update(1) is None  # only 2 frames after reset

    def test_threshold_one(self):
        clf = make_clf(threshold=1)
        assert clf.update(2) == "COMPOST"


class TestCategoryMapping:

    def test_recyclable(self):
        clf = make_clf(threshold=1)
        assert clf.update(1) == "RECYCLABLE"

    def test_compost(self):
        clf = make_clf(threshold=1)
        assert clf.update(2) == "COMPOST"

    def test_landfill(self):
        clf = make_clf(threshold=1)
        assert clf.update(3) == "LANDFILL"

    def test_unknown_class_returns_none(self):
        clf = make_clf(threshold=1)
        assert clf.update(99) is None

    def test_category_names_list(self):
        clf = make_clf()
        assert set(clf.category_names) == {"RECYCLABLE", "COMPOST", "LANDFILL"}
