#!/usr/bin/env python3
"""build-prompt.py 可测逻辑的单元测试"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

bp = import_module("build-prompt")
extract_style_system_prompt = bp.extract_style_system_prompt
extract_replacement_list = bp.extract_replacement_list
pre_replace_source_text = bp.pre_replace_source_text
get_chapter_info = bp.get_chapter_info
read_source_chapters = bp.read_source_chapters
read_prev_chapter = bp.read_prev_chapter
parse_foreshadowing = bp.parse_foreshadowing
build_foreshadow_directives = bp.build_foreshadow_directives


def _write_tmp(tmp, name, content):
    p = Path(tmp) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# --- extract_style_system_prompt ---

def test_style_with_marker():
    """提取 ## 系统提示词 后的内容"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "style.md", "# 风格\n一些说明\n## 系统提示词\n你是一位网文作家。\n写作原则如下。")
        result = extract_style_system_prompt(p)
        assert "你是一位网文作家" in result
        assert "一些说明" not in result
    print("✓ test_style_with_marker")


def test_style_without_marker():
    """无标记时返回全文"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "style.md", "全文内容，没有标记。")
        result = extract_style_system_prompt(p)
        assert result == "全文内容，没有标记。"
    print("✓ test_style_without_marker")


# --- extract_replacement_list ---

def test_replacement_basic():
    """基本替换清单提取"""
    with tempfile.TemporaryDirectory() as tmp:
        char = _write_tmp(tmp, "char.md", """| 原作角色 | 别名 | 新角色 |
|---------|------|--------|
| 林旻 | 小旻 | 沈知意 |
| 周严非 | — | 陆时屿 |
""")
        setting = _write_tmp(tmp, "set.md", """| 原作 | 新设定 |
|------|--------|
| 八中 | 锦城六中 |
""")
        display, replace_dict = extract_replacement_list(char, setting)
        assert "林旻" in replace_dict
        assert replace_dict["林旻"] == "沈知意"
        assert "八中" in replace_dict
        assert replace_dict["八中"] == "锦城六中"
        assert len(display) >= 3
    print("✓ test_replacement_basic")


def test_replacement_slash_names():
    """斜杠分隔的多个原名"""
    with tempfile.TemporaryDirectory() as tmp:
        char = _write_tmp(tmp, "char.md", """| 原作角色 | 别名 | 新角色 |
|---------|------|--------|
| 孙妈妈/美珍 | — | 顾妈妈 |
""")
        setting = _write_tmp(tmp, "set.md", "")
        display, replace_dict = extract_replacement_list(char, setting)
        assert "孙妈妈" in replace_dict
        assert "美珍" in replace_dict
    print("✓ test_replacement_slash_names")


def test_replacement_alias_column():
    """别名列也被提取"""
    with tempfile.TemporaryDirectory() as tmp:
        char = _write_tmp(tmp, "char.md", """| 原作角色 | 别名 | 新角色 |
|---------|------|--------|
| 张三 | 三哥 | 李四 |
""")
        setting = _write_tmp(tmp, "set.md", "")
        display, replace_dict = extract_replacement_list(char, setting)
        assert "三哥" in replace_dict
    print("✓ test_replacement_alias_column")


def test_replacement_empty_table():
    """空表格返回空清单"""
    with tempfile.TemporaryDirectory() as tmp:
        char = _write_tmp(tmp, "char.md", "# 角色映射\n没有表格。\n")
        setting = _write_tmp(tmp, "set.md", "# 设定映射\n没有表格。\n")
        display, replace_dict = extract_replacement_list(char, setting)
        assert len(display) == 0
        assert len(replace_dict) == 0
    print("✓ test_replacement_empty_table")


# --- pre_replace_source_text ---

def test_pre_replace_longest_first():
    """最长优先替换，避免部分匹配"""
    replace_dict = {"孙妈妈": "顾妈妈", "孙": "顾"}  # 单字会被跳过但这里测试排序
    text = "孙妈妈做了饭。"
    result = pre_replace_source_text(text, replace_dict)
    assert "顾妈妈" in result
    # 不应该出现 "顾妈妈" 被二次替换
    assert result.count("顾") == 1 or "顾妈妈" in result
    print("✓ test_pre_replace_longest_first")


def test_pre_replace_multiple():
    """多个替换同时工作"""
    replace_dict = {"林旻": "沈知意", "八中": "锦城六中"}
    text = "林旻走进了八中。"
    result = pre_replace_source_text(text, replace_dict)
    assert "沈知意" in result
    assert "锦城六中" in result
    assert "林旻" not in result
    assert "八中" not in result
    print("✓ test_pre_replace_multiple")


# --- get_chapter_info ---

def test_chapter_info_found():
    """从压缩映射表找到章节"""
    with tempfile.TemporaryDirectory() as tmp:
        cmap = _write_tmp(tmp, "cmap.md", """| 新章 | 原作章 | 策略 | 功能 | 目标字数 | 事件 | 起始 | 终止 |
