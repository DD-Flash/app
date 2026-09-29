"""Progress view component for displaying flash progress."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from dd_flash.flash_manager import FlashProgress, FlashState


class ProgressView(Gtk.Box):
    """Widget for displaying flash progress."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self._build_ui()
        self.set_visible(False)

    def _build_ui(self):
        """Build the progress view UI."""
        # Status label
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.add_css_class("heading")
        self.append(self.status_label)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("")
        self.append(self.progress_bar)

        # Details box
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        details_box.set_halign(Gtk.Align.FILL)

        # Speed
        self.speed_label = Gtk.Label(label="")
        self.speed_label.add_css_class("progress-text")
        self.speed_label.set_halign(Gtk.Align.START)
        self.speed_label.set_hexpand(True)
        details_box.append(self.speed_label)

        # Data copied
        self.data_label = Gtk.Label(label="")
        self.data_label.add_css_class("progress-text")
        self.data_label.set_halign(Gtk.Align.START)
        self.data_label.set_hexpand(True)
        details_box.append(self.data_label)

        # ETA
        self.eta_label = Gtk.Label(label="")
        self.eta_label.add_css_class("progress-text")
        self.eta_label.set_halign(Gtk.Align.END)
        details_box.append(self.eta_label)

        self.append(details_box)

    def update_progress(self, progress: FlashProgress):
        """Update the progress display.

        Args:
            progress: Current flash progress
        """
        self.progress_bar.set_fraction(progress.percent / 100.0)
        self.progress_bar.set_text(f"{progress.percent:.1f}%")

        self.speed_label.set_label(progress.speed_human)
        self.data_label.set_label(f"{progress.bytes_copied_human} / {progress.total_bytes_human}")
        self.eta_label.set_label(f"ETA {progress.eta_formatted}")

    def set_state(self, state: FlashState, message: str = ""):
        """Set the display state.

        Args:
            state: Current flash state
            message: Optional status message
        """
        if state == FlashState.FLASHING:
            self.set_visible(True)
            self.status_label.set_label("Flashing...")
            self.status_label.remove_css_class("error-label")
            self.status_label.remove_css_class("success-label")
        elif state == FlashState.COMPLETED:
            self.status_label.set_label("Flash completed successfully")
            self.status_label.add_css_class("success-label")
            self.status_label.remove_css_class("error-label")
        elif state == FlashState.ERROR:
            self.status_label.set_label(f"Flash failed\n{message}")
            self.status_label.add_css_class("error-label")
            self.status_label.remove_css_class("success-label")
        elif state == FlashState.CANCELLED:
            self.status_label.set_label("Flash cancelled")
            self.status_label.add_css_class("warning-label")
            self.status_label.remove_css_class("error-label")
            self.status_label.remove_css_class("success-label")
        else:
            self.set_visible(False)

    def reset(self):
        """Reset the progress view."""
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.speed_label.set_label("")
        self.data_label.set_label("")
        self.eta_label.set_label("")
        self.status_label.set_label("Ready")
        self.status_label.remove_css_class("error-label")
        self.status_label.remove_css_class("success-label")
        self.status_label.remove_css_class("warning-label")
        self.set_visible(False)
