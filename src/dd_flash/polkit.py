"""Polkit integration for privileged operations."""

import subprocess
import os
import shutil
from typing import Optional, Tuple


class PolkitManager:
    """Manages Polkit privilege escalation."""

    HELPER_SCRIPT = "dd_flash/helper.py"
    POLKIT_ACTION = "com.gerchan.DDFlash.flash"

    def __init__(self):
        self._helper_path: Optional[str] = None
        self._find_helper()

    def _find_helper(self):
        """Find the helper script path."""
        # Try several locations
        possible_paths = [
            # Installed location
            "/usr/lib/dd-flash/helper.py",
            "/usr/local/lib/dd-flash/helper.py",
            # Relative to this file
            os.path.join(os.path.dirname(__file__), "helper.py"),
            # Development location
            os.path.join(os.path.dirname(__file__), "..", "helper.py"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                self._helper_path = os.path.abspath(path)
                break

    @property
    def helper_available(self) -> bool:
        """Check if the helper script is available."""
        return self._helper_path is not None

    def check_privileges(self) -> Tuple[bool, str]:
        """Check if we can obtain elevated privileges.

        Returns:
            Tuple of (success, error_message)
        """
        if not self._find_helper():
            return False, "Helper script not found."

        if not shutil.which("pkexec"):
            return False, "pkexec not found. Please install polkit."

        # Try to run a simple command with pkexec
        try:
            result = subprocess.run(
                ["pkexec", "--disable-internal-agent", self._helper_path, "test"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr.strip() or "Authentication failed."
        except subprocess.TimeoutExpired:
            return False, "Authentication timed out."
        except FileNotFoundError:
            return False, "pkexec not found."

    def run_flash(
        self,
        image_path: str,
        device_path: str,
        stdout_callback=None,
        stderr_callback=None,
    ) -> Tuple[bool, str]:
        """Run the flash operation with elevated privileges.

        Args:
            image_path: Path to the image file
            device_path: Path to the target device
            stdout_callback: Callback for stdout lines
            stderr_callback: Callback for stderr lines

        Returns:
            Tuple of (success, message)
        """
        if not self.helper_available:
            return False, "Helper script not found."

        if not shutil.which("pkexec"):
            return False, "pkexec not found. Please install polkit."

        cmd = ["pkexec", self._helper_path, "flash", image_path, device_path]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Read output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line and stdout_callback:
                    stdout_callback(line.strip())

            returncode = process.wait()

            if returncode == 0:
                return True, "Flash completed successfully."
            else:
                stderr_output = process.stderr.read()
                return False, stderr_output.strip() or "Flash failed."

        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Flash operation timed out."
        except FileNotFoundError:
            return False, "pkexec not found."
        except Exception as e:
            return False, f"An error occurred: {str(e)}"

    def unmount_device(self, device_path: str) -> Tuple[bool, str]:
        """Unmount a device with elevated privileges.

        Args:
            device_path: Path to the device

        Returns:
            Tuple of (success, message)
        """
        if not self.helper_available:
            return False, "Helper script not found."

        cmd = ["pkexec", self._helper_path, "unmount", device_path]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr.strip() or "Failed to unmount device."
        except subprocess.TimeoutExpired:
            return False, "Unmount operation timed out."
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
