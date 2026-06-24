#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
STORE_FILES = {
    "goals.json": {},
    "courses.json": [],
    "exercises.json": [],
    "review_queue.json": [],
    "daily_logs.json": [],
    "backlog.json": [],
    "mistakes.json": [],
    "modules.json": [],
    "papers.json": [],
    "current_week.json": {},
    "dashboard_completions.json": [],
    "materials.json": [],
    "meta.json": {},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a minimal Study Planner profile without overwriting existing data.")
    parser.add_argument("--profile", default=os.environ.get("STUDY_PROFILE", "default"))
    parser.add_argument("--codex-home", default=str(DEFAULT_CODEX_HOME))
    parser.add_argument("--goal", default="Long-term exam preparation")
    parser.add_argument("--deadline", default="2026-12-20")
    parser.add_argument("--subjects", default="Math,Professional Course,English,Politics")
    return parser.parse_args()


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json_if_missing(path: Path, data) -> bool:
    if path.exists():
        return False
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main() -> None:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser()
    profile_dir = codex_home / "study-planner" / "profiles" / args.profile
    profile_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for filename, default in STORE_FILES.items():
        if write_json_if_missing(profile_dir / filename, default):
            created.append(filename)

    goals_path = profile_dir / "goals.json"
    goals = read_json(goals_path, {})
    if not goals:
        goals = {
            "goal": args.goal,
            "deadline": args.deadline,
            "subjects": [item.strip() for item in args.subjects.split(",") if item.strip()],
            "priority_weights": {},
            "notes": "Seed profile. Replace with the user's real baseline, materials, and constraints before serious planning.",
        }
        goals_path.write_text(json.dumps(goals, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "profile": args.profile,
                "profile_dir": str(profile_dir),
                "created": created,
                "goals": goals,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
