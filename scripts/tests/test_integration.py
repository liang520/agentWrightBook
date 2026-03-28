#!/usr/bin/env python3
"""
Dry-run integration test — validates file contracts between pipeline scripts
without calling any external APIs.

Tests that:
1. build-prompt.py output is parseable by write-chapter.py's parse_prompt()
2. verify-chapter.py accepts clean chapters and rejects leaked ones
3. The shared map_parser produces consistent results for both consumers
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

write_mod = import_module("write-chapter")
bp_mod = import_module("build-prompt")
map_parser = import_module("map_parser")

PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python3"
VERIFY_SCRIPT = Path(__file__).parent.parent / "verify-chapter.py"


def _setup_novel(tmp):
    """Create a minimal novel structure for integration testing."""
    novel = Path(tmp) / "novels" / "test-novel"
    source = Path(tmp) / "sources" / "test-source"

    # Config files
    config = novel / "config"
    config.mkdir(parents=True)

    (config / "style.md").write_text(
        "# 风格\n\n## 系统提示词\n你是一位网文作家。写出精彩的章节。\n",
        encoding="utf-8"
    )

    (config / "character-map.md").write_text(
        "| 原作角色 | 别名 | 新角色 |\n|---------|------|--------|\n| 林旻 | 小旻 | 沈知意 |\n| 周严非 | — | 陆时屿 |\n",
        encoding="utf-8"
    )

    (config / "setting-map.md").write_text(
        "| 原作 | 新设定 |\n|------|--------|\n| 八中 | 锦城六中 |\n",
        encoding="utf-8"
    )

    (config / "compression-map.md").write_text(
        "| 新章 | 原作章 | 策略 | 功能 | 目标字数 | 事件 | 起始 | 终止 |\n"
        "|------|--------|------|------|---------|------|------|------|\n"
        "| 1 | 001 | 保留 | 开篇 | 2000 | 引入主角 | E01 | E02 |\n"
        "| 2 | 002 | 保留 | 推进 | 1500 | 冲突 | E03 | E04 |\n",
        encoding="utf-8"
    )

    # Context files
    context = novel / "context"
    context.mkdir()
    (context / "memory-outline.md").write_text("全书大纲占位", encoding="utf-8")
    (context / "recent-context.md").write_text("最近上下文占位", encoding="utf-8")

    # Chapters dir
    (novel / "chapters").mkdir()

    # Source chapters
    src_chapters = source / "chapters"
    src_chapters.mkdir(parents=True)
    (src_chapters / "001.md").write_text(
        "\n".join([f"林旻在八中读书。第{i}行内容。" for i in range(100)]),
        encoding="utf-8"
    )

    return novel, source


def test_build_prompt_to_parse_prompt():
    """build-prompt output is parseable by write-chapter's parse_prompt."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, source = _setup_novel(tmp)
        output_file = Path(tmp) / "prompt.txt"

        # Build prompt (calling the function directly, not subprocess)
        # We need to simulate what main() does
        style_path = novel / "config" / "style.md"
        cmap_path = novel / "config" / "compression-map.md"
        char_path = novel / "config" / "character-map.md"
        set_path = novel / "config" / "setting-map.md"

        system_prompt = bp_mod.extract_style_system_prompt(style_path)
        ch_info = bp_mod.get_chapter_info(cmap_path, 1)
        replacements, replace_dict = bp_mod.extract_replacement_list(char_path, set_path)
        source_text = bp_mod.read_source_chapters(str(source), ch_info["source_chapters"])
        source_text = bp_mod.pre_replace_source_text(source_text, replace_dict)
        prev_chapter = bp_mod.read_prev_chapter(novel / "chapters", 1)

        # Assemble prompt (simplified version of main)
        prompt = f"""=== SYSTEM ===
{system_prompt}

=== USER ===
【字数硬要求】目标字数：{ch_info['target_words']}字。

【名词替换清单】
{chr(10).join(replacements)}

【写作任务】第1章
## 原作参考
{source_text}

## 前章内容
{prev_chapter}
"""
        output_file.write_text(prompt, encoding="utf-8")

        # Parse it with write-chapter's parser
        system_part, user_part = write_mod.parse_prompt(prompt)
        assert system_part, "System prompt should not be empty"
        assert "网文作家" in system_part, "System prompt should contain style content"
        assert user_part, "User prompt should not be empty"
        assert "字数" in user_part, "User prompt should contain word count requirement"
        assert "替换清单" in user_part, "User prompt should contain replacement list"

    print("✓ test_build_prompt_to_parse_prompt")


