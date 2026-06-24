#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
PROFILE_FILES = {
    "goals": "goals.json",
    "materials": "materials.json",
    "mistakes": "mistakes.json",
    "reviews": "review_queue.json",
    "current_week": "current_week.json",
    "logs": "daily_logs.json",
    "obsidian": "obsidian.json",
}


def profile_dir(codex_home: Path, profile: str) -> Path:
    return codex_home / "study-planner" / "profiles" / profile


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load(codex_home: Path, profile: str, key: str) -> Any:
    default: Any = {} if key in {"goals", "current_week", "obsidian"} else []
    return read_json(profile_dir(codex_home, profile) / PROFILE_FILES[key], default)


def save(codex_home: Path, profile: str, key: str, data: Any) -> None:
    write_json(profile_dir(codex_home, profile) / PROFILE_FILES[key], data)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\r\n")
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key.strip()] = [part.strip().strip('"\'') for part in value[1:-1].split(",") if part.strip()]
        else:
            data[key.strip()] = value.strip('"\'')
    return data, body


def frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            joined = ", ".join(str(item) for item in value)
            lines.append(f"{key}: [{joined}]")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def markdown_files(vault: Path) -> list[Path]:
    ignored = {".obsidian", ".git"}
    rows = []
    for path in vault.rglob("*.md"):
        if any(part in ignored for part in path.parts):
            continue
        rows.append(path)
    return rows


