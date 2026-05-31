# Repo Manager

> **A Skill Suite for Agent Handoff and AI Code Health Review**
>
> 面向多 Coding Agent 的仓库交接管理与 AI 代码健康审查 Skill 套件

Repo Manager 不是一个普通代码检查器，而是一个面向 AI coding agents 的仓库管理 skill suite：一个 skill 负责 agent 对接和上下文交接，另一个 skill 负责检查 AI 生成代码是否正在损害仓库健康。

## 两个核心 Skill

### Agent Bridge (`agent-bridge`)

负责 agent 对接、任务交接、仓库风格学习、共享上下文管理。

| 功能 | 说明 |
|------|------|
| 任务看板 | 维护 `.board/tasks.yaml`，追踪任务状态和依赖 |
| 交接记录 | 读写结构化 handoff JSON（`handoff.schema.json`） |
| Review 记录 | 写 review markdown 到 `.board/reviews/` |
| 风格学习 | 分析 repo 命名惯例、docstring 覆盖、函数长度统计 |
| Agent 上下文 | 维护 `.repo_manager/agent_context.md` 帮助下一个 agent 快速接手 |

**输出文件：**
- `.board/tasks.yaml`
- `.board/handoffs/<task_id>_<agent>.json`
- `.board/reviews/<task_id>_review.md`
- `.repo_manager/repo_style_profile.json`
- `.repo_manager/agent_context.md`

### Code Health Review (`code-health-review`)

检查 AI 生成 Python 代码的结构健康。

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| patch_name_smell | medium | 函数名含 fix/patch/temp/hack/debug/safe |
| unused_function | low | 定义但未被其他扫描函数调用 |
| wrapper_function | low | ≤5 行且只委托给一个函数 |
| duplicate_function_name | low | 同名函数出现多次 |
| suspicious_file_name | medium | 文件名含 final/old/backup/temp/fixed/patch/debug |
| fragmented_helpers | medium | 一个文件 ≥4 个短 helper 函数 |
| too_many_top_level_python_files | medium | 顶级 .py 文件 >8 |
| suspicious_directory_name | low | 目录名含 old/temp/backup/final |
| python_file_inside_output_directory | medium | .py 文件在 output/artifact 目录内 |

**输出文件：**
- `outputs/repo_profile.json`
- `outputs/smell_report.json`
- `outputs/style_profile.json`
- `outputs/code_health_report.md`

## 目录结构

```
repo-manager/
├── repo_manager_core/       # 唯一核心实现
│   ├── board/               # Agent Bridge: 看板 I/O、交接、验证
│   ├── style/               # 风格学习、profile 构建
│   └── health/              # Code Health: AST 扫描、味道检测
├── skills/
│   ├── agent-bridge/        # Skill: 任务交接管理
│   └── code-health-review/  # Skill: 代码健康审查
├── tools/
│   ├── gui_app.py           # Streamlit GUI
│   └── benchmark_scorer.py  # 评分运行器
├── template/                # 示例仓库
│   ├── clean_case/          # 健康代码示例
│   ├── messy_ai_case/       # 有味道代码示例
│   └── expense_lite/        # 多 agent 交接演示
├── install/                 # 安装脚本（Claude Code/Codex/OpenCode）
├── tests/                   # 测试
├── .board/                  # Agent Bridge 状态文件
├── .repo_manager/           # 风格 profile 和 agent context
└── docs/                    # 研究文档
```

## 快速开始

### 安装 Skill

```bash
# 安装到 Claude Code
bash install/install_claude.sh

# 安装到所有平台
bash install/install_all.sh
```

### 使用 Code Health Review

```bash
# 扫描仓库
python skills/code-health-review/scripts/health_scan.py template/messy_ai_case --output outputs/repo_profile.json

# 检测函数味道
python skills/code-health-review/scripts/health_detect_smells.py template/messy_ai_case --output outputs/smell_report.json

# 生成完整报告
python skills/code-health-review/scripts/health_generate_report.py template/messy_ai_case --output-dir outputs
```

### 使用 Agent Bridge

```bash
# 初始化看板
python skills/agent-bridge/scripts/bridge_init_board.py

# 更新任务状态
python skills/agent-bridge/scripts/bridge_status.py T001 IN_PROGRESS --owner agent-c

# 创建交接记录
python skills/agent-bridge/scripts/bridge_handoff.py T001 agent-c first_worker --files src/parser.py

# 学习仓库风格
python skills/agent-bridge/scripts/bridge_learn_style.py .

# 更新 agent 上下文
python skills/agent-bridge/scripts/bridge_update_context.py --agent-id agent-c --task-id T001
```

### 启动 GUI

```bash
streamlit run tools/gui_app.py
```

### 运行测试

```bash
python -m pytest tests/ -v
```

## 演示流程

```
用户让 Claude Code 继续一个任务
        ↓
Claude Code 使用 agent-bridge
读取 .board/tasks.yaml 和 agent_context.md
        ↓
Claude Code 理解当前任务和 repo 风格
        ↓
Claude Code 完成或审查代码
        ↓
Claude Code 使用 code-health-review
检查 AI 代码健康
        ↓
Claude Code 使用 agent-bridge
写 handoff、更新任务板、保存 review 记录
```

## 核心原则

- **`repo_manager_core/` 是唯一实现** — skill scripts 是 thin wrapper，零代码重复
- **Agent Bridge 管"过程"** — 任务交接、上下文传递
- **Code Health 管"质量"** — 代码结构审查
- **仓库状态是真理来源** — 不依赖聊天记录传递上下文
