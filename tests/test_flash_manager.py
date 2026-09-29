"""Tests for flash_manager module."""

import unittest
from unittest.mock import patch, MagicMock
import re

from dd_flash.flash_manager import FlashManager, FlashProgress, FlashState


class TestFlashProgress(unittest.TestCase):
    """Test FlashProgress dataclass."""

    def test_initial_state(self):
        p = FlashProgress()
        self.assertEqual(p.bytes_copied, 0)
        self.assertEqual(p.total_bytes, 0)
        self.assertEqual(p.percent, 0.0)

    def test_percent_calculation(self):
        p = FlashProgress(bytes_copied=50, total_bytes=100)
        self.assertEqual(p.percent, 0.0)  # percent is set externally

    def test_eta_formatted(self):
        p = FlashProgress(eta_seconds=0)
        self.assertEqual(p.eta_formatted, "--:--")

        p = FlashProgress(eta_seconds=48)
        self.assertEqual(p.eta_formatted, "00:48")

        p = FlashProgress(eta_seconds=3661)
        self.assertEqual(p.eta_formatted, "01:01:01")


class TestFlashManager(unittest.TestCase):
    """Test FlashManager class."""

    def setUp(self):
        self.fm = FlashManager()

    def test_initial_state(self):
        self.assertEqual(self.fm.state, FlashState.IDLE)
        self.assertFalse(self.fm.is_flashing)

    def test_bytes_to_human(self):
        from dd_flash.flash_manager import _bytes_to_human
        self.assertEqual(_bytes_to_human(0), "0 B")
        self.assertEqual(_bytes_to_human(1024), "1.0 KB")
        self.assertEqual(_bytes_to_human(1024 * 1024), "1.0 MB")

    def test_dd_progress_regex(self):
        """Test that we can parse dd progress output."""
        line = "123456789 bytes (123 MB, 118 MiB) copied, 5.678 s, 21.7 MB/s"
        match = FlashManager.DD_PROGRESS_RE.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 123456789)
        self.assertEqual(match.group(7), "21.7")
        self.assertEqual(match.group(8), "MB")


if __name__ == "__main__":
    unittest.main()
