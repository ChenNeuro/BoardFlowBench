# BoardFlowBench

> **A repo-local benchmark and skill suite for sequential coding-agent handoff**
>
> 面向 Coding Agent 的仓库内共享状态、顺序交接、协作纪律与代码健康评测

BoardFlowBench 的核心目标不是做一个 GUI 工具，也不是单纯检查代码风格，而是研究和评测 coding agents 在同一个仓库中顺序接力时，是否能通过 repo-local shared state 降低上下文丢失、重复工作、scope drift 和交接不完整等问题。

本仓库包含三层内容：

- **BoardFlow 协议**：`.board/`、`.repo_manager/` 等仓库内状态文件，用来记录任务、交接、风险、验证证据和 agent 上下文。
- **Agent skills**：Claude Code 可使用的 skills，帮助 agent 读取状态、更新看板、写 handoff、做代码健康审查。
- **Benchmark checks**：`tools/benchmark_scorer.py` 和 core checker，用可观察的 repo 状态评估任务完成、交接质量、scope control、hygiene 和 board consistency。

Expense Lite demo 不再作为本仓库中的业务代码维护。它位于独立仓库
`ChenNeuro/ExpenseLiteBenchDemo`，每次实验从固定 seed commit clone 到临时 workspace。
根目录的 `PROJECT_BOARD.md` 和 `.board/` 只记录 BoardFlowBench 自身研发任务。

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

检查 AI 生成 Python 代码的结构健康，重点发现 agent 接力开发中常见的 patch/helper 膨胀、重复函数、临时文件和风格漂移。检测规则现在是 **repo-adaptive** 的：默认 smell 规则从 `repo_manager_core/default_smell_rules.json` 读取，默认扫描范围从 `repo_manager_core/default_search_rules.json` 读取；具体仓库会在 `.repo_manager/` 下生成自己的规则文件，后续人工反馈和 agent 调整都只改 repo-local 文件，所有学习结果都可审计、可回滚。

| 检测项 | 严重度 | 说明 | 主要调整入口 |
|--------|--------|------|--------------|
| patch_name_smell | medium | 函数名命中 `patch_keywords`，具体策略由规则文件决定 | `.repo_manager/smell_rules.json` |
| unused_function | low | 定义但未被其他扫描函数调用 | 源码阈值/入口点规则 |
| wrapper_function | low | ≤5 行且只委托给一个函数 | 源码阈值 |
| duplicate_function_name | low | 同名函数出现多次 | 源码规则 |
| suspicious_file_name | medium | 文件名命中 `suspicious_file_keywords` | `.repo_manager/smell_rules.json` |
| fragmented_helpers | medium | 一个文件 ≥4 个短 helper-like 函数 | `.repo_manager/smell_rules.json` + 源码阈值 |
| too_many_top_level_python_files | medium | 顶级 .py 文件 >8 | 源码阈值 |
| suspicious_directory_name | low | 目录名命中 `suspicious_directory_keywords` | `.repo_manager/smell_rules.json` |
| python_file_inside_output_directory | medium | .py 文件在 output/artifact/result 目录内 | 源码 keyword |

**输出文件：**
- `repo_manager_report/repo_profile.json`
- `repo_manager_report/smell_report.json`
- `repo_manager_report/style_profile.json`
- `repo_manager_report/code_health_report.md`

**规则与反馈文件：**
- `repo_manager_core/default_smell_rules.json`：包内默认规则
- `repo_manager_core/default_search_rules.json`：包内默认扫描范围
- `.repo_manager/smell_rules.json`：当前仓库的 smell keyword 策略
- `.repo_manager/search_rules.json`：当前仓库的扫描范围策略
- `.repo_manager/user_feedback.jsonl`：人工反馈事件日志

**优先调整位置：**
- 改扫描范围：编辑 `.repo_manager/search_rules.json`。
- 改 keyword 是否可疑：编辑 `.repo_manager/smell_rules.json`，或通过 `--feedback` 写入。
- 改默认初始规则：编辑 `repo_manager_core/default_smell_rules.json` 或 `repo_manager_core/default_search_rules.json`。
- 改算法阈值：当前仍在源码中，例如 wrapper 长度、fragmented helper 数量、顶层 Python 文件数量。

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
├── benchmark/
│   ├── targets/             # 独立 demo 仓库地址和固定 seed commit
│   ├── tasks/expense_lite/  # Demo benchmark 任务规格
│   └── templates/           # 注入临时 workspace 的协议模板
├── project/tasks/           # BoardFlowBench 自身研发任务规格
├── install/                 # Claude Code 安装脚本
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

