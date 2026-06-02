# BoardFlowBench Research Plan

项目名称：BoardFlowBench

项目副标题：A benchmark for repo-local shared state in sequential multi-agent coding handoff.

> 注：本文保留早期研究设计语言，作为项目演进记录。当前实现以 `docs/EXPERIMENT_PROTOCOL.md`、`benchmark/scenarios/`、`benchmark/targets/` 和 `scripts/run_scenario.py` 为准。Expense Lite 已拆分为独立 target 仓库。

## 1. Problem statement

现代开发者经常在 Codex、Claude Code、OpenCode、Cursor、GitHub Copilot 等 coding agents 之间切换。同一个 repo 中的任务可能由一个 agent 开始、另一个 agent 接手、第三个 agent 复核或修补。当前常见问题不是单个 agent 完全不会写代码，而是在 sequential handoff 中容易丢失上下文和协作纪律。

典型失败包括：

- 新 agent 不了解前一个 agent 已经完成了什么，重复实现或推翻已有工作。
- 临时文件、调试脚本、实验输出被留在 repo 中。
- 输出命名不一致，导致评审者和后续 agent 难以判断哪些文件是正式产物。
- agent 修改与当前任务无关的文件，造成 scope drift。
- 任务状态、剩余风险、未验证假设没有被结构化记录。
- 测试、lint、review gate、CI 状态没有被纳入 handoff 语境。

BoardFlowBench 的问题定义是：在 sequential multi-agent coding handoff 中，repo-local shared state 是否能降低 context loss 和 coordination failures。

本项目不试图证明某个 agent 的 coding ability 更强，也不试图建立所有 agent 必须遵守的 universal standard。研究目标是评估一个轻量、repo-local、可检查的协作协议是否能让不同 agent 在同一个 repo 内更稳定地延续彼此的工作。

## 2. Motivation

coding agents 的使用方式正在从“单轮问答”转向“长任务协作”。真实开发中，人的上下文不只存在于聊天记录里，也存在于 repo 内的 issue、milestone、branch、commit、PR、CI、review comment 和 handoff note 中。相比之下，很多 agent handoff 依赖对话历史或用户口头转述，这两者都容易丢失、不可验证、也不一定被后续 agent 自动读取。

BoardFlow 的基本动机是把一小部分人类软件协作机制下沉到 repo-local shared state 中，让上下文成为代码库的一部分。这样做有几个潜在优势：

- 后续 agent 不需要访问前一个 agent 的私有会话历史，也能读到任务状态。
- 协作约束可以被 checker 验证，而不是只依赖自然语言提醒。
- benchmark 可以测量 coordination discipline，而不是只看最终代码能否跑通。
- repo-local 文件易于版本控制，适合课程项目、公开复现和横向比较。

TODO: 需要通过小规模 pilot run 验证不同 coding agents 是否会主动读取这些 repo-local 文件；如果不会，benchmark prompt 中需要明确要求读取 BoardFlow 文件。

## 3. Human software collaboration analogy

人类团队很少只靠记忆完成复杂软件协作。常见机制包括 milestone planning、ticket ownership、handoff notes、PR review、CI gate、release checklist 和 repo hygiene rules。BoardFlow 将这些机制压缩成一个适合 agent benchmark 的最小协议。

类比如下：

| Human collaboration mechanism | BoardFlow artifact | 作用 |
| --- | --- | --- |
| Milestone board | `PROJECT_BOARD.md` | 记录当前 milestone、任务队列、完成标准和整体进度 |
| Ticket database | `.board/tasks.yaml` | 以结构化方式记录 task id、状态、owner、依赖和验收条件 |
| Handoff note | `.board/handoffs/*.json` | 记录前一个 agent 的完成内容、未完成事项、验证结果和风险 |
| Team onboarding doc | `AGENTS.md` | 告诉 agent 如何进入项目、如何阅读状态、如何交接 |
| Working agreement | `AI_CONTRACT.md` | 定义 agent 不应做什么、必须保留什么、何时更新 board |
| CI and review gates | hygiene checker / board consistency checker | 检查临时文件、状态不一致、缺失 handoff 等问题 |
| Release or evaluation script | scoring script | 将 handoff 质量和 hygiene 结果转化为 benchmark score |

