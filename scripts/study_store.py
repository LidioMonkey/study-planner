#!/usr/bin/env python3
"""Small JSON store for the study-planner skill."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".codex" / "study-planner" / "profiles"
REVIEW_INTERVALS = [1, 3, 7, 14, 30]
MODULE_TEMPLATES = {
    "408-os": {
        "subject": "408 - Operating System",
        "course_title": "Wangdao operating system",
        "exercise_resource": "Wangdao after-class questions",
        "course_output": "framework notes and representative examples",
        "exercise_acceptance": "correct all wrong questions and tag conceptual gaps",
        "course_minutes": 60,
        "exercise_quantity": 25,
        "priority": 1,
    },
    "408-cn": {
        "subject": "408 - Computer Network",
        "course_title": "Wangdao computer network",
        "exercise_resource": "Wangdao after-class questions",
        "course_output": "layer/protocol/mechanism table",
        "exercise_acceptance": "correct all conceptual questions and summarize confusions",
        "course_minutes": 50,
        "exercise_quantity": 20,
        "priority": 2,
    },
    "408-co": {
        "subject": "408 - Computer Organization",
        "course_title": "Wangdao computer organization",
        "exercise_resource": "Wangdao after-class questions",
        "course_output": "structure diagram and method checklist",
        "exercise_acceptance": "correct mistakes and map them to formulas or mechanisms",
        "course_minutes": 60,
        "exercise_quantity": 25,
        "priority": 1,
    },
    "408-ds": {
        "subject": "408 - Data Structure",
        "course_title": "Wangdao data structure",
        "exercise_resource": "Wangdao after-class questions",
        "course_output": "algorithm/data-structure comparison table",
        "exercise_acceptance": "correct wrong choices and summarize algorithm conditions",
        "course_minutes": 60,
        "exercise_quantity": 30,
        "priority": 2,
    },
    "math2-linear": {
        "subject": "Math II - Linear Algebra",
        "course_title": "Li Yongle linear algebra foundation",
        "exercise_resource": "Li Yongle foundation exercises",
        "course_output": "condition checklist and typical-problem methods",
        "exercise_acceptance": "correct all mistakes and summarize conditions",
        "course_minutes": 60,
        "exercise_quantity": 25,
        "priority": 2,
    },
    "math2-advanced": {
        "subject": "Math II - Advanced Math",
        "course_title": "Wu Zhongxiang high math",
        "exercise_resource": "660",
        "course_output": "method framework and representative-problem notes",
        "exercise_acceptance": "correct all wrong questions and tag concept/calculation/method causes",
        "course_minutes": 60,
        "exercise_quantity": 30,
        "priority": 2,
    },
    "english2": {
        "subject": "English II",
        "course_title": "English II main materials",
        "exercise_resource": "English II practice",
        "course_output": "sentence/vocabulary/output notes",
        "exercise_acceptance": "extract vocabulary, locate evidence, and correct wrong choices",
        "course_minutes": 40,
        "exercise_quantity": 1,
        "priority": 3,
    },
    "politics": {
        "subject": "Politics",
        "course_title": "Politics main route",
        "exercise_resource": "Xiao 1000",
        "course_output": "framework notes and confusion points",
        "exercise_acceptance": "record confusing knowledge points",
        "course_minutes": 30,
        "exercise_quantity": 20,
        "priority": 4,
    },
}
MODEL_408 = {
    "408 - Data Structure": {
        "linear list": 1,
        "stack queue array": 1,
        "tree": 3,
        "graph": 3,
        "search": 2,
        "sorting": 2,
    },
    "408 - Computer Organization": {
        "data representation": 2,
        "instruction system": 2,
        "cpu": 3,
        "memory": 3,
        "io": 1,
    },
    "408 - Operating System": {
        "process threads": 3,
        "scheduling pv": 3,
        "memory management": 3,
        "file system": 2,
        "io": 1,
    },
    "408 - Computer Network": {
        "architecture": 1,
        "physical": 1,
        "data link": 2,
        "network layer": 3,
        "transport layer": 3,
        "application": 2,
    },
}
FILES = {
    "goals": "goals.json",
    "courses": "courses.json",
    "exercises": "exercises.json",
    "reviews": "review_queue.json",
    "logs": "daily_logs.json",
    "mistakes": "mistakes.json",
    "modules": "modules.json",
    "papers": "papers.json",
    "backlog": "backlog.json",
    "current_week": "current_week.json",
    "materials": "materials.json",
    "meta": "meta.json",
}


def today_iso() -> str:
    return date.today().isoformat()


def parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def profile_dir(profile: str) -> Path:
    return ROOT / profile


def ensure_profile(profile: str) -> Path:
    path = profile_dir(profile)
    path.mkdir(parents=True, exist_ok=True)
    for filename in FILES.values():
        file_path = path / filename
        if not file_path.exists():
            default: Any = {} if filename in {"goals.json", "meta.json"} else []
            write_json(file_path, default)
    meta_path = path / FILES["meta"]
    meta = read_json(meta_path, {})
    if "next_id" not in meta:
        meta["next_id"] = 1
        write_json(meta_path, meta)
    return path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load(profile: str, key: str) -> Any:
    path = ensure_profile(profile)
    default: Any = {} if key in {"goals", "meta"} else []
    return read_json(path / FILES[key], default)


def save(profile: str, key: str, data: Any) -> None:
    path = ensure_profile(profile)
    write_json(path / FILES[key], data)


def next_id(profile: str) -> str:
    meta = load(profile, "meta")
    current = int(meta.get("next_id", 1))
    meta["next_id"] = current + 1
    save(profile, "meta", meta)
    return f"T{current:03d}"


def next_material_id(profile: str) -> str:
    meta = load(profile, "meta")
    current = int(meta.get("next_material_id", 1))
    meta["next_material_id"] = current + 1
    save(profile, "meta", meta)
    return f"MAT{current:03d}"


def parse_catalog_units(value: str) -> list[str]:
    return split_csv(value)


def add_material(args: argparse.Namespace) -> None:
    materials = load(args.profile, "materials")
    material = {
        "id": args.material_id or next_material_id(args.profile),
        "name": args.name,
        "kind": args.kind,
        "subject": args.subject or "",
        "edition": args.edition or "",
        "teacher": args.teacher or "",
        "source": args.source or "",
        "catalog_status": "complete" if args.catalog else "missing",
        "catalog_source": args.catalog_source or "",
        "catalog_units": [],
        "notes": args.notes or "",
        "created": today_iso(),
    }
    if args.catalog:
        for raw_unit in args.catalog.split(";"):
            parts = [part.strip() for part in raw_unit.split("|")]
            if not parts or not parts[0]:
                continue
            unit = {
                "id": parts[0],
                "title": parts[1] if len(parts) > 1 else parts[0],
                "page_range": parts[2] if len(parts) > 2 else "",
                "lecture_range": parts[3] if len(parts) > 3 else "",
                "problem_range": parts[4] if len(parts) > 4 else "",
                "parent": parts[5] if len(parts) > 5 else "",
            }
            material["catalog_units"].append(unit)
    materials.append(material)
    save(args.profile, "materials", materials)
    print_json(material)


def find_material(profile: str, material_id: str) -> dict[str, Any] | None:
    if not material_id:
        return None
    for material in load(profile, "materials"):
        if material.get("id") == material_id or material.get("name") == material_id:
            return material
    return None


def material_unit_index(material: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not material:
        return {}
    index = {}
    for unit in material.get("catalog_units", []):
        unit_id = str(unit.get("id", ""))
        title = str(unit.get("title", ""))
        if unit_id:
            index[unit_id] = unit
        if title:
            index[title] = unit
    return index


def apply_catalog_ranges(task: dict[str, Any], material: dict[str, Any] | None, unit_refs: list[str]) -> None:
    if not material:
        return
    task["material_id"] = material.get("id", "")
    task["catalog_units"] = unit_refs
    index = material_unit_index(material)
    matched = [index[ref] for ref in unit_refs if ref in index]
    if not matched:
        return
    for field in ["page_range", "lecture_range", "problem_range"]:
        if task.get(field):
            continue
        values = [unit.get(field, "") for unit in matched if unit.get(field)]
        if values:
            task[field] = "；".join(values)
    if not task.get("chapter"):
        titles = [unit.get("title", "") for unit in matched if unit.get("title")]
        if titles:
            task["chapter"] = "；".join(titles)
    if not task.get("scope"):
        titles = [unit.get("title", "") for unit in matched if unit.get("title")]
        if titles:
            task["scope"] = "；".join(titles)


def validate_task_catalog(profile: str, task: dict[str, Any], material_field: str, scope_field: str) -> dict[str, Any]:
    material_id = task.get("material_id", "")
    catalog_units = task.get("catalog_units", [])
    material_name = task.get(material_field, "")
    scope = task.get(scope_field, "")
    issue = ""
    severity = "ok"
    if not material_id:
        issue = "未绑定 materials.json 中的真实资料目录"
        severity = "missing-material"
    else:
        material = find_material(profile, material_id)
        if not material:
            issue = "material_id 不存在"
            severity = "invalid-material"
        elif material.get("catalog_status") not in ("complete", "partial") or not material.get("catalog_units"):
            issue = "资料目录缺失"
            severity = "catalog-incomplete"
        elif not catalog_units:
            issue = "未引用目录单元"
            severity = "missing-catalog-unit"
    return {
        "task_id": task.get("id"),
        "type": task.get("type"),
        "subject": task.get("subject"),
        "material": material_name,
        "scope": scope,
        "material_id": material_id,
        "catalog_units": catalog_units,
        "page_range": task.get("page_range", ""),
        "lecture_range": task.get("lecture_range", ""),
        "problem_range": task.get("problem_range", ""),
        "severity": severity,
        "issue": issue,
    }


def material_report(args: argparse.Namespace) -> None:
    materials = load(args.profile, "materials")
    rows = []
    for material in materials:
        rows.append(
            {
                "id": material.get("id"),
                "name": material.get("name"),
                "kind": material.get("kind"),
                "subject": material.get("subject"),
                "catalog_status": material.get("catalog_status", "missing"),
                "unit_count": len(material.get("catalog_units", [])),
                "catalog_source": material.get("catalog_source", ""),
            }
        )
    print_json({"profile": args.profile, "materials": rows})


def catalog_audit(args: argparse.Namespace) -> None:
    rows = []
    for task in load(args.profile, "courses"):
        row = validate_task_catalog(args.profile, task, "title", "chapter")
        if args.all or row["severity"] != "ok":
            rows.append(row)
    for task in load(args.profile, "exercises"):
        row = validate_task_catalog(args.profile, task, "resource", "scope")
        if args.all or row["severity"] != "ok":
            rows.append(row)
    summary: dict[str, int] = {}
    for row in rows:
        summary[row["severity"]] = summary.get(row["severity"], 0) + 1
    print_json({"profile": args.profile, "summary": summary, "items": rows})


def init_profile(args: argparse.Namespace) -> None:
    ensure_profile(args.profile)
    goals = load(args.profile, "goals")
    goals.update(
        {
            "goal": args.goal,
            "deadline": args.deadline,
            "subjects": split_csv(args.subjects),
            "priority_weights": parse_weights(args.weights),
            "created": today_iso(),
            "notes": args.notes or "",
        }
    )
    save(args.profile, "goals", goals)
    print_json({"profile": args.profile, "goal": goals})


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_weights(value: str | None) -> dict[str, float]:
    weights: dict[str, float] = {}
    if not value:
        return weights
    for part in value.split(","):
        if "=" not in part:
            continue
        key, raw_weight = part.split("=", 1)
        key = key.strip()
        try:
            weights[key] = float(raw_weight.strip())
        except ValueError:
            continue
    return weights


def set_weights(args: argparse.Namespace) -> None:
    goals = load(args.profile, "goals")
    goals["priority_weights"] = parse_weights(args.weights)
    save(args.profile, "goals", goals)
    print_json(goals)


def add_course(args: argparse.Namespace) -> None:
    courses = load(args.profile, "courses")
    material = find_material(args.profile, args.material_id)
    catalog_units = parse_catalog_units(args.catalog_units)
    task = {
        "id": next_id(args.profile),
        "type": "course",
        "subject": args.subject,
        "title": args.title,
        "chapter": args.chapter or "",
        "material_id": args.material_id or "",
        "catalog_units": catalog_units,
        "page_range": args.page_range or "",
        "lecture_range": args.lecture_range or "",
        "problem_range": args.problem_range or "",
        "slice": args.slice,
        "estimated_minutes": args.minutes,
        "output": args.output,
        "exercise": args.exercise or "",
        "depends_on": split_csv(args.depends_on),
        "priority": args.priority,
        "status": "pending",
        "created": today_iso(),
    }
    apply_catalog_ranges(task, material, catalog_units)
    courses.append(task)
    save(args.profile, "courses", courses)
    print_json(task)


def add_exercise(args: argparse.Namespace) -> None:
    exercises = load(args.profile, "exercises")
    material = find_material(args.profile, args.material_id)
    catalog_units = parse_catalog_units(args.catalog_units)
    task = {
        "id": next_id(args.profile),
        "type": "exercise",
        "subject": args.subject,
        "resource": args.resource,
        "scope": args.scope,
        "material_id": args.material_id or "",
        "catalog_units": catalog_units,
        "page_range": args.page_range or "",
        "lecture_range": args.lecture_range or "",
        "problem_range": args.problem_range or "",
        "quantity": args.quantity,
        "mode": args.mode,
        "acceptance": args.acceptance
        or "Correct all wrong answers and tag error causes.",
        "depends_on": split_csv(args.depends_on),
        "priority": args.priority,
        "status": "pending",
        "created": today_iso(),
    }
    apply_catalog_ranges(task, material, catalog_units)
    exercises.append(task)
    save(args.profile, "exercises", exercises)
    print_json(task)


def add_course_task(
    profile: str,
    subject: str,
    title: str,
    chapter: str,
    slice_name: str,
    minutes: int,
    output: str,
    exercise: str,
    priority: int,
    depends_on: list[str] | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    courses = load(profile, "courses")
    task = {
        "id": next_id(profile),
        "type": "course",
        "subject": subject,
        "title": title,
        "chapter": chapter,
        "page_range": "",
        "lecture_range": "",
        "problem_range": "",
        "slice": slice_name,
        "estimated_minutes": minutes,
        "output": output,
        "exercise": exercise,
        "depends_on": depends_on or [],
        "priority": priority,
        "status": "pending",
        "created": today_iso(),
    }
    if module_id:
        task["module_id"] = module_id
    courses.append(task)
    save(profile, "courses", courses)
    return task


def add_exercise_task(
    profile: str,
    subject: str,
    resource: str,
    scope: str,
    quantity: int,
    mode: str,
    acceptance: str,
    priority: int,
    depends_on: list[str] | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    exercises = load(profile, "exercises")
    task = {
        "id": next_id(profile),
        "type": "exercise",
        "subject": subject,
        "resource": resource,
        "scope": scope,
        "page_range": "",
        "lecture_range": "",
        "problem_range": "",
        "quantity": quantity,
        "mode": mode,
        "acceptance": acceptance,
        "depends_on": depends_on or [],
        "priority": priority,
        "status": "pending",
        "created": today_iso(),
    }
    if module_id:
        task["module_id"] = module_id
    exercises.append(task)
    save(profile, "exercises", exercises)
    return task


def add_module(args: argparse.Namespace) -> None:
    if args.template not in MODULE_TEMPLATES:
        available = ", ".join(sorted(MODULE_TEMPLATES))
        raise SystemExit(f"Unknown template: {args.template}. Available: {available}")
    template = MODULE_TEMPLATES[args.template]
    modules = load(args.profile, "modules")
    module_id = next_id(args.profile).replace("T", "MOD")
    module = {
        "id": module_id,
        "template": args.template,
        "name": args.name,
        "subject": args.subject or template["subject"],
        "status": "pending",
        "created": today_iso(),
        "depends_on": split_csv(args.depends_on),
        "notes": args.notes or "",
    }
    modules.append(module)
    save(args.profile, "modules", modules)

    subject = module["subject"]
    priority = args.priority if args.priority is not None else int(template["priority"])
    course = add_course_task(
        args.profile,
        subject,
        args.course_title or template["course_title"],
        args.name,
        args.course_slice or f"{args.name} concept and method slice",
        args.minutes or int(template["course_minutes"]),
        args.output or template["course_output"],
        args.exercise or f"{template['exercise_resource']} {args.name}",
        priority,
        depends_on=module["depends_on"],
        module_id=module_id,
    )
    exercise = add_exercise_task(
        args.profile,
        subject,
        args.exercise_resource or template["exercise_resource"],
        args.exercise_scope or args.name,
        args.quantity or int(template["exercise_quantity"]),
        args.mode,
        args.acceptance or template["exercise_acceptance"],
        priority,
        depends_on=[course["id"]],
        module_id=module_id,
    )
    reviews: list[dict[str, Any]] = []
    for weak in split_csv(args.weak_points):
        reviews.extend(
            add_review_item(
                args.profile,
                subject,
                f"module:{module_id} weak point",
                weak,
                start=date.today(),
            )
        )
    print_json({"module": module, "created_tasks": [course, exercise], "created_reviews": reviews})


def module_report(args: argparse.Namespace) -> None:
    modules = load(args.profile, "modules")
    all_tasks = active_tasks(args.profile)
    rows: list[dict[str, Any]] = []
    for module in modules:
        module_tasks = [task for task in all_tasks if task.get("module_id") == module.get("id")]
        total = len(module_tasks)
        done = sum(1 for task in module_tasks if task.get("status") == "done")
        rows.append(
            {
                "module": module,
                "task_count": total,
                "done_count": done,
                "completion_rate": round(done / total * 100, 1) if total else 0,
                "tasks": [compact_task(task) for task in module_tasks],
            }
        )
    print_json({"profile": args.profile, "modules": rows})


def add_review_item(
    profile: str,
    subject: str,
    source: str,
    content: str,
    start: date | None = None,
) -> list[dict[str, Any]]:
    start = start or date.today()
    reviews = load(profile, "reviews")
    created: list[dict[str, Any]] = []
    for interval in REVIEW_INTERVALS:
        item = {
            "id": next_id(profile),
            "type": "review",
            "subject": subject,
            "source": source,
            "content": content,
            "due": (start + timedelta(days=interval)).isoformat(),
            "interval": interval,
            "status": "pending",
            "created": today_iso(),
        }
        reviews.append(item)
        created.append(item)
    save(profile, "reviews", reviews)
    return created


def add_review(args: argparse.Namespace) -> None:
    start = parse_date(args.start)
    created = add_review_item(
        args.profile,
        args.subject,
        args.source,
        args.content,
        start=start,
    )
    print_json(created)


def pending(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item.get("status", "pending") == "pending"]


def done_task_ids(profile: str) -> set[str]:
    ids: set[str] = set()
    for key in ["courses", "exercises", "reviews", "backlog"]:
        for item in load(profile, key):
            if item.get("status") == "done" and item.get("id"):
                ids.add(item["id"])
    return ids


def is_unblocked(item: dict[str, Any], done_ids: set[str]) -> bool:
    return all(dep in done_ids for dep in item.get("depends_on", []))


def set_dependency(args: argparse.Namespace) -> None:
    deps = split_csv(args.depends_on)
    for key in ["courses", "exercises", "reviews", "backlog"]:
        items = load(args.profile, key)
        for item in items:
            if item.get("id") == args.task_id:
                item["depends_on"] = deps
                save(args.profile, key, items)
                print_json(item)
                return
    raise SystemExit(f"Task not found: {args.task_id}")


def priority_key(item: dict[str, Any]) -> tuple[int, str]:
    priority = int(item.get("priority", 3))
    created = item.get("created", "")
    return priority, created


def subject_group(subject: str, weights: dict[str, float]) -> str:
    for key in sorted(weights, key=len, reverse=True):
        if key.lower() in subject.lower():
            return key
    return subject


def subject_weight(item: dict[str, Any], weights: dict[str, float]) -> float:
    group = subject_group(item.get("subject", ""), weights)
    return float(weights.get(group, 0))


def weighted_key(item: dict[str, Any], weights: dict[str, float]) -> tuple[int, float, str]:
    priority = int(item.get("priority", 3))
    created = item.get("created", "")
    return priority, -subject_weight(item, weights), created


def select_diverse_tasks(
    candidates: list[dict[str, Any]], weights: dict[str, float], limit: int
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_groups: set[str] = set()
    remaining = sorted(candidates, key=lambda item: weighted_key(item, weights))

    for item in remaining:
        group = subject_group(item.get("subject", ""), weights)
        if group in used_groups:
            continue
        selected.append(item)
        used_groups.add(group)
        if len(selected) >= limit:
            return selected

    for item in remaining:
        if item["id"] in {task["id"] for task in selected}:
            continue
        selected.append(item)
        if len(selected) >= limit:
            return selected

    return selected


def due_reviews(profile: str, when: date) -> list[dict[str, Any]]:
    reviews = pending(load(profile, "reviews"))
    due: list[dict[str, Any]] = []
    for item in reviews:
        try:
            due_date = parse_date(item.get("due"))
        except ValueError:
            continue
        if due_date <= when:
            due.append(item)
    return sorted(due, key=lambda item: (item.get("due", ""), item.get("subject", "")))


def generate_today(args: argparse.Namespace) -> None:
    when = parse_date(args.date)
    weights = load(args.profile, "goals").get("priority_weights", {})
    done_ids = done_task_ids(args.profile)
    courses = sorted(
        [item for item in pending(load(args.profile, "courses")) if is_unblocked(item, done_ids)],
        key=lambda item: weighted_key(item, weights),
    )
    exercises = sorted(
        [item for item in pending(load(args.profile, "exercises")) if is_unblocked(item, done_ids)],
        key=lambda item: weighted_key(item, weights),
    )
    backlog = [item for item in pending(load(args.profile, "backlog")) if is_unblocked(item, done_ids)]
    reviews = due_reviews(args.profile, when)

    must_do: list[dict[str, Any]] = []
    must_do.extend(backlog[:1])
    candidates = courses + exercises
    candidates = [item for item in candidates if item["id"] not in {task["id"] for task in must_do}]
    must_do.extend(select_diverse_tasks(candidates, weights, 3 - len(must_do)))
    must_do = must_do[:3]

    optional_candidates = [item for item in courses + exercises if item["id"] not in {t["id"] for t in must_do}]
    optional = sorted(optional_candidates, key=lambda item: weighted_key(item, weights))
    output = {
        "date": when.isoformat(),
        "profile": args.profile,
        "today_must_do": must_do,
        "today_review": reviews[:8],
        "optional_extra": optional[:3],
        "minimum_version": build_minimum_version(must_do, reviews),
    }
    print_json(output)


def weekly_plan(args: argparse.Namespace) -> None:
    print_json(build_weekly_plan(args.profile, parse_date(args.start), args.days))


def commit_weekly_plan(args: argparse.Namespace) -> None:
    plan = build_weekly_plan(args.profile, parse_date(args.start), args.days)
    plan["committed_at"] = today_iso()
    save(args.profile, "current_week", plan)
    print_json(plan)


def build_weekly_plan(profile: str, start: date, days: int) -> dict[str, Any]:
    if days <= 0:
        days = days_until_sunday(start)
    weights = load(profile, "goals").get("priority_weights", {})
    simulated_done = done_task_ids(profile)
    remaining_courses = pending(load(profile, "courses"))
    remaining_exercises = pending(load(profile, "exercises"))
    remaining_backlog = pending(load(profile, "backlog"))
    remaining_reviews = pending(load(profile, "reviews"))
    plan_days: list[dict[str, Any]] = []

    for offset in range(days):
        when = start + timedelta(days=offset)
        available_backlog = [
            item for item in remaining_backlog if is_unblocked(item, simulated_done)
        ]
        available_courses = [
            item for item in remaining_courses if is_unblocked(item, simulated_done)
        ]
        available_exercises = [
            item for item in remaining_exercises if is_unblocked(item, simulated_done)
        ]

        must_do: list[dict[str, Any]] = []
        must_do.extend(sorted(available_backlog, key=priority_key)[:1])
        candidates = [
            item
            for item in available_courses + available_exercises
            if item["id"] not in {task["id"] for task in must_do}
        ]
        must_do.extend(select_diverse_tasks(candidates, weights, 3 - len(must_do)))
        must_do = must_do[:3]

        selected_ids = {item["id"] for item in must_do}
        simulated_done.update(selected_ids)
        remaining_courses = [item for item in remaining_courses if item["id"] not in selected_ids]
        remaining_exercises = [
            item for item in remaining_exercises if item["id"] not in selected_ids
        ]
        remaining_backlog = [item for item in remaining_backlog if item["id"] not in selected_ids]

        optional_candidates = [
            item
            for item in available_courses + available_exercises
            if item["id"] not in selected_ids
        ]
        optional = sorted(optional_candidates, key=lambda item: weighted_key(item, weights))[:3]
        reviews = local_due_reviews(remaining_reviews, when)[:8]
        review_ids = {item["id"] for item in reviews}
        remaining_reviews = [item for item in remaining_reviews if item["id"] not in review_ids]

        plan_days.append(
            {
                "date": when.isoformat(),
                "main_tasks": [plan_task_view(item) for item in must_do],
                "review_tasks": [plan_task_view(item) for item in reviews],
                "optional_extra": [plan_task_view(item) for item in optional],
                "minimum_version": build_minimum_version(must_do, reviews),
            }
        )

    return {
        "profile": profile,
        "start": start.isoformat(),
        "days": days,
        "plan": plan_days,
        "note": "Weekly plans simulate task completion for dependency ordering but do not update stored statuses.",
    }


def days_until_sunday(start: date) -> int:
    return 7 - start.weekday()


def plan_task_view(item: dict[str, Any]) -> dict[str, Any]:
    material = item.get("title") or item.get("resource") or item.get("source") or ""
    scope = item.get("chapter") or item.get("scope") or item.get("content") or ""
    action = item.get("slice") or item.get("task") or item.get("scope") or item.get("content") or scope
    quantity = task_quantity_text(item)
    acceptance = item.get("output") or item.get("acceptance") or ""
    range_parts = [
        item.get("page_range") and f"页码：{item.get('page_range')}",
        item.get("lecture_range") and f"讲次：{item.get('lecture_range')}",
        item.get("problem_range") and f"题号：{item.get('problem_range')}",
    ]
    precise_range = "；".join(part for part in range_parts if part)
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "subject": item.get("subject"),
        "task": action,
        "material": material,
        "scope": scope,
        "material_id": item.get("material_id", ""),
        "catalog_units": item.get("catalog_units", []),
        "page_range": item.get("page_range", ""),
        "lecture_range": item.get("lecture_range", ""),
        "problem_range": item.get("problem_range", ""),
        "precise_range": precise_range,
        "quantity": quantity,
        "acceptance": acceptance,
        "display_title": explicit_task_title(item, material, scope, action, quantity, acceptance),
        "output_or_acceptance": acceptance,
        "depends_on": item.get("depends_on", []),
        "priority": item.get("priority"),
    }


def task_quantity_text(item: dict[str, Any]) -> str:
    if item.get("type") == "course":
        minutes = item.get("estimated_minutes")
        return f"{minutes} 分钟" if minutes else "1 个课程切片"
    if item.get("type") == "exercise":
        quantity = item.get("quantity")
        mode = item.get("mode", "untimed")
        mode_text = "限时" if mode == "timed" else "不限时"
        return f"{quantity} 题，{mode_text}" if quantity else mode_text
    if item.get("type") == "review":
        interval = item.get("interval")
        return f"1 个复习项，{interval} 天间隔" if interval else "1 个复习项"
    return ""


def explicit_task_title(
    item: dict[str, Any],
    material: str,
    scope: str,
    action: str,
    quantity: str,
    acceptance: str,
) -> str:
    task_type = item.get("type")
    if task_type == "course":
        parts = [
            material or "specified course/material",
            scope or "specified section",
            quantity or "one course slice",
            action,
        ]
        title = " | ".join(part for part in parts if part)
        if acceptance:
            title += f" | 输出：{acceptance}"
        exercise = item.get("exercise")
        if exercise:
            title += f" | 配套练习：{exercise}"
        return title
    if task_type == "exercise":
        parts = [
            material or "specified question bank",
            scope or action or "specified scope",
            quantity,
        ]
        title = " | ".join(part for part in parts if part)
        if acceptance:
            title += f" | 验收：{acceptance}"
        return title
    if task_type == "review":
        parts = [
            material or "review queue",
            scope or action or "specified review content",
            quantity,
        ]
        return " | ".join(part for part in parts if part)
    return action or scope or material or item.get("id", "task")


def local_due_reviews(reviews: list[dict[str, Any]], when: date) -> list[dict[str, Any]]:
    due: list[dict[str, Any]] = []
    for item in reviews:
        try:
            due_date = parse_date(item.get("due"))
        except ValueError:
            continue
        if due_date <= when:
            due.append(item)
    return sorted(due, key=lambda item: (item.get("due", ""), item.get("subject", "")))


def build_minimum_version(
    must_do: list[dict[str, Any]], reviews: list[dict[str, Any]]
) -> list[str]:
    minimum: list[str] = []
    for item in must_do[:2]:
        if item.get("type") == "course":
            minimum.append(
                f"{item.get('subject')}：从《{item.get('title')}》{item.get('chapter')}完成 20 分钟，并写出 3 个关键点；验收：{item.get('output')}。"
            )
        elif item.get("type") == "exercise":
            quantity = max(5, int(item.get("quantity", 10)) // 3)
            minimum.append(
                f"{item.get('subject')}：做《{item.get('resource')}》{item.get('scope')} {quantity} 题，并订正错题。"
            )
        else:
            minimum.append(f"{item.get('subject', 'Study')}: make one small verifiable step.")
    if reviews:
        minimum.append("Review 1 due item and mark whether it still feels weak.")
    return minimum or ["Complete one 25-minute focused study task and log the result."]


def update_item_status(items: list[dict[str, Any]], task_id: str, status: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("id") == task_id:
            item["status"] = status
            item["updated"] = today_iso()
            return item
    return None


def log_progress(args: argparse.Namespace) -> None:
    found: dict[str, Any] | None = None
    found_key = ""
    for key in ["courses", "exercises", "reviews", "backlog"]:
        items = load(args.profile, key)
        found = update_item_status(items, args.task_id, args.status)
        if found:
            save(args.profile, key, items)
            found_key = key
            break

    logs = load(args.profile, "logs")
    entry = {
        "date": args.date or today_iso(),
        "task_id": args.task_id,
        "status": args.status,
        "accuracy": args.accuracy,
        "error_causes": split_csv(args.error_causes),
        "note": args.note or "",
    }
    replaced = False
    for idx, old in enumerate(logs):
        if old.get("date") == entry["date"] and old.get("task_id") == entry["task_id"]:
            logs[idx] = entry
            replaced = True
            break
    if not replaced:
        logs.append(entry)
    save(args.profile, "logs", logs)

    created_reviews: list[dict[str, Any]] = []
    if args.status in {"done", "partial"} and (args.review or args.accuracy is not None):
        subject = found.get("subject", "Study") if found else "Study"
        source = found.get("resource") or found.get("title") or args.task_id if found else args.task_id
        content = args.review or args.note or f"Review task {args.task_id}"
        created_reviews = add_review_item(args.profile, subject, source, content)

    if args.status in {"missed", "partial"} and found and found_key != "backlog":
        backlog = load(args.profile, "backlog")
        backlog_item = dict(found)
        backlog_item["status"] = "pending"
        backlog_item["backlog_reason"] = args.status
        backlog_item["backlog_date"] = today_iso()
        backlog.append(backlog_item)
        save(args.profile, "backlog", backlog)

    print_json(
        {
            "logged": entry,
            "replaced_existing_log": replaced,
            "updated_task": found,
            "created_reviews": created_reviews,
        }
    )


def weekly_review(args: argparse.Namespace) -> None:
    end = parse_date(args.end)
    start = end - timedelta(days=6)
    logs = [
        log
        for log in load(args.profile, "logs")
        if start <= parse_date(log.get("date")) <= end
    ]
    status_counts: dict[str, int] = {}
    accuracies: list[float] = []
    for log in logs:
        status = log.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if log.get("accuracy") is not None:
            accuracies.append(float(log["accuracy"]))

    done = status_counts.get("done", 0)
    total = len(logs)
    completion = round(done / total * 100, 1) if total else 0
    avg_accuracy = round(sum(accuracies) / len(accuracies), 1) if accuracies else None
    backlog = pending(load(args.profile, "backlog"))
    reviews = due_reviews(args.profile, end)

    output = {
        "range": f"{start.isoformat()} to {end.isoformat()}",
        "logged_tasks": total,
        "status_counts": status_counts,
        "completion_rate": completion,
        "average_accuracy": avg_accuracy,
        "pending_backlog": len(backlog),
        "due_reviews": len(reviews),
        "suggestion": weekly_suggestion(completion, avg_accuracy, len(backlog)),
    }
    print_json(output)


def weekly_suggestion(completion: float, accuracy: float | None, backlog_count: int) -> str:
    if backlog_count >= 5 or completion < 50:
        return "Reduce new input next week, keep review, and clear the highest-priority backlog first."
    if accuracy is not None and accuracy < 60:
        return "Return to basics and representative examples before adding large new exercise sets."
    if accuracy is not None and accuracy > 80 and completion >= 70:
        return "Increase mixed or timed practice while keeping scheduled review."
    return "Keep the current load, reserve one buffer block, and strengthen mistake rework."


def analytics_report(args: argparse.Namespace) -> None:
    end = parse_date(args.end)
    start = end - timedelta(days=args.days - 1)
    goals = load(args.profile, "goals")
    weights = goals.get("priority_weights", {})
    task_map = subject_task_map(args.profile)
    logs = [
        log
        for log in load(args.profile, "logs")
        if start <= parse_date(log.get("date")) <= end
    ]
    pending_tasks = [
        item for item in active_tasks(args.profile) if item.get("status", "pending") == "pending"
    ]

    daily = daily_completion_stats(logs, start, end)
    accuracy = accuracy_trends(logs, task_map, weights)
    errors = error_cause_stats(logs, task_map, weights)
    delay = delay_predictions(args.profile, end, weights, pending_tasks, logs)

    output = {
        "profile": args.profile,
        "range": f"{start.isoformat()} to {end.isoformat()}",
        "daily_completion": daily,
        "accuracy_trends": accuracy,
        "error_causes": errors,
        "delay_prediction": delay,
        "next_week_protect": protect_candidates(pending_tasks, weights),
        "next_week_cut_or_downgrade": cut_candidates(pending_tasks),
        "adjustment_advice": adjustment_advice(daily, accuracy, errors, delay),
    }
    print_json(output)


def blocked_report(args: argparse.Namespace) -> None:
    weights = load(args.profile, "goals").get("priority_weights", {})
    all_tasks = subject_task_map(args.profile)
    done_ids = done_task_ids(args.profile)
    blocked: list[dict[str, Any]] = []
    blocker_scores: dict[str, dict[str, Any]] = {}

    for task in active_tasks(args.profile):
        if task.get("status") != "pending":
            continue
        missing = [dep for dep in task.get("depends_on", []) if dep not in done_ids]
        if not missing:
            continue
        for dep in missing:
            score = blocker_scores.setdefault(dep, {"count": 0, "best_priority": 99, "weight": 0.0})
            score["count"] += 1
            score["best_priority"] = min(score["best_priority"], int(task.get("priority", 3)))
            score["weight"] = max(score["weight"], subject_weight(task, weights))
        blocked.append(
            {
                "task": compact_task(task),
                "missing_dependencies": [compact_task(all_tasks.get(dep, {"id": dep})) for dep in missing],
                "subject_group": subject_group(task.get("subject", "Unspecified"), weights),
            }
        )

    top_blockers = sorted(
        blocker_scores.items(),
        key=lambda item: (-item[1]["count"], item[1]["best_priority"], -item[1]["weight"]),
    )
    output = {
        "profile": args.profile,
        "blocked_count": len(blocked),
        "blocked_tasks": blocked,
        "top_blockers": [
            {
                "blocker": compact_task(all_tasks.get(task_id, {"id": task_id})),
                "blocks": score["count"],
                "best_blocked_priority": score["best_priority"],
            }
            for task_id, score in top_blockers[: args.limit]
        ],
        "suggestion": blocked_suggestion(top_blockers, all_tasks),
    }
    print_json(output)


def blocked_suggestion(
    top_blockers: list[tuple[str, dict[str, Any]]], all_tasks: dict[str, dict[str, Any]]
) -> str:
    if not top_blockers:
        return "No blocked pending tasks. Keep following the weighted plan."
    task_id, score = top_blockers[0]
    task = all_tasks.get(task_id, {"id": task_id})
    name = task.get("chapter") or task.get("scope") or task.get("slice") or task_id
    return f"Protect {task_id} ({name}) first; it unlocks {score['count']} pending task(s)."


def course_ratio_report(args: argparse.Namespace) -> None:
    source = args.source
    if source == "current-week":
        data = load(args.profile, "current_week")
        tasks = tasks_from_committed_week(data)
    elif source == "pending":
        tasks = active_tasks(args.profile)
    else:
        data = build_weekly_plan(args.profile, parse_date(args.start), args.days)
        tasks = tasks_from_committed_week(data)

    rows = course_ratio_rows(tasks)
    total = sum(row["count"] for row in rows.values())
    course_count = rows.get("course", {}).get("count", 0)
    course_ratio = round(course_count / total * 100, 1) if total else 0
    cap = args.cap
    output = {
        "profile": args.profile,
        "source": source,
        "course_ratio_percent": course_ratio,
        "course_cap_percent": cap,
        "by_type": rows,
        "status": "over_cap" if course_ratio > cap else "ok",
        "suggestion": course_ratio_suggestion(course_ratio, cap),
    }
    print_json(output)


def tasks_from_committed_week(data: Any) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for day in data.get("plan", []) if isinstance(data, dict) else []:
        for key in ["main_tasks", "review_tasks", "optional_extra"]:
            for item in day.get(key, []):
                tasks.append(item)
    return tasks


def course_ratio_rows(tasks: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    for task in tasks:
        task_type = task.get("type", "unknown")
        row = rows.setdefault(task_type, {"count": 0})
        row["count"] += 1
    return rows


def course_ratio_suggestion(course_ratio: float, cap: float) -> str:
    if course_ratio <= cap:
        return "Course input is within cap. Keep pairing courses with exercises and review."
    return "Course input is over cap. Move lower-priority lectures to optional extras and protect exercises, correction, and review."


def add_mistake(args: argparse.Namespace) -> None:
    mistakes = load(args.profile, "mistakes")
    mistake = {
        "id": next_id(args.profile).replace("T", "M"),
        "subject": args.subject,
        "source": args.source,
        "question": args.question,
        "knowledge": args.knowledge,
        "error_causes": split_csv(args.error_causes),
        "note": args.note or "",
        "status": "pending",
        "created": args.date or today_iso(),
    }
    mistakes.append(mistake)
    save(args.profile, "mistakes", mistakes)
    created_reviews = add_review_item(
        args.profile,
        args.subject,
        f"mistake:{mistake['id']} {args.source}",
        f"{args.question} - {args.knowledge} - {args.note}".strip(" -"),
        start=parse_date(args.date),
    )
    print_json({"mistake": mistake, "created_reviews": created_reviews})


def mistake_pack(args: argparse.Namespace) -> None:
    mistakes = load(args.profile, "mistakes")
    rows = [
        mistake
        for mistake in mistakes
        if (not args.subject or args.subject.lower() in mistake.get("subject", "").lower())
        and (not args.error_cause or args.error_cause in mistake.get("error_causes", []))
        and (not args.knowledge or args.knowledge.lower() in mistake.get("knowledge", "").lower())
        and mistake.get("status", "pending") == args.status
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for mistake in rows:
        key = mistake.get("knowledge") or "Unspecified"
        grouped.setdefault(key, []).append(mistake)
    print_json({"profile": args.profile, "count": len(rows), "groups": grouped})


def phase_report(args: argparse.Namespace) -> None:
    today = parse_date(args.date)
    goals = load(args.profile, "goals")
    deadline = parse_date(args.deadline or goals.get("deadline"))
    days_left = max((deadline - today).days, 0)
    inventory = inventory_counts(args.profile)
    course_ratio = current_course_ratio(args.profile)
    phase = infer_phase(days_left, inventory, course_ratio)
    output = {
        "profile": args.profile,
        "date": today.isoformat(),
        "deadline": deadline.isoformat(),
        "days_left": days_left,
        "phase": phase,
        "course_ratio_percent": course_ratio,
        "inventory": inventory,
        "rules": phase_rules(phase),
    }
    print_json(output)


def inventory_counts(profile: str) -> dict[str, int]:
    tasks = active_tasks(profile)
    return {
        "pending": sum(1 for item in tasks if item.get("status") == "pending"),
        "done": sum(1 for item in tasks if item.get("status") == "done"),
        "course_pending": sum(
            1 for item in tasks if item.get("type") == "course" and item.get("status") == "pending"
        ),
        "exercise_pending": sum(
            1 for item in tasks if item.get("type") == "exercise" and item.get("status") == "pending"
        ),
    }


def current_course_ratio(profile: str) -> float:
    data = load(profile, "current_week")
    tasks = tasks_from_committed_week(data)
    rows = course_ratio_rows(tasks)
    total = sum(row["count"] for row in rows.values())
    if not total:
        return 0
    return round(rows.get("course", {}).get("count", 0) / total * 100, 1)


def infer_phase(days_left: int, inventory: dict[str, int], course_ratio: float) -> str:
    if days_left <= 21:
        return "sprint"
    if days_left <= 60:
        return "past-exam"
    if inventory["course_pending"] > inventory["exercise_pending"] or course_ratio > 35:
        return "foundation-close"
    return "strengthening"


def phase_rules(phase: str) -> list[str]:
    rules = {
        "foundation-close": [
            "Close first-round gaps and start blank subjects.",
            "Keep course ratio at or below 40%.",
            "Every course slice must pair with output and practice.",
        ],
        "strengthening": [
            "Lower course ratio to 20%.",
            "Protect main question banks, mistakes, and review.",
            "Use extra teachers only for weak points.",
        ],
        "past-exam": [
            "Lower course ratio to 10%.",
            "Use timed past papers and theme analysis.",
            "Cut full supplemental resources into selective repair.",
        ],
        "sprint": [
            "Do not open large new content.",
            "Focus on mock exams, recitation, formulas/frameworks, and mistakes.",
            "Protect sleep and review stability.",
        ],
    }
    return rules[phase]


def week_audit(args: argparse.Namespace) -> None:
    current_week = load(args.profile, "current_week")
    if not current_week:
        raise SystemExit("No current_week.json found. Run commit-weekly-plan first.")
    start = parse_date(current_week.get("start"))
    end = start + timedelta(days=int(current_week.get("days", 7)) - 1)
    logs = [
        log
        for log in load(args.profile, "logs")
        if start <= parse_date(log.get("date")) <= end
    ]
    planned = planned_task_ids(current_week)
    done = {log["task_id"] for log in logs if log.get("status") == "done"}
    partial = {log["task_id"] for log in logs if log.get("status") == "partial"}
    missed = {log["task_id"] for log in logs if log.get("status") == "missed"}
    planned_done = planned & done
    planned_partial = planned & partial
    planned_missed = planned & missed
    unlogged = planned - done - partial - missed
    extra_done = done - planned

    pending_tasks = [
        item for item in active_tasks(args.profile) if item.get("status", "pending") == "pending"
    ]
    output = {
        "profile": args.profile,
        "range": f"{start.isoformat()} to {end.isoformat()}",
        "planned_count": len(planned),
        "planned_done": sorted(planned_done),
        "planned_partial": sorted(planned_partial),
        "planned_missed": sorted(planned_missed),
        "planned_unlogged": sorted(unlogged),
        "extra_done": sorted(extra_done),
        "planned_completion_rate": round(len(planned_done) / len(planned) * 100, 1)
        if planned
        else 0,
        "carryover_to_protect": [compact_task(item) for item in pending_tasks if item.get("id") in unlogged][:8],
        "cut_or_downgrade_candidates": cut_candidates(pending_tasks),
        "suggestion": week_audit_suggestion(len(planned_done), len(planned), len(unlogged), len(extra_done)),
    }
    print_json(output)


def next_week_plan(args: argparse.Namespace) -> None:
    current_week = load(args.profile, "current_week")
    if current_week:
        start = parse_date(current_week.get("start")) + timedelta(
            days=int(current_week.get("days", 7))
        )
    else:
        start = parse_date(args.start)
    audit = build_week_audit(args.profile)
    days = args.days if args.days > 0 else days_until_sunday(start)
    plan = build_weekly_plan(args.profile, start, days)
    protected_ids = {item.get("id") for item in audit.get("carryover_to_protect", [])}
    plan["source_audit"] = {
        "previous_range": audit.get("range"),
        "previous_completion_rate": audit.get("planned_completion_rate"),
        "carryover_to_protect": audit.get("carryover_to_protect", []),
        "cut_or_downgrade_candidates": audit.get("cut_or_downgrade_candidates", []),
    }
    plan["note"] = (
        "Generated for the next week using current pending tasks. Carryover IDs from the previous audit "
        f"should be protected when present: {sorted(protected_ids)}"
    )
    if args.commit:
        plan["committed_at"] = today_iso()
        save(args.profile, "current_week", plan)
    print_json(plan)


def build_week_audit(profile: str) -> dict[str, Any]:
    current_week = load(profile, "current_week")
    if not current_week:
        return {
            "range": "",
            "planned_completion_rate": 0,
            "carryover_to_protect": [],
            "cut_or_downgrade_candidates": [],
        }
    start = parse_date(current_week.get("start"))
    end = start + timedelta(days=int(current_week.get("days", 7)) - 1)
    logs = [log for log in load(profile, "logs") if start <= parse_date(log.get("date")) <= end]
    planned = planned_task_ids(current_week)
    done = {log["task_id"] for log in logs if log.get("status") == "done"}
    partial = {log["task_id"] for log in logs if log.get("status") == "partial"}
    missed = {log["task_id"] for log in logs if log.get("status") == "missed"}
    unlogged = planned - done - partial - missed
    pending_tasks = [item for item in active_tasks(profile) if item.get("status") == "pending"]
    return {
        "range": f"{start.isoformat()} to {end.isoformat()}",
        "planned_completion_rate": round(len(planned & done) / len(planned) * 100, 1)
        if planned
        else 0,
        "carryover_to_protect": [
            compact_task(item) for item in pending_tasks if item.get("id") in unlogged
        ][:8],
        "cut_or_downgrade_candidates": cut_candidates(pending_tasks),
    }


def planned_task_ids(current_week: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for day in current_week.get("plan", []):
        for key in ["main_tasks", "review_tasks", "optional_extra"]:
            for item in day.get(key, []):
                task_id = item.get("id")
                if task_id:
                    ids.add(task_id)
    return ids


def week_audit_suggestion(done: int, planned: int, unlogged: int, extra_done: int) -> str:
    if not planned:
        return "No planned tasks found. Commit a weekly plan before auditing."
    completion = done / planned * 100
    if completion < 50:
        return "Next week is overloaded or under-logged. Reduce must-do tasks and carry over only high-priority unfinished work."
    if unlogged > done:
        return "Many planned tasks are unlogged. Do a quick status pass before generating next week."
    if extra_done > done:
        return "Many completed tasks were outside the plan. Re-align next week around the actual path."
    return "Execution is usable. Carry over unfinished main tasks and keep the current structure."


def add_paper(args: argparse.Namespace) -> None:
    papers = load(args.profile, "papers")
    paper = {
        "id": next_id(args.profile).replace("T", "P"),
        "subject": args.subject,
        "name": args.name,
        "paper_type": args.paper_type,
        "year": args.year,
        "score": args.score,
        "total_score": args.total_score,
        "minutes": args.minutes,
        "wrong_count": args.wrong_count,
        "weak_topics": split_csv(args.weak_topics),
        "error_causes": split_csv(args.error_causes),
        "note": args.note or "",
        "date": args.date or today_iso(),
    }
    papers.append(paper)
    save(args.profile, "papers", papers)
    created_reviews: list[dict[str, Any]] = []
    for topic in paper["weak_topics"]:
        created_reviews.extend(
            add_review_item(args.profile, args.subject, f"paper:{paper['id']}", topic)
        )
    print_json({"paper": paper, "created_reviews": created_reviews})


def paper_report(args: argparse.Namespace) -> None:
    papers = [
        paper
        for paper in load(args.profile, "papers")
        if not args.subject or args.subject.lower() in paper.get("subject", "").lower()
    ]
    by_subject: dict[str, dict[str, Any]] = {}
    weak_topics: dict[str, int] = {}
    error_causes: dict[str, int] = {}
    for paper in papers:
        subject = paper.get("subject", "Unspecified")
        row = by_subject.setdefault(subject, {"count": 0, "scores": [], "avg_score": None})
        row["count"] += 1
        if paper.get("score") is not None:
            row["scores"].append(float(paper["score"]))
        for topic in paper.get("weak_topics", []):
            weak_topics[topic] = weak_topics.get(topic, 0) + 1
        for cause in paper.get("error_causes", []):
            error_causes[cause] = error_causes.get(cause, 0) + 1
    for row in by_subject.values():
        if row["scores"]:
            row["avg_score"] = round(sum(row["scores"]) / len(row["scores"]), 1)
    print_json(
        {
            "profile": args.profile,
            "paper_count": len(papers),
            "by_subject": by_subject,
            "weak_topics": dict(sorted(weak_topics.items(), key=lambda item: item[1], reverse=True)),
            "error_causes": dict(sorted(error_causes.items(), key=lambda item: item[1], reverse=True)),
        }
    )


def model_408_report(args: argparse.Namespace) -> None:
    tasks = active_tasks(args.profile)
    modules = load(args.profile, "modules")
    papers = load(args.profile, "papers")
    rows: dict[str, dict[str, Any]] = {}
    for subject, topics in MODEL_408.items():
        subject_tasks = [
            task for task in tasks if subject.lower() in task.get("subject", "").lower()
        ]
        subject_modules = [
            module for module in modules if subject.lower() in module.get("subject", "").lower()
        ]
        subject_papers = [
            paper for paper in papers if subject.lower() in paper.get("subject", "").lower()
        ]
        topic_rows: dict[str, dict[str, Any]] = {}
        for topic, weight in topics.items():
            related_tasks = [
                task for task in subject_tasks if topic_match(topic, task.get("chapter", ""), task.get("scope", ""), task.get("slice", ""))
            ]
            related_modules = [
                module for module in subject_modules if topic_match(topic, module.get("name", ""))
            ]
            related_papers = [
                paper
                for paper in subject_papers
                if any(topic_match(topic, weak) for weak in paper.get("weak_topics", []))
            ]
            done = sum(1 for task in related_tasks if task.get("status") == "done")
            pending = sum(1 for task in related_tasks if task.get("status") == "pending")
            risk = "yellow" if pending == 0 and done == 0 else "green"
            if related_papers:
                risk = "yellow"
            topic_rows[topic] = {
                "weight": weight,
                "task_count": len(related_tasks),
                "done": done,
                "pending": pending,
                "module_count": len(related_modules),
                "paper_weak_hits": len(related_papers),
                "risk": risk,
            }
        rows[subject] = {"topics": topic_rows}
    print_json({"profile": args.profile, "model": rows})


def topic_match(topic: str, *texts: str) -> bool:
    normalized_topic = topic.lower().replace("-", " ")
    aliases = {
        "process threads": ["process", "thread", "进程", "线程"],
        "scheduling pv": ["scheduling", "pv", "调度", "同步", "互斥"],
        "memory management": ["memory", "paging", "segmentation", "内存", "页", "段"],
        "network layer": ["network layer", "ip", "routing", "网络层"],
        "transport layer": ["transport", "tcp", "udp", "传输层"],
        "data link": ["data link", "mac", "数据链路"],
        "tree": ["tree", "b tree", "树"],
        "graph": ["graph", "critical path", "图", "关键路径"],
        "cpu": ["cpu", "processor", "中央处理器"],
        "memory": ["cache", "memory", "存储"],
    }
    candidates = [normalized_topic] + aliases.get(normalized_topic, [])
    haystack = " ".join(text.lower() for text in texts if text)
    return any(candidate.lower() in haystack for candidate in candidates)


def daily_completion_stats(
    logs: list[dict[str, Any]], start: date, end: date
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    days = (end - start).days + 1
    for offset in range(days):
        current = start + timedelta(days=offset)
        day_logs = [log for log in logs if parse_date(log.get("date")) == current]
        total = len(day_logs)
        done = sum(1 for log in day_logs if log.get("status") == "done")
        partial = sum(1 for log in day_logs if log.get("status") == "partial")
        missed = sum(1 for log in day_logs if log.get("status") == "missed")
        completion = round(done / total * 100, 1) if total else None
        result.append(
            {
                "date": current.isoformat(),
                "logged": total,
                "done": done,
                "partial": partial,
                "missed": missed,
                "completion_rate": completion,
            }
        )
    return result


def accuracy_trends(
    logs: list[dict[str, Any]],
    task_map: dict[str, dict[str, Any]],
    weights: dict[str, float],
) -> dict[str, Any]:
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for log in logs:
        if log.get("accuracy") is None:
            continue
        task = task_map.get(log.get("task_id"), {})
        subject = subject_group(task.get("subject", "Unspecified"), weights)
        by_subject.setdefault(subject, []).append(
            {"date": log.get("date"), "accuracy": float(log["accuracy"])}
        )

    result: dict[str, Any] = {}
    for subject, rows in by_subject.items():
        rows = sorted(rows, key=lambda row: row["date"])
        first = rows[0]["accuracy"]
        last = rows[-1]["accuracy"]
        avg = round(sum(row["accuracy"] for row in rows) / len(rows), 1)
        result[subject] = {
            "average": avg,
            "first": first,
            "last": last,
            "delta": round(last - first, 1),
            "points": rows,
        }
    return result


def error_cause_stats(
    logs: list[dict[str, Any]],
    task_map: dict[str, dict[str, Any]],
    weights: dict[str, float],
) -> dict[str, Any]:
    total: dict[str, int] = {}
    by_subject: dict[str, dict[str, int]] = {}
    for log in logs:
        causes = log.get("error_causes") or []
        if not causes:
            continue
        task = task_map.get(log.get("task_id"), {})
        subject = subject_group(task.get("subject", "Unspecified"), weights)
        subject_counts = by_subject.setdefault(subject, {})
        for cause in causes:
            total[cause] = total.get(cause, 0) + 1
            subject_counts[cause] = subject_counts.get(cause, 0) + 1
    return {"total": total, "by_subject": by_subject}


def delay_predictions(
    profile: str,
    today: date,
    weights: dict[str, float],
    pending_tasks: list[dict[str, Any]],
    logs: list[dict[str, Any]],
) -> dict[str, Any]:
    goals = load(profile, "goals")
    deadline = parse_date(goals.get("deadline"))
    remaining_weeks = max((deadline - today).days / 7, 0.1)
    pending_counts = pending_by_subject(pending_tasks, weights)
    recent_done = recent_done_from_logs(logs, subject_task_map(profile), weights)
    predictions: dict[str, Any] = {}

    for subject, pending_count in pending_counts.items():
        weekly_velocity = recent_done.get(subject, 0)
        required = pending_count / remaining_weeks
        if weekly_velocity <= 0:
            predicted_weeks = None
            risk = "yellow"
        else:
            predicted_weeks = round(pending_count / weekly_velocity, 1)
            risk = "red" if predicted_weeks > remaining_weeks else "green"
            if weekly_velocity < required * 0.7:
                risk = "yellow" if risk == "green" else risk
        predictions[subject] = {
            "pending_units": pending_count,
            "recent_weekly_velocity": weekly_velocity,
            "required_weekly_velocity": round(required, 2),
            "predicted_weeks_to_clear": predicted_weeks,
            "remaining_weeks": round(remaining_weeks, 1),
            "risk": risk,
        }
    return predictions


def recent_done_from_logs(
    logs: list[dict[str, Any]],
    task_map: dict[str, dict[str, Any]],
    weights: dict[str, float],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for log in logs:
        if log.get("status") != "done":
            continue
        task = task_map.get(log.get("task_id"), {})
        subject = subject_group(task.get("subject", "Unspecified"), weights)
        result[subject] = result.get(subject, 0) + 1
    return result


def adjustment_advice(
    daily: list[dict[str, Any]],
    accuracy: dict[str, Any],
    errors: dict[str, Any],
    delay: dict[str, Any],
) -> list[str]:
    advice: list[str] = []
    logged_days = [day for day in daily if day["logged"]]
    if logged_days:
        avg_completion = sum(day["completion_rate"] for day in logged_days) / len(logged_days)
        if avg_completion < 60:
            advice.append("Reduce next week's must-do count or move lower-priority tasks to optional extras.")
    for subject, stats in accuracy.items():
        if stats["average"] < 60:
            advice.append(f"{subject}: accuracy is below 60%; return to examples and smaller targeted sets.")
        elif stats["delta"] < -10:
            advice.append(f"{subject}: accuracy is dropping; schedule mistake rework before new input.")
    top_errors = sorted(
        errors.get("total", {}).items(), key=lambda item: item[1], reverse=True
    )[:3]
    if top_errors:
        causes = ", ".join(cause for cause, _ in top_errors)
        advice.append(f"Top error causes: {causes}; convert them into next week's review tasks.")
    for subject, stats in delay.items():
        if stats["risk"] == "red":
            advice.append(f"{subject}: predicted delay risk is red; cut supplemental tasks and protect main path.")
        elif stats["risk"] == "yellow":
            advice.append(f"{subject}: no recent completion or slow pace; protect one concrete task next week.")
    return advice or ["Keep current load, protect review/correction, and continue logging accuracy and error causes."]


def active_tasks(profile: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for key in ["courses", "exercises", "backlog"]:
        tasks.extend(load(profile, key))
    return tasks


def subject_task_map(profile: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key in ["courses", "exercises", "reviews", "backlog"]:
        for item in load(profile, key):
            if "id" in item:
                result[item["id"]] = item
    return result


def inventory_report(args: argparse.Namespace) -> None:
    weights = load(args.profile, "goals").get("priority_weights", {})
    rows: dict[str, dict[str, Any]] = {}

    for item in active_tasks(args.profile):
        group = subject_group(item.get("subject", "Unspecified"), weights)
        row = rows.setdefault(
            group,
            {"total": 0, "pending": 0, "done": 0, "partial": 0, "missed": 0, "by_type": {}},
        )
        status = item.get("status", "pending")
        task_type = item.get("type", "task")
        row["total"] += 1
        row[status] = row.get(status, 0) + 1
        row["by_type"][task_type] = row["by_type"].get(task_type, 0) + 1

    reviews = load(args.profile, "reviews")
    review_rows: dict[str, int] = {}
    for item in reviews:
        if item.get("status", "pending") != "pending":
            continue
        group = subject_group(item.get("subject", "Unspecified"), weights)
        review_rows[group] = review_rows.get(group, 0) + 1

    print_json({"profile": args.profile, "inventory": rows, "pending_reviews": review_rows})


def control_report(args: argparse.Namespace) -> None:
    goals = load(args.profile, "goals")
    weights = goals.get("priority_weights", {})
    deadline = parse_date(args.deadline or goals.get("deadline"))
    today = parse_date(args.date)
    remaining_days = max((deadline - today).days, 0)
    remaining_weeks = max(remaining_days / 7, 0.1)

    tasks = active_tasks(args.profile)
    pending_tasks = [item for item in tasks if item.get("status", "pending") == "pending"]
    completed_recent = recent_completed_by_subject(args.profile, today, weights, days=7)
    inventory_by_subject = pending_by_subject(pending_tasks, weights)
    subject_reports: dict[str, dict[str, Any]] = {}

    for subject, pending_count in inventory_by_subject.items():
        required = pending_count / remaining_weeks
        actual = completed_recent.get(subject, 0)
        risk = risk_level(pending_count, required, actual, remaining_weeks)
        subject_reports[subject] = {
            "pending_units": pending_count,
            "required_weekly_burndown": round(required, 2),
            "actual_completed_last_7_days": actual,
            "risk": risk,
        }

    output = {
        "profile": args.profile,
        "deadline": deadline.isoformat(),
        "remaining_days": remaining_days,
        "remaining_weeks": round(remaining_weeks, 1),
        "overall_risk": overall_risk(subject_reports),
        "subjects": subject_reports,
        "tasks_to_protect": protect_candidates(pending_tasks, weights),
        "cut_or_downgrade_candidates": cut_candidates(pending_tasks),
        "rule": "If risk is yellow/red, reduce optional course watching and supplemental books before cutting review, correction, main question banks, or past papers.",
    }
    print_json(output)


def pending_by_subject(
    pending_tasks: list[dict[str, Any]], weights: dict[str, float]
) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in pending_tasks:
        group = subject_group(item.get("subject", "Unspecified"), weights)
        result[group] = result.get(group, 0) + 1
    return result


def recent_completed_by_subject(
    profile: str, today: date, weights: dict[str, float], days: int
) -> dict[str, int]:
    start = today - timedelta(days=days - 1)
    task_map = subject_task_map(profile)
    result: dict[str, int] = {}
    for log in load(profile, "logs"):
        if log.get("status") != "done":
            continue
        try:
            log_date = parse_date(log.get("date"))
        except ValueError:
            continue
        if not (start <= log_date <= today):
            continue
        task = task_map.get(log.get("task_id"), {})
        group = subject_group(task.get("subject", "Unspecified"), weights)
        result[group] = result.get(group, 0) + 1
    return result


def risk_level(
    pending_count: int, required_weekly: float, actual_weekly: int, remaining_weeks: float
) -> str:
    if pending_count == 0:
        return "green"
    if remaining_weeks <= 3 and pending_count > actual_weekly * max(remaining_weeks, 1):
        return "red"
    if actual_weekly == 0:
        return "yellow"
    if actual_weekly < required_weekly * 0.4:
        return "red"
    if actual_weekly < required_weekly * 0.7:
        return "yellow"
    return "green"


def overall_risk(subject_reports: dict[str, dict[str, Any]]) -> str:
    risks = [report["risk"] for report in subject_reports.values()]
    if "red" in risks:
        return "red"
    if "yellow" in risks:
        return "yellow"
    return "green"


def protect_candidates(
    pending_tasks: list[dict[str, Any]], weights: dict[str, float], limit: int = 8
) -> list[dict[str, Any]]:
    sorted_tasks = sorted(
        pending_tasks,
        key=lambda item: (int(item.get("priority", 3)), -subject_weight(item, weights)),
    )
    return [compact_task(item) for item in sorted_tasks[:limit]]


def cut_candidates(pending_tasks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in pending_tasks
        if int(item.get("priority", 3)) >= 3
        or "supplement" in item.get("resource", "").lower()
        or "extra" in item.get("resource", "").lower()
    ]
    candidates = sorted(candidates, key=lambda item: (-int(item.get("priority", 3)), item.get("created", "")))
    return [compact_task(item) for item in candidates[:limit]]


def compact_task(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "subject": item.get("subject"),
        "title_or_resource": item.get("title") or item.get("resource"),
        "chapter_or_scope": item.get("chapter") or item.get("scope"),
        "priority": item.get("priority"),
    }


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Study Planner JSON store")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--profile", default="default")
    init.add_argument("--goal", required=True)
    init.add_argument("--deadline", required=True)
    init.add_argument("--subjects", default="")
    init.add_argument("--weights", default="")
    init.add_argument("--notes", default="")
    init.set_defaults(func=init_profile)

    weights = sub.add_parser("set-weights")
    weights.add_argument("--profile", default="default")
    weights.add_argument("--weights", required=True)
    weights.set_defaults(func=set_weights)

    material = sub.add_parser("add-material")
    material.add_argument("--profile", default="default")
    material.add_argument("--material-id", default="")
    material.add_argument("--name", required=True)
    material.add_argument("--kind", choices=["book", "exercise-book", "course", "paper-set", "app", "handout", "other"], default="book")
    material.add_argument("--subject", default="")
    material.add_argument("--edition", default="")
    material.add_argument("--teacher", default="")
    material.add_argument("--source", default="")
    material.add_argument("--catalog-source", default="")
    material.add_argument("--catalog", default="", help="Semicolon-separated units: id|title|page_range|lecture_range|problem_range|parent")
    material.add_argument("--notes", default="")
    material.set_defaults(func=add_material)

    material_report_parser = sub.add_parser("material-report")
    material_report_parser.add_argument("--profile", default="default")
    material_report_parser.set_defaults(func=material_report)

    catalog_audit_parser = sub.add_parser("catalog-audit")
    catalog_audit_parser.add_argument("--profile", default="default")
    catalog_audit_parser.add_argument("--all", action="store_true")
    catalog_audit_parser.set_defaults(func=catalog_audit)

    course = sub.add_parser("add-course")
    course.add_argument("--profile", default="default")
    course.add_argument("--subject", required=True)
    course.add_argument("--title", required=True)
    course.add_argument("--chapter", default="")
    course.add_argument("--material-id", default="")
    course.add_argument("--catalog-units", default="")
    course.add_argument("--page-range", default="")
    course.add_argument("--lecture-range", default="")
    course.add_argument("--problem-range", default="")
    course.add_argument("--slice", required=True)
    course.add_argument("--minutes", type=int, default=45)
    course.add_argument("--output", required=True)
    course.add_argument("--exercise", default="")
    course.add_argument("--depends-on", default="")
    course.add_argument("--priority", type=int, default=2)
    course.set_defaults(func=add_course)

    exercise = sub.add_parser("add-exercise")
    exercise.add_argument("--profile", default="default")
    exercise.add_argument("--subject", required=True)
    exercise.add_argument("--resource", required=True)
    exercise.add_argument("--scope", required=True)
    exercise.add_argument("--material-id", default="")
    exercise.add_argument("--catalog-units", default="")
    exercise.add_argument("--page-range", default="")
    exercise.add_argument("--lecture-range", default="")
    exercise.add_argument("--problem-range", default="")
    exercise.add_argument("--quantity", type=int, required=True)
    exercise.add_argument("--mode", choices=["timed", "untimed"], default="untimed")
    exercise.add_argument("--acceptance", default="")
    exercise.add_argument("--depends-on", default="")
    exercise.add_argument("--priority", type=int, default=2)
    exercise.set_defaults(func=add_exercise)

    module = sub.add_parser("add-module")
    module.add_argument("--profile", default="default")
    module.add_argument("--template", required=True)
    module.add_argument("--name", required=True)
    module.add_argument("--subject", default="")
    module.add_argument("--course-title", default="")
    module.add_argument("--course-slice", default="")
    module.add_argument("--minutes", type=int)
    module.add_argument("--output", default="")
    module.add_argument("--exercise", default="")
    module.add_argument("--exercise-resource", default="")
    module.add_argument("--exercise-scope", default="")
    module.add_argument("--quantity", type=int)
    module.add_argument("--mode", choices=["timed", "untimed"], default="untimed")
    module.add_argument("--acceptance", default="")
    module.add_argument("--depends-on", default="")
    module.add_argument("--weak-points", default="")
    module.add_argument("--priority", type=int)
    module.add_argument("--notes", default="")
    module.set_defaults(func=add_module)

    module_report_parser = sub.add_parser("module-report")
    module_report_parser.add_argument("--profile", default="default")
    module_report_parser.set_defaults(func=module_report)

    dependency = sub.add_parser("set-dependency")
    dependency.add_argument("--profile", default="default")
    dependency.add_argument("--task-id", required=True)
    dependency.add_argument("--depends-on", required=True)
    dependency.set_defaults(func=set_dependency)

    review = sub.add_parser("add-review")
    review.add_argument("--profile", default="default")
    review.add_argument("--subject", required=True)
    review.add_argument("--source", required=True)
    review.add_argument("--content", required=True)
    review.add_argument("--start", default="")
    review.set_defaults(func=add_review)

    today = sub.add_parser("today")
    today.add_argument("--profile", default="default")
    today.add_argument("--date", default="")
    today.set_defaults(func=generate_today)

    week_plan = sub.add_parser("weekly-plan")
    week_plan.add_argument("--profile", default="default")
    week_plan.add_argument("--start", default="")
    week_plan.add_argument("--days", type=int, default=0)
    week_plan.set_defaults(func=weekly_plan)

    commit_week = sub.add_parser("commit-weekly-plan")
    commit_week.add_argument("--profile", default="default")
    commit_week.add_argument("--start", default="")
    commit_week.add_argument("--days", type=int, default=0)
    commit_week.set_defaults(func=commit_weekly_plan)

    log = sub.add_parser("log")
    log.add_argument("--profile", default="default")
    log.add_argument("--task-id", required=True)
    log.add_argument("--status", choices=["done", "partial", "missed"], required=True)
    log.add_argument("--accuracy", type=float)
    log.add_argument("--error-causes", default="")
    log.add_argument("--note", default="")
    log.add_argument("--review", default="")
    log.add_argument("--date", default="")
    log.set_defaults(func=log_progress)

    weekly = sub.add_parser("weekly")
    weekly.add_argument("--profile", default="default")
    weekly.add_argument("--end", default="")
    weekly.set_defaults(func=weekly_review)

    inventory = sub.add_parser("inventory")
    inventory.add_argument("--profile", default="default")
    inventory.set_defaults(func=inventory_report)

    control = sub.add_parser("control-report")
    control.add_argument("--profile", default="default")
    control.add_argument("--deadline", default="")
    control.add_argument("--date", default="")
    control.set_defaults(func=control_report)

    analytics = sub.add_parser("analytics-report")
    analytics.add_argument("--profile", default="default")
    analytics.add_argument("--end", default="")
    analytics.add_argument("--days", type=int, default=7)
    analytics.set_defaults(func=analytics_report)

    blocked = sub.add_parser("blocked-report")
    blocked.add_argument("--profile", default="default")
    blocked.add_argument("--limit", type=int, default=8)
    blocked.set_defaults(func=blocked_report)

    course_ratio = sub.add_parser("course-ratio-report")
    course_ratio.add_argument("--profile", default="default")
    course_ratio.add_argument("--source", choices=["current-week", "pending", "preview"], default="current-week")
    course_ratio.add_argument("--start", default="")
    course_ratio.add_argument("--days", type=int, default=7)
    course_ratio.add_argument("--cap", type=float, default=40)
    course_ratio.set_defaults(func=course_ratio_report)

    mistake = sub.add_parser("add-mistake")
    mistake.add_argument("--profile", default="default")
    mistake.add_argument("--subject", required=True)
    mistake.add_argument("--source", required=True)
    mistake.add_argument("--question", required=True)
    mistake.add_argument("--knowledge", required=True)
    mistake.add_argument("--error-causes", default="")
    mistake.add_argument("--note", default="")
    mistake.add_argument("--date", default="")
    mistake.set_defaults(func=add_mistake)

    pack = sub.add_parser("mistake-pack")
    pack.add_argument("--profile", default="default")
    pack.add_argument("--subject", default="")
    pack.add_argument("--error-cause", default="")
    pack.add_argument("--knowledge", default="")
    pack.add_argument("--status", choices=["pending", "done"], default="pending")
    pack.set_defaults(func=mistake_pack)

    phase = sub.add_parser("phase-report")
    phase.add_argument("--profile", default="default")
    phase.add_argument("--date", default="")
    phase.add_argument("--deadline", default="")
    phase.set_defaults(func=phase_report)

    audit = sub.add_parser("week-audit")
    audit.add_argument("--profile", default="default")
    audit.set_defaults(func=week_audit)

    next_week = sub.add_parser("next-week-plan")
    next_week.add_argument("--profile", default="default")
    next_week.add_argument("--start", default="")
    next_week.add_argument("--days", type=int, default=0)
    next_week.add_argument("--commit", action="store_true")
    next_week.set_defaults(func=next_week_plan)

    paper = sub.add_parser("add-paper")
    paper.add_argument("--profile", default="default")
    paper.add_argument("--subject", required=True)
    paper.add_argument("--name", required=True)
    paper.add_argument("--paper-type", choices=["past-paper", "mock", "section"], default="mock")
    paper.add_argument("--year", type=int)
    paper.add_argument("--score", type=float)
    paper.add_argument("--total-score", type=float)
    paper.add_argument("--minutes", type=int)
    paper.add_argument("--wrong-count", type=int)
    paper.add_argument("--weak-topics", default="")
    paper.add_argument("--error-causes", default="")
    paper.add_argument("--note", default="")
    paper.add_argument("--date", default="")
    paper.set_defaults(func=add_paper)

    paper_report_parser = sub.add_parser("paper-report")
    paper_report_parser.add_argument("--profile", default="default")
    paper_report_parser.add_argument("--subject", default="")
    paper_report_parser.set_defaults(func=paper_report)

    model_408 = sub.add_parser("408-model-report")
    model_408.add_argument("--profile", default="default")
    model_408.set_defaults(func=model_408_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
