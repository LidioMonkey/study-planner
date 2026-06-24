# Planning Rules

## Task-First Planning

Default to task lists rather than hour-by-hour schedules. Use time blocks only for fixed availability, mock exams, focused writing, Pomodoro execution, or reminders.

A good task is verifiable:

- Bad: study math.
- Good: finish 25 limit questions, correct all wrong answers, and write 3 method notes.

## Daily Limits

- Use 1-3 must-do tasks.
- Include due review separately from new learning.
- Add optional tasks only after the must-do plan is realistic.
- Always provide a minimum version for disrupted days.
- Do not plan a perfect day unless the user explicitly asks for a stretch plan.

## Course Slice Method

Course-heavy study should be split into 30-60 minute slices. Each slice needs:

- Course name and chapter
- Slice topic
- Output
- Matching practice when possible
- Review trigger

If courses fall behind, compress low-value watching first. Do not delete correction, review, or representative practice.

## Exercise-Book Method

Treat books and question banks as training pools:

- Foundation consolidation
- Type training
- Mixed strengthening
- Past exam/mock training
- Mistake rework

Each exercise task must include quantity, scope, correction, error diagnosis, and follow-up.

## Accuracy-Based Adjustment

- Below 60%: pause large new-question volume; return to examples, notes, course basics, and small targeted sets.
- 60-80%: continue chapter work; add mistake rework and method summaries.
- Above 80%: use mixed, timed, or past-exam practice.

## Backlog Rules

Unfinished tasks go into backlog, not into shame. When backlog grows:

- Drop optional extras first.
- Merge similar review tasks.
- Convert low-value tasks into minimum versions.
- Keep one weekly buffer block.
- Protect review and correction before new input.

## Review Cadence

Default intervals:

- Same day
- 1 day
- 3 days
- 7 days
- 14 days
- 30 days

Use shorter intervals for high-error or memory-heavy items.

## Weekly Audit

When a weekly plan has been committed, compare the committed plan against logs before generating the next week:

- Planned done
- Planned partial
- Planned missed
- Planned but unlogged
- Extra completed outside the plan
- Carryover tasks to protect
- Tasks to cut or downgrade

If planned completion is below 50%, reduce next week's must-do load before adding new material.

Generate the next week after audit when the user wants rolling planning:

```bash
python scripts/study_store.py next-week-plan --profile default
python scripts/study_store.py next-week-plan --profile default --commit
```

Use `--commit` only after reviewing the generated plan.
