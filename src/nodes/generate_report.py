import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from ..state import CoverageState


RECOMMEND_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 QA 테스트 설계 전문가다.\n"
     "입력으로 Requirement 요약과 gaps 리스트가 주어진다.\n"
     "각 gap을 '추가 테스트케이스 추천 항목'으로 변환하라.\n"
     "각 항목은 다음 필드를 가진 JSON 배열로만 출력해라(추가 텍스트 금지):\n"
     "[\n"
     "  {{\n"
     '    "title": "...",\n'
     '    "purpose": "...",\n'
     '    "suggested_steps": ["...", "..."],\n'
     '    "expected": "..."\n'
     "  }}\n"
     "]\n"
     "규칙:\n"
     "- title은 짧고 명확하게(20~40자)\n"
     "- purpose는 왜 필요한지 한 줄\n"
     "- suggested_steps는 3~6개\n"
     "- expected는 한 줄\n"
     "- gaps가 비어있으면 [] 출력\n"
     ),
    ("human",
     "REQ: {req_id}\n"
     "Title: {title}\n"
     "Description: {description}\n"
     "Status: {status}\n"
     "Gaps: {gaps}\n")
])



def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _status_emoji(status: str) -> str:
    return {
        "covered": "✅",
        "partial": "🟡",
        "not_covered": "❌",
        "unclear": "❓",
    }.get(status, "❓")


