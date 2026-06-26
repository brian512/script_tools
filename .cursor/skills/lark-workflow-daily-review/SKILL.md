---
name: lark-workflow-daily-review
version: 1.0.0
description: "每日工作回顾：并行拉取飞书消息、文档评论、排期表/多维表格、日程，整理【前一个工作日+今天】的已完成/待办，去重后同步飞书任务并按日期分组。适用于每日早报、工作日复盘、/daily-review 或定时自动化触发。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 每日工作回顾工作流

**CRITICAL — 认证规则读 [`references/lark-auth.md`](references/lark-auth.md)**（Cloud 无 `~/.agents/skills/lark-shared`）

## 文件路径（按运行环境）

| 环境 | SKILL 路径 | data-sources 路径 |
|------|-----------|-------------------|
| **Cloud Automation** | `.cursor/skills/lark-workflow-daily-review/SKILL.md` | `.cursor/skills/lark-workflow-daily-review/references/data-sources.md` |
| 本地 Cursor Agent | `~/.agents/skills/lark-workflow-daily-review/SKILL.md` | 同上（`~/.agents/...`） |

Cloud 容器内 **`~/.agents/skills/` 不存在**，不要 Read 该路径。Automation 必须先 checkout 含本 skill 的 git 仓库（如 `script_tools`），再 Read **仓库内**相对路径。

## 工具硬性约束（Automation / Cloud 必读）

| 能力 | 唯一正确方式 | 禁止 |
|------|-------------|------|
| 飞书任务 | `lark-cli task +create` / `+complete` / `+update` / `+search` | **禁止** `aily-task`、Aily MCP、飞书任务 MCP |
| 日程 | `lark-cli calendar +agenda` | **禁止** `aily-calendar` |
| 排期表导出 | `lark-cli sheets +workbook-export --output-path ./yoho_schedule.csv` | **禁止** `/tmp/...`、`/home/...` 等绝对路径 |
| Markdown 报告 | Cursor **Write 工具** 写 `artifacts/daily_review_*.md` | 不要用 `lark-cli` 写报告文件 |

找不到 `lark-cli` 或 `task +create` 失败时：**报错停止**，不得改写成「仅以报告交付」。

`+workbook-export` 的 `--output-path` **必须是当前工作目录下的相对路径**（如 `./yoho_schedule.csv`）。导出前 `cd` 到 workspace 根目录；失败提示 `unsafe output path` 时改用 `./文件名`。

## 适用场景

- 「每日早报」「工作日复盘」「帮我整理这两天的工作」
- Cursor Automation 定时触发（周一至周五 09:30）
- `/daily-review` 手动触发

## 身份与常量

仅支持 **user 身份**（`--as user`）。

| 常量 | 值 |
|------|-----|
| 花名 | 满满 |
| open_id | `ou_f515587a96cf38096db988e9106b0975` |
| user_id | `7004656958481416194` |

执行前确认 `lark-cli auth status` 中 user 身份可用；`openId` 与上表不一致时以 `auth status` 为准。

数据源 token、字段名、filter-json 见 [`references/data-sources.md`](references/data-sources.md)。

## Step 0：预检（必须先过）

