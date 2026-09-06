# Nexus-Hub
**为你的 AI 编码助手提供生产级能力升级**

> **将通用 AI 变成高级工程师。**
> 一键配置 Claude Code (Anthropic)、Gemini (Google)、GitHub Copilot (Microsoft)、Codex (OpenAI)、Cursor 和 OpenCode。

[English](README.md) | 中文

> **v2.0.0 起原 DevAI-Hub 已重命名为 Nexus-Hub**，与同源项目 [Nexus](https://github.com/bendourthe/Nexus-AI) 对齐。下方 v1.0.0 历史发布说明保留原始名称以反映当时的发布事实。

---

## v1.0.0 更新内容（历史发布说明，当时项目名为 DevAI-Hub）

**首个稳定版本。** 以"反向工程优先"为核心的安全加固 - DevAI-Hub（v2.0.0 起为 Nexus-Hub）现在可在受监管环境中安全使用，专有源代码、提示词和查询文本不会泄露给第三方数据处理服务。版本号从 0.9.7 直接跳至 1.0.0（跳过 0.9.8），反映此次政策层变更的广度。

### 🛡️ 增强的安全能力

- **MCP 注册表政策（含反向工程优先决策树）** ([AGENTS.md](AGENTS.md) + 7 个平台指令文件同步内联)。每个 MCP 注册条目的 `_comment` 现在必须回答 5 问审计（谁运行该进程、出站调用、API 密钥、传输数据、供应商关系）。硬性禁止：搜索即服务、嵌入即服务、抓取即服务、生成即服务。

- **反向工程矩阵** ([docs/policy/mcp-reverse-engineering-matrix.md](docs/policy/mcp-reverse-engineering-matrix.md)) - 对每个曾经考虑过的 MCP 进行权威分类（共 18 行）。驱动保留 / 移除 / 重建决策。

- **发布前安全审查** 发现 3 个 HIGH 和 1 个 MEDIUM 等级的安全问题，全部修复并附带回归测试。详见 [docs/security/penetration-test-2026-04-27.md](docs/security/penetration-test-2026-04-27.md)。

- **消除 pickle 反序列化风险**。`devai-code-search` 现以 JSON 形式持久化索引；恶意构造的索引文件无法在加载时执行任意代码。

- **`devai-web-fetch` 中的纵深 SSRF 防御**：每跳重新校验重定向目标、DNS 钉扎防止重绑定攻击、默认屏蔽 RFC 1918 / 回环 / 链路本地地址。

- **`devai-code-search` 中的符号链接安全遍历器**：索引不可信仓库时，符号链接不会泄露索引根之外的文件。

### 🧰 新内部 MCP 服务器

零出站调用、零 API 密钥、零模型下载。两者均随安装器分发。

- [`devai-code-search`](extensions/devai-code-search/) - 本地代码搜索。关键字检索（倒排索引 + rapidfuzz）、内容哈希增量索引、`.gitignore` + `.devaiignore` 支持、符号链接安全的遍历器。v1.1.0 计划加入密集 / 混合检索。

- [`devai-web-fetch`](extensions/devai-web-fetch/) - 本地 HTTP 抓取 + 可读性提取。每跳 SSRF 防护、DNS 钉扎、手动重定向处理。仅支持单 URL；无第三方中介。

### 📚 新技能

- `code-semantic-search` - `rag-implementation` 的代码语料专门化版本，引用内部 `devai-code-search` MCP 作为参考实现（无外部归属）。

- `ui-component-generation` - LLM 原生方式替代外部 UI 组件生成服务（替代 `magic-ui` 类 MCP）。

- `local-docs-lookup` - 库 / API 问题的 7 步本地查找序列（自省 -> vendored README -> 内置文档 -> 类型存根 -> 项目文档 -> man pages -> 用户批准的单一 URL，通过 `devai-web-fetch`）。替代 `context7` 类 MCP。

### ⚙️ 命令与工作流改进

- **`/run-deep-review` 命令** - 全新的 12 阶段发布前深度审查协调器。串联已知缺陷收集、健康检查（测试执行 + 80% 行覆盖率阈值）、依赖扫描、文档 / git / CI/CD / 发布就绪卫生检查、项目验证器、`/analyze-codebase`、`/run-security-audit`、`/run-penetration-test --depth=deep` 和 `/review-codebase`。将所有结果合并为一份按 P0/P1/P2/P3 严重度排序的报告，附带 GO / GO-WITH-CONDITIONS / NO-GO 的发布判断。

- **`/compare-project` 第 9 节"安全与风险评估"** - 强制性章节，在生成任何采纳计划之前评估威胁建模、逐项风险评分、反向工程可行性与推荐排序。链入 `/generate-plan` 时始终传递 `reverse-engineer-first=true`，使生成的计划按 skill-native 优先 -> RE 重建 -> 受信任供应商封装（含合理化论证）的顺序排序。

- **内部 MCP 基准测试套件** - `make benchmark` 运行 `scripts/devai_mcp_benchmark.py` 测试三个内部 MCP 的延迟。本地 MCP 测试阶段会拒绝任何出站套接字连接。

- **样式指南文件迁出 `catalog/commands/`** 移至 `catalog/style-guides/`（同级目录）。它们不再出现在斜杠菜单中，避免 `/compile-deep-research-style-guide` 与 `/generate-report-style-guide` 与各自的父命令并列时造成视觉干扰。

- **生成文档的 Markdown 样式指南** ([catalog/style-guides/markdown.md](catalog/style-guides/markdown.md)) - 规范化的格式参考（空行规则、嵌套缩进规则、列表中代码块规则、ASCII 规则）。从 `AGENTS.md` 引用，代理在每次会话开始时即可获得该规则。

### 💥 破坏性变更

- **移除 4 个第三方 MCP 注册条目**：`context7`（Upstash 搜索即服务）、`exa-web-search`（Exa 搜索即服务）、`firecrawl`（抓取即服务）、`magic-ui`（21st.dev 生成即服务）。仍依赖这些条目的用户可手动添加到自己的 `.claude/settings.json` 中；DevAI-Hub 不再提供这些片段。

- **从斜杠菜单移除两个命令**：`/compile-deep-research-style-guide` 与 `/generate-report-style-guide`。父命令 `/compile-deep-research` 与 `/generate-report` 不受影响。

- **`/generate-implementation-plan` 弃用别名已移除**。请直接使用 `/generate-plan`。

完整计划：[docs/archives/v1/v1.0/plans/security-hardening-v100.md](docs/archives/v1/v1.0/plans/security-hardening-v100.md)。详细发布说明：[docs/archives/v1/v1.0/RELEASE_NOTES.md](docs/archives/v1/v1.0/RELEASE_NOTES.md)。

---

## 快速开始（一条命令）

打开终端，粘贴适合你系统的一条命令即可安装 - 无需下载、解压或 `cd`。

1. **打开终端**（macOS：用 Spotlight 搜索 Terminal；Windows：在开始菜单搜索 PowerShell；Linux：按 Ctrl+Alt+T）。
2. **粘贴并运行一条命令**：
   - **macOS / Linux**：`curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`（没有 curl 就用 `wget -qO-`）。
   - **Windows**：`irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`。
3. **就这样，没有任何提问。** 安装器会下载技能目录、预检依赖，并对检测到的每个受支持助手执行全局安装；你没有的助手会被跳过并附带说明，你的自定义内容会被保留。之后可运行 `nexus-hub upgrade` 就地更新。

**完成。**
- **全局**：你的用户配置文件现在拥有所有 256 个 Claude 技能、15 个命令、23 个钩子、23 个代理，以及 Gemini 和 Codex 指令。
- **本地**：你的项目有针对编程语言定制的 `copilot-instructions.md`。

---

## 这是什么？

大多数 AI 助手（Claude、Copilot、ChatGPT）是"通才"，它们知道一切，但精通不了任何一个领域。它们写出的代码尚可，但经常遗漏边界情况、安全问题或你的特定风格。

**Nexus-Hub** 是一套"系统指令"和"技能"的集合，注入到你的 AI 中让它变得更聪明。

### 它为你的 AI 提供：
1. **行为规则**："不要只修复错误，要解释*为什么*会发生，并检查安全风险。"
2. **自主技能**："在 Reddit 上进行趋势研究，找到最佳库，然后实现它。"
3. **工作流感知**："当我要求'代码审查'时，按照这个精确的 6 步清单执行。"

---

## 🎯 推荐工作流

Nexus-Hub 提供两个有主张的端到端工作流。可作为起点，再根据你的项目调整。

### 全新项目工作流（5 个阶段）

以 AI 编码代理作为主要伙伴从零构建项目。

#### 1. 规划

打开 AI 聊天工具（Claude.ai 或 ChatGPT），头脑风暴：要解决的问题、目标用户、核心功能、技术栈、约束条件。会话结束时，让聊天工具生成一份结构化的 Markdown 实施计划 - 包含多个阶段，每个阶段下包含若干子任务，每个子任务携带一段独立完整的提示词，可由代理直接执行。

#### 2. 项目设置

1. 创建 Git 仓库与三层分支模型：`main` / `develop` / `feature/*`。

2. 安装 Nexus-Hub 工具包 - 粘贴适合你系统的一条安装命令（见上方"快速开始"）。

3. 在 Claude Code 中运行 `/setup-project` - 通过 8 个引导阶段自动生成 `CLAUDE.md`、目录结构、`.gitignore`、`README.md`、`DEVLOG.md` 和 `CHANGELOG.md`。

4. 将第 1 步生成的实施计划保存至 `docs/<version>/plans/<slug>.md`。

5. 运行 `/generate-commit-message` 提交。

#### 3. 开发（核心循环）

对计划中的每个阶段：

1. 创建特性分支：`feature/phase-N-short-description`。

2. 开启全新的 Claude Code 会话。

3. 运行 `/implement-phase <slug> <phase>` - 该命令会逐个执行子任务、生成并运行测试、修复问题、运行 `/update-gitignore` + `/update-documentation`、生成会话历史文件并产出提交消息。

4. 提交并推送特性分支。

5. 合并到 `develop`。然后进入下一个阶段。

#### 4. 质量保证（发布前）

1. 运行 `/run-deep-review` - 一个 12 阶段的协调器，串联已知缺陷收集、健康检查、依赖扫描、文档与 git 卫生检查、项目验证器、`/analyze-codebase`、`/run-security-audit`、`/run-penetration-test --depth=deep` 和 `/review-codebase`。

2. 阅读综合报告 - 它会生成一份按 P0 / P1 / P2 / P3 严重度排序的发现列表，附带 GO / GO-WITH-CONDITIONS / NO-GO 的发布判断。

3. 在发布前修复所有 P0 与 P1 问题。P2 问题可推迟到补丁版本；P3 问题为建议性。

4. 运行 `/generate-sbom` 生成合规文档。

#### 5. 发布

1. 运行 `/update-version` - 协调版本检测、目录布局清理、`.gitignore` 审计、所有配置文件中的版本号更新、CHANGELOG 迁移、文档同步以及 DEVLOG 条目。

2. 将 `develop` 合并到 `main`，打标签，推送。

### 继承项目工作流（2 个阶段）

适用于继承的项目或需要审计的项目。

#### 1. 初步分析与深度审查

1. 克隆仓库，在 VS Code 中打开，开启 Claude Code 会话。

2. 运行 `/run-deep-review` - 与全新项目工作流第 4 阶段相同的 12 阶段协调器。综合报告中的优先级路线图（P0 / P1 / P2 / P3）即成为你的初始任务积压。

3. 如果文档稀缺，可补全：`/generate-readme`（如缺失）、`/generate-changelog`（基于 git 历史）、`/generate-devlog`、`/refactor-project-layout`（仅当存在结构性问题）。

4. 如尚未存在则建立 `develop` 分支。

5. 提交分析产出。

#### 2. 进行变更

对每次变更：

1. 在聊天工具中头脑风暴，然后运行 `/generate-plan` 生成结构化实施计划，保存至 `docs/<version>/plans/<slug>.md`。

2. 对每个阶段运行 `/implement-phase <slug> <phase>` - 与全新项目工作流的开发循环完全相同。

3. （可选）使用 git worktree 进行并行工作（例如：在开发新特性的同时修复关键安全 bug）：

    ```bash
    git worktree add ../project-fix feature/security-fix
    # 在另一个 Claude Code 会话中工作，完成后：
    git worktree remove ../project-fix
    ```

4. 当所有变更合入 `develop` 后，再次运行 `/run-deep-review` 验证未发生回归，然后运行 `/update-version` 并合并到 `main`。

QA 与发布步骤与全新项目工作流完全相同。

---

## 手动使用方法

如果你更喜欢自己复制文件，以下是仓库的组织方式：

### 1. Claude Code (Anthropic)
最强大的集成方式，添加**自主代理能力**。
- **CLAUDE.md**："大脑"。将 `catalog/CLAUDE.md` 复制到项目根目录并自定义。
- **技能**："双手"。将 `catalog/skills/` 中的文件夹复制到项目的 `.claude/skills/` 目录。

### 2. Gemini (Google)
为 Google Gemini 模型优化的指令。
- 将 `templates/ai-instructions/generic-instructions.md` 复制到项目或用户配置文件的 `.gemini/GEMINI.md`。

### 3. GitHub Copilot (Microsoft)
VS Code Copilot Chat 的指令。
- 将 `templates/ai-instructions/coding-instructions/{language}.md` 复制到 `.github/copilot-instructions.md`。

### 4. Codex (OpenAI)

OpenAI Codex CLI 集成。Codex 读取项目根目录的 `AGENTS.md`（开放标准，Cursor / Aider / Jules 也遵循该约定）以及位于 `~/.codex/` 的用户级配置。

- **AGENTS.md**：将 `templates/ai-instructions/base-codex.md` 的内容复制到项目的 `AGENTS.md`。
- **技能与提示词**：安装器会将 `catalog/skills/` 镜像到 `~/.codex/skills/`，并将 `catalog/commands/` 镜像到 `~/.codex/prompts/`。手动配置时，将这两个目录树复制到对应位置即可。

### 5. Cursor
Cursor IDE 集成。
- 使用安装器从 `templates/ai-instructions/base-cursor.md` 生成 Cursor 兼容指令。

### 6. OpenCode
OpenCode IDE 集成。
- 使用安装器从 `templates/ai-instructions/base-opencode.md` 生成 OpenCode 兼容指令。

---

## 精选技能

| 技能 | 功能 |
|------|------|
| **架构设计** | 系统分解、ADR、C4 图和适应性函数。 |
| **AI 代理开发** | 构建带工具使用、记忆系统和多代理编排的代理。 |
| **RAG 实现** | 端到端 RAG 管道，包含分块、嵌入和评估。 |
| **API 设计** | REST、GraphQL 和 gRPC 设计，含版本管理和错误处理。 |
| **代码审查** | 合并前的 6 步深度审查（安全、性能、逻辑）。 |
| **测试生成** | 使用 AAA 模式和 mock 编写全面的单元测试。 |
| **E2E 测试** | Playwright/Cypress 自动化，含页面对象和 CI 集成。 |
| **合规检查** | 根据 SOC2、GDPR 和 ISO 标准检查代码。 |
| **趋势研究** | 研究 Reddit/X 近 30 天的趋势，编写提示词。 |
| **Vue 专家** | 使用 Composition API、Pinia 和 Vue Router 构建 Vue 3 应用。 |
| **Android 开发** | 使用 Kotlin、Jetpack Compose 和 Material Design 3 构建 Android 应用。 |
| **iOS 开发** | 使用 Swift、SwiftUI 和 UIKit 构建 iOS 应用。 |
| **PDF 文档生成** | 使用 ReportLab、WeasyPrint 或 Puppeteer 生成专业 PDF。 |

[→ 查看完整技能目录](catalog/skills/README.md)

---

## 使用量监控

三种互补方式跟踪你的 Claude Code 使用限制：

### CLI 使用量显示（自动）
Stop 钩子在每次 Claude Code 响应后直接在终端显示使用限制。低于 50% 时静默。

### VS Code 扩展
从 VS Code 状态栏监控使用量，带完整仪表板。

### `/check-usage` 命令
按需详细使用报告，带模型切换建议。

---

## 贡献

发现了更好的提示词？更智能的规则？欢迎提 PR！我们致力于构建 AI 编码的终极知识库。

---

## 许可证

MIT
