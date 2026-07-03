"""
initiate_packaging.py — Sigvet Assist v1 Debian Package Builder
================================================================
Run from anywhere inside the cloned repo:
    python3 initiate_packaging.py

What it does:
  1. Detects the repo root automatically.
  2. Builds a .deb package for sigvet-assist-v1.
  3. Installs the .deb (no password prompts — script self-elevates to root).
  4. Installs a polkit rule so the app can run with root privileges.
  5. Pins the app to the GNOME dash for the 'sigvet' user.

Maintainer : Abhishek S <abhishek@sigtuple.com>
"""

import base64
import os
import shutil
import subprocess
import sys
import textwrap

# ---------------------------------------------------------------------------
# SELF-ELEVATION — re-exec with sudo if not already root so the entire
# script (including 'apt install') runs without mid-flow password prompts.
# ---------------------------------------------------------------------------
if os.geteuid() != 0:
    print("  Not running as root — re-launching with sudo...")
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
APP_NAME    = "sigvet-assist-v1"
VERSION     = "1.0.0"
ARCH        = "amd64"
MAINTAINER  = "Abhishek S <abhishek@sigtuple.com>"
DESCRIPTION = "Sigvet Assist — Production Compute Suite"
APP_ICON    = "icon.png"
DEVICE_USER = "sigvet"

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def run(cmd: list, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def step(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def _b64(code: str) -> str:
    """Base64-encode a Python snippet for safe embedding in bash scripts."""
    return base64.b64encode(textwrap.dedent(code).strip().encode()).decode()


# ---------------------------------------------------------------------------
# BUILD STEPS
# ---------------------------------------------------------------------------

def clean_build(build_dir: str):
    step("Cleaning previous build")
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
        except PermissionError:
            print("  Directory is root-owned — using rm -rf...")
            subprocess.run(["rm", "-rf", build_dir], check=True)
    print("  Done.")


def create_structure(base_dir: str):
    step("Creating directory structure")
    for d in [
        f"{base_dir}/DEBIAN",
        f"{base_dir}/usr/local/bin",
        f"{base_dir}/usr/lib/{APP_NAME}",
        f"{base_dir}/usr/share/applications",
        f"{base_dir}/usr/share/icons/hicolor/48x48/apps",
        f"{base_dir}/usr/share/icons/hicolor/128x128/apps",
        f"{base_dir}/usr/share/icons/hicolor/256x256/apps",
        f"{base_dir}/usr/share/polkit-1/actions",
        f"{base_dir}/etc/sudoers.d",
    ]:
        os.makedirs(d, exist_ok=True)
    print("  Done.")


def create_control_file(base_dir: str):
    step("Writing DEBIAN/control")
    with open(f"{base_dir}/DEBIAN/control", "w") as f:
        f.write("\n".join([
            f"Package: {APP_NAME}",
            f"Version: {VERSION}",
            "Section: utils",
            "Priority: optional",
            f"Architecture: {ARCH}",
            ("Depends: python3 (>= 3.10), python3-venv, python3-pip, fio, stress-ng, "
             "memtester, network-manager, libxcb-cursor0, libxcb-xinerama0, libgl1, policykit-1"),
            f"Maintainer: {MAINTAINER}",
            f"Description: {DESCRIPTION}",
            " A production-grade compute benchmarking suite built with Python and PyQt6.",
            " Includes modules for CPU, Disk I/O, Network, Wi-Fi, and Stress testing.",
        ]) + "\n")
    print("  Done.")


def create_postinst(base_dir: str):
    """
    Write DEBIAN/postinst.

    Key design:
    - postinst runs as root (dpkg). We use 'su - USER -c' to run gsettings
      as the desktop user. Root → user via su never prompts for a password.
    - The Python helper that edits the GNOME favorites list is embedded as a
      base64-encoded string and decoded at runtime with 'base64 -d'. This
      avoids all heredoc-inside-heredoc quoting nightmares.
    """
    step("Writing DEBIAN/postinst")

    # Python snippet: appends the app desktop entry to GNOME favorites.
    # Receives: sys.argv[1] = current GVariant string, sys.argv[2] = entry name.
    b64_append = _b64(r"""
        import ast, sys
        current = sys.argv[1]
        entry   = sys.argv[2]
        try:
            lst = ast.literal_eval(current)
            if not isinstance(lst, list):
                lst = []
        except Exception:
            lst = []
        if entry not in lst:
            lst.append(entry)
        print("[" + ", ".join("'" + e + "'" for e in lst) + "]")
    """)

    # Note: We use plain string concatenation here (no f-string) for the
    # sections that contain bash ${VAR} syntax to prevent Python from
    # interpreting those braces. Only safe APP_NAME / VERSION / DEVICE_USER
    # values are interpolated with f-string.
    script = (
        "#!/bin/bash\n"
        "set -e\n"
        "\n"
        f'INSTALL_DIR="/usr/lib/{APP_NAME}"\n'
        'VENV_DIR="$INSTALL_DIR/.venv"\n'
        f'DEVICE_USER="{DEVICE_USER}"\n'
        "\n"
        'echo ""\n'
        'echo "=============================================="\n'
        f'echo "  Configuring {APP_NAME} v{VERSION}"\n'
        'echo "=============================================="\n'
        "\n"
        "# 1. Create virtual environment\n"
        'if [ ! -d "$VENV_DIR" ]; then\n'
        '    echo "[1/5] Creating Python virtual environment..."\n'
        '    python3 -m venv "$VENV_DIR"\n'
        "else\n"
        '    echo "[1/5] Virtual environment already exists -- skipping."\n'
        "fi\n"
        "\n"
        "# 2. Install Python dependencies\n"
        'echo "[2/5] Installing Python dependencies..."\n'
        'if [ -f "$INSTALL_DIR/requirements.txt" ]; then\n'
        '    "$VENV_DIR/bin/pip" install --upgrade pip --quiet\n'
        '    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet\n'
        '    echo "      Dependencies installed."\n'
        "else\n"
        '    echo "      WARNING: requirements.txt not found -- skipping."\n'
        "fi\n"
        "\n"
        "# 3. Set file permissions\n"
        'echo "[3/5] Setting permissions..."\n'
        'chmod -R 755 "$INSTALL_DIR"\n'
        f'chmod +x "/usr/local/bin/{APP_NAME}"\n'
        "\n"
        "# 4. Update icon cache\n"
        'echo "[4/5] Updating icon cache..."\n'
        "gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true\n"
        "update-desktop-database /usr/share/applications >/dev/null 2>&1 || true\n"
        "\n"
        "# 5. Pin to GNOME dash\n"
        "# postinst runs as root; 'su - USER -c' never asks for a password.\n"
        'echo "[5/5] Pinning app to GNOME dash for user \'$DEVICE_USER\'..."\n'
        'if id "$DEVICE_USER" >/dev/null 2>&1; then\n'
        '    DEVICE_UID=$(id -u "$DEVICE_USER")\n'
        '    DBUS="unix:path=/run/user/${DEVICE_UID}/bus"\n'
        f'    ENTRY="{APP_NAME}.desktop"\n'
        "\n"
        '    CURRENT=$(su - "$DEVICE_USER" -c \\\n'
        '        "DBUS_SESSION_BUS_ADDRESS=$DBUS gsettings get org.gnome.shell favorite-apps" \\\n'
        '        2>/dev/null) || CURRENT=""\n'
        "\n"
        '    if [ -n "$CURRENT" ]; then\n'
        '        TMPPY=$(mktemp /tmp/gnome_favs_XXXXXX.py)\n'
        # Embed base64 — safe to use in any bash context, no quoting issues
        f'        echo "{b64_append}" | base64 -d > "$TMPPY"\n'
        '        NEW=$(python3 "$TMPPY" "$CURRENT" "$ENTRY") || NEW=""\n'
        '        rm -f "$TMPPY"\n'
        "\n"
        '        if [ -n "$NEW" ]; then\n'
        '            su - "$DEVICE_USER" -c \\\n'
        "                \"DBUS_SESSION_BUS_ADDRESS=\\$DBUS gsettings set org.gnome.shell favorite-apps '\\$NEW'\" \\\n"
        '                2>/dev/null \\\n'
        "                && echo \"      Pinned '\\$ENTRY' to GNOME dash.\" \\\n"
        '                || echo "      Note: Could not pin (session may not be active)."\n'
        '        fi\n'
        '    else\n'
        '        echo "      Note: GNOME session not active -- skipping dash pin."\n'
        '    fi\n'
        "else\n"
        '    echo "      WARNING: User \'$DEVICE_USER\' not found -- skipping dash pin."\n'
        "fi\n"
        "\n"
        'echo ""\n'
        'echo "  Installation complete!"\n'
        f'echo "  Launch: {APP_NAME}"\n'
        f"echo \"  Or find '{APP_NAME}' in the application menu.\"\n"
        'echo "=============================================="\n'
        "exit 0\n"
    )

    path = f"{base_dir}/DEBIAN/postinst"
    with open(path, "w", newline="\n") as f:
        f.write(script)
    os.chmod(path, 0o755)
    print("  Done.")


def create_prerm(base_dir: str):
    """Write DEBIAN/prerm."""
    step("Writing DEBIAN/prerm")

    b64_remove = _b64(r"""
        import ast, sys
        current = sys.argv[1]
        entry   = sys.argv[2]
        try:
            lst = ast.literal_eval(current)
            if not isinstance(lst, list):
                lst = []
        except Exception:
            lst = []
        lst = [e for e in lst if e != entry]
        print("[" + ", ".join("'" + e + "'" for e in lst) + "]")
    """)

    script = (
        "#!/bin/bash\n"
        "set -e\n"
        "\n"
        f'DEVICE_USER="{DEVICE_USER}"\n'
        "\n"
        f'echo "Removing {APP_NAME}..."\n'
        "\n"
        'if id "$DEVICE_USER" >/dev/null 2>&1; then\n'
        '    DEVICE_UID=$(id -u "$DEVICE_USER")\n'
        '    DBUS="unix:path=/run/user/${DEVICE_UID}/bus"\n'
        f'    ENTRY="{APP_NAME}.desktop"\n'
        "\n"
        '    CURRENT=$(su - "$DEVICE_USER" -c \\\n'
        '        "DBUS_SESSION_BUS_ADDRESS=$DBUS gsettings get org.gnome.shell favorite-apps" \\\n'
        '        2>/dev/null) || CURRENT=""\n'
        "\n"
        '    if [ -n "$CURRENT" ]; then\n'
        '        TMPPY=$(mktemp /tmp/gnome_favs_XXXXXX.py)\n'
        f'        echo "{b64_remove}" | base64 -d > "$TMPPY"\n'
        '        NEW=$(python3 "$TMPPY" "$CURRENT" "$ENTRY") || NEW=""\n'
        '        rm -f "$TMPPY"\n'
        "\n"
        '        if [ -n "$NEW" ]; then\n'
        '            su - "$DEVICE_USER" -c \\\n'
        "                \"DBUS_SESSION_BUS_ADDRESS=\\$DBUS gsettings set org.gnome.shell favorite-apps '\\$NEW'\" \\\n"
        '                2>/dev/null || true\n'
        '        fi\n'
        '    fi\n'
        "fi\n"
        "\n"
        "exit 0\n"
    )

    path = f"{base_dir}/DEBIAN/prerm"
    with open(path, "w", newline="\n") as f:
        f.write(script)
    os.chmod(path, 0o755)
    print("  Done.")


def create_polkit_policy(base_dir: str):
    step("Writing polkit policy (root permissions)")
    policy_id = f"com.sigtuple.{APP_NAME.replace('-', '')}"
    with open(f"{base_dir}/usr/share/polkit-1/actions/{policy_id}.policy", "w") as f:
        f.write("\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            "<!DOCTYPE policyconfig PUBLIC",
            '  "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"',
            '  "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">',
            "",
            "<policyconfig>",
            "",
            "  <vendor>Sigtuple Technologies</vendor>",
            "  <vendor_url>https://www.sigtuple.com</vendor_url>",
            "",
            f'  <action id="{policy_id}.run">',
            f"    <description>Run {APP_NAME} with elevated privileges</description>",
            f"    <message>Authentication is required to run {APP_NAME}</message>",
            "    <defaults>",
            "      <!-- No password required for any active session user -->",
            "      <allow_any>auth_admin</allow_any>",
            "      <allow_inactive>auth_admin</allow_inactive>",
            "      <allow_active>yes</allow_active>",
            "    </defaults>",
            f'    <annotate key="org.freedesktop.policykit.exec.path">/usr/local/bin/{APP_NAME}</annotate>',
            '    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>',
            "  </action>",
            "",
            "</policyconfig>",
        ]) + "\n")
    print("  Done.")