这个类比不是要把人类团队流程完整搬进 repo，而是提取对 sequential handoff 最关键的最小信号：任务状态、责任边界、已完成工作、剩余风险、验证证据和 repo 清洁度。

## 4. Why sequential handoff is the first target instead of parallel development

parallel multi-agent development 也重要，但它引入了更多变量：分支合并、冲突解决、任务拆分策略、并发调度、权限控制和 inter-agent messaging。这些问题会让 benchmark 很快变成分布式协作系统评估，而不是专注于 context continuity。

sequential handoff 更适合作为第一阶段目标：

- 场景更常见：用户经常让一个 agent 做到一半，再换另一个 agent 继续。
- 控制变量更少：同一时间只有一个 agent 修改 repo，更容易定位失败来源。
- 失败更可观察：重复工作、遗漏 handoff、未更新 board、误删前人成果等问题可以直接在 diff 和 checker 中看到。
- 更接近课程项目规模：可以用少量任务、少量 agents、少量 runs 建立可复现实验。
- 是 parallel development 的基础：如果 sequential handoff 都不稳定，parallel handoff 的结果更难解释。

因此 BoardFlowBench 第一阶段只评估 A -> B -> C 这类顺序交接。parallel development 可以作为后续扩展，而不是 minimal viable benchmark 的一部分。

## 5. BoardFlow protocol overview

BoardFlow 是一个轻量 repo-local protocol，不是新的 coding agent，也不是跨平台标准。它只规定 benchmark repo 内需要存在的一组共享状态文件和检查规则。

核心文件：

- `PROJECT_BOARD.md`：面向人类和 agent 的 milestone board，描述 milestone、任务状态、验收标准、当前阻塞项和近期 handoff。
- `.board/tasks.yaml`：结构化任务清单，供 checker 和 scoring script 读取。应包含 task id、title、status、owner、depends_on、acceptance、evidence 等字段。
- `.board/handoff.schema.json`：handoff 文件的 JSON Schema，用于校验 handoff note 是否包含必要字段。
- `.board/handoffs/*.json`：每次 agent 交接时生成的结构化 handoff record。应记录 agent identity、task id、summary、changed files、validation、open questions、risks、next recommended action。
- `AGENTS.md`：agent onboarding 文档，说明进入项目后必须先读哪些文件、如何声明任务、如何更新 BoardFlow 状态、如何交接。
- `AI_CONTRACT.md`：行为约束文档，强调 scope control、repo hygiene、不得保留临时文件、不得绕过 checker、不得虚构验证结果。

辅助工具：

- hygiene checker：检查临时文件、未跟踪输出、调试残留、命名异常、root clutter、无关大文件等 repo hygiene 问题。
- board consistency checker：检查 `PROJECT_BOARD.md`、`.board/tasks.yaml` 和 handoff records 之间是否一致。
- scoring script：汇总任务完成度、handoff 完整度、hygiene 违规、board 一致性和验证证据，形成 benchmark score。

协议边界：

- BoardFlow 不要求 agent 使用特定模型、IDE、插件或上下文窗口。
- BoardFlow 不替代 Git、CI 或 issue tracker，而是在 benchmark repo 内提供最小可复现状态。
- BoardFlow 不评估通用工程能力的所有维度，只聚焦 sequential handoff 的连续性和纪律。

## 6. Difference from general coding benchmarks

一般 coding benchmarks 通常关注最终答案是否正确，例如算法题、单函数修复、单 repo bug fix、测试是否通过或模型能否定位 bug。BoardFlowBench 的关注点不同。

主要差异：

- 评估对象不同：BoardFlowBench 评估 handoff continuity 和 coordination discipline，而不是只评估 coding ability。
- 任务形态不同：任务被设计成多个 sequential stages，每个 stage 会留下 partial progress 和交接信息。
- 状态载体不同：benchmark 明确比较有无 repo-local shared state 的条件。
- 失败类型不同：重复工作、状态不一致、未记录风险、hygiene 违规、修改无关文件都属于核心 failure modes。
- 评分信号不同：最终测试通过只是一个维度，handoff completeness、board consistency、scope discipline、validation honesty 同样重要。

