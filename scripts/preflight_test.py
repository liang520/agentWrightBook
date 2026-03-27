#!/usr/bin/env python3
"""
Pre-flight: 手动验证 Gemini 2.5 Flash 的中文网文写作 + 审查能力。
使用 Vertex AI 服务账号认证。

验收标准：
1. 写作：生成的章节可读、风格匹配、无原作名泄漏
2. 审查：5维度评分，reviewer 能捕获至少 1 个真实问题
"""
import json, sys, time
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as AuthRequest

# --- Config ---
KEY_FILE = Path('/Users/liang/CodeSelf/novelOrignal/googleKey.json')
PROJECT_ID = 'phoenix-browser'
REGION = 'us-central1'
MODEL = 'gemini-2.5-flash'
API_URL = (f'https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}'
           f'/locations/{REGION}/publishers/google/models/{MODEL}:generateContent')

REPO = Path('/Users/liang/CodeSelf/agentWrightBook')


def get_creds():
    creds = service_account.Credentials.from_service_account_file(
        str(KEY_FILE), scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    creds.refresh(AuthRequest())
    print(f"认证成功: {creds.service_account_email}")
    return creds


def call_gemini(creds, system_prompt, user_prompt, max_tokens=4096, thinking=False):
    if not creds.valid:
        creds.refresh(AuthRequest())
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json',
    }
    gen_config = {
        "temperature": 0.7,
        "maxOutputTokens": max_tokens,
    }
    if not thinking:
        gen_config["thinkingConfig"] = {"thinkingBudget": 0}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": gen_config,
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    result = resp.json()
    text = result['candidates'][0]['content']['parts'][0]['text']
    usage = result.get('usageMetadata', {})
    return text, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)


def test_write(creds):
    """测试 1: Gemini 写章节"""
    print("\n" + "="*60)
    print("TEST 1: 章节写作能力")
    print("="*60)

    style = (REPO / 'novels/campus-genius/config/style.md').read_text()
    char_map = (REPO / 'novels/campus-genius/config/character-map.md').read_text()
    setting_map = (REPO / 'novels/campus-genius/config/setting-map.md').read_text()
    source_ch = (REPO / 'sources/kjwd-sw/chapters/010.md').read_text()
    prev_ch_tail = (REPO / 'novels/campus-genius/chapters/009.md').read_text()[-500:]

    system_prompt = style.split('## 系统提示词')[-1].strip()

    user_prompt = f"""你正在仿写一部校园学霸逆袭小说。请根据以下原作章节，用新的角色和设定改写。

## 角色映射表
{char_map[:2000]}

## 设定映射表
{setting_map}

## 上一章结尾（衔接参考）
{prev_ch_tail}

## 原作第10章（需要改写的内容）
{source_ch}

## 要求
1. 严格使用映射表中的新角色名和新设定名，绝不能出现原作角色名
2. 保持第一人称（沈知意视角）
3. 风格：幽默吐槽、快节奏、章末必有钩子
4. 字数：800-1200字
5. 章节标题格式：# 第10章 [标题]
"""

    print("调用 Gemini 写作...")
    start = time.time()
    text, in_tok, out_tok = call_gemini(creds, system_prompt, user_prompt, thinking=True)
    elapsed = time.time() - start

    print(f"耗时: {elapsed:.1f}s | 输入: {in_tok} tokens | 输出: {out_tok} tokens")
    print(f"字数: {len(text)} 字符")
    print("\n--- 生成内容 ---")
    print(text)
    print("--- 结束 ---\n")

    # 检查原作名泄漏
    leak_terms = ['林旻', '孙书仪', '周严非', '萧领', '江既白', '宋小雪', '邹文', '古月',
                  '八中', '一中', '清华', '北大', '哈佛']
    leaks = [t for t in leak_terms if t in text]
    if leaks:
        print(f"⚠️ 发现原作名泄漏: {leaks}")
    else:
        print("✓ 无原作名泄漏")

    return text


def test_review(creds, chapter_text):
    """测试 2: Gemini 审查能力"""
    print("\n" + "="*60)
    print("TEST 2: 章节审查能力")
    print("="*60)

    style = (REPO / 'novels/campus-genius/config/style.md').read_text()
    char_map = (REPO / 'novels/campus-genius/config/character-map.md').read_text()[:2000]

    system_prompt = "你是一位严格的网文编辑，负责审查章节质量。"

    user_prompt = f"""请审查以下章节，从5个维度评分(0-10)并列出具体问题。

=== 风格要求 ===
{style[:1000]}

=== 角色映射 ===
{char_map}

=== 待审章节 ===
{chapter_text}

=== 审查任务 ===
请从以下5个维度评分(0-10)，并列出具体issues，输出JSON格式：
1. character: 角色是否符合映射表设定，有无名字泄漏
2. style: 是否符合风格要求（幽默吐槽、快节奏）
3. continuity: 情节连续性
4. hook: 章末是否有钩子
5. overall: 总体质量

输出格式（JSON）：
```json
{{
  "scores": {{"character": N, "style": N, "continuity": N, "hook": N, "overall": N}},
  "issues": ["问题1", "问题2", ...],
  "passed": true/false
}}
```
passed = true 当 overall >= 6
"""

    print("调用 Gemini 审查...")
    start = time.time()
    text, in_tok, out_tok = call_gemini(creds, system_prompt, user_prompt, max_tokens=2048)
    elapsed = time.time() - start

    print(f"耗时: {elapsed:.1f}s | 输入: {in_tok} tokens | 输出: {out_tok} tokens")
    print("\n--- 审查结果 ---")
    print(text)
    print("--- 结束 ---\n")

    # 尝试提取 JSON
    import re
    json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            scores = result.get('scores', {})
            issues = result.get('issues', [])
            passed = result.get('passed', False)
            print(f"评分: {scores}")
            print(f"passed: {passed}")
            print(f"issues 数量: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

            overall = scores.get('overall', 0)
            if overall >= 6:
                print(f"\n✓ overall={overall} ≥ 6，质量达标")
            else:
                print(f"\n⚠️ overall={overall} < 6，质量不达标")

            if len(issues) >= 1:
                print("✓ reviewer 发现了具体问题")
            else:
                print("⚠️ reviewer 未发现任何问题（可能是审查太宽松）")

            return result
        except json.JSONDecodeError:
            print("⚠️ JSON 解析失败")
    else:
        print("⚠️ 未找到 JSON 代码块")

    return None


def main():
    print("Pre-flight: Gemini 2.5 Flash 质量验证")
    print(f"Model: {MODEL}")
    print(f"Key: {KEY_FILE}")

    creds = get_creds()

    # Test 1: 写章节
    chapter = test_write(creds)

    # Test 2: 审查章节
    review = test_review(creds, chapter)

    # 总结
    print("\n" + "="*60)
    print("PRE-FLIGHT 总结")
    print("="*60)
    if review:
        overall = review.get('scores', {}).get('overall', 0)
        issues = review.get('issues', [])
        if overall >= 6 and len(issues) >= 1:
            print("✅ PASS: 写作质量达标 + 审查有效")
        elif overall >= 6:
            print("⚠️ PARTIAL: 写作达标但审查太宽松（未发现问题）")
        else:
            print("❌ FAIL: 写作质量不达标，需调整 prompt")
    else:
        print("❌ FAIL: 审查结果无法解析")


if __name__ == '__main__':
    main()