def copy_files(base_dir: str):
    step("Copying source files")
    dest = f"{base_dir}/usr/lib/{APP_NAME}"

    for folder in ["config", "core", "display", "tests", "utils"]:
        src = os.path.join(REPO_ROOT, folder)
        if os.path.exists(src):
            shutil.copytree(src, f"{dest}/{folder}")
            print(f"  Copied folder: {folder}/")
        else:
            print(f"  WARNING: folder '{folder}' not found — skipping.")

    for file in ["main.py", "requirements.txt", "config.yaml", APP_ICON]:
        src = os.path.join(REPO_ROOT, file)
        if os.path.exists(src):
            shutil.copy(src, f"{dest}/{file}")
            print(f"  Copied file:   {file}")
        else:
            print(f"  WARNING: file '{file}' not found — skipping.")

    icon_src = os.path.join(REPO_ROOT, APP_ICON)
    if os.path.exists(icon_src):
        for size in ["48x48", "128x128", "256x256"]:
            shutil.copy(icon_src, f"{base_dir}/usr/share/icons/hicolor/{size}/apps/{APP_NAME}.png")
        print("  Copied icon to hicolor sizes.")
    else:
        print(f"  WARNING: {APP_ICON} not found — app menu icon will be missing.")

def create_sudoers_rule(base_dir: str):
    """
    Write /etc/sudoers.d/sigvet-assist-v1.

    Grants the DEVICE_USER permission to run the app's python binary with
    root privileges and NO password prompt, ever.
    sudoers.d files must be mode 0440 (readable only by root).
    """
    step("Writing sudoers NOPASSWD rule")
    rule = (
        f"# Allow {DEVICE_USER} to launch {APP_NAME} as root without a password.\n"
        f"{DEVICE_USER} ALL=(root) NOPASSWD: "
        f"/usr/lib/{APP_NAME}/.venv/bin/python3 /usr/lib/{APP_NAME}/main.py\n"
    )
    path = f"{base_dir}/etc/sudoers.d/{APP_NAME}"
    with open(path, "w", newline="\n") as f:
        f.write(rule)
    # sudoers.d files MUST be 0440 or sudo will refuse to load them
    os.chmod(path, 0o440)
    print("  Done.")


