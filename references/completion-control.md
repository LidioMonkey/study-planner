# Completion Control

Use this reference when the user asks how to ensure all exam preparation can finish before the test date, or when a long-term plan needs deadline control.

## Core Principle

Do not ensure completion by filling every day with time blocks. Ensure completion by:

1. Building a total task inventory.
2. Reverse-planning from the deadline.
3. Tracking weekly burn-down.
4. Adding buffers.
5. Cutting low-value tasks when risk appears.

## Task Inventory

Break every subject into countable units:

- Course slices
- Chapter tasks
- Exercise sets of 20-30 questions
- Past papers or mock papers
- Mistake rework packs
- Recitation rounds
- Vocabulary/review batches

Avoid vague inventory items like "review math" or "finish 408". Convert them into units that can be counted and closed.

## Reverse Planning

Work backward from the exam date. Reserve the final sprint for review, mock exams, recitation, and mistakes; do not plan large new content there unless the user explicitly accepts the risk.

Default phases for postgraduate entrance exam preparation:

- **Foundation close**: finish first-round gaps and start blank subjects.
- **Strengthening**: main question banks, method summaries, mistake rework.
- **Past exam phase**: timed past papers, theme analysis, weak-point repair.
- **Sprint**: mock exams, recitation, formulas/framework recall, final mistakes.

## Weekly Burn-Down

Each weekly review should estimate:

```text
remaining task units / remaining weeks = minimum weekly burn-down
```

Track by subject, not only globally. A good global completion rate can hide an empty subject.

Use these signals:

- Planned units this week
- Completed units this week
- Remaining units
- Remaining weeks
- Required weekly pace
- Actual weekly pace
- Backlog growth

## Risk Levels

### Green

- Actual weekly pace is at or above required pace.
- No high-weight subject is empty or ignored.
- Backlog is stable.

Action: keep the plan and preserve buffer.

### Yellow

- A subject is below 70% of required weekly pace for 2 consecutive weeks.
- Backlog grows but is still recoverable.
- Review or correction is being squeezed by new input.

Action:

- Reduce optional extras.
- Merge or shrink low-yield tasks.
- Add one buffer block.
- Protect review and correction.

### Red

- A high-weight subject is more than 2 weeks behind.
- A blank subject remains unstarted after its start deadline.
- Required weekly pace becomes unrealistic under the user's available hours.

Action:

- Cut non-main resources.
- Stop full coverage of supplemental books.
- Keep only main textbook/lecture, core question bank, past papers, and mistakes.
- Convert some materials into selective weak-point practice.

## Cut-Line Rules

When there are too many resources, rank them:

1. Main syllabus or main textbook
2. Main question bank
3. Past papers
4. Mistakes and weak points
5. Supplemental books and extra teachers

If time is tight, cut from the bottom first.

For postgraduate entrance exam preparation:

- Extra question banks become selective weak-point pools.
- Extra teachers are used only for weak chapters.
- Full textbook reading is replaced by framework notes when late.
- New content is not introduced in the final sprint unless it is critical and small.

## Buffer Rules

- Keep at least one weekly buffer block.
- Keep 20% planning slack for illness, low accuracy, hard chapters, and mock-exam feedback.
- Keep the final 2-3 weeks mostly for review, mock exams, recitation, and mistake rework.

## Weekly Review Questions

Ask these during weekly review:

- Which subjects are above or below required pace?
- Did any high-weight subject get ignored?
- Did the user protect review and correction?
- Did backlog grow or shrink?
- Are any resources now too expensive to finish?
- What should be cut, downgraded, or moved to selective practice?

## Output Format

When reporting completion control, use:

```text
Deadline:
Remaining days/weeks:
Subject inventory:
Required weekly pace:
Current actual pace:
Risk level:
Tasks to protect:
Tasks to cut/downgrade:
Next 7-day correction:
```

## Local Script Support

Use `scripts/study_store.py` for persistent control reports:

```bash
python scripts/study_store.py inventory --profile default
python scripts/study_store.py control-report --profile default
python scripts/study_store.py control-report --profile default --deadline 2026-12-20
python scripts/study_store.py analytics-report --profile default --days 7
python scripts/study_store.py blocked-report --profile default
```

`inventory` summarizes pending/done task units by subject and type.

`control-report` outputs:

- remaining days/weeks
- pending units by subject
- required weekly burn-down
- actual completed units in the last 7 days
- green/yellow/red risk
- tasks to protect
- cut/downgrade candidates

`analytics-report` should be used after several days of logs. It outputs daily completion rate, accuracy trend, error-cause statistics, delay prediction, protected tasks, cut candidates, and automatic adjustment advice.

`blocked-report` finds dependency-blocked tasks and the upstream task IDs that unlock the most downstream work. Use it before changing a weekly plan when several tasks depend on a small number of prerequisites.
