"""Disk selector component for choosing target USB device."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from dd_flash.disk_manager import DiskInfo, DiskManager


class DiskSelector(Gtk.Box):
    """Widget for selecting a target USB disk."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.disk_manager = DiskManager()
        self._disks: list[DiskInfo] = []
        self._selected_disk: DiskInfo | None = None

        # Build UI
        self._build_ui()

        # Initial refresh
        self.refresh_disks()

    def _build_ui(self):
        """Build the disk selector UI."""
        # Title with refresh button
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_halign(Gtk.Align.FILL)

        title_label = Gtk.Label(label="Target")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        title_label.add_css_class("heading")
        header.append(title_label)

        refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_button.add_css_class("flat")
        refresh_button.set_tooltip_text("Refresh device list")
        refresh_button.connect("clicked", lambda b: self.refresh_disks())
        header.append(refresh_button)

        self.append(header)

        # Disk list box
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class("boxed-list")
        self.list_box.connect("row-selected", self._on_row_selected)
        self.append(self.list_box)

        # Empty state label
        self.empty_label = Gtk.Label(label="No USB devices detected")
        self.empty_label.add_css_class("dim-label")
        self.empty_label.set_visible(False)
        self.append(self.empty_label)

    def refresh_disks(self):
        """Refresh the list of available USB disks."""
        # Clear existing rows
        while True:
            row = self.list_box.get_row_at_index(0)
            if row is None:
                break
            self.list_box.remove(row)

        # Get disks
        self._disks = self.disk_manager.refresh_disks(force=True)

        if not self._disks:
            self.empty_label.set_visible(True)
            self._selected_disk = None
            return

        self.empty_label.set_visible(False)

        for disk in self._disks:
            row = self._create_disk_row(disk)
            self.list_box.append(row)

    def _create_disk_row(self, disk: DiskInfo) -> Adw.ActionRow:
        """Create a list box row for a disk."""
        row = Adw.ActionRow()
        row.set_title(disk.model or "Unknown Device")
        row.set_subtitle(
            f"{disk.size_human} • {disk.device_path} • {disk.transport.upper()}"
        )

        # Icon
        icon = Gtk.Image.new_from_icon_name("drive-removable-media-usb-symbolic")
        icon.set_icon_size(Gtk.IconSize.LARGE)
        row.add_prefix(icon)

        # Store disk info
        row.disk_info = disk

        return row

    def _on_row_selected(self, list_box, row):
        """Handle row selection."""
        if row and hasattr(row, "disk_info"):
            self._selected_disk = row.disk_info
        else:
            self._selected_disk = None

    @property
    def selected_disk(self) -> DiskInfo | None:
        """Get the currently selected disk."""
        return self._selected_disk

    @property
    def has_selection(self) -> bool:
        """Check if a disk is selected."""
        return self._selected_disk is not None
