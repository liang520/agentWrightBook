#!/usr/bin/env python3
"""
review-chapter.py — 调用 Gemini 审查章节质量（5维度评分）。
使用 Vertex AI 服务账号认证。

接口：--review-context-file --report-file [--config-file]
Exit codes:
  0 = 审查完成（report-file 包含评分和 issues）
  1 = JSON 解析失败
  2 = API 调用失败 / 其他异常
"""
import json
import re
import sys
from pathlib import Path

import argparse
from gemini_client import load_config, get_credentials, call_gemini


def extract_json(text):
    """从响应文本中提取 JSON。

    尝试顺序：
    1. 直接解析整个文本
    2. 从 ```json ... ``` 代码块提取
    3. 从 ``` ... ``` 代码块提取
    """
    # 尝试直接解析
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown code block 提取
    patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    return None


def validate_review(data):
    """验证审查结果格式，宽松模式。"""
    if not isinstance(data, dict):
        return False
    scores = data.get("scores")
    if scores is None or not isinstance(scores, dict) or len(scores) == 0:
        # 尝试从顶层字段提取分数（Gemini 有时展平 scores）
        fallback_scores = {}
        for dim in ["character", "style", "continuity", "hook", "overall"]:
            if dim in data and isinstance(data[dim], (int, float)):
                fallback_scores[dim] = data[dim]
        if len(fallback_scores) >= 3:  # 至少3个维度就接受（宽松模式）
            data["scores"] = fallback_scores
            if "overall" not in fallback_scores:
                data["scores"]["overall"] = sum(fallback_scores.values()) / len(fallback_scores)
            print("WARNING: [review-chapter] Used fallback flat-scores extraction", file=sys.stderr)
            return True
        return False
    # 正常路径：至少有 overall
    if "overall" not in scores:
        if len(scores) > 0:
            data["scores"]["overall"] = sum(v for v in scores.values() if isinstance(v, (int, float))) / max(1, len([v for v in scores.values() if isinstance(v, (int, float))]))
            return True
        return False
    if not isinstance(scores["overall"], (int, float)):
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Gemini chapter reviewer")
    parser.add_argument("--review-context-file", required=True)
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--config-file", default=None)
    args = parser.parse_args()

    config = load_config(args.config_file)
    creds = get_credentials(config)

    # Read review context
    ctx_path = Path(args.review_context_file)
    if not ctx_path.exists():
        print(f"ERROR: [review-chapter] Context file not found: {ctx_path}", file=sys.stderr)
        sys.exit(2)

    review_context = ctx_path.read_text(encoding="utf-8")

    # System instruction for review
    system_instruction = (
        "你是一位严格的网文编辑。请严格按以下JSON格式输出，不要多余解释：\n"
        '{"scores":{"character":1-10,"style":1-10,"continuity":1-10,"hook":1-10,"overall":1-10},'
        '"issues":["问题1","问题2"]}\n'
        "scores必须包含character/style/continuity/hook/overall五个维度，每个1-10分。"
        "issues列出发现的问题。如果没有问题则为空数组[]。"
    )

    # Review-specific gen config
    review_gen_config = {
        "temperature": 0.3,
        "maxOutputTokens": 2048,
    }

    # Call Gemini
    try:
        text, in_tok, out_tok = call_gemini(
            config, creds, system_instruction, review_context,
            gen_config=review_gen_config
        )
        print(f"Review response: {in_tok} in / {out_tok} out tokens", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: [review-chapter] API call failed: {e}", file=sys.stderr)
        sys.exit(2)

    # Parse JSON
    data = extract_json(text)
    if data is None:
        print(f"ERROR: [review-chapter] JSON parse failed", file=sys.stderr)
        print(f"Raw response: {text[:500]}", file=sys.stderr)
        sys.exit(1)

    if not validate_review(data):
        print(f"ERROR: [review-chapter] Invalid review format: {json.dumps(data, ensure_ascii=False)[:300]}", file=sys.stderr)
        sys.exit(1)

    # Compute passed
    overall = data["scores"]["overall"]
    data["passed"] = overall >= 6

    # Write report
    Path(args.report_file).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: overall={overall}, passed={data['passed']}, issues={len(data.get('issues', []))}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
