#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and run the Study Planner dashboard.")
    parser.add_argument("--profile", default=os.environ.get("STUDY_PROFILE", "default"))
    parser.add_argument("--codex-home", default=str(DEFAULT_CODEX_HOME))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--static-port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_STATIC_PORT", "8787")))
    parser.add_argument("--api-port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_API_PORT", "8790")))
    parser.add_argument("--open", action="store_true", help="Open the dashboard in the default browser.")
    parser.add_argument("--no-static", action="store_true", help="Only generate HTML and start the write API.")
    parser.add_argument("--no-api", action="store_true", help="Only generate HTML and start the static dashboard.")
    return parser.parse_args()


def wait_url(url: str, seconds: float = 5.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=0.8) as response:
                return 200 <= response.status < 500
        except Exception:
            time.sleep(0.2)
    return False


def start_process(args: list[str], cwd: Path | None = None) -> subprocess.Popen:
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def main() -> None:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser()
    out_dir = Path(args.out_dir).expanduser() if args.out_dir else codex_home / "study-planner" / "dashboards" / args.profile
    out_dir.mkdir(parents=True, exist_ok=True)

    dashboard_script = SCRIPT_DIR / "study_dashboard.py"
    server_script = SCRIPT_DIR / "study_dashboard_server.py"

    generate_cmd = [
        sys.executable,
        str(dashboard_script),
        "--profile",
        args.profile,
        "--codex-home",
        str(codex_home),
        "--out-dir",
        str(out_dir),
        "--api-host",
        args.host,
        "--api-port",
        str(args.api_port),
        "--static-port",
        str(args.static_port),
    ]
    subprocess.run(generate_cmd, check=True)

    api_url = f"http://{args.host}:{args.api_port}/api/health"
    static_url = f"http://127.0.0.1:{args.static_port}/"
    processes: list[subprocess.Popen] = []

    if not args.no_api:
        processes.append(
            start_process(
                [
                    sys.executable,
                    str(server_script),
                    "--profile",
                    args.profile,
                    "--codex-home",
                    str(codex_home),
                    "--host",
                    args.host,
                    "--port",
                    str(args.api_port),
                    "--static-port",
                    str(args.static_port),
                    "--out-dir",
                    str(out_dir),
                ]
            )
        )
        wait_url(api_url)

    if not args.no_static:
        processes.append(start_process([sys.executable, "-m", "http.server", str(args.static_port)], cwd=out_dir))
        wait_url(static_url)

    if args.open:
        webbrowser.open(static_url)

    print(f"Study Planner dashboard generated: {out_dir / 'index.html'}")
    if not args.no_static:
        print(f"Dashboard URL: {static_url}")
    if not args.no_api:
        print(f"Local write API: {api_url}")
    if processes:
        print("Processes were started in the background. Stop them from your system process manager when finished.")


if __name__ == "__main__":
    main()
