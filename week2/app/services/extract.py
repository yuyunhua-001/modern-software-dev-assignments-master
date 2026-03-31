from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List
import json
from typing import Any
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 必须在导入 ollama 之前设置，否则公司代理会拦截 localhost 请求
os.environ["NO_PROXY"] = "*"
load_dotenv()

from ollama import Client

# 使用 trust_env=False 绕过代理，直连本地 Ollama（公司网络代理会返回 504）
LLM_TIMEOUT_SECONDS = int(os.environ.get("OLLAMA_EXTRACT_TIMEOUT", "300"))
_ollama_client = Client(
    host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
    trust_env=False,
    timeout=httpx.Timeout(LLM_TIMEOUT_SECONDS),
)


# Schema for LLM structured output: JSON array of strings (test factors / key challenges)
class TestFactorsResponse(BaseModel):
    items: list[str]


class KeyChallengesResponse(BaseModel):
    items: list[str]


class RequirementPoint(BaseModel):
    category: str   # 模块/分类，如"权限"、"数据校验"
    summary: str    # 一句话描述该条需求


class UnderstandResponse(BaseModel):
    points: list[RequirementPoint]


def _compose_user_message(requirements_text: str, hint: str | None = None) -> str:
    """将需求正文与用户补充提示合并为发给模型的 user 消息。"""
    body = requirements_text.strip()
    h = (hint or "").strip()
    if not h:
        return body
    return f"【用户补充提示】\n{h}\n\n【需求文档】\n{body}"


UNDERSTAND_PROMPT = """You are a senior BA (business analyst). Given a raw requirements document (which may be informal, verbose, or written in Chinese/English), restructure it into clear, concise, structured requirement points.

## 理解需求，识别核心需求
- **功能要求**：核心功能、算法逻辑、业务规则，识别其中涉及的对象和它们之间的关系。
- **核心考点**：需要深入推理的逻辑，复杂的时间或操作顺序演进等。

Each point must have:
- "category": the module or concern area (e.g. "权限管理", "数据校验", "业务流程", "Performance")
- "summary": one concise sentence describing the requirement

Return a JSON object: {"points": [{"category": "...", "summary": "..."}, ...]}
Support both Chinese and English. Preserve all key constraints (numbers, conditions, roles).
Return only valid JSON, no extra text."""

TEST_FACTORS_PROMPT = """You are a senior software test engineer. Given a requirements document, identify the 3–5 MOST CRITICAL test factors for test case design.

### 测试因子分析
- 识别关键测试因子
- 注意：不仅仅是明面上的参数，更关键的推理识别出隐含的因子。

A test factor is an independent testable dimension, such as: file format, user permission, data size limit, redirect behavior, session state, etc.

Rules:
- Extract only 3–5 factors total — prioritize the most impactful ones.
- Each factor is a dimension/variable, NOT a specific value or boundary point.
  WRONG: "File size: 0B, 2MB, 2MB+1B" (those are test values, not a factor)
  RIGHT: "文件大小限制" or "File size limit"
- Keep each factor concise: 4–15 words, no examples or values inside the factor name.
- Include implicit factors (e.g. "must be logged in" → "用户登录态" or "Authentication state").
- Support both Chinese and English. Match the language used in the document.

Return a JSON object: {"items": ["factor1", "factor2", ...]}
Return only valid JSON, no extra text."""

KEY_CHALLENGES_PROMPT = """You are a senior software architect and BA. Given a requirements document, identify exactly TWO key difficulties or risks: the hardest parts to implement, verify, or reason about.

### 关键难点
- Focus on: ambiguous rules, distributed/concurrent behavior, security or consistency edge cases, performance at scale, complex state machines, integration traps, or implicit constraints that are easy to get wrong.
- Do NOT repeat generic test factors; name *why* each point is hard (reasoning cost, coupling, or uncertainty).

Rules:
- Return **exactly 2** entries in "items" — the two most critical difficulties only.
- Each entry: one concise sentence, 12–40 words, Chinese or English matching the document.
- No numbering prefixes inside the strings; no duplicate themes.

Return a JSON object: {"items": ["difficulty1", "difficulty2"]}
Return only valid JSON, no extra text."""


def _extract_raw_json(text: str) -> str | None:
    """从 content 或 thinking 文本中找到第一个完整 JSON 对象并返回原始字符串。"""
    if not text:
        return None
    for m in re.finditer(r'\{', text):
        start = m.start()
        depth, i = 0, start
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        import json
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        break
        else:
            continue
    return None


