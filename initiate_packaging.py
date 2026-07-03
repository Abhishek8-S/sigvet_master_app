"""
build_deb.py — Sigvet Assist v1 Debian Package Builder
=======================================================
Run this script from anywhere inside the cloned repo:
    python3 build_deb.py

What it does:
  1. Detects the repo root automatically (no manual path config needed).
  2. Builds a .deb package for sigvet-assist-v1.
  3. Installs the .deb on the device (requires sudo).
  4. Installs a polkit rule so the app can run with root privileges.
  5. Pins the app to the GNOME dash for user 'sigvet'.

Maintainer : Abhishek S <abhishek@sigtuple.com>
"""

import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
APP_NAME    = "sigvet-assist-v1"
VERSION     = "1.0.0"
ARCH        = "amd64"
MAINTAINER  = "Abhishek S <abhishek@sigtuple.com>"
DESCRIPTION = "Sigvet Assist — Production Compute Suite"
APP_ICON    = "icon.png"

# Production device username that will receive the dash pin
DEVICE_USER = "sigvet"

# Automatically resolve the repo root (directory containing this script),
# so the build works regardless of where it is invoked from.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def run(cmd: list, **kwargs):
    """Run a shell command, printing it first. Raises on failure."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def step(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

# ---------------------------------------------------------------------------
# BUILD STEPS
# ---------------------------------------------------------------------------

def clean_build(build_dir: str):
    """Remove previous build artifacts.

    Falls back to 'sudo rm -rf' when the directory is root-owned
    (a previous dpkg-deb --root-owner-group run leaves root-owned files).
    """
    step("Cleaning previous build")
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
        except PermissionError:
            print("  Directory is root-owned — using sudo rm -rf...")
            subprocess.run(["sudo", "rm", "-rf", build_dir], check=True)
    print("  Done.")


def create_structure(base_dir: str) -> None:
    """Create the Debian directory skeleton."""
    step("Creating directory structure")
    dirs = [
        f"{base_dir}/DEBIAN",
        f"{base_dir}/usr/local/bin",
        f"{base_dir}/usr/lib/{APP_NAME}",
        f"{base_dir}/usr/share/applications",
        f"{base_dir}/usr/share/icons/hicolor/48x48/apps",
        f"{base_dir}/usr/share/icons/hicolor/128x128/apps",
        f"{base_dir}/usr/share/icons/hicolor/256x256/apps",
        f"{base_dir}/usr/share/polkit-1/actions",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("  Done.")


def create_control_file(base_dir: str):
    """Write DEBIAN/control."""
    step("Writing DEBIAN/control")
    content = f"""\
Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCH}
Depends: python3 (>= 3.10), python3-venv, python3-pip, fio, stress-ng, memtester, network-manager, libxcb-cursor0, libxcb-xinerama0, libgl1, policykit-1
Maintainer: {MAINTAINER}
Description: {DESCRIPTION}
 A production-grade compute benchmarking suite built with Python and PyQt6.
 Includes modules for CPU, Disk I/O, Network, Wi-Fi, and Stress testing.
"""
    with open(f"{base_dir}/DEBIAN/control", "w") as f:
        f.write(content)
    print("  Done.")


def create_postinst(base_dir: str):
    """
    Write DEBIAN/postinst — runs after dpkg installs the package.
    Responsibilities:
      - Create Python venv and install pip dependencies.
      - Set correct file permissions.
      - Pin app to GNOME dash for DEVICE_USER.
      - Update icon cache.
    """
    step("Writing DEBIAN/postinst")
    content = f"""\
#!/bin/bash
set -e

INSTALL_DIR="/usr/lib/{APP_NAME}"
VENV_DIR="$INSTALL_DIR/.venv"
DEVICE_USER="{DEVICE_USER}"

echo ""
echo "=============================================="
echo "  Configuring {APP_NAME} v{VERSION}"
echo "=============================================="

# ── 1. Create virtual environment ──────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/5] Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "[1/5] Virtual environment already exists — skipping."
fi

# ── 2. Install Python dependencies ─────────────────────────────────────────
echo "[2/5] Installing Python dependencies..."
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet
    echo "      Dependencies installed."
else
    echo "      WARNING: requirements.txt not found — skipping pip install."
fi

# ── 3. Set file permissions ─────────────────────────────────────────────────
echo "[3/5] Setting permissions..."
chmod -R 755 "$INSTALL_DIR"
chmod +x "/usr/local/bin/{APP_NAME}"

# ── 4. Update icon cache ────────────────────────────────────────────────────
echo "[4/5] Updating icon cache..."
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor &>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications &>/dev/null || true
fi

