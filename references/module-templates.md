# Module Templates

Use modules when the user wants to add a chapter/topic without manually creating every task.

## Command

```bash
python scripts/study_store.py add-module --profile default --template 408-os --name "Memory management" --weak-points "paging,segmentation"
python scripts/study_store.py module-report --profile default
```

## Built-In Templates

- `408-os`: Wangdao OS course slice + Wangdao after-class questions.
- `408-cn`: Wangdao computer network course slice + after-class questions.
- `408-co`: Wangdao computer organization course slice + after-class questions.
- `408-ds`: Wangdao data structure course slice + after-class questions.
- `math2-linear`: Li Yongle linear algebra slice + foundation exercises.
- `math2-advanced`: Wu Zhongxiang high math slice + 660 questions.
- `english2`: English input/output slice + practice.
- `politics`: Politics framework slice + Xiao 1000 warm-up.

## Rules

- A module should represent one chapter, topic, or problem family.
- The generated exercise task depends on the generated course task.
- Use `--depends-on` when the module itself depends on an earlier module or task.
- Use `--weak-points` for known fragile concepts; each weak point becomes spaced review.
- Override defaults only when the local resource differs.
