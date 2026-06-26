# Cursor Automation Prompt — 每日工作回顾

将此 prompt 粘贴到 Cursor Automation 的 Instructions 字段。触发器：**周一至周五 09:30**（cron: `30 9 * * 1-5`）。

---

请先 Read 仓库内文件（相对于 checkout 根目录）：
- `.cursor/skills/lark-workflow-daily-review/SKILL.md`
- `.cursor/skills/lark-workflow-daily-review/references/data-sources.md`
- `.cursor/skills/lark-workflow-daily-review/references/lark-auth.md`

**不要** Read `~/.agents/skills/`（Cloud 不存在）。

帮我用 lark-cli 读取飞书消息和文档，整理【前一个工作日 + 今天】我参与的工作内容，按【已完成 ✅ / 待办 🔥】梳理后同步到飞书任务，按日期分组。

## 时间范围
- 起始：前一个工作日 00:00（周五→上周四；周一→上周五；周二/周三/周四→昨天；遇到周末/节假日不视为工作日）
- 截止：今天当前时间
- 跨周末时只覆盖工作日，跳过周六日

## 数据源（请并行获取，避免漏数据）
1. 飞书消息
   - 群聊中 @我的消息（排除 @all 通知，@all 单独标注【无需回复】即可）
   - 跳过 `CR Report`、`技术规划延期提醒` 卡片（表格已覆盖）
   - 我发起或参与回复的活跃 thread / topic（从「我发送的群消息」提取 thread_id 后 `+threads-messages-list`）
   - 私聊：只提取含 @我 或明确待办语义的，必须展示对方花名/昵称
2. 飞书文档 @我的：搜索当前用户 @满满 的新评论，覆盖全部文档
3. 排期表 / 任务表（常量见 data-sources.md）
   - Yoho 排期表：用 `+workbook-export` 读 V5.45；筛选 `Android`=满满，读 `Android 提测`、`Android 状态`
   - 技术规划：`任务执行人` 含满满；`预计完成日期` 为空不设 due
   - CR 看板：`指派人`=满满 且 `状态`=未解决
4. 反向验证（lark-calendar）：查这两天日程，反查会议背景，把会议相关的待办补上

## 同步到飞书任务的规则
- 已完成任务 → 标题格式「[已完成][YYYY-MM-DD] 事项」，task_status=closed；due 取来源明确日期，技术规划无「预计完成日期」则不设 due
- 待办任务 → 标题格式「[P1/P2/P3][YYYY-MM-DD] 事项」，task_status=open
- **技术规划**：`预计完成日期` 为空 → 创建任务时不传 `--due`；后续表格填入日期 → `task +update --due` 更新
- 按日期分组：前一个工作日一组、今天一组；P1 红 / P2 橙 / P3 蓝标签
- 去重：多源 union 后合并；创建前 `task +search` 避免重复
- 跟进人字段：必须含「满满（自己）」+ 其他关键人，花名优先
- 任务描述：消息原文摘要 + 时间戳 + 跟进人 + 来源链接

## 输出
- 用 `im +messages-send` 向自己发送结构化摘要（已闭环 / 待办 分组 + 任务链接）
- 完整 markdown 报告落地到 /home/workspace/artifacts/daily_review_YYYY-MM-DD.md
- 如果数据源无任何新消息 / 无待办，安静返回「今天没有新待办 ✅」即可

## 预检
执行前确认 `auth status` 含 `search:message`、`search:docs:read`、`calendar:calendar.event:read`、`im:message.send_as_user`。缺权限按 skill 排障节处理，不要半跑半停。
