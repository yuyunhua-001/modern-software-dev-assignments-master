from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from .. import db
from ..services.extract import (
    extract_key_challenges_llm,
    extract_test_factors_llm,
    understand_requirements_llm,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-factors", tags=["test-factors"])


def _hint_from_payload(payload: Dict[str, Any]) -> str | None:
    raw = payload.get("hint")
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


@router.post("/analyze")
def analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    """同时执行「理解需求」「提取测试因子」「提取关键难点」，并行调用 LLM。"""
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    hint = _hint_from_payload(payload)

    # 多个 LLM 任务并行执行以缩短等待
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_understand = pool.submit(understand_requirements_llm, text, hint)
        future_factors = pool.submit(extract_test_factors_llm, text, hint)
        future_challenges = pool.submit(extract_key_challenges_llm, text, hint)

        try:
            req_points = future_understand.result()
        except Exception as e:
            logger.warning("understand_requirements_llm failed (%s)", e)
            req_points = []

        try:
            factors = future_factors.result()
        except Exception as e:
            logger.warning("extract_test_factors_llm failed (%s), no factors returned", e)
            factors = []

        try:
            key_challenges = future_challenges.result()
        except Exception as e:
            logger.warning("extract_key_challenges_llm failed (%s), no key challenges returned", e)
            key_challenges = []

    ids = db.insert_test_factors(factors, doc_id=None)
    return {
        "doc_id": None,
        "requirements": req_points,
        "factors": [{"id": i, "factor": f} for i, f in zip(ids, factors)],
        "key_challenges": key_challenges,
    }


@router.post("/extract")
def extract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """提取测试因子与关键难点（不含结构化需求理解）。"""
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    hint = _hint_from_payload(payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        future_factors = pool.submit(extract_test_factors_llm, text, hint)
        future_challenges = pool.submit(extract_key_challenges_llm, text, hint)
        try:
            factors = future_factors.result()
        except Exception as e:
            logger.warning("extract_test_factors_llm failed (%s), no factors returned", e)
            factors = []
        try:
            key_challenges = future_challenges.result()
        except Exception as e:
            logger.warning("extract_key_challenges_llm failed (%s), no key challenges returned", e)
            key_challenges = []

    ids = db.insert_test_factors(factors, doc_id=None)
    return {
        "doc_id": None,
        "factors": [{"id": i, "factor": f} for i, f in zip(ids, factors)],
        "key_challenges": key_challenges,
    }


@router.get("")
def list_all(doc_id: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = db.list_test_factors(doc_id=doc_id)
    return [
        {
            "id": r["id"],
            "doc_id": r["doc_id"],
            "factor": r["factor"],
            "covered": bool(r["covered"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.post("/{factor_id}/covered")
def mark_covered(factor_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """标记测试因子是否已设计用例。"""
    covered = bool(payload.get("covered", True))
    db.mark_test_factor_covered(factor_id, covered)
    return {"id": factor_id, "covered": covered}
