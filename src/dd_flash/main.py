"""DD Flash - Main application entry point."""

import sys
import os

# Ensure the source directory is in the path when running from source
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib

from dd_flash.window import DDFlashWindow
from dd_flash import __app_id__, __version__


class DDFlashApplication(Adw.Application):
    """Main application class for DD Flash."""

    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.window = None

        # Add CSS provider for custom styling
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(b"""
            .flash-button {
                font-weight: bold;
                padding: 12px 24px;
            }
            .flash-button:disabled {
                opacity: 0.5;
            }
            .progress-text {
                font-family: monospace;
                font-size: 13px;
            }
            .error-label {
                color: @error_color;
                font-weight: bold;
            }
            .success-label {
                color: @success_color;
                font-weight: bold;
            }
            .warning-label {
                color: @warning_color;
                font-weight: bold;
            }
            .device-row {
                padding: 8px;
            }
            .device-row-selected {
                background-color: alpha(@accent_color, 0.1);
            }
        """)

    def do_startup(self):
        """Initialize the application."""
        Adw.Application.do_startup(self)

        # Set up CSS
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Set up actions
        self._setup_actions()

    def _setup_actions(self):
        """Set up application actions."""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda a, p: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

    def _on_about(self, action, param):
        """Show about dialog."""
        dialog = Adw.AboutWindow.new_from_appdata(
            "/usr/share/metainfo/com.gerchan.DDFlash.metainfo.xml",
            __version__,
        )
        dialog.set_transient_for(self.window)
        dialog.present()

    def do_activate(self):
        """Activate the application."""
        if not self.window:
            self.window = DDFlashWindow(application=self)
        self.window.present()

    def do_open(self, files, n_files, hint):
        """Handle file open."""
        self.do_activate()
        if n_files > 0 and files[0].get_path():
            self.window.set_image_from_path(files[0].get_path())


def main():
    """Main entry point."""
    # Handle --version before initializing GTK
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"DD Flash {__version__}")
        return 0

    app = DDFlashApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
