#!/usr/bin/env python3
"""
gemini_client.py — 共用的 Vertex AI Gemini API 客户端。
被 write-chapter.py 和 review-chapter.py 共同使用。

提供：
  - load_config(): 加载 model-config.json
  - get_credentials(): 获取 Vertex AI 认证
  - call_gemini(): 调用 Gemini API
"""
import json
import os
import sys
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as AuthRequest


def load_config(config_file=None):
    """加载 model-config.json。
    如果未指定路径，使用 scripts/model-config.json。
    """
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path(__file__).parent / "model-config.json"

    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(3)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_credentials(config):
    """获取 Vertex AI 服务账号认证。

    认证文件查找顺序：
    1. config 中的 key_file 字段
    2. GOOGLE_APPLICATION_CREDENTIALS 环境变量

    返回 google.oauth2.service_account.Credentials 对象（已刷新）。
    失败时 sys.exit(3)。
    """
    key_file = config.get("key_file", "") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not key_file or not Path(key_file).exists():
        print("ERROR: Key file not found. Set GOOGLE_APPLICATION_CREDENTIALS or add key_file to config.", file=sys.stderr)
        sys.exit(3)

    try:
        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(AuthRequest())
        return creds
    except Exception as e:
        print(f"ERROR: Auth failed: {e}", file=sys.stderr)
        sys.exit(3)


def call_gemini(config, creds, system_prompt, user_prompt, gen_config=None):
    """调用 Gemini API，返回 (text, input_tokens, output_tokens)。

    参数：
      config: model-config.json 内容
      creds: 认证凭据
      system_prompt: 系统提示词（可为空字符串）
      user_prompt: 用户消息
      gen_config: 可选的 generationConfig 覆盖（dict）
    """
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

    # 默认生成配置
    if gen_config is None:
        temp = config.get("temperature", 1.0)
        max_tokens = config.get("max_output_tokens", 16384)
        gen_config = {
            "temperature": float(temp) if temp and isinstance(temp, (int, float)) else 1.0,
            "maxOutputTokens": int(max_tokens) if max_tokens and isinstance(max_tokens, (int, float)) else 16384,
        }
        # Flash 支持 thinkingBudget=0，Pro 不支持
        if "flash" in model.lower():
            gen_config["thinkingConfig"] = {"thinkingBudget": 0}

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": gen_config,
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    timeout_val = config.get("timeout", 180)
    timeout = int(timeout_val) if timeout_val and isinstance(timeout_val, (int, float)) and timeout_val > 0 else 180
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    result = resp.json()

    # Check SAFETY
    candidates = result.get("candidates", [])
    if not candidates:
        block_reason = result.get("promptFeedback", {}).get("blockReason", "")
        if block_reason:
            raise SafetyBlockError(f"SAFETY block: {block_reason}")
        raise ValueError("No candidates in response")

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason", "")
    if finish_reason == "SAFETY":
        raise SafetyBlockError("SAFETY filter triggered")

    text = candidate["content"]["parts"][0]["text"]
    usage = result.get("usageMetadata", {})
    return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


class SafetyBlockError(Exception):
    """Gemini SAFETY filter triggered."""
    pass
