from langchain_core.runnables import RunnableConfig
from .llm import get_llm
from .graph import build_graph

def main():
    llm = get_llm(model="qwen3:8b", temperature=0.0)
    app = build_graph(llm)

    objective = "qTest의 Requirements와 TestCase를 매핑하고, 전체 커버리지를 점검한 리포트를 만들어줘"

    config = RunnableConfig(
        recursion_limit=10,
        configurable={"thread_id": "qtest-coverage-001"},
    )

    out = app.invoke({"objective": objective, "batch_size": 10}, config=config)


    print("=== DONE ===")
    print("Covered:", out.get("covered_requirements", []))
    print("Partial:", out.get("partial_requirements", []))
    print("Not Covered:", out.get("uncovered_requirements", []))
    print("Unclear:", out.get("unclear_requirements", []))

    print("Report saved to outputs/report.md")

if __name__ == "__main__":
    main()
