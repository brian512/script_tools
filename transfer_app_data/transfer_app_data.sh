#!/bin/bash

set -e

PACKAGE="com.voicechat.live.group"
TEMP_FILE="app_data_backup.tar"
DEVICE_TEMP="/sdcard/$TEMP_FILE"
LOCAL_TEMP="./$TEMP_FILE"

COLOR_GREEN="\033[32m"
COLOR_RED="\033[31m"
COLOR_YELLOW="\033[33m"
COLOR_RESET="\033[0m"

log_info()  { echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"; }
log_warn()  { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"; }
log_error() { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"; }

get_device_serial() {
    local tmpfile
    tmpfile=$(mktemp)
    adb devices | tr -d '\r' | awk '/\tdevice/{print $1}' > "$tmpfile"
    local count
    count=$(wc -l < "$tmpfile" | tr -d ' ')

    if [ "$count" -eq 0 ]; then
        rm -f "$tmpfile"
        log_error "没有检测到已连接的设备"
        exit 1
    fi

    echo "" >&2
    log_info "已连接的设备：" >&2
    local i=1
    while IFS= read -r serial; do
        local model
        model=$(timeout 3 adb -s "$serial" shell getprop ro.product.model 2>/dev/null | tr -d '\r\n' || echo "unknown")
        echo "  $i) $serial  ($model)" >&2
        i=$((i + 1))
    done < "$tmpfile"
    echo "" >&2

    if [ "$count" -eq 1 ]; then
        local selected
        selected=$(head -1 "$tmpfile")
        log_info "只有一台设备，自动选择: $selected" >&2
        rm -f "$tmpfile"
        echo "$selected"
    else
        read -rp "请选择设备编号: " choice
        local selected
        selected=$(sed -n "${choice}p" "$tmpfile")
        rm -f "$tmpfile"
        if [ -z "$selected" ]; then
            log_error "无效的编号: $choice"
            exit 1
        fi
        echo "$selected"
    fi
}

adb_su() {
    local serial=$1
    shift
    adb -s "$serial" shell "echo '$*' | su"
}

get_uid() {
    local serial=$1
    adb -s "$serial" shell dumpsys package "$PACKAGE" 2>/dev/null | grep "userId=" | head -1 | grep -o '[0-9]*'
}

check_package_installed() {
    local serial=$1
    if ! adb -s "$serial" shell pm list packages 2>/dev/null | grep -q "$PACKAGE"; then
        log_error "设备 $serial 上未安装 $PACKAGE"
        exit 1
    fi
}

do_export() {
    log_info "===== 导出模式 ====="

    log_info "选择源设备（导出数据的设备）："
    local serial
    serial=$(get_device_serial)
    log_info "使用设备: $serial"

    check_package_installed "$serial"

    log_info "强杀应用..."
    adb_su "$serial" "am force-stop $PACKAGE"

    log_info "打包应用数据..."
    adb_su "$serial" "tar cf $DEVICE_TEMP -C /data/data $PACKAGE"

    log_info "拉取到电脑..."
    adb -s "$serial" pull "$DEVICE_TEMP" "$LOCAL_TEMP"

    log_info "清理设备临时文件..."
    adb -s "$serial" shell rm "$DEVICE_TEMP"

    local size
    size=$(du -h "$LOCAL_TEMP" | awk '{print $1}')
    log_info "导出完成！文件: $LOCAL_TEMP ($size)"
}

do_import() {
    log_info "===== 导入模式 ====="

    if [ ! -f "$LOCAL_TEMP" ]; then
        log_error "找不到备份文件: $LOCAL_TEMP"
        log_error "请先执行导出操作"
        exit 1
    fi

    log_info "选择目标设备（导入数据的设备）："
    local serial
    serial=$(get_device_serial)
    log_info "使用设备: $serial"

    check_package_installed "$serial"

    local uid
    uid=$(get_uid "$serial")
    if [ -z "$uid" ]; then
        log_error "无法获取应用 UID"
        exit 1
    fi
    log_info "应用 UID: $uid"

    log_info "强杀应用..."
    adb_su "$serial" "am force-stop $PACKAGE"

    log_info "推送备份文件到设备..."
    adb -s "$serial" push "$LOCAL_TEMP" "$DEVICE_TEMP"

    log_info "删除旧数据..."
    adb_su "$serial" "rm -rf /data/data/$PACKAGE"

    log_info "解压还原..."
    adb_su "$serial" "tar xf $DEVICE_TEMP -C /data/data"

    log_info "修复目录权限..."
    adb_su "$serial" "find /data/data/$PACKAGE -type d -exec chmod 771 {} +"

    log_info "修复文件权限..."
    adb_su "$serial" "find /data/data/$PACKAGE -type f -exec chmod 660 {} +"

    log_info "修复所有者..."
    adb_su "$serial" "chown -R $uid:$uid /data/data/$PACKAGE"

    log_info "恢复 SELinux 上下文..."
    adb_su "$serial" "restorecon -R /data/data/$PACKAGE" 2>/dev/null || log_warn "restorecon 不可用，跳过"

    log_info "清理设备临时文件..."
    adb -s "$serial" shell rm "$DEVICE_TEMP"

    log_info "启动应用..."
    adb -s "$serial" shell am start -n "$PACKAGE/.MainActivity" 2>/dev/null || \
    adb -s "$serial" shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 2>/dev/null

    log_info "导入完成！"
}

do_transfer() {
    log_info "===== 一键转移模式 ====="
    do_export
    echo ""
    do_import
    log_info "===== 转移完成 ====="
}

show_help() {
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  export    从设备导出应用数据到电脑"
    echo "  import    从电脑导入应用数据到设备"
    echo "  transfer  一键从设备A转移到设备B"
    echo ""
    echo "示例:"
    echo "  $0 export     # 先从源设备导出"
    echo "  $0 import     # 再导入到目标设备"
    echo "  $0 transfer   # 或一键完成（需同时连接两台设备）"
    echo ""
}

case "${1:-}" in
    export)   do_export ;;
    import)   do_import ;;
    transfer) do_transfer ;;
    *)        show_help ;;
esac
