# APK字符串提取工具

一款强大的APK字符串资源提取工具，支持多语言过滤，快速导出为Excel或CSV格式。

## 🚀 快速开始

### 基本使用

```bash
# 推荐使用方式（指定多语言列表）
./run_local.sh your_app.apk --languages default,zh-rCN,en,ja

# 自动使用配置文件（如果存在）
./run_local.sh your_app.apk

# 指定输出文件和格式
./run_local.sh your_app.apk -o strings.xlsx --languages default,en
./run_local.sh your_app.apk -o strings.csv -f csv --languages default,zh-rCN,en
```

### 语言过滤功能

```bash
# 使用命令行参数指定多语言（推荐，新增功能）
python3 apk_string_extractor_local.py app.apk --languages default,zh-rCN,en,ja

# 使用语言配置文件过滤
python3 apk_string_extractor_local.py app.apk -l supported_languages.txt

# 导出所有语言（不使用配置文件）
python3 apk_string_extractor_local.py app.apk

# 查看完整帮助信息
python3 apk_string_extractor_local.py --help
```

### 完整参数示例

```bash
# 包含所有可用参数的完整命令（复制修改使用）
python3 apk_string_extractor_local.py \
    your_app.apk \
    --output strings_output.xlsx \
    --format excel \
    --languages default,zh-rCN,en,ja \
    --tools-dir ./tools

# 使用配置文件的方式
python3 apk_string_extractor_local.py \
    your_app.apk \
    --lang-config supported_languages.txt

# 简化版本（现在也支持语言过滤）
python3 apk_string_extractor_simple.py \
    your_app.apk \
    --output strings_output.xlsx \
    --format csv \
    --languages default,en,zh-rCN
```

### 参数说明

| 参数 | 短选项 | 说明 | 默认值 | 简化版支持 | 示例 |
|------|--------|------|--------|-----------|------|
| `apk_path` | - | APK文件路径（必需） | - | ✅ | `app.apk` |
| `--output` | `-o` | 输出文件路径 | `strings.xlsx` | ✅ | `-o my_strings.xlsx` |
| `--format` | `-f` | 输出格式 | `excel` | ✅ | `-f csv` |
| `--languages` | - | **多语言列表（逗号分隔）** | 无 | ✅ | `--languages default,zh-rCN,en` |
| `--lang-config` | `-l` | 语言配置文件 | 无 | ❌ | `-l supported_languages.txt` |
| `--tools-dir` | - | 工具目录路径 | `./tools` | ❌ | `--tools-dir /path/to/tools` |

> **新增功能**: `--languages` 参数支持用逗号分隔的多语言列表，优先级高于配置文件，两个版本都支持。

## ⭐ 核心功能

- ✅ **智能语言过滤**：只导出业务需要的多语言，过滤系统/第三方库语言
- ✅ **缺失语言统计**：自动统计每个字符串缺失的翻译数量
- ✅ **多格式输出**：支持Excel (.xlsx) 和CSV (.csv) 格式
- ✅ **高兼容性**：支持混淆APK和二进制XML格式
- ✅ **本地工具**：使用Android SDK工具，无需网络连接

## 📊 输出格式

| Key         | 缺失语言数 | default  | zh-rTW   | en      | fr        | de        |
| ----------- | ---------- | -------- | -------- | ------- | --------- | --------- |
| app_name    | 0          | 我的应用 | 我的應用 | My App  | Mon App   | Meine App |
| welcome_msg | 1          | 欢迎使用 | 歡迎使用 | Welcome | Bienvenue |           |

### 语言配置文件 (supported_languages.txt)

```
# 支持的业务多语言配置文件
# 每行一个语言代码，# 开头为注释

default
zh-rTW
en
ja
ko
fr
de
```

## 🛠️ 目录结构

```
export_apk_strings/
├── apk_string_extractor_local.py     # 主要工具（推荐）
├── apk_string_extractor_simple.py    # 简化版本
├── run_local.sh                      # 启动脚本
├── supported_languages.txt           # 语言配置文件
├── requirements.txt                  # Python依赖
└── tools/aapt/                       # Android工具
    ├── aapt                          # ✅ 已拷贝
    └── aapt2                         # ✅ 已拷贝
```

## 📋 版本说明

### 主要版本 - apk_string_extractor_local.py

- ✅ 推荐日常使用
- ✅ 支持所有APK格式
- ✅ 性能最佳，兼容性最强

### 简化版本 - apk_string_extractor_simple.py

- ✅ 快速测试使用
- ✅ 纯Python实现
- ❌ 不支持二进制XML

## 🔧 批量处理示例

```bash
# 批量处理多个APK文件
for apk in *.apk; do
    echo "正在处理: $apk"
    ./run_local.sh "$apk" -o "${apk%.apk}_strings.xlsx"
done
```

## ⚠️ 注意事项

1. **权限问题**: 确保启动脚本有执行权限 `chmod +x *.sh`
2. **Python依赖**: 确保安装依赖 `pip install pandas openpyxl tqdm`
3. **工具验证**: 工具已从本地Android SDK拷贝并验证

---

**享受高效的APK字符串提取体验！** 🚀
