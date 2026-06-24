# Paper and Mock Mode

Use paper mode for past papers, mock exams, section tests, and timed sets.

## Commands

```bash
python scripts/study_store.py add-paper --profile default --subject "408 - Operating System" --name "OS mock 1" --paper-type mock --score 32 --total-score 45 --minutes 45 --weak-topics "memory management,scheduling pv" --error-causes "concept,timing"
python scripts/study_store.py paper-report --profile default --subject "408"
```

## Rules

- Record score, total score, time, wrong count, weak topics, and error causes.
- Weak topics become spaced review items automatically.
- Use paper reports to decide whether to add new tasks, rework mistakes, or cut supplemental material.
- In the past-exam phase, paper analysis should drive the next weekly plan more than course progress.
