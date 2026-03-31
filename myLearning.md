## week1
### k-shot/few-shot
问题：反转字符串 httpstatus
- 模型太小或推理能力弱，无法完成任务：使用qwen:7b 就很难完成 k_shot 的字符串反转的任务，而用 deepseek:8b 就比较容易。
(没有提示词)直接把问题通过聊天界面给deepseek:8b，跑了几十分钟也终止不了，最后它思考的内容已经偏离到跟原始任务基本没关系了。
- 字符串越长、任务越难：模型可能尝试理解字符串中的语义。长度大于10之后deepseek:8b可能就搞不定了（结果不对，或者运行几十分钟无结果），长度10对qwen7b就很难搞定了。
- temperature 越小，结果越稳定。
- 提示词主要是给出例子，其它描述影响不大。

k_shot/few-shot 原理：给 k 个示例=把“任务定义+输出模板”放进上下文，模型在推理时做 in-context learning（不改参数），通过模式补全把当前输入对齐到示例中的变换/推理轨迹/格式约束。示例既提供规则也提供边界（允许什么、不允许什么），会显著改变输出分布。效果取决于：示例是否无歧义且覆盖关键变体/反例、与目标输入的结构相似度、示例顺序与一致性（近因效应/格式漂移）、以及提示里是否显式要求“只输出答案/固定格式”。常见失败：示例过少导致歧义、示例风格不一致、过拟合示例细节或夹带解释文字；可用增加对比示例/反例、统一格式、把规则上移到 system prompt 来改善稳定性。

k_shot 教学目标总结：
用 few-shot 示例让模型学会“字符串反转”，并严格按格式只输出答案。设计：把示例放 system prompt 提升优先级；用户提示写死 ONLY output 防多话；用 EXPECTED_OUTPUT 精确匹配做可重复评测；多次运行+温度检验稳定性；取最后一行做轻容错但仍要求干净输出。

### chain of thought
问题：what is 3^{12345} (mod 100)?
- 没有提示词，deepseek-r1:8b运行10分钟没结果


---
## week2
### 简单的前后端项目
web框架：FastAPI 
数据库：SQLite
测试框架： pytest
异步服务：uvicorn

### 自我练习
将文章提取改造成为需求分析和测试因子提取，增加一些


---
# Week 3 — Build a Custom MCP Server


---
# Week 4 — SubAgent

### Build Your Automation (Choose 2 or more)
SubAgents are specialized AI assistants configured to handle specific tasks with their own system prompts, tools, and context. Design two or more cooperating agents, each responsible for a distinct step in a single workflow.

- Example 1: TestAgent + CodeAgent
  - Flow: TestAgent writes/updates tests for a change → CodeAgent implements code to pass tests → TestAgent verifies.
- Example 2: DocsAgent + CodeAgent
  - Flow: CodeAgent adds a new API route → DocsAgent updates `API.md` and `TASKS.md` and checks drift against `/openapi.json`.
- Example 3: DBAgent + RefactorAgent
  - Flow: DBAgent proposes a schema change (adjust `data/seed.sql`) → RefactorAgent updates models/schemas/routers and fixes lints.


### 交付件 A write-up `writeup.md` under `week4/` that includes:
  - Design inspiration (e.g. cite the best-practices and/or sub-agents docs)
  - Design of each automation, including goals, inputs/outputs, steps
  - How to run it (exact commands), expected outputs, and rollback/safety notes
  - Before vs. after (i.e. manual workflow vs. automated workflow)
  - How you used the automation to enhance the starter application


---
# Week 5 — SubAgent
### Warp
Warp 将自己定位为“Agentic Development Environment（代理型开发环境）”，它不再只是一个传统的终端，而是一个集成了强大 AI 代理、现代化编辑器功能，并能覆盖软件开发生命周期全流程的统一开发平台。
Warp 的目标是将 IDE 的能力与 CLI 的灵活性融合，由 AI 代理（Agent）作为核心执行单元，极大地扩展了传统终端能做的事情。
- 不只是终端：它拥有现代化的编辑器界面，支持文件树、代码高亮、LSP（语言服务器协议）等 IDE 级特性。
- 代理为核心：内置了名为 Oz 的先进代理，并允许你在同一个终端里无缝调用 Claude Code、Codex、Gemini CLI 等其他主流代理。

