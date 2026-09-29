project('dd-flash', 'c',
  version: '1.0.0',
  license: 'GPL-3.0-or-later',
  default_options: ['warning_level=2'],
)

# Installation directories
prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
libdir = prefix / get_option('libdir')

# Python module
python = import('python')
python_installation = python.find_installation('python3', required: true)

# Install Python package
install_subdir('src/dd_flash',
  install_dir: python_installation.get_install_dir() / 'dd_flash',
  strip_directory: true,
)

# Install helper script (privileged)
install_data('src/dd_flash/helper.py',
  install_dir: python_installation.get_install_dir() / 'dd_flash',
)

# Create and install dd-flash launcher script
configure_file(
  input: 'data/dd-flash.in',
  output: 'dd-flash',
  configuration: {
    'PYTHON': python_installation.path(),
    'PKGDATADIR': python_installation.get_install_dir() / 'dd_flash',
  },
  install_dir: bindir,
  install_mode: 'rwxr-xr-x',
)

# Install desktop file
install_data('data/com.gerchan.DDFlash.desktop',
  install_dir: datadir / 'applications',
)

# Install metainfo
install_data('data/com.gerchan.DDFlash.metainfo.xml',
  install_dir: datadir / 'metainfo',
)

# Install icons
install_data('data/icons/com.gerchan.DDFlash.svg',
  install_dir: datadir / 'icons' / 'hicolor' / 'scalable' / 'apps',
)

# Install Polkit policy
install_data('data/com.gerchan.DDFlash.policy',
  install_dir: datadir / 'polkit-1' / 'actions',
)