def generate_report(state: CoverageState, llm) -> CoverageState:
    requirements: List[dict] = state["requirements"]
    req_by_id: Dict[str, dict] = {r["req_id"]: r for r in requirements}

    per_eval: Dict[str, Any] = state.get("per_requirement_eval", {})
    strict_rate = state.get("coverage_rate_strict", 0.0)

    covered = set(state.get("covered_requirements", []))
    partial = set(state.get("partial_requirements", []))
    not_covered = set(state.get("uncovered_requirements", []))
    unclear = set(state.get("unclear_requirements", []))

    # --- 1) REQ별 status 표 데이터 만들기 ---
    rows: List[Tuple[str, str, float, str, str]] = []
    # (req_id, status, confidence, matched_tc_ids, notes)
    for rid in req_by_id.keys():
        info = per_eval.get(rid, {})
        status = info.get("status", "unclear")
        conf = _safe_float(info.get("confidence", 0.0), 0.0)
        matched = info.get("matched_tc_ids", [])
        notes = info.get("notes", "")

        rows.append((
            rid,
            status,
            conf,
            ", ".join(matched) if matched else "(none)",
            notes.replace("\n", " ").strip(),
        ))

    # --- 2) confidence 낮은 순으로 검토 우선순위 정렬 ---
    # 우선순위는 기본적으로 "낮은 confidence + 위험 status"가 위로 오게
    def priority_key(r: Tuple[str, str, float, str, str]):
        _, status, conf, _, _ = r
        status_rank = {"not_covered": 0, "partial": 1, "unclear": 2, "covered": 3}.get(status, 2)
        # status 먼저, 그 다음 confidence 오름차순
        return (status_rank, conf)

    rows_sorted = sorted(rows, key=priority_key)

    # --- 3) gaps -> 추가 TC 추천 항목 만들기 (partial/not_covered만) ---
    recommendations: Dict[str, List[dict]] = {}

    for rid, status, conf, matched, notes in rows_sorted:
        if status not in ("partial", "not_covered"):
            continue
        info = per_eval.get(rid, {})
        gaps = info.get("gaps", []) or []
        req = req_by_id[rid]

        # gaps가 없으면 굳이 LLM 호출하지 않음
        if not gaps:
            recommendations[rid] = []
            continue

        resp = (RECOMMEND_PROMPT | llm).invoke({
            "req_id": rid,
            "title": req.get("title", ""),
            "description": req.get("description", ""),
            "status": status,
            "gaps": json.dumps(gaps, ensure_ascii=False),
        }).content

        try:
            rec_items = json.loads(resp)
            if not isinstance(rec_items, list):
                rec_items = []
        except Exception:
            # JSON 깨졌으면 안전하게 비워두고, raw는 notes에 남길 수도 있음
            rec_items = []

        recommendations[rid] = rec_items

    # --- Markdown 리포트 생성 ---
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md: List[str] = []
    md.append("# Requirement Coverage Report (STRICT)\n")
    md.append(f"- Generated: **{now}**\n")
    md.append(f"- Strict Coverage(covered only): **{strict_rate * 100:.1f}%**\n")
    md.append(f"- Covered: {len(covered)} / {len(requirements)}\n")
    md.append(f"- Partial: {len(partial)} / {len(requirements)}\n")
    md.append(f"- Not Covered: {len(not_covered)} / {len(requirements)}\n")
    md.append(f"- Unclear: {len(unclear)} / {len(requirements)}\n")

    # (A) REQ별 status 표
    md.append("\n## 1) REQ Status Table\n")
    md.append("| Priority | REQ_ID | Status | Confidence | Matched TC | Notes |\n")
    md.append("|---:|---|---|---:|---|---|\n")
    for i, (rid, status, conf, matched, notes) in enumerate(rows_sorted, start=1):
        emoji = _status_emoji(status)
        md.append(f"| {i} | {rid} | {emoji} {status} | {conf:.2f} | {matched} | {notes} |\n")

    # (B) 검토 우선순위(낮은 confidence 순 + 위험도 반영)
    md.append("\n## 2) Review Priority (Low Confidence First)\n")
    md.append("아래 항목부터 우선 검토를 권장합니다. (status 위험도 + confidence 낮음)\n\n")
    for i, (rid, status, conf, matched, notes) in enumerate(rows_sorted[:10], start=1):
        md.append(f"{i}. **{rid}** — `{status}` (confidence={conf:.2f})\n")

    # (C) 추가 TC 추천 항목
    md.append("\n## 3) Additional TestCase Recommendations (from gaps)\n")
    md.append("partial / not_covered 요구사항의 gaps를 기반으로 추가 테스트를 추천합니다.\n")

    for rid, status, conf, matched, notes in rows_sorted:
        if status not in ("partial", "not_covered"):
            continue

        req = req_by_id[rid]
        md.append(f"\n### {rid} — {req.get('title','')}\n")
        md.append(f"- Status: `{status}` (confidence={conf:.2f})\n")
        md.append(f"- Currently mapped: {matched}\n")

        info = per_eval.get(rid, {})
        gaps = info.get("gaps", []) or []
        if gaps:
            md.append("- Identified gaps:\n")
            for g in gaps:
                md.append(f"  - {g}\n")
        else:
            md.append("- Identified gaps: (none provided)\n")

        recs = recommendations.get(rid, [])
        if not recs:
            md.append("\n**Suggested additional TCs:** (none)\n")
            continue

        md.append("\n**Suggested additional TCs:**\n")
        for idx, item in enumerate(recs, start=1):
            title = item.get("title", f"Additional TC {idx}")
            purpose = item.get("purpose", "")
            steps = item.get("suggested_steps", [])
            expected = item.get("expected", "")
            md.append(f"\n- **{title}**\n")
            if purpose:
                md.append(f"  - Purpose: {purpose}\n")
            if steps:
                md.append("  - Steps:\n")
                for s in steps:
                    md.append(f"    1. {s}\n")
            if expected:
                md.append(f"  - Expected: {expected}\n")

    report_md = "".join(md)

    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/report.md").write_text(report_md, encoding="utf-8")

    # 디버깅/추적용 JSON도 저장 (원하면 나중에 LangSmith 붙이기 좋음)
    Path("outputs/coverage_raw.json").write_text(
        json.dumps(state.get("llm_coverage", {}), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {**state, "report_md": report_md}
