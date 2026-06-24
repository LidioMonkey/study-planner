#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import argparse
import re
import sys
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8790
STATIC_PORT = 8787
RUN_DATE = date.today().isoformat()
PROFILE_NAME = "default"
CODEX_ROOT = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
PROFILE = CODEX_ROOT / "study-planner" / "profiles" / PROFILE_NAME
STORE = SCRIPT_DIR / "study_store.py"
GENERATOR = SCRIPT_DIR / "study_dashboard.py"
OUT_DIR = CODEX_ROOT / "study-planner" / "dashboards" / PROFILE_NAME
ALLOWED_ORIGINS = {
    "http://127.0.0.1:8787",
    "http://localhost:8787",
}
ALLOWED_ORIGINS.update(
    origin.strip()
    for origin in os.environ.get("STUDY_DASHBOARD_ORIGINS", "").split(",")
    if origin.strip()
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Study Planner dashboard local write API.")
    parser.add_argument("--profile", default=os.environ.get("STUDY_PROFILE", "default"))
    parser.add_argument("--codex-home", default=str(CODEX_ROOT))
    parser.add_argument("--host", default=os.environ.get("STUDY_DASHBOARD_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_API_PORT", "8790")))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--static-port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_STATIC_PORT", "8787")))
    parser.add_argument("--date", default=date.today().isoformat())
    return parser.parse_args()


def validate_profile(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name):
        raise SystemExit("profile 只能包含字母、数字、下划线、点和短横线")
    return name


def configure(args: argparse.Namespace) -> None:
    global HOST, PORT, STATIC_PORT, RUN_DATE, PROFILE_NAME, CODEX_ROOT, PROFILE, OUT_DIR, ALLOWED_ORIGINS
    HOST = args.host
    PORT = args.port
    STATIC_PORT = args.static_port
    RUN_DATE = args.date
    PROFILE_NAME = validate_profile(args.profile)
    CODEX_ROOT = Path(args.codex_home).expanduser()
    PROFILE = CODEX_ROOT / "study-planner" / "profiles" / PROFILE_NAME
    OUT_DIR = Path(args.out_dir).expanduser() if args.out_dir else CODEX_ROOT / "study-planner" / "dashboards" / PROFILE_NAME
    ALLOWED_ORIGINS.update(
        {
            f"http://127.0.0.1:{args.static_port}",
            f"http://localhost:{args.static_port}",
        }
    )


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_store(*args: str):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(STORE), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def regenerate_dashboard():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--profile",
            PROFILE_NAME,
            "--codex-home",
            str(CODEX_ROOT),
            "--out-dir",
            str(OUT_DIR),
            "--api-host",
            HOST,
            "--api-port",
            str(PORT),
            "--static-port",
            str(STATIC_PORT),
            "--date",
            RUN_DATE,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return {"ok": True, "output": str(OUT_DIR / "index.html")}


def task_exists(task_id: str) -> bool:
    for filename in ["courses.json", "exercises.json", "review_queue.json", "backlog.json"]:
        for item in read_json(PROFILE / filename, []):
            if item.get("id") == task_id:
                return True
    return False


def log_dashboard_only(payload: dict, status: str, when: str):
    path = PROFILE / "dashboard_completions.json"
    rows = read_json(path, [])
    key = str(payload.get("key") or "").strip()
    if not key:
        raise ValueError("缺少 key")
    record = {
        "key": key,
        "date": when,
        "status": status,
        "layer": payload.get("layer"),
        "layer_name": payload.get("layer_name"),
        "title": payload.get("title"),
        "raw_task": payload.get("raw_task"),
        "note": payload.get("note") or "HTML 看板同步",
        "updated": datetime.now().isoformat(timespec="seconds"),
    }
    replaced = False
    for index, row in enumerate(rows):
        if row.get("key") == key:
            rows[index] = record
            replaced = True
            break
    if not replaced:
        rows.append(record)
    write_json(path, rows)
    return {"logged": record, "dashboard_only": True, "replaced_existing_log": replaced}


