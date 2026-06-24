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
    "courses": "courses.json",
    "exercises": "exercises.json",
}

OUTLINE_408_SPECS = [
    {
        "id": "MAT-WANGDAO-DS",
        "name": "王道数据结构复习指导书",
        "kind": "book",
        "subject": "408 - Data Structure",
        "folder": "01-数据结构",
        "index": "数据结构目录.md",
        "prefix": "DS",
    },
    {
        "id": "MAT-WANGDAO-CO",
        "name": "王道计算机组成原理复习指导书",
        "kind": "book",
        "subject": "408 - Computer Organization",
        "folder": "02-计算机组成原理",
        "index": "计算机组成原理目录.md",
        "prefix": "CO",
    },
    {
        "id": "MAT-WANGDAO-OS",
        "name": "王道操作系统复习指导书",
        "kind": "book",
        "subject": "408 - Operating System",
        "folder": "03-操作系统",
        "index": "操作系统目录.md",
        "prefix": "OS",
    },
    {
        "id": "MAT-WANGDAO-CN",
        "name": "王道计算机网络复习指导书",
        "kind": "book",
        "subject": "408 - Computer Network",
        "folder": "04-计算机网络",
        "index": "计算机网络目录.md",
        "prefix": "CN",
    },
]

OUTLINE_408_BINDINGS = {
    "T005": ("MAT-WANGDAO-DS", ["DS-06"]),
    "T017": ("MAT-WANGDAO-DS", ["DS-06"]),
    "T006": ("MAT-WANGDAO-CO", ["CO-04"]),
    "T019": ("MAT-WANGDAO-CO", ["CO-04"]),
    "T007": ("MAT-WANGDAO-CO", ["CO-05"]),
    "T020": ("MAT-WANGDAO-CO", ["CO-05"]),
    "T008": ("MAT-WANGDAO-OS", ["OS-02"]),
    "T009": ("MAT-WANGDAO-OS", ["OS-03", "OS-04"]),
    "T021": ("MAT-WANGDAO-OS", ["OS-02", "OS-03", "OS-04"]),
    "T010": ("MAT-WANGDAO-CN", ["CN-01"]),
    "T022": ("MAT-WANGDAO-CN", ["CN-01"]),
}