BoardFlowBench 的理想结果不是“某 agent 写出了最多代码”，而是“在相同任务难度下，使用 BoardFlow 的 sequential agents 更少丢上下文、更少破坏 repo、更清楚地把工作交给下一位”。

## 7. Proposed demo repository domain

建议 demo repository 采用一个小型、离线、确定性的 issue triage and release note tool。暂定名称可以是 `IssuePulse`，但具体名称不属于本阶段决策。

该 demo domain 的特点：

- 输入是 repo 内的 JSON 或 Markdown issue fixtures。
- 输出是分类后的 issue summary、release note draft 或 maintenance report。
- 功能可以自然拆成 parser、validator、classifier、report renderer、CLI、tests、docs 等模块。
- 不需要外部 API 或真实生产数据，便于复现实验。
- 有足够多的文件和阶段，能观察 sequential handoff 是否维持上下文。
- 业务逻辑不会过于困难，避免 benchmark 被 coding ability 完全主导。

这个 domain 与 BoardFlow 本身相互独立。BoardFlow 是 benchmark protocol；demo repository 是被 agents 修改的目标软件。两者分离可以减少“agent 只是在修改 benchmark 自己”的混淆。

TODO: 需要确认课程项目是否允许包含一个小型 demo application；如果课程更偏研究设计，也可以先用 synthetic repo fixtures 替代完整应用。

## 8. Proposed benchmark tasks

benchmark tasks 应该被设计成连续阶段，每个阶段由不同 agent 接手。任务不应过度依赖复杂算法，而应制造合理的上下文延续需求。

候选任务：

1. 初始化 demo app 的核心数据模型和 fixture 读取逻辑。
2. 增加 issue severity、component、release-blocker 等分类规则。
3. 添加 report renderer，生成 Markdown release note draft。
4. 增加 CLI 参数和错误处理，要求保持前一阶段接口兼容。
5. 添加测试覆盖，并修复前一阶段遗漏的边界条件。
6. 根据 review note 做一次小范围 refactor，但不得改变 public output format。
7. 更新用户文档和 examples，并确保 docs 与 CLI 行为一致。
8. 模拟 bug fix：后续 agent 必须先理解前一个 handoff 中标出的风险，再修补问题。
9. 模拟 incomplete work：前一个 agent 故意留下未完成 TODO，后续 agent 需要判断继续、回滚还是重做。
10. 模拟 hygiene challenge：任务过程中会产生临时输出，agent 必须清理或将其放到约定位置。

每个 task 应包含：

- task id
- 起始状态
- 允许修改范围
- acceptance criteria
- expected validation
- handoff requirements
- scoring hooks

TODO: 需要在下一阶段决定任务数量。课程项目最小版本可以先做 4 到 6 个 sequential tasks，避免实验规模失控。

## 9. Proposed experimental conditions

建议至少比较三个 experimental conditions：

1. No BoardFlow baseline
   - repo 只有普通 README 和测试。
   - 每个 agent 只收到当前任务 prompt。
   - 不提供 `PROJECT_BOARD.md`、structured handoff 或 checker。

2. BoardFlow docs only
   - repo 包含 `PROJECT_BOARD.md`、`AGENTS.md`、`AI_CONTRACT.md`。
   - 允许自然语言 board 和 handoff note。
   - 不强制 schema 或 automated checker。

3. Full BoardFlow
   - repo 包含完整 BoardFlow artifacts。
   - 每次 handoff 必须写 `.board/handoffs/*.json`。
   - checker 验证 board consistency 和 repo hygiene。
   - scoring script 记录任务完成与协作失败。

可选扩展条件：

- Full BoardFlow without explicit prompt reminder：测试 agent 是否会自主读取 repo-local protocol。
- Full BoardFlow with mixed agents：例如 Codex -> Claude Code -> Cursor。
- Full BoardFlow with same agent repeated：作为控制组，观察 agent identity 变化是否是主要因素。

TODO: 需要确认实际可访问的 agents、运行次数和人工标注成本。若样本量较小，应避免声称统计显著性，只报告 exploratory findings。

## 10. Proposed metrics

metrics 应同时覆盖最终产物、handoff 质量和 repo hygiene。

任务完成类：

- pass rate：最终测试或验收脚本通过比例。
- task completion score：每个 task 的 acceptance criteria 满足程度。
- regression count：后续 task 是否破坏前一阶段功能。