按顺序执行，任一失败则按 [排障](#排障) 处理后再继续，**不要带着权限错误硬跑后半段**。

```bash
# 1. CLI 存在
which lark-cli && lark-cli --version

# 2. 身份
lark-cli auth status --as user

# 3. 任务子命令可用（确认不是去找 aily-task）
lark-cli task +create --help >/dev/null
```

缺 scope 时走 [`lark-auth.md`](references/lark-auth.md) 设备码授权：先 `--no-wait --json` 把 `verification_url` 给用户，**本轮结束**；用户确认扫码后，下轮执行 `auth login --device-code <code>` 换票，再从头预检。

Automation 首次部署前建议人工跑一遍预检并完成增量授权，避免定时任务卡在扫码。

## 时间范围

### 前一个工作日（`PREV_WORKDAY`）

从 **前一个工作日 00:00（Asia/Shanghai）** 起算：

| 今天 | 前一个工作日 |
|------|-------------|
| 周一 | 上周五 |
| 周二 | 昨天（周一） |
| 周三 | 昨天（周二） |
| 周四 | 昨天（周三） |
| 周五 | 昨天（周四） |

**跳过规则**：周六、周日、法定节假日不视为工作日。跨周末时只覆盖工作日区间。

节假日：无官方 API 时，仅跳过周末；若用户维护了节假日列表则一并跳过。

### 截止

**今天当前时间**（`NOW`）。

### ISO 时间窗

```text
START = PREV_WORKDAY 00:00:00+08:00
END   = NOW（ISO 8601 +08:00）
TODAY = 今天日期 YYYY-MM-DD
```

## 工作流总览

```text
计算 PREV_WORKDAY / START / END
        │
        ├─► [并行] 数据源 1–4 全部拉取
        │
        ├─► 归一化为 WorkItem 列表
        │
        ├─► union + 去重（多源合并，标注来源）
        │
        ├─► 分类：已完成 ✅ / 待办 🔥 + P1/P2/P3
        │
        ├─► 同步飞书任务（按日期分组）
        │
        └─► 输出：消息摘要 + markdown 报告
```

## Step 0.1：计算工作日

根据当前日期（Asia/Shanghai）推算 `PREV_WORKDAY` 与 `TODAY`，生成 `START`、`END`。

## Step 1：并行拉取数据源

**必须并行**执行以下四路，避免串行漏数据。

### 1.1 飞书消息

#### A. 群聊 @我

```bash
lark-cli im +messages-search \
  --is-at-me \
  --chat-type group \
  --start "<START>" --end "<END>" \
  --page-all --format json
```

- **排除 @all 作为待办**：正文含 `@_all` / `@all` / `@所有人` 且无需个人跟进的，标【无需回复】，不入待办。
- 其余 @我 消息提取行动项。

**消息降噪**（表格已覆盖的卡片通知直接跳过，避免重复建任务）：

| 模式 | 处理 |
|------|------|
| `CR Report` / `技术规划延期提醒` 卡片 | 跳过（已由 CR 看板 / 技术规划表覆盖） |
| 纯 `@_all` 广播（如技术中心通知） | 【无需回复】 |
| 含明确 `@满满` 且带问题/确认语义的 | 纳入待办 |

`+messages-search` 返回列表在 `data.messages`（不是 `data.items`）。私聊 175 条量级时只提取含 @我、明确问句、或 thread 跟进的条目，不要全量建任务。

#### B. 活跃 thread / topic

```bash
# 时间窗内我发送过的群消息（含 thread 入口）
lark-cli im +messages-search \
  --sender ou_f515587a96cf38096db988e9106b0975 \
  --chat-type group \
  --start "<START>" --end "<END>" \
  --page-all --format json
```

对「我发送过的群消息」返回中带 `thread_id` 的条目，去重后拉完整 thread：

```bash
lark-cli im +threads-messages-list --thread-id <thread_id> --page-all --as user
```

纳入：我发起或参与回复的 thread；含我消息前后的上下文回复。thread 与 @我 消息重复时合并为一条。

#### C. 私聊 / 单聊

```bash
lark-cli im +messages-search \
  --chat-type p2p \
  --start "<START>" --end "<END>" \
  --page-all --format json
```

**必须展示对方花名/昵称**：用结果中的 `chat_name` 或 `sender_name`；禁止用 `chat_id` 代替。缺失时调用 `lark-cli contact +resolve --query <open_id>` 补全。

### 1.2 飞书文档 @我的评论

```bash
# 时间窗内我收到/相关的文档评论
lark-cli drive +search \
  --query "满满" \
  --only-comment \
  --commented-since "<PREV_WORKDAY>" \
  --format json --page-all
```

对命中文档逐个拉评论：

```bash
lark-cli drive file.comments list \
  --params '{"file_token":"<token>","page_size":50}' \
  --as user
```

筛选 @满满 / 当前用户 open_id 的评论；记录文档标题、评论摘要、时间、文档 URL。

### 1.3 排期表 / 任务表

三张表 **并行**读取，筛选负责人/处理人/指派人 = 满满 或 user_id = `7004656958481416194`：

| 表 | URL | 类型 |
|----|-----|------|
| Yoho 排期表 | `https://micoworld.feishu.cn/wiki/wikcnQdImFbIxMozD7qO60TBBZb` | sheet |
| 技术规划 | `https://micoworld.feishu.cn/wiki/K0pJwPAzbiRvHPkxzgucZnu9nne?table=tblezrNOKPrfc5CQ&view=vewXxBNTOK` | bitable |
| CR 管理-未解决看板 | `https://micoworld.feishu.cn/wiki/YBnJw8jkRinzNBkHRyTcb4MYnee?table=tbl6U9BbxbZ9FwLi&view=vewNUO06So` | bitable |

**Sheet（Yoho 排期表）**：

排期表按版本分 sheet（如 `V5.45`）。先解析 wiki 节点拿到 `obj_token`，再导出当前版本 sheet 为 CSV（该表 `+cells-get` 可能返回空，**以 export 为准**）：

```bash
# wiki → spreadsheet token
lark-cli wiki +node-get --node-token "https://micoworld.feishu.cn/wiki/wikcnQdImFbIxMozD7qO60TBBZb" --as user

# 列出版本 sheet，取最新有数据的 V5.xx 的 sheet_id
lark-cli sheets +workbook-info --spreadsheet-token <obj_token> --as user

# 导出为 CSV 后解析（--output-path 必须相对路径，禁止 /tmp/）
cd <workspace_root>
lark-cli sheets +workbook-export \
  --spreadsheet-token <obj_token> \
  --file-extension csv \
  --sheet-id <sheet_id> \
  --output-path ./yoho_schedule.csv \
  --as user
```

**表头列名（V5.45 实测）**：`需求`、`优先级`、`Android`（指派人）、`Android 提测`、`Android 耗时`、`Android 状态`。

**筛选规则（Android 列）**：

每行一条需求，读取同一行三列：

| 列名 | 用途 |
|------|------|
| `Android` | 指派人 = `满满` 才纳入 |
| `Android 提测` | 作为 `due`；落在 `PREV_WORKDAY`~`TODAY` 或已过期未完结 → 提高优先级 |
| `Android 状态` | `已提测`/`完成测试`/`已上线` → done；`开发中`/`未开始`/`联调中` → todo |

同行左侧取 `需求`、`优先级` 作为 WorkItem 标题与 P 级。

**旧版兼容**（无 `Android` 列、仅有 `各端` 子行时）：`各端`=Android 且 `负责人`=满满。

**Bitable（技术规划 / CR 看板）**：

```bash
lark-cli base +record-list \
  --base-token <base_token> \
  --table-id <table_id> \
  --filter-json '<人员字段 eq 满满 open_id 的 filter>' \
  --field-id 任务描述 --field-id 进展 --field-id 优先级 --field-id 预计完成日期 \
  --page-all
```

字段名因表而异，先 `+field-list` 确认字段 ID，再构造 `--filter-json`。详见 [`../lark-base/references/lark-base-data-analysis-sop.md`](../lark-base/references/lark-base-data-analysis-sop.md)。

**技术规划 due 规则**：`预计完成日期` 为空时，创建飞书任务**不传 `--due`**；表格后续填入日期后，用 `task +update --task-id <guid> --due <日期>` 补上。不得用 today 兜底。

### 1.4 日程反查（lark-calendar）

```bash
lark-cli calendar +agenda \
  --start "<PREV_WORKDAY>" --end "<TODAY>" \
  --as user
```

用会议标题、描述、参会人反查会议相关待办，补全消息/表格中遗漏的行动项。

## Step 2：归一化与去重

### WorkItem 结构

```text
{
  title: 事项简述,
  status: done | todo,
  priority: P1 | P2 | P3,       // 仅 todo
  date: YYYY-MM-DD,             // 归属日期（PREV_WORKDAY 或 TODAY）
  due: YYYY-MM-DD | null,       // 技术规划：仅当「预计完成日期」有值；消息取明确时间戳；禁止无依据填 today
  summary: 消息原文摘要,
  timestamp: 原始时间,
  followers: [满满, 产品/服务端/测试花名...],
  sources: [{type, url, snippet}],
  completed_signals: [...]       // 判断已完成的依据
}
```

### 去重规则

同一事项在多个数据源出现时 **合并为一条**：

1. 标题相似度 ≥ 80% 或指向同一需求/CR/排期行 → 合并。
2. `sources` 数组保留全部来源。
3. 状态取最高置信：表格「已完成」> 消息「已搞定/已合入」> 默认 todo。
4. 优先级取最高：P1 > P2 > P3。

### 优先级启发式

| 级别 | 条件 | 标签色 |
|------|------|--------|
| P1 | 今日截止、阻塞、加急、CR 未解决、明确「今天」 | 红 |
| P2 | 本周排期、技术规划进行中、需跟进但未阻塞 | 橙 |
| P3 | FYI、@all【无需回复】、低优咨询 | 蓝 |

### 已完成判定

- 消息：「已完成」「已合入」「done」「搞定」「已发布」等。
- 表格：状态列 = 完成/Done/已上线。
- 会议：纪要中标记完成的事项。

## Step 3：同步飞书任务

### 标题格式

| 类型 | 格式 | 状态 |
|------|------|------|
| 已完成 | `[已完成][YYYY-MM-DD] 事项` | closed |
| 待办 | `[P1/P2/P3][YYYY-MM-DD] 事项` | open |

### 创建命令

```bash
# 待办（有 due 时）
lark-cli task +create \
  --summary "[P1][2026-06-25] 修复 CR 评论问题" \
  --description "**摘要**：...\n**时间**：...\n**跟进人**：满满、张三\n**来源**：群聊 xxx / CR看板\n**链接**：..." \
  --assignee ou_f515587a96cf38096db988e9106b0975 \
  --follower ou_xxx \
  --due "2026-06-25"

# 待办（技术规划无「预计完成日期」时：省略 --due）
lark-cli task +create \
  --summary "[P1][2026-06-25] 启动任务管理" \
  --description "..." \
  --assignee ou_f515587a96cf38096db988e9106b0975

# 技术规划后续补填「预计完成日期」后更新
lark-cli task +update --task-id <guid> --due "2026-07-10"

# 已完成：创建后立刻标记完成
lark-cli task +create \
  --summary "[已完成][2026-06-24] 合入 feature X" \
  --description "..." \
  --assignee ou_f515587a96cf38096db988e9106b0975 \
  --due "2026-06-24"

lark-cli task +complete --task-id <guid>
```

### 任务描述模板

```markdown
**摘要**：{消息原文摘要}
**时间**：{timestamp}
**跟进人**：满满（自己）、{其他关键人花名}
**来源**：{来源类型} — {链接}
```

### 跟进人

- **必须含**「满满（自己）」。
- 追加产品/服务端/测试等关键人，**花名优先**；用 `lark-cli contact +resolve` 解析 open_id → 花名。

### 按日期分组

- `PREV_WORKDAY` 一组、`TODAY` 一组。
- 可通过 `tasklists` + `section_guid` 归入自定义分组；无清单时按标题日期前缀区分。

### P1/P2/P3 标签

标题前缀 `[P1]`/`[P2]`/`[P3]` 为必选。若用户任务清单已配置优先级自定义字段，额外写入对应 `custom_fields`（需先 `custom_fields list` 查 guid）。

### 去重与幂等

创建前用 `lark-cli task +search --query "<事项关键词>"` 或 `+get-my-tasks` 检查同日同标题是否已存在，避免重复创建。

已存在的技术规划任务：若 bitable `预计完成日期` 从空变为有值，且飞书任务当前无 due，执行 `task +update` 写入 due；若 due 已存在且与表格一致则跳过。

## Step 4：输出

### 4.1 空结果

数据源无任何新消息且无待办时，**安静返回**：

```text
今天没有新待办 ✅
```

不创建任务、不写报告、不发消息。

### 4.2 消息摘要

用 `lark-cli im +messages-send` 向自己发送结构化摘要（result 模式）：

```bash
lark-cli im +messages-send \
  --user-id ou_f515587a96cf38096db988e9106b0975 \
  --markdown "$(cat <<'EOF'
## 每日工作回顾 {TODAY}

### {PREV_WORKDAY} — 已完成 ✅
- [已完成][日期] 事项 — [任务链接](url)

### {PREV_WORKDAY} — 待办 🔥
- [P1][日期] 事项 — [任务链接](url)

### {TODAY} — 已完成 ✅
...

### {TODAY} — 待办 🔥
...
EOF
)"
```

每条待办/已完成附上 `task +create` 返回的 `url`。

### 4.3 Markdown 报告

用 **Write 工具**（不是 shell 重定向）写入：

```text
artifacts/daily_review_YYYY-MM-DD.md
```

Cloud 环境对应 `/home/workspace/artifacts/daily_review_YYYY-MM-DD.md`；本地调试写 `artifacts/` 或项目根目录。

报告结构：

```markdown
# 每日工作回顾 YYYY-MM-DD

## 时间范围
- 起始：{PREV_WORKDAY} 00:00
- 截止：{NOW}

## {PREV_WORKDAY}
### 已完成 ✅
### 待办 🔥

## {TODAY}
### 已完成 ✅
### 待办 🔥

## 数据源覆盖
| 来源 | 命中数 |
|------|--------|
| 群聊@我 | n |
| thread | n |
| 私聊 | n |
| 文档评论 | n |
| Yoho排期表 | n |
| 技术规划 | n |
| CR看板 | n |
| 日程反查 | n |

## 去重合并记录
（列出被合并的重复项及来源）
```

## 权限表

| 命令 | scope |
|------|-------|
| `im +messages-search` | `search:message` |
| `im +threads-messages-list` | `im:message.group_msg:get_as_user` |
| `drive +search --only-comment` | `search:docs:read` |
| `drive file.comments list` | `docs:document.comment:read` |
| `sheets +workbook-export` | `sheets:spreadsheet:read` |
| `base +record-list` | `base:record:read` |
| `calendar +agenda` | `calendar:calendar.event:read` |
| `task +create` / `+complete` / `+update` | `task:task:write` |
| `im +messages-send` | `im:message.send_as_user` |
| `contact +resolve` | `contact:user.basic_profile:readonly` |

## 排障

| 现象 | 原因 | 处理 |
|------|------|------|
| Agent 找 `aily-task` / `aily-calendar` | 工具名幻觉；本工作流只用 `lark-cli` | 改用 `lark-cli task` / `lark-cli calendar`；禁止降级为仅报告 |
| `unsafe output path` | `workbook-export` 用了绝对路径 | 改为 `./yoho_schedule.csv` 等相对路径 |
| 消息/日程/文档搜索 403 | 缺 `search:message` 等 scope | Step 0 增量授权，扫码后 `--device-code` 换票 |
| 排期表 API 返回空、UI 有数据 | `+cells-get` / `+csv-get` 对该表无效 | 改用 `+workbook-export` 导出 CSV |
| `base +record-list --url` 报错 | 不支持 wiki URL 直传 | 用 `wiki +node-get` 取 `base_token`，命令传 `--base-token` + `--table-id` |
| `sheets +sheet-info --url` 无数据 | 需先 wiki 解析 `obj_token` | `wiki +node-get` → `spreadsheet_token` |
| 技术规划任务误设今天截止 | `预计完成日期` 为空却传了 `--due` | 创建时省略 `--due`；表填日期后 `task +update` |
| 授权扫码后仍 403 | 只扫码未换票 | 执行 `auth login --device-code <device_code>` |
| 重复任务 | 卡片通知与表格双源 | 按「消息降噪」跳过；创建前 `task +search` 去重 |

## 参考

- [lark-auth.md](references/lark-auth.md) — 认证（Cloud 必读）
- [data-sources.md](references/data-sources.md) — token、字段、filter 常量（必读）
- [agent-instructions.md](references/agent-instructions.md) — Automation Instructions 全文
