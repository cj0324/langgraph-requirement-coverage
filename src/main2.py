from .llm import get_llm
from .nodes.load_data import load_data
from .nodes.plan_node import plan_node

from langgraph.graph import StateGraph, START, END


llm = get_llm()


class CoverageState2(TypedDict, total=False):
    objective: str


g = StateGraph(CoverageState2)

g.add_node("plan_node", plan_node)


g.add_edge(START, "plan_node")
g.add_edge("plan_node", END)