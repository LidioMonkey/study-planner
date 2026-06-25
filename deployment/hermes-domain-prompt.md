# Hermes Domain Deployment Prompt

Use this prompt when Hermes must deploy the Study Planner dashboard to a Linux server domain.

## Prompt

Deploy the `study-planner` repository to a Linux server domain with the bundled `kaoyan` profile.

Non-negotiable constraints:

1. Use the repository scripts exactly as bundled. Do not reimplement the dashboard or API.
2. Restore the bundled profile from `deployment/profiles/kaoyan/` into `${CODEX_HOME:-$HOME/.codex}/study-planner/profiles/kaoyan/`.
3. Deploy the HTML dashboard under the real domain, not only on localhost.
4. Keep the Python write API bound to `127.0.0.1` unless the user explicitly requests a public bind and accepts the risk.
5. If direct checkbox sync from the domain page is required, expose `/api/` through Nginx reverse proxy instead of binding the Python server publicly.
6. Set `STUDY_DASHBOARD_ORIGINS` to the exact domain origin, such as `https://study.example.com`.
7. Inspect `obsidian.json` before any Obsidian command. If it still contains a Windows path such as `D:\\hyh-note`, do not run Obsidian sync until the real Linux vault path is provided and written.
8. Use explicit `--profile kaoyan` on every Study Planner command.
9. After any profile change, regenerate the domain HTML with the bundled generator script.
10. If any required input is missing, stop and report exactly what is missing instead of guessing.

Required execution order:

1. Read `SKILL.md`.
2. Read `references/agent-integration.md`.
3. Read `deployment/README.md`.
4. Read `deployment/domain-deploy.md`.
5. Restore the bundled profile:
   `bash deployment/restore_to_codex_home.sh kaoyan`
6. Validate Python syntax:
   `python -m py_compile scripts/study_store.py scripts/study_dashboard.py scripts/study_dashboard_server.py scripts/study_dashboard_launch.py scripts/study_profile_seed.py scripts/obsidian_sync.py`
7. Generate dashboard into the domain web root:
   `bash deployment/generate_domain_dashboard.sh kaoyan /var/www/study-planner/kaoyan`
8. If direct writes are required, start:
   `STUDY_DASHBOARD_ORIGINS="https://study.example.com" python scripts/study_dashboard_server.py --profile kaoyan --host 127.0.0.1 --port 8790 --out-dir /var/www/study-planner/kaoyan`
9. Configure Nginx from `deployment/nginx.study-planner.conf.example`.

Required final report:

- Restored profile path
- Domain web root path
- Whether `obsidian.json` still contains an invalid Windows path
- Exact command used to generate the dashboard
- Exact command used to start the write API, if started
- Whether `/api/` is proxied or intentionally omitted
- Any blocked step and the smallest exact next action
