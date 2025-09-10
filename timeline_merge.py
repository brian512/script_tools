#!/usr/bin/env python3
import os
import re
import argparse
import heapq
from datetime import datetime
from collections import defaultdict

# 日志时间戳正则
LOG_TIME_PATTERN = re.compile(r"^\[.\]\[(\d{4}-\d{2}-\d{2}) [^ ]+ (\d{2}:\d{2}:\d{2}\.\d{3})\]")


def parse_args():
    parser = argparse.ArgumentParser(description="Merge logs from different directories by timeline and split by date.")
    parser.add_argument('--logDir', default=None, help='Log root directory (default: script location)')
    parser.add_argument('--items', nargs='*', default=None, help='Log directories to search (default: all first-level subdirs)')
    parser.add_argument('--output-dir', default='timeline', help='Output directory (default: timeline)')
    return parser.parse_args()


def find_log_files(log_dirs):
    log_files = []
    for d in log_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if fname.endswith('.log'):
                log_files.append(os.path.join(d, fname))
    return log_files


def extract_log_time(line):
    m = LOG_TIME_PATTERN.match(line)
    if m:
        date_str, time_str = m.groups()
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
            return dt, date_str
        except Exception:
            return None, None
    return None, None


def log_line_generator(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            dt, date_str = extract_log_time(line)
            if dt:
                yield (dt, date_str, line)
            else:
                # 跳过无法解析时间的行
                continue


def main():
    args = parse_args()
    if args.logDir:
        root = os.path.abspath(args.logDir)
    else:
        root = os.path.dirname(os.path.abspath(__file__))
    if args.items:
        log_dirs = [os.path.join(root, d) if not os.path.isabs(d) else d for d in args.items]
    else:
        # 默认所有一级子目录
        log_dirs = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    log_files = find_log_files(log_dirs)
    if not log_files:
        print("No log files found.")
        return
    print("读取到的日志文件列表：")
    for f in log_files:
        print(f"  {f}")
    # 多路归并日志行
    generators = [log_line_generator(f) for f in log_files]
    merged_iter = heapq.merge(*generators, key=lambda x: x[0])
    # 按日期分组输出
    output_dir = args.output_dir
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(root, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_files = dict()
    output_file_set = set()
    try:
        for dt, date_str, line in merged_iter:
            out_path = os.path.join(output_dir, f"timeline_{date_str}.log")
            if date_str not in out_files:
                out_files[date_str] = open(out_path, 'a', encoding='utf-8')
                output_file_set.add(out_path)
            out_files[date_str].write(line)
    finally:
        for f in out_files.values():
            f.close()
    print("\n输出的日志文件列表：")
    for f in sorted(output_file_set):
        print(f"  {f}")
    print("\n日志合并完成。")

if __name__ == '__main__':
    main() 