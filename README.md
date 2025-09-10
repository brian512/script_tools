# 🛠️ Script Tools - 开发工具脚本集合

一个专为Android开发和系统维护设计的工具脚本集合，提供高效、便捷的自动化工具。

## 📦 工具概览

| 工具 | 类型 | 功能描述 | 状态 |
|------|------|----------|------|
| [APK导出工具](./export_apk/) | Shell脚本 | 智能导出Android应用APK文件 | ✅ 稳定 |
| [APK字符串提取工具](./export_apk_strings/) | Python脚本 | 提取APK多语言字符串资源 | ✅ 稳定 |
| [日志时间线合并工具](./timeline_merge.py) | Python脚本 | 按时间线合并多目录日志文件 | ✅ 稳定 |

## 🚀 快速开始

### 环境要求

- **操作系统**: macOS, Linux, Windows (WSL)
- **Python**: 3.6+ (用于Python工具)
- **ADB**: Android Debug Bridge (用于APK相关工具)
- **Bash**: Shell环境 (用于Shell脚本)

### 安装依赖

```bash
# 克隆或下载工具集合
cd script_tools

# 安装Python依赖
pip install pandas openpyxl tqdm

# 安装ADB (macOS)
brew install android-platform-tools

# 安装ADB (Ubuntu)
sudo apt-get install android-tools-adb
```

## 🔧 工具详细介绍

### 1. APK导出工具 📱

**位置**: `./export_apk/`  
**类型**: Shell脚本  
**版本**: v2.0.0

智能导出Android应用APK文件的工具，支持自动检测前台应用。

#### 核心功能
- ✨ **智能模式**: 无需参数即可自动检测前台应用并导出
- 🎯 **自动检测**: 智能识别当前设备上正在运行的应用
- 📁 **灵活输出**: 支持目录、文件名、完整路径等多种输出方式
- 🔍 **包名命名**: 自动使用包名作为文件名，确保准确性

#### 使用示例
```bash
# 最简单的使用方式
./export_apk/export_apk.sh

# 输出到桌面
./export_apk/export_apk.sh ~/Desktop

# 指定文件名
./export_apk/export_apk.sh myapp.apk
```

#### 文档
- [详细文档](./export_apk/README.md)
- [快速开始](./export_apk/README.md#-快速开始)

---

### 2. APK字符串提取工具 🌐

**位置**: `./export_apk_strings/`  
**类型**: Python脚本  
**版本**: 最新

强大的APK字符串资源提取工具，支持多语言过滤和多种输出格式。

#### 核心功能
- 🌍 **多语言支持**: 智能过滤业务需要的多语言
- 📊 **缺失统计**: 自动统计每个字符串缺失的翻译数量
- 📈 **多格式输出**: 支持Excel (.xlsx) 和CSV (.csv) 格式
- 🔧 **高兼容性**: 支持混淆APK和二进制XML格式

#### 使用示例
```bash
# 快速使用
./export_apk_strings/run_local.sh your_app.apk

# 指定输出格式
./export_apk_strings/run_local.sh your_app.apk -o strings.xlsx -f excel

# 使用语言过滤
python3 export_apk_strings/apk_string_extractor_local.py app.apk -l supported_languages.txt
```

#### 文档
- [详细文档](./export_apk_strings/README.md)
- [参数说明](./export_apk_strings/README.md#参数说明)

---

### 3. 日志时间线合并工具 📝

**位置**: `./timeline_merge.py`  
**类型**: Python脚本  
**版本**: 最新

按时间线合并多个目录中的日志文件，按日期分组输出。

#### 核心功能
- ⏰ **时间线合并**: 按时间戳顺序合并多个日志文件
- 📅 **日期分组**: 自动按日期分组输出到不同文件
- 🔍 **智能解析**: 自动识别日志时间戳格式
- 📁 **批量处理**: 支持处理多个目录中的日志文件

#### 使用示例
```bash
# 合并当前目录下所有子目录的日志
python3 timeline_merge.py

# 指定日志根目录
python3 timeline_merge.py --logDir /path/to/logs

# 指定特定目录
python3 timeline_merge.py --items dir1 dir2 --output-dir merged_logs
```

#### 参数说明
- `--logDir`: 日志根目录 (默认: 脚本所在目录)
- `--items`: 要处理的日志目录列表 (默认: 所有一级子目录)
- `--output-dir`: 输出目录 (默认: timeline)

---

## 🎯 使用场景

### Android开发
- **APK分析**: 快速导出应用APK进行逆向分析
- **多语言管理**: 提取和管理应用的多语言字符串资源
- **调试支持**: 导出特定版本APK进行问题复现

### 系统维护
- **日志分析**: 合并多个服务的日志文件进行问题排查
- **性能监控**: 按时间线分析系统性能日志
- **故障诊断**: 快速定位跨服务的问题

### 自动化脚本
- **CI/CD集成**: 在构建流程中自动提取APK信息
- **批量处理**: 批量处理多个APK文件或日志文件
- **报告生成**: 自动生成多语言翻译报告

## 🔧 高级用法

### 批量处理示例

```bash
# 批量导出APK
for app in com.example.app1 com.example.app2; do
    echo "导出应用: $app"
    ./export_apk/export_apk.sh $app ~/Desktop/${app}.apk
done

# 批量提取字符串
for apk in *.apk; do
    echo "处理APK: $apk"
    ./export_apk_strings/run_local.sh "$apk" -o "${apk%.apk}_strings.xlsx"
done

# 批量合并日志
python3 timeline_merge.py --logDir /var/log --output-dir daily_logs
```

### 集成到CI/CD

```yaml
# GitHub Actions 示例
- name: Extract APK strings
  run: |
    python3 export_apk_strings/apk_string_extractor_local.py app.apk -o strings.xlsx
    # 上传到存储或发送通知
```

## 📋 系统要求

### 基础环境
- **操作系统**: macOS 10.14+, Ubuntu 18.04+, Windows 10+ (WSL)
- **Python**: 3.6+ (推荐 3.8+)
- **内存**: 至少 2GB 可用内存
- **存储**: 至少 1GB 可用空间

### 工具特定要求
- **APK导出工具**: ADB, Android设备连接
- **APK字符串提取**: Android SDK工具 (aapt/aapt2)
- **日志合并工具**: 无特殊要求

## 🛠️ 故障排除

### 常见问题

#### 1. 权限问题
```bash
# 给脚本添加执行权限
chmod +x export_apk/export_apk.sh
chmod +x export_apk_strings/run_local.sh
```

#### 2. Python依赖问题
```bash
# 安装依赖
pip install -r export_apk_strings/requirements.txt

# 或手动安装
pip install pandas openpyxl tqdm
```

#### 3. ADB连接问题
```bash
# 检查设备连接
adb devices

# 重启ADB服务
adb kill-server && adb start-server
```

#### 4. 工具路径问题
```bash
# 检查工具是否存在
ls -la export_apk_strings/tools/aapt/
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这些工具：

1. **Fork** 项目
2. **创建** 功能分支
3. **提交** 更改
4. **推送** 到分支
5. **创建** Pull Request

### 开发规范
- 保持代码简洁和可读性
- 添加适当的错误处理
- 更新相关文档
- 测试新功能

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 支持

如果遇到问题或有建议，请：

1. 查看各工具的详细文档
2. 检查故障排除部分
3. 搜索已有的Issue
4. 创建新的Issue并详细描述问题

## 🎉 致谢

感谢所有为这些工具做出贡献的开发者和用户！

---

**让开发更高效，让工具更智能！** 🚀
