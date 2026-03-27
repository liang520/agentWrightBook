#!/usr/bin/env python3
"""review-chapter.py 可测逻辑的单元测试（不 mock API）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

review_mod = import_module("review-chapter")
extract_json = review_mod.extract_json
validate_review = review_mod.validate_review


def test_extract_json_direct():
    """直接 JSON 文本"""
    text = '{"scores": {"character": 8, "style": 7, "continuity": 9, "hook": 8, "overall": 8}, "issues": [], "passed": true}'
    result = extract_json(text)
    assert result is not None
    assert result["scores"]["overall"] == 8
    print("✓ test_extract_json_direct")


def test_extract_json_code_block():
    """从 ```json ... ``` 代码块提取"""
    text = """一些说明文字。

```json
{"scores": {"character": 7, "style": 6, "continuity": 8, "hook": 7, "overall": 7}, "issues": ["问题1"], "passed": true}
```

更多说明。"""
    result = extract_json(text)
    assert result is not None
    assert result["scores"]["overall"] == 7
    assert len(result["issues"]) == 1
    print("✓ test_extract_json_code_block")


def test_extract_json_plain_code_block():
    """从 ``` ... ``` 代码块提取（无 json 标记）"""
    text = """```
{"scores": {"character": 5, "style": 4, "continuity": 6, "hook": 3, "overall": 5}, "issues": ["差"], "passed": false}
```"""
    result = extract_json(text)
    assert result is not None
    assert result["scores"]["overall"] == 5
    print("✓ test_extract_json_plain_code_block")


def test_extract_json_invalid():
    """无法解析的文本"""
    text = "这不是JSON，只是普通文本。"
    result = extract_json(text)
    assert result is None
    print("✓ test_extract_json_invalid")


def test_validate_review_valid():
    """合法的审查结果"""
    data = {
        "scores": {"character": 8, "style": 7, "continuity": 9, "hook": 8, "overall": 8},
        "issues": ["问题1"],
        "passed": True,
    }
    assert validate_review(data) is True
    print("✓ test_validate_review_valid")


def test_validate_review_partial_dims():
    """部分维度（≥1个有 overall）→ 宽松接受"""
    data = {
        "scores": {"character": 8, "style": 7, "overall": 8},  # 缺 continuity, hook
        "issues": [],
    }
    assert validate_review(data) is True  # 宽松模式：有 overall 就接受
    print("✓ test_validate_review_partial_dims")


def test_validate_review_flat_scores():
    """展平格式（scores 不在嵌套 dict 里）→ fallback 接受"""
    data = {"character": 7, "style": 8, "continuity": 6, "hook": 7, "overall": 7, "issues": []}
    assert validate_review(data) is True
    assert "scores" in data  # fallback 应该创建 scores 字段
    assert data["scores"]["overall"] == 7
    print("✓ test_validate_review_flat_scores")


def test_validate_review_auto_average():
    """部分维度无 overall → 自动计算平均"""
    data = {"scores": {"character": 8, "style": 6}}
    assert validate_review(data) is True
    assert data["scores"]["overall"] == 7.0  # (8+6)/2
    print("✓ test_validate_review_auto_average")


def test_validate_review_non_numeric():
    """非数字分数但有数字 overall → 宽松接受"""
    data = {
        "scores": {"character": "high", "style": 7, "continuity": 9, "hook": 8, "overall": 8},
        "issues": [],
    }
    assert validate_review(data) is True  # 有数字 overall 就接受
    print("✓ test_validate_review_non_numeric")


def test_score_boundary_pass():
    """边界：overall=6 → passed=true"""
    data = {"scores": {"character": 6, "style": 6, "continuity": 6, "hook": 6, "overall": 6}}
    assert validate_review(data) is True
    # 模拟 passed 计算
    assert data["scores"]["overall"] >= 6
    print("✓ test_score_boundary_pass")


def test_score_boundary_fail():
    """边界：overall=5 → passed=false"""
    data = {"scores": {"character": 5, "style": 5, "continuity": 5, "hook": 5, "overall": 5}}
    assert validate_review(data) is True  # 格式有效
    assert data["scores"]["overall"] < 6  # 但不通过
    print("✓ test_score_boundary_fail")


if __name__ == "__main__":
    tests = [
        test_extract_json_direct,
        test_extract_json_code_block,
        test_extract_json_plain_code_block,
        test_extract_json_invalid,
        test_validate_review_valid,
        test_validate_review_partial_dims,
        test_validate_review_flat_scores,
        test_validate_review_auto_average,
        test_validate_review_non_numeric,
        test_score_boundary_pass,
        test_score_boundary_fail,
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
