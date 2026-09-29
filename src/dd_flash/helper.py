#!/usr/bin/env python3
"""
DD Flash - Privileged helper script.

This script runs with elevated privileges (via pkexec) to perform
operations that require root access, such as unmounting devices
and running dd for image flashing.

Usage:
    helper.py test                          - Test if running as root
    helper.py unmount <device_path>         - Unmount all partitions of a device
    helper.py flash <image> <device>        - Flash image to device
"""

import sys
import os
import subprocess
import signal
import json
import re
import time


def is_root() -> bool:
    """Check if running as root."""
    return os.geteuid() == 0


def cmd_test() -> int:
    """Test command - just check if we're root."""
    if is_root():
        print("OK: Running as root")
        return 0
    else:
        print("ERROR: Not running as root", file=sys.stderr)
        return 1


def cmd_unmount(device_path: str) -> int:
    """Unmount all partitions of a device."""
    if not is_root():
        print("ERROR: Must run as root", file=sys.stderr)
        return 1

    if not os.path.exists(device_path):
        print(f"ERROR: Device {device_path} does not exist", file=sys.stderr)
        return 1

    # Find all mounted partitions
    try:
        result = subprocess.run(
            ["lsblk", "-n", "-o", "MOUNTPOINTS", device_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"ERROR: Failed to query device: {result.stderr.strip()}", file=sys.stderr)
            return 1

        mountpoints = [mp.strip() for mp in result.stdout.strip().split("\n") if mp.strip()]

        if not mountpoints:
            print("OK: No partitions to unmount")
            return 0

        for mountpoint in mountpoints:
            print(f"Unmounting {mountpoint}...")
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
                    print(f"ERROR: Failed to unmount {mountpoint}: {result.stderr.strip()}", file=sys.stderr)
                    return 1

        print("OK: All partitions unmounted")
        return 0

    except subprocess.TimeoutExpired:
        print("ERROR: Unmount operation timed out", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1


def cmd_flash(image_path: str, device_path: str) -> int:
    """Flash an image to a device using dd."""
    if not is_root():
        print("ERROR: Must run as root", file=sys.stderr)
        return 1

    # Validate inputs
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}", file=sys.stderr)
        return 1

    if not os.path.exists(device_path):
        print(f"ERROR: Device not found: {device_path}", file=sys.stderr)
        return 1

    if not os.access(image_path, os.R_OK):
        print(f"ERROR: Cannot read image file: {image_path}", file=sys.stderr)
        return 1

    # Check that device is not a partition (should be whole disk)
    device_name = os.path.basename(device_path)
    if device_name[-1].isdigit():
        print(f"ERROR: {device_path} appears to be a partition. Use the whole disk (e.g., /dev/sdb, not /dev/sdb1).", file=sys.stderr)
        return 1

    # Unmount all partitions first
    print(f"Unmounting partitions on {device_path}...")
    ret = cmd_unmount(device_path)
    if ret != 0:
        print("WARNING: Failed to unmount some partitions, continuing anyway...", file=sys.stderr)

    # Get image size
    image_size = os.path.getsize(image_path)
    print(f"Image size: {image_size} bytes")

    # Run dd
    cmd = [
        "dd",
        f"if={image_path}",
        f"of={device_path}",
        "bs=4M",
        "status=progress",
        "conv=fsync",
    ]

    print(f"Starting dd: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Forward stderr (progress) to our stderr
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line, end="", file=sys.stderr, flush=True)

        returncode = process.wait()

        if returncode == 0:
            # Sync to ensure all data is written
            print("Syncing...")
            subprocess.run(["sync"], timeout=30)
            print("OK: Flash completed successfully")
            return 0
        else:
            print(f"ERROR: dd exited with code {returncode}", file=sys.stderr)
            return returncode

    except subprocess.TimeoutExpired:
        process.kill()
        print("ERROR: Flash operation timed out", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("ERROR: dd command not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: helper.py <command> [args...]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  test                          - Test if running as root", file=sys.stderr)
        print("  unmount <device_path>        - Unmount device partitions", file=sys.stderr)
        print("  flash <image> <device>       - Flash image to device", file=sys.stderr)
        return 1

    command = sys.argv[1]

    if command == "test":
        return cmd_test()
    elif command == "unmount":
        if len(sys.argv) < 3:
            print("ERROR: Device path required", file=sys.stderr)
            return 1
        return cmd_unmount(sys.argv[2])
    elif command == "flash":
        if len(sys.argv) < 4:
            print("ERROR: Image path and device path required", file=sys.stderr)
            return 1
        return cmd_flash(sys.argv[2], sys.argv[3])
    else:
        print(f"ERROR: Unknown command: {command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
