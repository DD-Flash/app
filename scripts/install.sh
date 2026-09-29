#!/usr/bin/env bash
# DD Flash - Universal installer
# Detects distribution, installs dependencies, builds and installs DD Flash.
#
# Usage:
#   ./scripts/install.sh              # Install DD Flash
#   ./scripts/install.sh --uninstall  # Uninstall DD Flash
#   ./scripts/install.sh --check      # Check dependencies only

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Print functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Print banner
print_banner() {
    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║          DD Flash Installer          ║"
    echo "╚══════════════════════════════════════╝"
    echo ""
}

# Map derivative distributions to their base distribution
map_derivative() {
    local id="$1"
    case "$id" in
        # Arch derivatives
        manjaro|endeavouros|garuda|artix|arcolinux)
            echo "arch"
            ;;
        # Fedora derivatives
        rhel|centos|rocky|alma|ol|fedora)
            echo "fedora"
            ;;
        # Debian derivatives
        debian|linuxmint|pop|elementary|zorin|antix|mx)
            echo "debian"
            ;;
        # Ubuntu derivatives
        ubuntu|linuxmint|pop|elementary|zorin|neon|kubuntu|xubuntu|lubuntu)
            echo "ubuntu"
            ;;
        *)
            echo "$id"
            ;;
    esac
}

# Detect distribution
detect_distribution() {
    local id=""
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        id="${ID,,}"
    elif [[ -f /etc/arch-release ]]; then
        id="arch"
    elif [[ -f /etc/fedora-release ]]; then
        id="fedora"
    elif [[ -f /etc/debian_version ]]; then
        id="debian"
    else
        id="unknown"
    fi

    # Map derivatives to base distribution
    map_derivative "$id"
}

# Detect architecture
detect_architecture() {
    local arch
    arch="$(uname -m)"
    case "$arch" in
        x86_64|amd64) echo "x86_64" ;;
        aarch64|arm64) echo "aarch64" ;;
        *) echo "$arch" ;;
    esac
}

# Check if running as root
is_root() {
    [[ $EUID -eq 0 ]]
}

# Get sudo command
get_sudo() {
    if is_root; then
        echo ""
    elif command -v sudo &>/dev/null; then
        echo "sudo"
    else
        error "This installer requires root privileges or sudo."
        exit 1
    fi
}

# Check if a command exists
command_exists() {
    command -v "$1" &>/dev/null
}

# Print supported distributions
print_supported() {
    echo "Supported distributions:"
    echo "  - Arch Linux (Manjaro, EndeavourOS, Garuda, Artix)"
    echo "  - Fedora (RHEL, CentOS, Rocky, AlmaLinux)"
    echo "  - Debian (Linux Mint, Pop!_OS, elementary, Zorin)"
    echo "  - Ubuntu (Kubuntu, Xubuntu, Lubuntu, Neon)"
    echo ""
}

# Install packages for Arch Linux
install_arch() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    if ! command_exists pacman; then
        error "pacman not found. This installer is for Arch Linux."
        exit 1
    fi

    local packages=(python python-gobject gtk4 libadwaita polkit meson ninja)

    # Filter out already installed packages
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! pacman -Q "$pkg" &>/dev/null; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -gt 0 ]]; then
        info "Installing packages: ${to_install[*]}"
        $sudo_cmd pacman -S --noconfirm --needed "${to_install[@]}"
    else
        ok "All packages already installed."
    fi
}

# Install packages for Fedora
install_fedora() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    if ! command_exists dnf; then
        error "dnf not found. This installer is for Fedora."
        exit 1
    fi

    local packages=(python3 python3-gobject gtk4 libadwaita polkit meson ninja-build)

    # Filter out already installed packages
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! rpm -q "$pkg" &>/dev/null; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -gt 0 ]]; then
        info "Installing packages: ${to_install[*]}"
        $sudo_cmd dnf install -y "${to_install[@]}"
    else
        ok "All packages already installed."
    fi
}

# Install packages for Debian
install_debian() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    if ! command_exists apt; then
        error "apt not found. This installer is for Debian."
        exit 1
    fi

    info "Updating package lists..."
    $sudo_cmd apt update

    local packages=(python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 polkitd meson ninja-build)

    # Filter out already installed packages
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -gt 0 ]]; then
        info "Installing packages: ${to_install[*]}"
        $sudo_cmd apt install -y "${to_install[@]}"
    else
        ok "All packages already installed."
    fi
}

# Install packages for Ubuntu
install_ubuntu() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    if ! command_exists apt; then
        error "apt not found. This installer is for Ubuntu."
        exit 1
    fi

    info "Updating package lists..."
    $sudo_cmd apt update

    local packages=(python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 polkitd meson ninja-build)

    # Filter out already installed packages
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -gt 0 ]]; then
        info "Installing packages: ${to_install[*]}"
        $sudo_cmd apt install -y "${to_install[@]}"
    else
        ok "All packages already installed."
    fi
}

