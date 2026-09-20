"""System startup configuration manager for Desktop Agent (Windows, macOS, Linux)."""

import os
from pathlib import Path
import platform
import sys

AGENT_DIR = Path(__file__).resolve().parent
AGENT_PY = AGENT_DIR / "agent.py"
APP_NAME = "TrackerDesktopAgent"


def _get_python_executable() -> str:
    """Find pythonw.exe (windowless background) on Windows, or sys.executable."""
    if platform.system().lower() == "windows":
        py_dir = Path(sys.executable).parent
        pyw = py_dir / "pythonw.exe"
        if pyw.exists():
            return str(pyw)
    return sys.executable


# ==============================================================================
# WINDOWS STARTUP (Startup Folder + Registry fallback)
# ==============================================================================

def _get_windows_startup_path() -> Path:
    """Return path to user's Windows Startup folder."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _install_windows() -> bool:
    """Create a silent launcher script in the user's Startup folder."""
    startup_dir = _get_windows_startup_path()
    startup_dir.mkdir(parents=True, exist_ok=True)

    py_exe = _get_python_executable()
    vbs_file = startup_dir / f"{APP_NAME}.vbs"

    # Silent VBScript launcher (prevents terminal pop-up on login)
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{py_exe}"" ""{AGENT_PY}""", 0, False
'''
    try:
        with open(vbs_file, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print(f"[Startup] Windows startup script created: {vbs_file}")
        return True
    except Exception as exc:
        print(f"[Startup] Failed to write startup script: {exc}", file=sys.stderr)
        return False


def _uninstall_windows() -> bool:
    """Remove launcher script from Startup folder."""
    startup_dir = _get_windows_startup_path()
    vbs_file = startup_dir / f"{APP_NAME}.vbs"
    bat_file = startup_dir / f"{APP_NAME}.bat"

    removed = False
    for f in (vbs_file, bat_file):
        if f.exists():
            try:
                f.unlink()
                print(f"[Startup] Removed startup file: {f}")
                removed = True
            except Exception as exc:
                print(f"[Startup] Failed to delete {f}: {exc}", file=sys.stderr)
    return removed


def _is_installed_windows() -> bool:
    startup_dir = _get_windows_startup_path()
    return (startup_dir / f"{APP_NAME}.vbs").exists() or (startup_dir / f"{APP_NAME}.bat").exists()


# ==============================================================================
# MACOS STARTUP (LaunchAgents)
# ==============================================================================

def _get_macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.tracker.{APP_NAME.lower()}.plist"


def _install_macos() -> bool:
    plist_path = _get_macos_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tracker.{APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{AGENT_PY}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
    try:
        with open(plist_path, "w", encoding="utf-8") as f:
            f.write(plist_content)
        print(f"[Startup] macOS LaunchAgent installed: {plist_path}")
        return True
    except Exception as exc:
        print(f"[Startup] Failed to install macOS LaunchAgent: {exc}", file=sys.stderr)
        return False


def _uninstall_macos() -> bool:
    plist_path = _get_macos_plist_path()
    if plist_path.exists():
        plist_path.unlink()
        print(f"[Startup] Removed macOS LaunchAgent: {plist_path}")
        return True
    return False


# ==============================================================================
# CROSS-PLATFORM INTERFACE
# ==============================================================================

def install_startup() -> bool:
    """Configure agent to automatically start on user log in."""
    system = platform.system().lower()
    if "windows" in system:
        return _install_windows()
    elif "darwin" in system:
        return _install_macos()
    else:
        print("[Startup] Linux: Please configure via systemd user service or crontab (@reboot).")
        return False


def uninstall_startup() -> bool:
    """Remove agent from automatic system startup."""
    system = platform.system().lower()
    if "windows" in system:
        return _uninstall_windows()
    elif "darwin" in system:
        return _uninstall_macos()
    else:
        return False


def is_startup_installed() -> bool:
    """Check if startup service/script is currently active."""
    system = platform.system().lower()
    if "windows" in system:
        return _is_installed_windows()
    elif "darwin" in system:
        return _get_macos_plist_path().exists()
    return False
