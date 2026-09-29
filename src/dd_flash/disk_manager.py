"""Disk management module - enumerates and validates USB storage devices."""

import subprocess
import re
import os
import json
import sys
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


def bytes_to_human(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


@dataclass
class DiskInfo:
    """Information about a storage device."""
    device_path: str          # e.g., /dev/sdb
    model: str                # e.g., "Kingston DataTraveler"
    vendor: str               # e.g., "Kingston"
    size_bytes: int           # Total size in bytes
    size_human: str           # Human-readable size, e.g., "32 GB"
    transport: str            # e.g., "usb", "sata", "nvme"
    is_removable: bool        # Whether the device is removable
    is_read_only: bool        # Whether the device is read-only
    partitions: List[str] = field(default_factory=list)  # e.g., ["/dev/sdb1"]
    mountpoints: List[str] = field(default_factory=list)  # e.g., ["/mnt/usb"]
    serial: str = ""          # Device serial number

    @property
    def is_usb(self) -> bool:
        """Check if the device is USB-connected."""
        return self.transport.lower() == "usb"

    @property
    def is_safe_target(self) -> bool:
        """Check if the device is a safe flash target."""
        return self.is_usb and self.is_removable and not self.is_read_only

    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        name = self.model or self.device_path
        if self.size_human:
            name += f" • {self.size_human}"
        return name

    @property
    def short_info(self) -> str:
        """Get short info string for display."""
        parts = []
        if self.model:
            parts.append(self.model)
        if self.size_human:
            parts.append(self.size_human)
        parts.append(self.device_path)
        if self.transport:
            parts.append(self.transport.upper())
        return " • ".join(parts)


class DiskManager:
    """Manages disk enumeration and validation."""

    # Critical mount points that indicate a system disk
    CRITICAL_MOUNTPOINTS = {"/", "/boot", "/boot/efi", "/home", "/usr", "/var", "/etc"}

    def __init__(self):
        self._cached_disks: List[DiskInfo] = []
        self._cache_valid = False

    def refresh_disks(self, force: bool = False) -> List[DiskInfo]:
        """Refresh the list of available USB disks."""
        if self._cache_valid and not force:
            return list(self._cached_disks)

        disks = []
        try:
            disks = self._enumerate_usb_disks()
        except Exception:
            pass

        self._cached_disks = disks
        self._cache_valid = True
        return list(disks)

    def _enumerate_usb_disks(self) -> List[DiskInfo]:
        """Enumerate USB storage devices using lsblk."""
        disks = []

        try:
            result = subprocess.run(
                [
                    "lsblk", "-J", "-b",
                    "-o", "NAME,SIZE,TYPE,TRAN,RM,RO,MOUNTPOINTS,MODEL,VENDOR,SERIAL",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return disks

            data = json.loads(result.stdout)
            devices = data.get("blockdevices", [])

            for dev in devices:
                # Only consider whole disks (not partitions)
                if dev.get("type") != "disk":
                    continue

                # Only USB devices
                transport = dev.get("tran") or ""
                if transport.lower() != "usb":
                    continue

                name = dev.get("name", "")
                if not name:
                    continue

                device_path = f"/dev/{name}"
                size_bytes = dev.get("size", 0)
                is_removable = dev.get("rm", False)
                is_read_only = dev.get("ro", False)

                # Get partitions
                partitions = []
                mountpoints = []
                children = dev.get("children", [])
                for child in children:
                    child_name = child.get("name", "")
                    if child_name:
                        partitions.append(f"/dev/{child_name}")
                    child_mounts = child.get("mountpoints", []) or []
                    for mp in child_mounts:
                        if mp:
                            mountpoints.append(mp)

                # Get model and vendor
                model = dev.get("model", "").strip()
                vendor = dev.get("vendor", "").strip()
                serial = dev.get("serial", "").strip()

                # Build display model name
                display_model = model
                if vendor and vendor not in model:
                    display_model = f"{vendor} {model}".strip()

                disk = DiskInfo(
                    device_path=device_path,
                    model=display_model,
                    vendor=vendor,
                    size_bytes=size_bytes,
                    size_human=bytes_to_human(size_bytes),
                    transport=transport,
                    is_removable=is_removable,
                    is_read_only=is_read_only,
                    partitions=partitions,
                    mountpoints=mountpoints,
                    serial=serial,
                )

                disks.append(disk)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            pass

        return disks

    def _bytes_to_human(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        return bytes_to_human(size_bytes)

    def is_system_disk(self, device_path: str) -> bool:
        """Check if a device is a system disk (contains critical partitions)."""
        # Check if any partition of this device is mounted at a critical mountpoint
        try:
            result = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", "/"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                root_source = result.stdout.strip()
                if root_source.startswith(device_path):
                    return True

            # Check /proc/mounts for critical mountpoints
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    mountpoint = parts[1]
                    source = parts[0]

                    if mountpoint in self.CRITICAL_MOUNTPOINTS:
                        if source.startswith(device_path):
                            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False

    def is_mounted(self, device_path: str) -> bool:
        """Check if any partition of the device is currently mounted."""
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    source = parts[0]
                    if source.startswith(device_path):
                        return True
        except FileNotFoundError:
            pass
        return False

    def get_mountpoints(self, device_path: str) -> List[str]:
        """Get all mountpoints for a device."""
        mountpoints = []
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    source = parts[0]
                    mountpoint = parts[1]
                    if source.startswith(device_path):
                        mountpoints.append(mountpoint)
        except FileNotFoundError:
            pass
        return mountpoints

    def validate_flash_target(self, device_path: str) -> tuple[bool, str]:
        """Validate if a device is safe to flash to.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if device exists
        if not os.path.exists(device_path):
            return False, f"Device {device_path} does not exist."

        # Check if it's a system disk
        if self.is_system_disk(device_path):
            return False, (
                f"Cannot flash to {device_path}: "
                "This device contains the root filesystem or other critical system partitions."
            )

        # Check if it's a USB device
        try:
            result = subprocess.run(
                ["lsblk", "-n", "-d", "-o", "TRAN", device_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                transport = result.stdout.strip()
                if transport.lower() != "usb":
                    return False, (
                        f"Cannot flash to {device_path}: "
                        f"Device is not a USB device (transport: {transport or 'unknown'})."
                    )
        except subprocess.TimeoutExpired:
            pass

        # Check if removable
        try:
            result = subprocess.run(
                ["lsblk", "-n", "-d", "-o", "RM", device_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                rm = result.stdout.strip()
                if rm != "1":
                    return False, (
                        f"Cannot flash to {device_path}: "
                        "Device is not removable. Only removable USB devices can be flashed."
                    )
        except subprocess.TimeoutExpired:
            pass

        return True, ""

    def is_hybrid_iso(self, image_path: str) -> bool:
        """Check if an ISO file is hybrid (can be written directly to USB).

        Args:
            image_path: Path to the ISO file

        Returns:
            True if the ISO is hybrid, False otherwise
        """
        try:
            result = subprocess.run(
                ["file", "--brief", image_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                # Check for hybrid indicators
                if "bootable" in output and "iso 9660" in output:
                    # Check if it has isohybrid boot sector
                    result2 = subprocess.run(
                        ["fdisk", "-l", image_path],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result2.returncode == 0:
                        # Hybrid ISOs typically have a partition table
                        if "disklabel type" in result2.stdout.lower():
                            return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_boot_mode(self) -> str:
        """Detect system boot mode (UEFI or Legacy).

        Returns:
            "UEFI", "Legacy", or "Unknown"
        """
        if os.path.exists("/sys/firmware/efi"):
            return "UEFI"
        return "Legacy"

    def is_uefi_bootable(self, image_path: str) -> bool:
        """Check if an ISO supports UEFI boot.

        Args:
            image_path: Path to the ISO file

        Returns:
            True if the ISO supports UEFI boot
        """
        try:
            # Check for EFI boot files in the ISO
            result = subprocess.run(
                ["isoinfo", "-l", "-i", image_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if "efi" in output or "boot" in output:
                    return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def unmount_device(self, device_path: str) -> tuple[bool, str]:
        """Safely unmount all partitions of a device.

        Returns:
            Tuple of (success, error_message)
        """
        mountpoints = self.get_mountpoints(device_path)

        if not mountpoints:
            return True, ""

        for mountpoint in mountpoints:
            try:
                result = subprocess.run(
                    ["umount", mountpoint],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    # Try lazy unmount
                    result = subprocess.run(
                        ["umount", "-l", mountpoint],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode != 0:
                        return False, f"Failed to unmount {mountpoint}: {result.stderr.strip()}"
            except subprocess.TimeoutExpired:
                return False, f"Timeout while unmounting {mountpoint}"

        return True, ""