# Verify dependencies
verify_deps() {
    local distro="$1"
    local all_ok=true

    info "Checking dependencies..."

    case "$distro" in
        arch)
            local deps=(python3 gtk4 libadwaita polkit meson ninja)
            for dep in "${deps[@]}"; do
                if pacman -Q "$dep" &>/dev/null; then
                    ok "$dep"
                else
                    error "$dep is not installed."
                    all_ok=false
                fi
            done
            ;;
        fedora)
            local deps=(python3 python3-gobject gtk4 libadwaita polkit meson ninja-build)
            for dep in "${deps[@]}"; do
                if rpm -q "$dep" &>/dev/null; then
                    ok "$dep"
                else
                    error "$dep is not installed."
                    all_ok=false
                fi
            done
            ;;
        debian|ubuntu)
            local deps=(python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 polkitd meson ninja-build)
            for dep in "${deps[@]}"; do
                if dpkg -l "$dep" 2>/dev/null | grep -q "^ii"; then
                    ok "$dep"
                else
                    error "$dep is not installed."
                    all_ok=false
                fi
            done
            ;;
    esac

    if [[ "$all_ok" != true ]]; then
        error "Some dependencies are missing. Please install them and try again."
        exit 1
    fi

    echo ""
    ok "All dependencies installed."
}

# Build and install DD Flash
build_and_install() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    info "Building DD Flash..."

    cd "$PROJECT_ROOT"

    # Clean previous build
    rm -rf build

    # Setup and build
    meson setup build --prefix=/usr --buildtype=release
    ninja -C build

    ok "Build completed."

    info "Installing DD Flash..."
    $sudo_cmd ninja -C build install

    ok "Installation completed."
}

# Uninstall DD Flash
uninstall() {
    local sudo_cmd
    sudo_cmd="$(get_sudo)"

    echo ""
    echo "This will remove DD Flash from your system."
    echo ""
    read -rp "Continue? [y/N] " response
    case "$response" in
        [yY]|[yY][eE][sS])
            ;;
        *)
            info "Uninstallation cancelled."
            exit 0
            ;;
    esac

    echo ""
    info "Removing DD Flash files..."

    # Remove binary
    if command_exists dd-flash; then
        $sudo_cmd rm -f "$(command -v dd-flash)"
        ok "Removed binary"
    fi

    # Remove Python package
    if [[ -d /usr/lib/python3*/site-packages/dd_flash ]] || [[ -d /usr/lib/python3*/dist-packages/dd_flash ]]; then
        $sudo_cmd rm -rf /usr/lib/python3*/site-packages/dd_flash
        $sudo_cmd rm -rf /usr/lib/python3*/dist-packages/dd_flash
        ok "Removed Python package"
    fi

    # Remove data files
    local data_files=(
        "/usr/share/applications/com.gerchan.DDFlash.desktop"
        "/usr/share/metainfo/com.gerchan.DDFlash.metainfo.xml"
        "/usr/share/icons/hicolor/scalable/apps/com.gerchan.DDFlash.svg"
        "/usr/share/polkit-1/actions/com.gerchan.DDFlash.policy"
    )

    for file in "${data_files[@]}"; do
        if [[ -f "$file" ]]; then
            $sudo_cmd rm -f "$file"
            ok "Removed $file"
        fi
    done

    # Remove build directory if it exists
    if [[ -d build ]]; then
        rm -rf build
        ok "Removed build directory"
    fi

    echo ""
    ok "DD Flash has been uninstalled."
    echo ""
}

# Check dependencies only
check_deps() {
    local distro
    distro="$(detect_distribution)"

    info "Distribution: ${distro}"
    info "Architecture: $(detect_architecture)"
    echo ""

    verify_deps "$distro"
}

# Main installation logic
main_install() {
    print_banner

    # Detect system info
    info "Detecting distribution..."
    local distro
    distro="$(detect_distribution)"
    local version
    version="$(detect_version)"
    local arch
    arch="$(detect_architecture)"

    info "Distribution: ${distro} ${version}"
    info "Architecture: ${arch}"
    echo ""

    # Check if distribution is supported
    local supported=false
    case "$distro" in
        arch|fedora|debian|ubuntu)
            supported=true
            ;;
    esac

    # Also check if it's a known derivative
    if [[ "$supported" != true ]]; then
        local mapped
        mapped="$(map_derivative "$distro")"
        if [[ "$mapped" != "$distro" ]]; then
            distro="$mapped"
            supported=true
        fi
    fi

    if [[ "$supported" != true ]]; then
        error "DD Flash does not currently support your distribution."
        echo ""
        print_supported
        exit 1
    fi

    ok "${distro^} detected."
    echo ""

    # Install dependencies
    info "Checking dependencies..."
    case "$distro" in
        arch) install_arch ;;
        fedora) install_fedora ;;
        debian) install_debian ;;
        ubuntu) install_ubuntu ;;
    esac
    echo ""

    # Verify dependencies
    verify_deps "$distro"
    echo ""

    # Build and install
    build_and_install
    echo ""

    # Final message
    ok "DD Flash has been installed successfully."
    echo ""
    echo "Run:"
    echo "    dd-flash"
    echo ""
}

# Detect distribution version
detect_version() {
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        echo "${VERSION_ID:-unknown}"
    else
        echo "unknown"
    fi
}

# Main entry point
main() {
    case "${1:-}" in
        --uninstall)
            uninstall
            ;;
        --check)
            check_deps
            ;;
        *)
            main_install
            ;;
    esac
}

main "$@"
