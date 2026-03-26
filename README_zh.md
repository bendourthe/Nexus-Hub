# DevAI Hub
**为你的 AI 编码助手提供生产级能力升级**

> **将通用 AI 变成高级工程师。**
> 一键配置 Claude Code (Anthropic)、Gemini (Google)、GitHub Copilot (Microsoft)、Codex (OpenAI)、Cursor 和 OpenCode。

[English](README.md) | 中文

---

## v0.8.9 更新内容

- **分层技能发现** — 每个技能现在都有 L0（一行摘要）和 L1（完整上下文）的分层摘要，支持层级浏览而不会占满上下文窗口。
- **MCP 技能服务器** — 新增 `devai-skill-server` Python 扩展，支持关键词搜索、分类浏览和捆绑工具，实现程序化技能发现。
- **编译技能索引** — `data/SKILL_INDEX.md` 和 `{{SKILL_INDEX}}` 模板占位符自动将完整技能目录注入到 AI 指令文件中。
- **分阶段发布协调器** — `update-version` 命令重构为五个阶段（A-E），带确认关卡和子命令委派。
- **构建工具** — 新增 `Makefile`、`LICENSE`（MIT）、`.pr_agent.toml`，以及 shellcheck/commitizen 预提交钩子。

---

## 快速开始（30 秒配置）

不想手动复制粘贴文件？我们准备了安装器。

1. **克隆或下载** 本仓库。
2. **运行安装器**：
   - **Windows**：双击 **`install.bat`**。
   - **macOS / Linux**：在终端中运行 `./install.sh`。
3. **拖放** 你的目标项目文件夹。
4. **确认** 安装全局技能。
5. **（可选）选择项目** 配置工作区规则。

**完成。**
- **全局**：你的用户配置文件现在拥有所有 163+ Claude 技能、29 个命令、11 个钩子、10 个代理和 Gemini 指令。
- **本地**：你的项目有针对编程语言定制的 `copilot-instructions.md`。

---

## 这是什么？

大多数 AI 助手（Claude、Copilot、ChatGPT）是"通才"，它们知道一切，但精通不了任何一个领域。它们写出的代码尚可，但经常遗漏边界情况、安全问题或你的特定风格。

**DevAI Hub** 是一套"系统指令"和"技能"的集合，注入到你的 AI 中让它变得更聪明。

### 它为你的 AI 提供：
1. **行为规则**："不要只修复错误，要解释*为什么*会发生，并检查安全风险。"
2. **自主技能**："在 Reddit 上进行趋势研究，找到最佳库，然后实现它。"
3. **工作流感知**："当我要求'代码审查'时，按照这个精确的 6 步清单执行。"

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

### 4. Cursor
Cursor IDE 集成。
- 使用安装器从 `templates/ai-instructions/base-cursor.md` 生成 Cursor 兼容指令。

### 5. OpenCode
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
