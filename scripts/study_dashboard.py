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
  <title>学习任务看板</title>
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
      padding:28px clamp(18px,4vw,56px) 18px;
      border-bottom:2px solid var(--black);
      background:rgba(247,244,237,.92);
      position:sticky; top:0; z-index:10; backdrop-filter:blur(8px);
    }}
    .topline {{ display:flex; justify-content:space-between; gap:18px; align-items:flex-end; flex-wrap:wrap; }}
    h1 {{ margin:0; font-size:clamp(28px,4.5vw,54px); line-height:.95; font-weight:900; }}
    .stamp {{ border:2px solid var(--black); padding:8px 12px; font-weight:800; background:#efe3c8; }}
    .countdown {{ text-align:right; min-width:260px; }}
    .countdown-label {{ color:var(--muted); font-size:12px; font-weight:800; }}
    .countdown-seconds {{ font-size:24px; line-height:1; font-weight:900; font-variant-numeric:tabular-nums; }}
    .countdown-sub {{ color:var(--muted); font-size:12px; margin-top:4px; }}
    nav {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:18px; }}
    nav button {{
      border:1px solid var(--black); background:var(--panel); padding:9px 12px; cursor:pointer;
      font-weight:800; border-radius:0; min-height:38px;
    }}
    nav button.active {{ background:var(--black); color:var(--paper); }}
    main {{ padding:24px clamp(14px,3vw,44px) 48px; max-width:1500px; margin:auto; }}
    .grid {{ display:grid; gap:14px; }}
    .stats {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .two {{ grid-template-columns:1.2fr .8fr; }}
    .three {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .card {{
      background:var(--panel); border:2px solid var(--black); padding:16px; box-shadow:5px 5px 0 var(--black);
      min-width:0;
    }}
    .card h2, .card h3 {{ margin:0 0 12px; line-height:1.1; }}
    .metric {{ font-size:32px; font-weight:900; line-height:1; }}
    .label {{ color:var(--muted); font-size:13px; margin-top:6px; }}
    .bar {{ height:12px; border:1px solid var(--black); background:#eee2cf; overflow:hidden; margin:8px 0; }}
    .bar > i {{ display:block; height:100%; background:var(--green); }}
    .pill {{ display:inline-flex; align-items:center; border:1px solid var(--black); padding:4px 7px; margin:2px; font-size:12px; font-weight:800; background:#efe3c8; }}
    .pill.red {{ background:#ecd0c8; }} .pill.blue {{ background:#d4e2ef; }} .pill.green {{ background:#d6e6d6; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px 6px; text-align:left; vertical-align:top; }}
    th {{ color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .section {{ display:none; }} .section.active {{ display:block; }}
    .day {{ border-left:6px solid var(--black); margin-bottom:12px; }}
    .day-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }}
    .day-progress {{ min-width:92px; text-align:right; font-weight:900; }}
    .todo-groups {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .todo-group {{ border-top:2px solid var(--black); padding-top:10px; min-width:0; }}
    .todo-group h3 {{ display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:15px; }}
    .todo-list {{ list-style:none; margin:0; padding:0; display:grid; gap:8px; }}
    .todo-item {{ margin:0; }}
    .todo-item label {{
      display:grid; grid-template-columns:24px 1fr; gap:9px; align-items:start;
      border:1px solid var(--line); background:#fbf5e8; padding:9px; cursor:pointer; min-height:44px;
    }}
    .todo-item input {{ width:18px; height:18px; margin:1px 0 0; accent-color:var(--green); cursor:pointer; }}
    .todo-title {{ font-weight:800; line-height:1.35; overflow-wrap:anywhere; }}
    .todo-meta {{ color:var(--muted); font-size:12px; margin-top:3px; }}
    .todo-detail {{ display:grid; gap:2px; color:var(--muted); font-size:12px; margin-top:6px; line-height:1.45; }}
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
    @media (max-width:1100px) {{ .todo-groups {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media (max-width:900px) {{ .stats,.two,.three,.deploy,.calendar {{ grid-template-columns:1fr; }} header {{ position:static; }} }}
    @media (max-width:640px) {{ .todo-groups {{ grid-template-columns:1fr; }} .day-progress {{ text-align:left; }} }}
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>学习任务看板</h1>
        <div class="muted">任务清单优先 · 真实目录驱动 · 复习回炉 · 进度追踪</div>
      </div>
      <div class="stamp" id="stamp"></div>
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
      ["materials","资料目录"],["mistakes","错题/真题"],["mistakeCalendar","错题回炉"],["diagnostics","高级诊断"],["deploy","部署"]
    ];
    const app = document.getElementById("app");
    const stamp = document.getElementById("stamp");
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
      const weekStart = DATA.currentWeek?.start;
      const weekDays = DATA.currentWeek?.days || 0;
      if (weekStart && weekDays) {{
        const end = new Date(weekStart + "T00:00:00");
        end.setDate(end.getDate() + weekDays - 1);
        end.setHours(23, 59, 59, 999);
        return {{ date:end, label:"本周期剩余", target:`${{ymd(end)}} 23:59:59` }};
      }}
      if (DATA.goals?.deadline) {{
        const end = new Date(DATA.goals.deadline + "T23:59:59");
        return {{ date:end, label:"目标截止剩余", target:`${{DATA.goals.deadline}} 23:59:59` }};
      }}
      return null;
    }}
    function renderTopCountdown() {{
      const target = getCountdownTarget();
      if (!target) {{
        stamp.innerHTML = `<div class="countdown"><div class="countdown-label">档案 ${{esc(PROFILE)}}</div><div class="countdown-sub">尚未设置周期或截止日期</div></div>`;
        return;
      }}
      const ms = Math.max(target.date - new Date(), 0);
      const totalSeconds = Math.floor(ms / 1000);
      const days = Math.floor(totalSeconds / 86400);
      const hours = Math.floor((totalSeconds % 86400) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      stamp.innerHTML = `<div class="countdown"><div class="countdown-label">${{target.label}} · 档案 ${{esc(PROFILE)}}</div><div class="countdown-seconds">${{days}}天 ${{pad2(hours)}}:${{pad2(minutes)}}:${{pad2(seconds)}}</div><div class="countdown-sub">目标 ${{esc(target.target)}} · 生成 ${{esc(DATA.generated)}}</div></div>`;
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
      "Instruction system tail":"指令系统尾巴", "Processes and threads":"进程与线程",
      "Scheduling and PV":"调度与 PV", "Architecture and layering":"体系结构与分层",
      "Long sentences":"长难句", "Framework warm-up":"框架预热", "Sorting":"排序",
      "CPU":"CPU", "Quadratic forms":"二次型", "Advanced math strengthening phase":"高数强化阶段"
    }};
    const phraseMap = [
      ["repair exercises after finishing the course section","补齐课后习题并修补听课后的漏洞"],
      ["close double-integral foundation tail","收口二重积分基础尾巴"],
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
      ["start OS from process/thread basics","从进程与线程基础启动"],
      ["clear remaining instruction-system exercises","清掉指令系统习题尾巴"],
      ["entry route for scheduling and PV problems","调度与 PV 问题入门"],
      ["eigenvalues and eigenvectors","特征值与特征向量"],
      ["instruction system tail","指令系统尾巴"],
      ["process threads scheduling PV","进程线程、调度与 PV"],
      ["sorting","排序"],
      ["start diagonalization after eigenvalue exercise repair","特征值习题修补后启动矩阵对角化"],
      ["advanced math launch after double-integral close","高数 660 启动"],
      ["second pass vocabulary","词汇二刷"],
      ["start central processor unit chapter","启动中央处理器章节"],
      ["matrix diagonalization","矩阵对角化"],
      ["architecture and layering","体系结构与分层模型"],
      ["start CN from architecture and layered model","从体系结构与分层模型启动计网"],
      ["start long-sentence foundation","启动长难句基础"],
      ["finish first-round linear algebra tail","线代一轮收尾"],
      ["foundation reading launch","基础阅读启动"],
      ["data structure weak-topic selective choices","数据结构弱点专项选择题"],
      ["start strengthening guide after 660 launch","660 启动后进入高数强化讲义"],
      ["double-integral tail","二重积分收尾"],
      ["warm-up after framework starts","框架启动后的预热"],
      ["finish remaining problems, correct mistakes, summarize region-choice patterns","完成剩余题目，订正错题，总结积分区域选择模式"],
      ["correct all wrong questions and mark concept/calculation/method causes","订正全部错题，并标记概念、计算、方法错因"],
      ["repair post-course gap, correct all mistakes, summarize conditions","修补课后缺口，订正全部错题，总结适用条件"],
      ["write diagonalization condition checklist and correct mistakes","写出对角化条件清单并订正错题"],
      ["correct all wrong choices and compare sorting algorithms","订正全部错选题，并比较排序算法"],
      ["start selective practice after Wangdao sorting, tag weak topics","王道排序后启动专项选择题，并标记薄弱点"],
      ["clear remaining tail and correct mistakes","清掉剩余尾巴并订正错题"],
      ["match CPU framework with questions and correct mistakes","用题目校准 CPU 框架并订正错题"],
      ["build OS entry confidence and tag conceptual gaps","建立 OS 入门信心，并标记概念缺口"],
      ["start CN from zero and correct conceptual questions","从零启动计网，并订正概念题"],
      ["finish daily push and mark stubborn words","完成每日推词，并标记顽固词"],
      ["finish one passage, locate wrong-answer evidence, extract 10 words and 3 long sentences","完成 1 篇阅读，定位错因证据，摘出 10 个单词和 3 个长难句"],
      ["record confusing knowledge points; low priority before formal start","记录混淆知识点；正式启动前低优先级处理"],
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
      ["Close first-round gaps and start blank subjects.","收口一轮漏洞，并启动空白科目"],
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
    const layerText = {{ main:"主线任务", review:"复习任务", extra:"加餐任务", minimum:"保底任务" }};
    function todoTitle(item) {{
      if (typeof item === "string") return zh(item);
      const action = item.task || item.slice || item.scope || item.chapter_or_scope || item.content || item.id;
      return `${{zh(item.subject)}}：${{zh(action)}}`;
    }}
    function todoItem(date, layer, item, index) {{
      const key = todoKey(date, layer, item, index);
      const title = todoTitle(item);
      const meta = typeof item === "string" ? "保底版本" : `${{zh(item.type)}}${{item.id ? " · " + item.id : ""}}${{item.priority ? " · 优先级 " + item.priority : ""}}`;
      const details = typeof item === "string" ? "" : [
        item.material ? `资料：${{zh(item.material)}}` : "",
        item.material_id ? `目录资料：${{materialLabel(item.material_id)}}` : "目录资料：未绑定真实目录",
        item.catalog_units?.length ? `目录单元：${{item.catalog_units.map(unit=>catalogUnitLabel(item.material_id, unit)).join("、")}}` : "目录单元：未指定",
        item.scope ? `范围：${{zh(item.scope)}}` : "",
        item.precise_range ? `精确范围：${{zh(item.precise_range)}}` : "",
        item.page_range ? `页码：${{zh(item.page_range)}}` : "",
        item.lecture_range ? `讲次：${{zh(item.lecture_range)}}` : "",
        item.problem_range ? `题号：${{zh(item.problem_range)}}` : "",
        item.quantity ? `数量：${{zh(item.quantity)}}` : "",
        item.acceptance || item.output_or_acceptance ? `验收：${{zh(item.acceptance || item.output_or_acceptance)}}` : ""
      ].filter(Boolean).map(line=>`<span>${{esc(line)}}</span>`).join("");
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
      const list = items && items.length ? items.map((item,index)=>todoItem(date, layer, item, index)).join("") : `<li class="muted">无</li>`;
      return `<div class="todo-group" data-todo-group><h3>${{title}} <span class="pill" data-group-count>0/0</span></h3><ul class="todo-list">${{list}}</ul></div>`;
    }}
    function metric(label,value,sub) {{ return `<div class="card"><div class="metric">${{esc(zh(value))}}</div><div class="label">${{label}}</div>${{sub?`<div class="muted">${{esc(zh(sub))}}</div>`:""}}</div>`; }}
    function renderOverview() {{
      const inv = DATA.inventory.inventory || {{}};
      const pending = Object.values(inv).reduce((a,b)=>a+(b.pending||0),0);
      const done = Object.values(inv).reduce((a,b)=>a+(b.done||0),0);
      const reviews = Object.values(DATA.inventory.pending_reviews || {{}}).reduce((a,b)=>a+b,0);
      const weekStart = DATA.currentWeek.start;
      const weekDays = DATA.currentWeek.days || 0;
      const weekEndDate = weekStart && weekDays ? new Date(new Date(weekStart + "T00:00:00").getTime() + (weekDays - 1) * 86400000) : null;
      const weekEnd = weekEndDate ? ymd(weekEndDate) : "未生成";
      const today = new Date(DATA.generated + "T00:00:00");
      const cycleDaysLeft = weekEndDate ? Math.max(Math.ceil((weekEndDate - today) / 86400000), 0) : 0;
      const countdown = getCountdownTarget();
      const secondsLeft = countdown ? Math.max(Math.floor((countdown.date - new Date()) / 1000), 0) : 0;
      return `<section id="overview" class="section active">
        <div class="grid stats">
          ${{metric("阶段", DATA.phase.phase, `${{DATA.phase.days_left}} 天到暂定截止日`)}}
          ${{metric("剩余秒数", secondsLeft.toLocaleString(), countdown ? countdown.target : `${{weekStart || "未生成"}} 至 ${{weekEnd}}`)}}
          ${{metric("总任务", pending+done, `${{done}} 已完成 · ${{pending}} 待完成`)}}
          ${{metric("课程占比", DATA.courseRatio.course_ratio_percent+"%", `上限 ${{DATA.courseRatio.course_cap_percent}}% · ${{zh(DATA.courseRatio.status)}}`)}}
        </div>
        <div class="grid two" style="margin-top:16px">
          <div class="card"><h2>当前规则</h2>${{DATA.phase.rules.map(r=>`<span class="pill green">${{esc(zh(r))}}</span>`).join("")}}</div>
          <div class="card"><h2>下一优先解锁</h2><p>${{esc(zh(DATA.blocked.suggestion))}}</p></div>
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
      return `<section id="week" class="section"><div class="grid">
        ${{days.map(d=>`<div class="card day">
          <div class="day-head"><h2>${{d.date}}</h2><div class="day-progress" data-day-progress>0/0</div></div>
          <div class="todo-groups">
            ${{todoGroup("主线任务", d.date, "main", d.main_tasks || [])}}
            ${{todoGroup("复习任务", d.date, "review", d.review_tasks || [])}}
            ${{todoGroup("加餐任务", d.date, "extra", d.optional_extra || [])}}
            ${{todoGroup("保底任务", d.date, "minimum", d.minimum_version || [])}}
          </div>
        </div>`).join("")}}
      </div>${{exportPanel}}</section>`;
    }}
    function renderSubjects() {{
      const tasks = [...(DATA.courses||[]), ...(DATA.exercises||[])];
      const subjects = {{}};
      for (const task of tasks) {{
        const subject = task.subject || "未分类";
        const materialName = task.title || task.resource || task.source || "未命名资料";
        const key = task.material_id || materialName;
        subjects[subject] ??= {{}};
        subjects[subject][key] ??= {{
          name: materialName,
          material_id: task.material_id || "",
          catalog_status: task.material_id ? (materialMap[task.material_id]?.catalog_status || "missing") : "missing",
          total:0,
          done:0,
          pending:0,
          course:0,
          exercise:0,
          chapter_bound:0
        }};
        const row = subjects[subject][key];
        row.total += 1;
        if (task.status === "done") row.done += 1; else row.pending += 1;
        if (task.type === "course") row.course += 1;
        if (task.type === "exercise") row.exercise += 1;
        if (task.catalog_units?.length || task.chapter || task.scope) row.chapter_bound += 1;
      }}
      return `<section id="subjects" class="section"><div class="grid">
        ${{Object.entries(subjects).map(([subject,materials])=>`<div class="card"><h2>${{esc(zh(subject))}}</h2><table>
          <tr><th>资料/题册/网课</th><th>完成率</th><th>任务</th><th>构成</th><th>目录</th><th>章节绑定</th></tr>
          ${{Object.values(materials).map(row=>`<tr><td>${{row.material_id?`<code>${{esc(row.material_id)}}</code> `:""}}${{esc(zh(row.name))}}</td><td><div class="bar"><i style="width:${{pct(row.done,row.total)}}%"></i></div><b>${{pct(row.done,row.total)}}%</b></td><td>${{row.done}} 已完成 / ${{row.total}} 总数</td><td><span class="pill blue">课程 ${{row.course}}</span><span class="pill green">习题 ${{row.exercise}}</span></td><td><span class="pill ${{catalogPillClass(row.catalog_status, !!row.material_id)}}">${{catalogStatusText(row.catalog_status, !!row.material_id)}}</span></td><td>${{row.chapter_bound}}/${{row.total}}</td></tr>`).join("")}}
        </table></div>`).join("") || "<div class='card'><h2>科目进度</h2><p class='muted'>暂无课程或习题任务。</p></div>"}}
      </div></section>`;
    }}
    function renderReviews() {{
      const due = [...DATA.reviews].sort((a,b)=>String(a.due).localeCompare(String(b.due))).slice(0,40);
      return `<section id="reviews" class="section"><div class="card"><h2>复习队列</h2><table>
        <tr><th>日期</th><th>科目</th><th>内容</th><th>间隔</th></tr>
        ${{due.map(r=>`<tr><td>${{esc(r.due)}}</td><td>${{esc(zh(r.subject))}}</td><td>${{esc(zh(r.content))}}</td><td>${{esc(r.interval)}} 天</td></tr>`).join("")}}
      </table></div></section>`;
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
    function renderMistakeCalendar() {{
      const rows = DATA.reviews
        .filter(r => String(r.source || "").includes("mistake:"))
        .sort((a,b)=>String(a.due).localeCompare(String(b.due)) || String(a.subject).localeCompare(String(b.subject)));
      const groups = {{}};
      for (const row of rows) {{
        groups[row.due || "未定日期"] ??= [];
        groups[row.due || "未定日期"].push(row);
      }}
      const body = rows.length ? `<div class="calendar">${{Object.entries(groups).map(([day,items])=>`<div class="calendar-day">
        <h3>${{esc(day)}} <span class="pill">${{items.length}} 项</span></h3>
        <ul>${{items.map(r=>`<li>${{esc(zh(r.subject))}}：${{esc(zh(r.content))}} <span class="muted">· 间隔 ${{esc(r.interval)}} 天 · ${{esc(zh(r.status))}}</span></li>`).join("")}}</ul>
      </div>`).join("")}}</div>` : `<p class="muted">暂无错题回炉任务；添加错题后，会自动进入当天、1 天、3 天、7 天、14 天、30 天复习队列。</p>`;
      return `<section id="mistakeCalendar" class="section">
        <div class="card"><h2>错题回炉日历</h2><p class="muted">只展示来源标记为 <code>mistake:</code> 的复习项，用来追踪错题的二刷、三刷和长期回炉。</p>${{body}}</div>
      </section>`;
    }}
    function renderDeploy() {{
      return `<section id="deploy" class="section"><div class="grid deploy">
        <div class="card"><h2>没有域名：本机运行</h2><p>推荐使用一键启动脚本。</p><div class="command">python "${{esc(DATA.scripts.launcher)}}" --profile "${{esc(PROFILE)}}" --open</div><p>也可以手动启动页面服务和本地档案写入服务。</p><div class="command">cd "${{esc(DATA.outDir)}}"<br>python -m http.server ${{new URL(DATA.staticUrl).port || "8787"}}<br>${{esc(DATA.staticUrl)}}<br><br>python "${{esc(DATA.scripts.server)}}" --profile "${{esc(PROFILE)}}" --out-dir "${{esc(DATA.outDir)}}"</div></div>
        <div class="card"><h2>有域名：挂到域名下</h2><p>把当前输出目录作为静态站点部署到 Nginx、Cloudflare Pages、Vercel、Netlify 或服务器任意 Web 根目录。</p><div class="command">${{esc(DATA.outDir)}}<br>&nbsp;&nbsp;index.html</div><p class="muted">域名页面可以展示看板；直接写入本地档案仍需要你电脑上的本地写入服务。若域名页要写入本机档案，需要启动服务前设置 STUDY_DASHBOARD_ORIGINS 为你的域名来源。不开本地服务时，使用底部备用导出。</p></div>
      </div></section>`;
    }}
    app.innerHTML = renderOverview()+renderWeek()+renderSubjects()+renderReviews()+renderMaterials()+renderMistakes()+renderMistakeCalendar()+renderDiagnostics()+renderDeploy();
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
