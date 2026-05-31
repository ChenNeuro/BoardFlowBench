# BoardFlowBench

> **A repo-local benchmark and skill suite for sequential coding-agent handoff**
>
> 面向 Coding Agent 的仓库内共享状态、顺序交接、协作纪律与代码健康评测

BoardFlowBench 的核心目标不是做一个 GUI 工具，也不是单纯检查代码风格，而是研究和评测 coding agents 在同一个仓库中顺序接力时，是否能通过 repo-local shared state 降低上下文丢失、重复工作、scope drift 和交接不完整等问题。

本仓库包含三层内容：

- **BoardFlow 协议**：`.board/`、`.repo_manager/` 等仓库内状态文件，用来记录任务、交接、风险、验证证据和 agent 上下文。
- **Agent skills**：Claude Code / Codex / OpenCode 可使用的 skills，帮助 agent 读取状态、更新看板、写 handoff、做代码健康审查。
- **Benchmark checks**：`tools/benchmark_scorer.py` 和 core checker，用可观察的 repo 状态评估任务完成、交接质量、scope control、hygiene 和 board consistency。

## 核心 Agent Skills

### Agent Bridge (`agent-bridge`)

负责 agent 对接、任务交接、仓库风格学习、共享上下文管理。它面向“一个 agent 做到一半，另一个 agent 接着做”的场景。

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

检查 AI 生成 Python 代码的结构健康，重点发现 agent 接力开发中常见的 patch/helper 膨胀、重复函数、临时文件和风格漂移。

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
BoardFlowBench/
├── .claude/
│   └── skills/              # Claude Code 项目级 skill 入口
├── repo_manager_core/       # 唯一核心实现
│   ├── board/               # Agent Bridge: 看板 I/O、交接、验证
│   ├── style/               # 风格学习、profile 构建
│   └── health/              # Code Health: AST 扫描、味道检测
├── skills/
│   ├── agent-bridge/        # Skill: 任务交接管理
│   └── code-health-review/  # Skill: 代码健康审查
├── tools/
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

### 0. 准备环境

本仓库的 core package 要么安装到当前 Python 环境，要么从源码运行时显式设置 `PYTHONPATH=.`。

```bash
# 推荐：开发模式安装
python3 -m pip install -e .

# 或者不安装，后续命令都加 PYTHONPATH=.
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_init_board.py --help
```

`pyproject.toml` 要求 Python `>=3.11`。测试依赖见 `requirements.txt`。

### 1. 在 Coding Agent 里使用

这个项目里的“agent”不是一个单独启动的后台服务，而是一组给 Claude Code / Codex / OpenCode 读取的 **skills + repo-local 状态协议**。实际用法是：让当前 coding agent 调用对应 skill，skill 再读写 `.board/` 和 `.repo_manager/` 中的共享状态。

#### 作为 Claude Code 项目使用

仓库内已经包含 Claude Code 项目级 skill 配置：

```text
.claude/skills/agent-bridge/SKILL.md
.claude/skills/code-health-review/SKILL.md
```

打开本仓库时，Claude Code 可以直接读取这些项目级 skills。它们是 wrapper，真正实现仍在 `skills/` 和 `repo_manager_core/` 中，避免维护两份逻辑。

#### 作为 Codex / OpenCode / 全局 skill 使用

如果希望在其他仓库中也使用这些 skills：

```bash
# 安装到 Claude Code
bash install/install_claude.sh

# 安装到 Codex
bash install/install_codex.sh

# 安装到 OpenCode
bash install/install_opencode.sh

# 安装到所有平台
bash install/install_all.sh
```

安装后重启对应 agent 客户端。

### 2. Agent Bridge 怎么用

`agent-bridge` 用来做任务接手、状态同步和交接记录。你可以直接在 agent 对话里这样要求：

```text
Use the agent-bridge skill. Read .board/tasks.yaml and .repo_manager/agent_context.md, then continue task T002.
```

