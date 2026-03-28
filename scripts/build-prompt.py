#!/usr/bin/env python3
"""
build-prompt.py — 自动组装 Gemini 写作 prompt。
读取 style.md、compression-map.md、character-map.md、setting-map.md、
前章正文、memory-outline.md、recent-context.md，输出填充好的 prompt 文件。

接口：--novel-dir --chapter N --source-dir --output-file
Exit codes:
  0 = 成功
  1 = 缺少必要文件
"""
import argparse
import re
import sys
from pathlib import Path


def extract_style_system_prompt(style_path):
    """从 style.md 提取 '## 系统提示词' 到文件末尾的内容。"""
    text = style_path.read_text(encoding="utf-8")
    marker = "## 系统提示词"
    if marker not in text:
        print(f"WARNING: '{marker}' not found in {style_path}", file=sys.stderr)
        return text  # 降级：返回全文
    after = text.split(marker, 1)[1]
    # 跳过标题行本身，取后续内容
    lines = after.split("\n", 1)
    return lines[1].strip() if len(lines) > 1 else ""


def extract_replacement_list(char_map_path, setting_map_path):
    """从 character-map.md 和 setting-map.md 提取替换清单。
    返回 (display_list, replace_dict)。
    display_list: ["orig → new", ...] 用于 prompt 展示
    replace_dict: {orig: new, ...} 用于原作文本预替换
    """
    display = []
    replace_dict = {}
    for path in [char_map_path, setting_map_path]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            if "---" in cells[0] or "原作" in cells[0] or "角色" in cells[0]:
                continue
            orig = cells[0].strip()
            if orig and orig != "—":
                new = cells[2].strip() if len(cells) > 2 and cells[2].strip() and cells[2].strip() != "—" else cells[1].strip()
                if new and new != "—":
                    display.append(f"{orig} → {new}")
                    # 处理 "/" 分隔的多个原名
                    for part in orig.split("/"):
                        part = part.strip()
                        if part and len(part) >= 2:  # 跳过单字
                            replace_dict[part] = new.split("/")[0].strip()
                    # 也提取别名列（第2列，如果表头含"别名"/"原作"）
                    if len(cells) > 1:
                        alias = cells[1].strip()
                        if alias and alias != "—" and alias != new and len(alias) >= 2:
                            replace_dict[alias] = new.split("/")[0].strip()
    return display, replace_dict


def pre_replace_source_text(text, replace_dict):
    """对原作文本做名词预替换，消除泄漏源头。"""
    for orig, new in sorted(replace_dict.items(), key=lambda x: -len(x[0])):
        text = text.replace(orig, new)
    return text


def get_chapter_info(compression_map_path, chapter_num):
    """从 compression-map.md 读取指定章号的信息。"""
    text = compression_map_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        try:
            ch = int(cells[0])
        except ValueError:
            continue
        if ch == chapter_num:
            return {
                "source_chapters": cells[1],
                "strategy": cells[2],
                "function": cells[3],
                "target_words": cells[4],
                "events": cells[5],
                "start_event": cells[6],
                "end_event": cells[7] if len(cells) > 7 else "",
            }
    return None


def read_source_chapters(source_dir, source_str):
    """读取原作章节内容。source_str 如 '003+004' 或 '005'。"""
    parts = re.split(r"[+＋]", source_str.strip())
    content = []
    for part in parts:
        part = part.strip()
        # 尝试多种格式
        # 处理 "038前半" / "038后半" 等非纯数字格式
        is_second_half = "后半" in part
        try:
            num = int(part)
            candidates = [f"{num:03d}.md"]
        except ValueError:
            import re as _re
            m = _re.match(r"(\d+)", part)
            candidates = [f"{int(m.group(1)):03d}.md"] if m else [f"{part}.md"]
        for fmt in candidates:
            path = Path(source_dir) / "chapters" / fmt
            if path.exists():
                text = path.read_text(encoding="utf-8")
                all_lines = text.splitlines()
                if is_second_half:
                    # 后半：取后60行
                    lines = all_lines[-60:]
                else:
                    # 前半或完整：取前60行
                    lines = all_lines[:60]
                content.append("\n".join(lines))
                break
    return "\n\n---\n\n".join(content) if content else "(原作章节未找到)"


def read_prev_chapter(chapters_dir, chapter_num):
    """读取前一章末尾500字。"""
    if chapter_num <= 1:
        return "本章为全书第1章，无前章内容。"
    prev_path = chapters_dir / f"{chapter_num - 1:03d}.md"
    if not prev_path.exists():
        return f"(前章 {chapter_num - 1:03d}.md 不存在)"
    text = prev_path.read_text(encoding="utf-8")
    # 取末尾约500字（1500字节）
    return text[-1500:] if len(text) > 1500 else text


