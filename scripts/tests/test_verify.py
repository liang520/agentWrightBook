#!/usr/bin/env python3
"""verify-chapter.py 单元测试"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "verify-chapter.py"
PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python3"


def run_verify(chapter_text, char_map, setting_map):
    """运行 verify-chapter.py，返回 (exit_code, report_dict)"""
    with tempfile.TemporaryDirectory() as tmp:
        ch = Path(tmp) / "chapter.md"
        cm = Path(tmp) / "character-map.md"
        sm = Path(tmp) / "setting-map.md"
        rpt = Path(tmp) / "report.json"

        ch.write_text(chapter_text, encoding="utf-8")
        cm.write_text(char_map, encoding="utf-8")
        sm.write_text(setting_map, encoding="utf-8")

        result = subprocess.run(
            [str(PYTHON), str(SCRIPT),
             "--chapter-file", str(ch),
             "--character-map", str(cm),
             "--setting-map", str(sm),
             "--report-file", str(rpt)],
            capture_output=True, text=True
        )

        report = None
        if rpt.exists():
            report = json.loads(rpt.read_text(encoding="utf-8"))

        return result.returncode, report


CHAR_MAP = """# 角色映射表

## 主要角色

| 原作角色 | 新角色 | 原型 |
|---------|--------|------|
| 林旻（穿越者灵魂） | 沈知意 | 学霸 |
| 孙书仪（躯体原主） | 顾念念 | 差生 |
| 周严非（男主） | 陆时屿 | 痞帅学神 |
| 萧领（男二） | 傅清晏 | 高冷学霸 |

## 次要角色

| 原作角色 | 新角色 | 首次出场 | 功能 |
|---------|--------|---------|------|
| 孙妈妈/美珍 | 顾妈妈/秀兰 | 第8章 | 母亲 |
"""

SETTING_MAP = """# 设定映射表

## 学校

| 原作 | 新设定 |
|------|--------|
| 八中 | 锦城六中 |
| 清华 | 华清大学 |
"""


def test_no_leak():
    """无泄漏 → exit 0"""
    chapter = "沈知意走进了锦城六中的大门，陆时屿在操场上打篮球。"
    code, report = run_verify(chapter, CHAR_MAP, SETTING_MAP)
    assert code == 0, f"Expected exit 0, got {code}"
    assert report["leaks_found"] == 0
    print("✓ test_no_leak")


def test_main_name_leak():
    """主名泄漏 → exit 1"""
    chapter = "那时的我，是意气风发的林旻。"
    code, report = run_verify(chapter, CHAR_MAP, SETTING_MAP)
    assert code == 1, f"Expected exit 1, got {code}"
    assert "林旻" in report["leaked_terms"]
    print("✓ test_main_name_leak")


def test_alias_leak():
    """别名泄漏（括号内 + 斜杠分隔）→ exit 1"""
    # "穿越者灵魂" 在括号内，"美珍" 在斜杠后
    chapter = "美珍阿姨做了一桌子菜。"
    code, report = run_verify(chapter, CHAR_MAP, SETTING_MAP)
    assert code == 1, f"Expected exit 1, got {code}"
    assert "美珍" in report["leaked_terms"]
    print("✓ test_alias_leak")


def test_setting_leak():
    """设定泄漏 → exit 1"""
    chapter = "沈知意考上了清华大学。"
    code, report = run_verify(chapter, CHAR_MAP, SETTING_MAP)
    assert code == 1, f"Expected exit 1, got {code}"
    assert "清华" in report["leaked_terms"]
    print("✓ test_setting_leak")


def test_single_char_skip():
    """单字词过滤（"明" → 跳过）"""
    # 单个汉字不应被视为泄漏
    single_char_map = """| 原作角色 | 新角色 |
|---------|--------|
| 明 | 光 |
| 林旻 | 沈知意 |
"""
    chapter = "明天天气很好。"
    code, report = run_verify(chapter, single_char_map, SETTING_MAP)
    assert code == 0, f"Expected exit 0 (single char filtered), got {code}"
    print("✓ test_single_char_skip")


def test_empty_term_list():
    """空映射表 → exit 2"""
    empty_map = "# 角色映射表\n\n没有表格内容。\n"
    chapter = "一些文本。"
    code, report = run_verify(chapter, empty_map, empty_map)
    assert code == 2, f"Expected exit 2, got {code}"
    print("✓ test_empty_term_list")


def test_markdown_table_parsing():
    """确认表格解析正确处理各种格式"""
    complex_map = """# 映射

## 主要

| 原作角色 | 新角色 | 备注 |
|---------|--------|------|
| 张三（男主） | 李四 | 主角 |
| 王五/老五 | 赵六 | 配角 |

## 其他文本（不是表格）

这里没有表格。
"""
    # 张三 和 王五/老五 都应该被扫描
    chapter = "老五走了过来。"
    code, report = run_verify(chapter, complex_map, "| a | b |\n|---|---|\n| cc | dd |")
    assert code == 1, f"Expected exit 1, got {code}"
    assert "老五" in report["leaked_terms"]
    print("✓ test_markdown_table_parsing")


def test_alias_column_leak():
    """龙套表的独立别名列泄漏 → exit 1"""
    alias_col_map = """# 龙套列表

| 原作名 | 原作别名 | 新名 | 出场章 |
|--------|---------|------|--------|
| 张三 | 三哥 | 李四 | 第5章 |
| 王五 | 老五 | 赵六 | 第8章 |
"""
    # "三哥" 在别名列，应该被扫描到
    chapter = "三哥走了过来。"
    code, report = run_verify(chapter, alias_col_map, SETTING_MAP)
    assert code == 1, f"Expected exit 1 (alias column leak), got {code}"
    assert "三哥" in report["leaked_terms"]
    print("✓ test_alias_column_leak")


def test_file_not_found_exit2():
    """文件不存在 → exit 2（不是 exit 1）"""
    result = subprocess.run(
        [str(PYTHON), str(SCRIPT),
         "--chapter-file", "/nonexistent/chapter.md",
         "--character-map", "/nonexistent/map.md",
         "--setting-map", "/nonexistent/setting.md",
         "--report-file", "/tmp/test-report.json"],
        capture_output=True, text=True
    )
    assert result.returncode == 2, f"Expected exit 2 for missing file, got {result.returncode}"
    print("✓ test_file_not_found_exit2")


if __name__ == "__main__":
    tests = [
        test_no_leak,
        test_main_name_leak,
        test_alias_leak,
        test_setting_leak,
        test_single_char_skip,
        test_empty_term_list,
        test_markdown_table_parsing,
        test_alias_column_leak,
        test_file_not_found_exit2,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: UNEXPECTED ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {len(tests) - failed}/{len(tests)} passed")
    if failed:
        sys.exit(1)
    print("All tests passed!")
