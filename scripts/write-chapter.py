#!/usr/bin/env python3
"""
write-chapter.py — 调用 Gemini 生成仿写章节。
使用 Vertex AI 服务账号认证。

接口：--prompt-file --output-file [--config-file]
Exit codes:
  0 = 成功
  1 = 生成失败（空/短/API错误，已重试3次）
  2 = SAFETY 过滤
  3 = 认证失败（密钥文件不存在或无效）
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as AuthRequest


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


def load_config(config_file):
    """加载 model-config.json"""
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def call_gemini(config, creds, system_prompt, user_prompt):
    """调用 Gemini API，返回 (text, input_tokens, output_tokens)"""
    if not creds.valid:
        creds.refresh(AuthRequest())

    model = config["model"]
    project_id = config["project_id"]
    region = config["region"]
    api_url = (
        f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/{region}/publishers/google/models/{model}:generateContent"
    )

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    resp = requests.post(api_url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    result = resp.json()

    # Check SAFETY
    candidates = result.get("candidates", [])
    if not candidates:
        # Check if blocked by safety
        block_reason = result.get("promptFeedback", {}).get("blockReason", "")
        if block_reason:
            print(f"ERROR: [write-chapter] SAFETY block: {block_reason}", file=sys.stderr)
            sys.exit(2)
        raise ValueError("No candidates in response")

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason", "")
    if finish_reason == "SAFETY":
        print(f"ERROR: [write-chapter] SAFETY filter triggered", file=sys.stderr)
        sys.exit(2)

    text = candidate["content"]["parts"][0]["text"]
    usage = result.get("usageMetadata", {})
    return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


def validate_output(text):
    """验证输出：非空、非过短、有效 UTF-8"""
    if not text or not text.strip():
        return False, "empty response"
    # 去除空白后至少 200 字符（约 100 汉字）
    cleaned = text.strip()
    if len(cleaned) < 200:
        return False, f"too short ({len(cleaned)} chars)"
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
    args = parser.parse_args()

    # Resolve config file
    if args.config_file:
        config_path = Path(args.config_file)
    else:
        # Find config relative to this script
        config_path = Path(__file__).parent / "model-config.json"

    if not config_path.exists():
        print(f"ERROR: [write-chapter] Config file not found: {config_path}", file=sys.stderr)
        sys.exit(3)

    config = load_config(config_path)

    # Check key file: config key_file > GOOGLE_APPLICATION_CREDENTIALS env var
    key_file = config.get("key_file", "") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not key_file or not Path(key_file).exists():
        print(f"ERROR: [write-chapter] Key file not found. Set GOOGLE_APPLICATION_CREDENTIALS or add key_file to config.", file=sys.stderr)
        sys.exit(3)

    # Authenticate
    try:
        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(AuthRequest())
    except Exception as e:
        print(f"ERROR: [write-chapter] Auth failed: {e}", file=sys.stderr)
        sys.exit(3)

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
            valid, reason = validate_output(text)
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
