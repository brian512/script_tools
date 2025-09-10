#!/bin/bash

# APK导出工具
# 功能：自动检测前台应用或指定包名导出APK文件
# 作者：Android开发工具团队
# 版本：2.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 全局变量
PACKAGE_NAME=""
OUTPUT_PATH=""
AUTO_DETECT=false
DEFAULT_MODE=false

# 显示帮助信息
show_help() {
    echo -e "${CYAN}APK导出工具 v2.0.0${NC}"
    echo ""
    echo "用法: $0 [选项] [包名] [输出路径]"
    echo ""
    echo "选项:"
    echo "  -a, --auto          自动检测前台应用"
    echo "  -o, --output <路径>  指定输出文件路径"
    echo "  -h, --help          显示此帮助信息"
    echo ""
    echo "智能模式 (推荐):"
    echo "  $0                    # 自动检测前台应用，输出到当前目录"
    echo "  $0 ~/Desktop         # 自动检测前台应用，输出到指定目录"
    echo "  $0 app.apk           # 自动检测前台应用，指定输出文件名"
    echo "  $0 ~/Desktop/app.apk # 自动检测前台应用，指定完整输出路径"
    echo ""
    echo "传统模式:"
    echo "  $0 -a -o ~/Desktop/app.apk          # 导出前台应用"
    echo "  $0 com.example.app -o app.apk       # 导出指定应用"
    echo "  $0 --help                           # 显示帮助"
    echo ""
    echo "注意:"
    echo "  - 需要ADB连接和USB调试权限"
    echo "  - 确保输出目录存在或有写入权限"
    echo "  - 包名格式: com.example.app"
    echo "  - 智能模式下，未指定文件名时自动使用包名"
}

# 检查ADB连接
check_adb_connection() {
    if ! command -v adb &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到ADB命令${NC}"
        echo "请先安装Android Platform Tools:"
        echo "  macOS: brew install android-platform-tools"
        echo "  Ubuntu: sudo apt-get install android-tools-adb"
        exit 1
    fi

    local devices=$(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l)
    if [ "$devices" -eq 0 ]; then
        echo -e "${RED}❌ 错误: 未检测到已连接的Android设备${NC}"
        echo "请确保:"
        echo "  1. 设备已启用USB调试"
        echo "  2. 设备已通过USB连接"
        echo "  3. 已在设备上授权USB调试"
        echo ""
        echo "检查连接状态: adb devices"
        exit 1
    fi
}

# 检测前台应用
detect_foreground_app() {
    echo -e "${BLUE}🔍 正在检测前台应用...${NC}"
    
    # 主要方法：使用dumpsys activity
    local package_name=$(adb shell dumpsys activity | grep "mFocusedApp" | head -1 | sed 's/.*ActivityRecord{[^}]* \([^}]*\)}.*/\1/' | cut -d'/' -f1)
    
    # 备用方法：使用dumpsys window
    if [ -z "$package_name" ]; then
        package_name=$(adb shell dumpsys window | grep "mCurrentFocus" | head -1 | sed 's/.*{\([^}]*\)}.*/\1/' | cut -d'/' -f1)
    fi
    
    if [ -z "$package_name" ]; then
        echo -e "${RED}❌ 错误: 无法检测到前台应用${NC}"
        echo "请确保有应用正在前台运行，或手动指定包名"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 检测到前台应用: $package_name${NC}"
    PACKAGE_NAME="$package_name"
}

# 获取应用名称
get_app_name() {
    local package_name="$1"
    local app_name=""
    
    # 尝试获取应用标签
    app_name=$(adb shell pm list packages -f "$package_name" 2>/dev/null | sed 's/.*=//' | sed 's/\.apk$//' | sed 's/.*\///')
    
    # 如果获取失败，使用包名
    if [ -z "$app_name" ]; then
        app_name="$package_name"
    fi
    
    echo "$app_name"
}

# 获取APK路径
get_apk_path() {
    echo -e "${BLUE}🔍 正在查找APK路径...${NC}" >&2
    
    local apk_path=$(adb shell pm path "$PACKAGE_NAME" 2>/dev/null | cut -d ":" -f 2 | tr -d '\r\n' | xargs)
    
    if [ -z "$apk_path" ]; then
        echo -e "${RED}❌ 错误: 找不到包名为 $PACKAGE_NAME 的应用${NC}" >&2
        echo "请检查包名是否正确，或使用 -a 参数自动检测前台应用" >&2
        exit 1
    fi
    
    echo -e "${GREEN}✅ 找到APK路径: $apk_path${NC}" >&2
    echo "$apk_path"
}

