"""Dialog components for DD Flash."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from dd_flash.disk_manager import DiskInfo


def show_confirmation_dialog(
    parent: Gtk.Window,
    disk_info: DiskInfo,
    on_confirm: callable,
    on_cancel: callable = None,
) -> Adw.MessageDialog:
    """Show a confirmation dialog before flashing.

    Args:
        parent: Parent window
        disk_info: Information about the target disk
        on_confirm: Callback when user confirms
        on_cancel: Callback when user cancels

    Returns:
        The dialog instance
    """
    dialog = Adw.MessageDialog.new(
        parent,
        "Warning",
        f"All data on:\n\n"
        f"{disk_info.model or 'Unknown device'}\n"
        f"{disk_info.device_path}\n"
        f"{disk_info.size_human}\n\n"
        f"will be permanently erased.",
    )

    dialog.add_response("cancel", "Cancel")
    dialog.add_response("flash", "Flash USB")
    dialog.set_response_appearance("flash", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_response(dialog, response):
        if response == "flash":
            on_confirm()
        elif on_cancel:
            on_cancel()

    dialog.connect("response", on_response)
    dialog.present()

    return dialog


def show_error_dialog(
    parent: Gtk.Window,
    title: str,
    message: str,
) -> Adw.MessageDialog:
    """Show an error dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Error message

    Returns:
        The dialog instance
    """
    dialog = Adw.MessageDialog.new(parent, title, message)
    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.present()
    return dialog


def show_success_dialog(
    parent: Gtk.Window,
    title: str,
    message: str,
) -> Adw.MessageDialog:
    """Show a success dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Success message

    Returns:
        The dialog instance
    """
    dialog = Adw.MessageDialog.new(parent, title, message)
    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.present()
    return dialog


def show_cancel_confirmation(
    parent: Gtk.Window,
    on_confirm: callable,
    on_dismiss: callable = None,
) -> Adw.MessageDialog:
    """Show a confirmation dialog for cancelling flash operation.

    Args:
        parent: Parent window
        on_confirm: Callback when user confirms cancellation
        on_dismiss: Callback when user dismisses

    Returns:
        The dialog instance
    """
    dialog = Adw.MessageDialog.new(
        parent,
        "Cancel Flash Operation?",
        "The flash operation is in progress. "
        "Cancelling may leave the USB drive in an unusable state.",
    )

    dialog.add_response("continue", "Continue Flashing")
    dialog.add_response("cancel", "Cancel Flash")
    dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("continue")
    dialog.set_close_response("continue")

    def on_response(dialog, response):
        if response == "cancel":
            on_confirm()
        elif on_dismiss:
            on_dismiss()

    dialog.connect("response", on_response)
    dialog.present()

    return dialog
