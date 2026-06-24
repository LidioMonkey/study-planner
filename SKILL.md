---
name: study-planner
description: Create and maintain task-based study plans for exams, certifications, postgraduate entrance exam preparation, and daily learning. Use when the user asks to plan study, arrange courses, schedule exercise books, manage review, track progress, recover from falling behind, create daily task lists, do daily/weekly reviews, or set study reminders.
---

# Study Planner

## Core Idea

Use task lists as the default planning unit. Time blocks are optional support for fixed schedules, mock exams, writing practice, Pomodoro sessions, and reminders.

Daily plans should answer:

1. What are the few outcomes that matter today?
2. What old material is due for review?
3. If the user is behind, what should be adjusted without breaking the whole plan?

Default weekly planning cycle:

- Treat the current cycle as **start date through Sunday**.
- Do not force a 7-day plan unless the user explicitly asks for a 7-day rolling window.
- When rolling forward, the next plan starts after the current committed period and ends on that period's Sunday.
- The HTML dashboard should show the active period and countdown to the current period end.

## Modes

- **Build profile**: collect the learning goal, deadline, subjects, baseline, available time, resources, and preferred output style.
- **Build material catalog**: before planning from a book, course, question bank, app, handout, or paper set, create or verify its real catalog in `materials.json`.
- **Obsidian sync**: when the user wants to connect an Obsidian vault, import material catalogs and mistakes from Markdown, and export weekly plans, daily logs, materials, and mistakes back to Markdown.
- **Plan**: create a long-term, stage, weekly, or daily plan.
- **Today**: generate today's task list from course, exercise, review, and backlog queues.
- **Weekly plan**: generate a layered plan from the start date through Sunday with main tasks, review tasks, optional extras, and minimum versions.
- **Commit weekly plan**: save the generated weekly plan as the current comparison baseline for later review.
- **Log progress**: convert the user's completion report into structured progress, review items, and backlog changes.
- **Adjust**: repair an overloaded or delayed plan, reduce scope, and protect review/feedback loops.
- **Review**: produce daily or weekly reviews with completion rate, weak points, next actions, and plan changes.
- **Analytics and prediction**: summarize daily completion rates, accuracy trends, error causes, delay risks, protected tasks, and cut candidates.
- **Mistake packs**: store wrong questions by source, knowledge point, and error cause, then generate rework packs and review queues.
- **Module templates**: add a study module, such as an OS chapter or math topic, and automatically create its course task, exercise task, dependencies, and optional weak-point reviews.
- **Phase control**: infer whether the plan is in foundation-close, strengthening, past-exam, or sprint phase and enforce different course/practice ratios.
- **Week audit**: compare the committed weekly plan against actual logs, identify carryover tasks, and prepare next-week adjustments.
- **Next-week rolling plan**: generate the next week from the current audit, carry over protected unfinished work, and optionally commit it.
- **Import dashboard export**: when the user pastes a `study_planner_week_export` block from the HTML dashboard, parse completed and pending tasks, write completed tasks into progress logs where task ids are available, preserve pending tasks for carryover analysis, then run weekly review and next-week rolling logic if requested.
- **Dashboard local sync**: when the HTML dashboard has the local sync server available, checkbox changes should write directly to the local profile. Use copy/export only as a fallback for migration, backup, or service failure.
- **Paper/mock mode**: record past papers, mock exams, section tests, scores, time, weak topics, and convert weak topics into review.
- **Detailed 408 model**: track 408 subtopics across data structure, computer organization, OS, and computer network.
- **Completion control**: when the user asks whether they can finish before an exam, build a total task inventory, reverse-plan from the deadline, calculate weekly burn-down, flag risks, and cut low-value tasks when needed.
- **Course control**: when the plan includes many online courses or lectures, cap passive watching, split videos into course slices, require outputs and matching exercises, and downgrade redundant teachers or rewatches when progress is at risk.
- **Dependency control**: find blocked tasks and the upstream tasks that unlock the most downstream work.
- **Reminder**: when the user asks for recurring study reminders, use the available automation/reminder tool instead of only writing advice.