def test_source_pre_replacement_removes_originals():
    """Pre-replacement should remove all original names from source text."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, source = _setup_novel(tmp)

        char_path = novel / "config" / "character-map.md"
        set_path = novel / "config" / "setting-map.md"

        _, replace_dict = bp_mod.extract_replacement_list(char_path, set_path)
        source_text = bp_mod.read_source_chapters(str(source), "001")

        # Before replacement: should contain original names
        assert "林旻" in source_text, "Source should contain original name before replacement"
        assert "八中" in source_text, "Source should contain original setting before replacement"

        # After replacement
        replaced = bp_mod.pre_replace_source_text(source_text, replace_dict)
        assert "林旻" not in replaced, "Original name should be removed after replacement"
        assert "八中" not in replaced, "Original setting should be removed after replacement"
        assert "沈知意" in replaced, "New name should be present after replacement"
        assert "锦城六中" in replaced, "New setting should be present after replacement"

    print("✓ test_source_pre_replacement_removes_originals")


def test_shared_parser_consistency():
    """map_parser terms should be a superset of build-prompt replace_dict keys."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, source = _setup_novel(tmp)

        char_text = (novel / "config" / "character-map.md").read_text(encoding="utf-8")
        set_text = (novel / "config" / "setting-map.md").read_text(encoding="utf-8")

        # Shared parser: terms for leak scanning
        terms = map_parser.extract_original_terms(char_text, set_text)

        # Shared parser: replacement pairs for prompt building
        _, replace_dict = map_parser.extract_replacement_pairs(char_text, set_text)

        # Every key in replace_dict should be scannable by verify
        for key in replace_dict:
            assert key in terms, f"replace_dict key '{key}' not in verify terms — leak gap!"

    print("✓ test_shared_parser_consistency")


def test_verify_accepts_clean_chapter():
    """verify-chapter should accept a chapter with no original names."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, _ = _setup_novel(tmp)
        chapter_file = Path(tmp) / "clean_chapter.md"
        chapter_file.write_text("沈知意走进锦城六中，陆时屿在操场上打球。", encoding="utf-8")
        report_file = Path(tmp) / "report.json"

        result = subprocess.run(
            [str(PYTHON), str(VERIFY_SCRIPT),
             "--chapter-file", str(chapter_file),
             "--character-map", str(novel / "config" / "character-map.md"),
             "--setting-map", str(novel / "config" / "setting-map.md"),
             "--report-file", str(report_file)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}: {result.stderr}"

    print("✓ test_verify_accepts_clean_chapter")


def test_verify_rejects_leaked_chapter():
    """verify-chapter should reject a chapter containing original names."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, _ = _setup_novel(tmp)
        chapter_file = Path(tmp) / "leaked_chapter.md"
        chapter_file.write_text("林旻走进了八中的大门。", encoding="utf-8")
        report_file = Path(tmp) / "report.json"

        result = subprocess.run(
            [str(PYTHON), str(VERIFY_SCRIPT),
             "--chapter-file", str(chapter_file),
             "--character-map", str(novel / "config" / "character-map.md"),
             "--setting-map", str(novel / "config" / "setting-map.md"),
             "--report-file", str(report_file)],
            capture_output=True, text=True
        )
        assert result.returncode == 1, f"Expected exit 1, got {result.returncode}: {result.stderr}"

    print("✓ test_verify_rejects_leaked_chapter")


def test_pre_replaced_source_passes_verify():
    """Source text after pre-replacement should pass verify (the key integration point)."""
    with tempfile.TemporaryDirectory() as tmp:
        novel, source = _setup_novel(tmp)

        char_path = novel / "config" / "character-map.md"
        set_path = novel / "config" / "setting-map.md"

        _, replace_dict = bp_mod.extract_replacement_list(char_path, set_path)
        source_text = bp_mod.read_source_chapters(str(source), "001")
        replaced = bp_mod.pre_replace_source_text(source_text, replace_dict)

        # Write replaced source as if it were a chapter
        chapter_file = Path(tmp) / "replaced_source.md"
        chapter_file.write_text(replaced, encoding="utf-8")
        report_file = Path(tmp) / "report.json"

        result = subprocess.run(
            [str(PYTHON), str(VERIFY_SCRIPT),
             "--chapter-file", str(chapter_file),
             "--character-map", str(char_path),
             "--setting-map", str(set_path),
             "--report-file", str(report_file)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Pre-replaced source should pass verify, got exit {result.returncode}: {result.stderr}"

    print("✓ test_pre_replaced_source_passes_verify")


if __name__ == "__main__":
    tests = [
        test_build_prompt_to_parse_prompt,
        test_source_pre_replacement_removes_originals,
        test_shared_parser_consistency,
        test_verify_accepts_clean_chapter,
        test_verify_rejects_leaked_chapter,
        test_pre_replaced_source_passes_verify,
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
