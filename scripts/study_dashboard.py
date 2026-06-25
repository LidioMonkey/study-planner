#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import argparse
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
STORE = SCRIPT_DIR / "study_store.py"
PROFILE_NAME = "default"
CODEX_HOME = DEFAULT_CODEX_HOME
PROFILE_DIR = CODEX_HOME / "study-planner" / "profiles" / PROFILE_NAME
OUT_DIR = CODEX_HOME / "study-planner" / "dashboards" / PROFILE_NAME
RUN_DATE = date.today().isoformat()
API_HOST = "127.0.0.1"
API_PORT = 8790
STATIC_PORT = 8787
COURSE_CAP = 40
ANALYTICS_DAYS = 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Study Planner HTML dashboard.")
    parser.add_argument("--profile", default=os.environ.get("STUDY_PROFILE", "default"))
    parser.add_argument("--codex-home", default=str(DEFAULT_CODEX_HOME))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--api-host", default=os.environ.get("STUDY_DASHBOARD_API_HOST", "127.0.0.1"))
    parser.add_argument("--api-port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_API_PORT", "8790")))
    parser.add_argument("--static-port", type=int, default=int(os.environ.get("STUDY_DASHBOARD_STATIC_PORT", "8787")))
    parser.add_argument("--course-cap", type=int, default=40)
    parser.add_argument("--analytics-days", type=int, default=7)
    return parser.parse_args()


def configure(args: argparse.Namespace) -> None:
    global PROFILE_NAME, CODEX_HOME, PROFILE_DIR, OUT_DIR, RUN_DATE, API_HOST, API_PORT, STATIC_PORT, COURSE_CAP, ANALYTICS_DAYS
    PROFILE_NAME = args.profile
    CODEX_HOME = Path(args.codex_home).expanduser()
    PROFILE_DIR = CODEX_HOME / "study-planner" / "profiles" / PROFILE_NAME
    OUT_DIR = Path(args.out_dir).expanduser() if args.out_dir else CODEX_HOME / "study-planner" / "dashboards" / PROFILE_NAME
    RUN_DATE = args.date
    API_HOST = args.api_host
    API_PORT = args.api_port
    STATIC_PORT = args.static_port
    COURSE_CAP = args.course_cap
    ANALYTICS_DAYS = args.analytics_days


def read_json(name: str, default):
    path = PROFILE_DIR / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def run_report(*args: str):
    cmd = ["python", str(STORE), *args]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return json.loads(result.stdout)


def safe_report(*args: str, default=None):
    try:
        return run_report(*args)
    except Exception as exc:
        return default if default is not None else {"error": str(exc), "args": list(args)}


def pct(done: int, total: int) -> float:
    return round(done / total * 100, 1) if total else 0


def main() -> None:
    configure(parse_args())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    goals = read_json("goals.json", {})
    courses = read_json("courses.json", [])
    exercises = read_json("exercises.json", [])
    reviews = read_json("review_queue.json", [])
    logs = read_json("daily_logs.json", [])
    mistakes = read_json("mistakes.json", [])
    modules = read_json("modules.json", [])
    papers = read_json("papers.json", [])
    materials = read_json("materials.json", [])
    current_week = read_json("current_week.json", {})

    data = {
        "generated": date.today().isoformat(),
        "profile": PROFILE_NAME,
        "codexHome": str(CODEX_HOME),
        "profileDir": str(PROFILE_DIR),
        "outDir": str(OUT_DIR),
        "apiBase": f"http://{API_HOST}:{API_PORT}",
        "staticUrl": f"http://127.0.0.1:{STATIC_PORT}/",
        "scripts": {
            "dashboard": str(SCRIPT_DIR / "study_dashboard.py"),
            "server": str(SCRIPT_DIR / "study_dashboard_server.py"),
            "launcher": str(SCRIPT_DIR / "study_dashboard_launch.py"),
            "store": str(STORE),
        },
        "goals": goals,
        "courses": courses,
        "exercises": exercises,
        "reviews": reviews,
        "logs": logs,
        "mistakes": mistakes,
        "modules": modules,
        "papers": papers,
        "materials": materials,
        "currentWeek": current_week,
        "inventory": safe_report("inventory", "--profile", PROFILE_NAME, default={"inventory": {}, "pending_reviews": {}}),
        "phase": safe_report("phase-report", "--profile", PROFILE_NAME, "--date", RUN_DATE, default={"phase": "未初始化", "days_left": 0, "rules": []}),
        "blocked": safe_report("blocked-report", "--profile", PROFILE_NAME, default={"suggestion": "暂无阻塞分析", "top_blockers": [], "blocked_tasks": []}),
        "courseRatio": safe_report("course-ratio-report", "--profile", PROFILE_NAME, "--source", "current-week", "--cap", str(COURSE_CAP), default={"course_ratio_percent": 0, "course_cap_percent": COURSE_CAP, "status": "ok"}),
        "analytics": safe_report("analytics-report", "--profile", PROFILE_NAME, "--end", RUN_DATE, "--days", str(ANALYTICS_DAYS), default={}),
        "model408": safe_report("408-model-report", "--profile", PROFILE_NAME, default={"model": {}}),
        "catalogAudit": safe_report("catalog-audit", "--profile", PROFILE_NAME, default={"summary": {}, "items": []}),
    }
    html = render_html(data)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")


