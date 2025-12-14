from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import CoverageState
from .nodes.load_data import load_data
from .nodes.plan_node import plan_node
from .nodes.evaluate_coverage import evaluate_coverage
from .nodes.generate_report import generate_report
from .nodes.human_review import human_review
from .nodes.evaluate_coverage_llm import evaluate_coverage_llm


def build_graph(llm):
    g = StateGraph(CoverageState)

    g.add_node("plan_node", lambda s: plan_node(s, llm))
    g.add_node("load_data", load_data)
    # g.add_node("evaluate_coverage", evaluate_coverage)
    g.add_node("generate_report", lambda s: generate_report(s, llm))
    g.add_node("human_review", human_review)
    g.add_node("evaluate_coverage", lambda s: evaluate_coverage_llm(s, llm))


    g.add_edge(START, "plan_node")
    g.add_edge("plan_node", "load_data")
    g.add_edge("load_data", "evaluate_coverage")
    g.add_edge("evaluate_coverage", "generate_report")
    g.add_edge("generate_report", "human_review")
    

    def route(state: CoverageState):
        return state.get("action", "approve")

    g.add_conditional_edges(
        "human_review",
        route,
        {
            "approve": END,
            "revise_plan": "plan_node",
            "regenerate_report": "generate_report",  # ✅ 추가
        },
    )

    return g.compile(checkpointer=MemorySaver())