OUTLINE_408_HINTS = {
    "MAT-WANGDAO-DS": {
        "subject": ["Data Structure", "数据结构"],
        "unit_hints": {
            "DS-01": ["线性表", "顺序表", "链表"],
            "DS-02": ["栈", "队列"],
            "DS-03": ["树", "二叉树", "平衡二叉树"],
            "DS-04": ["图", "关键路径", "拓扑排序", "最短路径"],
            "DS-05": ["查找", "B 树", "B树", "散列", "哈希"],
            "DS-06": ["排序", "快速排序", "归并排序", "堆排序"],
            "DS-07": ["算法分析", "复杂度"],
        },
    },
    "MAT-WANGDAO-CO": {
        "subject": ["Computer Organization", "计算机组成原理", "计组"],
        "unit_hints": {
            "CO-01": ["计算机系统概述"],
            "CO-02": ["数据的表示", "数据表示", "运算"],
            "CO-03": ["存储器", "Cache", "缓存"],
            "CO-04": ["指令系统", "寻址方式"],
            "CO-05": ["中央处理器", "CPU", "数据通路", "控制器"],
            "CO-06": ["总线"],
            "CO-07": ["输入输出系统", "I/O", "IO"],
        },
    },
    "MAT-WANGDAO-OS": {
        "subject": ["Operating System", "操作系统"],
        "unit_hints": {
            "OS-01": ["操作系统概述", "操作系统引论"],
            "OS-02": ["进程", "线程", "PCB"],
            "OS-03": ["处理机调度", "调度算法", "CPU调度"],
            "OS-04": ["进程同步", "死锁", "PV", "互斥"],
            "OS-05": ["存储器管理", "内存管理"],
            "OS-06": ["虚拟存储器", "虚拟内存"],
            "OS-07": ["输入输出系统", "I/O", "IO"],
            "OS-08": ["文件管理", "文件系统"],
            "OS-09": ["磁盘"],
            "OS-10": ["多处理机"],
            "OS-11": ["虚拟化", "云计算"],
        },
    },
    "MAT-WANGDAO-CN": {
        "subject": ["Computer Network", "计算机网络", "计网"],
        "unit_hints": {
            "CN-01": ["计算机网络概述", "体系结构", "分层", "OSI", "TCP/IP"],
            "CN-02": ["物理层"],
            "CN-03": ["数据链路层"],
            "CN-04": ["网络层", "IP"],
            "CN-05": ["传输层", "TCP", "UDP"],
            "CN-06": ["应用层"],
            "CN-07": ["网络安全"],
        },
    },
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


def parse_wiki_outline_units(path: Path, prefix: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    units = []
    seen = set()
    pattern = re.compile(r"\[\[(?P<link>[^\]|]+)(?:\|(?P<alias>[^\]]+))?\]\]")
    for match in pattern.finditer(text):
        link = match.group("link").strip()
        alias = (match.group("alias") or "").strip()
        chapter_match = re.search(r"第\s*(\d+)\s*章[-－—\s]*(.+)$", link)
        if not chapter_match:
            continue
        chapter_no = int(chapter_match.group(1))
        title = chapter_match.group(2).strip() or alias or Path(link).stem
        unit_id = f"{prefix}-{chapter_no:02d}"
        if unit_id in seen:
            continue
        seen.add(unit_id)
        note_path = path.parent / f"第{chapter_no}章-{title}.md"
        units.append(
            {
                "id": unit_id,
                "title": f"第{chapter_no}章 {title}",
                "page_range": "",
                "lecture_range": "",
                "problem_range": "",
                "parent": "",
                "obsidian_link": link,
                "source_note": str(note_path) if note_path.exists() else "",
            }
        )
    return units


def upsert_material(materials: list[dict[str, Any]], material: dict[str, Any]) -> None:
    material_id = material.get("id")
    for item in materials:
        if item.get("id") == material_id:
            item.update(material)
            return
    materials.append(material)


def bind_task_to_material(task: dict[str, Any], material: dict[str, Any], unit_ids: list[str]) -> None:
    task["material_id"] = material.get("id", "")
    task["catalog_units"] = unit_ids
    index = {unit.get("id"): unit for unit in material.get("catalog_units", [])}
    titles = [index[unit_id].get("title", "") for unit_id in unit_ids if unit_id in index]
    if titles:
        scope = "；".join(titles)
        if task.get("type") == "course":
            task["chapter"] = scope
        else:
            task["scope"] = scope
    for field in ["page_range", "lecture_range", "problem_range"]:
        if task.get(field):
            continue
        values = [index[unit_id].get(field, "") for unit_id in unit_ids if unit_id in index and index[unit_id].get(field)]
        if values:
            task[field] = "；".join(values)


def task_search_text(task: dict[str, Any]) -> str:
    fields = [
        task.get("subject", ""),
        task.get("title", ""),
        task.get("resource", ""),
        task.get("material", ""),
        task.get("chapter", ""),
        task.get("scope", ""),
        task.get("slice", ""),
        task.get("exercise", ""),
        task.get("acceptance", ""),
    ]
    return " ".join(str(field) for field in fields if field)


def infer_408_binding(task: dict[str, Any]) -> tuple[str, list[str]] | None:
    if task.get("id") in OUTLINE_408_BINDINGS:
        return OUTLINE_408_BINDINGS[task["id"]]
    text = task_search_text(task)
    if "王道" not in text and not str(task.get("material_id", "")).startswith("MAT-WANGDAO-"):
        return None
    for material_id, hints in OUTLINE_408_HINTS.items():
        if not any(hint in text for hint in hints["subject"]):
            continue
        matched = []
        for unit_id, unit_hints in hints["unit_hints"].items():
            if any(hint in text for hint in unit_hints):
                matched.append(unit_id)
        if matched:
            return material_id, matched
    return None


def bind_408_tasks(codex_home: Path, profile: str, material_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    changed = []
    for key in ["courses", "exercises"]:
        tasks = load(codex_home, profile, key)
        touched = False
        for task in tasks:
            binding = infer_408_binding(task)
            if not binding:
                continue
            material_id, unit_ids = binding
            material = material_by_id.get(material_id)
            if not material:
                continue
            bind_task_to_material(task, material, unit_ids)
            changed.append({"task_id": task.get("id"), "file": PROFILE_FILES[key], "material_id": material_id, "catalog_units": unit_ids})
            touched = True
        if touched:
            save(codex_home, profile, key, tasks)
    current_week = load(codex_home, profile, "current_week")
    if isinstance(current_week, dict) and current_week.get("plan"):
        touched_week = False
        for day in current_week.get("plan", []):
            for bucket in ["main_tasks", "review_tasks", "optional_extra"]:
                for item in day.get(bucket, []):
                    binding = infer_408_binding(item)
                    if not binding:
                        continue
                    material_id, unit_ids = binding
                    material = material_by_id.get(material_id)
                    if not material:
                        continue
                    bind_task_to_material(item, material, unit_ids)
                    item["catalog_units"] = unit_ids
                    changed.append({"task_id": item.get("id"), "file": PROFILE_FILES["current_week"], "material_id": material_id, "catalog_units": unit_ids})
                    touched_week = True
        if touched_week:
            save(codex_home, profile, "current_week", current_week)
    return changed


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


def import_408_outline(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home).expanduser()
    vault = resolve_vault(codex_home, args.profile, args.vault)
    materials = load(codex_home, args.profile, "materials")
    imported = []
    material_by_id = {}
    for spec in OUTLINE_408_SPECS:
        index_path = vault / spec["folder"] / spec["index"]
        units = parse_wiki_outline_units(index_path, spec["prefix"])
        material = {
            "id": spec["id"],
            "name": spec["name"],
            "kind": spec["kind"],
            "subject": spec["subject"],
            "edition": "",
            "teacher": "",
            "source": str(index_path),
            "catalog_status": "complete" if units else "missing",
            "catalog_source": f"obsidian-outline:{index_path}",
            "catalog_precision": "chapter",
            "catalog_units": units,
            "notes": "由 Obsidian 408 目录笔记导入。当前目录精度为章级；页码、讲次、题号为空时不得由 agent 编造。",
            "updated": date.today().isoformat(),
        }
        upsert_material(materials, material)
        material_by_id[spec["id"]] = material
        imported.append({"id": spec["id"], "name": spec["name"], "units": len(units), "path": str(index_path)})
    save(codex_home, args.profile, "materials", materials)
    bound = bind_408_tasks(codex_home, args.profile, material_by_id) if args.bind_tasks else []
    print_json({"ok": True, "profile": args.profile, "imported": imported, "bound_tasks": bound})


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
            "catalog_source": material.get("catalog_source", ""),
            "catalog_precision": material.get("catalog_precision", ""),
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

    import_408_parser = sub.add_parser("import-408-outline")
    import_408_parser.add_argument("--vault", default="")
    import_408_parser.add_argument("--bind-tasks", action="store_true", help="Bind known Wangdao 408 tasks in the current profile to imported units.")
    import_408_parser.set_defaults(func=import_408_outline)

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
