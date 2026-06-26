# Automation Instructions（复制到 Cursor Automation）

> Cloud Agent **读不到** `~/.agents/skills/`。二选一：

## 方案 A：绑定 git 仓库（推荐，易维护）

Automation 配置 **Git 仓库** = `brian512/script_tools`（或你的 fork），分支 `main`。

Instructions：

```text
执行「满满」每日工作回顾。

先 Read 仓库内文件（路径相对于 checkout 根目录）：
1. .cursor/skills/lark-workflow-daily-review/SKILL.md
2. .cursor/skills/lark-workflow-daily-review/references/data-sources.md
3. .cursor/skills/lark-workflow-daily-review/references/lark-auth.md

然后严格按 SKILL 执行。硬性约束：
- 只用 lark-cli task（禁止 aily-task / MCP）
- 排期表 workbook-export 用 ./yoho_schedule.csv 相对路径
- 技术规划无「预计完成日期」不传 --due
- 失败报错停止，不得仅写报告交付
```

## 方案 B：自包含（不依赖 Read 文件）

把 `agent-instructions.md` 中 `---` 之间的全文直接粘贴进 Instructions，不 Read 任何 skill 文件。
