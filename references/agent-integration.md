# Agent Integration

Use this reference when an agent needs to run Study Planner outside the original author's workspace.

## Goals

- Do not hard-code user-specific paths.
- Do not rewrite bundled dashboard scripts unless the user explicitly asks to change dashboard behavior.
- Treat JSON files under the selected profile as the source of truth.
- Keep local write APIs bound to `127.0.0.1` unless the user explicitly asks for another host and accepts the risk.

## Portable Paths

Resolve paths in this order:

1. Skill directory: the folder containing `SKILL.md`.
2. Scripts: `<skill-dir>/scripts`.
3. Data root: `$CODEX_HOME/study-planner/profiles/<profile>` or `~/.codex/study-planner/profiles/<profile>`.
4. Dashboard output: `$CODEX_HOME/study-planner/dashboards/<profile>`.

Never assume `C:\Users\h`, `/Users/h`, a particular workspace, or a fixed profile such as `kaoyan`.

## First Run

```bash
python <skill-dir>/scripts/study_profile_seed.py --profile default
python <skill-dir>/scripts/study_dashboard_launch.py --profile default --open
```

If browser/process control is unavailable:

```bash
python <skill-dir>/scripts/study_dashboard.py --profile default
cd ~/.codex/study-planner/dashboards/default
python -m http.server 8787
python <skill-dir>/scripts/study_dashboard_server.py --profile default
```

## Existing Profile

```bash
python <skill-dir>/scripts/study_dashboard.py --profile <profile>
python <skill-dir>/scripts/study_dashboard_launch.py --profile <profile> --open
```

Regenerate the dashboard after any command that changes profile data.

If the repository contains a bundled deployment snapshot under `deployment/profiles/<profile>/`, restore that snapshot into `${CODEX_HOME}/study-planner/profiles/<profile>` or `~/.codex/study-planner/profiles/<profile>` before generating the dashboard. Prefer the bundled restore script when available.

Do not silently keep machine-specific Obsidian paths from another OS. If `obsidian.json` still points to a Windows path such as `D:\...` on Linux, stop Obsidian-related actions until the vault path is explicitly corrected.

## Direct Checkbox Writes

The generated HTML posts to:

```text
http://127.0.0.1:<api-port>/api/log-task
```

Expected payload:

```json
{
  "profile": "default",
  "task_id": "T001",
  "date": "2026-06-24",
  "status": "done",
  "checked": true,
  "note": "HTML 看板勾选同步"
}
```

If `task_id` is missing, the API writes to `dashboard_completions.json` instead of `daily_logs.json`.

## Domain Deployment

The HTML can be deployed as static files. Direct local writes still require the local API on the user's machine.

If a domain page must call the local API, start the server with:

```bash
STUDY_DASHBOARD_ORIGINS=https://example.com python <skill-dir>/scripts/study_dashboard_server.py --profile default
```

For Windows PowerShell:

```powershell
$env:STUDY_DASHBOARD_ORIGINS='https://example.com'
python <skill-dir>\scripts\study_dashboard_server.py --profile default
```

## Hermes Notes

Hermes-style agents should prefer deterministic script calls:

1. Read `SKILL.md`.
2. For dashboard work, read this file only if needed.
3. Run scripts with explicit `--profile`.
4. Return the dashboard URL or output `index.html` path to the user.
5. Avoid generating a new dashboard implementation in the conversation unless the bundled scripts are missing or broken.
6. If `deployment/hermes-prompt.md` exists, follow it exactly for Linux/Hermes migration work.

## Validation

Run:

```bash
python -m py_compile <skill-dir>/scripts/study_store.py <skill-dir>/scripts/study_dashboard.py <skill-dir>/scripts/study_dashboard_server.py <skill-dir>/scripts/study_dashboard_launch.py <skill-dir>/scripts/study_profile_seed.py
python <skill-dir>/scripts/study_profile_seed.py --profile smoke-test
python <skill-dir>/scripts/study_dashboard.py --profile smoke-test
```
