# study-planner

`study-planner` 是一个面向考试、考证、考研和长期自学的 Codex skill。它把学习系统拆成可执行任务、复习队列、错题回炉、周计划滚动、进度预测和 HTML 看板，目标是让 agent 不只会“写计划”，还能持续维护本地学习档案。

适合场景：

- 考研、考公、考证、期末复习、语言学习、编程学习
- 需要安排网课、教材、讲义、习题册、真题和套卷
- 需要每日待办、本周计划、复盘、提醒、进度追踪
- 需要控制“看课太多、做题太少”的风险
- 需要本地 HTML 看板和可勾选任务清单

## 核心能力

### 1. 学习档案

档案保存在本地 JSON：

```text
~/.codex/study-planner/profiles/<profile>/
```

包含：

- `goals.json`：目标、截止日期、科目、权重
- `courses.json`：网课/教材任务
- `exercises.json`：习题册/题库任务
- `review_queue.json`：复习队列
- `daily_logs.json`：每日完成记录
- `mistakes.json`：错题包
- `papers.json`：真题/套卷记录
- `current_week.json`：当前周计划
- `dashboard_completions.json`：无 task id 的看板勾选记录

### 2. 任务生成规则

默认使用任务清单，而不是纯时间块。

每个任务必须尽量具体到：

- 资料：哪本书、哪个网课、哪个题库、哪个 App
- 范围：章节、小节、页码、讲次、题号
- 数量：多少页、多少讲、多少题、多少词、多少篇
- 动作：看、读、做、订正、总结、背诵、回炉
- 验收：错题订正、错因标记、公式表、框架图、总结页

禁止用模糊任务糊弄执行，比如：

```text
收口一下高数
启动 OS
清尾巴
做点专项
复习当前章节
```

如果页码、讲次、题号未知，skill 会要求 agent 询问用户或查资料，而不是凭空编造。

### 3. 周计划系统

支持生成完整周计划，并按层级组织：

- 主线任务：必须保护的推进任务
- 复习任务：到期复习、错题回炉、公式/单词/框架
- 保底任务：低能量或被打断时的最低完成版本
- 加餐任务：有余力再做，不计入失败

默认周期是“当天到本周日”，而不是强行 7 天。

### 4. 网课控制

网课不是完成本身，只是输入。

规则：

- 每个网课切片建议 30-60 分钟
- 每个切片必须绑定输出
- 数学、408、技术科目必须配套练习
- 默认每天不超过 3 个新课切片
- 课程占比超标时，优先压缩低价值看课，保护做题、订正和复习

### 5. 习题册安排

习题任务包含：

- 题源
- 范围
- 数量
- 限时/不限时
- 订正
- 错因标记
- 后续回炉

正确率低于 60% 时，自动建议降新题量、回到例题/笔记/基础课；60%-80% 继续章节练习并增加订正；80% 以上进入混合和限时训练。

### 6. 复盘与预测

支持：

- 每日完成率统计
- 正确率趋势
- 错因统计
- 每周自动调整建议
- 预测某科是否延期
- 生成“下周必须保护的任务”
- 生成“可以砍掉或降级的任务”

### 7. 错题回炉日历

错题不只是记录，会自动进入复习队列。

默认间隔：

```text
当天 / 1 天 / 3 天 / 7 天 / 14 天 / 30 天
```

HTML 看板里有独立的“错题回炉”标签页，只展示来源标记为 `mistake:<id>` 的回炉任务。

### 8. 真题/套卷模式

支持记录：

- 科目
- 卷名
- 真题/模拟/章节测
- 分数
- 总分
- 用时
- 薄弱专题
- 错因

真题和套卷里的薄弱点会进入后续复习和预测。

### 9. 408 专项模型

内置 408 更细的专题模型：

- 数据结构
- 计算机组成原理
- 操作系统
- 计算机网络

可按专题追踪任务数、完成数、套卷弱点和风险。

### 10. HTML 看板

内置本地 HTML 看板，支持：

- 总览
- 本周任务待办
- 科目进度
- 复习队列
- 阻塞任务
- 408 模型
- 错题/真题
- 错题回炉日历
- 部署说明

本周任务可以直接勾选。开启本地写入服务后，勾选会写入本地学习档案，不需要复制导出。

## 安装

把仓库放到 Codex skills 目录：

```bash
git clone https://github.com/LidioMonkey/study-planner.git ~/.codex/skills/study-planner
```

Windows PowerShell 示例：

```powershell
git clone https://github.com/LidioMonkey/study-planner.git "$env:USERPROFILE\.codex\skills\study-planner"
```

如果你使用自定义 `CODEX_HOME`，放到：

```text
$CODEX_HOME/skills/study-planner
```

## 快速开始

进入 skill 目录：

```bash
cd ~/.codex/skills/study-planner
```

初始化一个最小档案：

```bash
python scripts/study_profile_seed.py --profile default
```

一键生成并启动看板：

```bash
python scripts/study_dashboard_launch.py --profile default --open
```

默认地址：

```text
HTML 看板：http://127.0.0.1:8787/
本地写入 API：http://127.0.0.1:8790/api/health
```

## 常用命令

### 初始化档案

```bash
python scripts/study_store.py init --profile default --goal "2027 考研" --deadline 2026-12-20
```

### 设置科目权重

```bash
python scripts/study_store.py set-weights --profile default --weights "Math II=30,408 - Operating System=16,408 - Computer Organization=12,408 - Computer Network=10,408 - Data Structure=7,English II=15,Politics=10"
```

### 添加网课任务

