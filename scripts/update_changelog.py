#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目更新日志自动更新脚本

使用方法:
    python scripts/update_changelog.py --type "新增功能" --title "功能名称" --desc "功能描述" --details "详细说明1" --details "详细说明2"
"""

import argparse
import datetime
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"


def get_current_date() -> str:
    """获取当前日期字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d")


def read_changelog() -> str:
    """读取更新日志文件"""
    if not CHANGELOG_PATH.exists():
        return ""
    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        return f.read()


def write_changelog(content: str) -> None:
    """写入更新日志文件"""
    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def add_entry(
    entry_type: str,
    title: str,
    desc: str,
    details: list[str] = None
) -> None:
    """
    添加新的更新日志条目

    Args:
        entry_type: 类型（新增功能、功能优化、Bug修复等）
        title: 标题
        desc: 描述
        details: 详细说明列表
    """
    content = read_changelog()
    current_date = get_current_date()
    
    # 构建新的条目
    entry_lines = [f"- **{title}**：{desc}"]
    if details:
        for detail in details:
            entry_lines.append(f"  - {detail}")
    new_entry = "\n".join(entry_lines)
    
    # 检查今天是否已经有记录
    date_header = f"### {current_date}"
    type_header = f"#### {entry_type}"
    
    if date_header in content:
        # 今天已有记录，添加到对应类型下
        if type_header in content:
            # 类型已存在，在该类型下添加新条目
            lines = content.split("\n")
            result = []
            i = 0
            while i < len(lines):
                result.append(lines[i])
                if lines[i] == type_header and i + 1 < len(lines):
                    # 找到类型标题，在下一行添加新条目
                    result.append("")
                    result.append(new_entry)
                i += 1
            content = "\n".join(result)
        else:
            # 类型不存在，在日期下添加新类型
            lines = content.split("\n")
            result = []
            i = 0
            while i < len(lines):
                result.append(lines[i])
                if lines[i] == date_header and i + 1 < len(lines):
                    # 找到日期标题，在下一行添加新类型和条目
                    result.append("")
                    result.append(type_header)
                    result.append(new_entry)
                i += 1
            content = "\n".join(result)
    else:
        # 今天没有记录，在[最新版本]后添加
        latest_version_marker = "## [最新版本]"
        if latest_version_marker in content:
            new_section = f"{latest_version_marker}\n\n{date_header}\n\n{type_header}\n{new_entry}\n\n---"
            content = content.replace(latest_version_marker, new_section)
        else:
            # 如果没有最新版本标记，在文件开头添加
            new_section = f"## [最新版本]\n\n{date_header}\n\n{type_header}\n{new_entry}\n\n---\n\n"
            content = new_section + content
    
    write_changelog(content)
    print(f"✅ 更新日志已添加: {title}")


def main():
    parser = argparse.ArgumentParser(description="项目更新日志自动更新脚本")
    parser.add_argument(
        "--type", 
        required=True, 
        choices=["新增功能", "功能优化", "Bug修复", "性能优化", "代码重构", "文档更新"],
        help="更新类型"
    )
    parser.add_argument("--title", required=True, help="标题")
    parser.add_argument("--desc", required=True, help="描述")
    parser.add_argument("--details", action="append", default=[], help="详细说明（可多次使用）")
    
    args = parser.parse_args()
    
    add_entry(
        entry_type=args.type,
        title=args.title,
        desc=args.desc,
        details=args.details
    )


if __name__ == "__main__":
    main()