def slug(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", value).strip()
    return cleaned or "untitled"


def parse_markdown_table(body: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(lines) < 2:
        return []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def normalize_unit(row: dict[str, str]) -> dict[str, str]:
    def pick(*names: str) -> str:
        lowered = {key.lower(): value for key, value in row.items()}
        for name in names:
            if name in row:
                return row[name]
            if name.lower() in lowered:
                return lowered[name.lower()]
        return ""

    unit_id = pick("id", "ID", "单元", "编号") or pick("标题", "title", "章节")
    return {
        "id": unit_id,
        "title": pick("title", "标题", "章节", "小节") or unit_id,
        "page_range": pick("page_range", "页码", "页码范围"),
        "lecture_range": pick("lecture_range", "讲次", "课程", "视频"),
        "problem_range": pick("problem_range", "题号", "题号范围"),
        "parent": pick("parent", "父级", "章"),
    }


def configure(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home).expanduser()
    vault = Path(args.vault).expanduser()
    if not vault.exists():
        raise SystemExit(f"Obsidian vault not found: {vault}")
    config = load(codex_home, args.profile, "obsidian")
    config.update(
        {
            "vault": str(vault),
            "study_root": args.study_root,
            "updated": date.today().isoformat(),
        }
    )
    save(codex_home, args.profile, "obsidian", config)
    print_json({"ok": True, "profile": args.profile, "obsidian": config})


def resolve_vault(codex_home: Path, profile: str, vault_arg: str) -> Path:
    if vault_arg:
        return Path(vault_arg).expanduser()
    config = load(codex_home, profile, "obsidian")
    if not config.get("vault"):
        raise SystemExit("Missing vault. Run configure first or pass --vault.")
    return Path(config["vault"]).expanduser()


def import_materials(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home).expanduser()
    vault = resolve_vault(codex_home, args.profile, args.vault)
    materials = load(codex_home, args.profile, "materials")
    by_id = {item.get("id"): item for item in materials if item.get("id")}
    imported = []
    for path in markdown_files(vault):
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm.get("type") != "material":
            continue
        material_id = fm.get("id") or fm.get("material_id") or f"MAT-OBS-{slug(path.stem)}"
        rows = parse_markdown_table(body)
        units = [normalize_unit(row) for row in rows]
        material = {
            "id": material_id,
            "name": fm.get("name") or path.stem,
            "kind": fm.get("kind") or "book",
            "subject": fm.get("subject") or "",
            "edition": fm.get("edition") or "",
            "teacher": fm.get("teacher") or "",
            "source": str(path),
            "catalog_status": "complete" if units else "missing",
            "catalog_source": fm.get("catalog_source") or f"obsidian:{path.name}",
            "catalog_units": units,
            "notes": fm.get("notes") or "",
            "updated": date.today().isoformat(),
        }
        if material_id in by_id:
            by_id[material_id].update(material)
        else:
            materials.append(material)
            by_id[material_id] = material
        imported.append({"id": material_id, "name": material["name"], "units": len(units), "path": str(path)})
    save(codex_home, args.profile, "materials", materials)
    print_json({"ok": True, "profile": args.profile, "imported": imported})


def import_mistakes(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home).expanduser()
    vault = resolve_vault(codex_home, args.profile, args.vault)
    mistakes = load(codex_home, args.profile, "mistakes")
    by_id = {item.get("id"): item for item in mistakes if item.get("id")}
    imported = []
    for path in markdown_files(vault):
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm.get("type") != "mistake":
            continue
        mistake_id = fm.get("id") or fm.get("source_id") or f"M-OBS-{slug(path.stem)}"
        mistake = {
            "id": mistake_id,
            "subject": fm.get("subject") or "",
            "source": fm.get("material") or fm.get("source") or "",
            "question": fm.get("question") or path.stem,
            "page_range": fm.get("page_range") or "",
            "problem_range": fm.get("problem_range") or "",
            "knowledge": fm.get("knowledge") or "",
            "error_causes": fm.get("error_causes") if isinstance(fm.get("error_causes"), list) else split_csv(fm.get("error_causes", "")),
            "note": body.strip(),
            "status": fm.get("status") or "pending",
            "source_path": str(path),
            "updated": date.today().isoformat(),
        }
        if mistake_id in by_id:
            by_id[mistake_id].update(mistake)
        else:
            mistakes.append(mistake)
            by_id[mistake_id] = mistake
        imported.append({"id": mistake_id, "question": mistake["question"], "path": str(path)})
    save(codex_home, args.profile, "mistakes", mistakes)
    print_json({"ok": True, "profile": args.profile, "imported": imported})


def export_markdown(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home).expanduser()
    vault = resolve_vault(codex_home, args.profile, args.vault)
    config = load(codex_home, args.profile, "obsidian")
    root_name = args.study_root or config.get("study_root") or "Study Planner"
    root = vault / root_name
    root.mkdir(parents=True, exist_ok=True)
    written = []
    written.extend(export_material_notes(codex_home, args.profile, root))
    written.extend(export_mistake_notes(codex_home, args.profile, root))
    written.append(export_week_note(codex_home, args.profile, root))
    written.append(export_daily_log_note(codex_home, args.profile, root))
    print_json({"ok": True, "profile": args.profile, "written": [str(path) for path in written if path]})


def export_material_notes(codex_home: Path, profile: str, root: Path) -> list[Path]:
    out_dir = root / "04-Materials"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for material in load(codex_home, profile, "materials"):
        path = out_dir / f"{slug(material.get('id','MAT'))}-{slug(material.get('name','material'))}.md"
        fm = {
            "type": "material",
            "id": material.get("id", ""),
            "name": material.get("name", ""),
            "kind": material.get("kind", ""),
            "subject": material.get("subject", ""),
            "catalog_status": material.get("catalog_status", ""),
        }
        rows = ["| id | title | page_range | lecture_range | problem_range | parent |", "|---|---|---|---|---|---|"]
        for unit in material.get("catalog_units", []):
            rows.append(
                f"| {unit.get('id','')} | {unit.get('title','')} | {unit.get('page_range','')} | {unit.get('lecture_range','')} | {unit.get('problem_range','')} | {unit.get('parent','')} |"
            )
        path.write_text(frontmatter(fm) + "\n".join(rows) + "\n", encoding="utf-8")
        written.append(path)
    return written


def export_mistake_notes(codex_home: Path, profile: str, root: Path) -> list[Path]:
    out_dir = root / "03-Mistakes"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for mistake in load(codex_home, profile, "mistakes"):
        path = out_dir / f"{slug(mistake.get('id','M'))}-{slug(mistake.get('question','mistake'))}.md"
        fm = {
            "type": "mistake",
            "id": mistake.get("id", ""),
            "subject": mistake.get("subject", ""),
            "material": mistake.get("source", ""),
            "question": mistake.get("question", ""),
            "knowledge": mistake.get("knowledge", ""),
            "error_causes": mistake.get("error_causes", []),
            "status": mistake.get("status", "pending"),
        }
        body = mistake.get("note", "") or "## 复盘\n\n- 错因：\n- 正解：\n- 下次检查：\n"
        path.write_text(frontmatter(fm) + body.strip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def export_week_note(codex_home: Path, profile: str, root: Path) -> Path | None:
    week = load(codex_home, profile, "current_week")
    if not week:
        return None
    out_dir = root / "01-Weekly Plans"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"Week-{week.get('start','current')}.md"
    lines = [
        frontmatter({"type": "weekly-plan", "profile": profile, "week_start": week.get("start", "")}).rstrip(),
        "",
        f"# 周计划 {week.get('start','')}",
        "",
    ]
    for day in week.get("plan", []):
        lines.append(f"## {day.get('date','')}")
        for title, key in [("主线任务", "main_tasks"), ("复习任务", "review_tasks"), ("加餐任务", "optional_extra")]:
            lines.append(f"### {title}")
            for item in day.get(key, []):
                lines.append(f"- [ ] `{item.get('id','')}` {item.get('subject','')}：{item.get('task','')}")
        lines.append("### 保底任务")
        for item in day.get("minimum_version", []):
            lines.append(f"- [ ] {item}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_daily_log_note(codex_home: Path, profile: str, root: Path) -> Path:
    logs = load(codex_home, profile, "logs")
    out_dir = root / "02-Daily Logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"Daily-Logs-{date.today().isoformat()}.md"
    lines = [
        frontmatter({"type": "daily-log-index", "profile": profile, "generated": date.today().isoformat()}).rstrip(),
        "",
        "# 学习日志",
        "",
        "| date | task_id | status | accuracy | error_causes | note |",
        "|---|---|---|---|---|---|",
    ]
    for log in logs:
        causes = ",".join(log.get("error_causes") or [])
        lines.append(f"| {log.get('date','')} | {log.get('task_id','')} | {log.get('status','')} | {log.get('accuracy','')} | {causes} | {str(log.get('note','')).replace('|','/')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Study Planner profiles with an Obsidian vault.")
    parser.add_argument("--profile", default=os.environ.get("STUDY_PROFILE", "default"))
    parser.add_argument("--codex-home", default=str(DEFAULT_CODEX_HOME))
    sub = parser.add_subparsers(dest="command", required=True)

    configure_parser = sub.add_parser("configure")
    configure_parser.add_argument("--vault", required=True)
    configure_parser.add_argument("--study-root", default="Study Planner")
    configure_parser.set_defaults(func=configure)

    import_materials_parser = sub.add_parser("import-materials")
    import_materials_parser.add_argument("--vault", default="")
    import_materials_parser.set_defaults(func=import_materials)

    import_mistakes_parser = sub.add_parser("import-mistakes")
    import_mistakes_parser.add_argument("--vault", default="")
    import_mistakes_parser.set_defaults(func=import_mistakes)

    export_parser = sub.add_parser("export")
    export_parser.add_argument("--vault", default="")
    export_parser.add_argument("--study-root", default="")
    export_parser.set_defaults(func=export_markdown)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