## First Questions

Ask only for missing information that materially changes the plan. If the user wants to start quickly, make reasonable assumptions and mark them.

Minimum useful inputs:

- Goal and deadline
- Subjects or skills
- Current baseline by subject
- Weekday/weekend available study time
- Main courses, books, question banks, or materials
- Weakest/highest-priority subject

For postgraduate entrance exam plans, also ask for target major/school when relevant, exam subjects, and current stage.

## Daily Plan Shape

Use this structure by default:

```text
Today Must Do
- 1-3 high-impact, verifiable tasks.

Today Review
- Due review, recitation, old mistakes, vocabulary, or formulas.

Optional Extra
- Useful tasks that do not count as failure if skipped.

Minimum Version
- A tiny fallback plan for low-energy or disrupted days.
```

Every task should have an acceptance condition. Prefer "finish 25 limit problems and correct all wrong ones" over "study calculus".

## Task Specificity Rules

Never generate vague tasks such as "finish the tail", "start the chapter", "repair exercises", "weak-topic practice", "foundation launch", or only a topic name.

Never invent a book/course/question-bank structure. Every plan that uses a material should reference that material's real catalog. If the catalog is missing, stop planning that material and either search authoritative/current sources or ask the user for the table of contents, lecture list, page photos, PDF, OCR text, or problem-number ranges.

Every executable task must include:

- **Material**: the exact book, question bank, app, handout, course, teacher route, or paper.
- **Catalog binding**: `material_id` and `catalog_units` when the material is known in `materials.json`.
- **Scope**: chapter, section, lecture range, page range, problem range, passage number, or topic boundary.
- **Precise range**: use `page_range`, `lecture_range`, and/or `problem_range` whenever the material has pages, lecture numbers, or question numbers. Prefer "第 3 章第 2 节 / P45-P58 / 例 12-18 / 习题 1-25" over only a topic name.
- **Quantity**: number of videos, minutes, pages, questions, passages, words, formulas, or review cards.
- **Action**: watch, read, do, correct, summarize, recite, rework, time, or diagnose.
- **Acceptance**: a visible output, such as corrected wrong questions, error-cause tags, summary table, formula sheet, solved set, or notes.

If material names, chapter boundaries, page ranges, lecture numbers, or problem ranges are unknown, do not invent them. Ask the user for the missing detail, or, when the user explicitly allows web lookup/current information, search authoritative pages or official/catalog sources first. Mark any inferred range as an assumption.

When exact ranges are still unknown, keep the task usable but explicitly mark the missing field as needing completion, such as `page_range: 待补充教材页码` or `problem_range: 待补充题号范围`. Do not hide missing precision behind phrases like "尾巴", "启动", "收口", "专项练习", or "当前章节".

## Material Catalog Rules

Use `materials.json` as the source of truth for every resource's structure.

Each material should store:

- `id`: stable id such as `MAT001`.
- `name`: exact book, course, question bank, app, or paper-set name.
- `kind`: `book`, `exercise-book`, `course`, `paper-set`, `app`, `handout`, or `other`.
- `subject`, `edition`, `teacher`, and source notes when known.
- `catalog_status`: `complete` only when real chapters/lectures/problem ranges are known.
- `catalog_units`: real units with `id`, `title`, `page_range`, `lecture_range`, `problem_range`, and optional `parent`.

Planning rule:

1. Before creating tasks for a material, run `material-report` or inspect `materials.json`.
2. If no material exists, create it with `add-material`.
3. If the catalog is missing or incomplete, ask the user for the catalog or search authoritative/current sources when web lookup is allowed.
4. Only create tasks with `--material-id` and `--catalog-units` after the material's actual structure is known.
5. Run `catalog-audit` after generating or importing tasks. Treat any non-`ok` item as a planning defect, not as a harmless warning.

Example:

