"""Flash manager - handles the actual dd-based image writing process."""

import subprocess
import re
import threading
import time
import os
import signal
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional
from pathlib import Path


class FlashState(Enum):
    """States of the flashing process."""
    IDLE = auto()
    FLASHING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    ERROR = auto()


@dataclass
class FlashProgress:
    """Progress information during flashing."""
    bytes_copied: int = 0
    total_bytes: int = 0
    bytes_per_sec: float = 0.0
    percent: float = 0.0
    eta_seconds: int = 0

    @property
    def bytes_copied_human(self) -> str:
        return _bytes_to_human(self.bytes_copied)

    @property
    def total_bytes_human(self) -> str:
        return _bytes_to_human(self.total_bytes)

    @property
    def speed_human(self) -> str:
        return f"{_bytes_to_human(int(self.bytes_per_sec))}/s"

    @property
    def eta_formatted(self) -> str:
        if self.eta_seconds <= 0:
            return "--:--"
        minutes, seconds = divmod(self.eta_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


def _bytes_to_human(size_bytes: int) -> str:
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


class FlashManager:
    """Manages the image flashing process."""

    # Regex to parse dd progress output
    DD_PROGRESS_RE = re.compile(
        r"(\d+)\s+bytes\s+\(([\d.]+)\s*(\w+),\s*([\d.]+)\s*(\w+)\)\s+copied,\s*([\d.]+)\s*s,\s*([\d.]+)\s*(\w+)/s"
    )

    def __init__(self):
        self.state = FlashState.IDLE
        self.process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._flash_thread: Optional[threading.Thread] = None
        self._progress = FlashProgress()
        self._error_message = ""
        self._success_message = ""

        # Callbacks
        self.on_progress: Optional[Callable[[FlashProgress], None]] = None
        self.on_state_changed: Optional[Callable[[FlashState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_complete: Optional[Callable[[bool, str], None]] = None

    @property
    def progress(self) -> FlashProgress:
        return self._progress

    @property
    def is_flashing(self) -> bool:
        return self.state == FlashState.FLASHING

    def start_flash(
        self,
        image_path: str,
        device_path: str,
        total_bytes: int,
    ) -> bool:
        """Start the flashing process.

        Args:
            image_path: Path to the ISO/IMG file
            device_path: Path to the target device (e.g., /dev/sdb)
            total_bytes: Total size of the image in bytes

        Returns:
            True if flashing started successfully
        """
        if self.state == FlashState.FLASHING:
            return False

        # Validate image file
        if not os.path.exists(image_path):
            self._set_error(f"Image file not found: {image_path}")
            return False

        if not os.access(image_path, os.R_OK):
            self._set_error(f"Cannot read image file: {image_path}")
            return False

        # Validate device
        if not os.path.exists(device_path):
            self._set_error(f"Device not found: {device_path}")
            return False

        # Check image size vs device size
        image_size = os.path.getsize(image_path)
        if image_size > total_bytes:
            self._set_error(
                f"The selected image ({_bytes_to_human(image_size)}) is too large "
                f"for this USB drive ({_bytes_to_human(total_bytes)})."
            )
            return False

        self._cancel_event.clear()
        self._progress = FlashProgress(total_bytes=image_size)
        self._error_message = ""
        self._success_message = ""

        self._set_state(FlashState.FLASHING)

        # Start flashing in a separate thread
        self._flash_thread = threading.Thread(
            target=self._flash_worker,
            args=(image_path, device_path, image_size),
            daemon=True,
        )
        self._flash_thread.start()

        return True

    def _flash_worker(self, image_path: str, device_path: str, total_bytes: int):
        """Worker thread that runs the dd command."""
        try:
            # Build the dd command
            cmd = [
                "dd",
                f"if={image_path}",
                f"of={device_path}",
                "bs=4M",
                "status=progress",
                "conv=fsync",
            ]

            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Read stderr for progress (dd outputs progress to stderr)
            last_progress_time = time.time()

            while True:
                if self._cancel_event.is_set():
                    self._cancel_flash()
                    return

                line = self.process.stderr.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    continue

                # Parse progress line
                match = self.DD_PROGRESS_RE.search(line)
                if match:
                    bytes_copied = int(match.group(1))
                    speed_str = match.group(7)
                    speed_unit = match.group(8)

                    # Convert speed to bytes/sec
                    speed_bytes = float(speed_str)
                    if speed_unit == "KB":
                        speed_bytes *= 1024
                    elif speed_unit == "MB":
                        speed_bytes *= 1024 * 1024
                    elif speed_unit == "GB":
                        speed_bytes *= 1024 * 1024 * 1024

                    percent = (bytes_copied / total_bytes * 100) if total_bytes > 0 else 0

                    # Calculate ETA
                    remaining_bytes = total_bytes - bytes_copied
                    eta = int(remaining_bytes / speed_bytes) if speed_bytes > 0 else 0

                    self._progress = FlashProgress(
                        bytes_copied=bytes_copied,
                        total_bytes=total_bytes,
                        bytes_per_sec=speed_bytes,
                        percent=min(percent, 100.0),
                        eta_seconds=eta,
                    )

                    last_progress_time = time.time()

                    if self.on_progress:
                        self.on_progress(self._progress)

                # Check for timeout (no progress for 60 seconds)
                if time.time() - last_progress_time > 60:
                    self._cancel_flash()
                    self._set_error("Flash operation timed out - no progress for 60 seconds.")
                    return

            # Process finished
            returncode = self.process.wait()

            if self._cancel_event.is_set():
                self._set_state(FlashState.CANCELLED)
                if self.on_complete:
                    self.on_complete(False, "Flash cancelled by user.")
                return

            if returncode == 0:
                # Run sync to ensure all data is written
                subprocess.run(["sync"], timeout=30)
                self._success_message = "Flash completed successfully"
                self._set_state(FlashState.COMPLETED)
                if self.on_complete:
                    self.on_complete(True, self._success_message)
            else:
                error_msg = self._parse_dd_error(self.process.stderr.read())
                self._set_error(error_msg)

        except subprocess.TimeoutExpired:
            self._cancel_flash()
            self._set_error("Flash operation timed out.")
        except FileNotFoundError:
            self._set_error("dd command not found. Please install coreutils.")
        except PermissionError:
            self._set_error(
                "Permission denied. The application needs elevated privileges to write to the device."
            )
        except Exception as e:
            self._set_error(f"An unexpected error occurred: {str(e)}")

    def _parse_dd_error(self, stderr_output: str) -> str:
        """Parse dd error output into a user-friendly message."""
        if not stderr_output:
            return "Flash failed with an unknown error."

        stderr_lower = stderr_output.lower()

        if "no space left" in stderr_lower:
            return "Not enough space on the target device."
        elif "input/output error" in stderr_lower or "i/o error" in stderr_lower:
            return "The USB device reported an I/O error."
        elif "permission denied" in stderr_lower:
            return "Permission denied. Please try again."
        elif "read-only" in stderr_lower:
            return "The device is read-only."
        else:
            # Return the last non-empty line
            lines = [l.strip() for l in stderr_output.strip().split("\n") if l.strip()]
            if lines:
                return f"Flash failed: {lines[-1]}"
            return "Flash failed with an unknown error."

    def cancel_flash(self):
        """Request cancellation of the current flash operation."""
        if self.state != FlashState.FLASHING:
            return

        self._cancel_event.set()

    def _cancel_flash(self):
        """Internal method to cancel the flash process."""
        if self.process and self.process.poll() is None:
            try:
                # Send SIGTERM first
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    self.process.kill()
                    self.process.wait(timeout=5)
            except (ProcessLookupError, OSError):
                pass

        # Run sync to ensure filesystem consistency
        try:
            subprocess.run(["sync"], timeout=10)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _set_state(self, new_state: FlashState):
        """Set the flash state and notify listeners."""
        self.state = new_state
        if self.on_state_changed:
            self.on_state_changed(new_state)

    def _set_error(self, message: str):
        """Set error state with message."""
        self._error_message = message
        self._set_state(FlashState.ERROR)
        if self.on_error:
            self.on_error(message)
        if self.on_complete:
            self.on_complete(False, message)

    def cleanup(self):
        """Clean up resources."""
        if self.state == FlashState.FLASHING:
            self.cancel_flash()
        if self._flash_thread and self._flash_thread.is_alive():
            self._flash_thread.join(timeout=10)