def create_launcher(base_dir: str):
    """Write /usr/local/bin launcher. Uses sudo + NOPASSWD sudoers rule — no password dialog."""
    step("Writing launcher script")
    content = (
        "#!/bin/bash\n"
        f"# {APP_NAME} launcher\n"
        "# Elevated via sudo with NOPASSWD rule in /etc/sudoers.d — no password prompt.\n"
        'export DISPLAY="${DISPLAY:-:0}"\n'
        'export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"\n'
        'export XDG_RUNTIME_DIR="/run/user/$(id -u)"\n'
        "exec sudo "
        f"/usr/lib/{APP_NAME}/.venv/bin/python3 "
        f"/usr/lib/{APP_NAME}/main.py "
        '"$@"\n'
    )
    path = f"{base_dir}/usr/local/bin/{APP_NAME}"
    with open(path, "w", newline="\n") as f:
        f.write(content)
    os.chmod(path, 0o755)
    print("  Done.")


def create_desktop_entry(base_dir: str):
    step("Writing .desktop entry")
    with open(f"{base_dir}/usr/share/applications/{APP_NAME}.desktop", "w") as f:
        f.write("\n".join([
            "[Desktop Entry]",
            "Version=1.0",
            "Name=Sigvet Assist v1",
            "GenericName=Compute Suite",
            "Comment=Sigvet Production Compute Suite",
            f"Exec={APP_NAME}",
            f"Icon={APP_NAME}",
            "Terminal=false",
            "Type=Application",
            "Categories=System;Utility;",
            "StartupNotify=true",
            "Keywords=sigvet;benchmark;compute;hardware;",
        ]) + "\n")
    print("  Done.")


