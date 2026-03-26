#!/usr/bin/env python3
"""write-chapter.py 可测逻辑的单元测试（不 mock API）"""
import sys
from pathlib import Path

# Add parent to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

# Import the module
write_mod = import_module("write-chapter")
parse_prompt = write_mod.parse_prompt
validate_output = write_mod.validate_output


def test_parse_prompt_both_sections():
    """解析包含 SYSTEM 和 USER 的 prompt"""
    text = """=== SYSTEM ===
你是一位网文作家。
=== USER ===
请写第10章。"""
    system, user = parse_prompt(text)
    assert system == "你是一位网文作家。", f"system={system!r}"
    assert user == "请写第10章。", f"user={user!r}"
    print("✓ test_parse_prompt_both_sections")


def test_parse_prompt_user_only():
    """只有 USER 部分"""
    text = """=== USER ===
请写一个章节。"""
    system, user = parse_prompt(text)
    assert system == "", f"system={system!r}"
    assert user == "请写一个章节。", f"user={user!r}"
    print("✓ test_parse_prompt_user_only")


def test_parse_prompt_no_markers():
    """没有标记，全部当 user"""
    text = "直接写内容，没有标记。"
    system, user = parse_prompt(text)
    assert system == ""
    assert user == "直接写内容，没有标记。"
    print("✓ test_parse_prompt_no_markers")


def test_parse_prompt_system_only():
    """只有 SYSTEM 部分"""
    text = """=== SYSTEM ===
仅系统提示。"""
    system, user = parse_prompt(text)
    assert system == "仅系统提示。"
    assert user == ""
    print("✓ test_parse_prompt_system_only")


def test_validate_output_valid():
    """正常输出通过验证"""
    text = "这是一段正常的章节内容。" * 20  # 足够长
    valid, reason = validate_output(text)
    assert valid is True
    print("✓ test_validate_output_valid")


def test_validate_output_empty():
    """空输出不通过"""
    valid, reason = validate_output("")
    assert valid is False
    assert "empty" in reason
    print("✓ test_validate_output_empty")


def test_validate_output_too_short():
    """过短输出不通过"""
    valid, reason = validate_output("太短了。")
    assert valid is False
    assert "short" in reason
    print("✓ test_validate_output_too_short")


def test_validate_output_none():
    """None 输出不通过"""
    valid, reason = validate_output(None)
    assert valid is False
    print("✓ test_validate_output_none")


if __name__ == "__main__":
    tests = [
        test_parse_prompt_both_sections,
        test_parse_prompt_user_only,
        test_parse_prompt_no_markers,
        test_parse_prompt_system_only,
        test_validate_output_valid,
        test_validate_output_empty,
        test_validate_output_too_short,
        test_validate_output_none,
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