handoff continuity 类：

- handoff completeness：handoff record 是否包含 summary、changed files、validation、risks、next steps。
- context reuse score：后续 agent 是否引用并延续前一个 handoff 中的信息。
- duplicate work count：是否重复实现已有功能或重复创建相同文件。
- unresolved TODO tracking：未完成事项是否从 handoff 传递到 board 或下一 task。

coordination discipline 类：

- board consistency violations：`PROJECT_BOARD.md`、`.board/tasks.yaml`、handoff files 之间的状态冲突数量。
- scope drift count：修改了任务允许范围之外的文件或模块的次数。
- validation honesty：声称运行测试但没有证据，或忽略失败结果的次数。
- ownership clarity：当前 task owner、状态和 next action 是否清楚。

repo hygiene 类：

- root clutter count：repo root 中不应存在的临时文件数量。
- temporary artifact count：调试输出、scratch 文件、无关日志等残留数量。
- naming consistency violations：输出文件命名是否偏离约定。
- checker pass rate：hygiene checker 和 board consistency checker 是否通过。

人工评审类：

- reviewer effort：人工理解当前状态所需时间。
- handoff readability：评审者是否能从 board 和 handoff 中判断下一步。
- failure diagnosis clarity：出现失败时能否定位责任阶段和原因。

TODO: 需要定义每个 metric 的精确评分 rubric，避免人工评审过于主观。

## 11. Risks and limitations

主要风险：

- 样本量不足：课程项目可能无法运行足够多 agent combinations，因此结论应定位为 exploratory benchmark proposal。
- prompt sensitivity：不同 prompt 写法可能显著影响 agent 是否遵守 BoardFlow。
- tool access 差异：不同 agent 对文件系统、git、terminal、test runner 的访问能力不同，可能影响结果。
- reviewer bias：人工评价 handoff 质量时可能带有主观判断。
- protocol overhead：BoardFlow 可能增加额外文档和检查成本，小任务中收益不明显。
- benchmark gaming：agent 可能机械更新 board，但并未真正理解上下文。
- demo domain 偏差：一个 issue triage tool 不能代表所有软件项目。
- checker coverage 有限：hygiene checker 能发现文件残留，但很难自动判断所有 scope drift 或设计质量问题。

缓解策略：

- 使用相同 task sequence 和相同起始 repo，对比不同 experimental conditions。
- 将自动 metrics 和人工 review 分开报告。
- 在 prompt 中记录 agent 可用工具和运行环境。
- 把 BoardFlow overhead 作为 metric 之一，而不是默认认为它没有成本。
- 对所有不确定结论使用 TODO 或 limitation 标注。

## 12. Minimal viable implementation plan

第一阶段只产出研究设计和最小协议草案，不实现代码。

建议路线：

1. 完成 `docs/RESEARCH_PLAN.md`，明确研究问题、协议范围、实验条件和 metrics。
2. 起草 BoardFlow protocol 文件模板：
   - `PROJECT_BOARD.md`
   - `.board/tasks.yaml`
   - `.board/handoff.schema.json`
   - `AGENTS.md`
   - `AI_CONTRACT.md`
3. 设计 demo repository 的最小 task sequence，先控制在 4 到 6 个 tasks。
4. 编写 checker 规格，而不是立即实现 checker：
   - hygiene rules
   - board consistency rules
   - scoring fields
5. 实现 demo app 的起始版本和任务 fixtures。
6. 实现 hygiene checker、board consistency checker 和 scoring script。
7. 跑一次 small pilot：
   - baseline condition
   - Full BoardFlow condition
   - 至少一次 sequential handoff
8. 根据 pilot 结果修订 task design 和 scoring rubric。
9. 撰写课程报告，重点讨论 context continuity、coordination failures 和 protocol overhead。

最小可行版本的成功标准：

- 能复现至少一个 sequential handoff 场景。
- 能观察并记录至少三类 coordination failure。
- 能比较 No BoardFlow baseline 和 Full BoardFlow 的差异。
- 能用自动 checker 捕捉一部分 repo hygiene 或 board consistency 问题。
- 能清楚说明哪些结论已经被 pilot 支持，哪些仍是 TODO。