# 智能解析输出路径
smart_parse_output_path() {
    local arg="$1"
    
    # 如果参数包含斜杠，认为是路径
    if [[ "$arg" == */* ]]; then
        # 如果以.apk结尾，认为是完整路径
        if [[ "$arg" == *.apk ]]; then
            OUTPUT_PATH="$arg"
        else
            # 否则认为是目录，使用包名作为文件名
            OUTPUT_PATH="$arg/${PACKAGE_NAME}.apk"
        fi
    else
        # 如果不包含斜杠，检查是否以.apk结尾
        if [[ "$arg" == *.apk ]]; then
            OUTPUT_PATH="./$arg"
        else
            # 否则认为是文件名，输出到当前目录
            OUTPUT_PATH="./$arg.apk"
        fi
    fi
}

# 导出APK文件
export_apk() {
    local apk_path="$1"
    
    echo -e "${BLUE}📤 正在导出APK文件...${NC}"
    
    # 确保输出目录存在
    local output_dir=$(dirname "$OUTPUT_PATH")
    if [ ! -d "$output_dir" ]; then
        mkdir -p "$output_dir"
    fi
    
    # 执行导出
    if adb pull "$apk_path" "$OUTPUT_PATH"; then
        echo -e "${GREEN}✅ APK导出成功: $OUTPUT_PATH${NC}"
        
        # 显示文件信息
        if [ -f "$OUTPUT_PATH" ]; then
            local file_size=$(ls -lh "$OUTPUT_PATH" | awk '{print $5}')
            echo -e "${CYAN}📊 文件大小: $file_size${NC}"
        fi
    else
        echo -e "${RED}❌ APK导出失败${NC}"
        echo "可能的原因:"
        echo "  - 权限不足"
        echo "  - 路径不存在"
        echo "  - 磁盘空间不足"
        exit 1
    fi
}

# 解析命令行参数
parse_arguments() {
    local args=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--auto)
                AUTO_DETECT=true
                shift
                ;;
            -o|--output)
                OUTPUT_PATH="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                echo -e "${RED}❌ 错误: 未知选项 $1${NC}"
                show_help
                exit 1
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # 智能模式处理
    if [ "$AUTO_DETECT" = false ] && [ -z "$OUTPUT_PATH" ] && [ ${#args[@]} -gt 0 ]; then
        # 检查第一个参数是否是包名（不包含斜杠且不是.apk文件）
        if [[ "${args[0]}" != */* ]] && [[ "${args[0]}" != *.apk ]]; then
            # 可能是包名，检查第二个参数
            if [ ${#args[@]} -gt 1 ]; then
                PACKAGE_NAME="${args[0]}"
                smart_parse_output_path "${args[1]}"
            else
                # 只有一个参数，可能是输出路径
                smart_parse_output_path "${args[0]}"
            fi
        else
            # 第一个参数是路径，启用自动检测
            AUTO_DETECT=true
            smart_parse_output_path "${args[0]}"
        fi
    elif [ "$AUTO_DETECT" = false ] && [ -z "$OUTPUT_PATH" ] && [ ${#args[@]} -eq 0 ]; then
        # 没有任何参数，启用默认模式
        DEFAULT_MODE=true
        AUTO_DETECT=true
        # 注意：这里不能直接调用detect_foreground_app，因为还没有检查ADB连接
        # 输出路径将在main函数中设置
    fi
}

# 验证参数
validate_arguments() {
    # 检查是否指定了输出路径
    if [ -z "$OUTPUT_PATH" ]; then
        echo -e "${RED}❌ 错误: 必须指定输出路径${NC}"
        show_help
        exit 1
    fi
    
    # 检查是否指定了包名或自动检测
    if [ -z "$PACKAGE_NAME" ] && [ "$AUTO_DETECT" = false ]; then
        echo -e "${RED}❌ 错误: 必须指定包名或使用 -a 参数自动检测${NC}"
        show_help
        exit 1
    fi
}

# 主函数
main() {
    echo -e "${PURPLE}🚀 APK导出工具 v2.0.0 启动...${NC}"
    echo ""
    
    # 解析参数
    parse_arguments "$@"
    
    # 检查ADB连接
    check_adb_connection
    
    # 如果启用自动检测，检测前台应用
    if [ "$AUTO_DETECT" = true ]; then
        detect_foreground_app
        
        # 如果是默认模式且没有设置输出路径，则设置默认路径
        if [ "$DEFAULT_MODE" = true ] && [ -z "$OUTPUT_PATH" ]; then
            # 使用包名作为默认文件名
            OUTPUT_PATH="./${PACKAGE_NAME}.apk"
            echo -e "${CYAN}📝 使用默认输出路径: $OUTPUT_PATH${NC}"
        fi
    fi
    
    # 验证参数 (在设置完默认路径后验证)
    validate_arguments
    
    # 显示目标信息
    echo -e "${CYAN}📦 目标应用: $PACKAGE_NAME${NC}"
    echo -e "${CYAN}📁 输出路径: $OUTPUT_PATH${NC}"
    echo ""
    
    # 获取APK路径
    local apk_path=$(get_apk_path)
    
    # 导出APK
    export_apk "$apk_path"
    
    echo ""
    echo -e "${GREEN}🎉 操作完成！${NC}"
}

# 执行主函数
main "$@" 