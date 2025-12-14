from ..state import CoverageState

def evaluate_coverage(state: CoverageState) -> CoverageState:
    mapping = state["req_tc_mapping"]
    req_ids = [r["req_id"] for r in state["requirements"]]

    covered, uncovered = [], []
    weak, over_tested = [], []

    for rid in req_ids:
        matched = mapping.get(rid, [])

        if not matched:
            uncovered.append(rid)
        else:
            covered.append(rid)

            # ✅ 정책 예시: TC 1개면 약함(weak)
            if len(matched) == 1:
                weak.append(rid)

            # ✅ 정책 예시: 5개 이상이면 과다(over-tested)
            if len(matched) >= 5:
                over_tested.append(rid)

    rate = 0.0 if not req_ids else (len(covered) / len(req_ids))

    return {
        **state,
        "covered_requirements": covered,
        "uncovered_requirements": uncovered,
        "weak_requirements": weak,
        "over_tested_requirements": over_tested,
        "coverage_rate": rate,
    }