def set_current_week_item_status(task_id: str, when: str, status: str) -> None:
    path = PROFILE / "current_week.json"
    data = read_json(path, {})
    changed = False
    for day in data.get("plan", []):
        if day.get("date") != when:
            continue
        for key in ["main_tasks", "review_tasks", "optional_extra"]:
            for item in day.get(key, []):
                if item.get("id") == task_id:
                    item["dashboard_status"] = status
                    item["dashboard_updated"] = datetime.now().isoformat(timespec="seconds")
                    changed = True
    if changed:
        write_json(path, data)


def log_task(payload: dict):
    profile = payload.get("profile", PROFILE_NAME)
    if profile != PROFILE_NAME:
        raise ValueError(f"只允许写入当前档案：{PROFILE_NAME}")
    task_id = str(payload.get("task_id") or "").strip()
    status = payload.get("status") or ("done" if payload.get("checked") else "pending")
    if status == "pending":
        status = "missed"
    if status not in {"done", "partial", "missed"}:
        raise ValueError("status 必须是 done/partial/missed/pending")
    when = payload.get("date") or date.today().isoformat()
    if not task_id:
        return log_dashboard_only(payload, status, when)
    if not task_exists(task_id):
        raise ValueError(f"任务不存在：{task_id}")
    args = [
        "log",
        "--profile",
        PROFILE_NAME,
        "--task-id",
        task_id,
        "--status",
        status,
        "--date",
        when,
        "--note",
        payload.get("note") or "HTML 看板同步",
    ]
    if payload.get("accuracy") is not None:
        args.extend(["--accuracy", str(payload["accuracy"])])
    if payload.get("error_causes"):
        args.extend(["--error-causes", ",".join(payload["error_causes"]) if isinstance(payload["error_causes"], list) else str(payload["error_causes"])])
    result = run_store(*args)
    set_current_week_item_status(task_id, when, status)
    return result


def roll_next_cycle(payload: dict):
    args = ["next-week-plan", "--profile", PROFILE_NAME, "--commit"]
    if payload.get("start"):
        args.extend(["--start", payload["start"]])
    plan = run_store(*args)
    regenerate_dashboard()
    return {"plan": plan, "regenerated": True}


def mistake_calendar():
    reviews = read_json(PROFILE / "review_queue.json", [])
    mistakes = read_json(PROFILE / "mistakes.json", [])
    mistake_sources = {f"mistake:{m.get('id')}" for m in mistakes}
    rows = []
    for item in reviews:
        source = item.get("source", "")
        if "mistake:" not in source:
            continue
        rows.append(
            {
                "id": item.get("id"),
                "due": item.get("due"),
                "subject": item.get("subject"),
                "source": source,
                "content": item.get("content"),
                "interval": item.get("interval"),
                "status": item.get("status", "pending"),
            }
        )
    rows.sort(key=lambda x: (x.get("due") or "", x.get("subject") or ""))
    return {"profile": PROFILE_NAME, "count": len(rows), "items": rows, "mistake_count": len(mistakes)}


class Handler(BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                self.send_json({"ok": True, "profile": PROFILE_NAME, "dashboard": str(OUT_DIR / "index.html")})
            elif path == "/api/mistake-calendar":
                self.send_json(mistake_calendar())
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_body()
            if path == "/api/log-task":
                self.send_json({"ok": True, "result": log_task(payload)})
            elif path == "/api/roll-next-cycle":
                self.send_json({"ok": True, "result": roll_next_cycle(payload)})
            elif path == "/api/regenerate-dashboard":
                self.send_json({"ok": True, "result": regenerate_dashboard()})
            else:
                self.send_json({"error": "not found"}, 404)
        except subprocess.CalledProcessError as exc:
            self.send_json({"ok": False, "error": exc.stderr or str(exc)}, 500)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

    def log_message(self, fmt, *args):
        print(f"[study-dashboard] {self.address_string()} - {fmt % args}")


def main():
    configure(parse_args())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Study dashboard API: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
