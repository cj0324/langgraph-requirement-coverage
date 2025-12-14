import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from ..state import CoverageState

EVAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 QA 커버리지 리뷰어다.\n"
     "입력으로 requirements, testcases, 그리고 req↔tc 매핑이 주어진다.\n\n"
     "각 Requirement에 대해, 매핑된 TestCase의 steps/expected를 근거로\n"
     "요구사항이 '실제로 충분히 검증되는지'를 STRICT 기준으로 판단하라.\n\n"
     "STRICT 기준 정의:\n"
     "- covered: 요구사항의 핵심 기능 + 중요한 예외/부정 케이스/경계 조건까지 합리적으로 검증됨\n"
     "- partial: 핵심(happy-path)은 있으나 중요한 예외/부정/경계 검증이 부족함\n"
     "- not_covered: 매핑된 TC가 없거나, TC 내용이 요구사항 검증과 무관함\n"
     "- unclear: TC/요구사항 서술이 너무 모호하여 판단 불가\n\n"
     "반드시 아래 JSON 형식으로만 출력해라(추가 텍스트 금지).\n"
     "{{\n"
     '  "per_requirement": {{\n'
     '    "REQ-001": {{\n'
     '      "status": "covered|partial|not_covered|unclear",\n'
     '      "matched_tc_ids": ["TC-101"],\n'
     '      "gaps": ["빠진 검증 포인트(예: 실패 케이스, 경계조건 등)"],\n'
     '      "notes": "판단 근거(짧게)",\n'
     '      "confidence": 0.0\n'
     "    }}\n"
     "  }},\n"
     '  "summary": {{\n'
     '    "covered": [],\n'
     '    "partial": [],\n'
     '    "not_covered": [],\n'
     '    "unclear": [],\n'
     '    "coverage_rate_strict": 0.0\n'
     "  }}\n"
     "}}\n\n"
     "- coverage_rate_strict는 covered만 커버로 계산\n"
     "- confidence는 0~1\n"
     ),
    ("human",
     "requirements:\n{requirements}\n\n"
     "testcases:\n{testcases}\n\n"
     "req_tc_mapping:\n{mapping}\n")
])


def _index_testcases(testcases: List[dict]) -> Dict[str, dict]:
    return {tc["tc_id"]: tc for tc in testcases}

def _chunk(lst: List[Any], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

def evaluate_coverage_llm(state: CoverageState, llm) -> CoverageState:
    reqs_all = state["requirements"]
    tcs = state["testcases"]
    mapping = state["req_tc_mapping"]

    batch_size = int(state.get("batch_size", 10))  # 기본 10개
    tc_by_id = _index_testcases(tcs)

    merged_per_req: Dict[str, Any] = {}

    # requirements를 batch로 나눠서 평가
    for req_batch in _chunk(reqs_all, batch_size):
        # batch에 포함된 requirement들에 매핑된 testcase만 추려서 LLM에 제공 (토큰 절약)
        used_tc_ids = set()
        mapping_batch = {}
        for r in req_batch:
            rid = r["req_id"]
            tc_ids = mapping.get(rid, [])
            mapping_batch[rid] = tc_ids
            for tc_id in tc_ids:
                used_tc_ids.add(tc_id)

        used_tcs = [tc_by_id[tc_id] for tc_id in used_tc_ids if tc_id in tc_by_id]

        resp = (EVAL_PROMPT | llm).invoke({
            "requirements": json.dumps(req_batch, ensure_ascii=False),
            "testcases": json.dumps(used_tcs, ensure_ascii=False),
            "mapping": json.dumps(mapping_batch, ensure_ascii=False),
        }).content

        result: Dict[str, Any] = json.loads(resp)
        per_req = result.get("per_requirement", {})

        # batch 결과를 merge
        merged_per_req.update(per_req)

    # --- 전체 summary를 우리가 다시 계산 (STRICT) ---
    covered, partial, not_covered, unclear = [], [], [], []
    for r in reqs_all:
        rid = r["req_id"]
        info = merged_per_req.get(rid, {})
        status = info.get("status", "unclear")
        if status == "covered":
            covered.append(rid)
        elif status == "partial":
            partial.append(rid)
        elif status == "not_covered":
            not_covered.append(rid)
        else:
            unclear.append(rid)

    total = len(reqs_all) if reqs_all else 0
    strict_rate = (len(covered) / total) if total else 0.0

    llm_coverage = {
        "per_requirement": merged_per_req,
        "summary": {
            "covered": covered,
            "partial": partial,
            "not_covered": not_covered,
            "unclear": unclear,
            "coverage_rate_strict": strict_rate,
            "batch_size": batch_size,
            "total_requirements": total,
        },
    }

    return {
        **state,
        "llm_coverage": llm_coverage,
        "per_requirement_eval": merged_per_req,
        "covered_requirements": covered,
        "partial_requirements": partial,
        "uncovered_requirements": not_covered,
        "unclear_requirements": unclear,
        "coverage_rate_strict": strict_rate,
    }