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


def parse_markdown_table(text):
    """解析 Markdown 表格，提取所有原作侧列的值。

    规则：
    - 跳过表头行和 --- 分隔行
    - 解析每行：[c.strip() for c in line.split("|") if c.strip()]
    - 提取第一列（原作名）+ 含有别名/称号的列
    - 仅保留 ≥ 2 字符的词
    """
    terms = set()
    lines = text.strip().split("\n")

    in_table = False
    header_cols = []

    for line in lines:
        stripped = line.strip()
        if not stripped or not "|" in stripped:
            in_table = False
            header_cols = []
            continue

        cells = [c.strip() for c in stripped.split("|") if c.strip()]
        if not cells:
            continue

        # 检测分隔行 (--- 或 :---: 等)
        if all(re.match(r"^:?-+:?$", c) for c in cells):
            in_table = True
            continue

        if not in_table:
            # 这是表头行，记录列名用于识别原作侧列
            header_cols = [c.lower() for c in cells]
            continue

        # 提取原作侧的所有列内容
        # 策略：扫描前两列（第一列=原作名，第二列=原作别名，如果表头含"别名"/"原作"）
        # 对于简单的两列表（原作|新），只扫描第一列
        # 对于龙套表（原作名|原作别名|新名|出场章），扫描前两列
        original_side_cells = [cells[0]] if cells else []

        # 如果有第二列且表头暗示是原作侧（含"别名"/"原作"/"称号"）
        if len(cells) >= 2 and header_cols:
            if len(header_cols) >= 2:
                col1_header = header_cols[1] if len(header_cols) > 1 else ""
                if any(kw in col1_header for kw in ["别名", "原作", "称号", "alias"]):
                    original_side_cells.append(cells[1])

        for cell_text in original_side_cells:
            cell_text = cell_text.strip()
            if not cell_text:
                continue

            # 处理 "/" 分隔（如 "孙妈妈/美珍"）
            parts = cell_text.split("/") if "/" in cell_text else [cell_text]

            for part in parts:
                part = part.strip()
                # 去除括号说明，如 "林旻（穿越者灵魂）" → 提取 "林旻" + "穿越者灵魂"
                paren_match = re.match(r"^(.+?)(?:[（(](.+?)[）)])?$", part)
                if paren_match:
                    main_name = paren_match.group(1).strip()
                    if len(main_name) >= 2:
                        terms.add(main_name)
                    alias_in_paren = paren_match.group(2)
                    if alias_in_paren and len(alias_in_paren.strip()) >= 2:
                        terms.add(alias_in_paren.strip())
                elif len(part) >= 2:
                    terms.add(part)

    return terms


def extract_original_terms(char_map_text, setting_map_text):
    """从 character-map 和 setting-map 提取所有原作侧词汇。"""
    terms = set()

    # 解析 character-map
    terms.update(parse_markdown_table(char_map_text))

    # 解析 setting-map
    terms.update(parse_markdown_table(setting_map_text))

    # 过滤：仅保留 ≥ 2 字符
    terms = {t for t in terms if len(t) >= 2}

    return terms


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

    # Read files — file I/O errors are exit 2 (infrastructure), not exit 1 (leak found)
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

    # Extract terms
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
