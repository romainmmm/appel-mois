"""Desktop launcher: runs the Streamlit server in the background and shows it
in a native window (no browser chrome) via pywebview.

Double-click `lancer.bat` (or the desktop shortcut) to start it.
"""

import os
import socket
import subprocess
import sys
import time

import webview

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8520
URL = f"http://localhost:{PORT}"


def _is_up(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _start_streamlit() -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", os.path.join(HERE, "app.py"),
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=HERE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    proc = None
    if not _is_up(PORT):
        proc = _start_streamlit()
        # Wait up to ~30s for the server to come up
        for _ in range(60):
            if _is_up(PORT):
                break
            time.sleep(0.5)

    webview.create_window(
        "Répartition des ménages — Motel Panoramique",
        URL,
        width=1280,
        height=860,
    )
    try:
        webview.start()
    finally:
        if proc is not None:
            proc.terminate()


if __name__ == "__main__":
    main()
