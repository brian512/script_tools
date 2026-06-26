# 数据源常量（满满 daily-review）

执行时优先用本文件中的 token / 字段 / filter，避免每次重新 `+field-list` 或猜 URL 参数。

## 身份

| 键 | 值 |
|----|-----|
| open_id | `ou_f515587a96cf38096db988e9106b0975` |
| user_id | `7004656958481416194` |
| 花名 | 满满 |

## Yoho 排期表（sheet）

| 键 | 值 |
|----|-----|
| wiki | `https://micoworld.feishu.cn/wiki/wikcnQdImFbIxMozD7qO60TBBZb` |
| node_token | `wikcnQdImFbIxMozD7qO60TBBZb` |
| spreadsheet_token | `shtcnnKf72ardl8WSgp65mjBvFg` |
| 当前版本 sheet | `V5.45` / sheet_id `KEIVil` |

**读取方式**：必须用 `+workbook-export` 导出 CSV；`+cells-get` / `+csv-get` 对该表常返回空。

⚠️ `--output-path` **只能是相对路径**（如 `./yoho_schedule.csv`），禁止 `/tmp/`、`/home/workspace/` 等绝对路径，否则报 `unsafe output path`。

```bash
cd <workspace_root>
lark-cli sheets +workbook-export \
  --spreadsheet-token shtcnnKf72ardl8WSgp65mjBvFg \
  --file-extension csv \
  --sheet-id KEIVil \
  --output-path ./yoho_schedule.csv \
  --as user
```

解析 CSV 时用 `encoding=utf-8-sig`。筛选 `Android` 列 = `满满`，读取 `Android 提测`、`Android 状态`，同行取 `需求`、`优先级`。

## 技术规划（bitable）

| 键 | 值 |
|----|-----|
| wiki | `https://micoworld.feishu.cn/wiki/K0pJwPAzbiRvHPkxzgucZnu9nne` |
| base_token | `U8pqbVO5YamA3UsEuIZcCzJ7n2f` |
| table_id | `tblezrNOKPrfc5CQ` |

```bash
lark-cli base +record-list \
  --base-token U8pqbVO5YamA3UsEuIZcCzJ7n2f \
  --table-id tblezrNOKPrfc5CQ \
  --filter-json '{"logic":"and","conditions":[["任务执行人","contains","ou_f515587a96cf38096db988e9106b0975"],["进展","!=","已完成"]]}' \
  --field-id 任务描述 --field-id 进展 --field-id 优先级 --field-id 预计完成日期 --field-id 最新进展记录 \
  --page-all --as user
```

人员字段名是 **任务执行人**（不是「负责人」）。`预计完成日期` 为空 → 创建任务不传 `--due`。

## CR 管理-未解决看板（bitable）

| 键 | 值 |
|----|-----|
| wiki | `https://micoworld.feishu.cn/wiki/YBnJw8jkRinzNBkHRyTcb4MYnee` |
| base_token | `Xttxb7fxcaHQYxssBY1cTcQ7ncc` |
| table_id | `tbl6U9BbxbZ9FwLi` |

```bash
lark-cli base +record-list \
  --base-token Xttxb7fxcaHQYxssBY1cTcQ7ncc \
  --table-id tbl6U9BbxbZ9FwLi \
  --filter-json '{"logic":"and","conditions":[["指派人","==","ou_f515587a96cf38096db988e9106b0975"],["状态","==","未解决"]]}' \
  --field-id fld12lll9b --field-id 状态 --field-id 优先级 --field-id 文档详情链接 --field-id fld2gLl0ep \
  --page-all --as user
```

`+record-list` 用 `--base-token` + `--table-id`，**不要**用 `--url`（会报错）。

## 预检所需 scope

首次或 Automation 部署前，一次性补齐：

```bash
lark-cli auth login --scope "search:message contact:user.basic_profile:readonly calendar:calendar.event:read search:docs:read im:message.send_as_user" --no-wait --json
```

扫码后由 agent 执行 `lark-cli auth login --device-code <device_code>` 完成换票（见 `references/lark-auth.md`）。
