%global pypi_name dd-flash

Name:           dd-flash
Version:        1.0.0
Release:        1%{?dist}
Summary:        Modern GTK4 GUI for safely writing ISO/IMG images to USB drives

License:        GPL-3.0-or-later
URL:            https://github.com/gerchann/dd-flash
Source0:        %{pypi_name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  meson
BuildRequires:  ninja-build

Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       polkit
Requires:       coreutils
Requires:       util-linux

%description
DD Flash is a modern, minimalist GTK4/Libadwaita application for safely
writing ISO and IMG disk images to USB drives.

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install

# Install data files
mkdir -p %{buildroot}%{_datadir}/applications
cp data/com.gerchan.DDFlash.desktop %{buildroot}%{_datadir}/applications/

mkdir -p %{buildroot}%{_datadir}/metainfo
cp data/com.gerchan.DDFlash.metainfo.xml %{buildroot}%{_datadir}/metainfo/

mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp data/icons/com.gerchan.DDFlash.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

mkdir -p %{buildroot}%{_datadir}/polkit-1/actions
cp data/com.gerchan.DDFlash.policy %{buildroot}%{_datadir}/polkit-1/actions/

%files
%{python3_sitelib}/dd_flash/
%{_bindir}/dd-flash
%{_datadir}/applications/com.gerchan.DDFlash.desktop
%{_datadir}/metainfo/com.gerchan.DDFlash.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/com.gerchan.DDFlash.svg
%{_datadir}/polkit-1/actions/com.gerchan.DDFlash.policy

%changelog
* Mon Sep 29 2026 gerchann - 1.0.0-1
- Initial release