def build_package(build_dir: str, base_dir: str) -> str:
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
        print("\n  ✗ ERROR: 'dpkg-deb' not found. Install with: apt install dpkg")
        sys.exit(1)


def install_package(deb_path: str):
    """Install the .deb. Already root (self-elevated above), no sudo needed."""
    step("Installing .deb on device")
    if not os.path.exists(deb_path):
        print(f"  ✗ ERROR: {deb_path} not found.")
        sys.exit(1)
    try:
        run(["apt", "install", "-y", deb_path])
        print(f"\n  ✓ {APP_NAME} installed successfully.")
    except subprocess.CalledProcessError:
        print("\n  ✗ ERROR: Installation failed. Check the output above.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║   Sigvet Assist v1 — Debian Package Builder              ║\n"
        "║   Maintainer : Abhishek S <abhishek@sigtuple.com>        ║\n"
        f"║   App        : {APP_NAME:<44}║\n"
        f"║   Version    : {VERSION:<44}║\n"
        f"║   Repo Root  : {REPO_ROOT:<44}║\n"
        "╚══════════════════════════════════════════════════════════╝\n"
    )

    BUILD_DIR = os.path.join(REPO_ROOT, "build")
    BASE_DIR  = os.path.join(BUILD_DIR, f"{APP_NAME}_{VERSION}_{ARCH}")

    os.chdir(REPO_ROOT)

    clean_build(BUILD_DIR)
    create_structure(BASE_DIR)
    create_control_file(BASE_DIR)
    create_postinst(BASE_DIR)
    create_prerm(BASE_DIR)
    create_polkit_policy(BASE_DIR)
    create_sudoers_rule(BASE_DIR)
    copy_files(BASE_DIR)
    create_launcher(BASE_DIR)
    create_desktop_entry(BASE_DIR)

    deb_file = build_package(BUILD_DIR, BASE_DIR)
    install_package(deb_file)

    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║   ✓  All done!                                           ║\n"
        "║                                                          ║\n"
        "║   The app has been installed and should appear in the    ║\n"
        '║   application menu as "Sigvet Assist v1".                ║\n'
        "╚══════════════════════════════════════════════════════════╝\n"
    )