def _call_ollama(system_prompt: str, user_text: str) -> str:
    """通用 Ollama 调用，返回 LLM 原始响应字符串（content 或 thinking）。"""
    use_think = os.environ.get("OLLAMA_THINK", "").lower() in ("1", "true", "yes")
    num_predict = 4096 if use_think else 2048
    response = _ollama_client.chat(
        model=os.environ.get("OLLAMA_MODEL", "qwen3.5:4b"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        think=use_think,
        options={"temperature": 0.3, "num_predict": num_predict},
    )
    raw = response.message.content or ""
    if not raw and hasattr(response.message, "thinking") and response.message.thinking:
        raw = response.message.thinking
    logger.info("LLM raw (%d chars): %s...", len(raw), raw[:200] if raw else "(empty)")
    return raw


def _extract_items_json(
    text: str,
    model_cls: type[BaseModel] = TestFactorsResponse,
) -> List[str] | None:
    """从文本中提取 {\"items\": [...]} 并解析为字符串列表。支持 content 或 thinking 字段。"""
    if not text or not text.strip():
        return None
    # 1. 查找完整 JSON 块，支持 {"items": 或 {\n  "items": 等带空白的格式
    for m in re.finditer(r'\{\s*"items"', text):
        start = m.start()
        depth, i = 0, start
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = model_cls.model_validate_json(text[start : i + 1])
                        return list(getattr(parsed, "items", []))
                    except Exception:
                        break
        else:
            continue
    # 2. 思考模型若被截断，尝试从 "Item N: xxx" 或 "N. xxx" 模式提取
    for pattern in (
        r"[Ii]tem\s+\d+\s*[.:]\s*([^\n*]+)",
        r"^\s*\d+[.)]\s*(.+?)(?=\n|$)",
    ):
        items = re.findall(pattern, text, re.MULTILINE)
        if items:
            cleaned = [s.strip().strip(".-").strip() for s in items if len(s.strip()) > 2]
            if cleaned:
                return cleaned
    return None


def _extract_json_from_text(text: str) -> List[str] | None:
    """从文本中提取 JSON 并解析为 test factors（与 _extract_items_json 等价）。"""
    return _extract_items_json(text, TestFactorsResponse)


def _call_test_factors(text: str, hint: str | None = None) -> List[str]:
    """调用 LLM 提取测试因子，返回字符串列表。"""
    raw = _call_ollama(TEST_FACTORS_PROMPT, _compose_user_message(text, hint))
    items = _extract_json_from_text(raw)
    if items is None:
        logger.warning("LLM response has no valid items JSON")
        return []
    logger.info("LLM test factors: %s", items)
    return items


def _call_key_challenges(text: str, hint: str | None = None) -> List[str]:
    """调用 LLM 提取关键难点，固定最多 2 条。"""
    raw = _call_ollama(KEY_CHALLENGES_PROMPT, _compose_user_message(text, hint))
    items = _extract_items_json(raw, KeyChallengesResponse)
    if items is None:
        logger.warning("LLM response has no valid key challenges items JSON")
        return []
    cleaned = [s.strip() for s in items if isinstance(s, str) and s.strip()]
    out = cleaned[:2]
    logger.info("LLM key challenges: %s", out)
    return out


def _call_understand(text: str, hint: str | None = None) -> List[dict]:
    """调用 LLM 理解需求，返回结构化需求点列表 [{"category": ..., "summary": ...}]。"""
    raw = _call_ollama(UNDERSTAND_PROMPT, _compose_user_message(text, hint))
    json_str = _extract_raw_json(raw)
    if not json_str:
        logger.warning("LLM understand response has no JSON")
        return []
    try:
        parsed = UnderstandResponse.model_validate_json(json_str)
        return [{"category": p.category, "summary": p.summary} for p in parsed.points]
    except Exception as e:
        logger.warning("Failed to parse understand response: %s", e)
        return []


def _run_with_timeout(fn, *args):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args)
        try:
            return future.result(timeout=LLM_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            raise TimeoutError(f"Ollama did not respond within {LLM_TIMEOUT_SECONDS}s") from None


def _normalize_hint(hint: str | None) -> str | None:
    if hint is None:
        return None
    s = str(hint).strip()
    return s if s else None


def extract_test_factors_llm(text: str, hint: str | None = None) -> List[str]:
    """Extract test factors from requirements document using an LLM (Ollama)."""
    if not text or not text.strip():
        return []
    return _run_with_timeout(_call_test_factors, text.strip(), _normalize_hint(hint))


def extract_key_challenges_llm(text: str, hint: str | None = None) -> List[str]:
    """Extract two key implementation/verification difficulties from requirements using an LLM (Ollama)."""
    if not text or not text.strip():
        return []
    return _run_with_timeout(_call_key_challenges, text.strip(), _normalize_hint(hint))


def understand_requirements_llm(text: str, hint: str | None = None) -> List[dict]:
    """Restructure raw requirements into structured points using an LLM (Ollama)."""
    if not text or not text.strip():
        return []
    return _run_with_timeout(_call_understand, text.strip(), _normalize_hint(hint))