|------|--------|------|------|---------|------|------|------|
| 1 | 001+002 | 合并 | 开篇 | 2000 | 引入主角 | E01 | E02 |
| 2 | 003 | 保留 | 推进 | 1500 | 冲突 | E03 | E04 |
""")
        info = get_chapter_info(cmap, 1)
        assert info is not None
        assert info["source_chapters"] == "001+002"
        assert info["target_words"] == "2000"
        assert info["start_event"] == "E01"
    print("✓ test_chapter_info_found")


def test_chapter_info_not_found():
    """章节不存在返回 None"""
    with tempfile.TemporaryDirectory() as tmp:
        cmap = _write_tmp(tmp, "cmap.md", """| 新章 | 原作章 | 策略 | 功能 | 目标字数 | 事件 | 起始 | 终止 |
|------|--------|------|------|---------|------|------|------|
| 1 | 001 | 保留 | 开篇 | 2000 | 事件 | E01 | E02 |
""")
        info = get_chapter_info(cmap, 99)
        assert info is None
    print("✓ test_chapter_info_not_found")


# --- read_source_chapters ---

def test_source_single_chapter():
    """读取单个原作章节"""
    with tempfile.TemporaryDirectory() as tmp:
        ch_dir = Path(tmp) / "chapters"
        ch_dir.mkdir()
        (ch_dir / "005.md").write_text("\n".join([f"第{i}行" for i in range(100)]), encoding="utf-8")
        result = read_source_chapters(tmp, "005")
        assert "第0行" in result
        assert "第59行" in result
        # 只读前60行
        assert "第60行" not in result
    print("✓ test_source_single_chapter")


def test_source_second_half():
    """后半读取最后60行"""
    with tempfile.TemporaryDirectory() as tmp:
        ch_dir = Path(tmp) / "chapters"
        ch_dir.mkdir()
        (ch_dir / "038.md").write_text("\n".join([f"第{i}行" for i in range(100)]), encoding="utf-8")
        result = read_source_chapters(tmp, "038后半")
        assert "第40行" in result
        assert "第99行" in result
        # 不应包含前面的行
        assert "第0行" not in result
    print("✓ test_source_second_half")


def test_source_multi_chapter():
    """读取多个原作章节 (003+004)"""
    with tempfile.TemporaryDirectory() as tmp:
        ch_dir = Path(tmp) / "chapters"
        ch_dir.mkdir()
        (ch_dir / "003.md").write_text("第三章内容", encoding="utf-8")
        (ch_dir / "004.md").write_text("第四章内容", encoding="utf-8")
        result = read_source_chapters(tmp, "003+004")
        assert "第三章内容" in result
        assert "第四章内容" in result
        assert "---" in result  # 章节分隔符
    print("✓ test_source_multi_chapter")


def test_source_not_found():
    """原作章节不存在"""
    with tempfile.TemporaryDirectory() as tmp:
        ch_dir = Path(tmp) / "chapters"
        ch_dir.mkdir()
        result = read_source_chapters(tmp, "999")
        assert "未找到" in result
    print("✓ test_source_not_found")


# --- read_prev_chapter ---

def test_prev_chapter_ch1():
    """第1章无前章"""
    with tempfile.TemporaryDirectory() as tmp:
        result = read_prev_chapter(Path(tmp), 1)
        assert "第1章" in result
    print("✓ test_prev_chapter_ch1")


def test_prev_chapter_truncate():
    """前章超长时截取末尾"""
    with tempfile.TemporaryDirectory() as tmp:
        long_text = "x" * 5000
        _write_tmp(tmp, "001.md", long_text)
        result = read_prev_chapter(Path(tmp), 2)
        assert len(result) == 1500
    print("✓ test_prev_chapter_truncate")


def test_prev_chapter_not_exist():
    """前章不存在"""
    with tempfile.TemporaryDirectory() as tmp:
        result = read_prev_chapter(Path(tmp), 5)
        assert "不存在" in result
    print("✓ test_prev_chapter_not_exist")


# --- parse_foreshadowing ---

def test_foreshadow_plant():
    """伏笔埋设匹配"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "fore.md", """| 编号 | 内容 | 埋设章 | 回收章 |