中文也可以直接说：

```text
使用 agent-bridge。先读 .board/tasks.yaml 和 .repo_manager/agent_context.md，检查 T002 的依赖、allowed_paths 和 acceptance_commands，然后继续任务。
```

agent 应该按这个顺序工作：

1. 读取 `.board/tasks.yaml`，确认任务状态、依赖和允许修改范围。
2. 读取 `.repo_manager/agent_context.md`，理解上一轮 agent 留下的上下文。
3. 只修改任务 `allowed_paths` 里的文件。
4. 运行任务里的 `acceptance_commands`。
5. 更新 `.board/tasks.yaml` 的状态和 owner。
6. 停止或移交前写 `.board/handoffs/<task_id>_<agent>.json`。
7. 更新 `.repo_manager/agent_context.md`，让下一个 agent 能接手。

当前仓库的 `.board/tasks.yaml` 中，`T001` 已经是 `DONE`，`T002` 还在 `TODO`，所以演示接手时通常从 `T002` 开始。

### 3. 直接运行 Agent Bridge 脚本

如果不用 agent 客户端，也可以直接运行脚本维护 repo-local shared state。未执行 `pip install -e .` 时，命令前加 `PYTHONPATH=.`：

```bash
# 初始化看板
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_init_board.py --repo .

# 更新任务状态
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_status.py T002 IN_PROGRESS --owner codex --repo .

# 创建交接记录
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_handoff.py T002 codex first_worker \
  --repo . \
  --status IN_PROGRESS \
  --files template/expense_lite/src/expense_lite/parser.py \
  --risks "CSV edge cases still need review" \
  --next-step "Run parser and validator tests"

# 学习仓库风格
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_learn_style.py .

# 更新 agent 上下文
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_update_context.py --repo . --agent-id codex --task-id T002
```

### 4. Code Health Review 怎么用

`code-health-review` 用来审查 AI 生成代码是否出现临时 patch/helper 膨胀、重复函数、wrapper 函数、可疑文件名和风格漂移。它只报告问题，不修改源码。

在 agent 对话里可以这样要求：

```text
Use the code-health-review skill to review this repo for AI-generated code health issues.
```

也可以直接运行脚本：

```bash
# 扫描仓库
PYTHONPATH=. python3 skills/code-health-review/scripts/health_scan.py template/messy_ai_case --output outputs/repo_profile.json

# 检测函数味道
PYTHONPATH=. python3 skills/code-health-review/scripts/health_detect_smells.py template/messy_ai_case --output outputs/smell_report.json

# 生成完整报告
PYTHONPATH=. python3 skills/code-health-review/scripts/health_generate_report.py template/messy_ai_case --output-dir outputs
```

### 5. 运行 Benchmark Scorer

```bash
PYTHONPATH=. python3 tools/benchmark_scorer.py --task path/to/task.yaml --repo . --output outputs/score.json
```

### 6. 运行测试

```bash
PYTHONPATH=. python3 -m pytest tests/ -v
```

## Agent 交接流程

```
用户让 Agent A 开始任务
        ↓
Agent A 使用 agent-bridge
读取 .board/tasks.yaml、agent_context.md、任务验收条件
        ↓
Agent A 修改允许范围内的文件并记录验证证据
        ↓
Agent A 更新任务状态并写 handoff
        ↓
用户让 Agent B 继续
        ↓
Agent B 只依赖可观察的 repo 状态接手
        ↓
Reviewer / scorer 检查任务完成、handoff、scope、hygiene 和 board consistency
```

## 核心原则

- **`repo_manager_core/` 是唯一实现** — skill scripts 是 thin wrapper，零代码重复
- **Agent Bridge 管"过程"** — 任务交接、上下文传递
- **Code Health 管"质量"** — 代码结构审查
- **Benchmark Scorer 管"证据"** — 只基于可观察 repo 状态评分
- **仓库状态是真理来源** — 不依赖聊天记录传递上下文
