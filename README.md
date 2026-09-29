# DD Flash

Modern GTK4/Libadwaita GUI for safely writing `.iso` and `.img` images to USB drives.

## Features

- **Modern interface** — GTK4 + Libadwaita, dark-mode friendly
- **Real-time progress** — speed, ETA, data written
- **Safety** — removable/USB checks, blocks system disks
- **Auto USB detection** — refreshes device list on hotplug
- **Polkit** — GUI runs as normal user, flashing with elevated privileges
- **Cancellation** — safe interruption with confirmation

## Installation

### Quick Install

```bash
git clone https://github.com/gerchann/dd-flash.git
cd dd-flash
./scripts/install.sh
```

The installer automatically detects your distribution and installs all dependencies.

### Supported Distributions

| Base | Derivatives |
|---|---|
| Arch Linux | Manjaro, EndeavourOS, Garuda, Artix, ArcoLinux |
| Fedora | RHEL, CentOS, Rocky, AlmaLinux, Oracle Linux |
| Debian | Linux Mint, Pop!_OS, elementary, Zorin, antiX, MX |
| Ubuntu | Kubuntu, Xubuntu, Lubuntu, Neon |

### Uninstall

```bash
./scripts/uninstall.sh
```

### Check Dependencies

```bash
./scripts/install.sh --check
```

## Requirements

- Python 3.10+
- GTK 4.0+
- Libadwaita 1.0+
- PyGObject
- `dd` (coreutils)
- `pkexec` (polkit)
- `lsblk` (util-linux)

## Usage

```bash
# Launch
dd-flash

# Or directly
python3 -m dd_flash.main

# Open with a file
dd-flash /path/to/image.iso
```

## Architecture

```
src/dd_flash/
├── main.py            # Application entry point
├── window.py          # Main window
├── disk_manager.py    # Disk management (lsblk, validation)
├── flash_manager.py   # dd process management
├── polkit.py          # Polkit integration
├── helper.py          # Privileged helper (pkexec)
└── ui/
    ├── file_chooser.py    # ISO/IMG selection
    ├── disk_selector.py   # Target disk selection
    ├── progress_view.py   # Progress display
    └── dialogs.py         # Confirmation/error dialogs
```

## Safety

DD Flash performs the following checks before writing:

1. Device must be **removable**
2. Device must be **USB**
3. Device must not contain the **root filesystem** (`/`)
4. Device must not contain **critical mountpoints** (`/home`, `/boot`, `/usr`, `/var`)
5. Image size must be **≤ device size**
6. All partitions are **unmounted** before writing

## Author

**gerchanisko**

## License

GPL-3.0-or-later
