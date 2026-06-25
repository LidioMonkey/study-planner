# Hermes Deployment Prompt

Use this exact prompt, or adapt it without weakening any constraints.

## Prompt

You are deploying the `study-planner` skill on a Linux server for Hermes.

Constraints:

1. Use the repository itself as the only source of truth for code and bundled profile data.
2. Use the bundled profile snapshot at `deployment/profiles/kaoyan/`.
3. Restore that profile into `${CODEX_HOME:-$HOME/.codex}/study-planner/profiles/kaoyan/`.
4. Never assume any Windows path is valid on Linux.
5. Before using Obsidian integration, inspect `obsidian.json` and explicitly replace the `vault` path if it still points to a Windows location such as `D:\\...`.
6. If the real Linux Obsidian vault path is unknown, do not run any Obsidian import/export command. Instead, report that the path must be provided first.
7. Do not rewrite the dashboard implementation. Reuse only the bundled scripts under `scripts/`.
8. Always run every data-changing action with `--profile kaoyan`.
9. After restoring the profile, regenerate the dashboard with `python scripts/study_dashboard.py --profile kaoyan`.
10. If local checkbox sync is required, run `python scripts/study_dashboard_server.py --profile kaoyan` and keep it bound to `127.0.0.1` unless the user explicitly requests another host and accepts the risk.
11. Do not expose the local write API to the public internet by default.
12. If validation fails, stop and report the exact failing command and the smallest safe next action.

Required execution order:

1. Read `SKILL.md`.
2. Read `references/agent-integration.md`.
3. Read `deployment/README.md`.
4. Restore the bundled profile with `bash deployment/restore_to_codex_home.sh kaoyan`.
5. Validate script syntax with:
   `python -m py_compile scripts/study_store.py scripts/study_dashboard.py scripts/study_dashboard_server.py scripts/study_dashboard_launch.py scripts/study_profile_seed.py scripts/obsidian_sync.py`
6. Generate the dashboard:
   `python scripts/study_dashboard.py --profile kaoyan`
7. Report the dashboard output path.
8. If requested, start the local API and static preview.

Output requirements:

- Report the restored profile path.
- Report whether `obsidian.json` still contains a machine-specific path.
- Report the exact command needed to fix the Obsidian vault path.
- Report the exact dashboard generation command used.
- Report any blocked step separately from successful steps.

Forbidden behaviors:

- Do not invent or silently rewrite the Linux Obsidian vault path.
- Do not change profile names.
- Do not discard bundled study data.
- Do not create a new empty profile unless the user explicitly asks for one.
- Do not replace the bundled scripts with ad hoc HTML or API code.