```bash
python scripts/study_store.py add-material --profile default --name "李永乐线性代数基础篇讲义" --kind book --subject "Math II - Linear Algebra" --teacher "李永乐" --catalog-source "用户提供目录/OCR/官网目录" --catalog "LA-01|行列式|P1-P24|||;LA-02|矩阵|P25-P58|||;LA-05|特征值与特征向量|P120-P150|第 10-11 讲||"
python scripts/study_store.py add-course --profile default --subject "Math II - Linear Algebra" --title "李永乐线性代数基础篇讲义" --material-id MAT001 --catalog-units LA-05 --slice "学习特征值与特征向量并整理条件清单" --output "特征值、特征向量、相似矩阵条件清单"
python scripts/study_store.py catalog-audit --profile default
```

## Obsidian Rules

Use `scripts/obsidian_sync.py` when connecting a profile to an Obsidian vault.

Supported v1 workflow:

```bash
python scripts/obsidian_sync.py --profile default configure --vault "/path/to/ObsidianVault" --study-root "Study Planner"
python scripts/obsidian_sync.py --profile default import-materials
python scripts/obsidian_sync.py --profile default import-mistakes
python scripts/obsidian_sync.py --profile default export
```

Obsidian material notes should use frontmatter and a Markdown table:

```markdown
---
type: material
id: MAT001
name: 李永乐线性代数基础篇讲义
kind: book
subject: Math II - Linear Algebra
teacher: 李永乐
catalog_source: 用户提供目录/OCR/官网目录
---

| id | title | page_range | lecture_range | problem_range | parent |
|---|---|---|---|---|---|
| LA-05 | 特征值与特征向量 | P120-P150 | 第 10-11 讲 | 例 1-20 | 第五章 |
```

Obsidian mistake notes should use frontmatter:

```markdown
---
type: mistake
id: M001
subject: Math II
material: 660 题
question: 二重积分 #12
knowledge: 积分区域换序
error_causes: [concept, method]
status: pending
---

这里写错因、正解和下次回炉提示。
```

Use Obsidian as the preferred source for real material catalogs when the user already keeps notes there. Import the catalog before generating new tasks. Export after weekly planning, logging, or adding mistakes so the vault remains a readable knowledge base.

For exercise books, specify the resource and quantity at minimum. Prefer exact ranges when known:

```text
Bad: Linear algebra eigenvalue exercises.
Good: 李永乐线代基础篇讲义：特征值与特征向量配套习题 25 题；订正并总结相似矩阵/特征向量条件。
```

For courses, a video task is not complete by watching alone:

```text
Bad: Start OS process threads.
Good: 王道操作系统复习指导书 + 对应网课：进程与线程小节 1 个 45-60 分钟切片；输出进程状态转换图，并做配套选择题 8 题。
```

## Course Rules

Courses are input, not completion by themselves.

- Split courses into 30-60 minute slices.
- Every slice must produce an output: notes, formulas, examples, comparison table, recitation outline, flashcards, or a question list.
- Math and technical subjects should pair course slices with exercises.
- English course tasks should pair with vocabulary, close reading, translation, long-sentence analysis, speaking, or writing output.
- Political theory or memory-heavy subjects should pair with outlines, multiple-choice practice, or recitation.
- Default to no more than 3 new course slices per day.

## Exercise Rules

Question-bank tasks must include doing, correcting, diagnosing, and follow-up review.

Use fields like:

```text
Resource:
Scope:
Quantity:
Mode: timed/untimed
Acceptance:
Follow-up:
```

When accuracy is below 60%, reduce new questions and return to examples, notes, or course basics. At 60-80%, continue chapter practice and increase rework. Above 80%, move toward mixed or timed training.

## Review Rules

Use spaced review for notes, mistakes, recitation, vocabulary, formulas, and representative problems.

Default intervals: same day, 1 day, 3 days, 7 days, 14 days, 30 days.

Do not let new course progress erase review time. If the plan is overloaded, protect review and correction before adding new input.

