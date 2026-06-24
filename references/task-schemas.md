# Task Schemas

## Study Profile

```json
{
  "goal": "2027 postgraduate entrance exam",
  "deadline": "2026-12-20",
  "subjects": ["Math", "English", "Politics", "Major"],
  "baseline": {"Math": "weak", "English": "medium"},
  "availability": {"weekday_hours": 5, "weekend_hours": 8},
  "priority": ["Math", "Major"]
}
```

## Course Task

```json
{
  "type": "course",
  "subject": "Math",
  "course": "Advanced Math foundation",
  "chapter": "Limits",
  "slice": "definition and properties",
  "page_range": "P12-P24",
  "lecture_range": "Lecture 3-4",
  "problem_range": "",
  "estimated_minutes": 45,
  "output": "5-point summary + 2 example methods",
  "exercise": "660 limits 25 questions",
  "depends_on": [],
  "status": "pending"
}
```

## Exercise Task

```json
{
  "type": "exercise",
  "subject": "Math",
  "resource": "660",
  "scope": "limits",
  "page_range": "",
  "lecture_range": "",
  "problem_range": "#1-25",
  "quantity": 25,
  "mode": "untimed",
  "acceptance": "all wrong questions corrected with error causes",
  "depends_on": ["T001"],
  "status": "pending"
}
```

## Weekly Plan

```json
{
  "date": "2026-06-24",
  "main_tasks": [],
  "review_tasks": [],
  "optional_extra": [],
  "minimum_version": []
}
```

Weekly plans should layer tasks rather than produce an hour-by-hour grid.

Every weekly task should carry the most exact range available. Use `page_range` for book pages, `lecture_range` for course lecture numbers or video ranges, and `problem_range` for exercise IDs or question numbers. If the exact range is unknown, write a visible placeholder such as `"待补充题号范围"` and ask for the missing catalog instead of hiding it in vague wording.

Commit a weekly plan when the user wants future review to compare planned tasks against actual logs:

```bash
python scripts/study_store.py commit-weekly-plan --profile default --start 2026-06-24 --days 7
```

## Review Item

```json
{
  "subject": "Math",
  "source": "660 limits mistakes",
  "content": "5 wrong questions about limit existence",
  "due": "2026-06-27",
  "interval": 3,
  "status": "pending"
}
```

## Daily Log

```json
{
  "date": "2026-06-24",
  "completed": ["T001"],
  "partial": ["T002"],
  "missed": ["T003"],
  "accuracy": {"T001": 72},
  "error_causes": {"T001": ["concept", "calculation"]},
  "notes": "Concept confusion in limit existence."
}
```

## Error Causes

Use short tags:

- concept
- formula
- method
- calculation
- reading
- memory
- timing
- careless

For English tasks, add tags such as vocabulary, long-sentence, option-trap, locating.

## Mistake

```json
{
  "id": "M001",
  "subject": "Math II",
  "source": "660",
  "question": "limits #12",
  "page_range": "P36",
  "problem_range": "#12",
  "knowledge": "limit existence",
  "error_causes": ["concept", "method"],
  "status": "pending"
}
```

Mistakes should also generate review items whose `source` contains `mistake:<id>` so the dashboard can build the mistake rework calendar.

## Module

```json
{
  "id": "MOD001",
  "template": "408-os",
  "name": "Memory management",
  "subject": "408 - Operating System",
  "depends_on": ["T008"],
  "status": "pending"
}
```

`add-module` creates a module plus a course task and exercise task. The exercise depends on the generated course task by default.

## Weekly Review

```text
Completion:
Course progress:
Exercise progress:
Accuracy:
Review queue:
Main problems:
Next week adjustment:
```
