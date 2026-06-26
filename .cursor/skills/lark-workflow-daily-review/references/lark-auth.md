# lark-cli 认证（Cloud Automation 精简版）

本工作流全程 `--as user`。预检：`lark-cli auth status --as user`，`identities.user.status` 应为 `ready`。

## 缺 scope

```bash
lark-cli auth login --scope "search:message contact:user.basic_profile:readonly calendar:calendar.event:read search:docs:read im:message.send_as_user task:task:write" --no-wait --json
```

把返回的 `verification_url` 给用户扫码；**本轮结束**。用户确认后下轮：

```bash
lark-cli auth login --device-code <device_code>
```

## 禁止

- 对 user 身份任务使用 `aily-task` 或 MCP 替代 `lark-cli task`
- 扫码后未执行 `--device-code` 换票就继续跑（会 403）