这个项目里的“agent”不是一个单独启动的后台服务，而是一组给 Claude Code 读取的 **skills + repo-local 状态协议**。实际用法是：让当前 coding agent 调用对应 skill，skill 再读写 `.board/` 和 `.repo_manager/` 中的共享状态。

#### 作为 Claude Code 项目使用

仓库内已经包含 Claude Code 项目级 skill 配置：

```text
.claude/skills/agent-bridge/SKILL.md
.claude/skills/code-health-review/SKILL.md
```

打开本仓库时，Claude Code 可以直接读取这些项目级 skills。它们是 wrapper，真正实现仍在 `skills/` 和 `repo_manager_core/` 中，避免维护两份逻辑。

#### 安装为 Claude Code 全局 skill

如果希望在其他仓库中也使用这些 skills：

```bash
# 安装到 Claude Code
bash install/install_claude.sh
```

安装后重启 Claude Code。

### 2. Agent Bridge 怎么用

`agent-bridge` 用来做任务接手、状态同步和交接记录。你可以直接在 agent 对话里这样要求：

```text
Use the agent-bridge skill. Read .board/tasks.yaml and .repo_manager/agent_context.md, then continue the assigned project task.
```

中文也可以直接说：

```text
使用 agent-bridge。先读 .board/tasks.yaml 和 .repo_manager/agent_context.md，检查被分配项目任务的依赖和验收条件，然后继续任务。
```

agent 应该按这个顺序工作：

1. 读取 `.board/tasks.yaml`，确认任务状态、依赖和允许修改范围。
2. 读取 `.repo_manager/agent_context.md`，理解上一轮 agent 留下的上下文。
3. 只修改任务 `allowed_paths` 里的文件。
4. 运行任务里的 `acceptance_commands`。
5. 更新 `.board/tasks.yaml` 的状态和 owner。
6. 停止或移交前写 `.board/handoffs/<task_id>_<agent>.json`。
7. 更新 `.repo_manager/agent_context.md`，让下一个 agent 能接手。

根 taskboard 只服务 BoardFlowBench 研发。Demo 实验使用初始化命令生成自己的 B 系列 taskboard。

### 3. 直接运行 Agent Bridge 脚本

如果不用 agent 客户端，也可以直接运行脚本维护 repo-local shared state。未执行 `pip install -e .` 时，命令前加 `PYTHONPATH=.`：

```bash
# 初始化看板
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_init_board.py --repo .

# 更新任务状态
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_status.py P004 IN_PROGRESS --owner codex --repo .

# 开始任务前刷新 blackboard、sticker 和 git 状态
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py \
  --phase start --agent-id codex --task-id P004 --repo .

# 创建交接记录
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_handoff.py P004 codex first_worker \
  --repo . \
  --status IN_PROGRESS \
  --files src/parser.py \
  --risks "CSV edge cases still need review" \
  --next-step "Run parser and validator tests"

# 学习仓库风格
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_learn_style.py .

# 更新 agent 上下文
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_update_context.py --repo . --agent-id codex --task-id P004

# 结束前刷新共享上下文
PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py \
  --phase end --agent-id codex --task-id P004 --repo .
```

### 4. Code Health Review 怎么用

`code-health-review` 用来审查 AI 生成代码是否出现临时 patch/helper 膨胀、重复函数、wrapper 函数、可疑文件名和风格漂移。它只报告问题，不修改源码。规则加载顺序是：

1. 尝试读取当前 repo 的 `.repo_manager/search_rules.json`；如果不存在，就从 `repo_manager_core/default_search_rules.json` 生成初始版本。
2. 尝试读取当前 repo 的 `.repo_manager/smell_rules.json`；如果不存在，就从 `repo_manager_core/default_smell_rules.json` 生成初始版本。
3. 使用 `search_rules` 控制扫描哪些目录、文件后缀，以及要排除的目录/文件/glob。
4. 使用 `smell_rules` 控制哪些 keyword 可疑、上下文相关、允许或逐例判断。
5. 生成 `repo_manager_report/`，并在报告里列出 `Learned Repository Policies` 和 `Feedback Requested`。
6. 只有用户显式提供 `--feedback` 时，才会写入 `.repo_manager/user_feedback.jsonl` 并更新 `.repo_manager/smell_rules.json`。

