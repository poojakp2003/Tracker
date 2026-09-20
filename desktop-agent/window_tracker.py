"""Cross-platform active window and application detection.

Supported platforms:
- Windows (via Win32 ctypes & psutil, or pygetwindow)
- macOS (via osascript / AppKit)
- Linux (via xdotool / wmctrl)
"""

from dataclasses import dataclass
import os
import platform
import subprocess
import sys


@dataclass
class WindowInfo:
    """Represents the currently active window and its application."""

    app_name: str
    window_title: str
    process_id: int | None = None


# Friendly name mapping for common executable names
FRIENDLY_APP_NAMES: dict[str, str] = {
    "chrome.exe": "Google Chrome",
    "code.exe": "VS Code",
    "msedge.exe": "Microsoft Edge",
    "firefox.exe": "Firefox",
    "brave.exe": "Brave",
    "slack.exe": "Slack",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "notepad.exe": "Notepad",
    "explorer.exe": "File Explorer",
    "windowsterminal.exe": "Windows Terminal",
    "cmd.exe": "Command Prompt",
    "powershell.exe": "PowerShell",
    "devenv.exe": "Visual Studio",
    "pycharm64.exe": "PyCharm",
    "idea64.exe": "IntelliJ IDEA",
    "postman.exe": "Postman",
    "zoom.exe": "Zoom",
    "teams.exe": "Microsoft Teams",
}


def _clean_app_name(raw_name: str) -> str:
    """Normalize process name into human-readable application name."""
    if not raw_name:
        return "Unknown"
    lower = raw_name.lower().strip()
    if lower in FRIENDLY_APP_NAMES:
        return FRIENDLY_APP_NAMES[lower]
    # Strip extension if .exe
    if lower.endswith(".exe"):
        name = raw_name[:-4]
        # Capitalize nicely if all lowercase
        return name.capitalize() if name.islower() else name
    return raw_name


def _get_active_window_windows() -> WindowInfo | None:
    """Retrieve active window on Windows using native ctypes & psutil."""
    try:
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        # 1. Window Title
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
        else:
            title = ""

        # 2. Process ID
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = pid.value

        # 3. Process Name via psutil
        raw_app_name = ""
        try:
            import psutil

            proc = psutil.Process(process_id)
            raw_app_name = proc.name()
        except Exception:
            # Fallback if psutil is not available
            raw_app_name = title.split(" - ")[-1] if " - " in title else "Windows App"

        app_name = _clean_app_name(raw_app_name)
        return WindowInfo(app_name=app_name, window_title=title or app_name, process_id=process_id)

    except Exception as exc:
        return None


def _get_active_window_macos() -> WindowInfo | None:
    """Retrieve active window on macOS using osascript (AppleScript)."""
    script = """
    global frontApp, frontAppName, windowTitle
    set windowTitle to ""
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        set frontAppName to name of frontApp
        tell frontApp
            if (count of windows) > 0 then
                set windowTitle to name of first window
            end if
        end tell
    end tell
    return frontAppName & "|||" & windowTitle
    """
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
        if proc.returncode == 0 and proc.stdout.strip():
            parts = proc.stdout.strip().split("|||")
            app_name = parts[0].strip() or "macOS App"
            window_title = parts[1].strip() if len(parts) > 1 else app_name
            return WindowInfo(app_name=app_name, window_title=window_title or app_name)
    except Exception:
        pass
    return None


def _get_active_window_linux() -> WindowInfo | None:
    """Retrieve active window on Linux using xdotool."""
    try:
        # Get active window ID
        wid_proc = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1.0)
        if wid_proc.returncode != 0:
            return None
        wid = wid_proc.stdout.strip()

        # Get window title
        name_proc = subprocess.run(["xdotool", "getwindowname", wid], capture_output=True, text=True, timeout=1.0)
        title = name_proc.stdout.strip() if name_proc.returncode == 0 else ""

        # Get process PID
        pid_proc = subprocess.run(["xdotool", "getwindowpid", wid], capture_output=True, text=True, timeout=1.0)
        pid = int(pid_proc.stdout.strip()) if pid_proc.returncode == 0 and pid_proc.stdout.strip().isdigit() else None

        app_name = "Linux App"
        if pid:
            try:
                import psutil

                app_name = _clean_app_name(psutil.Process(pid).name())
            except Exception:
                pass

        return WindowInfo(app_name=app_name, window_title=title or app_name, process_id=pid)
    except Exception:
        return None


def get_active_window() -> WindowInfo | None:
    """OS-agnostic entry point to detect the currently focused desktop window."""
    current_os = platform.system().lower()
    if "windows" in current_os:
        return _get_active_window_windows()
    elif "darwin" in current_os:
        return _get_active_window_macos()
    else:
        return _get_active_window_linux()
