from typing import Dict, List, TypedDict, Any

class CoverageState(TypedDict, total=False):
    objective: str
    plan: List[str]
    plan_feedback: str

    requirements: List[dict]
    testcases: List[dict]
    req_tc_mapping: Dict[str, List[str]]

    # ✅ LLM 평가 결과
    llm_coverage: Dict[str, Any]
    per_requirement_eval: Dict[str, Any]

    covered_requirements: List[str]
    partial_requirements: List[str]
    uncovered_requirements: List[str]
    unclear_requirements: List[str]

    coverage_rate_strict: float