```bash
python scripts/study_store.py add-course --profile default --subject "Math II" --title "李永乐线代基础篇" --slice "矩阵对角化" --lecture-range "第 12-13 讲" --page-range "P80-P96" --output "对角化条件清单" --exercise "配套习题 1-25"
```

### 添加习题任务

```bash
python scripts/study_store.py add-exercise --profile default --subject "Math II" --resource "660 题" --scope "二重积分" --problem-range "第 1-30 题" --quantity 30
```

### 生成本周计划

```bash
python scripts/study_store.py weekly-plan --profile default
```

### 提交当前周计划为基线

```bash
python scripts/study_store.py commit-weekly-plan --profile default
```

### 记录完成情况

```bash
python scripts/study_store.py log --profile default --task-id T001 --status done --accuracy 72 --error-causes "concept,calculation" --note "8 道错题，主要是概念混淆"
```

### 添加错题

```bash
python scripts/study_store.py add-mistake --profile default --subject "Math II" --source "660 题" --question "二重积分 #12" --knowledge "积分区域换序" --error-causes "concept,method"
```

### 生成错题包

```bash
python scripts/study_store.py mistake-pack --profile default --subject "Math II" --error-cause concept
```

### 添加真题/套卷记录

```bash
python scripts/study_store.py add-paper --profile default --subject "408 - Operating System" --name "OS 模拟卷 1" --paper-type mock --score 32 --total-score 45 --minutes 45 --weak-topics "memory management,scheduling pv" --error-causes "concept,timing"
```

### 查看分析报告

```bash
python scripts/study_store.py analytics-report --profile default --days 7
python scripts/study_store.py control-report --profile default
python scripts/study_store.py blocked-report --profile default
python scripts/study_store.py course-ratio-report --profile default --source current-week --cap 40
python scripts/study_store.py 408-model-report --profile default
```

## 看板脚本

### 生成 HTML

```bash
python scripts/study_dashboard.py --profile default
```

输出位置：

```text
~/.codex/study-planner/dashboards/default/index.html
```

### 启动本地写入 API

```bash
python scripts/study_dashboard_server.py --profile default
```

接口：

```text
GET  /api/health
GET  /api/mistake-calendar
POST /api/log-task
POST /api/roll-next-cycle
POST /api/regenerate-dashboard
```

### 一键启动

```bash
python scripts/study_dashboard_launch.py --profile default --open
```

可选参数：

```bash
--profile <name>
--codex-home <path>
--static-port <port>
--api-port <port>
--out-dir <path>
--no-static
--no-api
```

## 本地写入逻辑

HTML 勾选任务时会调用：

```text
POST http://127.0.0.1:8790/api/log-task
```

有 `task_id` 的任务写入：

```text
daily_logs.json
```

没有 `task_id` 的保底任务写入：

```text
dashboard_completions.json
```

这样不会把纯文本保底任务伪装成正式任务完成。

## 域名部署

HTML 看板本身是静态页面，可以部署到：

- Nginx
- Cloudflare Pages
- Vercel
- Netlify
- 任意静态 Web 根目录

但直接写入本地档案仍需要用户电脑上的本地 API 服务。

如果域名页面需要访问本机 API，需要设置允许来源：

```bash
STUDY_DASHBOARD_ORIGINS=https://example.com python scripts/study_dashboard_server.py --profile default
```

Windows PowerShell：

```powershell
$env:STUDY_DASHBOARD_ORIGINS='https://example.com'
python scripts\study_dashboard_server.py --profile default
```

安全建议：本地写入服务默认绑定 `127.0.0.1`，不要随便开放到公网。

## Agent / Hermes 适配

这个 skill 已经按“其它 agent 可复用”的方式封装：

- 所有脚本在 `scripts/`
- 不依赖作者本机路径
- 不写死 profile 名
- 不写死 `CODEX_HOME`
- 支持显式 `--profile`
- 支持显式端口
- 支持隔离输出目录
- 有 `references/agent-integration.md` 说明

Hermes 或其它 agent 推荐流程：

1. 读取 `SKILL.md`
2. 需要部署/迁移/端口/路径时读取 `references/agent-integration.md`
3. 先运行 `study_profile_seed.py` 或 `study_store.py init`
4. 用 `study_store.py` 修改学习档案
5. 每次数据变化后运行 `study_dashboard.py`
6. 本地浏览使用 `study_dashboard_launch.py`
7. 不要重新手写 HTML/API，优先复用内置脚本

## 文件结构

```text
study-planner/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── agent-integration.md
│   ├── completion-control.md
│   ├── course-control.md
│   ├── exam-presets.md
│   ├── model-408.md
│   ├── module-templates.md
│   ├── paper-mode.md
│   ├── planning-rules.md
│   └── task-schemas.md
└── scripts/
    ├── study_store.py
    ├── study_dashboard.py
    ├── study_dashboard_server.py
    ├── study_dashboard_launch.py
    └── study_profile_seed.py
```

## 当前状态

已完成：

- 任务式学习计划
- 周计划生成
- 主线/复习/保底/加餐分层
- 网课控制
- 习题册安排
- 依赖控制
- 完成率和正确率分析
- 错因统计
- 延期预测
- 错题包
- 错题回炉日历
- 真题/套卷模式
- 408 专项模型
- HTML 看板
- 本地勾选直写档案
- 备用导出
- 通用 agent / Hermes 封装

仍可继续增强：

- HTML 内新增/编辑任务
- HTML 内录入正确率和错因
- HTML 内添加错题
- 自动备份和恢复 UI
- 多用户权限
- 更完整的移动端交互

## License

未指定许可证。公开复用前建议补充明确 license。
