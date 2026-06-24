# Course Control

Use this reference when a study plan includes online courses, recorded lectures, live classes, teacher systems, or repeated video watching.

## Core Principle

Courses are input. Completion requires output.

Do not count "watched a lecture" as complete unless the task also produces notes, solved examples, questions, recitation output, or a follow-up exercise set.

## Course Task Requirements

Every course task should include:

```text
Teacher/course:
Chapter:
Slice:
Estimated minutes:
Output:
Matching exercise:
Review trigger:
Watch policy:
```

Good:

```text
Watch OS scheduling 45 minutes, write a scheduling comparison table, then do 15 matching Wangdao questions.
```

Bad:

```text
Watch OS class for 2 hours.
```

## Slice Rules

- Split videos into 30-60 minute slices.
- A slice should map to one concept, method, or problem type.
- Do not schedule more than 2-3 new course slices in one day by default.
- If the user is tired, switch from new course input to review or correction.

## Course Ratio Caps

Use course ratios by stage:

- Foundation close: course up to 40%, exercises/review at least 60%.
- Strengthening: course up to 20%, exercises/review at least 80%.
- Past exam phase: course up to 10%, only for weak points.
- Sprint: no systematic new course; only short targeted repair.

If a plan exceeds these caps, reduce passive watching before reducing correction or review.

## Multiple-Teacher Control

Do not let the user run several full teacher systems in parallel.

Rules:

- One main teacher/system per subject or module.
- Extra teachers are used only for weak chapters or alternative explanations.
- If two teachers cover the same chapter, choose one as the main path and convert the other into selective repair.
- Never restart a whole course just because one chapter feels weak.

## Rewatch Rules

Rewatching is expensive. Use this order:

1. Try examples and notes.
2. Do a small diagnostic set.
3. Rewatch only the exact 10-30 minute weak segment.
4. Immediately do matching questions.

Do not schedule full-section rewatch unless the diagnostic accuracy is very low or the concept is foundational.

## Watch-Skip Decisions

Watch when:

- The chapter is new.
- Diagnostic accuracy is below 60%.
- The topic is foundational for later chapters.
- The user cannot explain the concept or solve representative examples.

Skip or compress when:

- The user can solve representative problems.
- The lecture duplicates material already mastered.
- The course is a supplemental teacher path.
- The exam is close and practice/review is more valuable.

## Course Debt

Course backlog should not silently grow.

During weekly review, track:

- Planned course slices
- Completed course slices
- Matching exercises completed
- Course-only tasks with no output
- Rewatch time
- Course backlog

If course backlog grows for 2 weeks:

- Keep only core chapters.
- Convert low-value lectures into outline reading.
- Use extra teachers only for weak points.
- Increase exercise/correction share.

## Local Script Support

Use course ratio reports to prevent passive watching from taking over:

```bash
python scripts/study_store.py course-ratio-report --profile default --source current-week --cap 40
python scripts/study_store.py course-ratio-report --profile default --source preview --start 2026-06-24 --days 7 --cap 40
```

For strengthening and past-exam phases, lower `--cap` to 20 or 10.

Use phase reports to choose the cap:

```bash
python scripts/study_store.py phase-report --profile default
```

Default caps:

- foundation-close: 40
- strengthening: 20
- past-exam: 10
- sprint: no large new course input

## Output Standards

Each course slice should produce at least one:

- One-page framework
- Formula/method checklist
- Comparison table
- Representative example notes
- Wrong-question list
- Recitation outline
- Flashcards or review prompts

For exam preparation, course output should be tied to questions whenever possible.
