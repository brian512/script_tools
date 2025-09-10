# APK导出工具 (export_apk.sh)

一个功能强大的Android APK导出工具，支持自动检测前台应用并导出APK文件。

## 🚀 功能特性

- **智能模式 (新)**: 无需参数即可自动检测前台应用并导出
- **自动检测前台应用**: 智能识别当前设备上正在运行的应用
- **指定包名导出**: 支持通过包名精确导出特定应用的APK
- **自定义输出路径**: 灵活指定APK文件的保存位置
- **智能文件名**: 自动使用包名作为文件名，确保准确性和一致性
- **完整的错误处理**: 提供详细的错误信息和用户友好的提示
- **支持帮助信息**: 内置帮助文档，使用简单

## 📋 系统要求

- **操作系统**: macOS, Linux, Windows (WSL)
- **必需工具**: 
  - ADB (Android Debug Bridge)
  - Bash shell
- **设备要求**: 
  - Android设备已启用USB调试
  - 设备已通过ADB连接

## 📖 使用方法

### 智能模式 (推荐) 🆕

新版本支持智能模式，无需复杂的参数即可使用：

```bash
# 自动检测前台应用，输出到当前目录，使用包名作为文件名
./export_apk.sh

# 自动检测前台应用，输出到指定目录，使用包名作为文件名
./export_apk.sh ~/Desktop

# 自动检测前台应用，指定输出文件名
./export_apk.sh app.apk

# 自动检测前台应用，指定完整输出路径
./export_apk.sh ~/Desktop/app.apk
```

### 传统模式

```bash
./export_apk.sh [选项] [包名] -o <输出路径>
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-a` | 自动检测前台应用 | `./export_apk.sh -a -o app.apk` |
| `-o <路径>` | 指定输出文件路径 | `-o ~/Desktop/myapp.apk` |
| `-h, --help` | 显示帮助信息 | `./export_apk.sh --help` |
| `包名` | 指定要导出的应用包名 | `com.example.app` |

### 使用示例

#### 1. 智能模式 (新功能)
```bash
# 最简单的使用方式 - 自动检测前台应用，输出到当前目录
./export_apk.sh
# 输出: ./com.example.app.apk (使用包名作为文件名)

# 输出到桌面目录，自动生成文件名
./export_apk.sh ~/Desktop
# 输出: ~/Desktop/com.example.app.apk (使用包名作为文件名)

# 指定文件名，输出到当前目录
./export_apk.sh myapp.apk
# 输出: ./myapp.apk

# 指定完整路径
./export_apk.sh ~/Desktop/myapp.apk
# 输出: ~/Desktop/myapp.apk
```

#### 2. 自动检测并导出前台应用
```bash
# 导出当前前台应用的APK到桌面
./export_apk.sh -a -o ~/Desktop/foreground.apk

# 导出到指定目录
./export_apk.sh -a -o /Users/username/Documents/apps/current.apk
```

#### 3. 导出指定应用
```bash
# 导出微信APK
./export_apk.sh com.tencent.mm -o ~/Desktop/wechat.apk

# 导出支付宝APK
./export_apk.sh com.eg.android.AlipayGphone -o ~/Desktop/alipay.apk
```

#### 4. 查看帮助信息
```bash
./export_apk.sh --help
```

## 🔍 技术原理

### 智能模式解析
新版本增加了智能参数解析功能：

1. **无参数**: 自动启用前台应用检测，输出到当前目录，使用包名作为文件名
2. **路径参数**: 自动判断是目录还是文件，智能生成输出路径
3. **文件名策略**: 自动使用包名作为文件名，确保准确性和一致性

### 前台应用检测
脚本使用以下方法检测前台应用：

1. **主要方法**: `adb shell dumpsys activity | grep "mFocusedApp"`
   - 解析ActivityManager的输出
   - 提取当前焦点应用的包名

2. **备用方法**: `adb shell dumpsys window | grep "mCurrentFocus"`
   - 当主要方法失败时的备用检测方式

### 文件名生成策略
```bash
# 默认模式：使用包名作为文件名
OUTPUT_PATH="./${PACKAGE_NAME}.apk"

# 智能模式：根据参数类型自动判断
# 目录参数：OUTPUT_PATH="目录/${PACKAGE_NAME}.apk"
# 文件名参数：OUTPUT_PATH="./文件名.apk"
```
- **包名优势**: 包名是唯一的，不会重复，与Android系统标识保持一致
- **可预测性**: 文件名完全可预测，便于脚本自动化
- **避免冲突**: 不同应用即使名称相似，包名也不同

