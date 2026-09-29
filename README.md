# DD Flash

Modern GTK4/Libadwaita GUI pro bezpečné zapisování `.iso` a `.img` obrazů na USB disky.

## Funkce

- **Moderní rozhraní** — GTK4 + Libadwaita, dark-mode friendly
- **Skutečný progress** — rychlost, ETA, zapsaná data
- **Bezpečnost** — kontrola removable/USB, blokování systémových disků
- **Automatická detekce USB** — obnova seznamu při připojení/odpojení
- **Polkit** — GUI běží jako běžný uživatel, zápis s elevated oprávněmi
- **Zrušení** — bezpečné přerušení s potvrzením

## Instalace

### Arch Linux

```bash
git clone https://github.com/gerchann/dd-flash.git
cd dd-flash
./scripts/install.sh
```

### Fedora

```bash
git clone https://github.com/gerchann/dd-flash.git
cd dd-flash
./scripts/install.sh
```

### Debian / Ubuntu

```bash
git clone https://github.com/gerchann/dd-flash.git
cd dd-flash
./scripts/install.sh
```

`install.sh` automaticky zjistí distribuci a nainstaluje potřebné dependencies.

## Odinstalace

```bash
./scripts/uninstall.sh
```

## Požadavky

- Python 3.10+
- GTK 4.0+
- Libadwaita 1.0+
- PyGObject
- `dd` (coreutils)
- `pkexec` (polkit)
- `lsblk` (util-linux)

## Použití

```bash
# Spuštění
dd-flash

# Nebo přímo
python3 -m dd_flash.main

# S otevřením souboru
dd-flash /path/to/image.iso
```

## Architektura

```
src/dd_flash/
├── main.py            # Vstupní bod aplikace
├── window.py          # Hlavní okno
├── disk_manager.py    # Správa disků (lsblk, validace)
├── flash_manager.py   # Správa dd procesu
├── polkit.py          # Polkit integrace
├── helper.py          # Privilegovaný helper (pkexec)
└── ui/
    ├── file_chooser.py    # Výběr ISO/IMG
    ├── disk_selector.py   # Výběr cílového disku
    ├── progress_view.py   # Zobrazení progressu
    └── dialogs.py         # Dialogy (potvrzení, chyby)
```

## Bezpečnost

DD Flash provádí následující kontroly před zápisem:

1. Zařízení musí být **removable**
2. Zařízení musí být **USB**
3. Zařízení nesmí obsahovat **root filesystem** (`/`)
4. Zařízení nesmí obsahovat **kritické mountpointy** (`/home`, `/boot`, `/usr`, `/var`)
5. Velikost image musí být **≤ velikosti zařízení**
6. Před zápisem se **odmontují** všechny partition

## Licence

GPL-3.0-or-later
