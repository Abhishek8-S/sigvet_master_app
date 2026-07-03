import os
import shutil
import subprocess
import sys

# --- CONFIGURATION ---
APP_NAME = "sigvet-assist"
VERSION = "1.0.0"
ARCH = "amd64"
MAINTAINER = "Abhishek S <abhishek@sigtuple.com>"
DESCRIPTION = "Sigvet Assistence Tool"
# Icon is in project root based on user upload
APP_ICON = "icon.png" 

def clean_build():
    """Removes previous build artifacts."""
    if os.path.exists("build"):
        shutil.rmtree("build")
    print("Cleaned previous build.")

def create_structure():
    """Creates the Debian directory structure."""
    base_dir = f"build/{APP_NAME}_{VERSION}_{ARCH}"
    
    dirs = [
        f"{base_dir}/DEBIAN",
        f"{base_dir}/usr/local/bin",
        f"{base_dir}/usr/lib/{APP_NAME}",
        f"{base_dir}/usr/share/applications",
        f"{base_dir}/usr/share/icons/hicolor/48x48/apps",
        f"{base_dir}/usr/share/icons/hicolor/128x128/apps",
        f"{base_dir}/usr/share/icons/hicolor/256x256/apps",
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    return base_dir

def create_control_file(base_dir):
    """Creates the DEBIAN/control metadata file."""
    # Added libxcb-cursor0 and libxcb-xinerama0 for Qt6 compatibility
    content = f"""Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCH}
Depends: python3 (>= 3.10), python3-venv, python3-pip, fio, stress-ng, memtester, network-manager, libxcb-cursor0, libxcb-xinerama0, libgl1
Maintainer: {MAINTAINER}
Description: {DESCRIPTION}
 A comprehensive system benchmarking tool built with Python and PyQt6.
 Includes modules for CPU, Disk IO, Network, WiFi, and Stress testing.
"""
    with open(f"{base_dir}/DEBIAN/control", "w") as f:
        f.write(content)

def create_postinst(base_dir):
    """Creates the post-installation script to setup venv."""
    content = f"""#!/bin/bash
set -e

# Define installation path
INSTALL_DIR="/usr/lib/{APP_NAME}"
VENV_DIR="$INSTALL_DIR/.venv"

echo "Configuring {APP_NAME}..."

# 1. Create Virtual Environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Install dependencies
echo "Installing Python dependencies..."
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
fi

# 3. Set permissions
chmod -R 755 "$INSTALL_DIR"
chmod +x "/usr/local/bin/{APP_NAME}"

echo "{APP_NAME} installation complete."
exit 0
"""
    path = f"{base_dir}/DEBIAN/postinst"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)

def copy_files(base_dir):
    """Copies source code and assets."""
    dest = f"{base_dir}/usr/lib/{APP_NAME}"
    
    # Folders to copy
    folders = ["config", "core", "display", "tests", "utils", "assets"]
    for folder in folders:
        if os.path.exists(folder):
            shutil.copytree(folder, f"{dest}/{folder}")
    
    # Files to copy
    files = ["main.py", "requirements.txt", "icon.png", "config.yaml"] # Added config.yaml and icon.png here
    for file in files:
        if os.path.exists(file):
            shutil.copy(file, f"{dest}/{file}")

    # Copy Icon for System Menu (multiple sizes for sharp display)
    if os.path.exists(APP_ICON):
        for size in ["48x48", "128x128", "256x256"]:
            icon_dest = f"{base_dir}/usr/share/icons/hicolor/{size}/apps/{APP_NAME}.png"
            shutil.copy(APP_ICON, icon_dest)
    else:
        print(f"Warning: {APP_ICON} not found. App menu icon will be missing.")

def create_launcher(base_dir):
    """Creates the executable script in /usr/local/bin."""
    content = f"""#!/bin/bash
export DISPLAY="${{DISPLAY:-:0}}"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
cd /usr/lib/{APP_NAME}
./.venv/bin/python3 main.py "$@"
"""
    path = f"{base_dir}/usr/local/bin/{APP_NAME}"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)

def create_desktop_entry(base_dir):
    """Creates the .desktop file for the system menu."""
    content = f"""[Desktop Entry]
Name=Sigvet Assistance
GenericName=Compute Tester
Comment=Sigvet Production Compute Suite
Exec={APP_NAME}
Icon={APP_NAME}
Terminal=false
Type=Application
Categories=System;Utility;
StartupNotify=true
"""
    with open(f"{base_dir}/usr/share/applications/{APP_NAME}.desktop", "w") as f:
        f.write(content)

def build_package(base_dir):
    """Runs dpkg-deb to build the final package."""
    print(f"Building .deb package from {base_dir}...")
    try:
        subprocess.run(["dpkg-deb", "--build", base_dir], check=True)
        print(f"\nBuild successful: {base_dir}.deb")
    except subprocess.CalledProcessError:
        print("\nError: dpkg-deb failed. Make sure you have 'dpkg' installed.")
    except FileNotFoundError:
        print("\nError: 'dpkg-deb' command not found. Are you on Debian/Ubuntu?")

if __name__ == "__main__":
    print("--- Starting Debian Package Build ---")
    clean_build()
    base = create_structure()
    create_control_file(base)
    create_postinst(base)
    copy_files(base)
    create_launcher(base)
    create_desktop_entry(base)
    build_package(base)
    print("--- Done ---")