### APK路径获取
```bash
adb shell pm path <包名>
```
- 使用PackageManager查询应用的安装路径
- 支持多APK应用（split APKs）
- 自动处理路径中的特殊字符

### 文件导出
```bash
adb pull <设备路径> <本地路径>
```
- 使用ADB的pull命令从设备复制文件
- 自动处理权限和路径问题

## 🛠️ 故障排除

### 常见问题

#### 1. 设备未连接
**错误信息**: `error: no devices/emulators found`

**解决方案**:
```bash
# 检查设备连接
adb devices

# 重启ADB服务
adb kill-server
adb start-server

# 检查USB调试是否启用
# 在设备上: 设置 > 开发者选项 > USB调试
```

#### 2. 应用未找到
**错误信息**: `找不到包名为 xxx 的应用`

**解决方案**:
```bash
# 查看已安装应用列表
adb shell pm list packages

# 搜索特定应用
adb shell pm list packages | grep <关键词>

# 确认包名是否正确
```

#### 3. 权限不足
**错误信息**: `Permission denied`

**解决方案**:
```bash
# 检查ADB权限
adb root

# 重新授权USB调试
# 在设备上重新确认USB调试授权
```

#### 4. 路径问题
**错误信息**: `No such file or directory`

**解决方案**:
```bash
# 检查APK路径是否存在
adb shell ls <APK路径>

# 使用绝对路径
# 确保输出路径的目录存在
mkdir -p <输出目录>
```

### 调试模式

启用详细输出进行调试：
```bash
# 查看ADB详细输出
adb -v pull <设备路径> <本地路径>

# 检查脚本执行过程
bash -x ./export_apk.sh -a -o test.apk

# 调试默认模式
bash -x ./export_apk.sh
```

## 📝 日志和输出

### 成功输出示例
```
🚀 APK导出工具 v2.0.0 启动...

🔍 正在检测前台应用...
✅ 检测到前台应用: com.android.launcher3
📝 使用默认输出路径: ./com.android.launcher3.apk

📦 目标应用: com.android.launcher3
📁 输出路径: ./com.android.launcher3.apk

🔍 正在查找APK路径...
✅ 找到APK路径: /system/system_ext/priv-app/MtkLauncher3QuickStep/MtkLauncher3QuickStep.apk
📤 正在导出APK文件...
✅ APK导出成功: ./com.android.launcher3.apk
📊 文件大小: 19M

🎉 操作完成！
```

### 错误输出示例
```
❌ 错误: 找不到包名为 com.invalid.app 的应用
请检查包名是否正确，或使用 -a 参数自动检测前台应用
```

## 🔒 安全注意事项

1. **权限管理**: 确保只导出有权限访问的应用
2. **文件安全**: 导出的APK文件可能包含敏感信息
3. **设备安全**: 仅在可信设备上使用此工具
4. **法律合规**: 遵守相关法律法规，不用于非法用途

## 🆕 版本更新

### v2.0.0 (最新) - 2024-08-11
- ✨ 新增智能模式，无需参数即可使用
- ✨ 自动文件名生成，使用包名作为文件名
- ✨ 智能路径解析，支持目录和文件参数
- ✨ 改进的用户体验和错误提示
- 🔧 代码重构和性能优化
- 🐛 修复默认模式下的执行顺序问题

### v1.0.0
- 🎯 基础APK导出功能
- 🔍 前台应用自动检测
- 📁 自定义输出路径支持
- 🛠️ 完整的错误处理

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个工具：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 📞 支持

如果遇到问题或有建议，请：

1. 查看本文档的故障排除部分
2. 搜索已有的Issue
3. 创建新的Issue并详细描述问题

## 🧪 测试验证

脚本已经过充分测试，支持以下场景：

- ✅ 默认模式（无参数）：自动检测前台应用，使用包名作为文件名
- ✅ 智能模式：自动识别参数类型，智能设置输出路径
- ✅ 传统模式：保持向后兼容，支持所有原有参数
- ✅ 错误处理：完善的错误提示和用户指导
- ✅ 文件名生成：确保所有文件名都以.apk结尾