运行后，如果当前仓库还没有这些文件，工具会自动创建：

```text
.repo_manager/search_rules.json
.repo_manager/smell_rules.json
```

后续让 agent 调整扫描策略时，优先让它改这两个文件，而不是改 Python 源码。这样不同仓库可以保留自己的规则，默认配置也不会被污染。

在 agent 对话里可以这样要求：

```text
Use the code-health-review skill to review this repo for AI-generated code health issues.
```

也可以直接运行脚本：

```bash
# 扫描当前工作空间
PYTHONPATH=. python3 skills/code-health-review/scripts/health_scan.py .

# 检测函数味道
PYTHONPATH=. python3 skills/code-health-review/scripts/health_detect_smells.py .

# 生成完整报告
PYTHONPATH=. python3 skills/code-health-review/scripts/health_generate_report.py .
```

如果报告里提示某个 keyword 需要确认，可以显式记录反馈：

```bash
# 将 fix 标记为上下文相关：只有未使用/缺少验证时才更可疑
PYTHONPATH=. python3 skills/code-health-review/scripts/health_generate_report.py . \
  --feedback fix=contextual \
  --feedback-reason "Used in public APIs"

# 将 old 目录标记为允许，例如它是兼容层
PYTHONPATH=. python3 skills/code-health-review/scripts/health_generate_report.py . \
  --feedback suspicious_directory_keywords:old=allowed \
  --feedback-reason "Compatibility layer"
```

支持的 policy：

- `suspicious`：总是作为可疑信号
- `contextual`：只在上下文更可疑时提示，例如未被扫描调用
- `allowed`：当前仓库允许这种命名
- `case_by_case`：不自动报警，但继续在报告里请求人工判断

典型调整方式：

```json
{
  "patch_keywords": {
    "fix": {
      "policy": "contextual",
      "source": "user_feedback",
      "reason": "This repo exposes fix_* functions as stable public APIs"
    },
    "safe": {
      "policy": "allowed",
      "source": "repo_convention",
      "reason": "safe_* is the local convention for tolerant parsers"
    }
  }
}
```

`.repo_manager/smell_rules.json` 示例：

```json
{
  "patch_keywords": {
    "fix": {
      "policy": "contextual",
      "source": "user_feedback",
      "reason": "Used in public APIs"
    }
  }
}
```

`.repo_manager/search_rules.json` 示例：

```json
{
  "include_paths": ["src", "tests"],
  "exclude_dirs": [".git", ".venv", "__pycache__", "repo_manager_report"],
  "exclude_files": ["main_rocopar.py", "tests/main_rocopar_test.py"],
  "exclude_globs": ["scripts/debug_*.py", "generated/*.py"],
  "file_suffixes": [".py"],
  "schema_version": 1
}
```

`exclude_files` 支持两种写法：`"main.py"` 会排除任意目录下同名文件，`"src/main.py"` 只排除指定相对路径。`exclude_globs` 用于排除一类文件；不含 `/` 的 pattern 按文件名匹配，包含 `/` 的 pattern 按仓库相对路径匹配。

### 5. 运行 Benchmark Scorer

先从独立 demo seed 初始化临时实验 workspace：

```bash
PYTHONPATH=. python3 scripts/init_benchmark_workspace.py \
  --target expense_lite \
  --condition boardflow_sequential \
  --task-id B001 \
  --workspace /tmp/boardflowbench-runs/run-001
```

本地验证尚未推送的 sibling demo 仓库时，追加
`--source-repo ../ExpenseLiteBenchDemo`。

后续阶段只在依赖完成后注入当前任务规格：

```bash
PYTHONPATH=. python3 scripts/activate_benchmark_task.py \
  --workspace /tmp/boardflowbench-runs/run-001 \
  --task-id B002
```

scorer 针对临时 workspace 运行：

```bash
PYTHONPATH=. python3 tools/benchmark_scorer.py \
  --task .board/assigned_task.yaml \
  --repo /tmp/boardflowbench-runs/run-001 \
  --output /tmp/boardflowbench-runs/run-001-score.json
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
- **Demo 是独立测试平台** — 根仓库不维护 demo 业务功能，实验使用固定 seed 的临时 clone
