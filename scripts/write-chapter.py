#!/usr/bin/env python3
"""
write-chapter.py — 调用 Gemini 生成仿写章节。
使用 Vertex AI 服务账号认证。

接口：--prompt-file --output-file [--config-file] [--target-words]
Exit codes:
  0 = 成功
  1 = 生成失败（空/短/API错误，已重试3次）
  2 = SAFETY 过滤
  3 = 认证失败（密钥文件不存在或无效）
"""
import argparse
import re
import sys
import time
from pathlib import Path

from gemini_client import load_config, get_credentials, call_gemini, SafetyBlockError


def parse_prompt(prompt_text):
    """解析 prompt 文件，提取 SYSTEM 和 USER 部分。

    格式：
      === SYSTEM ===
      系统提示词...
      === USER ===
      用户消息...
    """
    system_part = ""
    user_part = ""

    if "=== SYSTEM ===" in prompt_text:
        after_system = prompt_text.split("=== SYSTEM ===", 1)[1]
        if "=== USER ===" in after_system:
            system_part = after_system.split("=== USER ===", 1)[0].strip()
            user_part = after_system.split("=== USER ===", 1)[1].strip()
        else:
            system_part = after_system.strip()
    elif "=== USER ===" in prompt_text:
        user_part = prompt_text.split("=== USER ===", 1)[1].strip()
    else:
        # 没有标记，全部当作 user message
        user_part = prompt_text.strip()

    return system_part, user_part


def validate_output(text, target_words=0):
    """验证输出：非空、非过短、有效 UTF-8、字数达标"""
    if not text or not text.strip():
        return False, "empty response"
    # 去除空白后至少 200 字符（约 100 汉字）
    cleaned = text.strip()
    if len(cleaned) < 200:
        return False, f"too short ({len(cleaned)} chars)"
    # 字数检查：去除空白和 Markdown 标记后的字符数
    if target_words > 0:
        content = re.sub(r"[#*\->\|`\[\]()!]", "", cleaned)
        content = re.sub(r"\s+", "", content)
        char_count = len(content)
        min_chars = int(target_words * 0.9)
        max_chars = int(target_words * 1.3)
        if char_count < min_chars:
            return False, f"word count too low ({char_count} chars, need >= {min_chars})"
        if char_count > max_chars:
            return False, f"word count too high ({char_count} chars, need <= {max_chars})"
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="Gemini chapter writer")
    parser.add_argument("--prompt-file", required=True, help="Prompt file path")
    parser.add_argument("--output-file", required=True, help="Output file path")
    parser.add_argument(
        "--config-file",
        default=None,
        help="model-config.json path (default: scripts/model-config.json)",
    )
    parser.add_argument(
        "--target-words",
        type=int,
        default=0,
        help="Target word count. If set, output must be >= 90%% of this value.",
    )
    args = parser.parse_args()

    config = load_config(args.config_file)
    creds = get_credentials(config)

    # Read prompt
    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        print(f"ERROR: [write-chapter] Prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)

    prompt_text = prompt_path.read_text(encoding="utf-8")
    system_prompt, user_prompt = parse_prompt(prompt_text)

    if not user_prompt:
        print("ERROR: [write-chapter] Empty user prompt", file=sys.stderr)
        sys.exit(1)

    # Retry loop: 3 attempts with backoff
    backoff = [2, 8, 30]
    for attempt in range(3):
        try:
            text, in_tok, out_tok = call_gemini(config, creds, system_prompt, user_prompt)
            valid, reason = validate_output(text, target_words=args.target_words)
            if valid:
                # Write output
                output_path = Path(args.output_file)
                output_path.write_text(text, encoding="utf-8")
                print(
                    f"OK: {len(text)} chars, {in_tok} in / {out_tok} out tokens",
                    file=sys.stderr,
                )
                sys.exit(0)
            else:
                print(
                    f"ERROR: [write-chapter] Attempt {attempt+1}/3: {reason}",
                    file=sys.stderr,
                )
        except SafetyBlockError as e:
            print(f"ERROR: [write-chapter] {e}", file=sys.stderr)
            sys.exit(2)
        except SystemExit:
            raise  # Don't catch our own exit calls
        except Exception as e:
            print(
                f"ERROR: [write-chapter] Attempt {attempt+1}/3: {e}",
                file=sys.stderr,
            )

        if attempt < 2:
            time.sleep(backoff[attempt])

    # All retries exhausted
    print("ERROR: [write-chapter] All 3 attempts failed", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
