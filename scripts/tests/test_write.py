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


def test_validate_output_target_words_pass():
    """字数达标通过（90%-130%范围内）"""
    text = "这是一段正常的章节内容。" * 100  # ~1200 chars, within 90%-130% of 1000
    valid, reason = validate_output(text, target_words=1000)
    assert valid is True
    print("✓ test_validate_output_target_words_pass")


def test_validate_output_target_words_fail():
    """字数不达标"""
    text = "短内容。" * 50  # ~150 chars content
    valid, reason = validate_output(text, target_words=2000)
    assert valid is False
    assert "word count" in reason
    print("✓ test_validate_output_target_words_fail")


def test_validate_output_target_words_zero():
    """target_words=0 跳过字数检查"""
    text = "这是一段正常的章节内容。" * 20  # 足够长过 200 char minimum
    valid, reason = validate_output(text, target_words=0)
    assert valid is True
    print("✓ test_validate_output_target_words_zero")


def test_validate_output_target_words_too_high():
    """字数超标（>130%）不通过"""
    text = "这是一段很长的章节内容，每个字都算数。" * 100  # ~1800 chars content
    valid, reason = validate_output(text, target_words=1000)
    assert valid is False
    assert "too high" in reason
    print("✓ test_validate_output_target_words_too_high")


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
        test_validate_output_target_words_pass,
        test_validate_output_target_words_fail,
        test_validate_output_target_words_too_high,
        test_validate_output_target_words_zero,
        test_validate_output_target_words_too_high,
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