## Mistake Rework Calendar

Wrong questions should not only be stored; they should enter a visible rework calendar.

- When adding a mistake, create review items for same day, 1 day, 3 days, 7 days, 14 days, and 30 days unless the user requests a custom interval.
- Mark mistake review items with a `source` value containing `mistake:<id>` so the dashboard can separate them from ordinary weak-point review.
- A mistake rework task should include subject, material/source, original question location, knowledge point, error cause, rework date, and pass/fail result.
- If a mistake is still wrong on rework, keep it in the queue and generate a smaller diagnostic task before adding new tasks on that topic.

## Local Data

For persistent tracking, use `scripts/study_store.py`. It stores JSON under:

```text
~/.codex/study-planner/profiles/<profile>/
```

Use `CODEX_HOME` when available. Otherwise use `~/.codex`. Do not hard-code a user's home directory, workspace path, profile name, or localhost port inside generated instructions or scripts.

Useful commands:

```bash
python scripts/study_store.py init --profile default --goal "2027 postgraduate entrance exam" --deadline 2026-12-20
python scripts/study_store.py add-course --profile default --subject Math --title "Limits" --slice "definition and properties" --output "summary + examples" --exercise "660 limits 25 questions"
python scripts/study_store.py add-exercise --profile default --subject Math --resource "660" --scope "limits" --quantity 25
python scripts/study_store.py add-module --profile default --template 408-os --name "Memory management" --weak-points "paging,segmentation"
python scripts/study_store.py module-report --profile default
python scripts/study_store.py set-weights --profile default --weights "408 - Operating System=16,408 - Computer Organization=12,408 - Computer Network=10,408 - Data Structure=7,Math II=30,English II=15,Politics=10"
python scripts/study_store.py set-dependency --profile default --task-id T046 --depends-on T014
python scripts/study_store.py today --profile default
python scripts/study_store.py weekly-plan --profile default --start 2026-06-24 --days 7
python scripts/study_store.py commit-weekly-plan --profile default --start 2026-06-24 --days 7
python scripts/study_store.py log --profile default --task-id T001 --status done --accuracy 72 --error-causes "concept,calculation" --note "8 wrong, mostly concept confusion"
python scripts/study_store.py weekly --profile default
python scripts/study_store.py inventory --profile default
python scripts/study_store.py control-report --profile default
python scripts/study_store.py analytics-report --profile default --days 7
python scripts/study_store.py blocked-report --profile default
python scripts/study_store.py course-ratio-report --profile default --source current-week --cap 40
python scripts/study_store.py add-mistake --profile default --subject Math --source "660" --question "limits #12" --knowledge "limit existence" --error-causes "concept,method"
python scripts/study_store.py mistake-pack --profile default --subject Math --error-cause concept
python scripts/study_store.py phase-report --profile default
python scripts/study_store.py week-audit --profile default
python scripts/study_store.py next-week-plan --profile default --commit
python scripts/study_store.py add-paper --profile default --subject "408 - Operating System" --name "OS mock 1" --paper-type mock --score 32 --total-score 45 --minutes 45 --weak-topics "memory management,scheduling pv" --error-causes "concept,timing"
python scripts/study_store.py paper-report --profile default --subject "408"
python scripts/study_store.py 408-model-report --profile default
```

## Dashboard Packaging

The dashboard is bundled with the skill. Prefer these scripts instead of recreating HTML or API code in the workspace:

```bash
python scripts/study_profile_seed.py --profile default
python scripts/study_dashboard.py --profile default
python scripts/study_dashboard_launch.py --profile default --open
python scripts/study_dashboard_server.py --profile default
```

Script roles:

- `study_profile_seed.py`: create a minimal profile without overwriting existing data.
- `study_dashboard.py`: generate `index.html` from the profile JSON.
- `study_dashboard_server.py`: serve the local write API for checkbox completion, mistake calendar, dashboard regeneration, and weekly rolling.
- `study_dashboard_launch.py`: generate the dashboard and start both the static HTML server and local write API.
- `obsidian_sync.py`: connect an Obsidian vault, import material catalogs/mistakes, and export plans/logs/mistakes/materials as Markdown.

