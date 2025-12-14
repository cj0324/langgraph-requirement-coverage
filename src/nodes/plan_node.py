from langchain_core.prompts import ChatPromptTemplate

PLAN_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 QA 커버리지 분석 워크플로우 플래너다.\n"
     "기존 계획과 사람의 피드백을 참고하여\n"
     "더 나은 단계별 계획을 다시 작성하라.\n"
     "단계는 5~8개, 한국어로 작성하라."),
    ("human",
     "목표:\n{objective}\n\n"
     "기존 계획:\n{current_plan}\n\n"
     "사람 피드백:\n{feedback}")
])

def plan_node(state, llm):
    objective = state.get("objective", "")
    current_plan = state.get("plan", [])
    feedback = state.get("plan_feedback", "없음")

    plan_text = (PLAN_PROMPT | llm).invoke({
        "objective": objective,
        "current_plan": "\n".join(current_plan),
        "feedback": feedback,
    }).content

    new_plan = [
        line.strip("- ").strip()
        for line in plan_text.splitlines()
        if line.strip()
    ]

    return {
        **state,
        "plan": new_plan,
        "plan_feedback": None,  # 한번 쓰고 비워도 좋음
    }