# ── 5. Pin to GNOME dash for {DEVICE_USER} ────────────────────────────────
echo "[5/5] Pinning app to GNOME dash for user '$DEVICE_USER'..."
if id "$DEVICE_USER" &>/dev/null; then
    USER_HOME=$(eval echo "~$DEVICE_USER")
    DCONF_DB="$USER_HOME/.config/dconf/user"

    # Run gsettings as DEVICE_USER using sudo
    sudo -u "$DEVICE_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $DEVICE_USER)/bus" \\
        gsettings set org.gnome.shell favorite-apps \\
        "$(sudo -u "$DEVICE_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $DEVICE_USER)/bus" \\
            gsettings get org.gnome.shell favorite-apps 2>/dev/null \\
            | sed "s/]$/, '{APP_NAME}.desktop']/; s/\\[, /[/")" 2>/dev/null || \\
    echo "      Note: Could not pin to dash automatically (session may not be active). Run manually:"
    echo "      gsettings set org.gnome.shell favorite-apps \\$(gsettings get org.gnome.shell favorite-apps | sed \"s/]$/, '{APP_NAME}.desktop']/; s/\\[, /[/\")"
else
    echo "      WARNING: User '$DEVICE_USER' not found — skipping dash pin."
fi

echo ""
echo "  Installation complete!"
echo "  Launch: {APP_NAME}"
echo "  Or find '{APP_NAME}' in the application menu."
echo "=============================================="
exit 0
"""
    path = f"{base_dir}/DEBIAN/postinst"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    print("  Done.")


def create_prerm(base_dir: str):
    """Write DEBIAN/prerm — clean up venv and dash pin before removal."""
    step("Writing DEBIAN/prerm")
    content = f"""\
#!/bin/bash
set -e

DEVICE_USER="{DEVICE_USER}"

echo "Removing {APP_NAME}..."

# Remove from GNOME dash
if id "$DEVICE_USER" &>/dev/null; then
    sudo -u "$DEVICE_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $DEVICE_USER)/bus" \\
        gsettings set org.gnome.shell favorite-apps \\
        "$(sudo -u "$DEVICE_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $DEVICE_USER)/bus" \\
            gsettings get org.gnome.shell favorite-apps 2>/dev/null \\
            | sed "s/, '{APP_NAME}.desktop'//g; s/'{APP_NAME}.desktop', //g; s/'{APP_NAME}.desktop'//g")" 2>/dev/null || true
fi

exit 0
"""
    path = f"{base_dir}/DEBIAN/prerm"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    print("  Done.")


def create_polkit_policy(base_dir: str):
    """
    Install a polkit action so the app can execute privileged operations
    without a password prompt when running as user 'sigvet'.
    """
    step("Writing polkit policy (root permissions)")
    policy_id = f"com.sigtuple.{APP_NAME.replace('-', '')}"
    content = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
  "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
  "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">

<policyconfig>

  <vendor>Sigtuple Technologies</vendor>
  <vendor_url>https://www.sigtuple.com</vendor_url>

  <action id="{policy_id}.run">
    <description>Run {APP_NAME} with elevated privileges</description>
    <message>Authentication is required to run {APP_NAME}</message>
    <defaults>
      <!-- No password required for any active session user -->
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/local/bin/{APP_NAME}</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>

</policyconfig>
"""
    path = f"{base_dir}/usr/share/polkit-1/actions/{policy_id}.policy"
    with open(path, "w") as f:
        f.write(content)
    print("  Done.")


def copy_files(base_dir: str):
    """Copy source code and assets from the repo into the package."""
    step("Copying source files")
    dest = f"{base_dir}/usr/lib/{APP_NAME}"

    folders = ["config", "core", "display", "tests", "utils"]
    for folder in folders:
        src = os.path.join(REPO_ROOT, folder)
        if os.path.exists(src):
            shutil.copytree(src, f"{dest}/{folder}")
            print(f"  Copied folder: {folder}/")
        else:
            print(f"  WARNING: folder '{folder}' not found — skipping.")

    files = ["main.py", "requirements.txt", "config.yaml", APP_ICON]
    for file in files:
        src = os.path.join(REPO_ROOT, file)
        if os.path.exists(src):
            shutil.copy(src, f"{dest}/{file}")
            print(f"  Copied file:   {file}")
        else:
            print(f"  WARNING: file '{file}' not found — skipping.")

    # Copy icon to all hicolor sizes
    icon_src = os.path.join(REPO_ROOT, APP_ICON)
    if os.path.exists(icon_src):
        for size in ["48x48", "128x128", "256x256"]:
            icon_dest = f"{base_dir}/usr/share/icons/hicolor/{size}/apps/{APP_NAME}.png"
            shutil.copy(icon_src, icon_dest)
        print(f"  Copied icon to hicolor sizes.")
    else:
        print(f"  WARNING: {APP_ICON} not found — app menu icon will be missing.")


