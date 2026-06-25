# Domain Deployment Guide

Use this guide when the Study Planner HTML dashboard must be deployed under a Linux server domain.

## Goal

Deploy:

1. Static dashboard HTML under a real domain, and
2. Optional write API behind the same domain, proxied to the local Python server bound on `127.0.0.1`.

Recommended domain layout:

```text
https://study.example.com/          -> static dashboard files
https://study.example.com/api/      -> reverse proxy to 127.0.0.1:8790/api/
```

## Security Rules

1. Do not bind `study_dashboard_server.py` directly to `0.0.0.0` unless the user explicitly accepts the risk.
2. Prefer keeping the Python API bound to `127.0.0.1`.
3. Expose `/api/` through Nginx reverse proxy only if direct checkbox writes from the domain page are required.
4. Set `STUDY_DASHBOARD_ORIGINS` to the exact domain origin, for example `https://study.example.com`.
5. If the dashboard only needs read-only access, deploy the static HTML only and do not proxy the write API.

## Step 1: Restore the Bundled Profile

```bash
bash deployment/restore_to_codex_home.sh kaoyan
```

## Step 2: Fix Obsidian Path If Needed

Bundled profile file:

```text
deployment/profiles/kaoyan/obsidian.json
```

Bundled value currently contains a Windows path:

```text
D:\hyh-note
```

This path is invalid on Linux. Replace it before any Obsidian sync command, or leave Obsidian unused until the real Linux vault path is known.

## Step 3: Generate Dashboard Into Web Root

Example:

```bash
bash deployment/generate_domain_dashboard.sh kaoyan /var/www/study-planner/kaoyan
```

This writes:

```text
/var/www/study-planner/kaoyan/index.html
```

## Step 4: Start Local Write API

Only needed if the domain dashboard should support direct checkbox sync.

```bash
export STUDY_DASHBOARD_ORIGINS="https://study.example.com"
python scripts/study_dashboard_server.py --profile kaoyan --host 127.0.0.1 --port 8790 --out-dir /var/www/study-planner/kaoyan
```

## Step 5: Configure Nginx

Use the bundled example:

```text
deployment/nginx.study-planner.conf.example
```

Key behavior:

- `/` serves static dashboard files
- `/api/` proxies to `127.0.0.1:8790/api/`

## Step 6: Regenerate After Any Data Change

Whenever the profile changes:

```bash
bash deployment/generate_domain_dashboard.sh kaoyan /var/www/study-planner/kaoyan
```

If the API server is already running, no restart is required for HTML-only regeneration.

## Minimal Validation

```bash
python -m py_compile scripts/study_store.py scripts/study_dashboard.py scripts/study_dashboard_server.py scripts/study_dashboard_launch.py scripts/study_profile_seed.py scripts/obsidian_sync.py
python scripts/study_dashboard.py --profile kaoyan --out-dir /var/www/study-planner/kaoyan
curl -I http://127.0.0.1:8790/api/health
```

If Nginx is configured:

```bash
curl -I https://study.example.com/
curl -I https://study.example.com/api/health
```
