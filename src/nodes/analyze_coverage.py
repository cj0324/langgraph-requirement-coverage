from ..state import CoverageState

def analyze_coverage(state: CoverageState) -> CoverageState:
    mapping = state["req_tc_mapping"]
    req_ids = [r["req_id"] for r in state["requirements"]]

    covered = []
    uncovered = []
    weak = []
    over_tested = []

    for rid in req_ids:
        tcs = mapping.get(rid, [])

        if not tcs:
            uncovered.append(rid)
        else:
            covered.append(rid)
            if len(tcs) == 1:
                weak.append(rid)
            if len(tcs) >= 5:
                over_tested.append(rid)

    coverage_rate = len(covered) / len(req_ids) if req_ids else 0

    return {
        **state,
        "covered_requirements": covered,
        "uncovered_requirements": uncovered,
        "weak_requirements": weak,
        "over_tested_requirements": over_tested,
        "coverage_rate": coverage_rate,
    }