def create_launcher(base_dir: str):
    """
    Create the /usr/local/bin launcher script.
    Uses pkexec so the app acquires root privileges via the installed polkit policy.
    """
    step("Writing launcher script")
    content = f"""\
#!/bin/bash
# {APP_NAME} launcher
# Runs the app with root privileges via polkit (no password needed for active sessions).
export DISPLAY="${{DISPLAY:-:0}}"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
exec pkexec env DISPLAY="${{DISPLAY}}" XAUTHORITY="${{XAUTHORITY:-$HOME/.Xauthority}}" XDG_RUNTIME_DIR="${{XDG_RUNTIME_DIR}}" \\
    /usr/lib/{APP_NAME}/.venv/bin/python3 /usr/lib/{APP_NAME}/main.py "$@"
"""
    path = f"{base_dir}/usr/local/bin/{APP_NAME}"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    print("  Done.")


def create_desktop_entry(base_dir: str):
    """Create the .desktop file for the application menu."""
    step("Writing .desktop entry")
    content = f"""\
[Desktop Entry]
Version=1.0
Name=Sigvet Assist v1
GenericName=Compute Suite
Comment=Sigvet Production Compute Suite
Exec={APP_NAME}
Icon={APP_NAME}
Terminal=false
Type=Application
Categories=System;Utility;
StartupNotify=true
Keywords=sigvet;benchmark;compute;hardware;
"""
    with open(f"{base_dir}/usr/share/applications/{APP_NAME}.desktop", "w") as f:
        f.write(content)
    print("  Done.")


def build_package(build_dir: str, base_dir: str) -> str:
    """Run dpkg-deb to produce the final .deb file."""
    step("Building .deb package")
    deb_path = os.path.join(build_dir, f"{APP_NAME}_{VERSION}_{ARCH}.deb")
    try:
        run(["dpkg-deb", "--build", "--root-owner-group", base_dir, deb_path])
        print(f"\n  ✓ Package built: {deb_path}")
        return deb_path
    except subprocess.CalledProcessError:
        print("\n  ✗ ERROR: dpkg-deb failed.")
        sys.exit(1)
    except FileNotFoundError:
        print("\n  ✗ ERROR: 'dpkg-deb' not found. Install it with: sudo apt install dpkg")
        sys.exit(1)


def install_package(deb_path: str):
    """Install the .deb on the current device using sudo apt install."""
    step("Installing .deb on device")
    if not os.path.exists(deb_path):
        print(f"  ✗ ERROR: {deb_path} not found.")
        sys.exit(1)
    try:
        # apt install handles dependencies automatically
        run(["sudo", "apt", "install", "-y", deb_path])
        print(f"\n  ✓ {APP_NAME} installed successfully.")
    except subprocess.CalledProcessError:
        print("\n  ✗ ERROR: Installation failed. Check the output above.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   Sigvet Assist v1 — Debian Package Builder              ║
║   Maintainer : Abhishek S <abhishek@sigtuple.com>        ║
║   App        : {APP_NAME:<44}║
║   Version    : {VERSION:<44}║
║   Repo Root  : {REPO_ROOT:<44}║
╚══════════════════════════════════════════════════════════╝
""")

    BUILD_DIR = os.path.join(REPO_ROOT, "build")
    BASE_DIR  = os.path.join(BUILD_DIR, f"{APP_NAME}_{VERSION}_{ARCH}")

    # Change to repo root so all relative paths resolve correctly
    os.chdir(REPO_ROOT)

    clean_build(BUILD_DIR)
    create_structure(BASE_DIR)
    create_control_file(BASE_DIR)
    create_postinst(BASE_DIR)
    create_prerm(BASE_DIR)
    create_polkit_policy(BASE_DIR)
    copy_files(BASE_DIR)
    create_launcher(BASE_DIR)
    create_desktop_entry(BASE_DIR)

    deb_file = build_package(BUILD_DIR, BASE_DIR)
    install_package(deb_file)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║   ✓  All done!                                           ║
║                                                          ║
║   The app has been installed and should appear in the    ║
║   application menu as "Sigvet Assist v1".                ║
║                                                          ║
║   If the dash pin didn't apply automatically (user       ║
║   session was not active during install), log in as      ║
║   '{DEVICE_USER}' and run:                                      ║
║                                                          ║
║   gsettings set org.gnome.shell favorite-apps            ║
║     "$(gsettings get org.gnome.shell favorite-apps |     ║
║       sed \"s/]$/, '{APP_NAME}.desktop']/\")"           ║
╚══════════════════════════════════════════════════════════╝
""")