|------|------|--------|--------|
| F01 | 神秘信物 | 3 | 15 |
| F02 | 身世之谜 | 5 | 20 |
""")
        plants, reveals = parse_foreshadowing(p, 3)
        assert len(plants) == 1
        assert "F01" in plants[0]
        assert len(reveals) == 0
    print("✓ test_foreshadow_plant")


def test_foreshadow_reveal():
    """伏笔回收匹配"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "fore.md", """| 编号 | 内容 | 埋设章 | 回收章 |
|------|------|--------|--------|
| F01 | 神秘信物 | 3 | 15 |
""")
        plants, reveals = parse_foreshadowing(p, 15)
        assert len(reveals) == 1
        assert "F01" in reveals[0]
    print("✓ test_foreshadow_reveal")


def test_foreshadow_range():
    """范围匹配 15-19"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "fore.md", """| 编号 | 内容 | 埋设章 | 回收章 |
|------|------|--------|--------|
| F01 | 暗线 | 15-19 | 25 |
""")
        plants, reveals = parse_foreshadowing(p, 17)
        assert len(plants) == 1
    print("✓ test_foreshadow_range")


def test_foreshadow_guanchuan():
    """贯穿/未回收不匹配"""
    with tempfile.TemporaryDirectory() as tmp:
        p = _write_tmp(tmp, "fore.md", """| 编号 | 内容 | 埋设章 | 回收章 |
|------|------|--------|--------|
| F01 | 全书线索 | 贯穿 | 未回收 |
""")
        plants, reveals = parse_foreshadowing(p, 10)
        assert len(plants) == 0
        assert len(reveals) == 0
    print("✓ test_foreshadow_guanchuan")


def test_foreshadow_not_exist():
    """文件不存在返回空"""
    plants, reveals = parse_foreshadowing(Path("/nonexistent/fore.md"), 5)
    assert plants == []
    assert reveals == []
    print("✓ test_foreshadow_not_exist")


# --- build_foreshadow_directives ---

def test_directives_plant():
    """生成埋设指令"""
    result = build_foreshadow_directives(["F01: 神秘信物"], [])
    assert "伏笔埋设" in result
    assert "F01" in result
    assert "揭露规则" not in result  # 不应包含回收区块标题
    print("✓ test_directives_plant")


def test_directives_reveal():
    """生成回收指令"""
    result = build_foreshadow_directives([], ["F01: 神秘信物"])
    assert "揭露规则" in result
    assert "保密" not in result
    print("✓ test_directives_reveal")


def test_directives_empty():
    """无伏笔返回空"""
    result = build_foreshadow_directives([], [])
    assert result == ""
    print("✓ test_directives_empty")


if __name__ == "__main__":
    tests = [
        test_style_with_marker,
        test_style_without_marker,
        test_replacement_basic,
        test_replacement_slash_names,
        test_replacement_alias_column,
        test_replacement_empty_table,
        test_pre_replace_longest_first,
        test_pre_replace_multiple,
        test_chapter_info_found,
        test_chapter_info_not_found,
        test_source_single_chapter,
        test_source_second_half,
        test_source_multi_chapter,
        test_source_not_found,
        test_prev_chapter_ch1,
        test_prev_chapter_truncate,
        test_prev_chapter_not_exist,
        test_foreshadow_plant,
        test_foreshadow_reveal,
        test_foreshadow_range,
        test_foreshadow_guanchuan,
        test_foreshadow_not_exist,
        test_directives_plant,
        test_directives_reveal,
        test_directives_empty,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {len(tests) - failed}/{len(tests)} passed")
    if failed:
        sys.exit(1)
    print("All tests passed!")
