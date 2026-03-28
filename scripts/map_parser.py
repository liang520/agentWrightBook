#!/usr/bin/env python3
"""
map_parser.py — 共用的 Markdown 映射表解析器。
被 build-prompt.py 和 verify-chapter.py 共同使用。

提供两个主要接口：
  - extract_original_terms(): 提取所有原作侧词汇（用于泄漏扫描）
  - extract_replacement_pairs(): 提取替换对（用于 prompt 展示和原作文本预替换）
"""
import re


def parse_markdown_table_rows(text):
    """解析 Markdown 表格，返回 (header_cols, data_rows) 列表。

    每个 data_row 是 [cell0, cell1, cell2, ...] 的字符串列表。
    header_cols 是最近一次表头的列名列表（小写）。
    """
    rows = []
    header_cols = []
    in_table = False

    for line in text.strip().split("\n"):
        stripped = line.strip()
        if not stripped or "|" not in stripped:
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
            # 表头行
            header_cols = [c.lower() for c in cells]
            continue

        rows.append((header_cols, cells))

    return rows


def _split_names(text):
    """将 '孙妈妈/美珍' 或 '林旻（穿越者灵魂）' 拆分为独立词列表，过滤单字。"""
    results = []
    parts = text.split("/") if "/" in text else [text]
    for part in parts:
        part = part.strip()
        paren_match = re.match(r"^(.+?)(?:[（(](.+?)[）)])?$", part)
        if paren_match:
            main_name = paren_match.group(1).strip()
            if len(main_name) >= 2:
                results.append(main_name)
            alias_in_paren = paren_match.group(2)
            if alias_in_paren and len(alias_in_paren.strip()) >= 2:
                results.append(alias_in_paren.strip())
        elif len(part) >= 2:
            results.append(part)
    return results


def _is_alias_column(header_cols, col_idx):
    """判断第 col_idx 列是否是原作侧的别名列。"""
    if col_idx >= len(header_cols):
        return False
    col_header = header_cols[col_idx]
    return any(kw in col_header for kw in ["别名", "原作", "称号", "alias"])


def extract_original_terms(char_map_text, setting_map_text):
    """从 character-map 和 setting-map 提取所有原作侧词汇（用于泄漏扫描）。

    返回 set of strings，每个 >= 2 字符。
    """
    terms = set()

    for text in [char_map_text, setting_map_text]:
        for header_cols, cells in parse_markdown_table_rows(text):
            # 第一列总是原作侧
            if cells:
                terms.update(_split_names(cells[0]))
            # 第二列如果是别名列，也扫描
            if len(cells) >= 2 and _is_alias_column(header_cols, 1):
                terms.update(_split_names(cells[1]))

    return {t for t in terms if len(t) >= 2}


def extract_replacement_pairs(char_map_text, setting_map_text):
    """从 character-map 和 setting-map 提取替换对。

    返回 (display_list, replace_dict)。
    display_list: ["orig → new", ...] 用于 prompt 展示
    replace_dict: {orig: new, ...} 用于原作文本预替换
    """
    display = []
    replace_dict = {}

    for text in [char_map_text, setting_map_text]:
        for header_cols, cells in parse_markdown_table_rows(text):
            if len(cells) < 2:
                continue
            # 跳过表头关键词行
            if any(kw in cells[0] for kw in ["原作", "角色", "---"]):
                continue

            orig = cells[0].strip()
            if not orig or orig == "—":
                continue

            # 新名取第三列（如果有且非空），否则取第二列
            new = ""
            if len(cells) > 2 and cells[2].strip() and cells[2].strip() != "—":
                new = cells[2].strip()
            elif cells[1].strip() and cells[1].strip() != "—":
                new = cells[1].strip()

            if not new or new == "—":
                continue

            display.append(f"{orig} → {new}")

            # 拆分原名中的多个词
            for part in _split_names(orig):
                replace_dict[part] = new.split("/")[0].strip()

            # 别名列也提取
            if len(cells) > 1:
                alias = cells[1].strip()
                if alias and alias != "—" and alias != new and len(alias) >= 2:
                    replace_dict[alias] = new.split("/")[0].strip()

    return display, replace_dict
