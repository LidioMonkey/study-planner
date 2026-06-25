# Study Planner Deployment Bundle

This folder packages the `study-planner` skill together with a real profile snapshot for migration to another machine or agent environment.

## Included Data

- Skill code: the whole repository root
- Profile snapshot: `deployment/profiles/kaoyan/`
- Current profile name: `kaoyan`

## Important Path-Specific Data

The bundled profile contains a machine-specific Obsidian config in:

```text
deployment/profiles/kaoyan/obsidian.json
```

Current bundled value:

```json
{
  "vault": "D:\\hyh-note",
  "study_root": "Study Planner"
}
```

This Windows path is not valid on Linux. Any Linux/Hermes deployment MUST either:

1. Replace `vault` with the real Linux path to the Obsidian vault, or
2. Remove / ignore `obsidian.json` until the real vault path is known.

Do not keep the Windows path on Linux.

## Linux Restore

Run:

```bash
bash deployment/restore_to_codex_home.sh kaoyan
```

Optional custom target:

```bash
CODEX_HOME=/srv/hermes/.codex bash deployment/restore_to_codex_home.sh kaoyan
```

This copies:

- `deployment/profiles/<profile>` to `${CODEX_HOME:-$HOME/.codex}/study-planner/profiles/<profile>`

It does not guess or rewrite Obsidian paths automatically.

## After Restore

Generate the dashboard:

```bash
python scripts/study_dashboard.py --profile kaoyan
```

Run the local write API:

```bash
python scripts/study_dashboard_server.py --profile kaoyan
```

Optional local static preview:

```bash
python scripts/study_dashboard_launch.py --profile kaoyan --open
```

If browser/process control is unavailable:

```bash
python scripts/study_dashboard.py --profile kaoyan
cd "${CODEX_HOME:-$HOME/.codex}/study-planner/dashboards/kaoyan"
python -m http.server 8787
python <skill-dir>/scripts/study_dashboard_server.py --profile kaoyan
```

## Hermes Requirements

Hermes must:

1. Use the bundled scripts under `scripts/`.
2. Use explicit `--profile kaoyan` unless the user requests another profile.
3. Treat profile JSON files as the source of truth.
4. Never assume the Windows Obsidian path is valid on Linux.
5. Ask for the real Linux vault path before running any Obsidian sync command.
6. Regenerate the dashboard after any data-changing command.

## Recommended Migration Order

1. Clone the repository onto the Linux server.
2. Restore the bundled profile with `deployment/restore_to_codex_home.sh`.
3. Inspect or rewrite `obsidian.json`.
4. Run `python -m py_compile` on the scripts.
5. Generate the dashboard.
6. Start the local API if direct checkbox writes are needed.
