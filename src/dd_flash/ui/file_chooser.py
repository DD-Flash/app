"""File chooser component for selecting ISO/IMG files."""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gio

from dd_flash.disk_manager import bytes_to_human


class ImageFileChooser(Gtk.Box):
    """Widget for selecting an ISO/IMG file."""

    def __init__(self, parent_window: Gtk.Window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.parent_window = parent_window
        self._image_path: str = ""
        self._image_size: int = 0

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the file chooser UI."""
        # Title
        title_label = Gtk.Label(label="Image")
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("heading")
        self.append(title_label)

        # File row
        self.file_row = Adw.ActionRow()
        self.file_row.set_title("No file selected")
        self.file_row.set_subtitle("Select an .iso or .img file to flash")

        # File icon
        icon = Gtk.Image.new_from_icon_name("media-optical-symbolic")
        icon.set_icon_size(Gtk.IconSize.LARGE)
        self.file_row.add_prefix(icon)

        # Browse button
        browse_button = Gtk.Button(label="Browse")
        browse_button.add_css_class("pill")
        browse_button.connect("clicked", self._on_browse_clicked)
        self.file_row.add_suffix(browse_button)

        # Size label (hidden initially)
        self.size_label = Gtk.Label(label="")
        self.size_label.set_halign(Gtk.Align.START)
        self.size_label.add_css_class("caption")
        self.size_label.set_visible(False)

        # Assemble
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.append(self.file_row)
        box.append(self.size_label)
        self.append(box)

    def _on_browse_clicked(self, button):
        """Handle browse button click."""
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select Image File")

        # Set up filters
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Disk Images")
        filter_images.add_pattern("*.iso")
        filter_images.add_pattern("*.img")

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        filters.append(filter_all)

        dialog.set_filters(filters)
        dialog.set_default_filter(filter_images)

        dialog.open(self.parent_window, None, self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        """Handle file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                if path:
                    self.set_image(path)
        except GLib.Error:
            pass

    def set_image(self, path: str):
        """Set the selected image file.

        Args:
            path: Path to the image file
        """
        if not os.path.exists(path):
            return

        self._image_path = path
        self._image_size = os.path.getsize(path)

        filename = os.path.basename(path)
        self.file_row.set_title(filename)
        self.file_row.set_subtitle(path)

        if self._image_size > 0:
            self.size_label.set_label(f"Size: {bytes_to_human(self._image_size)}")
            self.size_label.set_visible(True)

    def clear(self):
        """Clear the selected image."""
        self._image_path = ""
        self._image_size = 0
        self.file_row.set_title("No file selected")
        self.file_row.set_subtitle("Select an .iso or .img file to flash")
        self.size_label.set_visible(False)

    @property
    def image_path(self) -> str:
        """Get the selected image path."""
        return self._image_path

    @property
    def image_size(self) -> int:
        """Get the selected image size in bytes."""
        return self._image_size

    @property
    def is_valid(self) -> bool:
        """Check if a valid image is selected."""
        return bool(self._image_path) and os.path.exists(self._image_path)