def render_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2027 考研</title>
  <style>
    :root {{
      --ink:#18211c; --muted:#66736b; --paper:#f7f4ed; --panel:#fffdf7;
      --line:#d9d1c3; --green:#2f7d57; --blue:#345f8a; --red:#a4493d;
      --amber:#b47a29; --black:#101511;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; color:var(--ink); background:
        linear-gradient(90deg, rgba(16,21,17,.045) 1px, transparent 1px) 0 0/28px 28px,
        linear-gradient(rgba(16,21,17,.035) 1px, transparent 1px) 0 0/28px 28px,
        var(--paper);
      font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
      letter-spacing:0;
    }}
    header {{
      padding:0 clamp(14px,2.4vw,32px) 16px;
      border-bottom:1px solid rgba(16,21,17,.35);
      background:var(--paper);
    }}
    .exam-hero {{
      position:relative; overflow:hidden; min-height:310px; border-radius:0 0 14px 14px;
      background:
        linear-gradient(90deg, rgba(16,21,17,.04) 1px, transparent 1px) 0 0/80px 60px,
        linear-gradient(rgba(16,21,17,.03) 1px, transparent 1px) 0 0/80px 60px,
        radial-gradient(circle at 75% 18%, rgba(209,166,74,.12), transparent 32%),
        var(--paper);
      color:var(--ink); padding:24px clamp(22px,3.2vw,42px) 26px;
      box-shadow:0 18px 36px rgba(16,21,17,.08);
    }}
    .exam-kicker {{
      color:var(--muted); font-size:14px; letter-spacing:8px; text-transform:uppercase; font-weight:700;
    }}
    .exam-title {{ margin:12px 0 38px; font-size:clamp(58px,8vw,104px); line-height:.85; font-weight:900; letter-spacing:0; }}
    .hero-countdown {{ display:flex; align-items:end; gap:28px; flex-wrap:wrap; }}
    .time-block {{ min-width:112px; }}
    .time-value {{
      font-size:clamp(54px,6.5vw,86px); line-height:.86; font-weight:900; font-variant-numeric:tabular-nums;
      color:var(--ink);
    }}
    .time-label {{ color:var(--muted); font-size:12px; text-align:center; margin-top:12px; }}
    .time-sep {{ color:#6f675d; font-size:42px; font-weight:900; padding-bottom:23px; }}
    .exam-sub {{ color:var(--muted); font-size:14px; padding-bottom:20px; }}
    nav {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }}
    nav button {{
      border:1px solid var(--black); background:var(--panel); padding:9px 12px; cursor:pointer;
      font-weight:800; border-radius:0; min-height:38px;
    }}
    nav button.active {{ background:var(--black); color:var(--paper); }}
    main {{ padding:24px clamp(18px,2.4vw,40px) 48px; width:100%; max-width:none; margin:0; }}
    .grid {{ display:grid; gap:14px; }}
    .stats {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .two {{ grid-template-columns:1.2fr .8fr; }}
    .three {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .card {{
      background:linear-gradient(180deg, #fffdf8 0%, #fbf6ec 100%); border:1px solid rgba(29,36,31,.55); padding:16px 16px 14px; box-shadow:0 10px 24px rgba(16,21,17,.08);
      border-radius:8px;
      min-width:0;
    }}
    .card h2, .card h3 {{ margin:0 0 12px; line-height:1.15; }}
    .card h2 {{ font-size:18px; }}
    .card h3 {{ font-size:15px; }}
    .metric {{ font-size:30px; font-weight:900; line-height:1; }}
    .label {{ color:var(--muted); font-size:12px; margin-top:6px; }}
    .bar {{ height:8px; border:1px solid rgba(29,36,31,.5); background:#eee2cf; overflow:hidden; margin:8px 0; border-radius:999px; }}
    .bar > i {{ display:block; height:100%; background:linear-gradient(90deg, #3f6f4a, #88a95e); }}
    .pill {{ display:inline-flex; align-items:center; border:1px solid rgba(29,36,31,.55); padding:4px 7px; margin:2px; font-size:12px; font-weight:800; background:#efe3c8; border-radius:999px; }}
    .pill.red {{ background:#ecd0c8; }} .pill.blue {{ background:#d4e2ef; }} .pill.green {{ background:#d6e6d6; }}
    .subject-board {{ display:grid; gap:16px; }}
    .subject-card {{
      position:relative; overflow:hidden; padding:18px;
      background:linear-gradient(180deg,#fffdfa 0%,#fbf5e9 100%);
    }}
    .subject-card::before {{
      content:""; position:absolute; inset:0 auto 0 0; width:5px;
      background:linear-gradient(180deg,#315f43,#d1a64a); opacity:.9;
    }}
    .subject-head {{
      display:grid; grid-template-columns:minmax(0,1fr) 180px; gap:18px; align-items:start;
      margin:0 0 14px 0; padding-left:8px;
    }}
    .subject-head h2 {{ font-size:23px; margin-bottom:5px; }}
    .subject-head .metric {{ font-size:30px; text-align:right; }}
    .subject-score {{ display:grid; justify-items:end; gap:4px; }}
    .subject-score .bar {{ width:170px; margin:2px 0 0; }}
    .resource-groups {{ display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); gap:12px; padding-left:8px; }}
    .resource-group {{
      grid-column:span 6; border:1px solid #d9cdbd; background:rgba(255,255,255,.74); border-radius:8px; padding:12px; min-width:0;
      box-shadow:0 6px 14px rgba(42,35,24,.04);
    }}
    .resource-group.is-wide {{ grid-column:1 / -1; }}
    .resource-group h3 {{ display:flex; justify-content:space-between; gap:8px; align-items:center; margin-bottom:10px; font-size:16px; }}
    .resource-list {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:10px; }}
    .resource-row {{ border:1px solid #ded3c4; background:#fffdfa; border-radius:8px; padding:12px; display:grid; gap:7px; }}
    .resource-title {{ font-weight:900; line-height:1.35; overflow-wrap:break-word; font-size:16px; }}
    .resource-meta {{ color:var(--muted); font-size:12px; line-height:1.5; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
    .resource-status {{ display:flex; gap:6px; flex-wrap:wrap; align-items:center; }}
    .chapter-strip {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(26px,1fr)); gap:4px; margin-top:2px; }}
    .chapter-dot {{
      height:18px; border:1px solid transparent; background:#eee3d1; font-size:0; display:block; min-width:0; border-radius:5px;
      box-shadow:inset 0 0 0 1px rgba(29,36,31,.12);
    }}
    .chapter-dot::after {{ content:attr(data-label); font-size:10px; color:rgba(29,36,31,.55); display:flex; align-items:center; justify-content:center; height:100%; }}
    .chapter-dot.done {{ background:#cfe1cf; border-color:#8daf92; }}
    .chapter-dot.pending {{ background:#f2e7d7; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px 6px; text-align:left; vertical-align:top; }}
    th {{ color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .section {{ display:none; }} .section.active {{ display:block; }}
    #week {{ overflow-x:auto; padding-bottom:8px; }}
    .week-grid {{ display:grid; grid-template-columns:1fr; gap:18px; align-items:start; min-width:1320px; }}
    .day {{
      margin-bottom:0;
      border-left:none;
      position:relative;
      overflow:hidden;
      display:grid;
      grid-template-columns:160px 1fr;
      gap:16px;
    }}
    .day::before {{
      content:"";
      position:absolute;
      left:0; top:0; right:0;
      height:4px;
      background:linear-gradient(90deg, var(--green) 0%, #7ea98d 100%);
    }}
    .day-head {{ display:grid; gap:12px; align-content:start; padding-top:10px; }}
    .day-head h2 {{ font-size:20px; }}
    .day-progress {{
      width:max-content; min-width:72px; text-align:left; font-weight:900; font-size:13px;
      color:#355641; background:#edf4ec; border:1px solid #bfd2c2; padding:6px 8px; border-radius:999px;
    }}
    .todo-groups {{ display:grid; grid-template-columns:1fr; gap:12px; align-items:start; }}
    .todo-group {{
      border:1px solid #ddd3c4; padding:12px; min-width:0; border-radius:8px;
      background:rgba(255,255,255,.72);
      display:grid; grid-template-columns:132px 1fr; gap:12px; align-items:start;
    }}
    .todo-group.is-empty {{ display:none; }}
    .todo-group h3 {{ display:grid; gap:8px; align-content:start; font-size:14px; margin:0; }}
    .todo-group h3 .pill {{ width:max-content; margin:0; }}
    .todo-list {{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(auto-fit,minmax(480px,1fr)); gap:10px; }}
    .todo-item {{ margin:0; }}
    .todo-item label {{
      display:grid; grid-template-columns:24px 1fr; gap:9px; align-items:start;
      border:1px solid #ddd4c7; background:#fffdfa; padding:11px 12px 10px; cursor:pointer; min-height:44px; border-radius:8px;
    }}
    .todo-item input {{ width:18px; height:18px; margin:1px 0 0; accent-color:var(--green); cursor:pointer; }}
    .todo-title {{ display:block; font-weight:800; font-size:16px; line-height:1.42; overflow-wrap:break-word; word-break:normal; }}
    .todo-meta {{ color:var(--muted); font-size:12px; margin-top:3px; }}
    .todo-detail {{ display:grid; gap:2px; color:var(--muted); font-size:12px; margin-top:7px; line-height:1.45; }}
    .todo-detail .extra-detail {{ display:none; }}
    .todo-item label:hover .extra-detail,
    .todo-item label:focus-within .extra-detail {{ display:block; }}
    .todo-item.done label {{ background:#e6eadf; }}
    .todo-item.done .todo-title {{ text-decoration:line-through; color:var(--muted); }}
    .sync-state {{ margin-top:6px; font-size:12px; font-weight:800; }}
    .sync-state.ok {{ color:var(--green); }} .sync-state.warn {{ color:var(--amber); }} .sync-state.bad {{ color:var(--red); }}
    .calendar {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .calendar-day {{ border:1px solid var(--black); background:#fffaf0; padding:12px; min-width:0; }}
    .calendar-day h3 {{ margin:0 0 8px; display:flex; justify-content:space-between; gap:8px; }}
    .calendar-day ul {{ margin-left:16px; }}
    .week-tools {{ display:grid; gap:10px; margin-bottom:14px; }}
    .tool-row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
    .tool-row button {{
      border:2px solid var(--black); background:#efe3c8; padding:9px 12px; cursor:pointer;
      font-weight:900; min-height:38px;
    }}
    .tool-row button.primary {{ background:var(--black); color:var(--paper); }}
    .export-box {{
      width:100%; min-height:180px; resize:vertical; border:2px solid var(--black);
      background:#fffaf0; color:var(--ink); padding:12px; font:13px/1.55 "Microsoft YaHei", "Noto Sans SC", sans-serif;
    }}
    ul {{ margin:8px 0 0 18px; padding:0; }} li {{ margin:5px 0; }}
    code {{ background:#efe3c8; padding:2px 5px; border:1px solid var(--line); }}
    .deploy {{ grid-template-columns:1fr 1fr; }}
    .command {{ background:#141814; color:#f5f0e7; padding:12px; overflow:auto; border:2px solid var(--black); }}
    .muted {{ color:var(--muted); }}
    .overview-grid {{ display:grid; grid-template-columns:1.15fr .85fr; gap:14px; }}
    .overview-side {{ display:grid; gap:14px; }}
    .donut-board {{ display:grid; grid-template-columns:220px 1fr; gap:20px; align-items:center; }}
    .donut {{
      width:210px; aspect-ratio:1; border-radius:50%;
      background:conic-gradient(var(--green) calc(var(--p)*1%), #eadfcd 0);
      display:grid; place-items:center; box-shadow:inset 0 0 0 1px rgba(29,36,31,.45);
    }}
    .donut::before {{ content:""; width:132px; aspect-ratio:1; border-radius:50%; background:#fffdf8; box-shadow:inset 0 0 0 1px var(--line); }}
    .donut-label {{ position:absolute; text-align:center; font-weight:900; }}
    .donut-wrap {{ position:relative; display:grid; place-items:center; }}
    .subject-progress-list {{ display:grid; gap:10px; }}
    .subject-progress-row {{ display:grid; grid-template-columns:92px 1fr 54px; gap:10px; align-items:center; }}
    .today-list {{ display:grid; gap:10px; margin:0; padding:0; list-style:none; }}
    .today-card {{ border:1px solid #ddd3c4; background:#fffdfa; border-radius:8px; padding:11px 12px; }}
    .today-card b {{ display:block; font-size:15px; margin-bottom:4px; }}
    .today-card span {{ display:block; color:var(--muted); font-size:12px; line-height:1.45; }}
    .risk-list {{ display:grid; gap:8px; }}
    .risk-item {{ display:flex; justify-content:space-between; gap:12px; border-bottom:1px solid var(--line); padding:7px 0; }}
    @media (max-width:1500px) {{ .todo-list {{ grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); }} }}
    @media (max-width:1200px) {{ .week-grid {{ grid-template-columns:1fr; }} }}
    @media (max-width:1100px) {{ .day {{ grid-template-columns:1fr; }} .todo-group {{ grid-template-columns:1fr; }} .todo-list {{ grid-template-columns:1fr; }} }}
    @media (max-width:900px) {{ .stats,.two,.three,.deploy,.calendar,.resource-groups,.overview-grid,.donut-board {{ grid-template-columns:1fr; }} header {{ position:static; }} .exam-hero {{ min-height:0; }} .time-block {{ min-width:86px; }} }}
    @media (max-width:640px) {{ .day-progress {{ text-align:left; }} }}
  </style>
</head>
<body>
  <header>
    <div class="exam-hero">
      <div class="exam-kicker">Graduate Entrance Exam</div>
      <div class="exam-title">2027 考研</div>
      <div class="hero-countdown" id="heroCountdown">
        <div class="time-block"><div class="time-value">--</div><div class="time-label">天</div></div>
        <div class="time-sep">:</div>
        <div class="time-block"><div class="time-value">--</div><div class="time-label">时</div></div>
        <div class="time-sep">:</div>
        <div class="time-block"><div class="time-value">--</div><div class="time-label">分</div></div>
        <div class="time-sep">:</div>
        <div class="time-block"><div class="time-value">--</div><div class="time-label">秒</div></div>
        <div class="exam-sub" id="heroSub">距 2027 考研初试</div>
      </div>
    </div>
    <nav id="tabs"></nav>
  </header>
  <main id="app"></main>
  <script>
    const DATA = {payload};
    const PROFILE = DATA.profile || "default";
    const API_BASE = DATA.apiBase || "http://127.0.0.1:8790";
    const tabs = [
      ["overview","总览"],["week","本周"],["subjects","科目"],["reviews","复习"],
      ["materials","资料目录"],["mistakes","错题/真题"],["diagnostics","高级诊断"],["deploy","部署"]
    ];
    const app = document.getElementById("app");
    const heroCountdown = document.getElementById("heroCountdown");
    const heroSub = document.getElementById("heroSub");
    document.getElementById("tabs").innerHTML = tabs.map((t,i)=>`<button class="${{i===0?'active':''}}" data-tab="${{t[0]}}">${{t[1]}}</button>`).join("");
    document.getElementById("tabs").onclick = e => {{
      if(e.target.tagName !== "BUTTON") return;
      document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("active", b===e.target));
      document.querySelectorAll(".section").forEach(s=>s.classList.toggle("active", s.id===e.target.dataset.tab));
    }};
    const esc = v => String(v ?? "").replace(/[&<>"]/g, s=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[s]));
    const pct = (done,total)=> total ? Math.round(done/total*1000)/10 : 0;
    const pad2 = n => String(n).padStart(2, "0");
    function getCountdownTarget() {{
      if (DATA.goals?.deadline) {{
        const end = new Date(DATA.goals.deadline + "T23:59:59");
        return {{ date:end, label:"距 2027 考研初试", target:`${{DATA.goals.deadline}} 23:59:59` }};
      }}
      const weekStart = DATA.currentWeek?.start;
      const weekDays = DATA.currentWeek?.days || 0;
      if (weekStart && weekDays) {{
        const end = new Date(weekStart + "T00:00:00");
        end.setDate(end.getDate() + weekDays - 1);
        end.setHours(23, 59, 59, 999);
        return {{ date:end, label:"本周期剩余", target:`${{ymd(end)}} 23:59:59` }};
      }}
      return null;
    }}
    function renderTopCountdown() {{
      const target = getCountdownTarget();
      if (!target) {{
        heroCountdown.querySelectorAll(".time-value").forEach(node => node.textContent = "--");
        heroSub.textContent = `档案 ${{PROFILE}} · 尚未设置截止日期`;
        return;
      }}
      const ms = Math.max(target.date - new Date(), 0);
      const totalSeconds = Math.floor(ms / 1000);
      const days = Math.floor(totalSeconds / 86400);
      const hours = Math.floor((totalSeconds % 86400) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      const values = [days, pad2(hours), pad2(minutes), pad2(seconds)];
      heroCountdown.querySelectorAll(".time-value").forEach((node, index) => node.textContent = values[index]);
      heroSub.textContent = `${{target.label}} · 目标 ${{target.target}}`;
    }}
    const mapText = {{
      "foundation-close":"基础后段", "strengthening":"强化阶段", "past-exam":"真题阶段", "sprint":"冲刺阶段",
      "green":"安全", "yellow":"预警", "red":"危险", "ok":"正常", "over_cap":"超标",
      "course":"课程", "exercise":"习题", "review":"复习", "pending":"待完成", "done":"已完成",
      "timed":"限时", "untimed":"不限时", "partial":"部分完成", "missed":"未完成",
      "concept":"概念", "calculation":"计算", "method":"方法", "timing":"时间分配",
      "Math II":"数学二", "English II":"英语二", "Politics":"政治",
      "408":"408",
      "408 - Data Structure":"408 数据结构", "408 - Computer Organization":"408 计组",
      "408 - Operating System":"408 操作系统", "408 - Computer Network":"408 计网",
      "Math II - Linear Algebra":"数学二 线代", "Math II - Advanced Math":"数学二 高数",
      "Wu Zhongxiang high math":"武忠祥高数", "Wu selected problems":"武忠祥严选题",
      "Wu Zhongxiang strengthening guide":"武忠祥强化讲义", "Li Yongle linear algebra foundation":"李永乐线代基础",
      "Li Yongle foundation exercises":"李永乐基础篇习题", "Wangdao data structure":"王道数据结构",
      "Wangdao computer organization":"王道计组", "Wangdao operating system":"王道操作系统",
      "Wangdao computer network":"王道计网", "Wangdao after-class questions":"王道课后题",
      "Turing 1800":"图灵 1800", "Bubei vocabulary app":"不背单词 App",
      "Liu Xiaoyan materials":"刘晓艳资料", "Liu Xiaoyan 58 readings":"刘晓艳 58 篇阅读",
      "Xu Tao intro route":"徐涛导学路线", "Xiao 1000":"肖秀荣 1000 题",
      "Weak point":"薄弱点", "Double integrals":"二重积分", "Eigenvalues and eigenvectors":"特征值与特征向量",
      "Instruction system tail":"第4章 指令系统", "Processes and threads":"进程与线程",
      "Scheduling and PV":"调度与 PV", "Architecture and layering":"体系结构与分层",
      "Long sentences":"长难句", "Framework warm-up":"框架预热", "Sorting":"排序",
      "CPU":"CPU", "Quadratic forms":"二次型", "Advanced math strengthening phase":"高数强化阶段"
    }};
    const phraseMap = [
      ["repair exercises after finishing the course section","完成课后习题并订正错题"],
      ["close double-integral foundation tail","完成二重积分基础章节"],
      ["summary of computation regions and coordinate choices","计算区域与坐标选择总结"],
      ["finish remaining selected problems","完成剩余严选题"],
      ["wrong-question notes and method summary","错题笔记与方法总结"],
      ["foundation exercises for eigenvalues/eigenvectors","特征值与特征向量基础篇习题"],
      ["conditions and procedure checklist","条件与步骤清单"],
      ["foundation exercises for diagonalization","矩阵对角化基础篇习题"],
      ["canonical-form and positive-definite checklist","标准形与正定性清单"],
      ["foundation exercises for quadratic forms","二次型基础篇习题"],
      ["continue current sorting chapter","继续排序章节"],
      ["algorithm comparison table and weak examples","算法对比表与薄弱例题"],
      ["Wangdao after-class sorting questions","王道排序课后题"],
      ["wrong-question causes and instruction-format notes","错因与指令格式笔记"],
      ["Wangdao instruction system after-class questions","王道指令系统课后题"],
      ["datapath/control unit framework","数据通路与控制器框架"],
      ["Wangdao CPU after-class questions","王道 CPU 课后题"],
      ["process-thread-state framework","进程、线程与状态框架"],
      ["Wangdao OS process/thread questions","王道 OS 进程线程题"],
      ["scheduling comparison table and PV templates","调度对比表与 PV 模板"],
      ["Wangdao scheduling/PV questions","王道调度与 PV 题"],
      ["layer model and protocol-unit table","分层模型与协议单元表"],
      ["Wangdao architecture questions","王道体系结构题"],
      ["3 parsed long sentences and vocabulary notes","3 个长难句拆解与词汇笔记"],
      ["88 sentences or matching practice","88 句或配套练习"],
      ["light politics introduction and framework","政治轻量导学与框架"],
      ["first-level framework notes","一级框架笔记"],
      ["light multiple-choice warm-up after materials are ready","资料到位后轻量选择题预热"],
      ["method framework and representative-problem notes","方法框架与代表题笔记"],
      ["matching strengthening-guide problems","配套强化讲义习题"],
      ["start OS from process/thread basics","学习进程与线程基础"],
      ["clear remaining instruction-system exercises","完成指令系统习题订正"],
      ["entry route for scheduling and PV problems","调度与 PV 问题入门"],
      ["eigenvalues and eigenvectors","特征值与特征向量"],
      ["instruction system tail","第4章 指令系统"],
      ["process threads scheduling PV","进程线程、调度与 PV"],
      ["sorting","排序"],
      ["start diagonalization after eigenvalue exercise repair","完成特征值习题后学习矩阵对角化"],
      ["advanced math launch after double-integral close","进入高数 660 二重积分题组"],
      ["second pass vocabulary","词汇二刷"],
      ["start central processor unit chapter","学习中央处理器章节"],
      ["matrix diagonalization","矩阵对角化"],
      ["architecture and layering","体系结构与分层模型"],
      ["start CN from architecture and layered model","学习计网体系结构与分层模型"],
      ["start long-sentence foundation","学习长难句基础"],
      ["finish first-round linear algebra tail","线代一轮收尾"],
      ["foundation reading launch","基础阅读第1篇"],
      ["data structure weak-topic selective choices","数据结构弱点专项选择题"],
      ["start strengthening guide after 660 launch","完成 660 后进入高数强化讲义"],
      ["double-integral tail","二重积分章节"],
      ["warm-up after framework starts","完成框架学习后的选择题巩固"],
      ["finish remaining problems, correct mistakes, summarize region-choice patterns","完成剩余题目，订正错题，总结积分区域选择模式"],
      ["correct all wrong questions and mark concept/calculation/method causes","订正全部错题，并标记概念、计算、方法错因"],
      ["repair post-course gap, correct all mistakes, summarize conditions","修补课后缺口，订正全部错题，总结适用条件"],
      ["write diagonalization condition checklist and correct mistakes","写出对角化条件清单并订正错题"],
      ["correct all wrong choices and compare sorting algorithms","订正全部错选题，并比较排序算法"],
      ["start selective practice after Wangdao sorting, tag weak topics","王道排序后完成选择题巩固，并标记薄弱点"],
      ["clear remaining tail and correct mistakes","完成剩余题目并订正错题"],
      ["match CPU framework with questions and correct mistakes","用题目校准 CPU 框架并订正错题"],
      ["build OS entry confidence and tag conceptual gaps","建立 OS 入门信心，并标记概念缺口"],
      ["start CN from zero and correct conceptual questions","学习计网第1章并订正概念题"],
      ["finish daily push and mark stubborn words","完成每日推词，并标记顽固词"],
      ["finish one passage, locate wrong-answer evidence, extract 10 words and 3 long sentences","完成 1 篇阅读，定位错因证据，摘出 10 个单词和 3 个长难句"],
      ["record confusing knowledge points; low priority before formal start","记录混淆知识点；首轮前低优先级处理"],
      ["B tree concepts, insertion/deletion/search details, representative choices","B 树：插入、删除、查找与典型选择题"],
      ["critical path: AOE network, earliest/latest time, slack, typical calculation","关键路径：AOE 网、最早/最迟时间、时差与计算"],
      ["Cache mapping: direct, fully associative, set associative, address partition","Cache 映射：直接、全相联、组相联与地址划分"],
      ["pipeline: speedup, throughput, hazard, timing diagram problems","流水线：加速比、吞吐率、相关与时序图"],
      ["finish 20 minutes of","完成 20 分钟"],
      ["and write 3 key points","并写 3 个关键点"],
      ["do 8 questions from","做 8 题，来源"],
      ["do 10 questions from","做 10 题，来源"],
      ["do 40 questions from","完成 40 个，来源"],
      ["and correct mistakes","并订正错题"],
      ["questions, untimed","题，不限时"],
      ["questions, timed","题，限时"],
      ["minutes","分钟"],
      ["output:","输出："],
      ["acceptance:","验收："],
      ["paired practice:","配套练习："],
      ["finish 20 minutes from","完成 20 分钟，资料"],
      ["and write 3 key points for","并写 3 个关键点；验收"],
      ["do 5 questions from","做 5 题，来源"],
      ["do 6 questions from","做 6 题，来源"],
      ["Review 1 due item and mark whether it still feels weak.","复习 1 个到期项目，并标记是否仍薄弱"],
      ["Complete one 25-minute focused study task and log the result.","完成 1 个 25 分钟专注学习任务并记录结果"],
      ["Close first-round gaps and start blank subjects.","完成一轮缺口处理，并安排空白科目章节"],
      ["Keep course ratio at or below 40%.","课程占比控制在 40% 以内"],
      ["Every course slice must pair with output and practice.","每个课程切片必须绑定输出和练习"],
      ["Course input is within cap. Keep pairing courses with exercises and review.","课程输入占比正常。继续保证课程、习题和复习配套。"],
      ["Lower course ratio to 20%.","课程占比降到 20% 左右"],
      ["Protect main question banks, mistakes, and review.","优先保护主线题库、错题和复习"],
      ["Use extra teachers only for weak points.","额外老师只用于薄弱点补强"],
      ["Protect","优先保护"], ["first; it unlocks","；它能解锁"], ["pending task(s).","个待办任务"],
      ["Processes and threads","进程与线程"], ["Matrix diagonalization","矩阵对角化"]
    ];
    const topicMap = {{
      "linear list":"线性表", "stack queue array":"栈/队列/数组", "tree":"树", "graph":"图",
      "search":"查找", "sorting":"排序", "data representation":"数据表示", "instruction system":"指令系统",
      "cpu":"CPU", "memory":"存储系统", "io":"I/O", "process threads":"进程与线程",
      "scheduling pv":"调度与 PV", "memory management":"内存管理", "file system":"文件系统",
      "architecture":"体系结构", "physical":"物理层", "data link":"数据链路层",
      "network layer":"网络层", "transport layer":"传输层", "application":"应用层"
    }};
    const materialMap = Object.fromEntries((DATA.materials||[]).map(m=>[m.id,m]));
    function zh(v) {{
      let s = String(v ?? "");
      if (mapText[s]) return mapText[s];
      if (topicMap[s]) return topicMap[s];
      s = s.replace(/^([^:：]+):\\s*do\\s+(\\d+)\\s+questions from\\s+(.+?)\\s+and correct mistakes\\.?$/, (_, subject, count, source) =>
        `${{zh(subject)}}：做 ${{count}} 题，来源 ${{zh(source)}}，并订正错题`);
      for (const [a,b] of phraseMap) s = s.replaceAll(a,b);
      s = s.replace(/^([^:：]+):\\s*完成 20 分钟\\s+(.+?)\\s+并写 3 个关键点\\.?$/, (_, subject, task) =>
        `${{zh(subject)}}：完成 20 分钟 ${{zh(task)}}，并写 3 个关键点`);
      s = s.replace(/^([^:：]+):\\s*做\\s+(\\d+)\\s+题，来源\\s+(.+?)\\s+并订正错题\\.?$/, (_, subject, count, source) =>
        `${{zh(subject)}}：做 ${{count}} 题，来源 ${{zh(source)}}，并订正错题`);
      s = s.replace(/^([^:：]+):\\s*完成\\s+(\\d+)\\s+个，来源\\s+(.+?)\\s+并订正错题\\.?$/, (_, subject, count, source) =>
        `${{zh(subject)}}：做 ${{count}} 题，来源 ${{zh(source)}}，并订正错题`);
      s = s.replace(/^([^:：]+)：/, (_, subject) => `${{zh(subject)}}：`);
      return s;
    }}
    const taskName = t => esc(zh(t.task || t.slice || t.scope || t.chapter_or_scope || t.title_or_resource || t.content || t.id));
    const taskLine = t => `<li><code>${{esc(t.id)}}</code> ${{esc(zh(t.subject))}}：${{taskName(t)}}</li>`;
    const ymd = d => `${{d.getFullYear()}}-${{String(d.getMonth()+1).padStart(2,"0")}}-${{String(d.getDate()).padStart(2,"0")}}`;
    function materialLabel(materialId) {{
      const material = materialMap[materialId];
      return material ? `${{materialId}}（${{zh(material.name)}}）` : zh(materialId);
    }}
    function catalogPillClass(status, hasMaterial=true) {{
      if (!hasMaterial) return "red";
      if (status === "complete") return "green";
      if (status === "partial") return "blue";
      return "red";
    }}
    function catalogStatusText(status, hasMaterial=true, completeText="已建章节目录") {{
      if (!hasMaterial) return "未绑定真实目录";
      if (status === "complete") return completeText;
      if (status === "partial") return "部分目录";
      return "目录缺失";
    }}
    function catalogUnitLabel(materialId, unitId) {{
      const material = materialMap[materialId];
      const unit = (material?.catalog_units || []).find(row => row.id === unitId);
      return unit ? `${{unitId}}（${{zh(unit.title)}}）` : zh(unitId);
    }}
    const todoKey = (date, layer, item, index) => `${{PROFILE}}-week-${{DATA.currentWeek.start || "current"}}:${{date}}:${{layer}}:${{item?.id || index}}`;
    const layerText = {{ main:"主线任务", review:"复习任务", extra:"加餐任务" }};
    function todoTitle(item) {{
      if (typeof item === "string") return zh(item);
      const action = item.task || item.slice || item.scope || item.chapter_or_scope || item.content || item.id;
      return `${{zh(item.subject)}}：${{zh(action)}}`;
    }}
    function todoItem(date, layer, item, index) {{
      const key = todoKey(date, layer, item, index);
      const title = todoTitle(item);
      const meta = typeof item === "string" ? "文本任务" : `${{zh(item.type)}}${{item.id ? " · " + item.id : ""}}${{item.priority ? " · 优先级 " + item.priority : ""}}`;
      const primaryDetails = typeof item === "string" ? [] : [
        item.material ? `资料：${{zh(item.material)}}` : "",
        item.scope ? `范围：${{zh(item.scope)}}` : "",
        item.quantity ? `数量：${{zh(item.quantity)}}` : "",
        item.acceptance || item.output_or_acceptance ? `验收：${{zh(item.acceptance || item.output_or_acceptance)}}` : ""
      ].filter(Boolean);
      const extraDetails = typeof item === "string" ? [] : [
        item.knowledge_point ? `知识点：${{zh(item.knowledge_point)}}` : "",
        item.review_kind === "mistake" ? "类型：错题回炉" : (item.type === "review" ? "类型：知识点复习" : ""),
        item.prompt_items?.length ? `提问：${{item.prompt_items.map(zh).join(" / ")}}` : "",
        item.material_id ? `目录资料：${{materialLabel(item.material_id)}}` : "目录资料：未绑定真实目录",
        item.catalog_units?.length ? `目录单元：${{item.catalog_units.map(unit=>catalogUnitLabel(item.material_id, unit)).join("、")}}` : "目录单元：未指定",
        item.precise_range ? `精确范围：${{zh(item.precise_range)}}` : "",
        item.page_range ? `页码：${{zh(item.page_range)}}` : "",
        item.lecture_range ? `讲次：${{zh(item.lecture_range)}}` : "",
        item.problem_range ? `题号：${{zh(item.problem_range)}}` : ""
      ].filter(Boolean);
      const details = [
        ...primaryDetails.map(line=>`<span>${{esc(line)}}</span>`),
        ...extraDetails.map(line=>`<span class="extra-detail">${{esc(line)}}</span>`)
      ].join("");
      const raw = typeof item === "string" ? {{ text:item }} : item;
      const currentStatus = typeof item === "string" ? "" : (item.dashboard_status || "");
      return `<li class="todo-item" data-todo-item data-key="${{esc(key)}}" data-date="${{esc(date)}}" data-layer="${{esc(layer)}}" data-layer-name="${{esc(layerText[layer] || layer)}}" data-title="${{esc(title)}}" data-meta="${{esc(meta)}}" data-current-status="${{esc(currentStatus)}}" data-raw="${{esc(JSON.stringify(raw))}}">
        <label>
          <input type="checkbox" data-todo-check data-key="${{esc(key)}}" aria-label="${{esc(title)}}">
          <span><span class="todo-title">${{esc(title)}}</span><span class="todo-meta">${{esc(meta)}}</span><span class="todo-detail">${{details}}</span><span class="sync-state" data-sync-state></span></span>
        </label>
      </li>`;
    }}
    function todoGroup(title, date, layer, items) {{
      const hasItems = items && items.length;
      const list = hasItems ? items.map((item,index)=>todoItem(date, layer, item, index)).join("") : "";
      return `<div class="todo-group ${{hasItems ? "" : "is-empty"}}" data-todo-group><h3><span>${{title}}</span><span class="pill" data-group-count>0/0</span></h3><ul class="todo-list">${{list}}</ul></div>`;
    }}
    function metric(label,value,sub) {{ return `<div class="card"><div class="metric">${{esc(zh(value))}}</div><div class="label">${{label}}</div>${{sub?`<div class="muted">${{esc(zh(sub))}}</div>`:""}}</div>`; }}
    function dayTasksFor(dateText) {{
      const day = (DATA.currentWeek.plan || []).find(d => d.date === dateText) || (DATA.currentWeek.plan || [])[0] || {{}};
      return [...(day.main_tasks || []), ...(day.review_tasks || []), ...(day.optional_extra || [])];
    }}
    function currentWeekSubjectProgress() {{
      const rows = {{}};
      const addItem = (item, isDone) => {{
        const subject = item?.subject || "未分类";
        rows[subject] ??= {{ done: 0, total: 0 }};
        rows[subject].total += 1;
        if (isDone) rows[subject].done += 1;
      }};
      const domItems = [...document.querySelectorAll("[data-todo-item]")];
      if (domItems.length) {{
        domItems.forEach(item => {{
          let raw = {{}};
          try {{ raw = JSON.parse(item.dataset.raw || "{{}}"); }} catch {{}}
          const check = item.querySelector("[data-todo-check]");
          addItem(raw, Boolean(check?.checked));
        }});
        return rows;
      }}
      for (const day of DATA.currentWeek.plan || []) {{
        for (const item of [...(day.main_tasks || []), ...(day.review_tasks || []), ...(day.optional_extra || [])]) {{
          addItem(item, item?.dashboard_status === "done");
        }}
      }}
      return rows;
    }}
    function subjectProgressRows(inv) {{
      return Object.entries(inv).map(([subject,row]) => {{
        const done = row.done || 0;
        const total = done + (row.pending || 0) + (row.partial || 0) + (row.missed || 0);
        return `<div class="subject-progress-row"><b>${{esc(zh(subject))}}</b><div class="bar"><i style="width:${{pct(done,total)}}%"></i></div><span>${{Math.round(pct(done,total))}}%</span></div>`;
      }}).join("");
    }}
    function weekSubjectProgressRows(rows) {{
      const entries = Object.entries(rows).sort((a, b) => {{
        const aPct = pct(a[1].done || 0, a[1].total || 0);
        const bPct = pct(b[1].done || 0, b[1].total || 0);
        return bPct - aPct || String(a[0]).localeCompare(String(b[0]));
      }});
      return entries.length
        ? entries.map(([subject, row]) => `<div class="subject-progress-row"><b>${{esc(zh(subject))}}</b><div class="bar"><i style="width:${{pct(row.done || 0, row.total || 0)}}%"></i></div><span>${{(row.done || 0)}}/${{(row.total || 0)}}</span></div>`).join("")
        : `<div class="muted">本周暂无已排科目任务。</div>`;
    }}
    function todayCard(item) {{
      const title = todoTitle(item);
      const meta = [item.material, item.scope, item.quantity].filter(Boolean).map(zh).join(" · ");
      return `<li class="today-card"><b>${{esc(title)}}</b><span>${{esc(meta || zh(item.type || "任务"))}}</span></li>`;
    }}
    function currentWeekProgress() {{
      const items = [...document.querySelectorAll("[data-todo-item]")];
      if (items.length) {{
        const checks = items.map(item => item.querySelector("[data-todo-check]")).filter(Boolean);
        const done = checks.filter(check => check.checked).length;
        return {{ done, total: checks.length, pct: Math.round(pct(done, checks.length)) }};
      }}
      const days = DATA.currentWeek.plan || [];
      const total = days.reduce((sum, day) => sum + (day.main_tasks || []).length + (day.review_tasks || []).length + (day.optional_extra || []).length, 0);
      const done = days.reduce((sum, day) => {{
        const all = [...(day.main_tasks || []), ...(day.review_tasks || []), ...(day.optional_extra || [])];
        return sum + all.filter(item => item && item.dashboard_status === "done").length;
      }}, 0);
      return {{ done, total, pct: Math.round(pct(done, total)) }};
    }}
    function syncOverviewDonut() {{
      const stat = currentWeekProgress();
      const donut = document.querySelector("[data-week-donut]");
      const metric = document.querySelector("[data-week-donut-metric]");
      const label = document.querySelector("[data-week-donut-label]");
      if (donut) donut.style.setProperty("--p", stat.pct);
      if (metric) metric.textContent = `${{stat.pct}}%`;
      if (label) label.textContent = `${{stat.done}}/${{stat.total}} 本周任务`;
    }}
    function syncOverviewSubjectProgress() {{
      const node = document.querySelector("[data-week-subject-progress]");
      if (!node) return;
      node.innerHTML = weekSubjectProgressRows(currentWeekSubjectProgress());
    }}
    function renderOverview() {{
      const inv = DATA.inventory.inventory || {{}};
      const weekSubjectRows = currentWeekSubjectProgress();
      const reviews = Object.values(DATA.inventory.pending_reviews || {{}}).reduce((a,b)=>a+b,0);
      const weekProgress = currentWeekProgress();
      const weekStart = DATA.currentWeek.start;
      const weekDays = DATA.currentWeek.days || 0;
      const weekEndDate = weekStart && weekDays ? new Date(new Date(weekStart + "T00:00:00").getTime() + (weekDays - 1) * 86400000) : null;
      const weekEnd = weekEndDate ? ymd(weekEndDate) : "未生成";
      const today = new Date(DATA.generated + "T00:00:00");
      const cycleDaysLeft = weekEndDate ? Math.max(Math.ceil((weekEndDate - today) / 86400000), 0) : 0;
      const countdown = getCountdownTarget();
      const secondsLeft = countdown ? Math.max(Math.floor((countdown.date - new Date()) / 1000), 0) : 0;
      const todays = dayTasksFor(DATA.generated).slice(0,5);
      const risks = Object.entries(DATA.analytics?.delay_prediction || {{}})
        .filter(([,v])=>v.risk && v.risk !== "green")
        .slice(0,5);
      return `<section id="overview" class="section active">
        <div class="overview-grid">
          <div class="card">
            <h2>本周进度</h2>
            <div class="donut-board">
              <div class="donut-wrap"><div class="donut" data-week-donut style="--p:${{weekProgress.pct}}"></div><div class="donut-label"><div class="metric" data-week-donut-metric>${{weekProgress.pct}}%</div><div class="label" data-week-donut-label>${{weekProgress.done}}/${{weekProgress.total}} 本周任务</div></div></div>
              <div>
                <div class="subject-progress-list" data-week-subject-progress>${{weekSubjectProgressRows(weekSubjectRows)}}</div>
                <div style="margin-top:12px"><span class="pill green">课程占比 ${{DATA.courseRatio.course_ratio_percent}}%</span><span class="pill">本周到 ${{esc(weekEnd)}}</span><span class="pill blue">复习队列 ${{reviews}}</span></div>
              </div>
            </div>
          </div>
          <div class="overview-side">
            <div class="card"><h2>今日任务</h2><ul class="today-list">${{todays.length ? todays.map(todayCard).join("") : "<li class='today-card'><b>今天暂无任务</b><span>可以生成本周计划或记录完成情况。</span></li>"}}</ul></div>
            <div class="card"><h2>下一步</h2><p>${{esc(zh(DATA.blocked.suggestion))}}</p><div class="risk-list">${{risks.length ? risks.map(([s,v])=>`<div class="risk-item"><span>${{esc(zh(s))}}</span><span class="pill red">${{esc(zh(v.risk))}}</span></div>`).join("") : "<div class='muted'>当前没有红黄延期风险。</div>"}}</div></div>
          </div>
        </div>
      </section>`;
    }}
    function renderWeek() {{
      const days = DATA.currentWeek.plan || [];
      const exportPanel = `<div class="week-tools card">
        <h2>本周完成情况备用导出</h2>
        <div class="muted">默认已通过本地服务直接写入档案。只有本地服务不可用、需要迁移或备份时，再使用这里的导出文本。</div>
        <div class="tool-row">
          <span class="pill blue" data-api-status>本地写入服务：检测中</span>
          <button type="button" data-check-api>重新检测</button>
        </div>
        <div class="tool-row">
          <button class="primary" type="button" data-export-week>生成导出文本</button>
          <button type="button" data-copy-export>复制导出文本</button>
          <button type="button" data-download-export>下载 JSON</button>
          <span class="muted" data-export-status></span>
        </div>
        <textarea class="export-box" data-export-box placeholder="点击“生成导出文本”后，这里会出现可复制给 agent 的本周完成情况。"></textarea>
      </div>`;
      return `<section id="week" class="section"><div class="week-grid">
        ${{days.map(d=>`<div class="card day">
          <div class="day-head"><h2>${{d.date}}</h2><div class="day-progress" data-day-progress>0/0</div></div>
          <div class="todo-groups">
            ${{todoGroup("主线任务", d.date, "main", d.main_tasks || [])}}
            ${{todoGroup("复习任务", d.date, "review", d.review_tasks || [])}}
            ${{todoGroup("加餐任务", d.date, "extra", d.optional_extra || [])}}
          </div>
        </div>`).join("")}}
      </div>${{exportPanel}}</section>`;
    }}
    function renderSubjects() {{
      const tasks = [...(DATA.courses||[]), ...(DATA.exercises||[])];
      const subjects = {{}};
      const taskUnitsByMaterial = {{}};
      for (const task of tasks) {{
        if (!task.material_id) continue;
        taskUnitsByMaterial[task.material_id] ??= new Set();
        if (task.status === "done") {{
          for (const unit of task.catalog_units || []) taskUnitsByMaterial[task.material_id].add(unit);
        }}
      }}
      const materialTaskKinds = {{}};
      for (const task of tasks) {{
        if (!task.material_id) continue;
        materialTaskKinds[task.material_id] ??= {{course:0, exercise:0, doneTasks:0, totalTasks:0}};
        materialTaskKinds[task.material_id].totalTasks += 1;
        if (task.status === "done") materialTaskKinds[task.material_id].doneTasks += 1;
        if (task.type === "course") materialTaskKinds[task.material_id].course += 1;
        if (task.type === "exercise") materialTaskKinds[task.material_id].exercise += 1;
      }}
      const directSubjectMaterials = DATA.materials || [];
      for (const m of directSubjectMaterials) {{
        const subject = m.subject || "未分类";
        subjects[subject] ??= [];
        const units = (m.catalog_units || []).filter(u => !u.parent);
        const progress = m.progress || {{}};
        const taskDone = taskUnitsByMaterial[m.id] || new Set();
        const completed = new Set([...(progress.completed_units || []), ...taskDone]);
        const doneCount = progress.status === "done" ? units.length : units.filter(u=>completed.has(u.id)).length;
        const taskKinds = materialTaskKinds[m.id] || {{course:0, exercise:0, doneTasks:0, totalTasks:0}};
        subjects[subject].push({{
          id:m.id, name:m.name, kind:m.kind || "other", teacher:m.teacher || "", status:progress.status || "active",
          done:doneCount, total:units.length, units, completed, taskKinds, note:progress.note || m.notes || ""
        }});
      }}
      const kindLabel = kind => {{
        if (["book","handout"].includes(kind)) return "书籍 / 讲义";
        if (kind === "exercise-book") return "题册 / 习题";
        if (kind === "course") return "网课 / 课程";
        if (kind === "app") return "App / 词库";
        if (kind === "paper-set") return "真题 / 套卷";
        return "其他资料";
      }};
      const groupOrder = ["书籍 / 讲义","题册 / 习题","网课 / 课程","App / 词库","真题 / 套卷","其他资料"];
      const statusText = row => row.status === "done" ? "已完成" : (row.done ? "进行中" : "未完成");
      const statusPill = row => row.status === "done" ? "green" : (row.done ? "blue" : "");
      const chapterDots = row => row.units.length ? `<div class="chapter-strip">${{row.units.map((u,i)=>`<span class="chapter-dot ${{(row.status==="done" || row.completed.has(u.id))?"done":"pending"}}" data-label="${{i+1}}" title="${{esc(zh(u.title||u.id))}}"></span>`).join("")}}</div>` : `<p class="muted">该资料暂不按章节计数。</p>`;
      const resourceCard = row => `<div class="resource-row">
        <div class="resource-title">${{esc(zh(row.name))}}</div>
        <div class="resource-meta"><code>${{esc(row.id)}}</code><span>${{row.teacher?`主线：${{esc(zh(row.teacher))}}`:"资料进度"}}</span><span>${{row.done}}/${{row.total || row.taskKinds.totalTasks}} 章完成</span><span>任务 ${{row.taskKinds.doneTasks}}/${{row.taskKinds.totalTasks}}</span></div>
        <div class="bar"><i style="width:${{pct(row.done,row.total || row.taskKinds.totalTasks)}}%"></i></div>
        <div class="resource-status"><span class="pill ${{statusPill(row)}}">${{statusText(row)}}</span><span class="pill">${{Math.round(pct(row.done,row.total || row.taskKinds.totalTasks))}}%</span></div>
        ${{chapterDots(row)}}
      </div>`;
      return `<section id="subjects" class="section"><div class="subject-board">
        ${{Object.entries(subjects).map(([subject,rows])=>{{
          const done = rows.reduce((s,r)=>s+r.done,0);
          const total = rows.reduce((s,r)=>s+(r.total || r.taskKinds.totalTasks || 0),0);
          const groups = Object.groupBy ? Object.groupBy(rows, r=>kindLabel(r.kind)) : rows.reduce((acc,r)=>((acc[kindLabel(r.kind)]??=[]).push(r),acc),{{}});
          const visibleGroups = groupOrder.filter(g=>groups[g]?.length);
          return `<div class="card subject-card"><div class="subject-head"><div><h2>${{esc(zh(subject))}}</h2><div class="muted">该科目的资料构成、主线状态和章节完成度。</div></div><div class="subject-score"><div class="metric">${{Math.round(pct(done,total))}}%</div><div class="label">${{done}}/${{total}} 章完成</div><div class="bar"><i style="width:${{pct(done,total)}}%"></i></div></div></div>
            <div class="resource-groups">${{visibleGroups.map(g=>`<div class="resource-group ${{visibleGroups.length===1?'is-wide':''}}"><h3>${{esc(g)}} <span class="pill">${{groups[g].length}} 项</span></h3><div class="resource-list">${{groups[g].map(resourceCard).join("")}}</div></div>`).join("")}}</div>
          </div>`;
        }}).join("") || "<div class='card'><h2>科目进度</h2><p class='muted'>暂无课程、题册或资料。</p></div>"}}
      </div></section>`;
    }}
    function renderReviews() {{
      const rows = [...(DATA.reviews || [])]
        .sort((a,b)=>String(a.due).localeCompare(String(b.due)) || String(a.subject).localeCompare(String(b.subject)));
      const grouped = {{}};
      for (const row of rows) {{
        const sourceText = String(row.source || "");
        const key = [
          row.subject || "",
          row.knowledge_point || row.content || "",
          sourceText.includes("mistake:") ? sourceText.split(" ")[0] : sourceText,
          row.review_kind || (sourceText.includes("mistake:") ? "mistake" : "knowledge")
        ].join("||");
        grouped[key] ??= [];
        grouped[key].push(row);
      }}
      const items = Object.values(grouped).map(group => {{
        const ordered = [...group].sort((a,b)=>String(a.due).localeCompare(String(b.due)));
        const pending = ordered.filter(r => (r.status || "pending") !== "done");
        const next = pending[0] || ordered[ordered.length - 1];
        return {{
          subject: next.subject,
          knowledge_point: next.knowledge_point || next.content || "",
          content: next.content || "",
          source: next.source || "",
          prompt_items: next.prompt_items || [],
          acceptance: next.acceptance || "",
          review_kind: next.review_kind || (String(next.source || "").includes("mistake:") ? "mistake" : "knowledge"),
          next_due: pending.length ? (next.due || "未定日期") : "",
          status_text: pending.length ? `下次复习：${{next.due || "未定日期"}}` : "复习结束",
          intervals: ordered.map(r => r.interval).filter(v => v !== undefined && v !== null),
          total_rounds: ordered.length,
          done_rounds: ordered.length - pending.length,
        }};
      }}).sort((a,b)=> {{
        const aDone = a.status_text === "复习结束";
        const bDone = b.status_text === "复习结束";
        if (aDone !== bDone) return aDone ? 1 : -1;
        return String(a.next_due || "9999-99-99").localeCompare(String(b.next_due || "9999-99-99")) || String(a.subject).localeCompare(String(b.subject));
      }});
      const reviewCard = r => {{
        const prompts = (r.prompt_items || []).length
          ? `<div class="todo-detail">${{(r.prompt_items || []).map((q, idx)=>`<span>提问 ${{idx+1}}：${{esc(zh(q))}}</span>`).join("")}}</div>`
          : `<div class="todo-detail"><span class="muted">当前没有题目，按该知识点自行提问与回忆。</span></div>`;
        const sourceText = String(r.source || "");
        const isMistake = r.review_kind === "mistake" || sourceText.includes("mistake:");
        const kindText = isMistake ? "错题回炉" : "知识点复习";
        const acceptance = r.acceptance ? `<div class="todo-detail"><span>验收：${{esc(zh(r.acceptance))}}</span></div>` : "";
        const rounds = r.intervals?.length ? `轮次：${{r.done_rounds}}/${{r.total_rounds}}（${{r.intervals.join("/")}} 天）` : `轮次：${{r.done_rounds}}/${{r.total_rounds}}`;
        return `<div class="today-card">
          <b>${{esc(zh(r.subject))}} · ${{esc(zh(r.knowledge_point || r.content))}}</b>
          <span>${{esc(zh(r.status_text))}} · ${{kindText}}</span>
          <span>${{esc(rounds)}}</span>
          <span>${{esc(zh(sourceText || "未记录来源"))}}</span>
          ${{prompts}}
          ${{acceptance}}
        </div>`;
      }};
      return `<section id="reviews" class="section"><div class="grid">
        <div class="card">
          <h2>统一复习队列</h2>
          <p class="muted">这里按知识点合并显示复习和错题回炉。同一个知识点只显示一次，只看下一次复习时间；整组都完成后显示“复习结束”。</p>
          <p><span class="pill blue">知识点总数 ${{items.length}}</span><span class="pill green">错题回炉 ${{items.filter(r=>String(r.review_kind) === "mistake").length}}</span><span class="pill">知识点复习 ${{items.filter(r=>String(r.review_kind) !== "mistake").length}}</span></p>
        </div>
        ${{items.length ? `<div class="card"><h2>知识点列表 <span class="pill">${{items.length}} 项</span></h2><div class="today-list">${{items.map(reviewCard).join("")}}</div></div>` : `<div class="card"><h2>统一复习队列</h2><p class="muted">暂无复习项。没有错题就不会显示错题回炉；普通复习可直接用知识点 + 提问的方式新增。</p></div>`}}
      </div></section>`;
    }}
    function renderBlocks() {{
      return `<section id="blocks" class="section"><div class="grid two">
        <div class="card"><h2>关键前置任务</h2><table><tr><th>ID</th><th>任务</th><th>解锁数</th></tr>
        ${{(DATA.blocked.top_blockers||[]).map(b=>`<tr><td><code>${{esc(b.blocker.id)}}</code></td><td>${{taskName(b.blocker)}}</td><td>${{b.blocks}}</td></tr>`).join("")}}</table></div>
        <div class="card"><h2>被阻塞任务</h2><ul>${{(DATA.blocked.blocked_tasks||[]).slice(0,18).map(x=>taskLine(x.task)).join("")}}</ul></div>
      </div></section>`;
    }}
    function renderMaterials() {{
      const rows = DATA.materials || [];
      const auditItems = DATA.catalogAudit?.items || [];
      const summary = DATA.catalogAudit?.summary || {{}};
      const unitRows = (m) => (m.catalog_units||[]).map(u=>`<tr><td><code>${{esc(u.id||"")}}</code></td><td>${{esc(zh(u.title||""))}}</td><td>${{esc(zh(u.page_range||"待补充"))}}</td><td>${{esc(zh(u.lecture_range||"待补充"))}}</td><td>${{esc(zh(u.problem_range||"待补充"))}}</td><td>${{esc(u.source_note||u.obsidian_link||"")}}</td></tr>`).join("");
      return `<section id="materials" class="section"><div class="grid two">
        <div class="card"><h2>资料目录库</h2>${{rows.length?`<table><tr><th>ID</th><th>资料</th><th>类型</th><th>科目</th><th>目录</th><th>单元数</th></tr>${{rows.map(m=>`<tr><td><code>${{esc(m.id)}}</code></td><td>${{esc(zh(m.name))}}</td><td>${{esc(zh(m.kind))}}</td><td>${{esc(zh(m.subject))}}</td><td><span class="pill ${{catalogPillClass(m.catalog_status, true)}}">${{catalogStatusText(m.catalog_status, true, "已建目录")}}</span></td><td>${{(m.catalog_units||[]).length}}</td></tr>`).join("")}}</table>`:"<p class='muted'>暂无资料目录。先为每本书、题册、网课建立真实章节目录。</p>"}}</div>
        <div class="card"><h2>目录审计</h2><p class="muted">用于发现仍未绑定真实目录或未指定目录单元的任务。页码、讲次、题号是增强信息，不作为默认计划硬性要求。</p>
          <p>${{Object.entries(summary).map(([k,v])=>`<span class="pill ${{k==='ok'?'green':'red'}}">${{esc(zh(k))}}：${{v}}</span>`).join("") || "<span class='pill red'>未运行审计</span>"}}</p>
          ${{auditItems.length?`<table><tr><th>任务</th><th>资料</th><th>范围</th><th>问题</th></tr>${{auditItems.slice(0,40).map(x=>`<tr><td><code>${{esc(x.task_id)}}</code> ${{esc(zh(x.subject))}}</td><td>${{esc(zh(x.material))}}</td><td>${{esc(zh(x.scope))}}</td><td><span class="pill red">${{esc(zh(x.issue || x.severity))}}</span></td></tr>`).join("")}}</table>`:"<p class='muted'>所有任务都已通过目录审计。</p>"}}
        </div>
      </div>
      <div class="grid" style="margin-top:16px">
        ${{rows.map(m=>`<div class="card"><h2>${{esc(zh(m.name))}} <span class="pill">${{esc(m.catalog_precision || "目录")}}</span></h2>
          <p class="muted">来源：${{esc(m.catalog_source || m.source || "未记录")}}</p>
          ${{(m.catalog_units||[]).length?`<table><tr><th>单元</th><th>真实章节</th><th>页码</th><th>讲次</th><th>题号</th><th>Obsidian 笔记</th></tr>${{unitRows(m)}}</table>`:"<p class='muted'>暂无目录单元。</p>"}}
        </div>`).join("")}}
      </div></section>`;
    }}
    function render408() {{
      const model = DATA.model408.model || {{}};
      return `<section id="model408" class="section"><div class="grid">
        ${{Object.entries(model).map(([subject,body])=>`<div class="card"><h2>${{esc(zh(subject))}}</h2><table>
          <tr><th>专题</th><th>权重</th><th>任务</th><th>套卷弱点</th><th>风险</th></tr>
          ${{Object.entries(body.topics).map(([topic,row])=>`<tr><td>${{esc(zh(topic))}}</td><td>${{row.weight}}</td><td>${{row.done}} 已完成 / ${{row.pending}} 待完成</td><td>${{row.paper_weak_hits}}</td><td><span class="pill ${{row.risk==='yellow'?'red':'green'}}">${{zh(row.risk)}}</span></td></tr>`).join("")}}
        </table></div>`).join("")}}
      </div></section>`;
    }}
    function renderDiagnostics() {{
      const blockedCount = DATA.blocked?.blocked_count || 0;
      const model = DATA.model408?.model || {{}};
      const has408 = Object.keys(model).length > 0 && Object.values(model).some(body => Object.values(body.topics || {{}}).some(row => row.task_count || row.module_count || row.paper_weak_hits));
      return `<section id="diagnostics" class="section"><div class="grid two">
        <div class="card"><h2>阻塞诊断</h2><p class="muted">作用：只在任务有前置依赖时有用，例如“先完成 660 二重积分，再进入高数强化篇”。它会找出哪个上游任务卡住了最多下游任务。普通背书、刷题计划如果没有依赖，可以忽略。</p>
          <p><span class="pill ${{blockedCount?'red':'green'}}">当前阻塞任务：${{blockedCount}}</span></p>
          ${{blockedCount?`<table><tr><th>ID</th><th>任务</th><th>解锁数</th></tr>${{(DATA.blocked.top_blockers||[]).map(b=>`<tr><td><code>${{esc(b.blocker.id)}}</code></td><td>${{taskName(b.blocker)}}</td><td>${{b.blocks}}</td></tr>`).join("")}}</table>`:`<p class="muted">当前没有明显阻塞链。</p>`}}
        </div>
        <div class="card"><h2>408 专项模型</h2><p class="muted">作用：只服务计算机考研 408，把数据结构、计组、操作系统、计网拆成专题风险。非 408 考试可以忽略；如果你的考试不是 408，这一块不会影响周计划。</p>
          ${{has408?`<p><span class="pill green">检测到 408 任务，已启用专项分析</span></p>${{Object.entries(model).map(([subject,body])=>`<h3>${{esc(zh(subject))}}</h3><table><tr><th>专题</th><th>任务</th><th>风险</th></tr>${{Object.entries(body.topics).filter(([topic,row])=>row.task_count||row.module_count||row.paper_weak_hits).map(([topic,row])=>`<tr><td>${{esc(zh(topic))}}</td><td>${{row.done}} 已完成 / ${{row.pending}} 待完成</td><td><span class="pill ${{row.risk==='yellow'?'red':'green'}}">${{zh(row.risk)}}</span></td></tr>`).join("")}}</table>`).join("")}}`:`<p><span class="pill">未检测到需要展示的 408 专项任务</span></p>`}}
        </div>
      </div></section>`;
    }}
    function renderMistakes() {{
      return `<section id="mistakes" class="section"><div class="grid two">
        <div class="card"><h2>错题包</h2>${{DATA.mistakes.length?`<ul>${{DATA.mistakes.map(m=>`<li>${{esc(zh(m.subject))}} · ${{esc(zh(m.knowledge))}} · ${{esc(zh((m.error_causes||[]).join("、")))}}</li>`).join("")}}</ul>`:"<p class='muted'>暂无错题记录</p>"}}</div>
        <div class="card"><h2>真题/套卷</h2>${{DATA.papers.length?`<ul>${{DATA.papers.map(p=>`<li>${{esc(zh(p.subject))}} · ${{esc(zh(p.name))}} · ${{esc(p.score)}}/${{esc(p.total_score)}}</li>`).join("")}}</ul>`:"<p class='muted'>暂无真题/套卷记录</p>"}}</div>
      </div></section>`;
    }}
    function renderDeploy() {{
      return `<section id="deploy" class="section"><div class="grid deploy">
        <div class="card"><h2>没有域名：本机运行</h2><p>推荐使用一键启动脚本。</p><div class="command">python "${{esc(DATA.scripts.launcher)}}" --profile "${{esc(PROFILE)}}" --open</div><p>也可以手动启动页面服务和本地档案写入服务。</p><div class="command">cd "${{esc(DATA.outDir)}}"<br>python -m http.server ${{new URL(DATA.staticUrl).port || "8787"}}<br>${{esc(DATA.staticUrl)}}<br><br>python "${{esc(DATA.scripts.server)}}" --profile "${{esc(PROFILE)}}" --out-dir "${{esc(DATA.outDir)}}"</div></div>
        <div class="card"><h2>有域名：挂到域名下</h2><p>把当前输出目录作为静态站点部署到 Nginx、Cloudflare Pages、Vercel、Netlify 或服务器任意 Web 根目录。</p><div class="command">${{esc(DATA.outDir)}}<br>&nbsp;&nbsp;index.html</div><p class="muted">域名页面可以展示看板；直接写入本地档案仍需要你电脑上的本地写入服务。若域名页要写入本机档案，需要启动服务前设置 STUDY_DASHBOARD_ORIGINS 为你的域名来源。不开本地服务时，使用底部备用导出。</p></div>
      </div></section>`;
    }}
    app.innerHTML = renderOverview()+renderWeek()+renderSubjects()+renderReviews()+renderMaterials()+renderMistakes()+renderDiagnostics()+renderDeploy();
    function setItemSyncState(el, text, state="warn") {{
      const node = el?.querySelector("[data-sync-state]");
      if (!node) return;
      node.textContent = text;
      node.className = `sync-state ${{state}}`;
    }}
    function updateTodoProgress() {{
      document.querySelectorAll("[data-todo-group]").forEach(group => {{
        const checks = [...group.querySelectorAll("[data-todo-check]")];
        const done = checks.filter(c => c.checked).length;
        const badge = group.querySelector("[data-group-count]");
        if (badge) badge.textContent = `${{done}}/${{checks.length}}`;
      }});
      document.querySelectorAll(".day").forEach(day => {{
        const checks = [...day.querySelectorAll("[data-todo-check]")];
        const done = checks.filter(c => c.checked).length;
        const progress = day.querySelector("[data-day-progress]");
        if (progress) progress.textContent = `${{done}}/${{checks.length}}`;
      }});
      syncOverviewDonut();
      syncOverviewSubjectProgress();
    }}
    function hydrateTodoState() {{
      document.querySelectorAll("[data-todo-check]").forEach(check => {{
        const item = check.closest("[data-todo-item]");
        const status = item?.dataset.currentStatus || "";
        const local = localStorage.getItem(check.dataset.key);
        check.checked = status ? status === "done" : local === "1";
        item?.classList.toggle("done", check.checked);
        if (status === "done") setItemSyncState(item, "本地档案：已完成", "ok");
        else if (status === "missed") setItemSyncState(item, "本地档案：已标记未完成", "warn");
        else setItemSyncState(item, "本地档案：待同步", "warn");
      }});
      updateTodoProgress();
    }}
    async function syncTodoCheck(check) {{
      const item = check.closest("[data-todo-item]");
      let raw = {{}};
      try {{ raw = JSON.parse(item?.dataset.raw || "{{}}"); }} catch {{}}
      const payload = {{
        profile: PROFILE,
        key: item?.dataset.key,
        task_id: raw.id || null,
        date: item?.dataset.date,
        layer: item?.dataset.layer,
        layer_name: item?.dataset.layerName,
        title: item?.dataset.title,
        checked: check.checked,
        status: check.checked ? "done" : "pending",
        note: check.checked ? "HTML 看板勾选同步" : "HTML 看板取消勾选同步",
        raw_task: raw.task || raw.text || raw.slice || raw.scope || raw.chapter_or_scope || raw.title_or_resource || raw.content || null
      }};
      setItemSyncState(item, "正在写入本地档案...", "warn");
      const res = await fetch(`${{API_BASE}}/api/log-task`, {{
        method:"POST",
        headers:{{"Content-Type":"application/json"}},
        body:JSON.stringify(payload)
      }});
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "写入失败");
      item.dataset.currentStatus = check.checked ? "done" : "missed";
      setItemSyncState(item, check.checked ? "已同步到本地档案" : "已同步为未完成", check.checked ? "ok" : "warn");
    }}
    app.addEventListener("change", async e => {{
      if (!e.target.matches("[data-todo-check]")) return;
      const check = e.target;
      const item = check.closest("[data-todo-item]");
      localStorage.setItem(check.dataset.key, check.checked ? "1" : "0");
      item?.classList.toggle("done", check.checked);
      updateTodoProgress();
      try {{
        await syncTodoCheck(check);
      }} catch (err) {{
        setItemSyncState(item, `同步失败：${{err.message || err}}。请确认本地服务 8790 已启动。`, "bad");
      }}
    }});
    async function checkApi() {{
      const node = document.querySelector("[data-api-status]");
      if (!node) return;
      node.textContent = "本地写入服务：检测中";
      node.className = "pill blue";
      try {{
        const res = await fetch(`${{API_BASE}}/api/health`);
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || "不可用");
        node.textContent = "本地写入服务：已连接，可直接写入档案";
        node.className = "pill green";
      }} catch {{
        node.textContent = "本地写入服务：未连接，勾选只能暂存在浏览器";
        node.className = "pill red";
      }}
    }}
    function buildWeekExport() {{
      const items = [...document.querySelectorAll("[data-todo-item]")].map(el => {{
        const check = el.querySelector("[data-todo-check]");
        let raw = {{}};
        try {{ raw = JSON.parse(el.dataset.raw || "{{}}"); }} catch {{}}
        return {{
          key: el.dataset.key,
          date: el.dataset.date,
          layer: el.dataset.layer,
          layer_name: el.dataset.layerName,
          title: el.dataset.title,
          meta: el.dataset.meta,
          checked: Boolean(check?.checked),
          status: check?.checked ? "done" : "pending",
          task_id: raw.id || null,
          task_type: raw.type || null,
          subject: raw.subject || null,
          raw_task: raw.task || raw.text || raw.slice || raw.scope || raw.chapter_or_scope || raw.title_or_resource || raw.content || null,
          priority: raw.priority ?? null
        }};
      }});
      const byDate = {{}};
      for (const item of items) {{
        byDate[item.date] ??= {{ total:0, done:0, pending:0, done_items:[], pending_items:[] }};
        byDate[item.date].total += 1;
        if (item.checked) {{
          byDate[item.date].done += 1;
          byDate[item.date].done_items.push(item);
        }} else {{
          byDate[item.date].pending += 1;
          byDate[item.date].pending_items.push(item);
        }}
      }}
      const total = items.length;
      const done = items.filter(x=>x.checked).length;
      const pending = total - done;
      const completion_rate = total ? Math.round(done / total * 1000) / 10 : 0;
      return {{
        type: "study_planner_week_export",
        profile: PROFILE,
        week_start: DATA.currentWeek.start || null,
        generated_at: new Date().toISOString(),
        summary: {{ total, done, pending, completion_rate }},
        days: Object.fromEntries(Object.entries(byDate).map(([date,row]) => [date, {{
          total: row.total,
          done: row.done,
          pending: row.pending,
          completion_rate: row.total ? Math.round(row.done / row.total * 1000) / 10 : 0,
          done_items: row.done_items,
          pending_items: row.pending_items
        }}])),
        items
      }};
    }}
    function weekExportText() {{
      const data = buildWeekExport();
      const lines = [
        `请导入以下本周完成情况，并据此更新 ${{PROFILE}} 学习档案、生成周复盘和下一周滚动计划。`,
        "",
        `本周：${{data.week_start || "未标记"}}`,
        `总完成率：${{data.summary.done}}/${{data.summary.total}}（${{data.summary.completion_rate}}%）`,
        "",
        "每日概览："
      ];
      for (const [date,row] of Object.entries(data.days)) {{
        lines.push(`- ${{date}}：${{row.done}}/${{row.total}}（${{row.completion_rate}}%）`);
      }}
      lines.push("", "已完成任务：");
      const doneItems = data.items.filter(x=>x.checked);
      lines.push(...(doneItems.length ? doneItems.map(x=>`- [${{x.date}}] ${{x.layer_name}} · ${{x.task_id || "无ID"}} · ${{x.title}}`) : ["- 无"]));
      lines.push("", "未完成任务：");
      const pendingItems = data.items.filter(x=>!x.checked);
      lines.push(...(pendingItems.length ? pendingItems.map(x=>`- [${{x.date}}] ${{x.layer_name}} · ${{x.task_id || "无ID"}} · ${{x.title}}`) : ["- 无"]));
      lines.push("", "结构化数据：", "```json", JSON.stringify(data, null, 2), "```");
      return lines.join("\\n");
    }}
    function setExportStatus(text) {{
      const status = document.querySelector("[data-export-status]");
      if (status) status.textContent = text;
    }}
    app.addEventListener("click", async e => {{
      if (e.target.matches("[data-export-week]")) {{
        const box = document.querySelector("[data-export-box]");
        if (box) box.value = weekExportText();
        setExportStatus("已生成，可复制给 agent。");
      }}
      if (e.target.matches("[data-copy-export]")) {{
        const box = document.querySelector("[data-export-box]");
        if (!box?.value) box.value = weekExportText();
        box.select();
        try {{
          await navigator.clipboard.writeText(box.value);
          setExportStatus("已复制到剪贴板。");
        }} catch {{
          document.execCommand("copy");
          setExportStatus("已尝试复制；如失败可手动复制文本框内容。");
        }}
      }}
      if (e.target.matches("[data-download-export]")) {{
        const data = buildWeekExport();
        const blob = new Blob([JSON.stringify(data, null, 2)], {{ type:"application/json;charset=utf-8" }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${{PROFILE}}-week-${{data.week_start || "current"}}-完成情况.json`;
        a.click();
        URL.revokeObjectURL(url);
        setExportStatus("JSON 已下载。");
      }}
      if (e.target.matches("[data-check-api]")) {{
        checkApi();
      }}
    }});
    hydrateTodoState();
    checkApi();
    renderTopCountdown();
    setInterval(renderTopCountdown, 1000);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    main()
