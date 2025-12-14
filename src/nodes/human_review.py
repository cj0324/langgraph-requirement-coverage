from ..state import CoverageState

def human_review(state: CoverageState) -> CoverageState:
    print("\n" + "=" * 60)
    print("[Human Review]")
    print(f"- Coverage: {state.get('coverage_rate', 0.0) * 100:.1f}%")
    print(f"- Uncovered: {state.get('uncovered_requirements', [])}")
    print(f"- Weak(only 1 TC): {state.get('weak_requirements', [])}")
    print(f"- Over-tested(>=5 TC): {state.get('over_tested_requirements', [])}")
    print("=" * 60)

    print("\nChoose next action:")
    print("  1) approve (종료)")
    print("  2) revise_plan (플랜 다시 만들기)")
    print("  3) regenerate_report (리포트만 다시 생성)")

    while True:
        choice = input("Enter 1/2/3: ").strip()
        if choice in ("1", "2", "3"):
            break
        print("Invalid input. Please enter 1, 2, or 3.")

    if choice == "1":
        return {**state, "action": "approve"}
    elif choice == "2":
        feedback = input("플랜을 어떻게 바꾸고 싶어? (한 줄 피드백): ").strip()
        return {**state, "action": "revise_plan", "plan_feedback": feedback}
    else:
        # 리포트 생성 노드로만 다시 보냄
        return {**state, "action": "regenerate_report"}
