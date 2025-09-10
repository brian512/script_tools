#!/bin/bash
# APK字符串提取工具 - 本地工具版启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "APK字符串提取工具 - 本地工具版"
echo "==============================="
echo "使用本地Android SDK工具，支持完整APK反编译"
echo ""

# 检查工具是否存在
if [ ! -f "./tools/aapt/aapt" ]; then
    echo "错误: 未找到aapt工具"
    echo "请确保已从Android SDK拷贝工具到 ./tools/aapt/ 目录"
    exit 1
fi

if [ ! -f "./tools/aapt/aapt2" ]; then
    echo "错误: 未找到aapt2工具"
    echo "请确保已从Android SDK拷贝工具到 ./tools/aapt/ 目录"
    exit 1
fi

echo "工具检查完成 ✓"
echo ""

# 检查是否有语言配置文件和命令行参数
if [ -f "./supported_languages.txt" ] && [[ ! "$*" =~ (-l|--lang-config|--languages) ]]; then
    echo "检测到语言配置文件 supported_languages.txt，将自动使用"
    echo "如需禁用，请使用 -l 参数指定其他配置文件或使用 --languages 参数"
    echo ""
    python3 apk_string_extractor_local.py -l supported_languages.txt "$@"
else
    python3 apk_string_extractor_local.py "$@"
fi
