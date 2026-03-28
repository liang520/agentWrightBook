#!/usr/bin/env python3
"""
verify-chapter.py — 扫描章节中的原作名泄漏（硬门禁）。
基于 character-map.md 和 setting-map.md 的所有原作侧列进行子串匹配。

接口：--chapter-file --character-map --setting-map --report-file
Exit codes:
  0 = 无泄漏
  1 = 发现泄漏（report-file 包含详情）
  2 = 词列表为空（映射表解析失败）
"""
import argparse
import json
import re
import sys
from pathlib import Path

from map_parser import extract_original_terms


def scan_leaks(chapter_text, terms):
    """扫描章节文本中是否包含原作词汇。"""
    leaks = []
    for term in sorted(terms):
        if re.search(re.escape(term), chapter_text):
            leaks.append(term)
    return leaks


def main():
    parser = argparse.ArgumentParser(description="Verify chapter for name leaks")
    parser.add_argument("--chapter-file", required=True)
    parser.add_argument("--character-map", required=True)
    parser.add_argument("--setting-map", required=True)
    parser.add_argument("--report-file", required=True)
    args = parser.parse_args()

    # Read files
    for fpath, label in [
        (args.chapter_file, "chapter"),
        (args.character_map, "character-map"),
        (args.setting_map, "setting-map"),
    ]:
        if not Path(fpath).exists():
            print(f"ERROR: [verify-chapter] {label} file not found: {fpath}", file=sys.stderr)
            sys.exit(2)

    chapter_text = Path(args.chapter_file).read_text(encoding="utf-8")
    char_map_text = Path(args.character_map).read_text(encoding="utf-8")
    setting_map_text = Path(args.setting_map).read_text(encoding="utf-8")

    # Extract terms using shared parser
    terms = extract_original_terms(char_map_text, setting_map_text)

    if not terms:
        print("ERROR: [verify-chapter] Empty term list — mapping table parse failed", file=sys.stderr)
        sys.exit(2)

    print(f"Scanning {len(terms)} terms...", file=sys.stderr)

    # Scan
    leaks = scan_leaks(chapter_text, terms)

    # Write report
    report = {
        "total_terms": len(terms),
        "leaks_found": len(leaks),
        "leaked_terms": leaks,
    }
    Path(args.report_file).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if leaks:
        print(f"ERROR: [verify-chapter] Found {len(leaks)} leaks: {leaks}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"OK: No leaks found ({len(terms)} terms checked)", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
