"""Tests for disk_manager module."""

import unittest
from unittest.mock import patch, MagicMock
import json

from dd_flash.disk_manager import DiskManager, DiskInfo


class TestDiskInfo(unittest.TestCase):
    """Test DiskInfo dataclass."""

    def test_is_usb(self):
        disk = DiskInfo(
            device_path="/dev/sdb",
            model="Test",
            vendor="",
            size_bytes=1024,
            size_human="1 KB",
            transport="usb",
            is_removable=True,
            is_read_only=False,
        )
        self.assertTrue(disk.is_usb)

    def test_is_not_usb(self):
        disk = DiskInfo(
            device_path="/dev/sda",
            model="Test",
            vendor="",
            size_bytes=1024,
            size_human="1 KB",
            transport="sata",
            is_removable=False,
            is_read_only=False,
        )
        self.assertFalse(disk.is_usb)

    def test_is_safe_target(self):
        disk = DiskInfo(
            device_path="/dev/sdb",
            model="Test",
            vendor="",
            size_bytes=1024,
            size_human="1 KB",
            transport="usb",
            is_removable=True,
            is_read_only=False,
        )
        self.assertTrue(disk.is_safe_target)

    def test_display_name(self):
        disk = DiskInfo(
            device_path="/dev/sdb",
            model="Kingston DataTraveler",
            vendor="Kingston",
            size_bytes=32000000000,
            size_human="32 GB",
            transport="usb",
            is_removable=True,
            is_read_only=False,
        )
        self.assertIn("Kingston", disk.display_name)
        self.assertIn("32 GB", disk.display_name)


class TestDiskManager(unittest.TestCase):
    """Test DiskManager class."""

    def setUp(self):
        self.dm = DiskManager()

    @patch("subprocess.run")
    def test_refresh_disks_empty(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"blockdevices": []}),
        )
        disks = self.dm.refresh_disks(force=True)
        self.assertEqual(len(disks), 0)

    @patch("subprocess.run")
    def test_refresh_disks_with_usb(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "blockdevices": [
                    {
                        "name": "sdb",
                        "size": 32000000000,
                        "type": "disk",
                        "tran": "usb",
                        "rm": True,
                        "ro": False,
                        "model": "DataTraveler",
                        "vendor": "Kingston",
                        "serial": "ABC123",
                        "mountpoints": [],
                        "children": [],
                    }
                ]
            }),
        )
        disks = self.dm.refresh_disks(force=True)
        self.assertEqual(len(disks), 1)
        self.assertEqual(disks[0].device_path, "/dev/sdb")
        self.assertTrue(disks[0].is_usb)

    @patch("subprocess.run")
    def test_is_system_disk(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/dev/sda1\n",
        )
        with patch("builtins.open", MagicMock()):
            self.assertTrue(self.dm.is_system_disk("/dev/sda"))

    def test_bytes_to_human(self):
        self.assertEqual(self.dm._bytes_to_human(0), "0 B")
        self.assertEqual(self.dm._bytes_to_human(512), "512 B")
        self.assertEqual(self.dm._bytes_to_human(1024), "1.0 KB")
        self.assertEqual(self.dm._bytes_to_human(1024 * 1024), "1.0 MB")
        self.assertEqual(self.dm._bytes_to_human(1024 * 1024 * 1024), "1.0 GB")


if __name__ == "__main__":
    unittest.main()