def read_file_safe(path, default=""):
    """安全读取文件，不存在则返回默认值。"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def parse_foreshadowing(foreshadow_path, chapter_num):
    """从 foreshadowing.md 提取当前章节的伏笔指令。
    返回 (plant_directives, reveal_directives) 两个列表。
    """
    plants = []  # 本章埋设的伏笔
    reveals = []  # 本章回收的伏笔

    if not foreshadow_path.exists():
        return plants, reveals

    text = foreshadow_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if "---" in cells[0] or "编号" in cells[0]:
            continue

        fid = cells[0].strip()
        content = cells[1].strip()
        plant_ch_str = cells[2].strip()
        reveal_ch_str = cells[3].strip()

        if not fid or not content:
            continue

        # 解析章号（支持 "1", "15-19", "5/19/22/27", "贯穿", "未回收"）
        def matches_chapter(ch_str, ch_num):
            if not ch_str or ch_str in ("贯穿", "未回收", "待埋设"):
                return False
            for part in re.split(r"[/,]", ch_str):
                part = part.strip()
                if "-" in part:
                    try:
                        a, b = part.split("-", 1)
                        if int(a) <= ch_num <= int(b):
                            return True
                    except ValueError:
                        pass
                else:
                    try:
                        if int(part) == ch_num:
                            return True
                    except ValueError:
                        pass
            return False

        if matches_chapter(plant_ch_str, chapter_num):
            plants.append(f"{fid}: {content}")
        if matches_chapter(reveal_ch_str, chapter_num):
            reveals.append(f"{fid}: {content}")

    return plants, reveals


def build_foreshadow_directives(plants, reveals):
    """将伏笔列表转换为 prompt 中的操作性指令。"""
    lines = []
    if plants:
        lines.append("【伏笔埋设 — 保密规则】")
        for p in plants:
            lines.append(f"- {p}")
            lines.append(f"  → 本章只暗示此悬念，不得直接揭露。涉及的角色身份/秘密不得点名确认。")
        lines.append("")
    if reveals:
        lines.append("【伏笔回收 — 揭露规则】")
        for r in reveals:
            lines.append(f"- {r}")
            lines.append(f"  → 本章揭露此前悬念。揭露前保持隐藏称呼，揭露场景后才切换真名。")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build Gemini writing prompt")
    parser.add_argument("--novel-dir", required=True, help="Novel directory (e.g., novels/blade-assassins)")
    parser.add_argument("--chapter", required=True, type=int, help="Chapter number to write")
    parser.add_argument("--source-dir", required=True, help="Source directory (e.g., sources/bjsdss)")
    parser.add_argument("--output-file", required=True, help="Output prompt file path")
    parser.add_argument("--leak-feedback", default="", help="Optional leak feedback from previous verify failure")
    args = parser.parse_args()

    novel = Path(args.novel_dir)
    source = Path(args.source_dir)
    ch = args.chapter

    # 检查必要文件
    style_path = novel / "config" / "style.md"
    cmap_path = novel / "config" / "compression-map.md"
    char_path = novel / "config" / "character-map.md"
    set_path = novel / "config" / "setting-map.md"

    for p in [style_path, cmap_path, char_path]:
        if not p.exists():
            print(f"ERROR: Required file not found: {p}", file=sys.stderr)
            sys.exit(1)

    # 1. 系统提示词
    system_prompt = extract_style_system_prompt(style_path)

    # 2. 章节信息
    ch_info = get_chapter_info(cmap_path, ch)
    if not ch_info:
        print(f"ERROR: Chapter {ch} not found in compression-map.md", file=sys.stderr)
        sys.exit(1)

    # 3. 替换清单
    replacements, replace_dict = extract_replacement_list(char_path, set_path)

    # 4. 原作内容（预替换原作名词）
    source_text = read_source_chapters(source, ch_info["source_chapters"])
    source_text = pre_replace_source_text(source_text, replace_dict)

    # 5. 前章正文
    prev_chapter = read_prev_chapter(novel / "chapters", ch)

    # 6. 记忆系统
    memory_outline = read_file_safe(novel / "context" / "memory-outline.md", "(空)")
    recent_context = read_file_safe(novel / "context" / "recent-context.md", "(空)")

    # 7. 伏笔指令
    foreshadow_path = novel / "config" / "foreshadowing.md"
    plants, reveals = parse_foreshadowing(foreshadow_path, ch)
    foreshadow_block = build_foreshadow_directives(plants, reveals)

    # 8. 组装 prompt
    target = ch_info["target_words"]

    leak_block = ""
    if args.leak_feedback:
        leak_block = f"""❌ 上次输出包含以下泄漏，必须彻底杜绝：
{args.leak_feedback}

"""

    prompt = f"""=== SYSTEM ===
{system_prompt}

=== USER ===
{leak_block}【字数硬要求 — 第一优先级】
本章目标字数：{target}字。你必须写到至少该字数的90%。不满足字数的输出将被拒绝重写。

【名词替换清单 — 第二优先级】
绝对不能出现左侧任何词：
{chr(10).join(replacements)}

{foreshadow_block}【写作任务】第{ch}章
- 对应原作：第{ch_info['source_chapters']}章
- 压缩策略：{ch_info['strategy']}
- 叙事功能：{ch_info['function']}
- 核心事件：{ch_info['events']}

## 全书记忆
{memory_outline}

## 最近章节上下文
{recent_context}

## 前章内容
{prev_chapter}

## 事件边界
- 本章起始事件：{ch_info['start_event']}
- 本章终止事件：{ch_info['end_event']}

## 原作参考情节
{source_text}

【防重叠规则 - 强制执行】
1. 从前章结尾处自然接续，绝不重复前章事件。
2. 只负责本章事件，不得越界。
3. 写到本章终止事件落地即止。
4. 如果本章与前章或后章对应同一原作章节的不同部分，必须严格区分事件边界——前半章的事件不能在后半章重复。

【输出要求】
- 以"# 第{ch}章"开头，标题自拟
- 章末必须有悬念钩子
- 不要输出任何JSON或元数据
"""

    # 写入
    Path(args.output_file).write_text(prompt, encoding="utf-8")
    print(f"OK: prompt built for ch{ch:03d}, {len(prompt)} chars", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
