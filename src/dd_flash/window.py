"""Main application window for DD Flash."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gio

from dd_flash.disk_manager import DiskManager, DiskInfo
from dd_flash.flash_manager import FlashManager, FlashState, FlashProgress
from dd_flash.polkit import PolkitManager
from dd_flash.ui.file_chooser import ImageFileChooser
from dd_flash.ui.disk_selector import DiskSelector
from dd_flash.ui.progress_view import ProgressView
from dd_flash.ui.dialogs import (
    show_confirmation_dialog,
    show_error_dialog,
    show_success_dialog,
    show_cancel_confirmation,
)


class DDFlashWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.disk_manager = DiskManager()
        self.flash_manager = FlashManager()
        self.polkit_manager = PolkitManager()

        # Set up flash manager callbacks
        self.flash_manager.on_progress = self._on_flash_progress
        self.flash_manager.on_state_changed = self._on_flash_state_changed
        self.flash_manager.on_error = self._on_flash_error
        self.flash_manager.on_complete = self._on_flash_complete

        # Build UI
        self._build_ui()

        # Set window properties
        self.set_default_size(500, 600)
        self.set_title("DD Flash")

    def _build_ui(self):
        """Build the main window UI."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="DD Flash"))

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(self._create_menu())
        header.pack_end(menu_button)

        main_box.append(header)

        # Content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_hexpand(True)
        content_box.set_vexpand(True)

        # Image file chooser
        self.file_chooser = ImageFileChooser(self)
        content_box.append(self.file_chooser)

        # Disk selector
        self.disk_selector = DiskSelector()
        content_box.append(self.disk_selector)

        # Flash button
        self.flash_button = Gtk.Button(label="Flash USB")
        self.flash_button.add_css_class("flash-button")
        self.flash_button.add_css_class("suggested-action")
        self.flash_button.set_halign(Gtk.Align.CENTER)
        self.flash_button.connect("clicked", self._on_flash_clicked)
        content_box.append(self.flash_button)

        # Progress view
        self.progress_view = ProgressView()
        content_box.append(self.progress_view)

        # Scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(content_box)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        main_box.append(scrolled)

        # Status bar
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_start(16)
        self.status_label.set_margin_end(16)
        self.status_label.set_margin_bottom(8)
        self.status_label.add_css_class("dim-label")
        main_box.append(self.status_label)

        # Update button state
        self._update_button_state()

    def _create_menu(self) -> Gio.Menu:
        """Create the application menu."""
        menu = Gio.Menu()

        # About
        menu.append("About", "app.about")

        # Quit
        menu.append("Quit", "app.quit")

        return menu

    def _update_button_state(self):
        """Update the flash button state based on selections."""
        has_image = self.file_chooser.is_valid
        has_disk = self.disk_selector.has_selection
        is_flashing = self.flash_manager.is_flashing

        self.flash_button.set_sensitive(has_image and has_disk and not is_flashing)

        if is_flashing:
            self.flash_button.set_label("Flashing...")
        else:
            self.flash_button.set_label("Flash USB")

    def _on_flash_clicked(self, button):
        """Handle flash button click."""
        image_path = self.file_chooser.image_path
        disk = self.disk_selector.selected_disk

        if not image_path or not disk:
            return

        # Validate image size vs disk size
        image_size = self.file_chooser.image_size
        if image_size > disk.size_bytes:
            show_error_dialog(
                self,
                "Image Too Large",
                f"The selected image ({self._bytes_to_human(image_size)}) is too large "
                f"for this USB drive ({disk.size_human}).",
            )
            return

        # Validate target
        is_valid, error_msg = self.disk_manager.validate_flash_target(disk.device_path)
        if not is_valid:
            show_error_dialog(self, "Invalid Target", error_msg)
            return

        # Show confirmation dialog
        show_confirmation_dialog(
            self,
            disk,
            on_confirm=lambda: self._start_flash(image_path, disk),
        )

    def _start_flash(self, image_path: str, disk: DiskInfo):
        """Start the flashing process."""
        # Unmount device first
        success, error = self.disk_manager.unmount_device(disk.device_path)
        if not success:
            show_error_dialog(self, "Unmount Failed", error)
            return

        # Start flashing
        started = self.flash_manager.start_flash(
            image_path=image_path,
            device_path=disk.device_path,
            total_bytes=disk.size_bytes,
        )

        if not started:
            show_error_dialog(
                self,
                "Flash Failed",
                self.flash_manager._error_message or "Failed to start flash operation.",
            )

    def _on_flash_progress(self, progress: FlashProgress):
        """Handle flash progress updates."""
        GLib.idle_add(self.progress_view.update_progress, progress)

    def _on_flash_state_changed(self, state: FlashState):
        """Handle flash state changes."""
        GLib.idle_add(self._update_button_state)

        if state == FlashState.FLASHING:
            GLib.idle_add(self.progress_view.set_state, state)
            GLib.idle_add(self._set_status, "Flashing...")
        elif state == FlashState.COMPLETED:
            GLib.idle_add(self.progress_view.set_state, state)
            GLib.idle_add(self._set_status, "Flash completed successfully")
        elif state == FlashState.ERROR:
            GLib.idle_add(self.progress_view.set_state, state, self.flash_manager._error_message)
            GLib.idle_add(self._set_status, "Flash failed")
        elif state == FlashState.CANCELLED:
            GLib.idle_add(self.progress_view.set_state, state)
            GLib.idle_add(self._set_status, "Flash cancelled")

    def _on_flash_error(self, message: str):
        """Handle flash errors."""
        GLib.idle_add(show_error_dialog, self, "Flash Error", message)

    def _on_flash_complete(self, success: bool, message: str):
        """Handle flash completion."""
        if success:
            GLib.idle_add(show_success_dialog, self, "Success", message)
        # Refresh disk list after completion
        GLib.idle_add(self.disk_selector.refresh_disks)

    def _set_status(self, message: str):
        """Set the status bar message."""
        self.status_label.set_label(message)

    def _bytes_to_human(self, size_bytes: int) -> str:
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

    def set_image_from_path(self, path: str):
        """Set the image file from a path (for command-line file open)."""
        self.file_chooser.set_image(path)
        self._update_button_state()

    def do_close_request(self) -> bool:
        """Handle window close request."""
        if self.flash_manager.is_flashing:
            show_cancel_confirmation(
                self,
                on_confirm=self._on_cancel_confirmed,
                on_dismiss=lambda: None,
            )
            return True  # Prevent closing
        return False  # Allow closing

    def _on_cancel_confirmed(self):
        """Handle cancel confirmation."""
        self.flash_manager.cancel_flash()