Portable defaults:

- Profile: `default`, override with `--profile <name>`.
- Data root: `${CODEX_HOME}/study-planner/profiles/<profile>` or `~/.codex/study-planner/profiles/<profile>`.
- Dashboard output: `${CODEX_HOME}/study-planner/dashboards/<profile>/index.html`.
- Static dashboard: `http://127.0.0.1:8787/`, override with `--static-port`.
- Local write API: `http://127.0.0.1:8790/`, override with `--api-port`.

For Hermes and other agents:

1. Resolve the skill directory and run scripts from `scripts/`; do not depend on the user's current workspace.
2. If the profile is missing, run `study_profile_seed.py` first or create the profile with `study_store.py init`.
3. Generate the dashboard with `study_dashboard.py` after any data-changing command.
4. Use `study_dashboard_launch.py` for local browser use when process control is available.
5. If process control is unavailable, generate the HTML and tell the user the output path plus the optional server commands.
6. Keep all UI text Chinese when the user is Chinese or the profile content is Chinese.

When adding course or exercise tasks, pass exact ranges if known:

```bash
python scripts/study_store.py add-course --profile default --subject Math --title "李永乐线代基础篇" --slice "矩阵对角化" --lecture-range "第 12-13 讲" --page-range "P80-P96" --output "对角化条件清单" --exercise "配套习题 1-25"
python scripts/study_store.py add-exercise --profile default --subject Math --resource "660 题" --scope "二重积分" --problem-range "第 1-30 题" --quantity 30
```

Dashboard direct-write workflow:

1. Keep the profile under `~/.codex/study-planner/profiles/<profile>/`.
2. Start the dashboard local sync server before using direct checkbox writes.
3. A checked task with a known `task_id` writes a `done` progress log to the local profile.
4. An unchecked task with a known `task_id` writes a `missed` progress log, replacing the same date/task log when present.
5. A text-only minimum task without `task_id` writes to `dashboard_completions.json` instead of pretending to complete a formal task.
6. If local sync is unavailable, use the dashboard export block as the fallback import path.

Dashboard export workflow:

1. The HTML dashboard can export the current week as a text block containing `study_planner_week_export` JSON.
2. When this block is pasted into the conversation, treat it as authoritative for dashboard checkbox completion.
3. For each exported item with `status: done` and a `task_id`, record a completed log unless it is already logged for that date.
4. Keep `pending` items as carryover candidates rather than marking them complete.
5. After import, summarize completion rate, protected unfinished tasks, cut candidates, and whether the next week should be regenerated.
6. If the user asks to roll forward, run the week audit and next-week plan flow, then regenerate the dashboard.

Read `references/planning-rules.md` for detailed planning heuristics, `references/exam-presets.md` for exam-specific templates, and `references/task-schemas.md` for structured task formats.

Read `references/completion-control.md` when planning backward from an exam date, checking whether all materials can be completed before the deadline, deciding phase milestones, or handling yellow/red progress warnings.

Read `references/course-control.md` when arranging online courses, deciding whether to watch or skip lectures, controlling course overload, handling multiple teachers, or converting lectures into task-based outputs.

Read `references/module-templates.md` when adding a new chapter/topic as a reusable module instead of manually creating course and exercise tasks.

Read `references/paper-mode.md` when the user records or analyzes past papers, mock exams, section tests, scores, timing, and weak topics.

Read `references/model-408.md` when planning, auditing, or predicting 408 progress at the subtopic level.

Read `references/agent-integration.md` when packaging the skill for another agent, running it outside the original workspace, adapting it for Hermes, deploying the dashboard, or debugging profile/path/port portability.

Read `references/obsidian-integration.md` when importing from or exporting to an Obsidian vault, designing material catalog notes, mistake notes, or vault folder structure.
