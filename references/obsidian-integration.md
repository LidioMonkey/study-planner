# Obsidian Integration

Use this reference when a Study Planner profile should connect to an Obsidian vault.

## Purpose

Obsidian is best used as the human-readable knowledge base:

- Material catalogs with real chapters, pages, lecture numbers, and problem ranges.
- Mistake cards with knowledge points, error causes, and rework notes.
- Exported weekly plans and daily logs.
- Long-term review and paper notes.

The JSON profile remains the operational source of truth for scripts and dashboards. Obsidian Markdown is the readable and editable knowledge layer.

## Commands

```bash
python scripts/obsidian_sync.py --profile default configure --vault "/path/to/Vault" --study-root "Study Planner"
python scripts/obsidian_sync.py --profile default import-materials
python scripts/obsidian_sync.py --profile default import-wangdao-pdfs --pdf-dir "/path/to/408-pdfs" --bind-tasks
python scripts/obsidian_sync.py --profile default import-408-outline --bind-tasks
python scripts/obsidian_sync.py --profile default import-mistakes
python scripts/obsidian_sync.py --profile default export
```

Pass `--vault` to import/export commands when the vault has not been configured.

## Folder Layout

Export creates:

```text
Study Planner/
  01-Weekly Plans/
  02-Daily Logs/
  03-Mistakes/
  04-Materials/
```

The importer scans all Markdown files in the vault except `.obsidian` and `.git`.

## Wangdao 408 PDF Import

When the user provides actual Wangdao PDFs, import those before using ordinary Obsidian outline notes:

```bash
python scripts/obsidian_sync.py --profile default import-wangdao-pdfs --pdf-dir "/path/to/408-pdfs" --bind-tasks
```

Default file names under `--pdf-dir`:

```text
2025王道数据结构考研复习指导.pdf
2026年计算机组成原理考研复习指导.pdf
2025王道操作系统考研复习指导.pdf
2025王道计算机网络考研复习指导.pdf
```

Explicit paths are also supported:

```bash
python scripts/obsidian_sync.py --profile default import-wangdao-pdfs --ds "...数据结构.pdf" --co "...计组.pdf" --os "...操作系统.pdf" --cn "...计算机网络.pdf" --bind-tasks
```

Import behavior:

- Reads PDF bookmarks with `pypdf`.
- Creates chapter and section catalog units.
- Stores PDF page ranges such as `P359-P420`.
- Sets `catalog_precision: chapter-section-page`.
- With `--bind-tasks`, known Wangdao 408 tasks are rebound to the PDF units.

Authority rule:

- If a PDF catalog conflicts with an older Obsidian knowledge graph, trust the PDF for the book catalog.
- Keep the Obsidian knowledge graph as notes and cross-links, not as the source of truth for Wangdao page ranges or chapter numbers.
- Do not invent problem numbers; PDF bookmark import gives page ranges, not exact exercise numbers.

## Existing 408 Outline Import

Some users already keep 408 notes as ordinary Obsidian wiki-link outlines rather than `type: material` frontmatter tables. Use:

```bash
python scripts/obsidian_sync.py --profile default import-408-outline --vault "/path/to/Vault" --bind-tasks
```

Expected files:

```text
01-数据结构/数据结构目录.md
02-计算机组成原理/计算机组成原理目录.md
03-操作系统/操作系统目录.md
04-计算机网络/计算机网络目录.md
```

Expected outline style:

```markdown
## [[01-数据结构/第6章-排序|排序]]
```

Import behavior:

- Creates or updates four Wangdao materials: `MAT-WANGDAO-DS`, `MAT-WANGDAO-CO`, `MAT-WANGDAO-OS`, `MAT-WANGDAO-CN`.
- Converts wiki links such as `第6章-排序` into catalog units such as `DS-06 / 第6章 排序`.
- Stores `catalog_precision: chapter`.
- Keeps `page_range`, `lecture_range`, and `problem_range` empty unless they are present elsewhere in a supported material table.
- With `--bind-tasks`, known Wangdao 408 task ids in the active profile are linked to the imported chapter units.

This command is intentionally conservative. It imports real chapter boundaries from the vault, but it must not invent page numbers, lecture numbers, or problem ranges.

## Material Note Format

```markdown
---
type: material
id: MAT001
name: 李永乐线性代数基础篇讲义
kind: book
subject: Math II - Linear Algebra
edition: 2027
teacher: 李永乐
catalog_source: 用户提供目录/OCR/官网目录
---

| id | title | page_range | lecture_range | problem_range | parent |
|---|---|---|---|---|---|
| LA-01 | 行列式 | P1-P24 | 第 1-2 讲 | 例 1-20 | 第一章 |
| LA-05 | 特征值与特征向量 | P120-P150 | 第 10-11 讲 | 习题 1-25 | 第五章 |
```

Import result:

- Creates or updates `materials.json`.
- Uses `id` as the stable material id.
- Uses table rows as `catalog_units`.
- Marks `catalog_status` as `complete` when rows exist.

## Mistake Note Format

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

## 错因

不会判断积分区域换序。

## 正解

...

## 下次回炉

重画区域，先判断横纵切片。
```

Import result:

- Creates or updates `mistakes.json`.
- Does not yet auto-create spaced review items; use `study_store.py add-mistake` for automatic review generation, or add review generation in a later integration pass.

## Export Behavior

`obsidian_sync.py export` writes:

- Materials from `materials.json` to `04-Materials/`.
- Mistakes from `mistakes.json` to `03-Mistakes/`.
- Current week plan to `01-Weekly Plans/`.
- Daily log index to `02-Daily Logs/`.

Existing files with the same generated file name are overwritten.

## Agent Rules

- Prefer importing material catalogs from Obsidian before generating tasks.
- Run `catalog-audit` after import and before planning.
- Do not invent pages, lectures, or problem ranges if the Obsidian material note lacks them.
- For an imported outline with `catalog_precision: chapter`, chapter-level plans are allowed and are the default. Page-level or question-number-level plans still require a richer material table, OCR, screenshots, PDF text, or user confirmation.
- Keep Obsidian paths user-configurable with `--vault`; never hard-code a local vault path.