### Vercel
Vercel 将自己定位为 AI Cloud（AI 云）——一个专为现代前端和全栈应用打造的一体化平台。它不仅能把你的代码在全球范围内快速部署，更提供了一整套针对 AI 应用开发的工具链和基础设施


---
# Week 6 — Scan and Fix Vulnerabilities with Semgrep

Semgrep 是一个现代化的静态代码分析平台，定位于将语义级代码搜索与安全审计能力相结合，帮助开发者和安全团队在编码、提交和 CI/CD 阶段高效发现并修复代码中的漏洞、质量问题及硬编码密钥。

- Semgrep Code (SAST)：静态应用安全测试，用于检测第一方代码中的安全漏洞、逻辑错误和编码规范问题。
- Semgrep Supply Chain (SCA)：软件成分分析，检测项目所依赖的开源库中是否存在已知漏洞。
- Semgrep Secrets：密钥检测，识别代码中意外硬编码的 API 密钥、密码、Token 等敏感凭证。


---
# Week 7 – Exploring AI Code Review Using Graphite
Graphite 的 AI Code Review 是一套深度集成在开发流程中的智能代码审查解决方案。它不仅仅是简单的"找错"，而是通过 Graphite Agent（AI 审查代理）和 Graphite Chat（对话式协作）两大核心组件，将代码审查从被动的"等待反馈"转变为主动的"协作改进"，帮助团队在不增加认知负担的前提下，高效处理由 AI 生成或人工编写的大量代码变更。同类产品中，[CodeRabbit](https://www.coderabbit.ai/) 更偏「PR 专用 AI 审查员」；下文有 **Graphite 与 CodeRabbit 对比**。

在 AI 使代码/MR 产能暴涨的背景下，业界更成熟的做法通常是：把 Review 从“纯人工逐行阅读”升级为“自动化门禁 + 人工高价值判断”的分层流程。

## 常用的 Code Review 工具（业界实践）
- **PR 编排/拆分（降低认知负担）**：
  - **Graphite / stacked diffs**：将大改动拆分为可 Review 的堆叠 PR，减少单次 review 的上下文与等待成本（参考：[Benefits of stacked diffs in code review](https://www.graphite.com/guides/benefits-of-stacked-diffs-in-code-review)；[Stacked Diffs (and why you should know about them)](https://newsletter.pragmaticengineer.com/p/stacked-diffs)）。
- **规模化审查路由（把“该谁审”制度化）**：
  - **CODEOWNERS**：将关键模块绑定到 owner，自动请求审查、并可与分支保护结合形成“必须 owner 批准才能合并”的机制（参考：[GitHub — About code owners](https://docs.github.com/articles/about-code-owners)；[GitLab — Code Owners](https://docs.gitlab.com/ee/user/project/codeowners/index.html)）。
- **自动化质量门禁（把机械问题前移）**：
  - **lint/format/typecheck/test**：用 pre-commit/CI 把格式、静态检查与基础正确性在进入人工 review 前拦截。
  - **安全扫描**：SAST/Secrets/SCA（如 Semgrep、CodeQL、依赖漏洞扫描）作为“禁止类问题”的硬门槛。
- **AI 辅助 Review（作为第二双眼）**：
  - 常见模式是让 AI 提供“变更摘要、潜在风险、建议测试点”，用来加速 reviewer 定位重点，但最终决策仍由代码 owner/人类负责。

## 面对 AI 高产的 Review 最佳实践（可落地）
- **分层 Review（L0→L2）**：
  - **L0 自动门禁**：lint/format、类型检查、单测、SAST/Secrets/SCA、覆盖率阈值（不通过直接退回）。
  - **L1 轻量人工**：重点看 PR 描述是否清晰、风险是否识别、是否给出测试证据与回滚方案。
  - **L2 深度人工（仅高风险变更）**：权限/鉴权、资金/计费、数据迁移、并发一致性、可观测性等。
- **强制“小 PR + 好描述”**：AI 易一次改太多，成功团队通常用模板约束：动机、范围、非目标、测试步骤/结果、风险与回滚（参考：[Google — The CL author’s guide](https://google.github.io/eng-practices/review/developer/)；[GitHub Docs — Helping others review your changes](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes)）。
- **“可 Review 的代码”原则**：把一次改动拆成单一意图、避免混合格式化与逻辑修改，提升审查吞吐（参考：[Phabricator — Writing Reviewable Code](https://secure.phabricator.com/book/phabflavor/article/writing_reviewable_code/)）。
- **让测试成为主要审查对象**：当 AI 产出代码量指数增长，扩展审查能力最稳的方式是把“测试质量”当作合约：覆盖关键路径与失败模式、明确断言与边界条件。

### Graphite 简介：前置条件、原理、使用过程与费用
Graphite 是一套面向 GitHub 工作流的工程协作工具，核心卖点是 **stacked PR（堆叠式 PR）** 与配套的 **AI Review / Chat**，用于提升“高吞吐 PR 时代”的可审查性与合并效率（参考：[The stacking workflow](https://graphite.com/stacking)）。

#### 前置条件 / 准备过程
- **平台前提**：Graphite 的集成主要围绕 **GitHub**，通常需要安装 **Graphite GitHub App** 或使用 GitHub Token 完成授权（参考：[Authenticate With GitHub — Graphite](https://www.graphite.com/docs/authenticate-with-github-app)；[AI reviews setup](https://graphite.com/docs/ai-reviews-setup)）。
- **权限前提**：若要在组织层面开启 AI reviews/规则，往往需要组织管理员或具备相应仓库管理权限的账号完成安装与配置。
- **本地工具（可选但常用）**：Graphite CLI（`gt`）用于创建/同步堆叠分支与 PR。官方提供 Homebrew/npm 安装与 `gt auth` 登录流程（参考：[Install & Authenticate The CLI](https://graphite.com/docs/install-the-cli)）。

#### 大致原理（为什么能提升 Review 吞吐）
- **把“大改动”拆成“可 Review 的小片段”**：通过 stacked diffs 将一个 feature 拆成多个依赖的 PR，reviewer 每次只需要理解一层意图，显著降低认知负担与等待成本（参考：[Benefits of stacked diffs in code review](https://www.graphite.com/guides/benefits-of-stacked-diffs-in-code-review)）。
- **合并队列化**：堆叠 PR 可按顺序合并，Graphite 提供“按栈合并”的工作流与工具支持，减少手工 rebase/串联操作带来的摩擦（参考：[Merge Pull Requests — Graphite](https://graphite.com/docs/merge-pull-requests)）。
- **AI Review 的定位**：Graphite Agent 通常以“自动评论 PR、提示潜在问题与测试建议”的方式工作，作用类似“第二双眼 + 阅读加速器”，与 CI/测试门禁互补（参考：[How AI code review works](https://graphite.com/guides/how-ai-code-review-works)）。

#### 使用过程（典型团队落地路径）
- **启用与配置**：安装 GitHub App → 选择启用 AI review 的仓库/组织 → 配置 Rules & exclusions（哪些目录不审、哪些规则更严格）（参考：[AI reviews setup](https://graphite.com/docs/ai-reviews-setup)）。
- **开发与提 PR**：用 `gt` 创建/管理堆叠分支与 PR（例如先提交基础重构 PR，再在其上叠功能 PR），让每个 PR 保持“小、单一意图、可独立审查”。
- **Review 与合并**：reviewer 按层审阅；CI 通过后按栈顺序合并；作者同步本地分支（常见是 `gt sync`）以保持栈一致。

#### 是否收费 / 费用要求
Graphite 提供免费与付费档位，差异通常体现在团队协作能力、AI reviews/Chat 的配额与组织级能力上。定价以官方页面为准（参考：[Graphite Pricing](https://graphite.com/pricing)；[Billing & plans](https://graphite.com/docs/billing-plans)）。

### Graphite 与 CodeRabbit 对比
两者都提供 **PR 上的 AI 辅助审查**，但产品重心不同，可并行使用（Graphite 管「怎么拆 PR、怎么合并」，CodeRabbit 管「谁来自动挑问题」）。

| 维度 | Graphite | CodeRabbit |
|------|----------|------------|
| **产品定位** | 以 **GitHub PR 工作流** 为中心的一体化平台：stacked PR、`gt` CLI、PR inbox、merge queue、AI Review / Chat，并与 Cursor 生态有产品整合（见 [Graphite 官网](https://graphite.com/)） | 以 **AI 代码审查** 为核心：在 PR 上自动总结 diff、行级评论、与机器人对话迭代；偏「审查员即服务」（见 [CodeRabbit](https://www.coderabbit.ai/)、[文档](https://docs.coderabbit.ai/)） |
| **代码托管** | 深度绑定 **GitHub**（安装 GitHub App / Token 授权） | 官方支持多种宿主（如 GitHub、GitLab 等，具体以 [CodeRabbit 文档](https://docs.coderabbit.ai/) 为准） |
| **独有能力** | 堆叠式 PR 编排、栈感知的合并与同步、团队级 review 收件箱与指标；AI 是工作流的一环 | 强调 PR 级 walkthrough、与静态分析/安全等工具链的集成、IDE/CLI 侧接入（以官方功能说明为准） |
| **典型选型** | 团队痛点是 **大 MR、串行等待、合并冲突、需要「拆小 + 按序合」** | 团队痛点是 **希望每个 PR 自动多一双眼、少漏 bug/安全点**，且宿主不一定是 GitHub |

**简要结论**：Graphite 解决的是 **审查与合并的「流程与结构」**；CodeRabbit 解决的是 **单次 PR 的「自动审查深度与覆盖面」**。若已在 GitHub 上用 Graphite 拆栈，仍可加装 CodeRabbit 做 AI 评论层（需注意两套 bot 的评论噪音与规则配置，避免重复刷屏）。



---
# Week 8 – Multi-Stack AI-Accelerated Web App Build
At least one version must be created using [`bolt.new`](https://bolt.new/), an AI app generation platform. 
At least one version must use a non-JavaScript language for either the frontend or backend (e.g., Django, Ruby on Rails).

## Minimum Functional Scope 
- User can create, read, update, and delete a primary resource (e.g., notes, tasks, posts).
- Persistent storage (database or file-based) where appropriate for the stack.
- Basic validation and error handling.
- Simple but functional UI that surfaces the main flows.
- Clear instructions to run each version locally (and deploy links if you deploy).

## Stack Requirements
Build 3 separate versions of the same app, each of which use a distinct stack. Examples:
- MERN (MongoDB, Express, React, Node.js)
- MEVN (MongoDB, Express, Vue.js, Node.js)
- Django + React (or Vue)
- Flask + Vanilla JS (or React)
- Next.js + Node (or NestJS)
- Ruby on Rails (full-stack)

### Bolt.new
Bolt.new 是由 StackBlitz 团队推出的一款革命性 AI 驱动开发平台。它的核心能力是：让你仅用自然语言对话，在浏览器中直接生成、运行、修改并一键部署一个完整的全栈 Web 应用。
Bolt.new的WebContainers：它在你的浏览器内部直接模拟了一个完整的Node.js操作系统。这意味着，当AI生成代码后，它能立即在浏览器沙箱中执行npm install、启动开发服务器，并在右侧屏幕提供实时预览。整个过程无需任何本地环境配置，完全在网页中完成。

